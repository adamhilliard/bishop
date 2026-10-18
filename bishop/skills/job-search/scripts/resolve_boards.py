#!/usr/bin/env python
"""
Resolve company names to confirmed job-board endpoints.

Part of Bishop, a free job-search plugin for Claude Code.
By Adam Hilliard - https://linkedin.com/in/adamhilliard - MIT licensed.

Why this exists: building a named-employer list is easy, but a list of names
is not sweepable. Each company needs its applicant tracking system and its
board slug, and the standing rule is never to add a row on a guessed slug.
This script does the probing so the rule is cheap to follow: it tries slug
candidates against each platform's public API and keeps only the ones that
return a real board payload. A confirmed 200 with the expected shape is not a
guess.

Feed it the output of a "major employers in <metro>" or "companies in
<industry>" search. It prints a markdown table ready to paste into
Employer_Index.md, plus the unresolved names as a separate tier.

Usage:
    python resolve_boards.py --names "Acme Health,Northwind Logistics"
    python resolve_boards.py --file companies.txt      # one name per line
    echo "Acme Co" | python resolve_boards.py

Workday needs a hint, because a Workday site name cannot be derived from the
company name. Put the tenant and site after a pipe, or paste any Workday URL
for the employer (the apply link on one of their postings is the usual
source); the host in the URL is ignored:

    Acme Co | acme/ACMEUS
    Acme Co | https://acme.wd1.myworkdayjobs.com/ACMEUS

The hinted tenant and site are then tried on every Workday host in
WORKDAY_HOSTS. The host is the part people get wrong: a board can answer only
on wd503 while every other live host returns 422 for the same tenant and
site, and a probe on the wrong host reads as "no board".

Options:
    --slow      2s between probes instead of 0.4s, for large lists
    --loose     also try shortened slugs on platforms that cannot be verified.
                Recovers boards whose slug is shorter than the company name,
                at the cost of rows you must check yourself. Off by default:
                a confident wrong board is worse than an unresolved one.
    --verbose   print every candidate tried, not just the hits

Output is two markdown tables. The first is Tier A, confirmed and sweepable
by employer_sweep.py. The second is Tier B: real companies whose board sits
on a platform without a public API, or under a slug this script could not
guess. **Tier B is unresolved access, not a negative finding.** Resolve those
by hand on a cycle where the browser is already connected, and never record
them as "no openings."
"""

import sys
import re
import json
import time
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Dropped when generating slug candidates. Legal and structural suffixes only:
# never drop a word that could be part of the trading name.
SUFFIXES = {
    "inc", "inc.", "llc", "l.l.c.", "ltd", "ltd.", "limited", "corp", "corp.",
    "corporation", "co", "co.", "company", "holdings", "holding", "plc", "gmbh",
    "sa", "nv", "ag", "lp", "llp", "pllc", "pc", "the",
}

# The platforms probed from a bare name. employer_sweep.py sweeps more
# (workday, icims, smartrecruiters, successfactors, jobvite, avature, adp,
# oracle), but those slugs cannot be derived from a company name; read them
# off the employer's apply link instead. Workday is probed from a hint.
PLATFORMS = ("greenhouse", "lever", "ashby")

# Workday data-center hosts, tried in order for a hinted tenant/site. A host
# that does not exist fails DNS quickly, so the list errs wide. Seen on live
# boards: wd1, wd3, wd5, wd108, wd503.
WORKDAY_HOSTS = ("wd1", "wd2", "wd3", "wd5", "wd10", "wd12", "wd100", "wd101",
                 "wd102", "wd103", "wd105", "wd108", "wd501", "wd502", "wd503")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def words_of(name):
    clean = re.sub(r"\([^)]*\)", " ", name)                 # drop parentheticals
    words = [w for w in re.split(r"[\s,&/]+", clean) if w]
    words = [w for w in words if w.lower().strip(".") not in SUFFIXES]
    return words or [name]


