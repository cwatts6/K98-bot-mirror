# Codex Task Pack - Discord Embed Payload Safety Phase 2F Active Reminder Tracker Atomic Persistence

## 1. Task Header

- Task name: `Discord Embed Payload Safety Phase 2F Active Reminder Tracker Atomic Persistence`
- Date: `2026-09-07`
- Owner/context: `Chris Watts / next audit-first slice after Phase 2E candidate delivery`
- Task type: `restart-sensitive persistence reliability`
- One-pass approved: `no; audit/scope and architecture planning first, then stop for approval`
- Status: `prepared; implementation not approved`
- Repository: `K98-bot-mirror` bot repository first; SQL is no-diff unless separately approved

## 2. Prerequisites And Required Reading

Read current `AGENTS.md`, the core references indexed by `docs/reference/README.md`, applicable
`SECURITY.md`, `docs/reference/events_and_dm_reminders.md`, `docs/reference/runbook_startup.md`,
`docs/reference/singleton_lock.md`, the archived Discord Embed Payload Safety findings, and the
archived Phase 2E task pack.

Before selecting an implementation base, revalidate mirror PR #256 and production PR #563 merge
states, final production-main source presence, mirror and production branch/head, worktree state,
and Phase 1-2E prerequisites. Phase 2E was candidate-delivered and operator-smoke accepted on
2026-09-07, but both PR merges and final production-main verification were still operator-owned when
this pack was prepared. Read-only audit may begin before those gates complete; do not edit runtime
code or tests until the delivered Phase 2E tree is verified in the intended base and the operator
approves the Phase 2F findings and exact manifest.

## 3. Objective

Determine and, only after separate approval, implement the smallest atomic replacement boundary for
the restart-sensitive active public-reminder JSON tracker. Preserve the exact semantic state contract,
Discord message identity, reminder timing and eligibility, mentions, cleanup, startup/rehydration,
scheduler, and non-raising failure behavior.

The audit must decide whether the existing shared writer can be used without changing compatibility
or whether a narrowly scoped writer adjustment is required. Do not assume that JSON formatting,
key ordering, Unicode escaping, deterministic temporary naming, or concurrent-writer safety is
irrelevant merely because the parsed object is equivalent.

## 4. Current Evidence To Revalidate

- `event_scheduler.py::save_active_reminders()` serializes each active message as `channel_id`,
  `message_id`, and optional event fallback metadata, but writes the live tracker directly with
  `open(..., "w")` and `json.dump(..., indent=2, sort_keys=True)`.
- Save callers include successful reminder publication/replacement, `safe_delete_reminder()` in its
  cleanup boundary, and orphan cleanup. Their mutation and save order must remain unchanged.
- `load_active_reminders(bot)` accepts legacy JSON, records raw IDs for later orphan cleanup,
  re-fetches channels/messages, uses live event data or stored fallback metadata, reattaches the
  existing `LocalTimeToggleView`, and rebuilds the in-memory `active_reminders` mapping.
- Startup rehydration runs through `core/event_rehydration_lifecycle.py`; cleanup occurs before the
  normal scheduler lifecycle proceeds.
- The repository already has `file_utils.atomic_write_json`, but it differs from the tracker writer
  in formatting defaults and uses a deterministic `.tmp` path. The single-process lock reduces
  cross-process overlap, but thread and coroutine callers still require proof before deciding that no
  lock or unique temporary path is needed.

Treat these as preparation evidence, not final findings. Re-read current code and tests.

## 5. In Scope

- Map every active-reminder state producer, in-memory mutation, save, load, validation, recovery,
  cleanup, restart, and rehydration boundary.
- Prove the actual execution model for every writer: event-loop sequencing, thread offload, process
  ownership, overlapping saves, and shutdown behavior.
- Compare the current direct writer, `file_utils.atomic_write_json`, any existing alternate atomic
  helper, and one narrowly scoped local/extended writer.
- Define exact compatibility requirements for path, semantic keys, identifiers, fallback metadata,
  datetime encoding, indentation/order/Unicode behavior where operationally relevant, malformed and
  incomplete entries, and raw-ID cleanup.
- Define interruption, flush/fsync, replace, retry, temporary-file cleanup, warning, recovery, and
  rollback behavior without making a save failure fatal to the reminder flow.
- Add focused deterministic persistence/rehydration tests only after the audit and exact file
  manifest are approved.
- Update task records, deferred ownership, security evidence, smoke guidance, and rollback evidence.

## 6. Out Of Scope

