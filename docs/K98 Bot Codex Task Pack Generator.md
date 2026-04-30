# K98 Deferred → Codex Task Pack Generator

## Purpose
Convert structured deferred optimisation items into a scoped, Codex-ready delivery pack.

## Input Sources
Use one or more:

- `/docs/deferred_optimisations.md`
- GitHub Issues labelled `deferred`
- GitHub Issues labelled `batch-candidate`
- GitHub Project column `Grouped`
- PR review notes
- Previous task “Deferred Optimisations” section

## Step 1 — Import Deferred Items

Paste structured items here:

```md
### Deferred Optimisation
- Area:
- Type:
- Description:
- Suggested Fix:
- Impact:
- Risk:
- Dependencies:
Step 2 — Score Items

Apply the scoring model from K98 Deferred Optimisation Scoring Model.md.

Item	Area	Type	Impact	Frequency	Risk	Effort	Score	Recommendation
								
Step 3 — Group Items

Group items when they share one or more:

same module
same subsystem
same architecture concern
same service/repository boundary
same UI/view layer
same cache or persistence pattern

Do not group unrelated high-risk items just because they are nearby.

Step 4 — Select Batch
Batch Name

<Subsystem> <Theme> Optimisation Pack

Batch Goal

Describe the target improvement in 2–4 lines.

Included Items
Item	Reason Included
	
Excluded Items
Item	Reason Excluded	Future Batch
		
Step 5 — Generate Codex Task Pack
Codex Task Pack — <Batch Name>
Required Reading

Read and follow:

Feature / optimisation batch overview
K98 Bot — Project Engineering Standards.md
K98 Bot — Coding Execution Guidelines.md
K98 Bot — Testing Standards.md
K98 Bot — Skills & Refactor Triggers.md
K98 Bot — Deferred Optimisation Framework.md
K98 Code Prompt v3.md
Objective
<Batch goal>
Source Deferred Items
<Paste included deferred items>
Scope
In Scope
Out of Scope
Mandatory Workflow

Follow K98 Code Prompt v3.

Stop after:

Audit
Architecture validation
Implementation plan

Do not code until approval unless explicitly told this is a one-pass task.

Audit Requirements

Review:

direct SQL in commands/views
business logic in interaction layers
duplicate helpers
dead code
cache and persistence safety
restart safety
test coverage
logging quality
Target Architecture
Concern	Target
Commands	commands/<domain>_cmds.py
Views	ui/views/
Services	subsystem service module
DAL / Repository	repository module
Shared helpers	core/ or existing helper
SQL schema	SQL repo sql_schema/...
Tests	tests/
Likely Files to Review
Likely Files to Modify
Implementation Requirements
Keep commands and views thin
Move business logic into services
Move data access into repository/DAL
Reuse existing helpers
Preserve restart safety
Add or improve logging
Add/update tests
Do not expand scope
Capture new out-of-scope findings as deferred optimisations
Testing Requirements

Include:

happy path
negative path
regression
permission boundary where relevant
restart/persistence where relevant
cache safety where relevant

Suggested commands:

python -m black --check .
python -m ruff check .
python -m pyright
python -m pytest -q
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
Acceptance Criteria
 Included deferred items are resolved or explicitly re-deferred
 Commands/views remain thin
 Business logic is service-owned
 No new direct SQL in commands/views
 Helper reuse checked and documented
 Logging is adequate
 Restart safety preserved
 Tests added/updated
 Quality gates run or documented
 New deferred items captured structurally
Required Output

Use the strict output format from K98 Code Prompt v3.

PR Summary Template
Summary
Changes
Tests
Deferred Optimisations
Risk / Rollback
