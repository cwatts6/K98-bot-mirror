# TASK 6 — Build Pipeline Orchestrator

## Objective
Implement a production-ready orchestrator that runs the full Event Calendar refresh pipeline sequentially and safely:

**Sheets Sync → SQL Instance Generation → JSON Export**

Task 6 should make pipeline execution deterministic, observable, and resilient under partial failures, while preserving last-known-good SQL/JSON runtime behavior.

---

## Scope

### 1) Pipeline orchestrator module
Create module:

- `event_calendar/calendar_pipeline.py`

Implement primary function:

- `refresh_event_calendar_pipeline(...)`

Suggested signature (flexible to current service patterns):

- `refresh_event_calendar_pipeline(actor_user_id=None, sheet_id=None, horizon_days=365, force_empty=False)`

Behavior:

- Execute stages in strict sequence:
  1. Sheets sync
  2. SQL instance generation
  3. JSON cache publish
- Stop on terminal stage failure unless explicit retry policy says otherwise.
- Return a structured result object with stage outcomes and aggregate status.

---

### 2) Result contract (required)
Return object must include:

```json
{
  "ok": true,
  "stage": "done",
  "sheets_sync_success": true,
  "sql_generation_success": true,
  "json_export_success": true,
  "events_generated": 123,
  "errors": []
}
```

Minimum required fields:

- `sheets_sync_success`
- `sql_generation_success`
- `json_export_success`
- `events_generated`
- `errors`

Recommended additional fields:

- `pipeline_started_utc`
- `pipeline_completed_utc`
- `duration_ms`
- `stage_durations_ms` (sync/generate/publish)
- `stage_status` details blocks

---

### 3) Orchestrator integration points
Integrate with existing service/admin flow without duplicating logic:

- Prefer reusing existing `CalendarService.refresh()`, `generate()`, `publish_cache()` (or `refresh_full`) where possible.
- Keep operation lock compatibility with existing admin commands and scheduler loop.

---

### 4) Partial failure handling and resilience
Required behavior:

- Sequential stage execution.
- If a stage fails:
  - return failure with clear stage + error list.
  - do not clobber usable existing SQL/JSON state.
- Preserve-on-empty publish behavior must remain in effect unless forced by admin option.

---

### 5) Observability and telemetry
Emit structured telemetry at:

- pipeline started
- per-stage started/success/failure
- pipeline completed/failure

Include:

- actor (if provided)
- stage name/status
- duration
- key counters (`events_generated`, `events_written`)
- error type/message

---

### 6) Retry/timeout policy (Task 6 upgrade)
Define orchestrator-level policy (env-driven or constants-backed):

- per-stage timeout
- per-stage retries
- exponential backoff (with cap)
- clear terminal failure reporting after retry exhaustion

Do not block event loop on heavy sync/generation/publish operations.

---

### 7) Determinism + safety expectations
- Repeated runs with unchanged source should be deterministic in outcome.
- Integrate with diff-aware publish semantics if already implemented (skip unchanged write + explicit status).
- Avoid duplicate/parallel runs by honoring operation locking strategy.

---

### 8) Mandatory code-review follow-ups to include in Task 6 scope

#### a) Harden float env parsing for anomaly thresholds (`constants.py`)
Current float parsing using `float(_env_str(...))` can raise raw `ValueError` at import time and crash startup with poor operator diagnostics.

Required changes:
- Add `_env_float(name: str, default: float | None = None) -> float` helper (mirrors `_env_int` style).
- Use `_env_float` for:
  - `EVENT_CALENDAR_ANOMALY_VOLUME_SPIKE_MULTIPLIER`
  - `EVENT_CALENDAR_ANOMALY_CANCELLED_RATIO_WARN`
- Validate ranges with clear config errors:
  - `EVENT_CALENDAR_ANOMALY_VOLUME_SPIKE_MULTIPLIER > 0`
  - `0.0 <= EVENT_CALENDAR_ANOMALY_CANCELLED_RATIO_WARN <= 1.0`
- Raise `RuntimeError` with actionable message on invalid values.

#### b) Remove/fix tautological runtime-cache wrapper tests
Current tests that monkeypatch and call the same target do not verify behavior.

Required changes:
- If `commands/runtime_cache.py` wrapper exists:
  - test real delegation by monkeypatching `event_calendar.runtime_cache.*`
  - assert wrapper delegates/returns correctly.
