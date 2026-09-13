# Maintaining Bishop

Notes for the maintainer. Users need `README.md` at the root and `bishop/README.md` after install; neither needs anything here.

## Layout

```
.claude-plugin/marketplace.json      makes this repo an installable marketplace
bishop/                              the plugin
├── .claude-plugin/plugin.json
├── LICENSE                          a copy; marketplace installs only copy the plugin dir
├── README.md                        what recipients read
└── skills/
    ├── job-search/                  /bishop:job-search
    │   ├── SKILL.md
    │   ├── references/              interview, scaffolding, techniques, quality audit, feedback loop
    │   └── scripts/                 sweep, audit, and capture tooling
    └── dashboard/                   /bishop:dashboard
        └── SKILL.md
build_package.py                     builds the handoff zip
```

## Distribution

**The repo is the marketplace.** `.claude-plugin/marketplace.json` at the root points at `./bishop`. Most users add it from the desktop app (Customize → Plugins → Add → Add marketplace → type `adamhilliard/bishop` → Sync → Install). Terminal users run `/plugin marketplace add adamhilliard/bishop` then `/plugin install bishop@bishop`. Updates reach them when they click **Sync** again or run `/plugin marketplace update`, gated on the `version` field in `plugin.json`, so **bump it on every release or nobody gets the change.**

> **`/plugin` does not run in the desktop app's chat box.** It answers "isn't available in this environment." Every install doc must say so, and must lead with the desktop Plugins screen. Two rounds of published instructions got this wrong (2026-09-02).
>
> **Open question, desktop marketplace add for non-owners.** A tester who does not own the repo reported that after adding the marketplace, Bishop Job Search did not appear in the list. Whether the desktop picker accepts a public repo the user doesn't own is undocumented, and it can't be tested from the maintainer's account (the picker autocompletes the maintainer's own repos). Until a non-owner confirms the desktop path end to end, every install doc carries the `bishop.zip` drop-in as the fallback.

**`python build_package.py` still builds `bishop.zip`**, which stays useful for two things: attaching to a GitHub Release for people not installing from a marketplace, and `claude --plugin-dir bishop.zip` for a one-session trial. The zip is not committed; it's a release asset.

> **Verify before announcing.** `claude plugin validate ./bishop`, then load the plugin and confirm both skills come up as `/bishop:job-search` and `/bishop:dashboard`.
>
> **`validate` only reads `plugin.json`.** It checks the manifest and never opens a skill file, so a plugin with broken skill frontmatter validates clean, installs clean, lists clean, and then does nothing when someone asks it for a job search. That shipped once already (`af31`, "fix the job-search skill's frontmatter, which failed to parse"). **Only loading it actually proves it loads.**

> **Don’t install Bishop on the machine running the live search.** The skill description tells Claude to treat a personally-named job bot as referring to Bishop, so an installed copy captures the live search’s requests. That rules out the obvious check (`/plugin marketplace add .`) on the maintainer’s own machine, which is why this step keeps getting skipped.
>
> **Use the zip instead**, from a scratch folder. It loads for one session and writes nothing to the skills directory:
>
> ```bash
> claude --plugin-dir bishop.zip
> ```
>
> Ask it to set up a job search. If the interview opens, the skills loaded. Close the window and it's gone.
>
> **`claude` may not be on `PATH`.** On the maintainer’s Windows machine it lives at `%USERPROFILE%\.local\bin\claude.exe`. Worth remembering before concluding the CLI isn’t installed.

## Version numbering

`MAJOR.MINOR.PATCH`, and **the patch digit is the default.** Most releases are a patch.

| Digit | Use it for |
|---|---|
| **Patch** (1.4.**1**) | Fixes, clarifications, and additions inside an existing question, technique, or file |
| **Minor** (1.**5**.0) | A new skill, a new interview question, or a change that makes searches already running behave differently |
| **Major** (**2**.0.0) | A file layout that existing searches have to migrate to |

**When in doubt it is a patch.** Bumping the minor digit every time something improves burns through the numbering and stops telling anyone which releases actually matter.

> **Judge the version by the size and substance of the change, not the calendar.** The one-week window is a guideline, not a hard rule: two small fixes shipped days apart are usually both patches, and burning a minor on each would make the number meaningless. But a genuinely large change earns its minor even inside the week. A new skill, a rewritten interview, or anything that reshapes how running searches behave is a minor whenever it ships. **Let the window steer the close calls, and let size win outright.**

