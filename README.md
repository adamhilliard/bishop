# Bishop

Bishop is an AI agent that runs recurring job searches in Claude. One setup interview saves your profile and scoring rules onto your own computer. A scheduled task then sources roles from job boards, applicant tracking systems, and the job pages startup investors keep for their companies. Bishop then checks each posting is real, scores it against what you actually want, and hands you a ranked digest.

When an interview lands, Bishop builds a deck you practice out loud: the question shows, the answer hides, the timer runs. You answer the questions every interview asks once, in your own words, and each company gets one deck, tailored to the posting and the people you'll meet in every round.

Free, MIT licensed, and it works at any career level, from first job to executive search.

## Install

**You need the [Claude](https://claude.com) desktop app.** It's free to download. Have your resume or a PDF of your LinkedIn profile handy.

Prefer pictures? The [install guide on adamhilliard.com](https://adamhilliard.com/bishop) walks through the same steps with screenshots.

1. Open Claude. **First time using Claude Code?** In a chat, type *"Help me set up Claude Code"* and follow the prompts.
2. Click **Customize** in the left sidebar, then the **Plugins** tab. (Plugins are free add-ons for Claude. Bishop is one of them.)
3. In the top right, click **Add**, then **Add marketplace**.
4. In the box, type `adamhilliard/bishop` and click **Sync**. Type it and click Sync. Don't press Enter, and ignore any repository suggestions that pop up.
5. **Bishop Job Search** appears in the list. Click **Install**.
6. Start a **new conversation in Claude Code**. It won't appear in one that's already open. Don't use plain Claude chat for Bishop's work; performance degrades quickly there.
7. Say: *"Help me set up a job search."*

**Nothing happening?** Close Claude, open it again, and try step 6.

**To update later:** open the same Plugins screen and click **Sync**.

> **Don't type `/plugin` commands into the Claude app's chat box.** They only work in a terminal (see the last section below). The steps above need no terminal.

<details>
<summary><b>Bishop Job Search didn't appear? Drop the folder in instead.</b></summary>

Download `bishop.zip` from the [latest release](https://github.com/adamhilliard/bishop/releases/latest) and unzip it into your skills directory:

| | Path |
|---|---|
| **macOS / Linux** | `~/.claude/skills/` |
| **Windows** | `%USERPROFILE%\.claude\skills\` |

You should end up with `.claude/skills/bishop/.claude-plugin/plugin.json`. Fully quit and reopen Claude and it loads as `bishop@skills-dir`, no install step.

</details>

<details>
<summary><b>Using the Claude Code terminal instead</b></summary>

Open a terminal, run `claude`, then type:

```
/plugin marketplace add adamhilliard/bishop
```

```
/plugin install bishop@bishop
```

`bishop@bishop` is correct: the plugin's name, then the marketplace it came from. If the install summary says `Run /reload-plugins to activate`, run that. Update later with `/plugin marketplace update`.

To try it for one session without writing anything to your skills directory:

```bash
claude --plugin-dir bishop.zip
```

</details>

## Start a search

In a new conversation, say:

> Help me set up a job search.

**Setup saves your files in a folder on your computer.** Just tell it where you’d like them; if you’re not sure, tell Bishop and it will pick a spot for you.

**The setup interview takes about fifteen minutes.** Have your resume or a PDF of your LinkedIn profile handy.

**LinkedIn is optional, and you should know the risk before you say yes.** Bishop can read your LinkedIn feed and job alerts through your browser. LinkedIn's User Agreement prohibits automated access without its permission, and LinkedIn does restrict accounts it flags for automation. Bishop keeps it light and read-only, but the risk to your account is real. Setup asks you first; say no and Bishop never touches LinkedIn and still searches everywhere else.

**You can rename it.** The last question of your first setup is whether you'd like to call Bishop something else, and every file it writes uses the name you pick.

## What you get

| | |
|---|---|
| `/bishop:job-search` | The main skill. Setup interview, search techniques, verification rules, the recurring cycle, and a weekly quality audit that checks whether the search is mechanically doing what it claims. |
| `/bishop:dashboard` | Optional. Turns your tracking files into a private web dashboard at a bookmarkable link that refreshes every cycle. Run it after your first cycle. |
| `/bishop:interviews` | Interview practice. Builds your core deck (the questions every interview asks, answered in your own words) and a tailored study deck for each interview. Each deck is one file that opens in any browser. Say *"Help me prep for my interview with…"* |

You don't need to type any of these names. Describe what you want, or use the name you gave your search, and Claude picks the right one.

## What it touches

**Bishop reads public information and writes only to your machine.** Everything that reaches an account of yours is off by default but can be turned on one at a time during setup: your browser session, Slack, calendar, and read-only email intake.

> **The browser session is the one with a prerequisite.** It needs Claude's browser extension installed and signed in, and it's worth having, since your logged-in job-board feed and alerts are invisible to anonymous search. Setup checks and tells you if it's missing.

**It will not apply to a job, message a recruiter, accept terms on your behalf, or enter personal or financial details into a form.** It finds and ranks roles and hands you the list.

**Nothing is sent anywhere.** Your profile, your tracked roles, and your digest stay on your machine and in your own repo. There is no account, no telemetry, and no server. The author receives nothing.

> Full detail on every integration and its scope is in [the plugin's own README](bishop/README.md), which is also what lands in your skills folder after install.

## Author and license

By **Adam Hilliard** ([adamhilliard.com](https://adamhilliard.com), [linkedin.com/in/adamhilliard](https://linkedin.com/in/adamhilliard)), a fractional CPO / COO who built it to run his own search and then generalized it so other people could use it, co-built with L&D Expert **Danielle Beram** ([linkedin.com/in/danielle-beram](https://linkedin.com/in/danielle-beram)) and inspired by Recruiting Ops Expert **Loren Boykoff** ([linkedin.com/in/lorenboykoff](https://linkedin.com/in/lorenboykoff)).

MIT, see [LICENSE](LICENSE). Use it, change it, pass it on, with the copyright line kept. If it helps you land something, say so; that's the only thing asked in return.

Building on it or cutting a release? See [MAINTAINING.md](MAINTAINING.md).
