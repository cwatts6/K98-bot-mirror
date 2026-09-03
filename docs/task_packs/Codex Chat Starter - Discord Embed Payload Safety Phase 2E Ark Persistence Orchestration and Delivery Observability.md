# Codex Chat Starter - Discord Embed Payload Safety Phase 2E Ark Persistence Orchestration and Delivery Observability

Status: prepared on 2026-09-03 for the next audit-first slice. Implementation is not approved.
Revalidate Phase 2D merges and final production-main verification before selecting an implementation
base.

## Copy/Paste Starter

```markdown
# Files mentioned by the user:

## Codex Task Pack - Discord Embed Payload Safety Phase 2E Ark Persistence Orchestration and Delivery Observability.md:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Discord Embed Payload Safety Phase 2E Ark Persistence Orchestration and Delivery Observability.md

## Discord Embed Payload Safety Audit Findings.md:
C:\discord_file_downloader\docs\task_packs\archive\Discord Embed Payload Safety Audit Findings.md

## My request for Codex:

Begin Discord Embed Payload Safety Phase 2E Ark Persistence Orchestration and Delivery Observability.

Use the task pack:

C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Discord Embed Payload Safety Phase 2E Ark Persistence Orchestration and Delivery Observability.md

Phase 2D operator diagnostics delivery, review remediation, automated validation, final bot
Changes-only/Deep-off security review, candidate deployment, and operator smoke were accepted
through mirror PR #255 and production PR #562. Revalidate both PR merge states, final
production-main verification, branch/head, worktree, and Phase 1-2D presence rather than assuming
the preparation record is current.

Start with audit/scope and architecture planning only. Do not edit runtime code or tests in the
first response.

Required first response:

1. Confirm branch/head, working-tree state, Phase 1-2D prerequisite state, both PR merge states,
   final production-main verification state, intended base, and bot-first scope.
2. Map every `confirmation_updates` producer, JSON load/save, render, refresh, cleanup, restart,
   failure, privacy, and historical-visibility boundary; measure production cardinality safely.
3. Compare keep-all, bounded-with-count, archive, and separately approved SQL retention options,
   including migration, compatibility, concurrency, recovery, and rollback; recommend `fix now` or
   `defer` from evidence.
4. Map team-builder assign/remove/reset/auto-balance/publish/unpublish persistence and audit
   ownership, exact action/detail contracts, permissions/ownership, acknowledgement order,
   webhook refresh/fallback, timeout, and failure behavior.
5. Propose the exact service boundary that removes direct DAL audit orchestration from the view
   without adding duplicate audits or changing interaction sequencing.
6. Map every registration upsert caller and missing destination/channel, fresh send, edit, move,
   forced repost, recreation, edit failure, send failure, state write, and announcement outcome.
7. Propose an explicit outcome vocabulary that distinguishes `edited`, `moved`, `reposted`,
   `recreated`, and `failed` while preserving delivery, return, caller, state, and mention behavior.
8. Produce a findings matrix with `safe`, `fix now`, `defer`, or `not runtime` dispositions and
   name exact runtime, test, documentation, and separately gated SQL files.
9. Explain how commands, permissions, visibility, requester ownership, mentions, ordering,
   match/roster/team meaning, SQL/DAL, JSON compatibility, message/view identity, timeouts,
   restart/rehydration, scheduler, and executor behavior remain unchanged.
10. Give selector-driven/risk-based tests, bot Changes-only/Deep-off security routing, SQL no-diff
    criteria, production smoke, rollback, and explicit approval questions.
11. Stop for approval.

Important boundaries:

- Do not reopen Phase 1, Phase 2A, Phase 2B, Phase 2C, or Phase 2D behavior.
- Do not silently discard persisted confirmation history or choose SQL storage without evidence and
  separate approval.
- Do not change commands, permissions, guild/channel restrictions, public/ephemeral/DM visibility,
  requester ownership, mentions, Ark domain meaning, message/view identity, timeouts, startup,
  restart, rehydration, scheduler, or executor semantics.
- Preserve exact audit actions/details and persistence/audit/acknowledgement order unless the audit
  proves a defect and separate approval is obtained.
- Keep Phase 2F active-reminder atomicity, Phase 2G atomic Pre-KVK reservation, and separate
  Stats/KVK History executor audits out of scope.
- Use a bot Changes-only security review with Deep off after implementation. SQL is a documented
  no-diff skip only if unchanged. Do not run a Standard/Codebase or Deep scan.

Stop for approval after the first response.
```
