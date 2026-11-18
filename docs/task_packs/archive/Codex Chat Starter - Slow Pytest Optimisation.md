# Codex Task Pack — Slow Pytest Optimisation

## Archive Status

Archived after PR 107 (`pytest-log-delivery-docs`) resolved and production-smoke-tested the
original high-impact slow pytest offenders. The remaining post-PR-107 duration outliers are tracked
as a separate active item in `docs/reference/deferred_optimisations.md`.

## 1. Task Header

- Task name: Slow Pytest Optimisation
- Date: 2026-05-19
- Owner/context: Deferred optimisation from pytest log-isolation production smoke audit
- Task type: deferred optimisation batch
- One-pass approved: no

## 2. Required Reading

Before implementation, read and follow:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/deferred_optimisations.md`

Then follow any additional conditional references from `docs/reference/README.md`.

## 3. Objective

Investigate and resolve the root causes of slow-running pytest tests discovered after the pytest log-isolation production smoke validation.

Reduce full-suite runtime and failure-review noise without weakening timeout coverage, negative-path coverage, production timeout behaviour, or log-noise validation.

## 4. Background

Production smoke validation passed with:

```text
1450 passed, 2 skipped, 19 warnings in 638.91s

Command used:

pytest -q tests -v --durations=30 --durations-min=1.0 2>&1 | Tee-Object -FilePath .codex_pytest_audit.log

Primary audit log:

C:\Users\cwatt\Downloads\.codex_pytest_audit.log

Worst-performing tests from the duration audit:

252.28s tests/test_processing_pipeline.py::test_run_stats_copy_archive_success
234.79s tests/test_processing_pipeline.py::test_run_stats_copy_archive_unexpected_shape
45.00s  tests/test_event_cache.py::test_refresh_event_cache_times_out
17.27s  tests/test_processing_pipeline_run_step_and_normalization.py::test_run_step_with_sync_and_async
17.26s  tests/test_processing_pipeline_build_cache.py::test_build_player_stats_cache_offloaded_and_completes
16.32s  tests/test_processing_pipeline_build_cache.py::test_build_player_stats_cache_timeout_handled
```

Likely first hypothesis:

The two tests/test_processing_pipeline.py tests mock run_stats_copy_archive, but their successful mocked result still lets execute_processing_pipeline() continue into expensive downstream stages such as cache rebuilds, post-import maintenance, ProcConfig preflight/import, exports, lock waits, or timeout paths. These tests should remain unit tests and should not spend real wall-clock minutes exercising production-style downstream work.

5. Scope
In Scope
Audit the slowest pytest paths listed above.
Start with:
tests/test_processing_pipeline.py
tests/test_processing_pipeline_build_cache.py
tests/test_processing_pipeline_run_step_and_normalization.py
tests/test_event_cache.py
Classify each slow test as:
expected wait
insufficient mock boundary
unmocked dependency access
excessive retry/backoff
genuine defect
Patch heavy unit-test boundaries where safe:
cache rebuilds
post-import maintenance
ProcConfig preflight/import
exports
lock waits
intentional timeout sleeps
offload paths
Preserve orchestration assertions and negative-path assertions.
Add focused duration regression validation.
Out of Scope
Do not suppress genuine failures.
Do not remove timeout coverage.
Do not weaken scripts/analyse_pytest_log_noise.py.
Do not convert production timeout behaviour into test-only behaviour unless cleanly injected, patched, or faked at the test boundary.
Do not broaden into unrelated test-environment blockers unless discovered as direct causes of the listed slow tests.
Do not perform command-surface, SQL deployment, or DL_bot routing optimisation work in this task.
6. Source Deferred Items

### Deferred Optimisation
- Area: `tests/test_processing_pipeline.py`, `tests/test_processing_pipeline_build_cache.py`, `tests/test_processing_pipeline_run_step_and_normalization.py`, `tests/test_event_cache.py`, slow full-suite pytest paths
- Type: performance
- Description: Production smoke validation for the pytest log-isolation delivery passed, but the saved duration audit shows several unit tests spending real wall-clock time in expensive pipeline, timeout, lock, or offload paths. The worst offenders were `tests/test_processing_pipeline.py::test_run_stats_copy_archive_success` at 252.28s, `tests/test_processing_pipeline.py::test_run_stats_copy_archive_unexpected_shape` at 234.79s, `tests/test_event_cache.py::test_refresh_event_cache_times_out` at 45.00s, `tests/test_processing_pipeline_run_step_and_normalization.py::test_run_step_with_sync_and_async` at 17.27s, `tests/test_processing_pipeline_build_cache.py::test_build_player_stats_cache_offloaded_and_completes` at 17.26s, and `tests/test_processing_pipeline_build_cache.py::test_build_player_stats_cache_timeout_handled` at 16.32s.
- Suggested Fix: Start with the two `tests/test_processing_pipeline.py` cases and audit which downstream stages still execute after `run_stats_copy_archive` is mocked. Patch heavy unit-test boundaries such as cache rebuilds, post-import maintenance, ProcConfig preflight/import, exports, lock waits, and intentional timeout sleeps so unit coverage asserts orchestration and failure handling without real multi-second waits. Add duration-focused regression validation using `pytest -vv --durations=30 --durations-min=1.0` and keep full-suite log-noise validation intact.
- Impact: high
- Risk: medium
- Dependencies: Preserve negative-path coverage and production timeout behaviour; do not weaken `scripts/analyse_pytest_log_noise.py` or live integration gating.
7. Codex Skills To Use
Skill	Decision	Notes
k98-architecture-scope	use	Required before implementation to confirm affected services, test boundaries, cache/offload ownership, and approval checkpoints.
k98-discord-command-feature	not applicable	No slash command, view, modal, embed, or Discord interaction change is planned.
k98-sql-validation	use if needed	Use only if audit finds live SQL access, ProcConfig SQL dependencies, SQL-backed cache calls, or DB integration leakage in these tests.
k98-test-selection	use	Required before validation to combine focused duration tests with repo gates.
k98-deferred-optimisation-capture	use	Capture any additional out-of-scope test-performance or environment blockers structurally.
k98-pr-review	use	Required before PR handoff.
k98-promotion-check	not applicable unless promoted	Use only if this proceeds to production promotion.
8. Mandatory Workflow
Audit / scope review first, then stop for approval.
Classify each slow test before implementation.
Propose a remediation plan that preserves coverage and production timeout behaviour.
Implement only after approval.
Validate with focused duration runs and normal repo gates.
Provide final delivery output using the required delivery shape.
9. Audit Requirements

Run first:

.\.venv\Scripts\python.exe -m pytest -vv `
  tests/test_processing_pipeline.py `
  tests/test_processing_pipeline_build_cache.py `
  tests/test_processing_pipeline_run_step_and_normalization.py `
  tests/test_event_cache.py `
  --durations=0 --durations-min=0.1

