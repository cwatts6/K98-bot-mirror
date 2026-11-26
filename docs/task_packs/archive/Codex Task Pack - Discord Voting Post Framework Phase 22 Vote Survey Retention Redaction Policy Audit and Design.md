# Codex Task Pack - Discord Voting Post Framework Phase 22 Vote Survey Retention Redaction Policy Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 22 Vote Survey Retention Redaction Policy Audit and Design`
- Date: `2026-07-08`
- Owner/context: `Closing policy and SQL-admin cleanup slice after Phase 21 graph descope`
- Task type: `audit | privacy policy | SQL data lifecycle | SQL-only destructive admin operation implementation | programme closeout`
- One-pass approved: `no`
- Status: `archived; SQL-only admin delete contract implemented in SQL migration 20260709_001_add_vote_survey_admin_delete with no bot runtime/UI changes`

## 2. Objective

Audit and design the final voting programme slice: retention/redaction policy for vote/survey data,
plus a strictly SQL-side admin function to delete test votes and surveys, including their results,
when those test records pollute leadership stats and engagement reporting.

Phase 1 through Phase 21 are complete or audit-closed. The current runtime is useful enough that
no further bot-side command, dashboard, graph, export, survey-answer-type, or public-output work is
planned in this programme. Phase 22 should close the remaining data-lifecycle gap and then let the
Discord Voting Post Framework programme pack close. Future enhancements should start a new
programme pack.

Implementation approval was granted after the audit/scope packet confirmed the policy, SQL
contract, rollback posture, Codex Security requirement, tests, smoke plan, and communication plan.
The delivered implementation remains SQL-side only.

## 2A. Completion Update

Phase 22 is delivered as the final planned Discord Voting Post Framework slice.

Delivered SQL-side only in `C:\K98-bot-SQL-Server`:

- `migrations/20260709_001_add_vote_survey_admin_delete.sql`
- `sql_schema/dbo.VoteSurveyDeletionAudit.Table.sql`
- `sql_schema/dbo.usp_VoteSurveyAdminDelete.StoredProcedure.sql`

The approved policy and deletion semantics are:

- Default retention remains unchanged for production votes, surveys, text/detail answers, drafts,
  private exports/report bundles, dashboard summaries, engagement CSV contracts, and generated
  in-memory artifacts.
- Test/training records may be hard-deleted by SQL admin when they pollute reporting.
- Break-glass production deletion is allowed through the same manual SQL-admin path, but the
  expected use remains test/training cleanup.
- Vote/survey and text/detail answer data use the same retention/redaction policy.
- Public Discord messages are handled manually outside SQL, with no bot deletion and no public
  deletion post required.
- Rollback after confirmed hard delete is backup/pre-delete-script restore only. No reverse
  procedure is provided.

The SQL implementation adds:

- `dbo.VoteSurveyDeletionAudit`, a durable audit/readback table outside the deleted vote/survey
  item tree.
- `dbo.usp_VoteSurveyAdminDelete`, a manual SQL-admin procedure with `@ContentKind`, explicit
  `@VotePostID` or `@SurveyID`, dry-run default, mandatory `@Reason`, mandatory `@DeletedBy`,
  `@ConfirmDelete`, `@BreakGlassProductionDelete`, row-count readback, local audit summary capture,
  closed-item enforcement, `XACT_ABORT ON`, and dependency-order deletes.

No bot command, Discord UI, dashboard control, autocomplete, modal, service/DAL runtime path,
scheduled job, export schema change, response semantic change, Phase 16 lock change, public output,
or Discord message deletion was added.

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
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 20 Per-User Engagement Export List and Graph Audit and Design.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 21 Private Engagement Graph Assessment Audit and Design.md`
- this Phase 22 task pack

Use these skills as applicable:

- `k98-architecture-scope`
- `k98-sql-validation` because this phase is explicitly SQL-facing and includes destructive
  SQL-only delete design
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review` before runtime or SQL PR handoff if implementation is approved
- `k98-promotion-check` before production promotion if SQL or bot implementation is approved
- `codex-security` security review before runtime or SQL PR handoff because this touches private
  data, SQL/data access, deletion/redaction, auditability, and operational controls

## 4. Delivered Baseline

Phase 1 through Phase 21 delivered or audit-closed:

- SQL-backed one-choice votes, single-question multi-select votes, and multi-question surveys.
- Choice, text, detail, optional, configurable rating, and ranking survey questions.
- Persisted survey drafts/resume with drafts excluded from public/private result and reporting
  surfaces until final submit.
