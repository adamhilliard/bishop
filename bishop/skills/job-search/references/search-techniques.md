# Search Techniques

**The running bot's manual: how to source without silently missing half the market, and how to decide what is actually true about a posting.**

> **Q-numbers** are shorthand for the setup interview's questions in `setup-interview.md`, now organized there as lettered sections A through G. Match each by the topic the surrounding sentence names.

The scheduled task reads this file every cycle. It holds nothing candidate-specific,
so improvements here reach every search already running.

| Section | What it covers | When it matters |
|---|---|---|
| **Search Integrity** | The seven rules that keep a partial sweep from reporting as a complete one | Read first; every technique below depends on it |
| **Sourcing Techniques** | Source cadence, query design, the catch-up sweep, ATS site-search, VC boards, named-employer and association boards, role-list posters, recruiter postings, contact discovery, browser handling, volume management | Step 3 of the cycle |
| **Verification Techniques** | Authority order, workplace type, time-zone restrictions, freshness, expiry, dating a posting, apply links, scope ownership, years-of-experience | Steps 2 and 4 of the cycle |

> **`quality-audit.md` is the companion to Search Integrity and runs weekly, not per cycle.** These rules make a broken source detectable; that file is what actually goes looking.

---

## Search Integrity

**Read this before any technique below. Every one of them depends on it.**

The most expensive failure here is not a bad search. It's a search that ran incompletely and reported normally. **A partial result set is indistinguishable from a complete one in the write-up**, so a cycle says "nothing new" off a fraction of the market and nobody notices for weeks.

**It is one defect class met under many names:** a truncating loop, a wrong hostname, a stale API recipe, a rule that never reached the query. Every one of them returns a confident nothing. These seven rules exist to break that tie from outside the source.

### 1. Never infer completeness from "the loop ran"

**Terminate on evidence of exhaustion, not on a page count.**

- **Dedupe by the posting's own ID and stop after two consecutive pages yielding no new IDs.** Don't stop on an empty page: many endpoints re-serve earlier results rather than returning empty, so an empty-page test loops forever.
- **Never assume a page size.** Stepping an offset by 25 against an endpoint that returns 10 per page skips 15 of every 25 while looking like correct pagination. One such run returned 40 rows against a true 712, about 6% coverage, reported as complete.
- **Rendered lists lie a second way.** Virtualized lists build only the cards on screen; one query reporting 51 results rendered 12, and neither scrolling the container nor scripting each element into view forced the rest. **Prefer an endpoint you can paginate over a DOM you have to scrape.**
- **A crash mid-run leaves a readable partial file**, which is the same failure wearing a different hat. One sweep died at row 246 of 779 when a non-Latin-1 company name hit a console encoding default, and the partial output was well-formed and indistinguishable from a complete run. **Make the script's last act be printing its own verdict**, so a missing verdict is itself the signal.
- **Put pagination in a committed script, not in prose instructions.** Both bugs above hit hand-rolled loops written from careful instructions, in a single day.

> **Never cap a sweep at a policy row count.** A cap looks safe on the theory that the first N results are the relevant ones and the tail is padding. Measured against that theory: two runs of the same query on the same day shared only **87% of their rows**. The first 750 is a different 750 each run, not a stable prefix, and the cut was discarding 26% of what the endpoint would serve. **Keep a `SAFETY_CAP` as a runtime guard against an infinite loop**, set it well above any real result set, and report when it fires.

> **A single clean pass is not full coverage when the endpoint samples.** Some guest job-board endpoints return a *different, incomplete* sample on every call, even for the identical query a minute apart, and this is a larger source of missed roles than the throttle, the sort, or the stem list. Measured on one bucket: three back-to-back runs returned **289 / 285 / 283 rows against a 399-row union**, and 23% of the roles appeared in only one of the three runs. A single pass, however cleanly it paginated, silently dropped about a quarter of the set, fresh roles at the same rate as any other, and the sort can't rescue them because the endpoint ignores its date sort. **Run the bucket two or more times and union by posting ID.** Union coverage rises ~71% → ~92% → ~98% across one, two, three passes, and a role has to lose the coin-flip on every pass to be missed. `scripts/linkedin_sweep.py` does this by default (`--passes 2`).

> **An intermittent block is retryable state, not a reason to fall back to a lossy pass.** The same endpoint that hangs one minute paginates clean the next, so a throttle is a retry, not a verdict: re-run the whole bucket after a short cooldown before dropping to any fallback. And a fallback sweep that stopped on a page cap, a timeout, or a rate-limit is `INCOMPLETE`, never a trustworthy "relevance-front" sample. Guest cards come back relevance-sorted, which tempts a caller to treat a truncated pass as "the on-target ones anyway," but a truncated pass is exactly how a dead-center role goes missing. `COMPLETE` requires exhaustion with no holes and no dropped page, on a fallback surface as much as the primary one.

### 2. A nil is a claim, and it needs evidence

**Anything that can return "nothing" must be able to distinguish *nothing was there* from *I didn't look*.**

**Every source reports a status every cycle**, from one vocabulary:

| Status | Means |
|---|---|
| `COMPLETE` | Paginated to exhaustion, or enumerated the whole surface |
| `INCOMPLETE` | Ran, and could not reach part of it. **Name the part** |
| `CUT AT n` | Stopped on a runtime guard, not on exhaustion |
| `SAMPLED` | The surface can only be sampled, never enumerated. A social feed pass is always this |
| `FAILED` | Did not run. **Name the reason** |
| `OFF-CADENCE` | Not scheduled this cycle, so its silence is not a nil |

**A source returning nothing must prove it can return something.** Keep one canary per source: a control query known to have results, run only on the cycles that would otherwise report a nil. **Cost is one extra query, only when it matters.**

> **Design the canary against the failure, not against the endpoint.** A canary asking "did anything come back" passes the worst case every time. One ATS host answered HTTP 200 with real, plausible job postings for an unknown number of cycles while serving **the vendor's own corporate careers site** instead of tenant requisitions. The canary that catches it counts **distinct third-party employers** and passes only at two or more. Ask what a broken version of this source would return, then write the check that version fails.

### 3. Verify the address, not only the answer

**A source pointed at the wrong address fails exactly like a source pointed at an empty market.**

- **Test the bare domain before enumerating subdomains.** Where a platform shards tenants across numbered or regional subdomains, a search against one shard quietly covers a fraction of it. One missed posting sat on shard 501 while the search covered 1, 3, and 5. The same shape appears in regional versions of a board, where a remote role lands on the national domain and never on the metro one.
- **A hostname that reads like the vendor usually is the vendor's own site.** Four hosts in one ATS list named marketing sites rather than requisition hosts, and their nils were recorded as dead markets for months.
- **Anything that encodes an address as a template has to re-verify the address.** One source URL carried the year in its path. The new edition moved to a different folder, substituting the year returned a clean 404, and the search ran ten months on a stale edition, because **a 404 on a templated path is indistinguishable from "not published yet."**

### 4. Log what ran, and what each member returned

**A status is a claim about a group; a count is evidence about a member.** `ATS: COMPLETE 25/25` was true and useless. The group passed, so nothing ever asked which hosts contributed, and four hosts returning nothing stayed invisible.

- **List the exact query terms and sources run, every cycle**, and point at the source section rather than re-typing the list. A copied title list stops covering new targets the moment one is added, and nothing announces that.
- **Log a result count per member for any grouped or paginating source, zeros included:** `ATS 25/25 COMPLETE · lever 6 · greenhouse 4 · ashby 3 · icims 0 · bamboo 0`. It costs one line per cycle and replaces nothing. **Zero is the value the line exists to carry.** A member at zero for three cycles while its peers return results is a wrong address, and that inference is impossible from a group status and trivial from a count.
- **Count parseable results, never roles that made the table.** A healthy source produces zero tracked roles for months; that is the market, not a defect. A source producing zero *parseable results* is broken. **Conflating the two demotes working sources and protects broken ones.**
- **Log returned against claimed on anything paginated:** `getro 412/10976`. **A count that is exactly 20, 25, 50, 100, 250, 500, 750 or 1000 against a large inventory is a truncation signature**, not a result. One board API served exactly 20 rows per board against boards carrying 25,000.

