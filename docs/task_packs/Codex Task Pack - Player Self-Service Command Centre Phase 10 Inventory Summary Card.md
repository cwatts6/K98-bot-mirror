# Codex Task Pack - Player Self-Service Command Centre Phase 10 Inventory Summary Card

## 1. Task Header

- Task name: `Player Self-Service Command Centre Phase 10 Inventory Summary Card`
- Date: `2026-06-25`
- Owner/context: Player Self-Service Command Centre programme after Phase 9 Quick Launch and Export Options was delivered in production PR #479 and smoke tested successfully
- Task type: `Discord command feature | inventory summary card | player self-service UX alignment | service/DAL audit | visual card rollout`
- One-pass approved: `no`
- Implementation approved after audit/scope: `yes`
- Status: `implemented for validation`

## 2. Required Reading

Before implementation, read:

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
- `docs/task_packs/Player Self-Service Command Centre - Programme Pack.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 9 Quick Launch Expansion and Legacy Export Rollout.md`
- `docs/player_self_service_command_centre_briefing.md`

Conditionally read:

- `docs/reference/Promotion Guide.md` only for production promotion or deployment sequencing.
- Inventory report/export service and DAL tests when summary values, authorization, exports, or report defaults are touched.
- Existing visual-card renderer tests before changing card rendering behavior.

Validate SQL-backed inventory data assumptions against `C:\K98-bot-SQL-Server` before relying on table, view, procedure, or column names.

## 3. Objective

Make Inventory a coherent `/me` destination instead of only a direct handoff into the existing
`/myinventory` report/export journey.

Phase 9 added the private Inventory button and smoke testing confirmed the existing inventory
selector/report flow works and produces cards correctly. The remaining UX gap is that Accounts,
Reminders, Preferences, and Exports now have matching generated `/me` cards, while Inventory does
not. Phase 10 should add a private Inventory summary card using the prepared
`assets/me/cards/me inventory.png` background, then preserve the existing `/myinventory` report
journey for detailed output, timescale controls, and export buttons.

## 4. Background

Delivered context:

- Phase 2 created the private `/me` command-centre shell.
- Phase 5 added the generated private dashboard card and inventory visibility preference control.
- Phase 6 converted Accounts, Reminders, Preferences, and Exports into generated private cards.
- Phase 8 made `/me exports` a private export launchpad.
- Phase 9 removed risky KVK Quick Launch targets, added safe private Inventory and Exports
  navigation, made `/me exports` the preferred export route with option windows, aligned button
  styling across `/me` pages, and preserved all legacy export commands.

Smoke feedback after Phase 9: Inventory works and cards are produced as expected, but it feels out
of sync for Inventory to exist in `/me` only as a direct report/export handoff. The bot already has
enough inventory data to create a useful summary card: resources and values, speedups and values,
and materials and values across three rows. If a player has no approved inventory data, the card
should point them toward the inventory upload channel/process.

## 5. Scope

### In Scope

- Audit current inventory data sources and service boundaries before implementation:
  - approved inventory import data for resources
  - approved inventory import data for speedups
  - approved inventory import data for materials
  - existing inventory report summary/calculation helpers
  - existing inventory export scope and authorization helpers
  - registered-governor account resolution for the current Discord user
- Decide whether Phase 10 should add `/me inventory` as a sixth private subcommand or keep
  Inventory as a dashboard/page-navigation destination without a new slash subcommand. If a new
  subcommand is approved, update command registration governance and canonical command reference.
- Add an Inventory summary state/model in the player self-service service layer or an inventory
  service helper without adding Discord types to service code.
- Render a generated private Inventory summary card using:
  - `assets/me/cards/me inventory.png`
  - safe embed fallback
  - the established `/me` full-bleed card style
  - rows for resources, speedups, and materials
  - latest approved values where available
- Handle user states clearly:
  - no registered governors
  - one registered governor with no approved inventory data
  - multiple registered governors with partial inventory data
  - approved resources only, speedups only, materials only, or combinations
  - unavailable inventory data source
