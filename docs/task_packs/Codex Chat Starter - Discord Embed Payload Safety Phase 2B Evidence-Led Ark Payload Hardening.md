# Codex Chat Starter - Discord Embed Payload Safety Phase 2B Evidence-Led Ark Payload Hardening

Status: consumed on 2026-09-02. The operator approved the review-first audit proposal and the
Phase 2B implementation and its Changes-only security review are complete on the branch, pending
PR handoff. Scan `79603f53-69f8-4586-9296-760385dd9420` reviewed the exact
`4290b0fc..fccde886` bot range with Deep off and found zero reportable issues; SQL is a documented
no-diff skip. The copy/paste starter below is retained as the initiating record.

## Copy/Paste Starter

```markdown
# Files mentioned by the user:

## Codex Task Pack - Discord Embed Payload Safety Phase 2B Evidence-Led Ark Payload Hardening.md:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Discord Embed Payload Safety Phase 2B Evidence-Led Ark Payload Hardening.md

## Discord Embed Payload Safety Audit Findings.md:
C:\discord_file_downloader\docs\task_packs\archive\Discord Embed Payload Safety Audit Findings.md

## My request for Codex:

Begin Discord Embed Payload Safety Phase 2B Evidence-Led Ark Payload Hardening.

Use the task pack:

C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Discord Embed Payload Safety Phase 2B Evidence-Led Ark Payload Hardening.md

Phase 1 established the canonical `core/discord_embed_limits.py` contract. Phase 2A event/calendar
convergence was delivered and operator accepted through mirror PR #252 and production PR #559,
pending manual merges. Its 2026-09-02 production restart smoke rehydrated the pinned view, armed the
daily refresh and reminder loop, and edited existing message `1488086669876920341` in place for 27
events with `fields=15`, `chars=4789`, `max_field_value=533`, `compacted_events=0`, and
`omitted_events=0`. No duplicate or Discord `50035` occurred. Revalidate current branch/head and
both PR merge states rather than assuming this preparation record is current.

Interpret the prerequisite evidence correctly. Phase 2A's representative smoke accepted its
restart/rehydration and pinned edit path; it did not manually force public or DM reminders,
fallback, or an omission marker. Those unchanged Phase 2A paths retain automated coverage and must
not be reopened in Phase 2B.

Start with audit/scope and architecture planning only. Do not edit runtime code or tests in the
first response.

Required first response:

1. Confirm branch/head, working-tree state, Phase 1/2A prerequisite and PR merge state, and bot-only
   scope.
2. Reconfirm the canonical helper and current Discord hard limits.
3. Map Ark builders and delivery/state flows in `ark/embeds.py`, `ark/registration_messages.py`,
   `ark/registration_flow.py`, `ark/confirmation_flow.py`, `ark/ark_scheduler.py`,
   `ark/reminders.py`, `ark/team_publish.py`, `commands/ark_cmds.py`, relevant Ark/team views,
   Ark state/DAL modules, and `rehydrate_views.py`.
4. Include public sends/edits, ephemeral interactions, DMs, visibility, permissions,
   `AllowedMentions`, first-publication pings, registration/confirmation/team message IDs, trackers,
   sent state, reminder preferences/deduplication, fallback, and restart/rehydration.
5. Trace current Sheet/SQL/config/cache/state/Discord data contracts and measure normal,
   exact-boundary, one-over, and realistic pathological payloads, including a pathological single
   value and maximum credible roster/team cardinality.
6. Measure plain-text team mention chunks separately, including the header and no-Discord-name
   suffix, and compare all local field/page/soft policies with the canonical full contract.
7. Produce a findings matrix with `safe`, `fix now`, `defer`, or `not runtime` dispositions.
8. Propose exact complete-roster/team/update/result packing, compaction, pagination/additional
   embeds/attachments, and count-bearing omission-marker behavior for every approved output,
   including field/aggregate/embed exhaustion and a pathological single unit.
9. Explain how match selection/status/lifecycle, caps, roster/team assignment, permissions,
   visibility, pings, reminder eligibility/preferences/timing, state, deduplication, message identity,
   SQL-backed first-publication, restart/rehydration, and fallback remain unchanged.
10. Name exact runtime, test, and documentation files proposed for modification.
11. Give selector-driven and risk-based tests, bot Changes-only/Deep-off security routing, SQL
    no-diff skip, production smoke, and rollback.
12. List approval questions and stop.

Important boundaries:

- Do not reopen Phase 1 Pre-KVK or Phase 2A event/calendar behavior.
- Do not change commands, permissions, visibility, mentions, match selection/order/status/lifecycle,
  caps, roster/team assignment, reminder eligibility/preferences/timing/deduplication, source data,
  SQL/DAL, cache/state schemas, tracker formats, message IDs, scheduler timing/task names, startup
  order, or rehydration semantics.
- Preserve the SQL-backed first-publication-only ping and current `AllowedMentions` behavior.
- Do not add a competing limit helper or force every path through `send_embed_safe()`.
- Do not silently truncate meaningful rosters, teams, updates, results, or reports.
- Keep Ark orchestration extraction, rankings/history, diagnostics, active-reminder atomicity, and
  atomic Pre-KVK reservation outside Phase 2B.
- Use a bot Changes-only security review with Deep off after implementation. SQL is a documented
  no-diff skip. Do not run a standard or deep codebase scan.

Stop for approval after the first response.
```
