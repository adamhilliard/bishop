# -*- coding: utf-8 -*-
"""Build one interview deck: a single HTML file that opens anywhere, with no server.

    python build_deck.py <deck folder> [--master <answers file>] [--round <id>] [-o <out.html>] [--check]

A deck folder holds meta.json and content/*.json (references/deck-schema.md). The page is
assets/template.html with its three slots filled: the deck's content, its meta, and, when given,
the candidate's answers file (references/answers-file.md), which lets a company deck show the
answers they wrote in their master deck. The page lands next to the deck folder as <slug>.html, so
every deck sits side by side and a deck's "Edit in the master deck" link finds core.html.

One deck per company covers every round of its process: meta.deck.rounds lists them and
meta.deck.round picks the one coming up. --round builds or checks another round without changing
the files. The top bar carries the name the candidate gave their search, read from
Reference_Profile.md in the Bishop folder above the deck.

--check validates without writing. Exits 1 on any error. Python 3.8+, standard library only.
"""
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))

KINDS = {"readiness", "cover", "hub", "shortlist", "section", "question", "notes"}
ORIGINS = {"standard", "jd", "recruiter", "research", "risk"}
# The candidate writes every answer in the deck, so a deck file never carries answer text: no script,
# cues, closing or pivot line, or coaching note, and none of the slide kinds built from written answers.
# The engine drops them too (questionsOnly); this is where they're caught and explained.
ANSWER_FIELDS = ("script", "beats", "landing", "bridge", "avoid", "gateNote", "strategic", "lens", "extras", "framing")
ANSWER_KINDS = {"story", "visual", "match"}
ANSWER_DECK = ("gates", "beatLabels", "storyTargets", "stageLabels")
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


def search_name(folder):
    """The name the candidate gave their search at setup: Reference_Profile.md's Bot Name field,
    else its title ("# Wall-E Reference Profile: Maya Chen"), in the nearest folder above the deck."""
    d = os.path.abspath(folder)
    for _ in range(4):
        d = os.path.dirname(d)
        p = os.path.join(d, "Reference_Profile.md")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            lines = [x.rstrip() for x in f]
        for i, line in enumerate(lines):
            if re.match(r"^#+\s*Bot Name\s*$", line):
                for nxt in lines[i + 1 :]:
                    if nxt.strip().startswith("#"):
                        break
                    if nxt.strip():
                        return nxt.strip().strip("*").strip()
        for line in lines:
            m = re.match(r"^#\s+(.+?)\s+Reference Profile\b", line)
            if m:
                return m.group(1).strip()
        return None
    return None


def apply_round(meta, content, round_id, errors):
    """One deck per company, every round in it: keep the picked round's shortlist and its questions
    (a slide with "rounds" is only for those rounds), name the questions-to-ask section for that
    round's interviewer, put the round's guide first on the cover, and set the interview line."""
    deck = dict(meta.get("deck") or {})
    rounds = deck.get("rounds")
    if not rounds:
        return meta, content
    if not isinstance(rounds, list):
        errors.append("deck.rounds: a list of the process's rounds")
        return meta, content
    ids = [r.get("id") for r in rounds]
    for r in rounds:
        if not r.get("id") or not r.get("label"):
            errors.append("deck.rounds: every round needs an id and a label (%s)" % json.dumps(r))
    pick = round_id or deck.get("round")
    cur = next((r for r in rounds if r.get("id") == pick), None)
    if not cur:
        errors.append('deck.round "%s" is not one of deck.rounds (%s)' % (pick, ", ".join(str(i) for i in ids)))
        return meta, content
    for c in content:
        for r in c.get("rounds") or []:
            if r not in ids:
                errors.append('%s: rounds names "%s", which is not in deck.rounds' % (c.get("id", "?"), r))
    keep = lambda c: (c.get("round") in (None, cur["id"])) if c.get("kind") == "shortlist" else (not c.get("rounds") or cur["id"] in c["rounds"])
    dropped = {c.get("id") for c in content if not keep(c)}
    content = [c for c in content if keep(c)]
    deck["round"] = cur["id"]
    deck["interview"] = {"date": cur.get("date"), "time": cur.get("time"), "round": cur.get("label")}
    # Who this round is with ("Priya Shah, Recruiter") leads the sidebar's people; deck.sidebar holds only
    # what's true in every round.
    if cur.get("who"):
        deck["sidebar"] = [cur["who"]] + list(deck.get("sidebar") or [])
    if cur.get("guide"):
        cover = dict(deck.get("cover") or {})
        cover["guides"] = [cur["guide"]] + list(cover.get("guides") or [])
        deck["cover"] = cover
    out = dict(meta)
    out["deck"] = deck
    ask = next((s for s in meta.get("sections") or [] if s.get("role") == "ask"), None)
    if ask and cur.get("ask"):
        title = "Questions for %s" % cur["ask"]
        out["sections"] = [dict(s, title=title, questionLabel="Ask %s" % cur["ask"]) if s is ask else s for s in meta["sections"]]
        content = [dict(c, title=title) if c.get("kind") == "section" and c.get("section") == ask.get("id") else c for c in content]
    if meta.get("risks"):
        out["risks"] = [dict(rk, answers=[a for a in rk.get("answers") or [] if a not in dropped]) for rk in meta["risks"]]
    content = [dict(c, priorities=[dict(p, answers=[a for a in p.get("answers") or [] if a not in dropped]) for p in c["priorities"]])
               if c.get("kind") == "hub" and c.get("priorities") else c for c in content]
    return out, content


