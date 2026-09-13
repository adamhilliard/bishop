---
name: dashboard
description: Turn a Bishop job search's tracking files into a private, interactive web dashboard that refreshes itself every cycle. Builds a self-contained dashboard.html with a stat band, ranked role cards carrying a score ring and per-bucket pass/fail chips, filters for track and score and stage, save-for-later and archive buttons, then publishes it as a private artifact at a stable URL and wires regeneration into the existing scheduled search task. Use this when someone with a recurring job search wants to see their tracked roles as a page rather than a markdown table, asks for a dashboard or a visual view or a scoreboard of their search, wants a bookmarkable link to their shortlist, or wants their job tracking to stop living in a table they have to scroll. Users often refer to their search by a personal name they chose at setup, so a request to build a dashboard for a named job bot belongs here. Requires an existing search built by the job-search skill plus at least one completed cycle.
---

# Bishop Dashboard

Turns a job search's tracking files into a private, interactive web dashboard that refreshes itself every cycle.

**Prerequisite:** the `job-search` setup interview has been completed and at least one search cycle has run. This skill reads the files that setup created.

> **Say it in plain language, on the page and out loud.** This is the surface the user looks at most, and it is the one place internal vocabulary reaches them every single day. **Nothing rendered on the page or spoken about it carries a file path, a script name, a platform slug, or a system word** like "artifact," "localStorage," "fetch," "cycle," "rubric," "bucket," or "hard excludes." Name each thing by what it does for them. **The build notes in this file are for you and stay technical**; what the page says does not.
>
> - **The user learned a vocabulary during setup, and the page must not invent a second one.** They were told about their *search* and its *runs*. They chose *what matters to them* and *the lowest salary they'd accept*. Those are the words on the page.
> - **Never print a platform's own name.** The scripts emit `getro`, `icims`, `lever`, `greenhouse`, `ashby`, `bamboo`. On the page, `getro` is "startup investor job pages" and every ATS platform is "company hiring systems," the same translation the digest's coverage note uses.

> **Use the name the user gave their search, not "Bishop."** The interview's opening question set it and the profile records it as a named field. That name is the page's masthead and how the user refers to the thing in conversation.

**What the user gets:** a stat band up top (active roles, top score, disclosed-pay count, saved count), then a ranked card per role with a score ring, a pass/fail chip for each scoring bucket with the reason on hover, comp and flags at a glance, and expandable details with a working apply link. Filters cover track, minimum score, disclosed pay, and remote. Every card carries save-for-later and archive buttons. Published as a private Claude artifact at a stable URL that the scheduled search task republishes after every run, so the bookmark never goes stale.

## The build

**Run these steps in order. Steps 1 and 2 are discovery, 3 through 5 build, 6 and 7 wire it into the recurring cycle.**

### Step 1: Read the existing bot

Read, in full: `Reference_Profile.md`, `Operating_Procedures.md`, and every `Tracking_*.md` in the project folder. (Older setups keep all of this in one profile file; read whatever exists.) From them, derive rather than asking the user for anything readable:

