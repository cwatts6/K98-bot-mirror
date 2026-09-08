# Codex Chat Starter - Discord Embed Payload Safety Phase 2H Isolated Pre-KVK Dispatch Diagnostics

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
