# Player Self-Service Command Centre v2 Phase 1 Governor Dashboard Product Blueprint and Audit Report

Status: Phase 1 audit/design complete and archived after the Phase 2 foundation was delivered. No runtime command, SQL, renderer, redirect, or permission changes are included in this slice.

Historical sequencing note: the active programme pack supersedes this audit's provisional later
phase numbering. Phases 2-4 have since completed. The authoritative remaining order is Phase 5A
direct inventory reports, Phase 5B existing `/me` page presentation alignment, Phase 6 Export Stats
integration, Phase 7 private `/me history`, Phase 8 required admin/leadership `/me inspect`, and
Phase 9 usage-led migration review.

## 1. Summary

`/me` should become the governor-first daily command centre. The safest target journey is:

1. Player opens the `/me` entry point.
2. The bot privately resolves the player's registered governors.
3. The player selects a governor, or the bot opens the main/only governor directly.
4. A premium governor dashboard opens.
5. Governor-specific actions preserve the selected governor until the player backs out or changes governor.

The current `/me` implementation is a Discord-user-level setup hub. It is private, useful, and already provides the correct foundation for account/reminder/preference/export/inventory workflows, but it is not yet a governor dashboard. Phase 2 should add a governor-context service and selector before any command redirects or legacy removals are considered.

The visual direction should be treated as a first-class workstream. The current `/me` card is large in raw pixels, but it reads smaller and more compressed than the `/kvk` cards because its information hierarchy, metric blocks, and text density are setup-oriented. The new dashboard should use the premium KVK-style visual grammar: strong governor identity, large metric values, fixed zones, fewer explanatory paragraphs, and deliberate mobile-preview testing.

## 2. File Manifest

Phase 1 report added:

- `docs/task_packs/Player Self-Service Command Centre v2 Phase 1 Governor Dashboard Product Blueprint and Audit Report.md`

Audited primary Python surfaces:

- `commands/me_cmds.py`
- `ui/views/player_self_service_views.py`
- `player_self_service/service.py`
- `player_self_service/page_cards.py`
- `player_self_service/dashboard_card.py`
- `commands/inventory_cmds.py`
- `ui/views/inventory_report_views.py`
- `inventory/reporting_service.py`
- `inventory/dal/inventory_reporting_dal.py`
- `commands/stats_cmds.py`
- `embed_my_stats.py`
- `stats_service.py`
- `commands/telemetry_cmds.py`
- `commands/player_profile_flow.py`
- `services/profile_lookup_service.py`
- `embed_player_profile.py`
- `commands/kvk_cmds.py`
- `services/kvk_history_service.py`
- `commands/kvk_history_card_posting.py`
- `kvk/dal/kvk_history_dal.py`
- `kvk/rendering/kvk_stats_card_renderer.py`
- `kvk/rendering/kvk_targets_card_renderer.py`
- `kvk/rendering/kvk_history_renderer.py`

Audited reference/task documents:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - player self service v2 phase1 governor dashboard task pack.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

SQL validation source consulted:

- `C:\K98-bot-SQL-Server`

No runtime files or SQL files were changed.

## 3. Current `/me` Command Map

Owner module: `commands/me_cmds.py`

`/me` is registered as a `discord.SlashCommandGroup` with these subcommands:

| Command | Current role | Visibility | Core owner chain |
| --- | --- | --- | --- |
| `/me dashboard` | Private account/reminder/preference setup overview | Private response | `me_cmds.py` -> `send_player_self_service_page(PAGE_DASHBOARD)` |
| `/me accounts` | Linked governor/account management | Private response | `me_cmds.py` -> `player_self_service_views.py` |
| `/me reminders` | Reminder status/navigation | Private response | `me_cmds.py` -> `player_self_service_views.py` |
| `/me preferences` | User-level profile/export/inventory preferences | Private response | `me_cmds.py` -> `player_self_service_views.py` |
| `/me inventory` | Inventory summary and report launcher | Private response, report visibility later follows preference | `me_cmds.py` -> `player_self_service_views.py` -> inventory report flow |
| `/me exports` | Export launch page | Private response | `me_cmds.py` -> `player_self_service_views.py` |

Common decorators:

- `@versioned`
- `@safe_command`
- `@track_usage`

