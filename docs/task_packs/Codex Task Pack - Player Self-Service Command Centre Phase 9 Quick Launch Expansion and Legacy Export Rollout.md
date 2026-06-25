# Codex Task Pack - Player Self-Service Command Centre Phase 9 Quick Launch Expansion and Legacy Export Rollout

## 1. Task Header

- Task name: `Player Self-Service Command Centre Phase 9 Quick Launch Expansion and Legacy Export Rollout`
- Date: `2026-06-25`
- Owner/context: Player Self-Service Command Centre programme after Phase 8 `/me exports` was delivered in production PR #478 and smoke tested successfully
- Task type: `Discord command feature | launch-surface audit | export option workflow | legacy command rollout design | privacy and channel-rule review`
- One-pass approved: `approved after audit/scope discussion on 2026-06-25`
- Status: `implementation prepared for review`

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
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 8 Exports Launchpad and Quick Launch Expansion.md`
- `docs/player_self_service_command_centre_briefing.md`

Conditionally read:

- `docs/reference/Promotion Guide.md` only for production promotion or deployment sequencing.
- Existing KVK, inventory, stats, and export command tests when direct launch or redirect behavior is touched.
- `docs/reference/events_and_dm_reminders.md` only if launch scope unexpectedly touches reminder/calendar commands.

Validate SQL-backed command usage or export assumptions against `C:\K98-bot-SQL-Server` before relying on them.

## 3. Objective

Decide the next `/me` launch-surface step after Phase 8 validated private exports, and decide the
first safe rollout step for legacy export commands.

Phase 9's approved decision is to remove risky KVK command targets from Dashboard Quick Launch,
keep those outputs in their existing channel-gated command paths, and add only safe private
dashboard handoffs for Inventory and Exports.

Phase 9 also makes `/me exports` the preferred private export route by adding option child windows
for Stats and Inventory exports. `/my_stats_export` and `/export_inventory` remain live unless a
later operator-approved communication and no-feedback window explicitly approves redirect or
removal.

## 4. Background

Delivered context:

- Phase 2 created the private `/me` shell and dashboard Quick Launch guidance.
- Phase 6 added generated private cards for Accounts, Reminders, Preferences, and Exports while
  keeping `/me exports` guidance-only.
- Phase 7 aligned `/me dashboard` with the full-bleed card style and preserved dashboard-only
  Quick Launch.
- Phase 8 turned `/me exports` into a direct private launchpad for validated default Stats Excel,
  Stats CSV, Inventory Excel, and Inventory CSV downloads. Smoke testing confirmed all four export
  actions work, outputs are ephemeral/private, `/me dashboard` has no direct export button, Quick
  Launch `Exports` opens the card correctly, and legacy export commands still work.

The programme question was resolved during Phase 9 scoping: using Quick Launch to initiate
`/kvk stats`, `/kvk targets`, `/kvk history`, or `/kvk rankings` has too much risk of bypassing
channel and public-output expectations while adding little player value. `/me exports` is the
better place to improve the export journey because it is already private and service-backed.

## 5. Scope

### In Scope

- Audit the current Dashboard Quick Launch targets:
  - `/kvk stats`
  - `/kvk targets`
  - `/kvk history`
  - `/kvk rankings`
  - `/myinventory`
  - `/me exports`
- For each target, map channel restrictions, admin overrides, permission decorators, public vs
  private output behavior, required parameters, interaction timing, and whether a launch handoff
  can safely be represented inside `/me`.
- Remove KVK command targets from dashboard Quick Launch.
- Add dashboard `Inventory` and `Exports` buttons only.
- Route dashboard Inventory into the equivalent existing `/myinventory` selector/report journey,
  preserving report visibility settings and existing inventory report controls.
- Route dashboard Exports into `/me exports`.
- Update `/me exports` to show two controls: `Export Stats` and `Export Inventory`.
- Add a Stats export child window with Format and Days selectors. Defaults: Format `Excel`, Days
  `90`. Options: Format `Excel`, `CSV`, `Google Sheets`; Days `30`, `60`, `90`, `180`, `360`.
- Add an Inventory export child window with Format, View, Governor, and Days selectors. Defaults
  must match existing inventory export behavior.
- Keep Download/Cancel child-window behavior private and simple.
- Implement only launch controls that preserve every target command's existing channel,
  visibility, permission, privacy, and argument rules.
- Review `/my_stats_export` and `/export_inventory` usage, smoke feedback, player communication,
  and compatibility needs.
- Design the first legacy export rollout step as: keep live, prefer `/me exports`, and defer any
  redirect/removal until after player communication and a no-feedback window are separately
  approved.
- Preserve `/my_stats_export` and `/export_inventory` unless operator approval explicitly includes
  redirect/removal.
- Keep `commands/me_cmds.py`, command modules, and views thin.
- Keep service logic Discord-type-free except adapter/view code.
- Update card/control copy only where needed to support the approved launch model.
- Update canonical command reference, programme docs, briefing, and deferred backlog as needed.
- Add focused command/view/service tests plus standard validators.

### Out of Scope

- Export schema or file-format redesign.
- New export types.
- New SQL schema unless separately approved after audit.
- Broad Preferences Hub expansion.
- Shared visual-card renderer helper consolidation.
- Redirect/removal of non-export legacy self-service commands.
- Public KVK/calendar command redesign.
- Redesigning `/kvk stats`, `/kvk targets`, `/kvk history`, `/kvk rankings`, `/myinventory`, or
  `/me exports` output formats.
- Making public outputs private or private outputs public without explicit approval.

## 6. Source Deferred Items

### Deferred Optimisation
- Area: `/me dashboard`, `/me exports`, `ui/views/player_self_service_views.py`, player self-service Quick Launch controls
- Type: consistency
- Description: Phase 8 delivered `/me exports` while Dashboard Quick Launch remained dashboard-only and guidance-only for KVK stats, KVK targets, KVK history, KVK rankings, inventory, and exports. Phase 9 resolves this by removing KVK targets from the dashboard launch surface and keeping only safe private Inventory and Exports handoffs.
- Suggested Fix: Implement the approved Phase 9 resolution: remove KVK Quick Launch targets, add dashboard Inventory and Exports buttons, preserve target-command guards, and add command/view tests plus manual smoke for the new private handoff paths.
- Impact: medium
- Risk: medium
- Dependencies: Phase 8 export launchpad delivered and smoke tested; operator approved the Phase 9 Inventory/Exports-only handoff model.

### Deferred Optimisation
- Area: `commands/stats_cmds.py`, `commands/inventory_cmds.py`, `/my_stats_export`, `/export_inventory`, player self-service docs/tests
- Type: cleanup
- Description: Phase 9 keeps `/my_stats_export` and `/export_inventory` live while making `/me exports` the preferred route with Stats and Inventory option windows. The legacy paths remain useful compatibility surfaces, but they need a deliberate communication, monitoring, redirect, deprecation, or removal decision after Phase 9 is smoke tested.
- Suggested Fix: Review usage and player feedback after Phase 9, decide whether each legacy export command should remain live indefinitely, redirect to `/me exports`, or be removed after a no-feedback window, then update command registration baselines, canonical command reference, player briefing, and focused command tests.
- Impact: medium
- Risk: medium
- Dependencies: Phase 9 `/me exports` option windows smoke tested; operator approval for any redirect/removal; player communication before final removal.

### Deferred Optimisation
- Area: `player_self_service/page_cards.py`, `player_self_service/dashboard_card.py`, `kvk/rendering/`, `prekvk/report_image_renderer.py`, visual card renderers
- Type: refactor
- Description: Shared visual-card renderer consolidation remains inside the Player Self-Service Command Centre programme because `/me` established the cross-page card model. It is not part of Phase 9 because launch-surface and legacy-command rollout decisions should stay behavior-focused.
- Suggested Fix: Keep shared renderer consolidation as a later programme phase. Extract stable primitives only after Phase 9 launch/legacy behavior is settled, migrate one renderer at a time, and preserve existing card filenames, fallback behavior, dimensions, and player-name Unicode handling.
- Impact: medium
- Risk: medium
- Dependencies: Phase 9 launch/legacy decisions complete or explicitly out of the way; existing renderer tests green.

### Deferred Optimisation
- Area: `services/stats_export_service.py`, `stats/dal/stats_export_dal.py`, `stats_exporter.py`, `stats_exporter_csv.py`, `inventory/export_service.py`, `inventory/dal/`, SQL repo export views/tables, export docs/tests
- Type: architecture
- Description: Export schema and format redesign remains separate from Player Self-Service. Phase 8 intentionally reused existing stats and inventory export schemas and file formats, and Phase 9 should not change file contracts while deciding launch/legacy behavior.
- Suggested Fix: Treat export schema and format redesign as a separate export-output programme unless a later approved task explicitly narrows one backwards-compatible file-format improvement into this programme.
- Impact: high
- Risk: high
- Dependencies: Operator approval for a dedicated export-output programme; SQL validation and downstream consumer review before any schema/format changes.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Phase 9 crosses `/me`, KVK/inventory/stats launch behavior, command compatibility, docs, and privacy/channel boundaries. |
| `k98-discord-command-feature` | use | Quick Launch controls, redirects, private/public responses, and interaction timing are Discord command work. |
| `k98-sql-validation` | use if SQL-backed usage/export assumptions are touched | Validate any SQL-backed usage or export contract before relying on it. |
| `k98-test-selection` | use | Select focused command, service, view, redirect, and command-registration tests. |
| `k98-deferred-optimisation-capture` | use | Keep renderer consolidation and export schema redesign structurally captured but out of Phase 9 implementation. |
| `k98-pr-review` | use before handoff | Review channel/privacy preservation, command compatibility, tests, and docs. |
| `codex-security:security-diff-scan` | run or justify before PR handoff | Discord interactions, redirects, permissions, file delivery, and user-visible outputs are security-sensitive. |

## 8. Mandatory Workflow

1. Start with audit/scope only unless the operator explicitly approves one-pass implementation.
2. Map each Quick Launch target's command rules before designing direct controls.
3. Map legacy export command usage and compatibility expectations before designing redirect or
   deprecation behavior.
4. Propose the safest launch model and legacy export rollout option.
5. Implement the approved Phase 9 slice: dashboard Inventory/Exports handoffs plus `/me exports`
   option windows.
6. Preserve existing target command channel, visibility, permission, privacy, and argument rules.
7. Preserve `/my_stats_export` and `/export_inventory` unless redirect/removal is explicitly
   approved.
8. Add/update focused tests.
9. Run selected validators and tests.
10. Run Codex Security or explicitly justify skipping.

## 9. Likely Files

```text
commands/me_cmds.py
commands/kvk_cmds.py
commands/stats_cmds.py
commands/inventory_cmds.py
player_self_service/service.py
player_self_service/page_cards.py
ui/views/player_self_service_views.py
ui/views/player_self_service_export_views.py
ui/views/kvk_personal_views.py
ui/views/inventory_report_views.py
tests/test_me_cmds.py
tests/test_player_self_service_service.py
tests/test_player_self_service_views.py
tests/test_player_self_service_page_cards.py
tests/test_player_self_service_export_views.py
tests/test_my_stats_export_command.py
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
.\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_views.py tests\test_player_self_service_page_cards.py tests\test_player_self_service_export_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_my_stats_export_command.py tests\test_stats_export.py tests\test_stats_exporter_csv.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_*.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py
```

Run full pytest when direct launch controls, redirects, command registration, or shared view
behavior changes.

## 11. Manual Smoke Checklist

- `/me dashboard` remains private.
- Dashboard no longer includes KVK Quick Launch targets.
- Dashboard Inventory opens the existing `/myinventory` selector/report journey.
- Dashboard Exports opens `/me exports`.
- `/me exports` remains private and opens Stats and Inventory child option windows.
- Stats export defaults to Excel and 90 days and can send Excel, CSV, and Google Sheets.
- Inventory export defaults match existing inventory export behavior and can send selected
  format/view/governor/day options.
- Cancel closes each child option window without sending a file.
- `/my_stats_export` and `/export_inventory` remain live unless redirect/removal is explicitly
  approved.
- If an export legacy command redirects, the redirect is private, clear, and does not break command
  registration validation.
- `/me accounts`, `/me reminders`, and `/me preferences` remain visually and behaviorally
  unchanged except for approved launch-surface copy.
- Legacy player commands remain registered and usable unless specifically approved for redirect.

## 12. Acceptance Criteria

- [x] Phase 9 began with audit/scope before operator-approved implementation.
- [x] Every Quick Launch target's channel, visibility, permission, privacy, and argument rules are
  mapped before direct launch controls are designed.
- [x] Dashboard KVK Quick Launch is removed rather than expanded into direct KVK launch controls.
- [x] Expanded launch paths are limited to private Inventory and Exports handoffs.
- [x] `/my_stats_export` and `/export_inventory` remain live unless explicit redirect/removal
  approval is recorded.
- [x] Legacy export rollout includes player communication/no-feedback planning before final removal.
- [x] No export schema, file format, SQL, or output redesign is included.
- [x] Shared visual-card renderer consolidation remains captured for a later programme phase.
- [x] Focused tests and standard validators pass.
- [x] Codex Security is run or explicitly justified.
- [x] Deferred findings are captured structurally.

## 13. PR Summary Template

```md
## Summary

- Removed risky KVK command targets from dashboard Quick Launch and kept KVK commands in their
  existing channel-gated paths.
- Added private dashboard Inventory and Exports handoffs.
- Made `/me exports` the preferred export route with Stats and Inventory option child windows.
- Preserved `/my_stats_export` and `/export_inventory` unchanged for compatibility.

## Changes

- `/me dashboard`: Inventory and Exports buttons only for launch handoffs.
- `/me exports`: Export Stats and Export Inventory option windows with Download/Cancel.
- Docs/tests updated for Phase 9 decisions.

## Tests

- <commands run>

## Manual Smoke

- <Quick Launch and legacy export smoke notes>

## AI Review Gates

- Codex Security: <run or skipped with reason>

## Risk / Rollback

- Roll back by reverting the Phase 9 launch/legacy changes while leaving Phase 8 `/me exports` and
  all legacy export commands live.
```
