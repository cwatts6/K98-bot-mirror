# Player Self-Service Command Centre v2 — Programme Pack

## 1. Programme Header

- Programme name: `Player Self-Service Command Centre v2`
- Programme nickname: `GovernorOS`
- Date: `2026-07-13`
- Owner/context: KD98 / Kingdom 1198 player experience modernisation after the original Player Self-Service Command Centre programme completed in production PR #486 and GovernorOS v2 Phase 5A completed in mirror PR #219 and production PR #526
- Programme type: `Product UX | Discord command architecture | player stats/profile/inventory integration | visual redesign | SQL-backed data service foundation`
- One-pass approved: `No`
- Headline: **Turn `/me` into the definitive KD98 governor operating system — bold, premium, personal, and unmistakably better than a normal Discord bot command.**

## 2. Phases 1-4 Conclusion

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

Phase 3 is also complete. It wired that foundation into `/me dashboard`, delivered the private
no/one/multiple governor journey, rechecked access before payload fetch, preserved selected context
through current navigation, and retained every existing `/me` and named legacy command. Operator
smoke passed all journey states and the corrected live-data presentation on 2026-07-10.

Phase 4 is complete. It delivered the dedicated 1180x640 premium governor card using the approved
`assets/me/cards/me.png` background and invoking-player Discord avatar, made the PNG a standalone
attachment for materially better Discord readability, retained the Phase 3 private fallback embed,
and completed attachment/file-stream cleanup across the current transitions. Operator smoke on
2026-07-11 exercised every governor option and accepted the author-gated Change Governor dropdown.

Phase 5A is complete. It delivered private direct `/me resources`, `/me materials`, and
`/me speedups` reports, matching selected-dashboard actions, selected-governor Inventory totals on
the 1180x760 dashboard, honest native no-data reports, private exports, and report-preserving
Change Governor controls. Operator smoke on 2026-07-13 accepted the desktop/mobile presentation,
no-data journey, and governor switching. `/me inventory`, `/myinventory`, Inventory visibility,
imports, reporting data, ranges, exports, filenames, and Google Sheets behavior remain unchanged.

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

### Phase 4 presentation and navigation contract for later phases

Every later `/me` phase must treat the accepted Phase 4 delivery as the baseline, not rediscover
the presentation rules independently:

- Generated visual cards are sent as standalone attachments for maximum Discord width. Embed-wrapped
  `attachment://` images are retained only where a phase has not yet migrated or as an explicitly
  documented fallback.
- Every generated-card path retains a concise private embed or text fallback built from the same
  already-authorized payload. Rendering or delivery failure must not trigger a second data fetch or
  bypass an access decision.
- Global navigation keeps the accepted blue-primary top-row pattern, with secondary navigation and
  page-specific success actions below it where component limits permit.
- Governor-specific pages expose an author-gated `Change Governor` dropdown below their other
  controls when multiple linked governors exist. The dropdown preserves the current page, report
  type, and applicable filters, supports more than 25 governors through paging, and rechecks access
  before loading replacement data.
- Discord-user-level or all-governor aggregate pages do not show a misleading governor dropdown.
  They preserve selected governor context only for returning to governor-specific pages.
- Selector-to-card, card-to-selector, card-to-page, page-to-card, card refresh, fallback, denied,
  unavailable, timeout, cancellation, and stale/concurrent transitions clear or replace attachments
  deliberately and release every file stream.
- Personal cards may use the invoking player's Discord avatar best-effort, with a safe local
  fallback. Buttons and dropdowns remain real Discord components and are never painted into images.

Delivery ownership:

- Phase 5A applied the contract to direct governor-specific Resources, Materials, and Speedups.
- Phase 5B refreshes the shared 1400x980 Inventory report renderer with approved premium backdrops
  without changing report data or interaction behavior.
- Phases 5C-5G migrate Accounts, Reminders, Preferences, Inventory, and Exports summary cards one
  page at a time as matching operator-approved assets become available.
- Phases 6-8 must use the same contract for Exports actions, History, and Inspect respectively.

