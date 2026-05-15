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
- `docs/reference/deferred_optimisations.md`
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

## 18. PR 84 Completion Update

Status: tested successfully and deployed to production.

PR 84 completed the first registry command standardisation pass:

- `commands/registry_cmds.py` now reuses shared account-slot and Discord user-id parsing helpers from `services/governor_account_service.py`.
- Registry account ordering now uses the canonical `registry/account_slots.py` list, expanded through Farm 20.
- User-facing GovernorID roster lookups no longer read `target_utils._name_cache` directly from command handlers; they use `target_utils.lookup_governor_row_by_id()`.
- `/my_registrations` now loads through `registry_service.load_registry_as_dict` instead of the removed legacy `load_registry` facade path.
- The import-confirm apply path no longer reloads the old facade registry before applying an import plan.
- Focused tests were added for registry command helper usage, GovernorID lookup, account slots, and the `/my_registrations` loader regression.
- The task pack was added to the PR and later cleaned for trailing whitespace so production promotion validation passes.

Validation completed during PR 84:

- `.\.venv\Scripts\python.exe -m py_compile commands/registry_cmds.py services/governor_account_service.py target_utils.py registry/account_slots.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_registry_cmds.py tests/test_governor_account_service.py tests/test_target_utils_governor_lookup.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests -k "registry or registration or governor"`
- Full suite result reported during the PR: `1323 passed, 2 skipped`.

## 19. Refactor Decision Outcomes

Issue	Decision	Reason
Duplicate account type lists	complete in PR 84	Canonical account slots now come from `registry/account_slots.py` and command autocomplete uses `services/governor_account_service.py`.
Direct _name_cache access	complete in PR 84	Command handlers now call `target_utils.lookup_governor_row_by_id()` instead of reading `target_utils._name_cache`.
Duplicate GovernorID normalisation	complete for registry command audit/import/export in PR 85A	Registry audit, export, and import helper logic now lives in `registry/registry_command_service.py`; broader shared account-resolution normalisation remains deferred as PR 85B.
Duplicate Excel-safe helpers	complete in PR 85A	Excel-safe export formatting moved into `registry/registry_command_service.py` and was made idempotent after review feedback.
Heavy audit logic in command	complete in PR 85A	Registration audit summary and file construction now live in `registry/registry_command_service.py`; the command remains Discord response plumbing.
Heavy import dry-run/apply logic in command	complete in PR 85A	Bulk import preview, error-file construction, apply result shaping, and summary text now live in `registry/registry_command_service.py`.
Mixed registry load methods	complete in PR 84 for registry commands	`/my_registrations` and touched import-confirm paths no longer rely on the old `load_registry` facade reference.
Inline imports inside command functions	partially complete / opportunistic cleanup	PR 85A removed DAL access from `commands/registry_cmds.py`; one local registry-service import remains in the admin remove flow and can be cleaned up when that flow is next touched.
Response/defer inconsistency	preserved / no active deferred item	PR 85A preserved command names, permissions, ephemeral/admin behaviour, CSV/XLSX compatibility, and overwrite confirmation behaviour.
Test gaps	complete for PR 85A scope	Focused service and command regression coverage was added for audit payloads, export shaping, import preview/apply summaries, member-cache fallback, glyph preservation, Excel-safe formatting, and command-layer DAL boundaries.

## 20. Remaining Deferred Items After PR 85A

PR 85A has been smoke tested successfully and deployed to production. It completed the registry command-service extraction for registration audit, bulk export, bulk import dry-run preview/error files, and bulk import apply summary shaping.

Two strategic registry/account optimisation items remained deferred after PR 85A:

- Move `RegisterGovernorView`, `ModifyGovernorView`, and `ConfirmRemoveView` out of `registry/governor_registry.py` into the UI layer, keeping the facade persistence-only.
- Consolidate richer account resolution across registry, stats, telemetry, MGE, and inventory into one shared summary object. PR 84 introduced basic helpers, but `StatsAccountSummary`, `AccountLookup`, inventory `RegisteredGovernor` resolution, and any MGE/telemetry account lookup paths are still separate shapes.

Recommended next item: move the registry view classes out of `registry/governor_registry.py`.

Rationale:

- It is a tighter PR-sized architecture cleanup than the shared account summary work.
- It finishes the registry facade cleanup started by PR 84 and PR 85A.
- It should mostly affect registry imports, view placement, and smoke tests rather than several subsystems at once.
- It reduces legacy coupling before the shared account summary migration touches registry, stats, telemetry, MGE, and inventory.

Keep the shared richer account-resolution summary deferred for the following phase unless a new task explicitly approves a broader cross-subsystem design PR.

## 21. Historical PR 85A Chat Starter

This starter was used for PR 85A and is retained for history:

```text
Codex, start the next phase after PR 84 (`registry-cmds-audit-and-optimisation`) was tested and deployed to production.

Use the K98 repo workflow and required docs. Read `docs/task_packs/Codex Task Pack - Audit and Optimise registry_cmds.md` and `docs/reference/deferred_optimisations.md` first.

Goal: implement the deferred phase from PR 84. Focus on extracting registry audit, bulk export, and bulk import dry-run/apply orchestration out of `commands/registry_cmds.py` into a service/helper layer, and design the shared richer account-resolution summary object for registry/stats/telemetry/MGE/inventory. Keep the work PR-sized: if both themes are too large, scope and propose the split before coding.

Important context:
- PR 84 already centralised basic account slots, Discord user-id parsing, and public GovernorID roster lookup.
- Do not regress `/my_registrations`; it must use `registry_service.load_registry_as_dict`.
- Preserve command names, permissions, ephemeral/admin behaviour, CSV/XLSX compatibility, and overwrite confirmation behaviour.
- Check whether `StatsAccountSummary`, `AccountLookup`, inventory `RegisteredGovernor` resolution, and any MGE/telemetry account lookup paths can share one richer summary object.
- Update deferred items as completed/deferred and run the K98 validation gates selected by `scripts/select_tests.py`.
```

## 22. PR 85A Scope Update

Split decision: the next phase is divided into two PR-sized changes.

PR 85A implements the registry command-service extraction only:

- Extract registration audit summary/file construction into a Discord-free registry command service.
- Extract bulk registration export row/file construction into the same service.
- Extract bulk import dry-run preview/error-file construction and apply summary shaping into the same service.
- Keep `commands/registry_cmds.py` responsible for slash command registration, permissions, safe defer/respond/followup handling, attachment waiting/reading, embeds, Discord files, and confirmation views.
- Preserve `/my_registrations` loading through `registry_service.load_registry_as_dict`.
- Preserve command names, admin-only restrictions, ephemeral/admin behavior, CSV/XLSX compatibility, and overwrite confirmation behavior.
- Remove the matching active deferred item from `docs/reference/deferred_optimisations.md` once implemented.

PR 85B remains deferred:

- Design and migrate the richer shared account-resolution summary object across registry, stats, telemetry, MGE, and inventory.
- Preserve `StatsAccountSummary`, `AccountLookup`, and inventory `RegisteredGovernor` behavior until each command surface has focused migration tests.

## 23. PR 85A Completion Update

Status: smoke tested successfully and deployed to production.

PR 85A delivered:

- `registry/registry_command_service.py` as a Discord-free service/helper layer for registration audit, bulk export, bulk import dry-run preview/error files, and bulk import apply summary shaping.
- Thinner `commands/registry_cmds.py` handlers that keep Discord permissions, safe defer/respond/followup handling, attachment waiting/reading, embeds, Discord files, and confirmation views in the command layer.
- Preservation of command names, admin restrictions, ephemeral/admin behaviour, CSV/XLSX compatibility, overwrite confirmation behaviour, and `/my_registrations` loading through `registry_service.load_registry_as_dict`.
- Review fixes for registration audit member-cache fallback, admin-facing warning/arrow glyphs, unnecessary audit-count sorting, command-layer DAL imports, and idempotent Excel-safe formatting.
- Focused regression coverage in `tests/test_registry_command_service.py` and `tests/test_registry_cmds.py`.

Validation completed during PR 85A:

- `.\.venv\Scripts\python.exe -m py_compile commands/registry_cmds.py registry/registry_command_service.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pre_commit run -a`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_registry_cache.py tests/test_registry_cmds.py tests/test_registry_command_service.py tests/test_registry_dal.py tests/test_registry_governor_registry.py tests/test_registry_io.py tests/test_registry_io_error_roundtrip.py tests/test_registry_io_xlsx.py tests/test_registry_service.py tests/test_registry_views_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests -k "registry"`
- `.\.venv\Scripts\python.exe -m pytest -q tests`

## 24. Next Phase Chat Starter

Use this in a fresh Codex chat for the recommended next optimisation:

```text
Codex, start the next registry optimisation after PR 85A (`registry-command-service-extraction`) was smoke tested successfully and deployed to production.

