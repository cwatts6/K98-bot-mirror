# Codex Chat Starter - Discord Voting Post Framework Phase 4 Voter-Level Audit Export Privacy and Access Controls

Status: active starter for the next Discord Voting Post Framework slice.

Phase 1, Phase 2, and Phase 3 are complete and smoke tested. SQL-backed live voting works, guided
vote creation works, closed vote lookup/export works, totals-only CSV export is private/ephemeral,
and existing open vote buttons work after restart and deployment.

Use this starter to begin Phase 4 with audit/scope only.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 4: Voter-Level Audit Export Privacy and Access
Controls.

Phase 1, Phase 2, and Phase 3 are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one vote per Discord user, vote changes, scheduler reminders, automatic
close, manual close, disabled buttons after close, restart-safe open vote buttons, guided create
fields, guided close durations, autocomplete vote lookup for status/update/close/export, guided
update target selection, vertical result bars, clear winner/tie/no-vote outcomes, and private
totals-only CSV export for one closed vote at a time.

Phase 3 smoke test confirmed:
- /vote_admin export looks good.
- Export response posts ephemerally/private as expected.
- Existing vote buttons work after restart and deployment.

Phase 4 objective:
Decide whether voter-level audit export is allowed, define the privacy/permission model, and only
after approval implement the safe export path if approved.

Start with audit/scope only. Do not implement until I approve the architecture, privacy, SQL,
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
- docs/reference/ENV_REFERENCE.md
- docs/reference/deferred_optimisations.md
- docs/task_packs/Discord Voting Post Framework - Programme Pack.md
- docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 4 Voter-Level Audit Export Privacy and Access Controls.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation for all SQL-facing voter/audit/export assumptions
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- k98-promotion-check before production promotion
- codex-security security review before PR handoff if implementation is approved because this
  touches Discord interactions, permissions/privacy, user input, SQL-backed persistence, and
  generated export files

Confirmed Phase 4 audit scope:
- Decide whether voter-level audit export is allowed now.
- Decide which users can receive voter-level audit export.
- Decide exact allowed/redacted/excluded columns.
- Decide whether Discord user ID only is enough or whether names/governor identity are deferred.
- Decide whether audit export needs SQL audit logging.
- Validate authoritative SQL objects and columns against C:\K98-bot-SQL-Server.
- Preserve totals-only export behavior.
- Keep export responses private/ephemeral by default.
- Preserve Phase 1, Phase 2, and Phase 3 behavior.
- Keep SQL as the source of truth.
- Avoid new top-level commands; prefer an approved /vote_admin export mode or guided /vote_admin path.

Do not include in Phase 4 unless separately approved:
- role-restricted voting
- anonymous/hidden results
- governor-linked voting implementation
- multi-select/survey voting
- saved templates
- website/dashboard reporting
- public voter-level export posting
- batch/date-filtered exports
- renaming/removing /vote_admin
- changing player vote button behavior

Audit/scope requirements:
1. Confirm whether voter-level audit export is allowed now or should remain deferred.
2. Confirm the exact permission model for users who can request it.
3. Confirm the allowed, redacted, and excluded voter/audit columns.
4. Confirm whether a new SQL query/index or audit-log write is needed.
5. Confirm whether the command shape should be an export mode, separate subcommand, or guided selector.
6. Produce a test plan before implementation.
7. Update deferred optimisation status in the plan.

Expected validation after any approved implementation:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- focused voting/admin/export/DAL/service tests
- .\.venv\Scripts\python.exe -m pytest -q tests
- Codex Security review or explicit justification

Stop after the audit/scope packet for approval.
```