## 11. Target Data / Service Contract

Phase 2 introduced the stable data foundation now used by the visible dashboard.

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
| Highest Acclaim | latest `KingdomScanData4.HighestAcclaim` | Optional fallback |
| Dead | Latest stats | Optional fallback |
| Helps | Latest stats | Optional fallback |
| Healed | Latest stats | Optional fallback |
| Ark joined/won | latest `KingdomScanData4.AOOJoined`, `AOOWon` | Null/zero guarded |
| Ark win ratio | Derived | Show `N/A` if no joined value |
| Times Named Autarch | latest `KingdomScanData4.AutarchTimes` | Optional fallback |
| Times Autarch Participated | latest `KingdomScanData4.KvKPlayed` | Optional fallback |
| Conduct Score | SQL field `Conduct` | UI label `Conduct Score` |
| Civilisation | SQL field `Civilization` | UI label `Civilisation` |
| Location | `PlayerLocation.X`, `PlayerLocation.Y` | Show `X:Y`; optional fallback |
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

Status: `complete - operator smoke passed 2026-07-10`.

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
- Phase 3 added a dashboard-specific, private, author-gated selector/view that renders and
  switches dashboard context in place.
- Do not use the shared `AccountPickerView` directly: it is a one-shot selector that also owns
  lookup/register/refresh behavior and does not match the dashboard's persistent context-switching
  contract.
- Reuse Phase 2 governor options/context/access services and established interaction-safety,
  timeout, and message-edit patterns.
- Recheck governor access on every selected-governor action and selection callback.

Delivered in mirror PR `K98-bot-mirror#217` and production PR `K98-bot#524` on 2026-07-10:

- `/me dashboard` now resolves the private no/one/multiple/unavailable/denied governor journey.
- One linked governor opens directly; multiple linked governors use a dashboard-specific selector
  before any dashboard payload fetch.
- Selected and changed governors are re-resolved against the active registry before payload access.
- The private author-gated view edits in place, rejects foreign/stale/forged interactions, disables
  on timeout, and paginates safely beyond Discord's 25-option select limit.
- The fallback shell shows the approved Phase 2 identity, profile, battle, Ark, honour, and
  freshness fields with predictable missing-value behavior and no Olympia content.
- Initial operator smoke corrections source acclaim, Ark, and Autarch values from the latest
  `KingdomScanData4` row, map numeric civilisation through `Civilization_Mapping`, use compact
  player-facing numbers, omit scan order, disable controls through the original ephemeral response
  on timeout, and retain selected-governor context across compatibility-page navigation.
- Second-pass smoke corrections add `KvKPlayed` as Times Autarch Participated, add the indexed
  `PlayerLocation` `X:Y` lookup, avoid repeated `VIP` wording, and make the governor predicate
  index-seekable. Mixed generated-card/embed transitions are explicitly parked for the Phase 4-6
  renderer upgrades, with SQL execution-plan measurement captured before any new view/index/table.
- Accounts, Reminders, Preferences, Inventory, and Exports remain reachable with unchanged
  semantics; all existing `/me` and named legacy command registrations remain intact.
- The operator approved active registry linkage as the Phase 3 self-view authority, backed by
  Discord onboarding audit, monthly reconciliation against in-game records, and owner-approved
  account transfer controls.
- Admin/leadership inspect was reconfirmed as a required programme outcome. It remains a separate
  permission-gated slice so Phase 3 does not silently enable arbitrary-governor access.
- Final operator smoke passed the no-governor setup journey, single-governor direct open,
  multiple-governor selector, Change Governor, and corrected dashboard-data presentation on
  2026-07-10.

### Phase 4 — Premium Governor Dashboard Renderer

Status: `complete - operator smoke passed 2026-07-11`.

Goal: replace the successful selected-governor fallback shell with a premium generated card without
changing the delivered data, access, selector, or command contracts.

Deliver:

- Dedicated deterministic Pillow renderer consuming the existing `GovernorDashboardPayload`.
- Wide premium card benchmarked at `1180x640`, or an operator-approved equivalent after prototype
  review.
