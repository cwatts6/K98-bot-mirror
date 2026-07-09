# Codex Chat Starter - Discord Voting Post Framework Phase 22 Vote Survey Retention Redaction Policy Audit and Design

Use this to start the final Phase 22 audit/design slice.

```text
Codex, start Discord Voting Post Framework Phase 22: Vote/Survey Retention and Redaction Policy
Audit and Design.

Phase 1 through Phase 21 are complete or audit-closed. Phase 21 confirmed no private engagement
graph is required now because the Phase 20 CSV export provides the data and leadership can create
ad hoc graphs externally if needed.

Phase 22 objective:
Audit and design the final voting programme slice: vote/survey retention and redaction policy, plus
a strictly SQL-side admin function to delete test votes and surveys, including their result data.
We created many training/test votes and surveys while helping users and leadership learn the tools,
and those records now pollute dashboard/engagement/export stats. The delete function is admin
territory, must be used with caution, and must be SQL-side only. Do not create a bot command,
dashboard control, Discord UI, autocomplete, modal, DAL/service runtime path, scheduled job, or
public output for deletion.

Start with audit/scope confirmation. Do not implement cleanup, deletion, redaction, SQL changes,
command controls, file cleanup, deployment behavior, or retention policy changes until I approve
the policy, SQL contract, deletion semantics, rollback posture, audit/readback behavior, tests,
Codex Security review, rollout, smoke checks, and operator communication plan.

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
- docs/reference/deferred_optimisations.md
- docs/task_packs/Discord Voting Post Framework - Programme Pack.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 20 Per-User Engagement Export List and Graph Audit and Design.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 21 Private Engagement Graph Assessment Audit and Design.md
- docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 22 Vote Survey Retention Redaction Policy Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-sql-validation because the phase is SQL-facing and includes destructive SQL-only delete design
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before SQL/runtime PR handoff if implementation is approved
- k98-promotion-check before production promotion if SQL/runtime implementation is approved
- codex-security security review before SQL/runtime PR handoff because this touches private data,
  SQL/data access, deletion/redaction, auditability, and operational controls

Candidate Phase 22 audit scope to confirm:
- Inventory all vote/survey stored data:
  - VotePosts, VotePostOptions, VotePostVotes, VotePostMultiSelectVotes,
    VotePostMultiSelectSelections, VotePostReminders, VotePostAudit
  - SurveyPosts, SurveyQuestions, SurveyQuestionOptions, SurveyResponses, SurveyAnswers,
    SurveyTextAnswers, SurveyAnswerDetails, SurveyRatingAnswers, SurveyRankingAnswers,
    SurveyRatingChoiceLabels, SurveyResponseDrafts, SurveyReminders, SurveyAudit
  - reporting views/procedures, exports, report bundles, dashboard summaries, engagement CSV
    contracts, and generated/local artifacts
- Define retention and redaction policy for:
  - production votes/surveys
  - training/test votes/surveys
  - raw text/detail answers
  - private exports/report bundles
  - drafts
  - audit metadata
  - generated/local artifacts
- Design SQL-side-only delete function:
  - manual SQL-admin execution only
  - no bot command or Discord UI
  - delete by explicit VotePostID and/or SurveyID
  - delete results and dependent rows so stats no longer include the test item
  - dry-run/readback by default
  - explicit confirmation parameter and mandatory reason
  - row-count output before and after
  - transaction and dependency-order safety
  - deletion audit/readback stored outside the deleted item tree if approved
  - rollback expectations before execution
- Confirm whether deletes are limited to test/training records or include break-glass production
  deletion.
- Confirm whether public Discord messages are manually handled outside SQL.
- Confirm SQL deployment order, validation, Codex Security review, smoke checks, and programme
  closeout steps.

Do not include unless separately approved:
- /vote_admin delete or any bot-side delete command.
- Dashboard delete button, modal, select, autocomplete, or admin panel.
- Public deletion controls or player-facing deletion visibility.
- Automatic scheduled retention jobs.
- Bulk deletion by date/window/role/title pattern.
- Export schema changes.
- Vote/survey response semantic changes.
- Phase 16 survey update lock changes.
- Discord message deletion through the bot.
- Retention/redaction changes outside vote/survey framework data.
- Role-restricted voting, governor-linked voting/reporting, saved templates, per-rating comments,
  workbooks, public detail/voter-level outputs, or engagement graphs.

Expected validation for the audit/docs portion:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py

Stop after the audit/scope packet unless I explicitly approve implementation. Once Phase 22 is
delivered, update and close the Discord Voting Post Framework programme pack. Any future voting
enhancements should start in a new programme pack.
```
