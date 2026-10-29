---
name: start
description: >-
  Bishop's front door. Runs once, the first time someone sets Bishop up in a folder: checks this is the right place to run, handles an older Bishop setup already in the folder, shows the welcome and the author's letter, lets the person pick which modules they want, then runs each chosen module's setup in order. The job-search skill hands every first setup here; the interviews skill does too when no Bishop files exist yet. Use it directly when someone says "let's keep going" to resume a Bishop setup they paused, or asks to add a Bishop module they skipped.
---

# Bishop: the front door

**Every first setup starts here.** People still start Bishop by saying *"Help me set up a job search."* That reaches the job-search skill, which hands a first setup to this one. Nothing about how people start Bishop changes.

**Ask one thing at a time and wait for the answer.** Every rule in "How to run this" in `skills/job-search/references/setup-interview.md` applies here and in every module's setup: pickers wherever the answer is a small set, the recommended option first, `Say:` lines close to verbatim, plain words, derive then confirm, never celebrate the occasion.

**Modules always run in this order: job search, interviews, outreach.** One at a time: the first module they picked runs start to finish, including its own permissions and its first result. Only then does Bishop ask about the next one. A module they didn't pick is skipped.

> **Offer only the modules this copy of Bishop ships.** A module ships when its skill is in this plugin (`skills/job-search/`, `skills/interviews/`, `skills/outreach/`). Never offer, describe, or promise one that isn't there.

## 1. Can this run here? (silent)

**Run the capability probe** in "Before anything: can this actually run here?" in `skills/job-search/references/setup-interview.md`, exactly as written, including its words when a probe fails.

- **All pass: say nothing.** Go to step 2.
- **Scheduling is checked only when job search needs it.** Interviews alone never schedules anything, so a setup with only interviews that can't schedule still goes ahead.

## 2. Is there already a Bishop here?

**Look for every file any version of Bishop wrote, not just today's.** No Bishop files at all: go straight to the splash.

| What to look for | Written by |
|---|---|
| `Reference_Profile.md`, `Methodology.md`, `Operating_Procedures.md`, `Decisions_Log.md`, `Audit_Log.md`, `Employer_Index.md`, `Weekly_Check.md`, `Update_Notice.md` | Job search, every version |
| `Tracking_*.md`, `Archived_*.md`, `Index_*.md`, `Notes_*.md` | Job search's tracking files and their splits |
| `dashboard.html` | Dashboard |
| `Archived_Setup_*` folders | Earlier "archive and start fresh" runs |
| `Postings/`, `Resume.*` | Job search captures; the saved resume |
| `Interview_Prep/` | Interviews |
| `Outreach/` | Outreach |
| `Bishop_Setup.md` | This front door |
| Scheduled tasks whose prompt names this folder | Job search's cycle and weekly check |

**When anything is found, picker,** single-select, header `Existing setup`. **Say:**

