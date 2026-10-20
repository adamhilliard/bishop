# -*- coding: utf-8 -*-
"""Apply-link resolver.  Bishop, by Adam Hilliard (MIT).

Why this file exists: freshness re-verification only ever protected rows
already in the table, so a FIRST cycle protected nothing. Two independent
testers reported the same thing, from different searches and different career
levels: a first digest whose top-ranked roles and below-the-cap links opened to
"page not found." Nothing errored. Nothing had checked.

This runs BEFORE research and scoring, so a dead role costs one request instead
of a research pass and a full rubric scoring.

THE ONE RULE THIS FILE EXISTS TO ENFORCE: a failed check is never an expiry.

  live        the requisition page renders
  expired     positive evidence of closure, and only from the three sources
              enumerated in EXPIRY EVIDENCE below
  unverified  the check could not run: timeout, block, JS-only shell,
              unresolvable host, anything ambiguous

Absence from a board is not expiry, and a 404 from an ATS's own per-requisition
API is not expiry either: one board's JSON omitted a requisition entirely and
its per-requisition endpoint reported the document missing, while the rendered
page served HTTP 200 with the full description, unchanged title, and unchanged
reporting line. Only the rendered page settles it.

THE CANARY IS NOT OPTIONAL. A control URL known to be live is resolved before
anything is classified. If it fails, the whole run downgrades to unverified and
NOTHING is marked expired. Without that, one proxy, rate-limit, or network blip
marks an entire table dead in a single cycle, silently and plausibly.

Usage:
    python resolve_links.py --urls-file rows.txt --canary https://known/live/req
    python resolve_links.py --urls-file rows.txt

Input is one URL per line, optionally followed by a tab and a label echoed
back. Output is one line per row, then CANARY, COUNT, and STATUS. The COUNT
and CANARY lines supply the numbers for the cycle's Search Notes RESOLVE line,
and that RESOLVE line is what the weekly audit reads (check E8); keep its shape.
"""

import argparse
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")

TIMEOUT = 20
PER_HOST_DELAY = 0.6          # polite, and keeps us off rate limiters
SAFETY_CAP = 400              # rows per invocation, then stop and SAY SO
BODY_CAP = 200000             # bytes of page read; we need markers, not content

# ---------------------------------------------------------------------------
# EXPIRY EVIDENCE: the ONLY three things that may produce "expired".
# Adding a fourth is a decision, not a tweak. Read the module docstring first.
# ---------------------------------------------------------------------------

# 1. An expiry marker in the final URL after redirects. Cheapest and most
#    definitive: boards redirect a dead posting to a search page and name the
#    reason in a tracking parameter.
#
#    THE ABBREVIATED FORMS MATTER AS MUCH AS THE SPELLED-OUT ONES. The largest
#    board's marker is `trk=expired_jd_redirect`, and `expired_jd` matches none
#    of the `expired_job` spellings below. One word apart, and the single most
#    common expiry signal any search will meet came back `live` for three
#    releases. Found on a port, by a test written against what a board actually
#    sends rather than against what the list already had.
#
#    Match on the stem. A guess at the whole parameter name is how this broke.
URL_EXPIRY_MARKERS = (
    "expired_jd_redirect", "expired_jd", "expired-jd",
    "jobnotfound", "job-not-found", "job_not_found",
    "expiredjob", "expired-job", "expired_job",
    "positionfilled", "position-filled",
    "nolongeravailable", "no-longer-available",
    "reason=expired", "status=expired", "src=expired",
)

# 2. A closure banner on the rendered requisition page.
PAGE_EXPIRY_PATTERNS = (
    r"no longer (?:accepting|available|active|open|posted)",
    r"this (?:job|position|posting|requisition|opening) (?:is|has been) "
    r"(?:closed|filled|expired|removed)",
    r"(?:job|position|posting) (?:has expired|is no longer)",
    r"applications? (?:are )?(?:now )?closed",
    r"we are no longer accepting applications",
    r"this posting has been filled",
    r"job not found",          # one major ATS says exactly this and no more
)

# 3. A hard gone-status on the rendered requisition page itself.
HARD_GONE = (404, 410)

# A shell with no body text is a JS-only render, NOT an expiry.
JS_ONLY_MIN_TEXT = 400        # chars of visible text below which we abstain

LIVE, EXPIRED, UNVERIFIED = "live", "expired", "unverified"


def visible_text(html):
    """Crude, deliberately. We need enough to spot a banner, not to parse."""
    html = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", html)).strip()