### 5. One rule, one place

**Any rule copied into a second document goes stale silently.** A dashboard rubric panel, a summary card, a prompt that restates a threshold: each is a copy that regeneration never touches. A superseded comp floor survived on a published page for a full cycle after the real rule changed.

- **The fix is deletion, not synchronization.** Keeping a copy accurate requires someone to remember it on every change. Deleting it makes the question unanswerable anywhere but the owner file, and the copy gets a pointer instead.
- **The scheduled-task prompt is the dangerous copy.** It is the only surface that runs unattended, it is read before the rule files, and it lives outside the project folder where no repo-wide search reaches it. One prompt's stale cadence table reverted a decision within hours of its being made, and every run afterward executed the schedule that decision had just overturned. **The prompt states no rule it does not own**; see `scaffolding.md`.
- **State the file map once**, in the procedures file, and give every other file a pointer to it. A map line duplicated into ten headers went stale in three of them within minutes of a file being added, and no check caught it.

### 6. A rule that lives only in prose is not in effect

**When a rule changes, change the thing that executes it in the same pass.** This is the opposite failure from rule 5: here the rule exists in exactly one place, correctly written, and still never runs.

| The rule | Where it lived | What actually ran |
|---|---|---|
| A title tier put in scope at a named set of employers | Methodology prose | Every sweep still filtered to the tier above it. **Never once applied** |
| A domain-seat family put in scope, and named | Profile prose | No stem in the combined query could reach it. **Found only by body-text luck** |
| A title stem measured, adopted, and documented | Methodology prose | **Never added to the query string.** Cost the highest-paying role on the board, unfound for two weeks |

**When a rule changes, walk all four surfaces:** the rule file · the executing surface (committed scripts, the combined query text, the ATS title chain) · any second copy · the decisions log.

- **Widening a criterion is the case that bites.** Making a family "in scope" changes nothing until a stem can reach it. Check the query the same day, then backfill.
- **File boundaries are the executing surface for a read rule.** A rule saying "read only part of this file" cannot execute while the part it excludes shares a file with the part it requires. See `scaffolding.md`.
- **A rule with no executing surface fires only when someone remembers it.** That is a legitimate design, but say so explicitly, so a later cycle doesn't read it as a bug and doesn't trust it as coverage.

### 7. Say when a source failed, and don't take a delegate's word for it

Extension disconnects, timeouts, and challenge pages happen. **A cycle that fell back to search-only is recoverable; a cycle that fell back silently is a hole in the record.** Name the failed source and the reason in the digest.

**A sub-agent's coverage report is a lead, not a finding.** Delegating the sweeps to cheaper sub-agents to save context ran for exactly one cycle:

- **Both agents silently dropped documented steps from a long procedural brief**, and two of that cycle's four reported coverage failures traced to the delegation rather than to the sources.
- **Two rules written straight from those reports needed correcting within hours.** Both reports were directionally right and materially wrong.
- **It was reverted on cost, measured rather than assumed:** verifying and repairing the reports cost more than the context the delegation saved, and both sweeps had to be re-run anyway.
- **The one shape that worked** was a narrow read-only audit with a fixed return shape. Don't generalize from it back to the sweeps, and **never delegate the quality audit** in `quality-audit.md`: detecting self-reported success is the entire job.

> **What survived the experiment is worth keeping without it.** Briefing an agent to report its own coverage limits is what made the gaps visible at all. Rules 2 and 4 make that structural rather than dependent on who ran the sweep.

---

## Sourcing Techniques

Nothing here is candidate-specific, which is why it lives in the skill and is read at run time rather than copied into the methodology file. **The volume section is the exception**: it applies only where a cycle returns more roles than a person can read.

### Sources, and how often each one runs

1. **A logged-in job-board session via browser automation.** Personalized feeds and email alerts are invisible to anonymous web search. **Where the user turned browser access on at Q12, this is a required source, not best-effort:** run it every cycle, and when it fails say so in the digest. Where they turned it off, or never installed the browser extension, the search runs without it and nothing here applies.
2. **Aggregators** (Indeed, ZipRecruiter, Glassdoor, regional boards) via web search, **used to harvest company names from snippets and re-search those directly.** Don't build a dedicated channel around their own job search; see the measured verdict below.
3. **Direct careers pages** for companies of interest.
4. **ATS site-search.**
5. **VC portfolio job boards.** Skip where the field doesn't overlap with venture-backed employers; see Q11.
6. **Curated, association, and certifying-body boards** for the field. From Q11.

**Tier sources by measured yield and give each tier assigned days.** Running everything every cycle costs wall-clock time that the low-yield half doesn't earn back.

| Tier | Cadence | Moves down when | Moves up when |
|---|---|---|---|
| **A** | Every cycle | 15 cycles with nothing tracked | |
| **B** | Two fixed weekdays | 15 more cycles with nothing tracked | 2 tracked roles |
| **C** | Weekly, or on a re-probe condition | | 2 tracked roles |

**Seed the tiers at setup, because tiering is measured and a new search has measured nothing.** Until a source has a `last tracked role` to judge, use this:

| Tier | Seed membership |
|---|---|
| **A** | The logged-in job-board session, and ATS site-search |
| **B** | Named-employer sweeps, the user's certifying-body or association board, VC portfolio boards where the field overlaps with venture-backed employers |
| **C** | Aggregators mined for company names, role-list posters, and anything vetted in during Q11 |

> **Re-tier on measurement, not on the seed.** The seed is a guess about which sources pay off, and it is wrong for some fields: in trades, healthcare, education, and most local employment, the VC boards belong nowhere and an association board is Tier A from day one. **Q11's verdicts override the seed immediately.**

- **The profile's rigor setting decides which tiers run at all.** Light is Tier A only, standard runs each tier on its day, deep runs everything every cycle. **Tiering still measures every source it runs**, so a light search keeps promoting and demoting normally and will say when its Tier A dries up.
- **A skipped tier is `OFF-CADENCE`, never a nil.** Rigor narrows what gets looked at; it never narrows what gets reported.
- **Record `last tracked role` per source.** That single field is what makes the rule executable instead of aspirational.
- **A scheduled skip is not a nil.** Report `OFF-CADENCE`, or a Tier B source's quiet Wednesday reads as a dead source.
- **Never demote on an unvouched zero.** One source was demoted on a yield count taken while four of its eleven hosts were pointed at the wrong address, so the yield figure was measuring a defect in the host list. **Fix the address, then re-measure, then decide.**

> **The structural-invisibility exemption, and it is what saves the named-employer sweep.** A source whose job is to surface what the rubric structurally *cannot* score is judged on whether it surfaces those roles at all, never on what they score. A role a mile from home scores identically to one an hour away against a binary remote bucket; a top-preference industry that isn't a bucket scores nothing at all. **The roles that sweep exists to catch are low scorers by construction**, so tracked-role counts will always undersell it. **Exempt it from demotion on score, never from demotion on silence.**

> **Aggregator job search was measured and is not worth a channel of its own.** On a logged-in session with no bot challenge and working URL filters, a senior title stem returned 17 results of which about 2 were the actual title, and a quoted two-word version of it returned 1 nationally over 30 days, and net-new qualifying roles were **zero**. There is no true phrase gate, so quoting narrows without enforcing. **Being logged in bought nothing**: everything that rendered was public job-board content. The index also carries dead reqs, which kills the fallback case for using it as an expiry check. **Re-probe condition: the site shipping real exact-phrase or boolean search.** Nothing else changes the arithmetic, and "we should try logging in" has been tested and closed.

### Technique: query design, stems over full titles

**Quote your search terms, but quote the shortest distinctive stem rather than the whole title.**

