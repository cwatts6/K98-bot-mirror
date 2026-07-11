# Codex Task Pack - Player Self-Service Command Centre v2 Phase 4 Premium Governor Dashboard Renderer

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 4 Premium Governor Dashboard Renderer`
- Date: `2026-07-10`
- Owner/context: Follow-on from the completed and operator-smoke-approved Phase 3 governor selector and dashboard shell.
- Task type: `Generated visual card | Discord attachment integration | fallback-safe renderer migration`
- One-pass approved: `No`
- Implementation approved: `Yes - visual direction approved and operator smoke accepted`
- Status: `complete - operator smoke passed 2026-07-11`

## Implementation Record

- Operator approved the 1180x640 wide visual direction and the operator-created
  `assets/me/cards/me.png` background.
- The invoking player's Discord avatar is fetched best-effort in the Discord view layer and passed
  as optional bytes to the off-thread renderer; the payload contract is unchanged.
- Missing or invalid avatars use a KD98 medallion fallback. Render, file, and delivery failures use
  the existing embed without another payload fetch.
- Initial operator smoke confirmed the dashboard works and requested a standalone attachment for
  wider display, exact identity/metric panel alignment, blue primary navigation, an in-card
  Change Governor dropdown, and `Last Login: TBC` until its future data contract is delivered.
- Complete, sparse, long-name, CJK, and emoji samples were reviewed at original, desktop, and
  mobile scale. Focused/full automated validation passed. Final operator smoke on 2026-07-11
  exercised every linked-governor option, confirmed the author-gated Change Governor dropdown,
  and accepted the standalone card as materially larger and easier to read.

## 2. Objective

Replace the selected-governor fallback embed as the primary successful `/me dashboard` presentation
with a dedicated premium PNG governor card, while retaining that embed as the safe fallback.

Phase 4 changes presentation only. It must consume the existing renderer-independent
`GovernorDashboardPayload` and preserve the Phase 3 selector, registry authorization, access
rechecks, private response behavior, timeout handling, Change Governor journey, compatibility-page
navigation, and command surface.

## 3. Scope Confirmation / Approval Checkpoint

Before implementation, confirm:

1. The approved visual direction is a wide KD98 premium card benchmarked at `1180x640`, or an
   operator-approved equivalent if the representative prototype proves that the approved fields
   cannot remain readable at that size.
2. The visual hierarchy is governor identity first, then headline battle metrics, profile/status,
   Ark and Autarch honours, and freshness.
3. Existing repository assets may be assessed, but the implementation must not introduce
   unlicensed game artwork, logos, or copied player-card assets. A new background or material
   visual change requires operator review of the rendered prototype.
4. Phase 4 does not change data sources, add fields, or alter commands/actions.

If a materially different layout, new data field, new asset family, or shared renderer framework
is required, stop and obtain approval rather than expanding this slice.

## 4. Required Reading

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 4 Premium Governor Dashboard Renderer.md`
- `docs/task_packs/archive/Player Self-Service Command Centre v2 Phase 1 Governor Dashboard Product Blueprint and Audit Report.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 2 Governor Context and Dashboard Data Foundation.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 3 Governor Selector and Dashboard Shell.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Inspect before coding:

- `player_self_service/governor_dashboard_models.py`
- `player_self_service/governor_dashboard_service.py`
- `ui/views/player_self_service_governor_dashboard_views.py`
- `ui/views/player_self_service_views.py`
- `player_self_service/page_cards.py`
- `player_self_service/dashboard_card.py`
- `core/visual_text.py`
- `kvk/rendering/kvk_stats_card_renderer.py`
- `kvk/rendering/kvk_targets_card_renderer.py`
- `kvk/rendering/kvk_history_renderer.py`
- `tests/test_governor_dashboard_discord_views.py`
- `tests/test_player_self_service_dashboard_card.py`
- `tests/test_core_visual_text.py`

No SQL schema or query change is expected. If implementation appears to require one, stop and
scope it separately against `C:\K98-bot-SQL-Server`.

## 5. Delivered Baseline

Phase 2 provides the typed renderer-independent payload and self/inspect privacy separation.
Phase 3 provides:

- private no/one/multiple/unavailable/denied journey handling
- direct one-governor opening and multi-governor selection
- access re-resolution before payload fetch
- Change Governor and compatibility-page navigation
- safe stale, foreign, forged, timeout, and concurrent-transition handling
- an approved fallback embed with all current player-facing fields
- operator-smoke-approved data mapping, compact values, VIP wording, location, and freshness

Phase 4 must not move these responsibilities into the renderer.

## 6. Architecture Direction

Recommended placement:

- Create `player_self_service/governor_dashboard_renderer.py` for Pillow rendering and a small
  rendered-card result contract (`filename`, `image_bytes`, dimensions as appropriate).
- Keep payload assembly and authorization in the existing service.
- Keep Discord file creation, edit/fallback behavior, message/view references, and attachment
  replacement in `ui/views/player_self_service_governor_dashboard_views.py`.
- Reuse `core.visual_text` for glyph-safe font selection, fitting, measurement, and drawing.
- Reuse proven KVK visual ideas, but do not couple the governor renderer to KVK payloads, themes,
  mode selection, or renderer-private helpers.
- Run Pillow rendering off the event loop using the repository's established `asyncio.to_thread`
  pattern.

The renderer must be deterministic from the payload, perform no SQL/network/Discord IO, and own no
authorization or navigation decisions.

## 7. In Scope

- Dedicated premium governor dashboard PNG renderer.
- Fixed, documented output dimensions and stable filename.
- Strong identity treatment for governor name and ID.
- Self-view account type and optional VIP presentation from `payload.self_view` only.
- Alliance, Civilisation, `X:Y` Location, Conduct Score, and freshness.
- Power, Kill Points, Highest Acclaim, Dead, Helps, and Healed using compact player-facing values.
- Ark joined, Ark won, guarded win ratio, Times Named Autarch, and Times Autarch Participated.
- Safe and visually intentional missing-value states.
- Responsive font fitting/truncation for long and Unicode governor/alliance names.
- Primary selected-governor card delivery with the existing embed as fallback.
- Attachment replacement/clearing for selector-to-card, card-to-selector, card-to-page,
  page-to-card, card refresh, fallback embed, denied, unavailable, and setup transitions.
- Resource cleanup when a render becomes stale, times out, is replaced, or fails to send/edit.
- Preserve Change Governor and all existing compatibility buttons.
- Increment `/me dashboard` command version for the visible presentation change.
- Representative local visual samples and Discord-like desktop/mobile review.
- Focused renderer, Discord view, command-version, and compatibility tests.

## 8. Explicitly Out of Scope

- No new dashboard data fields or data-source corrections.
- No Olympia field, label, placeholder, icon, or empty tile.
- No `/me resources`, `/me materials`, `/me speedups`, `/me history`, or `/me inspect`.
- No direct inventory action, export semantic, KVK history, or inspect implementation.
- No changes to Accounts, Reminders, Preferences, Inventory, or Exports behavior.
- No changes to `/my_stats`, `/myinventory`, `/stats player`, `/player_profile`,
  `/mykvkcrystaltech`, or `/kvk history`.
- No SQL schema, view, index, table, stored procedure, or DAL query change.
- No registry ownership-policy change or unlinked inspect access.
- No broad KVK/inventory/player-card renderer framework extraction.
- No website/API work or persistent rendered-image cache.

## 9. Visual Contract

Required zones:

1. **Hero identity** - governor name is dominant; ID, alliance, account type/VIP, and freshness are
   immediately discoverable.
2. **Battle metrics** - Power, Kill Points, Highest Acclaim, Dead, Helps, and Healed use large,
   short values with unambiguous labels.
3. **Profile/status** - Civilisation, Location, and Conduct Score remain readable without competing
   with headline metrics.
4. **Ark and honours** - joined, won, ratio, Named Autarch, and Autarch Participated are grouped
   coherently.
5. **Confidence/footer** - data freshness and private self-view status are clear but not dominant.

Presentation rules:

- Prefer fixed zones, concise labels, contrast, and whitespace over paragraph text.
- Do not encode meaning only by colour.
- Preserve `N/A`, `Not set`, and no-recent-scan meaning consistently with the fallback embed.
- Sanitize/fit user-controlled names and never render raw Discord mention markup as actionable
  content.
- The card must remain legible when Discord scales it on desktop and mobile.
- Buttons remain Discord components; do not paint fake interactive controls into the card.

## 10. Discord Delivery and Fallback Contract

Selected-governor success flow:

```text
revalidated selected context
-> build existing GovernorDashboardPayload
-> render PNG off-thread
-> create Discord file
-> edit original private message in place with card + existing view
-> clear superseded attachments
```

Fallback rules:

- If render, file creation, or image delivery fails, use the current approved dashboard embed in
  the same private message where possible.
- A fallback must not trigger a second payload fetch or bypass the access check.
- Stale/expired/replaced transitions must not edit the message after the current transition loses
  ownership.
- Close/reset file streams on every success, failure, cancellation, stale suppression, and fallback
  path.
- Setup, selector, denied, unavailable, and terminal error states remain concise embeds and remove
  any previous governor-card attachment.

## 11. Command and Data Impact

Expected command surface:

- Top-level command count: unchanged.
- `/me` grouped subcommand count: unchanged.
- `/me dashboard`: version increment only.
- All other command registrations, decorators, permissions, tracking, and semantics: unchanged.

Expected data impact:

- Existing Phase 2/3 payload contract only.
- No SQL or DAL changes.
- No cache, persistence, startup, scheduler, or rehydration changes.

## 12. Likely Files

Likely create:

- `player_self_service/governor_dashboard_renderer.py`
- `tests/test_governor_dashboard_renderer.py`

Likely modify:

- `ui/views/player_self_service_governor_dashboard_views.py`
- `player_self_service/__init__.py` only if a clean renderer export is useful
- `commands/me_cmds.py` for the command version only
- `tests/test_governor_dashboard_discord_views.py`
- `tests/test_me_cmds.py`
- `tests/test_player_self_service_views.py` where attachment-transition coverage belongs
- programme, briefing, command, task-pack, and deferred documentation after delivery

Assets may be reused or added only after the visual approval checkpoint and license/provenance
review.

## 13. Test Requirements

Renderer tests:

- successful PNG output, stable filename, fixed dimensions, and non-empty bytes
- all approved field groups represented; no Olympia text or placeholder
- compact large-number formatting and guarded Ark zero-joined handling
- missing VIP, missing metrics, missing location, and missing freshness remain readable
- very long governor/alliance names fit their bounds
- Unicode and special-character names render without crashing or unsafe mention behavior
- negative, zero, and very large numeric values do not overflow their zones
- self-view-only account type/VIP are not synthesized when `payload.self_view` is absent

Discord/view tests:

- selected state prefers the rendered card and retains the existing author-gated view
- render exception and send/edit failure fall back to the existing private embed
- no second payload fetch during fallback
- selector/setup/denied/unavailable/error transitions clear old attachments
- card-to-card, card-to-selector, card-to-page, page-to-card, and embed-to-card edits replace the
  previous attachment correctly
- stale, timeout, cancellation, and concurrent-transition suppression close file streams and do
  not edit a superseded message
- Change Governor, navigation, access rechecks, foreign-user denial, and timeout behavior remain
  unchanged
- command counts/decorators remain stable and `/me dashboard` version is updated
- existing `/me` and named legacy commands remain compatible

Visual QA:

- Render representative complete, sparse/missing-data, and long/Unicode-name samples.
- Inspect the original images plus Discord-like desktop and mobile scaled previews.
- Record operator approval or specific correction feedback before completion.

## 14. Validation

Use `k98-test-selection` after the touched-file set is known. Expected focused commands include:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_governor_dashboard_renderer.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_governor_dashboard_discord_views.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_player_self_service_views.py tests/test_me_cmds.py
```

