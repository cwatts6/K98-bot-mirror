# Codex Chat Starter - Discord Voting Post Framework Phase 8 Survey Free Text and Add Details

Status: active starter for the next Discord Voting Post Framework slice.

Phase 1 through Phase 7 are complete and smoke tested. SQL-backed live voting works, guided vote
creation works, totals-only and voter-audit exports are private/ephemeral for one closed vote at a
time, hidden-until-close result visibility works, single-question multi-select voting works, and
choice-only multi-question surveys now work under `/vote_admin survey_*`.

Use this starter to begin Phase 8 with audit/scope only.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 8: Survey Free Text and Add Details.

Phase 1 through Phase 7 are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one-choice voting, single-question multi-select voting, SQL-backed
choice-only multi-question surveys, one ballot/response per Discord user, vote/response changes
when enabled, scheduler reminders, automatic close, manual close, disabled controls after close,
restart-safe one-choice buttons, multi-select opener buttons, and survey Answer survey buttons,
guided vote create fields, guided survey builder controls, autocomplete vote/survey lookup for
status/close/export, private admin live totals, PublicLive and HiddenUntilClose result visibility,
public close reveal, private totals-only CSV export, private voter-level vote audit CSV export,
and private survey response-detail CSV export.

Phase 7 smoke test confirmed:
- Survey creation works for single-choice and multi-select questions.
- Response submission works.
- Response updates after submit work.
- PublicLive and HiddenUntilClose survey results work as required.
- Manual close works.
- Automatic close works.
- The guided survey builder flow is good after button/label/limit/timeout polish.
- Unpublished survey drafts intentionally do not survive bot restart, and ordinary builder timeout
  now expires gracefully.

Phase 8 objective:
Audit and design the next approved survey slice: free-text survey questions and optional
choice-question Add details text. Confirm the safest implementation slice and define product
scope, privacy, SQL, permissions, command/builder/view UX, exports, tests, smoke plan, migration
order, rollback posture, and deferred follow-up work.

Start with audit/scope only. Do not implement SQL migrations, runtime survey text/detail storage,
free-text response UI, export shape changes, dashboard/reporting implementation, or command
changes until I approve the architecture, product scope, privacy, SQL, permissions, and UX
direction.

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
- docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 8 Survey Free Text and Add Details.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation for all SQL-facing text/detail/schema/export assumptions
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- k98-promotion-check before production promotion
- codex-security security review before PR handoff if any implementation is later approved because
  survey text/details touch Discord interactions, permissions/privacy, user input, SQL-backed
  persistence, result aggregation, generated export/report surfaces, and restart-sensitive
  persistence

Confirmed Phase 8 audit scope:
- Free-text survey questions.
- Optional choice-question Add details text.
- Whether Add details is per survey, per question, per option, or tied to selected options only.
- Text/detail length limits, validation, editing, and empty/whitespace rules.
- Player interaction UX for entering, reviewing, prefilled editing, and submitting text/details.
- Admin builder UX for adding text questions and enabling details without free-typed question-type
  values.
- PublicLive and HiddenUntilClose behavior for text-bearing surveys.
- Private admin/leadership live status behavior.
- Private response-detail export shape including submitted text/detail data.
- CSV formula-safety and spreadsheet-safe Discord ID behavior.
- SQL storage options for free-text answers and per-choice detail notes.
- Audit metadata without storing full text payloads in audit JSON.
- Restart-safe public survey opener and no persisted partial player drafts unless separately
  approved.
- Deferred status for draft/resume, optional questions, rating questions, emoji/icon, richer
  exports, and dashboard/reporting.

Do not include in Phase 8 unless separately approved:
- Implementing survey free-text/details before architecture approval.
- SQL migrations before approval.
- Persisted partial player response drafts.
- Optional survey questions.
- Rating/ranking questions.
- Per-option emoji/icon support.
- Dashboard/reporting implementation.
- Role-restricted voting.
- Governor-linked voting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.
- Renaming/removing /vote_admin.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing choice-only survey behavior.
- Changing existing totals-only, voter-audit, or survey response-detail export behavior except as
  explicitly approved for text/detail columns.

Audit/scope requirements:
1. Produce a survey text/detail decision matrix.
2. Confirm product value, permission/privacy model, SQL contract needs, command/builder/view UX,
   tests, and smoke plan for each candidate shape.
3. Identify the safest first implementation slice.
4. Split remaining approved work into future task-pack outlines or structured deferred items.
5. Validate authoritative SQL assumptions against C:\K98-bot-SQL-Server before recommending a SQL
   shape.
6. Preserve Phase 1 through Phase 7 behavior.
7. Update deferred optimisation status so no survey draft/resume, optional question, emoji/icon,
   reporting, or export work is lost.

Expected validation for this audit/docs slice:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py

Stop after the audit/scope packet for approval.
```