- Identity, battle metrics, profile/status, Ark/Autarch honours, and freshness zones.
- Glyph-safe responsive text fitting and deliberate missing-value presentation.
- Existing fallback embed retained for render/file/send failures.
- Off-event-loop rendering and complete file-stream cleanup.
- One attachment replacement/clearing contract across selector, card, fallback embed, and all
  current `/me` page transitions.
- Visual sample review at original, Discord-desktop, and Discord-mobile scales.
- No Olympia fields, placeholders, icons, or empty zones.

Implementation record:

- Approved `assets/me/cards/me.png` as the operator-created background at the 1180x640 target.
- Uses the invoking player's Discord avatar in the medallion when available, with a KD98 fallback.
- Posts the successful PNG as a standalone attachment for wider Discord presentation, aligns the
  identity and battle-metric edges, uses blue primary navigation, and places the author-gated
  Change Governor dropdown below the navigation.
- Shows the operator-approved `Last Login: TBC` presentation placeholder without changing the
  Phase 2 payload, DAL, or SQL contract; future data wiring remains separately deferred.
- Retains the Phase 3 embed from the same payload when avatar retrieval, rendering, file creation,
  or image delivery fails.
- Focused tests, repository validators, pre-commit, full pytest, and complete/sparse/Unicode visual
  samples passed. Operator Discord smoke on 2026-07-11 exercised every linked-governor option,
  confirmed the author-gated dropdown, and accepted the materially larger, easier-to-read
  standalone card.

Approval gate:

- Confirm the visual hierarchy, target dimensions, and asset/background provenance before coding.
- Any new field, SQL/data change, new action, or broad shared renderer framework requires separate
  approval.

Command/data impact: `/me dashboard` version increment only; no command-count, SQL, DAL, payload,
permission, registry-authority, inventory, export, history, or inspect change.

### Phase 5A — Direct Inventory Reports and Governor Context

Status: `complete - automated validation and operator smoke passed on 2026-07-13`.

Goal: let the selected governor open a specific existing inventory report without returning to the
all-report picker.

Deliver:

- `/me resources`, `/me materials`, and `/me speedups` grouped subcommands, subject to command
  registration approval.
- Matching dashboard actions carrying the selected governor context.
- Direct-command no/one/multiple governor resolution: setup guidance for none, direct open for one,
  and an author-gated selector before report fetch for multiple.
- Access re-resolution before every report fetch/action.
- Reuse existing inventory reporting services, views, ranges, export controls, and approved
  visibility semantics; do not duplicate report SQL or business logic.
- Reuse the existing 1400x980 inventory report renderer and stable filenames as standalone primary
  attachments; do not redesign the renderer or introduce a new visual framework.
- Add report-type controls for Resources, Materials, and Speedups, keep 1M/3M/6M/12M range and
  existing export controls, and add a paged author-gated Change Governor dropdown below the report
  controls when multiple linked governors exist.
- Keep `/me` direct reports private regardless of the legacy Inventory visibility preference. The
  existing `/myinventory` journey continues to honor that preference unchanged.
- Preserve selected report type and range when changing governor, then recheck access and replace
  the attachment in place.
- Preserve `/me inventory`, `/myinventory`, inventory imports, schemas, and output contracts.
- Attachment/page-transition alignment with the Phase 4 card contract.

Command impact: no top-level command-count change; `/me` grouped subcommands increase from 6 to 9.

Approval gate: confirm the recommended private-only `/me` report policy, the three grouped
subcommands, the dashboard action layout, and the compact report-control layout before
implementation.

Operator decision on 2026-07-12:

- Approved private `/me resources`, `/me materials`, and `/me speedups`; Resources uses an `RSS`
  dashboard label.
- Approved keeping `/me inventory` unchanged but removing its selected-dashboard button.
- Approved a governor-only multiple-account entry selector.
- Approved selected-governor-only latest RSS, combined Speedups days, and legendary-equivalent
  Materials totals on a new third dashboard metric row.