def fetch(url, opener=None):
    """Return (status, final_url, body, error). Never raises."""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read(BODY_CAP).decode("utf-8", "replace")
            return r.getcode(), r.geturl(), body, None
    except urllib.error.HTTPError as e:
        try:
            body = e.read(BODY_CAP).decode("utf-8", "replace")
        except Exception:
            body = ""
        return e.code, getattr(e, "url", url) or url, body, None
    except Exception as e:                      # timeout, DNS, TLS, reset
        return None, url, "", type(e).__name__


def classify(url, fetcher=fetch):
    """-> (state, evidence). The only place `expired` can be produced."""
    status, final, body, err = fetcher(url)

    if status is None:
        return UNVERIFIED, "could not reach (%s)" % err

    # Evidence 1: expiry named in the final URL. Checked first; it is
    # definitive and does not depend on reading the page.
    low = (final or "").lower().replace("%2d", "-")
    for marker in URL_EXPIRY_MARKERS:
        if marker in low:
            return EXPIRED, "redirected to an expiry URL (%s)" % marker

    if status in HARD_GONE:
        # Evidence 3, but only for a rendered page, never an API endpoint.
        path = urllib.parse.urlparse(url).path
        if re.search(r"/api/|\.json$", path, re.I):
            return UNVERIFIED, ("HTTP %d from an API path; only the rendered "
                                "page settles expiry" % status)
        return EXPIRED, "HTTP %d on the requisition page" % status

    if status >= 400:
        return UNVERIFIED, ("HTTP %d (blocked or erroring, not evidence of "
                            "closure)" % status)

    text = visible_text(body)
    if len(text) < JS_ONLY_MIN_TEXT:
        return UNVERIFIED, "page rendered no readable text (JS-only shell)"

    # Evidence 2: a closure banner on a page that did render.
    head = text[:6000].lower()
    for pat in PAGE_EXPIRY_PATTERNS:
        if re.search(pat, head):
            return EXPIRED, "closure notice on the page"

    return LIVE, "renders"


def read_rows(path):
    src = sys.stdin if path in (None, "-") else open(path, encoding="utf-8")
    rows = []
    for line in src:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        url, _, label = line.partition("\t")
        rows.append((url.strip(), label.strip()))
    if src is not sys.stdin:
        src.close()
    return rows


def run(rows, canary=None, fetcher=fetch, out=None):
    """Shared by main() and the tests. Returns the counts dict."""
    emit = (out or sys.stdout).write

    truncated = len(rows) > SAFETY_CAP
    rows = rows[:SAFETY_CAP]

    # ---- The canary, before anything is classified. ----------------------
    trust_expiry = False
    if canary:
        state, why = classify(canary, fetcher)
        if state == LIVE:
            trust_expiry = True
            emit("CANARY: PASS - control requisition resolved live\n")
        else:
            emit("CANARY: FAIL - control requisition came back %s (%s). "
                 "Reachability is the problem, not the postings. NOTHING is "
                 "marked expired this run.\n" % (state, why))
    else:
        emit("CANARY: NONE - no control URL given, so no row can be marked "
             "expired. Pass --canary to enable expiry.\n")

    counts = {LIVE: 0, EXPIRED: 0, UNVERIFIED: 0}
    last_host = None
    for url, label in rows:
        host = urllib.parse.urlparse(url).netloc
        if host == last_host and fetcher is fetch:
            time.sleep(PER_HOST_DELAY)
        last_host = host

        state, why = classify(url, fetcher)
        # The canary gate. An expiry claim without a passing canary is
        # downgraded, never printed.
        if state == EXPIRED and not trust_expiry:
            state, why = UNVERIFIED, "expiry not trusted: %s" % why
        counts[state] += 1
        emit("  %-10s | %-46s | %s\n" % (state, (label or url)[:46], why))

    emit("-" * 60 + "\n")
    emit("COUNT: resolve read=%d live=%d expired=%d unverified=%d\n"
         % (sum(counts.values()), counts[LIVE], counts[EXPIRED],
            counts[UNVERIFIED]))
    if truncated:
        emit("STATUS: INCOMPLETE - input exceeded the %d-row safety cap. "
             "Report this as a coverage gap.\n" % SAFETY_CAP)
    elif not trust_expiry:
        emit("STATUS: INCOMPLETE - ran without a passing canary, so every row "
             "is at best unverified. Report this as a coverage gap.\n")
    else:
        emit("STATUS: COMPLETE - every row resolved against a passing "
             "canary.\n")
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls-file", default="-",
                    help="one URL per line, optional tab-separated label")
    ap.add_argument("--canary",
                    help="a URL known to be live. Without one, nothing is "
                         "marked expired and the run reports CANARY: NONE.")
    args = ap.parse_args()

    rows = read_rows(args.urls_file)
    if not rows:
        print("STATUS: UNREADABLE - no URLs on input")
        return 0
    run(rows, args.canary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
