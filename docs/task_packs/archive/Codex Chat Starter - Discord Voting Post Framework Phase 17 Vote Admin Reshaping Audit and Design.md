# Codex Chat Starter - Discord Voting Post Framework Phase 17 Vote Admin Reshaping Audit and Design

Status: archived starter. Phase 17 is complete and closed with no runtime command change.

Phase 17 audit outcome: keep `/vote_admin` as-is. The existing command paths, top-level group,
permissions, autocomplete, usage tracking, command registration baseline, canonical documentation,
private surfaces, exports, reports, dashboard contracts, and survey update locks remain unchanged.
Leadership is comfortable with the current naming convention, only a small operator set creates or
updates votes/surveys, and no runtime help panel is needed.

Phase 1 through Phase 16 are complete and smoke tested. Phase 16 delivered guided survey builder
review/edit/delete/reorder controls for already-added draft survey questions and
`/vote_admin survey_update` for open published surveys. The update path covers title, description,
close time, reminder offsets, reminder `@everyone`, close `@everyone`, option icons, response
changes, and result visibility. Option icons, response changes, and result visibility are blocked
once submitted responses exist, and closed surveys are locked.

Use this starter to begin Phase 17 with audit/scope confirmation before implementation.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 17: Vote Admin Reshaping Audit and Design.

Phase 1 through Phase 16 are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one-choice voting, single-question multi-select voting, SQL-backed
multi-question surveys, choice/text/detail/optional/configurable-rating/ranking survey questions,
configurable rating scales up to 1-10, scale endpoint labels, named rating choices, persisted
survey response drafts/resume for surveys only, one ballot/response per Discord user, response
changes when enabled, scheduler reminders, automatic close, manual close, disabled controls after
close, restart-safe public openers, guided vote create fields, guided survey builder controls,
pre-publish survey review/edit/delete/reorder controls, autocomplete vote/survey lookup for
status/close/export/update, private admin live totals, PublicLive and HiddenUntilClose result
visibility, public close reveal, private totals-only CSV export, private voter-level vote audit CSV
export, private survey response-detail CSV export, private survey report-bundle CSV export,
aggregate-only public rating/ranking results, private export/status/report representation for all
delivered answer types, SQL-backed persisted survey draft exclusion from all result/export/report/
dashboard surfaces until submit, private admin/leadership dashboard-safe reporting contracts,
`/vote_admin dashboard` private aggregate UI, Phase 14 rating-scale extension compatibility,
Phase 15 option emoji/icon support across approved Discord/status/dashboard surfaces, and Phase 16
`/vote_admin survey_update` for safe open-survey metadata updates.

Phase 16 smoke and regression testing confirmed:
- Pre-publish review, edit, delete, and reorder all succeeded.
- Post-publish updates all succeeded.
- Survey update locks after a response is recorded.
- Survey updates are locked after close.
- Existing regression tests completed.

Phase 17 objective:
Audit and design whether `/vote_admin` should be reshaped now that the command group covers vote
creation/update/status/close/export, survey creation/status/close/export/report/dashboard, and
`/vote_admin survey_update`. Keep the principle simple: make it easy for admins to find and run the
right voting or survey action.

Start with audit/scope confirmation. Do not implement command renames, aliases, new top-level
commands, launch panels, help views, command registration baseline changes, player controls,
SQL/DAL changes, export/report/dashboard shape changes, public rendering changes, or broad
`/vote_admin` reshaping until I approve the command architecture, product scope, permissions,
compatibility, documentation, tests, rollout, rollback, and operator communication plan.

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
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 16 Survey Authoring Edit Controls Audit and Design.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 17 Vote Admin Reshaping Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature if command/view changes are approved after audit
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before runtime PR handoff if implementation is approved
- k98-promotion-check before production promotion if implementation is approved
- codex-security security review before runtime PR handoff if implementation touches permissions,
  Discord interactions, command routing, private surfaces, user-controlled input, or
  restart-sensitive flows

Candidate Phase 17 audit scope to confirm:
- Inventory the current `/vote_admin` command group, subcommands, modes, autocomplete paths,
  permissions, command versions, usage tracking, and canonical documentation.
- Compare current vote and survey admin workflows for create, update, status, close, export,
  report bundle, dashboard, and survey update.
- Identify operator pain points such as discoverability, naming consistency, too many sibling
  subcommands, duplicated status/export patterns, update-vs-survey_update confusion, and help text.
- Decide whether the safest next step is command reshaping, a private `/vote_admin` launch/help
  panel, documentation improvements, no runtime command change, or a staged combination.
- Confirm whether existing command paths must remain stable and whether compatibility aliases are
  needed.
- Confirm whether any new top-level command is justified. Default expectation: keep the existing
  approved `/vote_admin` top-level group.
- Confirm permission boundaries for admin-only and leadership-visible surfaces.
- Confirm command-registration baseline, canonical command reference, smoke references, and
  operator/player briefing updates required by any approved shape change.
- Confirm restart-sensitive view implications if a launch/help panel or persistent admin view is
  proposed.
- Confirm tests, Codex Security requirement, deployment order, rollback posture, and deferred
  follow-up work.

Do not include in Phase 17 unless separately approved:
- New voting or survey answer types.
- SQL schema, DAL, export, report-bundle, dashboard, public rendering, or result-shape changes.
- Changing submitted vote or survey response semantics.
- Changing the Phase 16 survey update locks.
- Cross-survey workbook exports or export schema redesign.
- Retention/redaction policy changes.
- SQL-native combined vote/survey reporting views/procedures.
- Public dashboard, public raw text/detail display, or public voter-level/detail exports.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Per-rating comments.
- Generated-card custom emoji asset fetching or animation.

Remaining separate follow-up slices:
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