- PublicLive and HiddenUntilClose result visibility.
- Private admin/leadership status, vote exports, survey exports, survey report bundles,
  `/vote_admin dashboard`, and `/vote_admin engagement` CSV export.
- Phase 18 cross-survey/workbook export redesign closed as not required.
- Phase 21 private engagement graph assessment closed as not required.

Phase 22 closes the remaining active concern: training/test votes and surveys can now be removed
from SQL-backed dashboard, engagement, export, and report-bundle data through a cautious manual
SQL-admin path after deployment and backup confirmation.

## 5. Source Deferred Item

### Deferred Optimisation
- Area: `voting/`, private exports, report bundles, dashboard/reporting summaries, SQL-backed vote/survey data
- Type: architecture
- Description: Retention and redaction policy for vote/survey data, exports, reports, audit metadata, and generated artifacts remains intentionally unchanged. The framework stores vote/survey posts, options/questions, responses, text/detail/rating/ranking answers, drafts, reminders, audit metadata, private exports, dashboard summaries, and engagement reporting contracts. Training/test votes and surveys can now pollute leadership stats.
- Suggested Fix: Promoted into Phase 22. Audit vote/survey retention and redaction policy, then design a SQL-side-only admin delete function for test votes and surveys including results. Define data inventory, deletion scope, dry-run/readback, caution gates, audit logging, rollback posture, SQL validation, Codex Security review, tests, deployment order, and programme closeout.
- Impact: high
- Risk: high
- Dependencies: Operator privacy policy approval; SQL repo validation; SQL owner approval; no bot-side delete command or UI; Codex Security review before SQL or runtime PR handoff; no destructive cleanup without rollback and smoke plan.

Closeout: implemented through the SQL-only Phase 22 migration and resolved from the active
deferred backlog. Future voting work should start in a new programme pack.

## 6. SQL Object Families To Inventory

Validate current names and dependencies against `C:\K98-bot-SQL-Server` before implementation.
Initial SQL repo search found these object families:

- Vote post data:
  - `dbo.VotePosts`
  - `dbo.VotePostOptions`
  - `dbo.VotePostVotes`
  - `dbo.VotePostMultiSelectVotes`
  - `dbo.VotePostMultiSelectSelections`
  - `dbo.VotePostReminders`
  - `dbo.VotePostAudit`
- Survey post data:
  - `dbo.SurveyPosts`
  - `dbo.SurveyQuestions`
  - `dbo.SurveyQuestionOptions`
  - `dbo.SurveyResponses`
  - `dbo.SurveyAnswers`
  - `dbo.SurveyTextAnswers`
  - `dbo.SurveyAnswerDetails`
  - `dbo.SurveyRatingAnswers`
  - `dbo.SurveyRankingAnswers`
  - `dbo.SurveyRatingChoiceLabels`
  - `dbo.SurveyResponseDrafts`
  - `dbo.SurveyReminders`
  - `dbo.SurveyAudit`
- Reporting dependencies to review:
  - survey reporting views/procedures introduced in Phase 10 and later compatibility views
  - voting/reporting DAL reads in the bot repo
  - `/vote_admin dashboard`, `/vote_admin engagement`, and private export/report-bundle outputs

The audit must confirm exact foreign-key order, indexes, and dependent views/procedures before any
delete procedure is implemented.

## 7. Candidate Phase 22 Scope To Confirm

### Delivered Scope

- Inventory vote/survey persisted data:
  - active/open/closed posts;
  - options, questions, labels, emoji metadata;
  - one-choice and multi-select vote rows;
  - submitted survey responses;
  - choice, text, detail, rating, ranking answer rows;
  - survey drafts;
  - reminders and scheduler state;
  - vote/survey audit rows;
  - private export/report/dashboard/engagement data contracts;
  - generated local files or temporary artifacts, if any.
- Define retention/redaction policy:
  - default retention posture;
  - whether test/training records should be deleted rather than retained;
  - whether raw text/detail answer data needs a stricter policy than aggregate votes;
  - whether audit metadata is retained, redacted, or moved;
  - whether drafts need expiry/cleanup policy;
  - whether generated exports/artifacts need local cleanup guidance.
- Delivered SQL-side-only admin delete function:
  - SQL repo implementation only;
  - no bot command;
  - no Discord UI;
  - no dashboard/admin button;
  - no `ProcConfig` bot launcher unless separately approved;
  - manual SQL-admin execution only;
  - delete a specific vote by `VotePostID` or a specific survey by `SurveyID`;
  - delete results and dependent rows so stats no longer include the test item;
  - support dry-run mode with row counts before deletion;
  - require an explicit confirmation parameter and reason;
  - return post title/status/count metadata for operator readback;
  - record a deletion audit row outside the deleted item tree before confirmed deletion;
  - make rollback expectations explicit before any destructive action.
