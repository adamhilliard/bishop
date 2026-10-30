# The Feedback Loop and Known Limitations

**How the bot gets better after setup, and what it will never do.**

> **A correction to generic technique belongs in the skill, not in the user's files.**
> If the fix would help any search, edit `search-techniques.md`. If it is true only for
> this person, it goes in their profile, methodology, or procedures, with the reasoning
> in their decisions log.

---

## The Feedback Loop and the Decisions Log

The bot gets meaningfully better around cycle three or four, and only if you close the loop. **At daily cadence that's the first week; at weekly it's a month.** Judge it in cycles, not calendar time.

**What the loop is correcting differs by level.** Senior searches spend it on query design and screening judgment, because each role is expensive to get wrong. High-volume searches spend it on the cap and the tie-breakers: what made the table, what got buried, and whether the top ten were actually the ten worth applying to. Ask that question explicitly after each of the first few cycles.

**Three-tier note-taking:**

| Where | What goes there |
|---|---|
| **Search Notes** (tracking file) | Tactical, this-cycle observations. Sources that failed, queries that underperformed, roles checked and skipped with the reason, and the exact terms run. |
| **Profile / methodology / procedures** | Rules that are **validated and durable**. Anything that should govern every future run. |
| **Decisions log** | *Why* each of those rules exists, what triggered it, and what was considered and rejected. |

**Notes graduate upward.** When the same observation appears two or three cycles running, promote it into a rule. That promotion is the entire learning mechanism.

**Correct the bot in conversation, not by editing rows.** Tell it what it got wrong; have it write the corrected rule into the right file and the reasoning into the log. Nearly every technique in `search-techniques.md` originated as a correction.

**When the user says "make a rule," route it by what the rule does:**

| The rule | Goes in |
|---|---|
| **Removes roles** from the search | The profile's Hard Excludes |
| **Ranks roles**, raising or lowering them and removing none | The profile's Company Profile, or the motivator buckets |
| **Has a review trigger** (a stage, a date, or an event that reopens it) | Stage-Tied Rules, and only these |

**On a new hard exclude, re-screen ACTIVE/ROLLING.** Rows that now fail move to NOT INTERESTED with `Excluded by rule [DL-xx]`, and the digest names them. If the named example matches no tracked employer, say so in one line.

> **Writing the rule down is half the correction.** The other half is changing whatever executes it, in the same pass. A widened criterion that no query can reach, or a new tier of role that every sweep still filters out, reads as fixed and behaves as if you never touched it. See "A rule that lives only in prose is not in effect" in `search-techniques.md`.

### Open Trials: every rule on trial, in one table, with a review date

**A trial with no due date is a permanent rule nobody voted for.** Keep one table at the top of the decisions log, and put every trial in it regardless of which file the rule lives in.

| Trial | Opened | Review due | Kill criteria | Status |
|---|---|---|---|---|
| | | | | |

- **Write the kill criteria when the trial opens, not at review.** Deciding what would count as failure after seeing the results is not a test.
- **On review the row is deleted, not annotated.** A settled trial belongs in Do Not Re-Propose or in the rule file. A table of annotated dead trials is a second decisions log.
- **State the trial in terms of what it should surface**, so an ambiguous result is legible as ambiguous.

> **This exists because trials go feral quietly.** One search had three running from three different files, each carrying its own review date in its own prose, and one was already overdue with no surface asking for it. **Nothing was tracking them as a set**, so the only thing that would have triggered a review was somebody remembering.

> **An ambiguous review is a decision for the user, not a unilateral edit.** One trial added six query terms; the review found a real cost in row count and two tracked roles, **neither of whose titles contained any of the six terms.** The cost was proven and the credit was not attributable either way. The honest output there is a recommendation and a question, not a quiet revert.

### Why the decisions log is worth the overhead

**A rule without its origin case gets "fixed" by a future run.** Six weeks later, a threshold looks arbitrary, an exclusion looks over-tight, and a well-meaning cycle proposes reversing a decision that was made deliberately with the tradeoff named. The log is what makes a decision stay decided.

**Four practices, and the first is the one that pays:**