Audit each listed slow test for:

real sleeps or asyncio.sleep
real timeout constants
retry/backoff loops
lock wait behaviour
offload/subprocess execution
downstream orchestration after mocked success
SQL or Google Sheets access leakage
cache rebuilds or export calls
post-import maintenance
missing boundary mocks
test assertions that accidentally require production wall-clock timing

Produce an audit table:

Test	Current duration	Classification	Cause	Proposed fix	Coverage preserved
10. Architecture Targets
Concern	Target
Test boundary fixes	tests/ fixtures, monkeypatches, fakes, or helper factories
Production timeout constants	Patch in tests only where safe, or inject cleanly without changing production defaults
Pipeline orchestration	Keep production code behaviour unchanged unless audit proves a genuine defect
Cache/offload dependencies	Mock at service boundary, not deep internals, where practical
SQL access	Gate integration behaviour or patch DAL/service boundary
Documentation	Update deferred item or notes only if scope changes
11. Likely Files
Review
tests/test_processing_pipeline.py
tests/test_processing_pipeline_build_cache.py
tests/test_processing_pipeline_run_step_and_normalization.py
tests/test_event_cache.py
processing_pipeline.py
event_cache.py
cache/offload helpers used by the above tests
scripts/analyse_pytest_log_noise.py
docs/reference/deferred_optimisations.md
Modify

To be confirmed after audit. Likely:

tests/test_processing_pipeline.py
tests/test_processing_pipeline_build_cache.py
tests/test_processing_pipeline_run_step_and_normalization.py
tests/test_event_cache.py
Create

Only if justified:

shared pytest fixture/helper for fast timeout/backoff/offload fakes
12. Implementation Requirements
Keep tests meaningful; do not simply skip slow tests.
Replace real multi-second waits with controlled fakes, patched constants, or explicit boundary mocks.
Preserve negative-path and timeout-path assertions.
Preserve production timeout defaults.
Keep integration-style coverage clearly separated from unit tests.
Avoid weakening log-noise checks.
Avoid broad production refactors unless the audit proves a genuine defect.
Capture any new out-of-scope findings as structured deferred optimisations.
13. Refactor Decisions

During audit, classify findings:

Issue	Decision	Reason
Slow unit test caused by missing downstream mock	fix now	Directly in scope.
Real timeout/sleep needed for production but not unit test	fix now	Replace with fake/patch in test.
Live SQL/Sheets dependency leaking into unit test	fix now or defer with marker	Fix if local to listed tests; defer if broader test-environment blocker.
Broad pipeline architecture concern	defer	Capture structurally unless required to fix the listed duration issue.
Existing unrelated slow test outside target list	defer	Capture separately unless trivial and safe.
14. Testing Requirements

Expected validation after remediation:

.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py

Focused duration validation:

