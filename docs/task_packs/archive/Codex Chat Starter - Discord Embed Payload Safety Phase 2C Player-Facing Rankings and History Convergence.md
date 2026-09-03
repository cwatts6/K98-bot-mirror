# Codex Chat Starter - Discord Embed Payload Safety Phase 2C Player-Facing Rankings and History Convergence

Status: completed and archived on 2026-09-03. The operator approved an evidence-led
tests/documentation-only implementation after the audit proved every live rankings/history payload
safe under current source and cardinality contracts. Review, candidate deployment, and smoke
testing passed through mirror PR #254 and production PR #561; manual merges and final
production-main verification remain operator-owned.

## Copy/Paste Starter

```markdown
# Files mentioned by the user:

## Codex Task Pack - Discord Embed Payload Safety Phase 2C Player-Facing Rankings and History Convergence.md:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Discord Embed Payload Safety Phase 2C Player-Facing Rankings and History Convergence.md

## Discord Embed Payload Safety Audit Findings.md:
C:\discord_file_downloader\docs\task_packs\archive\Discord Embed Payload Safety Audit Findings.md

## My request for Codex:

Begin Discord Embed Payload Safety Phase 2C Player-Facing Rankings and History Convergence.

Use the task pack:

C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Discord Embed Payload Safety Phase 2C Player-Facing Rankings and History Convergence.md

Phase 1 established the canonical `core/discord_embed_limits.py` contract. Phase 2A
event/calendar convergence and Phase 2B Ark hardening were delivered. Phase 2B candidate smoke on
2026-09-02 built a registration payload with `fields=4`, `chars=346`, `compacted_units=0`, and
`omitted_units=0`, reused the existing message reference with `should_announce=False`, and changed
neither state nor identity. No duplicate or Discord `50035` occurred. Revalidate branch/head,
working-tree state, Phase 1-2B presence, and mirror PR #253 / production PR #560 merge states rather
than assuming this preparation record is current.

Start with audit/scope and architecture planning only. Do not edit runtime code or tests in the
first response.

Required first response:

1. Confirm branch/head, working-tree state, prerequisite/PR state, intended base, and bot-only scope.
2. Reconfirm the canonical helper and current Discord hard limits.
3. Map current rankings/history builders, services, views, commands, fallback, exports, and final
   public/ephemeral send/edit boundaries; prove legacy/test-only/dead paths.
4. Include permissions, channel restrictions, requester ownership, visibility, mentions,
   attachments, message/view identity, timeouts, fallback, and restart implications.
5. Trace SQL/config/cache/model/Discord contracts and measure normal, exact-boundary, one-over,
   realistic pathological, maximum-cardinality, grouped multi-embed, and pathological-single-unit
   payloads.
6. Compare every local row/page/preview/Top/overlay/soft-upload policy with the canonical full
   message contract.
7. Produce a findings matrix with `safe`, `fix now`, `defer`, or `not runtime` dispositions.
8. Propose exact complete-row/history-unit packing, pagination/additional embeds, existing
   attachments/exports, visible compaction, and count-bearing omission-marker behavior under every
   exhaustion mode.
9. Explain how commands, selection/order/status, finalized-KVK logic, limits, permissions,
   visibility, channel/owner enforcement, mentions, files, fallback, data/SQL/DAL/cache, identity,
   timeouts, restart, and existing executor behavior remain unchanged.
10. Name exact runtime, test, and documentation files proposed for modification.
11. Give selector-driven/risk-based tests, bot Changes-only/Deep-off security routing, SQL no-diff
    skip, production smoke, rollback, and approval questions.
12. Stop for approval.

Important boundaries:

- Do not reopen Phase 1, Phase 2A, or Phase 2B behavior.
- Do not change commands, permissions, visibility, selection/order/status, Top limits,
  finalized-KVK logic, account selection, channel restrictions, requester ownership, chart/table
  meaning, file schemas, SQL/DAL, config/cache/state, message/view identity, timeouts, startup,
  restart, or fallback semantics.
- Do not silently truncate meaningful ranking/history rows.
- Do not add mentions or broaden `AllowedMentions`.
- Keep diagnostics, Ark persistence/orchestration, active-reminder atomicity, and atomic Pre-KVK
  reservation in Phases 2D-2G.
- Coordinate with, but do not implement, the separate KVK History `_offload_callable` once-only
  executor audit.
- Use a bot Changes-only security review with Deep off after implementation. SQL is a documented
  no-diff skip. Do not run a Standard/Codebase or Deep scan.

Stop for approval after the first response.
```