Required repository gates:

```powershell
.\.venv\Scripts\python.exe scripts/validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts/validate_deferred_items.py
.\.venv\Scripts\python.exe scripts/select_tests.py
.\.venv\Scripts\python.exe scripts/smoke_imports.py
.\.venv\Scripts\python.exe scripts/validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
```

Run Codex Security review because Discord attachments/file streams, private responses,
user-controlled names, interaction transitions, and fallback delivery are in scope. No SQL security
review is required unless the approved scope changes.

## 15. Manual Discord Smoke Test

1. One linked governor opens the premium card directly and privately.
2. Multiple linked governors select and switch cards in the same private message.
3. Change Governor clears the card and shows the selector without a stale attachment.
4. Returning from Accounts, Reminders, Preferences, Inventory, and Exports restores the selected
   governor card without another selector step and without mixed old/new visuals.
5. No linked governor still shows the setup embed with Accounts as primary action.
6. Long/Unicode governor and alliance names remain readable.
7. Missing VIP/data/location/freshness states remain deliberate and readable.
8. Render/delivery failure uses the fallback embed privately.
9. Timeout disables controls gracefully without `This interaction failed`.
10. Foreign, forged, stale, and concurrent interactions remain safely rejected.
11. Desktop and mobile previews preserve the intended hierarchy.
12. Existing `/me` and named legacy commands remain unchanged.

