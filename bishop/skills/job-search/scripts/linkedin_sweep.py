#!/usr/bin/env python
"""
LinkedIn guest-search sweep for the job-search digest.

Why this file exists: two silent truncation bugs, found 8/4/26, both of which
made a partial result set look identical to a complete one.

  1. The authenticated results page is virtualized. A query reporting 51
     results rendered only 12 of its 25 first-page cards, and no amount of
     scrolling forced the rest.
  2. The guest endpoint returns TEN cards per page, not 25. The ad-hoc script
     that replaced (1) stepped `start` by 25, so it skipped 15 results per
     page while looking like it was paginating correctly.

Both failures are invisible downstream: the digest just reports fewer roles.
So this tool refuses to report a result set it cannot vouch for. Every run
ends with either COMPLETE or an explicit INCOMPLETE line naming what was
missed, and callers are expected to surface INCOMPLETE in the digest as a
coverage gap the same way a skipped LinkedIn run is surfaced.

Usage:
    python linkedin_sweep.py "<keywords>" "<location>" [--window r604800] [--remote]
                             [--max-rows N] [--retries 2] [--cooldown 45]
                             [--passes 2]

    --window     r604800 = past week (default), r2592000 = past month
    --remote     adds f_WT=2
    --max-rows   stop after roughly N rows (default: uncapped)
    --retries    whole-bucket cooldown-retries on a throttle (default 2)
    --cooldown   seconds to wait between bucket retries (default 45)
    --passes     independent full sweeps of the bucket, unioned (default 2).
                 The guest endpoint samples non-deterministically; one pass
                 silently drops a chunk of real roles. See "Why repeat-and-
                 union" below. --passes 1 restores single-pass behavior.

Output: one "id ~ title ~ company ~ location ~ date" line per unique posting,
then a STATUS line. Parse the STATUS line; do not trust the rows without it.
Progress is written to STDERR so a caller can see the sweep is working and not
hung; only rows and the STATUS line go to STDOUT.

STATUS values, and they mean different things:

  COMPLETE            paginated until LinkedIn stopped serving new ids, with
                      no unreadable pages and no mid-stream short page.
  INCOMPLETE          a real coverage gap; report it in the digest. The line
                      names the cause: THROTTLED (the guest endpoint blocked
                      the whole bucket, even after retries), unreadable pages
                      (holes in the middle), a short page (a dropped page,
                      fewer than 10 cards before exhaustion), or the cap.
  CUT AT n (policy)   we chose to stop (--max-rows). NOT a gap, NOT complete.

Retry-before-bail:

  The guest-endpoint throttle is INTERMITTENT, not a hard block: a bucket that
  hangs one minute paginates cleanly the next. So a throttle is retryable
  state, not a reason to bail to a lossy partial:

    * fetch() times out fast (15s) and distinguishes a throttle (429 /
      timeout / connection error -> None) from the genuine end of results
      (400 / 404 -> "").
    * A run of HARD_BLOCK_STREAK consecutive unreadable pages is treated as a
      throttle onset: the attempt bails immediately rather than grinding every
      page to the cap at ~90s each (which is what looks "hung" and gets the
      process killed).
    * The whole bucket is then re-run after a cooldown, up to --retries times.
      An intermittent throttle usually clears, so the retry returns COMPLETE
      where the first attempt would have been a lossy INCOMPLETE.
    * Only if every retry still fails does it report INCOMPLETE / THROTTLED,
      which tells the caller to rerun the bucket later -- never to trust a
      partial as if it were complete.

Why the sweep is uncapped by default:

  A policy cap on the theory that the tail past N rows is relevance-decay
  padding did not survive measurement. Two runs of the same query on the same
  day shared only ~87% of their rows, so the first N is a different N each run,
  not a stable prefix, and the cut was discarding roughly a quarter of what the
  endpoint would serve. Narrowing the query does not get under the ceiling and
  neither does the date window; what a bucket exhausts at is a property of the
  endpoint. So the cut is off by default and SAFETY_CAP sits above the observed
  ceiling, so a genuine exhaustion reports COMPLETE rather than tripping the
  runaway guard. --max-rows still forces a deliberate stop.

Why repeat-and-union:

  The single largest cause of missed roles is not the throttle, the sort, or
  the stem list. It is that the guest endpoint returns a DIFFERENT, INCOMPLETE
  sample on every call, even for the identical query in the same minute.

  Measured on one quoted-title bucket: three back-to-back runs returned 289,
  285 and 283 rows, but their UNION was 399 unique roles. Any single run held
  only ~71% of it, and 92 roles (23%) appeared in exactly ONE of the three
  runs. A real, in-window role was absent from one run and present in the other
  two -- a coin-flip per pass.

  So a single pass, however clean its STATUS, silently drops roughly a quarter
  of the matching set, fresh roles at the same rate as any other. The sort
  cannot protect them: sortBy=DD is not honored by this endpoint (the date
  order comes back jumbled either way).

  The fix is to run the bucket --passes times and union by job id. Union
  coverage rises fast (~71% one pass -> ~92% two -> ~98% three on the measured
  bucket), and a role has to lose the coin-flip on EVERY pass to be missed.
  This is the default now (--passes 2). It composes with the retry logic above:
  each pass still retries its own throttle before contributing to the union.

Part of Bishop, a free job-search plugin for Claude Code.
By Adam Hilliard - https://linkedin.com/in/adamhilliard - MIT licensed.
"""

