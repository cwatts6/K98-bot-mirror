# Codex Chat Starter - Discord Voting Post Framework Phase 9C Ranking Survey Questions

Status: complete starter archived after Phase 9C delivery and smoke test.

Phase 1 through Phase 9B are complete and smoke tested. SQL-backed voting, one-choice voting,
single-question multi-select voting, choice/text/rating multi-question surveys, PublicLive and
HiddenUntilClose result visibility, private admin status, private closed-only exports, free-text
answers, choice-question details, aggregate text-question totals rows, optional survey questions,
fixed 1-5 rating questions, aggregate-only rating averages/distributions, and private
response-detail text/detail/optional/rating export semantics are working.

This starter launched Phase 9C with audit/scope confirmation before implementation. Phase 9C was
delivered and smoke tested on 2026-07-04; keep this file as the execution record only.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 9C: Ranking Survey Questions.

Phase 1 through Phase 9B are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one-choice voting, single-question multi-select voting, SQL-backed
choice/text/rating multi-question surveys, one ballot/response per Discord user, vote/response
changes when enabled, scheduler reminders, automatic close, manual close, disabled controls after
close, restart-safe one-choice buttons, multi-select opener buttons, survey Answer survey buttons,
guided vote create fields, guided survey builder controls, autocomplete vote/survey lookup for
status/close/export, private admin live totals, PublicLive and HiddenUntilClose result visibility,
public close reveal, private totals-only CSV export, private voter-level vote audit CSV export,
private survey response-detail CSV export, required free-text survey questions, optional
choice-question Add details text, aggregate text-question totals rows, private/export-only raw
text/detail visibility, optional survey questions for existing choice/text survey types, and fixed
1-5 rating survey questions with aggregate-only public results and private export/status
representation.

Phase 9B smoke test confirmed:
- Rating-question creation works.
- Option/details controls are disabled or rejected for rating questions.
- Required and optional rating questions both submit correctly.
- Optional rating skip/clear behavior works.
- Public cards display average rating and distribution from submitted rating answers only.
- Existing choice-only survey, text/detail survey, optional survey, multi-select vote, and
  one-choice vote behavior remains compatible.

Phase 9C objective:
Audit and design the next survey slice: ranking survey questions. Confirm product scope, privacy,
SQL, permissions, command/builder/view UX, exports, tests, smoke plan, migration order, rollback
posture, and deferred follow-up work. If the architecture is approved, implement the ranking slice
only.

Start with audit/scope confirmation. Do not implement SQL migrations, ranking runtime storage,
response UI, export shape changes, dashboard/reporting implementation, or command changes until I
approve the architecture, product scope, privacy, SQL, permissions, and UX direction.

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
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 9 Advanced Survey Question Types Audit and Design.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 9B Rating Survey Questions.md
- docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 9C Ranking Survey Questions.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation for all SQL-facing ranking/schema/export assumptions
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff if implementation is approved
- k98-promotion-check before production promotion if implementation is approved
- codex-security security review before PR handoff because ranking answers touch Discord
  interactions, permissions/privacy, user input, SQL-backed persistence, result aggregation,
  generated export/report surfaces, and restart-sensitive response flows

Candidate Phase 9C scope to confirm:
- Complete ranking survey questions over existing 2-6 survey options.
- Required versus optional ranking completion semantics using the delivered Phase 9A model.
- Optional ranking skip/clear behavior, with partial rankings deferred unless explicitly approved.
- Admin builder UX without free-typed question-type values.
- Player interaction UX for entering, reviewing, prefilled editing, skipping optional rankings,
  duplicate-rank prevention, and submitting ranking answers.
- PublicLive and HiddenUntilClose aggregate-only behavior for ranking summaries.
- Private admin/leadership live status behavior.
- Private response-detail export shape including skipped optional rankings and ranked option rows.
- CSV formula-safety and spreadsheet-safe Discord ID behavior.
- SQL storage options, constraints, indexes, migration order, migration guards, and rollback
  posture.
- Audit metadata without storing full answer payloads in audit JSON.
- Restart-safe public survey opener and no persisted partial player drafts unless separately
  approved.
- Deferred status for draft/resume, rating scale extensions, emoji/icon, richer exports,
  dashboard/reporting, role/governor voting, saved templates, public detail exports, and
  /vote_admin reshaping.

Do not include in Phase 9C unless separately approved:
- Partial top-N rankings.
- Ties, weighted scoring variants, pairwise voting, Condorcet/IRV/STV logic, or winner election
  algorithms beyond conservative aggregate summaries.
- Ranking comments.
- Custom rating scales, 1-10 scales, scale labels, emoji/icons, or rating comments.
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
- Changing existing choice/text/rating/optional survey behavior except as explicitly approved for
  ranking compatibility.

Audit/scope requirements:
1. Confirm complete-ranking product value and scope.
2. Confirm permission/privacy model, SQL contract, command/builder UX, player UX, tests, and smoke
   plan.
3. Validate authoritative SQL assumptions against C:\K98-bot-SQL-Server before recommending a SQL
   shape.
4. Preserve Phase 1 through Phase 9B behavior.
5. Update deferred optimisation status so no draft/resume, rating-scale, emoji/icon, reporting,
   export, role/governor, template, or public-detail work is lost.
6. If implementation is approved, keep the PR scoped to ranking questions only.

Expected validation for the audit/docs portion:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py

Stop after the audit/scope packet unless I explicitly approve implementation.
```