Quoting matters: one test dropped a result set from 97 loose matches to 4 tight ones, and that collapse is the goal at senior levels. What breaks is quoting the *full* title. **Exact-phrase matching requires the words contiguous**, so a decorated title ("Coordinator, Regional Operations"), a connector ("Manager of Operations"), or a spelled-out form ("Registered Nurse" against a query for "RN") all fail to match. **Enumerating every full-title variant is whack-a-mole**, and each miss is silent.

- **Quote the stem that survives decoration.** `"Operations Manager"` catches the Regional and Assistant forms that `"Regional Operations Manager"` drops. A standalone functional phrase catches every title built around it.
- **The cost, accepted:** broader stems pull in roles below the target level. Filter those locally, on the posting text you already have.
- **Different tokens are not synonyms.** An abbreviation and its expansion ("Ops" and "Operations") match nothing of each other. Include both.
- **Run one loose, unquoted sweep alongside the quoted ones.** Titles with a word inserted mid-phrase are invisible to every quoted stem, and the loose pass is the only thing that catches them.
- **Below the senior band, chain in more variants rather than accepting a tiny result set** (Coordinator, Associate, Analyst, Specialist, Assistant). Precision is the scarce thing when four roles exist; coverage is the scarce thing when four hundred do.

**Run one combined OR query per location bucket, not one query per title:**

```
"{{STEM_1}}" OR "{{STEM_2}}" OR "{{STEM_3}}" OR "{{STEM_4}}"
```

- Once against remote (location = country, remote filter on).
- Once against your metro (for hybrid/onsite).
- Both with a past-week date filter.

Two searches per cycle instead of twelve, with no coverage loss. Verified by re-running the terms individually and comparing result sets.

**Keep high-noise keywords out of the combined query.** Any term containing a common cross-industry word drags its noise into every other term it's chained with. Search those separately.

> **Watch for fake results.** A "no matching jobs" state often still renders a "jobs you may be interested in" list underneath. That is not your result set.

**Cut a term on evidence, not on impression, and say which track the cut applies to.** Run it for a full backlog first; a term that returns zero across both location buckets and a full past-month window is dead, and a term returning the wrong job family for one track is often exactly right for the other.

> **Never argue for or against a query term from its row count.** Guest job-board endpoints top out at a fixed ceiling, so **every broad query returns roughly the same number and any comparison between two of them compares nothing.** One search read a 1,000-row cap as silent truncation and proposed three fixes; raising the cap terminated on exhaustion at 986, tightening the window moved nothing, and the date sort was ignored. **The number was a property of the endpoint, not of the query.**
>
> **Judge a term by inspecting its results:** what fraction is on-target, and what did it surface that nothing else did. Sampling one broad stem for genuine matches ran 50/50 at rows 0-50 and **14/50 at rows 850-900**, so the tail is relevance decay, not lost coverage. A stem measured this way was cut at 2% precision, and a different one was adopted despite a large row count because the roles were real.

### Technique: the weekly catch-up sweep

**Per-cycle searches use a past-week filter to catch new postings, which means a still-live posting older than a week never reappears.** Roles sit open for months. A query that only ever looks forward will never see them.

- **Once a week, run the same queries against a past-month window**, both location buckets, paginated to exhaustion. Anchor it to the start of the week, where it's worth most.
- **Always run a backfill immediately after changing a query.** A widened query only helps postings made after the change unless the backlog is re-scanned, and a fix that surfaces nothing looks like a fix that didn't work.
- **Don't widen past a month** once the per-cycle sweep paginates properly. New postings then get caught while fresh, the backlog stops growing, and a wider window mostly re-scans roles already screened.
- **Known residual cost, accepted:** a posting already open and older than a month when the sweep starts stays invisible to it. That's a real gap, and it's cheaper than the re-scan.

### Technique: ATS site-search

Most employers post to their applicant tracking system directly, and those pages are search-indexed. This reaches roles invisible to both job boards and generic search.

**Method: pass the host to the search tool's `allowed_domains` parameter. Do not use a `site:` operator.**

- **`site:` degrades silently as the OR chain grows**, which used to force splitting the title list into 4-5 term segments. `allowed_domains` is a separate parameter, so **chain length costs nothing.** Measured the other way round: a 12-term chain against one host returned 10 results, all on-host, and surfaced a role the 4-term chain had been missing. **Longer chains now strictly dominate**, and the sweep collapses from ~110 host-by-segment pairs to one chain per host per track.
- **One host per query. Never batch several hosts into one `allowed_domains` array.** Batching is the obvious way to hold cost flat and it **drops hosts silently**: in one 6-host batch, five of ten results came from a single host and two hosts that pass solo returned nothing at all.
- **Give the parent domain, not a tenant subdomain.** The parameter matches by suffix, so `icims.com` reaches every `careers-<tenant>.icims.com`. This is the same rule as testing the bare domain first.
- **Report `COMPLETE n/n` or `PARTIAL n/n` naming what didn't run**, with a per-host result count. Four wrong hostnames survived for months inside a group status.

**Hosts, ordered by installed base. Canary each one before trusting a nil from it.**

| Tier | Hosts |
|---|---|
| **Core** | `jobs.lever.co` · `job-boards.greenhouse.io` **and** `boards.greenhouse.io` · `jobs.ashbyhq.com` · `myworkdayjobs.com` · `apply.workable.com` · `jobs.smartrecruiters.com` · `ats.rippling.com` |
| **Mid-market**, where mid-size employers and their senior seats concentrate | `icims.com` · `bamboohr.com` · `applytojob.com` · `workforcenow.adp.com` · `myjobs.adp.com` · `recruiting.paylocity.com` · `paycomonline.net` · `jobs.dayforcehcm.com` · `recruiting.ultipro.com` · `breezy.hr` · `jobs.gem.com` |
| **Enterprise**, slower turnover, carries the top seats | `taleo.net` · `oraclecloud.com` · `csod.com` · `avature.net` · `eightfold.ai` · `teamtailor.com` (EU-skewed) |

**Four host names that look right and are wrong.** Each serves the vendor's own site or nothing at all, and each returned a clean-looking nil for months:

| Wrong | Right |
|---|---|
| `careers.icims.com` | `icims.com` |
| `careers.workable.com` | `apply.workable.com` |
| `jobs.bamboohr.com` | `bamboohr.com` |
| `apply.jazz.co` | `applytojob.com` |

**Rules that came from confirmed misses:**

1. **Greenhouse has two host domains and you need both.** Boards migrated to `job-boards.greenhouse.io` and legacy URLs redirect, so the old host reaches only the legacy-indexed set.
2. **Search `myworkdayjobs.com` bare, never a shard.** Tenants shard across numbered subdomains running far past the usual `wd1 / wd3 / wd5` examples, and this is the most common enterprise ATS among large employers.
3. **Block the vendor's own marketing subdomain** where the parent domain floods: `www.icims.com`, `www.bamboohr.com`, `www.avature.net`, `eightfold.ai/company`, `breezy.hr/resources`.
4. **When a staffing or search firm surfaces on an ATS hit, pull its whole board.** These firms run every client requisition through one tenant, so **the indexed result is one row of many and disproportionately the stale one.**
5. **`recruiting.ultipro.com` is PARTIAL by construction.** Board landing pages index; the detail pages render client-side and index thinly. Never read a nil there as clean.
6. **Retry an unreadable host once before recording it unread.** A transient tool error (`invalid_tool_input`, a timeout) on a single host silently drops that whole platform's roles, and the gap hides inside a group status. Re-issue the `allowed_domains` query for that host before logging it as a nil, and **report the retry outcome**, so a genuinely down host still shows as a gap rather than being hidden by the retry. **Greenhouse is the highest-value host to protect this way**; never close a cycle with it unread when a retry is available.