- Approved expanding the governor dashboard to 1180x760 while retaining the existing 1400x980
  Inventory reports unchanged for this phase.
- Approved direct-report rows for type, range, private export, Dashboard/paging, and Change
  Governor; missing report data links the configured upload channel.

Completion record:

- Delivered all three private commands and dashboard actions with the approved order `RSS`,
  `Speedups`, `Materials`.
- Kept the standalone 1400x980 report contract and introduced an honest renderer-native empty state
  only where required to replace the dashboard attachment reliably; no dummy values or trends are
  drawn.
- Passed 106 focused tests, the full suite (`2487 passed, 2 skipped`), repository validators,
  pre-commit, hosted quality checks, and Codex Security review.
- Operator smoke accepted populated and empty report journeys, upload guidance, tabs, ranges,
  private exports, Dashboard navigation, and Change Governor state preservation.
- Added six approved Resources, Materials, and Speedups backdrop files as dormant Phase 5B inputs;
  Phase 5A does not load or render them.

### Phase 5B — Premium Inventory Report Backdrops and Visual Alignment

Status: `next proposed slice; task pack and chat starter prepared`.

Goal: bring the existing Resources, Speedups, Materials, and honest no-data Inventory report PNGs
up to the accepted premium GovernorOS v2.0 visual standard using the approved report-specific
backdrops without changing what the reports calculate or how players interact with them.

Deliver:

- Use the supplied 1400x980 Resources, Materials, and Speedups production backdrops in the existing
  shared Inventory renderer; retain the 2800x1960 `_master_2x` files as source assets only.
- Align panels, chart surfaces, typography, spacing, contrast, and no-data treatment to those
  backdrops while retaining output dimensions and stable filenames.
- Apply the renderer refresh consistently to direct private `/me` reports and legacy
  `/myinventory` reports because both intentionally share the renderer.
- Preserve report payloads, calculations, tabs, 1M/3M/6M/12M ranges, exports, visibility,
  standalone delivery, same-payload fallback, attachment replacement, and stream cleanup.
- Preserve author-gated Change Governor and >25 paging on direct governor-specific reports;
  preserve report type and range when switching governor.
- Never use dummy report data, invented trends, or sample figures in no-data output.
- No SQL, DAL, service, command, view, export schema, filename, dimension, import, or Google Sheets
  behavior change.

Approval gate: approve the shared-renderer impact, backdrop/runtime policy, visual hierarchy, and
representative Resources, Speedups, Materials, and no-data prototypes before implementation.

### Phase 5C-5G — Premium `/me` Summary Cards

Status: `proposed as five independent asset-led slices after Phase 5B`.

- Phase 5C: Premium Accounts Summary Card.
- Phase 5D: Premium Reminders Summary Card.
- Phase 5E: Premium Preferences Summary Card.
- Phase 5F: Premium Inventory Summary Card.
- Phase 5G: Premium Exports Summary Card.

Each slice owns one existing Discord-user or all-governor page, its operator-approved backdrop,
standalone attachment migration where still required, same-payload private fallback, current
actions/disabled states, blue-primary global navigation, attachment/stream cleanup, and
desktop/mobile smoke. These pages must not show Change Governor. Selected governor context may be
retained only for returning to the governor dashboard or an explicitly governor-specific action.
No slice changes page data, service ownership, permissions, visibility, or export behavior.

### Phase 6 — Export Stats Action Decision and Integration

Status: `proposed`.

Goal: add a dashboard Export Stats action only after its governor scope is unambiguous.

Deliver:

- Explicit product decision between selected-governor export and the current all-linked/user-level
  export behavior.
- Dashboard action that calls the existing service-backed export path under the approved scope.
- Clear copy when the selected dashboard governor does not narrow the resulting file.
- Use standalone attachment delivery and the accepted navigation/fallback/cleanup contract. Show
  Change Governor only if the approved export is selected-governor scoped; omit it for all-linked
  user-level exports.
