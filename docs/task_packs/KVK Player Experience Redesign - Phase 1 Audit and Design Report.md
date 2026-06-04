# KVK Player Experience Redesign - Phase 1 Audit and Design Report

Date: 2026-06-03

Scope: audit/design only. No runtime code, SQL, command registration, or output behaviour changed.

Phase 2A completion update: admin/operator KVK commands have now moved from `/kvk ...` to
`/kvk_admin ...` in PR #140. The collision identified by this audit is resolved, and `/kvk`
is available for the Phase 2B player scaffold.

Phase 2B completion update: the player `/kvk` scaffold is complete, merged in mirror PR #141, and
promoted to production. The active player command surface now includes `/kvk stats`,
`/kvk targets`, `/kvk history`, and `/kvk rankings type:<kvk|honor|prekvk>` while legacy flat
commands remain live during rollout.

## 1. Summary

The programme goal is sound: the current KVK player experience is valuable but fragmented across flat legacy commands, mixed modules, and inconsistent output styles. The target should be a coherent player journey around:

- `/kvk stats`
- `/kvk targets`
- `/kvk history`
- `/kvk rankings`

The key design correction from the initial programme pack was that `/kvk` already existed as an admin/operator command group in `commands/stats_cmds.py`, with subcommands such as `export_all`, `recompute`, `list_scans`, `refresh_stats_cache`, `test_export`, `test_embed`, and `window_preview`. Phase 2 could not simply add player subcommands under that `/kvk` group without mixing player and operator journeys. Phase 2A has now delivered the recommended path: `/kvk` is reserved for players, and the admin/operator commands live under `/kvk_admin`.

Approved Phase 2 direction and delivery status:

1. Split Phase 2 into Phase 2A admin collision resolution and Phase 2B player `/kvk` scaffold.
   Complete.
2. Keep all legacy flat commands live during migration. Complete through Phase 2B.
3. Include all three `/kvk rankings` modes in the Phase 2B scaffold: `kvk`, `honor`, and `prekvk`.
   Complete.
4. Preserve `/kvk stats` visibility semantics: account selection is private, but selected
   single-account stats post publicly. Complete.
5. Include Acclaim/contribution metrics in the programme once SQL source, naming, and display
   rules are validated. Still pending for a later phase.
6. Treat KVK targets service/DAL cleanup as in-programme work, not deferred out of the redesign.
   Still pending for the targets visual/service phase or a focused cleanup pack.
7. Define a KVK stats service payload dataclass before Phase 3 visual rendering. Next action.

## 2. Current Command Inventory

| Current path | Module | Role | Permission/visibility | Current dependency/output | Future disposition |
|---|---|---|---|---|---|
| `/mykvkstats` | `commands/stats_cmds.py` | Player KVK stats | `channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=True)`; selector ephemeral, single-account result posts publicly | `governor_account_service`, `load_last_kvk_map`, `load_stat_row`, `build_stats_embed`, `MyKVKStatsSelectView`; embed plus optional file | Map to `/kvk stats`; keep legacy alias during rollout. |
| `/mykvktargets` | `commands/telemetry_cmds.py` | Player KVK targets | `channel_only(KVK_TARGET_CHANNEL_ID, admin_override=True)`; `only_me` option controls visibility | `run_target_lookup`, `make_kvk_targets_view`, `target_utils`, `targets_sql_cache`, `build_kvk_targets_embed`; embed/view | Map to `/kvk targets`; preserve manual governor ID option. |
| `/mykvkhistory` | `commands/stats_cmds.py` | Player KVK history | `channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=False)`; user-selectable `ephemeral` default false | `kvk_history_service`, `KVKHistoryView`, `kvk_history_utils`; chart/table images and CSV export | Map to `/kvk history`; preserve table-first accessibility. |
| `/kvk_rankings` | `commands/stats_cmds.py` | Public KVK ranking | `channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=True)`; public | `load_stat_cache`, `KVKRankingView`, `build_kvkrankings_embed`; paginated embed | Map to `/kvk rankings type:kvk`; keep legacy path. |
| `/honor_rankings` | `commands/stats_cmds.py` | Public honor ranking | `channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=False)`; public | `get_latest_honor_top`, `HonorRankingView`, `build_honor_rankings_embed`; paginated embed/buttons | Map to `/kvk rankings type:honor` after parity tests. |
| `/prekvk report` | `commands/prekvk_cmds.py` | Player/public PreKvK report | Public command-level access; currently defers ephemerally then posts report to channel when possible | `prekvk.report_service`, `PreKvkReportView`, `render_prekvk_report`; generated PNG with controls | Map to `/kvk rankings type:prekvk` in Phase 2B; keep legacy path. |
| `/mygovernorid` | `commands/telemetry_cmds.py` | Player lookup/support | Public command-level access; ephemeral | `lookup_governor_id`, autocomplete, fuzzy select, post-lookup actions | Support journey, not core `/kvk`; link from empty-state actions. |
| `/my_stats` | `commands/stats_cmds.py` | Broader player stats | `channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=True)`; ephemeral | `get_stats_payload`, `build_embeds`, `SliceButtons`; embeds/charts | Do not fold wholesale into `/kvk stats`; use only relevant KVK facts. |
| `/my_stats_export` | `commands/stats_cmds.py` | Personal stats export | Public command-level access; ephemeral | `stats_export_service.build_personal_stats_export`; downloadable file | Out of KVK player core; possible future `/stats export`. |
| `/player_profile` | `commands/telemetry_cmds.py` | Leadership profile lookup | Admin/leadership allowed channels; ephemeral command ack, posts profile through service | `profile_lookup_service`, `player_profile_flow`, profile card file | Do not include in Phase 2 player `/kvk`; possible later `/kvk profile` only after approval. |
| `/stats player` | `commands/stats_cmds.py` | Leadership player stats | Admin/leadership decorator; ephemeral | `build_player_profile_embed`/stats view path | Preserve as leadership surface. |
| `/mykvkcrystaltech` | `commands/telemetry_cmds.py` | Player KVK CrystalTech | CrystalTech channel decorator; default private | `run_crystaltech_flow_service`; guided view | Adjacent KVK journey, but out of initial `/kvk` core. |

