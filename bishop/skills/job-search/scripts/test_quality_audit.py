# -*- coding: utf-8 -*-
"""Tests for quality_audit.py.  Bishop, by Adam Hilliard (MIT).

    python test_quality_audit.py

Each case builds a throwaway project folder that contains exactly one defect,
then asserts the matching check trips and that a clean folder trips nothing.
The audit exists to catch a broken recipe reporting success, so an audit that
silently stops checking is the same failure one level up.
"""

import datetime
import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.join(HERE, "quality_audit.py")

CLEAN_CYCLES = u"""
### 2026-08-04 · cycle 1
COVERAGE: linkedin COMPLETE 933 · lever 6 · icims 3
CANARY: icims PASS

### 2026-08-05 · cycle 2
COVERAGE: linkedin COMPLETE 901 · lever 7 · icims 4
CANARY: icims PASS

### 2026-08-06 · cycle 3
COVERAGE: linkedin COMPLETE 880 · lever 5 · icims 2
CANARY: icims PASS
"""

GATE_CYCLES = u"""
### 2026-08-04 · cycle 1
COVERAGE: linkedin COMPLETE 933 · lever 6 · icims 3
CANARY: icims PASS
EVENTS: 2 new · 0 expired
GATE: 2 assessed · 0 flagged

### 2026-08-05 · cycle 2
COVERAGE: linkedin COMPLETE 901 · lever 7 · icims 4
CANARY: icims PASS
EVENTS: 3 new · 1 expired
"""

RESOLVE_CYCLES = u"""
### 2026-08-04 · cycle 1
COVERAGE: linkedin COMPLETE 933 · lever 6 · icims 3
CANARY: icims PASS
EVENTS: 2 new · 0 expired
GATE: 2 assessed · 0 flagged
RESOLVE: 12 read · 10 live · 2 expired · 0 unverified · canary PASS

### 2026-08-05 · cycle 2
COVERAGE: linkedin COMPLETE 901 · lever 7 · icims 4
CANARY: icims PASS
EVENTS: 3 new · 1 expired
GATE: 3 assessed · 0 flagged
"""

RESOLVE_LINE = (u"RESOLVE: 12 read · 10 live · 2 expired · 0 unverified"
                u" · canary PASS\n")

METHODOLOGY = u"""# Methodology

### Queries

| Stem | Filter to | State |
|---|---|---|
| `"Operations Manager"` | mid | live |

```
"Operations Manager"
```
"""

DECISIONS = u"""# Decisions Log

## Open Trials

| Trial | Opened | Review due | Kill criteria | Status |
|---|---|---|---|---|
| A stem family | 2026-08-01 | 2099-01-01 | flood | open |

## T · Targets and Scope
"""


def dates(start, gaps, n):
    """n entry dates from start, stepping through gaps in days: (7,) is a
    weekly search, (3, 4) a Monday/Thursday one."""
    d = datetime.date(*(int(x) for x in start.split("-")))
    out = []
    for i in range(n):
        out.append(d.isoformat())
        d += datetime.timedelta(days=gaps[i % len(gaps)])
    return out


WEEKLY = (7,)
TWICE_WEEKLY = (3, 4)


def entries(days, coverage, canary=u"icims PASS"):
    """Search Notes entries, one per date. coverage and canary are one string
    for every entry, or a list with one per entry (None for no CANARY line)."""
    out = []
    for i, d in enumerate(days):
        cov = coverage[i] if isinstance(coverage, list) else coverage
        can = canary[i] if isinstance(canary, list) else canary
        out.append(u"\n### %s · cycle %d\nCOVERAGE: %s\n" % (d, i + 1, cov))
        if can:
            out.append(u"CANARY: %s\n" % can)
    return u"".join(out)


STEADY = u"linkedin COMPLETE 900 · lever 6 · icims 3"
DROPPED = u"linkedin COMPLETE 900 · lever 0 · icims 3"


