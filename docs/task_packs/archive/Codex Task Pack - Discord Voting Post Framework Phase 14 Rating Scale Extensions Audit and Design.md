# Codex Task Pack - Discord Voting Post Framework Phase 14 Rating Scale Extensions Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 14 Rating Scale Extensions Audit and Design`
- Date: `2026-07-07`
- Owner/context: `Follow-up after Phase 13 private dashboard UI delivery and smoke testing`
- Task type: `audit | product scope | SQL-backed survey extension design | Discord interaction UX | reporting/export review`
- One-pass approved: `approved after audit/scope and architecture approval`
- Status: `delivered, review-hardened, operator smoke tested, and archived after Phase 14 closeout`

## 2. Objective

Audit and design rating-scale extensions for the delivered fixed 1-5 survey rating question type.

Phase 9B intentionally delivered a predictable fixed 1-5 rating contract. Phases 10 through 13
then taught exports, reporting contracts, persisted drafts, and the private dashboard how to
represent that fixed scale safely. Phase 14 should decide whether and how to extend rating scales
without breaking existing 1-5 rating responses, public aggregate rendering, private exports,
dashboard summaries, draft/resume behavior, or report bundles.

Operator direction after initial audit confirms real KD98 value in bringing the broader rating
scale work into Phase 14 now: configurable numeric min/max scales, the expanded 1-10 scale, scale
labels, and named rating choices. Per-rating comments are explicitly not required and must not be
included in Phase 14 or carried as default deferred scope.

Phase 14 is now delivered. The historical audit-first instruction below is preserved for traceability:
runtime work was not started until product scope, privacy model, SQL posture, compatibility plan,
tests, smoke plan, deployment order, rollback posture, and deferred boundaries were approved.

## 2A. Delivered Runtime Shape

Phase 14 delivered configurable survey rating scales while preserving all existing fixed 1-5 rating
behavior:

- Configurable numeric min/max scales for survey `Rating` questions, bounded to the approved 1-10
  global range.
- First-class 1-10 rating surveys.
- Scale endpoint labels and named rating choices.
- Backward-compatible default fixed 1-5 rating interpretation for existing questions and
  responses.
- SQL-backed rating scale metadata through migration `20260707_001_add_survey_rating_scales`.
- Player response UX with compact fixed 1-5 behavior preserved and select controls for extended
  scales.
- Persisted draft/resume compatibility, including prefilled extended rating answers.
- PublicLive and HiddenUntilClose aggregate-only public output for extended scales.
- Private status, export, report bundle, and `/vote_admin dashboard` representation of scale
  metadata, counts, averages, distributions, and labels.
- Review hardening for missing SQL migration preflight errors, non-numeric label validation, SQL
  collation/BOM/FK/aggregation concerns, and rating-label export precedence.

Per-rating comments were explicitly excluded and are not carried as default future deferred scope.

Delivered through:

- Mirror PR: `cwatts6/K98-bot-mirror#209`
- Production PR: `cwatts6/k98-bot#516`
- SQL PR: `cwatts6/K98-bot-SQL-Server#37`
- SQL migration: `20260707_001_add_survey_rating_scales`
- Operator smoke and regression testing: `2026-07-07`

Smoke testing confirmed:

