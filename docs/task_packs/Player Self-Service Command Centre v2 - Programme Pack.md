# Player Self-Service Command Centre v2 — Programme Pack

## 1. Programme Header

- Programme name: `Player Self-Service Command Centre v2`
- Programme nickname: `GovernorOS`
- Date: `2026-07-15`
- Owner/context: KD98 / Kingdom 1198 player experience modernisation after the original Player Self-Service Command Centre programme completed in production PR #486, GovernorOS v2 Phases 1-5B completed through mirror PR #220 and production PR #527, Phase 5C Accounts completed and operator accepted in mirror PR #221 and production PR #528 on 2026-07-14, Phase 5D Reminders completed and operator accepted in mirror PR #222 and production PR #529 on 2026-07-15, and Phase 5D.1 Authoritative Next Scheduled Alert Projection implemented with final operator smoke pending
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

Phase 5B is complete and operator accepted. It applied the GovernorOS visual standard to the shared
Resources, Materials, and Speedups renderer with approved room-specific backdrops, larger readable
typography, restored icons, Discord avatar handling, genuine upload dates, and honest populated/no-
data presentation.

Phase 5C is complete and operator accepted. `/me accounts` is now a private linked-governor
portfolio with earned READY/REVIEW/SETUP state, four latest-snapshot metrics, a two-column
scan-health roster, one deterministic portfolio insight, the unchanged guided Manage journey, and
a private avatar-enabled paginated Account Summary plus complete CSV. The accepted `1702x924`
runtime backdrop is `assets/me/cards/me_accounts.png`.

Phase 5D is complete and operator accepted after final smoke on 2026-07-15.
`/me reminders` is now a private premium operational summary with earned ACTIVE/REVIEW/OFF state,
the approved truthful coverage hero, friendly KVK and Calendar summaries, one deterministic Reminder
Insight, and the unchanged guided Manage journey. The strict `1702x924` runtime backdrop is
`assets/me/cards/me_reminders.png`. Repository inspection confirmed that an exact cross-system next-
alert projection would duplicate materially different KVK and Calendar scheduler eligibility, so
that logic was not copied into the summary service. Final smoke accepted Manage refresh/reflected
updates, graceful timeout, invoking-user avatar, duplicate-safe identity, removal of deprecated
Inventory navigation, right-aligned state support, and the split full UTC footer.

Phase 5D.1 Authoritative Next Scheduled Alert Projection is implemented and locally validated with
final operator Discord smoke pending before Phase 5E Preferences. It promoted the projection item
out of the deferred backlog and extracted narrow pure KVK/Calendar candidate eligibility shared by
live dispatch and read-only Player Self-Service. Existing `/calendar_next_event`, `/next_kvk_event`,
and `/next_kvk_fight` remain unchanged bulk-reader evidence. The operator authorised the discovered
KVK zero-duration truthiness correction so saved `now` is genuinely at-start eligible; its existing
horizon, tracker, task, retry, rehydration, cleanup, and duplicate-send ownership is preserved. No
Calendar, command, SQL, persistence, event-source/type, lead-time, cadence, or DM-content change was
introduced.

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
- Across all my linked governors, what are my combined Power, T4+T5 Kills, and current RSS holdings?
- Which linked account is stale, missing, unusually concentrated, or otherwise needs attention?

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
/me accounts       = all-linked-governor portfolio, scan health, management, and private Account Summary
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
- Phase 5B completed the shared 1400x980 Inventory report renderer refresh with approved premium
  backdrops without changing report data or interaction behavior.
- Phase 5C completed the approved Accounts portfolio and Account Summary using
  `assets/me/cards/me_accounts.png`; Phases 5D-5G continue Reminders, Preferences, Inventory, and
  Exports one page at a time as matching operator-approved assets and contracts become available.
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

### Phase 5C Accounts portfolio data contract

Phase 5C explicitly approves a read-only, set-based data/service expansion for the all-linked-
governor Accounts portfolio and private Account Summary. It does not approve SQL schema or
persistence changes.

Recommended service-level concepts:

```text
AccountsPortfolioPayload
- Discord-user identity and generated time
- global latest Kingdom 1198 scan date
- READY | REVIEW | SETUP state
- linked and role counts
- Main governor
- Portfolio Power, T4+T5 Kills, and current RSS Total with coverage
- ordered linked-governor rows
- deterministic Portfolio Insight

LinkedGovernorPortfolioRow
- slot, role, registered name, current scanned name, Governor ID
- Civilisation, City Hall, Power, Troop Power
- Kill Points, T4 kills, T5 kills, Deads, Healed, Highest Acclaim, Helps
- RSS Gathered, RSS Assistance, canonical current RSS Total
- Conduct, Location X:Y, last governor scan, Inventory snapshot time
- CURRENT | STALE | NO DATA | UNRESOLVED
```

Freshness is deliberately simple because Kingdom 1198 is the only dataset: compare every linked
Governor ID's `MAX(ScanDate)` with the single global `MAX(ScanDate)`. Inventory coverage is reported
separately and does not redefine governor DATA state. Portfolio queries must be bulk/set-based and
designed for hundreds of linked accounts. The canonical Inventory RSS calculation must be reused,
not copied or redefined.

