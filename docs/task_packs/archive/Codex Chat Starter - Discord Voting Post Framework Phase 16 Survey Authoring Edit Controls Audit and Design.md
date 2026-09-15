# Codex Chat Starter - Discord Voting Post Framework Phase 16 Survey Authoring Edit Controls Audit and Design

Status: archived starter. Phase 16 is complete, review-hardened, smoke/regression tested, and no
longer the active next slice.

Phase 1 through Phase 15 are complete and smoke tested. Phase 15 delivered additive nullable vote
and survey option emoji metadata, Unicode/custom Discord emoji support, guided option-polish
controls, Discord button/select display, private status/dashboard emoji display including animated
custom emoji, generated-card custom emoji text fallback, no export/report schema expansion, review
hardening, SQL PR #38 production deployment, and successful operator smoke/regression testing.

Historical note: Phase 16 delivered guided survey builder review/edit controls for already-added
draft questions, including edit, delete, and reorder, plus `/vote_admin survey_update` for open
published surveys. The update path covers title, description, close time, reminder offsets,
reminder `@everyone`, close `@everyone`, option icons, response changes, and result visibility.
Option icons, response changes, and result visibility are blocked once submitted responses exist,
and closed surveys are locked. Broad `/vote_admin` reshaping is promoted to Phase 17.

Use this starter only for historical context.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 16: Survey Authoring Edit Controls Audit and Design.

Phase 1 through Phase 15 are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one-choice voting, single-question multi-select voting, SQL-backed
multi-question surveys, choice/text/detail/optional/configurable-rating/ranking survey questions,
configurable rating scales up to 1-10, scale endpoint labels, named rating choices, persisted
survey response drafts/resume for surveys only, one ballot/response per Discord user, response
changes when enabled, scheduler reminders, automatic close, manual close, disabled controls after
close, restart-safe public openers, guided vote create fields, guided survey builder controls,
autocomplete vote/survey lookup for status/close/export, private admin live totals, PublicLive and
HiddenUntilClose result visibility, public close reveal, private totals-only CSV export, private
voter-level vote audit CSV export, private survey response-detail CSV export, private survey
report-bundle CSV export, aggregate-only public rating/ranking results, private export/status/report
representation for all delivered answer types, SQL-backed persisted survey draft exclusion from all
result/export/report/dashboard surfaces until submit, private admin/leadership dashboard-safe
reporting contracts, `/vote_admin dashboard` private aggregate UI, Phase 14 rating-scale extension
compatibility, and Phase 15 option emoji/icon support across approved Discord/status/dashboard
surfaces.

Phase 15 smoke and regression testing confirmed:
- Vote and survey emoji behavior works.
- Unicode emoji work.
- Custom Discord emoji work.
- Animated custom Discord emoji display correctly in Discord/status/dashboard.
- Generated PNG cards intentionally fall back to custom emoji text such as `:alert:`.
- Guided option-polish controls work.
- SQL PR #38 was merged and pushed to production before bot rollout.
- Existing regression tests pass.

Phase 16 objective:
Audit and design guided survey authoring edit controls so admins can correct already-added draft
survey questions before publish, especially option emoji/icon metadata. Confirm whether a narrow
post-publish survey option-icon update path should exist for open surveys, and under what
restrictions. Keep the principle simple: make it easy for admins to create surveys.

Start with audit/scope confirmation. Do not implement builder controls, post-publish update
commands, SQL/DAL changes, player controls, export/report/dashboard shape changes, public rendering
changes, command changes, or broad `/vote_admin` reshaping until I approve the architecture,
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
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 15 Emoji Icon Support and Visual Polish Audit and Design.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 16 Survey Authoring Edit Controls Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature if Discord builder/player/dashboard/status/export controls are approved after audit
- k98-sql-validation if SQL option metadata, audit rows, constraints, DAL, or query-shape changes are proposed
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before runtime PR handoff if implementation is approved
- k98-promotion-check before production promotion if implementation is approved
- codex-security security review before runtime PR handoff if implementation touches permissions,
  Discord interactions, SQL/data access, generated reports/exports, private data, user-controlled
  text/emoji parsing, or restart-sensitive flows

Candidate Phase 16 audit scope to confirm:
- Guided survey builder review controls for already-added draft questions before publish.
- Guided edit controls for draft question text, required/optional flag, option labels, and option
  emoji metadata where safe.
- Option emoji/icon correction for draft single-choice, multi-select, and ranking questions.
- Whether rating/text/detail questions need any draft edit controls in this slice.
- Whether delete/reorder belongs in Phase 16 or a later slice.
- Whether an explicit Review survey step should appear before publish.
- Whether a narrow post-publish survey option-icon update path should exist for open surveys.
- Whether post-publish icon updates should be blocked after responses exist, only after close, or
  never allowed.
- SQL source-of-truth validation against C:\K98-bot-SQL-Server before proposing persistence
  changes.
- Whether existing Phase 15 nullable emoji metadata is sufficient or audit/concurrency changes are
  needed.
- Player response UX, editing/prefill behavior, and restart-safe opener compatibility.
- PublicLive and HiddenUntilClose aggregate output after metadata-only icon updates.
- Private admin/leadership status, export, report bundle, and dashboard representation.
- Formula-safety, spreadsheet-safe IDs, raw/detail privacy boundaries, tests, smoke screenshots,
  Codex Security requirement, deployment order, rollback posture, and promotion gates.

Do not include in Phase 16 unless separately approved:
- Broad /vote_admin reshaping.
- Changing submitted survey response semantics.
- Post-publish question type changes, option deletes, option reordering, or label changes that
  would reinterpret existing responses.
- Cross-survey workbook exports or export schema redesign.
- Retention/redaction policy changes.
- SQL-native combined vote/survey reporting views/procedures.
- Public dashboard, public raw text/detail display, or public voter-level/detail exports.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Per-rating comments.
- Generated-card custom emoji asset fetching or animation.

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
