# Codex Chat Starter - Discord Voting Post Framework Phase 14 Rating Scale Extensions Audit and Design

Status: archived starter. Phase 14 rating scale extensions were delivered, review-hardened, and
operator smoke/regression tested on 2026-07-07.

Phase 1 through Phase 13 are complete and smoke tested. Phase 13 delivered `/vote_admin dashboard`
as a private admin/leadership aggregate dashboard UI over the Phase 11 dashboard-safe reporting
contract. Smoke testing confirmed vote and survey dashboard pages, refresh, next, previous, close,
open/closed filters, admin/leadership access control, and no details or Discord names visible.

Historical starter preserved for traceability. Phase 15 is also complete and archived; use the
programme pack or the current active starter in `docs/task_packs/` for the next Discord Voting
Post Framework slice.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 14: Rating Scale Extensions Audit and Design.

Phase 1 through Phase 13 are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one-choice voting, single-question multi-select voting, SQL-backed
multi-question surveys, choice/text/detail/optional/fixed-1-5-rating/ranking survey questions,
persisted survey response drafts/resume for surveys only, one ballot/response per Discord user,
response changes when enabled, scheduler reminders, automatic close, manual close, disabled
controls after close, restart-safe public openers, guided vote create fields, guided survey
builder controls, autocomplete vote/survey lookup for status/close/export, private admin live
totals, PublicLive and HiddenUntilClose result visibility, public close reveal, private totals-only
CSV export, private voter-level vote audit CSV export, private survey response-detail CSV export,
private survey report-bundle CSV export, aggregate-only public rating/ranking results, private
export/status/report representation for all delivered answer types, SQL-backed persisted survey
draft exclusion from all result/export/report/dashboard surfaces until submit, private
admin/leadership dashboard-safe reporting contracts, and `/vote_admin dashboard` private aggregate
UI.

Phase 13 smoke and regression testing confirmed:
- `/vote_admin dashboard` opens privately for admin/leadership users.
- Votes and surveys both render aggregate dashboard summaries.
- Refresh, Next, Previous, Close, Open filter, and Closed filter work as expected.
- Access is correctly limited to leadership and admin.
- No details or Discord names are visible.
- Dashboard output is aggregate-only and private.
- Regression tests and review hardening passed.

Phase 14 objective:
Audit and design rating-scale extensions for the delivered fixed 1-5 survey rating question type.
Confirm product scope, privacy, SQL storage shape, backward compatibility for existing 1-5 ratings,
builder/player UX, persisted draft/resume compatibility, PublicLive/HiddenUntilClose aggregate
behavior, private status/export/report/dashboard representation, tests, smoke plan, deployment
order, rollback posture, and deferred follow-up work.

Start with audit/scope confirmation. Do not implement SQL migrations, new rating storage shape,
builder controls, player controls, export/report/dashboard shape changes, public rendering changes,
or command changes until I approve the architecture, product scope, privacy, SQL/reporting posture,
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
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 9B Rating Survey Questions.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 10 Survey Export v2 and Reporting Readiness Audit and Design.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 11 Private Dashboard Reporting Runtime Audit and Design.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 12 Survey Draft Resume Audit and Design.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 13 Private Dashboard UI Audit and Design.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 14 Rating Scale Extensions Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature if Discord builder/player/dashboard/status/export controls are approved after audit
- k98-sql-validation if SQL storage, constraints, reporting objects, DAL, or query-shape changes are proposed
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before runtime PR handoff if implementation is approved
- k98-promotion-check before production promotion if implementation is approved
- codex-security security review before runtime PR handoff if implementation touches permissions,
  Discord interactions, SQL/data access, generated reports/exports, private data, user-controlled
  text, or restart-sensitive draft flows

Candidate Phase 14 audit scope to confirm:
- Whether KD98 needs fixed 1-10 ratings, configurable numeric min/max scales, scale labels,
  named rating choices, per-rating comments, or no rating-scale extension for now.
- Backward compatibility for existing fixed 1-5 rating questions and responses.
- SQL source-of-truth validation against C:\K98-bot-SQL-Server before proposing storage changes.
- Whether new SQL columns/tables/check constraints/views/procedures are needed; prefer additive
  backward-compatible changes only when justified.
- Builder UX for approved scale choices without free-form unsafe values.
- Player response UX, editing/prefill behavior, required/optional semantics, optional skip/clear,
  and persisted draft/resume compatibility.
- PublicLive and HiddenUntilClose aggregate output for extended scales.
- Private admin/leadership status, export, report bundle, and dashboard representation.
- Formula-safety, spreadsheet-safe IDs, raw/detail privacy boundaries, tests, smoke plan, Codex
  Security requirement, deployment order, rollback posture, and promotion gates.

Do not include in Phase 14 unless separately approved:
- Per-option emoji/icon support.
- Broad /vote_admin reshaping.
- Cross-survey workbook exports or export schema redesign beyond rating-scale compatibility.
- Retention/redaction policy changes.
- Public dashboard, public raw text/detail display, or public voter-level/detail exports.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- SQL-native combined vote/survey reporting views/procedures unless performance or reporting
  consumers justify them and I separately approve SQL scope.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing choice/text/detail/optional/ranking survey behavior except as approved for
  rating-scale compatibility.

Required separate follow-up slices:
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
