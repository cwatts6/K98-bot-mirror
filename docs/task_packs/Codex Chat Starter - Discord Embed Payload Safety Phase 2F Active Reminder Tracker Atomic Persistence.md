# Codex Chat Starter - Discord Embed Payload Safety Phase 2F Active Reminder Tracker Atomic Persistence

Status: prepared on 2026-09-07 for the next audit-first slice. Implementation is not approved.

## Copy/Paste Starter

```markdown
# Files mentioned by the user:

## Codex Task Pack - Discord Embed Payload Safety Phase 2F Active Reminder Tracker Atomic Persistence.md:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Discord Embed Payload Safety Phase 2F Active Reminder Tracker Atomic Persistence.md

## Discord Embed Payload Safety Audit Findings.md:
C:\discord_file_downloader\docs\task_packs\archive\Discord Embed Payload Safety Audit Findings.md

## My request for Codex:

Begin Discord Embed Payload Safety Phase 2F Active Reminder Tracker Atomic Persistence.

Use the task pack:

C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Discord Embed Payload Safety Phase 2F Active Reminder Tracker Atomic Persistence.md

Phase 2E candidate delivery and operator smoke completed successfully through mirror PR #256 and
production PR #563. Revalidate both PR merge states, final production-main verification,
branch/head, worktree, and Phase 1-2E presence rather than assuming this preparation record is
current.

Start with audit/scope and architecture planning only. Do not edit runtime code or tests in the
first response.

Required first response:

1. Confirm branch/head, worktree, Phase 1-2E prerequisite state, both PR merge states, final
   production-main verification state, intended base, and bot-only scope.
2. Map every `active_reminders` producer, in-memory mutation, JSON save/load, restart, rehydration,
   cleanup, scheduler, exception, and message/view identity boundary.
3. Prove the actual writer concurrency model across coroutines, threads, processes, shutdown, and
   restart, including what the singleton lock does and does not guarantee.
4. Compare the current direct write, existing atomic helpers, and any narrowly scoped writer option,
   including formatting/key-order/Unicode compatibility, temp collision, fsync/replace/retry,
   recovery, cleanup, and rollback.
5. Produce a findings matrix with `safe`, `fix now`, `defer`, or `not runtime` dispositions and name
   exact runtime, test, documentation, and separately gated SQL files.
6. Explain how tracker path/shape, IDs, fallback metadata, malformed-entry behavior, raw-ID cleanup,
   Discord ordering, in-memory state, mentions, timing, expiry, view identity, startup, scheduler,
   logging, and non-raising failure behavior remain unchanged.
7. Give selector-driven/risk-based tests, bot Changes-only/Deep-off security routing, SQL no-diff
   criteria, natural production smoke, rollback, and explicit approval questions.
8. Stop for approval.

Important boundaries:

- Do not reopen Phase 1-2E behavior.
- Do not change commands, permissions, visibility, requester ownership, reminder eligibility,
  mentions, event meaning, message/view identity, timing, startup, rehydration, scheduler, or
  executor semantics.
- Preserve the exact tracker path and semantic JSON compatibility; do not silently change formatting
  assumptions without evidence.
- Keep DM tracker redesign, broad JSON consolidation, Phase 2G atomic Pre-KVK reservation, and
  separate Stats/KVK History executor audits out of scope.
- Use a bot Changes-only security review with Deep off after implementation. SQL is a documented
  no-diff skip only if unchanged. Do not run a Standard/Codebase or Deep scan.

Stop for approval after the first response.
```