- If wrapper is removed/unused:
  - remove wrapper delegation tests entirely.
- Ensure no tautological tests remain.

---

## Non-functional requirements

- Local-first deployment compatibility.
- Event-loop safe orchestration (offload blocking work).
- Clear operator-facing status and failure context.
- No regression of Task 1–5 resilience guarantees.

---

## Acceptance criteria

- Pipeline runs sequentially (**Sheets → Generate → Publish**).
- Partial failures are handled and reported clearly.
- Existing SQL/JSON remains usable after stage failures.
- Result object includes required fields:
  - `sheets_sync_success`
  - `sql_generation_success`
  - `json_export_success`
  - `events_generated`
  - `errors`
- Telemetry emitted for pipeline + stage outcomes.
- Operation lock compatibility maintained.
- Float env parsing for anomaly thresholds hardened with explicit helper + range validation.
- Tautological runtime-cache tests removed/fixed.
- Tests pass locally.

---

## Minimum test plan (pytest)

Add/extend tests:

- `tests/test_calendar_pipeline.py`
- `tests/test_calendar_service.py` (orchestrator integration coverage)
- `tests/test_calendar_publish_cache.py` (preserve-on-empty interaction path)
- `tests/test_constants.py` (or equivalent) for `_env_float` behavior/range validation
- wrapper test file only if wrapper remains (`tests/test_commands_runtime_cache_wrapper.py`)

Cover:

1. **Happy path**
   - all stages succeed
   - expected result flags true
   - counters populated

2. **Sync failure**
   - pipeline stops at sync
   - generation/publish not called
   - result shows sync failure + error list

3. **Generation failure**
   - sync success, generate fail, publish skipped
   - proper stage/error reporting

4. **Publish failure**
   - sync+generate success, publish fail
   - prior SQL state remains usable

5. **Preserve-on-empty path**
   - publish returns preserve/skip status
   - treated per agreed success semantics

6. **Retry behavior**
   - transient failure then success within retries
   - retry exhaustion returns terminal failure

7. **Timeout behavior**
   - stage timeout produces clear error classification/status

8. **Telemetry emission**
   - start/success/failure events include expected keys

9. **Lock compatibility**
   - concurrent invoke attempts serialize or no-op according to lock policy

10. **Env float helper validation**
   - valid float parses correctly
   - invalid float raises `RuntimeError` with clear message
   - out-of-range cancelled ratio fails with clear error
   - non-positive spike multiplier fails with clear error

11. **Wrapper delegation tests (only if wrapper exists)**
   - patch canonical `event_calendar.runtime_cache.*`
   - assert wrapper returns delegated values
   - no self-patched tautological assertions

---

## SQL/local verification scripts (recommended)

In SQL repo/local scripts, verify:

- source tables remain intact after simulated stage failures
- EventInstances not partially corrupted by failed pipeline run
- publish source readiness remains valid after retries/failures

Suggested scripts:

- `sql/tests/verify_calendar_pipeline_orchestrator_smoke.sql`
- `sql/tests/verify_calendar_pipeline_failure_safety.sql`

---

## Implementation order (recommended)

1. Create orchestrator module and result contract
2. Wire sequential stage execution with early-stop rules
3. Add per-stage timeout/retry/backoff policy
4. Add telemetry for pipeline + stage events
5. Integrate with existing service/admin entry points
6. Implement `_env_float` + anomaly threshold range validation in `constants.py`
7. Fix/remove tautological runtime-cache wrapper tests
8. Add pytest coverage for happy/failure/retry/timeout/config-validation paths
9. Add SQL verification scripts and run locally
10. Update docs/status notes

---

## Notes / context to carry forward from Task 5

- Task 5 is completed and locally validated.
- Task 4 feedback baseline has been integrated (including non-blocking calendar health path).
- Runtime architecture remains:
  - Sheets (editor surface) → SQL (operational source) → JSON cache (runtime source).
- Reuse-first principle applies:
  - do not re-implement sync/generate/publish internals if service-layer functions already provide correct behavior.
- Local-first workflow remains:
  - pytest for bot code, SQL scripts for SQL verification, manual PR creation.