- Normal existing fixed 1-5 rating surveys pass.
- 1-10 rating surveys pass.
- Custom min/max scales pass.
- Scale endpoint labels and named rating choices pass.
- Save/draft/resume pass.
- `/vote_admin dashboard`, export, repost, and status pass.
- Other listed regression tests pass.

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
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/Discord Voting Post Framework - Programme Pack.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 9B Rating Survey Questions.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 10 Survey Export v2 and Reporting Readiness Audit and Design.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 11 Private Dashboard Reporting Runtime Audit and Design.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 12 Survey Draft Resume Audit and Design.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 13 Private Dashboard UI Audit and Design.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 14 Rating Scale Extensions Audit and Design.md`

## 4. Delivered Baseline

Phase 1 through Phase 13 are complete and smoke tested. The voting framework supports:

- SQL-backed one-choice votes, single-question multi-select votes, and SQL-backed multi-question
  surveys.
- Choice, text, detail, optional, fixed 1-5 rating, and complete ranking survey questions.
- Persisted survey drafts/resume for surveys only, with unsubmitted draft exclusion from public
  results, private status totals, dashboard summaries, exports, and report bundles.
- PublicLive and HiddenUntilClose result visibility.
- Private admin/leadership live status, private closed-only exports, private survey report bundles,
  dashboard-safe aggregate reporting contracts, and `/vote_admin dashboard`.
- Aggregate-only public rating/ranking results.
- Dashboard-safe private aggregate dashboard UI with filters, pagination, refresh, close, and no
  Discord identity, per-user rows, raw text/detail answers, or draft answers.

Phase 13 smoke testing on 2026-07-07 confirmed `/vote_admin dashboard` works for votes and surveys,
access is limited to admin/leadership, refresh/pagination/filter/close controls work, and no details
or Discord names are visible.

## 5. Source Deferred Item

Phase 14 promotes the active rating-scale extension deferred item.

### Deferred Optimisation
- Area: `voting/`, future survey rating scale extensions, survey response UX, export/report surfaces
- Type: architecture
- Description: Phase 9B intentionally delivered only a fixed 1-5 rating question type. Phase 14 now has operator-confirmed product value for configurable numeric min/max scales, an expanded 1-10 scale, scale labels, and named rating choices. Per-rating comments are explicitly not required and must not be treated as deferred scope unless a later operator decision reverses that status. Phase 10 exports/report bundles, Phase 11 dashboard-safe aggregates, Phase 12 drafts, and Phase 13 private dashboard UI preserve the fixed-scale contract until Phase 14 changes are approved and delivered.
- Suggested Fix: Design and, after explicit architecture approval, deliver configurable numeric rating scales with backward compatibility for existing 1-5 ratings, SQL-backed scale metadata, private-safe export/report/dashboard representation, public aggregate-only rendering, builder/player UX, persisted draft/resume compatibility, validation, migration order, rollback posture, and smoke coverage. Exclude per-rating comments from Phase 14 and from future deferred scope by default.
- Impact: medium
- Risk: medium
- Dependencies: Phase 9B fixed 1-5 rating questions delivered and smoke tested on 2026-07-04; Phase 10 export/report bundle delivered and smoke tested on 2026-07-05; Phase 11 dashboard/reporting contract delivered and smoke/regression tested on 2026-07-06; Phase 12 persisted survey draft/resume delivered and smoke/regression tested on 2026-07-06; Phase 13 private dashboard UI delivered and smoke tested on 2026-07-07; operator approval for configurable rating scales, 1-10, scale labels, and named rating choices; SQL repo validation; export/report/dashboard shape approval; Codex Security review before runtime handoff if implemented.

## 6. Candidate Phase 14 Scope To Confirm

### Confirmed Product Scope For Phase 14

- Add configurable numeric min/max scales for survey `Rating` questions.
- Add an expanded 1-10 rating scale as an approved first-class scale option.
- Add scale labels such as low/high captions for rating questions.
- Add named rating choices so numeric values can have player-facing/admin-facing labels.
- Preserve fixed 1-5 as the default and the backward-compatible interpretation for all existing
  rating questions and responses.
- Exclude per-rating comments. They are not required for Phase 14 and should not be kept as a
  default future deferred item.

### In Scope For Audit/Design

- Confirm whether custom scales apply only to survey `Rating` questions or also affect public
  vote/survey result cards, private status, exports, report bundles, and the private dashboard.
- Confirm backward compatibility for all existing fixed 1-5 rating questions and answers.
- Validate current SQL objects and constraints in `C:\K98-bot-SQL-Server` before proposing a shape.
- Confirm whether new SQL columns/tables/check constraints/views/procedures are needed; prefer
  additive, backward-compatible changes only if product value justifies them.
- Confirm builder UX for scale selection without free-form unsafe values.
- Confirm player response UX, editing/prefill behavior, required/optional semantics, optional
  skip/clear behavior, and persisted draft/resume compatibility.
- Confirm PublicLive and HiddenUntilClose aggregate output for extended scales.
- Confirm private admin/leadership status, export, report bundle, and dashboard representation.
- Confirm formula-safety, spreadsheet-safe IDs, and raw/detail privacy boundaries.
- Define tests, smoke plan, Codex Security requirement, deployment order, rollback posture, and
  deferred follow-up work.

### Recommended Architecture Direction To Approve

- Keep `QuestionType = Rating`; do not create separate question types such as `Rating10`.
- Store scale metadata with the rating question, not with each response.
- Preserve submitted answers as one scalar numeric `RatingValue` per response/question.
- Use an additive SQL shape:
  - `SurveyQuestions` metadata for numeric bounds and low/high scale captions, or a narrow
    companion metadata table if SQL deployment review prefers not to widen `SurveyQuestions`.
  - A dedicated per-value label table for named rating choices, keyed by survey/question/value.
  - A widened `SurveyRatingAnswers` value constraint that supports the approved global bounds.
- Make service validation authoritative for each question's min/max range and labels.
- Use Discord-safe guided builder controls only; do not allow arbitrary unsafe free-form scale
  definitions.
- Use a select menu for larger or named scales if button count/label length makes buttons awkward;
  fixed 1-5 may keep the existing compact button UX.
- Keep PublicLive and HiddenUntilClose aggregate-only. Public output may show count, average,
  min/max, and distribution by value/label, but never per-user ratings.
- Keep private response-detail export as the only profile that includes per-response rating values.
- Keep dashboard summaries aggregate-only and free of Discord identity, raw text/detail, and draft
  data.

### Candidate Implementation Scope If Approved Later

- Add a backward-compatible rating-scale model for survey `Rating` questions.
- Update guided survey builder controls for approved scale choices.
- Update player rating controls, prefill/editing, optional skip/clear, and draft save/resume.
- Update aggregate public rendering, private status, exports, report bundles, and dashboard
  presentation for the approved scale metadata.
- Add rollout-safe SQL and bot behavior for deployment ordering.
- Add focused tests for SQL/DAL/service/view/export/report/dashboard behavior and full validation
  before promotion.

## 7. Out Of Scope Unless Separately Approved

- Per-option emoji/icon support.
- Per-rating comments.
- Broad `/vote_admin` reshaping.
- Cross-survey workbook exports or export schema redesign beyond rating-scale compatibility.
- Retention/redaction policy changes.
- Public dashboard, public raw text/detail display, or public voter-level/detail exports.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing choice/text/detail/optional/ranking survey behavior except as needed for
  approved rating-scale compatibility.
- SQL-native combined vote/survey reporting views/procedures unless performance or reporting
  consumers justify them and the operator separately approves the SQL scope.

## 8. Required Separate Follow-Up Slices

- Emoji/Icon Support.
- `/vote_admin` Reshaping.
- Cross-survey/workbook export redesign.
- Retention/redaction policy changes.
- Optional SQL-native combined reporting views/procedures if reporting consumers or performance
  needs justify them.

Definitely not required unless a later operator decision reverses the status:

- Per-rating comments.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.

## 9. Codex Skills To Use

| Skill | Use |
|---|---|
| `k98-architecture-scope` | Required for product/architecture boundary decisions before coding. |
| `k98-discord-command-feature` | Required if builder/player/dashboard/status/export Discord controls are approved after audit. |
| `k98-sql-validation` | Required if any SQL storage, constraint, reporting view/procedure, DAL, or migration shape is proposed. |
| `k98-test-selection` | Required to select focused service/DAL/view/export/report/dashboard tests. |
| `k98-deferred-optimisation-capture` | Required to keep emoji/icon, command reshaping, export redesign, retention, and optional SQL reporting slices visible. |
| `k98-pr-review` | Required before runtime PR handoff if implementation is approved. |
| `k98-promotion-check` | Required before production promotion if implementation is approved. |
| `codex-security:security-diff-scan` | Required before runtime PR handoff if implementation touches permissions, Discord interactions, SQL/data access, reports/exports, private data, user-controlled text, or restart-sensitive draft flows. |

## 10. SQL And Reporting Questions To Validate

- Current `dbo.SurveyQuestions` question-type and rating metadata shape.
- Current `dbo.SurveyRatingAnswers` check constraints, indexes, uniqueness, and FK behavior.
- Whether fixed 1-5 responses can remain valid with default scale metadata.
- Whether scale metadata belongs on `SurveyQuestions`, a dedicated rating-scale metadata table, or
  another additive structure.
- Whether named rating choices should be stored in a dedicated per-value label table and how to
  enforce one label per rating value.
- Whether `SurveyRatingAnswers.RatingValue` should allow the approved global numeric bounds while
  service validation enforces each question's exact min/max range.
- How exports/report bundles/dashboard aggregates should represent custom scale bounds and labels.
- Whether existing SQL reporting views/procedure require changes, and whether bot-side adapters are
  sufficient.
- Rollback posture after custom-scale questions or responses exist.

## 11. Test Strategy

Expected audit/docs validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

If implementation is approved, likely focused tests include:

- `tests/test_survey_service.py`
- `tests/test_survey_dal.py`
- `tests/test_survey_post_view.py`
- `tests/test_survey_export_service.py`
- `tests/test_voting_reporting_service.py`
- `tests/test_voting_reporting_dal.py`
- `tests/test_vote_admin_dashboard_presentation.py`
- `tests/test_vote_admin_dashboard_view.py`
- `tests/test_validate_command_registration.py` if command or builder surface changes affect
  registration.

Run smoke imports, command registration validation, pre-commit, full pytest, SQL repo validation,
and Codex Security review before runtime handoff if implementation is approved.

## 12. Manual Smoke Plan To Confirm During Audit

Candidate smoke plan if runtime implementation is approved:

1. Create a default fixed 1-5 rating survey and confirm unchanged behavior.
2. Create an expanded 1-10 rating survey.
3. Create a custom min/max rating survey with scale labels and named rating choices.
4. Submit required and optional ratings, including optional skip/clear.
5. Reopen submitted responses and confirm rating prefill/editing.
6. Save/resume an unsubmitted draft and confirm extended ratings are excluded until final submit.
7. Confirm PublicLive and HiddenUntilClose aggregate-only rating output.
8. Confirm private status, report bundle, exports, and dashboard represent scale metadata safely.
9. Confirm no raw details, Discord names, Discord IDs, or per-user rows appear in public or
   dashboard-safe outputs.
10. Confirm existing one-choice, multi-select, choice/text/detail/optional/ranking survey behavior
   remains compatible.

## 13. Stop Point

Stop after the audit/scope packet unless implementation is explicitly approved.
