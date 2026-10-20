# Wall-E Search Methodology: Sam Rivera

### Search Integrity
Follows the Search Integrity rules in the Bishop job-search skill's
search-techniques.md, read there every cycle. Nothing is copied in here.

### Sources
Rigor is light (Reference_Profile.md, Customization), so only Tier A runs; every
other tier reports `OFF-CADENCE` on every cycle, never a nil.

| Source | Tier | Cadence | Verdict | Last tracked role |
|---|---|---|---|---|
| Company hiring systems (ATS site-search, the full host set) | A | every cycle | live, seeded | 2030-02-25 |
| Named employers, swept from Employer_Index.md | A | every cycle | live; promoted from the Tier B seed at setup [DL-S2] | 2030-02-21 |
| Startup investor job pages (`getro` in the coverage line) | B | Monday | seeded; OFF-CADENCE under light rigor | none yet |
| Big job-listing sites, mined for company names | C | weekly | seeded; OFF-CADENCE under light rigor | none yet |
| LinkedIn (logged-in session, sweep, pay check) | none | never | declined at setup [DL-S1] | n/a |
| Field-specific association boards | none | n/a | not set up ("Your field's sources" not run) | n/a |

### Queries
| Stem | Filter results to | State |
|---|---|---|
| `"Field Service"` | Director, Senior Director, VP, and Head of seats | live |
| `"Field Operations"` | Director, Senior Director, VP, and Head of seats | live |
| `"Service Operations"` | Director, Senior Director, VP, and Head of seats | live |
| `"Service Delivery"` | VP and Head of seats (peer function) | live |
| `"Customer Operations"` | Director and VP seats (peer function) | trial, review 2030-03-07 |

```
("Field Service" OR "Field Operations" OR "Service Operations" OR "Service Delivery" OR "Customer Operations") AND (Director OR "Senior Director" OR VP OR "Vice President" OR "Head of")
```

### Standing Techniques
Per search-techniques.md. Deviations:

- **Named-employer sweep:** run `employer_sweep.py`, from scripts/ in the Bishop plugin's job-search skill directory (absolute path in Operating_Procedures.md's File Map), against Employer_Index.md every cycle. Its per-board counts go into the COVERAGE line as printed. The index's unresolved row is a coverage gap, reported as such.

### Verification
Per search-techniques.md. No deviations.
