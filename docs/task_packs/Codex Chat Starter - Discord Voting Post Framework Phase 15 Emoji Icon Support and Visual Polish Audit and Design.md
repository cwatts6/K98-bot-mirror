# Codex Chat Starter - Discord Voting Post Framework Phase 15 Emoji Icon Support and Visual Polish Audit and Design

Status: active starter for the next Discord Voting Post Framework slice.

Phase 1 through Phase 14 are complete and smoke tested. Phase 14 delivered configurable survey
rating scales, including existing fixed 1-5 compatibility, fixed 1-10 ratings, custom min/max
scales, scale endpoint labels, named rating choices, persisted draft/resume compatibility,
PublicLive/HiddenUntilClose aggregate output, private export/report/status/dashboard
representation, SQL migration `20260707_001_add_survey_rating_scales`, review hardening, and
successful operator smoke/regression testing.

Use this starter to begin Phase 15 with audit/scope confirmation before implementation.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 15: Emoji/Icon Support and Visual Polish Audit and Design.

Phase 1 through Phase 14 are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one-choice voting, single-question multi-select voting, SQL-backed
multi-question surveys, choice/text/detail/optional/fixed-or-configurable-rating/ranking survey
questions, configurable rating scales up to 1-10, scale endpoint labels, named rating choices,
persisted survey response drafts/resume for surveys only, one ballot/response per Discord user,
response changes when enabled, scheduler reminders, automatic close, manual close, disabled
controls after close, restart-safe public openers, guided vote create fields, guided survey
builder controls, autocomplete vote/survey lookup for status/close/export, private admin live
totals, PublicLive and HiddenUntilClose result visibility, public close reveal, private totals-only
CSV export, private voter-level vote audit CSV export, private survey response-detail CSV export,
private survey report-bundle CSV export, aggregate-only public rating/ranking results, private
export/status/report representation for all delivered answer types, SQL-backed persisted survey
draft exclusion from all result/export/report/dashboard surfaces until submit, private
admin/leadership dashboard-safe reporting contracts, `/vote_admin dashboard` private aggregate UI,
and Phase 14 rating-scale extension compatibility across public/private/reporting surfaces.

Phase 14 smoke and regression testing confirmed:
- Normal existing fixed 1-5 rating surveys pass.
- 1-10 rating surveys pass.
- Custom min/max scales pass.
- Scale endpoint labels and named rating choices pass.
- Save/draft/resume pass.
- `/vote_admin dashboard`, export, repost, and status pass.
- Other listed regression tests pass.

Phase 15 objective:
Audit and design per-option emoji/icon support for the delivered voting and survey framework,
alongside narrow visual-readability polish for long labels and dense aggregate summaries observed
during Phase 14 smoke testing. Confirm product scope, privacy, SQL storage shape, backward
compatibility, builder/player UX, restart safety, PublicLive/HiddenUntilClose behavior, private
status/export/report/dashboard representation, generated-card glyph fallback, tests, smoke plan,
deployment order, rollback posture, and deferred follow-up work.

Start with audit/scope confirmation. Do not implement SQL migrations, option metadata storage,
builder controls, player controls, renderer changes, export/report/dashboard shape changes, public
rendering changes, command changes, or broad card redesign until I approve the architecture,
product scope, privacy, SQL/reporting posture, permissions, and UX direction.

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
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 13 Private Dashboard UI Audit and Design.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 14 Rating Scale Extensions Audit and Design.md
- docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 15 Emoji Icon Support and Visual Polish Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature if Discord builder/player/dashboard/status/export controls are approved after audit
- k98-sql-validation if SQL option metadata, constraints, reporting objects, DAL, or query-shape changes are proposed
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before runtime PR handoff if implementation is approved
- k98-promotion-check before production promotion if implementation is approved
- codex-security security review before runtime PR handoff if implementation touches permissions,
  Discord interactions, SQL/data access, generated reports/exports, private data, user-controlled
  text/emoji parsing, or restart-sensitive flows

Candidate Phase 15 audit scope to confirm:
- Whether emoji/icon support applies to one-choice vote options, multi-select vote options,
  survey choice options, ranking options, public cards, Discord buttons/selects, private status,
  exports, report bundles, and dashboard summaries.
- Whether rating labels receive no emoji support, or only benefit from visual density/card
  readability polish.
- Whether supported values are Unicode emoji only, custom Discord emoji only, or both.
- SQL source-of-truth validation against C:\K98-bot-SQL-Server before proposing storage changes.
- Whether new SQL columns/tables/check constraints/views/procedures are needed; prefer additive
  backward-compatible changes only when justified.
- Builder UX for approved emoji/icon entry without unsafe free-form values.
- Player response UX, editing/prefill behavior, and restart-safe opener compatibility.
- PublicLive and HiddenUntilClose aggregate output for emoji/icon options.
- Private admin/leadership status, export, report bundle, and dashboard representation.
- Formula-safety, spreadsheet-safe IDs, raw/detail privacy boundaries, tests, smoke screenshots,
  Codex Security requirement, deployment order, rollback posture, and promotion gates.

Do not include in Phase 15 unless separately approved:
- Broad /vote_admin reshaping.
- Cross-survey workbook exports or export schema redesign.
- Retention/redaction policy changes.
- SQL-native combined vote/survey reporting views/procedures.
- Public dashboard, public raw text/detail display, or public voter-level/detail exports.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Per-rating comments.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing choice/text/detail/optional/rating/ranking survey behavior except as approved
  for emoji/icon or visual-readability compatibility.

Required separate follow-up slices:
- /vote_admin Reshaping.
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

Expected validation for the audit/docs portion:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py

Stop after the audit/scope packet unless I explicitly approve implementation.
```