### Phase 5D Reminders summary data contract

Phase 5D explicitly approves a narrow read-only service/payload expansion for the premium Reminders
summary. It does not approve a new scheduler, event source, lead time, DM behavior, persistence
contract, SQL schema, or reminder mutation.

Recommended service-level concepts:

```text
RemindersSummaryPayload
- Discord-user identity and generated time
- ACTIVE | REVIEW | OFF state and supporting text
- KVK ReminderSystemSummary
- Calendar ReminderSystemSummary
- discriminated ReminderHero
- one deterministic Reminder Insight
- warnings / unavailable saved selections

ReminderSystemSummary
- enabled and completeness state
- selected event keys plus player-facing labels and counts
- selected alert-time keys plus canonical labels and counts
- unavailable-selection counts
- longest lead time, latest alert point, At-start inclusion, and coverage label

NextScheduledReminderAlert
- KVK or Calendar system
- stable occurrence/event identity and player-facing label
- exact alert-at and event-start UTC datetimes
- canonical lead-time key and label

ReminderHero
- NEXT_ALERT | NO_UPCOMING | COVERAGE | UNAVAILABLE
- optional next-alert payload
- headline and one or two concise lines
```

`ACTIVE` requires at least one enabled system and a complete valid event/time configuration for every
enabled system. `REVIEW` is reserved for enabled configurations that cannot produce reminders; a
deliberately disabled system, a quiet schedule, passed warning windows, or a temporary source read
failure does not by itself make the saved configuration invalid. `OFF` means both systems are
disabled, while saved inactive choices remain visible and clearly labelled.

A next alert may be shown only when existing reminder/event services can expose the earliest eligible
future alert through the same domain semantics as dispatch without side effects. Prefer reuse of an
existing projection service, then a narrow pure helper extracted from scheduler-domain logic. When
that cannot be done without parallel scheduling logic or wider redesign, `REMINDER COVERAGE` is the
approved outcome and the projection is recorded as deferred. No card read may create jobs, send DMs,
mark delivery, acknowledge an alert, or mutate persistence.

Raw event/time keys remain internal. The UI reuses the authoritative player-facing catalog and order,
normalises equivalent `now`/`start` presentation to `At start`, shows genuine counts and deterministic
`+ N more` overflow, and never infers a favourite event or community recommendation.

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

Status: `complete - operator smoke and final visual acceptance passed 2026-07-13`.

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

Delivery record:

- Operator approved the shared-renderer impact and retained 1400x980 runtime/output policy before
  implementation; the 2800x1960 `_master_2x` files remain source-only.
- The renderer-only refresh uses the three report-specific production backdrops and aligns panels,
  charts, typography, spacing, contrast, long-name handling, and native no-data presentation.
- Operator visual review accepted the premium theme/content direction and requested restoration of
  the supplied item icons, use of the invoking player's Discord avatar in the top-left identity
  position, and a safe readability increase. The follow-up applies to populated and native no-data
  reports while retaining the report-logo fallback when avatar retrieval is unavailable.
- A final operator-requested chart pass replaces the fixed first/middle/last x-axis labels with up
  to six evenly spaced genuine upload dates and draws density-aware diamonds at every plotted
  upload, so players can see history depth without changing or inventing data.
- Automated validation passed 255 focused Inventory/dashboard tests and the full suite (`2503 passed, 2
  skipped`) plus architecture, deferred-item, import, registration, formatting, type, and secret
  checks.
- Original-size, Discord desktop, and Discord mobile samples cover populated and honest no-data
  Resources, Speedups, and Materials.
- Operator smoke and final visual acceptance passed on 2026-07-13. The operator confirmed the
  finished reports look premium, with populated/no-data data fidelity and the existing interaction
  behavior preserved. The completed task pack and chat starter are archived.

### Phase 5C-5G — Premium `/me` Summary Cards

Status: `Phase 5C Accounts and Phase 5D Reminders are complete and operator accepted; Phase 5D.1 is implemented with operator smoke pending; Phases 5E-5G remain separately scoped`.

The five summary pages share a presentation and interaction baseline but remain independent PR-sized
slices. A later page must reuse the accepted rules from earlier pages without creating a broad
renderer/view framework or silently inheriting page-specific decisions.

Shared premium summary-card contract:

- Keep the current 1702x924 output and stable `me_<page>_<discord_user_id>.png` filename by default.
  A different dimension requires explicit page-specific approval after original-size, Discord
  desktop, and Discord mobile comparison; source masters must not be loaded at runtime.
- Deliver the successful generated PNG as a standalone private attachment for full Discord width,
  not inside an embed image container. Retain the concise private embed built from the same already-
  authorized summary payload as the rendering/delivery fallback.
- Render off the event loop, replace prior attachments deliberately, preserve the fallback without
  a second data fetch, and close every file/stream on success, fallback, timeout, cancellation,
  stale suppression, and concurrent navigation.
- The invoking-user avatar remains a page-specific design decision. Phase 5C applies the accepted
  bounded avatar treatment to Accounts and every Account Summary section. Following operator smoke,
  Phase 5D reuses that bounded circular avatar with a safe no-avatar fallback. Keep long/Unicode
  display names fitted and never derive a user-level page identity from a selected governor.
