# Bishop

A recurring job search that runs itself in Claude. It interviews you once to learn what you're after, then works on a schedule: finding new roles across job boards and company career pages, checking each posting is real and still says what it said, ranking them against what actually matters to you, and handing you a ranked digest.

Works at any career level, from first job to executive search.

## Install

**About a minute. The only typing is Bishop's address.**

1. Open the Claude app on your computer. **First time using Claude Code?** In a chat, type *"Help me set up Claude Code"* and follow the prompts.
2. Click **Customize** in the left sidebar, then the **Plugins** tab. (Plugins are free add-ons for Claude. Bishop is one of them.)
3. In the top right, click **Add**, then **Add marketplace**. Nothing here costs anything.
4. In the box, type `adamhilliard/bishop` and click **Sync**. Type it and click Sync. Don't press Enter, and ignore any repository suggestions that pop up.
5. **Bishop Job Search** appears in the list. Click **Install**.
6. Start a **new conversation in Claude Code**. Bishop won't show up in one that's already open.
7. Say: *"Help me set up a job search."*

**Stuck?** Close Claude, open it again, and try step 6.

**To update later:** open that same Plugins screen and click **Sync**.

> **Don't type `/plugin` commands into the Claude app's chat box.** They only work in a terminal. The steps above need no terminal.

<details>
<summary><b>Bishop Job Search didn't appear? Drop the folder in instead.</b></summary>

Download `bishop.zip` from the [latest release](https://github.com/adamhilliard/bishop/releases/latest) and unzip it into your skills directory:

| | Path |
|---|---|
| **macOS / Linux** | `~/.claude/skills/` |
| **Windows** | `%USERPROFILE%\.claude\skills\` |

You should end up with `.claude/skills/bishop/.claude-plugin/plugin.json`. Fully quit and reopen Claude and it loads with no install step.

</details>

<details>
<summary><b>Using the Claude Code terminal instead (advanced).</b></summary>

Open a terminal, run `claude`, then type:

```
/plugin marketplace add adamhilliard/bishop
```

```
/plugin install bishop@bishop
```

The odd-looking `bishop@bishop` is correct: it's the plugin's name, then where it came from. If the summary says `Run /reload-plugins to activate`, run that. Update later with `/plugin marketplace update`.

To try it for one session without writing anything to your skills directory:

```bash
claude --plugin-dir bishop.zip
```

</details>

## Then start it

Open a new conversation and say:

> Help me set up a job search.

Have your resume or a LinkedIn PDF handy. Bishop asks where to save your files, then walks you through the rest and hands you your first digest.

> **About LinkedIn.** Bishop can read your LinkedIn feed and job alerts through your browser, and it asks you first. **LinkedIn's User Agreement prohibits automated access without its permission, and LinkedIn does restrict accounts it flags for automation.** Bishop keeps it light and read-only, but the risk to your account is real and it is yours to take or skip. Say no during setup and Bishop never touches LinkedIn; it still searches everywhere else.

It'll also ask for a one-time OK so it doesn't have to interrupt you at every step, and so your searches can keep running on schedule while you're away.

**What you installed:**

| | |
|---|---|
| `/bishop:job-search` | The main skill: the setup interview, the recurring search, and a weekly self-check. |
| `/bishop:dashboard` | Optional. Turns your search into a private web dashboard at a bookmarkable link. Run it after your first search. |

You don't need to type either name. Just describe what you want and Claude picks the right one.

## What it touches

Bishop reads a lot and writes only to your machine. **Anything that reaches one of your accounts is off by default, and turned on only when you choose.**

| | What it does |
|---|---|
| **Web search** | Job boards, the hiring systems companies post to directly, and the job pages startup investors keep for their companies. All public pages |
| **Your browser session** *(optional)* | Reads your logged-in job-board feed and alerts, which anonymous search can't see. **Needs Claude's browser extension.** **Browsing only.** It never applies, never messages, never views anyone's profile |
| **Your files** | Writes a folder for your search in the place you started it. Everything stays on your computer |
| **Slack** *(optional)* | Posts your digest to your own DM or a private channel you own. Never a shared channel |
| **Calendar** *(optional)* | Creates events for your interviews and follow-up dates. **Never invites anyone** |
| **Email** *(optional)* | Reads mail from employers already in your list to log applications and rejections (scoped to those). Can also email you your digest. It only ever emails you, never replies, archives, or deletes |

It will never apply to a job, message a recruiter, agree to anything for you, or enter your personal or financial details into a form. It finds and ranks roles and hands you the digest.

Nothing leaves your computer: your profile, your saved roles, and your digest all stay on your machine. No account, no sign-up, no server, and the person who made Bishop receives nothing.

## Uninstall

Open the same Plugins screen where you installed it and click **Uninstall**. Nothing else to undo.

(If you installed from the terminal, `/plugin uninstall bishop@bishop` there does the same thing. If you dropped the folder in by hand, delete the `bishop` folder you unzipped.)

**Your search stays.** The project folder Bishop wrote is yours: plain markdown, readable and useful without the plugin. Removing the tooling doesn't touch it, and the scheduled tasks are yours to delete when you want them gone.

## Credits

Bishop is by **Adam Hilliard** ([linkedin.com/in/adamhilliard](https://linkedin.com/in/adamhilliard)), an HR executive who built it to run his own search and then generalized it so other people could use it, co-built with L&D Expert **Danielle Beram** ([linkedin.com/in/danielle-beram](https://linkedin.com/in/danielle-beram)) and inspired by Recruiting Ops Expert **Loren Boykoff** ([linkedin.com/in/lorenboykoff](https://linkedin.com/in/lorenboykoff)).

Free under the MIT license, included as `LICENSE` in this folder. Use it, change it, pass it on. If it helps you land something, say so; that's the only thing asked in return.