- Point players with no approved inventory data toward the inventory upload channel/process.
- Preserve existing `/myinventory` behavior:
  - governor selection
  - output type/report view selection
  - report visibility preference
  - report timescale controls
  - report export buttons
  - existing ephemeral/private prompt behavior
- Keep dashboard/page navigation consistent with Phase 9 button layout.
- Keep `commands/me_cmds.py`, command modules, and views thin.
- Keep inventory summary business logic in service/DAL layers.
- Update command reference, briefing, programme pack, tests, and deferred backlog after implementation.

### Out of Scope

- Inventory import OCR, approval, correction, or review redesign.
- Full legacy `/myinventory` report card redesign.
- Inventory export schema or file-format changes.
- Stats export changes.
- Legacy export redirect/removal.
- Shared visual-card renderer helper consolidation.
- Preferences Hub expansion beyond inventory summary needs.
- SQL schema changes unless separately approved after audit.
- Public KVK output or channel-rule changes.

## 6. Source Deferred Items

### Deferred Optimisation
- Area: `/me dashboard`, `/me inventory`, `player_self_service/service.py`, `player_self_service/page_cards.py`, `ui/views/player_self_service_views.py`, inventory report services
- Type: consistency
- Description: Phase 9 makes Inventory a visible private `/me` navigation destination, but it still opens the existing `/myinventory` selector/report journey directly instead of showing a matching `/me` Inventory summary card. Smoke testing confirmed the inventory report journey works and cards are produced as expected, but the experience is visually out of sync with Accounts, Reminders, Preferences, and Exports.
- Suggested Fix: Promote an Inventory Summary Card phase that audits existing approved inventory data sources, adds a private generated Inventory card using `assets/me/cards/me inventory.png`, summarizes resources, speedups, and materials with values, handles no-account/no-data states with upload-channel guidance, and preserves the existing `/myinventory` report journey, report visibility controls, and export buttons.
- Impact: medium
- Risk: medium
- Dependencies: Phase 9 Inventory handoff smoke tested successfully; SQL/data-source validation before using inventory summary values; operator approval before adding a sixth `/me inventory` subcommand if selected.

This deferred item has been executed by Phase 10 and removed from the active deferred backlog.

Related deferred items that remain out of Phase 10 unless explicitly approved:

- shared visual-card renderer consolidation
- legacy export command communication/deprecation rollout
- export schema and format redesign
- broader Preferences Hub expansion

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Phase 10 crosses `/me`, inventory data/service boundaries, command governance, card rendering, and docs. |
| `k98-discord-command-feature` | use | `/me` navigation, optional `/me inventory`, buttons, embeds/cards, and timeouts are Discord interaction work. |
| `k98-sql-validation` | use if SQL-backed inventory assumptions are touched | Validate inventory tables/views/procedures and approved-data contracts against the SQL repo. |
| `k98-test-selection` | use | Select focused inventory, player self-service, renderer, view, and command-registration tests. |
| `k98-deferred-optimisation-capture` | use | Keep renderer consolidation, legacy redirects, and export redesign structurally out of Phase 10. |
| `k98-pr-review` | use before handoff | Review privacy, data-source boundaries, command compatibility, tests, docs, and fallback behavior. |
| `codex-security:security-diff-scan` | run or justify before PR handoff | Inventory data, Discord interactions, file/card rendering, and user-specific output are security-sensitive. |

## 8. Mandatory Workflow

1. Start with audit/scope only unless the operator explicitly approves one-pass implementation.
2. Map current inventory data sources and approved-data rules before designing card values.
3. Validate any SQL-backed object, column, procedure, or view assumptions against `C:\K98-bot-SQL-Server`.
4. Decide whether `/me inventory` should become a slash subcommand or only a private navigation page.
5. Design the service-owned inventory summary state and no-data guidance.
6. Implement the approved Phase 10 slice: `/me inventory` is the selected sixth private
   subcommand, with dashboard Inventory navigating to the generated Inventory page.
