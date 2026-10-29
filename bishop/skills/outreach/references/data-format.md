# Outreach data format

The shape of every file and browser store the outreach module reads or writes. For Claude and the maintainer; the user never needs this.

> **Contacts never pass through Claude.** The user uploads their LinkedIn export inside the page, and the page keeps contacts and the board in the browser. Claude writes only the settings files below, and saves a hand-picked names file without reading it.

## Where everything lives

| What | Where | Written by |
|---|---|---|
| The user's groups, in tab order | `Outreach/segments.json` | Claude, at setup and on "add a group" |
| A hand-picked group's names | `Outreach/<file>.csv` | Claude, saved as the user handed it over, unread |
| The warm window | `Outreach/settings.json` | Claude, at setup |
| The page | `Outreach/outreach.html` | `scripts/build_page.py` |
| Contacts, read from the export | the browser, `bishop_outreach_network_v1` | the page |
| The board: stages, stars, notes, logs | the browser, `bishop_outreach_board_v1` | the page |

**Every file is optional.** With no `segments.json` the page uses `assets/segments.default.json`; with no `settings.json` the warm window is `"any"`; with no job search the company lists are empty.

## `Outreach/segments.json`

**The user's groups, in tab order. A person lives in the first group that matches; every other match shows as a tag.**

```json
{
  "format": "bishop.outreach.segments",
  "version": 1,
  "groups": [
    { "key": "warm", "label": "Warm", "rule": "Anyone you've exchanged messages with.", "default": "warm" },
    { "key": "studios", "label": "Game Studios", "rule": "Anyone at a game studio on your list.",
      "match": { "companies": ["Brightfall Games", "Copperline Interactive"] } }
  ]
}
```

- **Format line:** `"format": "bishop.outreach.segments"` and `"version": 1`. A file without them is read as version 1. Any other version stops the build with one plain line.
- **Everyone Else is never listed.** It always exists, always last, and holds whoever matches no group.
- **A dropped default is simply left out.** Order in the list is tab order and match order.
- **Fields starting with `_`** (like `_about`) are notes and are ignored.

### A group

| Field | Holds |
|---|---|
| `key` | Short id: lowercase letters, numbers and dashes, starting with a letter, up to 32 characters. Unique. `motion` and `others` are taken by the board |
| `label` | The tab's name. Unique, and not "Everyone Else" |
| `rule` | One plain line saying who belongs here. It is the group's subtitle on the board |
| `default` | One of the five default rules (below). Give a group `default` or `match`, never both |
| `match` | One custom rule (below) |

### The defaults

Read people's own titles and company names only.

| `default` | Usual label | Matches |
|---|---|---|
| `warm` | Warm | A two-way message thread whose last message falls inside the warm window |
| `recruiters` | Recruiters | Title has recruiter, talent acquisition, sourcer, headhunter or search; or the company name says search, recruiting, staffing, headhunting or talent partners |
| `hr` | HR / People | Title has HR, HRBP, CHRO, human resources, people or total rewards, and no recruiting words |
| `exec` | Executives | Title has CEO, COO, CFO, CTO, Chief, VP, SVP, EVP, President, General Manager or Managing Director |
| `founders` | Entrepreneurs | Title has founder, owner or self-employed |

`assets/segments.default.json` lists all five in this order with their labels and rule lines. Each default appears at most once.

### The custom rules

`match` holds exactly one of these.

| Rule | Shape | Matches | "Why here" says |
|---|---|---|---|
| Company list | `{"companies": ["Brightfall Games", "Copperline Interactive"]}` | Anyone whose company is on the list | works at Brightfall Games |
| Title words | `{"titleWords": ["finance", "controller"]}` | A title holding any of the words, as whole words, any case | title has "controller" |
| Connected dates | `{"connected": {"from": "2016-01-01", "to": "2021-06-30"}}` | Connected on a date in the range, both ends included. Either end can be left out | connected May 2018, inside your dates |
| Hand-picked list | `{"namesFile": "mentors.csv"}` | Anyone whose full name is in the file | on your hand-picked list |
| Job search | `{"jobSearch": true}` | Anyone at a company in the user's Bishop job search | works at Initech, in your job search |

