# Codex Task Pack - Discord Voting Post Framework Phase 8 Survey Free Text and Add Details

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 8 Survey Free Text and Add Details`
- Date: `2026-07-03`
- Owner/context: `Follow-up after successful Phase 7 choice-only survey delivery and smoke test`
- Task type: `audit | product scope | SQL-backed survey extension design | Discord interaction UX | privacy/export review`
- One-pass approved: `no`
- Status: `prepared; start with audit/scope only`

## 2. Objective

Audit and design the second survey slice: free-text survey questions and optional
choice-question `Add details` text.

Phase 7 delivered choice-only multi-question surveys. Phase 8 should extend that model carefully
for text-bearing responses, including privacy, SQL shape, UI, exports, and moderation/retention
considerations. Do not implement runtime changes until the architecture, product scope, privacy,
SQL, permissions, and UX direction are approved.

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
- `docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 8 Survey Free Text and Add Details.md`

Conditionally read:

- `docs/reference/Promotion Guide.md` before production promotion.
- SQL repo `C:\K98-bot-SQL-Server` before recommending any answer table, column, index,
  migration, view, stored procedure, constraint, or audit shape.

## 4. Delivered Baseline

Phase 1 through Phase 7 are complete and smoke tested.

The voting framework now supports:

- SQL-backed one-choice votes.
- SQL-backed single-question multi-select votes.
- SQL-backed choice-only multi-question surveys under `/vote_admin survey_*`.
- Guided admin survey builder with question/option modals, min/max dropdowns, visible limits, and
  graceful timeout for unpublished drafts.
- Persistent public `Answer survey` buttons.
- Private paged survey response panels.
- Submitted-answer prefill and response-change allowed/blocked behavior.
- PublicLive and HiddenUntilClose survey aggregate visibility.
- Manual and automatic survey close.
- Private admin/leadership live survey status.
- Private closed-only survey totals and response-detail CSV exports.
- Restart-safe public survey opener behavior.

Phase 7 smoke testing confirmed:

- Survey creation works for single-choice and multi-select questions.
- Response submission and response update work.
- PublicLive and HiddenUntilClose survey results work as required.
- Manual and automatic close work.
- Builder UX polish is acceptable after button/label/limit/timeout refinements.
- Unpublished survey drafts intentionally do not survive bot restart.

## 5. Source Deferred Items

This task promotes the active survey text/details deferred item into the next prepared voting
slice.

### Deferred Optimisation
- Area: `voting/`, future survey question model, survey exports
- Type: architecture
- Description: Free-text and other non-choice survey question types were intentionally excluded from the first choice-only survey slice. Operator follow-up confirmed the second survey slice should add free-text questions and optional choice-question `Add details` text, and that submitted text/detail data must be included in private admin/leadership exports. Text responses increase privacy, moderation, CSV formula-safety, retention, and export risks beyond choice-only aggregate voting.
- Suggested Fix: Define free-text questions, per-choice `Add details` text, SQL storage shape, retention/redaction rules, private export columns containing submitted text/detail data, formula-safety handling, private admin/leadership detail access matching current vote results visibility, and public aggregate behavior before any SQL or runtime implementation.
- Impact: high
- Risk: high
- Dependencies: Phase 7 choice-only survey model delivered and smoke tested; Codex Security review before runtime PR handoff; SQL schema design for type-specific answers and per-choice detail notes; export regression tests.

## 6. Scope

### In Scope

- Confirm the exact product value for:
  - full free-text questions
  - optional `Add details` text attached to a selected choice
- Decide whether Phase 8 should include both text features in one implementation slice or split
  them into smaller sub-slices.
- Define text answer limits, validation copy, empty/whitespace handling, editing rules, and
  response-change behavior.
- Define whether `Add details` is globally enabled per survey, per question, or per option.
- Define the player UX for entering text in Discord without making the flow frustrating.
- Define admin builder UX changes for adding a free-text question or enabling details on a choice
  question.
- Define PublicLive and HiddenUntilClose behavior for text-bearing surveys.
- Define private admin/leadership live status behavior for text-bearing surveys.
- Define summary and response-detail export changes, including formula-safety and text inclusion.
- Define audit metadata for text/detail response submission, change, export, and oversized export
  handling without storing full text payloads in audit JSON.
- Validate SQL options against `C:\K98-bot-SQL-Server`.
- Preserve Phase 1 through Phase 7 behavior.
- Update deferred optimisation status so draft/resume, optional questions, rating questions,
  emoji/icon, dashboard/reporting, and richer exports remain tracked.

### Out of Scope

- Implementing survey free-text or `Add details` runtime behavior before approval.
- SQL migrations before approval.
- Persisted partial player response drafts.
- Admin draft persistence across bot restart.
- Optional survey questions.
- Rating/ranking questions.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.
- Dashboard/reporting implementation.
- Cross-survey exports or workbook-style export redesign.
- Per-option emoji/icon support.
- Renaming/removing `/vote_admin`.
- Changing existing one-choice, single-question multi-select, or choice-only survey behavior.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required for survey extension boundaries, command/view placement, persistence, privacy, and tests. |
| `k98-discord-command-feature` | use | Text/details affect slash command builder UX, modals, private response panels, and stale/timeout behavior. |
| `k98-sql-validation` | use | Required before recommending answer columns/tables, constraints, indexes, migrations, or reporting views. |
| `k98-test-selection` | use | Required to select focused survey service/DAL/view/export/scheduler/regression tests. |
| `k98-deferred-optimisation-capture` | use | Required to update active deferred items and keep later survey/reporting/export work visible. |
| `k98-pr-review` | use | Use before handoff to check docs, SQL direction, test plan, and privacy boundaries. |
| `k98-promotion-check` | conditional | Use before production promotion if docs or runtime branches are promoted. |
| `codex-security:security-diff-scan` | conditional | Required before runtime implementation because text responses touch privacy, user input, SQL persistence, exports, and Discord interactions. Usually skipped for audit-only docs with explicit justification. |

## 8. Mandatory Workflow

1. Audit the delivered Phase 7 survey model and SQL contract.
2. Validate SQL-facing assumptions against `C:\K98-bot-SQL-Server`.
3. Compare text/detail storage options:
   - add nullable text columns to `dbo.SurveyAnswers`
   - add a normalized text answer table
   - add a separate detail-note table keyed to response/question/option
   - use a single answer-value table with typed answer kinds
4. Compare Discord UX options for text entry:
   - modal per free-text question
   - modal opened from a question page
   - details modal attached to a selected option
   - separate review/edit page
5. Produce a decision matrix covering product value, privacy, permissions, SQL, UX, exports,
   tests, smoke plan, rollout risk, and rollback posture.
6. Recommend the safest first implementation slice.
7. Split larger text/detail/reporting/export work into future task-pack outlines or structured
   deferred items.
8. Stop for operator approval before implementation.

## 9. Architecture Direction To Validate

Initial preferred direction, subject to audit:

- Keep surveys as separate `dbo.Survey*` SQL objects.
- Preserve `dbo.SurveyAnswers` for choice selections.
- Add text/detail persistence additively rather than overloading option IDs.
- Keep response submit/change service-owned and transactional.
- Keep Discord views focused on interaction flow; services validate text limits and answer rules.
- Keep public posts aggregate-only. Never render raw text answers publicly.
- Keep response-detail export private/admin-leadership only.
- Keep text/detail audit JSON to operational metadata, not full answer payloads.

## 10. SQL Questions To Answer

- Should free-text answers live in `dbo.SurveyAnswers`, a new `dbo.SurveyTextAnswers`, or a more
  general typed answer table?
- Should `Add details` text attach to:
  - a response/question pair
  - a response/question/option selection
  - the whole response envelope
- What max length should SQL enforce for text answers and detail notes?
- Should text/detail values have created/updated timestamps separate from the response envelope?
- How should deleted/replaced text be handled when response changes are enabled?
- What indexes are needed for detail export without creating dashboard/reporting scope?
- What constraints prevent text answers on choice-only questions or details on unselected options?
- What migration rollback posture is acceptable for additive text tables/columns?

## 11. UX Questions To Answer

- How does an admin add a free-text question in the current guided builder without reintroducing
  brittle free-typed question-type input?
- Does `Add details` appear as a per-question toggle, per-option toggle, or always-available
  optional text after selecting choices?
- Should players enter text immediately on the question page, through a modal, or through an
  explicit `Add details` button?
- How is existing text/detail prefilled when a player reopens a submitted response?
- What happens when response changes are disabled?
- How does a timed-out private response panel behave if text has been entered but not submitted?
- What copy makes text length limits clear without turning the panel into instructions?

## 12. Export And Privacy Requirements

- Summary exports should remain aggregate and should not include raw text answers unless a
  separate text-summary design is approved.
- Response-detail exports must include submitted free-text answers and `Add details` notes.
- Text values must be CSV formula-safe.
- Discord user ID must remain spreadsheet-safe text.
- Discord names may be resolved at export time as in current voter/detail exports.
- Governor identity remains excluded unless a later governor-linked voting task is reopened.
- Export audit should include requester, export mode, row count, byte count, column profile,
  oversized flag, and delivery status, but not full text/detail payloads.
- Oversized exports must fail privately with operator guidance.

## 13. Test Strategy To Define

Likely focused tests:

- `tests/test_survey_service.py`: free-text validation, detail-note validation, response change,
  closed rejection, required-answer enforcement, stale/invalid text payloads.
- `tests/test_survey_dal.py`: transactional text/detail persistence, replacement semantics,
  export row mapping, constraints, and missing/stale SQL state.
- `tests/test_survey_post_view.py`: builder controls, text/detail modal flow, owner-only private
  panel behavior, prefill, timeout, and closed/stale rejection.
- `tests/test_survey_export_service.py`: response-detail text columns, formula safety, Discord ID
  text handling, closed-only enforcement, oversized handling, audit metadata.
- `tests/test_survey_presentation.py` or current presentation tests: PublicLive/HiddenUntilClose
  leak prevention for text-bearing surveys.
- `tests/test_vote_admin_cmds.py`: command handoff, option ordering, permission/defer behavior,
  and canonical command registration if command surfaces change.

Regression tests to keep running:

- Existing survey service/view/export/scheduler tests.
- Existing one-choice and multi-select vote tests.
- Command registration validation.
- Full pytest before runtime PR handoff if implementation touches shared survey services,
  scheduler, exports, or command registration.

Baseline validation for this audit/docs slice:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

## 14. Manual Smoke Plan To Define

At minimum, the eventual implementation smoke plan should cover:

1. Create a choice-only survey to prove Phase 7 regression safety.
2. Create a survey with one free-text question.
3. Create a survey with one choice question that allows optional details.
4. Submit a complete response with text/details.
5. Reopen and confirm text/details prefill.
6. Change text/details when response changes are enabled.
7. Confirm changes are blocked when disabled.
8. Confirm HiddenUntilClose does not expose text/detail data publicly while open.
9. Close manually and by scheduler.
10. Export response detail privately and confirm text/details are included and formula-safe.
11. Confirm summary export stays aggregate unless explicitly changed.
12. Confirm existing one-choice vote, multi-select vote, and choice-only survey behavior remains
    compatible.

## 15. Acceptance Criteria

- [ ] Phase 7 survey SQL and runtime contracts are audited.
- [ ] Survey text/detail candidate shapes are compared in a decision matrix.
- [ ] The safest first text/detail implementation slice is recommended with rationale.
- [ ] SQL contract options, constraints, indexes, migration order, and rollback posture are
      documented.
- [ ] Permission/privacy and result-visibility behavior is documented.
- [ ] Builder/player view UX is documented.
- [ ] Export and audit implications are documented, including private text/detail export.
- [ ] Automated tests and manual smoke plan are documented.
- [ ] Deferred optimisation backlog is updated so no draft/resume, optional question, emoji,
      reporting, or export work is lost.
- [ ] Audit-only constraint is satisfied before implementation approval.
- [ ] Required docs validators pass.

## 16. PR Summary Template

```md
## Summary

- Audited free-text survey questions and optional choice-question Add details after Phase 7.
- Recommended the safest first text/detail implementation slice.
- Updated deferred voting backlog and preserved later survey/reporting/export work.

## Tests

- <commands run>

## Risk / Rollback

- Risk: documentation/scope only unless implementation is separately approved.
- Rollback: revert docs/backlog/task-pack changes.
```
