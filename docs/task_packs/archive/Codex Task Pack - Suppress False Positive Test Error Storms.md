# Codex Task Pack — Urgent: Suppress False Positive Test Error Storms

## 1. Task Header

- Task name: Urgent pytest false-positive error storm cleanup
- Date: 2026-05-19
- Owner/context: Production deployment log hygiene issue from `pytest -q tests`
- Task type: bug fix / tooling / test infrastructure
- Priority: Critical
- One-pass approved: no

## 2. Required Reading

Before implementation, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/deferred_optimisations.md`
- `tests/conftest.py`
- `bot_instance.py`
- `file_utils.py`
- `logging` / health monitor setup files
- any test logging helpers or pytest config files

Use `docs/templates/Codex Task Pack Template.md` as the canonical task shape.

## 3. Objective

Investigate and resolve the false-positive production-style error storm produced when running:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

The goal is that expected negative-path tests still validate failure handling, but no longer pollute production logs, trigger health warnings, flash dashboards, or look like real bot failures.

## 4. Background

Current test runs emit large volumes of realistic ERROR and WARNING log records. Examples include:

live DB access guard failures from tests/conftest.py surfacing as Ark scheduler errors
mocked Discord DM failures logged as production reminder failures
event calendar expected failure tests logging refresh failed, generate failed, and publish_cache failed
SQL retry storms producing health spike admin warnings
test-induced failures from MGE, inventory, KVK import, stats, telemetry, and location import paths

These are expected test scenarios but operationally indistinguishable from real failures. This slows releases, makes logs noisy, risks missing genuine failures, and may degrade the bot while tests run.

## 5. Scope

### In Scope

Audit all ERROR/WARNING emissions during pytest -q tests.
Classify each as:
expected negative-path test noise
real unmocked dependency access
actual bug
excessive retry/backoff behaviour during tests
Ensure tests can assert expected logging using caplog without sending those records into production log handlers.
Prevent pytest runs from triggering:
admin health alerts
dashboard flashing
production log error spike detection
slow DB retry storms
real external service calls
Add a clear test-mode logging boundary.
Add or update pytest config / fixtures to isolate test logs.
Fix dummy objects/mocks that cause avoidable errors, e.g. dummy send() not accepting embed=.
Fix unpatched DAL/service boundaries where unit tests attempt live DB access.
Add a validation script or pytest option to fail if tests emit unexpected production-level logs.

### Out of Scope

Rewriting subsystem business logic unless a genuine bug is found.
Reducing useful production logging outside test mode.
Removing negative-path tests.
Changing production alert thresholds as the primary fix.
Full logging framework redesign unless required by audit.

## 6. Source Deferred Item

**Deferred Optimisation**

Area: tests/, logging setup, health monitor, runtime dependency guards
Type: tooling / cleanup / consistency
Description: Running pytest -q tests in production produces a false-positive failure storm. Expected test failures are logged as real operational errors, triggering dashboard/health noise and making deployment logs harder to review.
Suggested Fix: Add test-mode logging isolation, classify expected negative-path logs, patch live dependency boundaries, and enforce a clean test log gate.
Impact: high
Risk: medium
Dependencies: Coordinate with bot operator before changing production health logging or deployment scripts.

## 7. Codex Skills To Use

Skill	Decision	Notes
k98-architecture-scope	use	Logging and test infrastructure touches multiple layers.
k98-discord-command-feature	use if touched	Some failures come from Discord views, embeds, DM reminders, and command flows.
k98-sql-validation	use	DB retry storms and DAL live-access guards are central to the issue.
k98-test-selection	use	Required before validation and final test selection.
k98-deferred-optimisation-capture	use	Capture out-of-scope logging/test debt.
k98-pr-review	use	Required before PR handoff.
k98-promotion-check	use	This affects deployment validation and production release flow.

## 8. Mandatory Workflow

Audit / scope review, then stop for approval.
Architecture validation, then stop for approval.
Implementation plan, then stop for approval.
Implementation after approval.
Validation and final review.

Do not proceed one-pass unless explicitly approved.

## 9. Audit Requirements

Run and capture:

.\.venv\Scripts\python.exe -m pytest -q tests

Then produce a grouped report of all WARNING, ERROR, traceback, health alert, DB retry, and external dependency messages.

Classify by source:

tests/conftest.py live DB guard
DB connection retry helpers
health monitor / admin DM spike detection
Ark scheduler/reminders
Event calendar services
Event data loader/cache
MGE services
Inventory services
KVK import/reporting
Stats service/embed refresh
Telemetry DAL
Google Sheets retry logic
rehydrate/view tracker locks
location import service

Known examples to investigate:

Unit test attempted live DB access
DummyClient.fetch_user...send() got an unexpected keyword argument 'embed'
EVENT_CALENDAR_SHEET_ID is not configured
mocked RuntimeError("boom"), db down, disk full, channel send failed
DB retry storms reaching 5 attempts
[HEALTH] Admin DM sent: error spike

## 10. Architecture Targets

Concern	Target
Test log isolation	tests/conftest.py, pytest.ini / pyproject.toml
Logging setup	central logging/bootstrap module or existing root setup
Health alerts	bot_instance.py / health monitor module
DB retry test mode	file_utils.py, DAL wrappers, test fixtures
External dependency guards	test fixtures and service boundaries
Documentation	deployment/promotion guide if pytest behaviour changes
Tests	focused tests proving expected negative-path logs do not trigger production handlers

## 11. Likely Files

**Review**

tests/conftest.py
pytest.ini
pyproject.toml
bot_instance.py
file_utils.py
constants.py
ark/ark_scheduler.py
ark/reminders.py
event_calendar/service.py
event_data_loader.py
event_cache.py
mge/*
inventory/*
stats_service.py
embed_my_stats.py
telemetry/dal/command_usage_dal.py
rehydrate_views.py
services/location_import_service.py

**Modify**

To be confirmed after audit.

**Create**

Likely:

tests/helpers/logging_assertions.py
tests/test_test_logging_isolation.py
optional scripts/analyse_pytest_log_noise.py

## 12. Implementation Requirements

Preserve negative-path test coverage.
Do not hide genuine test failures.
Ensure test-mode suppression is explicit and limited to pytest.
Expected errors should be asserted with caplog or local test log capture, not emitted to production handlers.
Unit tests must not perform live SQL, Google Sheets, Discord, OpenAI, or filesystem production-path writes.
DB retry loops must be short-circuited or patched in unit tests.
Health monitor/admin alerts must be disabled during pytest unless explicitly testing health alerts.
Any tests intentionally verifying error logging must mark or whitelist the expected record.
Add a final gate that fails on unexpected production-level logs during the full test run.

## 13. Refactor Decisions

Issue	Decision	Reason
Production handlers active during pytest	fix now	Primary cause of false-positive production noise.
Unit tests reaching live DB guard	fix now	Indicates missing DAL/service patching.
Mocked failures logged as real errors	fix now	Expected negative tests should not trigger operational alerts.
Excessive retry/backoff in tests	fix now	Adds deployment time and noise.
Broad logging redesign	defer	Only needed if targeted isolation is insufficient.

## 14. Testing Requirements

Minimum validation:

.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe -m pytest -q tests

Add a log-noise validation command, for example:

.\.venv\Scripts\python.exe -m pytest -q tests --log-cli-level=CRITICAL

or a project-specific script:

.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py

Pytest logs are reviewed through pytest output, `caplog`, or an explicitly captured audit file,
not through production operational logs. When a saved review artifact is needed, use:

.\.venv\Scripts\python.exe -m pytest -q tests 2>&1 | Tee-Object -FilePath .codex_pytest_audit.log

Expected result:

full test suite passes
no admin health alert triggered
no production dashboard warning triggered
no unexpected ERROR records reach production log handlers
expected negative-path logs remain assertable inside tests

## 15. Acceptance Criteria

 pytest -q tests no longer creates a production-style error storm.
 Expected negative-path tests still assert the intended behaviour.
 Unit tests do not attempt live DB access unless explicitly marked integration and run with RUN_DB_TESTS=1.
 DB retry storms are eliminated from normal unit test runs.
 Health/admin alert paths are disabled or isolated during pytest.
 Unexpected ERROR/WARNING logs are either fixed or explicitly whitelisted with rationale.
 Deployment logs are clean enough to identify genuine failures.
 Runtime production logging behaviour is not weakened.
 Documentation/promotion guidance is updated if deployment validation steps change.

## 15A. Delivery Status

Delivered and promoted to production on 2026-05-19.

Production smoke validation passed with:

```powershell
pytest -q tests -v 2>&1 | Tee-Object -FilePath .codex_pytest_audit.log
```

Observed result from the saved audit artifact:

- `1450 passed, 2 skipped, 19 warnings`
- production pytest smoke completed without false-positive operational error storms
- pytest evidence is reviewed through pytest output, `caplog`, or `.codex_pytest_audit.log`
- production operational logs remain runtime evidence, not negative-path unit-test evidence

Follow-up finding: the production smoke audit exposed slow-running tests. That performance work
is intentionally deferred and tracked in `docs/reference/deferred_optimisations.md` plus
`docs/task_packs/Codex Chat Starter - Slow Pytest Optimisation.md`.

## 16. Required Delivery Output

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

## 17. PR Summary Template

## Summary

- Isolated pytest logging from production operational handlers.
- Fixed false-positive test error storm sources from expected negative-path tests.
- Added validation to catch unexpected production-level logs during tests.

## Changes

- <change item>

## Tests

- `.\.venv\Scripts\python.exe -m pytest -q tests`
- `<new log-noise validation command>`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Risk: accidental suppression of genuine production logs if test-mode boundary is too broad.
- Rollback: revert logging/test fixture changes and restore previous pytest behaviour.