- Keep genuine current page values, states, names, action guidance, and empty/unavailable wording.
  Do not invent figures, trends, governors, status, or next actions to fill the backdrop.
- Keep global navigation as real Discord components: blue-primary `Accounts`, `Reminders`, and
  `Preferences` on the first row; secondary navigation and page-specific actions below; the active
  page remains disabled. Start each workshop from the current page's genuine actions and the
  accepted Accounts visual language, but approve the exact second/third rows page by page rather
  than mechanically copying an irrelevant button. Do not paint fake buttons into the image.
- Accounts, Reminders, Preferences, Inventory summary, and Exports summary are Discord-user or all-
  linked-governor pages. They must not show `Change Governor`, even when more than one governor is
  linked. The view may carry an optional selected governor only so `Dashboard` returns to the same
  governor. Direct `/me <page>` entry has no implicit governor filter and uses the normal dashboard
  no/one/multiple-governor resolution when the player returns.
- A governor-specific child action, such as Inventory VIP or a report, must perform its own explicit
  governor selection/resolution and current access recheck. Retained Dashboard-return context must
  never silently narrow a user-level page or bypass authorization.
- Governor dropdown routing is fixed across the remaining programme:
  - Dashboard and selected-governor Resources, Materials, Speedups, future History, and any future
    export explicitly approved as selected-governor scoped may show the author-gated paged Change
    Governor control when more than one governor is linked.
  - Accounts, Account Summary, Reminders, Preferences, Inventory summary, and Exports summary never
    show Change Governor because their data is Discord-user-level or all-linked-governor scoped.
  - Preferences `Update VIP` and Inventory `Open Report` are governor-specific child journeys: they
    use an explicit governor picker/resolver and recheck access, while their parent pages remain
    unfiltered and dropdown-free.
  - Phase 6 must decide selected-governor versus all-linked Export Stats semantics before a
    dashboard export can inherit a governor dropdown.
- Preserve private/ephemeral delivery, author gating, current timeouts, stale/foreign/forged/
  concurrent denial, action disabled states, persistence, and command registration. A page may
  expand read-only services/DAL/payloads only when its phase explicitly approves that scope; Phase
  5C does so for the Accounts portfolio and Account Summary.
- For each page, test direct-command entry, navigation from a selected dashboard, fallback from the
  same payload, render/delivery failure, attachment replacement, stream cleanup, timeout/stale/
  foreign/concurrent paths, empty/unavailable data, long names, and original/desktop/mobile output.

Remaining-phase consistency matrix:

| Phase | Parent scope | Premium output baseline | Governor routing | Product/behavior boundary |
|---|---|---|---|---|
| 5D Reminders | Discord user | 1702x924 standalone, invoking-user avatar with safe fallback, same-payload fallback, graceful timeout | No Change Governor | Complete and operator accepted; ACTIVE/REVIEW/OFF, truthful coverage hero, friendly KVK/Calendar summaries, one deterministic insight, unchanged persistence/scheduling/DM/Manage |
| 5D.1 Next alert | Discord user | Existing accepted Phase 5D card and delivery contract | No Change Governor | Shared pure scheduler-parity projection produces NEXT/NO UPCOMING/UNAVAILABLE without jobs, DMs, writes, new sources, SQL, or command changes |
| 5E Preferences | Discord user | Same premium baseline, page-approved backdrop and controls | No parent dropdown; Update VIP resolves governor explicitly | Preserve visibility/profile/VIP services and SQL contracts unless separately approved |
| 5F Inventory summary | All linked/user | Same premium baseline; direct 1400x980 reports remain separate | No parent dropdown; Open Report explicitly selects and report pages may switch governor | Preserve calculations, imports, ranges, visibility, export, filename, and Sheets contracts |
| 5G Exports summary | User/all-linked | Same premium baseline and private option windows | No Change Governor under current scope | Preserve schemas, formats, windows, filenames, services, and Sheets behavior |
| 6 Export Stats action | Decision gated | Accepted attachment/navigation lifecycle | Dropdown only if selected-governor export is approved | Decide selected versus all-linked before implementation; no schema redesign |
| 7 History | Selected governor | Accepted selected-governor standalone lifecycle | Paged Change Governor with access recheck | Preserve public/channel-gated `/kvk history`; add private `/me history` only |
| 8 Inspect | Explicit lookup target, inspect-safe | Private permission-gated premium output | Inspect lookup/ambiguity resolution, not the viewer's linked-governor dropdown | Approve permissions, safe fields/VIP, lookup, and telemetry first |
| 9 Migration review | Evidence only | No new renderer implied | No selector change implied | Usage-led recommendations only; redirects/removals need explicit later approval |

Every phase starts with repository inspection and an approval-gated product contract. A completed
phase's page-specific choices do not silently approve another page's metrics, workflow changes,
asset, or component rows.

#### Phase 5C - Premium Accounts Summary Card

Status: `complete and operator accepted on 2026-07-14`.

Approved product outcome:

- `/me accounts` remains private, author-gated, and scoped to the invoking Discord user's complete
  linked-governor registry rather than one selected governor.
- Successful output becomes a standalone `1702x924` PNG using the approved runtime asset
  `assets/me/cards/me_accounts.png` and stable `me_accounts_<discord_user_id>.png` filename.
