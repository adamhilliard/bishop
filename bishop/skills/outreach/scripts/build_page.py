# -*- coding: utf-8 -*-
"""Build the outreach board: one HTML file that opens from the user's own computer, with no server.

    python build_page.py <bishop folder> [--check]

Writes <bishop folder>/Outreach/outreach.html from assets/template.html, with its settings block
filled in. The page never holds contacts: the user uploads their LinkedIn export inside it, and the
contacts and the board stay in their browser. A rebuild keeps both.

Reads, from the Bishop folder (every file is optional, so outreach works with no job search):
  Outreach/segments.json     the user's groups, in tab order (assets/segments.default.json if missing)
  Outreach/<names file>      a hand-picked group's names, a CSV saved there as it was handed over
  Outreach/settings.json     the warm window ("any" if missing)
  Reference_Profile.md       the name they gave their Bishop, the accent color, past employers
  Tracking_*.md              companies in the live tables, for the job-search group and fit
  Employer_Index.md          the named employers, the same way

--check validates without writing. Exits 1 on any error. Python 3.8+, standard library only.
The file shapes are in references/data-format.md.
"""
import csv
import datetime
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))

CONFIG_FORMAT = "bishop.outreach.config"
SEGMENTS_FORMAT = "bishop.outreach.segments"
SETTINGS_FORMAT = "bishop.outreach.settings"
DEFAULTS = ("warm", "recruiters", "hr", "exec", "founders")
MATCHES = ("companies", "titleWords", "connected", "namesFile", "jobSearch")
WINDOWS = ("any", "3y", "1y")
RESERVED = ("motion", "others")
GROUP_FIELDS = {"key", "label", "rule", "default", "match"}
KEY_RE = re.compile(r"^[a-z][a-z0-9-]{0,31}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FALLBACK_ACCENT = "#4F6D9F"
LIVE_TABLES = re.compile(r"^(ACTIVE\s*/\s*ROLLING|BELOW THE CAP)\b", re.I)


class Stop(Exception):
    """A file this copy of outreach can't read. The message is the one line the user sees."""


# ---------- Reading files ----------

def read_text(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read()


def check_md_version(path, text):
    """A first-line `<!-- bishop-format: <file> <version> -->`. No line means version 1."""
    first = text.lstrip("﻿").split("\n", 1)[0]
    m = re.match(r"\s*<!--\s*bishop-format:\s*([A-Za-z_-]+)\s+(\S+)\s*-->", first)
    if m and m.group(2) != "1":
        raise Stop("%s is format version %s, and this copy of outreach reads version 1. Update Bishop, then build the page again."
                   % (os.path.basename(path), m.group(2)))


def read_json_file(path, fmt):
    try:
        data = json.loads(read_text(path))
    except ValueError as e:
        raise Stop("%s isn't valid JSON (%s). Fix the file, then build the page again." % (os.path.basename(path), e))
    if not isinstance(data, dict):
        raise Stop("%s should hold one JSON object, with a \"format\" line at the top." % os.path.basename(path))
    if "format" in data and data["format"] != fmt:
        raise Stop('%s says it is "%s"; outreach expects "%s".' % (os.path.basename(path), data["format"], fmt))
    if "version" in data and data["version"] != 1:
        raise Stop("%s is format version %s, and this copy of outreach reads version 1. Update Bishop, then build the page again."
                   % (os.path.basename(path), data["version"]))
    return data


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


def company_cell(cell):
    """`[Hooli](https://...)<br>One-line bio` -> `Hooli`."""
    cell = re.split(r"<br\s*/?>", cell, flags=re.I)[0]
    cell = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", cell)
    cell = re.sub(r"[*_`]", "", cell).strip()
    return "" if re.fullmatch(r"[-\u2014\u2013\s]*|none( yet)?\.?", cell, re.I) else cell


def column(table, names):
    head, rows = table
    low = [h.lower() for h in head]
    for n in names:
        if n in low:
            i = low.index(n)
            return [company_cell(r[i]) for r in rows if i < len(r)]
    return []


def unique(names):
    seen, out = set(), []
    for n in names:
        k = re.sub(r"\s+", " ", n).strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(re.sub(r"\s+", " ", n).strip())
    return out


# ---------- The profile, tracking files and employer index ----------

def bot_name(text):
    """The Bot Name section, else the title line ("# Wall-E Reference Profile: Sam Rivera")."""
    body = section(text, "Bot Name")
    if body:
        for line in body.splitlines():
            if line.strip():
                return line.strip().strip("*").strip()
    m = re.search(r"^#\s+(.+?)\s+Reference Profile\b", text, re.M)
    return m.group(1).strip() if m else None


def accent(text):
    body = section(text, "Customization") or ""
    for line in body.splitlines():
        if re.search(r"accent", line, re.I):
            m = re.search(r"#[0-9A-Fa-f]{6}\b", line)
            if m:
                return m.group(0).upper()
    m = re.search(r"#[0-9A-Fa-f]{6}\b", body)
    return m.group(0).upper() if m else None


def past_employers(text):
    body = section(text, "Full Career History") or ""
    out = []
    for t in tables(body):
        out += column(t, ["company", "employer"])
    return unique(out)


def tracking_companies(path, text):
    out, current = [], None
    lines = text.splitlines()
    # Split the file into headed parts; keep the tables under a live heading.
    parts, buf = [], []
    for line in lines:
        m = re.match(r"^#{1,6}\s+(.*)$", line)
        if m:
            parts.append((current, "\n".join(buf)))
            current, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    parts.append((current, "\n".join(buf)))
    for title, body in parts:
        if title and LIVE_TABLES.match(title):
            for t in tables(body):
                out += column(t, ["company"])
    return out


def index_companies(text):
    out = []
    for t in tables(text):
        out += column(t, ["company", "employer"])
    return out


def read_profile(folder):
    p = os.path.join(folder, "Reference_Profile.md")
    if not os.path.isfile(p):
        return None, None, []
    text = read_text(p)
    check_md_version(p, text)
    return bot_name(text), accent(text), past_employers(text)


def search_companies(folder):
    out = []
    for p in sorted(glob.glob(os.path.join(folder, "Tracking_*.md"))):
        text = read_text(p)
        check_md_version(p, text)
        out += tracking_companies(p, text)
    p = os.path.join(folder, "Employer_Index.md")
    if os.path.isfile(p):
        text = read_text(p)
        check_md_version(p, text)
        out += index_companies(text)
    return unique(out)


# ---------- A hand-picked group's names file ----------

def read_names(path):
    """Names from a CSV: a Name column, First Name plus Last Name columns, or else the first column.
    A byte-order mark is stripped. Excel's "CSV" saved on Windows may not be UTF-8, so that's tried second."""
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    text = text.lstrip("﻿")
    rows = [r for r in csv.reader(io.StringIO(text)) if any(c.strip() for c in r)]
    if not rows:
        return []
    # A header can sit below a few lines of notes (LinkedIn's own exports do this).
    for h, row in enumerate(rows[:10]):
        low = [c.strip().lstrip("﻿").lower() for c in row]
        if "name" in low or "full name" in low:
            i = low.index("name") if "name" in low else low.index("full name")
            return unique(r[i] for r in rows[h + 1:] if i < len(r))
        if "first name" in low and "last name" in low:
            a, b = low.index("first name"), low.index("last name")
            return unique(" ".join(x for x in ((r[a] if a < len(r) else ""), (r[b] if b < len(r) else "")) if x.strip())
                          for r in rows[h + 1:])
    # No header we know: the first column. A first cell that is a heading ("Person", "Contact") is skipped
    # only when it says "name"; anything else is taken as a person.
    body = rows[1:] if re.search(r"\bname\b", rows[0][0], re.I) else rows
    return unique(r[0] for r in body if r)


# ---------- segments.json ----------

def valid_date(s):
    if not isinstance(s, str) or not DATE_RE.match(s):
        return False
    try:
        datetime.date(*(int(x) for x in s.split("-")))
        return True
    except ValueError:
        return False


def check_groups(data, outreach_dir, errors, warnings, search):
    """Validate the groups; return them as the page reads them (names files read into names lists)."""
    groups = data.get("groups")
    if not isinstance(groups, list):
        errors.append('segments.json needs a "groups" list (it can be empty, which leaves everyone in Everyone Else)')
        return []
    if not groups:
        warnings.append("segments.json lists no groups, so everyone lands in Everyone Else")
    out, keys, labels, defaults = [], set(), set(), set()
    for n, g in enumerate(groups, 1):
        if not isinstance(g, dict):
            errors.append("group %d: each group is an object with a key, a label and a rule" % n)
            continue
        key = g.get("key")
        name = '"%s"' % (g.get("label") or key or "group %d" % n)
        for f in sorted(set(g) - GROUP_FIELDS):
            if not f.startswith("_"):
                errors.append('%s: "%s" isn\'t a group field (use key, label, rule, and default or match)' % (name, f))
        if not isinstance(key, str) or not KEY_RE.match(key):
            errors.append("%s: the key must be short, lowercase letters, numbers and dashes, starting with a letter (it is %s)" % (name, json.dumps(key)))
        elif key in RESERVED:
            errors.append('%s: the key "%s" is taken by the board itself; pick another' % (name, key))
        elif key in keys:
            errors.append('%s: another group already uses the key "%s"; every key is different' % (name, key))
        else:
            keys.add(key)
        label = g.get("label")
        if not isinstance(label, str) or not label.strip():
            errors.append("%s: needs a label, the tab's name" % name)
        elif label.strip().lower() in labels or label.strip().lower() == "everyone else":
            errors.append("%s: another tab already has this label" % name)
        else:
            labels.add(label.strip().lower())
        if not isinstance(g.get("rule"), str) or not g["rule"].strip():
            errors.append("%s: needs a rule, one plain line saying who belongs here" % name)
        has_default, has_match = "default" in g, "match" in g
        if has_default == has_match:
            errors.append("%s: give it either a default or a match, not %s" % (name, "both" if has_default else "neither"))
            continue
        page = {"key": key, "label": label, "rule": g.get("rule")}
        if has_default:
            d = g["default"]
            if d not in DEFAULTS:
                errors.append('%s: "%s" isn\'t a default group (the defaults are %s)' % (name, d, ", ".join(DEFAULTS)))
            elif d in defaults:
                errors.append('%s: the "%s" default is already in the list; each default appears once' % (name, d))
            else:
                defaults.add(d)
            page["default"] = d
            out.append(page)
            continue
        m = g["match"]
        if not isinstance(m, dict) or len(m) != 1:
            errors.append("%s: match holds exactly one rule, one of %s" % (name, ", ".join(MATCHES)))
            continue
        kind, val = next(iter(m.items()))
        if kind == "names":
            errors.append('%s: names never go in segments.json. Save the list as a CSV in the Outreach folder and use {"namesFile": "<file name>"}' % name)
            continue
        if kind not in MATCHES:
            errors.append('%s: "%s" isn\'t a match type (use %s)' % (name, kind, ", ".join(MATCHES)))
            continue
        if kind in ("companies", "titleWords"):
            if not isinstance(val, list) or not val or not all(isinstance(x, str) and x.strip() for x in val):
                errors.append("%s: %s is a list of %s, with at least one" % (name, kind, "company names" if kind == "companies" else "title words"))
                continue
            page["match"] = {kind: [x.strip() for x in val]}
        elif kind == "connected":
            if not isinstance(val, dict) or not (set(val) <= {"from", "to"}) or not val:
                errors.append('%s: connected is {"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"}' % name)
                continue
            bad = [k for k in ("from", "to") if k in val and not valid_date(val[k])]
            if bad:
                errors.append("%s: connected %s must be a real date written YYYY-MM-DD" % (name, " and ".join(bad)))
                continue
            if "from" in val and "to" in val and val["from"] > val["to"]:
                errors.append("%s: connected from (%s) comes after to (%s)" % (name, val["from"], val["to"]))
                continue
            page["match"] = {"connected": dict(val)}
        elif kind == "jobSearch":
            if val is not True:
                errors.append("%s: jobSearch is true, or leave the group out" % name)
                continue
            if not search:
                warnings.append("%s: no companies in a job search yet, so this group stays empty" % name)
            page["match"] = {"jobSearch": True}
        elif kind == "namesFile":
            if not isinstance(val, str) or not val.strip() or os.path.basename(val) != val or val in (".", ".."):
                errors.append("%s: namesFile is a file name inside the Outreach folder, with no folder path (it is %s)" % (name, json.dumps(val)))
                continue
            path = os.path.join(outreach_dir, val)
            if not os.path.isfile(path):
                errors.append("%s: its names file, %s, isn't in the Outreach folder" % (name, val))
                continue
            if not val.lower().endswith((".csv", ".txt")):
                errors.append("%s: %s isn't a CSV. Save the spreadsheet as CSV into the Outreach folder and point namesFile at that" % (name, val))
                continue
            names = read_names(path)
            if not names:
                errors.append("%s: %s has no names in it" % (name, val))
                continue
            page["match"] = {"names": names}
        out.append(page)
    return out


def read_segments(outreach_dir, errors, warnings, search):
    p = os.path.join(outreach_dir, "segments.json")
    source = p if os.path.isfile(p) else os.path.join(ASSETS, "segments.default.json")
    data = read_json_file(source, SEGMENTS_FORMAT)
    return check_groups(data, outreach_dir, errors, warnings, search), os.path.isfile(p)


def read_settings(outreach_dir, errors):
    p = os.path.join(outreach_dir, "settings.json")
    if not os.path.isfile(p):
        return "any"
    data = read_json_file(p, SETTINGS_FORMAT)
    w = data.get("warmWindow", "any")
    if w not in WINDOWS:
        errors.append('settings.json: warmWindow is "%s"; use "any", "3y" or "1y"' % w)
        return "any"
    return w


# ---------- Build ----------

def to_script(obj):
    # "<" inside a string could close the settings <script> early, so every one is escaped.
    return json.dumps(obj, indent=2, ensure_ascii=False).replace("<", "\\u003c")


def config_for(folder, errors, warnings):
    outreach_dir = os.path.join(folder, "Outreach")
    name, color, past = read_profile(folder)
    search = search_companies(folder)
    groups, _ = read_segments(outreach_dir, errors, warnings, search)
    window = read_settings(outreach_dir, errors)
    return {
        "format": CONFIG_FORMAT,
        "version": 1,
        "name": name or "Bishop",
        "accent": color or FALLBACK_ACCENT,
        "warmWindow": window,
        "groups": groups,
        "pastEmployers": past,
        "searchCompanies": search,
    }


def build(config):
    html = read_text(os.path.join(ASSETS, "template.html"))
    if html.count("__CONFIG__") != 1:
        sys.exit("assets/template.html needs exactly one __CONFIG__")
    return html.replace("__CONFIG__", to_script(config), 1)


def main(argv):
    args = [a for a in argv if a != "--check"]
    check = "--check" in argv
    if len(args) != 1 or args[0].startswith("-") or not os.path.isdir(args[0]):
        print(__doc__)
        return 1
    folder = os.path.abspath(args[0])
    errors, warnings = [], []
    try:
        config = config_for(folder, errors, warnings)
    except Stop as e:
        print("STOP:  " + str(e))
        return 1
    for w in warnings:
        print("WARN:  " + w)
    for e in errors:
        print("ERROR: " + e)
    if check or errors:
        print("%d groups checked, %d errors, %d warnings" % (len(config["groups"]), len(errors), len(warnings)))
        return 1 if errors else 0
    out_dir = os.path.join(folder, "Outreach")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "outreach.html")
    html = build(config)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("Wrote %s  (%d KB)  %d groups plus Everyone Else, warm window %s" % (out, len(html) // 1024, len(config["groups"]), config["warmWindow"]))
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    sys.exit(main(sys.argv[1:]))
