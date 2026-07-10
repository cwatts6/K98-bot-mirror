# Player Self-Service Command Centre v2 — Programme Pack

## 1. Programme Header

- Programme name: `Player Self-Service Command Centre v2`
- Programme nickname: `GovernorOS`
- Date: `2026-07-10`
- Owner/context: KD98 / Kingdom 1198 player experience modernisation after the original Player Self-Service Command Centre programme completed in production PR #486, the v2 Phase 1 blueprint completed, and the Phase 2 governor context/data foundation delivered
- Programme type: `Product UX | Discord command architecture | player stats/profile/inventory integration | visual redesign | SQL-backed data service foundation`
- One-pass approved: `No`
- Headline: **Turn `/me` into the definitive KD98 governor operating system — bold, premium, personal, and unmistakably better than a normal Discord bot command.**

## 2. Phase 1 and Phase 2 Conclusion

Phase 1 confirmed that the original `/me` work created the right foundation, but the current experience is still primarily a Discord-user setup hub. It helps players manage accounts, reminders, preferences, exports, and inventory, but it does not yet feel like the daily governor dashboard players should open to understand their account.

The future state is clear:

```text
/me dashboard
→ resolve registered governors privately
→ select governor, or open the only governor directly
→ premium governor dashboard
→ all governor-specific actions preserve the selected governor context
```

The audit also confirmed that legacy and adjacent commands must be treated carefully. `/my_stats`, `/myinventory`, `/stats player`, `/player_profile`, `/mykvkcrystaltech`, and `/kvk history` all serve established workflows and should not be redirected, removed, or silently changed during the first implementation phases.

The operator decision after Phase 1 is that Olympia data should be ignored for now. Olympia fights and Olympia win ratio are not currently in the source system, so they must not be included in Phase 2 or the first dashboard build. They can be added later if a reliable source/data contract is introduced.

Phase 2 is now complete. It delivered typed governor context and payload contracts, linked-governor
resolution for no/one/multiple states, default-deny self-view access checks, explicitly gated future
inspect context, a validated dashboard DAL/service, self-view versus inspect-safe data separation,
null-safe field handling, and focused regression coverage. The visible `/me` journey and every
legacy command remained unchanged. Operator smoke testing confirmed all existing `/me` and named
legacy commands work, and the full pytest and repository validation suite passed.

## 3. Programme Vision

The vision is to transform `/me` from a useful collection of setup pages into the **primary personal command centre for every KD98 governor**.

A player should be able to open `/me dashboard` and immediately see who they are, where they stand, what matters, and what they can do next. The experience should feel premium enough that players naturally choose it over legacy commands, not because those commands were removed, but because `/me` is better.

This should become a KD98 point of difference: a polished, app-like Discord experience that makes the kingdom feel organised, data-driven, and player-focused. It should combine strong visual design, governor-first navigation, privacy by default, and reliable data services behind a single coherent product.

The end state is not command migration. The end state is a **governor operating system** inside Discord.

## 4. Why This Programme Exists