## 3. Admin/Operator Command Audit

Historical finding before Phase 2A: `/kvk` was an admin/operator group in `commands/stats_cmds.py`:

- `/kvk test_export`
- `/kvk refresh_stats_cache`
- `/kvk export_all`
- `/kvk recompute`
- `/kvk list_scans`
- `/kvk test_embed`
- `/kvk window_preview`

These commands use `@is_admin_and_notify_channel()`, `@safe_command`, `@versioned()`, and `@track_usage()`. They are operational, SQL/data/export-facing, and should not share the final player `/kvk` group.

Delivered admin separation:

- Current operator commands moved to `/kvk_admin ...` in Phase 2A.
- Old `/kvk ...` admin paths were removed from the active command surface by approval.
- Player `/kvk stats` and admin `/kvk_admin recompute` are now separated before the Phase 2B scaffold.

Command-surface governance:

- `/kvk` remains reserved for the player group.
- `/kvk_admin` is now an approved top-level command group.
- `APPROVED_TOP_LEVEL_COMMANDS`, the canonical command reference, command inventory expectations, smoke tests, and operator rollout notes were updated in Phase 2A.

## 4. Player Journey Audit

Current journey gaps:

- Personal KVK performance lives at `/mykvkstats`, while broader stats live at `/my_stats`.
- Targets live in a different module and channel path at `/mykvktargets`.
- History is another flat command, with separate visibility defaults.
- KVK, honor, and PreKvK rankings are split across `/kvk_rankings`, `/honor_rankings`, and `/prekvk report`.
- Governor lookup is useful but disconnected from KVK empty states and account switching.

Target journeys:

- Player asks "How am I doing?" -> `/kvk stats`, with account selector, scan freshness, KVK rank, KP/kills, power, deads, healed/DKP where approved, and navigation buttons to targets/history/rankings.
- Player asks "What do I need to do?" -> `/kvk targets`, with explicit active target state, completion/progress, remaining work, and clear empty-state explanations.
- Player asks "How have I done over time?" -> `/kvk history`, preserving chart/table output and adding links back to stats/targets.
- Player asks "Where do I rank?" -> `/kvk rankings type:<kvk|honor|prekvk>`, initially embed/image parity with existing ranking views.
- Player has no linked account or unknown ID -> use `/mygovernorid`/registration actions rather than inventing a new lookup flow in Phase 2.

## 5. Output and Visual Audit

Current output styles:

- `/mykvkstats`: legacy Discord embeds from `build_stats_embed`, optional attached file, public result after private selector.
- `/mykvktargets`: embed/view built by `targets_embed` and `kvk_ui`, with account picker and fallback actions.
- `/mykvkhistory`: richer chart/table image flow via `KVKHistoryView` and `kvk_history_utils`.
- `/kvk_rankings` and `/honor_rankings`: paginated embeds and views.
- `/prekvk report`: generated PNG renderer (`prekvk/report_image_renderer.py`) with sort and top-N controls.
- Inventory reports: generated image renderer (`inventory/report_image_renderer.py`) with reusable patterns for header, stat panels, compact numbers, progress/graphs, avatar support, and deterministic byte output.
- Player profile: sends a generated card attachment and adds a link button to open the full card.

Visual direction:

- Phase 2 should remain output-parity first.
- Phase 3 should introduce a KVK card renderer with primitives inspired by inventory and PreKvK, not copied wholesale.
- The first card should be `/kvk stats`; it has the clearest hero metrics and strongest need for visual hierarchy.
- `/kvk history` should remain table/chart-first until a generated timeline card is clearly better than the existing accessible table.
- Rankings should stay embed/view-first until unified filters and pagination are stable.

Reusable visual primitives to define in Phase 3:

- KVK card payload model independent of Discord types.
- Card theme/background provider.
- Governor identity block.
- Metric tile.
- Progress bar.
- Rank badge.
- Scan freshness footer.
- Warning/disclaimer ribbon.
- Deterministic test mode for fonts, colours, filenames, and image bytes.

## 6. Metric and Terminology Review

Approved/current terminology that can be used if backed by existing payloads:

- KVK rank
- KP / kill points gain
- kills
- deads
- healed troops
- power / power delta
- DKP
- honor
- PreKvK points/stage points
- target completion/progress
- scan freshness

Terms requiring explicit approval before player-facing display:

- "KP loss" unless the source and semantics are validated.
- "tanking score" or any equivalent judgement label.
- "playstyle" labels.
- "on track" predictive modelling if it depends on scan cadence or assumptions.
- "contribution" or "acclaim" until the source and label are validated. Approval note: Acclaim/contribution should be included in this programme, with player-facing terminology favouring `Acclaim` / `acclaim_gain` rather than raw contribution wording.

KVK_ALL source-rule implications:

- Phase 10 corrected recompute precedence where Full Data v2 diff fields could be zero while cumulative endpoints moved. Later visual cards must trust the recomputed, validated output contract rather than recomputing player metrics in the renderer.
- Phase 11 is about output contract polish for Acclaim. For this programme, include Acclaim/contribution only after validating the bot-side source, label, and allowed display contexts against SQL and current KVK_ALL decisions.

## 7. SQL/DAL/Service Dependency Map

Bot-side dependencies found:

- Personal stats/cache: `player_stats_cache.py`, `utils.load_stat_cache`, `utils.load_stat_row`, `stats_cache_helpers.load_last_kvk_map`, `stats_service.get_stats_payload`.
- Personal KVK stats rendering: `embed_utils.build_stats_embed`, `ui/views/kvk_personal_views.py`.
- Targets: `target_utils.py`, `targets_sql_cache.get_targets_for_governor`, `targets_embed.build_kvk_targets_embed`, `kvk_state.get_kvk_context_today`.
- History: `services.kvk_history_service`, `kvk_history_utils.py`, `ui/views/kvk_history_view.py`, `kvk/dal/kvk_history_dal.py`.
- Rankings: `build_KVKrankings_embed.py`, `ui/views/stats_views.py`, `stats_alerts.honors`, `honor_rankings_view.py`.
- PreKvK report: `prekvk/report_service.py`, `prekvk/dal/report_dal.py`, `prekvk/report_image_renderer.py`, `ui/views/prekvk_report_views.py`.
- Admin KVK: `kvk/services/kvk_admin_service.py`, `kvk/dal/kvk_admin_dal.py`, `gsheet_module.py`.

SQL repo objects and patterns validated by search:

- Stats/current player data: `dbo.STATS_FOR_UPLOAD`, `dbo.SP_Stats_for_Upload`, `dbo.ALL_STATS_FOR_DASHBAORD`, `dbo.ALL_STATS_FOR_DASHBOARD`, `dbo.EXCEL_FOR_KVK_<N>`, `dbo.EXCEL_FOR_DASHBOARD`, `dbo.EXCEL_FOR_CURRENT_KVK`.
- Targets: `dbo.CURRENT_TARGETS`, `dbo.EXCEL_EXPORT_KVK_TARGETS_<N>`, `dbo.EXCEL_OUTPUT_KVK_TARGETS_<N>`, `dbo.EXEMPT_FROM_STATS`.
- KVK modern pipeline: `KVK.KVK_Scan`, `KVK.KVK_AllPlayers_Raw`, `KVK.sp_KVK_Recompute_Windows`, `KVK.vw_FightingDataset`.
- Registry/lookup: `dbo.DiscordGovernorRegistry`, `dbo.ALL_GOVS`, `dbo.ALL_GOVS_NAMES`, `dbo.vw_All_Governors_Clean`.
- PreKvK/honor: SQL repo contains PreKvK and honor-related objects referenced by importer/reporting flows; detailed object-by-object validation should happen in Phase 5 before unifying rankings.

Boundary findings:

- Phase 2B reused existing command/service/view functions for the delivered scaffold, but many
  current player flows still call utility modules directly from command handlers.
- `player_stats_cache.py` still contains embedded SQL and dynamic per-KVK table naming. It is a cache/data module rather than a command/view, so this is not a command-layer blocker, but Phase 3+ should avoid adding more renderer or command dependency on this shape.
- `target_utils.py` contains SQL-backed lookup/fallback logic and Discord response helpers in one module. This cleanup is now in-programme: create a KVK targets service payload contract and DAL boundary before modern target rendering.

## 8. Image Generation Feasibility Review

Feasible with existing stack:

- Pillow is already used for inventory and PreKvK report PNGs.
- Discord attachment patterns are already tested in inventory, PreKvK, KVK history, and player profile.
- Existing renderers produce `BytesIO` payloads suitable for deterministic unit tests.
- Existing views already handle refresh, controls, timeout disabling, and image attachment replacement.

Design constraints for KVK cards:

- Rendering should run in `asyncio.to_thread` from Discord views/commands.
- Card renderers must accept service payload dataclasses and must not fetch SQL or use Discord types.
- Fallback to embed output is required if rendering fails.
- Font fallback should cover non-ASCII governor names, borrowing from PreKvK renderer where needed.
- Tests should assert payload shape, filename, non-empty PNG bytes, and key renderer branches, not pixel-perfect screenshots by default.

Renderer recommendation:

- Use Pillow for Phase 3 unless the desired design requires browser-grade CSS layout, responsive typography, or HTML-to-image reuse for the future website.
- Pillow is the best near-term fit because it is already in the repo, deterministic under tests, easy to run off-thread, and avoids adding a headless browser/runtime dependency to the Discord bot.
- Consider a later HTML/CSS-to-image renderer only if KD98 webapp card components are built first and the bot should render the exact same component. That path is more visually flexible, but it adds browser/runtime packaging, screenshot determinism, font-loading, and operational complexity.
- SVG-to-PNG is attractive for simple badges and vector primitives, but less convenient for avatar compositing, dynamic tables, and rich metric layouts unless paired with another rasterization dependency.

## 9. Target Command Model

Recommended player group:

```text
/kvk stats [governor_id?] [private?]
/kvk targets [governor_id?] [private?]
/kvk history [governor_id?] [private?]
/kvk rankings [type: kvk|honor|prekvk] [sort?] [limit?]
```

Delivered admin/operator model:

```text
/kvk_admin export_all
/kvk_admin recompute
/kvk_admin list_scans
/kvk_admin refresh_stats_cache
/kvk_admin window_preview
/kvk_admin test_export
/kvk_admin test_embed
```

Phase 2A chose and implemented `/kvk_admin` before Phase 2B modifies `/kvk`.

## 10. Migration and Deprecation Plan

1. Complete: command-surface ownership approved as player `/kvk` plus admin `/kvk_admin`.
2. Complete: admin command paths moved to `/kvk_admin`; old `/kvk ...` admin paths removed by approval.
3. Complete: command registration validation, canonical command reference, command inventory tests, and smoke tests updated for `/kvk_admin`.
4. Add player `/kvk` subcommands with parity output and old-command reuse.
5. Soft-launch with player announcement listing old and new paths.
6. Monitor usage through command usage logs.
7. Deprecate flat commands with redirect/help responses after approval.
8. Remove old flat paths only after usage review and operator sign-off.

Legacy commands to keep live through at least Phase 5:

- `/mykvkstats`
- `/mykvktargets`
- `/mykvkhistory`
- `/kvk_rankings`
- `/honor_rankings`
- `/prekvk report`

## 11. Phase 2 Recommendation