- **The search's name**, from the profile's Bot Name field. It goes in the masthead and the page title.
- **The palette and any accessibility adjustments**, from the profile's Customization section: accent color, plus whichever of larger text, higher contrast, reduced motion, and colorblind-safe colors they asked for. **Setup already asked. Don't ask again.**
- **Where the digest link should go**, from Customization. It changes where this skill delivers the page at publish time.
- **Track names** (one per tracking file) and a short label for each.
- **The bucket list.** However many scoring buckets their rubric has, in their rank order. The dashboard renders *their* buckets, not a hard-coded set.
- **Career level / volume.** A senior search renders every active row as a full card. A high-volume search (a BELOW THE CAP section exists) renders full cards only for ACTIVE/ROLLING and a compact one-line list for below-the-cap rows, never a full card per row for two hundred roles.
- **Per-role data** from the ACTIVE/ROLLING tables: score, company (plus homepage link and one-line bio), title, comp text (whether it's disclosed, plus a numeric midpoint for sorting), location/work arrangement, each bucket's ✓ / ✗ / pending with its short reason, flags, and the apply link plus label.
- **Pipeline stage per role,** if the tracking files carry one: `open` / `applied` / `interviewing`, plus the date it changed and a one-line "what happens next." See the stage section below. If the files have no stage concept, skip it rather than inventing one.

### Step 2: Ask nothing that setup already answered

**Everything is derivable, including the color.** Setup's customization block records the accent, so read it and build.

- **Only ask if the profile has no Customization section**, which means an older setup. Then, one question: *"Pick an accent color for the dashboard, or say 'surprise me.'"* Write the answer back into the profile so it's asked once, ever.
- **If they name a brand or hand over brand guidelines**, extract that palette and typography and use it. Otherwise pick a clean accent and validate it (see Step 3 checks).
- **Honor every accessibility adjustment recorded**, and treat them as independent rather than as one mode:

| Adjustment | What changes |
|---|---|
| **Larger text** | Raise the base size and every step above it. Don't just scale the body and leave 11px micro-labels behind |
| **Higher contrast** | Push text and border contrast well past the minimum, and drop the soft elevation that depends on low-contrast shadow |
| **Reduced motion** | No transitions, no hover lifts, no animated score rings. Render the final state directly |
| **Colorblind-safe colors** | Pick track tones that separate on lightness, not hue, and never use red against green. **The text label on every mark stays either way**; it is the thing that makes color a redundant channel rather than the only one |

> **The dashboard is private by default.** Artifacts start private, so it stays private until the user shares the link themselves. Employer names are kept, the user alone decides who ever sees the page. **Where the digest link goes was decided at setup**; wire it into that destination on first publish and record that it's done.

### Step 3: Build `dashboard.html` in the project folder

One self-contained file: inline CSS, inline vanilla JS, **zero external requests**. Artifact pages block all external fetches, so no CDNs, no webfonts, no remote images. Embed the role data as a JS array in the file. The file is regenerated from the tracking files each cycle, so it never goes stale and never needs to fetch anything.

**Give the page a favicon so the browser tab is never blank.** Put an inline SVG data-URI link in the head, right after the `<title>`, so the tab shows an icon even when the file is opened directly rather than through the artifact. Default to a robot; keep it identical to the emoji passed at publish (Step 5):

```html
<link rel="icon" href='data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🤖</text></svg>'>
```

Single-quote the `href` so the SVG's own double quotes need no escaping. If the user set a brand emoji at setup, use that emoji in place of the robot in both spots. This is a head element, so it stays out of the plain-language rules that govern visible page text.

**Layout spec, battle-tested. Deviate on style, not structure:**

- **Header:** the name they gave their search, the search number and date (**"Search #7 · March 12"** — the word is *search*, never "cycle," anywhere on the page), and a one-line **source-status strip** (each source ✓, or the failure reason, **named in plain words, never by platform slug**). Surfacing failed sources is a core feature of the bot, so keep it visible. No taglines or decorative eyebrows; they get deleted within a day.
- **Stat band** (a "hero" card): 3 to 5 KPI tiles computed *from the embedded data at load time*, not hard-coded. For example a Fresh count with per-track split, in-play count broken down by stage, top score plus company, and a count of roles that list their pay with the typical figure. **Label the tiles in plain words:** "Pay listed," not "disclosed pay"; "typical: $145K," not "median midpoint." Skip decorative mini-charts unless the user asks; tiles earn their place, ornaments don't. **Lead with the Fresh tile**, the count of roles not acted on: that is the number they open the page for.
- **Sticky toolbar of filter buttons:** track tabs (All plus one per track) · min-score thresholds · **stage filter: Fresh / In play / All, defaulting to Fresh** · status views: Active / Saved / Archived · **Pay listed**, **Remote only**, and **Hide closed roles** toggles (**Hide closed on by default**; the count of what it hides shows next to it, so nothing disappears silently) · a "N shown · N saved · N archived" counter. Keep stage and status in visually separate groups; see the stage section below for why.

> **Open on Fresh, not on All.** The page exists to answer "what haven't I dealt with yet," and once most of the board is in play, an unfiltered default buries that answer under roles needing nothing. Ordering the control Fresh · In play · All puts the default first and the firehose last.

- **Ranked cards**, grouped by stage (see below), highest score first within each group, ties broken by disclosed comp midpoint:
  - a **score ring** (conic-gradient donut, no chart library) colored per track, `score/N` in the center
  - company name (hyperlinked, verified homepage) plus one-line bio and location
  - title; comp in tabular numerals (undisclosed styled muted/italic)
  - one **chip per scoring check**: ✓ / ✗ / ? with the 4 to 12-word reason as the `title` tooltip. **Give the row a one-line legend** (“green means it matches what you asked for”); an unexplained ? reads as a bug
  - **flags** as small callout rows (stretch flags, below-bar comp, level ambiguity, whatever the tracking file carries)
  - a details expander listing every bucket's full reason, ending in an **Apply button** with the real link
- **Card actions (top-right):** ☆ save-for-later (toggles; saved roles get a SAVED tag and populate the Saved view) and ✕ archive (hides from Active; the Archived view shows an ↩ Restore button). Persist statuses in `localStorage` keyed by a stable id (`encodeURIComponent(company + "|" + title)`) so they survive republishes. Event-delegate clicks on the card list; re-render (including the stat tiles) after every change. **Suppress ✕ archive on in-play cards.** Hiding a role you have applied to is a footgun.

**Pipeline stage (build this only if the tracking files carry a stage concept):**

The point of the dashboard is answering "what haven't I dealt with yet." Once a few roles are applied to, a flat ranked list stops answering it, because the roles needing attention are scattered through it and score-rank actively misleads. A low-scoring role you are interviewing for outranks everything in urgency.

- **Stage is a data field read from the tracking file, never a localStorage toggle.** It is the same on every device and the bot writes it. Saved/archived are per-device triage. Never put them in the same control group: identical-looking buttons with different persistence and different trust semantics is the mistake to avoid.
- **Group, don't tab.** Render an **In play** group above a **Fresh** group, each with a heading, count, and one-line hint. A tab hides the highest-attention items behind a click, and there are usually only two or three of them. Fall back to a flat list when the view is Saved/Archived or an explicit stage filter is on, since those are already a single intent.

> **The groups lead with In play; the filter defaults to Fresh.** Not a contradiction: grouping only renders on the All view, where in-play roles are the ones with dates ticking. Don't "fix" one to match the other on a later regeneration.

- **In-play cards show different information.** Stage tag, date, and a one-line "what happens next" callout. Score is history once you have applied, so it stops being the headline.
- **Compute day counts at load, not at generation.** `Applied 12 days ago` stays accurate between cycles, and it is the one thing a static page genuinely cannot do otherwise. Flag an application with no reply past a threshold (10 days works) in the card and in the stat tile.
- **Keep the vocabulary tiny:** `open`, `applied`, `interviewing`. Resist encoding how a role arrived (inbound vs outbound) as a stage; that is a note. Stage tracks what happens next.
- **Posting status is a separate axis from stage, and never a stage value.** Stage is what the user does next; posting status (live / expired / unverified) is a fact about the requisition. **Render it as a badge on the card, not as a stage chip**, so "Applied · Expired" stays expressible. That combination is the one users most need to see: the application is live even though the posting closed. Folding expiry into stage would overwrite the fact that they applied.
  - **Badge wording is plain:** **Closed** for expired, **Couldn’t check** for unverified, and nothing at all for live. Never "expired" as a bare status code, and never show a badge on a live role.
  - **Grey out the apply button on a closed role** rather than removing the card. The row still carries its research and its score.
  - **Sort live above closed at equal score.** A closed role holding the #2 slot in a stack-rank is the complaint this came from.
- **Two collapsible panels at the bottom:** (1) a compact restatement of how roles are scored, so the numbers explain themselves — **head these panels "How roles are scored," "What each check means," "Your pay floor," and "What I always skip," never "rubric," "buckets," "comp bar," or "hard excludes"**; (2) notes from the latest search plus decisions needed, mirroring whatever the latest digest flagged, with resolved decisions marked as decided rather than deleted.

> **The rubric panel is a second copy of rules that live in the profile, and second copies go stale silently.** A superseded comp floor once survived on a published page for a full cycle after the real rule changed, because regeneration only ever touched the roles array. Two mitigations, and do both: generate the panel's text from the profile every regeneration rather than hand-writing it once, and put the profile's last-updated date in the panel so a lagging copy is visible on the page.

> **Drive every recurring value from one variable, or from none.** A cycle number that lives in a JS constant *and* in hardcoded masthead and footer text will ship wrong the first time someone updates the constant and assumes that was enough. Either bind the text nodes to the variable, or accept the hardcoding and follow the grep rule in Step 6.

**Style spec:** commit to a **light theme**. Airy white cards on a near-white ground, hairline borders, soft elevation that lifts slightly on hover, system font stack, tabular numerals for money and scores, letter-spaced uppercase micro-labels for tile headings. If the user supplied brand guidelines, use that palette and type instead. Two checks either way:

1. The two track colors must be distinguishable to colorblind viewers. Since every track mark also carries a text label, a muted secondary is acceptable, but never rely on color alone.
2. Escape all role text before injecting into HTML (`&` and `<` at minimum). Company bios and flags contain ampersands constantly.

### Step 4: Verify before publishing

**Reconcile the card count, and refuse to publish on a mismatch.** Count the live rows across every tracking file, count the rendered cards with the stage filter on All, and compare. **Report the reconciled number in the cycle notes even when it matches**, because a check that leaves no trace is indistinguishable from a check that was skipped.

> **This exists because a role was invisible for two days.** It was added to the tracking file at a high score with the best disclosed pay on the board, and the regeneration simply never wrote it into the roles array. **The defect is that regeneration reports success either way:** it renders whatever is in the array, so a dropped role and a correct run produce identical output. It surfaced only when the user asked why three unrelated roles were missing. Nothing in the pipeline noticed, and nothing would have. **The count is the only cheap signal that separates the two.**

If Node is available, smoke-test: extract the `<script>` block, stub `document` and `localStorage`, `eval` it, and confirm it runs, the tiles render, and the card HTML contains the save/archive buttons. Otherwise open the file in a browser pane and look at it. Do not publish an unverified page.

### Step 5: Publish as a private artifact

Publish `dashboard.html` with the Artifact tool. Pass a favicon emoji and keep it forever, since it's how the user finds the tab. **Default to the robot (🤖), and use the same emoji here as the inline favicon in Step 3** so the tab looks the same whether the page is viewed as the artifact or opened directly. If the user set a brand emoji at setup, use that in both places instead. **Record the returned URL**, which goes into the scheduled task next. Tell the user the page is private until they share it from the page's share menu.

> **Write the favicon into the procedures file alongside the URL.** Every republish has to pass it, and it is not recoverable from the live page, the artifact listing, or the repo. Nothing else in the system carries it, so an unrecorded favicon means the next cycle guesses and the user's tab silently changes identity.

### Step 6: Wire regeneration into the scheduled task

Append a step to the existing scheduled search task's prompt, after the scoring/writing step and before the digest:

> REGENERATE THE DASHBOARD: rewrite `dashboard.html` with the fresh full role set. Keep the existing design, structure, filters, and theme. Refresh the embedded data array, the cycle number and date, the source-status strip, the decisions panel, and **the rubric panel, re-derived from the profile rather than carried over**.
>
> Before publishing, **search the whole file for the previous cycle number and date and fix every hit**, not just the variable. Masthead and footer text is frequently hardcoded and will not follow a variable you edited.
>
> Republish with the Artifact tool **passing the recorded URL as `url`** so the same link updates in place. Never mint a new artifact URL.

Include the actual URL literally in the prompt. This is the difference between a dashboard and a screenshot; without this step it's stale by the next cycle.

**Four operational notes learned the hard way:**

- If a republish returns a **version conflict** ("another session published a newer version"), don't force-overwrite. Fetch the live artifact, compare, merge if it actually differs, then publish. Manual "Run now" clicks on the scheduled task are the usual cause.
- When a source dies permanently (for example a board starts returning 403 to every method), **retire it everywhere at once**: the profile's source list (with the reason and date), the dashboard's source strip, and the scheduled task's prompt. A half-retired source resurfaces forever.
- **A cycle published under the wrong number is the standard failure here**, and it happens because updating the one obvious variable looks sufficient. Grep, don't assume.
- **Interim chat edits update the tracking file, not the dashboard.** When a role changes between cycles, edit the tracking file and stop; the next scheduled run regenerates the page from it. Six single-role changes given six full rewrite-verify-publish-commit passes is several times the cost of the same end state. **The page lagging a few days is the designed behavior.** Ask whether they want it current now if a session changed a lot; one question is cheaper than six republishes.

### Step 7: Say the caveats out loud

Tell the user, and put the first one on the dashboard itself:

1. **Saved and hidden roles are remembered by this browser only, and I can't see them.** Say it on the page as: *"Your starred and hidden roles are saved in this browser, so they won't follow you to your phone, and I can't see them. If you're really not interested in a role, tell me in chat and I'll take it off the list for good."*
2. **The page is a snapshot from the last search, not a live view.** Say it as: *"This page updates when your next search runs."* Day counts are the exception: those are worked out in the browser each time it loads, so they stay right in between.
3. **The link can be shared; the stars and hidden cards cannot.** Say it as: *"You can share this link, but your stars and hidden roles stay on your machine. Two people looking at the same page won't see each other's."*
4. **Stage is only as current as the last cycle.** If the user applies to something on a Wednesday, it stays under Fresh until the next run, unless they tell Claude in chat and it updates the tracking file immediately.

## Known limitations

- **The dashboard is a viewer, not the engine.** Sourcing, research, and scoring still happen in the scheduled Claude Code task. If the cycle doesn't run, the dashboard doesn't change.
- **The tracking files remain the source of truth.** If the dashboard and a tracking file disagree, the tracking file wins; regenerate the dashboard from it.
- **Every panel restating a rule is a duplicate that can drift.** The dashboard is the second place those rules live, and only the profile is authoritative. Re-derive on regeneration; never hand-edit a rule on the page.
- **High-volume searches:** cards are for the scored table only. Hundreds of below-the-cap rows render as one-liners or a count, never cards.
- **Custom fonts mostly won't load.** Artifacts can't reach font CDNs, so use a system stack, or accept the fallback if a brand font isn't installed on the viewer's machine.
