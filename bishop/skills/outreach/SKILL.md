---
name: outreach
description: >-
  Bishop's outreach board. Sorts the people someone already knows on LinkedIn into groups worth contacting (warm connections, recruiters, HR and people leaders, executives, entrepreneurs, and groups of their own) and gives them a private board, on their own computer, to track who they've reached out to. It reads only the LinkedIn data export they download themselves, inside the board, so their contacts never pass through the chat. Use this whenever someone wants to work their network, find who they know at a company, organize their LinkedIn connections, or keep track of networking conversations during a job search. Users name their own copy of Bishop during setup, so a request to their named job bot about their network belongs here.
---

# Bishop Outreach

This module turns someone's LinkedIn connections into a board they can work: groups in tabs, a stage for each person, and a note each time they reach out or hear back. **It tracks outreach only.** The person writes every message themselves.

> **You never see their contacts.** The board reads the LinkedIn export in their browser and keeps everything there. Never ask them to paste names, titles or messages into the chat, never open the export yourself, and never look for files on their computer: Downloads or anywhere else. **The one exception is a hand-picked group** (below): they drag a spreadsheet in, you save it into the Outreach folder without reading it, and the build script reads it.

> **Never draft a message.** If they ask you to write outreach for them, decline politely and say why. **Say:**
>
> > I'd rather not write this one for you. Messages written by AI usually read that way, and that can hurt your chances with the people you're reaching out to. Tell me who it's for and what you're hoping for, and I'll ask you a few questions to help you find your own words.

> **No time tracking.** No reminders, no timers, no "gone quiet" flags, nothing scheduled, and nothing in the job search digest. It isn't a CRM.

**Runs in Claude Code, like the rest of Bishop.** It needs a shell, file access and Python 3. Before anything else, confirm those work; if they don't, say so in one plain sentence and stop.

**No Bishop files in this folder yet?** Then this is a first setup: read `skills/start/SKILL.md` and follow it. The front door shows the welcome and the module picker, and runs this module's setup in its turn.

## Where the files go

In the person's Bishop folder (the one holding `Reference_Profile.md`, when they have a job search), in a folder named `Outreach`:

```
Outreach/
  segments.json     their groups: which defaults, their own, and the order
  settings.json     who counts as warm
  outreach.html     the board
  <names file>      a hand-picked group's spreadsheet, only if they made one
```

**Their contacts and their board (stages, notes, logs) live in their browser,** the way interview answers do. Rebuilding the page keeps both. Clearing the browser's data clears both; uploading the export again brings back the contacts, not the board.

Build the board with `python scripts/build_page.py <their Bishop folder>` (the path to this skill's `scripts/`). It writes `Outreach/outreach.html`. `--check` validates the groups without writing. The file shapes are in `references/data-format.md`.

**What the build reads from other modules,** all optional (`CONTRACTS.md` lists each part):

| From | What | For |
|---|---|---|
| Job search's profile | The Bishop name, the accent color, the companies in their career history | The top bar, the board's color, and "worked there" |
| Job search's tracking files and employer index | The companies in their search | The "in your job search" group type |

Without a job search, the board still works: the default Bishop name and color, no "worked there," and no job-search group.

## Job 1: set it up (once)

**Run `references/setup.md`.** The front door runs it in its turn. It asks for the LinkedIn export, asks who counts as warm, confirms the groups, writes `segments.json` and `settings.json`, builds the board and shows them around. It doesn't wait for LinkedIn: they upload the export into the board when it arrives.

## Job 2: change the groups

**When they want to add, drop, rename or reorder a group,** change `segments.json`, run `--check`, rebuild, and tell them to reload the board. Their stages and notes stay.

**A group of their own:** turn their words into one of these rules, then say the rule back in plain words before you save it.

| They say | The rule |
|---|---|
| "Anyone at a gaming studio" | A company list. Research it once and save the names |
| "Anyone in finance" | Words in a job title |
| "People I connected with at my last job" | A range of dates when they connected |
| "These specific people" | A hand-picked list: a spreadsheet they drag into the chat, saved into `Outreach/` unread |
| "Anyone at a company I'm applying to" | Anyone at a company in their Bishop job search |

- **Each person lives in one group,** the first that matches in tab order. Other matches show as tags.
- **You can't say how many people a rule catches.** The board shows the counts once they reload it.

## Job 3: everything else

- **A newer LinkedIn export:** they press Upload Export in the board. No rebuild. Stages, notes and logs stay with everyone still in their network.
- **Who counts as warm:** change `settings.json` and rebuild.
- **"Why is this person in this group?"** The board says, on each person: the rule that put them there. Point them to it; you can't see the person.
- **Their name or color changed in job search,** or their search added companies: rebuild, so the board picks it up.
- **A copy of their board:** it lives only in their browser, and there's no export. Say so plainly.
