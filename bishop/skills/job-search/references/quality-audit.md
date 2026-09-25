# The Quality Audit

**Is the search mechanically doing what it claims to be doing?** Runs once a week, on its own schedule. **No daily cycle reads this file.**

> **The target is one thing: a broken recipe that reports success.** Every case below looked exactly like a clean nil from the inside, and every one survived for weeks or months.

| Case | How long it reported success |
|---|---|
| An ATS host sweeping the vendor's own marketing site | Unknown, many cycles |
| Three more hosts pointed at vendor pages, logged as dead markets | Unknown |
| A board API returning 20 rows against boards carrying 25,000 | Until instrumented |
| A title stem documented, adopted, and never added to the query string | Two weeks, cost the best-paying role on the board |
| A scheduled prompt reverting a cadence decision hours after it was made | Until measured |

> **This is not a documentation review.** That kind of audit asks whether the files are tidy. **A perfectly formatted file set sweeping the wrong host passes that audit and fails this one.**

---

## 1. What counts as a failure

**Three things look similar in the files and are completely different. Conflating them makes the audit punish a working search.**

| Category | Example | Verdict |
|---|---|---|
| **Market movement** | A requisition closes. A role is filled. The user applies elsewhere first | **Not a failure.** No threshold, no finding |
| **Learning** | A posting reveals a title form no stem matched, and the stem gets added | **Progress.** Logged as a gain, never as a miss |
| **Mechanical failure** | A source reports `COMPLETE` while reading the wrong host | **The entire point of this file** |

- **A stem added because a real posting revealed it is the taxonomy working as designed.** The query set is built to grow a stem at a time.
- **The one recall case that is a defect is a rule that existed and did not execute.** The stem wasn't missing. It was missing from the thing that runs.
- **Expiry gets no failure threshold.** Penalising a requisition that closes days after it was found pushes the search toward surfacing fewer, staler roles, and recruiter-anonymous postings can close in two days. **The one exception is severe:** a freshness pass that vouched for a requisition later found already dead at that date is the same defect class as a broken sweep.

---

## 2. How it runs

**Its own weekly task, on the main thread.**

| Step | What |
|---|---|
| 1 | Run `scripts/quality_audit.py`, which computes every scripted check from the files |
| 2 | Run the live probe in §4, which needs the network and can't be scripted |
| 3 | Append one row to the audit log. Write prose only where a check tripped |
| 4 | Anything that changes a rule becomes a decisions-log entry, **never a paragraph here** |
| 5 | Write the weekly check (§6) and deliver it. **This is the only part the user reads** |

- **The script is the point, not the file.** A prose audit is a rule that doesn't execute wearing a new hat, so every check is computed from the files and none is self-reported. It exits nonzero when a check trips.
- **Never delegate this to a sub-agent.** Detecting self-reported success is the job, and a sub-agent reporting "coverage looks good" is the thing being detected.
- **A clean week writes one row and stops.** No recap, no narrative.
- **If a check can't be computed from the files, it isn't a check yet.** Park it, and say why.
- **Run `scripts/check_update.py --project <folder>` here too.** It compares the installed version (`plugin.json`) against the latest GitHub release, and writes `Update_Notice.md` in the project when a newer one exists, removing it once caught up. The next cycle's digest leads with that file if present. A network failure or an unreadable version is a quiet skip, never a trip, because a stale check is not a search defect. It never installs anything: `/plugin` commands don't run in a scheduled task.

> **Bishop installs from a third-party marketplace, where Claude Code's own auto-update is off by default.** That is why this check earns a place: without it most users never hear a new version exists. Anyone who prefers the hands-off path can enable auto-update for the marketplace and ignore these notices.

---

## 3. Silent-failure checks

**Every check here exists to distinguish *nothing was there* from *I didn't look*.** They all read the per-source status lines and per-member counts that `search-techniques.md` rules 2 and 4 require in the cycle notes. **Without those lines none of this computes**, which is why the logging rule comes first.

