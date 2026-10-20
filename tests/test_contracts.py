# -*- coding: utf-8 -*-
"""Check every contract in CONTRACTS.md against the made-up test candidate (tests/candidate/): each
part one module reads from another must still be there, in the shape the reader expects. Run by
tests/run_all.py; prints "ok <check>" or "FAIL <check>  (why)" per line and exits 1 on any failure.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, "candidate")
KNOWN = {"profile": 1, "procedures": 1, "tracking": 1, "employer-index": 1}
failures = 0


def report(name, ok, why=""):
    global failures
    print(("  ok   %s" if ok else "  FAIL %s  (" + why + ")") % name)
    failures += 0 if ok else 1


def read(name):
    p = os.path.join(C, name)
    return open(p, encoding="utf-8").read() if os.path.isfile(p) else None


def version_ok(name, text, kind):
    """A first-line format comment, or none (version 1). Any version the readers don't know fails."""
    m = re.match(r"\s*<!--\s*bishop-format:\s*([a-z-]+)\s+(\d+)\s*-->", text)
    if not m:
        report("%s format version (none means 1)" % name, True)
        return
    report("%s format version" % name, m.group(1) == kind and int(m.group(2)) == KNOWN[kind],
           "says %s %s, readers know %s %d" % (m.group(1), m.group(2), kind, KNOWN[kind]))


def section(text, title):
    """The body under a heading named `title` (any level), up to the next heading of the same or higher level."""
    m = re.search(r"^(#+)\s*%s\b[^\n]*\n" % re.escape(title), text, re.M | re.I)
    if not m:
        return None
    level = len(m.group(1))
    rest = text[m.end():]
    end = re.search(r"^#{1,%d}\s" % level, rest, re.M)
    return rest[: end.start()] if end else rest


def tables(text):
    """Every markdown table as (header cells, rows)."""
    out, lines = [], text.splitlines()
    i = 0
    while i < len(lines) - 1:
        if lines[i].strip().startswith("|") and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            head = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows, j = [], i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            out.append((head, rows))
            i = j
        else:
            i += 1
    return out


# ---- 1. The profile ----
profile = read("Reference_Profile.md")
report("profile exists", profile is not None, "tests/candidate/Reference_Profile.md is missing")
if profile:
    version_ok("profile", profile, "profile")
    name = section(profile, "Bot Name")
    has_name = bool(name and name.strip()) or bool(re.search(r"^#\s+.+?\s+Reference Profile\b", profile, re.M))
    report("profile: the search's name (dashboard, interviews)", has_name, "no Bot Name section and no title line")
    for title, readers in (("Customization", "dashboard"), ("Motivator Buckets", "dashboard"), ("Career Level", "interviews"), ("Current Role", "interviews"),
                           ("Full Career History", "interviews"), ("Target Roles", "interviews")):
        body = section(profile, title)
        report("profile: %s (%s)" % (title, readers), bool(body and body.strip()), "section missing or empty")
    hist = section(profile, "Full Career History") or ""
    t = tables(hist)
    cols = [c.lower() for c in t[0][0]] if t else []
    report("profile: career history is a table of period, role, company, highlights (interviews)",
           bool(t) and all(any(k in c for c in cols) for k in ("period", "role", "company", "highlight")),
           "columns: " + ", ".join(cols) if cols else "no table")

# ---- 2. The procedures ----
proc = read("Operating_Procedures.md")
report("procedures exist", proc is not None, "tests/candidate/Operating_Procedures.md is missing")
if proc:
    version_ok("procedures", proc, "procedures")
    report("procedures: the tracking-table format (dashboard)", bool(re.search(r"table", proc, re.I)) and bool(tables(proc)),
           "no table format described")

# ---- 3. The tracking files ----
tracks = sorted(f for f in os.listdir(C) if re.match(r"Tracking_.+\.md$", f)) if os.path.isdir(C) else []
report("at least one tracking file", bool(tracks), "no Tracking_*.md")
for f in tracks:
    text = read(f)
    version_ok(f, text, "tracking")
    live = [t for t in tables(text) if len(t[0]) >= 5 and t[1]]
    report("%s: a live table with roles (dashboard)" % f, bool(live), "no table with at least five columns and a row")
    if live:
        head = " | ".join(live[0][0]).lower()
        for k, why in (("score", "score"), ("company", "company"), ("title", "title"), ("link", "apply link")):
            report("%s: column for %s (dashboard)" % (f, why), k in head or (k == "link" and "apply" in head), "header: " + head)
        report("%s: apply links are links (dashboard, interviews)" % f, bool(re.search(r"https?://", text)), "no link in the file")
        bad = [r for r in live[0][1] if not re.search(r"\*\*Stage: (open|applied \d{4}-\d{2}-\d{2}|interviewing \d{4}-\d{2}-\d{2})\*\*", " | ".join(r))]
        no_next = [r for r in live[0][1] if r not in bad and "next:" not in " | ".join(r)]
        report("%s: every live row names its next step (dashboard)" % f, not no_next, "%d row(s) without next:" % len(no_next))
        report("%s: every live row opens Key Context with its stage (dashboard, interviews)" % f, not bad,
               "%d row(s) without a stage token" % len(bad))
    report("%s: search notes block (dashboard)" % f, bool(re.search(r"search notes", text, re.I)), "no search notes")

# ---- 4. The employer index ----
idx = read("Employer_Index.md")
if idx is None:
    report("employer index (outreach, once built)", True)
else:
    version_ok("employer index", idx, "employer-index")
    report("employer index: an employer table (outreach)", bool(tables(idx)), "no table")

sys.exit(1 if failures else 0)