```

# TASK 6 — Build Pipeline Orchestrator ✅ COMPLETED

## Objective
Implement a production-ready orchestrator that runs the full Event Calendar refresh pipeline sequentially and safely:

**Sheets Sync → SQL Instance Generation → JSON Export**

Task 6 finalizes deterministic pipeline execution, observability, retry/timeout policy, and failure-safe behavior while preserving last-known-good SQL/JSON runtime operation.

---

## Implementation approach used (reuse-first)
Per project guidance, Task 6 was implemented as a **service-layer orchestration enhancement** (not a full rewrite of stage internals).

### Canonical orchestration path
- `event_calendar/service.py`
  - Added canonical pipeline method:
    - `refresh_pipeline(...)`
  - `refresh_full(...)` now delegates to `refresh_pipeline(...)` for backward compatibility.
  - Existing stage methods reused:
    - `refresh(...)`
    - `generate(...)`
    - `publish_cache(...)`

### Scheduler integration
- `event_calendar/scheduler.py`
  - Updated loop to call `svc.refresh_pipeline(...)`
  - Maintains existing operation lock behavior and loop timeout guard.

---

## Delivered behavior

### 1) Sequential orchestration with early-stop safety
Pipeline executes strictly in order:
1. sync
2. generate
3. publish

If a stage fails, downstream stages are skipped and a structured failure result is returned.

### 2) Required result contract delivered
Pipeline result now includes required Task 6 fields:

- `sheets_sync_success`
- `sql_generation_success`
- `json_export_success`
- `events_generated`
- `errors`

### 3) Enhanced operator contract
Added additional operator-facing fields:

- `pipeline_run_id` (correlation across telemetry/events)
- `pipeline_started_utc`
- `pipeline_completed_utc`
- `duration_ms`
- `stage_durations_ms`
- `stage_status`
- `publish_reason`
- `severity` (`ok|warning|degraded|failed`)
- `actor_source` (`scheduler` or `admin:<id>`)

### 4) Retry + timeout + backoff policy
Added per-stage policy support (env/config driven):

- timeout per stage
- retry counts per stage
- exponential backoff with cap
- terminal reporting when retries are exhausted

### 5) Telemetry upgrades
Structured telemetry emitted for:

- pipeline started
- stage started/succeeded/failed
- retry scheduled
- pipeline completed/failed

with run correlation and key counters.

### 6) Preserve-on-empty compatibility
Publish preserve behavior remains valid:
- `skipped_empty_preserve_existing` is treated as successful export semantics.

---

## Mandatory follow-ups from Task 6 scope completed

### a) Float env hardening (`constants.py`)
Added explicit `_env_float(...)` helper and range validations for:

- `EVENT_CALENDAR_ANOMALY_VOLUME_SPIKE_MULTIPLIER > 0`
- `0.0 <= EVENT_CALENDAR_ANOMALY_CANCELLED_RATIO_WARN <= 1.0`

Config errors now raise actionable `RuntimeError` messages.

### b) Test quality correction
Runtime/scheduler/service tests were aligned to real orchestration paths and non-tautological behavior.

---

## Test & validation results

## Pytest
Task 6-related suites pass locally, including service and scheduler orchestration behavior.

## SQL verification scripts
Task 6 SQL verification scripts pass locally, confirming:

- no invalid time windows
- no duplicate logical instances
- `EffectiveHash` present
- failure-safety integrity checks pass

---

## Backward compatibility notes
- Existing callers of `refresh_full(...)` remain supported.
- Core stage result keys (`ok`, `status`, stage blocks) remain available.
- New pipeline fields are additive.

---

## Operational notes
- Architecture remains:
  - Sheets (editor) → SQL (source of truth) → JSON (runtime source)
- Commands/scheduler continue to run without direct Sheets dependency at runtime reads.
- Failure in one stage does not intentionally clobber last-known-good SQL/JSON runtime state.

---

## Task 6 acceptance criteria status
- [x] Sequential pipeline orchestration implemented
- [x] Partial failures handled with clear stage reporting
- [x] Required result contract fields included
- [x] Telemetry emitted for pipeline and stage outcomes
- [x] Operation lock compatibility maintained
- [x] Float env parsing hardened with range checks
- [x] Tests pass locally
- [x] SQL verification scripts pass locally

---

## Next (Task 7 handoff)
Task 7 can focus on admin/operator UX expansion and command-layer presentation improvements while reusing Task 6 canonical pipeline result/status model.