| ID | Check | Trips when | Catches |
|---|---|---|---|
| **S1** | **Per-member liveness.** Cycles since each member of a grouped source last returned any parseable result | 3+ cycles at zero while peers return results | A wrong address reading as a dead market |
| **S2** | **Round-number counts.** Any reported count of exactly 20, 25, 50, 100, 250, 500, 750, 1000 | Any | Pagination caps reported as exhaustion |
| **S3** | **Trend break.** A source averaging above zero for 4+ weeks that drops to exactly zero | Any | Recipe decay. Markets decline; they don't hit exactly zero |
| **S4** | **Unvouched nils.** Nils reported with no canary behind them | Rising two weeks running | Accumulating unverifiable claims |
| **S5** | **Canary debt.** Canaries owed, and for how long | Older than 14 days | A source whose nils nobody can vouch for |
| **S6** | **Success either way.** A source reporting `COMPLETE` at zero parseable results 3+ weeks running | Any | The defect that reports success regardless of outcome |
| **S7** | **Canary passes, query never does.** Source live 4+ weeks with a passing canary and an always-empty real query | Any | The source works and the query is wrong. Different fix from S1 |
| **S8** | **Cross-surface contradiction.** A role found on one surface whose host was swept the same cycle and returned nothing | Any | Direct proof a sweep is blind |

> **S8 is the strongest test available and the cheapest to overlook.** Any role another source surfaced that lives on a host the ATS sweep claims to cover is, by definition, invisible to that sweep. **The two observations contradict each other, and nothing in a normal cycle ever compares them.**

> **S1 measures liveness, not yield.** A healthy source can produce zero *tracked roles* for months; that's a market fact, and source tiering handles it. A source producing zero *parseable results* is broken. Conflating those is how a working source gets demoted and a broken one survives.

### Execution-integrity checks

**These hunt the rule that exists and doesn't run.**

| ID | Check | Trips when |
|---|---|---|
| **E1** | Every stem documented in the methodology appears in the actual query string | Any documented stem is absent |
| **E2** | Any figure stated in more than one file agrees across all copies | Two copies disagree |
| **E3** | The scheduled-task prompt restates no rule it doesn't own | The prompt contains a threshold, cadence table, or host list |
| **E4** | Every file's stated read budget matches its actual size | A per-cycle file exceeds its budget |
| **E5** | Every trial in the decisions log has a review date, and none is overdue | A trial is past due, or has no date |
| **E6** | Every tracking-file row has an index line, and every index line a row | Either side is orphaned |
| **E7** | Every Search Notes entry with a nonzero `new` count carries a `GATE:` line | An entry added rows and reported no gate count |
| **E8** | Every cycle entry adding rows carries a `RESOLVE` count, and its canary passed | A `RESOLVE` line is missing, or the run had no passing canary |

> **E7 exists because a check that finds nothing and a check that never ran produce identical files.** The reliability gate writes a clause only when two of its four checks trip, so a normal week and a skipped week both look like a table with no flags on it. **Nothing in a cycle can tell those apart**, which is the same blindness S6 catches on the sourcing side.
>
> **A gate count is not the same thing as a flag.** `GATE: 4 assessed · 0 flagged` is a passing week. E7 counts assessments and ignores flags entirely, so a search that never flags anything never trips it.
>
> **E7 reports `blocked` until the first `GATE:` line appears**, rather than failing every search that has not adopted the gate. It starts checking once the search starts reporting, which is the same self-activating shape as the index checks.

> **E1 is the check that would have caught the two-week miss.** "Every documented stem is in the query string" is a reading exercise against prose and a mechanical diff against a table. **Keep stem families in a table for that reason alone.**

---

## 4. The live probe

**Per-source canaries prove a source answers. They do not prove the query set would find a role the user wants.** Budget ten minutes.

1. **Pick 3 qualifying roles the search did not source**, from this week or the past month. The user's own manual finds are the best material.
2. **Run the current query set at them.**
3. **Record `n/3 reached`, and classify every miss:**