- The smoke-refined layout includes a best-effort Discord avatar on Accounts and every Account
  Summary section, and renders:
  - `ACCOUNT CENTRE` with earned `READY`, `REVIEW`, or `SETUP` state;
  - Discord display name, Kingdom 1198, and linked-governor count, with Main retained as the first
    roster tile rather than repeated in a separate header line;
  - `LATEST SNAPSHOTS` with exactly four metrics: Linked, Portfolio Power, T4+T5 Kills, and current
    Inventory-backed RSS Total;
  - role breakdown and honest `n/N reporting` coverage;
  - a readable two-column governor-tile roster with Slot, Governor, ID, prominent Power, and Data;
  - one deterministic `PORTFOLIO INSIGHT` line;
  - the existing Manage guidance and explicit UTC date-time `Refreshed` footer.
- Do not display linked count against configured capacity. The configured slot limit is not a
  player-facing account maximum.
- Main-card roster capacity is eight rows; with more than eight, show seven rows plus `+ N more`
  guidance. This is display overflow only. Account Summary covers every linked governor.

Approved scan/state rules:

- Kingdom 1198 is the only governor dataset.
- Global freshness is the dataset's `MAX(ScanDate)`; each governor uses its own `MAX(ScanDate)`.
- DATA states are `CURRENT`, `STALE`, `NO DATA`, and `UNRESOLVED`.
- `READY` requires a configured Main, unique/resolved linked IDs, and every governor in the latest
  scan; `REVIEW` covers stale/missing/unresolved/duplicate entries; `SETUP` covers no governors or no
  Main.
- Portfolio aggregates deduplicate by Governor ID, preserve nulls, and never treat missing as zero.
- RSS Total reuses the exact canonical current Inventory holdings calculation. RSS Gathered and RSS
  Assistance remain lifetime fields and are not the headline RSS value.

Approved interaction expansion:

- Main page rows remain blue `Accounts`/`Reminders`/`Preferences`, secondary
  `Dashboard`/`Exports`, then `Manage Accounts` and new `Account Summary`.
- `Manage Accounts` preserves the existing lookup/add/replace/remove/confirm/cancel/revalidation,
  ownership/claim, slot, audit, and host-refresh behavior.
- `Account Summary` is a new private, read-only, all-governor child journey using the same backdrop,
  standalone attachment delivery, eight rows per page, and three sections:
  - Overview: identity, Civilisation, City Hall, VIP, compact Power/Troop Power, Location, Last Scan UTC;
  - Combat: compact Kill Points, T4+T5 Kills, Deads, Healed, Highest Acclaim, calculated KP Loss,
    and percentage-labelled Tanking Score with a higher-is-better footer note;
  - Economy & Activity: compact RSS Gathered, RSS Assistance, current RSS Total, Helps,
    whole-number Conduct, and Inventory As Of.
- Summary controls provide section tabs, Previous/Next, complete private CSV, and Back to Accounts.
  The CSV contains exact values for every linked row and includes registered/current names, VIP,
  T4 and T5 components, KP Loss/Tanking Score, coordinates, data state, scan time, and Inventory
  time once each.
- Accounts and Account Summary preserve the current private attachment/fallback on timeout, disable
  every control, and show a concise rerun instruction without refetching or rerendering.
- No Change Governor appears on Accounts or Account Summary. Optional selected-governor context is
  retained only for validated Dashboard return.

Approved technical scope:

- read-only typed service/DAL/payload expansion is in scope and must be bulk/set-based;
- validate SQL field mappings against `C:\K98-bot-SQL-Server`;
- no SQL schema/table/view/index, persistence, registry-authority, slot, ownership, claim, lookup, or
  mutation redesign is approved;
- preserve same-payload fallbacks, off-event-loop rendering, attachment replacement, stream cleanup,
  command registration, privacy, author gating, and existing legacy redirects;
- run focused/full validation, original/desktop/mobile samples, and Codex Security review before
  operator Discord smoke.

The complete implementation contract is retained as the archived Phase 5C task pack and chat
starter. Mirror PR #221 and production PR #528 contain the accepted implementation.

#### Phase 5D - Premium Reminders Summary Card

Status: `complete and operator accepted on 2026-07-15`.

Implementation evidence recorded on 2026-07-14:

- One typed read-only payload owns state, label/time normalisation, genuine counts, deterministic
  overflow, saved inactive treatment, coverage, warnings, hero variants, injected UTC time, and the
  priority-ordered Reminder Insight.
- A dedicated renderer strictly validates the fully opaque `1702x924` production asset, uses the
  invoking user's circular Discord avatar with a safe fallback, renders the approved hierarchy, and
  delivers stable `me_reminders_<discord_user_id>.png` output.
- Standalone private attachment delivery, same-payload fallback, deliberate replacement, off-loop
  rendering, stream cleanup, graceful timeout, author gating, and selected-Dashboard return context
  retain the existing component architecture.
- KVK autosave/update and confirmation DM, Calendar Settings, Remove All revalidation, persistence,
  restart/rehydration, duplicate-send protection, retries, schedulers, event sources, and dispatch
  behavior are unchanged.
