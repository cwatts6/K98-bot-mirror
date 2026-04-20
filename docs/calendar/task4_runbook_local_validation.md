# Task 4 Local Validation Runbook

## 1) Pytest (calendar target suites)

```bash
pytest -q tests/test_calendar_service.py \
         tests/test_calendar_publish_cache.py \
         tests/test_event_generator.py \
         tests/test_calendar_runtime_cache.py \
         tests/test_calendar_scheduler.py
```

Expected: all pass.

---

## 2) Manual SQL verification scripts

Run in order:

1. `sql/tests/verify_calendar_task4_publish_source.sql`
2. `sql/tests/verify_calendar_task4_generation_determinism.sql`

Expected outcomes:
- no invalid time windows (`EndUTC <= StartUTC`)
- no duplicate logical instances by `(SourceKind, SourceID, StartUTC)`
- `EffectiveHash` populated for all rows

---

## 3) Runtime cache artifacts

After publish stage, confirm both files exist under `DATA_DIR`:

- `event_calendar_cache.json`
- `event_type_index.json`

Expected:
- JSON valid and parseable
- events sorted deterministically
- type index maps event type -> list of instance IDs

---

## 4) Preserve-on-empty safety

With existing cache present, simulate empty publish source and run publish (default `force_empty=False`).

Expected:
- publish status: `skipped_empty_preserve_existing`
- existing cache files preserved

---

## 5) Status and stale-cache checks

Run `/calendar_status` and verify:

- `sync`, `generate`, `publish` sections present
- `calendar_health` includes:
  - `cache_age_minutes`
  - `cache_stale_warning`
  - `next_upcoming_event_utc`
  - `last_successful_pipeline_utc`
  - `current_degraded_mode`

Stale thresholds:
- warning: 60 minutes
- degraded: 240 minutes

---

## 6) Scheduler smoke

Start scheduler-integrated calendar loop in local environment.

Expected:
- refresh_full executes on interval
- operation lock serialization works
- no overlap with manual admin operation lock usage