- **Company names compare loosely:** no case, accents or punctuation, and a trailing Inc, LLC, Ltd, Corp, Co, Company, PLC, GmbH and the like is ignored. "Acme Robotics" matches "Acme Robotics, LLC".
- **Names compare** on first plus last name, ignoring case and accents.
- **`names` never goes in `segments.json`.** The names stay in their own file.

### A hand-picked names file

**The user drags a spreadsheet into the chat; Claude saves it into `Outreach/` as it is, without reading it, and points `namesFile` at it.** `build_page.py` reads it and puts the names into the page's settings.

- **The file:** a CSV directly inside `Outreach/` (no folder path). A spreadsheet in another format is a `--check` error asking for it saved as CSV.
- **Layouts read, in this order:** a `Name` (or `Full Name`) column; `First Name` plus `Last Name` columns; otherwise the first column, skipping a first row that says "name".
- **The header can sit below a few lines of notes,** the way LinkedIn's own exports put it.
- **A byte-order mark is stripped.** UTF-8 is read first, then Windows (cp1252), which is what Excel's CSV often is.
- **A missing or empty file** is a `--check` error that names the group.

## `Outreach/settings.json`

```json
{ "format": "bishop.outreach.settings", "version": 1, "warmWindow": "3y" }
```

| `warmWindow` | Warm means a two-way thread whose last message is |
|---|---|
| `"any"` (the default) | any time |
| `"3y"` | within 3 years of the export's date |
| `"1y"` | within 1 year of the export's date |

**The window counts back from the export's date,** so a board built on an older export reads the same tomorrow as today. The export's date comes from the zip's name (`..._MM-DD-YYYY.zip`), else the files' saved date, else the day of the upload.

## What `build_page.py` reads from the rest of Bishop

```
python scripts/build_page.py <bishop folder> [--check]
```

| File | Part read | Becomes |
|---|---|---|
| `Reference_Profile.md` | The `### Bot Name` section, else the title line `# <name> Reference Profile: <person>` | `name` |
| `Reference_Profile.md` | The hex color on the accent line of `### Customization` | `accent` |
| `Reference_Profile.md` | The Company column of the `### Full Career History` table | `pastEmployers` |
| `Tracking_*.md` | The Company column of the live tables (ACTIVE/ROLLING, and BELOW THE CAP when there is one) | `searchCompanies` |
| `Employer_Index.md` | The Company (or Employer) column of every table | `searchCompanies` |

- **A Markdown file whose first line is `<!-- bishop-format: <file> <version> -->`** with a version other than 1 stops the build with one plain line. No line means version 1.
- **A company cell** like `[Hooli](https://...)<br>One-line bio` is read as `Hooli`.
- **Fallbacks:** no profile gives the name `Bishop` and the setup's default accent, slate blue `#4F6D9F`.
- **`--check`** validates `segments.json` (known defaults, valid match types, unique keys and labels, real dates, names files present and readable) and `settings.json`, prints each problem as one plain line, and exits 1 on any error. A build with errors stops the same way and writes nothing.

## The page's settings block

`assets/template.html` carries one slot, which the builder fills:

```html
<script id="outreach-config" type="application/json">__CONFIG__</script>
```

```json
{
  "format": "bishop.outreach.config",
  "version": 1,
  "name": "Wall-E",
  "accent": "#4F6D9F",
  "warmWindow": "3y",
  "groups": [
    { "key": "warm", "label": "Warm", "rule": "Anyone you've exchanged messages with.", "default": "warm" },
    { "key": "mentors", "label": "Mentors", "rule": "The people on your mentors list.",
      "match": { "names": ["Dana Whitfield", "Diego Nakamura"] } }
  ],
  "pastEmployers": ["Acme Robotics", "Globex Field Services"],
  "searchCompanies": ["Hooli", "Initech"]
}
```