def build(tmp, cycles=CLEAN_CYCLES, methodology=METHODOLOGY, decisions=DECISIONS,
          apply_link=u"https://boards.greenhouse.io/acme/jobs/1", files=None):
    def w(name, text):
        io.open(os.path.join(tmp, name), "w", encoding="utf-8").write(text)
    w("Reference_Profile.md", u"# Profile\n")
    w("Operating_Procedures.md", u"# Procedures\n")
    w("Methodology.md", methodology)
    w("Decisions_Log.md", decisions)
    w("Tracking_HR.md", u"# Tracking\n\n## ACTIVE/ROLLING\n\n| Score | Apply |\n"
                        u"|---|---|\n| 4/6 | %s |\n\n## Search Notes\n%s"
                        % (apply_link, cycles))
    for name, text in (files or {}).items():
        w(name, text)


def run(tmp, *extra):
    p = subprocess.run([sys.executable, AUDIT, "--project", tmp] + list(extra),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def case(name, expect_trip, absent=(), text=(), **kw):
    """expect_trip: the check that must trip, or None for a clean run. absent:
    checks that must NOT trip, where other checks may (the run need not be
    clean). text: substrings the output must contain."""
    tmp = tempfile.mkdtemp()
    try:
        extra = kw.pop("extra", ())
        build(tmp, **kw)
        code, out = run(tmp, *extra)
        tripped = [ln.split("]")[0].split()[-1] for ln in out.splitlines() if "[TRIP" in ln]
        for t in text:
            assert t in out, "%s: expected %r in the output\n%s" % (name, t, out)
        for cid in absent:
            assert cid not in tripped, ("%s: expected %s NOT to trip, got %s\n%s"
                                        % (name, cid, tripped, out))
        if expect_trip is None and not absent:
            assert code == 0, "%s: expected clean, got trips %s\n%s" % (name, tripped, out)
        elif expect_trip is not None:
            assert expect_trip in tripped, ("%s: expected %s to trip, got %s\n%s"
                                            % (name, expect_trip, tripped, out))
            assert code == 1, "%s: trips must exit 1" % name
        print("  ok  %-28s %s" % (name, expect_trip or (
            "no " + "/".join(absent) if absent else "clean")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("quality_audit self-test")

    case("clean project", None)

    case("member dark 3 cycles", "S1", cycles=CLEAN_CYCLES.replace(
        u"icims 3", u"icims 0").replace(u"icims 4", u"icims 0").replace(u"icims 2", u"icims 0"),
        apply_link=u"https://example.com/1")

    case("round-number count", "S2",
         cycles=CLEAN_CYCLES.replace(u"linkedin COMPLETE 880", u"getro 20/25000"))

    # S3-S7 measure their windows in days from the entry dates, because the
    # doc states them in weeks. Counting cycles made a twice-weekly search
    # trip in half the documented time. Each window gets a weekly case and a
    # twice-weekly one.

    # S3: above zero 4+ weeks, then exactly zero.
    case("S3 weekly, 4 weeks steady", "S3",
         cycles=entries(dates("2026-08-03", WEEKLY, 5), [STEADY] * 4 + [DROPPED]))
    case("S3 weekly, 3 weeks steady", None,
         cycles=entries(dates("2026-08-03", WEEKLY, 4), [STEADY] * 3 + [DROPPED]))
    case("S3 twice-weekly, 2 weeks", None,
         cycles=entries(dates("2026-08-03", TWICE_WEEKLY, 5), [STEADY] * 4 + [DROPPED]))
    case("S3 twice-weekly, 4 weeks", "S3",
         cycles=entries(dates("2026-08-03", TWICE_WEEKLY, 9), [STEADY] * 8 + [DROPPED]))

    # S3: a zero the same entry's canary vouched for is not a trend break.
    case("S3 zero vouched by canary", None,
         text=(u"vouched by a same-entry CANARY PASS: lever",),
         cycles=entries(dates("2026-08-03", WEEKLY, 5), [STEADY] * 4 + [DROPPED],
                        canary=[u"icims PASS"] * 4 + [u"icims PASS · lever PASS"]))

    # S4: unvouched nils rising two weeks running, week over week.
    nils = [u"linkedin COMPLETE 900 · lever 6 · icims 3 · ashby 4",
            u"linkedin COMPLETE 900 · lever 0 · icims 3 · ashby 4",
            u"linkedin COMPLETE 900 · lever 0 · icims 0 · ashby 4"]
    case("S4 weekly, rising 2 weeks", "S4",
         cycles=entries(dates("2026-08-03", WEEKLY, 3), nils, canary=None))
    case("S4 twice-weekly, one week", None,
         cycles=entries(dates("2026-08-03", TWICE_WEEKLY, 3), nils, canary=None))
    # A canary that failed or is still owed doesn't vouch for a zero; only PASS does.
    case("S4 failed canary doesn't vouch", "S4",
         cycles=entries(dates("2026-08-03", WEEKLY, 3), nils, canary=[None, u"lever FAIL", u"lever FAIL · icims OWED"]))

    # S5: canary debt is OWED or FAIL, and trips past 14 days by entry date.
    # Owed-then-passed is debt cleared, not debt.
    case("canary owed", "S5",
         cycles=entries(dates("2026-08-03", (7, 8), 3), STEADY,
                        canary=[u"icims OWED", None, None]))
    case("canary FAIL is debt", "S5",
         cycles=entries(dates("2026-08-03", (7, 8), 3), STEADY,
                        canary=[u"icims FAIL", u"icims FAIL", None]))
    case("canary owed 14 days", None,
         text=(u"icims OWED since 2026-08-03 (14 days)",),
         cycles=entries(dates("2026-08-03", WEEKLY, 3), STEADY,
                        canary=[u"icims OWED", None, None]))
    case("canary owed then passed", None,
         cycles=entries(dates("2026-08-03", WEEKLY, 4), STEADY,
                        canary=[u"icims OWED", None, u"icims PASS", None]))

    # S6: COMPLETE at zero 3+ weeks running. S1 also trips on these, which
    # is why the twice-weekly case asserts only that S6 stays quiet.
    at_zero = u"linkedin COMPLETE 900 · lever 6 · icims 0 COMPLETE"
    case("COMPLETE at zero", "S6", apply_link=u"https://example.com/1",
         cycles=entries(dates("2026-08-03", WEEKLY, 4), at_zero))
    case("COMPLETE at zero, 2 weeks", None, absent=("S6",),
         apply_link=u"https://example.com/1",
         cycles=entries(dates("2026-08-03", TWICE_WEEKLY, 5), at_zero))

    # S7: zero 4+ weeks with a passing canary for that member.
    live_empty = u"linkedin COMPLETE 900 · lever 6 · icims 0"
    case("S7 weekly, 4 weeks", "S7", apply_link=u"https://example.com/1",
         cycles=entries(dates("2026-08-03", WEEKLY, 5), live_empty))
    case("S7 twice-weekly, 2 weeks", None, absent=("S7",),
         apply_link=u"https://example.com/1",
         cycles=entries(dates("2026-08-03", TWICE_WEEKLY, 5), live_empty))

    case("role on a source that swept empty", "S8", cycles=CLEAN_CYCLES
         .replace(u"lever 6", u"greenhouse 0").replace(u"lever 7", u"greenhouse 0")
         .replace(u"lever 5", u"greenhouse 0"))

    case("stem documented, not in query", "E1", methodology=METHODOLOGY.replace(
        u'```\n"Operations Manager"\n```', u'```\n"Director of Operations"\n```'))

    case("trial with no review date", "E5", decisions=DECISIONS.replace(
        u"2099-01-01", u"after two cycles"))

    case("trial overdue", "E5", decisions=DECISIONS.replace(u"2099-01-01", u"2020-01-01"))

    # E7: cycle 2 added rows and reported no gate count, while cycle 1 did.
    # A gate that finds nothing and a gate that never ran write the same file.
    case("gate not reported on a cycle that added rows", "E7", cycles=GATE_CYCLES)

    # ...but a search that has never adopted the gate is blocked, not failed.
    case("gate never adopted", None, cycles=GATE_CYCLES.replace(
        u"GATE: 2 assessed · 0 flagged\n", u""))

    # E8: cycle 2 added rows and reported no resolve count. Same argument as
    # E7 one surface over: an unrun resolver and a clean one write the same
    # table, and the table is the thing the user clicks.
    case("resolver not reported on a cycle that added rows", "E8",
         cycles=RESOLVE_CYCLES)

    # A search that has never adopted the resolver is blocked, not failed.
    case("resolver never adopted", None,
         cycles=RESOLVE_CYCLES.replace(RESOLVE_LINE, u""))

    # An expiry behind a failed canary is a reachability problem wearing a
    # market event's clothes, so a reported-but-untrusted run still trips.
    case("resolver ran without a passing canary", "E8",
         cycles=RESOLVE_CYCLES.replace(
             u"GATE: 3 assessed · 0 flagged",
             u"GATE: 3 assessed · 0 flagged\n"
             u"RESOLVE: 9 read · 0 live · 0 expired · 9 unverified"
             u" · canary FAIL"))

    # E8 accepts `canary NONE` where nothing can be confirmed live yet: a
    # track's first logged cycle. Anywhere later it trips, and FAIL trips
    # even on the first cycle.
    both_resolved = RESOLVE_CYCLES.replace(
        u"GATE: 3 assessed · 0 flagged",
        u"GATE: 3 assessed · 0 flagged\n" + RESOLVE_LINE.strip())
    case("canary NONE on the first cycle", None,
         text=(u"canary NONE accepted on a first logged cycle",),
         cycles=both_resolved.replace(u"canary PASS", u"canary NONE", 1))
    case("canary NONE after the first cycle", "E8",
         cycles=both_resolved[::-1].replace(u"SSAP yranac", u"ENON yranac", 1)[::-1])
    case("canary FAIL on the first cycle", "E8",
         cycles=both_resolved.replace(u"canary PASS", u"canary FAIL", 1))

    # E4: one tracking file past the 50 KB split threshold trips on its own,
    # well inside the 200 KB total.
    case("tracking file past 50 KB", "E4",
         cycles=CLEAN_CYCLES + u"NOTE: " + u"x" * (51 * 1024) + u"\n")
    case("tracking file under 50 KB", None,
         cycles=CLEAN_CYCLES + u"NOTE: " + u"x" * (45 * 1024) + u"\n")

    # E6: an index with nothing to compare is blocked, never ok.
    case("index with no references", None, text=(u"[blkd E6 ]",),
         files={u"Index_HR.md": u"# Index\n", u"Archived_HR.md": u"# Archive\n"})
    case("index and archive agree", None, text=(u"[ ok  E6 ]",),
         files={u"Index_HR.md": u"- Acme, Ops Manager [#acme-ops-1]\n",
                u"Archived_HR.md": u'<a id="acme-ops-1"></a>\n### Acme\n'})

    # Two tracking files: each track is checked on its own, with its entries
    # sorted by date. Here Tracking_HR.md (which sorts first) has a
    # truncation signature on its latest entry, and Tracking_Ops.md was
    # written newest-first, with the signature on its newest entry. Read as
    # one concatenated log in file order, neither is "this cycle".
    hr = CLEAN_CYCLES.replace(u"linkedin COMPLETE 880", u"getro 20/25000")
    ops = (u"# Tracking\n\n## Search Notes\n"
           + entries([u"2026-08-20"], u"getro 20/25000 · lever 4")
           + entries([u"2026-08-05"], u"getro 412/10976 INCOMPLETE · lever 3"))
    case("two tracks, sorted per track", "S2", cycles=hr,
         files={u"Tracking_Ops.md": ops},
         text=(u"Tracking_HR.md: truncation signature",
               u"Tracking_Ops.md: truncation signature"))
    # ...and an older entry written last is not mistaken for the latest.
    ops_clean = (u"# Tracking\n\n## Search Notes\n"
                 + entries([u"2026-08-20"], u"getro 412/10976 INCOMPLETE · lever 4")
                 + entries([u"2026-08-05"], u"getro 20/25000 · lever 3"))
    case("two tracks, stale entry last", None, files={u"Tracking_Ops.md": ops_clean})

    print("all cases passed")


if __name__ == "__main__":
    main()