Use the K98 repo workflow and required docs. Read `docs/task_packs/Codex Task Pack - Audit and Optimise registry_cmds.md` and `docs/reference/deferred_optimisations.md` first.

Goal: move `RegisterGovernorView`, `ModifyGovernorView`, and `ConfirmRemoveView` out of `registry/governor_registry.py` into the UI layer, keeping `registry/governor_registry.py` as a compatibility facade over registry services/persistence only.

Important context:
- PR 84 centralised basic account slots, Discord user-id parsing, public GovernorID roster lookup, and `/my_registrations` loading through `registry_service.load_registry_as_dict`.
- PR 85A extracted registration audit, bulk export, bulk import dry-run preview/error files, and bulk import apply summary shaping into `registry/registry_command_service.py`.
- Preserve command names, permissions, ephemeral/admin behaviour, registration confirmation/cancel behaviour, and existing import paths where compatibility shims are needed.
- Update imports from registry commands, telemetry, stats, UI smoke tests, and any other callers without changing user-facing behaviour.
- Keep the shared richer account-resolution summary object deferred unless the audit finds a tiny prerequisite that is safe and clearly in scope.
- Update deferred docs as completed/deferred and run the K98 validation gates selected by `scripts/select_tests.py`.
```

## 25. PR 86 Registry View-Layer Extraction Completion Update

Status: smoke tested successfully and deployed to production.

PR 86 delivered:

- `RegisterGovernorView`, `ModifyGovernorView`, and `ConfirmRemoveView` now live in `ui/views/registry_views.py`.
- `registry/governor_registry.py` remains a compatibility facade for registry persistence/service helpers and exposes lazy compatibility re-exports for the moved view classes.
- `commands/registry_cmds.py` imports registry confirmation views from the UI layer.
- The remaining inline `registry.registry_service` import inside `remove_registration_by_id` was removed; the command now uses the module-level service imports.
- Registration confirmation, modification confirmation, removal confirmation, cancel behaviour, ephemeral behaviour, command names, and permission boundaries were preserved.
- Review fixes ensured moved view names remain available through `from registry.governor_registry import *`, confirmation callbacks defer before SQL-backed writes, blocking registry writes run through `asyncio.to_thread`, and removal confirmations clear the original prompt.
- Focused callback coverage was added for register, modify, remove, cancel, and compatibility import-star behaviour.
- The active deferred item for moving registry view classes was removed from `docs/reference/deferred_optimisations.md`.

Smoke coverage completed after deployment:

- `/register_governor` confirmation flow
- `/modify_registration` confirmation flow
- `/modify_registration` removal confirmation flow
- confirmation cancel paths
- `/my_registrations` post-change verification
- compatibility import checks for the moved registry view classes

Validation completed during PR 86:

- `.\.venv\Scripts\python.exe -m py_compile commands/registry_cmds.py registry/governor_registry.py ui/views/registry_views.py tests/test_registry_governor_registry.py tests/test_registry_views_smoke.py tests/test_ui_imports.py`
- `.\.venv\Scripts\python.exe -m pre_commit run -a`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_registry_governor_registry.py tests/test_registry_views_smoke.py tests/test_ui_imports.py tests/test_registry_cmds.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests -k "registry"`
- `.\.venv\Scripts\python.exe -m pytest -q tests`

The richer shared account-resolution summary is now the only remaining registry/account optimisation item from this audit series. It remains deferred as a separate cross-subsystem design and migration task.

## 26. Next Phase Chat Starter

Use this in a fresh Codex chat for the remaining registry/account optimisation:

```text
Codex, start the next registry/account optimisation after PR 86 (`registry-view-layer-extraction`) was smoke tested successfully and deployed to production.

Use the K98 repo workflow and required docs. Read `docs/task_packs/Codex Task Pack - Audit and Optimise registry_cmds.md` and `docs/reference/deferred_optimisations.md` first.

Goal: design and begin the migration for the remaining deferred richer shared account-resolution summary object across registry, stats, telemetry, MGE, and inventory. Keep the work PR-sized: start with an audit/scope pass, identify the shared result shape, and propose a safe first implementation slice before coding.

Important context:
- PR 84 centralised basic account slots, Discord user-id parsing, public GovernorID roster lookup, and `/my_registrations` loading through `registry_service.load_registry_as_dict`.
- PR 85A extracted registration audit, bulk export, bulk import dry-run preview/error files, and bulk import apply summary shaping into `registry/registry_command_service.py`.
- PR 86 moved `RegisterGovernorView`, `ModifyGovernorView`, and `ConfirmRemoveView` into `ui/views/registry_views.py`, kept compatibility re-exports from `registry/governor_registry.py`, and removed the remaining inline registry-service import in `remove_registration_by_id`.
- The remaining active registry/account deferred item is the shared account-resolution summary object. Current shapes include registry `AccountLookup`, stats `StatsAccountSummary`, inventory `RegisteredGovernor` resolution, and possible MGE/telemetry lookup variants.
- Preserve current command output, autocomplete ordering, permission checks, ephemeral/admin behaviour, inventory permission behaviour, and stats export behaviour.
- Validate SQL-facing assumptions against `C:\K98-bot-SQL-Server` before implementation, especially any GovernorID/account persistence assumptions.
- Update deferred docs as completed/deferred and run the K98 validation gates selected by `scripts/select_tests.py`.
```

## 27. PR 87 Shared Account-Resolution First Slice

Status: smoke tested successfully and deployed to production.

PR 87 delivered:

- A shared richer account-resolution summary object in `services/governor_account_service.py`.
- `ResolvedAccount` and `AccountResolutionSummary` with canonical account ordering, deduplicated GovernorIDs, GovernorID string/int access, account names, default choice, classification, free-slot, and ownership helpers.
- Preservation of the existing `AccountLookup` public shape for registry, telemetry, and UI callers.
- Preservation of `StatsAccountSummary` for stats commands and personal stats export while backing it with the shared summary.
- Preservation of inventory `RegisteredGovernor` output, inventory permission behavior, stale registry fallback behavior, legacy inventory display-label fallback behavior, and inventory report/export behavior while resolving accounts through the shared summary.
- Preservation of MGE linked-governor list output and self-service/admin signup behavior while resolving ownership through the shared summary.
- Documentation of the remaining command/view and Ark follow-up slices without removing compatibility adapters prematurely.

Smoke coverage completed after deployment:

- `/my_stats`
- `/mykvkstats`
- inventory import/report/export account resolution and permission paths
- MGE linked-governor signup behavior
- inventory missing-name display fallback (`Governor` or GovernorID rather than `Unknown`)

Validation completed during PR 87:

- `.\.venv\Scripts\python.exe -m py_compile services\governor_account_service.py services\stats_account_service.py inventory\inventory_service.py mge\mge_signup_service.py tests\test_governor_account_service.py tests\test_stats_account_service.py tests\test_inventory_service.py tests\test_mge_signup_service.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pre_commit run -a`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_governor_account_service.py tests\test_stats_account_service.py tests\test_inventory_service.py tests\test_inventory_export_service.py tests\test_inventory_reporting_service.py tests\test_mge_signup_service.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests -k "inventory"`
- `.\.venv\Scripts\python.exe -m pytest -q tests -k "mge"`
- `.\.venv\Scripts\python.exe -m pytest -q tests`

Follow-up slices intentionally left deferred:

1. Telemetry/KVK target/CrystalTech direct migration: update `commands/telemetry_cmds.py`, `account_picker.py`, and related KVK target views to consume the shared summary directly instead of only the `AccountLookup` compatibility adapter.
2. Registry command/view direct migration: update registry command and view account-selection flows to use the shared summary directly, then retire `AccountLookup` only after compatibility imports and smoke tests are updated.
3. Ark account-resolution audit: inspect `ark/registration_flow.py` account lookup and governor-name helpers for safe reuse of `AccountResolutionSummary`; migrate only if Ark signup behavior and tests remain stable.
4. Compatibility cleanup: after all command/view surfaces are migrated, remove duplicate local classification, linked-governor, and registered-governor adapter code that no longer has external callers.

## 28. Next Phase Chat Starter

Use this in a fresh Codex chat for the remaining shared account-resolution follow-up slices:

```text
Codex, start the next registry/account optimisation after PR 87 (`shared-account-resolution-slice`) was smoke tested successfully and deployed to production.