> **iCIMS listing pages are served `noindex`, so site-search misses fresh requisitions while older ones linger in the index.** A `site:` sweep of `icims.com` can still return a nonzero count off stale pages, which hides the gap: the newest reqs, the ones worth catching, are exactly the ones never indexed. A nonzero iCIMS count is not proof of coverage. **Reach an iCIMS employer by fetching its tenant board directly instead:** `careers-<tenant>.icims.com/jobs/search?in_iframe=1&pr=0` returns the whole current board server-side, no auth and no JavaScript. The named-employer sweep supports an `icims` platform for exactly this, so put the employers you care about there rather than trusting the keyword sweep to surface them.

> **SuccessFactors is a structural blind spot, and it is a top-ten ATS by installed base.** SAP gates every requisition behind a session token, so no detail page enters any index: roughly 25,000 companies, including 13.2% of the Fortune 500, are unreachable by keyword search. **Reach those employers through the named-employer sweep or a job board instead. State it as a coverage gap; never report it as a nil.**

> **Known limitation: expect a high dead-link rate.** Indexes of ATS pages go stale fast and a majority of hits may 404 or redirect to a generic openings page. Run it anyway; live matches slip through here that appear nowhere else. Some ATS pages need JavaScript, so read those with a browser rather than a plain fetch.

### Technique: VC portfolio job boards

Major VC firms run aggregated boards pooling openings across their portfolio companies. High signal, because every listing is implicitly a funded company.

**These look unreachable and aren't, but the reachable path changes.** Both platform recipes below broke on the same day once, in opposite directions, and a stale recipe reads exactly like a dead source. **Re-verify the recipe before recording a nil from either.**

**Platform 1: Getro.** Board lives on a custom domain. **Use `scripts/vc_sweep.py`; do not hand-roll this.**

> **The `?page=N` parameter on the board's own HTML is inert.** `page=0` and `page=3` return identical job data, so a `__NEXT_DATA__` parse caps at the first 20 jobs against boards carrying 10,000 to 25,000. `offset`, `start`, `from`, `p`, `pageIndex`, `skip` and the `_next/data` endpoint were all tested and all return the same first 20. **Twenty rows off a 25,000-job board is a token sample reported as coverage.**

The working surface is the board's own search API, found by watching the page's XHR rather than by retrying its documented one:

```bash
# 1. collection id, once per board, from the /jobs page's __NEXT_DATA__:
#    props.pageProps.network.id
# 2. then paginate the real API:
curl -s -X POST "https://api.getro.com/api/v2/collections/<id>/search/jobs" \
  -H "content-type: application/json" -H "Accept: application/json" \
  -H "Origin: https://<board-domain>" -H "Referer: https://<board-domain>/" \
  -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36" \
  --data '{"hitsPerPage":20,"page":N,"filters":{"page":N},"query":""}'
```

- **`Accept: application/json` is mandatory or it returns HTTP 406**, which reads like a dead endpoint and is not one. `Origin` and `Referer` are also required; a bare POST returns an empty body.
- **Page size is fixed at 20 server-side.** `hitsPerPage` is accepted and ignored.
- **Sweep with an empty query and filter titles locally.** Server-side `query` looks attractive because it cuts a 10,976-posting board to 73, but it does not reliably return exact title matches: on one board a query for a title returned 24 rows and omitted a posting carrying that exact title, which the unfiltered sweep finds. **That trades a visible cap for an invisible miss.**

**Platform 2: Consider.** White-labeled at `jobs.<firm>.com`. **Browser-only. There is no working `curl` recipe to write.**

> The documented `api-boards/search-jobs` POST now returns `{"error":"INVALID_CSRF"}`, and the endpoint has been **replaced** by a signed-token path rather than merely gated. Its filtering is UI-only rather than URL-addressable, so a DOM read is the only route and the pass is `SAMPLED`, never `COMPLETE`.

**Board index:**

| Platform | Boards |
|---|---|
| **Getro** (scriptable) | General Catalyst · Accel · Khosla · Insight Partners · Redpoint · Thrive · Menlo · Index Ventures · BITKRAFT (gaming/esports) · Antler · Techstars |
| **Consider** (browser-only) | a16z · Sequoia · Greylock · Bessemer · Lightspeed · Kleiner Perkins · NEA · Contrary · Battery Ventures |
| **Own platform** | Y Combinator (`workatastartup.com`), handle separately |

> **Checked, no dedicated public board found:** Benchmark, Founders Fund, Norwest, Foundation Capital, Craft, Emergence, IVP, Coatue, Tiger Global, Union Square, First Round, GV, Pear VC. Don't re-search these each cycle. Some of their roles surface only on shared multi-firm Getro networks.
>
> **Re-check the list about once a year, and treat a hit as a correction rather than a surprise.** Firms launch boards. One entry on this list was carried as "no board" long enough that a cycle stopped looking, and it had a live Consider board the whole time. **An inherited absence is weaker evidence than a probe**, so a no-board entry earns a re-probe on the same schedule a dead endpoint does.

> **Check the board's category taxonomy before trusting a low yield.** Several accelerator boards have no category at all for whole functions, and every URL guess for one 404s. That's a structural absence rather than a quiet week, and it means the *browsable board* is a poor surface for that search.
>
> **⚠️ A missing category retires the surface, not the source.** Before writing a board off, check whether it publishes a JSON or developer API. Aggregator front ends routinely expose a fraction of what they index: one board offering ~1,800 roles through its category paths returned **42,428** through its documented API, on a scope parameter the paths never exposed, with a working minimum-compensation filter the UI did not have. **A rejection recorded against the source name will be believed later by a cycle that has no idea only one surface was tested.**
>
> **So record which surface a rejection tested.** "The category paths carry no roles in this function" is a durable finding. "This board is a poor source" is the same finding with the qualifier lost, and it is the version that survives into next year.

### Technique: named-employer board sweeps

**Sweep a named list of employers directly, by board, rather than by keyword.** This is the countermeasure for the things the scoring rubric structurally cannot see, and every rubric has some.

**Two blind spots are built into the design of Q8, and neither is a bug to fix in the rubric:**

- **A binary bucket cannot see magnitude.** If work shape scores ✓ only on fully remote, then an onsite role a mile from the user's home scores exactly the same ✗ as one an hour away. The bucket is doing what it was told.
- **A tiebreaker earns no point.** Q6c usually makes industry a tiebreaker rather than a bucket, on purpose. So the user's single favorite industry never adds to a score, and roles there rank as if the preference didn't exist.

**Q6d asks for this list during setup, so the usual case is that it already exists.** Build the sweep from their `Employer_Index.md` and move on.

**The tell that it needs widening: the user keeps surfacing roles the search should have found.** When someone hands you two roles in two days that both scored near the bottom, both had the same invisible feature, and the search had sourced neither, the rubric isn't miscalibrated. It's blind, and no amount of re-weighting fixes a dimension that isn't measured. Go back to Q6d and ask again, using the specific miss as the example.

**What to do instead of changing the rubric:** add those employers to the index and sweep their boards by name every cycle. The roles still get scored honestly and still rank low. They just stop being invisible.

**Run it with the bundled script,** which reads every set out of the index and carries no employer list of its own:

```bash
python scripts/employer_sweep.py --index Employer_Index.md --list   # show sets
python scripts/employer_sweep.py --index Employer_Index.md          # sweep them
```

Its docstring documents the table format and the `sweep-config` block. Set that block from the user's answers: `seniority` from their target-level titles, `function` from their target titles, `stretch` from step-up titles (only if they're open to a step up), `step_down` from lower-rung titles (only if open to a step down), `comp_floor` from their salary floor, and `no_pay` from the "No salary posted" answer (`all` · `except_step_down` · `none`).

**Mechanics, the same shape as the VC portfolio sweep:**

