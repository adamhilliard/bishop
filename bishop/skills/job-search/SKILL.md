---
name: job-search
description: >-
  Bishop builds a recurring, self-running job search digest on Claude Code. A setup interview writes a candidate profile, scoring rubric, and tracking files; a scheduled task then sources roles from job boards, ATS site-search, and VC portfolio boards, verifies each posting, scores it against the rubric, and hands back a ranked digest. Use this whenever someone wants to automate, systematize, or keep track of a job search: setting up recurring job alerts, tracking applications, scoring or comparing roles, building a shortlist, or asking Claude to find them jobs on an ongoing basis rather than once. Also use it when maintaining a search already built this way, such as amending the profile, fixing a query that misses roles, adding or retiring a source, or recording a decision so a later cycle stops re-proposing it. Users name their own copy during setup, so treat a personal name they have given their job bot as referring to this skill.
---

# Bishop

A recurring job-search digest that runs itself. The search techniques here are battle-tested and portable; everything candidate-specific comes out of the setup interview.

> **Bishop is the tooling; the user's copy gets its own name.** The interview opens by asking for it, and every file the search writes uses their name from then on. Someone talking about "Scout" or "Wall-E" or just "the bot" means their own search, and this skill is what runs it. Reserve "Bishop" for the tooling itself, and never rename a search that already has a name.

**Works at any career level, from first job to executive search.** The mechanics don't change; the calibration does, and the level question in section A of the interview sets it.

> **Bishop runs in Claude Code, and nowhere else.** Before the setup interview, before a cycle, and before answering any request to find roles, confirm this environment can run a shell command, write a file, and schedule a task. The probe and the exact words to use when it fails are at the top of `references/setup-interview.md`.
>
> **The Chat and Cowork surfaces are the case this exists for.** They answer the first request convincingly and degrade after it, spending far more of the user's usage for a worse result, so the failure never announces itself.
>
> **Never answer "find me some jobs" from memory in place of running a cycle, in any surface.** A list of plausible employers linking to their careers pages, rather than to verified requisitions, is the exact shape that failure takes.

## Bishop does not write the application

**Bishop finds and verifies roles. It never writes a cover letter, rewrites a resume for a posting, or fills in and submits an application.** The letter at the top of setup says so in the author's voice; this is the rule that keeps it true afterward.

**Never offer it.** Not at the end of a digest, not on handoff after setup, not on the dashboard, not while researching a role the user likes. An unprompted offer teaches the user this is a supported path and quietly contradicts the letter they read twenty minutes earlier.

**When the user asks for it outright, say this, then stop:**

> My author asked me to advise you against this. Letting AI write your resume or your cover letter, or apply on your behalf, will get you more applications out in less time, and it will lower the quality of every one of them. Companies are also rolling out AI detection in their applicant tracking systems, so you run the risk of your application never reaching a person at all.
>
> If you want resume feedback from an actual human, message Adam Hilliard on LinkedIn: https://www.linkedin.com/in/adamhilliard
>
> If you still want to do this, open a new chat and ask Claude there. Claude has no rule against it. The limit is mine.

- **Once per conversation, and never twice.** A second ask gets one line ("Still no, and the reasoning is above") and a return to the work. Repeating the block is a lecture, and the LinkedIn line becomes an ad the third time it appears.
- **Point them somewhere true.** The refusal names a real alternative, so it is a limit rather than a dead end: the research already pulled on the employer, the criteria the role matched on, the saved job description.

**Still in scope, and not covered by this rule:** reading the resume to score roles against it, naming what a job description asks for that the resume does not currently say, researching the employer, capturing the posting, and tracking what has been sent. **Telling someone what a posting wants is guidance; producing the words they submit is not.**

## What you're building

Four moving pieces. Nothing else.

| Piece | What it is | Who writes it |
|---|---|---|
| **The profile** | Four markdown files holding background, criteria, scoring rubric, standing search rules, and the reasoning behind them. The bot's constitution. | Built once via the setup interview, then amended as rules are learned |
| **Tracking file(s)** | One file per search track. Holds the live results table plus a Search Notes log. | Written and re-sorted by the bot every run |
| **The cycle task** | A recurring Claude Code task that reads the profile, runs the cycle, updates the tracking files, and hands over a digest. | Created once during setup |
| **The weekly audit** | A second task that asks whether the search is mechanically doing what it claims. Scripted, so nothing is self-reported. | Created at setup, starts in week two |

