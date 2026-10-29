# Contracts between Bishop's modules

What each module reads from another module's files, exactly. For the maintainer; users never see this.

> **The rule.** A module writes only its own files. It reads another module's files only through an entry here.
> - **A part not listed here:** change it freely.
> - **A listed part:** bump that contract's version, update every reader in the same change, and pass `python tests/run_all.py`, which checks every entry against the made-up test candidate in `tests/candidate/`.

## Who owns what

| Module | Writes (owns) | Reads from others |
|---|---|---|
| **Front door** (`skills/start`) | `Bishop_Setup.md` (which modules were picked, and where setup stands), the saved resume `Resume.<ext>` | Nothing; it only checks which Bishop files exist |
| **Job search** (`skills/job-search`) | `Reference_Profile.md`, `Methodology.md`, `Operating_Procedures.md`, `Decisions_Log.md`, `Tracking_*.md`, `Audit_Log.md`, `Employer_Index.md`, `Weekly_Check.md`, the scheduled tasks | Nothing |
| **Dashboard** (`skills/dashboard`) | `dashboard.html` and its published page | Profile, procedures, tracking (contracts 1 to 3) |
| **Interviews** (`skills/interviews`) | `Interview_Prep/`: deck folders and built decks. The candidate's answers live only in their browser | Profile, tracking (contracts 1 and 3), and the saved resume, read as a whole document |
| **Outreach** (`skills/outreach`) | `Outreach/`: `segments.json`, `settings.json`, `outreach.html`, a hand-picked group's names file. Contacts and the board live only in the browser | Profile, tracking, employer index (contracts 1, 3 and 4) |

## Format versions

**Each file named in a contract carries its format version, so a reader can tell what it's reading.**
- **Markdown files:** a comment on the first line, `<!-- bishop-format: <file> <version> -->`, for example `<!-- bishop-format: profile 1 -->`. Setup writes it.
- **A file with no such line is version 1.** Every search set up before 2.0 has none, and keeps working untouched.
- **A reader that meets a version it doesn't know** says so in one plain line and stops, rather than guessing.

## 1. The profile: `Reference_Profile.md` (profile, version 1)

| Part read | Read by | Used for |
|---|---|---|
| `Bot Name` section: the search's name (or the title line, `# <name> Reference Profile: <person>`) | Dashboard, interviews, outreach | The dashboard header and page title; the name in the deck's and the board's top bar |
| `Customization` section: accent color, any accessibility adjustments the user asked for later (setup doesn't ask), where the digest link goes | Dashboard; outreach reads the accent only | The page's accent, its text, contrast, motion and colorblind settings, and where the link is delivered; the board's accent |
| `Motivator Buckets` section, in listed order (the list order is the rank order) | Dashboard | One check per bucket on each role card, in the candidate's order |
| `Career Level` section: the rung and the band | Interviews | Which behavioral layers the master deck asks, and the level the questions are pitched at |
| `Current Role` section | Interviews | Opening and tough questions |
| `Full Career History` section: the table of period, role, company, highlights | Interviews; outreach reads the company column only | Tenure, gap and pivot questions; resume questions when there's no resume file; "worked there" on the board |
| `Target Roles` section | Interviews | Technical questions, and the level the candidate is interviewing for |

## 2. The procedures: `Operating_Procedures.md` (procedures, version 1)

| Part read | Read by | Used for |
|---|---|---|
| The tracking-table format: the column list and what each column holds | Dashboard | Parsing the tracking files (contract 3) |

## 3. The tracking files: `Tracking_<Track>.md` (tracking, version 1)

| Part read | Read by | Used for |
|---|---|---|
| The track's name (from the file name) | Dashboard | One track label per file |
| The live tables (ACTIVE / ROLLING, and BELOW THE CAP when a search has one), every column per contract 2 | Dashboard | A card per role: score, company, title, pay, location, bucket checks, flags, apply link |
| The stage at the start of each row's Key Context: `**Stage: open\|applied YYYY-MM-DD\|interviewing YYYY-MM-DD** · Posting: live\|expired YYYY-MM-DD\|unverified`, then `next: …` and, on applied rows, `follow up YYYY-MM-DD` | Dashboard, interviews | The dashboard's stage filters and next steps; interviews finds the role an interview is for |
| A role's posting link and its notes | Interviews | The posting a company deck is built from |
| The company column of the live tables | Outreach | The "in your job search" group type |
| The search notes block (the run log and the sources line) | Dashboard | The header's run line and the square per source |

## 4. The employer index: `Employer_Index.md` (employer-index, version 1)

| Part read | Read by | Used for |
|---|---|---|
| The employer list (names) | Outreach | The "in your job search" group type |