import sys
import re
import time
import html
import urllib.request
import urllib.error

PAGE = 10                 # guest API page size, verified 8/4/26, NOT 25
SAFETY_CAP = 1200         # runaway guard, set above the observed guest-endpoint
                          # ceiling so a genuine exhaustion reports COMPLETE
EMPTY_STREAK_DONE = 2     # consecutive no-new-id pages that mean "exhausted"
HARD_BLOCK_STREAK = 3     # consecutive unreadable pages that mean "throttled"
DEFAULT_RETRIES = 2       # whole-bucket cooldown-retries on a throttle
DEFAULT_COOLDOWN = 45     # seconds between bucket retries
DEFAULT_PASSES = 2        # independent sweeps unioned per bucket
BASE = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/"
        "search?keywords={q}&location={loc}&f_TPR={tpr}{wt}&start={start}")


def fetch(url, attempts=3):
    """Page HTML, or "" at the genuine end of results, or None if blocked.

    None means the page could not be read after `attempts` (429, timeout, or
    connection error): a throttle, which the caller retries. "" means the
    endpoint returned 400/404, the genuine end of the result set.
    """
    for n in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(req, timeout=15).read().decode("utf8", "ignore")
        except urllib.error.HTTPError as e:
            if e.code == 429:            # rate limited — back off and retry
                time.sleep(3 * (n + 1))
                continue
            if e.code in (400, 404):     # past the end of the result set
                return ""
            time.sleep(1 + n)
        except Exception:
            time.sleep(1 + n)
    return None


def parse(page_html):
    out = []
    for card in page_html.split("<li>")[1:]:
        def grab(pattern, group=1):
            m = re.search(pattern, card, re.S)
            if not m:
                return ""
            return html.unescape(re.sub("<[^>]*>", "", m.group(group))).strip()

        jid = grab(r'data-entity-urn="urn:li:jobPosting:(\d+)"') or grab(r"-(\d{10})\?")
        if not jid:
            continue
        out.append((
            jid,
            grab(r'class="sr-only">\s*(.*?)\s*</span>'),
            grab(r"hidden-nested-link[^>]*>\s*(.*?)\s*</a>"),
            grab(r'job-search-card__location">\s*(.*?)\s*</span>'),
            grab(r'datetime="([\d-]+)"'),
        ))
    return out