- Phase 1-2E embed, Ark, diagnostics, confirmation-history, registration, or team-builder behavior.
- Phase 2G atomic Pre-KVK dispatch reservation.
- Stats or KVK History once-only executor audits.
- DM sent/scheduled tracker redesign, event-calendar redesign, or broad JSON writer consolidation.
- Commands, permissions, guild/channel restrictions, visibility, requester ownership, reminder
  eligibility/preferences, event selection, scheduling cadence, expiry timing, mentions, message or
  view identity, startup phase order, task names, scheduler/executor semantics, config, dependencies,
  SQL schema/procedure/DAL contracts, or data migration.
- Deleting a live reminder, corrupting the production tracker, forcing `@everyone`, or inducing a
  production write failure for smoke testing.

## 7. Mandatory First Response And Stop Gate

The first response is audit/scope and architecture planning only. Do not edit runtime code or tests.
It must:

1. Confirm branch/head, worktree, Phase 1-2E prerequisite presence, PR #256/#563 merge states, final
   production-main verification state, intended base, and bot-only scope.
2. Map every `active_reminders` mutation, save/load caller, startup/rehydration step, cleanup path,
   scheduler task, exception boundary, and message/view identity transition.
3. Prove or disprove concurrent writers across coroutines, threads, processes, shutdown, and restart;
   account for the singleton lock without treating it as proof of all writer sequencing.
4. Compare viable writer boundaries, including temporary-path collision behavior, fsync/replace/retry,
   recovery, stale-temp cleanup, compatibility, and rollback.
5. State whether formatting/key-order/Unicode differences are contractual, operationally observed, or
   safely non-semantic; do not silently change them.
6. Produce a findings matrix with `safe`, `fix now`, `defer`, or `not runtime` dispositions and name
   the exact runtime, test, documentation, and separately gated SQL files.
7. Explain how IDs, event fallback metadata, raw-ID cleanup, missing/malformed entries, Discord
   delete/send/edit order, in-memory mapping, mentions, timing, expiry, view reattachment, startup,
   scheduler, logs, and non-raising failures remain unchanged.
8. Give selector-driven tests, bot Changes-only/Deep-off security routing, SQL no-diff criteria,
   production smoke, rollback, and explicit approval questions.
9. Stop for approval.

## 8. Architecture And Compatibility Requirements

- Keep the existing tracker path and parsed JSON shape. Existing valid tracker files must load
  without migration or manual edits.
- Preserve `channel_id`, `message_id`, event fallback keys, datetime meaning, and missing-event basic
  ID fallback. Do not add a version field by implication.
- Preserve the in-memory `active_reminders` mapping and every existing mutation-before-save or
  deletion-finally-save boundary unless the audit proves a defect and separate approval is obtained.
- Preserve missing channel/message handling, malformed/incomplete entry behavior, returned raw IDs,
  orphan cleanup, and `LocalTimeToggleView` reattachment.
- Preserve existing Discord deletion, send, edit, mention, and replacement order. Atomic persistence
  must not become a new send gate or cause duplicate delivery.
- Preserve existing log templates and the broad, non-raising save-failure boundary unless an exact
  compatibility-safe improvement is separately approved.
- Prefer a proven shared utility when its contract fits. Do not broaden a shared helper merely to
  make the diff look uniform.

## 9. Candidate File Manifest

### Audit

- `event_scheduler.py`
- `core/event_rehydration_lifecycle.py`
- `file_utils.py`
- bot startup/scheduler lifecycle and singleton-lock ownership
- `tests/test_event_scheduler_payloads.py`
- `tests/test_event_rehydration_lifecycle.py`
- `tests/test_startup_lifecycle.py`
- `tests/test_scheduler_lifecycle.py`
- `tests/test_file_utils_atomic_write_retry.py`
- `tests/test_rehydrate_sanitize_and_fileio.py`

### Candidate Modify After Approval

- `event_scheduler.py`
- `file_utils.py` only if the audit proves the existing contract cannot safely be reused unchanged
- focused tests and delivery records

### Candidate Create After Approval

- `tests/test_event_scheduler_active_reminders.py`
- no SQL, migration, config, or dependency file

## 10. Deferred-Batch Decision

| Candidate | Impact | Frequency | Risk reduction | Effort | Score | Initial disposition |
|---|---:|---:|---:|---:|---:|---|
| Atomic active-reminder tracker replacement | 3 | 3 | 4 | 2 | 8 | Good `fix now` candidate after audit and approval |
| Broad JSON writer consolidation | 2 | 2 | 2 | 4 | 2 | Exclude; unrelated expansion |
| Phase 2G Pre-KVK reservation | 3 | 2 | 4 | 5 | 4 | Keep separately evidence/design-gated |