Current `/me` responses are safely deferred privately through `safe_defer(ctx, ephemeral=True)`. The view is author-gated through `interaction_check`, disables controls on timeout, and uses row-based Discord buttons for page navigation and page-specific actions.

The current dashboard does not select or preserve governor context. Its service payload is keyed by Discord user and includes account summary, reminder status, inventory/export preferences, VIP inventory profile status, and latest inventory snapshot summary.

## 4. Legacy and Adjacent Command Audit

| Path | Current behavior | Product finding |
| --- | --- | --- |
| `/my_stats` | Flat command, KVK-player-stats channel gated with admin override, private output, registered governor selection, legacy embed/chart renderer. | Preserve for compatibility. Its summary data belongs in the future governor dashboard, but redirects/removal require usage review and separate approval. |
| `/stats player` | Admin/leadership stats lookup by governor ID or fuzzy name, private output. | Leadership/admin workflow. Candidate source behavior for `/me inspect`, not normal player journey. |
| `/player_profile` | Admin/leadership profile lookup in allowed channels; sends profile to target channel and privately acknowledges. Includes Discord identity linkage. | Do not reuse directly for player `/me` or inspect dashboard. Use only as a reference for leadership needs and profile fields. |
| `/myinventory` | Private governor picker; report visibility then follows user inventory preference. Supports all/resources/speedups/materials reports and exports. | Preserve. Future `/me resources`, `/me materials`, and `/me speedups` should reuse this report machinery. |
| `/mykvkcrystaltech` | Specialist CrystalTech workflow, channel-gated, default private, registered governor picker/manual governor ID. | Keep outside v2 unless the operator makes a product decision to fold CrystalTech into `/me`. |
| `/kvk history` | Modern KVK-history card flow, KVK-player-stats channel gated, public output in current KVK journey. | Personal retrospective content fits `/me`, but the existing public KVK path should remain canonical until a private `/me` entry point proves out. |
| `/kvk stats` | Current/live KVK stats workflow. | Keep under `/kvk`; dashboard may link only to personal summary equivalents. |
| `/kvk targets` | Current/live KVK target workflow. | Keep under `/kvk`; not part of governor dashboard Phase 1 scope. |
| `/kvk rankings` | KVK rankings workflow. | Keep under `/kvk`; not a self-service dashboard candidate. |

## 5. Candidate Command Classification Table

| Candidate | Classification | Phase 1 recommendation |
| --- | --- | --- |
| `/me dashboard` | Redesign candidate | Make this the governor-first dashboard entry in a later phase. |
| `/me accounts` | Preserve with copy/navigation improvements | Keep Discord-user-level. Do not make governor-specific. |
| `/me reminders` | Preserve with copy/navigation improvements | Keep Discord-user-level. |
| `/me preferences` | Preserve with copy/navigation improvements | Keep Discord-user-level, with governor-aware preference affordances only where the underlying setting is governor-specific. |
| `/me inventory` | Preserve and strengthen | Keep all-three inventory compatibility. Add direct dashboard actions later. |
| `/me exports` | Preserve as compatibility | Remove from primary dashboard journey later, but keep command/functionality. |
| Future `/me resources` | Add `/me` entry point while keeping existing command | Reuse inventory report resources view. |
| Future `/me materials` | Add `/me` entry point while keeping existing command | Reuse inventory report materials view. |
| Future `/me speedups` | Add `/me` entry point while keeping existing command | Reuse inventory report speedups view. |
| Future `/me inspect` | Leadership/admin workflow | Add only with explicit permission and privacy tests. |
| `/my_stats` | Future redirect/removal candidate only after separate approval | Preserve now; use as data/UX source. |
| `/stats player` | Leadership/admin workflow | Preserve now; later route leadership needs through `/me inspect`. |
| `/player_profile` | Leadership/admin workflow | Preserve now; do not use public-posting behavior in `/me inspect`. |
| `/myinventory` | Preserve as-is | Keep even after direct `/me` inventory actions are added. |
| `/mykvkcrystaltech` | Specialist workflow outside v2 | Preserve outside dashboard. |
| `/kvk history` | Add `/me` entry point while keeping existing command | Recommend private `/me` entry later; keep `/kvk history` public/channel-gated. |
| Legacy redirected personal commands | Future removal candidates only after separate approval | Do not change during v2 Phase 1. |

## 6. Governor-First Journey Blueprint

