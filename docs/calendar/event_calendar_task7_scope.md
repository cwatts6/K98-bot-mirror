# TASK 7 — Admin Commands (Manual Control + Diagnostics)

## Objective
Provide robust admin command controls for manual pipeline execution and diagnostics, while preserving Task 6 resilience guarantees and integrating Task 6 code-review follow-ups.

Primary operator outcomes:

- manual trigger for full pipeline
- status/health diagnostics without requiring a refresh
- clear, actionable error reporting for admins

---

## Scope

### 1) Admin command surface
Implement/standardize:

- `/refresh_calendar`
- `/calendar_status`

Suggested file:

- `commands/commands_calendar.py` (or keep in `commands/admin_cmds.py` if repository convention prefers centralized admin commands)

### `/refresh_calendar`
Runs canonical pipeline and returns concise operational summary:

- overall status (`ok/failed/degraded/warning`)
- stage (`sync/generate/publish/done/exception`)
- run id (`pipeline_run_id`)
- durations
- generated/published counts
- errors (if any)

### `/calendar_status`
Must work at all times (even before any refresh) and display:

- last sync time/status
- last successful generation timestamp
- last pipeline run status/time
- number of cached events
- cache horizon
- stale/degraded indicators
- latest error context (if available)

---

## Task 6 code-review feedback incorporated into Task 7 scope

Task 7 includes completion/hardening of open Task 6 review items to avoid operational regressions.

### A) Scheduler outer timeout mismatch
Current scheduler wraps full pipeline in:

- `asyncio.wait_for(..., timeout=EVENT_CALENDAR_PIPELINE_TIMEOUT_SECONDS)`

Issue:
- outer timeout default can be lower than worst-case stage timeout/backoff envelope.

Task 7 requirement:
- remove or recompute outer timeout as validated upper bound based on configured stage policies + retries + max backoff
- emit explicit startup/config telemetry if bounds are invalid
- document final behavior in runbook

### B) `tests/test_constants.py` reload safety
Issue:
- `importlib.reload(constants)` failure can leave partial module state in `sys.modules`.

Task 7 requirement:
- isolate constants validation tests (subprocess-based import checks preferred), or ensure restoration to known-good module state in fixture teardown
- avoid cross-test contamination

### C) Minor test cleanup
Remove non-essential inline fixture comment:

- `type_index_path = "cache/event_type_index.json"`

(no inline “add this” comment)

### D) Retry policy currently bypassed by stage wrappers
Issue:
- stage methods catch exceptions and return `{ok: False}`, so exception-only retry logic often never triggers.

Task 7 requirement:
- implement explicit result-based retry policy in pipeline stage runner:
  - retry when `ok == False` and status is retryable
  - do not retry non-retryable statuses
- define retryable status map per stage (sync/generate/publish)

### E) Timeout + `to_thread` overlap risk
Issue:
- `asyncio.wait_for` timeout on coroutine using `to_thread` cannot cancel underlying thread; retries may create overlapping work.

Task 7 requirement:
- for thread-offloaded stages, avoid unsafe timeout+retry overlap:
  - either disable timeout-retry combinations for `to_thread` stages
  - or classify timeout as non-retryable for those stages
  - or move timeout cooperatively into blocking worker layer
- document concurrency safety rationale

### F) Pipeline env policy validation
Issue:
- stage timeout/retry/backoff constants parsed but not fully range-validated.

Task 7 requirement:
- validate all pipeline policy constants at import time:
  - timeouts > 0
  - retries >= 0
  - backoff base > 0
  - backoff cap > 0
  - cap >= base

### G) Override target-kind mapping consistency
Issue:
- mapping included `recurring` key while override validator accepted only `rule|oneoff|instance`.

Task 7 requirement:
- align behavior explicitly:
  - either accept `recurring` in validator and message
  - or remove unreachable mapping key
- keep source-of-truth docs consistent with accepted values

---

## Functional requirements