| Classification | Meaning | Action |
|---|---|---|
| **Reached** | The query set works. It was timing | None |
| **Reachable, wrong cadence** | A source that covers it ran on a different day | Check the tier |
| **No stem matches** | A title form nothing in the query set can reach | **Learning.** Add the stem, log it as a gain |
| **Source not covered** | Nothing in the source list carries this employer's postings | Candidate for a new source |
| **Structurally unreachable** | The employer's ATS gates every requisition | **State the gap.** Don't chase it |

---

## 5. The audit log

One row per week. **Prose only where something tripped.**

```markdown
| Date | Checks run | Tripped | Probe | Note |
|---|---|---|---|---|
| {{DATE}} | 14 | S5, E1 | 2/3 | Canary owed 3 weeks on two hosts; one stem missing from the query string |
```

- **A finding that changes a rule leaves as a decisions-log entry**, and this row keeps only the pointer.
- **Never write a conclusion the script didn't compute.** "Coverage looks healthy" is the sentence this whole file exists to distrust.

---

## 6. The weekly check (what the user reads)

**The audit log is the machine record. The weekly check is its plain-language twin, and the only output the user ever sees.** Same relationship as the COVERAGE line and the digest's coverage note.

> **The user has never heard of a stem, a canary, a nil, an ATS host, or check S5.** A check ID, a section number, or a decisions-log number in the weekly check is the same defect as a status code in a digest.

### 6.1 The shape

**Fixed shape, in this order. Drop any empty section except the first two.**

```markdown
# Weekly search check · {{DATE}}

{{VERDICT LINE}}

**Is anything broken?** {{one or two sentences}}

**Did it find what it should?** {{spot-check result, one or two sentences}}

**Your decisions:**
1. **{{Question, answerable yes or no}}** {{One sentence on why.}} Recommended: {{yes/no}}.

Reply with the numbers you approve, e.g. "approve 1". Anything you skip stays here until you answer.

**Fixed for you:** {{one line per fix, saying what it means for the user}}

**Bishop update:** {{only if Update_Notice.md exists}}
```

- **A clean week is three lines:** the title, the green verdict, and "Nothing broken, nothing to decide."
- **It fits on one phone screen.** If it doesn't, something is in here that belongs in the audit log.

### 6.2 The verdict line

**One of three, worded exactly like this, so the user learns to read the dot alone.**

| Verdict | When | Line |
|---|---|---|
| 🟢 | Nothing tripped, nothing to decide | **Your search is working. Nothing to do.** |
| 🟡 | Working, but one or more decisions are open | **Your search is working. {{N}} thing(s) need a yes or no from you.** |
| 🔴 | Any finding §6.4 marks 🔴 | **Something is broken, and you may be missing jobs until it's fixed.** |

### 6.3 Who acts on each finding

**Every finding goes to exactly one bucket.** Choosing the bucket is the main job of writing the check.

| Bucket | What goes here | How it reads |
|---|---|---|
| **Your decisions** | Anything that changes what gets searched or how the user's files are kept | A yes/no question, one sentence of why, a recommendation |
| **Fixed for you** | A fix with exactly one right answer, already applied during the audit | One line saying what changed for them |
| **Bishop problem** | A defect in Bishop itself: the audit script erroring, a check that can't run on any search | One line plus the report link (§6.6). Never a decision for the user |
| **Not shown** | Market movement (roles closing, reqs filled), checks still waiting on history, anything unchanged since last week's report | Nothing. The audit log keeps it |

> **A decision the user can't evaluate isn't a decision.** "Raise the read budget to 460KB?" fails. "Archive your 30 closed roles so each run stays fast?" passes. If the question needs a term from this file to make sense, rewrite it or make it a fix.

### 6.4 What each check says when it trips

**Use this wording.** A report that reads the same way every week is what lets a user skim it.

