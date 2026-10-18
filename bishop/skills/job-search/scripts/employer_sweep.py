#!/usr/bin/env python
"""
Direct-employer board sweep: pull a named list of employers' job boards and
filter locally.

Part of Bishop, a free job-search plugin for Claude Code.
By Adam Hilliard - https://linkedin.com/in/adamhilliard - MIT licensed.

Why this exists: a scoring rubric has structural blind spots, and keyword
search cannot reach them. If the work-shape bucket is binary, an office a
mile away scores the same as one an hour away. If industry is a tiebreaker
rather than a bucket, the user's favorite industry never earns a point. The
countermeasure is to sweep a named set of employers every cycle regardless of
score. See "Technique: named-employer board sweeps" in search-techniques.md.

This script hardcodes NO employers. It reads them from the user's own
Employer_Index.md, which is the canonical list; this file is only the runner.

Index format. Any heading followed by a table with Platform and Slug columns
becomes a sweepable set:

    ## Employers in my metro, 100+ staff

    | Company    | Platform   | Slug       |
    |---|---|---|
    | Example Co | greenhouse | exampleco  |
    | Another Co | lever      | anotherco  |

Supported platforms and what goes in the Slug column. Every value is read off
the employer's own board or apply link, never guessed:

    greenhouse       board token:      boards.greenhouse.io/<slug>
    lever            company:          jobs.lever.co/<slug>
    ashby            board:            jobs.ashbyhq.com/<slug>
    workday          `host / tenant / site`, e.g.
                     `acme.wd5.myworkdayjobs.com / acme / ACMEUS`
    icims            tenant:           careers-<slug>.icims.com
    smartrecruiters  company id:       jobs.smartrecruiters.com/<slug>
    successfactors   careers host:     careers.acme.com
    jobvite          company path:     jobs.jobvite.com/<slug>/jobs
    avature          portal root:      jobs.acme.com/en_US/careers
    adp              client id (cid) from the ADP career-center link
    oracle           `host / siteNumber`, e.g.
                     `acme.fa.us2.oraclecloud.com / CX_1`

Multi-part slugs are slash-separated, not pipe-separated: a pipe inside a
table cell would break the table.

iCIMS, SuccessFactors, Jobvite and Avature boards are read from the board's
own HTML, because none of them has a public JSON API and iCIMS and
SuccessFactors listing pages are noindex, so keyword search never surfaces
their fresh reqs. The ADP and Oracle readers call the same endpoint the
employer's careers page calls for itself. Oracle, SuccessFactors and Avature
host their pages for the employer, so check the employer's careers-site terms
and robots.txt before adding a row (search-techniques.md, named-employer
board sweeps).

Title filters come from an HTML comment anywhere in the index, so they stay
invisible in the rendered document:

    <!-- sweep-config
    seniority  = manager|supervisor|lead|head of
    function   = operations|logistics|supply chain
    stretch    = (senior )?director
    step_down  = coordinator|associate
    comp_floor = 120
    no_pay     = all
    -->

`function` must match a title, plus one of the level tiers, for a row to be
reported. `seniority` is the target level; `stretch` (optional) is a rung up;
`step_down` (optional) is a rung down.

Comp is read in thousands against `comp_floor`:
  - A stated number below the floor holds a stretch or step_down row back
    (target rows are always reported; the caller screens their floor).
  - A row with NO stated pay is governed by `no_pay`:
      all               show every no-pay row (the default)
      except_step_down  show them except on step_down titles
      none              hold every no-pay row back
Held-back rows are listed separately so nothing disappears silently.
`stretch_comp_floor` is still accepted as an alias for `comp_floor`.

Usage:
    python employer_sweep.py                          # every set in the index
    python employer_sweep.py --set "my metro"          # one set, substring match
    python employer_sweep.py --index path/to/Index.md
    python employer_sweep.py --list                   # show sets and exit

Output: one matching row per line, then a STATUS line naming any board that
could not be read. An unreadable board is a coverage gap, not an empty one.
"""

import sys
import re
import json
import time
import os
import urllib.request
from html import unescape