- Focused Phase 5D tests passed (`147 passed`), selected reminder/scheduler tests passed
  (`193 passed`), and full pytest passed (`2551 passed, 2 skipped`). Architecture, command
  registration, smoke imports, and the ten-case original/desktop/mobile visual matrix also passed.
- The final Manage-flow host refresh explicitly closes regenerated attachment streams in `finally`;
  the corrected tree passed `108` focused reminder/view tests, full pytest (`2551 passed, 2 skipped`),
  log-noise validation, and all pre-commit hooks.
- Codex Security standard scan `8fcf96f6-44e0-4d87-8521-7de721444ef7` sealed with `85/85` review
  receipts and `42/42` candidate ledgers. Its 20 reportable findings (`16 Medium`, `4 Low`) are in
  pre-existing repository authorization/import/Ark/MGE surfaces; Phase 5D has no security finding.
- Operator smoke on 2026-07-15 accepted Manage refresh and timeout behavior. The requested visual
  refinement adds the shared avatar, prevents duplicate `(1198)`, removes deprecated Inventory
  navigation from Reminders, right-aligns state support, and splits the UTC footer with full date-time;
  final visual re-smoke passed.
  Refinement validation passed `83` renderer/view tests, `146` focused cross-system regressions, full
  pytest (`2562 passed, 2 skipped`), pre-commit, architecture/deferred checks, smoke imports, command
  registration, log-noise analysis, and native-size visual review.
- The approved coverage hero is used because no existing pure cross-system projection can be reused
  without copying scheduler rules. The separately scoped extraction has been promoted from the
  deferred backlog into the active Phase 5D.1 task pack.
- Final operator Discord smoke accepted genuine reflected settings, Manage behavior, graceful
  timeout, avatar/identity, navigation, alignment, footer, and live visual presentation.

Approved product outcome:

- `/me reminders` remains private, author-gated, Discord-user scoped, and independent of any selected
  governor. It has no `Change Governor`; optional Dashboard governor context is return context only.
- Successful output becomes a standalone `1702x924` PNG using the approved runtime asset
  `assets/me/cards/me_reminders.png` and stable `me_reminders_<discord_user_id>.png` filename.
- The accepted alert/configuration-led layout uses the invoking user's bounded circular Discord
  avatar with a safe fallback and renders:
  - `REMINDER CENTRE` with earned `ACTIVE`, `REVIEW`, or `OFF` state;
  - invoking Discord display name, Kingdom 1198 context, and concise system-enablement/review copy;
  - one hero: `NEXT SCHEDULED ALERT`, `NO UPCOMING ALERT`, `REMINDER COVERAGE`, or
    `SCHEDULE UNAVAILABLE`;
  - balanced KVK and Calendar summaries with state/count, friendly event labels, canonical alert-time
    labels, deterministic overflow, and a compact coverage span;
  - exactly one deterministic `REMINDER INSIGHT`;
  - `Manage reminders` guidance and an explicit UTC refreshed/schedule footer.

Approved state rules:

- `ACTIVE`: at least one system is enabled and every enabled system has at least one valid selected
  event and at least one valid selected alert time.
- `REVIEW`: an enabled system cannot produce reminders from its saved configuration, including
  missing events, missing alert times, or unavailable saved selections.
- `OFF`: both systems are disabled. Saved inactive choices remain visible and are labelled as saved,
  not deleted.
- An intentionally disabled system, no upcoming selected occurrence, passed warning windows, or a
  temporary schedule-source read failure does not by itself make the configuration `REVIEW`.

Approved hero contract:

1. Show `NEXT SCHEDULED ALERT` only when an authoritative read-only projection identifies the
   earliest eligible future alert across KVK and Calendar using the same domain semantics as dispatch.
   Display absolute alert and event-start times in UTC, never a static countdown or delivery promise.
2. Show `NO UPCOMING ALERT` when that projection is healthy but has no future candidate; use the more
   specific passed-warning-window copy only when existing occurrence data proves it.
3. Show `REMINDER COVERAGE` when an exact projection would require parallel scheduler logic, a new
   event source, new persistence, or wider redesign. This is an approved implementation outcome, not
   a blocker.
4. Show `SCHEDULE UNAVAILABLE` when a normally available projection/source fails for the request;
   retain the saved settings and top-level configuration state.

Approved KVK/Calendar summary rules:

- Never expose raw identifiers such as `armament_reveal`; reuse the authoritative player-facing event
  catalog and ordering from the existing Manage/event system.
- Show genuine event and alert-time counts, singular/plural grammar, off-with-saved and incomplete
  states, and deterministic `+ <N> more` overflow.
- Reuse authoritative lead-time ordering and present semantically equivalent `now`/`start` choices as
  `At start` without changing persisted keys or scheduler behavior.
- Derive concise labels such as `Coverage: 24h → start`, while making no claim of continuous coverage
  between configured alert moments.
- Unknown saved selections are surfaced as unavailable/reviewable without displaying their raw keys.

Approved Reminder Insight priority:

1. configuration that cannot produce alerts;
2. a proven upcoming-event coverage gap;
3. one or both systems being disabled;
4. a neutral coverage characteristic worth reviewing;
5. a positive coverage summary.