def slug_of(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def interview_line(iv):
    if not iv or not iv.get("date"):
        return None
    y, m, d = (int(x) for x in iv["date"].split("-"))
    day = DAYS[datetime.date(y, m, d).weekday()]
    parts = [iv.get("round"), "%s, %s %d, %d" % (day, MONTHS[m - 1], d, y), iv.get("time")]
    return " · ".join(p for p in parts if p)


def prepare_meta(meta, defaults, name=None):
    deck = dict(meta.get("deck") or {})
    deck["askThemes"] = list(defaults["askThemes"]) + list(deck.get("askThemes") or [])
    deck["site"] = dict(defaults["site"])
    if name:
        deck["site"]["brand"] = name
    line = interview_line(deck.get("interview"))
    if line:
        deck["sidebar"] = [line] + list(deck.get("sidebar") or [])
        # A deck with rounds puts the round coming up first on the cover too; its description holds only
        # what's true in every round.
        if deck.get("rounds"):
            cover = dict(deck.get("cover") or {})
            cover["description"] = [line] + list(cover.get("description") or [])
            deck["cover"] = cover
    out = dict(meta)
    out["deck"] = deck
    return out


def master_ids(folder, meta):
    """The question ids in the master deck beside this one (Interview_Prep/core), or None if it isn't there."""
    slug = ((meta.get("deck") or {}).get("site") or {}).get("masterSlug") or "core"
    core = os.path.join(os.path.dirname(os.path.abspath(folder)), slug)
    if not os.path.isfile(os.path.join(core, "meta.json")):
        return None
    _, content = load(core)
    return {c.get("id") for c in content if c.get("kind") == "question"}


def validate(meta, content, defaults, masters=None):
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
        for f in ("id", "title"):
            if f not in s:
                errors.append("section %s: missing %s" % (s.get("id", "?"), f))
    role_of = {s["id"]: s.get("role") for s in sections if "id" in s}
    themes = {t["id"] for t in defaults["askThemes"]} | {t.get("id") for t in deck.get("askThemes") or []}
    for f in ANSWER_DECK:
        if f in deck:
            errors.append("deck.%s: answer coaching isn't used; the candidate writes every answer. Remove it." % f)
    for c in content:
        cid, kind = c.get("id", "?"), c.get("kind")
        if kind == "followup":
            errors.append("%s: follow-ups aren't used. Make it a question of its own, or cut it." % cid)
        elif kind in ANSWER_KINDS:
            errors.append('%s: a "%s" slide is built from a written answer, and the candidate writes every answer. Cut it.' % (cid, kind))
        elif kind not in KINDS:
            errors.append('%s: unknown kind "%s"' % (cid, kind))
        if "section" not in c:
            errors.append("%s: missing section" % cid)
        for f in ANSWER_FIELDS:
            if f in c:
                errors.append("%s: %s is answer text, and the candidate writes every answer in the deck. Remove it." % (cid, f))
        if kind == "question":
            for f in ("title", "why", "target"):
                if f not in c:
                    errors.append("%s: question missing %s" % (cid, f))
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
    for a in (deck.get("cover") or {}).get("actions") or []:
        if a.get("go") not in idset:
            errors.append("cover button '%s' goes to %s, which is not in the deck" % (a.get("label", "?"), a.get("go")))
    if deck.get("evergreen"):
        return errors, warnings
    # A linked question shows its master answer, so the master question has to exist.
    linked = [c for c in content if c.get("kind") == "question" and c.get("core")]
    if linked and masters is None:
        warnings.append("no master deck beside this one (Interview_Prep/core), so its links can't be checked")
    for c in linked:
        if masters is not None and c["core"] not in masters:
            errors.append("%s: core names %s, which isn't a question in the master deck" % (c.get("id", "?"), c["core"]))
    # The hub's links land on questions, and the hub and META.priorities describe the same priorities.
    hub_ids = set()
    for c in content:
        if c.get("kind") != "hub":
            continue
        for p in c.get("priorities") or []:
            hub_ids.add(p.get("id"))
            for a in p.get("answers") or []:
                if a not in idset:
                    errors.append("hub %s: question %s isn't in the deck" % (p.get("id"), a))
    for p in meta.get("priorities") or []:
        if hub_ids and p.get("id") not in hub_ids:
            warnings.append("priority %s has no card on the hub" % p.get("id"))
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


def build(meta, content, defaults, master=None, name=None):
    with open(os.path.join(ASSETS, "template.html"), encoding="utf-8") as f:
        html = f.read()
    fills = [
        ("__CONTENT__", to_script(content)),
        ("__META__", to_script(prepare_meta(meta, defaults, name))),
        ("__MASTER_DATA__", '<script type="application/json" id="master-data">%s</script>' % to_script(master) if master else ""),
    ]
    for token, value in fills:
        if html.count(token) != 1:
            sys.exit("assets/template.html needs exactly one %s; rebuild it with build_template.py" % token)
        html = html.replace(token, value, 1)
    return html


def check_answers_file(f, want):
    """The same checks the deck page runs (engine/answers.js checkFile): a file that fails them would
    silently show no master answers, so it stops the build instead."""
    if not isinstance(f, dict):
        return ["not an answers file"]
    p = []
    if f.get("format") != want["format"]:
        p.append('format is "%s", expected "%s"' % (f.get("format"), want["format"]))
    if f.get("version") != want["version"]:
        p.append("version is %s; this reads version %s" % (f.get("version"), want["version"]))
    decks = f.get("decks")
    if not isinstance(decks, dict):
        return p + ["decks must be an object keyed by deck slug"]
    for slug, d in decks.items():
        if not re.match(r"^[a-z0-9-]{1,60}$", slug):
            p.append('deck "%s": slug must be lowercase letters, digits and dashes' % slug)
        for qid, box in ((d or {}).get("answers") or {}).items():
            if box.get("sections") is not None and not isinstance(box["sections"], list):
                p.append("deck %s, %s: sections must be a list of {name, text}" % (slug, qid))
    return p


def main(argv):
    args, opts = [], {"master": None, "out": None, "check": False, "round": None}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--master", "--round", "-o", "--out"):
            if i + 1 >= len(argv) or argv[i + 1].startswith("-"):
                print("%s needs a value\n" % a)
                print(__doc__)
                return 1
            opts[{"-o": "out", "--out": "out"}.get(a, a.lstrip("-"))] = argv[i + 1]
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
    round_errors = []
    meta, content = apply_round(meta, content, opts["round"], round_errors)
    errors, warnings = validate(meta, content, defaults, master_ids(folder, meta))
    errors = round_errors + errors
    for w in warnings:
        print("WARN:  " + w)
    for e in errors:
        print("ERROR: " + e)
    if opts["check"] or errors:
        print("%d slides checked, %d errors, %d warnings" % (len(content), len(errors), len(warnings)))
        return 1 if errors else 0
    master = None
    if opts["master"]:
        if not os.path.isfile(opts["master"]):
            print("ERROR: no answers file at %s (build without --master until the candidate exports one)" % opts["master"])
            return 1
        try:
            master = read_json(opts["master"])
        except ValueError as e:
            print("ERROR: %s isn't readable JSON (%s)" % (opts["master"], e))
            return 1
        problems = check_answers_file(master, defaults["answersFile"])
        for problem in problems:
            print("ERROR: %s: %s" % (opts["master"], problem))
        if problems:
            return 1
    slug = (meta.get("deck") or {}).get("slug") or slug_of(os.path.basename(folder))
    out = opts["out"] or os.path.join(os.path.dirname(folder), slug + ".html")
    html = build(meta, content, defaults, master, search_name(folder))
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    n = lambda k: sum(1 for c in content if c.get("kind") == k)
    print("Wrote %s  (%d KB)  %d questions" % (out, len(html) // 1024, n("question")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