7. Preserve existing `/myinventory`, inventory report, inventory export, and visibility behavior.
8. Add/update focused tests.
9. Run selected validators and tests.
10. Run Codex Security or explicitly justify skipping.

## 9. Likely Files

```text
commands/me_cmds.py
commands/inventory_cmds.py
player_self_service/service.py
player_self_service/page_cards.py
player_self_service/dashboard_card.py
ui/views/player_self_service_views.py
ui/views/inventory_report_views.py
inventory/
assets/me/cards/me inventory.png
tests/test_me_cmds.py
tests/test_player_self_service_service.py
tests/test_player_self_service_views.py
tests/test_player_self_service_page_cards.py
tests/test_inventory_*.py
tests/test_command_registration_smoke.py
tests/test_validate_command_registration.py
docs/player_self_service_command_centre_briefing.md
docs/reference/canonical_command_reference.md
docs/reference/deferred_optimisations.md
docs/task_packs/Player Self-Service Command Centre - Programme Pack.md
```

## 10. Suggested Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_views.py tests\test_player_self_service_page_cards.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_*.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

Run full pytest if Phase 10 adds a new `/me inventory` slash subcommand, changes shared inventory
summary/report helpers, or changes shared renderer helpers.

## 11. Manual Smoke Checklist

- `/me dashboard` remains private.
- Inventory navigation opens the new private `/me inventory` summary card page.
- The Inventory summary card renders with `assets/me/cards/me inventory.png` and falls back to a
  private embed if rendering or attachment delivery fails.
- Resources, speedups, and materials rows show latest approved values where available.
- Players with no registered governors receive clear private guidance.
- Players with registered governors but no approved inventory data are pointed toward the
  inventory upload channel/process.
- Existing `/myinventory` report flow remains available and unchanged from the Inventory page.
- Existing inventory report timescale controls and export buttons still work.
- Existing `/export_inventory` and `/me exports` inventory export options still work.
- `/me accounts`, `/me reminders`, `/me preferences`, and `/me exports` navigation and button
  styling remain consistent.
- Legacy inventory commands remain registered and usable.

## 12. Acceptance Criteria

- [x] Phase 10 begins with audit/scope unless one-pass implementation is explicitly approved.
- [x] Inventory data sources, approved-data rules, and SQL-backed assumptions are mapped before
  card values are designed.
- [x] `/me` Inventory behavior is decided explicitly: new `/me inventory` subcommand or navigation
  page only.
- [x] The Inventory summary card uses `assets/me/cards/me inventory.png`.
- [x] Summary rows cover resources, speedups, and materials with values where available.
- [x] No-account and no-approved-data states guide players without leaking private data.
- [x] Existing `/myinventory` report behavior, timescale controls, visibility preference, and
  export buttons are preserved.
- [x] No inventory import OCR/review redesign, report schema redesign, export schema redesign, or
  shared renderer consolidation is included.
- [x] Focused tests and standard validators pass.
- [ ] Codex Security is run or explicitly justified.
- [x] Deferred findings are captured structurally.

## 13. PR Summary Template

```md
## Summary

- Added a private `/me` Inventory summary card using the prepared Inventory card background.
- Summarized approved inventory resources, speedups, and materials while preserving `/myinventory`.
- Kept export/report/import behavior unchanged.

## Changes

- <inventory summary service/card/view changes>
- <navigation or command-registration decision>
- <docs/tests>

## Tests

- <commands run>

## Manual Smoke

- <inventory card/report/export smoke notes>

## AI Review Gates

- Codex Security: <run or skipped with reason>

## Risk / Rollback

- Roll back by reverting Phase 10 Inventory card/navigation changes while leaving Phase 9
  Inventory handoff, `/myinventory`, `/me exports`, and legacy export commands live.
```