## 16. Acceptance Criteria

- [x] Operator confirms the visual direction and prototype/background choice.
- [x] The selected governor is presented primarily as a premium PNG card.
- [x] The existing embed remains a tested safe fallback.
- [x] Every approved Phase 3 field is represented safely and Olympia is completely absent.
- [x] Long, Unicode, missing, zero, and large values remain readable.
- [x] Rendering is off the event loop and performs no IO outside local asset/font reads.
- [x] Attachment lifecycle is correct across every current `/me` transition.
- [x] File streams are released on success, failure, cancellation, timeout, and stale suppression.
- [x] Selector, access, privacy, navigation, and timeout contracts are unchanged.
- [x] No command-count, SQL, DAL, export, inventory, history, or inspect change is introduced.
- [x] Focused/full validation, visual QA, operator smoke, and security-focused review are recorded.
- [x] Programme, briefing, command, task-pack, starter, and deferred documents reflect delivery.

## 17. Delivery Output

Provide:

1. Visual and user-journey summary.
2. File and asset manifest with asset provenance.
3. Renderer architecture and payload boundary confirmation.
4. Attachment/fallback/resource-cleanup behavior.
5. Command/data/SQL impact statement.
6. Rendered desktop/mobile samples and operator feedback.
7. Focused and full automated validation results.
8. Manual Discord smoke results.
9. Codex Security status.
10. Deferred findings and Phase 5 handoff notes.
