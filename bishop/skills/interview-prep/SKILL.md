---
name: interview-prep
description: >-
  Humblebrag, Bishop's interview prep. Builds interactive study decks the candidate drills out loud: a master deck of the questions every interview asks, and a deck for each interview with the questions that interview will ask, tailored to the posting, the interviewers, and the candidate's real gaps. The candidate writes every answer themselves, in the deck, and practices saying it. Each deck is one HTML file that opens in any browser with no account or server; answers save as they type, recordings play back with a transcript, and weak answers loop in a drill. Use this whenever someone has an interview coming up, wants to practice for one, wants a study deck, asks about "Humblebrag," or wants to prep for a role their Bishop search found.
---

# Humblebrag: interview prep

Humblebrag gives the candidate the questions an interview will ask and a place to practice answering them: they write each answer in their own words, then drill it out loud with the answer hidden and a timer running. It's a Bishop module: it reads the candidate's Bishop profile and the roles their search tracks, so they never re-enter their history.

> **You provide the questions. The candidate writes every answer.** Writing the answer down and drilling it *is* the practice; a drafted script turns prep into memorizing someone else's words. So never write a script, a sample answer, recall cues, a closing line, or advice on what to say. What you do write is everything about the *question*: what will be asked, why they're asking, where it came from (the posting, the recruiter, research, the candidate's own gaps), and the questions the candidate should ask them. If the candidate asks you to draft an answer, say this deck works best when the words are theirs, and offer to ask them questions that help them find their own.

**Two kinds of deck, one set of answers.**
- **The master deck (`core`)** holds the questions every interview asks: opening, behavioral, tough questions, and questions to ask. The candidate answers each once and keeps improving it. Built once, kept forever.
- **An interview deck** holds the questions one interview will ask: about the role's priorities, the candidate's gaps against them, and questions to ask this company. Where it asks what the master deck asks, it links to it (`core`) and shows the candidate's master answer until they write a version for this interview, so an answer improved once improves every deck.

> **Say it in plain language.** The candidate never needs to hear "JSON," "slug," "meta," or a script name. They have a *master deck*, *interview decks*, and *their answers*.

**Runs in Claude Code, like the rest of Bishop.** It needs a shell, file access, and Python 3 (the same as the job search). Before anything else, confirm those work; if they don't, say so in one plain sentence and stop.

## Where the files go

In the candidate's Bishop folder (the one holding `Reference_Profile.md`), in a folder named `Interview_Prep`:

```
Interview_Prep/
  core/                 the master deck's source: meta.json, content/*.json
  <company>/            one folder per interview deck, named by its slug (acme-robotics)
  core.html             the built decks, side by side
  <company>.html
  Master_Answers.json   the candidate's answers, exported from the master deck
```

Build a deck with `python scripts/build_deck.py Interview_Prep/<deck> --master Interview_Prep/Master_Answers.json` (the path to this skill's `scripts/`). It writes `<deck>.html` next to the folder. Leave out `--master` when the file doesn't exist yet. `--check` validates without writing.

## Job 1: build the master deck (once)

**Read first:** `Reference_Profile.md` (career level, current role, full history, target roles) and **the resume itself**, so a resume question can quote the bullet exactly as the interviewer will read it. They decide *which* questions to ask, never what the answers are.

### Step 0: ask how much practice they want

Before building anything, ask one question, and save the answer as `"rigor"` in the master deck's `deck` settings:

> **How much practice do you want?**
> - **Light:** the questions nearly every interview asks. About 15, for a quick tune-up or a first screen.
> - **Medium** *(recommended)*: a full prep for most interviews. About 30 to 40.
> - **Heavy:** everything, for a final round or a big career move. About 50 to 70.

`assets/rigor.json` sets how many questions each section gets at each level. They can change it any time ("switch me to heavy"): **raising it adds questions; lowering it hides only questions they haven't answered. Never remove an answered question.**

### Step 1: the sections

| Section | What goes in it |
|---|---|
| **A. Opening** | In order: Tell me about yourself · Why are you looking · What are you looking for · What are you doing now · What would you do in your first 90 days · then one their history invites (why they left a recent role, a gap, a career change). Light takes 2, medium 4, heavy 6 |
| **R. Resume** | "I see you did this" questions, one per resume bullet (below) |
| **T. Technical** | Knowledge of their field, from their target roles: how they'd approach the core problems of the job ("How do you decide what to build next?" for a product manager, "How do you structure pay at a growing company?" for HR). Field knowledge, never a claim from the resume |
| **C. Behavioral** | From `assets/behavioral.json`, word for word (below) |
| **E. Tough Questions** (`role: "hard"`) | The questions their profile makes likely: level, tenure, a layoff, a gap, a pivot, compensation. Each `origin: "standard"` |
| **F. Questions to Ask** (`role: "ask"`) | From the default themes (`assets/defaults.json`), each with its `theme` and `origin: "standard"` |

### Resume questions: "I see you did this"

This is how interviewers use a resume: they point at a line and ask about it. Each bullet is a claim, and the question asks the candidate to back it up.

- **One question per bullet, quoting it, and nothing more:** *"Your resume says you cut onboarding time in half. Walk me through how."* Put the role and the bullet word for word in `source` (`"Acme Robotics, 2021 to now: Cut onboarding time in half"`), most recent role first, bullets in resume order. `rigor.json` sets how many roles and bullets; **bullets with a number go first**, since interviewers press those hardest.

### Behavioral questions: from the bank

Use the bank's wording exactly; it's been reviewed and every question is balanced between successes and failures.

- **Layers by career level** (from their profile): **Universal** for everyone; **Leading people** for anyone who manages people (first-line manager and up); **Leading the business** for the senior or executive band.
- **How many** follows `rigor.json`: light takes the first question of the six light-marked universal competencies, plus one question per leadership layer they qualify for; medium takes the first question of every competency in their layers; heavy takes two per competency.
- Put the competency's title in `source` (`"Behavioral bank: Conflict"`) and its `tests` line in `why`.

### Step 2: build it and hand it over

Give every question a `why` (what the interviewer is trying to learn, in one sentence) and no `script`. Set `"deck": {"slug": "core", "master": true, "evergreen": true, "rigor": "medium", ...}`, open with a `readiness` slide (id `cover`, section `I`), build it, and open `core.html` for them.

**Tell them how to use it:** in **Study**, click into a question and write the answer the way they'd say it; **+ Add STAR** splits a "tell me about a time" into Situation, Task, Action, Result; **Lock In** marks an answer done; **+ Add Question** adds their own. Readiness shows what's left to write and lock. Then **Export Answers** (bottom of the sidebar) saves `Master_Answers.json`: ask them to save it into `Interview_Prep/`, or find it in their Downloads folder and move it there with their OK.

## Job 2: build a deck for an interview

When an interview is booked. Follow `references/deck-guide.md`, in order:

1. **Collect the inputs in one round:** the posting (from the tracking file, or ask), who's interviewing and their role, the format and date, notes from any earlier round (a recruiter's exact words are the most valuable input there is), and anything they're worried about. Research the company: public, recent, and dated.
2. **Map it,** in chat: the role's priorities, the candidate's gaps and risks against them, research findings, and which master questions each priority will draw on. The candidate corrects the map; then build the deck.
3. **Write the questions.** Custom first: every priority, risk and finding becomes a question before any standard question is added. A question that asks what a master question asks links to it with `"core"`. Questions to ask cite their source.
4. **Build it** with `--master` so their master answers show, fix every error, and open it.

The deck and the field reference are in `references/deck-schema.md`; the answers file is in `references/master-set.md`.

## Keeping the decks in step

The candidate's answers live in their browser as they type, and travel in `Master_Answers.json`. Whenever they've improved their master answers: they export, you rebuild every interview deck with `--master`, and each deck picks up the new answers (a deck's file always yields to newer answers already saved in that browser, never the other way). Rebuild before each interview.

## Check it before handing it over

- `--check` reports zero errors.
- No question carries a script, beats, or a landing line you wrote.
- Every custom question cites where it came from, and every fact about the company in a `why` has a source.
- The tough questions are actually tough: if nothing in the deck is uncomfortable to answer, it isn't finished.
- The deck would be wrong for a different candidate for this role, or for this candidate at a different company.

Then tell them how to practice: **Study** to write each answer, **Test** to say it out loud with the answer hidden and reveal it to check (Script shows their answer, Beats shows the first words of each part), flag what comes out wrong, and press **D** to loop only those.