The slash-command registration shape means the current directly invokable entry is `/me dashboard`, not bare `/me`. Product copy can call the experience `/me`, but implementation should respect Discord command constraints unless the command tree is intentionally restructured later.

Target states:

| State | Behavior |
| --- | --- |
| No registered governors | Show a private setup card with Accounts as the primary action, plus Preferences and Reminders. Do not show empty metric panels. |
| One registered governor | Open the governor dashboard directly. Preserve a lightweight change-governor affordance only if more accounts are later linked. |
| Multiple registered governors | Show a private governor selector first. Default/main governor may be highlighted, but the user should explicitly control context. |
| Selected governor | Render the governor dashboard. Every governor-specific action receives the selected governor ID. |
| User-level page | Accounts, Reminders, and Preferences remain Discord-user-level and must not pretend to be governor-specific. |
| Back/change governor | Return to selector or dashboard without losing author gating. |
| Timeout/stale interaction | Disable controls and provide a short private retry instruction. |

Context preservation requirements:

- Store `author_id` and `governor_id` in the view state.
- Encode page/action plus governor context in structured custom IDs or validated view state.
- Reject interactions from other Discord users.
- Re-resolve access for governor-specific actions before rendering sensitive output.
- Keep selected-governor context through resources, materials, speedups, stats export, and history actions.

## 7. Dashboard Field-to-Source Matrix

| Dashboard field | Validated/current source | Contract status | Notes |
| --- | --- | --- | --- |
| Governor Name | Registry/account summary; `v_PlayerLatestStats.Governor_Name`; profile views | Available | Prefer selected linked governor display name, then latest stats fallback. |
| VIP Level | `dbo.GovernorInventoryProfile` via `inventory.profile_service.fetch_inventory_profile` | Available, player-maintained | Optional. Label as not set when absent. Confirm before showing to leadership inspect. |
| Account type | Discord-governor registry/account summary | Available, Discord-user-level | Show in normal player dashboard only. Do not leak in `/me inspect`. |
| Governor ID | Registry/account summary; stats/profile views | Available | Safe governor identifier. |
| Alliance Name | `v_PlayerLatestStats.Alliance`; `v_PlayerProfile.Alliance` | Available | Use latest stats/profile source. |
| Power | `v_PlayerLatestStats.Power`; stats window payload | Available | Use latest value for dashboard. |
| Kill Points | `v_PlayerLatestStats.KillPoints`; KVK/export aggregate sources | Available | Use latest value for dashboard. |
| Highest Acclaim | `HighestAcclaim` in KVK/export aggregate/history surfaces | Available | Historical maximum; null-safe display required. |
| Deads | `v_PlayerLatestStats.Deads` | Available | Latest value. |
| Helps | `v_PlayerLatestStats.Helps` | Available | Latest value. |
| Healed | `v_PlayerLatestStats.HealedTroops`; KVK aggregate `HealedTroopsDelta` for history | Available | Dashboard should use latest healed troop total when available. |
| Olympia fights | No confirmed SQL contract found in inspected repo | Ambiguous/unavailable | Do not implement until source is identified or added. |
| Olympia win ratio | No confirmed SQL contract found in inspected repo | Ambiguous/unavailable | Same blocker as Olympia fights. |
| Ark of Osiris | `AOOJoined`, `AOOWon` in `ALL_STATS_FOR_DASHBOARD` / `v_EXCEL_FOR_KVK_All` / stats export payload | Available | Treat as all-time/current aggregate from stats export domain unless operator wants Ark subsystem semantics. |
| Ark win ratio | Derived from `AOOWon / AOOJoined` | Available with null guard | Show `N/A` when joined is zero or null. |
| Autarch count / times named Autarch | `AutarchTimes` in KVK/export aggregate/history surfaces | Available | Label can be "Times Named Autarch". |
| Conduct Score | SQL column `Conduct` in latest/profile/KVK aggregate views | Available | Source field is `Conduct`, not `ConductScore`. UI can label "Conduct Score". |
| Civilisation | SQL column `Civilization` in KVK/export aggregate sources | Available outside latest profile | UI may label "Civilisation"; implementation must use SQL name `Civilization`. |

Recommended service contract for implementation:

- A new dashboard payload should be assembled in a service/DAL layer, not in command modules or views.
- The payload should distinguish `governor_metric` fields from `discord_user_setting` fields.
- Missing/ambiguous fields should render as `N/A` or be hidden according to product decision, not guessed.

