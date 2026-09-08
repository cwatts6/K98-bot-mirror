# Codex Chat Starter - Discord Voting Post Framework Phase 7 Survey Builder Audit and Design

Status: archived starter. Phase 7 is complete and smoke tested; use the active Phase 8 starter for
the next survey slice.

Active next starter:

`docs/task_packs/Codex Chat Starter - Discord Voting Post Framework Phase 8 Survey Free Text and Add Details.md`

Phase 1 through Phase 6 are complete and smoke tested. SQL-backed live voting works, guided vote
creation works, totals-only and voter-audit exports are private/ephemeral for one closed vote at a
time, hidden-until-close result visibility works, single-question multi-select voting works, and
existing open vote controls work after restart.

Use this starter to begin Phase 7 with audit/scope only.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 7: Survey Builder Audit and Design.

Phase 1 through Phase 6 are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one-choice voting, single-question multi-select voting, one ballot per
Discord user, vote changes when enabled, scheduler reminders, automatic close, manual close,
disabled controls after close, restart-safe one-choice buttons and multi-select opener buttons,
guided create fields, guided close durations, autocomplete vote lookup for status/update/close/export,
guided update target selection, vertical result bars, clear one-choice winner/tie/no-vote outcomes,
mode-aware multi-select top-selection outcomes, private totals-only CSV export for one closed vote
at a time, private voter-level audit CSV export for one closed vote at a time, hidden-until-close
result visibility with public close reveal, and private admin live totals.

Phase 6 smoke test confirmed:
- Multi-select create/vote/update/close/status paths work.
- Vote changes allowed and blocked behavior works.
- Selection limits work.
- Restart-safe opener behavior works.
- Previously selected options display when reopening the selector and can be amended.
- One-choice regression behavior remains compatible.

Phase 7 objective:
Audit and design the next approved advanced voting slice: multi-question survey-style voting.
Decide the safest first survey implementation slice and define product scope, privacy, SQL,
permissions, command/view UX, exports, tests, smoke plan, migration order, and deferred follow-up
work.

Start with audit/scope only. Do not implement survey voting, SQL migrations, question-builder UI,
private response flows, export shape changes, dashboard/reporting implementation, or command
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
- docs/reference/ENV_REFERENCE.md
- docs/reference/deferred_optimisations.md
- docs/task_packs/Discord Voting Post Framework - Programme Pack.md
- docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 7 Survey Builder Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation for all SQL-facing survey/schema/audit assumptions
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- k98-promotion-check before production promotion
- codex-security security review before PR handoff if any implementation is later approved because
  survey voting touches Discord interactions, permissions/privacy, user input, SQL-backed
  persistence, result aggregation, generated export/report surfaces, and restart-sensitive
  persistence

Confirmed Phase 7 audit scope:
- Multi-question survey-style voting.
- Survey ownership and command placement.
- Question types and first-slice limits.
- Required/optional answer rules.
- Partial response, resume, and response-change rules.
- Result visibility behavior for PublicLive and HiddenUntilClose modes.
- Player interaction UX: private panel, paged flow, staged confirmation, and existing-answer prefill.
- SQL storage options for survey definitions, questions, options, response envelopes, and answers.
- Export and voter-audit/detail shape options.
- Restart-safe interaction and close behavior.
- Decide which future implementation slice should be first and why.
- Update deferred optimisation status so no survey, emoji/icon, reporting, or export work is lost.

Do not include in Phase 7 unless separately approved:
- Implementing survey voting.
- SQL migrations.
- Per-option emoji/icon support.
- Dashboard/reporting implementation.
- Role-restricted voting.
- Governor-linked voting.
- Saved vote/survey templates.
- Public voter-level export posting.
- Renaming/removing /vote_admin.
- Changing existing one-choice vote button behavior.
- Changing existing multi-select opener/panel behavior.
- Changing existing totals-only or voter-audit export behavior.

Audit/scope requirements:
1. Produce a survey-shape decision matrix.
2. Confirm product value, permission/privacy model, SQL contract needs, command/builder/view UX,
   tests, and smoke plan for each candidate shape.
3. Identify the safest first survey implementation slice.
4. Split remaining approved work into future task-pack outlines or structured deferred items.
5. Validate authoritative SQL assumptions against C:\K98-bot-SQL-Server before recommending a SQL
   shape.
6. Preserve Phase 1 through Phase 6 behavior.
7. Update deferred optimisation status in the plan.

Expected validation for this audit/docs slice:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py

Stop after the audit/scope packet for approval.
```