Use the K98 repo workflow and required docs. Read `docs/task_packs/Codex Task Pack - Audit and Optimise registry_cmds.md` and `docs/reference/deferred_optimisations.md` first.

Goal: deliver the next PR-sized follow-up slice for the shared account-resolution migration. PR 87 introduced `ResolvedAccount` and `AccountResolutionSummary` in `services/governor_account_service.py` and migrated the stats, inventory, and MGE service adapters while preserving their public shapes. Now audit and begin direct command/view migration for the remaining consumers.

Important context:
- PR 84 centralised basic account slots, Discord user-id parsing, public GovernorID roster lookup, and `/my_registrations` loading through `registry_service.load_registry_as_dict`.
- PR 85A extracted registration audit, bulk export, bulk import dry-run preview/error files, and bulk import apply summary shaping into `registry/registry_command_service.py`.
- PR 86 moved registry confirmation views into `ui/views/registry_views.py`, kept compatibility re-exports from `registry/governor_registry.py`, and removed the remaining inline registry-service import in `remove_registration_by_id`.
- PR 87 introduced the shared richer account-resolution summary object and migrated stats, inventory, and MGE service adapters.
- Remaining follow-up slices are:
  1. migrate telemetry/KVK target/CrystalTech picker setup in `commands/telemetry_cmds.py`, `account_picker.py`, `kvk_ui.py`, and related views to consume `AccountResolutionSummary` directly;
  2. migrate registry command/view account-selection flows in `commands/registry_cmds.py` and `ui/views/registry_views.py` to the shared summary;
  3. audit `ark/registration_flow.py` account lookup and governor-name helpers for safe reuse of the shared summary;
  4. remove compatibility adapters only after every direct command/view surface has focused regression coverage.
- Keep the work PR-sized. Start with audit/scope and propose whether the first implementation slice should be telemetry/KVK target/CrystalTech or registry command/view direct migration.
- Preserve current command output, autocomplete ordering, permission checks, ephemeral/admin behaviour, inventory permission behaviour, stats export behaviour, MGE signup behaviour, and Ark signup behaviour.
- Validate any SQL-facing assumptions against `C:\K98-bot-SQL-Server` before implementation.
- Update deferred docs as completed/deferred and run the K98 validation gates selected by `scripts/select_tests.py`.
```

## 29. PR 88 Telemetry/KVK Picker Direct Migration Completion Update

Status: smoke tested successfully and deployed to production.

PR 88 delivered:

- `commands/telemetry_cmds.py` now uses `get_account_summary_for_user()` directly for `/mykvktargets`, `/mykvkcrystaltech`, and the KVK registration callback.
- `account_picker.py` now accepts `AccountResolutionSummary` directly when building unique governor select options, while preserving legacy dict support for remaining unmigrated callers.
- `kvk_ui.py` selector refresh now rebuilds options from `AccountResolutionSummary`.
- Account selector label/value/description shape and GovernorID dedupe behaviour were preserved.
- Review feedback was addressed so blank, missing, or `Unknown` GovernorName values fall back to the slot label instead of rendering repeated `Unknown` picker labels.
- Registry command/view and Ark direct migrations remained deferred and were captured as separate active backlog items.
- Compatibility adapter cleanup remained deferred until all direct command/view and Ark consumers have focused regression coverage.

Smoke coverage completed after deployment:

- `/mykvktargets` typed GovernorID path.
- `/mykvktargets` one-linked-governor auto-open path.
- `/mykvktargets` multi-governor selector path.
- `/mykvktargets` no-linked-governor hint and picker path.
- KVK selector refresh, lookup, and register buttons.
- `/mykvkcrystaltech` typed GovernorID path.
- `/mykvkcrystaltech` one-linked-governor auto-open path.
- `/mykvkcrystaltech` multi-governor selector path.
- `/mykvkcrystaltech` no-linked-governor hint and picker path.
- `/my_registrations` spot check to confirm intentionally deferred registry flows still open normally.

Validation completed during PR 88:

- `.\.venv\Scripts\python.exe -m py_compile commands\telemetry_cmds.py account_picker.py kvk_ui.py tests\test_account_picker.py tests\test_mykvktargets.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_account_picker.py tests\test_mykvktargets.py tests\test_governor_account_service.py tests\test_crystaltech_service.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests -k "account_picker or mykvktargets or crystaltech or governor_account"`
- `.\.venv\Scripts\python.exe -m pytest -q tests` (`1349 passed, 2 skipped`)
- `.\.venv\Scripts\python.exe -m pre_commit run -a`
- Review-fix validation: `.\.venv\Scripts\python.exe -m pytest -q tests\test_account_picker.py tests\test_mykvktargets.py tests\test_governor_account_service.py tests\test_crystaltech_service.py` (`22 passed`)

Remaining follow-up slices intentionally left deferred:

1. Registry command/view direct migration: update registry command autocomplete and `MyRegsActionView` registration/modify entry points in `commands/registry_cmds.py` and `ui/views/registry_views.py` to consume `AccountResolutionSummary` directly while preserving write-sensitive behaviour.
2. Ark account-resolution audit/migration: inspect `ark/registration_flow.py` self-service join/sub/leave/switch lookup and governor-name resolution for safe reuse of `AccountResolutionSummary`.
3. Compatibility cleanup: remove obsolete `AccountLookup`-only pathways and duplicate local classification/option-shaping helpers only after telemetry/KVK, registry command/view, and Ark surfaces all have focused regression coverage.

## 30. Next Phase Chat Starter

Use this in a fresh Codex chat for the remaining shared account-resolution deferred elements:

```text
Codex, start the next registry/account optimisation after PR 88 (`account-summary-telemetry-picker`) was smoke tested successfully and deployed to production.

Use the K98 repo workflow and required docs. Read `docs/task_packs/Codex Task Pack - Audit and Optimise registry_cmds.md` and `docs/reference/deferred_optimisations.md` first.

Goal: deliver the next PR-sized follow-up slice for the shared account-resolution migration. PR 87 introduced `ResolvedAccount` and `AccountResolutionSummary` in `services/governor_account_service.py`; PR 88 migrated telemetry/KVK target/CrystalTech picker setup in `commands/telemetry_cmds.py`, `account_picker.py`, and `kvk_ui.py` to consume the shared summary directly. Now deliver the remaining deferred elements incrementally.

Important context:
- PR 84 centralised basic account slots, Discord user-id parsing, public GovernorID roster lookup, and `/my_registrations` loading through `registry_service.load_registry_as_dict`.
- PR 85A extracted registration audit, bulk export, bulk import dry-run preview/error files, and bulk import apply summary shaping into `registry/registry_command_service.py`.
- PR 86 moved registry confirmation views into `ui/views/registry_views.py`, kept compatibility re-exports from `registry/governor_registry.py`, and removed the remaining inline registry-service import in `remove_registration_by_id`.
- PR 87 introduced the shared richer account-resolution summary object and migrated stats, inventory, and MGE service adapters while preserving public shapes.
- PR 88 migrated telemetry/KVK target/CrystalTech picker setup to `AccountResolutionSummary` and preserved selector labels, option ordering, refresh behaviour, lookup/register buttons, and slot fallback labels for blank or `Unknown` GovernorName values.
- Remaining deferred slices are:
  1. migrate registry command/view account-selection flows in `commands/registry_cmds.py` and `ui/views/registry_views.py` to consume `AccountResolutionSummary` directly;
  2. audit and, if safe, migrate `ark/registration_flow.py` account lookup and governor-name helpers to reuse the shared summary;
  3. remove compatibility adapters and duplicate local classification/option-shaping helpers only after every direct command/view and Ark surface has focused regression coverage.
