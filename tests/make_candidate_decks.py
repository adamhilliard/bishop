# -*- coding: utf-8 -*-
"""Write the test candidate's interview decks (tests/candidate/Interview_Prep/): a core deck and one
company deck (Hooli, two rounds, recording audio only). Everything is made up: no real people or companies.
The core answers a company deck shows come from the browser; tests/run_all.py seeds them for the flows.

    python tests/make_candidate_decks.py
"""
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "candidate", "Interview_Prep")


def w(path, obj):
    path = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def q(id, sec, title, why, target=60, **kw):
    return {"kind": "question", "id": id, "section": sec, "chain": id, "title": title, "why": why, "target": target, **kw}


def section(sec, title):
    return {"kind": "section", "id": "S" + sec, "section": sec, "title": title, "cards": True}


ORANGE, BLUE = "#e2541b", "#2f6fde"

# ---- The core deck ----
w("core/meta.json", {"meta": {
    "deck": {"slug": "core", "title": "Core Deck", "brandTitle": "Core deck", "master": True, "evergreen": True,
             "rigor": "light", "theme": {"accent": ORANGE}, "jd": {"none": "Every interview"}},
    "sections": [
        {"id": "I", "title": "Readiness", "color": ORANGE},
        {"id": "A", "title": "Opening", "color": ORANGE},
        {"id": "R", "title": "Resume", "color": ORANGE},
        {"id": "C", "title": "Behavioral", "color": ORANGE},
        {"id": "E", "title": "Tough Questions", "color": ORANGE, "role": "hard"},
        {"id": "F", "title": "Questions to Ask", "color": ORANGE, "role": "ask"},
    ]}})
w("core/content/00-readiness.json", {"content": [{"kind": "readiness", "id": "cover", "section": "I", "title": "Your core deck"}]})
w("core/content/10-opening.json", {"content": [
    section("A", "Opening"),
    q("QA1", "A", "Tell me about yourself.", "The opener. They want the arc in two minutes, and why it leads here.", 120),
    q("QA2", "A", "Why are you looking?", "Whether you're running from something or toward something."),
]})
w("core/content/20-resume.json", {"content": [
    section("R", "Resume"),
    q("QR1", "R", "I see you cut first-visit fix time by 30%. Walk me through how.", "They want to see you own a number.", 90,
      source="Acme Robotics, 2021 to now: Cut first-visit fix time by 30% by rebuilding parts staging"),
]})
w("core/content/30-behavioral.json", {"content": [
    section("C", "Behavioral"),
    q("QC1", "C", "Tell me about a time a project went wrong. What did you do?", "Ownership when things break.", 90,
      source="Behavioral bank: Setbacks"),
]})
w("core/content/40-hard.json", {"content": [
    section("E", "Tough Questions"),
    q("QE1", "E", "What's your biggest weakness?", "Self-awareness, and whether you're working on it.", origin="standard"),
]})
w("core/content/50-ask.json", {"content": [
    section("F", "Questions to Ask"),
    q("QF1", "F", "Why is this seat open?", "What happened to the last person tells you what you're walking into.", 0,
      origin="standard", theme="history"),
    q("QF2", "F", "What does the first year need to deliver?", "Whether the plan is real.", 0, origin="standard", theme="first-year"),
]})