def sweep(keywords, location, window="r604800", remote=False, max_rows=None):
    """One full pagination attempt. Returns a dict of rows + integrity signals."""
    seen, rows = set(), []
    start, empty_streak, failed_pages = 0, 0, []
    consecutive_fail = 0
    short_pages = []          # pages with 0 < cards < PAGE that were NOT the tail
    cut_by_policy = False
    blocked = False
    pending_short = None      # a short page is only a drop if more full pages follow

    while start < SAFETY_CAP:
        if max_rows is not None and len(rows) >= max_rows:
            cut_by_policy = True
            break
        url = BASE.format(q=keywords, loc=location, tpr=window,
                          wt="&f_WT=2" if remote else "", start=start)
        page = fetch(url)

        if page is None:
            # A page we could not read is a hole. Record it, but a RUN of them
            # is a throttle, not scattered holes: bail this attempt so the
            # whole bucket can be retried after a cooldown rather than grinding
            # every page to the cap at ~90s each.
            failed_pages.append(start)
            consecutive_fail += 1
            if consecutive_fail >= HARD_BLOCK_STREAK:
                blocked = True
                break
            start += PAGE
            continue
        consecutive_fail = 0

        cards = parse(page)
        new = [c for c in cards if c[0] not in seen]
        for c in new:
            seen.add(c[0])
            rows.append(c)

        # Terminate on genuine exhaustion: no NEW ids, twice running. Checking
        # "no new ids" rather than "no cards" also catches the case where
        # LinkedIn loops back and re-serves earlier results forever.
        empty_streak = empty_streak + 1 if not new else 0
        if empty_streak >= EMPTY_STREAK_DONE:
            break

        # Per-page integrity: a full page has PAGE cards. A short page (fewer,
        # but still carrying new ids) is legitimate only as the last page
        # before exhaustion. If a full page follows it, it was a dropped or
        # partially-served page and the set is truncated. A short page is held
        # as `pending_short` and only promoted to a real drop once a later page
        # brings new ids.
        if new:
            if pending_short is not None:
                short_pages.append(pending_short)
                pending_short = None
            if len(cards) < PAGE:
                pending_short = start

        start += PAGE
        time.sleep(0.25)

    hit_cap = start >= SAFETY_CAP
    return {
        "rows": rows,
        "failed_pages": failed_pages,
        "hit_cap": hit_cap,
        "cut_by_policy": cut_by_policy,
        "blocked": blocked,
        "short_pages": short_pages,
    }


def clean(res):
    """A clean attempt: exhausted with no throttle, no holes, no dropped page."""
    return (not res["blocked"] and not res["failed_pages"]
            and not res["hit_cap"] and not res["short_pages"])


def sweep_with_retry(keywords, location, window, remote, max_rows,
                     retries=DEFAULT_RETRIES, cooldown=DEFAULT_COOLDOWN):
    """Run the bucket, retrying the whole thing on a throttle.

    Keeps the most complete attempt seen. Returns (result, attempts_used).
    """
    best = None
    for attempt in range(retries + 1):
        sys.stderr.write("[sweep] attempt %d of %d\n" % (attempt + 1, retries + 1))
        sys.stderr.flush()
        res = sweep(keywords, location, window, remote, max_rows)
        sys.stderr.write("[sweep] attempt %d: %d rows, blocked=%s, failed=%d, short=%d\n"
                         % (attempt + 1, len(res["rows"]), res["blocked"],
                            len(res["failed_pages"]), len(res["short_pages"])))
        sys.stderr.flush()

        if res["cut_by_policy"]:
            return res, attempt          # a deliberate stop is not retryable
        if best is None or len(res["rows"]) > len(best["rows"]):
            best = res
        if clean(res):
            return res, attempt
        if attempt < retries:
            sys.stderr.write("[sweep] incomplete; cooling down %ds then re-running the bucket\n"
                             % cooldown)
            sys.stderr.flush()
            time.sleep(cooldown)
    return best, retries


def sweep_union(keywords, location, window, remote, max_rows, passes,
                retries=DEFAULT_RETRIES, cooldown=DEFAULT_COOLDOWN):
    """Run the bucket `passes` times and union the rows by job id.

    The guest endpoint samples non-deterministically, so one pass drops a
    random ~quarter of the matching set. Unioning independent passes recovers
    it. Each pass still runs its own throttle-retry (sweep_with_retry) before
    contributing, so a throttle degrades coverage but never corrupts the union.

    Returns a result dict shaped like sweep(), plus union bookkeeping:
      rows           deduped union across all passes
      per_pass       row count of each individual pass
      volatile       number of ids that appeared in fewer than `passes` passes
      blocked/…      OR-ed integrity signals; the union is only "clean" if
                     every pass paginated cleanly to exhaustion.
    """
    by_id = {}
    seen_counts = {}
    per_pass = []
    agg = {"failed_pages": [], "hit_cap": False, "cut_by_policy": False,
           "blocked": False, "short_pages": []}
    for p in range(passes):
        sys.stderr.write("[union] pass %d of %d\n" % (p + 1, passes))
        sys.stderr.flush()
        res, _ = sweep_with_retry(keywords, location, window, remote, max_rows,
                                  retries, cooldown)
        per_pass.append(len(res["rows"]))
        for row in res["rows"]:
            if row[0] not in by_id:
                by_id[row[0]] = row
            seen_counts[row[0]] = seen_counts.get(row[0], 0) + 1
        # A union is only as clean as its passes: any pass that threw a signal
        # taints the union, so a caller can never read a throttled pass as if
        # it were complete coverage.
        for k in ("blocked", "hit_cap", "cut_by_policy"):
            agg[k] = agg[k] or res[k]
        agg["failed_pages"].extend(res["failed_pages"])
        agg["short_pages"].extend(res["short_pages"])

    rows = list(by_id.values())
    volatile = sum(1 for c in seen_counts.values() if c < passes)
    agg["rows"] = rows
    agg["per_pass"] = per_pass
    agg["volatile"] = volatile
    return agg