Phase 2 is split:

Phase 2A: admin collision resolution. Complete in PR #140.

- Moved current admin/operator `/kvk` commands away from the player `/kvk` surface.
- Preserved permissions, channel restrictions, usage tracking, command cache behaviour, and existing service/DAL ownership.
- Documented that old `/kvk ...` operator paths were removed from the active command surface.

Phase 2B: player `/kvk` scaffold.

- Add `/kvk stats`, `/kvk targets`, `/kvk history`, and `/kvk rankings`.
- `/kvk rankings` includes `type:kvk`, `type:honor`, and `type:prekvk` from the first scaffold.
- `/kvk stats` keeps private account selection and public selected single-account stat posting.
- Reuse existing renderers/views/services for output parity where safe.
- Start KVK targets service/DAL payload cleanup as part of the programme path, but avoid visual-card work until later phases.

## 12. Test Strategy

Phase 1 documentation-only validation:

- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`

Phase 2 focused tests:

- Command registration and inventory:
  - `tests/test_validate_command_registration.py`
  - `tests/test_command_inventory.py`
  - `tests/test_command_registration_smoke.py`
- KVK stats parity:
  - `tests/test_mykvkstats.py`
  - `tests/test_kvk_personal_views.py`
  - `tests/test_stats_service.py`
- Targets parity:
  - `tests/test_mykvktargets.py`
  - `tests/test_kvk_ui_rebuild_options.py`
  - relevant target/embed tests if present
- History parity:
  - `tests/test_kvk_history_offload_and_utils.py`
  - `tests/test_kvk_history_view.py` if present or add focused coverage
- Rankings:
  - `tests/test_build_kvkrankings_embed.py`
  - `tests/test_kvkrankingview.py`
  - `tests/test_honor_rankings_view.py`
  - `tests/test_prekvk_report_command.py`
  - `tests/test_prekvk_report_views.py`
- Admin migration:
  - `tests/test_stats_cmds.py`
  - `tests/test_kvk_admin_service.py`
  - command permission/registration tests

Phase 3 visual-card tests:

- Renderer returns PNG bytes and deterministic filename.
- Empty/invalid payload fallback.
- Long governor names and non-ASCII names.
- Metric tile formatting and missing metric handling.
- Command/view fallback to embeds if renderer fails.

Codex Security:

- Skip is acceptable for this Phase 1 documentation artifact.
- Required for Phase 2+ because command permissions, Discord interactions, SQL-backed outputs, and user-controlled options are touched.

## 13. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| `/kvk` already means admin controls | High | Resolve admin surface before player scaffold; avoid mixed player/operator group. |
| Player confusion from old and new commands | Medium | Parallel migration, announcement, and redirects only after approval. |
| Metric semantics overpromise | High | Use approved metric names only; no playstyle/tanking/on-track/acclaim labels without source approval. |
| Generated image performance | Medium | Phase 3 render in worker thread, add embed fallback, test byte output. |
| Ranking unification changes public visibility | Medium | Preserve legacy visibility defaults in Phase 2; review before changing public/private behaviour. |
| SQL result-shape drift | High | Validate object contracts against SQL repo before each implementation phase. |
| View restart/persistence assumptions | Medium | Keep Phase 2 views non-persistent unless explicitly designed; test timeout/stale interactions. |

## 14. Resolved Finding And Remaining Programme Work

Resolved Phase 2A finding:

- Area: `commands/stats_cmds.py` `/kvk` admin group and future KVK player commands
- Type: architecture
- Resolution: Admin/operator commands moved from `/kvk ...` to `/kvk_admin ...` in PR #140.
- Result: The player `/kvk` surface is available for Phase 2B, and command registration validation, canonical command reference, smoke tests, and operator documentation now reflect `/kvk_admin`.

The previous targets and personal stats payload findings are now programme work rather than deferred optimisations:

- KVK targets: create a service payload contract and DAL boundary before the modern targets output.
- Personal KVK stats: define a Phase 3 service payload dataclass that normalizes governor identity, scan freshness, KVK rank, metric deltas, targets, Acclaim/contribution where approved, and warning states before rendering.

## 15. Approval Questions

1. Resolved: Phase 2A uses `/kvk_admin ...` for the admin/operator commands.
2. For Acclaim/contribution, which exact SQL output object should be treated as the player-card source of truth?
3. Should Phase 2B expose ranking type as a required slash option, a defaulted slash option, or an interactive select after `/kvk rankings`?