- Preserve `/me exports`, the existing `/my_stats_export` redirect, file formats, schemas, date
  windows, Google Sheets behavior, and Inventory export behavior.
- Privacy, selected-context, filename/content, and compatibility tests.

Approval gate: operator must approve selected-governor versus all-linked semantics. Any schema,
header, worksheet, format, or SQL export-contract redesign remains a separate programme.

### Phase 7 — Private `/me history` Entry Point

Status: `proposed`.

Goal: give the selected governor a private personal-history path without changing the social/public
KVK command.

Deliver:

- Private `/me history` grouped subcommand and dashboard action.
- Re-resolve selected-governor access before loading history.
- Reuse the modern KVK history service/payload/renderer through a private delivery adapter.
- Deliver the history card as a standalone private attachment with the accepted fallback,
  attachment cleanup, blue navigation, and paged Change Governor contract.
- Preserve `/kvk history` command registration, channel gate, public behavior, filters, and output.
- No implicit redirect between `/me history` and `/kvk history`.
- Focused privacy, access, missing-history, rendering, and compatibility tests.

Approval gate: confirm `/me history` option shape and whether it initially opens the established
default history view or exposes private controls. Record the grouped-subcommand count change.

### Phase 8 — Leadership/Admin `/me inspect`

Status: `proposed`.

Goal: provide the required kingdom-management and player-support dashboard for authorized
leadership/admin users without weakening the self-view trust boundary.

Deliver:

- Private, permission-gated `/me inspect` grouped subcommand.
- Governor ID and normalized/fuzzy name lookup with a private ambiguity selector.
- Explicit unlinked inspect authorization path; self-view remains default-deny for unlinked IDs.
- Inspection-safe payload/card mode containing approved in-game governor metrics only.
- Exclude Discord account linkage, account type/slot, reminders, timezone, language, inventory
  visibility, export preferences, and other Discord-user relationship metadata.
- Decide explicitly whether player-maintained VIP is sufficiently authoritative for inspect; omit
  it until approved.
- Usage tracking plus structured inspect telemetry that identifies authorized use without logging
  unnecessary private values.
- Preserve `/stats player` and `/player_profile` until a later usage-led migration approval.
- Reuse the accepted standalone governor-card delivery and cleanup contract, but keep inspect lookup
  and ambiguity controls separate from the self-view linked-governor Change Governor dropdown.

Approval gate: define the exact admin/leadership permission policy, inspect-safe VIP decision,
lookup behavior, audit fields/retention, and grouped-subcommand count change. Run a dedicated Codex
Security review for permission, privacy, lookup-input, and telemetry boundaries.

### Phase 9 — Usage-Led Migration Review

Status: `proposed`.

Goal: use real adoption evidence to decide whether any compatibility command should change.

Deliver:

- Fresh `dbo.BotCommandUsage` evidence after Phases 5A-8 have had an agreed observation window.
- Separate player and leadership workflow analysis for `/my_stats`, `/myinventory`, `/stats player`,
  `/player_profile`, `/mykvkcrystaltech`, and `/kvk history`.
- Player/leadership communication and rollback plan.
- Proposed copy nudges, redirects, deprecations, or removals one command at a time.
- Command-registration/canonical-document impact and an explicit operator decision for every path.

Approval gate: no migration is implied by this review. Each command change requires evidence,
communication, a no-feedback window where appropriate, and explicit operator approval.

### Phase 10 — Future “Sticky” Player Features

Status: `future programme candidate - not a committed implementation slice`.

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

Entry gate:

- Complete and observe the core dashboard/action/inspect rollout first.
- Select a measurable player value hypothesis and validated source for each proposed metric.
- Validate privacy, freshness, historic comparability, SQL performance, and website/API boundaries.
- Create a new task pack or successor programme before implementation.

These ideas must not block or silently expand Phases 5A-9.

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