The insight must be one deterministic sentence, normally no more than two clauses. It must not infer
a favourite event, use cross-player popularity as a recommendation, claim delivery success, or treat
missing data as zero.

Approved interaction and technical scope:

- Keep the existing guided `Manage` child journey, KVK/Calendar switch, event/time choices, KVK
  autosave/update wording and confirmation DM, Calendar Settings handoff, Remove All confirmation,
  current-state revalidation, persistence/restart behavior, scheduled/sent cleanup, duplicate-send
  protections, scheduler, event sources, DMs, and host refresh behavior unchanged.
- Main component rows remain Accounts/Reminders/Preferences, Dashboard/Exports, then the
  existing Manage action; no separate KVK or Calendar host button is added.
- Phase 5D may add cohesive typed read-only summary models, friendly normalisation, deterministic
  state/coverage/insight helpers, and an optional side-effect-free next-alert projection. Commands and
  views stay thin; scheduler-domain logic is reused or narrowly extracted rather than copied.
- Successful delivery is a standalone private attachment; fallback is built from the same already-
  authorised payload with no second fetch. Rendering is off-loop, attachments are replaced
  deliberately, and every image/file stream is closed on success and all failure/timeout/navigation
  paths.
- Timeout preserves the report, visibly disables controls, rejects later interactions, and provides
  concise rerun guidance.
- No SQL schema/table/view/index, new scheduler, new event source, new event type, new lead time, new
  DM/calendar behavior, new persistence, defaults, presets, delivery history, popularity telemetry,
  public output, or broad renderer/view framework is approved.
- Original-size, Discord desktop, and mobile samples must cover every state/hero family, long names,
  overflow, incomplete selections, off-with-saved choices, and unavailable schedule preview.
- Focused/full repository validation, scheduler/dispatch regressions, Codex Security review, and
  operator Discord smoke are required before completion/promotion.

The authoritative implementation detail is retained in the archived Phase 5D task pack and chat
starter. The backdrop-generation task is complete; runtime uses only the production-size asset.

#### Phase 5D.1 - Authoritative Next Scheduled Alert Projection

Status: `implemented and locally validated - operator Discord smoke pending`.

Approved direction:

- Complete the accepted Reminders hero before Phase 5E Preferences by projecting the earliest
  genuine future KVK or Calendar alert from authoritative, side-effect-free scheduler semantics.
- Reuse the bulk occurrence-reader paths already exercised by `/calendar_next_event`,
  `/next_kvk_event`, and `/next_kvk_fight`. Those commands are evidence, not an alert contract: they
  do not combine player settings/offsets with KVK's 48-hour horizon and tracker rules or Calendar's
  grace and sent-key rules.
- Extract narrow pure candidate helpers that accept injected UTC time and already-loaded state, and
  make live dispatch consume the same semantics. Player Self-Service must not own a parallel scheduler.
- Choose the earliest candidate deterministically and map it into the existing typed
  `NEXT SCHEDULED ALERT`; use `NO UPCOMING ALERT` only for healthy empty projections and
  `SCHEDULE UNAVAILABLE` for request-level source/projection failure. Never imply delivery success.
- Preserve scheduled-versus-sent distinctions, restart/rehydration, retry, duplicate-send,
  unsubscribe/Remove All, Manage, source, lead-time, event-type, persistence, DM, and Calendar behavior.
- Preserve the complete accepted Phase 5D visual/interaction contract and the three existing
  next-event commands without registration or behavior changes.
- Introduce no SQL, schema, new persistence, new event source, N+1 occurrence reads, jobs, DMs,
  acknowledgements, cache refreshes, network calls, or tracker writes in the projection path.
- Require deterministic-clock dispatch parity, source-health, no-side-effect, restart, duplicate,
  Player Self-Service delivery, full regression, K98 PR-review/promotion, and Codex Security gates.

The authoritative implementation and escalation contract is in the active Phase 5D.1 task pack and
chat starter. Runtime now uses one typed cross-system projection plus narrow KVK and Calendar pure
eligibility helpers consumed by both live dispatch and Player Self-Service. KVK occurrences/config/
sent/scheduled state and Calendar runtime occurrences/preferences/sent state are bulk-loaded once
per request; projection performs no cache refresh, network call, job/task creation, DM,
acknowledgement, or persistence write. The earliest future candidate uses a deterministic KVK-first
tie-break, healthy empty inputs produce `NO UPCOMING ALERT`, and a required source/projection failure
produces `SCHEDULE UNAVAILABLE` without changing valid ACTIVE/REVIEW/OFF configuration state.

The section 16 audit exposed that KVK `now` was mapped to zero duration but skipped by the live
scheduler's truthiness check. The operator explicitly authorised the narrow correction on
2026-07-15: KVK `now` is now genuinely at-start eligible through the same existing task, tracker,
retry, rehydration, cleanup, and duplicate-send machinery. No Calendar, source, persistence,
lead-time, cadence, command, SQL, or DM-content contract changed. Local automated and native/
desktop/mobile visual validation is complete; final operator Discord smoke remains pending before
Phase 5D.1 completion and Phase 5E activation.

#### Phase 5E - Premium Preferences Summary Card