## 8. Dashboard Action Model

Primary dashboard actions after governor selection:

| Action | Context | Recommendation |
| --- | --- | --- |
| Change Governor | User/account context | Available when multiple linked governors exist. |
| Accounts | Discord-user-level | Keep visible but separate from governor metric actions. |
| Reminders | Discord-user-level | Keep visible; do not bind to selected governor unless reminder model changes. |
| Preferences | Mixed but currently Discord-user-level | Keep visible; route to existing preferences page. |
| Resources | Selected governor | New direct action using inventory resources report view. |
| Materials | Selected governor | New direct action using inventory materials report view. |
| Speedups | Selected governor | New direct action using inventory speedups report view. |
| Inventory | Selected governor / compatibility | Keep `/me inventory` for all-three report journey. |
| KVK History | Selected governor | Recommended later as private `/me` entry point while preserving `/kvk history`. |
| Export Stats | Selected governor preferred | Move to row 3 as a green action button on the dashboard card/view. Confirm whether export should be selected-governor or all-linked-governors before implementation. |

The separate dashboard-level Exports button should leave the primary journey in the redesign, but `/me exports` and all existing export functionality must remain available for compatibility.

## 9. Inventory Split Blueprint

Future direct paths:

- `/me resources`
- `/me materials`
- `/me speedups`
- `/me inventory`

Implementation guidance for later phases:

- Reuse `InventoryReportView.RESOURCES`, `InventoryReportView.MATERIALS`, `InventoryReportView.SPEEDUPS`, and `InventoryReportView.ALL`.
- Reuse `inventory.reporting_service.build_inventory_report_payload`.
- Reuse existing inventory export controls where appropriate.
- Preserve `/myinventory` and `/me inventory` behavior.
- Direct dashboard buttons should skip the all-report picker when a governor context is already selected.
- Content redesign is not required in Phase 1. Later work should primarily refresh visual presentation to match the premium dashboard/KVK style.

## 10. Card Size and Visual Standard Recommendation

Current comparison:

| Surface | Current format | Finding |
| --- | --- | --- |
| `/me` page card | `1702x924` generated image | Large raw canvas, but visually compressed due setup-card text density and low metric hierarchy. |
| `/kvk stats` | `1180x640` premium card | Stronger metric layout, clearer hierarchy, better scannability. |
| `/kvk targets` | `1180x640` premium card | Consistent KVK visual language and fixed metric zones. |
| `/kvk history` | `1180x640` premium card family | Better suited for fast personal stat reading. |
| Inventory cards | Existing report renderers | Content is useful; visual refresh should align with new dashboard style. |

Recommendation:

- Keep the new governor dashboard as a wide premium card, using the attached dashboard screenshot as the product benchmark.
- Rebuild layout around fixed identity, metrics, activity, conduct/civilisation, and action-status zones.
- Use KVK-style metric tiles with large values, short labels, and icon/color accents.
- Avoid paragraph-heavy setup text on the governor dashboard.
- Use fixed text bounds and responsive font-fitting for long governor/alliance names.
- Test rendered previews in Discord-like desktop and mobile widths before release.
- Treat raw canvas size and perceived readability separately. A large canvas can still feel small if too much copy competes with metrics.

Preferred later renderer strategy:

- Add a dedicated governor dashboard renderer instead of extending the existing setup-page renderer too far.
- Share visual primitives with KVK/inventory renderers only after the first dashboard card proves out.
- Do not change existing `/me` card renderer behavior until the new journey is approved.

## 11. `/kvk history` Product Placement Recommendation

`/kvk history` is more personal and retrospective than most `/kvk` commands, so it has a strong product fit under `/me`. However, its current behavior is public/channel-gated and is already part of the KVK command family.

Recommendation:

- Keep `/kvk history` unchanged as the canonical public KVK history path.
- Add a private `/me` entry point later, likely a dashboard button and/or `/me history`, using selected governor context.
- Reuse `kvk_history_service` and the modern history renderer.
- Do not redirect, remove, or rename `/kvk history` until there is fresh usage evidence and explicit operator approval.

## 12. Leadership/Admin Inspect Journey Recommendation

Preferred command name: `/me inspect`

Purpose: leadership/admin inspection of a governor dashboard without mixing that workflow into the normal player journey.

