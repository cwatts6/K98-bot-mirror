# Codex Chat Starter - Discord Voting Post Framework Phase 3 Admin Export and Audit Hardening

Status: archived completed starter. Phase 3 was delivered in mirror PR #195 and smoke tested on
2026-07-02. Use the Phase 4 starter in `docs/task_packs/` for the next voting slice.

Phase 1 and Phase 2 are complete. SQL-backed live voting works, guided vote creation works,
admins can select votes by lookup for status/update/close, the guided update panel works, closed
results show clear winner/tie/no-vote outcomes, buttons disable after close, and open vote buttons
survive bot restart.

Use this starter to begin Phase 3 with audit/scope only.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 3: Admin Export and Audit Hardening.

Phase 1 and Phase 2 are complete and smoke tested. The voting framework now supports SQL-backed
vote posts, one vote per Discord user, vote changes, scheduler reminders, automatic close, manual
close, disabled buttons after close, restart-safe open vote buttons, guided create fields, guided
close durations, autocomplete vote lookup for status/update/close, guided update target selection,
vertical result bars, and clear winner/tie/no-vote outcomes.

Phase 3 objective:
Make completed vote results and audit data easy for admins to retrieve safely.

Start with audit/scope only. Do not implement until I approve the architecture, privacy, SQL, and
UX direction.

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
- docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 3 Admin Export and Audit Hardening.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation for all SQL-facing lookup/export assumptions
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- k98-promotion-check before production promotion
- codex-security security review before PR handoff because this touches Discord interactions,
  permissions/privacy, user input, SQL-backed persistence, and generated export files

Confirmed Phase 3 scope:
- Guided admin lookup for closed vote results.
- Export final option totals for one completed vote.
- Decide whether voter-level audit export is allowed now or deferred.
- Keep export responses private/ephemeral by default.
- Preserve Phase 1 and Phase 2 behavior.
- Keep SQL as the source of truth.
- Avoid new top-level commands; prefer /vote_admin export or an approved /vote_admin guided path.

Audit/scope requirements:
1. Confirm whether /vote_admin export is the best command shape or whether export should be
   reached from status/history controls.
2. Confirm whether voter-level export is allowed for admin/leadership users or should be
   totals-only in the first implementation.
3. Confirm whether closed-vote lookup can use existing DAL queries efficiently or needs a new
   query/index.
4. Confirm whether export should support one vote at a time or a date/status-filtered batch.
5. Confirm whether CSV is enough for Phase 3 or whether embed-only summary output should also be
   included.
6. Validate authoritative SQL objects and columns against C:\K98-bot-SQL-Server.
7. Produce a test plan before implementation.

Do not include in Phase 3 unless separately approved:
- role-restricted voting
- anonymous/hidden results
- governor-linked voting
- multi-select/survey voting
- saved templates
- website/dashboard reporting
- public voter-level export posting
- renaming/removing /vote_admin
- changing player vote button behavior

Expected validation after implementation:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- focused voting/admin/export/DAL/presentation tests
- .\.venv\Scripts\python.exe -m pytest -q tests
- Codex Security review or explicit justification

Stop after the audit/scope packet for approval.
```
