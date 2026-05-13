Quality Automation + Review System (v1)
🎯 Objective

Implement a complete quality enforcement + review system that:

Enforces K98 architecture rules automatically
Prevents common Codex mistakes (SQL in commands, logic leakage, etc.)
Standardises PR quality
Introduces a mandatory Codex Review Pass
Improves consistency, reliability, and maintainability

This aligns with modern best practice where structured reviews + automation catch issues that tests alone miss

📚 Required Reading (MANDATORY)

Read in this order:

README-DEV.md
AGENTS.md
K98 Bot - Project Engineering Standards.md
K98 Bot - Coding Execution Guidelines.md
K98 Bot - Testing Standards.md
K98 Bot - Deferred Optimisation Framework.md
⚠️ Critical Rules
DO NOT expand scope
DO NOT refactor unrelated systems
ALL improvements outside scope → Deferred Optimisation
Step 1 MUST be review only (unless explicitly told otherwise)
🧩 Scope

Create / update:

.github/pull_request_template.md
.github/workflows/quality.yml

scripts/validate_architecture_boundaries.py
scripts/validate_deferred_items.py
scripts/select_tests.py

docs/templates/K98 Bot Standard Development Initiation Statement.md
AGENTS.md
README-DEV.md

tests/test_validate_architecture_boundaries.py
tests/test_validate_deferred_items.py
tests/test_select_tests.py
🏗️ Implementation
1. PR Template (MANDATORY)

Create:

.github/pull_request_template.md
## Summary

## File Manifest

## Helpers Reused

## SQL Changes

## Architecture Checks
- [ ] Commands remain thin
- [ ] Views remain interaction-only
- [ ] Services own business logic
- [ ] No SQL in commands/views
- [ ] Restart safety preserved

## Tests Run

## Deployment / Migration Notes

## Codex Review Pass
- [ ] Review pass completed
- [ ] Issues fixed or deferred
- [ ] No scope expansion during review

## Deferred Optimisations

### Deferred Optimisation
- Area:
- Type:
- Description:
- Suggested Fix:
- Impact:
- Risk:
- Dependencies:
2. Architecture Validator

Create:

scripts/validate_architecture_boundaries.py

Must:

FAIL if:
SQL keywords found in commands/
DAL imports in ui/views/
Discord types in services
WARN if:
New root-level files created
Allow override:
# architecture-check: allow
3. Deferred Optimisation Validator

Create:

scripts/validate_deferred_items.py

Must:

PASS ONLY IF:

All items follow:

### Deferred Optimisation
- Area:
- Type:
- Description:
- Suggested Fix:
- Impact:
- Risk:
- Dependencies:
FAIL if:
vague phrases like:
"improve later"
"todo"
"future work"
4. Test Selector

Create:

scripts/select_tests.py

Maps file changes → recommended tests

Examples:

Area	Tests
commands/stats	test_stats_service, test_mykvkstats
ark/	test_ark_*
mge/	test_mge_*
event_calendar/	test_calendar_*
ui/views/	test_ui_imports

Always include:

python scripts/smoke_imports.py
python scripts/validate_command_registration.py
5. GitHub Actions Workflow

Create:

.github/workflows/quality.yml

Run on PR:

python -m black --check .
python -m ruff check .
python -m pyright

python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py

python -m pytest -q tests

python scripts/smoke_imports.py
python scripts/validate_command_registration.py

⚠️ Only run tests from /tests

6. AGENTS.md Update

Add:

### Review & Validation Rules

- When tests fail:
  - Fix only if related to the task
  - Otherwise document and do NOT expand scope

- Before PR:
  - python scripts/validate_architecture_boundaries.py
  - python scripts/validate_deferred_items.py
  - python scripts/select_tests.py
7. Initiation Statement Update

Add new step:

Step 7 — Codex Review Pass (MANDATORY)

After implementation and testing:

Perform a read-only audit

MUST validate:
Architecture compliance
Refactor triggers
Test coverage correctness
Restart/state safety
Logging quality
MUST NOT:
Expand scope
Add features
Perform large refactors
Required Output
## Codex Review Summary

### ✅ What is correct

### ⚠️ Issues found (fix now)

### 🧩 Deferred Optimisations

### 🧪 Test Gaps

### 🔁 Restart / State Risks

### 📊 Overall Assessment
8. README-DEV Update

Add:

## Quality Automation

Run before committing:

python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/select_tests.py

pre-commit run -a
pytest -q tests
🧪 Tests

Create:

tests/test_validate_architecture_boundaries.py
tests/test_validate_deferred_items.py
tests/test_select_tests.py
Must cover:
SQL in command → FAIL
allow override works
deferred format valid → PASS
vague deferred → FAIL
test selector maps correctly
✅ Acceptance Criteria
PR template enforced
CI runs validation scripts
Architecture violations caught
Deferred items structured
Codex Review Pass added
Test selector functional
Docs updated
🚫 Out of Scope
No large refactors
No subsystem redesign
No production deployment changes
🧠 Why this matters (quick reality check)

Without this:

issues slip through despite good instructions
Codex behaves inconsistently
review quality depends on luck

With this:

every PR is checked against the same rules
architecture drift is prevented early
small issues are caught before production

Structured reviews + automation are proven to significantly improve code quality and reduce defects early in the lifecycle
