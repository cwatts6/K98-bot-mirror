# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 2 Governor Context and Dashboard Data Foundation

Status: archived after Phase 2 delivery, review hardening, smoke testing, and regression validation
completed on 2026-07-10. Superseded by the Phase 3 Governor Selector and Dashboard Shell starter.

## Copy/Paste Starter

```text
Codex, start Player Self-Service Command Centre v2 Phase 2: Governor Context and Dashboard Data Foundation.

Context:
The Phase 1 Governor Dashboard Product Blueprint and Audit is complete. The operator wants the /me redesign to go big and bold, becoming a premium KD98 governor operating system rather than a simple command cleanup. The next logical step is to build the safe service/DAL foundation before changing the visible Discord journey or renderer.

Important operator decision:
Ignore Olympia data for now. Olympia fights and Olympia win ratio are not in the current source system. Do not add Olympia fields, placeholders, guessed values, or implementation blockers for Olympia in Phase 2. It can be added later if a reliable source/data contract is introduced.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- docs/task_packs/Player Self-Service Command Centre v2 Phase 1 Governor Dashboard Product Blueprint and Audit Report.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 2 Governor Context and Dashboard Data Foundation.md
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Use SQL validation against:
- C:\K98-bot-SQL-Server

Likely SQL-backed objects to validate before relying on fields:
- dbo.v_PlayerLatestStats
- dbo.v_PlayerProfile
- dbo.ALL_STATS_FOR_DASHBOARD
- dbo.v_EXCEL_FOR_KVK_All
- dbo.v_EXCEL_FOR_KVK_Started
- dbo.GovernorInventoryProfile

Use these skills:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review
- codex-security:security-scan

Objective:
Build the governor-context and dashboard-data foundation for the future premium /me dashboard.

Scope:
1. Add a typed/structured governor dashboard context model.
2. Add service helpers to list linked governors for a Discord user.
3. Add service helpers to resolve no/one/multiple governor future journey states.
4. Add access checks so normal self-service mode only allows governors linked to the invoking Discord user.
5. Add a dashboard payload service/DAL layer for selected governor data.
6. Include approved fields only: governor name, governor ID, self-view account type, optional self-view VIP, alliance, power, kill points, highest acclaim, dead, helps, healed, Ark joined/won/win ratio, times named Autarch, Conduct Score from SQL field Conduct, Civilisation from SQL field Civilization, and freshness/update timestamp where available.
7. Exclude Olympia fights and Olympia win ratio completely.
8. Separate self-view-only data from future inspect-safe data.
9. Keep the payload renderer-independent and ready for the future premium card renderer.
10. Add focused tests for governor resolution, access denial, payload assembly, missing/null values, zero Ark joined, missing VIP, Conduct/Civilization mapping, excluded Olympia fields, and command registration compatibility.

Do not do in this phase:
- Do not change the visible /me dashboard journey.
- Do not add the governor selector UI.
- Do not build the final PNG dashboard renderer.
- Do not add /me resources, /me materials, /me speedups, /me history, or /me inspect commands.
- Do not redirect, remove, or alter /my_stats, /myinventory, /stats player, /player_profile, /mykvkcrystaltech, or /kvk history.
- Do not change inventory report output, export schemas, or stats export semantics.
- Do not add SQL schema changes unless a blocker is found and explicitly approved.

Expected command surface impact:
No top-level command count change and no grouped subcommand count change.

Suggested validation:
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py

Add and run focused pytest coverage based on the files you touch, likely including player_self_service service/dashboard/access tests and command registration smoke tests.

Acceptance criteria:
- Governor dashboard context model exists.
- Linked governor options can be resolved for a Discord user.
- No/one/multiple governor states are represented for the future selector.
- Access is denied when a normal user requests an unlinked governor.
- Dashboard payload builds for a valid selected governor.
- Payload contains only approved initial fields and excludes Olympia.
- Payload separates self-view-only data from future inspect-safe data.
- Missing/null values are safe and predictable.
- SQL field names are validated and accurately mapped.
- Current visible /me behavior and legacy commands remain unchanged.
- Tests and validation are run or documented.
- Codex Security review is run because access/data/privacy surfaces are touched.
```
