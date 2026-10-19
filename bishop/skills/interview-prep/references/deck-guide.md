# Building an interview deck

How to turn one interview into a deck: collect, map, write, build, check. The fields are in `deck-schema.md`.

## Step 1. Collect the inputs

Ask for everything in one round. Don't interview the candidate about their work history: that's what their Bishop profile and resume are for.

**Already in their Bishop folder (read first)**
- `Reference_Profile.md`: career level, current role, full history, target roles, compensation.
- The tracking file's entry for this role: the posting link, what the search found, and why it scored.
- `Interview_Prep/core/` and `Master_Answers.json`: the master questions and their answers.

**Ask the candidate**
1. Who is interviewing, their title, and how they connect to the role
2. The format, length, date and platform
3. Notes from any earlier round, especially a recruiter screen. **A recruiter's exact words are the most valuable input in the whole build:** they say what the hiring team thinks the job actually is.
4. Anything they know is coming, or have already answered badly
5. Known risks: a requirement they lack, scope they can't claim, comp, a short tenure, a layoff, a career change
6. Their target compensation and start date, if the round may ask

**Research the company.** Public, recent and specific: ownership and funding, leadership changes, layoffs, acquisitions, headcount and locations, news from the last 12 months, the interviewer's public profile. Record each finding as a fact, its source and the date you read it. Research shapes questions to ask and landing lines; the candidate asks about what you found rather than asserting it.

Build with what you get. A missing fact becomes a `verify` note, never a guess.

## Step 2. Map it before you write it

Read every source, then show the map in chat. Don't write answers yet. Every item gets an id, so the deck can show which slides cover it.

| Map item | Id | What it holds |
|---|---|---|
| **Priorities** (5 to 7) | P1… | What this hire is really being brought in to solve, ranked by what the hiring team said out loud, not the order the posting lists things. Each carries its evidence: a recruiter quote or a posting line. **Mark any the candidate can only partly speak to (`partial`).** |
| **Gaps and risks** | R1… | The answers most likely to go badly: a requirement they lack, scope they can't claim, the level or tenure or layoff question, the one they've fumbled before, and anything research found that an interviewer will raise. Each carries its source. |
| **Research findings** | F1… | Fact, source, date, and what it changes in the deck. |
| **Master answers** | master ids | Which master questions prove each priority. A priority no master answer covers needs a new master question first: add it to `core`, and ask the candidate to answer it. Never fill it with an invented story. |
| **Open facts** | | What you'd need to ask to write honestly: numbers without a source, dates, who owned what. |
| **Gates** | | Five or six pass conditions for this interview. Default: Ownership (lead with what they decided or drove), Evidence (one number or scope marker), Compression (land it in the time), Plain speech, **Honest scope** (names every partial priority and the top risk, and how to own each), and one named for the company (connect to their situation). |

Show the map. Ask for corrections: the candidate will fix scope, drop a story, and hand you numbers you didn't have. Then write the deck.

## Step 3. Write the deck

### Custom first

Every map item becomes deck content before any standard question is added, and a standard question never takes the place of a mapped risk.

| Map item | Becomes |
|---|---|
| Priority | A question in Their Priorities, and a card on the priority hub quoting the hiring team |
| Partial priority | All of that, plus a line in the Honest scope gate, and a tough question if a risk sits behind it |
| Risk | At least one tough question that presses it, listed in `META.risks` with the slides that cover it. The top risk is the cover's "Highest-risk answer." |
| Research finding | A question to ask, a landing line, or a `verify` note. Never an assertion in a script without its source. |
| Master answer | A question with `"core"` pointing at it and a `landing` line for this company |

### Section recipes

| Section | Recipe |
|---|---|
| **A. Opening** | Tell me about yourself, why this company, why now. Link each to its master question with `core`; the `landing` lands it on this company. |
| **B. Their priorities** | One question per priority. A partial priority leads with the honest boundary, then the transferable evidence, then how the candidate would close the gap. |
| **C. Behavioral** | Tell me about a time: each links to the master answer that proves it (`core`) with a `landing` line. |
| **E. Tough Questions** (`role: "hard"`) | At least two custom questions that press mapped risks, each with its `origin` and `source`. Then the master deck's tough questions that apply here, linked with `core`. Every risk in `META.risks` is covered. |
| **F. Questions to ask** (`role: "ask"`) | 3 or 4 custom questions from the posting, the recruiter or research, each citing its `source`, then 2 or 3 standard ones. Close with one that surfaces their doubts while the candidate can still answer them. Every one carries a `theme`. |
| **V. Company Specific** | Optional drills for this interview only: the gaps to own before they're probed, said from memory, then revealed. |
| **N. Evidence notes** | Confirmed facts, open items, and every research finding with its source and date. |

