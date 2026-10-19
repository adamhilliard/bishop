# Deck files

A deck is a folder: `meta.json` (the deck's settings, sections, priorities and risks) and `content/*.json` (the slides, read in file-name order). Each content file is `{"content": [ ...slides ]}`; `meta.json` is `{"meta": { ... }}`.

## Slides

Every slide has `kind`, `id`, `section` and `title`, and appears in the order of the files, grouped by section.

**question / followup**

| Field | Required | Notes |
|---|---|---|
| `title` | yes | The question, as it would be asked |
| `chain` | yes | The question's own id, or its parent's for a follow-up. Keeps follow-ups with their question when a section shuffles |
| `why` | yes | Why they're asking. Shows in the "why" panel (can be `""` in the master deck) |
| `target` | yes | Seconds to answer. `0` turns the timer off |
| `script` | yes, unless `core` or the master deck | The spoken answer. `\n\n` between paragraphs |
| `core` | | Interview decks: the master question this one asks the same thing as. Until the candidate writes a version for this deck, it shows their master answer, then `landing` |
| `landing` | with `core` | One line said after the master answer that ties it to this company |
| `beats` | recommended with a script | 4 to 6 recall cues, fragments, not sentences |
| `origin` | in `hard` and `ask` sections | `standard`, `jd`, `recruiter`, `research` or `risk`. Shown as a tag on the card |
| `source` | unless `standard` | The posting line, recruiter's words, finding (with its date) or resume fact behind it |
| `theme` | in `ask` sections | A theme id (`assets/defaults.json`, or `META.deck.askThemes`) |
| `parent`, `followupNumber` | follow-ups | The parent question's id; 1, 2, 3 |
| `bridge` | | One line: the point the answer has to land |
| `avoid` | | The specific way this answer goes wrong |
| `note` | | A confirmed detail worth holding |
| `verify` | | An open item. Shows a VERIFY badge until the candidate edits the answer |
| `gateNote` | | The test of a good answer |
| `when` | | Master deck only: when a conditional question applies |

```json
{"kind": "question", "id": "QA1", "section": "A", "chain": "QA1",
 "title": "Walk me through your background.", "target": 90,
 "why": "The opener. Give the arc, then land on why this role.",
 "core": "QA1",
 "landing": "That's why a robotics company building its first service team caught my eye."}
```

```json
{"kind": "question", "id": "QE1", "section": "E", "chain": "QE1",
 "title": "You haven't worked in robotics. Why you?", "target": 60,
 "origin": "risk", "source": "The posting asks for robotics experience.",
 "why": "The screen-out version of the industry gap.",
 "script": "I haven't, and I've learned three industries fast...",
 "beats": ["Own it in one line", "Three industries, learned fast", "What service always needs"]}
```

**section**: the first slide of every section that holds questions. `"cards": true` shows its questions as a page of cards.

**readiness**: the master deck's first slide (id `cover`, section `I`): what's left to write, to lock in, and flagged.

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
      "gates": [{"title": "Ownership", "body": "Lead with what you decided or drove."}],
      "cover": {
        "eyebrow": "Acme Robotics / Service",
        "title": "Head of Field Service",
        "description": ["What this deck is for, in one line."],
        "actions": [{"label": "Start practicing", "go": "QA1", "primary": true}],
        "risk": {"title": "Highest-risk answer: QE1", "body": "Own the industry gap before they raise it."}
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
