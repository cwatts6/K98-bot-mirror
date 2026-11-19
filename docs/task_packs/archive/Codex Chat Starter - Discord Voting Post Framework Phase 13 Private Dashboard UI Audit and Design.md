# Codex Chat Starter - Discord Voting Post Framework Phase 13 Private Dashboard UI Audit and Design

Status: archived starter. Phase 13 private dashboard UI was delivered, review-hardened, and
operator smoke tested on 2026-07-07.

Phase 1 through Phase 12 are complete and smoke tested. Phase 11 delivered the private
admin/leadership aggregate dashboard-safe reporting runtime contract for vote/survey summaries,
with no Discord identity, raw text, detail text, or per-user answer data in dashboard-safe payloads.
Phase 12 delivered persisted survey draft/resume for surveys only, with unsubmitted draft answers
excluded from public results, private dashboard summaries, status totals, totals exports,
response-detail exports, and report bundles until final submit.

Historical starter preserved for traceability. Use the active Phase 14 Rating Scale Extensions
starter in `docs/task_packs/` for the next Discord Voting Post Framework slice.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 13: Private Dashboard UI Audit and Design.

Phase 1 through Phase 12 are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one-choice voting, single-question multi-select voting, SQL-backed
multi-question surveys, choice/text/detail/optional/rating/ranking survey questions, SQL-backed
persisted survey response drafts/resume for surveys only, one ballot/response per Discord user,
response changes when enabled, scheduler reminders, automatic close, manual close, disabled
controls after close, restart-safe public openers, guided vote create fields, guided survey
builder controls, autocomplete vote/survey lookup for status/close/export, private admin live
totals, PublicLive and HiddenUntilClose result visibility, public close reveal, private totals-only
CSV export, private voter-level vote audit CSV export, private survey response-detail CSV export,
private survey report-bundle CSV export, aggregate-only public rating/ranking results, private
export/status/report representation for all delivered answer types, and private admin/leadership
aggregate dashboard-safe reporting contracts.

Phase 12 smoke and regression testing confirmed:
- Persisted survey drafts/resume work for surveys only.
- Automatic draft save and explicit Save and exit work.
- Restart-safe resume works.
- Duplicate in-flight panel stale revision protection works.
- Older stale panels are closed in place with clear guidance to continue in the newer panel.
- Draft-saved acknowledgement is orange and clearly says draft answers are not counted until
  submitted.
- Required/optional final submit behavior remains correct.
- Choice, text, details, rating, ranking, and optional answers are handled correctly.
- Unsubmitted draft answers stay excluded from public results, private dashboard summaries, status
  totals, totals exports, response-detail exports, and report bundles.
- Regression tests were successful.

Phase 13 objective:
Audit and design the private admin/leadership dashboard UI over the Phase 11 dashboard-safe
reporting service contract. Confirm product scope, permissions, privacy, command/interaction
surface, UX, result visibility behavior, answer-type representation, draft exclusion, SQL/reporting
performance posture, tests, smoke plan, deployment order, rollback posture, and deferred follow-up
work.

Start with audit/scope confirmation. Do not implement new commands, command reshaping, new SQL
objects, public dashboards, retention/redaction behavior changes, cross-survey workbook exports,
raw text/detail exposure, per-user dashboard rows, or Discord interaction runtime changes until I
approve the architecture, product scope, privacy, SQL/reporting posture, permissions, and UX
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
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 12 Survey Draft Resume Audit and Design.md
- docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 13 Private Dashboard UI Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature if Discord commands/views/panels are approved after audit
- k98-sql-validation if SQL/reporting object or query-shape changes are proposed
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before runtime PR handoff if implementation is approved
- k98-promotion-check before production promotion if implementation is approved
- codex-security security review before runtime PR handoff if implementation touches permissions,
  Discord interactions, SQL/data access, generated reports, private data, user-controlled text, or
  restart-sensitive flows

Candidate Phase 13 audit scope to confirm:
- Whether the dashboard UI should be a Discord private command/view, generated private file/card,
  internal private web surface, existing status/export flow extension, or another approved surface.
- Whether any command change is needed and whether it can stay within the existing /vote_admin
  command group.
- Admin/leadership permission boundaries and private/ephemeral delivery rules.
- Dashboard-safe data boundary: no Discord identity, no per-user answer rows, no raw text answers,
  no choice detail text, no unsubmitted draft answers, and no public posting.
- HiddenUntilClose behavior for private admin/leadership viewers versus public visibility.
- Vote and survey overview/detail UX, filters, pagination, refresh, loading/error states, mobile
  readability, and response-size limits.
- Answer-type representation for one-choice, multi-select, choice/text/detail survey questions,
  optional questions, rating questions, ranking questions, and excluded drafts.
- Whether Phase 11 service payloads are sufficient or presentation adapters are needed.
- SQL source-of-truth validation against C:\K98-bot-SQL-Server if any SQL/reporting changes are
  proposed.
- Whether new SQL tables/procedures/views are needed; prefer none unless justified.
- Tests, smoke plan, Codex Security requirement, deployment order, rollback posture, and promotion
  gates.

Do not include in Phase 13 unless separately approved:
- Public dashboard implementation or public website.
- Raw text/detail dashboard display.
- Per-user response rows or voter-level dashboard display.
- Public raw text/detail export posting.
- Public voter-level/detail export posting.
- Cross-survey workbook exports.
- Retention/redaction policy changes.
- Rating-scale extensions or custom rating scales.
- Per-option emoji/icon support.
- Broad /vote_admin reshaping beyond a narrowly approved dashboard surface.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- SQL-native combined vote/survey reporting views/procedures unless the audit proves they are
  needed and I approve them.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing submitted survey or draft/resume behavior except as approved for dashboard
  exclusion/display compatibility.

Required but separate follow-up slices:
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