if hasattr(sys.stdout, "reconfigure"):
    # Without this a single non-Latin-1 company name kills the run on Windows,
    # leaving a partial file that reads as complete. That is the exact silent
    # truncation the STATUS line exists to catch.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_SENIORITY = r"."         # match anything; the index should narrow this.
DEFAULT_FUNCTION = r"."          # A shipped default matching only senior titles
                                 # hides every other rung from anyone who never
                                 # writes a sweep-config.

# Paginating readers stop at this many rows and say so. A named-employer
# sweep is for a few dozen boards, not a 5,000-posting enterprise; a board
# that hits the cap is reported as partial on the STATUS line.
MAX_ROWS = 1000

CONFIG_RE = re.compile(r"<!--\s*sweep-config(.*?)-->", re.S | re.I)
HEADING_RE = re.compile(r"^#{2,4}\s+(.*?)\s*$")
ROW_RE = re.compile(r"^\|(.+)\|\s*$")


# --------------------------------------------------------------------------
# Reading the index
# --------------------------------------------------------------------------

def find_index(explicit=None):
    if explicit:
        if not os.path.isfile(explicit):
            sys.exit("no index file at %s" % explicit)
        return explicit
    for name in ("Employer_Index.md", "employer_index.md"):
        for d in (".", ".."):
            p = os.path.join(d, name)
            if os.path.isfile(p):
                return p
    sys.exit("no Employer_Index.md found. Pass --index PATH.")


def parse_config(text):
    cfg = {"seniority": DEFAULT_SENIORITY, "function": DEFAULT_FUNCTION,
           "stretch": "", "step_down": "",
           "comp_floor": "", "stretch_comp_floor": "0",
           "no_pay": "all"}
    m = CONFIG_RE.search(text)
    if m:
        for line in m.group(1).splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip().lower()
                if k in cfg:
                    cfg[k] = v.strip()
    return cfg


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_sets(text):
    """Return [(heading, [(company, platform, slug), ...]), ...].

    A set is any heading whose section contains a table with Platform and Slug
    columns. Tables without those columns (prose tables, tier notes) are
    skipped, so the index can hold plenty that is not sweepable.
    """
    sets, heading, header, idx = [], None, None, {}
    current = []

    def flush():
        if heading and current:
            sets.append((heading, list(current)))

    for line in text.splitlines():
        h = HEADING_RE.match(line)
        if h:
            flush()
            heading, header, idx, current = h.group(1), None, {}, []
            continue
        r = ROW_RE.match(line)
        if not r:
            continue
        cells = split_row(r.group(1))
        if set("".join(cells)) <= set("-: "):        # separator row
            continue
        low = [c.lower() for c in cells]
        if "platform" in low and "slug" in low:      # header row
            header = low
            idx = {"platform": low.index("platform"), "slug": low.index("slug"),
                   "company": low.index("company") if "company" in low else 0}
            continue
        if not header:
            continue
        if max(idx.values()) >= len(cells):
            continue
        company = re.sub(r"[*`\[\]]", "", cells[idx["company"]]).strip()
        platform = cells[idx["platform"]].strip().lower().strip("`")
        slug = cells[idx["slug"]].strip().strip("`")
        if company and platform and slug:
            current.append((company, platform, slug))
    flush()
    return sets


# --------------------------------------------------------------------------
# Pulling boards
# --------------------------------------------------------------------------

