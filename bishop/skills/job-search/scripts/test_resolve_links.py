# -*- coding: utf-8 -*-
"""Tests for resolve_links.py.  Bishop, by Adam Hilliard (MIT).

    python test_resolve_links.py

Every case runs against a stub fetcher. Nothing here touches the network, so
the suite is deterministic and safe to run in CI.

Most of these assert a NEGATIVE: that a given failure does NOT produce
"expired." That is the whole point of the file under test. A resolver that
marks unreachable postings dead is worse than no resolver at all, because it
silently empties a table and looks like it worked.
"""

import io
import sys

import resolve_links as R

FAILURES = []


def check(name, got, want):
    if got == want:
        print("  ok    %s" % name)
    else:
        print("  FAIL  %s\n          got  %r\n          want %r" % (name, got, want))
        FAILURES.append(name)


def stub(table):
    """table: url -> (status, final_url, body) or an Exception name."""
    def fetcher(url):
        v = table.get(url)
        if v is None:
            return None, url, "", "KeyError"
        if isinstance(v, str):
            return None, url, "", v
        status, final, body = v
        return status, final, body, None
    return fetcher


PAGE = "<html><body><p>" + ("a real job description. " * 60) + "</p></body></html>"
SHELL = "<html><body><div id='root'></div></body></html>"
CLOSED = "<html><body><h1>This job is no longer accepting applications.</h1>" \
         + ("filler " * 100) + "</body></html>"
TERSE_GONE = "<html><body><h1>Job not found</h1>" + ("filler " * 100) + "</body></html>"

LIVE_URL = "https://boards.example.com/jobs/1"


def test_classification():
    print("classification")
    t = {
        LIVE_URL: (200, LIVE_URL, PAGE),
        "https://b.example.com/jobs/404": (404, "https://b.example.com/jobs/404", ""),
        "https://b.example.com/api/jobs/9.json": (404, "https://b.example.com/api/jobs/9.json", ""),
        "https://b.example.com/jobs/gone": (200, "https://b.example.com/search?src=expired", PAGE),
        "https://b.example.com/jobs/closed": (200, "https://b.example.com/jobs/closed", CLOSED),
        "https://b.example.com/jobs/js": (200, "https://b.example.com/jobs/js", SHELL),
        "https://b.example.com/jobs/403": (403, "https://b.example.com/jobs/403", ""),
        "https://b.example.com/jobs/timeout": "timeout",
    }
    f = stub(t)
    check("a rendering page is live", R.classify(LIVE_URL, f)[0], R.LIVE)
    check("404 on the requisition page is expired",
          R.classify("https://b.example.com/jobs/404", f)[0], R.EXPIRED)
    check("404 from an API path is NOT expired",
          R.classify("https://b.example.com/api/jobs/9.json", f)[0], R.UNVERIFIED)
    check("an expiry marker in the final URL is expired",
          R.classify("https://b.example.com/jobs/gone", f)[0], R.EXPIRED)
    check("a closure banner is expired",
          R.classify("https://b.example.com/jobs/closed", f)[0], R.EXPIRED)
    check("a JS-only shell is NOT expired",
          R.classify("https://b.example.com/jobs/js", f)[0], R.UNVERIFIED)
    check("a 403 block is NOT expired",
          R.classify("https://b.example.com/jobs/403", f)[0], R.UNVERIFIED)
    check("a timeout is NOT expired",
          R.classify("https://b.example.com/jobs/timeout", f)[0], R.UNVERIFIED)


