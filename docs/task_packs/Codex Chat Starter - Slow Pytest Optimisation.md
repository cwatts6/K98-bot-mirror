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
