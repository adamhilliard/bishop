# -*- coding: utf-8 -*-
"""Build one interview study deck: a single HTML file that opens anywhere, with no server.

    python build_deck.py <deck folder> [--master <master file>] [-o <out.html>] [--check]

A deck folder holds meta.json and content/*.json (references/deck-schema.md). The page is
assets/template.html with its three slots filled: the deck's content, its meta, and, when given,
the user's master-set file (references/master-set.md), which lets a company deck show the answers
the user wrote in their master deck. The page lands next to the deck folder as <slug>.html, so
every deck sits side by side and a deck's "Edit in Core" link finds core.html.

--check validates without writing. Exits 1 on any error.

Mirrors Humblebrag's own builder (build_deck.mjs): the template and defaults.json are exported from
it, so only the filling happens here. Python 3.8+, standard library only.
"""
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))

KINDS = {"readiness", "cover", "hub", "shortlist", "section", "question", "followup",
         "story", "visual", "match", "notes"}
ORIGINS = {"standard", "jd", "recruiter", "research", "risk"}
WPM_WARN, WPM_ERROR = 165, 190
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load(folder):
    """meta.json, then content/*.json in name order: the same merge as build_deck.mjs."""
    content_dir = os.path.join(folder, "content")
    parts = [os.path.join(folder, "meta.json")]
    if os.path.isdir(content_dir):
        parts += [os.path.join(content_dir, f) for f in sorted(os.listdir(content_dir)) if f.endswith(".json")]
    meta, content = {}, []
    for p in parts:
        obj = read_json(p)
        if isinstance(obj, list):
            content += obj
            continue
        meta.update(obj.get("meta") or {})
        content += obj.get("content") or []
    return meta, content


