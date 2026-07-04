# Codex Chat Starter - Discord Voting Post Framework Phase 10 Survey Export v2 and Reporting Readiness Audit and Design

Status: active starter for the next Discord Voting Post Framework slice.

Phase 1 through Phase 9C are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one-choice voting, single-question multi-select voting, SQL-backed
multi-question surveys, choice/text/detail/optional/rating/ranking survey questions,
one-response-per-Discord-user semantics, response changes when enabled, scheduler reminders,
automatic close, manual close, disabled controls after close, restart-safe public openers,
guided vote/survey creation, PublicLive and HiddenUntilClose result visibility, private
admin/leadership live status, private closed-only exports, spreadsheet-safe Discord IDs, CSV
formula safety, aggregate-only public rating/ranking summaries, and audit metadata that avoids
full answer payloads.

Use this starter to begin Phase 10 with audit/scope confirmation before implementation.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 10: Survey Export v2 and Reporting Readiness Audit and Design.

Phase 1 through Phase 9C are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one-choice voting, single-question multi-select voting, SQL-backed
multi-question surveys, choice/text/detail/optional/rating/ranking survey questions,
one ballot/response per Discord user, response changes when enabled, scheduler reminders,
automatic close, manual close, disabled controls after close, restart-safe public openers,
guided vote create fields, guided survey builder controls, autocomplete vote/survey lookup for
status/close/export, private admin live totals, PublicLive and HiddenUntilClose result visibility,
public close reveal, private totals-only CSV export, private voter-level vote audit CSV export,
private survey response-detail CSV export, required free-text survey questions, optional
choice-question Add details text, aggregate text-question totals rows, optional survey questions,
fixed 1-5 rating survey questions, complete ranking survey questions, aggregate-only public
rating/ranking results, and private export/status representation for all delivered answer types.

Phase 9C smoke test confirmed:
- Ranking survey creation works.
- Required ranking response flow works.
- Optional ranking skip/clear behavior works.
- Ranking update/regression behavior works.
- Public cards display aggregate ranking summaries only.
- Existing choice/text/detail/optional/rating surveys, multi-select votes, and one-choice votes
  remain compatible.

Phase 10 objective:
Audit and design private Survey Export v2 and reporting readiness now that choice, text, details,
optional questions, fixed 1-5 ratings, and complete rankings are delivered. Confirm product scope,
privacy, SQL, permissions, command/status/export UX, output formats, retention/redaction,
dashboard-readiness boundaries, tests, smoke plan, migration order, rollback posture, and deferred
follow-up work.

Start with audit/scope confirmation. Do not implement SQL reporting views/procedures, workbook
exports, cross-survey exports, dashboard/reporting UI, command changes, export shape changes, or
retention/redaction behavior until I approve the architecture, product scope, privacy, SQL,
permissions, and UX direction.

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
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 9C Ranking Survey Questions.md
- docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 10 Survey Export v2 and Reporting Readiness Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-sql-validation for SQL reporting/view/procedure/index/export assumptions
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-discord-command-feature if command/status/export controls are changed after approval
- k98-pr-review before runtime PR handoff if implementation is approved
- k98-promotion-check before production promotion if implementation is approved
- codex-security security review before runtime PR handoff if implementation touches permissions,
  Discord interactions, SQL/data access, generated exports, private data, user-controlled text, or
  restart-sensitive flows

Candidate Phase 10 audit scope to confirm:
- Current private export inventory for vote totals, voter audit, survey totals, and survey
  response detail.
- Private export v2 consumers and product value.
- Whether richer single-survey exports, cross-survey exports, workbook-style exports, SQL
  reporting views/procedures, service-owned reporting queries, dashboard-ready private summary
  contracts, or export audit/history summaries are approved.
- Privacy boundaries for raw text/detail, per-user answers, Discord IDs, Discord names, result
  visibility, closed-only export, and admin/leadership access.
- Retention/redaction model for raw answers and per-user details.
- SQL source-of-truth validation against C:\K98-bot-SQL-Server.
- Migration order, rollback posture, deployment sequencing, and migration guards if SQL reporting
  objects are recommended.
- Command/admin UX direction for /vote_admin export and /vote_admin status only if approved.
- Tests, smoke plan, Codex Security requirement, and promotion gates.
- Deferred status for draft/resume, rating-scale extensions, emoji/icon support, dashboard runtime
  implementation, and /vote_admin reshaping.

Do not include in Phase 10 unless separately approved:
- Public raw text/detail export posting.
- Public voter-level/detail export posting.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public dashboard or website implementation.
- Draft/resume runtime implementation.
- Rating-scale extensions or custom rating scales.
- Per-option emoji/icon support.
- /vote_admin rename/removal or broad command reshaping.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing choice/text/detail/optional/rating/ranking survey behavior except as approved
  for reporting/export compatibility.

Required but separate follow-up slices:
- Survey Draft/Resume.
- Rating Scale Extensions.
- Emoji/Icon Support.
- /vote_admin Reshaping.

Definitely not required unless a later operator decision reverses the status:
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.

Expected validation for the audit/docs portion:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py

Stop after the audit/scope packet unless I explicitly approve implementation.
```
