<!-- bishop-format: procedures 1 -->
# Wall-E Operating Procedures: Sam Rivera

### File Map
The one copy; every other file points here.

| File | Holds |
|---|---|
| Reference_Profile.md | Who Sam is, what Sam wants, hard screens, comp, buckets, Customization |
| Methodology.md | Sources and tiers, query stems and strings, deviations from the skill's technique |
| Operating_Procedures.md | This file: tracking files, table format, ranking, digest, Search Notes shape |
| Decisions_Log.md | Why each rule exists |
| Tracking_Field_Service.md | The one track's live table, closed sections, and Search Notes |
| Audit_Log.md | One row per weekly quality audit |
| Employer_Index.md | Every named-employer list and its board endpoints |
| Weekly_Check.md | Sam's plain-language weekly report (written by the weekly audit) |
| dashboard.html | The private dashboard, regenerated every cycle |

### Read Contracts
| File | Contract |
|---|---|
| Reference_Profile.md, Methodology.md, Operating_Procedures.md | Read in full, every cycle |
| Tracking_Field_Service.md | Read in full, every cycle (split once the read passes roughly 50KB) |
| Employer_Index.md | Read by the employer sweep script, not by the cycle |
| Decisions_Log.md, Audit_Log.md | Never read by a cycle |

### Tracking Files
- **One track:** Field Service, in `Tracking_Field_Service.md`.
- **Sections:** ACTIVE/ROLLING, REJECTED, EXPIRED / NO LONGER POSTED, NOT INTERESTED, Search Notes / Observations. No BELOW THE CAP section: this is a senior search.
- **Applied and interviewing roles stay in ACTIVE/ROLLING.**
- **Freshness pass priority:** interviewing rows first, then applied rows, then open rows by score, highest first.
- **Closed sections use the same columns** as the live table. A row that was never scored carries `—` in Score and every bucket cell, and its Stage token keeps the last stage the role had before it closed.

### Results Table Format
Locked layout, in this order:

| Column | Holds |
|---|---|
| Score | 0 to 5, one point per bucket |
| Company | Name linked to its verified homepage, `<br>`, a one-line bio |
| Title | Job title, `<br>`, the title-progression bucket's ✓/✗ and reason |
| Comp | The posted pay as written, or `Not posted` |
| Pay | Pay-clears-floor bucket: ✓/✗ plus a 4 to 12 word reason |
| Commute | Commute / remote bucket: ✓/✗ plus reason, with the in-office cadence |
| Stability | Stability bucket: ✓/✗ plus reason |
| Reviews | Reviews bucket: ✓/✗ plus reason |
| Key Context | Opens with the stage and posting status tokens (below), then caveats and how the role arrived. 350 characters at most |
| Apply | A working link to the requisition |

**Stage and posting status tokens.** Key Context always opens with
`**Stage: <stage>** · Posting: <status>`, then any dates, separated by ` · `.

- **Stage** (what Sam does next): `open` · `applied <YYYY-MM-DD>` · `interviewing <YYYY-MM-DD>`, then `next: <one line>`. Applied rows add `follow up <YYYY-MM-DD>`.
- **Posting status** (a fact about the requisition): `live` · `expired <YYYY-MM-DD>` · `unverified`. Never two on one row.

### Ranking & Rank Overrides
Highest score first, then the rank overrides in Reference_Profile.md as bands
(no-pay roles below every role that clears the floor on a stated number). Ties
break on comp, higher first, undisclosed lowest. Re-sort the whole table every
run; never append.

### Digest Format & Cap
- **Channel:** chat, plus the dashboard (Reference_Profile.md, Customization).
- **Cap:** none. Senior band; every new role is listed.
- **Order:** new roles, freshness changes, follow-ups due, decisions needed.
- **Every digest ends with the coverage note**, four buckets in plain words: Searched in full · Checked partly · Not this run (with the day it next runs) · Couldn't reach (always shown, even as "none"). Status words and platform names are translated, never printed.
- **Dashboard:** `https://claude.ai/code/artifact/00000000-0000-4000-8000-000000000000` (test placeholder). Favicon 🤖 on every republish.

### Search Notes Shape
Fixed shape, about 4KB per entry at most. Counts, events, and tags; never reasoning.

```
### <YYYY-MM-DD> · cycle <N>
COVERAGE: <source> <status> <count> · <member> <count> · ...
CANARY: <member> PASS|FAIL ...
EVENTS: <n> new · <n> expired · <n> applied · <n> interviewing · <n> not-interested
GATE: <n> assessed · <n> flagged
RESOLVE: <n> read · <n> live · <n> expired · <n> unverified · canary PASS|FAIL
NOTE: <one line, only when something needs saying>
```

### Prose & Writing Rules
Plain language in anything Sam reads: no file paths, script names, platform
names, or status codes. ISO dates in files. The results table keeps its locked
layout and is exempt from prose rules except the Key Context cap.
