# Codex Task Pack - Discord Voting Post Framework Phase 17 Vote Admin Reshaping Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 17 Vote Admin Reshaping Audit and Design`
- Date: `2026-07-07`
- Owner/context: `Follow-up after Phase 16 survey authoring edit controls and survey_update delivery`
- Task type: `audit | command-surface governance | Discord interaction UX | permissions review | documentation planning`
- One-pass approved: `no`
- Status: `active next voting slice; audit/scope only until command architecture, permissions, compatibility, docs, tests, rollout, and operator communication direction are approved`

## 2. Objective

Audit and design whether `/vote_admin` should be reshaped now that the voting framework includes
vote creation/update/status/close/export, survey creation/status/close/export/report/dashboard,
and Phase 16 `/vote_admin survey_update`.

The goal is not to rename commands for tidiness. The goal is to make voting and survey admin work
easy to discover and operate without breaking existing muscle memory, permissions, autocomplete,
usage tracking, smoke references, or command registration guardrails.

Start with audit/scope confirmation. Do not implement command renames, aliases, new top-level
commands, launch panels, help views, command registration baseline changes, player controls,
SQL/DAL changes, export/report/dashboard shape changes, or broad `/vote_admin` reshaping until the
operator approves the architecture, product scope, permissions, compatibility, docs, tests,
rollout, rollback, and communication plan.

## 3. Required Reading