The player self-service surface is currently fragmented:

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me inventory
/me exports
/my_stats
/myinventory
/my_stats_export
/player_profile
/stats player
/kvk history
/mykvkcrystaltech
```

Some of these commands are old but heavily understood by players and leadership. Some are modern but still setup-oriented. Some are leadership-only. Some are public KVK social/reporting surfaces. The risk is not simply that the UX is inconsistent; the risk is that the bot starts to feel like a list of tools rather than a modern player product.

The newer `/kvk stats`, `/kvk targets`, `/kvk history`, and `/kvk rankings` cards raised the visual standard. The `/me` cards now need to match or exceed that standard. The attached dashboard inspiration shows the right ambition: a bold account card, strong identity section, large metrics, concise labels, meaningful status, and a polished game-like feel.

Doing this as a programme is necessary because the change crosses command surface governance, SQL-backed metrics, player privacy, leadership workflows, inventory reporting, exports, KVK history, rendering standards, and future website-ready data models.

## 5. Product Goal

Create a premium governor dashboard experience that answers these questions for a player in seconds:

- Which governor am I looking at?
- What is my latest power, KP, acclaim, dead, helps, and healed position?
- What alliance/civilisation/conduct score does the system currently hold for me?
- What lifetime or account-level achievements are visible now?
- What can I do next without remembering another command?
- Where are my resources, materials, speedups, history, preferences, reminders, and exports?
- Has the data been updated recently enough to trust?

For leadership, the long-term goal is a separate inspection journey that answers a different question:

- What does leadership need to know about this governor without exposing the player's private Discord-user settings?

## 6. Core Design Principles

1. **Governor-first, not Discord-user first** — the main journey should begin by choosing the governor, then every relevant action should preserve that context.
2. **One premium dashboard** — the dashboard should be the natural launchpad for personal stats, inventory, history, exports, and account settings.
3. **Go big and go bold** — this must feel like a flagship KD98 feature, not a tidied-up embed.
4. **Privacy by default** — normal `/me` output remains private and author-gated; leadership inspection must be a separate gated workflow.
5. **Compatibility before migration** — preserve legacy commands until usage data and operator approval justify redirects or removals.
6. **No unverified metrics** — do not display data that lacks a validated source. Olympia is excluded until a source exists.
7. **Commands and views stay thin** — dashboard assembly belongs in services/DALs, not command callbacks or Discord views.
8. **Source-of-truth naming matters** — UI may say `Conduct Score` and `Civilisation`, but implementation must respect SQL fields such as `Conduct` and `Civilization`.
9. **Current KVK stays `/kvk`; personal history can live in `/me`** — current/live KVK reporting remains under `/kvk`; retrospective personal history can gain a private `/me` entry point later.
10. **Design for the website future** — payloads and visual sections should be structured enough to support future web/dashboard surfaces.

## 7. Target Command Model

### Current `/me` command group to preserve

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me inventory
/me exports
```

### Planned grouped additions, subject to phase approval

```text
/me resources
/me materials
/me speedups
/me history
/me inspect
```

### Legacy/specialist commands to preserve through initial launch

```text
/my_stats
/myinventory
/my_stats_export
/stats player
/player_profile
/mykvkcrystaltech
/kvk history
```

### Product placement model

```text
/me dashboard      = personal governor command centre
/me accounts       = Discord-user/account linkage management
/me reminders      = Discord-user reminder settings
/me preferences    = Discord-user preference settings
/me inventory      = all-in-one inventory report journey
/me resources      = direct selected-governor resource report
/me materials      = direct selected-governor materials report
/me speedups       = direct selected-governor speedups report
/me history        = private selected-governor KVK history entry point
/me inspect        = gated leadership/admin governor dashboard inspection
/kvk history       = existing public/channel-gated KVK history path
/mykvkcrystaltech  = specialist workflow outside this programme for now
```

## 8. Target Workflow Model

### Normal player journey

```text
Player runs /me dashboard
→ bot resolves linked governors privately
→ no governors: setup card with Accounts as primary action
→ one governor: open dashboard directly
→ multiple governors: select governor
→ premium governor dashboard opens
→ actions preserve selected governor context
→ player can change governor, go to account/settings pages, or open selected-governor reports
```

### Governor context preservation

Every governor-specific action must carry or re-resolve:

```text
author Discord user ID
governor ID
viewer mode: self | inspect
access decision
privacy profile
data freshness
```

This context should flow through resources, materials, speedups, history, and future export actions. It should not be stored in a way that trusts stale/forged Discord component data without rechecking access.

### Leadership inspect journey, later phase

```text
Leadership/admin runs /me inspect
→ enter governor ID or fuzzy governor name
→ resolve ambiguity privately
→ build inspection-safe governor dashboard payload
→ render private inspection dashboard
→ exclude Discord-user private settings and relationship metadata
```

## 9. Governor Dashboard Product Model

The dashboard should feel like a premium player card and command dock, not a setup page.

### Zone A — Hero identity

Purpose: instantly answer “who is this?”

Recommended fields:

- Governor name
- Governor ID
- Account type, only for the player viewing their own linked governor
- VIP level, optional and only when available/trusted
- Alliance name
- Civilisation
- Conduct Score
- Last updated / scan freshness

### Zone B — Power and battle metric runway

Purpose: show the headline numbers players care about.

Recommended fields:

- Power
- Kill Points
- Highest Acclaim
- Dead
- Helps
- Healed

### Zone C — Honours and participation

Purpose: add personality and bragging rights.