def test_real_world_markers():
    """The markers boards actually send, not the ones the list already had.

    Both of these shipped broken through 1.6.0-1.6.2. The URL marker is the
    important one: it belongs to the largest board any search will hit, so the
    single most common expiry signal in the wild resolved `live`.
    """
    print("markers boards actually send")

    req = "https://www.example-board.com/jobs/view/4443209325/"
    redirected = ("https://www.example-board.com/jobs/search?"
                  "trk=expired_jd_redirect&origin=JOB_SEEKER_HOME")
    f = stub({req: (200, redirected, PAGE)})
    state, why = R.classify(req, f)
    check("an abbreviated URL marker (expired_jd) is expired", state, R.EXPIRED)
    check("the evidence names the marker", "expired_jd" in why, True)

    terse = "https://b.example.com/jobs/terse"
    f = stub({terse: (200, terse, TERSE_GONE)})
    check("a page saying only 'Job not found' is expired",
          R.classify(terse, f)[0], R.EXPIRED)

    # The guard the two additions must not weaken: neither new pattern may
    # fire on a page that is simply describing a job.
    f = stub({LIVE_URL: (200, LIVE_URL, PAGE)})
    check("a live posting still resolves live", R.classify(LIVE_URL, f)[0], R.LIVE)


def run(rows, canary, table):
    buf = io.StringIO()
    counts = R.run(rows, canary=canary, fetcher=stub(table), out=buf)
    return counts, buf.getvalue()


def test_canary_gate():
    print("the canary gate")
    dead = "https://b.example.com/jobs/404"
    rows = [(dead, "Acme - Analyst")]

    # Canary passes: a genuine expiry is reported.
    counts, out = run(rows, LIVE_URL, {
        LIVE_URL: (200, LIVE_URL, PAGE),
        dead: (404, dead, ""),
    })
    check("canary passing lets an expiry through", counts[R.EXPIRED], 1)
    check("canary pass is announced", "CANARY: PASS" in out, True)
    check("a clean run reports COMPLETE", "STATUS: COMPLETE" in out, True)

    # Canary fails: the SAME dead row must not be called expired.
    counts, out = run(rows, LIVE_URL, {
        LIVE_URL: "timeout",
        dead: (404, dead, ""),
    })
    check("canary failing suppresses every expiry", counts[R.EXPIRED], 0)
    check("the row downgrades to unverified", counts[R.UNVERIFIED], 1)
    check("canary failure is announced", "CANARY: FAIL" in out, True)
    check("a canary-less run is INCOMPLETE", "STATUS: INCOMPLETE" in out, True)

    # No canary at all: same protection.
    counts, out = run(rows, None, {dead: (404, dead, "")})
    check("no canary means no expiry", counts[R.EXPIRED], 0)
    check("absent canary is announced", "CANARY: NONE" in out, True)


def test_count_line():
    print("the COUNT line behind the Search Notes RESOLVE line")
    table = {
        LIVE_URL: (200, LIVE_URL, PAGE),
        "https://b.example.com/a": (200, "https://b.example.com/a", PAGE),
        "https://b.example.com/b": (404, "https://b.example.com/b", ""),
        "https://b.example.com/c": "timeout",
    }
    rows = [(u, "") for u in
            ("https://b.example.com/a", "https://b.example.com/b",
             "https://b.example.com/c")]
    counts, out = run(rows, LIVE_URL, table)
    check("COUNT line shape",
          "COUNT: resolve read=3 live=1 expired=1 unverified=1" in out, True)
    check("counts sum to rows read", sum(counts.values()), 3)


def test_help_names_the_printed_canary_state():
    print("help text and output agree on the no-canary state")
    import os
    import subprocess
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "resolve_links.py")
    p = subprocess.run([sys.executable, script, "--help"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    help_text = " ".join((p.stdout or "").split())
    check("help names CANARY: NONE", "CANARY: NONE" in help_text, True)
    check("help no longer says NO-CANARY", "NO-CANARY" in help_text, False)
    _, out = run([("https://b.example.com/a", "")], None,
                 {"https://b.example.com/a": (200, "https://b.example.com/a", PAGE)})
    check("output prints the same state", "CANARY: NONE" in out, True)


if __name__ == "__main__":
    test_classification()
    test_real_world_markers()
    test_canary_gate()
    test_count_line()
    test_help_names_the_printed_canary_state()
    print()
    if FAILURES:
        print("%d FAILED: %s" % (len(FAILURES), ", ".join(FAILURES)))
        sys.exit(1)
    print("all resolve_links tests passed")