> Both `bishop/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` carry the version. They have to agree.

## Releasing

1. Port whatever the live search has learned that generalizes. The test: would this help a stranger with a different career, in a different field, at a different level?
2. Bump `version` in `bishop/.claude-plugin/plugin.json`, **and the matching `version` in `.claude-plugin/marketplace.json`.** Two files carry it: the plugin manifest gates updates, the marketplace entry is what the Desktop plugin card shows.
3. **Update the Release history below. Every release, including patches.**
4. `python build_package.py`.
5. Tag the commit and cut a GitHub Release with `bishop.zip` attached, so the "no marketplace" path in `bishop/README.md` resolves.

> **The history is organized by minor, and a patch updates the minor's entry rather than opening its own.** A new minor opens a new `###` heading; every patch after it appends its line to that heading. **The rule is that no release lands without the history reflecting it**, which is what 1.4.0 through 1.4.2 broke: three releases shipped against a history that stopped at 1.3.0.

Candidate-specific detail never lands here: no company names, role titles, scores, comp figures, or screening thresholds. Illustrative examples are fine when the lesson is general and the identifying detail is stripped.

## Where this came from

Extracted from a live executive job search that has been running daily since July 2026. Nearly every technique in `references/search-techniques.md` started as a correction after a real cycle got something wrong: a sweep that silently returned 6% of its result set, a posting that gained a hard credential requirement without notice, an ATS API that reported a live requisition as missing.

**That search is a separate repository and this one does not read from it.** Fixes flow here as releases rather than as a live dependency, so a lagging copy here means an unreleased change, not a broken link.

## Attribution rules

**Attribution lives in six places, and nowhere else on purpose:** the root README, the plugin README recipients read at install, the `author` field in `plugin.json`, a one-line header in each bundled script, **a short signed letter shown once at the top of setup**, and **the refusal Bishop gives when asked to write an application** (1.6.2), which names the author and links his LinkedIn as the human-review alternative.

> **The sixth place is the only one that can fire more than once**, which is why the skill caps it at one per conversation. A second ask gets a one-line "still no" with no name and no link. Uncapped, it is an ad that appears every time someone asks a reasonable question. Setup also writes a single credit line into the profile it generates, which lands once in each user's own repo.

**The letter is the only verbatim block in the setup interview**, and the only place the tool speaks in the author's voice rather than the user's search's. It runs once, at setup. **Never on a cycle, never in a digest, never on the dashboard**, because a credit that reappears every run reads as an ad.

Deliberately not watermarked: the reference files, because Claude loads them into context every cycle and a credit line there is noise inside search instructions; and the digest, because it's someone's private job search and a recurring credit reads as an ad.

## Release history

### 1.7.0

LinkedIn sweep robustness, ported from the live search after three corrections that each traced to the same guest endpoint. All three change how a running search behaves, which is what earns the minor.