def main():
    # Windows defaults stdout to cp1252, which dies on the first non-Latin-1
    # character in a company name and kills the run mid-sweep (8/5/26). Progress
    # goes to stderr, so guard both streams.
    for stream in ("stdout", "stderr"):
        try:
            getattr(sys, stream).reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__)
        sys.exit(2)

    def opt(name, default):
        i = sys.argv.index(name) + 1 if name in sys.argv else None
        if i is None or i >= len(sys.argv):
            return default
        return sys.argv[i]

    window = opt("--window", "r604800")
    remote = "--remote" in sys.argv
    retries = int(opt("--retries", DEFAULT_RETRIES))
    cooldown = int(opt("--cooldown", DEFAULT_COOLDOWN))
    passes = int(opt("--passes", DEFAULT_PASSES))

    max_rows = None
    if "--max-rows" in sys.argv:
        raw = opt("--max-rows", None)
        max_rows = None if raw in (None, "0", "none", "off") else int(raw)

    if passes > 1:
        res = sweep_union(args[0], args[1], window, remote, max_rows, passes,
                          retries, cooldown)
        # Coverage note: how much the union recovered over the leanest single
        # pass, and how many roles were volatile (present in only some passes).
        thinnest = min(res["per_pass"]) if res["per_pass"] else 0
        recovered = len(res["rows"]) - thinnest
        coverage = ("%d passes, per-pass %s, union %d (+%d over the leanest "
                    "pass; %d roles were in only some passes)"
                    % (passes, "/".join(map(str, res["per_pass"])),
                       len(res["rows"]), recovered, res["volatile"]))
    else:
        res, _ = sweep_with_retry(args[0], args[1], window, remote, max_rows,
                                  retries, cooldown)
        coverage = "1 pass (no union; a single guest sample drops ~1/4 of roles)"

    rows = res["rows"]

    for r in sorted(rows, key=lambda x: (x[2].lower(), x[1].lower())):
        print(" ~ ".join(r))

    print("-" * 60)

    if res["cut_by_policy"]:
        print("STATUS: CUT AT %d (policy) — %d unique postings, stopped deliberately."
              % (max_rows, len(rows)))
        print("        NOT a coverage gap; the default is uncapped. %s." % coverage)
        return

    if not clean(res):
        problems = []
        if res["blocked"]:
            problems.append("THROTTLED — the guest endpoint blocked a pass even after "
                            "%d retries; rerun the bucket later" % retries)
        if res["failed_pages"]:
            problems.append("unreadable pages at start=" + ",".join(map(str, res["failed_pages"])))
        if res["short_pages"]:
            problems.append("dropped/short page (<%d cards) at start=%s"
                            % (PAGE, ",".join(map(str, res["short_pages"]))))
        if res["hit_cap"]:
            problems.append("hit the %d safety cap, more results exist" % SAFETY_CAP)
        print("STATUS: INCOMPLETE — %d unique postings. %s. %s"
              % (len(rows), coverage, "; ".join(problems)))
        print("        Report this as a coverage gap in the digest.")
        sys.exit(1)

    print("STATUS: COMPLETE — %d unique postings, every pass paginated to "
          "exhaustion (no throttle, no holes, no dropped page). %s." % (len(rows), coverage))


if __name__ == "__main__":
    main()
