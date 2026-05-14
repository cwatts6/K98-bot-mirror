Codex Task Pack - Audit and Optimise registry_cmds

## 1. Task Header

- Task name: `registry-cmds-audit-and-optimisation`
- Date: `2026-05-13`
- Owner/context: `K98 bot command standardisation pass after stats_cmds and telemetry_cmds`
- Task type: `refactor | deferred optimisation batch`
- One-pass approved: `no`

## 2. Required Reading

Before implementation, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the conditional reference order defined there.

For SQL-facing work, validate schema, procedures, views, indexes, and contracts against:

`C:\K98-bot-SQL-Server`

Also review:

- `commands/registry_cmds.py`
- `registry/registry_service.py`
- `registry/governor_registry.py`
- `registry/registry_io.py`
- `registry/dal/`
- `ui/views/registry_views.py`
- `ui/views/admin_views.py`
- `target_utils.py`
- `tests/` registry-related coverage
- `docs/deferred_optimisations.md`
- GitHub issues relating to registry, registration, governor lookup, import/export, audit, or command architecture

## 3. Objective

Audit, standardise, optimise, and enhance `registry_cmds.py` so it follows the same command-layer quality standard as the recently improved `stats_cmds` and `telemetry_cmds`.

The outcome should be a thinner command module, clearer service/DAL ownership, better helper reuse, safer import/export flows, stronger tests, and structured deferred optimisation capture for anything intentionally left out.

## 4. Background

`registry_cmds.py` is a significant command file covering:

- `/register_governor`
- `/modify_registration`
- `/remove_registration`
- `/remove_registration_by_id`
- `/my_registrations`
- `/admin_register_governor`
- `/registration_audit`
- `/bulk_export_registrations`
- `/bulk_import_registrations_dryrun`
- `/bulk_import_registrations`

Current observations from the uploaded file:

- Command handlers contain substantial business logic.
- There are duplicate helpers for account slot lists, user ID parsing, GovernorID extraction, GovernorID normalisation, role extraction, Excel-safe formatting, registry loading, and roster-cache access.
- Some logic uses `load_registry()` while other paths use `registry_service.load_registry_as_dict()`.
- Some commands import service functions inline.
- Several flows read `target_utils._name_cache` directly.
- Bulk import/export/audit handling is valuable but command-heavy.
- There is a mix of interaction response patterns.
- Some paths already use SQL-backed service logic and should be preserved.
- No matching open GitHub issue was found from connected issue search for registry/registration/governor deferred work, so this task should perform a fresh audit and also check local deferred optimisation docs.

## 5. Scope

### In Scope

- Full audit of `commands/registry_cmds.py`.
- Identify and remove duplicate helpers where safe.
- Move business logic from command handlers into registry service/helper modules.
- Standardise account-type autocomplete source.
- Standardise GovernorID validation and roster lookup.
- Standardise registry loading behaviour and SQL failure handling.
- Review admin/user permission boundaries.
- Review import/export/audit workflows for maintainability and reliability.
- Add or improve tests for command-adjacent logic.
- Capture out-of-scope findings as structured deferred optimisations.
- Review GitHub issues and deferred optimisation docs before implementation.

### Out of Scope

- Redesigning the entire registration UX.
- Replacing the SQL registry model unless required for correctness.
- Large database migrations unless the audit finds a blocking schema mismatch.
- Rewriting unrelated commands.
- Changing command names without separate approval.
- Changing player-facing copy beyond clarity and consistency improvements.

## 6. Source Deferred Items

Codex must search:

- `docs/deferred_optimisations.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- GitHub issues in `cwatts6/K98-bot-mirror`
- GitHub issues in `cwatts6/K98-bot`

If matching items are found, list them here before implementation:

```md
### Deferred Optimisation
- Area: Registry commands
- Type: architecture | cleanup | refactor | consistency
- Description:
- Suggested Fix:
- Impact:
- Risk:
- Dependencies:

If no existing items are found, state that explicitly.

7. Codex Skills To Use
Skill	Decision	Notes
k98-architecture-scope	use	Required before implementation because this is a significant command-layer audit/refactor.
k98-discord-command-feature	use	This task touches slash commands, autocompletes, views, admin boundaries, and user-facing flows.
k98-sql-validation	use	Registry is SQL-backed and import/export/audit paths depend on SQL contracts.
k98-test-selection	use	Required before validation to select focused registry tests plus architecture gates.
k98-deferred-optimisation-capture	use	Audit may uncover debt that should not be fixed in this pass.
k98-pr-review	use	Required before PR handoff.
k98-promotion-check	use	Required before production promotion because this changes registration commands.
8. Mandatory Workflow
Audit / scope review, then stop for approval.
Architecture validation, then stop for approval.
Implementation plan, then stop for approval.
Implementation after approval.
Validation and final review.

Do not proceed in one pass unless explicitly approved.

9. Audit Requirements

Review registry_cmds.py for:

direct or indirect SQL access in commands
business logic in command handlers
duplicate helper functions
stale helper logic
direct access to private caches such as target_utils._name_cache
inconsistent registry loading paths
inconsistent defer/respond/edit/followup handling
permission boundary risks
import/export file handling risks
error reporting consistency
logging quality
restart/persistence safety
test coverage gaps