- **Probe and confirm every endpoint before adding it.** Never add a board on a guessed slug. `scripts/resolve_boards.py` does this in bulk: give it company names and it returns confirmed platform-and-slug rows plus an unresolved tier. **A short slug landing on a different company is the trap it exists to prevent**, so it checks the board's own published name wherever the platform exposes one.
- **Separate confirmed access from unresolved access.** A board you cannot read yet is a coverage gap to resolve on a cycle where the browser is already connected. **It is not a negative finding about that employer**, and recording it as "nothing there" is how a gap becomes permanent.
- **Filter on seniority AND function**, locally, on the payload you already pulled. These sweeps return everything the employer has open.
- **Put it in the committed script** with the rest, and have it print `COMPLETE` or name the boards it could not read. A few dozen boards is cheap enough to run every cycle.

> **Membership in a premium list is not itself a qualification, and this trap is easy to walk into.** Once a list is framed as "employers who pay well" or "the best companies," the next step is relaxing a screen for it: undisclosed comp becomes a flag rather than a screen, because the premise says the band is high. **That reasoning puts bottom-scoring roles on the board.** A named list changes *which employers get looked at*. It never changes the title floor, the comp floor, or any hard filter. Say so in the profile when the list is created, because the relaxation is the natural next thought.

> **Keep the list in its own file, not inline in the methodology.** The methodology owns the rules for how a sweep runs; an employer index owns the names and endpoints. Otherwise the same list ends up half-copied in two places, and the technique section becomes unreadable. See `scaffolding.md`.

### Technique: association and certifying-body boards

**The board run by the user's own certifying body is consistently one of the better sources and one of the least remembered.** It's usually free, it carries senior roles, and its listings often appear nowhere else.

Expect these mechanics:
- **Browser-only access.** These sites frequently sit behind a bot-challenge layer that lets the first plain fetch through and challenges everything after.
- **Keyword search often doesn't work headlessly.** Use the site's own function or category filter pages, which render as plain listings.
- **The filters are loose.** A seniority filter will return assistant and coordinator roles alongside the executive ones. Filter locally rather than trusting the facet.

### Technique: role-list posters

**Individuals who publish recurring lists of open roles in one function.** They take submissions by DM from their own network, so **the inventory reaches no ATS and does not appear in job-board search.** One post carried three senior roles with comp bands, none of them findable by any query that search was running.

- **Reading a post is invisible to its author, and that is what makes the channel safe.** Post analytics show aggregate demographics only. **Engagement is the tripwire, not viewing:** a like, comment, repost, or follow notifies the author by name. Profile views stay off limits.
- **A known poster's permalink usually needs no session.** Post URLs are readable logged out; newsletter-format URLs on the same platforms generally are not.
- **Web search cannot find these people, so discovery has to happen in the feed.** Measured: ten searches and three fetches yielded one confirmed name, while one fetch of an already-known handle yielded ten roles with comp bands. Generic title keywords return profile pages, not posts.
- **Budget the pass by organic post count, and cap the scroll steps.** Roughly half of a loaded feed is ads and platform-injected modules, so page count is a misleading unit. Whichever limit hits first ends the pass.
- **Never budget by post age.** A Top-sorted feed interleaves: a 3-hour-old post can sit below two-week-old ones, so an age-based stop fires early and unpredictably.
- **Report `SAMPLED`, never `COMPLETE`.** A feed pass samples; it cannot enumerate.

> **Feed scraping breaks in ways that look like an empty feed.** Three mechanics were wrong at once in one implementation and the pass stalled at 3 posts against a 50-post budget, which read as a dead channel. **Scrolling a container already at its bottom produces no delta and no fetch**, so scroll up first and then back down to make each step real. Settle time was 2.5s and needed 6s. And a visually-hidden accessibility label was being counted as an attribute rather than as text. **Two counting traps inflated the "organic" number in the same pass**: the platform's own injected job modules carry the same post marker as a person's post, and the "Promoted" label renders run together with adjacent text, so a whitespace-bounded regex counted 2 promoted where the truth was 21.

> **Judge the channel on new posters found, not on roles found**, and set a review trigger before starting: if two consecutive passes surface no new poster, drop feed discovery to the day the known posters publish and stop running it mid-week. Reading a known handle by URL never needed the scroll.

### Technique: recruiter and undisclosed-employer postings

**Do not treat these as a lesser tier.** They are frequently real, senior, and exclusive, and at senior levels a meaningful share of the best roles never appear any other way.

- Screen them on the hard filters using the posting's own terms, same as any role.
- Company-dependent buckets (stability, culture) can't be scored without knowing the employer. **Flag the unknown; don't deprioritize the role.**
- Track them with the same rigor, scoring on whatever is knowable.

**Below the senior band the mix is different, and the bot should say which kind it's looking at.** Undisclosed-employer postings at junior levels are mostly staffing-agency listings, which are legitimate and often a real channel, plus a meaningful share of duplicate reposts and outright scams. Score them normally, and note in Key Context whether the poster is an identifiable agency or unidentifiable.

**Flag likely scam postings rather than tabling them silently.** The reliable tells: payment requested for training, equipment, or a background check · an interview conducted entirely over chat or SMS · a job offer with no interview · a request for bank details, SSN, or ID documents before an offer · a free-email-domain contact address for a named company · comp far above the market band for that title. **Never enter personal or financial details into an application on the bot's recommendation.** These target early-career seekers specifically, and volume searching increases exposure.

**Keep a blocked-poster list, and escalate to it when a flag recurs on the same firm.** Scam and low-signal postings cluster by poster, not by role, so the durable unit to screen on is the firm.

- **One suspicious posting is a flag on the row.** Note the tell in Key Context and move on.
- **The same firm flagged twice, especially across two tracks, is a question for the user.** Say the firm's name and propose blocking it. Don't keep re-flagging row by row.
- **A blocked firm's postings go straight to the closed section** with `Blocked poster: <firm>` as the reason. No research, no scoring. Report the count of blocked hits in the digest so the rule stays visible and correctable.
- **Record the identifiers, not just the name.** The hosting board or apply domain, the recurring boilerplate phrases, and the posting shape (comp band, location, whether the client is ever named). A firm that rebrands keeps its pattern.
- **Only the user adds a firm to the list.** The bot proposes; blocking a legitimate recruiter costs real roles, and undisclosed-employer postings are a genuine channel.

> This came from a firm that posted a string of "Confidential" client roles at implausibly high bands on interchangeable boilerplate. The bot flagged it on two separate tracks a week apart and never connected the two, so a per-row caveat kept getting rewritten instead of one screening rule getting written.

> **Note what the bot verified and what it didn't.** Some sources, community forums among them, aren't fetchable by these tools, so an allegation the user brings from one is the user's read rather than a confirmed finding. Verify the posting pattern independently, record that separately from the allegation, and say which is which. **If a blocked firm is ever cleared, delete the entry rather than editing the reason**, so the record doesn't read as a standing accusation.

**Anonymized reposters defeat the dedupe key, and the failure is structural rather than a quirk of one board.** A dedupe index keyed on company plus title cannot catch a reposter that publishes neither, however well the index is maintained.

- **Match on the disclosed comp band plus the reporting line.** A band like `$96,600-$172,500` is not a round number and will not collide by chance; pair it with the reporting line and the match is settled. Three confirmed cases in two days were all resolved this way, two against roles already live in the table.
- **Index the repost's own job ID under the reposter's name**, with the underlying role named in the write-up. That is what lets the next cycle's ID grep catch it, and it's the only mechanism that works when the company string is useless.
- **This doesn't make reposters a rejected channel.** They republish real requisitions and occasionally carry one nothing else reached. **The cost is that a role already in play arrives looking net-new**, which wastes a research pass and, worse, can put the user in front of a role they already applied to as though it were fresh.

### Technique: contact discovery

**Only if Q12 of the setup interview turned it on.** The bot sources, screens, scores, and ranks, then stops, which at senior levels leaves the highest-value fact off the row: the name of the person who decides.

**It is a note, never an action.** No outreach, no drafting, no connection requests, ever. **Only from sources that don't announce the visit:** profile views are visible to the person viewed, and an unattended run must not put the user in a stranger's viewer list. The company's own site, the firm's people pages, press coverage, and public bios are the whole surface.

**Record a full record, not a name**, since the expensive part is finding the person at all:

