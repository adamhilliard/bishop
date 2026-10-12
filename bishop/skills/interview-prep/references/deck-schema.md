# Deck files

A deck is a folder: `meta.json` (the deck's settings, sections, priorities and risks) and `content/*.json` (the slides, read in file-name order). Each content file is `{"content": [ ...slides ]}`; `meta.json` is `{"meta": { ... }}`.

## Slides

Every slide has `kind`, `id`, `section` and `title`, and appears in the order of the files, grouped by section.

**question**

| Field | Required | Notes |
|---|---|---|
| `title` | yes | The question, worded the way this interviewer would ask it |
| `chain` | yes | The question's own id |
| `why` | yes | What the interviewer is trying to learn, and for a custom question what makes it likely. Context, never a hint at the answer |
| `target` | yes | Seconds to answer, for the practice timer. `0` turns it off |
| `core` | | Interview decks: the master question this one asks the same thing as. Shows the candidate's master answer until they write a version for this interview |
| `origin` | in `hard` and `ask` sections | `standard`, `jd`, `recruiter`, `research` or `risk`. Shown as a tag on the card |
| `source` | unless `standard` | The posting line, recruiter's words, finding (with its date) or resume fact behind it |
| `theme` | in `ask` sections | A theme id (`assets/defaults.json`, or `META.deck.askThemes`) |
| `verify` | | A fact the candidate should confirm before the interview. Shows a VERIFY badge |
| `when` | | Master deck only: when a conditional question applies |

> **No follow-ups.** A second angle on a question is a question of its own; the builder rejects `"kind": "followup"`.

> **Leave the answer fields empty.** `script`, `beats`, `landing`, `bridge`, `avoid` and `gateNote` exist in the engine, but the candidate writes every answer in the deck. Don't fill them.

```json
{"kind": "question", "id": "QA1", "section": "A", "chain": "QA1",
 "title": "Walk me through your background.", "target": 90,
 "why": "The opener. They want the arc in two minutes, and why it leads here.",
 "core": "QA1"}
```

```json
{"kind": "question", "id": "QE1", "section": "E", "chain": "QE1",
 "title": "You haven't worked in robotics. Why you?", "target": 60,
 "origin": "risk", "source": "The posting asks for robotics experience.",
 "why": "The screen-out version of the industry gap. They want to see you own it."}
```

**section**: the first slide of every section that holds questions, id `S` plus the section letter. `"cards": true` shows its questions as a page of cards (use it in every section).

```json
{"kind": "section", "id": "SA", "section": "A", "title": "Opening", "cards": true}
```

**readiness**: the master deck's first slide: what's left to write, to lock in, and flagged. It needs only a title; the deck fills in the rest. Its section `I` goes first in `meta.sections`: `{"id": "I", "title": "Readiness"}`.

```json
{"kind": "readiness", "id": "cover", "section": "I", "title": "Your master deck"}
```

**cover**: an interview deck's first slide; its text comes from `META.deck.cover`.

**hub**: `priorities: [{id, title, quote, detail, answers: [slide ids]}]`. The quote is the hiring team's own words; leave it out rather than paraphrasing into quotation marks.

**visual**: a drill revealed one step at a time. `labels` and `details` (same length), `note`, `mode` (`"map"` for a hub-and-spoke, anything else for steps).

**notes**: `eyebrow`, `intro`, `cards: [{title, paragraphs, bullets}]`. A paragraph starting with `VERIFY` shows as an open item.

## meta.json

```json
{
  "meta": {
    "deck": {
      "slug": "acme-robotics",
      "title": "Acme Robotics Deck",
      "brandTitle": "Acme Robotics",
      "interview": {"date": "2030-03-04", "time": "10:00 a.m.", "round": "Recruiter screen"},
      "sidebar": ["Jordan Lee, Head of Service"],
      "jd": {"href": "https://posting-url", "label": "Job description"},
      "theme": {"accent": "#2f6fde"},
      "cover": {
        "eyebrow": "Acme Robotics / Service",
        "title": "Head of Field Service",
        "description": ["Recruiter screen with Jordan Lee, Head of Service."],
        "actions": [{"label": "Start practicing", "go": "QA1", "primary": true}],
        "risk": {"title": "Highest-risk question: QE1", "body": "The posting asks for robotics experience."}
      },
      "hub": {"title": "What this hire needs to solve.", "intro": "Ranked from the posting and the recruiter call."}
    },
    "sections": [
      {"id": "A", "title": "Opening", "color": "#2f6fde"},
      {"id": "E", "title": "Tough Questions", "color": "#2f6fde", "role": "hard"},
      {"id": "F", "title": "Questions to Ask", "color": "#2f6fde", "role": "ask", "questionLabel": "Ask Jordan"}
    ],
    "priorities": [{"id": "P1", "title": "Stand up the first service region", "detail": "...", "partial": false}],
    "risks": [{"id": "R1", "title": "No robotics background", "source": "The posting", "answers": ["QE1"]}]
  }
}
```

- **`deck.slug`** is required and matches the deck's folder name. The master deck is `core`, with `"master": true` and `"evergreen": true`.
- **`deck.interview.date`** is `YYYY-MM-DD`; the builder puts the round, date and time first in the sidebar.
- **`deck.theme.accent`** is the company's own brand color, read from their site, never guessed. The master deck keeps a neutral one.
- **`deck.jd`** links the posting in the header; with none, `{"none": "No posting · referral"}`.
- **`sections[].role`**: `"hard"` (Tough Questions) or `"ask"` (Questions to Ask) turns on the origin, source and theme checks.
- **`priorities[].partial`** marks a priority the candidate can only partly speak to. **`risks[].answers`** lists the slides that cover it, at least one in a `hard` section.
