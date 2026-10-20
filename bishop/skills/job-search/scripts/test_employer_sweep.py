# -*- coding: utf-8 -*-
"""Tests for employer_sweep.py.  Bishop, by Adam Hilliard (MIT).

    python test_employer_sweep.py

Every case runs against a stub pull(). Nothing here touches the network.

The per-board count lines exist because a total hides a board at zero, and a
board at zero while its peers return rows is a wrong slug. These cases assert
that every board gets a line, zeros included, and that the COVERAGE fragment
keeps the Search Notes shape the weekly audit parses.
"""

import contextlib
import io
import re
import sys

import employer_sweep as E

FAILURES = []


def check(name, got, want):
    if got == want:
        print("  ok    %s" % name)
    else:
        print("  FAIL  %s\n          got  %r\n          want %r" % (name, got, want))
        FAILURES.append(name)


ROW = ("Operations Manager", "Austin, TX", "")

BOARDS = {
    "acme": [ROW] * 3,
    "beta": [],                                  # read fine, nothing posted
    "acme.wd5.myworkdayjobs.com / acme / ACMEUS": [ROW, ROW],
}


def stub_pull(platform, slug):
    if slug == "gone":
        raise IOError("HTTP Error 404")
    if slug == "huge":
        raise E.PartialRead("1000 of 4000 postings read", [ROW] * 1000)
    return BOARDS[slug]


def run_sweep(board):
    """Run sweep() over board with the network and the sleeps stubbed out.
    Returns (failed, results, printed output)."""
    real_pull, real_sleep = E.pull, E.time.sleep
    E.pull, E.time.sleep = stub_pull, lambda s: None
    buf, results = io.StringIO(), []
    try:
        with contextlib.redirect_stdout(buf):
            failed = E.sweep("SET", board, re.compile("manager", re.I),
                             re.compile("operations", re.I), None, None, 0,
                             "all", results)
    finally:
        E.pull, E.time.sleep = real_pull, real_sleep
    return failed, results, buf.getvalue()


def test_per_board_lines():
    print("one count line per board, zeros included")
    board = [("Acme", "greenhouse", "acme"), ("Beta", "lever", "beta"),
             ("Acme WD", "workday", "acme.wd5.myworkdayjobs.com / acme / ACMEUS")]
    failed, results, out = run_sweep(board)
    lines = out.splitlines()
    check("acme count line", "  acme 3" in lines, True)
    check("zero board still gets a line", "  beta 0" in lines, True)
    check("multi-part slug is one token",
          "  acme.wd5.myworkdayjobs.com 2" in lines, True)
    check("total line kept", "  scanned 5 postings across 3 boards" in lines, True)
    check("nothing failed", failed, [])
    check("COVERAGE fragment, all read",
          E.coverage_line(results),
          u"employers 3/3 COMPLETE · acme 3 · beta 0"
          u" · acme.wd5.myworkdayjobs.com 2")


def test_gaps_are_not_zeros():
    print("an unreadable or partial board is a gap, never a zero")
    board = [("Acme", "greenhouse", "acme"), ("Gone", "lever", "gone"),
             ("Huge", "smartrecruiters", "huge")]
    failed, results, out = run_sweep(board)
    lines = out.splitlines()
    check("failed board line", "  gone FAILED" in lines, True)
    check("partial board line", "  huge 1000 INCOMPLETE" in lines, True)
    check("both on the STATUS list", len(failed), 2)
    frag = E.coverage_line(results)
    check("COVERAGE fragment, gaps named", frag,
          u"employers 1/3 INCOMPLETE · acme 3 · gone FAILED"
          u" · huge 1000 INCOMPLETE")


def test_fragment_parses_in_the_audit():
    print("the fragment reads back through the audit's parser")
    import quality_audit as Q
    frag = E.coverage_line([("acme", 3, "ok"), ("beta", 0, "ok"),
                            ("acme", 3, "ok")])
    check("a board in two sets is reported once", frag,
          u"employers 2/2 COMPLETE · acme 3 · beta 0")
    cycles, _ = Q.parse_cycles(u"### 2026-08-03 · cycle 1\nCOVERAGE: %s\n" % frag)
    got = [(m["name"], m["got"], m["claimed"], m["status"])
           for m in cycles[0]["coverage"]]
    check("members parse", got,
          [("employers", 2, 2, "COMPLETE"), ("acme", 3, None, None),
           ("beta", 0, None, None)])


if __name__ == "__main__":
    test_per_board_lines()
    test_gaps_are_not_zeros()
    test_fragment_parses_in_the_audit()
    print()
    if FAILURES:
        print("%d FAILED: %s" % (len(FAILURES), ", ".join(FAILURES)))
        sys.exit(1)
    print("all employer_sweep tests passed")