Recommended fields for initial build:

- Ark of Osiris joined/won
- Ark win ratio
- Times Named Autarch
- Times Participated, only where a reliable source exists

Explicitly excluded from initial build:

- Olympia fights
- Olympia win ratio

### Zone D — Action dock

Purpose: turn the dashboard into the daily launchpad.

Recommended actions after the main dashboard is live:

- Resources
- Materials
- Speedups
- Inventory
- KVK History
- Export Stats
- Accounts
- Reminders
- Preferences
- Change Governor, when more than one linked governor exists

### Zone E — Status and confidence

Purpose: explain trust without clutter.

Recommended display:

- Updated timestamp
- Missing data fallback such as `Not set`, `N/A`, or `No recent scan`
- Optional subtle data source/status icon where useful

## 10. Visual / Output Direction

The dashboard should adopt the visual ambition of the attached inspiration card and the readability of the newer KVK cards.

Target direction:

- Wide premium card with strong dark/fantasy styling.
- Clear governor identity on the left/top, not buried in body text.
- Large metric values with short labels and icon accents.
- Fixed zones for identity, metrics, honours, and actions/status.
- Fewer paragraphs; more scannable tiles.
- Stronger whitespace and hierarchy than the current `/me` setup card.
- Discord desktop and mobile preview checks before release.
- Dedicated renderer for governor dashboard rather than forcing the setup-page renderer to do too much.

Example UX for reference only:
- `docs/task_packs/me_dashboard_screenshot.jpg`

Recommended card standard:

```text
Format: generated PNG card plus fallback embed
Canvas: wide card, benchmarked against 1180x640 KVK cards or an approved equivalent
Priority: perceived readability over raw pixel count
Fallback: concise private embed with the same key fields
Privacy: private/ephemeral for normal /me dashboard
```

Design watchouts:

- A bigger canvas can still read small if copy density is too high.
- Long governor/alliance names need fixed text bounds and font-fitting.
- Missing values must not create ugly blank areas.
- Visual style should feel KD98-branded without relying on game logos or unsupported copyrighted assets.
- Action buttons belong in Discord components, but the card should still visually imply the action zones.

## 11. Target Data / Service Contract

Phase 2 should introduce a stable data foundation before the visible dashboard changes.

Recommended service-level concepts:

```text
GovernorDashboardContext
- viewer_discord_id
- viewer_mode: self | inspect
- selected_governor_id
- is_linked_to_viewer
- account_type_for_self_view
- access_decision
- privacy_profile

GovernorDashboardPayload
- identity
- latest_metrics
- historical_highlights
- activity_honours
- profile_status
- freshness
- available_actions
- missing_fields
```

Recommended data fields for the first dashboard payload:

| Field | Source direction | Initial handling |
|---|---|---|
| Governor name | Registry or latest stats/profile fallback | Required with fallback |
| Governor ID | Registry/stats/profile | Required |
| Account type | Discord-governor registry | Self view only |
| VIP level | `GovernorInventoryProfile` | Optional; self view only until inspect decision |
| Alliance | Latest stats/profile | Optional fallback |
| Power | Latest stats | Optional fallback |
| Kill Points | Latest stats / aggregate | Optional fallback |
| Highest Acclaim | KVK/export aggregate/history | Optional fallback |
| Dead | Latest stats | Optional fallback |
| Helps | Latest stats | Optional fallback |
| Healed | Latest stats | Optional fallback |
| Ark joined/won | `AOOJoined`, `AOOWon` aggregate source | Null/zero guarded |
| Ark win ratio | Derived | Show `N/A` if no joined value |
| Times Named Autarch | `AutarchTimes` aggregate/history | Optional fallback |
| Conduct Score | SQL field `Conduct` | UI label `Conduct Score` |
| Civilisation | SQL field `Civilization` | UI label `Civilisation` |
| Updated timestamp | latest scan/data source | Required if available |

Excluded until a source exists:

```text
Olympia fights
Olympia win ratio
```

## 12. Programme Phases

### Phase 1 — Governor Dashboard Product Blueprint and Audit

Status: `complete`.

Delivered:

- Current `/me` command map.
- Legacy and adjacent command classification.
- Governor-first journey blueprint.
- Dashboard field-to-source matrix.
- Inventory split recommendation.
- Card size and visual standard recommendation.
- `/kvk history` product placement recommendation.
- `/me inspect` leadership/admin recommendation.
- SQL/data contract findings.
- Privacy, permission, and compatibility risk review.

No runtime command, SQL, renderer, redirect, or permission changes were made.

### Phase 2 — Governor Context and Dashboard Data Foundation

Status: `complete`.

Goal: build the safe service/DAL foundation for the bold dashboard before changing the visible `/me` journey.

Deliver:

- Governor dashboard context model.
- Linked-governor resolver for self-service mode.
- Access checks for selected governors.
- Dashboard payload service and DAL/repository layer.
- Field formatting/null-handling helpers where appropriate.
- Source validation against SQL repo and current services.
- Focused tests for one/no/multiple governors, access denial, missing data, zero Ark joined, absent VIP, Conduct/Civilization naming, and excluded Olympia data.

Runtime change type: service/DAL foundation; no visible command redesign unless explicitly approved during implementation.

Delivered in mirror PR `K98-bot-mirror#216` and production PR `K98-bot#523`:

- `GovernorDashboardContext`, resolution, option, payload, and field-group models.
- Linked-governor option resolution and no/one/multiple journey states.
- Self-service access denial for unlinked governors.
- Explicit opt-in required before any future unlinked inspect context can be allowed.
- Dashboard DAL/service assembly for approved fields only, with no Olympia data.
- Self-view-only account type/VIP separation from future inspect-safe data.
- Safe missing/null behavior, Ark zero-join handling, SQL mapping, and DAL failure degradation.
- Focused tests plus successful operator smoke and full regression validation.

### Phase 3 — Governor Selector and Dashboard Shell

Status: `implementation complete - local validation passed; operator smoke pending`.

Deliver:

- `/me dashboard` opens selected governor context.
- No governor, one governor, and multiple governor flows.
- Private governor selector.
- Author-gated view state.
- Change governor affordance.
- Compatibility access to Accounts, Reminders, Preferences, Inventory, and Exports.
- Initial fallback embed/dashboard shell while premium renderer is completed.

Selector architecture decision:

- Phase 2 did not create or wire a Discord selector.
- Phase 3 should add a dashboard-specific, private, author-gated selector/view that renders and
  switches dashboard context in place.
- Do not use the shared `AccountPickerView` directly: it is a one-shot selector that also owns
  lookup/register/refresh behavior and does not match the dashboard's persistent context-switching
  contract.
- Reuse Phase 2 governor options/context/access services and established interaction-safety,
  timeout, and message-edit patterns.
- Recheck governor access on every selected-governor action and selection callback.

Delivered locally on 2026-07-10:

- `/me dashboard` now resolves the private no/one/multiple/unavailable/denied governor journey.
- One linked governor opens directly; multiple linked governors use a dashboard-specific selector
  before any dashboard payload fetch.
- Selected and changed governors are re-resolved against the active registry before payload access.
- The private author-gated view edits in place, rejects foreign/stale/forged interactions, disables
  on timeout, and paginates safely beyond Discord's 25-option select limit.
- The fallback shell shows the approved Phase 2 identity, profile, battle, Ark, honour, and
  freshness fields with predictable missing-value behavior and no Olympia content.
- Accounts, Reminders, Preferences, Inventory, and Exports remain reachable with unchanged
  semantics; all existing `/me` and named legacy command registrations remain intact.
- The operator approved active registry linkage as the Phase 3 self-view authority, backed by
  Discord onboarding audit, monthly reconciliation against in-game records, and owner-approved
  account transfer controls.
- Admin/leadership inspect was reconfirmed as a required programme outcome. It remains a separate
  permission-gated slice so Phase 3 does not silently enable arbitrary-governor access.

### Phase 4 — Premium Governor Dashboard Renderer

Status: `next proposed slice after Phase 3 operator smoke`.

Deliver:

- Dedicated governor dashboard PNG renderer.
- Fallback embed.
- Visual tests/golden-dimension checks.
- Discord-like desktop/mobile preview review.
- Premium card layout using identity, metrics, honours, status, and action zones.
- No Olympia fields.

### Phase 5 — Direct Inventory Action Upgrade

Status: `proposed`.

Deliver:

- `/me resources`.
- `/me materials`.
- `/me speedups`.
- Direct dashboard buttons for each report type.
- Reuse existing inventory report services/views.
- Preserve `/me inventory` and `/myinventory`.
- Start visual alignment plan for inventory cards.

### Phase 6 — Export Stats Action Decision and Integration

Status: `proposed`.

Deliver:

- Product decision: selected-governor export versus all-linked-governor export.
- Dashboard row/button action for Export Stats.
- Preserve `/me exports`, `/my_stats_export`, and current export compatibility.
- Tests for privacy and export semantics.

### Phase 7 — Private `/me history` Entry Point

Status: `proposed`.

Deliver:

- Private selected-governor KVK history entry point from `/me`.
- Reuse current modern KVK history service/renderer.
- Preserve `/kvk history` public/channel-gated behavior.
- Compatibility tests proving `/kvk history` is unchanged.

### Phase 8 — Leadership/Admin `/me inspect`

Status: `proposed`.

Deliver:

- Permission-gated `/me inspect`.
- Governor ID and fuzzy name lookup.
- Ambiguous match selector.
- Inspection-safe payload and renderer mode.
- No Discord-user private data leakage.
- Usage tracking and explicit inspect telemetry.
- Preserve `/stats player` and `/player_profile` until separate migration approval.

### Phase 9 — Usage-Led Migration Review

Status: `proposed`.

Deliver:

- Fresh `BotCommandUsage` analysis.
- Player/leadership communication plan.
- Proposed redirects, copy nudges, or removals only where justified.
- Operator approval checkpoint for every legacy path.

### Phase 10 — Future “Sticky” Player Features

Status: `future opportunity`.

Candidate ideas:

- Personal bests.
- Best KVK.
- Lifetime record badges.
- Current streaks.
- Recent changes since last scan.
- Rank-gap or target-distance insights.
- Kingdom top-10 record appearances.
- Visual achievement badges.
- Website-ready profile endpoint or export.

These should not block the core dashboard build, but Phase 2 should avoid data shapes that make them hard later.

## 13. In Scope for the Programme

- Governor-first `/me dashboard` journey.
- Governor context preservation across dashboard actions.
- Dashboard data service/DAL foundation.
- Premium governor dashboard card and fallback embed.
- Direct selected-governor inventory actions.
- Private `/me` KVK history entry point.
- Leadership/admin `/me inspect`, later and separately permission-gated.
- Compatibility preservation for legacy commands.
- Usage-based migration planning.
- Documentation, tests, command reference updates, and deferred optimisation capture.

## 14. Out of Scope for the First Implementation Build

- Redirecting or removing `/my_stats`, `/myinventory`, `/stats player`, `/player_profile`, `/mykvkcrystaltech`, or `/kvk history`.
- Adding Olympia fields.
- SQL schema changes unless a later phase explicitly approves them.
- Changing public/channel-gated KVK behavior.
- Changing inventory import behavior.
- Redesigning stats or inventory export schemas.
- Folding CrystalTech into `/me`.
- Website or external dashboard work.
- Public launch comms before the visible dashboard is ready.

## 15. Likely Source Commands and Areas

