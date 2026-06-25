# Codex Task Pack - Player Self-Service Command Centre Phase 8 Exports Launchpad and Quick Launch Expansion

## 1. Task Header

- Task name: `Player Self-Service Command Centre Phase 8 Exports Launchpad and Quick Launch Expansion`
- Date: `2026-06-25`
- Owner/context: Player Self-Service Command Centre programme after Phase 7 unified reminders and dashboard card alignment were smoke tested successfully
- Task type: `Discord command feature | export workflow design | launch surface design | privacy and authorization review`
- One-pass approved: `no`
- Status: `complete; delivered in production PR #478 and smoke tested successfully on 2026-06-25`

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
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 7 Unified Reminder Centre and Dashboard Card Alignment.md`
- `docs/player_self_service_command_centre_briefing.md`

Conditionally read:

- inventory export docs/tests when `/export_inventory` or inventory file delivery is touched
- stats export docs/tests when `/my_stats_export` or stats export file delivery is touched
- `docs/reference/Promotion Guide.md` only for production promotion or deployment sequencing

Validate SQL-backed export, account, stats, or inventory assumptions against `C:\K98-bot-SQL-Server`
before relying on them.

## 3. Objective

Turn `/me exports` from passive private guidance into a safe personal export launchpad where the
existing export services support it, and decide whether Quick Launch should remain dashboard-only
or expand into a richer launch surface.

Delivered result: Phase 8 added private `/me exports` buttons for validated default Stats Excel,
Stats CSV, Inventory Excel, and Inventory CSV downloads. The implementation reused existing
service-backed export generation, authorization, cleanup, telemetry, and private file delivery
paths; kept commands and views free of export persistence, SQL, or file-generation logic; preserved
`/my_stats_export` and `/export_inventory`; and kept Dashboard Quick Launch dashboard-only. Smoke
testing confirmed all four `/me exports` files work, outputs are ephemeral/private, Quick Launch
Exports opens the card correctly, `/me dashboard` does not gain an export button, and legacy export
commands still work.

Use the Phase 9 task pack for the next active phase:

`docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 9 Quick Launch Expansion and Legacy Export Rollout.md`

## 4. Background

Delivered context:

- Phase 2 created `/me dashboard`, `/me accounts`, `/me reminders`, `/me preferences`, and
  `/me exports` as a private command-centre shell. Dashboard Quick Launch was intentionally
  dashboard-only.
- Phase 5 delivered the first generated `/me dashboard` card and service-backed inventory
  visibility preference controls.
- Phase 6 converted `/me accounts`, `/me reminders`, `/me preferences`, and `/me exports` to
  generated private cards with safe embed fallback. `/me exports` remained guidance only.
- Phase 7 unified KVK and calendar reminder status/management, refreshed `/me dashboard` into the
  full-bleed row-based card style, and preserved dashboard-only Quick Launch plus `/me exports`
  no-Quick-Launch behavior.

Smoke testing confirmed Phase 7 looks good and is complete. The next highest-value self-service
gap is exports: players still need to understand which old export command to run and what each
export produces.

## 5. Scope

### In Scope

- Audit current personal export paths, especially `/my_stats_export`, `/export_inventory`, and any
  related stats/inventory export services.
- Map export authorization, file generation, private delivery, error handling, cooldown or
  long-running behavior, and Discord interaction timing.
- Map whether each export is user-owned, admin-assisted, channel-restricted, or visibility-sensitive.
- Design one `/me exports` status/action model that can guide users to stats export, inventory
  export, or unsupported/missing prerequisites without exposing private data.
- Add direct `/me exports` actions only where an existing service-backed, private, restart-safe
  delivery path can be reused without duplicating business logic in views or commands.
- Preserve `/my_stats_export` and `/export_inventory` as live legacy commands.
- Preserve dashboard-only Quick Launch unless Phase 8 audit proves an expanded launch surface is
  safe and operator-approved in the implementation prompt.
- If Quick Launch expands, preserve target command channel rules, visibility rules, permissions,
  and private/public response behavior.
- Keep `commands/me_cmds.py` thin.
- Keep service/export logic Discord-type-free except adapter/view code.
- Update `/me exports` card copy and controls to match the Phase 7 card style.
- Update canonical command reference, programme docs, briefing, and deferred backlog as needed.
- Add focused service/view/renderer/export tests plus standard validators.

### Out of Scope

- Redesigning the full stats report card or `/my_stats` output.
- Redesigning inventory visual reports or inventory import.
- Changing export file schemas without explicit approval.
- Making public outputs private or private outputs public without explicit approval.
- Removing, redirecting, or deprecating `/my_stats_export`, `/export_inventory`, or other legacy
  self-service commands.
- Adding new export types that do not already have a reliable service-backed source.
- Adding website/web-dashboard export delivery.
- Adding new SQL schema unless separately approved after audit.
- Preference hub expansion beyond export-launch behavior.

## 6. Source Deferred Items

### Deferred Optimisation
- Area: `/me dashboard`, `/me exports`, `ui/views/player_self_service_views.py`, player self-service Quick Launch controls
- Type: consistency
- Description: Phase 6 gives `/me exports` a private generated card but intentionally does not turn it into a full export launchpad or add dashboard Quick Launch controls to the exports page. Smoke feedback raised the product question of whether Quick Launch should later become a richer launch surface for KVK stats, targets, history, rankings, inventory, and exports. Pulling that into Phase 6 would mix export product design with the current dashboard/subpage card and Manage-flow simplification work.
- Suggested Fix: Scope Quick Launch expansion and export launchpad design in a later phase. Decide whether Quick Launch remains a dashboard-only select, adds direct export actions, or becomes a reusable launch section on selected pages. Preserve existing channel/visibility rules for target commands, private file-delivery constraints, dashboard-only behavior unless explicitly changed, and `/me exports` privacy expectations. Cover command/view tests and manual smoke for every added launch path.
- Impact: medium
- Risk: medium
- Dependencies: Phase 7 unified reminder centre and dashboard alignment complete and smoke tested; export authorization/private delivery paths validated before adding direct actions.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Phase 8 crosses `/me`, export services, inventory/stats command compatibility, docs, and privacy boundaries. |
| `k98-discord-command-feature` | use | `/me exports`, buttons/selects, private file delivery, interaction timing, and legacy command compatibility are Discord interaction work. |
| `k98-sql-validation` | use if SQL-backed export contracts are touched | Validate stats/inventory/account SQL-backed assumptions against the SQL repo before implementation. |
| `k98-test-selection` | use | Select focused export, view, renderer, command-registration, and standard validation gates. |
| `k98-deferred-optimisation-capture` | use | Capture preference expansion, legacy redirect/removal, export schema redesign, and renderer-helper consolidation out of scope. |
| `k98-pr-review` | use before handoff | Review privacy, authorization, file delivery, command compatibility, tests, and docs. |
| `codex-security:security-diff-scan` | run or justify before PR handoff | Export/file delivery, permissions, interactions, and user-controlled data are security-sensitive. |

## 8. Mandatory Workflow

1. Start with audit/scope only unless the operator explicitly approves one-pass implementation.
2. Map `/my_stats_export`, `/export_inventory`, and any reusable export services before designing
   `/me exports` mutation/action controls.
3. Identify export prerequisites and failure states, including no linked account, multiple linked
   accounts, missing stats, missing inventory authorization, file-generation failure, and Discord
   attachment failure.
4. Decide whether direct export actions are safe for Phase 8 or whether `/me exports` should ship
   improved guidance plus launch handoffs only.
5. Decide whether Quick Launch remains dashboard-only or expands in a tightly scoped way.
6. Implement only the validated Phase 8 slice.
7. Preserve legacy commands and command-registration baseline.
8. Add/update focused tests.
9. Run selected validators and tests.
10. Run Codex Security or explicitly justify skipping.

## 9. Likely Files

```text
commands/me_cmds.py
commands/stats_cmds.py
commands/inventory_cmds.py
player_self_service/service.py
player_self_service/page_cards.py
ui/views/player_self_service_views.py
inventory/
stats/
services/
tests/test_me_cmds.py
tests/test_player_self_service_service.py
tests/test_player_self_service_views.py
tests/test_player_self_service_page_cards.py
tests/test_inventory_*.py
tests/test_stats_export*.py
tests/test_my_stats_export_command.py
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
.\.venv\Scripts\python.exe -m pytest -q tests\test_stats_export.py tests\test_my_stats_export_command.py tests\test_stats_exporter_csv.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_*.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py
```

Run full pytest when direct export actions, file delivery, service authorization, or shared export
helpers change.

## 11. Manual Smoke Checklist

- `/me exports` remains private.
- `/me exports` renders the generated card or safe fallback embed.
- Export guidance/action copy is clear for users with no account, one account, and multiple
  accounts.
- Any direct stats export action uses the existing authorization, CSV/file generation, and private
  delivery behavior.
- Any direct inventory export action uses the existing authorization, data scope, and private file
  delivery behavior.
- Attachment or generation failures produce private, readable errors without leaking data.
- `/my_stats_export` and `/export_inventory` remain registered and usable.
- Dashboard Quick Launch remains dashboard-only unless the approved Phase 8 implementation
  explicitly changes that boundary.
- If Quick Launch expands, each target preserves its existing channel, visibility, and permission
  behavior.
- `/me dashboard`, `/me accounts`, `/me reminders`, and `/me preferences` remain visually and
  behaviorally unchanged except for approved launch links.

## 12. Acceptance Criteria

- [ ] Phase 8 begins with audit/scope unless one-pass implementation is explicitly approved.
- [ ] Export authorization, private file delivery, interaction timing, and legacy compatibility are
  mapped before direct actions are designed.
- [ ] `/me exports` can represent unavailable, guidance-only, and actionable export states without
  misleading users.
- [ ] Direct export controls are implemented only where service-backed authorization and private
  delivery are validated.
- [ ] No export persistence, SQL, or file generation logic is added to commands or views.
- [ ] Dashboard Quick Launch remains dashboard-only unless expansion is explicitly approved and
  validated.
- [ ] Legacy export commands remain live.
- [ ] Existing target command visibility, channel, and permission rules are preserved.
- [ ] Focused tests and standard validators pass.
- [ ] Codex Security is run or explicitly justified.
- [ ] Deferred findings are captured structurally.

## 13. PR Summary Template

```md
## Summary

- Improved `/me exports` as a private export launchpad.
- Preserved legacy export command compatibility and private delivery rules.
- <describe Quick Launch decision>

## Changes

- <export audit and service/view implementation>
- <card/control updates>
- <docs/tests>

## Tests

- <commands run>

## Manual Smoke

- <export and Quick Launch smoke notes>

## AI Review Gates

- Codex Security: <run or skipped with reason>

## Risk / Rollback

- Roll back by reverting the Phase 8 `/me exports` launchpad changes while leaving legacy export
  commands and Phase 7 cards/reminders live.
```