Preserve Inventory visibility state/actions, Inventory VIP, Discord-user timezone/location/language,
`Set Public`/`Set Private`, `Update VIP`, and `Manage Profile` behavior. VIP remains an explicitly
governor-resolved child action; the page itself is user-level and has no Change Governor. No profile
schema, preference, visibility, Google Sheets, or SQL change.

#### Phase 5F - Premium Inventory Summary Card

Preserve the existing all-linked-governor Resources/Speedups/Materials coverage summary, upload
guidance, and `Open Report` journey. This phase does not migrate or redesign the Phase 5B direct
1400x980 reports, does not add a selected-governor page filter, and does not change imports,
calculations, visibility, ranges, exports, filenames, or Google Sheets behavior.

#### Phase 5G - Premium Exports Summary Card

Preserve the current all-linked/user-level Stats and Inventory export availability, guidance,
disabled states, private option windows, schemas, formats, date windows, filenames, and Google
Sheets behavior. No Change Governor; any selected-governor export decision remains owned by the
separate Phase 6 approval gate.

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
- Premium all-linked-governor Accounts portfolio, scan health, insight, guided management, and
  private paginated Account Summary/CSV.
- Premium Discord-user Reminders summary with earned configuration state, truthful next-alert or
  coverage hero, friendly KVK/Calendar summaries, deterministic insight, and unchanged Manage flow.
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
- latest Kingdom 1198 governor scan source, including `KingdomScanData4` where authoritative
- `dbo.PlayerLocation` or its current repository equivalent
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
- [x] Direct Resources, Materials, and Speedups paths exist while `/me inventory` and `/myinventory` remain compatible.
- [x] Phase 5C Accounts delivers the approved portfolio card, scan health, insight, unchanged
  Manage flow, and private complete Account Summary/CSV.
- [x] Phase 5D Reminders product/content/visual contract and approved Herald's Watch backdrop are
  recorded in the programme, task pack, and implementation starter.
- [x] Phase 5D Reminders locally delivers the approved ACTIVE/REVIEW/OFF card, truthful coverage
  hero, friendly KVK/Calendar summaries, deterministic insight, unchanged Manage behavior, and
  automated/visual validation.
- [x] Phase 5D Reminders final operator visual re-smoke confirms genuine settings, reflected Manage
  updates, graceful timeout, refined avatar/identity, navigation, alignment, full UTC footer, and
  accepted live presentation on 2026-07-15.
- [x] Phase 5D.1 Authoritative Next Scheduled Alert Projection is promoted from the deferred backlog
  into an active task pack and chat starter, with existing next-event reader evidence and strict
  scheduler-parity/no-side-effect boundaries recorded.
- [ ] Export Stats semantics are explicitly decided and tested before dashboard integration.
- [ ] A private `/me history` path exists while `/kvk history` remains unchanged.
- [ ] `/me inspect` is permission-gated, private by default, and excludes Discord-user private data.
- [ ] Legacy commands are only redirected/removed after usage evidence and explicit operator approval.
- [x] Documentation and canonical command references reflect completed phases through Phase 5D.
- [x] Phase 5C documentation, canonical references, automated validation, security review, visual
  samples, and successful operator Discord smoke are recorded.