# ---- One company deck, every round in it ----
w("hooli/meta.json", {"meta": {
    "deck": {
        "slug": "hooli", "title": "Hooli Deck", "brandTitle": "Hooli", "record": "audio",
        "rounds": [
            {"id": "screen", "label": "Recruiter screen", "ask": "Priya", "who": "Priya Shah, Recruiter", "date": "2030-03-04", "time": "10:00 a.m."},
            {"id": "hm", "label": "Hiring manager", "ask": "Jordan", "who": "Jordan Lee, Head of Service",
             "guide": {"title": "Jordan owns the service plan", "body": "Expect the first-year plan and the numbers behind it."}},
        ],
        "round": "screen",
        "sidebar": ["Applied through the posting"],
        "jd": {"href": "https://example.com/hooli/vp-field-service", "label": "Job description"},
        "theme": {"accent": BLUE},
        "cover": {"eyebrow": "Hooli / Service", "title": "VP, Field Service",
                  "description": ["Every round of Hooli's process, one deck."],
                  "actions": [{"label": "Start practicing", "go": "QA1", "primary": True}],
                  "risk": {"title": "Highest-risk question: QE20", "body": "The posting asks for a 200-person org; Sam has led 60."}},
        "hub": {"title": "What this hire needs to solve.", "intro": "Ranked from the posting and the recruiter call."},
    },
    "sections": [
        {"id": "I", "title": "Overview", "color": BLUE},
        {"id": "A", "title": "Opening", "color": BLUE},
        {"id": "B", "title": "Their Priorities", "color": BLUE},
        {"id": "E", "title": "Tough Questions", "color": BLUE, "role": "hard"},
        {"id": "F", "title": "Questions to Ask", "color": BLUE, "role": "ask"},
        {"id": "N", "title": "Interview Notes", "color": BLUE},
    ],
    "priorities": [{"id": "P1", "title": "Scale the field org", "detail": "From one region to four in two years.", "partial": True}],
    "risks": [{"id": "R1", "title": "Has led 60, posting asks for 200", "source": "The posting", "answers": ["QE20"]}],
}})
w("hooli/content/00-intro.json", {"content": [
    {"kind": "cover", "id": "cover", "section": "I", "title": "Hooli"},
    {"kind": "hub", "id": "hub", "section": "I", "title": "Their priorities",
     "priorities": [{"id": "P1", "title": "Scale the field org", "quote": "We need someone who's built regions before.",
                     "detail": "Priya, via the recruiter call.", "answers": ["QB1"]}]},
]})
w("hooli/content/10-opening.json", {"content": [
    section("A", "Opening"),
    q("QA1", "A", "Walk me through your background.", "The opener, worded the way Priya asks it.", 90, core="QA1"),
    q("QA20", "A", "Why Hooli?", "Whether you know what they do and why it fits.", source="The posting: robots in 400 hospitals"),
]})
w("hooli/content/20-priorities.json", {"content": [
    section("B", "Their Priorities"),
    q("QB1", "B", "How would you take us from one region to four?", "P1, pressed where Sam only partly meets it.", 90,
      source="Recruiter call: built regions before", verify="Confirm how many techs the second Acme region had at launch."),
]})
w("hooli/content/40-hard.json", {"content": [
    section("E", "Tough Questions"),
    q("QE20", "E", "You've led 60 people. This is 200. Why you?", "The screen-out version of the scale gap.",
      origin="jd", source="The posting: leads a 200-person field org"),
    q("QE1", "E", "What's your biggest weakness?", "Self-awareness.", origin="standard", core="QE1"),
]})
w("hooli/content/50-ask.json", {"content": [
    section("F", "Questions to Ask"),
    q("QF20", "F", "How many of the four regions have a lead today?", "Tells you how much you'd build from zero.", 0,
      origin="research", source="Hooli careers page, 2030-02-20", theme="scope"),
    q("QF21", "F", "What would make the first ninety days a win for you?", "Jordan's own bar.", 0,
      origin="recruiter", source="Recruiter: Jordan sets the 90-day plan", theme="first-year", rounds=["hm"]),
    q("QF1", "F", "Why is this seat open?", "What happened to the last person.", 0, origin="standard", theme="history", core="QF1"),
]})
w("hooli/content/90-notes.json", {"content": [
    {"kind": "notes", "id": "notes", "section": "N", "title": "Interview Notes", "intro": "Facts to have straight before the call.",
     "cards": [{"title": "Research", "paragraphs": ["Hooli runs robots in about 400 hospitals (careers page, 2030-02-20).",
                                                    "VERIFY: whether the four regions are already staffed."]}]},
]})
print("wrote", ROOT)
