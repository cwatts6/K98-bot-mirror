# Codex Chat Starter - Discord Embed Payload Safety Phase 2H Isolated Pre-KVK Dispatch Diagnostics

## Operator acceptance — 2026-09-08

Phase 2H isolated diagnostic smoke passed on deployed pre-merge commit `7794d2ae`. Phase 2G’s real reservation protocol was exercised successfully through isolated diagnostics. Production-state comparison passed for the observed status/edit operations. Natural production calendar dispatch remains separately pending.

Owner: Chris Watts. Phase 2H is delivered, tested within the bounds below, explicitly accepted,
and archived. Mirror PR #259 and production PR #566 remain OPEN at documentation preparation;
operator merges and final production-main deployment/restart verification remain pending.
This acceptance supersedes earlier implementation/smoke-pending notes retained as history.

### Evidence and limits

| Check | Observed result |
|---|---|
| Deployed candidate | Operator-reported production HEAD `7794d2aee6cc9ea7483a2e0a0f46770e47c925c8`, restarted before smoke |
| Session | `9e986a8ec9034623a60b38b3f4e14b62`, guild `890980578034352138`, owner `559076207627468807`, destination `1380183673147490479` |
| Real protocol | Reserved, sent, isolated CSV slot 1/1, committed attempt `73b6e1dd0b5b4e5eba903b69a095e195`; message `1546875239743496235` |
| Payload | 13 fields, 2,052 characters, largest field 725; one event field, zero compacted/omitted events |
| Before restart | Read-only status at `2026-09-08T13:31:11.347528+00:00`; same-session edit at `13:31:48.427132+00:00` |
| After restart | Status at `2026-09-08T13:33:47.946759+00:00`; same-session edit at `13:34:20.645658+00:00`; same committed attempt retained |
| Guard | Both status/edit receipts reported fresh admission blocked (observation) True. Edits do not independently prove fresh-admission rejection |
| Interaction boundaries | Operator confirmed My Local Time visible only as expected and permission/destination boundaries working; button worked before and after reopening following restart |
| Production-state comparison | Empty Compare-Object result for Path, Exists, SHA256 over the observed status/edit interval; values below |

Message: https://discord.com/channels/890980578034352138/1380183673147490479/1546875239743496235

Diagnostic CSV was under
`logs/prekvk_dispatch_diagnostics/890980578034352138/1380183673147490479/9e986a8ec9034623a60b38b3f4e14b62/alerts.csv`.
Production comparison evidence:

| Production path | Exists before/after | SHA256 before/after |
|---|---|---|
| `logs/stats_alert_log.csv` | True | `D8D715D1CB54B41A7233D23B9869D723B9551E6C0FCB23CA39776ECBE2EB2980` |
| `logs/stats_alert_log.csv.dispatch.json` | False | absent |
| `logs/stats_alert_log.csv.state.json` | True | `44136FA355B3678A1146AD16F7E8649E94FB4FC21FE77E8310C060F61CAAFF8A` |

The comparison does not retrospectively prove unchanged production state during the first fresh
diagnostic send. No production journal was created during the compared operations. Boundary and
visibility checks are operator attestations; individual raw rejection logs were not supplied.
No live duplicate, crash, ambiguous-send retry, state swap or forced calendar change was used.
Natural calendar/scheduler dispatch, cross-process contention and all live failure modes are not
proved by this smoke; no exactly-once claim is made. Phase 2F's next natural public save remains
separately pending with Chris Watts. Keep diagnostic evidence; no cleanup/reset is authorized.

### Final delivery manifest

Runtime: `bot_instance.py`, `commands/prekvk_cmds.py`, `stats_alerts/diagnostic_sessions.py`,
`stats_alerts/diagnostics.py`, `stats_alerts/dispatch_reservations.py`,
`stats_alerts/embeds/prekvk.py`, `stats_alerts/state.py`,
`ui/views/prekvk_dispatch_diagnostic_view.py`.
Tooling: `scripts/validate_command_registration.py`.
Tests: `tests/test_command_registration_smoke.py`,
`tests/test_prekvk_dispatch_diagnostic_lifecycle.py`,
`tests/test_prekvk_dispatch_diagnostic_view.py`, `tests/test_prekvk_dispatch_diagnostics.py`,
`tests/test_prekvk_report_command.py`, `tests/test_validate_command_registration.py`.
Documentation: README-DEV, canonical command reference, deferred register and resolved archive,
events/reminders, diagnostic runbook, task/archive indexes, archived Phase 2G/2H and audit evidence,
and proposed Phase 2I pack/starter. SQL/config/dependency manifest: empty.
Earlier command placement in `commands/admin_cmds.py` was reverted; it has no final runtime delta.