Recommended behavior:

- Gate with leadership/admin permissions.
- Require either governor ID or fuzzy governor name lookup.
- Resolve ambiguous fuzzy matches through a private selector.
- Render the same governor-dashboard visual shell in `inspection_mode`.
- Default to private response.
- Audit usage through command tracking and explicit inspect telemetry.

Privacy boundary:

- Show governor/game metrics that are already appropriate for leadership inspection.
- Do not show linked Discord user private account data.
- Do not show account slot/type if it reveals the inspected player's Discord-user relationship.
- Do not show reminder settings, timezone, language, inventory visibility preference, export visibility preference, or private preference metadata.
- Be cautious with VIP until the operator confirms whether player-maintained VIP profile data is suitable for leadership inspection.

`/stats player` and `/player_profile` should remain available until `/me inspect` is implemented, tested, and separately approved as their preferred successor path.

## 13. Missed Player Self-Service Command Discovery

Additional commands considered:

| Command/surface | Finding |
| --- | --- |
| `/ark reminder_prefs` | Player self-service, but Ark-domain specific. Keep outside v2; Reminders may link to it later if product copy wants a unified reminder hub. |
| `/inventory import` | Upload workflow, not dashboard content. Keep channel-gated import path outside `/me`. |
| `/inventory_preferences` | Deprecated redirect to `/me preferences`; no new v2 work beyond compatibility monitoring. |
| `/export_inventory` | Deprecated redirect to `/me exports`; preserve. |
| `/my_stats_export` | Deprecated redirect to `/me exports`; preserve. |
| `/location player` | Leadership lookup, not player self-service. |
| `/activity top` | Leadership/reporting workflow, outside v2. |
| Account legacy redirects | Already covered by Phase 13; no Phase 1 changes. |
| Subscription/reminder legacy paths | Already represented in `/me reminders`; no Phase 1 redirect changes. |

No additional player self-service command should be pulled into Phase 2 without operator approval.

## 14. SQL/Data Contract Findings

Validated in the SQL source repo:

- `dbo.v_PlayerLatestStats` exposes latest governor stats including governor ID/name, alliance, power, kills, deads, helps, healed troops, kill points, power rank, and `Conduct`.
- `dbo.v_PlayerProfile` exposes profile-oriented latest/player fields including governor ID/name, alliance, location, status, power, city hall, kills, deads, RSS gathered, helps, power rank, and `Conduct`.
- `dbo.ALL_STATS_FOR_DASHBOARD` includes aggregate/dashboard-style fields such as `Civilization`, `HighestAcclaim`, `AOOJoined`, `AOOWon`, `Conduct`, `HealedTroopsDelta`, `KillPointsDelta`, and `AutarchTimes`.
- `dbo.v_EXCEL_FOR_KVK_All` and `dbo.v_EXCEL_FOR_KVK_Started` carry KVK/export/history fields used by current KVK history and stats workflows.
- `dbo.GovernorInventoryProfile` is the current VIP/profile preference source used by inventory profile services.
- `dbo.BotCommandUsage` exists for command usage evidence, but no live database query was run in this audit pass.

Important contract notes:

- The SQL source field is `Conduct`, not `ConductScore`.
- The SQL source field is `Civilization`; UI may label it "Civilisation".
- VIP is a player-maintained inventory profile value, not a confirmed game-imported latest-stat field.
- Olympia fights and Olympia win ratio were not confirmed in the inspected SQL contracts. They must not be guessed during implementation.
- Ark of Osiris values are available as `AOOJoined` and `AOOWon` in stats/export aggregate sources. Confirm whether product wants those aggregate stats or a separate Ark subsystem definition.

## 15. Privacy, Permission, and Channel-Gating Findings

Current safe foundations:

- `/me` pages are private and author-gated.
- `/myinventory` starts privately and only uses public output where the user has selected public inventory report visibility.
- `/my_stats` is private and channel-gated.
- `/stats player` is leadership/admin-only and private.
- `/player_profile` is leadership/admin-only, but posts profile output to a channel and includes Discord identity linkage.
- `/kvk history` is channel-gated and public-output oriented.

Future requirements:

- Normal `/me` dashboard must only show governors linked to the invoking Discord user.
- Governor-specific buttons must re-check selected governor access.
- User-level settings must not be displayed in leadership inspect mode.
- `/me inspect` must be permission-gated and private by default.
- Public KVK history behavior must not be silently changed when adding a private `/me` history entry.

