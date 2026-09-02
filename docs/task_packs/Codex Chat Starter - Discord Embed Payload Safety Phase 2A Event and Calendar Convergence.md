# Codex Chat Starter - Discord Embed Payload Safety Phase 2A Event and Calendar Convergence

Use this starter for the next phase. The first response is audit/scope and architecture planning
only. Do not change runtime code or tests until the operator approves that response.

## Copy/Paste Starter

```markdown
# Files mentioned by the user:

## Codex Task Pack - Discord Embed Payload Safety Phase 2A Event and Calendar Convergence.md:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Discord Embed Payload Safety Phase 2A Event and Calendar Convergence.md

## Discord Embed Payload Safety Audit Findings.md:
C:\discord_file_downloader\docs\task_packs\archive\Discord Embed Payload Safety Audit Findings.md

## My request for Codex:

Begin Discord Embed Payload Safety Phase 2A Event and Calendar Convergence.

Use the task pack:

C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Discord Embed Payload Safety Phase 2A Event and Calendar Convergence.md

Phase 1 was delivered through mirror PR #251 and production PR #558. Its canonical
`core/discord_embed_limits.py`, exact Pre-KVK regression, complete-event packing, shared-sender
repair, and sole module-owned `prekvk_daily` claim are the prerequisite. Revalidate the current
branch/head and PR merge state rather than assuming this preparation record is still current.

The 2026-09-02 operator smoke successfully validated and edited the existing Pre-KVK message:

- KVK 16 resolved to `DRAFT`.
- Payload metrics were `fields=13`, `chars=1847`, `max_field_value=530`, `event_fields=1`,
  `compacted_events=0`, `omitted_events=0`.
- Existing message `1544617668999381044` in channel `1209532242506813540` was edited.
- The persisted `prekvk_msg_id` matched that message.
- The observed `prekvk_daily` count was `1`.
- No duplicate post or Discord `50035` rejection occurred.

Interpret this evidence correctly: `/ops test_embed` bypasses daily guards and chose the edit path
because the same-day `prekvk_msg_id` was valid. The guard controls a fresh normal production send
when no editable message exists. The test did not independently exercise the scheduled first-send
ping/post-success claim, although those paths have automated coverage.

Start with audit/scope and architecture planning only. Do not edit runtime code or tests in the
first response.

Required first response:

1. Confirm branch/head, working-tree state, Phase 1 merge state, and bot-only scope.
2. Reconfirm the canonical helper and current Discord hard limits.
3. Map builders and delivery/state flows in `event_embed_manager.py`, `event_scheduler.py`,
   `event_calendar/reminders.py`, `daily_KVK_overview_embed.py`, and `ui/views/calendar.py`.
4. Include public sends, edits, DMs, text fallback, persistent/local-time views, message IDs,
   trackers, sent state, reminder deduplication, rehydration, visibility, and mentions.
5. Measure normal, exact-boundary, one-over, and realistic pathological payloads from current
   Sheet/cache data contracts.
6. Compare local field/page/soft-aggregate policies with the canonical full contract.
7. Produce a findings matrix with `safe`, `fix now`, `defer`, or `not runtime` dispositions.
8. Propose exact complete-event packing, compaction, pagination, and omission-marker behavior per
   approved output, including field/aggregate exhaustion and a pathological single event.
9. Explain how event selection, reminder eligibility, pings, visibility, state, deduplication,
   message identity, restart/rehydration, and fallback behavior remain unchanged.
10. Name exact runtime, test, and documentation files proposed for modification.
11. Give selector-driven and risk-based tests, Changes-only/Deep-off security routing, SQL skip,
    production smoke, and rollback.
12. List approval questions and stop.

Important boundaries:

- Do not reopen Phase 1 Pre-KVK behavior in this slice.
- Do not change commands, permissions, visibility, mentions, event selection/order/caps, reminder
  eligibility, source data, SQL, cache/state schemas, tracker formats, scheduler timing/task names,
  startup order, or rehydration semantics.
- Do not add a competing limit helper or force every path through `send_embed_safe()`.
- Do not silently truncate meaningful event lists.
- Keep Ark, rankings/history, diagnostics, public calendar UX redesign, and atomic Pre-KVK
  reservation outside Phase 2A.
- Use a bot Changes-only security review with Deep off after implementation. SQL is a documented
  no-diff skip. Do not run a standard or deep codebase scan.

Stop for approval after the first response.
```