### Final automated evidence

Final runtime: mirror `ba34d7a2360f03d3903de421641ece1e5b19dafa`, production
`7794d2aee6cc9ea7483a2e0a0f46770e47c925c8`; matching Python blobs. Final focused verification
passed 79 tests in each checkout. Full suite: 3,381 passed, 2 skipped; operational log-noise gate
passed. Hooks, architecture/deferred/security-routing validators, imports and registration passed.
Registration: 36 primary / 101 grouped / 25 ops / 3 prekvk. Command `/prekvk dispatch_test` v1.02
uses evaluated Option defaults; real Pycord invocation and serialized option-count/type tests
cover both live smoke failures fixed before this successful delivery.

Final correction Changes-only reviews, Deep off, complete with zero findings:
mirror `e5f0213d-ec9d-45d6-a2e5-2235601eef0c` (`05827d86..ba34d7a2`), production
`bbdbfb57-a2a3-4a51-a8a5-0e54e3ad7754` (`b1d22543..7794d2ae`). These incremental scans supplement
the original implementation and earlier review-fix evidence; they are not whole-PR rescan claims.
SQL manifest empty; no SQL deployment. This closeout changes Markdown only: runtime tests and a
new security scan are skipped for this exact documentation delta, with documentation validators.

### Handoff

Phase 2I Fighting-KVK Diagnostic Parity is selected for an audit/scope-first response, with design
and implementation unapproved. Its active pack and starter are in the parent task_packs directory.
Before next implementation, revalidate both Phase 2H PR merges, final production-main and deployed
head/restart evidence, clean branch/worktree and Phase 1–2H source. Do not infer a running process
revision from Git HEAD alone. Natural production Pre-KVK dispatch remains a separate observation.

## Historical preparation and implementation record


Status: implementation and deterministic/security review complete; Phase 2H promotion and operator smoke pending. Phase 2G PRs #258/#565 are merged and production
deployment of c0a3bc6ba5a618d5b6a2d9e26d7d4d332f5558ab is operator-attested. Use the active pack's
approved implementation record and diagnostics runbook; earlier preparation instructions below are historical.

## Copy/Paste Starter

```markdown
Begin Discord Embed Payload Safety Phase 2H Isolated Pre-KVK Dispatch Diagnostics.

Use:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Discord Embed Payload Safety Phase 2H Isolated Pre-KVK Dispatch Diagnostics.md

Historical evidence:
C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Discord Embed Payload Safety Phase 2G Atomic Pre-KVK Reservation.md
C:\discord_file_downloader\docs\task_packs\archive\Discord Embed Payload Safety Audit Findings.md

Phase 2G is complete by operator acceptance as delivered and tested as far as currently possible.
Full live Pre-KVK validation is explicitly carried forward, not assumed passed. Mirror PR #258 and
production PR #565 awaited operator merges and final verification at preparation. Revalidate both
PRs, final production-main and deployed heads, branch/worktree and Phase 1–2G source before coding.
Restart/KVK guard smoke passed; no fresh reservation/commit receipt was observed in supplied logs.

First response is audit/scope and architecture only. Propose an admin/notify-gated subcommand in an
existing group to exercise the real Pre-KVK reserve/send/commit flow outside the calendar window,
with explicit validated destination, mentions disabled and isolated durable journal, CSV, message
state and locks. Existing test mode bypasses reservation and still mutates shared message state;
custom ReservationStore(log_path) alone does not isolate message projections. Prove every path.

Define session ownership, restart reopening, retention/cleanup, receipt/status reporting, permission
and destination boundaries, cancellation, once-only offloads, uncertainty, rollback and production
default compatibility. Distinguish same-day edit from guard proof; never force a live duplicate.
No global monkeypatch, production calendar/SQL changes or live state swapping. Preserve Phase 1–2G
payloads, permissions, visibility, eligibility, mentions, identity, timing and executor semantics.

Produce safe/fix-now/defer/not-runtime findings, exact runtime/test/docs and separately gated SQL
manifest, selector/risk tests, Changes-only/Deep-off routing and a concrete operator smoke plan.
Keep natural calendar routing separately pending; diagnostics cannot prove exactly-once or all live
failure modes. Keep singleton/public-child lifecycle, generic view timeout, DM/broad JSON redesign,
Stats/KVK History executor audits and ProcConfig error/false-success repair separate.

Stop for approval after the first response. Do not implement the command or tests yet.
```