- [x] Command registration validation remains green through Phase 5D.
- [x] No new direct SQL exists in command/view layers through Phase 5D.
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
Complete the final Phase 5D.1 operator Discord smoke from its active task pack. Confirm the
authoritative NEXT/NO UPCOMING/UNAVAILABLE hero states, the authorised KVK at-start DM, Manage
refresh, timeout, fallback, attachment replacement, and selected-Dashboard return. Do not start
Phase 5E until that gate is accepted.
```

The accepted Reminders runtime backdrop remains `assets/me/cards/me_reminders.png` at exactly
`1702x924`. Phase 5D.1 changes the authoritative hero data, not the accepted card hierarchy,
components, renderer, fallback, Manage journey, or timeout contract.

Except for the explicitly authorised KVK `now` truthiness correction recorded above, Phase 5D.1
does not inherit permission to change reminder scheduling behavior, event sources,
event/time choices, lead times, grace, retries, DMs, Calendar behavior, persisted state, SQL,
another `/me` page, the three existing next-event commands, or the guided Manage workflow.

Use:

- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5D.1 Authoritative Next Scheduled Alert Projection.md`
- `docs/task_packs/Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5D.1 Authoritative Next Scheduled Alert Projection.md`

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
| 2026-07-13 | Phase 5B implemented and locally validated | Adopted the three 1400x980 report-specific runtime backdrops in the shared Inventory renderer, retained source-only 2x masters and stable behavior, added failure/data/stream/visual coverage, and passed focused plus full automated validation. Operator Discord smoke and final visual acceptance remain. |
| 2026-07-13 | Phase 5B completed and Phase 5C prepared | Recorded successful Phase 5B operator smoke and final premium visual acceptance; archived its task pack/starter; made Accounts the next approval-gated visual/product workshop; and defined the shared 1702x924-default standalone summary-card, page-specific avatar, navigation, fallback, cleanup, and no-Change-Governor contract for Phases 5C-5G. |
| 2026-07-14 | Phase 5C Accounts product, data, interaction, and backdrop contract approved | Locked the four-metric Accounts portfolio, global Kingdom 1198 latest-scan DATA/READY rules, arbitrary-size roster behavior, deterministic insight, unchanged Manage flow, private paginated Account Summary/CSV, no-avatar page layout, standalone delivery, scoped read-only DAL expansion, and approved `assets/me/cards/me_accounts.png` for implementation. |
| 2026-07-14 | Phase 5C Accounts implemented; operator smoke pending | Added typed all-linked portfolio models, set-based latest Kingdom 1198 and canonical current-RSS reads, the approved standalone 1702x924 Accounts renderer, unchanged Manage refresh, private three-section paginated Account Summary, complete formula-safe CSV, same-payload fallbacks, attachment cleanup, focused/full validation, visual samples, and Codex Security review. No SQL schema, registry, ownership, or existing report/export contract changed. |
| 2026-07-14 | Phase 5C operator smoke refinement | Removed Inventory navigation from Accounts/Summary, added author avatar and Discord-name suffix deduplication, increased/rebalanced typography, added UTC date-times and VIP, moved Helps to Economy, added compact combat/economy values plus KP Loss/Tanking Score, extended the exact CSV, and made Summary timeout visibly disable controls while preserving the private report. No SQL schema or registry mutation contract changed. |
| 2026-07-14 | Phase 5C operator smoke refinement 2 | Replaced the sparse main roster table with a larger two-column governor-tile grid, compacted Overview Power/Troop Power, renamed the visual section to Combat, displayed Tanking as a percentage with higher-is-better guidance, and moved Conduct from Combat to Economy. Payload, exact CSV, SQL, Manage, privacy, attachment, and timeout contracts remain unchanged. |
| 2026-07-14 | Phase 5C operator smoke refinement 3 | Removed the redundant Main-governor header line, enlarged the reclaimed Accounts header/metric typography, made governor-tile Power values prominent, and carried the existing bounded author avatar through Overview, Combat, and Economy renders. Payload, SQL, CSV, Manage, privacy, attachment, and timeout contracts remain unchanged. |
| 2026-07-14 | Phase 5C completed and Phase 5D prepared | Recorded successful final operator smoke and premium visual acceptance for Accounts and all Account Summary sections, archived the completed Phase 5C pack/starter, made Reminders the next approval-gated product workshop, and fixed the shared standalone/avatar/navigation plus governor-dropdown routing contract for Phases 5D-9. |
| 2026-07-14 | Phase 5D Reminders product/content/visual contract approved | Locked ACTIVE/REVIEW/OFF state, the authoritative next-alert/no-upcoming/coverage/unavailable hero decision, friendly KVK/Calendar summaries, deterministic insight, unchanged Manage and reminder behavior, no-avatar/no-Change-Governor presentation, standalone/fallback lifecycle, and approved `assets/me/cards/me_reminders.png`; implementation is the next active slice. |
| 2026-07-14 | Phase 5D Reminders implemented and locally validated | Added the typed dual-system summary, strict no-avatar 1702x924 renderer, approved coverage hero, friendly labels/times/counts/overflow/insight, standalone same-payload delivery, and unchanged Manage behavior. Focused tests passed 147, scheduler/reminder selection passed 193, full pytest passed 2551 with 2 skipped, and the ten-state original/desktop/mobile matrix passed visual review. Exact next-alert projection is deferred; operator Discord smoke remains pending. |
| 2026-07-14 | Phase 5D final security and cleanup validation | Closed the explicit host-refresh attachment stream lifecycle, reran focused/full/pre-commit/log-noise gates, and sealed Codex Security scan `8fcf96f6-44e0-4d87-8521-7de721444ef7` with 85/85 reviews, 42/42 candidate ledgers, 20 pre-existing wider-repository findings, and no Phase 5D security finding. Operator Discord smoke remains pending. |
| 2026-07-15 | Phase 5D operator smoke refinement | Manage refresh and timeout passed operator smoke. Added the shared invoking-user avatar with safe fallback, duplicate-safe `(1198)` identity, removed deprecated Inventory navigation from Reminders, right-aligned state support with the state pill, and split the footer into left UTC guidance plus right full refreshed date-time. Final visual re-smoke remains pending. |
| 2026-07-15 | Phase 5D completed and Phase 5D.1 prepared | Recorded successful final operator smoke and visual acceptance, archived the completed Phase 5D task pack/starter, promoted the authoritative next-alert projection out of the deferred backlog, and created the active Phase 5D.1 task pack/starter. Existing `/calendar_next_event`, `/next_kvk_event`, and `/next_kvk_fight` are recorded as reusable bulk reader evidence; shared live/projection parity, no side effects, no N+1 reads, and unchanged reminder/command behavior are the implementation boundary before Phase 5E Preferences. |
| 2026-07-15 | Phase 5D.1 implemented and locally validated | Added shared pure KVK/Calendar eligibility and a typed bulk-loaded cross-system projection for NEXT/NO UPCOMING/UNAVAILABLE. Live dispatch consumes the same rules; projection performs no tasks, DMs, acknowledgements, refreshes, network calls, or writes. The operator authorised correcting KVK `now` zero-duration eligibility while preserving existing task/tracker/rehydration/retry behavior. Native/desktop/mobile visual evidence passed; final operator Discord smoke remains pending. |