| Check | Reads as | Bucket |
|---|---|---|
| **S1** | "{{Site}} has returned nothing for {{N}} runs while similar sites kept returning jobs. The search there has probably broken." | 🔴 Decision: "Let Bishop test and repair the search for {{site}}?" |
| **S2** | "{{Source}} returned exactly {{N}} results, which usually means it stopped at a page limit. Jobs past that point weren't seen." | 🔴 Decision: "Let Bishop switch {{source}} to reading every page?" |
| **S3** | "{{Source}} found jobs every week for a month, then suddenly found none." | 🔴 Same repair decision as S1 |
| **S4** | "More sources are reporting 'no results' without a test search to back it up." | Fixed for you: run the test searches now and report what they showed |
| **S5** | "{{N}} test searches were overdue." | Fixed for you: run them. One that fails becomes an S1-style 🔴 |
| **S6** | "{{Source}} has reported success for {{N}} weeks while returning nothing." | 🔴 Repair decision |
| **S7** | "{{Source}} works, but your job titles never match anything on it." | 🔴 Decision: "Let Bishop rewrite the title search for {{source}}?" |
| **S8** | "Bishop found {{role}} on {{surface}}, but its search of {{site}} the same day said nothing was there. That search is missing jobs." | 🔴 Repair decision |
| **E1** | "'{{Title}}' is on your list of titles to search, but wasn't actually being searched." | Fixed for you: add it, and name the title |
| **E2** | "Your files disagree on {{figure}}: one says {{A}}, another says {{B}}." | Decision: "Which is right, {{A}} or {{B}}?" |
| **E3** | "Your scheduled search had its own copy of a rule that lives in your files." | Fixed for you: remove the copy |
| **E4** | "Your job tracker has grown long enough to slow down each run." | Decision: "Archive your {{N}} closed roles? Nothing is deleted." |
| **E5** | "The trial of {{what}} was due for review on {{date}}." | Decision: "Keep {{what}}, or drop it?" with the trial's own results |
| **E6** | "{{N}} tracker entries were out of sync with their index." | Fixed for you: resync |
| **E7** | "On {{N}} days the posting-quality check was skipped." | Fixed for you: run it on those roles now and report anything it flags |
| **E8** | "On {{N}} days the dead-link check was skipped." | Fixed for you: run it now and report any closed roles |
| **Script error** | "Bishop's weekly check couldn't run this week." | 🔴 Bishop problem |

### 6.5 The spot check

**Lead with the count in plain words:** "We tested the search against {{N}} real openings it hadn't shown you. It found {{n}}."

| Probe result | Reads as | Bucket |
|---|---|---|
| **Reached** | Counted in the "found" number, no further line | Not shown |
| **Wrong cadence** | "{{Role}} was on a source that runs on {{day}}, so it would have shown up then." | Not shown unless it cost a role |
| **No stem matches** | "{{Role}} was missed because its title, '{{title}}', isn't one Bishop searches for." | Decision: "Add '{{phrase}}' to your job-title searches?" |
| **Source not covered** | "{{Role}} was only posted on {{where}}, which none of your sources check." | Decision: "Add {{where}} to your sources?" |
| **Structurally unreachable** | "{{Role}} was only reachable from {{where}}, which Bishop can't read on a schedule." | One line under "Did it find what it should?", the first time only |

- **Name the role, the pay if posted, and the location.** A missed role the user would want is the most persuasive line in the report.
- **If a missed role is still open, offer it:** "Add {{role}} to your tracker?" It is the one decision that can put a job in front of them this week.
- **Fewer than 3 candidates is fine.** Report the real count. Never pad it with a role that doesn't qualify.

### 6.6 Delivery and answers

- **Write it to `Weekly_Check.md` in the project,** replacing last week's. Carry any unanswered decision forward, marked "open since {{date}}."
- **Deliver it** to the digest channel the profile names, as the audit task's final message.
- **The next digest leads with one line** while any decision is open: "{{N}} decision(s) from the weekly check are waiting for you." Nothing else from the check goes in the digest.
- **When the user approves an item,** apply it, log the change in `Decisions_Log.md`, and remove the item from `Weekly_Check.md`. **Log a "no" too,** so the same question isn't asked next week.
- **A Bishop problem carries this link,** `https://github.com/adamhilliard/bishop/issues/new`, plus a two-line summary the user can paste. Never ask the user to diagnose one.
- **Numbers need a comparison and a consequence.** "448KB against 420KB" fails. "Long enough to slow down each run" passes. Use a number only when it would change what the user does: pay, days, or a count of roles.
