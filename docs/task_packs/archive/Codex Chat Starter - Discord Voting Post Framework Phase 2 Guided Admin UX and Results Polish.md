# Codex Chat Starter - Discord Voting Post Framework Phase 2 Guided Admin UX and Results Polish

Status: archived starter for the completed Discord Voting Post Framework Phase 2 slice.

Completion note: Phase 2 was delivered and smoke tested on 2026-07-01. Use the Phase 3 starter in
`docs/task_packs/Codex Chat Starter - Discord Voting Post Framework Phase 3 Admin Export and Audit Hardening.md`
for the next voting slice.

Phase 1 is complete. SQL was deployed on 2026-07-01, the bot smoke test created a vote
successfully, voting and vote changes worked, `@everyone` behaved as configured, SQL records
updated correctly, manual close worked, timer close worked, and buttons disabled after close.

Use this starter to begin Phase 2 with audit/scope only.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 2: Guided Admin UX and Results Polish.

Phase 1 is complete and smoke tested. The SQL-backed vote post framework works: admins can create
votes, players can vote and change votes, SQL records reflect the source of truth, @everyone works
as configured, manual close works, timer close works, and buttons disable after close.

Phase 2 objective:
Make the admin UX guided and simple, and make closed results visually obvious.

Start with audit/scope only. Do not implement until I approve the architecture and UX direction.

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
- docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 2 Guided Admin UX and Results Polish.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation if SQL-facing assumptions or query changes are needed
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- k98-promotion-check before production promotion
- codex-security security review before PR handoff because this touches Discord interactions,
  permissions, user input, SQL-backed persistence, and restart-sensitive workflows

User feedback to preserve:
- Pipe-separated option input is too clunky.
- Option character limits fail too late.
- Use separate fields: Option 1 and Option 2 mandatory; Options 3-6 optional.
- Maximum option count should be 6 if layout remains safe.
- Close time should be selector-guided rather than raw UTC free text.
- Vote bars should be vertical rather than horizontal.
- update/status/close should select votes by title/dropdown/autocomplete, not raw VoteID.
- update with all optional fields is confusing; make the edit target explicit or guided.
- status looks good and should be preserved.
- manual and automatic close should show the winner/tie/no-vote result clearly.
- Make it simple, make it guided, and make it look great.

Audit/scope requirements:
1. Confirm whether installed Pycord supports string option max_length.
2. Confirm the best supported Discord pattern for guided close time: choices, autocomplete,
   select/menu, modal, staged flow, or another viable pattern.
3. Confirm whether vote-title autocomplete or select-style lookup is best for update/status/close.
4. Confirm whether 6 option buttons and 6 vertical bars are visually safe.
5. Confirm whether SQL query/index changes are needed for admin vote lookup.
6. Preserve Phase 1 behavior: SQL source of truth, one vote per Discord user, vote changes,
   scheduler reminders, automatic close, disabled buttons, backend late-vote rejection, restart
   safety, and no repeated @everyone on vote updates.
7. Produce a test plan before implementation.

Do not include in Phase 2 unless separately approved:
- export command
- role-restricted voting
- anonymous/hidden results
- governor-linked voting
- multi-select/survey voting
- saved templates
- website/dashboard reporting
- renaming/removing /vote_admin

Expected validation after implementation:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- focused voting/admin/render/scheduler/view tests
- .\.venv\Scripts\python.exe -m pytest -q tests
- Codex Security review or explicit justification

Stop after the audit/scope packet for approval.
```