def get(url, data=None, headers=None):
    h = {"User-Agent": "Mozilla/5.0"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    return json.load(urllib.request.urlopen(req, timeout=30))


def get_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


class PartialRead(Exception):
    """A board that was read up to a cap. `rows` holds what was read; the
    sweep still filters them and names the board on the STATUS line, because
    a cut-off board is a coverage gap even when its first thousand rows were
    fine.
    """
    def __init__(self, why, rows):
        super().__init__(why)
        self.rows = rows


def pull(platform, slug):
    """Return a list of (title, location, comp_summary) or raise.

    comp_summary is whatever the board publishes, or "". An absent value must
    stay an empty string: comp_k reads that as "no number stated", which the
    no_pay rule handles separately from a stated number below the floor.
    """
    if platform == "greenhouse":
        d = get("https://boards-api.greenhouse.io/v1/boards/%s/jobs" % slug)
        return [(j.get("title", ""), (j.get("location") or {}).get("name", ""), "")
                for j in d.get("jobs", [])]
    if platform == "lever":
        d = get("https://api.lever.co/v0/postings/%s?mode=json" % slug)
        return [(j.get("text", ""), (j.get("categories") or {}).get("location", ""), "")
                for j in d]
    if platform == "ashby":
        d = get("https://api.ashbyhq.com/posting-api/job-board/%s"
                "?includeCompensation=true" % slug)
        # workplaceType is the posting's own field. isRemote is NOT the same
        # thing and the two disagree routinely, so print the real one. It goes
        # FIRST because the location column gets truncated for display and this
        # is the field the location screen actually turns on.
        return [(j.get("title", ""),
                 "[%s] %s" % (j.get("workplaceType", "?"), j.get("location", "")),
                 (j.get("compensation") or {}).get("compensationTierSummary") or "")
                for j in d.get("jobs", [])]
    if platform == "workday":
        parts = [p.strip().strip("`") for p in re.split(r"[/|,]", slug) if p.strip()]
        if len(parts) != 3:
            raise ValueError("workday slug needs host / tenant / site, got %r" % slug)
        host, tenant, site = parts
        out, offset = [], 0
        while offset < 400:
            body = json.dumps({"appliedFacets": {}, "limit": 20, "offset": offset,
                               "searchText": ""}).encode()
            d = get("https://%s/wday/cxs/%s/%s/jobs" % (host, tenant, site), body,
                    {"content-type": "application/json"})
            posts = d.get("jobPostings", [])
            if not posts:
                break
            out += [(p.get("title", ""), p.get("locationsText", ""), "") for p in posts]
            offset += 20
            if offset >= (d.get("total") or 0):
                break
            time.sleep(0.2)
        return out
    if platform == "icims":
        # iCIMS has no clean JSON API and its listing pages are noindex, so
        # keyword search misses fresh reqs. The in-iframe search page returns
        # the whole current board server-side, no auth, no JS. slug is the
        # tenant: "acmecareers" -> careers-acmecareers.icims.com. Each job card
        # carries an anchor whose title attribute is "<id> - <Title>" and a
        # "Job Locations" span; paginate on pr until a page adds no new ids.
        out, seen, pr = [], set(), 0
        while pr < 25:
            page = get_text("https://careers-%s.icims.com/jobs/search"
                            "?in_iframe=1&pr=%d" % (slug, pr))
            new = 0
            for card in page.split("iCIMS_JobCardItem")[1:]:
                mt = re.search(r'iCIMS_Anchor"\s+title="(\d+)\s*-\s*([^"]+)"',
                               card)
                if not mt or mt.group(1) in seen:
                    continue
                seen.add(mt.group(1))
                new += 1
                ml = re.search(
                    r"Job Locations</span>\s*<span[^>]*>\s*([^<]+)", card)
                out.append((unescape(mt.group(2)).strip(),
                            unescape(ml.group(1)).strip() if ml else "", ""))
            if new == 0:
                break
            pr += 1
            time.sleep(0.2)
        return out
    if platform == "smartrecruiters":
        # Public postings API, 100 per page. slug is the company identifier
        # in the board URL: jobs.smartrecruiters.com/<slug>. Large tenants run
        # past the 1,000-row cap, so say so rather than return quietly.
        out, offset, total = [], 0, 0
        while offset < MAX_ROWS:
            d = get("https://api.smartrecruiters.com/v1/companies/%s/postings"
                    "?limit=100&offset=%d" % (slug, offset))
            rows = d.get("content", [])
            total = d.get("totalFound") or 0
            for j in rows:
                loc = j.get("location") or {}
                out.append((j.get("name", ""),
                            ", ".join(x for x in (loc.get("city"), loc.get("region")) if x),
                            ""))
            offset += 100
            if not rows or offset >= total:
                break
            time.sleep(0.2)
        out = list(dict.fromkeys(out))
        if total > offset:
            raise PartialRead("%d of %d postings read" % (len(out), total), out)
        return out
    if platform == "successfactors":
        # SAP SuccessFactors Career Site Builder renders results server-side;
        # there is no JSON call to use. slug is the careers host, e.g.
        # careers.example.com. Its robots.txt usually bars /services/ and
        # allows /search/, which is the page read here. Page size is set per
        # site, so step by what each page returned. Two page templates are in
        # use, tiles and the older table of data-rows; both are handled.
        out, seen, start, total = [], set(), 0, 0
        while start < MAX_ROWS:
            page = get_text("https://%s/search/?q=&startrow=%d" % (slug, start))
            tiles = (page.split('class="job-tile job-id-')[1:]
                     or page.split('<tr class="data-row')[1:])
            mt = (re.search(r"Showing \d+ to \d+ of (\d+)", page)
                  or re.search(r"paginationLabel.*?of <b>(\d+)</b>", page))
            total = int(mt.group(1)) if mt else 0
            new = 0
            for tile in tiles:
                mt = re.search(r'class="jobTitle-link[^"]*"[^>]*>\s*([^<]+?)\s*</a>', tile)
                mi = re.search(r'href="[^"]*/job/[^"]*/(\d+)/"', tile)
                if not mt or not mi or mi.group(1) in seen:
                    continue
                seen.add(mi.group(1))
                new += 1
                ml = (re.search(r'<div id="[^"]*-section-location-value"[^>]*>\s*([^<]+?)\s*<', tile)
                      or re.search(r'colLocation[^>]*>\s*<span class="jobLocation">\s*([^<]+?)\s*<', tile))
                out.append((unescape(mt.group(1)),
                            unescape(ml.group(1)) if ml else "", ""))
            start += len(tiles)
            if new == 0 or start >= total:
                break
            time.sleep(0.2)
        if total > len(out):
            raise PartialRead("%d of %d postings read" % (len(out), total), out)
        return out
    if platform == "jobvite":
        # Jobvite's hosted board lists every opening on one server-rendered
        # page, grouped by department. slug is the company path in
        # jobs.jobvite.com/<slug>/jobs.
        page = get_text("https://jobs.jobvite.com/%s/jobs" % slug)
        rows = re.findall(r'jv-job-list-name">\s*<a href="[^"]+">([^<]+)</a>\s*</td>'
                          r'\s*<td class="jv-job-list-location">(.*?)</td>', page, re.S)
        return [(unescape(t).strip(), re.sub(r"\s+", " ", unescape(l)).strip(), "")
                for t, l in rows]
    if platform == "avature":
        # Avature career portal, server-rendered, read through the portal's
        # own listing page. slug is the listing root without the scheme, e.g.
        # jobs.example.com/en_US/careers. Templates differ between portals,
        # so rows are keyed on the JobDetail links every template carries,
        # and the location is read from the list-item-location span. Confirm
        # by hand that page two returns different jobs before adding a
        # portal: a landing page that ignores jobOffset reads as a short,
        # complete board. Check the portal's robots.txt allows the path.
        out, seen, offset, total = [], set(), 0, 0
        while offset < MAX_ROWS:
            page = get_text("https://%s/Home/?jobRecordsPerPage=20&jobOffset=%d"
                            % (slug, offset))
            mt = re.search(r'aria-label="(\d+) results"', page)
            total = int(mt.group(1)) if mt else total
            new = 0
            parts = re.split(r'(?=<a[^>]+href="[^"]*/JobDetail/)', page)[1:]
            for part in parts:
                mh = re.match(r'<a[^>]+href="[^"]*/JobDetail/(?:[^"]*/)?(\d+)/?"[^>]*>(.*?)</a>',
                              part, re.S)
                if not mh or mh.group(1) in seen:
                    continue
                title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", mh.group(2))).strip()
                if not title:
                    continue
                seen.add(mh.group(1))
                new += 1
                ml = re.search(r'list-item-location"[^>]*>(.*?)</span>\s*(?:</span>|<span class="separator)',
                               part, re.S)
                loc = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", ml.group(1))).strip() if ml else ""
                out.append((unescape(title), unescape(loc), ""))
            if new == 0:
                break
            offset += 20
            if total and offset >= total:
                break
            time.sleep(0.2)
        if total > len(out):
            raise PartialRead("%d of %d postings read" % (len(out), total), out)
        return out
    if platform == "adp":
        # ADP Workforce Now career center. slug is the client id (cid), read
        # off the employer's own careers link, optionally followed by the
        # locale the link carries: `<cid> / en_CA`. This is the call the
        # career-center page makes itself. The API serves 20 rows a page
        # whatever $top asks, and $skip counts from 1. A tenant answers only
        # in its own locale (an en_CA client returns nothing for en_US), so
        # a few are tried when none is given.
        parts = [x.strip().strip("`") for x in re.split(r"[/|,]", slug) if x.strip()]
        cid = parts[0]
        locales = parts[1:] or ["en_US", "en_CA", "en_GB"]
        url = ("https://workforcenow.adp.com/mascsr/default/careercenter/public/"
               "events/staffing/v1/job-requisitions?cid=%s&ccId=19000101_000001"
               "&lang=%s&locale=%s&$top=20&$skip=%d")
        for loc in locales:
            out, skip, total = [], 1, 0
            while len(out) < MAX_ROWS:
                d = get(url % (cid, loc, loc, skip))
                reqs = d.get("jobRequisitions", [])
                total = (d.get("meta") or {}).get("totalNumber") or 0
                out += [(r.get("requisitionTitle", ""),
                         "; ".join(filter(None, ((l.get("address") or {}).get("cityName")
                                                 for l in r.get("requisitionLocations", [])))),
                         "")
                        for r in reqs]
                if not reqs or len(out) >= total:
                    break
                skip += 20
                time.sleep(0.2)
            if out or d.get("meta"):
                if total > len(out):
                    raise PartialRead("%d of %d postings read" % (len(out), total), out)
                return out
        return []
    if platform == "oracle":
        # Oracle Recruiting Cloud candidate site. slug is `host / siteNumber`,
        # e.g. `example.fa.us2.oraclecloud.com / CX_1`, both read off the
        # employer's apply link. This is the call the candidate-experience page
        # makes itself, no auth. Oracle hosts the page for the employer; read
        # the terms of the employer's own careers site before adding a row.
        parts = [p.strip().strip("`") for p in re.split(r"[/|,]", slug) if p.strip()]
        if len(parts) != 2:
            raise ValueError("oracle slug needs host / siteNumber, got %r" % slug)
        host, site = parts
        out, offset, total = [], 0, 0
        while offset < MAX_ROWS:
            d = get("https://%s/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
                    "?onlyData=true&expand=requisitionList.secondaryLocations"
                    "&finder=findReqs;siteNumber=%s,limit=25,offset=%d,"
                    "sortBy=POSTING_DATES_DESC" % (host, site, offset))
            item = (d.get("items") or [{}])[0]
            reqs = item.get("requisitionList") or []
            total = item.get("TotalJobsCount") or 0
            out += [(r.get("Title", ""), r.get("PrimaryLocation", ""), "")
                    for r in reqs]
            offset += 25
            if not reqs or offset >= total:
                break
            time.sleep(0.2)
        if total > len(out):
            raise PartialRead("%d of %d postings read" % (len(out), total), out)
        return out
    raise ValueError("unknown platform %r" % platform)


def comp_k(comp_summary):
    """Highest salary figure in the summary, in thousands, or None when the
    board stated no pay. Absent must read as None, not 0: the no_pay rule and
    the floor test treat "no number" and "a low number" differently.
    """
    if not comp_summary:
        return None
    nums = [int(m.group(1)) for m in re.finditer(r"\$(\d{2,3})K", comp_summary, re.I)]
    nums += [int(m.group(1).replace(",", "")) // 1000
             for m in re.finditer(r"\$(\d{1,3}(?:,\d{3})+)", comp_summary)]
    return max(nums) if nums else None


def classify(tier, comp_summary, floor_k, no_pay):
    """Return 'hit' (report the row) or 'held' (list it under held-back, never
    drop it). tier is 'target', 'step_up', or 'step_down'.
    """
    k = comp_k(comp_summary)
    if k is not None:
        # A stated number. Target rows are always reported (the caller screens
        # their floor); an off-target row must clear the floor to earn a spot.
        if tier == "target" or floor_k <= 0 or k >= floor_k:
            return "hit"
        return "held"
    # No stated pay: the user's no_pay choice decides.
    if no_pay == "none":
        return "held"
    if no_pay == "except_step_down" and tier == "step_down":
        return "held"
    return "hit"


# --------------------------------------------------------------------------
# Sweeping
# --------------------------------------------------------------------------

def sweep(name, board, seniority, function, stretch, step_down, floor_k, no_pay):
    hits, held, failed, scanned = [], [], [], 0
    print("=== %s (%d boards) ===" % (name, len(board)))
    for company, platform, slug in board:
        try:
            rows = pull(platform, slug)
        except PartialRead as e:
            rows = e.rows
            failed.append("%s (partial: %s)" % (company, e))
        except Exception as e:
            failed.append("%s (%s)" % (company, str(e)[:40]))
            continue
        scanned += len(rows)
        for title, loc, comp in rows:
            if not function.search(title):
                continue
            if seniority.search(title):
                tier = "target"
            elif stretch and stretch.search(title):
                tier = "step_up"
            elif step_down and step_down.search(title):
                tier = "step_down"
            else:
                continue
            if classify(tier, comp, floor_k, no_pay) == "hit":
                hits.append((company, title, loc, comp or ""))
            else:
                held.append((company, title, tier, comp or "no pay posted"))
        time.sleep(0.2)

    for c, t, l, comp in sorted(hits):
        print("  %-22s | %-52s | %-26s | %s" % (c, t[:52], l[:26], comp[:28]))
    if not hits:
        print("  (no target-title matches)")
    if held:
        print("  -- %d off-target rows held back (below the $%dK floor, or no pay "
              "posted under no_pay=%s):" % (len(held), floor_k, no_pay))
        for c, t, tier, reason in sorted(held):
            print("       %-20s | %-40s | %-9s | %s" % (c, t[:40], tier, reason[:24]))
        print("     Add one by hand only with a reason the board cannot show.")
    print("  scanned %d postings across %d boards" % (scanned, len(board)))
    return failed


def arg(flag, default=None):
    """Value following `flag`, or default. Safe when the flag is last."""
    if flag not in sys.argv:
        return default
    i = sys.argv.index(flag) + 1
    return sys.argv[i] if i < len(sys.argv) else default


def main():
    path = find_index(arg("--index"))
    text = open(path, encoding="utf-8").read()
    cfg = parse_config(text)
    sets = parse_sets(text)

    if not sets:
        sys.exit("no employer tables found in %s. Each set needs a heading plus a "
                 "table with Platform and Slug columns." % path)

    if "--list" in sys.argv:
        print("Sets in %s:" % path)
        for h, b in sets:
            print("  %-40s %d boards" % (h, len(b)))
        return

    wanted = arg("--set")
    if wanted:
        sets = [(h, b) for h, b in sets if wanted.lower() in h.lower()]
        if not sets:
            sys.exit("no set matching %r. Run --list to see them." % wanted)

    seniority = re.compile(cfg["seniority"], re.I)
    function = re.compile(cfg["function"], re.I)
    stretch = re.compile(cfg["stretch"], re.I) if cfg["stretch"] else None
    step_down = re.compile(cfg["step_down"], re.I) if cfg["step_down"] else None
    try:
        floor_k = int(cfg["comp_floor"] or cfg["stretch_comp_floor"])
    except ValueError:
        floor_k = 0
    no_pay = cfg["no_pay"].strip().lower()
    if no_pay not in ("all", "except_step_down", "none"):
        no_pay = "all"

    print("index: %s" % path)
    failed = []
    for heading, board in sets:
        failed += sweep(heading.upper(), board, seniority, function, stretch,
                        step_down, floor_k, no_pay)

    print("-" * 60)
    if failed:
        print("STATUS: INCOMPLETE - unreadable or partly read boards: %s" % "; ".join(failed))
        print("        Report this as a coverage gap in the digest.")
        sys.exit(1)
    print("STATUS: COMPLETE - every listed board read.")


if __name__ == "__main__":
    main()
