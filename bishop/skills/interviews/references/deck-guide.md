# Building a company's deck

How to turn one company's interview process into a deck of questions the candidate will practice answering: collect, map, write the questions, build, check. **One deck per company covers every round,** and two companies never share a deck. The fields are in `deck-schema.md`.

> **Questions only.** You write what will be asked and why. The candidate writes every answer, in the deck, and that's the practice. No scripts, sample answers, recall cues, closing lines, or "a strong answer covers…" notes.

## Step 1. Collect the inputs

Ask for everything in one round. Don't interview the candidate about their work history: that's what their Bishop profile and resume are for.

**Already in their Bishop folder (read first)**
- `Reference_Profile.md`: career level, current role, full history, target roles, compensation.
- Their resume, saved in `Interview_Prep/` when the master deck was built. Bishop's setup doesn't keep it; if it isn't there, ask for it as SKILL.md says.
- The tracking file's entry for this role: the posting link, what the search found, and why it scored.
- `Interview_Prep/core/`: the master questions this deck can link to.

**Ask the candidate**
1. Who is interviewing, their title, and how they connect to the role, and who they expect in every round after this one
2. The format, length, date and platform
3. Notes from any earlier round, especially a recruiter screen. **A recruiter's exact words are the most valuable input in the whole build:** they say what the hiring team thinks the job actually is.
4. Anything they know is coming, or have already answered badly
5. What worries them: a requirement they lack, scope they can't claim, comp, a short tenure, a layoff, a career change

**Research the company.** Public, recent and specific: ownership and funding, leadership changes, layoffs, acquisitions, headcount and locations, news from the last 12 months, the interviewer's public profile. Record each finding as a fact, its source and the date you read it. Findings become questions to ask, and context in a question's `why`.

## Step 2. Map it

Read every source, then show the map in chat. Every item gets an id, so the deck can show which questions cover it.