| Field | Note |
|---|---|
| Name and title | |
| Role in this requisition | Hiring manager, retained consultant, internal recruiter |
| Public profile URL | Recorded, never visited |
| Where it was found | The published page, so the claim is checkable |
| Published background | Prior firms, practice area, tenure |
| **Overlap with the user** | The field that earns the pass |

**The overlap field is the one worth the effort.** Join the contact's published background against the user's own history and report only real matches: shared employers, shared client-side industries, adjacent practices. **It is a public-record join**, so it cannot see connection degree or shared connections, and the row must never imply that it can.

> **Contact brokers are not a source, and this is a hard ban.** RocketReach, ZoomInfo, Apollo.io, Lusha, and ContactOut sell inferred patterns, and a web search will volunteer one unasked. Measured on a single first pass: a broker served a phone number that the firm's own bio page contradicts, and **fabricated an email address for a person who publishes none.** It was wrong about the number it had and invented the one it lacked. **Never record an address that traces back to one**, however right it looks. That is the specific way a wrong fact enters a file looking authoritative.

**Set the expectation at setup, because the yield is lopsided.** Measured across twelve records on a first pass: 8 named individuals, 4 published phone numbers, **0 published direct emails** (firms use contact forms), and 4 genuine overlaps.

- **Search firms are the higher-yield half by a wide margin.** They publish people pages carrying title, practice, phone, office, background, and the public profile URL. Employers publish a leadership page and a press release.
- **A firm name alone is an incomplete record, not a finished one.** "Retained by <firm>" means the consultant has not been found yet. Chase the individual.
- **Leave it blank rather than guessing.** An unverified name is worse than an empty field, because the user might act on it.
- **The pass throws off employer diligence for free.** One run found a firm described on the row as retained search reading publicly as an RPO, and a live executive search running off a site whose contact page still carried a template placeholder phone number. Both belong in Key Context.

**Where the record lives: in the block of the role that surfaced it, with a one-line pointer on the row.** A separate contacts file keyed by firm is the alternative, and it buys one real thing: a consultant's record outlives any single requisition and serves that firm's next one. **It costs a whole extra file, and the record then has to be kept in sync with two tracking files.** Default to the role block, and only split the file out once the same firms keep recurring.

### Technique: browser handling for unattended runs

An unattended run can't click a browser picker, and the properties that look like they'd let it choose are unreliable.

1. **Record the intended browser's device identifier in the profile during setup.** This is the only durable handle.
2. **List connected browsers at the start of every cycle** and select the recorded ID. Selection takes a device ID and needs no human input.
3. **If the recorded ID is absent and exactly one browser is connected**, proceed with it, and **verify the session identity** (read the logged-in account name off the page) before trusting the results. A run once proceeded under this fallback against an unrecognized browser that happened to be signed in as the right person; that was luck, not verification.
4. **If the recorded ID is absent at the very start, re-list once before falling back.** Extensions connect a minute or two into a run more often than you'd expect.
5. **Zero browsers, or an ambiguous result:** fall back to search-only for that cycle **and say so in the digest.**

**Don't try to identify a browser by anything else.** Display names get reassigned between runs (the same device showed as "Browser 2" and then "Browser 1" inside a single run), a browser extension's ID is identical on every install, and a locality flag can read true for two connected browsers at once.

> This exists because a run once treated browser selection as needing confirmation, silently skipped the logged-in source for a whole cycle, and reported nothing unusual.

> **Some browser tools filter what a page script can return.** Long digit strings, which is exactly what job IDs are, can trip a data guard and lose the whole result. Accumulate into a variable on the page, return only its length, then retrieve the contents in a second short call.

### Technique: volume management

**Everything else in this file was designed for a search returning a handful of roles a cycle. Below the senior band that assumption breaks**, and the failure is quiet: the run spends its whole budget researching role forty of two hundred, never reaches half its sources, and reports a normal-looking digest.

**Four rules, in order of how much they save:**

1. **Cap the scored table, not the search.** Score down to the cap from Q0 of the setup interview. Everything else that cleared the hard filters gets a one-line row in BELOW THE CAP: title, company, link, date found. Nothing is dropped, and nothing below the cap costs research time.
2. **Research per company, not per role.** One employer with nine openings is one culture lookup and one stability lookup, cached with its verification date. This alone can cut research time by half in fields where large employers post constantly.
3. **Filter before you research, never after.** Hard excludes and the location filter run on the posting text, which is already in hand. Culture and stability research runs only on what survived and made the cap.
4. **Deduplicate before scoring.** The same requisition reaches the table three times from three sources with three URLs. Match on employer plus title plus location, keep the most durable link (company ATS over aggregator), and note the other sources on the row.

**Tie-breaking at high volume**, since a third of the table will share a score. In order: disclosed comp, higher first · posting date, newer first · application friction, lower first (a five-minute form beats a portal that rebuilds your resume by hand) · direct employer posting over an agency repost.

> **Apply-rate honesty belongs in the digest at these levels.** Track applications sent per cycle against roles surfaced. A bot surfacing forty roles a week into a search sending two applications a week has a throughput problem, not a sourcing problem, and no amount of better search fixes it. Say that plainly rather than sourcing harder.

**Watch for the opposite failure too.** If a cycle returns hundreds of roles and the top of the table still looks wrong, the target titles in Q2 are too broad, not the filters too loose. Fix the query, not the rubric.


---

## Verification Techniques

Sourcing finds candidates for the table. This decides what's actually true about them. **Most of the wrong rows in a tracking file got there by trusting a field that looked authoritative and wasn't.**

### The authority order

When two sources disagree about a posting, they are not equally wrong. In descending order:

1. **The requisition page itself**, on the employer's own ATS.
2. **The employer's own website.**
3. **A retained recruiter's listing**, which usually carries the role as briefed.
4. **A job board's listing page.**
5. **An aggregator, a board's API, or a similar-jobs card.**

**Cross-referencing is encouraged.** Pull office address, onsite cadence, comp, and scope from the employer's site whenever the posting is thin.

### Rule: only the posting's own workplace-type field decides the arrangement

**This is the most common way a role gets tabled wrong, and it fails in two directions.**

- **A board's geo tag can show a posting under the viewer's own city**, inventing a local role that is actually remote and elsewhere. It can also hide a genuinely remote role under a city.
- **An ATS API's remote boolean is not the posting's workplace-type field, and they disagree systematically.** This is a property of the APIs, not a run of bad luck. One board carried dozens of records reading `isRemote: true` alongside `workplaceType: "Hybrid"`, with named office cities attached. The boolean is a coarse eligibility flag; the workplace-type field is the per-requisition arrangement.

> **Where an API exposes both fields, read the workplace-type one and ignore the boolean.** On Ashby that pair is `workplaceType` (`Remote` / `Hybrid` / `OnSite`, the answer) and `isRemote` (noise). A worked pair from one day: one req read `workplaceType: Remote` despite a city on its card and correctly passed the location screen; another read `workplaceType: Hybrid` and correctly failed. **Both carried `isRemote: true`.** If your sweep script touches this API, have it print the workplace-type field next to every location so the right field is the one on screen.
- **A location string naming a specific city is evidence against remote, not decoration alongside it.** A "remote" role whose posting names a city and whose description talks about that local market is a hybrid role with a stale flag.

**Open the posting and read its own workplace field.** Everything else is a hint.

### Rule: resolve the link before the row is ever shown

**Freshness re-verification only protects rows already in the table, so on a first cycle it protects nothing.** Two independent testers reported the same thing: a first digest whose top-ranked roles and below-the-cap links opened to "page not found." Nothing was broken. **No rule verified a link before its first appearance**, because freshness covers existing rows, the reliability gate is diagnostic and explicitly never screens, and below-the-cap rows are exempt from research entirely.

**Resolve every link that will be presented, before research and before scoring.** Three states, and the third is not a soft version of the second:

