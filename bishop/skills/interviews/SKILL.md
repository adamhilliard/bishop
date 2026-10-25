---
name: interviews
description: >-
  Bishop's interview practice. Builds interactive decks the candidate drills out loud: a core deck of the questions every interview asks, and one deck per company with the questions that company's interviews will ask, round by round, tailored to the posting, the interviewers, and the candidate's real gaps. The candidate writes every answer themselves, in the deck, and practices saying it. Each deck is one HTML file that opens in any browser with no account or server; answers save as they type, recordings play back (with a transcript if they choose one), and weak answers loop in a drill. Use this whenever someone has an interview coming up, wants to practice for one, wants a study deck or interview prep, or wants to prep for a role their Bishop search found. Users name their own copy of Bishop during setup, so a request to their named job bot for interview help belongs here.
---

# Bishop Interviews

This module gives the candidate the questions an interview will ask and a place to practice answering them: they write each answer in their own words, then drill it out loud with the answer hidden and a timer running. It reads the candidate's Bishop profile and the roles their search tracks, so they never re-enter their history. Every deck wears the same Bishop frame as the dashboard: the robot and their search's name in the top bar.

> **You provide the questions. The candidate writes every answer.** Writing the answer down and drilling it *is* the practice; a drafted script turns prep into memorizing someone else's words. So never write a script, a sample answer, recall cues, a closing line, or advice on what to say. What you do write is everything about the *question*: what will be asked, why they're asking, where it came from (the posting, the recruiter, research, the candidate's own gaps), and the questions the candidate should ask them. If the candidate asks you to draft an answer, decline politely and say why. **Say:**
>
> > I'd rather not write this one for you. An answer in my words would sound like mine when you say it, and interviewers can usually tell. If you tell me a little about what happened, I'll ask you a few questions to help you shape it.

**Two kinds of deck, one set of answers.**
- **The core deck (`core`)** holds the questions every interview asks: opening, behavioral, tough questions, and questions to ask. The candidate answers each once and keeps improving it. Built once, kept forever.
- **A company deck** holds the questions one company's interviews will ask, every round of its process: the role's priorities, the candidate's gaps against them, and questions to ask, aimed at each round's interviewer. Where it asks what the core deck asks, it links to it (`core`) and shows the candidate's core answer until they write a version for this company, so an answer improved once improves every deck.

> **One deck per company, never more, never shared.** A later round updates that company's deck; it never gets a deck of its own. Two companies never share a deck.

> **Say it in plain language.** The candidate never needs to hear "JSON," "slug," "meta," or a script name. They have a *core deck*, a *deck for each company*, and *their answers*. Never call it a master deck: it's one part of their prep, not everything.

**Runs in Claude Code, like the rest of Bishop.** It needs a shell, file access, and Python 3 (the same as the job search). Before anything else, confirm those work; if they don't, say so in one plain sentence and stop.

**No Bishop files in this folder yet?** Then this is a first setup: read `skills/start/SKILL.md` and follow it. The front door shows the welcome and the module picker, and runs this module's setup in its turn.

## Where the files go

In the candidate's Bishop folder (the one holding `Reference_Profile.md`), in a folder named `Interview_Prep`:

```
Interview_Prep/
  core/                 the core deck's source: meta.json, content/*.json
  <company>/            one folder per company, named by its slug (acme-robotics), every round in it
  core.html             the built decks, side by side
  <company>.html
```

Build a deck with `python scripts/build_deck.py Interview_Prep/<deck>` (the path to this skill's `scripts/`). It writes `<deck>.html` next to the folder. `--check` validates without writing; `--round <id>` builds or checks a round other than the one coming up.

**Their answers live in their browser,** saved as they type. A company deck reads their core answers from the same browser, so nothing needs exporting or rebuilding to carry an answer across.

**After changing anything under `engine/`** (the deck page's source, for the maintainer), run `python scripts/build_template.py` to rebuild `assets/template.html`, then rebuild the decks.

## Job 1: build the core deck (once)

**The first time, run `references/setup.md`.** It asks the setup questions in order (the level, how many interviews, recording) and uses this section to build.

### What Bishop gives you, and what it doesn't

Everything here decides *which* questions to ask, never what the answers are. **Don't interview them about their history; Bishop already has it.**

| Input | Where it is | What it decides |
|---|---|---|
| Career level | `Reference_Profile.md` → Career Level: the rung (First-line manager, Senior manager, Director…) and the band (Early career, Mid, Senior / exec) | The behavioral layers (below) |
| Current role, full history | `Reference_Profile.md` → Current Role, Full Career History (period, role, company, highlights) | Opening and tough questions: tenure, gaps, a layoff, a pivot |
| Target roles | `Reference_Profile.md` → Target Roles | Technical questions, and the level they're interviewing *for* |
| Resume bullets | The resume file in their Bishop folder (`Resume.*`), saved at setup with their OK; older setups kept only the history table, so look in `Interview_Prep/` too | Resume questions, quoted word for word |

**No resume file in the folder?** If they told setup they don't have one, never ask again. Otherwise ask once: *"Can you share your resume again? I'll use it to ask about the specific lines an interviewer will point at."* Save it into `Interview_Prep/` with their OK, so the next deck doesn't ask. If they have none, write the resume questions from the Career History highlights and put `"Bishop profile: <role>, <company>"` in `source`.

**Their level is the one they're interviewing for:** the higher of their current rung and their target roles (an explicit level word in a target title counts at face value, as in the job search: Director, VP, Chief; a bare "Head of" doesn't settle it, so go by the rest of the profile). A senior manager targeting director roles gets director-level questions, because that's what those interviewers ask. Older profiles may record only the band; then read the rung from Current Role and the resume. **Never ask for it directly.** State what you read in a short sentence they can correct, as setup's I3 does: *"I'm building this for director-level interviews in customer success."*

### Step 0: how much practice

**Setup asks it** (I4 in `references/setup.md`): how many interviews they expect with each company. Save it as `"rigor"` in the core deck's `deck` settings: 1 to 2 is `light` (about 15 questions), 3 to 4 is `medium` (30 to 40), 5 or more is `heavy` (50 to 70).

`assets/rigor.json` sets how many questions each section gets at each level. They can change it any time ("I have 5 or more interviews," or "switch me to heavy"): **raising it adds questions; lowering it hides only questions they haven't answered. Never remove an answered question.**

### Step 1: the sections

| Section | What goes in it |
|---|---|
| **A. Opening** | In order: Tell me about yourself · Why are you looking · What are you looking for · What are you doing now · What would you do in your first 90 days · then one their history invites (why they left a recent role, a gap, a career change). Light takes 2, medium 4, heavy 6 |
| **R. Resume** | "I see you did this" questions, one per resume bullet (below) |
| **T. Technical** | Knowledge of their field, from their target roles: how they'd approach the core problems of the job ("How do you decide what to build next?" for a product manager, "How do you structure pay at a growing company?" for HR). Field knowledge, never a claim from the resume |
| **C. Behavioral** | From `assets/behavioral.json`, word for word (below) |
| **E. Tough Questions** (`role: "hard"`) | The questions their profile makes likely: level, tenure, a layoff, a gap, a pivot, compensation. Each `origin: "standard"`. **Never repeat an Opening question in any wording:** "Why leave a job that's going well?" is "Why are you looking?" |
| **F. Questions to Ask** (`role: "ask"`) | From the default themes (`assets/defaults.json`), each with its `theme` and `origin: "standard"` |

### Resume questions: "I see you did this"

This is how interviewers use a resume: they point at a line and ask about it. Each bullet is a claim, and the question asks the candidate to back it up.

- **One question per bullet, pointing at the claim, and nothing more:** *"I see you cut onboarding time in half. Walk me through how."* The form stays simple on purpose: how an interviewer digs into a line is hard to predict, so the question just points at it. **Vary the opening** so the section doesn't read like a form letter: *"I see you…"*, *"Your resume says…"*, *"Walk me through…"*, *"Tell me more about…"*, *"How did you…?"* Quote the claim, not necessarily the whole bullet.
- **Put the role and the full bullet word for word in `source`** (`"Acme Robotics, 2021 to now: Cut onboarding time in half by rebuilding the kickoff"`), most recent role first, bullets in resume order.
- **A role is an employer.** Titles held at one company count as one role, with their bullets pooled; a promotion isn't a second job. `rigor.json` sets how many roles and bullets; **the biggest numbers go first**, since interviewers press those hardest: across all of an employer's titles, rank its bullets by the size of the result (retention up seven points, onboarding time cut by 40%, $14M in ARR), with a plain count (a team of 6) below any result, and bullets with no number last, in resume order.

### Behavioral questions: from the bank

Use the bank's wording exactly; it's been reviewed and every question is balanced between successes and failures.

- **Layers by the level they're interviewing for** (above): **Universal** for everyone; **Leading people** for any manager rung (First-line manager, Senior manager, Director, Executive); **Leading the business** when the level they're interviewing for is Functional or technical lead, Director or Executive, even if Career Level records a lower band.
- **How many** follows `rigor.json`: light takes the first question of the six light-marked universal competencies, plus one question per leadership layer they qualify for; medium takes the first question of every competency in their layers; heavy takes two per competency.
- Put the competency's title in `source` (`"Behavioral bank: Conflict"`) and its `tests` line in `why`.

### Step 2: build it and hand it over

Give every question a `why` (what the interviewer is trying to learn, in one sentence), a `target` in seconds (120 for tell me about yourself, 60 to 90 for the rest, 0 for questions to ask) and no `script`. Set `"deck": {"slug": "core", "title": "Core Deck", "brandTitle": "Core deck", "master": true, "evergreen": true, "rigor": "<light, medium or heavy>", "record": "<transcript, audio or off>", "theme": {"accent": "#e2541b"}, "jd": {"none": "Every interview"}}`, sections in the order of the table above, open with a `readiness` slide (id `cover`, section `I`, listed first in `sections`), start each section with its `section` slide, build it, and open `core.html` for them.

**Show them around** with setup's I7 words (`references/setup.md`). **+ Add Question** adds their own question, if they ask how.

## Job 2: build a company's deck, and update it each round

When the first interview with a company is booked. Follow `references/deck-guide.md`, in order. **Map every round of the process at the first build** (the guide lists the usual patterns), so a later round is an update, not a new deck:

1. **Collect the inputs in one round:** the posting (from the tracking file, or ask), who's interviewing and their role, the format and date, notes from any earlier round (a recruiter's exact words are the most valuable input there is), and anything they're worried about. Research the company: public, recent, and dated.
2. **Map it,** in chat: the role's priorities, the candidate's gaps and risks against them, research findings, and which core questions each priority will draw on. The candidate corrects the map; then build the deck.
3. **Write the questions.** Custom first: every priority, risk and finding becomes a question before any standard question is added. A question that asks what a core question asks links to it with `"core"`. Questions to ask cite their source.
4. **Build it,** with the core deck's `record` setting copied into its `deck` settings, fix every error, and open it. It shows their core answers from the browser. If the map added a question to their core deck, rebuild `core.html` too, and tell them before anything else.

**When the next round is booked,** open that company's deck folder, never a new one, and:
1. **Set `deck.round`** to it, with its `date`, `time` and `who` (the interviewer's name and title, which leads the sidebar).
2. **Re-run the map with the earlier round's notes:** re-rank the priorities, put the recruiter's exact words on the hub cards, and add any new risk with the tough question that presses it.
3. **Add what's new for this interviewer:** questions to ask tagged with `rounds`, and a shortlist or a guide if they help.
4. **Rebuild,** then `--check --round` every other round.

The builder puts the round, date and time first on the cover and in the sidebar, so `cover.description` and `deck.sidebar` hold only what's true in every round. Answers, flags and ticks carry over, because it's the same deck.

The deck and the field reference are in `references/deck-schema.md`.

## Keeping the decks in step

**Their answers live in the browser they practice in,** saved as they type. Every company deck reads the core answers from that same browser, so a better core answer shows up everywhere at once. Rebuild a deck only when its questions change.

**When they want a copy, or are moving computers,** offer a PDF of everything: open the deck at its address with `#print-all` added, which lists every question with their answer and opens the print dialog. Tell them to choose "Save as PDF." Don't offer it otherwise.

## Check it before handing it over

- `--check` reports zero errors.
- No `why` hints at what to say. The builder rejects answer fields, but it can't read a `why` that slips one in ("lead with your retention numbers").
- Every custom question cites where it came from, and every fact about the company in a `why` has a source.
- The tough questions are actually tough: if nothing in the deck is uncomfortable to answer, it isn't finished.
- The deck would be wrong for a different candidate for this role, or for this candidate at a different company.

Then tell them how to practice: **Study** to write each answer, **Test** to say it out loud or type it from memory with the answer hidden, then reveal it to check (Answer shows their whole answer, Beats shows the first words of each part), flag what comes out wrong, and press **D** to loop only those.