- Recommended next slice: registry command/view direct migration, because it is the next consumer in the account-registration workflow and should land before Ark or adapter cleanup.
- Preserve current command output, autocomplete ordering, permission checks, ephemeral/admin behaviour, registration confirmation/cancel behaviour, SQL-backed duplicate ownership checks, inventory permission behaviour, stats export behaviour, MGE signup behaviour, telemetry/KVK picker behaviour, and Ark signup behaviour.
- Validate any SQL-facing assumptions against `C:\K98-bot-SQL-Server` before implementation.
- Keep the work PR-sized. Start with audit/scope and stop for approval before implementation unless explicitly told otherwise.
- Update deferred docs as completed/deferred and run the K98 validation gates selected by `scripts/select_tests.py`.
```

## 31. PR 89 Registry Command/View Direct Migration Completion Update

Status: smoke tested successfully and deployed to production.

PR 89 delivered:

- `commands/registry_cmds.py` uses `get_account_summary_for_user()` directly for account-type autocomplete, `/modify_registration` slot existence checks, and admin remove pre-check display data.
- `ui/views/registry_views.py` uses `get_account_summary_for_user()` directly from `MyRegsActionView` when opening modify/register entry points.
- `ModifyStartView` now receives `AccountResolutionSummary` and builds options from `summary.ordered_accounts`.
- `RegisterStartView` can receive `AccountResolutionSummary` for registry flows while retaining `free_slots` compatibility for telemetry/KVK callers that still open the same start view.
- `AccountResolutionSummary.registered_slots()` was added so command autocomplete can preserve canonical registered-slot ordering without dropping back to `AccountLookup`.
- `/modify_registration` autocomplete now falls back to the invoking user only when the autocomplete context belongs to the self-service modify command.
- Admin remove autocomplete keeps the full slot list until a target Discord user or pasted user ID is present, avoiding accidental suggestions from the invoking admin's own registrations.
- `MyRegsActionView` modify entry now reports temporary registry unavailability separately instead of treating summary load failure as no accounts registered.
- Focused command/view/service tests cover summary-backed slot filtering, registry selection migration, view entry points, and registry-unavailable handling.
- The active deferred item for registry command/view direct migration was removed from `docs/reference/deferred_optimisations.md`.

Smoke coverage completed after deployment:

- `/modify_registration` registered-slot autocomplete shows the invoking user's registered slots in canonical order.
- `/modify_registration` valid modify path opens the existing confirmation prompt and preserves confirm/cancel behaviour.
- `/modify_registration` `REMOVE` path opens the existing removal confirmation prompt and preserves confirm/cancel behaviour.
- Admin `/remove_registration` autocomplete shows full slot suggestions before a target is entered, then target-specific registered slots once a Discord user or pasted ID is present.
- Admin `/remove_registration_by_id` still handles valid removals, unregistered slots, and no-registration IDs with the existing user-facing responses.
- `/my_registrations` action buttons open modify/register selectors from the shared account summary.
- `/register_governor` confirmation flow still opens and preserves confirm/cancel behaviour.
- Telemetry/KVK entry points that reuse `RegisterStartView` still open the slot picker through the preserved `free_slots` compatibility path.

Validation completed during PR 89:

- `.\.venv\Scripts\python.exe -m py_compile commands\registry_cmds.py ui\views\registry_views.py services\governor_account_service.py tests\test_registry_cmds.py tests\test_registry_views_smoke.py tests\test_governor_account_service.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_registry_cmds.py tests\test_registry_views_smoke.py tests\test_governor_account_service.py` (`23 passed` after review fixes)
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_registry_cmds.py tests\test_registry_views_smoke.py tests\test_governor_account_service.py tests\test_ui_imports.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests` (`1355 passed, 2 skipped` after review fixes)
- `.\.venv\Scripts\python.exe -m pre_commit run -a`

Remaining follow-up slices intentionally left deferred:

1. Ark account-resolution audit/migration: inspect `ark/registration_flow.py` self-service join/sub/leave/switch lookup and governor-name resolution for safe reuse of `AccountResolutionSummary`.
2. Compatibility cleanup: remove obsolete `AccountLookup`-only pathways and duplicate local classification/option-shaping helpers only after Ark has focused regression coverage and the existing stats, inventory, MGE, telemetry/KVK, and registry regression surfaces remain green.

## 32. Next Phase Chat Starter

Use this in a fresh Codex chat for the next shared account-resolution deferred slice:

```text
Codex, start the next registry/account optimisation after PR 89 (`registry-account-summary-direct`) was smoke tested successfully and deployed to production.

Use the K98 repo workflow and required docs. Read `docs/task_packs/Codex Task Pack - Audit and Optimise registry_cmds.md` and `docs/reference/deferred_optimisations.md` first.

Goal: deliver the next PR-sized follow-up slice for the shared account-resolution migration. PR 87 introduced `ResolvedAccount` and `AccountResolutionSummary` in `services/governor_account_service.py`; PR 88 migrated telemetry/KVK target/CrystalTech picker setup in `commands/telemetry_cmds.py`, `account_picker.py`, and `kvk_ui.py`; PR 89 migrated registry command/view account-selection flows in `commands/registry_cmds.py` and `ui/views/registry_views.py` to consume the shared summary directly. Now audit Ark and migrate only if the safe PR-sized shape is clear.

Important context:
- PR 84 centralised basic account slots, Discord user-id parsing, public GovernorID roster lookup, and `/my_registrations` loading through `registry_service.load_registry_as_dict`.
- PR 85A extracted registration audit, bulk export, bulk import dry-run preview/error files, and bulk import apply summary shaping into `registry/registry_command_service.py`.
- PR 86 moved registry confirmation views into `ui/views/registry_views.py`, kept compatibility re-exports from `registry/governor_registry.py`, and removed the remaining inline registry-service import in `remove_registration_by_id`.
- PR 87 introduced the shared richer account-resolution summary object and migrated stats, inventory, and MGE service adapters while preserving public shapes.
- PR 88 migrated telemetry/KVK target/CrystalTech picker setup to `AccountResolutionSummary` and preserved selector labels, option ordering, refresh behaviour, lookup/register buttons, and slot fallback labels for blank or `Unknown` GovernorName values.
- PR 89 migrated registry command/view account-selection flows to `AccountResolutionSummary`, preserved self-service/admin autocomplete behaviour, confirmation/cancel behaviour, duplicate ownership checks, and `RegisterStartView` compatibility for telemetry/KVK callers.
- Remaining deferred slices are:
  1. audit and, if safe, migrate `ark/registration_flow.py` account lookup and governor-name helpers to reuse `AccountResolutionSummary`;
  2. remove compatibility adapters and duplicate local classification/option-shaping helpers only after Ark has focused regression coverage.
- Recommended next slice: Ark account-resolution audit/migration. Start with audit/scope and stop for approval before implementation unless explicitly told otherwise.
- Preserve current Ark signup behaviour, join/sub/leave/switch flows, ban enforcement, roster filtering, active signup detection, persistent registration-message refresh, account picker labels/ordering, telemetry/KVK picker behaviour, registry flows, inventory permission behaviour, stats export behaviour, and MGE signup behaviour.
- Validate any SQL-facing assumptions against `C:\K98-bot-SQL-Server` before implementation.
- Keep the work PR-sized. If Ark migration is not safely small, propose the split and leave compatibility cleanup deferred.
- Update deferred docs as completed/deferred and run the K98 validation gates selected by `scripts/select_tests.py`.
```

## 33. PR 90 Ark Account-Resolution Direct Migration Completion Update

Status: smoke tested successfully and deployed to production.

PR 90 delivered:

- `ark/registration_flow.py` now uses `get_account_summary_for_user()` directly for self-service Ark join, sub, leave, and switch flows.
- Ark self-service governor selectors now pass `AccountResolutionSummary` to the shared account picker option builder, preserving selector ordering, GovernorID de-dupe, and slot fallback labels.
- Ark leave and switch roster filtering now derives linked GovernorIDs from `summary.governor_id_strings` instead of rebuilding local sets from raw account dictionaries.
- Ark signup and switch GovernorName snapshots now resolve through `AccountResolutionSummary.governor_name_for_id()`.
- The Ark-local raw account loader and duplicate governor-name helper were removed from `ark/registration_flow.py`.
- Admin add name-cache and fuzzy lookup behaviour was intentionally left unchanged because it is an admin roster-search flow, not a linked-account selection path; a structured deferred item now tracks that cleanup separately.
- The active Ark deferred optimisation item was removed from `docs/reference/deferred_optimisations.md`.
- Compatibility adapter cleanup remains deferred as a dedicated cleanup slice, alongside the separate `/my_registrations` display-loader item.

Validation completed during PR 90:

- `.\.venv\Scripts\python.exe -m py_compile ark\registration_flow.py services\governor_account_service.py tests\test_ark_registration_flow.py tests\test_governor_account_service.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_ark_registration_flow.py tests\test_governor_account_service.py tests\test_account_picker.py` (`33 passed`)
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_ark_bans_enforcement.py tests\test_ark_admin_roster.py` (`8 passed`)
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests` (`1356 passed, 2 skipped`)
- `.\.venv\Scripts\python.exe -m pytest -q <explicit test_ark_*.py file list>` (`165 passed`)
- `.\.venv\Scripts\python.exe -m pre_commit run -a`

Remaining follow-up slices intentionally left deferred:

