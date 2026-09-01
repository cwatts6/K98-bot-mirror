# Codex Task Pack - Pinned Calendar Tracker Atomic Persistence

## 1. Task Header

- Task name: `Pinned Calendar Tracker Atomic Persistence`
- Date: `2026-09-01`
- Owner/context: `Chris Watts / K98 event calendar reliability`
- Task type: `deferred optimisation execution task | restart-sensitive persistence hardening`
- One-pass approved: `no`
- Status: `implementation-ready task pack — audit/scope approval required before code changes`

## 2. Objective

Replace the direct JSON write in `event_calendar/pinned_embed.py::_save_tracker()` with the
established `file_utils.atomic_write_json()` helper while preserving the exact tracker contract,
best-effort error boundary, pinned-message recovery behavior, startup ordering, Discord output,
and scheduler behavior.

This is a narrow reliability fix. It is independent of Import Pipeline Task C Slice 14 evidence
collection and can proceed while naturally occurring fallback evidence accrues.

## 3. Deferred Item And Priority

The active deferred item records that `_save_tracker()` currently uses direct
`Path.write_text()` JSON persistence even though the file is consumed during restart rehydration.
The item is implementation-ready with medium impact and low implementation risk.

| Impact | Frequency | Risk reduction | Effort | Score | Recommendation |
|---|---:|---:|---:|---:|---|
| 3 | 3 | 4 | 1 | 9 | Good isolated implementation candidate |

The score reflects daily/startup use, the operational cost of a damaged tracker, and the small
surface of the proposed change. It does not broaden the task into calendar or lifecycle redesign.

## 4. Current Architecture And Contract

`event_calendar/pinned_embed.py` currently owns the tracker boundary:

- `_TRACKER_PATH` is `Path(DATA_DIR) / "calendar_pinned_tracker.json"`.
- `_load_tracker()` returns decoded JSON when available and returns `{}` after a missing file,
  malformed file, or read failure; read failures are logged.
- `_save_tracker()` creates the parent directory, writes indented JSON directly with
  `Path.write_text()`, logs any failure, and deliberately does not propagate the exception.
- `update_calendar_embed()` uses the tracker to edit the existing message when possible and
  recreates the message when the tracked target is missing.
- The edit path writes `channel_id`, `message_id`, and `updated_at_utc`.
- The create path preserves the loaded dictionary and sets `channel_id` and `message_id`; it does
  not independently add or remove other fields.
- `rehydrate_pinned_calendar_view()` returns `missing_tracker` when identifiers are absent and
  writes `{}` when the tracked channel/message can no longer be found.

The startup lifecycle schedules pinned-calendar rehydration through
`ready_pinned_calendar_rehydration`, then starts the daily pinned refresh and calendar reminder
tasks. This ordering, the eight-second background scheduling boundary, and task names are inherited
contracts.

## 5. Approved Implementation Boundary

The proposed PR-sized change is:

1. Import `atomic_write_json` from `file_utils` in `event_calendar/pinned_embed.py`.
2. Inside the existing `_save_tracker()` `try` block, call
   `atomic_write_json(_TRACKER_PATH, data, ensure_parent_dir=True)`.
3. Remove only the now-redundant explicit parent-directory creation from `_save_tracker()`.
4. Retain the existing `_save_tracker()` exception logging and non-raising behavior.
5. Add focused tracker persistence and rehydration regression tests in
   `tests/test_calendar_pinned_embed.py`.

`atomic_write_json()` is the preferred helper because it:

- already accepts `Path` or `str` targets;
- creates the parent directory;
- writes indented UTF-8 JSON with `ensure_ascii=False`;
- flushes and `fsync`s the temporary file before `os.replace()`;
- retries transient Windows sharing violations; and
- removes its temporary file after a failed final replace while leaving the previous target file
  intact.

Do not change `file_utils.py` for this slice. If implementation review discovers a separate shared
helper defect, stop and capture or scope that independently.

## 6. In Scope

- The `_save_tracker()` writer implementation in `event_calendar/pinned_embed.py`.
- Its import of the existing atomic helper.
- Focused tests for tracker save/load, failure protection, exact payload behavior, missing tracker,
  missing tracked message recovery, and successful restart rehydration.
- Minimal task-pack, test, and deferred-record alignment needed for the eventual PR.
- Bot-only validation and a bot-diff security review.

## 7. Explicitly Out Of Scope

- Tracker path, filename, schema, field normalization, migration, or SQL persistence.
- Changes to `_load_tracker()` semantics beyond test seams required for this fix.
- A new atomic JSON helper or changes to `atomic_write_json()`/`atomic_json_write()`.
- Locks, async offloading, scheduler redesign, task timing, or startup phase reordering.
- Calendar cache, reminder preferences/state, reminder dispatch, event selection, embeds, buttons,
  commands, permissions, channel configuration, or user-facing text.
- Automatic repair of malformed tracker JSON beyond the existing `{}` fallback.
- Forced message recreation, duplicate-message cleanup, or pin-permission behavior changes.
- SQL repository changes, migrations, deployment scripts, or import-pipeline work.
- Other direct JSON writers or broader persistence consolidation.

