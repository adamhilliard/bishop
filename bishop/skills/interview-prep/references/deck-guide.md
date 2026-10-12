# Building an interview deck

How to turn one interview into a deck of questions the candidate will practice answering: collect, map, write the questions, build, check. The fields are in `deck-schema.md`.

> **Questions only.** You write what will be asked and why. The candidate writes every answer, in the deck, and that's the practice. No scripts, sample answers, recall cues, closing lines, or "a strong answer covers…" notes.

## Step 1. Collect the inputs

Ask for everything in one round. Don't interview the candidate about their work history: that's what their Bishop profile and resume are for.

**Already in their Bishop folder (read first)**
- `Reference_Profile.md`: career level, current role, full history, target roles, compensation.
- Their resume, saved in `Interview_Prep/` when the master deck was built. Bishop's setup doesn't keep it; if it isn't there, ask for it as SKILL.md says.
- The tracking file's entry for this role: the posting link, what the search found, and why it scored.
- `Interview_Prep/core/`: the master questions this deck can link to.

**Ask the candidate**
1. Who is interviewing, their title, and how they connect to the role
2. The format, length, date and platform
3. Notes from any earlier round, especially a recruiter screen. **A recruiter's exact words are the most valuable input in the whole build:** they say what the hiring team thinks the job actually is.
4. Anything they know is coming, or have already answered badly
5. What worries them: a requirement they lack, scope they can't claim, comp, a short tenure, a layoff, a career change

**Research the company.** Public, recent and specific: ownership and funding, leadership changes, layoffs, acquisitions, headcount and locations, news from the last 12 months, the interviewer's public profile. Record each finding as a fact, its source and the date you read it. Findings become questions to ask, and context in a question's `why`.

## Step 2. Map it

Read every source, then show the map in chat. Every item gets an id, so the deck can show which questions cover it.

| Map item | Id | What it holds |
|---|---|---|
| **Priorities** (5 to 7) | P1… | What this hire is really being brought in to solve, ranked by what the hiring team said out loud, not the order the posting lists things. Each carries its evidence: a recruiter quote or a posting line. Mark any the candidate can only partly speak to (`partial`). |
| **Gaps and risks** | R1… | Where the interview will press: a requirement they lack, scope they can't claim, the level or tenure or layoff question, the one they've fumbled before, and anything research found that an interviewer will raise. Each carries its source. |
| **Research findings** | F1… | Fact, source, date, and the question it leads to. |
| **Master questions** | master ids | Which master questions each priority will draw on. A priority none of them covers needs a new master question: add it to `core` for the candidate to answer. |

Show the map. Ask for corrections: the candidate will fix the priorities and add what you couldn't know. Then write the questions.

## Step 3. Write the questions

### Custom first

Every map item becomes a question before any standard one is added, and a standard question never takes the place of a mapped risk.

| Map item | Becomes |
|---|---|
| Priority | A question in Their Priorities, and a card on the priority hub quoting the hiring team |
| Partial priority | All of that, plus a tough question if a risk sits behind it |
| Risk | At least one tough question that presses it, listed in `META.risks` with the questions that cover it. The top risk is named on the cover. |
| Research finding | A question to ask, or context in a question's `why`, always with its source |
| Master question | A question with `"core"` pointing at it, worded the way this interviewer would ask it |

### Section recipes

| Section | What goes in it |
|---|---|
| **A. Opening** | Tell me about yourself, why this company, why now, worded for this interview. Link each to its master question with `core`. |
| **B. Their priorities** | One question per priority, asked the way this hiring team would ask it. A second angle on a priority is a question of its own. |
| **C. Behavioral** | Tell me about a time, aimed at the priorities. Link each to the master question it draws on (`core`). |
| **E. Tough Questions** (`role: "hard"`) | At least two custom questions that press mapped risks, each with its `origin` and `source`. Then the master deck's tough questions that apply, linked with `core`. Every risk in `META.risks` is covered. |
| **F. Questions to ask** (`role: "ask"`) | 3 or 4 custom questions from the posting, the recruiter or research, each citing its `source`, then 2 or 3 standard ones. Close with one that surfaces their doubts while the candidate can still answer them. Every one carries a `theme`. |
| **N. Evidence notes** | The research findings, each with its source and date, and anything the candidate should confirm before the interview. |

**Tags.** Every question in Tough Questions or Questions to Ask carries an `origin`: `standard`, `jd` (the posting), `recruiter`, `research` or `risk`. Anything but `standard` also cites its `source`. The deck shows the tag on each card.

**Themes.** Questions to ask are grouped by theme: Role History, Team and Reporting, Scope, Stability and Runway, The First Year, Leadership and Culture, Terms, Before You Leave (`assets/defaults.json`). A company topic that fits none gets its own in `META.deck.askThemes` (`{id, code: "C1", title, testing}`).

### The `why` on each question

One sentence on what the interviewer is trying to learn, and, for a custom question, what in the posting, the recruiter's words or research makes it likely. It's context for the candidate, never a hint at the answer: "They named two failed hires in this seat; they're testing whether you'll last" is context. "Lead with your retention numbers" is an answer.

### Timing

Give each question a `target` in seconds, so the timer tells the candidate when they're running long: 60 to 90 for opening, priority and behavioral questions, 30 to 60 for a narrower question, 0 (no timer) for questions to ask. Roughly 150 spoken words a minute.

### What to produce

Size it to the candidate's rigor (`"rigor"` in the master deck's settings), then to the round:

| Rigor | Questions |
|---|---|
| Light | About 10 |
| Medium | About 20 |
| Heavy | About 30 |

A recruiter screen or 30-minute round takes the lower end; a full loop with a hiring manager or panel the higher. Linked questions count toward the total, so a priority the master deck already covers costs nothing extra to practice.

**Resume questions:** pick the resume bullets this role makes relevant, and link each to its master question (`core`), worded the way this interviewer would ask it.

### Writing the files

One folder per deck, named by its slug, inside `Interview_Prep/`: a `meta.json`, and one file per section in `content/` (`00-intro.json`, `10-opening.json`, `20-priorities.json`, `30-behavioral.json`, `40-hard.json`, `50-ask.json`, `90-notes.json`). Every section that holds questions starts with a `section` slide. The fields are in `deck-schema.md`.

## Step 4. Build and check

```
python <this skill>/scripts/build_deck.py Interview_Prep/<slug> --master Interview_Prep/Master_Answers.json
```

The builder checks before it writes: duplicate ids, missing fields, any follow-up (a second angle is a question of its own), a tough question or question to ask with no `origin`, a custom one with no `source`, and a question to ask with no `theme`. Fix every error.

**Then check by hand:**
- No question carries a script, beats, or a landing line.
- Every risk in `META.risks` has a tough question, and the top one is on the cover.
- Every company fact in the deck has its source and date in the evidence notes.
- The deck would be wrong for a different candidate for this role, or for this candidate at a different company. If it wouldn't, it isn't tailored yet.

Open the deck for them, then tell them how to practice: **Study** to write each answer in their own words (linked questions start from their master answer, which they can rewrite for this interview), **Test** to say it out loud with the answer hidden and reveal it to check, flag what comes out wrong, and press **D** to loop only those.