.\.venv\Scripts\python.exe -m pytest -vv `
  tests/test_processing_pipeline.py `
  tests/test_processing_pipeline_build_cache.py `
  tests/test_processing_pipeline_run_step_and_normalization.py `
  tests/test_event_cache.py `
  --durations=30 --durations-min=1.0

Log-noise validation:

.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py

Full-suite validation:

.\.venv\Scripts\python.exe -m pytest -q tests

Optional broader gates if touched production code or shared helpers:

.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe scripts\smoke_imports.py
15. Acceptance Criteria
 Audit/scope review completed before implementation.
 Each targeted slow test is classified.
 Root cause is identified for each targeted slow test.
 Unit tests no longer spend real wall-clock minutes in production-style downstream work.
 Negative-path coverage is preserved.
 Timeout-path coverage is preserved.
 Production timeout behaviour is not weakened.
 No genuine failures are suppressed.
 scripts/analyse_pytest_log_noise.py remains valid.
 Focused duration run shows material improvement.
 Full pytest -q tests is run or any blocker is documented.
 Any new out-of-scope debt is captured structurally.
16. Required Delivery Output

Use this delivery shape:

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

- Optimised slow pytest paths identified by the pytest duration audit.
- Replaced real wall-clock waits/heavy downstream unit-test paths with controlled fakes or boundary mocks.
- Preserved negative-path and timeout coverage.

## Changes

- <change item>
- <change item>

## Tests

- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe -m pytest -vv tests/test_processing_pipeline.py tests/test_processing_pipeline_build_cache.py tests/test_processing_pipeline_run_step_and_normalization.py tests/test_event_cache.py --durations=30 --durations-min=1.0`
- `.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests`

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Risk: medium; test-only timing changes must not reduce coverage of production timeout behaviour.
- Rollback: revert test-boundary changes and restore previous pytest behaviour.

# Codex Chat Starter - Slow Pytest Optimisation

Use this starter to begin the deferred optimisation captured from the production pytest
log-isolation smoke audit.

## Copy/Paste Starter

Codex, start a new deferred optimisation task to investigate and resolve the root causes of
slow-running pytest tests discovered after the pytest log-isolation production smoke validation.

Before doing implementation, read and follow:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/Codex Chat Starter - Slow Pytest Optimisation.md`

Primary evidence:

- Full audit log: `C:\Users\cwatt\Downloads\.codex_pytest_audit.log`
- Production smoke result: `1450 passed, 2 skipped, 19 warnings in 638.91s`
- Command used:

```powershell
pytest -q tests -v --durations=30 --durations-min=1.0 2>&1 | Tee-Object -FilePath .codex_pytest_audit.log
```

Start with the worst-performing tests from the audit:

1. `tests/test_processing_pipeline.py::test_run_stats_copy_archive_success` - 252.28s
2. `tests/test_processing_pipeline.py::test_run_stats_copy_archive_unexpected_shape` - 234.79s
3. `tests/test_event_cache.py::test_refresh_event_cache_times_out` - 45.00s
4. `tests/test_processing_pipeline_run_step_and_normalization.py::test_run_step_with_sync_and_async` - 17.27s
5. `tests/test_processing_pipeline_build_cache.py::test_build_player_stats_cache_offloaded_and_completes` - 17.26s
6. `tests/test_processing_pipeline_build_cache.py::test_build_player_stats_cache_timeout_handled` - 16.32s

Likely first hypothesis:

The two `tests/test_processing_pipeline.py` tests mock `run_stats_copy_archive`, but their
successful mocked result still lets `execute_processing_pipeline()` continue into expensive
downstream stages such as cache rebuilds, post-import maintenance, ProcConfig preflight/import,
exports, lock waits, or timeout paths. These tests should remain unit tests and should not spend
real wall-clock minutes exercising production-style downstream work.

Mandatory workflow:

1. Audit/scope review first, then stop with findings before implementation.
2. Classify each slow test as expected wait, insufficient mock boundary, unmocked dependency
   access, excessive retry/backoff, or genuine defect.
3. Propose a remediation plan that preserves negative-path coverage and production timeout
   behaviour.
4. Implement only after approval.
5. Validate with focused duration runs and the normal repo gates.

Audit commands to run first:

```powershell
.\.venv\Scripts\python.exe -m pytest -vv `
  tests/test_processing_pipeline.py `
  tests/test_processing_pipeline_build_cache.py `
  tests/test_processing_pipeline_run_step_and_normalization.py `
  tests/test_event_cache.py `
  --durations=0 --durations-min=0.1
```

Expected validation after remediation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe -m pytest -vv `
  tests/test_processing_pipeline.py `
  tests/test_processing_pipeline_build_cache.py `
  tests/test_processing_pipeline_run_step_and_normalization.py `
  tests/test_event_cache.py `
  --durations=30 --durations-min=1.0
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

Do not suppress genuine failures. Do not remove timeout coverage; replace real multi-second waits
with controlled fakes, patched constants, or explicit boundary mocks where safe.

## Deferred Item Link

This starter implements the slow pytest performance item in
`docs/reference/deferred_optimisations.md`.