1. `/my_registrations` display-loader migration: audit and, if safe, move the player-facing display payload from full-registry local selection to `AccountResolutionSummary` or a focused display service.
2. Ark admin fuzzy/name-cache lookup cleanup: move admin roster-search lookup out of the controller into a focused helper/service while preserving exact ID, partial ID, fuzzy name, refresh fallback, no-match responses, and admin slot prompts.
3. Compatibility cleanup: remove obsolete `AccountLookup`-only pathways and duplicate local classification/option-shaping helpers only after preserving focused regression coverage for stats export, inventory permissions, MGE signup, telemetry/KVK pickers, registry flows, KVK personal views, and Ark signup.

## 34. PR 91 My Registrations Display-Loader Completion Update

Status: smoke tested successfully and deployed to production.

PR 91 delivered:

- `/my_registrations` now loads the invoking user's display accounts through `get_account_summary_for_user()` instead of using the full-registry snapshot as the primary loader.
- A review fix preserved the previous stale-cache degraded mode by falling back to `registry_service.load_registry_as_dict()` only when the primary per-user summary load fails.
- The command builds its display from `AccountResolutionSummary.ordered_accounts`, preserving embed title/copy, account slot ordering, empty-state copy, action buttons, truncation guard, and ephemeral response behaviour.
- Registry audit, export, and import paths still use `registry_service.load_registry_as_dict()` because they require full-registry snapshots.
- Focused regression coverage now checks the `/my_registrations` summary-backed display payload, empty-state copy, stale-cache fallback success, and no-fallback failure behaviour.
- The active `/my_registrations` display-loader deferred item was removed from `docs/reference/deferred_optimisations.md`.

Smoke coverage completed after deployment:

- `/my_registrations` displays registered accounts in the expected canonical slot order.
- `/my_registrations` preserves the existing title/copy, empty-state copy, action buttons, and ephemeral response behaviour.
- `/my_registrations` action buttons still open the existing modify/register selectors.
- Registry audit, export, and import full-snapshot flows were not changed by this PR.

Validation completed during PR 91:

- `.\.venv\Scripts\python.exe -m py_compile commands\registry_cmds.py tests\test_registry_cmds.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_registry_cmds.py tests\test_registry_views_smoke.py tests\test_governor_account_service.py` (`28 passed` after review fixes)
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests` (`1361 passed, 2 skipped` after review fixes)
- `.\.venv\Scripts\python.exe -m pre_commit run -a`

Remaining follow-up slices intentionally left deferred:

1. Ark admin fuzzy/name-cache lookup cleanup: move admin roster-search lookup out of the controller into a focused helper/service while preserving exact ID, partial ID, fuzzy name, refresh fallback, no-match responses, slot prompts, ban enforcement, and admin/leadership permissions.
2. Compatibility cleanup: remove obsolete `AccountLookup`-only pathways and duplicate local classification/option-shaping helpers only after preserving focused regression coverage for stats export, inventory permissions, MGE signup, telemetry/KVK pickers, registry flows, KVK personal views, and Ark signup.

## 35. Next Phase Chat Starter

Use this in a fresh Codex chat for the final shared account-resolution cleanup slices:

```text
Codex, start the final registry/account optimisation phase after PR 91 (`my-registrations-display-loader`) was smoke tested successfully and deployed to production.

Use the K98 repo workflow and required docs. Read `docs/task_packs/Codex Task Pack - Audit and Optimise registry_cmds.md` and `docs/reference/deferred_optimisations.md` first.

Goal: deliver the remaining final PR-sized slices for the shared account-resolution migration. PR 87 introduced `ResolvedAccount` and `AccountResolutionSummary` in `services/governor_account_service.py`; PR 88 migrated telemetry/KVK target/CrystalTech picker setup in `commands/telemetry_cmds.py`, `account_picker.py`, and `kvk_ui.py`; PR 89 migrated registry command/view account-selection flows in `commands/registry_cmds.py` and `ui/views/registry_views.py`; PR 90 migrated Ark self-service join/sub/leave/switch account-selection flows in `ark/registration_flow.py`; PR 91 migrated `/my_registrations` display loading while preserving stale-cache fallback.

Important context:
- PR 84 centralised basic account slots, Discord user-id parsing, public GovernorID roster lookup, and initial `/my_registrations` loading through `registry_service.load_registry_as_dict`.
- PR 85A extracted registration audit, bulk export, bulk import dry-run preview/error files, and bulk import apply summary shaping into `registry/registry_command_service.py`.
- PR 86 moved registry confirmation views into `ui/views/registry_views.py`, kept compatibility re-exports from `registry/governor_registry.py`, and removed the remaining inline registry-service import in `remove_registration_by_id`.
- PR 87 introduced the shared richer account-resolution summary object and migrated stats, inventory, and MGE service adapters while preserving public shapes.
- PR 88 migrated telemetry/KVK target/CrystalTech picker setup to `AccountResolutionSummary` and preserved selector labels, option ordering, refresh behaviour, lookup/register buttons, and slot fallback labels for blank or `Unknown` GovernorName values.
- PR 89 migrated registry command/view account-selection flows to `AccountResolutionSummary`, preserving self-service/admin autocomplete behaviour, confirmation/cancel behaviour, duplicate ownership checks, and `RegisterStartView` compatibility for telemetry/KVK callers.
- PR 90 migrated Ark self-service join/sub/leave/switch flows to `AccountResolutionSummary`, preserving signup behaviour, ban enforcement, roster filtering, active signup detection, persistent registration-message refresh, and account picker labels/ordering.
- PR 91 migrated `/my_registrations` display loading to `AccountResolutionSummary`, restored stale-cache degraded fallback after review, and preserved embed copy, slot ordering, action buttons, truncation guard, and ephemeral behaviour.

Remaining active deferred slices:
1. Ark admin fuzzy/name-cache lookup cleanup: move admin roster-search lookup out of `ark/registration_flow.py` into a focused Discord-free helper/service while preserving exact ID, partial ID, fuzzy name, cache refresh fallback, no-match responses, fuzzy result ordering, slot prompts, ban enforcement, slot capacity checks, and admin/leadership permissions.
2. Compatibility cleanup: remove obsolete `AccountLookup`-only pathways and duplicate local account classification, linked-governor, registered-governor, and option-shaping helpers after auditing external callers.

Recommended approach:
- Start with audit/scope only and decide whether Ark admin fuzzy/name-cache cleanup and compatibility cleanup should be one PR or two.
- Prefer Ark admin fuzzy/name-cache cleanup first if compatibility cleanup still has uncertainty or broad caller risk.
- Keep compatibility cleanup deferred unless the audit shows no remaining public callers and the regression surface is small.

Preserve telemetry/KVK picker behaviour, registry flows, `/my_registrations` stale fallback, inventory permission behaviour, stats export behaviour, MGE signup behaviour, Ark self-service signup behaviour, and Ark admin add behaviour.

Validate any SQL-facing assumptions against `C:\K98-bot-SQL-Server` before implementation.

Run or justify the K98 validation gates selected by `scripts/select_tests.py`, including `scripts/validate_architecture_boundaries.py`, `scripts/validate_deferred_items.py`, `scripts/smoke_imports.py`, `scripts/validate_command_registration.py`, focused Ark/account tests, and full tests if selector/risk warrants it.