## 16. Usage Evidence and Compatibility Risks

Available evidence:

- The canonical command reference documents the current registered command surface.
- The previous player self-service programme documented nonzero usage across the legacy personal command paths and concentrated `/me` usage around smoke/operator windows.
- `dbo.BotCommandUsage` exists as the production evidence source for fresh usage checks.

Compatibility risks:

- Redirecting `/my_stats`, `/myinventory`, `/stats player`, `/player_profile`, or `/kvk history` too early could break established player and leadership workflows.
- Moving `/kvk history` from public KVK context to private `/me` context would change social/team visibility expectations.
- Reusing `/player_profile` directly for inspect would leak Discord-user identity and channel-posting behavior into a workflow that should be private.
- Export Stats needs a product decision before implementation: selected-governor export versus existing all-linked/user-level export semantics.

Recommendation:

- Before any redirect/removal phase, run fresh production usage analysis from `BotCommandUsage`.
- Preserve all current commands through initial dashboard launch.
- Treat copy/navigation nudges as safer than redirects until usage drops and operator approval is explicit.

## 17. Implementation Phase Plan

| Phase | Scope | Runtime change type |
| --- | --- | --- |
| Phase 2 | Add governor dashboard data service contract, access checks, no visible command change if possible. | Service/DAL foundation. |
| Phase 3 | Add governor selector and dashboard journey behind `/me dashboard`. | Discord view and command behavior. |
| Phase 4 | Add dedicated premium governor dashboard renderer. | Renderer and visual tests. |
| Phase 5 | Add direct Resources, Materials, Speedups actions while preserving `/me inventory` and `/myinventory`. | View/action integration. |
| Phase 6 | Move Export Stats to dashboard row 3 green action after selected-governor semantics are approved. | View/action/export behavior. |
| Phase 7 | Add gated `/me inspect`. | Permission-sensitive leadership workflow. |
| Phase 8 | Add private `/me` KVK History entry point while preserving `/kvk history`. | Compatibility-preserving entry point. |
| Phase 9 | Review usage evidence and propose any redirects/removals separately. | Operator-approved migration only. |

Each implementation phase should be PR-sized and include targeted tests plus command registration validation.

## 18. Refactor Findings

Existing deferred optimisation coverage already identifies the broad player self-service modernization gap. Phase 1 confirms these narrower refactor candidates:

| Finding | Type | Impact | Risk | Suggested later fix |
| --- | --- | --- | --- | --- |
| Legacy personal stats flow duplicates future dashboard metrics across `/my_stats`, `embed_my_stats.py`, and `stats_service.py`. | Architecture | High | Medium | Add a dashboard service payload and preserve `/my_stats` as compatibility until a later redirect decision. |
| Leadership profile flow mixes governor profile data with Discord identity and public channel posting. | Privacy/architecture | High | Medium | Build `/me inspect` on an inspection-safe renderer/service, not directly on `player_profile_flow`. |
| `/me`, KVK, and inventory cards use separate visual systems. | UI architecture | Medium | Medium | After the governor dashboard proves out, extract shared premium card primitives where it removes duplication. |
| Olympia dashboard metrics lack confirmed SQL/data source. | Data contract | Medium | Medium | Complete source discovery or add an approved SQL/data contract before implementation. |
| Export Stats semantics are not yet selected-governor versus all-linked-governor. | Product/data contract | Medium | Medium | Decide and document before moving the action to the governor dashboard. |

## 19. Test Plan

Recommended later test coverage:

- Governor selection: no governors, one governor, multiple governors, main/default governor.
- Governor access: selected governor must belong to invoking user; stale/foreign interactions rejected.
- Dashboard data service: null/missing fields, long governor/alliance names, missing VIP, missing Olympia data, zero AOO joined.
- Dashboard renderer: fixed dimensions, mobile preview, long text fitting, missing metric fallback, conduct/civilisation display.
- Inventory direct actions: resources/materials/speedups/all report payloads preserve selected governor.
- Export Stats: selected-governor or all-linked semantics once decided.
- `/me inspect`: permission denied for normal users, leadership/admin success, fuzzy ambiguity, no Discord-user private data leakage.
- `/kvk history` private entry: current `/kvk history` remains unchanged.
- Compatibility: `/my_stats`, `/stats player`, `/player_profile`, `/myinventory`, `/mykvkcrystaltech`, and `/kvk history` still register and behave as before.