- [x] `/me dashboard` is governor-first and opens the correct no/one/multiple governor journey.
- [x] The governor dashboard card is visually premium, readable, and meaningfully better than legacy embeds.
- [x] The dashboard uses validated data sources and excludes Olympia until a source exists.
- [x] Governor context is preserved safely through the dashboard and current compatibility actions.
- [x] Accounts, Reminders, and Preferences remain correctly Discord-user-level.
- [ ] Direct Resources, Materials, and Speedups paths exist while `/me inventory` and `/myinventory` remain compatible.
- [ ] Export Stats semantics are explicitly decided and tested before dashboard integration.
- [ ] A private `/me history` path exists while `/kvk history` remains unchanged.
- [ ] `/me inspect` is permission-gated, private by default, and excludes Discord-user private data.
- [ ] Legacy commands are only redirected/removed after usage evidence and explicit operator approval.
- [x] Documentation and canonical command references reflect the completed Phases 1-4.
- [x] Command registration validation remains green through Phase 4.
- [x] No new direct SQL exists in command/view layers through Phase 4.
- [x] Deferred findings from completed phases are captured structurally.

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
Approve Phase 5B's backdrop/runtime policy and representative Resources, Speedups, Materials, and
honest no-data visual direction, then implement the renderer-only refresh.
```

Phase 5A is complete and operator accepted. Phase 5B is deliberately presentation-only: the
existing shared report renderer adopts the supplied premium backdrops while every data,
calculation, command, interaction, privacy, export, and compatibility contract remains stable.

Use:

- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5B Premium Inventory Report Backdrops and Visual Alignment.md`
- `docs/task_packs/Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5B Premium Inventory Report Backdrops and Visual Alignment.md`

## 21. Programme Change Log

| Date | Change | Notes |
|---|---|---|
| 2026-06-27 | Initial v2 programme pack created | Follow-on from original Player Self-Service Command Centre programme. |
| 2026-07-09 | Programme updated after Phase 1 audit | Reframed as GovernorOS, added bold dashboard vision, revised phase plan, removed Olympia from initial scope, and made Phase 2 the service/data foundation. |
| 2026-07-10 | Phase 2 completed and Phase 3 prepared | Recorded the delivered governor context/data foundation, successful smoke/regression validation, explicit selector architecture decision, and Phase 3 as the next slice. |
| 2026-07-10 | Initial Phase 3 implementation validated | Added the private governor-first selector and fallback shell, recorded registry trust approval and required future inspect direction, and passed focused plus full repository validation before operator smoke corrections. |
| 2026-07-10 | Phase 3 operator smoke completed | Confirmed no-governor, single-governor, multiple-governor, Change Governor, and corrected dashboard-data journeys; Phase 4 became the next slice. |
| 2026-07-10 | Phase 4 scope pack prepared and remaining roadmap reconciled | Archived the completed Phase 3 execution pack/starter, created the Phase 4 task pack/starter, made Phase 7 history and Phase 8 inspect ordering authoritative, and added explicit approval gates for Phases 4-10. |
| 2026-07-11 | Phase 4 operator smoke completed | Accepted the wider standalone premium card as materially larger and easier to read, exercised every linked-governor option, and confirmed the author-gated Change Governor dropdown. Future `/me` page presentation alignment remains a separately phase-gated consistency item. |
| 2026-07-11 | Phase 4 archived and Phase 5A/5B scoped | Archived the completed Phase 4 task pack/starter, made Phase 5A direct inventory reports the next approval-gated slice, assigned existing `/me` summary-page standalone delivery to Phase 5B, and made the Phase 4 standalone/blue-navigation/governor-dropdown contract authoritative for later phases. |
| 2026-07-12 | Phase 5A revised scope approved | Approved the three private report commands, governor-only entry selector, selected-governor Inventory totals, 1180x760 dashboard, revised navigation, retained `/me inventory`, and unchanged 1400x980 Inventory renderer. |
| 2026-07-13 | Phase 5A completed and Phase 5B prepared | Recorded successful direct-report and no-data smoke, archived the completed pack/starter, accepted the Inventory visual-quality gap, added six dormant premium backdrop assets, made their renderer-only adoption the new Phase 5B, and separated the five user-level summary pages into Phases 5C-5G with no governor dropdown. |