### 1) Command behavior and UX
- both commands must defer/respond safely under Discord interaction deadlines
- use operation locks for refresh command to serialize manual operations
- responses should include run id for support traceability
- error embeds/messages must include stage + concise error detail

### 2) Status behavior without refresh
`/calendar_status` must return meaningful output if no pipeline run has happened yet:

- explicit `not_started` values
- no crashes on missing cache file
- clear stale/unavailable banner states

### 3) Runtime source integrity
- commands must not query Google Sheets directly
- status may read JSON cache metadata and service state only
- refresh uses canonical service pipeline path

---

## Non-functional requirements

- local-first deployment compatibility
- no blocking of event loop in command handlers
- backward-compatible with existing service/scheduler architecture
- deterministic and auditable operator output

---

## Acceptance criteria

- [x] `/refresh_calendar` triggers canonical pipeline and returns summary
- [x] `/calendar_status` works before and after refresh runs
- [x] status includes sync/generate/publish/pipeline + cache health elements
- [x] errors are clearly reported with stage context
- [x] command path remains Sheets-decoupled at runtime read layer
- [x] scheduler outer-timeout policy corrected/validated
- [x] retry behavior fixed for result-based failures (not exception-only)
- [x] thread-timeout overlap risk mitigated
- [x] pipeline env policy constants fully validated
- [x] constants tests made isolation-safe
- [x] minor test cleanup applied
- [x] override target-kind validation/mapping consistency resolved
- [x] pytest suites pass locally
- [x] SQL verification scripts pass locally

---

## Minimum test plan (pytest)

Add/extend tests in:

- `tests/test_admin_calendar_commands.py` (or existing admin command test file)
- `tests/test_calendar_service.py`
- `tests/test_calendar_pipeline.py`
- `tests/test_calendar_scheduler.py`
- `tests/test_constants.py` (subprocess or safe restoration approach)
- `tests/test_event_generator.py`

Cover:

1. `/refresh_calendar` happy path response includes run id + stage summary
2. `/refresh_calendar` failure path includes stage + error detail
3. `/calendar_status` works with no prior run (`not_started` states)
4. `/calendar_status` with cache missing/invalid returns safe diagnostics
5. scheduler timeout policy bound is valid for configured stage policies
6. result-based retry path retries configured retryable statuses
7. non-retryable statuses do not retry
8. timeout on thread-offloaded stage does not trigger unsafe overlapping retry
9. constants invalid policy values fail fast with clear RuntimeError
10. constants tests do not poison module state for later tests
11. override target-kind validation/mapping consistency tests pass

---

## SQL/local verification scripts (recommended)

Run existing plus Task 7 diagnostics scripts in local SQL workflow:

- verify pipeline integrity after manual command-triggered runs
- verify no partial EventInstances corruption on failed refresh paths
- verify publish source remains coherent after retry/timeout scenarios

Suggested additions:

- `sql/tests/verify_calendar_task7_command_refresh_smoke.sql`
- `sql/tests/verify_calendar_task7_failure_retry_safety.sql`

---

## Implementation order (recommended)

1. Wire/standardize `/refresh_calendar` command to canonical pipeline call
2. Wire/standardize `/calendar_status` output contract
3. Add stage/run-id summary formatting helpers
4. Fix scheduler outer-timeout policy strategy
5. Update service retry logic to support result-based retry eligibility
6. Mitigate timeout + to_thread overlap risk (disable unsafe retries or cooperative timeout approach)
7. Add full pipeline policy constant validation in `constants.py`
8. Align override TargetKind validation/mapping semantics
9. Harden constants tests for import isolation
10. Clean minor test nits and update fixtures
11. Run pytest and SQL scripts locally
12. Update docs/runbook with command usage + troubleshooting

---

## Operational notes

- Keep reuse-first principle from Task 6:
  - do not duplicate sync/generate/publish internals
  - command layer should orchestrate + present status only
- Include `pipeline_run_id` in every admin-facing refresh response for incident triage
- Keep status output operator-friendly and stable for future automation