Update `docs/reference/deferred_optimisations.md` and this task pack as completed/deferred before PR handoff.
```

## 36. PR 92 Ark Admin Governor Lookup Service Update

Status: smoke tested successfully and deployed to production.

PR 92 delivered the Ark admin fuzzy/name-cache lookup cleanup slice:

- `ark/registration_flow.py` now delegates admin add governor query resolution to a Discord-free Ark lookup service.
- `ark/admin_governor_lookup_service.py` owns exact numeric GovernorID lookup, partial GovernorID matching, fuzzy name lookup, stale/empty cache refresh fallback, substring fallback, and no-match result shaping.
- `target_utils.get_name_cache_rows()` exposes a small public cache-row accessor so Ark admin lookup no longer reads `target_utils._name_cache` from the controller.
- The Ark controller remains responsible for Discord modal/selector routing, fuzzy embed/view display, slot prompt wiring, and the existing admin add apply path.
- Existing ban enforcement, player/sub capacity checks, duplicate signup checks, active-weekend conflict checks, admin/leadership permissions, audit logging, and registration-message refresh remain in `_apply_admin_add`.
- Focused tests cover the lookup service exact ID path, partial ID ordering, substring fallback after refresh, numeric no-match copy, fuzzy selector routing, admin permissions, ban enforcement, and slot capacity behaviour.
- The active Ark admin fuzzy/name-cache lookup deferred item was removed from `docs/reference/deferred_optimisations.md`.

Smoke coverage completed after deployment:

- Ark admin add exact GovernorID lookup opens the existing slot prompt.
- Ark admin add partial GovernorID and fuzzy name matches open the existing fuzzy selector with preserved ordering.
- Ark admin add no-match responses preserve the existing player-facing copy.
- Ark admin add still enforces admin/leadership permissions, active-ban blocking or override behaviour, player/sub capacity checks, duplicate signup checks, active-weekend conflict checks, audit logging, and registration-message refresh.

Validation completed during PR 92 implementation:

- `.\.venv\Scripts\python.exe -m py_compile ark\registration_flow.py ark\admin_governor_lookup_service.py target_utils.py tests\test_ark_admin_governor_lookup_service.py tests\test_ark_admin_roster.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_ark_admin_governor_lookup_service.py tests\test_ark_admin_roster.py tests\test_ark_bans_enforcement.py tests\test_ark_registration_flow.py tests\test_ark_fuzzy_select_view.py` (`32 passed`)
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_account_picker.py tests\test_governor_account_service.py` (`14 passed`)
- `.\.venv\Scripts\python.exe -m pytest -q tests -k "ark"` (`453 passed, 2 skipped, 912 deselected`)
- `.\.venv\Scripts\python.exe -m pytest -q tests` (`1365 passed, 2 skipped`)
- `.\.venv\Scripts\python.exe -m pre_commit run -a`
- `git diff --check`

Remaining follow-up slice intentionally left deferred:

1. Compatibility cleanup: remove obsolete `AccountLookup`-only pathways and duplicate local account classification, linked-governor, registered-governor, and option-shaping helpers after preserving focused regression coverage for stats export, inventory permissions, MGE signup, telemetry/KVK pickers, registry flows, KVK personal views, and Ark signup.

## 37. Next Phase Chat Starter

Use this in a fresh Codex chat for the final shared account-resolution deferred slice:

```text
Codex, start the final registry/account optimisation cleanup after PR 92 (`ark-admin-governor-lookup-service`) was smoke tested successfully and deployed to production.

Use the K98 repo workflow and required docs. Read `docs/task_packs/Codex Task Pack - Audit and Optimise registry_cmds.md` and `docs/reference/deferred_optimisations.md` first.

Goal: complete the final deferred compatibility cleanup for the shared account-resolution migration. Before implementation, do a full repo-wide audit to ensure no remaining legacy account-resolution pathways or duplicate helpers have been missed.

Important completed context:
- PR 84 centralised basic account slots, Discord user-id parsing, public GovernorID roster lookup, and initial `/my_registrations` loading through `registry_service.load_registry_as_dict`.
- PR 85A extracted registration audit, bulk export, bulk import dry-run preview/error files, and bulk import apply summary shaping into `registry/registry_command_service.py`.
- PR 86 moved registry confirmation views into `ui/views/registry_views.py`, kept compatibility re-exports from `registry/governor_registry.py`, and removed the remaining inline registry-service import in `remove_registration_by_id`.
- PR 87 introduced `ResolvedAccount` and `AccountResolutionSummary` in `services/governor_account_service.py`, then migrated stats, inventory, and MGE service adapters while preserving public shapes.
- PR 88 migrated telemetry/KVK target/CrystalTech picker setup to `AccountResolutionSummary`.
- PR 89 migrated registry command/view account-selection flows in `commands/registry_cmds.py` and `ui/views/registry_views.py`.
- PR 90 migrated Ark self-service join/sub/leave/switch flows in `ark/registration_flow.py`.
- PR 91 migrated `/my_registrations` display loading to `AccountResolutionSummary` while preserving stale-cache fallback.
- PR 92 moved Ark admin add exact ID, partial ID, fuzzy name, substring fallback, and cache-refresh lookup into `ark/admin_governor_lookup_service.py` and removed controller-level direct `_name_cache` reads.

Required audit before coding:
- Search the full repo for `AccountLookup`, `get_accounts_for_user`, `classify_accounts`, `free_account_slots`, `resolve_governor_label`, `StatsAccountSummary`, `RegisteredGovernor`, `governors_to_accounts`, `build_unique_gov_options`, `safe_build_unique_gov_options`, `ordered_accounts`, `resolved_accounts`, `governor_ids`, `governor_id_strings`, `name_to_id`, `default_choice`, and direct `target_utils._name_cache` reads.
- Include tests, docs, views, command modules, services, and subsystem packages in the audit.
- Classify every finding as remove now, preserve as public compatibility, migrate to `AccountResolutionSummary`, or defer with a structured reason.
- Confirm whether any remaining duplicate local option-shaping or account classification helpers are still needed by external callers.

Likely cleanup candidates:
- `services/governor_account_service.py`: obsolete `AccountLookup` compatibility class and `get_accounts_for_user()` if no external runtime callers remain.
- `services/governor_account_service.py`: duplicate `classify_accounts`, `free_account_slots`, or `resolve_governor_label` pathways if callers can use `AccountResolutionSummary`.
- `services/stats_account_service.py`: `StatsAccountSummary` adapter if stats commands/tests can safely consume the shared summary directly.
- `services/kvk_personal_service.py` and `ui/views/kvk_personal_views.py`: local account classification and legacy registration action loading.
- `inventory/inventory_service.py`, `inventory/models.py`, and inventory views/reporting: registered-governor shaping if it can be simplified without breaking inventory permissions or report UX.
- `account_picker.py`, `ui/views/inventory_views.py`, `ui/views/mge_signup_view.py`, and related callers: duplicate option-shaping helpers only if the audit shows a safe shared path.

Preserve behaviour:
- telemetry/KVK picker labels, option ordering, refresh behaviour, lookup/register buttons, and blank/`Unknown` fallback labels.
- registry command/view flows, `/my_registrations` stale fallback, registry audit/export/import full-snapshot behaviour, and `RegisterStartView` compatibility where still needed.
- inventory permission behaviour and inventory report governor display.
- stats export and personal stats account selection.
- MGE signup behaviour.
- Ark self-service signup behaviour and Ark admin add behaviour.
- KVK personal views and CrystalTech user-facing copy.

Validate any SQL-facing assumptions against `C:\K98-bot-SQL-Server` before implementation. This cleanup should not require SQL changes, but do not guess if a caller depends on SQL-backed registry or Ark state.

Run or justify the K98 validation gates selected by `scripts/select_tests.py`, including:
- `scripts/validate_architecture_boundaries.py`
- `scripts/validate_deferred_items.py`
- `scripts/smoke_imports.py`
- `scripts/validate_command_registration.py`
- focused tests for governor account service, account picker, stats, inventory, MGE signup, telemetry/KVK, registry, KVK personal views, CrystalTech, and Ark
- full `.\.venv\Scripts\python.exe -m pytest -q tests` if the audit or touched files cross subsystem boundaries
- `.\.venv\Scripts\python.exe -m pre_commit run -a`

Update `docs/reference/deferred_optimisations.md` and this task pack as completed/deferred before PR handoff. If the repo-wide audit finds additional missed account-resolution debt, capture it using the required deferred optimisation structure instead of silently expanding scope.
```

## 38. Final Shared Account-Resolution Compatibility Cleanup Update

Status: smoke tested successfully and deployed to production.

PR 93 delivered the final shared account-resolution compatibility cleanup slice after PR 92:

- Removed obsolete `AccountLookup`, `get_accounts_for_user()`, `classify_accounts()`, `free_account_slots()`, `resolve_governor_label()`, and `StatsAccountSummary` adapter paths after confirming no runtime callers still require those public shapes.
- Migrated stats commands, stats export, CrystalTech, and KVK personal registration actions directly to `AccountResolutionSummary`.
- Preserve `inventory.models.RegisteredGovernor` as the inventory/reporting DTO because inventory report and export flows still use it as a domain model.
- Preserved shared `account_picker` helpers, but allowed them to consume `AccountResolutionSummary`, legacy account maps, linked-governor row lists, and `RegisteredGovernor` objects so local fake account maps could be removed.
- Removed inventory `governors_to_accounts()` and MGE signup local option-shaping where the shared picker can consume the existing domain rows directly.
- Brought `ark/ark_preference_service.py` into this slice by replacing direct `_name_cache` reads with public `target_utils.get_name_cache_rows()`.
- Kept `ui/views/mge_admin_add_signup_view.py` deferred as part of a broader governor fuzzy-lookup standardisation pass, because several Ark/MGE/registry/KVK lookup flows need to be audited together before extracting shared behaviour.
- Deleted `services/stats_account_service.py` and its dedicated tests after stats callers moved to the shared summary directly.