1. **Keep a `Do Not Re-Propose` table at the top.** One row per declined proposal: what was proposed, the verdict, and a link to the entry. **Check it before proposing any rule change.** Rediscovering settled reasoning is rediscovering a dead end, not spotting an oversight.
2. **Stable IDs, appended, never renumbered.** Rules in the other files cite the log by ID, and a renumber silently breaks every citation.
3. **Log the changes you *didn't* make.** When a rule is considered, deliberately left alone, and that isn't written down, a future run will helpfully fix it. Mark those `settled, do not change`, and name the tradeoff that was accepted.
4. **Date and attribute every entry**, and record who decided. When a rule stops making sense later, you need to know when it was added and what prompted it.

> **The log is an appendix, not a rulebook.** Nothing in it is an instruction. If a line in the log reads like a rule, it belongs in one of the other three files instead, and the log should carry only the reasoning.

**The bot proposes; the user decides.** That's the split for blocked posters, for exclude-list additions, and for any rule that would remove roles from the search without being asked. A proposal that's declined goes in the table above and is not raised again.


---

## Known Limitations

Setup doesn't read these out. When one shows up in a run (a quiet week, a flooded table, a browser drop), the digest says so in one plain sentence, so nobody mistakes it for a bug.

> **These are written for you, not for the user. Translate each into one plain sentence before saying it**, under the language rule in `setup-interview.md`: nothing spoken carries a file path, a script name, a platform slug, or a system word. "Requisition" is a job posting. "Session token" is a login. "Coverage gap" is a place I can't see into.
>
> - **Three of these are never spoken at all.** The rotted-recipe rule, the sub-agent finding, and the unvouched-nil rule are engineering rationale for you. They are not limitations the user can act on, and reading them aloud makes the tool sound broken.
> - **Say the rest only when they happen**, in the digest: what a quiet week means at their level, that sourcing is only part of the problem, that judging fit is theirs, and that a browser hiccup is recoverable.

- **ATS site-search dead-link rate is high.** A majority of hits may be closed requisitions. This is the search index, not your setup.
- **Some postings won't render their description.** Board listings occasionally return a shell with no body text. Log the posting with whatever is knowable and flag the gap rather than dropping it.
- **A zero-result cycle is normal at senior levels**, and so is a run of them. Whether that should ever trigger an automatic query review is the user's call, not a default; some explicitly decline the trigger, and the answer belongs in the decisions log either way.
- **A flooded cycle is normal at junior levels**, and the volume rules in `search-techniques.md` manage it rather than fixing it. A table that never shrinks because applications aren't going out is a throughput problem the bot can surface but not solve.
- **Sourcing is not the bottleneck at every level.** At senior levels the seat is rare, so finding it is most of the work. At junior levels the roles are plentiful and the constraints are application throughput, resume screening, and getting past the first filter. A search bot helps with the first of those and not the other two. Say this in the digest the first time a quiet or flooded week comes up, rather than letting the bot look ineffective for four cycles.
- **Some postings are older than any date window.** A requisition already open and older than the catch-up sweep's window stays invisible until it's reposted or someone surfaces it manually. That gap is deliberate; see `search-techniques.md`.
- **Automation can't judge fit.** The bot sources, screens, scores, and ranks. Every decision past that is yours.
- **Some ATS platforms are structurally unreachable by keyword search**, including one top-ten platform that gates every requisition behind a session token. Those employers have to be swept by name. It is a coverage gap to state, never a nil to report.
- **Third-party API recipes rot, and a rotted recipe reads exactly like a dead source.** Two portfolio-board platforms broke on the same day once, one replacing its API outright. **Re-verify a recipe before recording a nil from it.**
- **Delegating the sweeps to cheaper sub-agents does not pay.** It was tried and reverted: the agents dropped documented steps from a long brief, and verifying their reports cost more than the context saved. Treat any coverage claim from a delegate as a lead.
- **Integrations are only as available as the user's own connectors.** Bishop can't install one. A digest channel, calendar, or email intake that was offered and never connected is a setting with nothing behind it, so confirm the connection works on the first cycle rather than at setup.
- **Email intake sees status mail, not intent.** It can confirm an application landed and record an explicit rejection. It cannot tell whether a warm reply is going anywhere, and it will never guess.
- **Browser automation is the fragile part.** Extension disconnects and timeouts happen, and the run has to fall back to search-only. That's recoverable, but only if the digest says it happened.