### Commands to audit or touch across the programme

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me inventory
/me exports
/my_stats
/myinventory
/stats player
/player_profile
/mykvkcrystaltech
/kvk history
```

### Likely Python modules

```text
commands/me_cmds.py
ui/views/player_self_service_views.py
player_self_service/service.py
player_self_service/page_cards.py
player_self_service/dashboard_card.py
commands/inventory_cmds.py
ui/views/inventory_report_views.py
inventory/reporting_service.py
inventory/dal/inventory_reporting_dal.py
inventory/profile_service.py
commands/stats_cmds.py
embed_my_stats.py
stats_service.py
commands/player_profile_flow.py
services/profile_lookup_service.py
embed_player_profile.py
commands/kvk_cmds.py
services/kvk_history_service.py
commands/kvk_history_card_posting.py
kvk/dal/kvk_history_dal.py
kvk/rendering/kvk_history_renderer.py
```

### SQL contracts to validate when touched

```text
C:\K98-bot-SQL-Server
```

Likely SQL-backed objects:

- `dbo.v_PlayerLatestStats`
- `dbo.v_PlayerProfile`
- `dbo.ALL_STATS_FOR_DASHBOARD`
- `dbo.v_EXCEL_FOR_KVK_All`
- `dbo.v_EXCEL_FOR_KVK_Started`
- `dbo.GovernorInventoryProfile`
- `dbo.BotCommandUsage`

## 16. Cross-Programme Constraints

- Maintain command registration governance.
- Preserve top-level command count unless explicitly approved.
- Prefer grouped `/me` subcommands over new flat commands.
- Keep all player dashboard output private unless a specific action intentionally uses the user's visibility preference.
- Recheck access for governor-specific actions.
- Do not leak Discord-user private settings into leadership inspect mode.
- Avoid direct SQL in command and view layers.
- Validate SQL contracts against the SQL repo before relying on fields.
- Keep CrystalTech outside the programme until separately approved.
- Keep `/kvk history` unchanged when adding private `/me history`.
- Run Codex Security review for phases touching permissions, SQL/data access, interaction state, or privacy-sensitive behavior.

## 17. Programme-Level Validation Strategy

Every implementation phase should consider:

- Architecture boundary validation.
- Command registration validation.
- Focused command/view/service tests.
- Permission and privacy tests.
- Response visibility tests.
- Stale/foreign interaction tests.
- Service/DAL contract tests.
- SQL validation where data contracts are touched.
- Visual rendering dimension and fallback tests.
- Manual Discord smoke testing.
- Deferred optimisation validation.
- Codex Security review when security-sensitive surfaces are touched.

Baseline commands to consider:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
```

For broader runtime phases, also consider:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
```

## 18. Programme Acceptance Criteria

The programme is complete when:

- [ ] `/me dashboard` is governor-first and opens the correct no/one/multiple governor journey.
- [ ] The governor dashboard card is visually premium, readable, and meaningfully better than legacy embeds.
- [ ] The dashboard uses validated data sources and excludes Olympia until a source exists.
- [ ] Governor context is preserved safely through dashboard actions.
- [ ] Accounts, Reminders, and Preferences remain correctly Discord-user-level.
- [ ] Direct Resources, Materials, and Speedups paths exist while `/me inventory` and `/myinventory` remain compatible.
- [ ] Export Stats semantics are explicitly decided and tested before dashboard integration.
- [ ] A private `/me history` path exists while `/kvk history` remains unchanged.
- [ ] `/me inspect` is permission-gated, private by default, and excludes Discord-user private data.
- [ ] Legacy commands are only redirected/removed after usage evidence and explicit operator approval.
- [ ] Documentation and canonical command references are updated.
- [ ] Command registration validation remains green.
- [ ] No new direct SQL exists in command/view layers.
- [ ] Deferred findings are captured structurally.

## 19. Deferred / Future Opportunities

Do not include these in early phases unless separately approved:

- Olympia data integration after a source/data contract exists.
- Personal achievement and badge system.
- Personal bests and all-time kingdom records on the dashboard.
- Recent change summary since last scan.
- Rank gap to next player or next target band.
- Website/API dashboard endpoint.
- CrystalTech integration into `/me`.
- Automated player-facing launch campaign.

## 20. Suggested Next Action

```text
Complete Phase 3 operator smoke, then start Phase 4: Premium Governor Dashboard Renderer.
```

Phase 3 now makes `/me dashboard` governor-first using the completed Phase 2 foundation while
preserving all existing `/me` subcommands and legacy paths. Phase 4 should replace the fallback
shell with the premium PNG card without changing the service or access contract.

## 21. Programme Change Log

| Date | Change | Notes |
|---|---|---|
| 2026-06-27 | Initial v2 programme pack created | Follow-on from original Player Self-Service Command Centre programme. |
| 2026-07-09 | Programme updated after Phase 1 audit | Reframed as GovernorOS, added bold dashboard vision, revised phase plan, removed Olympia from initial scope, and made Phase 2 the service/data foundation. |
| 2026-07-10 | Phase 2 completed and Phase 3 prepared | Recorded the delivered governor context/data foundation, successful smoke/regression validation, explicit selector architecture decision, and Phase 3 as the next slice. |
| 2026-07-10 | Phase 3 implemented locally | Added the private governor-first selector and fallback shell, recorded registry trust approval and required future inspect direction, and passed focused plus full repository validation pending operator smoke. |