| Map item | Id | What it holds |
|---|---|---|
| **Priorities** (5 to 7) | P1… | What this hire is really being brought in to solve, ranked by what the hiring team said out loud, not the order the posting lists things. Each carries its evidence: a recruiter quote or a posting line. A hiring manager's words relayed by a recruiter are still a quote; attribute them as relayed ("Priya, via the recruiter"). Mark any the candidate can only partly speak to (`partial`). |
| **Gaps and risks** | R1… | Where the interview will press: a requirement they lack, scope they can't claim, the level or tenure or layoff question, the one they've fumbled before, and anything research found that an interviewer will raise. Each carries its source. |
| **Research findings** | F1… | Fact, source, date, and the question it leads to. |
| **The loop** | round ids | Every round of the process, mapped now: who's in it, their seat, what they decide, and what they'll test. Unknown rounds come from the usual pattern (below), named by seat. |
| **Master questions** | master ids | Which master questions each priority will draw on. A priority none of them covers needs a new master question: add it to `core` for the candidate to answer, in the section it belongs to (a resume bullet goes in Resume, even past the rigor's count, since this interview needs it), and say so in the map ("I'll add one question to your master deck: …"). |

**The usual rounds, when nobody has said:**

| Process | Rounds |
|---|---|
| Search firm | The associate's screen, the search lead, the hiring manager, then a panel or the CEO |
| In-house recruiter | Recruiter or talent screen, the hiring manager, a panel of peers, an executive |
| Warm intro | The introducer, the decision-maker, the team |

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
| **A. Opening** | Tell me about yourself, why this company, why now, worded for this interview. Link each to its master question with `core` ("why now" is "Why are you looking?"), except "why this company": it's different for every company, so the master deck has none to link to. Give it its `source` (the posting or the research behind it). |
| **B. Their priorities** | One question per priority, asked the way this hiring team would ask it. A second angle on a priority is a question of its own. **Resume questions go here too:** each one points at a bullet that answers a priority ("Our clinics take 90 days to go live. You cut time-to-live from 60 to 35 days. How?"). |
| **C. Behavioral** | Tell me about a time, aimed at the priorities. Link each to the master question it draws on (`core`). |
| **E. Tough Questions** (`role: "hard"`) | At least two custom questions that press mapped risks, each with its `origin` and `source`. Then the master deck's tough questions that apply, linked with `core`. Every risk in `META.risks` is covered. |
| **F. Questions to ask** (`role: "ask"`) | 3 or 4 custom questions from the posting, the recruiter or research, each citing its `source`, then 2 or 3 standard ones. Close with one that surfaces their doubts while the candidate can still answer them. Every one carries a `theme`. A question meant for one round's interviewer carries `rounds` (`["hm"]`); one any round can answer carries none. |
| **N. Evidence notes** | The research findings, each with its source and date, and anything the candidate should confirm before the interview. |

**Tags.** Every question in Tough Questions or Questions to Ask carries an `origin`: `standard`, `jd` (the posting), `recruiter`, `research` or `risk`. Anything but `standard` also cites its `source`. The deck shows the tag on each card.

**Themes.** Questions to ask are grouped by theme: Role History, Team and Reporting, Scope, Stability and Runway, The First Year, Leadership and Culture, Terms, Before You Leave (`assets/defaults.json`). A company topic that fits none gets its own in `META.deck.askThemes` (`{id, code: "C1", title, testing}`).

### The `why` on each question

One sentence on what the interviewer is trying to learn, and, for a custom question, what in the posting, the recruiter's words or research makes it likely. It's context for the candidate, never a hint at the answer: "They named two failed hires in this seat; they're testing whether you'll last" is context. "Lead with your retention numbers" is an answer.

### Timing

Give each question a `target` in seconds, so the timer tells the candidate when they're running long: 60 to 90 for opening, priority and behavioral questions, 30 to 60 for a narrower question, 0 (no timer) for questions to ask. Roughly 150 spoken words a minute.

### What to produce

Size it to the candidate's rigor, then to the round. **Read rigor from the master deck's settings** (`"rigor"` in `Interview_Prep/core/meta.json`), never from `Reference_Profile.md`: the job search has its own setting with the same name, and it has nothing to do with practice.

| Rigor | Questions |
|---|---|
| Light | About 18 |
| Medium | About 25 |
| Heavy | About 35 |

A recruiter screen or 30-minute round takes the lower end; a full loop with a hiring manager or panel the higher. **The count is a guide, the coverage is the rule:** every priority and every risk gets its question even when that runs past the number. Linked questions count toward the total, so a priority the master deck already covers costs nothing extra to practice.

**Resume questions:** pick the resume bullets this role makes relevant, put each in Their Priorities, and link it to its master question (`core`), worded the way this interviewer would ask it.

### Rounds

**List every round in `meta.deck.rounds` at the first build, and pick the one coming up with `meta.deck.round`.** Each round has an `id`, a `label`, and `ask` (the name in "Questions for …"), plus `date` and `time` once booked. Two optional extras help when the round calls for them:
- **A `guide`** (`{title, body}`): who this interviewer is and what they'll test. It shows first on the cover.
- **A `shortlist`** slide naming its `round`: the 8 to 12 questions that interviewer is most likely to ask, reached from a tab.

**When the next round comes, update this deck:** never start a second one for the same company.
1. **Set `deck.round`** to it, with its `date`, `time` and `who` (the interviewer's name and title, which leads the sidebar).
2. **Re-run the map with the earlier round's notes:** re-rank the priorities, put the recruiter's exact words on the hub cards, and add any new risk with the tough question that presses it.
3. **Add what's new for this interviewer:** questions to ask tagged with `rounds`, and a shortlist or a guide if they help.
4. **Rebuild,** then `--check --round` every other round.

The builder puts the round, date and time first on the cover and in the sidebar, so `cover.description` and `deck.sidebar` hold only what's true in every round. Answers, flags and ticks carry over, because it's the same deck.

### Writing the files

One folder per deck, named by its slug, inside `Interview_Prep/`: a `meta.json`, and one file per section in `content/` (`00-intro.json` holds the `cover` and the priority `hub`, in section `I`, listed first in `sections` as `{"id": "I", "title": "Overview"}`; then `10-opening.json`, `20-priorities.json`, `30-behavioral.json`, `40-hard.json`, `50-ask.json`, `90-notes.json`). Every section that holds questions starts with a `section` slide. The fields are in `deck-schema.md`.

## Step 4. Build and check

```
python <this skill>/scripts/build_deck.py Interview_Prep/<slug> --master Interview_Prep/Master_Answers.json
```

Then `--check --round <id>` for every other round in `deck.rounds`, since a build checks only the round it builds.

The builder checks before it writes: duplicate ids, missing fields, any answer text (a script, cues, a closing or pivot line), any follow-up (a second angle is a question of its own), a tough question or question to ask with no `origin`, a custom one with no `source`, a question to ask with no `theme`, a risk no tough question covers, no top risk on the cover, a link that lands nowhere (a `core` link to a master question that isn't there, a hub card or cover button pointing at a missing question), an answers file the deck page couldn't read, and a question written for this interview that doesn't say where it came from. Fix every error, and treat every warning as one unless you can say why it doesn't apply. **If you added a question to the master deck, rebuild `core.html` too.**

**Then check by hand:**
- No `why` hints at what to say. The builder rejects answer fields, but it can't read a `why` that slips one in.
- Every company fact in the deck has its source and date in the evidence notes.
- The deck would be wrong for a different candidate for this role, or for this candidate at a different company. If it wouldn't, it isn't tailored yet.

Open the deck for them. **If you added a master question, say so first:** "I added one question to your master deck, about …; answer it there and this deck shows your answer." Then tell them how to practice: **Study** to write each answer in their own words (linked questions start from their master answer, which they can rewrite for this interview), **Test** to say it out loud with the answer hidden and reveal it to check, flag what comes out wrong, and press **D** to loop only those.