def candidates(name, loose):
    """Slug guesses, most likely first.

    `loose` adds first-word and acronym forms. Those are only safe on a
    platform that publishes the board's own name, because they are exactly the
    guesses that land on a DIFFERENT company: "Universal Music Group" reduces
    to "universal", which is a real board belonging to somebody else. A
    confident wrong answer is worse than a 404, so an unverifiable platform
    gets the tight candidates only.
    """
    words = words_of(name)
    out = [norm("".join(words)), "-".join(norm(w) for w in words if norm(w))]
    if loose:
        out.append(norm(words[0]))
        acronym = "".join(w[0] for w in words if w[:1].isalpha()).lower()
        if len(words) > 1 and len(acronym) >= 2:
            out.append(acronym)
    seen, uniq = set(), []
    for c in out:
        if c and c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq


def name_matches(company, board_name):
    """True when the board plausibly belongs to this company.

    Every significant word of the company name has to appear in the board's
    own name. Containment in the other direction is not enough: "Universal"
    sits inside "Universal Music Group" while being a different employer.
    """
    if not board_name:
        return False
    bn = norm(board_name)
    return all(norm(w) in bn for w in words_of(company) if norm(w))


def fetch(url, data=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            if r.status != 200:
                return None
            return json.load(r)
    except Exception:
        return None


def probe(platform, slug, company):
    """Return (ok, verification) for one slug on one platform.

    An empty board is still a resolution: a company with no current openings
    has a valid endpoint. Shape is what's checked, never posting count.
    """
    if platform == "greenhouse":
        meta = fetch("https://boards-api.greenhouse.io/v1/boards/%s" % slug)
        if not isinstance(meta, dict) or "name" not in meta:
            return False, ""
        # Greenhouse is the one platform that publishes the board's own name,
        # so it is the one platform where a loose guess can be checked.
        if not name_matches(company, meta.get("name")):
            return False, ""
        return True, "name match (%s)" % meta.get("name")

    if platform == "lever":
        d = fetch("https://api.lever.co/v0/postings/%s?mode=json" % slug)
        return (isinstance(d, list), "slug only") if isinstance(d, list) else (False, "")

    if platform == "ashby":
        d = fetch("https://api.ashbyhq.com/posting-api/job-board/%s" % slug)
        # A bad slug returns an error object rather than a 404 here, so the
        # jobs key is what separates a real board from a rejection.
        if isinstance(d, dict) and "jobs" in d:
            return True, "slug only"
        return False, ""
    return False, ""


def workday_hint(hint):
    """(tenant, site) from "tenant/site" or any myworkdayjobs URL, else None."""
    m = re.search(r"([a-z0-9-]+)\.wd\d+\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([A-Za-z0-9_-]+)",
                  hint)
    if m:
        return m.group(1), m.group(2)
    m = re.fullmatch(r"\s*([a-z0-9-]+)\s*/\s*([A-Za-z0-9_-]+)\s*", hint)
    return (m.group(1), m.group(2)) if m else None


def resolve_workday(tenant, site, delay, verbose):
    """Try one tenant/site on every Workday host. Returns (slug, total) or
    (None, None).

    Shape is the check: a 200 carrying `total` and `jobPostings`. A wrong host
    answers 422, so a hit here is the real board, not a near miss. The slug
    comes back in employer_sweep.py's `host / tenant / site` form.
    """
    body = json.dumps({"appliedFacets": {}, "limit": 1, "offset": 0,
                       "searchText": ""}).encode()
    for wd in WORKDAY_HOSTS:
        host = "%s.%s.myworkdayjobs.com" % (tenant, wd)
        if verbose:
            print("    trying %-12s %s" % ("workday", host), file=sys.stderr)
        d = fetch("https://%s/wday/cxs/%s/%s/jobs" % (host, tenant, site), body)
        if isinstance(d, dict) and "jobPostings" in d and "total" in d:
            return "%s / %s / %s" % (host, tenant, site), d.get("total")
        time.sleep(delay)
    return None, None


def resolve(name, delay, verbose, wide=False):
    """Try tight candidates on every platform, then loose ones.

    Loose candidates go to Greenhouse by default, because Greenhouse is the
    only platform that lets a loose guess be checked against the board's own
    name. `wide` sends them everywhere, which recovers real boards whose slug
    is shorter than their name (a company trading as "Illumination
    Entertainment" on `lever/illumination`) at the cost of rows nothing can
    verify. Those get labelled so they are obvious.
    """
    tight = candidates(name, loose=False)
    loose = [s for s in candidates(name, loose=True) if s not in tight]

    attempts = [(p, s, False) for s in tight for p in PLATFORMS]
    if wide:
        attempts += [(p, s, True) for s in loose for p in PLATFORMS]
    else:
        attempts += [("greenhouse", s, True) for s in loose]

    for platform, slug, is_loose in attempts:
        if verbose:
            print("    trying %-12s %s" % (platform, slug), file=sys.stderr)
        ok, how = probe(platform, slug, name)
        if ok:
            if is_loose and how == "slug only":
                how = "LOOSE GUESS, verify before use"
            return platform, slug, how
        time.sleep(delay)
    return None, None, ""


def read_names():
    if "--names" in sys.argv:
        i = sys.argv.index("--names") + 1
        raw = sys.argv[i] if i < len(sys.argv) else ""
        return [n.strip() for n in raw.split(",") if n.strip()]
    if "--file" in sys.argv:
        i = sys.argv.index("--file") + 1
        if i >= len(sys.argv):
            sys.exit("--file needs a path")
        with open(sys.argv[i], encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    if not sys.stdin.isatty():
        return [ln.strip() for ln in sys.stdin if ln.strip()]
    sys.exit("give me names: --names \"A,B\" or --file list.txt or stdin")


def main():
    names = read_names()
    delay = 2.0 if "--slow" in sys.argv else 0.4
    verbose = "--verbose" in sys.argv
    wide = "--loose" in sys.argv

    print("probing %d companies across %s (workday for hinted rows)\n"
          % (len(names), ", ".join(PLATFORMS)), file=sys.stderr)

    hits, misses = [], []
    for line in names:
        n, _, hint = (x.strip() for x in line.partition("|"))
        wd = workday_hint(hint) if hint else None
        if hint and not wd:
            print("  ??   %-28s hint not understood: %s" % (n[:28], hint), file=sys.stderr)
        if wd:
            slug, total = resolve_workday(wd[0], wd[1], delay, verbose)
            if slug:
                hits.append((n, "workday", slug,
                             "host probe, %s postings; tenant/site from hint" % total))
                print("  ok   %-28s workday / %s" % (n[:28], slug), file=sys.stderr)
                continue
        platform, slug, how = resolve(n, delay, verbose, wide)
        if platform:
            hits.append((n, platform, slug, how))
            print("  ok   %-28s %s / %-22s %s" % (n[:28], platform, slug, how),
                  file=sys.stderr)
        else:
            misses.append(n)
            print("  --   %-28s unresolved" % n[:28], file=sys.stderr)

    unverified = [h for h in hits if h[3] != ""
                  and not h[3].startswith(("name match", "host probe"))]

    print("## Tier A: confirmed boards, swept every cycle\n")
    if hits:
        print("| Company | Platform | Slug | Confirmed by |")
        print("|---|---|---|---|")
        for n, p, s, how in sorted(hits):
            print("| %s | %s | `%s` | %s |" % (n, p, s, how))
        if unverified:
            print("\n> **Spot-check the %d row(s) confirmed by slug only.** Lever "
                  "and Ashby don't publish the board's own name, so those "
                  "resolutions rest on an exact name-to-slug match returning a "
                  "real board. That is strong but not proof. Open one posting "
                  "and confirm the employer before trusting the row."
                  % len(unverified))
    else:
        print("_None resolved. Every name is in Tier B below._")

    print("\n## Tier B: board not yet resolved\n")
    if misses:
        print("**Unresolved access, not a negative finding.** These are real "
              "employers whose board is on a platform without a public API, or "
              "under a slug this probe could not guess. Resolve by hand on a "
              "cycle where the browser is connected. Never record one as "
              "having no openings.\n")
        print("| Company | Known access |")
        print("|---|---|")
        for n in sorted(misses):
            print("| %s | unresolved, follow their careers page's apply link |" % n)
    else:
        print("_All names resolved._")

    print("\n---", file=sys.stderr)
    print("resolved %d of %d. Paste the tables above into Employer_Index.md."
          % (len(hits), len(names)), file=sys.stderr)


if __name__ == "__main__":
    main()
