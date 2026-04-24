# TASK 3 — Build Event Instance Generator + SQL→JSON Publish (Production-Ready)

## Objective
Implement the generation and publish stage of the Event Calendar pipeline:

Google Sheets → SQL source tables → EventInstances → JSON cache → Bot runtime

Task 3 must generate concrete event instances from SQL source tables, apply overrides deterministically, and publish a runtime JSON cache from SQL with strong resilience guarantees.

---

## Scope

### 1) Event instance generation from SQL
Create module:

- `event_calendar/event_generator.py`

Implement functions:

- `load_recurring_rules()`
- `load_oneoff_events()`
- `load_overrides()`
- `generate_recurring_instances()`
- `merge_events()`
- `apply_overrides()`
- `write_event_instances()`
- `generate_calendar_instances()`

Behavior:

- Read **active** rows from:
  - `dbo.EventRecurringRules`
  - `dbo.EventOneOffEvents`
  - `dbo.EventOverrides`
- Generate recurring occurrences within configured horizon (default 365 days from now UTC), constrained by:
  - `RecurrenceType`
  - `IntervalDays`
  - `FirstStartUTC`
  - `RepeatUntilUTC`
  - `MaxOccurrences`
- Compute recurring end time via duration:
  - `end_utc = start_utc + DurationDays`
- Merge one-off events into unified instance set.
- Sort deterministically by start time + stable tie-breakers.

### 2) Override application (deterministic)
Apply overrides after merge and before persistence.

Match precedence key:

- `TargetKind`
- `TargetID`
- `TargetOccurrenceStartUTC` (when provided)

Actions:

- `cancel` → mark cancelled (preferred) or remove from publish set (must be deterministic and documented)
- `modify` → patch `New*` fields onto target instance

Validation:

- enforce supported `TargetKind` values (`rule|oneoff|instance`)
- reject invalid time windows (`end <= start`)
- log row-context validation failures clearly

### 3) Persist generated instances into SQL
Write to:

- `dbo.EventInstances`

Requirements:

- No partial visible state on failure.
- Use transactional rebuild strategy (single transaction for rebuild phase).
- Prefer staging/swap or delete+insert inside one transaction.
- Compute and store `EffectiveHash` from final post-override payload.
- Ensure idempotent reruns and deterministic output.

### 4) Publish SQL → JSON runtime cache
Create module:

- `event_calendar/cache_publisher.py` (or equivalent service-layer function)

Behavior:

- Read from SQL `EventInstances` only (never from Sheets).
- Emit runtime JSON matching established cache contract.
- Include generation timestamp + horizon metadata.
- Preserve-on-empty safety:
  - do not overwrite last-known-good cache with empty/invalid payload unless explicitly forced by admin option.

### 5) Service + admin controls
Integrate in `event_calendar/service.py` and admin commands:

- `/calendar_generate` (or include generation as a stage of `/calendar_refresh`)
- `/calendar_publish_cache`
- `/calendar_status` must include:
  - last generate status/time
  - instances generated count
  - publish status/time
  - cache event count
  - last error (if any)

### 6) Logging and telemetry
Extend structured telemetry:

- generation started/success/failure
- publish started/success/failure
- counts and duration
- error type/message with context

Update `EventSyncLog` usage (or add generation log structure) so operators can audit each run clearly.

---

## Non-functional requirements (production quality)

- Graceful degradation: existing SQL + JSON remain usable during Sheets failures.
- Commands must stay responsive:
  - avoid blocking event loop for heavy sync/generation/publish operations.
- Concurrency safety:
  - serialize admin-triggered refresh/generate/publish operations with operation locks.
- Strong validation before DB writes.
- Deterministic behavior across reruns.

---

## Incorporate Task 1/2 review feedback where applicable

Task 3 implementation should carry forward these quality fixes:

1. Run blocking sync/generation DB+HTTP work off event loop (e.g., `asyncio.to_thread`) or move to async stack.
2. Emit telemetry on service-level exception paths too (not only happy path).
3. Serialize refresh/generate/publish via operation lock.
4. Keep config parsing consistent (`_env_str(...)` style).
5. Normalize CSV keys (trim/lower/BOM-safe) before parser access.
6. Validate override `TargetKind` before SQL write.
7. Prefer single transaction for multi-stage write operations to avoid partial commit.
8. Guard dynamic SQL helpers with identifier allowlists.
9. Ensure dependencies are declared if new imports are introduced.

---

## Acceptance criteria

- Recurring rules generate correct occurrences across horizon.
- One-off events merged correctly.
- Overrides:
  - cancel works correctly
  - modify works correctly
- `EventInstances` output is deterministic and sorted.
- Re-run is idempotent; no duplicate logical instances.
- `EffectiveHash` reflects final post-override payload.
- JSON cache publishes from SQL and matches cache contract.
- Preserve-on-empty guard prevents destructive cache overwrite.
- `/calendar_status` reports generation/publish metrics and last outcomes.
- Failures do not wipe last-known-good SQL/JSON runtime state.
- Unit tests and targeted integration-like tests pass.

---

## Minimum test plan

Add/extend tests:

- `tests/test_event_generator.py`
- `tests/test_event_overrides.py`
- `tests/test_calendar_publish_cache.py`
- `tests/test_calendar_service.py` (generation/publish status + failure paths)

Cover:

- recurrence intervals and boundaries (`repeat_until`, `max_occurrences`)
- all-day handling
- override precedence and patching
- cancel semantics
- deterministic sorting and hashing
- preserve-on-empty behavior
- failure rollback behavior for SQL writes