This is a single reliability slice rather than a forced multi-item batch. Restart-safety benefit and
the narrow affected surface justify promotion from the deferred register, but implementation remains
approval-gated.

## 11. Tests And Deterministic Validation

Use `scripts/select_tests.py` and risk-based selection. After approval, prove at minimum:

- exact path and semantic payload passed to the approved writer;
- real temporary-directory round trip with parsed semantic equality to the existing format;
- interrupted/failed replacement preserves the prior valid tracker and cleans temporary files;
- retry behavior and the existing non-raising warning boundary;
- missing file, malformed JSON, non-dict/incomplete entries, and valid legacy entries;
- stored event fallback datetime parsing and live-event preference;
- valid message/view rehydration, missing channel/message, returned raw IDs, and orphan cleanup;
- `safe_delete_reminder()` persists removal from its existing `finally` boundary;
- successful send updates the in-memory reference and then saves; send failure does not replace the
  reference; prior-message deletion failure behavior remains unchanged;
- existing `@everyone` behavior is unchanged at its current timing boundaries;
- no lost update or temporary-file collision under the execution model proved by the audit.

Run focused event scheduler/rehydration/startup/scheduler/helper tests, baseline validators, import
smoke, command-registration validation where selected, pre-commit, operational log-noise review, and
the full suite before promotion. Record exact counts.

## 12. Security And SQL Routing

Bot implementation requires one final Changes-only review over the exact approved base/head with
Deep off because it touches filesystem writes and restart-sensitive Discord identity. Do not run a
Standard/Codebase or Deep scan. Re-run after any runtime remediation so the final reviewed head is
exact.

SQL is a documented no-diff skip only when the SQL repository, migrations, schema snapshots, stored
procedures, DAL queries, and persistence contracts remain unchanged. Any proposed SQL work stops for
separate operator approval and `k98-sql-validation`.

Documentation-only preparation and closure edits are a security-review skip because they do not
change runtime, tests, configuration, dependencies, inputs, permissions, network, filesystem, or SQL
behavior.

## 13. Smoke, Deployment, And Rollback

After review and candidate deployment, perform only natural safe smoke:

- restart with a valid active-reminder tracker;
- verify the existing message is rehydrated with its view and no duplicate is created;
- allow the next natural reminder refresh/send/expiry to advance the tracker;
- confirm the tracker remains valid JSON and no stale temporary file or save/load warning appears.

Do not force a mention, delete a live reminder, corrupt production state, or manufacture failure.
Rollback is a bot-commit revert and redeploy. Because path and semantic JSON shape remain unchanged,
the prior code must be able to read a tracker written by the candidate. No SQL or data rollback is
expected.

## 14. Acceptance Criteria

- [ ] Phase 2E PR merges and final production-main source presence are revalidated before coding.
- [ ] Audit proves the writer/concurrency/compatibility design and the operator approves it.
- [ ] The prior valid tracker survives failed/interrupted replacement.
- [ ] Existing JSON loads without migration or manual edits.
- [ ] Message/view identity, timing, eligibility, mentions, cleanup, startup, and scheduler behavior remain unchanged.
- [ ] Save failure remains non-fatal and operationally visible through the preserved warning boundary.
- [ ] No unrelated JSON, DM tracker, Phase 2G, executor, SQL, config, or dependency work enters the diff.
- [ ] Focused and full validation pass.
- [ ] Final bot Changes-only/Deep-off review covers the exact final base/head with zero unresolved findings.
- [ ] Candidate smoke, rollback evidence, PR links, and operator-owned final verification are recorded.

## 15. Required Delivery Output

Return the audit findings and approval questions first, then stop. After separately approved
implementation, return the exact manifest, writer and compatibility decision, concurrency evidence,
tests and validators, security/SQL routing, preserved contracts, smoke, rollback, PR links, and
operator-owned merge/final verification. Do not claim delivery before it occurs.

## 16. Follow-Up Ownership

- Phase 2G retains evidence/design-gated atomic Pre-KVK reserve/commit/release semantics.
- Stats and KVK History once-only executor audits remain separate tasks.
- Confirmation-update history remains keep-all/deferred pending real production evidence and a new
  operator policy decision.

No deferred item becomes ownerless through this preparation.