| State | Means | Evidence required |
|---|---|---|
| **live** | The requisition page renders | The rendered page |
| **expired** | The posting is closed | The rendered page saying so, **or** an expiry marker in the redirect URL |
| **unverified** | The check could not run | Timeout, block, JS-only render, unresolvable host |

- **A failed check is never an expiry.** This is the same rule as "absence from a board is not expiry" and "a 404 from the ATS's own API is not expiry," applied one step earlier. Marking an unreachable posting dead is the false negative this file already documents three times.
- **Check before scoring, not after.** A confirmed-dead row is not researched and not scored, which is the cheapest place to save the work. Score it if it comes back.
- **Below-the-cap rows need this most.** They carry a clickable link and get no research on any cycle, so without an entry check their links are never verified at all. They are also the cheapest rows to batch: one line each, many sharing an origin.
- **Batch by origin.** A same-origin fetch over several job IDs returns each requisition's final URL and title in one call, which is what makes checking twenty rows affordable.
- **A dead link is a question, not a verdict.** Before writing a role off, check the employer's own board for a replacement requisition. **A repost is a live role behind a dead URL**, and it enters as a new row. This is the highest-value output the check produces, and it is the "boards answer the opposite question" rule below, used the useful way round.

> **Why this is a screen and the reliability gate is not.** The gate deliberately never removes a role, because a good role behind a stale posting should not lose points it deserves. That reasoning is about **scoring**. Whether a link opens is not a quality judgment, and a link that 404s should not be presented as a link.

### Rule: freshness re-verification, at the start of every cycle

**Run it before sourcing anything new.** Postings close continuously between runs, and a search that only ever looks for new roles will quietly fill its table with dead links.

Priority order, and don't let it expand past the first two categories when time is short:
1. Rows whose apply link is a generic listing page rather than a direct requisition.
2. Onsite/hybrid roles (smaller applicant pools close faster) and rows not re-verified in the past week.
3. Everything else, time permitting.

> **A week, not a fortnight.** This started at two weeks and was tightened after three rows went stale in a single day and the user caught all three before the pass did. **Don't expect any interval to catch everything:** a posting that lives 48 hours slips through every interval, and only checking every row every cycle would catch it, which isn't worth the time for one row in a hundred.

### Rule: check that the posting still says what it said

**A live-check that only tests existence misses the most damaging change there is.** One posting was confirmed live and unflagged, then quietly gained a hard credential requirement the candidate didn't hold, along with a rewritten title. The user found it while applying.

- **Re-read the title and the requirements, not just the HTTP status.**
- **Long-running requisitions are where titles mutate.** Prioritize rows older than about three weeks; a repost or a near-duplicate requisition number signals a rewrite.
- **The change *is* the finding.** Say so explicitly in the row and re-score. Don't silently update the cell.

### Rule: absence from a board is not expiry

**Only the direct requisition link is authoritative for whether a role is dead.** In one pass, board APIs produced a false negative on every ATS row checked: three requisitions were missing from their public board feeds and all three were live at their direct URLs. Requisitions are routinely live and linkable while unlisted, which is normal for confidential and executive searches.

> **Boards are good for the opposite question:** is there a *replacement* requisition? A role is safely called dead when its direct link 404s **and** the board carries no equivalent seat.

**The harder version: an explicit 404 from the ATS's own per-requisition API is still not expiry.** Absence from a listing is easy to discount. A positive "not found" from the system of record feels authoritative, and it isn't.

> **Worked example.** One ATS's board JSON omitted a requisition entirely, and its per-requisition endpoint returned `{"ok":false,"error":"Document not found"}`. The rendered requisition page served HTTP 200 with the full description, unchanged title, unchanged remote status, and unchanged reporting line.
>
> **Two JSON surfaces agreeing is not corroboration when both read the same listing flag.** They are one source wearing two hats. Only the rendered requisition page settles it, so open the page.

### Technique: expiry markers and batched checks

- **Job boards usually mark expiry in the URL.** A dead posting often redirects to a generic search page carrying a tracking parameter that names the redirect as an expiry. That parameter is definitive and cleaner than reading page text, and it's distinct from the "no longer accepting applications" banner a posting shows while still on its own page.
- **⚠️ Match the parameter a board actually sends, never a reasoned-out guess at it.** The largest board abbreviates the middle word of its marker, so a matcher built from the spelled-out spellings missed every expiry that board produced while looking like it worked. **If the check finds no expiries at all across several cycles, suspect the matcher before believing the market.**
- **Some closure pages say three words and stop.** A banner matcher tuned to full sentences walks straight past them, so keep the terse forms in the list alongside the sentences.
- **Batch the checks from a page already on that origin.** A same-origin fetch over several job IDs returns each requisition's final URL and title in one call, which turns a four-row freshness check into one request.

### Technique: dating a posting for free

Three ways to establish age or change without spending a fetch.

| Method | How it works | What it's good for |
|---|---|---|
| **ID interpolation** | Job IDs on the large boards increase monotonically at a fairly steady daily rate. Interpolate an unknown ID against two known-dated ones. | A promising search hit that turns out to be a stale index entry from many months ago |
| **The indexed slug** | Boards build a URL slug from the title at posting time; search engines freeze it at crawl while the page title updates live. When the two disagree, the edit is dated with no archive needed. | Proving a title changed, and roughly when |
| **A named incumbent** | Someone publicly announcing they've started in that seat resolves a row that would otherwise sit unverifiable. | Portals that won't render, ambiguous links |

Two cautions:

- **ID interpolation is a pre-filter, not a verification.** A low ID means deprioritize. It never means the role is dead, and it doesn't mean skip a role that would otherwise top the table.
- **A repost resets the displayed date but not the ID, so a "1 day ago" card can be a month-old requisition.** One posting showed "reposted 21 hours ago" against an ID interpolating to roughly four weeks earlier. This matters more than it sounds: a reposted req re-enters the past-week window every time, arriving as a fresh find in cycle after cycle. **Interpolate the ID before treating a new-looking card as net-new.**
- **An incumbent only dates a requisition if their tenure is current.** Profile aggregators keep showing people in seats they left years ago. Confirm start *and* end dates before reading an incumbent as a closure signal.

### Technique: apply-link rules

- **The link must resolve to the specific requisition, not a careers index.** When only an index page exists, use it, but add an explicit `**Apply link unconfirmed, generic listing page**` note and prioritize that row in the next freshness pass. One role was lost exactly this way: the link was a generic careers index, and by the time the user checked manually the role was gone.
- **Prefer the company's own ATS or careers link** over any aggregator link. A job board's URL is fine when nothing more durable exists.
- **Never guess a careers-site host.** The no-path-guessing rule covers hostnames, not just endpoint paths, and this is the more dangerous half. **A guessed host can return a confident, specific, wrong answer**, which beats a 404 for damage because it reads as authoritative and nothing prompts a second look.

> **Worked example.** A guessed host built from the parent company's name served "the job you are trying to apply for has been filled" for a live requisition. The real host was the operating brand's own domain, where the same req rendered in full and its apply flow worked. A plausible hostname is not a confirmed one: take the host from a search result or from the posting's own apply link.

### Technique: capture the description for every applied role

**A posting the user applied to will close, and then the description is gone exactly when they need it for interview prep.** Save it while the req is still reachable, as a file in the project folder, one folder per role.

- **Capture at the cycle that first sees the role staged as applied.** Users apply between cycles, so nothing enforces this unless the run checks. Cross-check the tracking files against the folder every cycle and report the result even when nothing is missing, since a silent pass and a skipped check look identical.
- **Check before you capture. This one bit hard.** A run once found four newly-applied roles, generated fresh files, and overwrote the user's own hand-saved captures without reading them first. They were recovered from git. **The test is "does a capture already exist for this role," and the answer "yes" means do nothing.**
- **A browser capture of the live page beats a generated one.** `scripts/jd2pdf.py` renders a posting's own description block verbatim to PDF and is the fallback for reqs the user can no longer reach, not the default path for roles they still have open.
- **Never fabricate or paraphrase a description.** If it can't be retrieved, say so and move on. The file is only worth having if it's verbatim.
- **Roles that arrived inbound from a recruiter are a different set** from roles the user applied to. Keep them apart, or the record stops answering "what did I actually pursue."