## 8. Required Behavior Invariants

- A successful save remains valid indented UTF-8 JSON at the existing path.
- Existing integer `channel_id` and `message_id` values and any existing `updated_at_utc` value are
  preserved exactly as supplied by the caller.
- The edit path still updates the existing message and records `updated_at_utc`.
- The create path still stores the new message identity without introducing a new schema rule.
- A missing tracker still loads as `{}` and leads to the current create/missing-tracker outcomes.
- A malformed or unreadable tracker still logs and falls back to `{}`.
- A failed atomic replace does not truncate or partially overwrite the previously valid tracker.
- Save failures remain logged as `[CALENDAR][PINNED] tracker save failed` and do not change the
  structured result returned by the current caller.
- A missing tracked message/channel still clears the tracker through `_save_tracker({})` and
  returns `message_or_channel_missing`.
- Startup and daily refresh must not create a duplicate pinned message when the stored target is
  valid.

## 9. Test And Validation Plan

### Focused automated coverage

Extend `tests/test_calendar_pinned_embed.py` to cover:

1. `_save_tracker()` writes through `atomic_write_json()` with the existing path and unmodified
   payload.
2. A real temporary-path save/load round trip produces valid JSON and preserves identifiers.
3. A simulated atomic-write failure is logged and leaves an existing valid tracker unchanged.
4. Missing and malformed tracker files return `{}` with the existing logging behavior.
5. The existing-message edit path persists the exact edit payload and does not send a duplicate.
6. The create path persists the new channel/message identifiers.
7. Rehydration with a valid tracker edits the existing message view.
8. Rehydration with a missing target clears the tracker through the same writer and returns the
   current status.

Retain the existing shared helper retry tests in `tests/test_file_utils_atomic_write_retry.py`; do
not duplicate the complete helper test suite in the calendar module.

### Deterministic validation

Run from the bot repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_calendar_pinned_embed.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_calendar_*.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_event_rehydration_lifecycle.py tests\test_scheduler_lifecycle.py tests\test_startup_lifecycle.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_file_utils_atomic_write_retry.py
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run --all-files
```

Because JSON persistence and restart rehydration are involved, run the full test suite before
production promotion when practical. If it is skipped, record the reason and retain the focused
restart/persistence evidence above.

## 10. Security Review Decision

The eventual implementation touches a filesystem state file consumed after restart. Route the bot
branch through `k98-security-review-routing` and run a Changes-only
`codex-security:security-diff-scan` against the intended base/head or working-tree patch. Confirm:

- Scan type: `Changes`.
- Deep scan: `off`.
- Target: bot repository implementation diff only.
- Focus: path remains fixed under `DATA_DIR`, payload remains internally generated, failed writes
  preserve the previous state, and rehydration does not widen channel/message authority.

Do not run a standard or deep codebase scan. This documentation-only preparation is eligible for a
documented security-review skip because it changes no executable behavior.

## 11. Manual Smoke Expectations

After the normal reviewed production promotion and bot restart:

1. Confirm startup reaches `ready_pinned_calendar_rehydration` and
   `ready_calendar_scheduler_tasks` without a pinned-calendar load/save failure.
2. Confirm the existing pinned calendar message is rehydrated/edited in place rather than a
   duplicate message being created.
3. Confirm `calendar_pinned_tracker.json` remains valid JSON with the expected channel/message IDs.
4. Confirm no stale tracker temporary file remains after a successful refresh.
5. Observe the next normal pinned refresh result and verify the existing `edited` or `created`
   telemetry/status semantics.

Do not intentionally create a production write failure or delete the live pinned message to test
the negative path. Automated tests cover failure preservation and missing-target recovery. No SQL
deployment or Discord command resync is expected.

## 12. Rollback

Revert the bot commit and redeploy through the normal production workflow. The tracker path and
JSON schema are unchanged, so the atomically written file remains readable by the previous code.
No data migration or SQL rollback is required.

## 13. Acceptance Criteria

- [ ] Scope review confirms `event_calendar/pinned_embed.py` is still the tracker owner.
- [ ] The existing `atomic_write_json()` contract is still suitable and no shared-helper change is
  needed.
- [ ] `_save_tracker()` no longer uses direct `Path.write_text()` persistence.
- [ ] Tracker schema, caller payloads, failure logging, and non-raising behavior are preserved.
- [ ] A simulated failed write leaves a prior valid tracker intact.
- [ ] Missing, malformed, create, edit, clear, and rehydration paths have focused coverage.
- [ ] Selected validators and focused tests pass; skips and unrelated failures are documented.
- [ ] The implementation diff receives the required Changes-only security review.
- [ ] Production smoke confirms restart rehydration and in-place refresh without duplicates.
- [ ] No SQL, command, UX, scheduler, cache, reminder, or shared-helper change is included.

## 14. Approval Gate

Begin the implementation chat with repository and scope audit only. Report the current writer,
helper contract, call/restart map, exact intended diff, validation selection, security routing, and
open questions. Stop for operator approval before changing code or tests.
