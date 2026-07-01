# Codex Task Pack - Player Self-Service Command Centre v2 Phase 1 Stats Profile Inventory Audit and Design

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 1 Stats Profile Inventory Audit and Design`
- Date: `2026-06-27`
- Owner/context: Follow-on audit after the first Player Self-Service Command Centre programme completed in production PR #486 and smoke testing confirmed the Phase 13 redirects
- Task type: `audit | command-surface design | player workflow modernisation planning`
- One-pass approved: No
- Status: `prepared - not started`

## 2. Objective

Audit the remaining larger player self-service-aligned paths that were intentionally preserved
outside the first programme:

```text
/my_stats
/stats player
/player_profile
/myinventory
```

Also review `/mykvkcrystaltech` for product fit, but do not assume it belongs in the same command
group or redesign slice.

Start with audit/scope only. Do not redirect, deprecate, remove, or redesign these commands until
the operator reviews and approves the classifications and recommendations.

## 3. Required Reading

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
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/player_self_service_command_centre_briefing.md`

Conditionally read:

- SQL repo `C:\K98-bot-SQL-Server` for stats/profile/inventory SQL contracts if the audit needs
  table, view, procedure, or export-schema details.
- `docs/reference/Promotion Guide.md` only for promotion or deployment tasks.

## 4. In Scope

For each candidate path, document:

- owner module and called service/view/DAL layers
- command registration shape and options
- permission model and channel gating
- public/private response behavior
- usage tracking identity and available usage evidence
- visual output and export/report contracts
- SQL/persistence dependencies
- restart/rehydration sensitivity
- current tests and missing coverage
- user-facing copy and likely player/operator confusion
- whether the command should be preserved, linked from `/me`, grouped, redesigned, or left out of
  v2

## 5. Classification Options

Classify each path as one of:

- preserve as-is
- preserve but improve copy/navigation
- add `/me` or grouped entry point while keeping existing command
- redesign candidate
- leadership/admin workflow, not player self-service
- specialist workflow outside v2
- removal/redirect candidate only after separate approval

## 6. Explicit Non-Goals

- Do not redirect or remove `/my_stats`, `/stats player`, `/player_profile`, `/myinventory`, or
  `/mykvkcrystaltech`.
- Do not redesign stats cards, inventory report cards, profile embeds, export schemas, or SQL
  contracts in Phase 1.
- Do not change public/channel-gated KVK behavior.
- Do not move leadership-only behavior into player-only `/me` flows without explicit approval.
- Do not fold CrystalTech into `/me` without a product decision.

## 7. Suggested Validation For Audit-Only Scope

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

If implementation is later approved, add focused tests for the touched command/service/view paths
and run the relevant stats, profile, inventory, command-registration, and smoke-import checks.

## 8. Acceptance Criteria

- Every candidate path has documented behavior, ownership, permissions, visibility, usage evidence,
  and command-registration details.
- The audit distinguishes player self-service paths from leadership/admin and specialist paths.
- Recommendations preserve compatibility unless an explicit later rollout is approved.
- Any proposed `/me` or grouped entry point includes privacy/channel/permission implications.
- SQL/data/export contracts are not guessed; ambiguous contracts are validated against the SQL
  repo or called out explicitly.
- Deferred optimisation items are updated if the audit confirms actionable follow-up work.
- No command behavior changes are made in the audit-only slice.