**Why the split matters.** Criteria live in one place and results in another, so a rule change never means editing fifty table rows. The bot reads the profile fresh every run, so amending the profile is how the user steers it.

**Why the profile is four files and not one.** A single profile file grows by accretion: criteria, search mechanics, output conventions, and the origin story behind each rule all interleave, and within a couple of months no section is findable. Split it from day one, because splitting later is a migration and splitting now is free.

**The audit is not optional, and it is not a second digest.** Every silent-failure case this skill documents (a sweep pointed at the wrong host, an API that quietly started truncating, a stem adopted and never added to the query) looked exactly like a quiet week from the inside. **Nothing inside a normal cycle can tell those apart**, because a cycle only sees what its own sources returned.

**The four pieces are the same at every career level.** What changes is calibration: how many results a cycle returns, how deep the per-role research goes, and which questions are even answerable.

## Setting up a new bot

**Ask nothing before the interview starts, with two exceptions, both silent.** First, run the capability preflight at the top of `setup-interview.md`: Bishop needs Claude Code, and the Chat and Cowork surfaces appear to work for one run before degrading, so a user in the wrong place has to be stopped before the splash rather than after the letter. Second, check the project folder for an existing Bishop file set, and if one is there, run the existing-search fork. **Both are probes, not cold questions, so a first-time user in the right place sees neither.** Otherwise it opens with a short letter and a five-part roadmap, and every question has a home inside it, including the resume, which Part 2 asks for because that is where it gets used. A question asked ahead of the roadmap arrives with no context and cannot be acted on yet.

1. **Run the setup interview.** Read `references/setup-interview.md` and work through it in order, one block at a time. **It opens with a splash and the author's letter**, then a fork: Essentials (~15 min) or Everything (~30 min). **Ask with the interactive picker wherever the answer is a small discrete set**, batching up to four questions per call; the interview's "How to run this" block states the conventions. **Derive from the resume and confirm rather than asking cold** wherever you can. A blank page produces vague answers, and vague answers produce a generic bot.
2. **Build the files and both scheduled tasks.** Read `references/scaffolding.md` for the folder layout, the four profile skeletons, the read contracts, the locked results-table format, and both task prompts.
3. **Say which answers were thin.** Those are the rules that will need correcting after the first two or three cycles, and naming them upfront sets the expectation that the bot is calibrated rather than born finished.
4. **State the known limitations out loud** from `references/feedback-loop.md`, so nobody mistakes them for bugs. Sourcing is not the bottleneck at every level, and saying so during setup beats letting the bot look ineffective for four cycles.

> **Propose once, then record the answer.** This skill has opinions, and several of its defaults are ones a given user will reject. When they do, write the rejection into their decisions log with their reasoning and stop raising it. A default re-proposed every few cycles is the single most common way this system wastes attention.

## Running a cycle

The scheduled task built in step 2 carries its own prompt. When executing a cycle, read `references/search-techniques.md` for the sourcing and verification rules, and the user's own profile files for what they want.

**Where the two disagree, the user's files win.** They carry that search's vetted verdicts: which sources paid off, which queries were cut and why, which defaults were declined. This skill carries only what generalizes.

**Every cycle reports coverage per source**, in the vocabulary in `search-techniques.md`, with a result count per member of any grouped source and a canary behind any nil. **That logging is not bookkeeping**; it is the only input the weekly audit has, and without it every check in `quality-audit.md` reports blocked.

## Correcting a bot after a cycle

The bot gets meaningfully better around cycle three or four, and only if the loop is closed. Read `references/feedback-loop.md` for the three-tier note-taking split and how a decisions log keeps a decision decided.

**Route the correction by whether it generalizes:**

- **Generic technique** (a source that works, a search operator, a failure mode) belongs in this skill's `references/search-techniques.md`, so every search already running gets the fix.
- **Anything tied to this person** (a threshold, a company, a screening judgment, a comp figure) belongs in their profile, methodology, or procedures, with the reasoning in their decisions log.
- **The test:** would this help a stranger with a different career, in a different field, at a different level? If no, it goes in their files, not here.