Read first:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/Discord Voting Post Framework - Programme Pack.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 16 Survey Authoring Edit Controls Audit and Design.md`
- `docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 17 Vote Admin Reshaping Audit and Design.md`

## 4. Delivered Baseline

Phase 1 through Phase 16 are complete and smoke tested. The voting framework supports:

- SQL-backed one-choice votes, single-question multi-select votes, and multi-question surveys.
- Choice, text, detail, optional, configurable rating, and ranking survey questions.
- Persisted survey drafts/resume for surveys only, with draft exclusion from result/export/report/
  dashboard surfaces until submit.
- PublicLive and HiddenUntilClose result visibility.
- Scheduler reminders, automatic close, manual close, disabled controls after close, restart-safe
  public openers, and one ballot/response per Discord user.
- Private admin/leadership status, export, report-bundle, and `/vote_admin dashboard` surfaces.
- Option emoji/icon metadata and display across approved Discord/status/dashboard surfaces.
- Guided survey builder review/edit/delete/reorder controls before publish.
- `/vote_admin survey_update` for open published surveys, covering title, description, close time,
  reminder offsets, reminder `@everyone`, close `@everyone`, option icons, response changes, and
  result visibility, with response-sensitive locks.

Phase 16 intentionally kept broad `/vote_admin` reshaping out of scope.

## 5. Source Deferred Item

### Deferred Optimisation
- Area: `voting/`, `/vote_admin`, voting command surface
- Type: architecture
- Description: `/vote_admin` has grown to cover vote creation, survey creation, update/status/close/export/report/dashboard flows, autocomplete lookups, and multiple export/report modes. It remains functional and approved, but broad command reshaping is now a distinct command-surface governance task rather than a prerequisite for remaining voting feature slices.
- Suggested Fix: Promoted into this Phase 17 `/vote_admin` Reshaping audit/design task pack. Validate whether subcommand names, grouping, autocomplete, permissions, docs, command registration baselines, smoke references, and migration guidance should change. Do not rename, remove, or alias existing command paths without operator approval, Codex Security review, updated canonical command documentation, and a communication plan.
- Impact: medium
- Risk: high
- Dependencies: Phase 16 survey authoring edit controls and `/vote_admin survey_update` delivered and smoke tested; explicit operator approval after Phase 17 audit; canonical command reference updates if command paths change; command registration validation; Codex Security review before runtime PR handoff.

## 6. Candidate Phase 17 Scope To Confirm

### In Scope For Audit/Design

- Inventory the current `/vote_admin` command group, subcommands, modes, autocomplete paths,
  permissions, command versions, usage tracking, and canonical documentation.
- Compare current vote and survey admin workflows for create, update, status, close, export,
  report bundle, dashboard, and survey update.
- Identify operator pain points: command discoverability, naming consistency, too many sibling
  subcommands, duplicated status/export patterns, update-vs-survey_update confusion, and help text.
- Decide whether the safest next step is command reshaping, a private `/vote_admin` launch/help
  panel, documentation improvements, no runtime command change, or a staged combination.
- Confirm whether any command path changes require temporary compatibility aliases or whether
  existing paths must remain stable.
- Confirm whether any new top-level command is justified. Default expectation: keep the existing
  approved `/vote_admin` top-level group.
- Confirm permission boundaries for admin-only and leadership-visible surfaces.
- Confirm command-registration baseline, canonical command reference, smoke references, and
  operator/player briefing updates required by any approved shape change.
- Confirm restart-sensitive view implications if a launch/help panel or persistent admin view is
  proposed.
- Confirm tests, Codex Security requirement, deployment order, rollback posture, and deferred
  follow-up work.

### Candidate Implementation Scope If Approved Later

- Update command names, groupings, descriptions, or autocomplete labels only where the approved
  audit shows clear operator value.
- Add a private admin launch/help panel only if it reduces command-discovery friction without
  creating a new persistent-state burden.
- Preserve existing behavior for vote and survey creation, update, status, close, export, report
  bundle, dashboard, and survey update.
- Preserve permission checks, private delivery defaults, audit logging, usage tracking, and
  command versioning.
- Update `docs/reference/canonical_command_reference.md`,
  `scripts/validate_command_registration.py`, tests, smoke references, and operator briefing docs
  for any approved command-surface change.

## 7. Out Of Scope Unless Separately Approved

- New voting or survey answer types.
- SQL schema, DAL, export, report-bundle, dashboard, public rendering, or result-shape changes.
- Changing submitted vote or survey response semantics.
- Changing the Phase 16 survey update locks.
- Cross-survey/workbook export redesign.
- Retention/redaction policy changes.
- SQL-native combined vote/survey reporting views/procedures.
- Public dashboards, public raw text/detail display, or public voter-level/detail exports.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Per-rating comments.
- Generated-card custom emoji asset fetching or animation.

## 8. Remaining Separate Follow-Up Slices

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

## 9. Codex Skills To Use

- `k98-architecture-scope`
- `k98-discord-command-feature` if command/view changes are approved after audit
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review` before runtime PR handoff if implementation is approved
- `k98-promotion-check` before production promotion if implementation is approved
- `codex-security` security review before runtime PR handoff if implementation touches
  permissions, Discord interactions, command routing, private surfaces, user-controlled input, or
  restart-sensitive flows

## 10. Validation Expectations

For audit/docs-only work:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

If implementation is later approved, expected validation areas include:

- command registration validation
- focused vote admin command tests
- permissions tests for admin/leadership surfaces
- view tests if an admin launch/help panel is added
- command usage/version tracking tests if command paths change
- smoke imports
- Codex Security diff scan before runtime PR handoff
- manual Discord smoke testing for old and new command paths, autocomplete, private delivery, and
  any compatibility aliases

## 11. Audit Packet Acceptance Criteria

The audit/scope packet is ready when it clearly answers:

- Whether `/vote_admin` should be reshaped now, or whether docs/help-panel polish is safer.
- Which command paths, descriptions, modes, or autocomplete labels would change if approved.
- Which existing command paths must remain stable and for how long.
- Whether any compatibility aliases are needed.
- Whether a new top-level command is rejected or explicitly justified.
- How permission boundaries, private delivery, usage tracking, command registration, canonical
  docs, smoke references, and operator communication are preserved.
- What tests, smoke checks, deployment order, rollback posture, and security review are required.

Stop after the audit/scope packet unless the operator explicitly approves implementation.
