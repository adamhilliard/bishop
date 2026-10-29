# -*- coding: utf-8 -*-
"""Check the outreach builder (bishop/skills/outreach/scripts/build_page.py) against the made-up test
candidate and against broken inputs. Run by tests/run_all.py; prints "ok <check>" or
"FAIL <check>  (why)" per line and exits 1 on any failure.

    python tests/test_outreach_build.py [--keep <folder>]

--keep builds the test candidate's page into <folder>/Bishop and leaves it there (run_all.py runs the
browser flows on it).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
CANDIDATE = os.path.join(HERE, "candidate")
EXPORT = os.path.join(HERE, "outreach", "export")
BUILDER = os.path.join(ROOT, "bishop", "skills", "outreach", "scripts", "build_page.py")
DEFAULTS = os.path.join(ROOT, "bishop", "skills", "outreach", "assets", "segments.default.json")
failures = 0


def report(name, ok, why=""):
    global failures
    print(("  ok   %s" if ok else "  FAIL %s  (" + why + ")") % name)
    failures += 0 if ok else 1


def run(folder, *extra):
    p = subprocess.run([sys.executable, BUILDER, folder] + list(extra), capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def page_config(folder):
    html = open(os.path.join(folder, "Outreach", "outreach.html"), encoding="utf-8").read()
    m = re.search(r'<script id="outreach-config" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(m.group(1)), html


def candidate_copy(work, name="Bishop"):
    dst = os.path.join(work, name)
    shutil.copytree(CANDIDATE, dst, ignore=shutil.ignore_patterns("Interview_Prep"))
    return dst


def write_segments(folder, groups):
    os.makedirs(os.path.join(folder, "Outreach"), exist_ok=True)
    with open(os.path.join(folder, "Outreach", "segments.json"), "w", encoding="utf-8") as f:
        json.dump({"format": "bishop.outreach.segments", "version": 1, "groups": groups}, f)


def candidate_build(work):
    folder = candidate_copy(work)
    code, out = run(folder, "--check")
    report("the test candidate's segments pass --check", code == 0 and " 0 errors" in out, out.strip().splitlines()[-1] if out.strip() else "no output")
    code, out = run(folder)
    report("the page builds from the test candidate", code == 0 and os.path.isfile(os.path.join(folder, "Outreach", "outreach.html")), out.strip())
    if code != 0:
        return folder
    cfg, html = page_config(folder)
    report("the settings block is filled in", "__CONFIG__" not in html and cfg.get("format") == "bishop.outreach.config" and cfg.get("version") == 1)
    report("name comes from the profile's Bot Name", cfg.get("name") == "Wall-E", repr(cfg.get("name")))
    report("accent comes from the profile's Customization", cfg.get("accent") == "#4F6D9F", repr(cfg.get("accent")))
    report("warm window comes from settings.json", cfg.get("warmWindow") == "3y", repr(cfg.get("warmWindow")))
    report("past employers come from the career history", cfg.get("pastEmployers") == ["Acme Robotics", "Globex Field Services"], repr(cfg.get("pastEmployers")))
    want = {"Soylent Systems", "Hooli", "Stark Industrial Services", "Globex Field Services", "Initech", "Umbrella Logistics", "Wayne Automation"}
    got = set(cfg.get("searchCompanies") or [])
    report("search companies: the live tables plus the employer index", got == want, "got %s" % sorted(got))
    report("a company only in Not Interested isn't in the search", "Vandelay Industries" not in got)
    keys = [g["key"] for g in cfg["groups"]]
    report("groups keep the user's order", keys == ["warm", "mentors", "search", "recruiters", "exec", "robotics", "finance", "founders", "globex-years"], repr(keys))
    report("a dropped default isn't in the list", not any(g.get("default") == "hr" for g in cfg["groups"]))
    mentors = next(g for g in cfg["groups"] if g["key"] == "mentors")
    names = (mentors.get("match") or {}).get("names")
    report("a names file is read into the page's names list", names == ["Dana Whitfield", "Diego Nakamura", "Fiona Hughes", "Yara Ellison"], repr(names))
    report("the page never carries a names file reference", "namesFile" not in json.dumps(cfg))
    report("no em dash in the built page", "\u2014" not in html)
    return folder


def defaults_and_no_search(work):
    folder = os.path.join(work, "Empty")
    os.makedirs(folder)
    code, out = run(folder)
    ok = code == 0
    report("builds with no profile, no search and no Outreach files", ok, out.strip())
    if not ok:
        return
    cfg, _ = page_config(folder)
    want = [g["key"] for g in json.load(open(DEFAULTS, encoding="utf-8"))["groups"]]
    report("no segments.json: the five defaults", [g["key"] for g in cfg["groups"]] == want == ["warm", "recruiters", "hr", "exec", "founders"], repr([g["key"] for g in cfg["groups"]]))
    labels = [g["label"] for g in cfg["groups"]]
    report("default labels", labels == ["Warm", "Recruiters", "HR / People", "Executives", "Entrepreneurs"], repr(labels))
    report("no profile: the name falls back to Bishop and the accent to the setup default",
           cfg["name"] == "Bishop" and cfg["accent"] == "#4F6D9F", "%s %s" % (cfg["name"], cfg["accent"]))
    report("no settings.json: warm window any", cfg["warmWindow"] == "any")
    report("no search: empty company lists", cfg["pastEmployers"] == [] and cfg["searchCompanies"] == [])


def broken(work):
    base = candidate_copy(work, "Broken")
    ok_group = {"key": "warm", "label": "Warm", "rule": "Anyone you've exchanged messages with.", "default": "warm"}
    cases = [
        ("an unknown default", [{"key": "pals", "label": "Pals", "rule": "x", "default": "friends"}], '"friends" isn\'t a default group'),
        ("an unknown match type", [{"key": "pals", "label": "Pals", "rule": "x", "match": {"schools": ["Ridgeview"]}}], '"schools" isn\'t a match type'),
        ("a duplicate key", [ok_group, dict(ok_group, label="Warm Again", default="recruiters")], 'already uses the key "warm"'),
        ("a default listed twice", [ok_group, dict(ok_group, key="warm2", label="Warm Two")], "each default appears once"),
        ("names written into segments.json", [{"key": "pals", "label": "Pals", "rule": "x", "match": {"names": ["Dana Whitfield"]}}], "names never go in segments.json"),
        ("a missing names file", [{"key": "pals", "label": "Pals", "rule": "x", "match": {"namesFile": "pals.csv"}}], '"Pals": its names file, pals.csv, isn\'t in the Outreach folder'),
        ("a names file outside the Outreach folder", [{"key": "pals", "label": "Pals", "rule": "x", "match": {"namesFile": "../pals.csv"}}], "no folder path"),
        ("a bad date", [{"key": "old", "label": "Old Team", "rule": "x", "match": {"connected": {"from": "2019-02-30", "to": "2020-01-01"}}}], "real date"),
        ("dates out of order", [{"key": "old", "label": "Old Team", "rule": "x", "match": {"connected": {"from": "2021-01-01", "to": "2020-01-01"}}}], "comes after"),
        ("an empty company list", [{"key": "co", "label": "Studios", "rule": "x", "match": {"companies": []}}], "at least one"),
        ("both default and match", [dict(ok_group, match={"jobSearch": True})], "not both"),
        ("a reserved key", [{"key": "others", "label": "Others", "rule": "x", "match": {"jobSearch": True}}], "taken by the board"),
        ("a key with spaces", [{"key": "Old Team", "label": "Old Team", "rule": "x", "match": {"jobSearch": True}}], "lowercase letters"),
        ("a missing rule line", [{"key": "pals", "label": "Pals", "match": {"jobSearch": True}}], "needs a rule"),
    ]
    for name, groups, expect in cases:
        write_segments(base, groups)
        code, out = run(base, "--check")
        report("--check fails on %s" % name, code != 0 and expect in out and "Traceback" not in out, out.strip().replace("\n", " | ")[:300])
    write_segments(base, [ok_group])
    with open(os.path.join(base, "Outreach", "segments.json"), "w", encoding="utf-8") as f:
        f.write('{"groups": [')
    code, out = run(base, "--check")
    report("--check fails plainly on broken JSON", code != 0 and "isn't valid JSON" in out and "Traceback" not in out, out.strip())
    write_segments(base, [{"key": "pals", "label": "Pals", "rule": "x", "match": {"namesFile": "pals.csv"}}])
    code, out = run(base)
    report("a build with errors stops and writes nothing", code != 0 and not os.path.exists(os.path.join(base, "Outreach", "outreach.html")), out.strip())
    write_segments(base, [ok_group])
    with open(os.path.join(base, "Outreach", "settings.json"), "w", encoding="utf-8") as f:
        json.dump({"format": "bishop.outreach.settings", "version": 1, "warmWindow": "2y"}, f)
    code, out = run(base, "--check")
    report("--check fails on an unknown warm window", code != 0 and 'warmWindow is "2y"' in out, out.strip())


def versions(work):
    folder = candidate_copy(work, "Versions")
    p = os.path.join(folder, "Reference_Profile.md")
    text = open(p, encoding="utf-8").read().replace("<!-- bishop-format: profile 1 -->", "<!-- bishop-format: profile 2 -->", 1)
    open(p, "w", encoding="utf-8").write(text)
    code, out = run(folder)
    report("a profile at format version 2 stops the build", code != 0 and "Reference_Profile.md is format version 2" in out and "Traceback" not in out, out.strip())
    folder = candidate_copy(work, "Versions2")
    p = os.path.join(folder, "Tracking_Field_Service.md")
    text = open(p, encoding="utf-8").read().replace("<!-- bishop-format: tracking 1 -->", "<!-- bishop-format: tracking 2 -->", 1)
    open(p, "w", encoding="utf-8").write(text)
    code, out = run(folder)
    report("a tracking file at format version 2 stops the build", code != 0 and "Tracking_Field_Service.md is format version 2" in out, out.strip())
    folder = candidate_copy(work, "Versions3")
    p = os.path.join(folder, "Outreach", "segments.json")
    data = json.load(open(p, encoding="utf-8"))
    data["version"] = 2
    json.dump(data, open(p, "w", encoding="utf-8"))
    code, out = run(folder, "--check")
    report("segments.json at version 2 stops the check", code != 0 and "segments.json is format version 2" in out, out.strip())


def names_layouts(work):
    sys.path.insert(0, os.path.dirname(BUILDER))
    import build_page  # noqa: E402

    d = os.path.join(work, "names")
    os.makedirs(d)
    cases = [
        ("a Name column", "Name,Team\nAva Lindgren,Design\nRavi Mehta,Sales\n", ["Ava Lindgren", "Ravi Mehta"]),
        ("First Name and Last Name columns", "Email,First Name,Last Name\nx@example.com,Ava,Lindgren\n,Ravi,Mehta\n", ["Ava Lindgren", "Ravi Mehta"]),
        ("the first column, no header", "Ava Lindgren,met at a hackathon\nRavi Mehta,old manager\n", ["Ava Lindgren", "Ravi Mehta"]),
        ("a byte-order mark", "﻿Name\nAva Lindgren\n", ["Ava Lindgren"]),
        ("notes above the header", "Notes:\n\"Exported list\"\n\nFirst Name,Last Name\nAva,Lindgren\n", ["Ava Lindgren"]),
        ("a Windows (cp1252) file", None, ["Zoë Brandt"]),
    ]
    for name, text, want in cases:
        p = os.path.join(d, "n.csv")
        if text is None:
            open(p, "wb").write("Name\nZoë Brandt\n".encode("cp1252"))
        else:
            open(p, "w", encoding="utf-8", newline="").write(text)
        got = build_page.read_names(p)
        report("names file layout: %s" % name, got == want, repr(got))


def export_zip():
    z = os.path.join(EXPORT, "Basic_LinkedInDataExport_10-12-2026.zip")
    ok = os.path.isfile(z)
    if ok:
        with zipfile.ZipFile(z) as f:
            for name in ("Connections.csv", "messages.csv"):
                inside = f.read(name).decode("utf-8").replace("\r\n", "\n")
                beside = open(os.path.join(EXPORT, name), encoding="utf-8", newline="").read().replace("\r\n", "\n")
                ok = ok and inside == beside
    report("the zipped export matches its two CSVs", ok, "regenerate the zip from the CSVs")


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    keep = argv[argv.index("--keep") + 1] if "--keep" in argv else None
    work = tempfile.mkdtemp(prefix="bishop-outreach-")
    try:
        built = candidate_build(work)
        if keep:
            dst = os.path.join(keep, "Bishop")
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(built, dst)
        defaults_and_no_search(work)
        broken(work)
        versions(work)
        names_layouts(work)
        export_zip()
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
