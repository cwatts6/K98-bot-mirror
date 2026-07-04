# Codex Task Pack - Discord Voting Post Framework Phase 9 Advanced Survey Question Types Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 9 Advanced Survey Question Types Audit and Design`
- Date: `2026-07-04`
- Owner/context: `Follow-up after successful Phase 8 survey text/details delivery and smoke test`
- Task type: `audit | product scope | SQL-backed survey extension design | Discord interaction UX | privacy/export review`
- One-pass approved: `no`
- Status: `prepared; audit/scope only until approved`

## 2. Objective

Audit and design the next approved survey slice: optional survey questions plus rating/ranking
question types.

Phase 8 delivered required free-text questions and optional choice-question details. Phase 9 should
decide the safest next implementation shape for advanced survey question types, including
completion semantics, SQL storage, validation, privacy, PublicLive/HiddenUntilClose behavior,
private exports, tests, smoke plan, migration order, rollback posture, and deferred follow-up work.

Do not implement SQL migrations, runtime optional/rating/ranking storage, response UI, export shape
changes, dashboard/reporting implementation, or command changes until the Phase 9 architecture,
product scope, privacy, SQL, permissions, and UX direction are approved.

## 3. Required Reading

Read first:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/ENV_REFERENCE.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/Discord Voting Post Framework - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 9 Advanced Survey Question Types Audit and Design.md`

## 4. Delivered Baseline

Phase 1 through Phase 8 are complete and smoke tested. The voting framework supports SQL-backed
vote posts, one-choice voting, single-question multi-select voting, SQL-backed choice/text
multi-question surveys, one ballot/response per Discord user, response changes when enabled,
scheduler reminders, automatic close, manual close, disabled controls after close, restart-safe
public controls, guided vote/survey creation, PublicLive and HiddenUntilClose result visibility,
private admin live totals, private totals/voter-audit/survey-detail CSV exports, required
free-text survey questions, one optional details capture per choice question, formula-safe
text/detail export cells, aggregate text-question totals rows, and no public raw text/detail
exposure.

## 5. Source Deferred Item

This task promotes the active advanced survey question-types deferred item into an audit/design
slice.

### Deferred Optimisation
- Area: `voting/`, future survey question model, survey builder, survey exports
- Type: architecture
- Description: Optional survey questions and rating/ranking question types remain intentionally outside Phase 8; they require changes to `SurveyQuestions.IsRequired`, missing-answer validation, response completion semantics, public count/card behavior, private export shape, and SQL constraints.
- Suggested Fix: Decide optional-answer semantics, rating/ranking storage, validation limits, export columns for missing/rated/ranked answers, PublicLive/HiddenUntilClose aggregate behavior, builder controls, and smoke tests before any implementation.
- Impact: high
- Risk: high
- Dependencies: Phase 8 text/details delivered and smoke tested; SQL repo validation; privacy/export approval for non-choice answers; regression tests for required choice/text surveys.

## 6. Scope

### In Scope

- Produce an advanced survey question-types decision matrix.
- Decide whether optional questions, rating questions, and ranking questions should ship together
  or as separate implementation slices.
- Define optional-question completion semantics:
  - what counts as survey complete
  - how missing optional answers appear in review/status/export
  - how submit gating changes when required and optional questions are mixed
  - how response changes handle newly answered or cleared optional answers
- Define rating-question semantics:
  - supported scale shapes and limits
  - required versus optional behavior
  - aggregate public summaries
  - private response-detail columns
- Define ranking-question semantics:
  - rank cardinality and duplicate prevention
  - whether ranking uses existing options or a separate item model
  - aggregate public summaries
  - private response-detail columns
- Define admin builder UX without free-typed question-type values.
- Define player response UX for entering, reviewing, editing, and submitting advanced answers.
- Define PublicLive and HiddenUntilClose behavior for optional/rating/ranking questions.
- Define private admin/leadership status and export behavior.
- Validate authoritative SQL assumptions against `C:\K98-bot-SQL-Server`.
- Update deferred optimisation status so draft/resume, emoji/icon, richer exports, reporting,
  templates, role/gov voting, and public detail export work remain visible.

### Out of Scope

- Runtime implementation before architecture approval.
- SQL migrations before approval.
- Persisted partial player response drafts or resume.
- Dashboard/reporting implementation.
- Cross-survey export/workbook redesign.
- Per-option emoji/icon support.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.
- Renaming/removing `/vote_admin`.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing choice/text survey behavior except where explicitly approved for advanced
  question-type compatibility.

## 7. Codex Skills To Use

| Skill | Use |
|---|---|
| `k98-architecture-scope` | Required for product/architecture boundary decisions before coding. |
| `k98-discord-command-feature` | Required because builder/player/status/export UX uses Discord interactions, modals, buttons, and private panels. |
| `k98-sql-validation` | Required for all SQL-facing schema, constraint, index, export, and migration assumptions. |
| `k98-test-selection` | Required to select focused service/DAL/view/export/scheduler/regression tests. |
| `k98-deferred-optimisation-capture` | Required to update active deferred items and keep later survey/reporting/export work visible. |
| `k98-pr-review` | Required before implementation handoff if a runtime slice is approved later. |
| `k98-promotion-check` | Required before production promotion if a runtime slice is approved later. |
| `codex-security:security-diff-scan` | Required before runtime PR handoff because advanced answers touch permissions/privacy, user input, SQL persistence, generated exports, and restart-sensitive response flows. |

## 8. Mandatory Audit Workflow

1. Read the required documents and Phase 8 archived task pack.
2. Audit current survey service, DAL, models, builder/view, presentation/rendering, scheduler,
   export, and command tests.
3. Validate current survey SQL schema and constraints against `C:\K98-bot-SQL-Server`.
4. Produce a decision matrix for these candidate shapes:
   - optional questions only
   - rating questions only
   - ranking questions only
   - optional + rating first
   - optional + rating + ranking together
5. For each candidate, confirm product value, privacy, permissions, SQL contract, command/builder
   UX, player UX, public result behavior, private status/export behavior, tests, smoke plan,
   migration order, rollback posture, and regression risk.
6. Identify the safest first implementation slice.
7. Split remaining approved work into future task-pack outlines or structured deferred items.
8. Stop after the audit/scope packet for approval.

## 9. Architecture Direction To Validate

- Preserve the separate SQL-backed survey model; do not fold surveys back into `VotePosts`.
- Prefer additive question-type metadata and answer tables over overloading choice/text answer
  rows.
- Keep all service validation authoritative; do not rely on Discord UI limits alone.
- Keep public outputs aggregate-only. Never render raw free text or detail notes publicly.
- Keep private response-detail exports admin/leadership-gated and closed-only.
- Keep audit JSON to operational metadata, not full answer payloads.
- Preserve no persisted partial player drafts unless a separate draft/resume slice is approved.

## 10. SQL Questions To Answer

- Should optionality reuse `SurveyQuestions.IsRequired`, and does the current constraint/default
  support optional choice and text questions safely?
- Do rating answers need a dedicated table, a typed scalar-answer table, or an extension of
  `SurveyTextAnswers`?
- Do ranking answers need a dedicated ranked-item table keyed by option and rank?
- What check constraints prevent rating/ranking data on incompatible question types?
- What indexes support closed-only response-detail export without creating dashboard/reporting
  scope?
- How are original answers represented for response changes?
- What migration order preserves Phase 7 and Phase 8 behavior during rollout?
- What rollback posture is acceptable if advanced answer tables contain user-submitted data?

## 11. UX Questions To Answer

- How does the builder select `Choice`, `Text`, `Rating`, or `Ranking` without free-typed values?
- How does the builder mark a question optional while keeping defaults required?
- How does the player panel communicate "answered", "optional and skipped", and "required missing"?
- Should submit stay disabled until all required questions are complete while optional questions
  remain skippable?
- How are rating scales displayed in Discord components without exceeding option limits?
- How are rankings entered and reviewed without a confusing multi-step flow?
- How are advanced answers prefilled when a player reopens a submitted response?

## 12. Export And Privacy Requirements

- Totals exports should remain aggregate and must not expose raw text/detail data.
- Response-detail exports must represent missing optional answers distinctly from blank strings.
- Rating/ranking export cells must be formula-safe where user-controlled labels can appear.
- Discord user IDs must remain spreadsheet-safe text.
- Export audit should include requester, export mode, row count, byte count, column profile,
  oversized flag, delivery status, and no full answer payloads.
- Public voter-level/detail posting remains out of scope.

## 13. Test Strategy To Define

Select tests after audit, but expect focused coverage around:

- `tests/test_survey_service.py`: optional completion rules, rating/ranking validation, stale
  payloads, response changes, closed rejection, and required-answer enforcement.
- `tests/test_survey_dal.py`: transactional advanced answer persistence, replacement semantics,
  original-answer metadata, and export row mapping.
- `tests/test_survey_post_view.py`: builder controls, player entry/edit/prefill, submit gating,
  timeout/stale behavior, and owner-only panels.
- `tests/test_survey_export_service.py`: aggregate rows, response-detail advanced columns,
  formula safety, closed-only enforcement, and oversized audit metadata.
- Survey presentation/render tests for PublicLive and HiddenUntilClose aggregate behavior.
- `tests/test_vote_admin_cmds.py` and command registration validation if command wiring changes.

Baseline audit/docs validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

## 14. Manual Smoke Plan To Define

The audit packet should define a smoke plan that covers:

1. Existing choice-only and text/detail survey regression.
2. Optional unanswered question submit behavior.
3. Rating submit/update/export behavior.
4. Ranking submit/update/export behavior.
5. PublicLive aggregate behavior.
6. HiddenUntilClose open/close behavior.
7. Private admin status behavior.
8. Private closed-only exports with spreadsheet-safe IDs and formula safety.
9. Manual close, automatic close, reminders, and restart-safe survey opener behavior.

## 15. Future Task-Pack / Deferred Outlines

Keep these as separate unless the audit explicitly promotes one:

- Survey Draft/Resume: SQL-backed partial drafts, resume after timeout/restart, cleanup/expiry,
  privacy approval, and export exclusion for unsubmitted drafts.
- Survey Export v2 / Reporting Readiness: cross-survey exports, workbook outputs, private
  reporting views/procedures, retention/redaction policy, and dashboard/reporting decisions.
- Emoji/Icon Support: option metadata, Discord button/select rendering, export representation, and
  generated-card glyph QA.
- Voting Identity/Policy Work: role-restricted voting, governor-linked voting/reporting, saved
  templates, public detail exports, and `/vote_admin` command reshaping.
