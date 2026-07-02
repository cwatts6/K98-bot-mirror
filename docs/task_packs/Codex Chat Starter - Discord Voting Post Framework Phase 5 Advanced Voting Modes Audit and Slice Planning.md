# Codex Chat Starter - Discord Voting Post Framework Phase 5 Advanced Voting Modes Audit and Slice Planning

Status: active starter for the next Discord Voting Post Framework slice.

Phase 1, Phase 2, Phase 3, and Phase 4 are complete and smoke tested. SQL-backed live voting works,
guided vote creation works, closed vote lookup/export works, totals-only CSV export is
private/ephemeral, voter-level audit CSV export is private/ephemeral for admin/leadership users,
and existing open vote buttons work after restart and deployment.

Use this starter to begin Phase 5 with audit/scope only.

## Copy/Paste Starter

```text
Codex, start Discord Voting Post Framework Phase 5: Advanced Voting Modes Audit and Slice Planning.

Phase 1 through Phase 4 are complete and smoke tested. The voting framework now supports
SQL-backed vote posts, one vote per Discord user, vote changes, scheduler reminders, automatic
close, manual close, disabled buttons after close, restart-safe open vote buttons, guided create
fields, guided close durations, autocomplete vote lookup for status/update/close/export, guided
update target selection, vertical result bars, clear winner/tie/no-vote outcomes, private
totals-only CSV export for one closed vote at a time, and private voter-level audit CSV export for
one closed vote at a time.

Phase 4 smoke test confirmed:
- /vote_admin export mode:voter_audit posts privately/ephemerally.
- CSV includes DiscordUserID and DiscordName.
- DiscordUserID opens in Excel/Sheets as text and preserves the full Discord snowflake.
- Governor names and GovernorID are excluded.
- VoteChanged is correct.
- SQL VotePostAudit writes ActionType=VoterAuditExported with requester ID and expected metadata.
- Regression tests passed.

Phase 5 objective:
Audit the remaining advanced voting-mode candidates and split them into safe future slices. Do not
implement an advanced voting mode in Phase 5 unless I separately approve a follow-up implementation
slice after the audit.

Start with audit/scope only. Do not implement until I approve the architecture, product scope,
privacy, SQL, permissions, and UX direction.

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
- docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 5 Advanced Voting Modes Audit and Slice Planning.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation for all SQL-facing mode/schema/audit assumptions
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- k98-promotion-check before production promotion
- codex-security security review before PR handoff if any implementation is approved because
  advanced modes touch Discord interactions, permissions/privacy, user input, SQL-backed
  persistence, and generated export/report surfaces

Confirmed Phase 5 audit scope:
- Role-restricted voting.
- Hidden-until-close or private result visibility.
- Governor-linked voting or governor-aware audit/reporting.
- Multi-select or survey-style voting.
- Saved vote templates.
- Per-option emoji/icon support.
- Dashboard/reporting readiness.
- Public voter-level export posting policy.
- Decide which future slice should be first and why.
- Update deferred optimisation status so no advanced-mode work is lost.

Do not include in Phase 5 unless separately approved:
- Implementing a voting mode.
- SQL migrations.
- Public voter-level export posting.
- Renaming/removing /vote_admin.
- Changing player vote button behavior.
- Changing existing totals-only or voter-audit export behavior.

Audit/scope requirements:
1. Produce a mode-by-mode decision matrix.
2. Confirm product value, permission/privacy model, SQL contract needs, command/view UX, tests, and
   smoke plan for each candidate mode.
3. Identify the safest first implementation slice.
4. Split remaining approved work into future task-pack outlines or structured deferred items.
5. Validate authoritative SQL assumptions against C:\K98-bot-SQL-Server before recommending a SQL
   shape.
6. Preserve Phase 1 through Phase 4 behavior.
7. Update deferred optimisation status in the plan.

Expected validation for this audit/docs slice:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py

Stop after the audit/scope packet for approval.
```