- **`groups`** are `segments.json`'s groups after checking, with each `namesFile` replaced by `{"names": [...]}` read from the file. The page also takes `names` directly.
- **`name`** shows in the top bar and the page title, the way the interview decks and the dashboard show it.
- **`accent`** colors the board (see the plan's Color section). Light and dark versions are derived in the page. A group whose color sits within 30 degrees of the accent's hue moves to a spare color.
- **`pastEmployers`:** anyone at one of these companies gets a "Worked There" reason or tag, and ranks just under people who helped before. An empty list never shows it.
- **`searchCompanies`:** feeds the job-search rule, the In Your Search tag and filter, and ranking. An empty list hides the filter.
- **Every `<` in the JSON is written as `<`,** so nothing in it can close the script tag.

## Browser stores

**Everything below lives in the user's browser (localStorage), keyed per page origin. Clearing the browser's data clears it; the page's help says so.** The keys are namespaced `bishop_outreach_` and the two data stores carry a version in the key and in the value (`"v": 1`).

### `bishop_outreach_network_v1`: the contacts

Written when the user presses Use This Export. Message text and email addresses are never kept.

```json
{
  "v": 1,
  "exported": "2026-10-12",
  "loaded": "2026-10-29",
  "hasMsgs": true,
  "people": [
    { "id": "dana-whitfield-bcde52", "first": "Dana", "last": "Whitfield", "title": "Data Analyst",
      "company": "Fernhollow Analytics", "url": "https://www.linkedin.com/in/dana-whitfield-bcde52",
      "connected": "2019-03-14", "dir": "both", "count": 6, "fm": "2026-08-25", "lm": "2026-09-14" }
  ]
}
```

- **`id`** is the profile link's last part (`linkedin.com/in/<id>`), which stays the same across exports. A row with no link gets `x-<first>-<last>-<company>`.
- **`dir`:** `both` (two-way), `you` (only you wrote), `them` (only they wrote), or `none`. `count`, `fm` and `lm` are the message count and the first and last message dates, from one-to-one threads only. Group threads, drafts and spam are skipped.
- **The export:** the zip LinkedIn emails, or its `Connections.csv` and `messages.csv`. The page reads the columns First Name, Last Name, URL, Company, Position and Connected On, and from messages Conversation ID, Sender Profile URL, Recipient Profile URLs, Date, Folder and Is Message Draft. The header row can sit below LinkedIn's notes.

### `bishop_outreach_board_v1`: the board

```json
{
  "v": 1,
  "p": {
    "dana-whitfield-bcde52": {
      "stage": "Active",
      "star": true,
      "outcome": "Helped",
      "notes": "Met at a product meetup.",
      "log": [ { "id": "k3j9x2a", "date": "2026-10-20", "type": "Email", "text": "Asked for 20 minutes to hear how their team works." } ]
    }
  },
  "co": { "fernhollow-analytics": true }
}
```

- **`p`** is keyed by person `id`. Someone with no entry is Not Started.
- **`stage`:** Not Started, Up Next, Contacted, Active, Concluded or Archived. **`outcome`** (Concluded only): Helped, No Reply or Not Now.
- **`log` types:** Email, Call, Meeting, Intro, Message, Note, plus Stage entries the page writes itself ("Moved to Contacted"). The Note It button opens the log.
- **`co`** holds starred companies, keyed by the company's loose name as a slug.
- **Older names are carried forward on load** (Skipped becomes Archived, and the like).

### Preferences

| Key | Holds |
|---|---|
| `bishop_outreach_theme` | `light` or `dark` |
| `bishop_outreach_view` | `people` or `company`, the group view |
| `bishop_outreach_tips` | Which tip cards the user dismissed |

## Merge rules

**A re-upload replaces the contacts and keeps the board.**
- **Matched by `id`:** stages, stars, outcomes, notes and logs stay with everyone still in the network.
- **Titles, companies, connect dates and message counts** come from the newer export, so a person can change group.
- **Someone who left the network** drops off the board. Their board entry is kept in the store, hidden, and comes back if they reappear in a later export.
- **Starred companies stay.**
- **The upload panel previews** connections, two-way threads and the count per group before anything is replaced.

**A rebuild of the page keeps both stores.** The page reads them by key, so `build_page.py` can run any time: new groups, a new window or a new accent apply on the next open.

**Remove My Export** (in the upload panel) deletes both stores after a confirm, and the page returns to its empty state: the upload panel.