### Technique: a title string on a page is not a listing

**A keyword match on a firm's website is not evidence of an open role.** Recurring false positives, all of which have burned a cycle at least once:

- A **testimonial byline** ("Director of Operations, {{COMPANY}}"), naming a past placement.
- An entry in a **function or practice-area menu**, listing what the firm recruits for.
- A **soft 404**, which returns the full site navigation (often 100KB of it, exec titles included) instead of a status code, so a keyword hit means nothing.

**This is a parsing verdict, never a verdict on the firm.** The board is usually real; the regex hit the wrong part of the page. Don't retire a source over it.

### Rule: remote is not location-free

**A genuinely remote role can still carry a time-zone or state-residency restriction, and it is frequently invisible until the application form.** Two cases in two days on one search: one fully remote role died on an Eastern-time residency requirement caught just before applying; another advertised two continents, named no zone anywhere in the posting, and asked which time zone the candidate works in **on the application form itself**.

- **Not screenable at sourcing time.** Neither the board card nor the JD body carried it in either case, so a screen would fire on an inference.
- **It is a question to ask early and a flag to record the moment it surfaces.**
- **A form asking which zone you work in is not the same as a stated requirement.** Preference and hard screen are indistinguishable there, and only the recruiter settles it. Leave the row live and flag the ambiguity.

### Rule: an undisclosed employer inherits the poster's geography, as a presumption

**When a requisition hides the employer and the poster owns the company, the poster's metro is the row's presumptive location.** One anonymized role named no city, no state, and no work arrangement, so the location filter could not run at all and the row went to the user with location as the open question. The posting's own author was the talent lead at the private-equity firm that owns the company, and that firm's metro was sitting in plain sight.

- **Write it as a presumption, not a finding:** `presumed <metro>, inherited from the posting's owner`. Screen the row on it, and reopen immediately if a posting names a city or a remote arrangement.
- **It applies only when the poster owns the company.** A third-party recruiter's metro says nothing about the client's, so this never extends to search firms or reposters.
- **What it saves is a full research pass on a row that was already unlikely. What it risks is a genuinely remote role reading as excluded**, which is why it stays a presumption with a named reopen condition.

### Technique: the scope-ownership test

**For any role where the title suggests broader scope than the duties deliver.** Applies to any blended or hybrid-scope target, at any level.

- The scope only counts if the role explicitly **owns** the function, not "partners with," "collaborates with," "supports," or "reports to" it.
- A title listing adjacent functions as partners is describing ordinary cross-functional relationships that any role at that level has. That is not ownership.
- **Read the actual duties, not the reporting line or the title.** A role can report into the right place, name all the right partner functions, and still be 100% the narrow version of the job.

> This rule exists because a role was logged as the closest match in months on exactly that reasoning, then corrected on a read of the duty list.

**The junior version of this is title inflation, and it's more common.** Coordinator, Associate, and Specialist titles are handed out for work that is entirely administrative support to the function rather than the function itself. Same test, applied downward: if the duty list is scheduling, data entry, and note-taking for the team that does the work, the title is decoration. Flag it in Key Context rather than excluding it, since these are still legitimate ways in.

> **Confirm before excluding, when the exclusion would be permanent.** An ambiguous posting screened out on a first read takes the comp, ownership, and reporting facts with it, and those often only surface on a direct read or at a screening call. Flag and ask; don't quietly close.

### Technique: the reliability gate, run once when a role enters the table

**Some postings are not real, current openings.** Three kinds, and all three are common enough to be worth one check rather than none:

- **Ghost postings.** A requisition the employer has no intention of filling now, kept up to bank resumes or to look like the company is growing.
- **Recycled postings.** The same requisition reposted every few weeks so it reads as fresh. The seeker applies to something that has been sitting for months.
- **Fabricated postings.** A role that does not exist, posted to harvest candidates.

**Every check below already exists elsewhere in this file.** What the gate adds is a place where they are asked *together, about one posting, at the moment the user is deciding whether to spend an hour on it.* Verification rules scattered across a technique list are each correct and none of them is a question anyone answers.

| # | Check | Trips when | Defined in |
|---|---|---|---|
| **R1** | **Posting age vs. displayed date.** Interpolate the job ID | The ID implies **3+ weeks older** than the displayed date | *Dating a posting for free* |
| **R2** | **Prior appearance.** Grep the resolved index for company + title | The same seat resolved before, on **any** outcome | Dedupe index, `scaffolding.md` |
| **R3** | **Employer named.** Is there a real company on the posting | The employer is stripped, "Confidential," or unidentifiable | *Recruiter and undisclosed-employer postings* |
| **R4** | **On the employer's own board.** Is the requisition on their careers page or ATS | The employer is named, their board is readable, and the requisition **is not on it** | *Apply-link rules* |

**Two or more trips writes one `Reliability flag: <clause>` into Key Context.** One trip writes nothing.

- **The clause says what tripped in plain words.** `Reliability flag: live since ~April, not on the employer's own board` beats a code.
- **The gate never screens a role out and never changes a score.** The scoring rubric measures job quality. Whether a posting is a real current opening is a different question and deserves a different output, or a good role behind a stale posting silently loses points it should not lose.
- **It never blocks a firm either.** Blocked-poster entries are the user's call, on the named-firm rule above. **The gate may propose nothing to that list.**

#### The guardrails matter more than the checks

> **⚠️ R3 alone never flags, and R3 plus R4 is not two trips.** An undisclosed-employer posting trips R3 by construction and cannot be checked against a board it has no name for. **Counting those as two makes the gate an automatic flag on every anonymous posting**, which is the class penalty the recruiter-posting technique above exists to prevent. At senior levels those postings are a real channel and some of the best roles arrive no other way.
>
> **On an undisclosed-employer posting, R3 and R4 together count as one trip**, so a flag there needs R1 or R2 as well.

- **A check that cannot run is `not assessed`, never a pass and never a trip.** Same convention as an unassessable scoring bucket. **R1 does not run where there is no interpolatable ID**, and inventing an age is worse than leaving it blank.
- **R4 never guesses a careers host.** An unresolvable host, an unreadable board, or a JS-only render is `not assessed`. A guessed 404 reads as a finding and is not one.
- **R4 is not the board-absence rule reversed.** Absence from a *third-party* board is still not expiry. R4 asks about the **employer's own** board, where a missing requisition is a real signal for a role the employer is advertising elsewhere.
- **R2 firing on a role the user already declined routes to the prior-decision rule**, which asks them. R2 here is mostly catching a seat that closed and came back.

**Cost is one network call.** R1 and R2 are free, R3 is a read of a posting the cycle already opened, and R4 is the only fetch. **On a role sourced from the employer's own ATS, R4 is already answered** by the apply-link rule and costs nothing.

> **State a retirement condition when the gate is turned on.** If two months of flags never once change what the user does, take it out. **A flag nobody acts on is a tax on every row**, and a caveat that is always present stops being read.

### Technique: the years-of-experience line

**Treat a posted experience requirement as a signal, not a gate.** Postings routinely ask for more than the role needs, and the requirement is often written by someone who wasn't the hiring manager.

- **Within roughly 2 years under the ask:** apply normally, no flag.
- **3 or more years under:** table it with a stretch flag and the gap noted, rather than filtering it out. Their call.
- **Substantially over the ask:** flag it as a possible level mismatch. An overqualified application is a real screen-out risk and worth knowing before the time is spent.
- **A hard credential, license, degree, or clearance requirement is different** and does gate. Those come from Q1 and screen like any hard filter.

> **Never let the bot silently drop a role on the years line.** It's the single most common false exclusion at early-career and mid levels, and it removes exactly the roles that would have been a step up.

