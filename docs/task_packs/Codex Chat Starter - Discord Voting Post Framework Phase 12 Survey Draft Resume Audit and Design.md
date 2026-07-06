# Codex Chat Starter - Discord Voting Post Framework Phase 12 Survey Draft Resume Audit and Design

Status: active starter for the next Discord Voting Post Framework slice.

Phase 1 through Phase 11 are complete and smoke tested. Phase 11 delivered the private
admin/leadership aggregate dashboard-safe reporting runtime contract for vote/survey summaries,
with no Discord identity, raw text, detail text, or per-user answer data in dashboard-safe payloads.
Smoke testing and regression testing completed successfully on 2026-07-06.

Use this starter to begin Phase 12 with audit/scope confirmation before implementation.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 12: Survey Draft Resume Audit and Design.

Phase 1 through Phase 11 are complete and smoke tested. The voting framework now supports
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
aggregate-only public rating/ranking results, private export/status/report representation for all
delivered answer types, and private admin/leadership aggregate dashboard-safe reporting contracts.

Phase 11 smoke and regression testing confirmed:
- Private aggregate dashboard-safe reporting runtime contract is delivered.
- Dashboard-safe summaries exclude Discord identity, raw text, detail text, and per-user answer
  rows.
- Existing private export profiles remain the approved surface for detailed admin/leadership
  review.
- Regression tests were successful.

Phase 12 objective:
Audit and design persisted survey draft/resume readiness. Confirm product scope, privacy, SQL,
permissions, Discord interaction UX, answer-type handling, optional/rating/ranking behavior,
result/export/dashboard exclusion, close/restart/timeout behavior, tests, smoke plan, deployment
order, rollback posture, and deferred follow-up work.

Start with audit/scope confirmation. Do not implement persisted drafts, new SQL tables, new
commands, command reshaping, retention/redaction behavior changes, or Discord interaction runtime
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
- docs/reference/deferred_optimisations.md
- docs/task_packs/Discord Voting Post Framework - Programme Pack.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 11 Private Dashboard Reporting Runtime Audit and Design.md
- docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 12 Survey Draft Resume Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-sql-validation for SQL persistence/table/procedure/index/export assumptions
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-discord-command-feature if Discord interactions or command/status/export controls are
  changed after approval
- k98-pr-review before runtime PR handoff if implementation is approved
- k98-promotion-check before production promotion if implementation is approved
- codex-security security review before runtime PR handoff if implementation touches permissions,
  Discord interactions, SQL/data access, generated reports, private data, user-controlled text, or
  restart-sensitive flows

Candidate Phase 12 audit scope to confirm:
- Whether draft/resume applies only to surveys, not one-choice or multi-select vote posts.
- Product value and target user journeys for timeout, restart, interruption, voluntary save, and
  resume.
- Whether drafts are automatic, explicit, or both.
- Draft identity key and whether it should use only SurveyID plus Discord user ID.
- How drafts coexist with the existing one submitted response per Discord user model.
- Behavior when response changes are enabled or disabled after final submission.
- Answer-type handling for choice, text, details, optional, rating, and ranking questions.
- Required/optional completion behavior and final submit validation.
- Whether unsubmitted draft answers stay excluded from public results, private dashboard summaries,
  status summaries, totals exports, response-detail exports, and report bundles.
- Whether admins/leadership can see draft counts only, and whether even that should be deferred.
- Close behavior, stale interaction behavior, duplicate in-flight sessions, cleanup/expiry, and
  restart idempotency.
- SQL source-of-truth validation against C:\K98-bot-SQL-Server.
- Whether new SQL tables/procedures are needed.
- Migration order, rollback posture, deployment sequencing, and migration guards if SQL persistence
  is recommended.
- Tests, smoke plan, Codex Security requirement, and promotion gates.

Do not include in Phase 12 unless separately approved:
- Private dashboard UI implementation over the Phase 11 reporting contract.
- Public dashboard implementation.
- New top-level commands or broad /vote_admin reshaping.
- Public raw text/detail export posting.
- Public voter-level/detail export posting.
- Cross-survey workbook exports.
- Retention/redaction policy changes beyond documenting draft posture.
- Rating-scale extensions or custom rating scales.
- Per-option emoji/icon support.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- SQL-native combined vote/survey reporting views/procedures.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing submitted survey behavior except as approved for draft compatibility.

Required but separate follow-up slices:
- Private Dashboard UI implementation over the Phase 11 reporting contract.
- Rating Scale Extensions.
- Emoji/Icon Support.
- /vote_admin Reshaping.
- Cross-survey/workbook export redesign.
- Retention/redaction policy changes.
- Optional SQL-native combined reporting views/procedures if reporting consumers or performance
  needs justify them.

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
