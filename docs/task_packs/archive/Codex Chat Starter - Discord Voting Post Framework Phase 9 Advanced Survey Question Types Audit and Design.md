# Codex Chat Starter - Discord Voting Post Framework Phase 9 Advanced Survey Question Types Audit and Design

Status: archived starter. Phase 9 audit completed and Phase 9A optional survey questions were
delivered and smoke tested on 2026-07-04.

Phase 1 through Phase 8 are complete and smoke tested. SQL-backed voting, one-choice voting,
single-question multi-select voting, choice/text multi-question surveys, PublicLive and
HiddenUntilClose result visibility, private admin status, private closed-only exports, free-text
answers, choice-question details, aggregate text-question totals rows, and private response-detail
text/detail exports are working.

Use this starter to begin Phase 9 with audit/scope only.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 9: Advanced Survey Question Types Audit and Design.

Phase 1 through Phase 8 are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one-choice voting, single-question multi-select voting, SQL-backed
choice/text multi-question surveys, one ballot/response per Discord user, vote/response changes
when enabled, scheduler reminders, automatic close, manual close, disabled controls after close,
restart-safe one-choice buttons, multi-select opener buttons, survey Answer survey buttons,
guided vote create fields, guided survey builder controls, autocomplete vote/survey lookup for
status/close/export, private admin live totals, PublicLive and HiddenUntilClose result visibility,
public close reveal, private totals-only CSV export, private voter-level vote audit CSV export,
private survey response-detail CSV export, required free-text survey questions, optional
choice-question Add details text, aggregate text-question totals rows, and private/export-only raw
text/detail visibility.

Phase 8 smoke test confirmed:
- Free-text survey questions work.
- Choice-question Add details works as one details capture per question.
- Text/detail modal guidance communicates character limits.
- Submit is gated until required questions are answered.
- Successful submit closes/clears the private response controls.
- PublicLive and HiddenUntilClose do not expose raw text/details.
- Private response-detail exports include formula-safe text/detail data.
- Totals export includes aggregate rows for text questions.
- Existing choice-only survey and vote behavior remains compatible.

Phase 9 objective:
Audit and design the next survey slice: optional survey questions plus rating/ranking question
types. Confirm the safest implementation slice and define product scope, privacy, SQL,
permissions, command/builder/view UX, exports, tests, smoke plan, migration order, rollback
posture, and deferred follow-up work.

Start with audit/scope only. Do not implement SQL migrations, runtime optional/rating/ranking
storage, response UI, export shape changes, dashboard/reporting implementation, or command changes
until I approve the architecture, product scope, privacy, SQL, permissions, and UX direction.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/reference/K98 Bot - Project Engineering Standards.md
- docs/reference/K98 Bot - Coding Execution Guidelines.md
- docs/reference/K98 Bot - Testing Standards.md
- docs/reference/K98 Bot - Skills & Refactor Triggers.md
- docs/reference/K98 Bot - Deferred Optimisation Framework.md
- docs/reference/canonical_command_reference.md
- docs/reference/ENV_REFERENCE.md
- docs/reference/deferred_optimisations.md
- docs/task_packs/Discord Voting Post Framework - Programme Pack.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 8 Survey Free Text and Add Details.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 9 Advanced Survey Question Types Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation for all SQL-facing optional/rating/ranking/schema/export assumptions
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff if implementation is later approved
- k98-promotion-check before production promotion if implementation is later approved
- codex-security security review before PR handoff if implementation is later approved because
  optional/rating/ranking answers touch Discord interactions, permissions/privacy, user input,
  SQL-backed persistence, result aggregation, generated export/report surfaces, and
  restart-sensitive response flows

Confirmed Phase 9 audit scope:
- Optional survey questions.
- Rating survey questions.
- Ranking survey questions.
- Whether optional/rating/ranking should ship together or split into smaller implementation slices.
- Required versus optional completion semantics.
- Submit gating and player help text for mixed required/optional surveys.
- Admin builder UX without free-typed question-type values.
- Player interaction UX for entering, reviewing, prefilled editing, skipping optional answers, and
  submitting advanced answers.
- PublicLive and HiddenUntilClose behavior for optional/rating/ranking aggregates.
- Private admin/leadership live status behavior.
- Private response-detail export shape including missing optional answers, ratings, and rankings.
- CSV formula-safety and spreadsheet-safe Discord ID behavior.
- SQL storage options, constraints, indexes, migration order, and rollback posture.
- Audit metadata without storing full answer payloads in audit JSON.
- Restart-safe public survey opener and no persisted partial player drafts unless separately
  approved.
- Deferred status for draft/resume, emoji/icon, richer exports, dashboard/reporting,
  role/governor voting, saved templates, public detail exports, and /vote_admin reshaping.

Do not include in Phase 9 unless separately approved:
- Implementing optional/rating/ranking behavior before architecture approval.
- SQL migrations before approval.
- Persisted partial player response drafts.
- Per-option emoji/icon support.
- Dashboard/reporting implementation.
- Cross-survey export/workbook redesign.
- Role-restricted voting.
- Governor-linked voting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.
- Renaming/removing /vote_admin.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing choice/text survey behavior except as explicitly approved for advanced
  question-type compatibility.

Audit/scope requirements:
1. Produce an advanced survey question-types decision matrix.
2. Confirm product value, permission/privacy model, SQL contract needs, command/builder/view UX,
   tests, and smoke plan for each candidate shape.
3. Identify the safest first implementation slice.
4. Split remaining approved work into future task-pack outlines or structured deferred items.
5. Validate authoritative SQL assumptions against C:\K98-bot-SQL-Server before recommending a SQL
   shape.
6. Preserve Phase 1 through Phase 8 behavior.
7. Update deferred optimisation status so no survey draft/resume, emoji/icon, reporting, export,
   role/governor, template, or public-detail work is lost.

Expected validation for this audit/docs slice:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py

Stop after the audit/scope packet for approval.
```
