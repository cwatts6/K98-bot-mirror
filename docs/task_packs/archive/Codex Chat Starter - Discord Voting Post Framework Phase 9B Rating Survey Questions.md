# Codex Chat Starter - Discord Voting Post Framework Phase 9B Rating Survey Questions

Status: archived starter. Phase 9B fixed 1-5 rating survey questions were delivered and operator
smoke tested on 2026-07-04.

Phase 1 through Phase 9A are complete and smoke tested. SQL-backed voting, one-choice voting,
single-question multi-select voting, choice/text multi-question surveys, PublicLive and
HiddenUntilClose result visibility, private admin status, private closed-only exports, free-text
answers, choice-question details, aggregate text-question totals rows, optional survey questions,
and private response-detail text/detail/optional export semantics are working.

Historical starter preserved for traceability. Use the active Phase 9C ranking starter in
`docs/task_packs/` for the next survey slice.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 9B: Rating Survey Questions.

Phase 1 through Phase 9A are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one-choice voting, single-question multi-select voting, SQL-backed
choice/text multi-question surveys, one ballot/response per Discord user, vote/response changes
when enabled, scheduler reminders, automatic close, manual close, disabled controls after close,
restart-safe one-choice buttons, multi-select opener buttons, survey Answer survey buttons,
guided vote create fields, guided survey builder controls, autocomplete vote/survey lookup for
status/close/export, private admin live totals, PublicLive and HiddenUntilClose result visibility,
public close reveal, private totals-only CSV export, private voter-level vote audit CSV export,
private survey response-detail CSV export, required free-text survey questions, optional
choice-question Add details text, aggregate text-question totals rows, private/export-only raw
text/detail visibility, and optional survey questions for existing choice/text survey types.

Phase 9A smoke test confirmed:
- Optional survey questions work for existing survey question types.
- Submit is gated only by required questions.
- Optional unanswered questions can be skipped.
- Successful submit closes/clears the private response controls.
- PublicLive and HiddenUntilClose do not expose raw text/details.
- Public cards can show mixed required/optional question counts.
- Private status/export behavior represents skipped optional answers distinctly.
- Existing choice-only survey, text/detail survey, multi-select vote, and one-choice vote behavior
  remains compatible.

Phase 9B objective:
Audit and design the next survey slice: fixed 1-5 rating survey questions. Confirm product scope,
privacy, SQL, permissions, command/builder/view UX, exports, tests, smoke plan, migration order,
rollback posture, and deferred follow-up work. If the architecture is approved, implement the
rating slice only.

Start with audit/scope confirmation. Do not implement SQL migrations, rating runtime storage,
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

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation for all SQL-facing rating/schema/export assumptions
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff if implementation is approved
- k98-promotion-check before production promotion if implementation is approved
- codex-security security review before PR handoff because rating answers touch Discord
  interactions, permissions/privacy, user input, SQL-backed persistence, result aggregation,
  generated export/report surfaces, and restart-sensitive response flows

Confirmed Phase 9B scope:
- Fixed 1-5 rating survey questions.
- Required versus optional rating completion semantics using the delivered Phase 9A model.
- Submit gating and player help text for mixed required/optional surveys.
- Admin builder UX without free-typed question-type values.
- Player interaction UX for entering, reviewing, prefilled editing, skipping optional ratings, and
  submitting rating answers.
- PublicLive and HiddenUntilClose behavior for rating aggregates.
- Private admin/leadership live status behavior.
- Private response-detail export shape including skipped optional ratings and rating values.
- CSV formula-safety and spreadsheet-safe Discord ID behavior.
- SQL storage options, constraints, indexes, migration order, and rollback posture.
- Audit metadata without storing full answer payloads in audit JSON.
- Restart-safe public survey opener and no persisted partial player drafts unless separately
  approved.
- Deferred status for ranking, draft/resume, emoji/icon, richer exports, dashboard/reporting,
  role/governor voting, saved templates, public detail exports, and /vote_admin reshaping.

Do not include in Phase 9B unless separately approved:
- Ranking survey questions.
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
- Changing existing choice/text/optional survey behavior except as explicitly approved for rating
  compatibility.

Audit/scope requirements:
1. Confirm fixed 1-5 rating product value and scope.
2. Confirm permission/privacy model, SQL contract, command/builder UX, player UX, tests, and smoke
   plan.
3. Validate authoritative SQL assumptions against C:\K98-bot-SQL-Server before recommending a SQL
   shape.
4. Preserve Phase 1 through Phase 9A behavior.
5. Update deferred optimisation status so no ranking, draft/resume, emoji/icon, reporting, export,
   role/governor, template, or public-detail work is lost.
6. If implementation is approved, keep the PR scoped to rating questions only.

Expected validation for the audit/docs portion:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py

Stop after the audit/scope packet unless I explicitly approve implementation.
```