Smoke coverage completed after deployment:

- Stats personal account selection and stats export continued to resolve the expected linked governors.
- KVK personal registration actions continued to show the correct lookup/register/edit options from the shared summary.
- CrystalTech picker/setup labels continued to render the selected governor with preserved fallback copy.
- Inventory import, permission, and report governor display paths continued to use the inventory/reporting DTO safely.
- MGE self-service signup continued to offer linked governor options through the shared picker.
- Ark preference validation continued to resolve valid governors and reject invalid IDs through the public target-utils cache accessor.

Validation completed during implementation:

- `.\.venv\Scripts\python.exe -m py_compile services\governor_account_service.py services\kvk_personal_service.py services\stats_export_service.py stats_service.py commands\stats_cmds.py commands\crystaltech_flow.py ui\views\kvk_personal_views.py ui\views\inventory_views.py ui\views\mge_signup_view.py ui\views\registry_views.py ark\ark_preference_service.py account_picker.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_governor_account_service.py tests\test_account_picker.py tests\test_stats_export_service.py tests\test_mykvkstats.py tests\test_kvk_personal_service.py tests\test_ark_preference_service.py tests\test_registry_views_smoke.py` (`39 passed`)
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_service.py tests\test_inventory_upload_flow.py tests\test_inventory_export_service.py tests\test_inventory_report_views.py tests\test_mge_signup_service.py tests\test_mge_signup_views.py tests\test_mykvktargets.py tests\test_crystaltech_service.py tests\test_registry_cmds.py tests\test_ark_registration_flow.py tests\test_ark_admin_governor_lookup_service.py tests\test_ark_admin_roster.py` (`120 passed`)
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_stats_service.py tests\test_mykvkstats.py tests\test_ui_imports.py` (`18 passed`)
- `.\.venv\Scripts\python.exe -m pytest -q tests` (`1355 passed, 2 skipped`)
- `.\.venv\Scripts\python.exe -m pre_commit run -a`

Deferred follow-up captured in `docs/reference/deferred_optimisations.md`:

```markdown
### Deferred Optimisation
- Area: `ui/views/mge_admin_add_signup_view.py`, Ark/MGE/registry governor fuzzy lookup flows
- Type: cleanup
- Description: MGE admin-add signup lookup still owns local name-cache/fuzzy lookup logic and reads `target_utils._name_cache` directly. The repo now has several governor fuzzy/name lookup flows, including Ark admin lookup, MGE admin-add lookup, registry/KVK lookup views, and target/profile lookup paths, so this should be standardised as a focused audit instead of being folded into account-resolution compatibility cleanup.
- Suggested Fix: In a dedicated fuzzy-lookup optimisation PR, audit all governor fuzzy/name/partial-ID lookup flows, compare exact ID, partial ID, fuzzy name, substring fallback, cache refresh, no-match copy, result ordering, and selector behaviour, then extract or reuse a shared service/helper where behaviour can be standardised without changing user-facing flows.
- Impact: medium
- Risk: medium
- Dependencies: Preserve MGE admin-add signup permissions and modal/select behaviour, Ark admin add lookup behaviour, registry/KVK lookup copy, target/profile lookup behaviour, and existing fuzzy result ordering.
```

## 39. Next Phase Chat Starter

Use this in a fresh Codex chat for the MGE admin-add fuzzy lookup and broader governor fuzzy-lookup standardisation item:

```text
Codex, start the MGE admin-add fuzzy lookup / broader governor fuzzy-lookup standardisation phase after PR 93 (`account-resolution-compatibility-cleanup`) was smoke tested successfully and deployed to production.

Use the K98 repo workflow and required docs. Read `docs/task_packs/Codex Task Pack - Audit and Optimise registry_cmds.md` and `docs/reference/deferred_optimisations.md` first.

Goal: audit and standardise governor fuzzy/name/partial-ID lookup flows, with MGE admin-add signup lookup as the primary cleanup candidate. Start with repo-wide audit/scope before coding, then keep the implementation PR-sized.

Important completed context:
- PR 84 centralised basic account slots, Discord user-id parsing, public GovernorID roster lookup, and initial `/my_registrations` loading through `registry_service.load_registry_as_dict`.
- PR 87 introduced `ResolvedAccount` and `AccountResolutionSummary` in `services/governor_account_service.py`.
- PR 88 through PR 91 migrated telemetry/KVK target/CrystalTech, registry, Ark self-service, and `/my_registrations` account-selection/display flows to `AccountResolutionSummary`.
- PR 92 moved Ark admin add exact ID, partial ID, fuzzy name, substring fallback, and cache-refresh lookup into `ark/admin_governor_lookup_service.py` and removed controller-level direct `_name_cache` reads.
- PR 93 removed obsolete account-resolution compatibility adapters, migrated remaining runtime callers to `AccountResolutionSummary`, and moved Ark preference validation to public `target_utils.get_name_cache_rows()`.
- The remaining active deferred item is fuzzy lookup standardisation, not shared account-resolution compatibility.

Required audit before coding:
- Search the full repo for `lookup_governor_id`, `autocomplete_governor_names`, `search_by_governor_name`, `lookup_governor_row_by_id`, `get_name_cache_rows`, `get_name_cache_status`, `refresh_name_cache_from_sql`, `sync_refresh_worker`, `_name_cache`, `fuzzy`, `fuzzy_matches`, `Governor Name Search Results`, `substring`, and `partial`.
- Include command modules, views, services, Ark, MGE, registry/KVK, target/profile lookup, autocomplete paths, tests, and docs.
- Classify every finding as preserve, migrate to shared lookup service/helper, remove, or defer with a structured reason.
- Compare exact numeric GovernorID, partial GovernorID, fuzzy name, substring fallback, cache warm/refresh behaviour, no-match copy, result ordering, selector behaviour, permission boundaries, and user-facing copy.
- Confirm whether reusable behaviour from `ark/admin_governor_lookup_service.py` should move into a shared target/governor lookup helper or stay Ark-specific behind smaller shared cache/search helpers.

Likely cleanup candidates:
- `ui/views/mge_admin_add_signup_view.py`: extract Discord-free lookup/service logic and replace direct `_name_cache` reads.
- `ark/admin_governor_lookup_service.py`: review for reusable exact/partial/fuzzy/cache-refresh behaviours without changing Ark admin add UX.
- Registry/KVK lookup views, target/profile lookup, and autocomplete paths: audit duplication and preserve existing copy/order unless there is a clear shared helper with focused coverage.

Preserve behaviour:
- MGE admin-add permissions, event lock/signup-close behaviour, modal/select copy, exact ID/partial/fuzzy behaviour, no-match messages, signup creation/edit flows, and result ordering.
- Ark admin add behaviour from PR 92.
- Registry/KVK lookup and target/profile user-facing copy.
- Cache refresh behaviour and stale/empty cache fallbacks.
- Existing fuzzy result ordering unless the audit proves a safer shared order.

Validate SQL-facing assumptions against `C:\K98-bot-SQL-Server`, especially the GovernorID/GovernorName source used by target-utils cache refresh, before implementation.

Run or justify the K98 validation gates selected by `scripts/select_tests.py`, including:
- `scripts/validate_architecture_boundaries.py`
- `scripts/validate_deferred_items.py`
- `scripts/smoke_imports.py`
- `scripts/validate_command_registration.py`
- focused tests for MGE admin add/signup views, Ark admin lookup, registry/KVK lookup views, target_utils lookup, telemetry/KVK, and affected fuzzy/autocomplete paths
- full `.\.venv\Scripts\python.exe -m pytest -q tests` if shared lookup code crosses subsystem boundaries
- `.\.venv\Scripts\python.exe -m pre_commit run -a`

Update `docs/reference/deferred_optimisations.md` and this task pack as completed/deferred before PR handoff.
```

## 40. MGE Admin-Add Fuzzy Lookup Standardisation Update

Status: smoke tested successfully and deployed to production.

This phase completed the active governor fuzzy/name/partial-ID lookup deferred item:

- Added `services/governor_lookup_service.py` as a Discord-free shared resolver for exact numeric GovernorID lookup, partial GovernorID matches, fuzzy name lookup, substring fallback, cache warm/refresh behaviour, and no-match shaping.
- Kept `ark/admin_governor_lookup_service.py` as the Ark-facing adapter so Ark admin add result shape and controller UX remain stable.
- Updated `ui/views/mge_admin_add_signup_view.py` so MGE admin-add lookup no longer imports or reads `target_utils._name_cache` directly; the view now owns only modal handling, fuzzy embed/select rendering, and signup-flow continuation.
- Preserved MGE admin-add permissions, event lock/completed-event gating, modal/select copy, signup creation/edit continuation, exact ID/partial/fuzzy behaviour, no-match messages, and cache refresh fallback.
- Audited registry/KVK lookup, target/profile lookup, autocomplete, Ark preference validation, and diagnostic/test cache reads. Those paths were preserved because they either already use public target-utils helpers or rely on different profile-cache semantics.
- Validated SQL-facing cache assumptions against `C:\K98-bot-SQL-Server`: `target_utils.sync_refresh_worker()` reads `dbo.vw_All_Governors_Clean`, whose SQL definition exposes `GovernorID`, trimmed `GovernorName`, and `CityHallLevel` from `dbo.ALL_GOVS`.
- Removed the active fuzzy lookup standardisation item from `docs/reference/deferred_optimisations.md`.
- Captured a separate deferred item for `/player_profile` and `/player_location`, which still use `profile_cache.search_by_governor_name()` and should be audited separately because that lookup depends on profile/location cache semantics rather than the target-utils roster cache.
- Addressed review feedback by reusing one `get_name_cache_rows()` snapshot per resolver path and passing it into helper searches, avoiding repeated copied-list allocations while preserving match ordering.

Smoke coverage completed after deployment:

- MGE admin-add exact GovernorID, partial GovernorID, fuzzy-name select, no-match messaging, and signup continuation worked in production.
- Ark admin add behaviour remained stable through the Ark-facing adapter.
- Registry/KVK lookup, target/profile lookup, autocomplete, and cache-refresh behaviour remained unchanged.

Validation completed during implementation and review follow-up:

- `.\.venv\Scripts\python.exe -m py_compile services\governor_lookup_service.py ark\admin_governor_lookup_service.py ui\views\mge_admin_add_signup_view.py tests\test_governor_lookup_service.py tests\test_ark_admin_governor_lookup_service.py tests\test_mge_simplified_leadership_admin_add.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_governor_lookup_service.py tests\test_ark_admin_governor_lookup_service.py tests\test_ark_admin_roster.py tests\test_mge_simplified_leadership_admin_add.py` (`17 passed` after review follow-up)
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_target_utils_governor_lookup.py tests\test_registry_views_smoke.py tests\test_kvk_personal_views.py tests\test_mykvktargets.py` (`26 passed`)
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_ark_registration_flow.py tests\test_ark_fuzzy_select_view.py tests\test_mge_signup_views.py tests\test_mge_signup_service.py` (`43 passed`)
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_ark_*.py` via explicit PowerShell file list (`166 passed`)
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_ui_imports.py` (`1 passed`)
- `.\.venv\Scripts\python.exe -m pytest -q tests` (`1358 passed, 2 skipped`)
- `.\.venv\Scripts\python.exe -m pre_commit run -a`
- `git diff --check`

## 41. Next Deferred Work Chat Starter

Use this in a fresh Codex chat to pick up the remaining active deferred optimisation backlog after PR 94:

```text
Codex, start the next deferred optimisation phase after PR 94 (`mge-admin-governor-lookup-standardisation`) was smoke tested successfully and deployed to production.

Use the K98 repo workflow and required docs. Read `docs/reference/deferred_optimisations.md` first, then follow `README-DEV.md` and the reference index in `docs/reference/README.md`.

Goal: review the remaining active deferred optimisation backlog and select a PR-sized implementation slice. Start with audit/scope only, classify each active item, then recommend the safest next task before coding.

Important completed context:
- PR 84 through PR 93 completed the registry/account-resolution cleanup series.
- PR 94 completed the MGE admin-add and broader governor fuzzy/name/partial-ID lookup standardisation. `services/governor_lookup_service.py` now owns the shared Discord-free lookup resolver, MGE admin-add no longer reads `target_utils._name_cache` directly, and Ark admin add remains behind its adapter.
- The active deferred backlog no longer contains account-resolution or target-utils roster governor fuzzy-lookup work. `/player_profile` and `/player_location` profile-cache name lookup remains separately deferred because it uses `profile_cache.search_by_governor_name()`.

Active deferred items to review:
- `/player_profile` and `/player_location` still use profile-cache name lookup and need a separate profile/location lookup audit before any shared-helper change.
- Non-Ark tests that still reach live SQL Server or connection construction in local/Codex validation without the bot machine's ODBC setup.
- Non-DB full-suite environment blockers: `DL_bot` interpreter path assumptions and sandbox-limited subprocess worker tests.
- `DL_bot.py` PreKvK upload routing still mixes filename matching, current-KVK lookup, offload dispatch, and Discord rendering.
- SQL repo legacy PreKvK phase objects still represent the old scan-window delta model.
- `DL_bot.py` KVK_ALL upload routing still mixes attachment filtering, offload dispatch, import result handling, Discord rendering, and export scheduling.

Recommended first slice:
- Start with the local validation environment consistency items if the goal is to make future PR validation more reliable. Keep it PR-sized by addressing either live-DB test gating or non-DB sandbox/interpreter blockers, not both at once unless the audit proves they share the same small test harness change.
- If choosing feature architecture instead, pick either PreKvK upload routing or KVK_ALL upload routing, not both, and preserve existing Discord output and offload behaviour.
- Treat the legacy SQL PreKvK phase-object cleanup as a SQL-repo audit/design task before any bot-code implementation.

Required audit before coding:
- Search the bot repo for the files and tests named in `docs/reference/deferred_optimisations.md`.
- For the profile/location lookup item, search `commands/telemetry_cmds.py`, `commands/location_cmds.py`, `profile_cache.py`, `commands/player_profile_flow.py`, and related tests for `search_by_governor_name`, `get_profile_cached`, profile-cache warm/refresh behaviour, and multi-match selector copy.
- If touching SQL-facing PreKvK or KVK paths, validate object names, views, stored procedures, and dependencies against `C:\K98-bot-SQL-Server` before implementation.
- Classify each active item as fix now, defer, blocked, or not applicable, with a structured reason.
- Keep runtime behaviour and production upload flows unchanged unless the selected task explicitly changes them.

Run or justify the K98 validation gates selected by `scripts/select_tests.py`, including:
- `scripts/validate_architecture_boundaries.py`
- `scripts/validate_deferred_items.py`
- `scripts/smoke_imports.py`
- `scripts/validate_command_registration.py` when command registration could be affected
- focused tests for the selected deferred slice
- full `.\.venv\Scripts\python.exe -m pytest -q tests` if the selected fix changes shared test harness, upload routing, or cross-subsystem validation behaviour
- `.\.venv\Scripts\python.exe -m pre_commit run -a`

Update `docs/reference/deferred_optimisations.md` and any affected task-pack/runbook docs before PR handoff.
```

## 42. Profile/Location Profile-Cache Lookup Standardisation Update

Status: implemented and ready for PR validation.

This phase completed the active `/player_profile` and `/player_location` profile-cache lookup item:

- Added `services/profile_lookup_service.py` as a Discord-free resolver for profile/location command input.
- Kept profile/location lookup on `profile_cache.search_by_governor_name()` instead of the SQL-backed target-utils roster cache used by `services/governor_lookup_service.py`.
- Updated `/player_profile` and `/player_location` so command handlers share the same profile-cache lookup semantics while preserving permission gates, autocomplete-ID handling, multi-match selectors, no-match copy, profile cache warm/disk fallback behaviour, and location refresh behaviour.
- Validated SQL-facing assumptions against `C:\K98-bot-SQL-Server`: `profile_cache.build_full_cache()` reads `dbo.v_PlayerProfile`, which exposes `GovernorID`, `Governor_Name`, profile stats, `PlayerLocation.X/Y/LastUpdated`, `PlayerAccountStatus`, and forts metadata.
- Removed the active profile/location lookup item from `docs/reference/deferred_optimisations.md`.
- Captured a separate deferred item for `/import_locations` command-layer import orchestration, which remains out of scope for the profile/location lookup PR.

Validation completed during implementation:

- `.\.venv\Scripts\python.exe -m py_compile services\profile_lookup_service.py commands\telemetry_cmds.py commands\location_cmds.py tests\test_profile_lookup_service.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_profile_lookup_service.py tests\test_location_views_smoke.py tests\test_registry_views_smoke.py` (`15 passed`)
- `.\.venv\Scripts\python.exe scripts\select_tests.py commands\telemetry_cmds.py commands\location_cmds.py services\profile_lookup_service.py tests\test_profile_lookup_service.py`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests` (`1365 passed, 2 skipped`)
- `.\.venv\Scripts\python.exe -m pre_commit run -a`