Suggested validation commands for docs/design slices and later PRs:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

Likely focused test candidates for implementation phases:

- `tests/test_me_cmds.py`
- `tests/test_player_self_service_views.py`
- `tests/test_player_self_service_service.py`
- `tests/test_player_self_service_page_cards.py`
- `tests/test_inventory_report_views.py`
- `tests/test_inventory_reporting_service.py`
- `tests/test_stats_cmds.py`
- `tests/test_stats_service.py`
- `tests/test_embed_my_stats.py`
- `tests/test_profile_lookup_service.py`
- `tests/test_kvk_history_service.py`
- `tests/test_kvk_history_card_posting.py`
- `tests/test_validate_command_registration.py`
- `tests/test_command_registration_smoke.py`

## 20. AI Review Gates

This Phase 1 slice is documentation-only and does not change runtime permissions, SQL/data access, Discord interactions, file handling, or lookup behavior. A Codex Security runtime scan is therefore skipped for this slice.

Codex Security review should be run before implementation phases that add or change:

- `/me inspect`
- governor lookup/fuzzy lookup behavior
- leadership/admin permission gates
- SQL/data access for dashboard metrics
- Discord interaction state carrying governor IDs
- inventory/export visibility behavior
- public/private output behavior

Before handoff, this report should be reviewed as a K98 pre-review artifact for scope, non-goals, and deferred optimisation quality.

## 21. Deployment / Rollout Notes for Later Phases

Rollout should be staged:

1. Ship governor dashboard behind existing `/me dashboard` without removing legacy paths.
2. Announce new dashboard entry points in user-facing copy.
3. Monitor command usage through `BotCommandUsage`.
4. Add private `/me` history and inventory direct actions only after dashboard stability is confirmed.
5. Add `/me inspect` separately with explicit leadership validation.
6. Propose redirects/removals only after usage evidence, smoke testing, and operator approval.

Rollback strategy:

- Keep legacy commands untouched during initial launch.
- Keep old `/me` pages reachable by command or compatibility navigation until the new dashboard has production evidence.
- Avoid SQL schema changes in early phases, reducing rollback to bot code/view behavior.

## 22. Deferred Optimisations

Deferred item candidates captured by this audit:

### Player stats dashboard consolidation

- **Problem**: `/my_stats`, `/stats player`, `embed_my_stats.py`, and the proposed dashboard all overlap on personal stats, but the legacy stats embed is not yet ready to be removed.
- **Suggested fix**: Introduce a dashboard data service and renderer first, then make legacy commands compatibility entry points only after usage evidence and approval.
- **Impact**: High.
- **Risk**: Medium.
- **Owner area**: Player self-service / stats.

### Inspection-safe leadership dashboard

- **Problem**: `/player_profile` combines governor data, Discord identity, and public channel posting, which is unsuitable for `/me inspect`.
- **Suggested fix**: Build `/me inspect` on a privacy-filtered governor dashboard payload with explicit permission tests.
- **Impact**: High.
- **Risk**: Medium.
- **Owner area**: Leadership tools / player self-service.

### Premium card visual primitive alignment

- **Problem**: `/me`, KVK, profile, and inventory visuals are implemented separately, making consistent premium styling harder.
- **Suggested fix**: After the governor dashboard renderer is approved, extract only the shared primitives that reduce real duplication.
- **Impact**: Medium.
- **Risk**: Medium.
- **Owner area**: Rendering/UI.

### Olympia data contract gap

- **Problem**: Olympia fights and win ratio are requested dashboard fields, but no confirmed SQL contract was found in the inspected schema.
- **Suggested fix**: Complete source discovery and either map an existing authoritative source or create a separately approved data-contract task.
- **Impact**: Medium.
- **Risk**: Medium.
- **Owner area**: SQL/data contracts.

### Export Stats selected-governor semantics

- **Problem**: The target design moves Export Stats onto the selected governor dashboard, but existing export flows may be Discord-user/all-linked-governor oriented.
- **Suggested fix**: Decide selected-governor versus all-linked export behavior before implementation, then test compatibility with `/me exports`.
- **Impact**: Medium.
- **Risk**: Medium.
- **Owner area**: Exports / player self-service.
