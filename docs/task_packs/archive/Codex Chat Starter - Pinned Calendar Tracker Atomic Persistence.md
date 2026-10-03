# Codex Chat Starter - Pinned Calendar Tracker Atomic Persistence

> **Completed record — 2026-09-01:** This starter launched the delivered atomic persistence fix.
> Mirror PR #250 and production PR #557 completed implementation and deployment. Automated
> validation, a Changes-only security review with Deep off and zero findings, and operator
> production restart smoke all passed. The existing pinned message was rehydrated and edited in
> place with unchanged channel/message identity and valid tracker JSON. This archived file is
> retained as execution history, not active work.

Use this starter to begin the implementation task. One-pass execution is not approved: the first
response is audit/scope only and must stop for approval before code or test changes.

## Copy/Paste Starter

```markdown
# Files mentioned by the user:

## Codex Task Pack - Pinned Calendar Tracker Atomic Persistence.md: C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Pinned Calendar Tracker Atomic Persistence.md

## My request for Codex:
Begin the Pinned Calendar Tracker Atomic Persistence task.

Use the task pack:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Pinned Calendar Tracker Atomic Persistence.md

This is a narrow bot reliability fix and is independent of Import Pipeline Task C Slice 14 evidence
collection. Start with audit/scope only. Do not change code or tests until I approve the first
response.

Current confirmed baseline to revalidate:
- event_calendar/pinned_embed.py owns DATA_DIR/calendar_pinned_tracker.json.
- _load_tracker() reads JSON and falls back to {} for a missing, malformed, or unreadable tracker.
- _save_tracker() currently creates the parent and writes indented JSON with Path.write_text(); it
  logs failures and deliberately does not propagate them.
- update_calendar_embed() edits the tracked message when available, recreates it when missing, and
  persists channel_id/message_id plus updated_at_utc on the edit path.
- rehydrate_pinned_calendar_view() uses the tracker during restart and clears it when the tracked
  message or channel is missing.
- startup schedules pinned-calendar rehydration before the daily pinned refresh/calendar reminder
  tasks.
- file_utils.atomic_write_json() is the preferred existing helper. It supports Path targets,
  parent creation, UTF-8 indented JSON, flush/fsync, atomic replace, Windows sharing-violation
  retries, and failed-temp cleanup.

Proposed implementation boundary:
- Import atomic_write_json into event_calendar/pinned_embed.py.
- Replace only the direct writer inside the existing _save_tracker() try/except with
  atomic_write_json(_TRACKER_PATH, data, ensure_parent_dir=True).
- Preserve the existing exception log and non-raising behavior.
- Add focused tests in tests/test_calendar_pinned_embed.py.
- Do not change file_utils.py unless a separately evidenced blocker is found and approved.

Preserve exactly:
- tracker path and current dictionary shape;
- edit/create payload differences and updated_at_utc behavior;
- missing/malformed tracker fallback;
- missing-message recovery and tracker clearing;
- caller result/status and telemetry semantics;
- startup ordering, scheduler timing and task names;
- pinned-message create/edit/pin behavior and all user-facing output.

Explicitly out of scope unless separately approved:
- tracker migration, SQL persistence, schema normalization, or a new helper;
- changes to atomic_write_json or atomic_json_write;
- locks, async offloading, lifecycle/scheduler redesign, or startup reordering;
- calendar cache/reminders/preferences, event rules, embeds, buttons, commands, permissions, config,
  channel behavior, or user-facing text;
- broad JSON writer consolidation, SQL changes, imports, or unrelated cleanup.

Required focused coverage:
- exact helper path/payload handoff and a real temporary-path save/load round trip;
- failed-write logging and preservation of a prior valid tracker;
- missing and malformed tracker behavior;
- create and existing-message edit persistence, including no duplicate send on edit;
- valid restart rehydration and missing-target clear behavior;
- existing shared atomic helper retry coverage and calendar/startup lifecycle regressions.

Required first response:
- Scope summary and why this is a bounded implementation-ready deferred item.
- Current tracker owner, write/read callers, startup/rehydration map, and concurrency assessment.
- Exact atomic helper comparison and confirmation that atomic_write_json remains the right choice.
- Exact proposed file/test diff and preserved behavior invariants.
- Selector-driven and risk-based validation plan, including focused calendar, rehydration, startup,
  atomic-helper, validator, smoke-import, command-registration, and pre-commit gates.
- Codex Security routing: implementation requires a bot Changes-only diff review with Deep off;
  no standard/deep codebase scan.
- Production smoke and rollback expectations.
- Open questions or approval needed.

Stop for approval before code or test changes. After approval, implement only the agreed boundary,
validate it, review it, create the mirror PR, and leave production promotion/deployment for the
normal separately approved workflow.
```
