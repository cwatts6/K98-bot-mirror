# DL_bot Upload Routing - Phase 3 Local Validation Blockers Starter

We are starting Phase 3 of the DL_bot upload-routing optimisation programme after:

- Phase 1 player-location upload routing was smoke tested successfully and pushed to production.
- Phase 2A PreKvK upload route extraction was smoke tested successfully and pushed to production.
- Phase 2B PreKvK SQL compatibility cleanup was deployed, smoke tested successfully, and pushed to
  production.
- Phase 2C delivered the public read-only `/prekvk report` image report, was smoke tested
  successfully, and pushed to production.
- Phase 2D refactored the scheduled PreKvK stats-alert path onto the Phase 2C report service
  architecture, was smoke tested successfully, and pushed to production.

Phase 3 was the required follow-on to improve local PR-validation confidence before the upload
routing programme moved on to higher-blast-radius route extraction work.

## Completion Note

Status: complete as a no-op on 2026-05-20.

The Phase 3 audit found that the listed DB and non-DB local validation blockers no longer
reproduce on current `main`. No bot code, SQL, tests, or deployment scripts were changed for this
phase.

Validation evidence:

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_stats_service.py tests/test_targets_sql_cache_subproc.py tests/test_prekvk_stats.py tests/test_proc_config_import_phase2.py tests/test_sheets_sync_flow.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_dl_bot_mge_auto_import.py tests/test_integration_end_to_end_fake_worker.py tests/test_maintenance_suite.py
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Observed results:

- Focused DB-facing blocker tests: `28 passed`.
- Focused non-DB environment blocker tests: `20 passed`.
- Full suite: `1461 passed, 2 skipped`.
- Pytest log-noise validation: production operational logs unchanged.

Phase 4 KVK_ALL upload-route extraction is the next upload-routing programme slice.

## Goal

Fix or capability-gate DB and non-DB local validation blockers that affect confidence in the
upload-routing work.

The desired end state is:

- Local test runs do not accidentally require live SQL Server or bot-machine-only ODBC setup unless
  they are explicitly marked/gated as integration tests.
- Full-suite or targeted validation failures caused by local environment capabilities are either
  fixed or skipped behind clear capability gates.
- Validation remains meaningful: real unit tests should still exercise DAL/service boundaries with
  fakes or mocks where live infrastructure is unavailable.
- The documented local environment command paths are aligned with the repository's actual `.venv`
  workflow or made configurable where tests need a runtime interpreter path.

Step 1 is an audit/design packet, not implementation. Stop before code changes until the blocker
classification and first PR scope are approved.

## Required Reading

Before audit work, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/Codex Task Pack - DL_bot Upload Routing Deferred Optimisation Audit.md`
- `docs/task_packs/DL_bot Upload Routing - Phase 2 PreKvK Initiation Statement.md`

Use `C:\K98-bot-SQL-Server` as the SQL source of truth for any SQL-facing tests or DAL/service
contracts reviewed during this phase.

## Skills To Use

- `k98-architecture-scope`
- `k98-sql-validation`
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review` before any PR handoff
- `k98-promotion-check` only before production promotion/deployment

Use `k98-discord-command-feature` only if a selected validation blocker touches Discord command,
view, modal, or listener behaviour.

## Source Deferred Items

### Deferred Optimisation
- Area: tests/stats_service.py, tests/targets_sql_cache_subproc.py, tests/prekvk_stats.py, tests/proc_config_import_phase2.py, tests/sheets_sync_flow.py
- Type: consistency
- Description: Several non-Ark unit tests still reach live SQL Server or connection construction when run in the Codex/local PR validation environment without the bot machine's ODBC setup.
- Suggested Fix: Add subsystem-specific DAL/service boundary patches or explicit integration markers, then gate live DB coverage behind RUN_DB_TESTS=1.
- Impact: high
- Risk: medium
- Dependencies: Agreement on which non-Ark tests should remain live DB integration coverage.

### Deferred Optimisation
- Area: tests/test_dl_bot_mge_auto_import.py, tests/test_integration_end_to_end_fake_worker.py, tests/test_maintenance_suite.py
- Type: consistency
- Description: Full-suite validation in the Codex/local PR environment has non-DB environment blockers: DL_bot expects venv/Scripts/python.exe while the documented command uses .venv, and subprocess worker tests fail with WinError 5 in the sandbox.
- Suggested Fix: Make startup interpreter validation configurable for tests and mark subprocess worker tests with an environment capability gate when process spawning is unavailable.
- Impact: medium
- Risk: medium
- Dependencies: Local validation environment contract for venv naming and subprocess permissions.