- Delivered deletion semantics:
  - open items are rejected and must be closed first;
  - public Discord messages are handled manually outside SQL;
  - item-local audit rows are summarized into `dbo.VoteSurveyDeletionAudit` before deletion;
  - expected use is test/training cleanup;
  - break-glass production deletion is allowed for SQL admins.
- Delivered validation and deployment direction:
  - SQL validation in `C:\K98-bot-SQL-Server`;
  - SQL PR and deployment order;
  - representative database dry-run;
  - pre/post deletion count checks;
  - bot smoke checks confirming dashboard/engagement stats exclude deleted test items;
  - Codex Security review.
- Delivered programme closeout:
  - update the programme pack after Phase 22 completion;
  - archive Phase 22 records;
  - remove or resolve the active deferred item;
  - mark the Discord Voting Post Framework programme complete.

### Explicitly Out Of Scope Unless Separately Approved

- Bot-side delete command, `/vote_admin delete`, dashboard delete button, modal, select, or
  autocomplete.
- Public deletion controls or player-facing deletion visibility.
- Automatic scheduled retention jobs.
- Bulk deletion by date/window/role/title pattern.
- Soft-delete status changes that leave records in current reporting unless explicitly approved.
- Changing vote/survey response semantics.
- Changing Phase 16 survey update locks.
- Changing export CSV/report bundle schemas.
- Deleting Discord messages through the bot.
- Retention/redaction changes outside vote/survey framework data.
- SQL-native combined vote/survey reporting views/procedures unless directly needed for validation.
- Role-restricted voting, governor-linked voting/reporting, saved templates, per-rating comments,
  workbooks, public detail/voter-level outputs, or engagement graphs.

## 8. Delivered Design

Delivered design posture:

- Phase 22 is the final delivered phase for this programme.
- Deletion is SQL-side only and admin/manual only.
- The SQL repo owns one strict procedure:
  - one procedure with a strict `ContentKind` parameter;
  - dry-run default;
  - explicit `@ConfirmDelete = 1`;
  - mandatory `@Reason`;
  - deletion summary output before/after;
  - transaction with `XACT_ABORT ON`;
  - dependency-order deletes based on actual foreign keys;
  - independent deletion audit table because item audit rows are removed.
- Current bot runtime behavior is preserved until deletion is manually executed by a SQL admin.
- No bot-side DAL/service code was added.
- The programme is closed after Phase 22 validation evidence is recorded.

## 9. Test Strategy

For this SQL-only implementation and docs closeout, run:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

- SQL dry-run validation for one vote and one survey test record.
- SQL transaction rollback test or representative-database validation.
- Pre/post row-count checks for every dependent table touched.
- Regression checks that dashboard, engagement, export, and report-bundle data no longer include
  deleted test items.
- Negative-path tests or validation for missing ID, ambiguous kind, missing confirmation, missing
  reason, open-item policy violation, and non-test/break-glass policy.
- SQL repo validation and SQL PR review.
- Codex Security review before SQL or runtime PR handoff.

Runtime bot pytest may be skipped because no bot code or tests changed, but bot-side smoke checks
should still confirm that existing reporting behaves correctly after any SQL deletion operation.

## 10. Rollout / Rollback / Smoke Direction

For the delivered SQL-only delete procedure:

1. Create SQL repo migration/procedure definitions.
2. Validate syntax and dependencies against a representative database.
3. Deploy SQL only; no bot rollout should be required.
4. Run dry-run mode for selected test vote/survey IDs and review row counts.
5. Execute deletion only after operator/SQL-admin confirmation.
6. Verify affected vote/survey no longer appears in `/vote_admin dashboard`, `/vote_admin
   engagement`, private exports, and report-bundle stats.
7. Preserve deletion audit/readback evidence outside the deleted item tree.

Rollback must be explicit before execution. If hard-delete is approved, normal rollback may require
database backup/restore or a SQL-generated pre-delete backup script. Do not rely on a bot PR revert
for SQL-side deletions.

## 11. Programme Closeout Direction

Phase 22 closeout:

- archive the Phase 22 task pack and chat starter;
- update `Discord Voting Post Framework - Programme Pack.md` to mark the programme complete;
- remove or resolve the active retention/redaction deferred item;
- keep future voting enhancements out of this programme pack;
- start a fresh programme pack for any later round of voting development or enhancement work.
