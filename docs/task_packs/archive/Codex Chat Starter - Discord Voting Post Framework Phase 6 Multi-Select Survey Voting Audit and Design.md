# Codex Chat Starter - Discord Voting Post Framework Phase 6 Multi-Select Survey Voting Audit and Design

Status: completed starter. Phase 6 has been delivered, smoke tested, and archived as the
single-question MultiSelect implementation slice.

Phase 1 through Phase 5 are complete and smoke tested. SQL-backed live voting works, guided vote
creation works, totals-only and voter-audit exports are private/ephemeral for one closed vote at a
time, hidden-until-close result visibility works, and existing open vote buttons work after restart
and deployment.

This starter is preserved as the historical initiation record for Phase 6. Use the Phase 7 Survey
Builder starter for the next voting slice.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 6: Multi-Select / Survey Voting Audit and Design.

Phase 1 through Phase 5 are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one vote per Discord user for the default one-choice mode, vote changes,
scheduler reminders, automatic close, manual close, disabled buttons after close, restart-safe open
vote buttons, guided create fields, guided close durations, autocomplete vote lookup for
status/update/close/export, guided update target selection, vertical result bars, clear
winner/tie/no-vote outcomes, private totals-only CSV export for one closed vote at a time, private
voter-level audit CSV export for one closed vote at a time, and hidden-until-close result
visibility with public close reveal.

Phase 5 smoke test confirmed:
- Hidden-until-close votes can be created and voted on through the normal public vote post.
- Open hidden-result votes do not leak public interim totals or outcome state.
- Closing the vote reveals total votes, option results, and winner/tie/no-vote outcome.
- Result visibility is shown clearly on the public post.
- Existing button, close, and export behavior remains compatible.

Phase 6 objective:
Audit and design the next approved advanced voting slice: multi-select or survey-style voting.
Decide whether the first implementation should be a single-question MultiSelect vote mode, a
broader multi-question survey mode, or a staged roadmap where MultiSelect ships first and full
survey builder work remains deferred.

Start with audit/scope only. Do not implement SQL migrations, vote-mode behavior, select-menu
interactions, export shape changes, survey builder UI, or command changes until I approve the
architecture, product scope, privacy, SQL, permissions, and UX direction.

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
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 6 Multi-Select Survey Voting Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation for all SQL-facing mode/schema/audit assumptions
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- k98-promotion-check before production promotion
- codex-security security review before PR handoff if any implementation is later approved because
  multi-select/survey voting touches Discord interactions, permissions/privacy, user input,
  SQL-backed persistence, result aggregation, and generated export/report surfaces

Confirmed Phase 6 audit scope:
- Single-question multi-select voting.
- Survey-style voting with multiple questions.
- Vote mode and selection cardinality rules.
- Min/max selection rules.
- Result visibility behavior for PublicLive and HiddenUntilClose modes.
- Player interaction UX: select menu, private panel, buttons, or staged confirmation.
- SQL storage options for multiple selections per Discord user.
- Export and voter-audit shape options.
- Restart-safe interaction and close behavior.
- Decide which future implementation slice should be first and why.
- Update deferred optimisation status so no multi-select, survey, emoji/icon, or reporting work is lost.

Do not include in Phase 6 unless separately approved:
- Implementing a voting mode.
- SQL migrations.
- Per-option emoji/icon support.
- Dashboard/reporting implementation.
- Role-restricted voting.
- Governor-linked voting.
- Saved vote templates.
- Public voter-level export posting.
- Renaming/removing /vote_admin.
- Changing existing one-choice vote button behavior.
- Changing existing totals-only or voter-audit export behavior.

Audit/scope requirements:
1. Produce a multi-select versus survey decision matrix.
2. Confirm product value, permission/privacy model, SQL contract needs, command/view UX, tests, and
   smoke plan for each candidate shape.
3. Identify the safest first implementation slice.
4. Split remaining approved work into future task-pack outlines or structured deferred items.
5. Validate authoritative SQL assumptions against C:\K98-bot-SQL-Server before recommending a SQL
   shape.
6. Preserve Phase 1 through Phase 5 behavior.
7. Update deferred optimisation status in the plan.

Expected validation for this audit/docs slice:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py

Stop after the audit/scope packet for approval.
```