def slug_of(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def interview_line(iv):
    if not iv or not iv.get("date"):
        return None
    y, m, d = (int(x) for x in iv["date"].split("-"))
    day = DAYS[datetime.date(y, m, d).weekday()]
    parts = [iv.get("round"), "%s, %s %d, %d" % (day, MONTHS[m - 1], d, y), iv.get("time")]
    return " · ".join(p for p in parts if p)


def prepare_meta(meta, defaults):
    deck = dict(meta.get("deck") or {})
    deck["askThemes"] = list(defaults["askThemes"]) + list(deck.get("askThemes") or [])
    deck["site"] = dict(defaults["site"])
    line = interview_line(deck.get("interview"))
    if line:
        deck["sidebar"] = [line] + list(deck.get("sidebar") or [])
    out = dict(meta)
    out["deck"] = deck
    return out


def validate(meta, content, defaults):
    errors, warnings = [], []
    deck = meta.get("deck") or {}
    ids = [c.get("id") for c in content]
    seen, dupes = set(), set()
    for i in ids:
        (dupes if i in seen else seen).add(i)
    if dupes:
        errors.append("duplicate slide ids: " + ", ".join(sorted(str(d) for d in dupes)))
    idset = set(ids)
    sections = meta.get("sections") or []
    for s in sections:
        for f in ("id", "title", "color"):
            if f not in s:
                errors.append("section %s: missing %s" % (s.get("id", "?"), f))
    role_of = {s["id"]: s.get("role") for s in sections if "id" in s}
    themes = {t["id"] for t in defaults["askThemes"]} | {t.get("id") for t in deck.get("askThemes") or []}
    for c in content:
        cid, kind = c.get("id", "?"), c.get("kind")
        if kind not in KINDS:
            errors.append('%s: unknown kind "%s"' % (cid, kind))
        if "section" not in c:
            errors.append("%s: missing section" % cid)
        if kind in ("question", "followup"):
            for f in ("title", "why", "target"):
                if f not in c:
                    errors.append("%s: question missing %s" % (cid, f))
            # No script is the normal case: the candidate writes every answer in the deck.
            if c.get("target") and c.get("script"):
                wpm = len(c["script"].split()) / (c["target"] / 60.0)
                if wpm > WPM_ERROR:
                    errors.append("%s: %d words a minute; cut the script" % (cid, wpm))
                elif wpm > WPM_WARN:
                    warnings.append("%s: %d words a minute, fast for speech" % (cid, wpm))
        if kind == "followup":
            errors.append("%s: follow-ups aren't used. Make it a question of its own, or cut it." % cid)
        role = role_of.get(c.get("section"))
        if kind == "question" and role in ("hard", "ask"):
            if c.get("origin") not in ORIGINS:
                errors.append("%s: needs an origin (%s)" % (cid, ", ".join(sorted(ORIGINS))))
            elif c["origin"] != "standard" and not str(c.get("source") or "").strip():
                errors.append("%s: a %s question cites its source" % (cid, c["origin"]))
            if role == "ask" and c.get("theme") not in themes:
                errors.append("%s: a question to ask needs a theme (%s)" % (cid, ", ".join(sorted(themes))))
        # An interview deck's own question (not linked to the master deck) says where it came from.
        elif kind == "question" and not deck.get("evergreen") and not c.get("core") and not str(c.get("source") or "").strip():
            warnings.append("%s: a question written for this interview cites its source (the posting line, recruiter's words, finding, or resume line)" % cid)
    if deck.get("evergreen"):
        return errors, warnings
    # Every risk is pressed by a tough question, and the top one is on the cover.
    hard_ids = {c.get("id") for c in content if role_of.get(c.get("section")) == "hard"}
    risks = meta.get("risks") or []
    if not risks:
        warnings.append("META.risks: no risk list; the map's risks belong here, each with the questions that cover it")
    for rk in risks:
        for f in ("id", "title", "source"):
            if not rk.get(f):
                errors.append("risk %s: missing %s" % (rk.get("id", "?"), f))
        answers = rk.get("answers") or []
        for a in answers:
            if a not in idset:
                errors.append("risk %s: question %s does not exist" % (rk.get("id"), a))
        if not any(a in hard_ids for a in answers):
            errors.append("risk %s: no tough question covers it (add one to Tough Questions and list it in answers)" % rk.get("id"))
    if risks and not (deck.get("cover") or {}).get("risk"):
        warnings.append("META.deck.cover.risk: name the top risk on the cover")
    return errors, warnings


def to_script(obj):
    # "</" inside a string would close the data's <script> early, so it is escaped.
    return json.dumps(obj, indent=2, ensure_ascii=False).replace("</", "<\\/")


def build(meta, content, defaults, master=None):
    with open(os.path.join(ASSETS, "template.html"), encoding="utf-8") as f:
        html = f.read()
    fills = [
        ("__CONTENT__", to_script(content)),
        ("__META__", to_script(prepare_meta(meta, defaults))),
        ("__MASTER_DATA__", '<script type="application/json" id="master-data">%s</script>' % to_script(master) if master else ""),
    ]
    for token, value in fills:
        if html.count(token) != 1:
            sys.exit("assets/template.html needs exactly one %s; export it again from Humblebrag" % token)
        html = html.replace(token, value, 1)
    return html


def main(argv):
    args, opts = [], {"master": None, "out": None, "check": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--master":
            opts["master"] = argv[i + 1]
            i += 1
        elif a in ("-o", "--out"):
            opts["out"] = argv[i + 1]
            i += 1
        elif a == "--check":
            opts["check"] = True
        else:
            args.append(a)
        i += 1
    if len(args) != 1 or not os.path.isfile(os.path.join(args[0], "meta.json")):
        print(__doc__)
        return 1
    folder = os.path.abspath(args[0])
    defaults = read_json(os.path.join(ASSETS, "defaults.json"))
    meta, content = load(folder)
    errors, warnings = validate(meta, content, defaults)
    for w in warnings:
        print("WARN:  " + w)
    for e in errors:
        print("ERROR: " + e)
    if opts["check"] or errors:
        print("%d slides checked, %d errors, %d warnings" % (len(content), len(errors), len(warnings)))
        return 1 if errors else 0
    master = None
    if opts["master"]:
        master = read_json(opts["master"])
        want = defaults["masterFormat"]
        if master.get("format") != want["format"] or master.get("version") != want["version"]:
            print("ERROR: %s is not a master-set file this version reads" % opts["master"])
            return 1
    slug = (meta.get("deck") or {}).get("slug") or slug_of(os.path.basename(folder))
    out = opts["out"] or os.path.join(os.path.dirname(folder), slug + ".html")
    html = build(meta, content, defaults, master)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    n = lambda k: sum(1 for c in content if c.get("kind") == k)
    print("Wrote %s  (%d KB)  %d questions" % (out, len(html) // 1024, n("question")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