> You already have {{what's here, in plain words: "a job search called Wall-E"}} in this folder. What would you like to do?

| Option | Description |
|---|---|
| **Add a module** (Recommended when the files are from 2.0) | Keep everything and set up {{the modules they don't have yet}} |
| **Delete everything and start over** (Recommended when the files are from before 2.0) | I remove every Bishop file, folder and scheduled task here, then set you up from scratch |
| **Archive it and start fresh** | I move the old files into a dated archive folder, then set everything up from a blank slate |
| **Change what I have** | Keep it and just take your changes; I skip the setup |

- **Files from 2.0 carry a format line** (`<!-- bishop-format: ... -->`) on line 1. Files without one are from an earlier version, so delete-and-start-over leads, first in the list.
- **Leave out "Add a module"** when every module this copy ships is already set up.
- **A separate setup in a new folder** isn't one of the four (a picker holds four); someone who asks for it gets it, run into the new folder they name.
- **Add a module:** skip the splash and the letter (they've seen them) and go to step 5, offering only what's missing.
- **Change what I have:** don't run any setup. Route to "Correcting a bot after a cycle" in the job-search skill, take the change, and stop.
- **Archive it and start fresh:** move every Bishop file and folder in the table into `Archived_Setup_{{DATE}}/` inside this folder, say in one line that it's moved, then go to the splash. **Build only from this setup's answers and the resume.** Don't read the archived files, and don't carry any remembered detail from an earlier chat into the new ones.

**Delete everything and start over:** confirm first, with exactly what goes. **Say:**

> Here's everything I'll remove from this folder: {{n}} files, {{n}} folders{{, including your old archive}}, and {{n}} scheduled tasks that run your search. Anything else in the folder stays. This can't be undone.
> {{If they have a dashboard:}} Your dashboard page online stays up; I can show you where to delete it afterward.

**Then picker,** single-select, header `Delete`: *Yes, delete it all* · *No, go back*. No recommended option.

- **On yes:** delete the files and folders in the table, delete the scheduled tasks whose prompt names this folder, and remove only Bishop's entries from `.claude/settings.json` (any other entries stay). Each deletion asks their permission; Bishop's permission list never includes deleting, and stays that way.
- **Then say in one line that it's done,** and go to the splash as a first setup.
- **Never delete anything outside the table,** and never anything outside this folder.
- **On "No, go back":** show the `Existing setup` picker again.

## 3. The splash (no input)

**Print the boot lines with a short beat between each, then the banner.**

```
> waking up .............. ok
> loading job sensors ..... ok
> dodging ghost jobs ...... ok
```
```
════════════════════════════════════════════════════════

                  W E L C O M E   T O

 ██████╗   ██╗  ███████╗  ██╗  ██╗   ██████╗   ██████╗ 
 ██╔══██╗  ██║  ██╔════╝  ██║  ██║  ██╔═══██╗  ██╔══██╗
 ██████╔╝  ██║  ███████╗  ███████║  ██║   ██║  ██████╔╝
 ██╔══██╗  ██║  ╚════██║  ██╔══██║  ██║   ██║  ██╔═══╝ 
 ██████╔╝  ██║  ███████║  ██║  ██║  ╚██████╔╝  ██║     
 ╚═════╝   ╚═╝  ╚══════╝  ╚═╝  ╚═╝   ╚═════╝   ╚═╝     

            your personal job-hunting robot

                         °   °
                         │   │
                         ╭───╮
                       \ │•‿•│ /
                        \╰─┬─╯/
                         ┌─┴─┐
                         │═══│
                         └┬─┬┘
                         (o)(o)

════════════════════════════════════════════════════════
```

## 4. The letter

**Lead with the title line below, then say the letter verbatim.** It is the only fully verbatim block in Bishop, and it is signed by a person: don't paraphrase it, extend it, or add a line after it.

**A Note From Bishop's Author**

> Whether you're looking for your next opportunity, or are in between roles, I built this AI agent to help you find jobs at companies that match your skills and interests. I hope this makes your search just a little bit easier.
>
> This agent helps you find new job postings, practice for interviews, and identify who in your network can open doors for you. As someone who has reviewed 1,000s of resumes, AI-generated ones are easy to spot, and several modern applicant tracking systems now have AI spam filters in place. Beyond that, hiring is, at its core, human. When Bishop finds you a role you like, take the few extra minutes you saved and go through it by hand. You will land more interviews.
>
> This agent is under continuous development and improvement. Send me a message on LinkedIn if you have feedback, so we can all improve this tool together.
>
> -Adam Hilliard
> linkedin.com/in/adamhilliard

> **Once, at setup, and nowhere else.** Never on a cycle, never in a digest, never on the dashboard, never in a module's own setup.

## 5. How I work

**Say:**

> Hi, I'm Bishop. I'm here to help you find a few new... angles (haha...get it?) for your job search. I can find new roles that match what you're looking for, verify they're real, and rank them for you. I can build you a deck to help you practice for interviews. I can also help you organize the people you already know, so the right conversations don't go cold. You pick which of those you want. Each one takes between 5 and 30 minutes to set up.

## 6. Pick your modules

**Picker,** multi-select, header `Modules`. **Say:**

> Which of these would you like? Pick any. You can add the others later just by asking.

| Option | Description |
|---|---|
| **Find new roles** (Recommended) | Bishop searches the internet for roles that meet your criteria, on a schedule you set, and serves them to you in a digest |
| **Practice for interviews** | Bishop builds you a deck of questions interviewers commonly ask, then you can write and practice your answers |
| **Work your network** | Bishop teaches you how to extract your LinkedIn contacts, and helps you organize them into groups worth contacting |

- **Job search is the recommended, first option.** The picker can't pre-tick a box, so "Recommended" and first place are how it reads as the default.
- **The dashboard isn't here.** It's offered inside job search's setup.
- **No "None" option.** If they submit with nothing chosen, ask once which one they'd like to start with.
- **Write `Bishop_Setup.md` now** (step 9), with every picked module `not started`.

## 7. Run the modules, in order

**Job search, then interviews, then outreach,** skipping any they didn't pick. Each runs completely, with nothing from another module mixed in.

| Module | Its setup | About |
|---|---|---|
| Job search | `skills/job-search/references/setup-interview.md`, from "Choose your setup" through "After the interview" | 15 to 30 minutes |
| Interviews | `skills/interviews/references/setup.md` | 5 minutes |
| Outreach | `skills/outreach/references/setup.md` | 10 minutes |

- **Job search's own closing note doesn't run** when this front door started it. Step 10 replaces it.
- **The shared basics belong to job search** (the resume, the one review line, the Team and Level pickers, target roles), asked in its sections A and B. When they skipped job search, the first module that runs asks those same questions in job search's exact words, plus job search's Permissions picker, before its own steps.
- **Save the resume file** into the Bishop folder with their OK (`Resume.<ext>`), so interviews can ask about its lines.
- **Mark each module `done` in `Bishop_Setup.md`** when it finishes.

## 8. Ask about the next module

**When a module finishes and they picked another, picker,** single-select, header `Next`. **Say:**

> {{The module just finished, in plain words}} has been set up. Do you want to set up the {{next one they picked}} module now? It takes about {{its time}}.

| Option | Description |
|---|---|
| **Yes, set it up now** (Recommended) | We keep going |
| **Later** | I'll save your place. Say "let's keep going" whenever you're ready |

- **Yes:** run that module start to finish, as in step 7, then ask again for the next one.
- **Later:** mark the rest `later` in `Bishop_Setup.md` and go to the closing note.
- **No module left that they picked:** skip the question and go to the closing note.
- **The name is the last question of the first module that runs,** so someone who stops after one module still has it. Job search asks it at the end of its questions (after G on Everything). If they skipped job search, the first module asks job search's Name question (section D, same words and options) at its end. Use the name in every file written from then on.

## 9. Save where setup stands (silent)

**`Bishop_Setup.md`** in the Bishop folder, format line first:

```markdown
<!-- bishop-format: setup 1 -->
# Bishop setup

Started: {{YYYY-MM-DD}}

| Module | State |
|---|---|
| Job search | done |
| Interviews | later |
```

- **States:** `not started`, `done`, `later`.
- **"Let's keep going"** reads it and runs the first module that isn't `done`, in the order of step 7, skipping the splash and the letter.
- **Adding a module later** adds its row.

## 10. Closing note

**Say:**

> You're set. {{If they set up interviews:}} When you confirm an interview, tell me: "I have an interview with {{company}}," and I'll build that company's deck.
