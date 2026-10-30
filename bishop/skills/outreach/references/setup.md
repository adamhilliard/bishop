# Outreach setup

**The front door (`skills/start/SKILL.md`) runs this,** last, after job search and interviews when they picked those. It builds the board. About 10 minutes.

**Every rule in "How to run this" in `skills/job-search/references/setup-interview.md` applies:** one question at a time, pickers for small sets, `Say:` lines close to verbatim, plain words. Read the profile job search wrote and never re-ask what it holds.

- **Setup doesn't wait for LinkedIn.** Ask for the export first, then the questions that don't need it, then build the board. They upload the export into the board when it arrives, so it never passes through the chat.
- **No time tracking.** No quiet-conversation flags, no timers, no reminders, nothing scheduled, and nothing in the job search digest.
- **LinkedIn only.** Every contact comes from their LinkedIn export. Other contact files carry names without titles or message history, so they can't be grouped.

## O0. About you (only when they skipped job search and interviews)

**Ask job search's shared basics in its exact words,** from sections A and B of `setup-interview.md`, then its Permissions picker. Save the answers in the profile's shared sections, the way job search's setup does.

## O1. What this is

**Say:**

> Now your network. Sometimes a connection can open a door for you that an application can't. If you extract your LinkedIn data (I'll show you how), I'll give you a board that sorts your contacts into groups worth contacting and tracks who you've spoken with.
>
> Nothing in this workflow requires I log into LinkedIn. Everything stays on your computer.

## O2. Ask LinkedIn for your data

**Say:**

> Here's how to get your LinkedIn data. It takes about a minute to ask for:
> - On LinkedIn, click **Me** (your photo at the top).
> - Click **Settings & Privacy**.
> - Click **Data privacy**.
> - Click **Get a copy of your data**.
> - Choose the option to pick specific data.
> - Tick **Connections**.
> - Tick **Messages**.
> - Click **Request archive**.
> - Enter your LinkedIn password if it asks.
>
> LinkedIn emails you your data, usually within a day. Tell me when you've finished the request, and we'll set up your board while you wait.

- **LinkedIn's menus change.** If what they see doesn't match, describe the equivalent step on the page they're on.
- **No LinkedIn account, or they'd rather not?** Outreach is built on the export and can't run without it. **Say:**

  > Outreach works from your LinkedIn data, so I can't set it up without it. If you change your mind, say "set up outreach."

  Save nothing, and hand back to the front door's step 8.

## O3. Who counts as warm

**Picker,** single-select, header `Warm`. **Say:**

> While LinkedIn gets that ready, one quick choice. Who should count as someone you're warm with?

| Option | Description |
|---|---|
| **Any real conversation, any time** (Recommended) | Anyone you've messaged back and forth with, however long ago. Old ties still open doors |
| **Within the last 3 years** | Only conversations from the last three years |
| **Within the last year** | Only recent conversations |

**Save it** in `Outreach/settings.json` (`any`, `3y` or `1y`), as `references/data-format.md` shows.

## O4. Your groups

**Confirm the groups by their rules.** You never hold the contacts, so the counts appear in the board once the export is uploaded. **Say:**

> Here's how your board will sort your network:
> - **Warm:** anyone you've messaged back and forth with
> - **Recruiters:** recruiters, sourcers and anyone at a search firm
> - **HR / People:** HR and People titles
> - **Executives:** C-suite, VPs, general managers and managing directors
> - **Entrepreneurs:** founders, owners and the self-employed
> - **Everyone Else:** kept in a searchable list, off the board
>
> Your tabs will show in this order, warm first. Anyone who fits two groups lives in the first one.
>
> Want to drop any of these, add a group of your own, or change the order? For example "anyone at a gaming studio," or "people I worked with at {{a past employer}}."

- **A group of their own:** turn the description into a rule (a company list, title words, a range of dates when they connected, a spreadsheet of names they drag into the chat, or anyone at a company in their job search) and say it back. Loop until they say "looks good."
- **Names stay off the chat.** A hand-picked group is a spreadsheet they drag in. Save it into `Outreach/` without reading it; the build script reads it. Never ask them to paste names, and never go looking for the file.
- **The past-employer example** uses a company from their career history when job search has one; otherwise use "people I worked with at my last job."
- **Save the groups** in `Outreach/segments.json`, then run `build_page.py --check`.

## O5. Build the board and open it

**Build it** with `python scripts/build_page.py <their Bishop folder>`, then **open `Outreach/outreach.html` in their browser. Say:**

> Here's your board. It's saved at {{full path to outreach.html}}, and only you can see it. Bookmark it so you can come back.
> - **When LinkedIn's email arrives,** download the file, open the board and press **Upload Export**. The board reads it right there; the file never comes to me.
> - **Each tab is one of your groups.** Press **Up Next** when you want to reach out.
> - **In Motion** shows everyone you're talking to.
> - **Note it** each time you reach out or hear back.
> - **Your board saves in this browser as you go.**

- **They upload the file; you never go looking for it.** Never search Downloads or anywhere else on their computer.
- **The board keeps names, titles, companies, profile links and message counts.** Message text and email addresses are skipped on upload.
- **A newer export later:** they press Upload Export again. Stages, notes and logs stay with everyone still in their network.
- **Clearing the browser's data clears the contacts and the board.** Uploading the export again brings back the contacts, not the board.

## O6. Done

**If they skipped job search and interviews,** ask job search's Name question first (section D of `setup-interview.md`, same words and options). It's always the last question of the first module.

**Hand back to the front door's step 8,** which asks about the next module they picked, or goes to the closing note.
