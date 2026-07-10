# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 4 Premium Governor Dashboard Renderer

Status: ready to start after operator approval of the Phase 4 scope and visual direction.

## Copy/Paste Starter

```text
Codex, start Player Self-Service Command Centre v2 Phase 4: Premium Governor Dashboard Renderer.

Context:
Phases 1-3 are complete. Phase 3 made /me dashboard governor-first and operator smoke passed the
no-governor, single-governor, multiple-governor, Change Governor, and final dashboard-data journeys.
The current successful selected-governor presentation is a concise fallback embed. Phase 4 replaces
that primary presentation with a premium PNG card while retaining the embed as fallback.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 4 Premium Governor Dashboard Renderer.md
- docs/task_packs/archive/Player Self-Service Command Centre v2 Phase 1 Governor Dashboard Product Blueprint and Audit Report.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 2 Governor Context and Dashboard Data Foundation.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 3 Governor Selector and Dashboard Shell.md
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Use these skills:
- k98-architecture-scope
- k98-discord-command-feature
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review
- codex-security:security-scan

Approval checkpoint:
Confirm the wide premium-card visual direction, target 1180x640 benchmark (or justify an
operator-approved equivalent after prototyping), and background/asset choice before implementation.
Do not introduce unlicensed game artwork or expand this into a shared renderer framework.

Objective:
Create a dedicated Pillow-based governor dashboard renderer that consumes the existing
GovernorDashboardPayload. Make the rendered PNG the primary selected-governor response and retain
the current embed as a safe private fallback.

Architecture requirements:
- Keep authorization, registry rechecks, and payload assembly in the existing service path.
- Put deterministic Pillow rendering in player_self_service/governor_dashboard_renderer.py.
- Keep Discord files, message edits, attachments, and fallback handling in the governor dashboard
  view layer.
- Reuse core.visual_text for glyph-safe text fitting/drawing.
- Render off the event loop using the established asyncio.to_thread pattern.
- Do not couple the new renderer to KVK payloads or renderer-private helpers.

Visual contract:
- Strong governor name/ID identity.
- Self-view account type and optional VIP only from payload.self_view.
- Alliance, Civilisation, X:Y Location, Conduct Score, and freshness.
- Power, Kill Points, Highest Acclaim, Dead, Helps, and Healed in compact notation.
- Ark joined/won/win ratio, Times Named Autarch, and Times Autarch Participated.
- Safe missing values and responsive long/Unicode name fitting.
- No Olympia text, fields, icons, placeholders, or empty tiles.
- Buttons remain Discord components, not painted fake controls.

Interaction/delivery requirements:
- Preserve no/one/multiple/unavailable/denied states, Change Governor, access rechecks, author
  gating, stale/concurrent suppression, timeout behavior, and private responses.
- Clear/replace attachments on selector-to-card, card-to-selector, card-to-page, page-to-card,
  embed-to-card, denied, unavailable, setup, and fallback transitions.
- Close/reset streams on every success, failure, cancellation, timeout, and stale-render path.
- If rendering or image delivery fails, use the existing fallback embed without a second payload
  fetch or access bypass.

Do not do in this phase:
- Do not add or change data fields or SQL/DAL queries.
- Do not add /me resources, /me materials, /me speedups, /me history, or /me inspect.
- Do not alter Accounts, Reminders, Preferences, Inventory, Exports, legacy commands, export
  semantics, inventory semantics, or public /kvk history behavior.
- Do not enable inspect mode or redesign registry authority.
- Do not create a persistent image cache or broad shared renderer framework.

Expected command surface impact:
- No top-level command count change.
- No /me grouped subcommand count change.
- /me dashboard version increment for visible presentation only.

Test requirements:
- PNG bytes, stable filename, fixed dimensions
- all approved fields and no Olympia
- complete/missing/zero/very-large data
- long/Unicode governor and alliance names
- render offload, fallback, no duplicate payload fetch
- attachment replacement and file cleanup across every current transition
- stale/timeout/cancellation/concurrent suppression
- author/access/privacy and Change Governor regression
- existing /me and named legacy compatibility
- command registration/decorator/version checks
- representative complete, sparse, and long-name visual samples reviewed at desktop/mobile scale

Run focused tests selected from touched files plus:
.\.venv\Scripts\python.exe scripts/validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts/validate_deferred_items.py
.\.venv\Scripts\python.exe scripts/select_tests.py
.\.venv\Scripts\python.exe scripts/smoke_imports.py
.\.venv\Scripts\python.exe scripts/validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests

Run Codex Security review because Discord attachments/file streams, private responses,
user-controlled names, interaction transitions, and fallback delivery are in scope.
```
