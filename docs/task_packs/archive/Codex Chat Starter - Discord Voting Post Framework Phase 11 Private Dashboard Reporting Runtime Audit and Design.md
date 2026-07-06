# Codex Chat Starter - Discord Voting Post Framework Phase 11 Private Dashboard Reporting Runtime Audit and Design

Status: archived starter. Phase 11 is delivered, smoke tested, regression tested, and archived.

Phase 1 through Phase 11 are complete and smoke tested. Phase 11 delivered the private
admin/leadership aggregate dashboard-safe reporting runtime contract. It did not add dashboard UI,
new commands, cross-survey/workbook exports, retention/redaction behavior changes, command
reshaping, public detail posting, or new SQL objects.

Use the active Phase 12 starter in `../` for the next Discord Voting Post Framework slice.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 11: Private Dashboard Reporting Runtime Audit and Design.

Phase 1 through Phase 10 are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one-choice voting, single-question multi-select voting, SQL-backed
multi-question surveys, choice/text/detail/optional/rating/ranking survey questions, one
ballot/response per Discord user, response changes when enabled, scheduler reminders, automatic
close, manual close, disabled controls after close, restart-safe public openers, guided vote
create fields, guided survey builder controls, autocomplete vote/survey lookup for status/close/
export, private admin live totals, PublicLive and HiddenUntilClose result visibility, public close
reveal, private totals-only CSV export, private voter-level vote audit CSV export, private survey
response-detail CSV export, private survey report-bundle CSV export, required free-text survey
questions, optional choice-question Add details text, aggregate text-question totals rows,
optional survey questions, fixed 1-5 rating survey questions, complete ranking survey questions,
aggregate-only public rating/ranking results, and private export/status/report representation for
all delivered answer types.

Phase 10 smoke test confirmed:
- Report bundle creates a private multi-CSV bundle.
- The generated CSV files open cleanly.
- The bundle contains expected rows.
- Regression tests were successful.

Phase 11 objective:
Audit and design private dashboard/reporting runtime readiness now that Phase 10 delivered the
single-survey report bundle and SQL survey reporting views/procedure. Confirm product scope,
privacy, SQL, permissions, command/status/export UX, runtime contract shape, result visibility,
raw text/detail boundaries, tests, smoke plan, deployment order, rollback posture, and deferred
follow-up work.

Start with audit/scope confirmation. Do not implement dashboard UI, new commands, combined SQL
views/procedures, cross-survey exports, workbook exports, retention/redaction behavior, or command
reshaping until I approve the architecture, product scope, privacy, SQL, permissions, and UX
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
- docs/reference/deferred_optimisations.md
- docs/task_packs/Discord Voting Post Framework - Programme Pack.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 10 Survey Export v2 and Reporting Readiness Audit and Design.md
- docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 11 Private Dashboard Reporting Runtime Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-sql-validation for SQL reporting/view/procedure/index/export assumptions
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-discord-command-feature if command/status/export controls are changed after approval
- k98-pr-review before runtime PR handoff if implementation is approved
- k98-promotion-check before production promotion if implementation is approved
- codex-security security review before runtime PR handoff if implementation touches permissions,
  Discord interactions, SQL/data access, generated reports, private data, user-controlled text, or
  restart-sensitive flows

Candidate Phase 11 audit scope to confirm:
- Private dashboard/reporting consumers and product value.
- Whether the first runtime output should be service/DAL contract, Discord command, generated
  file, or internal reporting contract.
- Combined vote/survey dashboard-safe summary dimensions.
- Participation, outcomes/top selections, result visibility, vote mode, answer type, optional,
  rating, and ranking dimensions.
- Raw text/detail, per-user answer, Discord ID, and Discord name privacy boundaries.
- Whether open hidden-until-close results remain public-hidden while admin/leadership private
  reporting can see live state.
- SQL source-of-truth validation against C:\K98-bot-SQL-Server.
- Whether new vote reporting views/procedures are needed after Phase 10's survey reporting views.
- Migration order, rollback posture, deployment sequencing, and migration guards if SQL reporting
  objects are recommended.
- Command/admin UX direction for /vote_admin status, survey_status, export, or a new approved
  report surface only if approved.
- Tests, smoke plan, Codex Security requirement, and promotion gates.
- Deferred status for cross-survey/workbook exports, retention/redaction policy, draft/resume,
  rating-scale extensions, emoji/icon support, and /vote_admin reshaping.

Do not include in Phase 11 unless separately approved:
- Public dashboard or website implementation.
- Public raw text/detail export posting.
- Public voter-level/detail export posting.
- Cross-survey workbook exports.
- Retention/redaction behavior changes.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Draft/resume runtime implementation.
- Rating-scale extensions or custom rating scales.
- Per-option emoji/icon support.
- /vote_admin rename/removal or broad command reshaping.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing choice/text/detail/optional/rating/ranking survey behavior except as approved
  for reporting compatibility.

Required but separate follow-up slices:
- Survey Draft/Resume.
- Rating Scale Extensions.
- Emoji/Icon Support.
- /vote_admin Reshaping.
- Cross-survey/workbook export redesign.
- Retention/redaction policy changes.

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