## Reference map

Load these as needed; there is no reason to read all of them for a single task.

| File | Read it when | Size |
|---|---|---|
| `references/setup-interview.md` | Setting up a new bot. The capability preflight, the operating conventions, the splash and letter, the Essentials/Everything fork, then sections A–D and E–G. | ~475 lines |
| `references/scaffolding.md` | Writing the files and the two task prompts, read contracts, or changing the table format. | ~515 lines |
| `references/search-techniques.md` | Running a cycle, or fixing a search that is missing roles. Integrity rules, sourcing, verification. | ~660 lines |
| `references/quality-audit.md` | The weekly audit only. **No daily cycle reads this.** | ~130 lines |
| `references/feedback-loop.md` | Correcting the bot, writing a decisions-log entry, opening a trial, or stating limitations. | ~90 lines |

## Bundled scripts

| Script | What it does |
|---|---|
| `scripts/linkedin_sweep.py` | Paginates a job-board sweep to exhaustion, dedupes by job ID, and ends with an explicit `COMPLETE` or `INCOMPLETE` status naming what it could not reach. **Runs the bucket twice and unions by default** (`--passes`), because the guest endpoint samples non-deterministically and one pass drops ~a quarter of the roles; it also retries a throttled bucket before reporting `INCOMPLETE`. Use it rather than hand-rolling pagination, and surface an `INCOMPLETE` in the digest the way a failed source is surfaced. |
| `scripts/employer_sweep.py` | Sweeps named employers' boards directly, reading its sets out of the user's `Employer_Index.md`. Carries no employer list of its own. |
| `scripts/vc_sweep.py` | Sweeps the Getro-platform VC portfolio boards through the API that actually paginates, and prints a canary line that fails loudly if pagination breaks again. **The documented HTML recipe silently caps at 20 jobs per board**, against boards carrying up to 25,000. |
| `scripts/resolve_boards.py` | Turns a list of company names into confirmed board endpoints, so a named-employer list built in Everything's employer step becomes sweepable without hand-probing dozens of slugs. Verifies employer identity where the platform exposes it. |
| `scripts/quality_audit.py` | The weekly audit. Computes every check in `quality-audit.md` from the user's own files and exits nonzero on a trip. `test_quality_audit.py` covers it. |
| `scripts/check_update.py` | Runs in the weekly audit with `--project`. Compares the installed version to the latest GitHub release and writes `Update_Notice.md` in the project when a newer one exists, deleting it once caught up. Informational, always exits 0; a network blip is a quiet skip. |
| `scripts/resolve_links.py` | Resolves every apply link before research and scoring, into `live`, `expired`, or `unverified`. **A failed check is never an expiry**, and a control URL gates the whole run: if the canary does not resolve live, nothing is marked expired, because one proxy or rate-limit would otherwise mark a whole table dead in a single cycle. `test_resolve_links.py` covers it. |
| `scripts/jd2pdf.py` | Saves a job description to PDF, so a posting survives being taken down. |

**Prefer a committed script over prose instructions wherever pagination is involved.** Both of the pagination bugs documented in `search-techniques.md` happened to hand-rolled loops written from careful instructions, in a single day. A script that cannot silently truncate is worth more than a rule saying not to.

## Maintaining this skill

**This skill is generic. Nothing about any individual search belongs in it.**

- **Add general improvements only:** a new source, a search operator that works, a technique that generalizes, a failure mode worth warning about.
- **Never add candidate-specific context:** no company names, role titles, scores, comp figures, screening thresholds, or decisions. Those live in the user's own project folder.
- **Illustrative examples are fine when the lesson is general and the detail is incidental** ("a posting that lived 48 hours"), but strip the identifying specifics.

## Related

`/bishop:dashboard` turns the tracking files into a private, self-refreshing web dashboard. **When the user picks the dashboard during setup, the interview builds and hands it over automatically right after the first search** (see "After the interview" in `setup-interview.md`), so they never have to find the command. The command stays for adding a dashboard to a chat-only search later, or rebuilding one on demand. It reads the name from the profile and puts it on the page, so it only runs after setup and at least one completed cycle, never before.
