---
name: interview-prep
description: >-
  Humblebrag, Bishop's interview prep. Builds interactive study decks the candidate drills out loud: a master deck of the questions every interview asks, answered once in their own words, and a deck for each interview, tailored to the posting, the interviewers, and the candidate's real gaps. Each deck is one HTML file that opens in any browser with no account or server; answers save as they type, recordings play back with a transcript, and weak answers loop in a drill. Use this whenever someone has an interview coming up, wants to practice answers, wants a study deck, asks about "Humblebrag," or wants to prep for a role their Bishop search found.
---

# Humblebrag: interview prep

Humblebrag turns an interview into a study deck the candidate practices out loud: the question shows, the answer hides, the timer runs, they say it, then reveal it to check. It's a Bishop module: it reads the candidate's Bishop profile and the roles their search tracks, so they never re-enter their history.

**Two kinds of deck, one set of answers.**
- **The master deck (`core`)** holds the questions every interview asks: opening, behavioral, tough questions, and questions to ask. The candidate answers each one once, in their own words, in the deck itself. Built once, kept forever.
- **An interview deck** is built for one interview: their priorities, the candidate's gaps against them, and questions to ask this company. Where it asks what the master deck asks, it shows the candidate's master answer plus one line tying it to this company, so an answer improved once improves every deck.

> **Never write the candidate's answers for them, and never invent a story.** The master deck's questions start empty: the candidate writes them. An interview deck's tailored scripts are drafts built only from facts the candidate gave you (their resume, profile, and what they tell you), with every number traceable to one of those, and anything uncertain marked `verify`. A plausible invented metric rehearsed out loud is worse than no deck.

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
  Master_Answers.json   the candidate's latest answers, exported from the master deck
```

Build a deck with `python scripts/build_deck.py Interview_Prep/<deck> --master Interview_Prep/Master_Answers.json` (the path to this skill's `scripts/`). It writes `<deck>.html` next to the folder. Leave out `--master` when the file doesn't exist yet. `--check` validates without writing.

## Job 1: build the master deck (once)

**Read first:** `Reference_Profile.md` (career level, current role, full history, target roles) and the resume it came from.

1. **Opening (section A):** tell me about yourself, why are you looking, what are you doing now, what are you looking for, what would you do in your first 90 days. Add the ones their history invites: why did you leave a recent role, a gap, a career change.
2. **Behavioral (section C):** 8 to 12 "tell me about a time" questions covering what their target roles are judged on, calibrated to their career level: teamwork and conflict for anyone; leading people and decisions for managers; strategy, executives, and change for senior leaders.
3. **Tough Questions (section E, `role: "hard"`):** the questions their profile makes likely: level, tenure, a layoff, a gap, a pivot, compensation. Each `origin: "standard"`.
4. **Questions to Ask (section F, `role: "ask"`):** 2 or 3 per theme, from the default themes (`assets/defaults.json`). Each carries its `theme` and `origin: "standard"`, and its `script` is the question as they'd ask it plus what to listen for.

Every question except the questions to ask leaves `script` out: the candidate's own answer goes there, written in the deck. Set `"deck": {"slug": "core", "master": true, "evergreen": true, ...}`, open with a `readiness` slide (id `cover`, section `I`), build it, and open `core.html` for them.

**Tell them how to use it:** in **Study**, click into a question and write the answer the way they'd say it; **+ Add STAR** splits a "tell me about a time" into Situation, Task, Action, Result; **Lock In** marks an answer done; **+ Add Question** adds their own. Readiness shows what's left to write and lock. Then **Export Answers** (bottom of the sidebar) saves `Master_Answers.json`: ask them to save it into `Interview_Prep/`, or find it in their Downloads folder and move it there with their OK.

## Job 2: build a deck for an interview

When an interview is booked. Follow `references/deck-guide.md`, in order:

1. **Collect the inputs in one round:** the posting (from the tracking file, or ask), who's interviewing and their role, the format and date, notes from any earlier round (a recruiter's exact words are the most valuable input there is), and anything they're worried about. Research the company: public, recent, and dated.
2. **Map it before writing it,** in chat: priorities, gaps and risks, research findings, which master answers prove each priority, and the open facts you'd need to write honestly. The candidate corrects the map; only then write the deck.
3. **Write the deck.** Custom first: every priority, risk and finding becomes deck content before any standard question is added. A question that asks what a master question asks carries `"core": "<master question id>"` and a `landing`: one company-specific closing line. Questions to ask cite their source.
4. **Build it** with `--master` so it carries their latest answers, fix every error, read every warning, and open it.

The deck and the field reference are in `references/deck-schema.md`; the answers file is in `references/master-set.md`.

## Keeping the decks in step

The candidate's answers live in their browser as they type, and travel in `Master_Answers.json`. Whenever they've improved their master answers: they export, you rebuild every interview deck with `--master`, and each deck picks up the new answers (a deck's file always yields to newer answers already saved in that browser, never the other way). Rebuild before each interview so the deck carries their latest words.

## Check it before handing it over

- `--check` reports zero errors.
- Every number in a script traces to something the candidate gave you, or carries a `verify`.
- The first sentence of every answer answers the question.
- The tough questions are actually tough: if nothing in the deck is uncomfortable, it isn't finished.
- The deck would fail if handed to a different candidate for this role, or to this candidate for a different company.

Then tell them how to drill: **Study** to build each answer, **Test** to say it out loud and reveal it (Script to learn the shape, then Beats for recall), flag what comes out wrong, and press **D** to loop only those.