**Tags.** Every question in Tough Questions or Questions to Ask carries an `origin`: `standard`, `jd` (the posting), `recruiter`, `research` or `risk`. Anything but `standard` also cites its `source`. The deck shows the tag on each card.

**Themes.** Questions to ask are grouped by theme: Role History, Team and Reporting, Scope, Stability and Runway, The First Year, Leadership and Culture, Terms, Before You Leave (`assets/defaults.json`). A company topic that fits none gets its own in `META.deck.askThemes` (`{id, code: "C1", title, testing}`).

### Voice

Spoken, first person, the way the candidate actually talks. Contractions are fine; sentences vary in length. No em dashes. No "passionate about," "wear many hats," "hit the ground running." No "it's not X, it's Y." If the candidate gave you a writing sample, match its cadence; if their profile records how they want to sound, follow it.

**Every answer states its point in the first sentence,** then supports it. Setup before the answer is the most common failure in a real interview, and a deck that rehearses setup teaches the failure.

### Behavioral answers use STAR

A "tell me about a time" answer goes Situation, Task, Action, Result, after a one-sentence headline that answers the question. Setup (Situation and Task) under 30% of it; Action at least 40%, said with "I"; the Result carries a number, then stops. The candidate builds these in the master deck (**+ Add STAR**); an interview deck links to them.

### Length

Roughly 150 spoken words a minute.

| Target | Words |
|---|---|
| 30s | 70 to 80 |
| 60s | 140 to 155 |
| 90s | 210 to 225 |

Opening and behavioral answers: 60 to 90 seconds. Follow-ups: 30 to 45. Questions to ask: no target (`0`). The builder warns above 165 words a minute and fails above 190: cut the script, never raise the target.

### Evidence rules

These matter more than the writing.

- Every number traces to something the candidate gave you. No invented metrics, no rounded-up scope, no borrowed industry statistics.
- Anything uncertain gets a `verify`. Leave it open rather than filling it with a plausible number.
- Separate what the candidate owned from what a partner owned from what the company did.
- Facts about the employer come only from sources you can name, with the date, in the evidence notes. A thin or old finding becomes a question to ask, not a statement.

### What to produce

A full loop (45 to 60 minutes with a hiring manager or panel): 20 to 30 questions, most with 2 or 3 follow-ups, the priority hub, and evidence notes. A recruiter screen or 30-minute round: 10 to 14 questions.

### Writing the files

One folder per deck, named by its slug, inside `Interview_Prep/`: a `meta.json`, and one file per section in `content/` (`00-intro.json`, `10-opening.json`, `20-priorities.json`, `30-behavioral.json`, `40-hard.json`, `50-ask.json`, `90-notes.json`). Small files keep each write small and let you fix one section without rewriting the rest. Every section that holds questions starts with a `section` slide. The fields are in `deck-schema.md`.

## Step 4. Build and check

```
python <this skill>/scripts/build_deck.py Interview_Prep/<slug> --master Interview_Prep/Master_Answers.json
```

The builder checks before it writes: duplicate ids, missing fields, a follow-up with no parent, a tough question or question to ask with no `origin`, a tailored one with no `source`, a question to ask with no `theme`, and a script over 190 words a minute. Fix every error; read every warning.

**Then check by hand:**
- Every risk in `META.risks` has a tough question, and the top one is on the cover.
- Every number traces to the candidate, or carries a `verify`.
- Read three scripts out loud against their targets.
- The deck would fail if handed to a different candidate for this role, or to this candidate for a different company. If it wouldn't, it isn't tailored yet.

Open the deck for them, then tell them how to drill: **Study** to build each answer, **Test** to say it out loud and reveal it (Script to learn the shape, then Beats for recall), flag what comes out wrong, and press **D** to loop only those.