- **The sweep runs twice and unions by default.** The guest search endpoint returns a *different, incomplete* sample on every call, even for the identical query a minute apart, and this turned out to be a larger source of missed roles than the throttle, the sort, or the stem list. Measured on one bucket: three back-to-back runs returned 289 / 285 / 283 rows against a 399-row union, and 23% of the roles appeared in only one of the three runs, fresh roles at the same rate as any other. A single clean pass silently dropped about a quarter of the set. `linkedin_sweep.py` now runs `--passes` independent sweeps (default 2) and unions them by job ID; coverage rises ~71% → ~92% → ~98% across one, two, three passes, and the union is only `COMPLETE` if every pass paginated cleanly. `search-techniques.md` carries the rule under Search Integrity: **a single clean pass is not full coverage when the endpoint samples.**
- **A throttle is retried before it's believed.** The guest-endpoint block is intermittent, not a hard wall: a bucket that hangs one minute paginates clean the next. The sweep now reads a run of consecutive unreadable pages as a throttle onset and bails that attempt in seconds instead of grinding every page to the cap (which looked "hung" and got the process killed), then re-runs the whole bucket after a cooldown up to `--retries` times. It reports `INCOMPLETE — THROTTLED` only once the retries are spent. The companion rule: **a fallback sweep that stopped on a cap, a timeout, or a rate-limit is `INCOMPLETE`, never a trustworthy "relevance-front" sample**, because a truncated pass is exactly how a dead-center role goes missing.
- **Per-page integrity and an honest cap.** A short page carrying new IDs is legitimate only as the last page before exhaustion; if a full page follows it, it was a dropped page and the set is truncated, now surfaced in the `INCOMPLETE` reason. A deliberate `--max-rows` stop reports `CUT AT n (policy)`, distinct from a coverage gap. The runaway guard sits above the observed ceiling so a genuine exhaustion reports `COMPLETE` rather than false-tripping `INCOMPLETE`.
- **The ATS sweep retries an unreadable host before calling it a gap.** A transient tool error on a single host silently drops that whole platform's roles, and the gap hides inside a group status. `search-techniques.md` gains the rule: re-issue the `allowed_domains` query for an unreadable host before logging it unread, report the retry outcome, and never close a cycle with Greenhouse unread when a retry is available.
- **1.7.1:** the generated dashboard had no favicon, so the browser tab rendered a blank icon. The dashboard skill now writes an inline SVG data-URI favicon into the page head (defaulting to a robot 🤖, or the user's brand emoji if setup recorded one) and passes the same emoji to the artifact publish, so the tab shows an icon whether the page is opened directly or viewed as the artifact.

### 1.6.0

Two independent testers hit the same defect, and the fix is new cycle behavior: **nothing verified an apply link before its first appearance.**

- **A resolve check before research and scoring.** Freshness re-verification only ever protected rows already in the table, so a first cycle protected nothing: top-ranked roles and below-the-cap links opened to "page not found." Every link that will be shown is now resolved first, in three states, where **a failed check is never an expiry** (`live` / `expired` / `unverified`). Confirmed-dead rows are not researched, not scored, and don't consume a slot under the cap; they get scored only if they come back. Below-the-cap rows are checked too, which is where the worst of it was: they carry a clickable link and get no research on any cycle. When a link dies, the employer's own board is checked for a replacement requisition, because a repost is a live role behind a dead URL.
- **Posting status is a second axis, not a stage.** `live` / `expired` / `unverified` sits parallel to `open` / `applied` / `interviewing`, so **"Applied · Expired" stays expressible.** An application is live even when the posting closes, and folding expiry into stage would erase the record that they applied. On the dashboard it renders as a badge, the apply button greys out rather than the card vanishing, live sorts above closed at equal score, and a "Hide closed roles" toggle is on by default with its own visible count.
- **Bishop now checks it can actually run before it starts.** A silent capability probe ahead of the splash: shell, Python, file write, scheduled task. All four pass and the user never learns it happened; any failure stops before the letter and routes them to Claude Code in plain words. The Chat and Cowork surfaces are the case it exists for, because they answer the first request convincingly and degrade after it. The same guard covers cycles and ad-hoc "find me some jobs," which must never be answered from memory in place of a real run.
- **The install path is click-first everywhere.** The plugin README recipients read never mentioned clicking at all: it opened with two slash commands, then an unzip into a hidden directory, then a raw `--plugin-dir` flag. It now leads with the Desktop click path, collapses the typing routes, and gives update and uninstall a click path. The root README drops "CLI" and "to disk" from its opening, glosses every unfamiliar word in the click list (plugin, repo, marketplace, sync), and adds the recovery line it never had.
- **A first-run warning, because that is where people bail.** Setup now says upfront that the first run asks for permission a lot, that a browser will open and move on its own, and that quiet stretches mean work rather than a hang. **The permission block genuinely does not help the first run** (settings don't take effect mid-session), and the interview is now told not to promise otherwise.
- **The permission block is inlined.** Setup pointed at a "Fewer permission prompts" section of the plugin README that has never existed in any commit, so every setup since 1.5.0 improvised its own permission list. The block now lives in the interview, with a merge-don't-overwrite rule and `git push`, deletes, and blanket `Bash(*)` deliberately absent.
- **Cadence carries measured guidance.** The schedule question now states that two runs a week is the sweet spot and fits a Claude Pro plan at roughly half its weekly usage, with the provenance and the conditions under which the number stops being true recorded alongside it.
- **A plain-language pass over everything the user reads.** The dashboard spec had no language rule at all and told Claude to print `localStorage` on the page; the coverage-note specimen every digest copies leaked "ATS boards (25/25)" and "aggregator name-mining"; source slugs (`getro`, `icims`, `lever`, `greenhouse`, `ashby`, `bamboo`) reached the screen untranslated; the known-limitations handoff read engineering notes aloud; and `check_update.py` printed a slash command into the top of the digest. All fixed, with the build-notes-stay-technical carve-out preserved.
- **The employer list asks a question** instead of ending on "cut anything that's wrong," which left users unsure a reply was expected and stalled the flow.
- **1.6.1:** the resolve check was prose, and both pagination bugs this repo documents happened to hand-rolled loops written from careful instructions. `scripts/resolve_links.py` makes it executable, with the three states enforced structurally: `expired` can only be produced by an expiry marker in the final URL, a closure banner on a rendered page, or a hard 404/410 on the requisition page itself, never an API path. **A control URL gates the run:** if the canary does not resolve live, nothing is marked expired, because a proxy or rate-limit would otherwise empty a table in one cycle and look like it worked. Search Notes gains a required `RESOLVE` field carrying the counts and the canary result, and audit check **E8** proves the resolver ran, on the same argument that earned `GATE` its E7: a clean run and an unrun one write the same table. 20 offline tests for the resolver, 3 more for E8.
- **1.6.2:** the letter said Bishop wouldn't write your application and nothing in the skill enforced it, so a handoff was free to end with "want me to draft a cover letter for this one?" `SKILL.md` gains the scope rule (no cover letters, no per-posting resume rewrites, no filling in or submitting an application), **never offered** in a digest, at handoff, on the dashboard, or mid-research. An outright request gets a fixed block in the author's voice: the quality argument, the AI detectors in applicant tracking systems, a human alternative, and a plain statement that a new chat with Claude carries no such rule, so the limit reads as deliberate rather than as a missing capability. **Capped at once per conversation**, since this is the sixth and only repeatable attribution surface. The carve-out is stated because the rule is otherwise easy to over-apply: reading the resume to score against, naming what a JD asks for that the resume doesn't say, employer research, posting capture, and stage tracking all continue. **Telling someone what a posting wants is guidance; producing the words they submit is not.** The cycle prompt carries the no-offer line directly, since a scheduled run never opens `SKILL.md`.
- **1.6.3:** the resolver's expiry-marker list never matched the largest board's marker, so **the most common expiry signal any search meets resolved as `live`** from 1.6.1 onward. That board abbreviates the middle word of its marker and the list carried only the spelled-out spellings, one word apart from a match. Found on a port to the live search this was extracted from, by a test written against what a board actually sends rather than against what the list already had. A closure page that says three words and stops was missed the same way, by a banner matcher tuned to full sentences. Both fixed, both pinned by tests, both with a guard case proving an ordinary live posting still resolves live. `search-techniques.md` gains the rule that produced the bug: **match the parameter a board actually sends, never a reasoned-out guess at it**, and read a check that finds no expiries at all across several cycles as evidence against the matcher before evidence about the market. **This is the failure mode the quality audit exists for, arriving inside the tool built to prevent it:** nothing errored, the counts were plausible, `RESOLVE` reported clean, and E8 passed, because a resolver that sees no expiries and a resolver that cannot see them write the same line.
- **1.6.4:** setup-interview refinements from a full test run, plus two behavior changes. **Undisclosed pay is a question now, not a hidden rule:** a new "No salary posted" picker (show all · show except step-downs · exclude) decides whether a role with no posted pay appears, and `employer_sweep.py` gains a step-down tier and a `no_pay` setting to honor it. Disclosed pay below the floor is still a hard screen, and held-back rows are still listed rather than dropped. **Confidential/open mode is removed.** It mostly guarded already-private surfaces (a private dashboard, a personal Slack, self-addressed email, local-only commits) and sometimes hurt by stripping employer names from a dashboard the user meant to share; in its place the current employer is a default hard exclude (drop on "include my employer"), the dashboard is private by default with names kept, and calendar titles stay discreet, the one place a search can actually leak. **Interview polish:** the splash banner is redrawn with cleaner letterforms and a two-antenna robot; the author's letter carries a title so it reads in the author's voice rather than the tool's; drive-time and LinkedIn-browser confirmations become pickers; permission, commute, and equity labels are clearer; a title-progression ranking factor is added; the Settings section leads with cadence before color; and local-employer research asks for a geographic anchor when a remote-only user gave none.
- **1.6.5:** the "How I work" intro now opens with a plain statement of what Bishop is for ("I'm here to help you find a few new angles for your job search") before it gets into mechanics, so the first thing the user hears is the point rather than the process.
- **1.6.6:** copy pass on the two things the user reads first. The author's letter drops its "Life's too short to hate going to work" opener and now leads on what the tool does, trims the paragraph about not writing applications down to "only focused on finding you new job postings" (the no-applications rule is enforced in the skill as of 1.6.2, so the letter no longer needs to promise it), and signs with a dash. The "How I work" line gets the bishop-moves-on-diagonals pun ("a few new... angles (haha...get it?)"). Wording only, no behavior change.
- **1.6.7:** iCIMS listing pages are served `noindex`, so keyword and `site:` search never surface an iCIMS employer's fresh requisitions even while older ones linger in the index and the host still returns a nonzero count, which hides the gap. `employer_sweep.py` gains an `icims` platform that fetches the tenant board directly (`careers-<tenant>.icims.com/jobs/search?in_iframe=1&pr=0`) server-side, no auth or JavaScript, so the named-employer sweep catches iCIMS employers the keyword pass structurally cannot. `search-techniques.md` documents the blind spot and the remedy, with the rule that **a nonzero iCIMS site-search count is not proof of coverage.**
- **1.6.8:** a pre-launch audit pass, all fixes. **`employer_sweep.py`'s comp parser only matched exactly-three-digit thousands,** so `$95K`, `$95,000`, and seven-figure `$1,200,000` all read as "no pay stated" rather than a number, which let a below-floor role slip past the comp screen for any search with a sub-$100K floor. The regex now spans two-digit-thousands through millions, pinned by twelve cases. **Setup no longer ships a raw placeholder or system vocabulary in what it says out loud:** the LinkedIn step's `{extension link}` becomes a spoken line plus a note telling Claude to insert the real install URL, and the employer-list question's `resolve_boards.py`/`Employer_Index.md` mechanics move out of the spoken block into a note. **`search-techniques.md` and `feedback-loop.md` stop pointing at the retired Q0–Q12 numbering,** which 1.5.0 replaced with sections A–G everywhere but these two files; their header notes now read the labels as topic shorthand. Plus: the skill's reference-map file sizes corrected to actual (the target of audit check E4), E7/E8 listed in order in `quality-audit.md`, a usage guard on `jd2pdf.py` and a trailing-`--window` guard on `linkedin_sweep.py` in place of an `IndexError`, and a one-word typo in the dashboard skill description.

### 1.5.0

A ground-up rewrite of the setup interview after first-user feedback that the old flow was too long.

- **The interview opens with a splash and the letter, then a fork:** Essentials (~15 min) or Everything (~30 min). Essentials gets you searching; Everything adds employer research, field sources, and connected tools. An Essentials user can trigger any Everything step later.
- **Derive-and-confirm from the resume.** Level, current role, and location are read from the resume and confirmed in one free-text pass instead of asked cold. Titles are a single review.
- **Questions cut or reordered:** the market-band comp lookup, the title floor, the motivator menu, search history, and the accessibility question are gone; the name is asked last; the culture bar is a silent 3.0 default; rigor defaults to light. Company-type rules and a second track are now reactive, triggered by the user saying "make a rule."
- **A permissions step** offers to write an allowlist so the search's own file writes and scripts stop prompting, which also lets the scheduled runs go unattended.
- **`scaffolding.md` and `SKILL.md` reconciled** to the new section names (A–D, E–G) in place of the old Q0–Q12 numbering.
- **1.5.1:** a second round of first-user feedback. Setup now checks for an existing search before the splash and offers to update it, archive it and start truly fresh (old files moved aside and never read), or build a separate one, so a returning user is no longer written over on a "rebuild from scratch." The dashboard is built and handed over automatically right after the first search when chosen, instead of waiting behind a slash command a non-technical user never runs. Every digest ends with a plain-language coverage note (searched in full · sampled · off this run · couldn't reach), so a quiet week reads differently from a broken sweep. The weekly audit gets a one-sentence plain explanation when it's created, and setup drops system jargon ("on disk," "allowlist," "search scripts") from anything the bot says out loud.

### 1.4.0

Sourcing reliability, plus the setup gaps a full walkthrough exposed.

- **Q2 takes a title the resume parse would never produce.** Every title was generated from the Q1 parse and both edit steps were subtractive, so a peer title in an adjacent function had no way into the query. Tier 2 now covers the peer title at every level, and the flattened list is shown with "what's missing?" asked outright.
- **A reliability gate on every role entering the table.** Four checks asked together at the moment a role first appears: posting age against displayed date, prior appearance in the index, employer named, requisition on the employer's own board. Two trips writes one Key Context clause. It never screens a role out and never re-scores.
- **A board rejection is against a surface, not a source.** A missing category taxonomy retires the browsable front end; check for a JSON or developer API before writing the firm off. The no-board list gets an annual re-probe.
- **Audit check E7 proves the gate ran.** A clean gate writes nothing, so a quiet week and a dead gate produced identical files. Search Notes gains a required GATE field.
- **1.4.1:** the plugin depended on Claude's browser extension everywhere and told nobody to install it. Q12 now lists connected browsers and names the prerequisite.
- **1.4.2:** a release inside seven days of the last one is a patch whatever it contains. Cadence overrides the version table.
- **1.4.3:** Q12's defaults table gains a job description capture row, so the cycle's "skip if the profile doesn't keep captures" branch has something that can set it.
- **1.4.4:** the weekly audit now checks for a newer Bishop release and surfaces it in the next digest, since third-party marketplaces have Claude Code's auto-update off by default. `scripts/check_update.py` writes `Update_Notice.md` when one exists and clears it once caught up; it is informational and never fails the audit. The plugin README is also slimmed to five sections and rewritten for a non-technical reader.

### 1.3.0

Setup-interview pass after a full walkthrough, plus an audit of every markdown file in the plugin.

- **The color question takes a color, not a color code.** "Teal" or "the blue in my logo" both work; the hex gets echoed back. The color-picker link moved to chat, where it renders as a link.
- **The accommodations question says "accommodations."** "Anything to make it easier to use" is vague enough that most people answer no.
- **Cadence is one picker of named schedules** (weekdays, Mon/Wed/Fri, Tue/Thu, weekly) instead of two day-by-day multi-selects.
- **Rigor carries its token tradeoff in the question text.**
- **Q1 stops re-asking Q0's target rung**, and the resume echo-back stops being fused onto the scope question. New global rule: one question per turn, and never re-ask what a picker already answered.
- **Audit fixes:** four of five file sizes in the skill's reference map were wrong · the customization block described a settings table that the pickers replaced · a "standard twenty" VC boards against an index of nineteen · the scheduled-prompt template restated the rigor-to-tier mapping it doesn't own, which is what check E3 exists to catch.

### 1.2.0

Ported from the live search after five weeks of corrections. Three of these are fixes to recipes that had gone wrong in the wild, not improvements:

- **Four ATS hostnames were pointed at the vendors' own marketing sites** and returned clean-looking nils for months. `site:` is replaced by the search tool's `allowed_domains` parameter, which makes chain length free, and the host list is rebuilt to 25 measured hosts.
- **Both VC-board recipes broke.** Getro's `?page=N` went inert and caps a hand-rolled read at 20 jobs against boards carrying 25,000; `scripts/vc_sweep.py` now drives the API that actually paginates. Consider replaced its API with a signed-token path and is browser-only.
- **A new weekly quality audit**, `references/quality-audit.md` plus `scripts/quality_audit.py`, whose whole target is a broken recipe that reports success. Every case in the file looked exactly like a quiet week from inside a cycle.
- **Search Integrity grew from five rules to seven**, around one idea: anything that can return "nothing" has to distinguish *nothing was there* from *I didn't look*. Per-source status vocabulary, canaries, per-member result counts, and address verification.
- **Read contracts and a split threshold** in `scaffolding.md`, so a tracking file's growth is a measurement rather than a judgment call, plus a character cap on the free-text table column and a fixed shape for the notes log.
- **A customization block at the front of setup.** Naming moves into it, the dashboard palette moves up from the dashboard skill so it's asked once, and it adds the optional integrations: digest delivery including Slack, calendar events for review blocks and dated commitments, read-only email intake that keeps the tracker honest, locale, and pause windows. **Everything is optional and every default works.**
- **Confidential mode**, one switch for anyone searching while employed. It governs the Slack workspace, calendar event titles, dashboard sharing, commit messages, browser profile, and whether their current employer is excluded. A leaked search is the only failure here with consequences outside the search.
- **The scheduled prompt now states no rule it does not own.** A stale cadence table inside a prompt reverted a decision hours after it was made, and no repo-wide search reaches a file that lives outside the project.

**Public history starts at 1.2.0.** The earlier development commits are not published: they carried the maintainer's own employer target lists, scoring rubric, and worked examples, extracted from the live search this was generalized from. Nothing candidate-specific ships in the plugin, and the pre-publication history is kept locally rather than rewritten in place.