Map:

commands
service functions
DAL functions
SQL objects/contracts
views/modals
autocomplete helpers
cache dependencies
persisted state
restart implications
docs needing update
10. Architecture Targets
Concern	Target
Slash commands	commands/registry_cmds.py remains thin orchestration only
Views / modals	ui/views/registry_views.py, ui/views/admin_views.py, registry/governor_registry.py only where already established
Business logic	registry/registry_service.py or new focused registry service module
Import/export/audit logic	registry/registry_io.py, registry/dal/audit_dal.py, or new helper module
Shared validation helpers	registry/ package or existing helper modules
SQL contracts	C:\K98-bot-SQL-Server
Tests	tests/
11. Likely Files
Review
commands/registry_cmds.py
registry/registry_service.py
registry/governor_registry.py
registry/registry_io.py
registry/account_slots.py
registry/dal/audit_dal.py
ui/views/registry_views.py
ui/views/admin_views.py
target_utils.py
tests/
docs/deferred_optimisations.md
Modify
commands/registry_cmds.py
registry/registry_service.py
registry/registry_io.py
registry/account_slots.py
relevant tests
Create

Only if justified by audit:

registry/registry_command_helpers.py
registry/registry_validation.py
tests/registry/test_registry_command_helpers.py
tests/registry/test_registry_import_export.py
12. Implementation Requirements
Keep command handlers thin.
Do not add new direct SQL in commands or views.
Do not read target_utils._name_cache directly from command handlers if a public helper can be added or reused.
Reuse VALID_ACCOUNT_TYPES or ACCOUNT_ORDER consistently.
Remove hardcoded duplicate account lists where practical.
Standardise user ID parsing.
Standardise GovernorID normalisation.
Standardise Excel-safe ID formatting.
Standardise role extraction.
Standardise registry load failure behaviour.
Preserve all existing command names and permissions.
Preserve admin-only restrictions.
Preserve ephemeral behaviour where currently expected.
Preserve import/export file support for CSV and XLSX.
Preserve audit outputs.
Improve logging only where operationally useful.
Add tests for moved logic.
Capture out-of-scope findings structurally.
13. Refactor Decisions

Codex must populate this table after audit:

Issue	Decision	Reason
Duplicate account type lists	fix now / defer	
Direct _name_cache access	fix now / defer	
Duplicate GovernorID normalisation	fix now / defer	
Duplicate Excel-safe helpers	fix now / defer	
Heavy audit logic in command	fix now / defer	
Heavy import dry-run/apply logic in command	fix now / defer	
Mixed registry load methods	fix now / defer	
Inline imports inside command functions	fix now / defer	
Response/defer inconsistency	fix now / defer	
Test gaps	fix now / defer	

Deferred items must use the structured format from docs/reference/K98 Bot - Deferred Optimisation Framework.md.

14. Testing Requirements

Run selection first:

.\.venv\Scripts\python.exe scripts\select_tests.py

Baseline quality gates:

.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py

Focused tests to add or run:

.\.venv\Scripts\python.exe -m pytest -q tests -k "registry or registration or governor"

If broader impact is found:

.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests

Cover:

happy path registration
invalid account type
invalid GovernorID
GovernorID not found
duplicate registration conflict
modify registration
remove registration
admin registration
audit helper logic
import dry-run validation
import error file generation
export row formatting
permission boundary
cache safety
15. Acceptance Criteria
 Existing deferred optimisation docs and GitHub issues were checked.
 Audit findings are documented before implementation.
 registry_cmds.py is materially thinner or a clear reason is documented.
 No new direct SQL exists in commands or views.
 Business logic moved to services/helpers where practical.
 Duplicate helpers are removed or deferred with reasons.
 Direct private cache access is removed or explicitly deferred.
 Admin/user permission boundaries are preserved.
 Import/export/audit flows still support current formats.
 Logging is adequate for changed operational paths.
 Restart/persistence safety is preserved or explicitly not applicable.
 Tests are added/updated or exceptions documented.
 Quality gates are run or skipped with reason.
 Deferred optimisations are captured structurally.
16. Required Delivery Output

Codex must return:

Summary
File Manifest
New Files
Modified Files
SQL Changes
Helpers Reused
Refactor Findings
Test Plan
Deployment Steps
Deferred Optimisations
17. PR Summary Template
## Summary

- Audited and standardised registry command handling.
- Moved reusable validation/import/export/audit logic out of command handlers where practical.
- Preserved existing registry command behaviour and admin boundaries.

## Changes

- Reduced duplication in registry command helpers.
- Standardised account type, GovernorID, and user ID validation.
- Improved registry import/export/audit maintainability.
- Added or updated focused registry tests.

## Tests

- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests -k "registry or registration or governor"`

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Medium risk because registry commands affect player account linking and admin import/export workflows.
- Rollback by reverting this PR and redeploying the previous bot version.
- No SQL deployment expected unless audit finds a contract mismatch.