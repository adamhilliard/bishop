# The answers file (Master_Answers.json)

> Copied from Humblebrag's MASTER_FORMAT.md by export_bishop.mjs. The candidate's Export Answers button writes this file; build_deck.py --master embeds it.

One person's whole Humblebrag in one JSON file: their competencies and questions, their stories and resume lines, every deck's settings and content, and every answer they've written. It's what an export writes and an import reads, and what a deck with no server behind it loads.

> **Version 1.** A reader refuses a file whose `format` or `version` it doesn't know. A later version adds fields; it never renames or repurposes one.

## Top level

| Field | What it holds |
|---|---|
| `format` | Always `"humblebrag.master"` |
| `version` | `1` |
| `exported` | When the file was written (ISO 8601) |
| `bank` | The competency framework and the stories (below) |
| `decks` | Every deck, keyed by its slug (`core`, `acme`) |

## `bank`

| Field | Each item |
|---|---|
| `groups` | `{id, title, sort}`: the sections competencies sit in (for example: Executive, Craft) |
| `competencies` | `{id, group, code, title, testing, questions[], technical[], sort}`. `questions` and `technical` are the questions asked about it, one per entry. A Core question's id comes from them: `q-<competency>-<slug of the question>` (`t-` for technical), the slug cut at 60 characters |
| `stories` | `{id, title, place, headline, situation, task, action, result, *_cue, result_value, result_unit, sources, open_items, status, resume_role, resume_line, resume_order, resume_competency, resume_question, resume_pivot, competencies[]}` |

**A story's home is a Core question:** the question named by `resume_question` under the competency `resume_competency`. Its words live in that question's answer, so the STAR fields here are the older copy, used only for a story with no Core answer. `resume_competency: "hidden"` keeps a story off every deck.

> The resume fields (`resume_*`) are on hold for a redesign. Carry them through unchanged.

## `decks.<slug>`

| Field | What it holds |
|---|---|
| `master` | `true` on the one master question set (Core). Company decks read its answers |
| `folder` | Where the deck's files live, when that differs from the slug |
| `meta` | The deck's `meta.json` |
| `files` | `[{name, json}]`: the deck's content files, in build order |
| `answers` | Keyed by question id (below) |
| `edits` | `[{id, field, before, after}]`: text edits made on the page and not yet written into the files. `field: "__added"` is a question added from the page (`after` is the question as JSON); `"__deleted"` removes one |

## `answers.<question id>`

| Field | What it holds |
|---|---|
| `sections` | `[{name, text}]`: the answer, in named sections (Answer, or Situation, Task, Action, Result) |
| `locked` | `true` when the answer is locked in (done) |
| `org` | The company the answer's card is tagged with, or `"__none"` |
| `story` | The story picked to answer it, or `"__own"` for your own example |
| `text` | An answer typed before sections existed |
| `star` | A STAR answer saved before sections existed |
| `extra` | Any other saved part, kept as text so nothing is lost |
