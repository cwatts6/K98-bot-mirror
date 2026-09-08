# Codex Chat Starter - Discord Voting Post Framework Phase 18 Cross Survey Workbook Export Redesign Audit and Design

Status: active starter for the next Discord Voting Post Framework slice.

Phase 1 through Phase 17 are complete. Phase 17 closed the `/vote_admin` reshaping audit with no
runtime command change: keep the existing `/vote_admin` group and command paths, do not add
aliases, a new top-level command, nested groups, or a help/launch panel, and archive the resolved
command-surface deferred item.

Use this starter to begin Phase 18 with audit/scope confirmation before implementation.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 18: Cross Survey Workbook Export Redesign Audit and Design.

Phase 1 through Phase 17 are complete. The voting framework now supports SQL-backed vote posts,
one-choice voting, single-question multi-select voting, SQL-backed multi-question surveys,
choice/text/detail/optional/configurable-rating/ranking survey questions, configurable rating
scales up to 1-10, scale endpoint labels, named rating choices, persisted survey response
drafts/resume for surveys only, one ballot/response per Discord user, response changes when
enabled, scheduler reminders, automatic close, manual close, disabled controls after close,
restart-safe public openers, guided vote create fields, guided survey builder controls,
pre-publish survey review/edit/delete/reorder controls, autocomplete vote/survey lookup for
status/close/export/update, private admin live totals, PublicLive and HiddenUntilClose result
visibility, public close reveal, private totals-only CSV export, private voter-level vote audit CSV
export, private survey response-detail CSV export, private survey report-bundle CSV export,
aggregate-only public rating/ranking results, private export/status/report representation for all
delivered answer types, SQL-backed persisted survey draft exclusion from all result/export/report/
dashboard surfaces until submit, private admin/leadership dashboard-safe reporting contracts,
`/vote_admin dashboard` private aggregate UI, Phase 14 rating-scale extension compatibility,
Phase 15 option emoji/icon support across approved Discord/status/dashboard surfaces, Phase 16
`/vote_admin survey_update` for safe open-survey metadata updates, and the Phase 17 decision to
keep `/vote_admin` as-is.

Phase 17 audit confirmed:
- The current `/vote_admin` command paths work.
- Leadership is comfortable with the naming convention.
- Only a small operator set creates or updates votes/surveys.
- Runtime help is not needed.
- No command renames, aliases, new top-level commands, launch/help panels, command registration
  baseline changes, player controls, SQL/DAL changes, export/report/dashboard shape changes,
  public rendering changes, or broad `/vote_admin` reshaping should be implemented.

Phase 18 objective:
Audit and design whether cross-survey summaries, workbook-style exports, longitudinal reports,
export audit/history summaries, or broader export profile redesign are actually needed now. Keep
the principle simple: preserve private, working export/report surfaces unless a concrete operator
or leadership workflow justifies a carefully scoped addition.

Start with audit/scope confirmation. Do not implement new export commands, workbook generation,
cross-survey selectors, SQL/DAL changes, export schema changes, dashboard changes, public
reporting, retention/redaction behavior, or SQL-native combined reporting until I approve the
product scope, privacy model, data contract, compatibility, documentation, tests, rollout,
rollback, and operator communication plan.

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
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 17 Vote Admin Reshaping Audit and Design.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 18 Cross Survey Workbook Export Redesign Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-sql-validation if SQL objects, DAL queries, export/reporting procedures, workbook source
  data, or SQL-backed reporting contracts are proposed
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before runtime PR handoff if implementation is approved
- k98-promotion-check before production promotion if implementation is approved
- codex-security security review before runtime PR handoff if implementation touches permissions,
  Discord interactions, SQL/data access, generated reports/exports, private data, file handling,
  user-controlled input, or restart-sensitive flows

Candidate Phase 18 audit scope to confirm:
- Inventory current vote and survey export/report surfaces:
  - /vote_admin export mode:totals
  - /vote_admin export mode:voter_audit
  - /vote_admin survey_export mode:totals
  - /vote_admin survey_export mode:response_detail
  - /vote_admin survey_export mode:report_bundle
  - /vote_admin dashboard
- Identify the concrete operator or leadership workflow that would justify cross-survey summaries,
  workbook-style output, longitudinal reporting, export audit/history summaries, or broader export
  profile redesign.
- Decide whether the safest next step is no runtime export change, documentation-only guidance,
  a narrowly scoped private workbook export, a private cross-survey aggregate workbook/report, or
  a staged combination.
- Confirm whether existing CSV profiles must remain byte/header compatible.
- Confirm whether a new export mode under an existing `/vote_admin` command is enough. Default
  expectation: keep the existing `/vote_admin` group and avoid new top-level commands.
- Confirm privacy boundaries for aggregate-only versus response-detail data, including Discord
  identity, raw text answers, choice details, draft exclusion, and HiddenUntilClose semantics.
- Confirm whether SQL repo changes are needed or whether existing bot-side DAL/reporting
  contracts are sufficient.
- Confirm workbook/file generation safety: temporary files, memory-only streams, file size
  protections, spreadsheet formula safety, and Discord upload fallback behavior.
- Confirm tests, Codex Security requirement, deployment order, rollback posture, smoke checks, and
  deferred follow-up work.

Do not include in Phase 18 unless separately approved:
- New voting or survey answer types.
- `/vote_admin` command reshaping, command aliases, new top-level commands, or help panels.
- Changing submitted vote or survey response semantics.
- Changing Phase 16 survey update locks.
- SQL schema or DAL changes not required by the approved export design.
- Public dashboard, public raw text/detail display, public workbook posting, or public
  voter-level/response-detail exports.
- Retention/redaction policy changes.
- SQL-native combined vote/survey reporting views/procedures unless explicitly approved.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Per-rating comments.
- Generated-card custom emoji asset fetching or animation.

Remaining separate follow-up slices:
- Retention/redaction policy changes.
- Optional SQL-native combined reporting views/procedures if reporting consumers or performance
  needs justify them and Phase 18 does not explicitly approve them.

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