## Phase 3 Scope

In scope:

- Audit the listed DB and non-DB validation blockers.
- Re-run or inspect the smallest reliable reproductions for each blocker.
- Decide which tests should become true unit tests with faked DAL/service boundaries.
- Decide which tests should remain live integration tests and be gated behind `RUN_DB_TESTS=1` or a
  similarly explicit capability flag.
- Decide whether interpreter path assumptions should be fixed in test setup, runtime config, or
  helper code.
- Decide whether subprocess-worker tests should be capability-gated in local/sandboxed
  environments.
- Update tests and validation documentation after implementation.
- Keep each PR focused: DB gating and non-DB process/interpreter gating may be split if the audit
  shows different risk profiles.

Out of scope until separately approved:

- Changing production import behaviour.
- Changing upload route behaviour or Discord output.
- Broad `DL_bot.py` lifecycle/startup refactor.
- KVK_ALL route extraction.
- Broad SQL schema changes.
- Retiring legacy SQL objects.
- Redesigning the validation framework beyond the blockers needed for PR confidence.

## Current Files To Review

Likely DB-facing blocker tests:

- `tests/test_stats_service.py`
- `tests/targets_sql_cache_subproc.py`
- `tests/test_prekvk_stats.py`
- `tests/test_proc_config_import_phase2.py`
- `tests/test_sheets_sync_flow.py`

Likely non-DB environment blocker tests:

- `tests/test_dl_bot_mge_auto_import.py`
- `tests/test_integration_end_to_end_fake_worker.py`
- `tests/test_maintenance_suite.py`

Likely implementation/helper files:

- `file_utils.py`
- `process_utils.py`
- `worker.py`
- `maintenance_suite.py`
- `DL_bot.py`
- `stats_service.py`
- `targets_sql_cache.py`
- `proc_config_import.py`
- `sheets_sync.py` or the current sheets-sync modules discovered during audit
- `scripts/select_tests.py`
- `scripts/smoke_imports.py`
- `scripts/validate_architecture_boundaries.py`
- `scripts/validate_deferred_items.py`

## Design Questions

- Which listed blockers still reproduce after Phase 2D and current main?
- Which tests are intended unit coverage and should never open real SQL connections?
- Which tests are valuable live integration coverage and should be opt-in with `RUN_DB_TESTS=1`?
- Should DB capability gating be implemented through pytest markers, environment checks, fixtures,
  or local helper functions?
- Which tests assume `venv/Scripts/python.exe`, and should that become `.venv` aware,
  configurable, or injected by test fixtures?
- Which subprocess tests fail only because the sandbox lacks process permissions, and what is the
  cleanest capability signal?
- How should `scripts/select_tests.py` recommend gated integration tests without making routine PR
  validation noisy?
- What documentation should tell future agents when to run live DB tests?

## Step 1 Required Output

Phase 3 Step 1 must produce:

- Audit Summary
- Current Validation Blocker Map
- DB-Backed Test Classification
- Non-DB Environment Blocker Classification
- Recommended Gating Pattern
- Recommended First PR Scope
- Test And Validation Strategy
- Deferred Optimisation Findings
- Approval Questions
- Explicit Stop Point

Do not write bot code, SQL, tests, or deployment scripts during Step 1.

## Validation Requirements

For audit/design-only work:

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

For implementation after approval, choose validation based on the selected blocker slice:

- focused tests for each fixed/gated blocker
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests`

If live SQL integration tests are intentionally retained, document and validate the opt-in path:

```powershell
$env:RUN_DB_TESTS="1"
.\.venv\Scripts\python.exe -m pytest -q <selected live DB tests>
```

## Acceptance Criteria

- Every source deferred validation blocker is classified as fixed-now, gated-now, already resolved,
  or deferred with a structured reason.
- Routine local PR validation can run without accidental live SQL Server or bot-machine-only
  dependencies.
- Opt-in live DB coverage remains available where it is still valuable.
- Subprocess or worker tests either run reliably in local validation or skip with a clear capability
  reason.
- `scripts/select_tests.py` output remains useful and not misleading.
- Out-of-scope follow-ups are captured structurally.

## Explicit Stop Point

Stop after the Phase 3 audit/design packet.

Do not implement fixes, alter SQL, change upload routing, or open a PR until the audit packet,
blocker classification, and first implementation scope have each been approved.

Completion decision: the approved Phase 3 outcome was no-op completion because all source blockers
were already resolved on current `main`.
