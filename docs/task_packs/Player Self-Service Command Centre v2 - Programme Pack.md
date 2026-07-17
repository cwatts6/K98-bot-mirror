# Player Self-Service Command Centre v2 — Programme Pack

## 1. Programme Header

- Programme name: `Player Self-Service Command Centre v2`
- Programme nickname: `GovernorOS`
- Date: `2026-07-16`
- Owner/context: KD98 / Kingdom 1198 player experience modernisation after the original Player
  Self-Service Command Centre programme completed in production PR #486; GovernorOS v2 Phases 1-5F
  completed and operator accepted through mirror PR #225 and production-branch commit `89f7da16`; and
  the Phase 5G Account Data Export Consolidation product/output/command contract, task pack, and chat
  starter approved on 2026-07-16; the Phase 5G working-branch implementation is now in validation.
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

The Phase 1 audit correctly required caution around legacy and adjacent commands during the initial implementation. Later production evidence and explicit operator decisions may supersede that preservation boundary one route at a time. Phase 5F records that evidence for `/myinventory`, `/inventory_preferences`, and `/me inventory`; `/my_stats`, `/stats player`, `/player_profile`, `/mykvkcrystaltech`, and `/kvk history` remain outside that approved retirement scope.

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

Phase 5D.1 Authoritative Next Scheduled Alert Projection is complete and operator accepted after
final Discord smoke on 2026-07-15. It promoted the projection item
out of the deferred backlog and extracted narrow pure KVK/Calendar candidate eligibility shared by
live dispatch and read-only Player Self-Service. Existing `/calendar_next_event`, `/next_kvk_event`,
and `/next_kvk_fight` remain unchanged bulk-reader evidence. The operator authorised the discovered
KVK zero-duration truthiness correction so saved `now` is genuinely at-start eligible; its existing
horizon, tracker, task, retry, rehydration, cleanup, and duplicate-send ownership is preserved. No
Calendar, command, SQL, persistence, event-source/type, lead-time, cadence, or DM-content change was
introduced. The final card uses bold gold for the authoritative event-start date-time, and the
default KVK cache snapshot shares the projection's injected UTC clock.

Phase 5E Preferences is complete, operator accepted, and deployed. `/me preferences` is now the
private **Personal Settings** centre for the invoking Discord user's regional profile and Inventory
privacy. It renders the approved `assets/me/cards/me_preferences.png` Governor's Accord backdrop at
`1702x924` with the invoking-user avatar in the top-left identity treatment, deterministic saved-
timezone local time and DST-aware UTC offset, honest UTC fallback, three-field profile coverage,
one Settings Insight, and the same-payload private fallback. The main action surface is one
`Manage settings` journey; deprecated Inventory navigation, direct visibility toggles, VIP content,
and Change Governor are absent. Governor-specific VIP editing now belongs to the existing `Manage
Accounts` task flow with explicit linked-governor resolution and current-access revalidation. The
atomic field-specific profile DAL upsert prevents unrelated concurrent field edits from overwriting
one another. No new setting, SQL schema, profile meaning, visibility rule, account rule, command, or
broad renderer framework was introduced.

Phase 5E's Inventory-visibility feature was intentionally transitional. Phase 5F subsequently
retired `/me inventory`, `/myinventory`, `/inventory_preferences`, `/export_inventory`, public
Inventory posting, combined `All` viewing/export, and the visibility application dependency in one
accepted bot release. The selected-governor dashboard, direct premium reports, report-page exports,
imports, audits, calculations, and filenames remain. Personal Settings keeps the accepted regional
profile and LOCAL/UTC experience with its refined profile-first layout. The dormant SQL preference
table remains untouched for rollback and later evidence-led cleanup.

Phase 5G is now product-approved as **Account Data Export Consolidation**, not a premium Exports
summary card. Repository inspection confirms that `/me exports` is a one-action Stats page,
`/my_stats_export` is redirect-only with discarded options, and Account Summary already owns the
well-received all-linked portfolio context. The canonical target is therefore `/me accounts ->
Account Summary -> Download data`; `/me exports` and `/my_stats_export` are removed rather than
retained as duplicate or redirect-only routes. The output choices are an Account-Summary-first full
workbook, the exact current snapshot CSV, and raw Stats history CSV. All identified export-window,
row-count, sheet, Forts, safety, freshness, and Google Sheets labelling defects are in Phase 5G scope.
`/my_stats` remains unchanged until the separate Phase 6 interactive-stats redesign and migration.

## 3. Programme Vision

The vision is to transform `/me` from a useful collection of setup pages into the **primary personal command centre for every KD98 governor**.

A player should be able to open `/me dashboard` and immediately see who they are, where they stand, what matters, and what they can do next. The experience should feel premium enough that players naturally choose it over legacy commands, not because those commands were removed, but because `/me` is better.

This should become a KD98 point of difference: a polished, app-like Discord experience that makes the kingdom feel organised, data-driven, and player-focused. It should combine strong visual design, governor-first navigation, privacy by default, and reliable data services behind a single coherent product.

The end state is not command migration. The end state is a **governor operating system** inside Discord.

## 4. Why This Programme Exists

Before Phase 5F, the player self-service surface still contains transitional Inventory routes:

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me inventory                 <- retire in Phase 5F
/me resources
/me speedups
/me materials
/me exports
/myinventory                  <- retire in Phase 5F
/inventory_preferences        <- retire in Phase 5F
/my_stats
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
5. **Compatibility until evidence supports retirement** — preserve legacy commands until usage data and explicit operator approval justify a route-specific redirect or removal; then remove the obsolete path cleanly rather than retaining a permanent second-class UX.
6. **No unverified metrics** — do not display data that lacks a validated source. Olympia is excluded until a source exists.
7. **Commands and views stay thin** — dashboard assembly belongs in services/DALs, not command callbacks or Discord views.
8. **Source-of-truth naming matters** — UI may say `Conduct Score` and `Civilisation`, but implementation must respect SQL fields such as `Conduct` and `Civilization`.
9. **Current KVK stays `/kvk`; personal history can live in `/me`** — current/live KVK reporting remains under `/kvk`; retrospective personal history can gain a private `/me` entry point later.
10. **Design for the website future** — payloads and visual sections should be structured enough to support future web/dashboard surfaces.

## 7. Target Command Model

### Canonical `/me` command group after Phase 5G

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me resources
/me speedups
/me materials
```

### Approved Phase 5F retirements

```text
/me inventory
/myinventory
/inventory_preferences
/export_inventory
```

### Approved Phase 5G retirements

```text
/me exports
/my_stats_export
```

The Phase 5G routes are removed rather than redirected. Account Summary already provides the richer
all-linked context and becomes the one central personal-data download home.

### Planned grouped additions, subject to later phase approval

```text
/me history
/me inspect
```

### Specialist commands retained after Phase 5G

```text
/my_stats
/stats player
/player_profile
/mykvkcrystaltech
/kvk history
/inventory import
/inventory audit
```

### Product placement model

```text
/me dashboard      = personal governor command centre plus selected-governor Inventory highlights
/me accounts       = all-linked portfolio, management, Account Summary, and Download data
/me reminders      = Discord-user reminder settings
/me preferences    = Discord-user regional profile and LOCAL/UTC reference
/me resources      = private selected-governor resource report and report-page export
/me speedups       = private selected-governor speedups report and report-page export
/me materials      = private selected-governor materials report and report-page export
/inventory import  = Inventory screenshot capture
/inventory audit   = admin Inventory import audit
/my_stats          = current interactive personal Stats experience until Phase 6
/me history        = future private selected-governor KVK history entry point
/me inspect        = future gated leadership/admin governor dashboard inspection
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
  `assets/me/cards/me_accounts.png`; Phase 5D and 5D.1 completed Reminders; Phase 5E completed
  Preferences using `assets/me/cards/me_preferences.png`; Phases 5F-5G continue Inventory and
  Exports one page at a time under separately approved contracts.
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

### Phase 5E Preferences summary data contract

Phase 5E approves a cohesive read-only summary expansion for the private Personal Settings card and
a narrow re-hosting of existing mutations. It does not approve a new profile field, a new privacy
meaning, a VIP data-model change, a SQL schema change, or a cross-module time-display preference.

Recommended service-level concepts:

```text
PreferencesSummaryPayload
- Discord-user identity and one aware generated-at UTC value
- PRIVATE | PUBLIC Inventory-visibility state and exact player-facing consequence text
- RegionalProfileSummary for timezone, location, and preferred language
- TimeReferenceSummary for LOCAL or UTC_FALLBACK presentation
- recognised profile-details-set count out of three
- one deterministic Settings Insight
- warnings / unavailable saved values

RegionalProfileSummary
- timezone PreferenceValueSummary
- location PreferenceValueSummary
- preferred-language PreferenceValueSummary

PreferenceValueSummary
- set / unset state
- recognised / unavailable state
- stored key or code retained internally
- friendly label and optional player-facing code

TimeReferenceSummary
- LOCAL | UTC_FALLBACK
- 24-hour display time
- friendly saved-timezone label when usable
- current DST-aware UTC-offset label when usable
- supporting location/language context where available
```

The same injected UTC timestamp drives the local-time hero and the full refreshed footer. Timezone
conversion is deterministic, side-effect free, and network free; it creates no timer, job, cache
refresh, or reminder behavior. Missing or unavailable timezone data produces an honest UTC-reference
variant rather than inferred location-based time. Location and language remain optional metadata;
profile coverage counts recognised usable values and does not create a pass/fail profile state.

Settings Insight priority is: unavailable saved metadata, no usable timezone, public Inventory
visibility, partial optional profile, then complete/private neutral-positive guidance. The service
must not infer that location and timezone should match, infer nationality or fluency, expose raw
unknown keys, or recommend settings from cross-player behavior.

Inventory visibility remains a Discord-user-level mutation owned by Preferences and must be explained
using the exact existing report-visibility contract. Private direct `/me resources`, `/me materials`,
and `/me speedups` remain private. VIP editing is removed from the Preferences payload and is
re-hosted inside `Manage Accounts`; the existing governor selection, current-linkage authorization,
VIP labels/range/not-set semantics, persistence, and read-only display elsewhere remain unchanged.


Phase 5F supersession: the above Inventory-visibility rules remain the accurate Phase 5E delivery
record, but they are not the target end state. Phase 5F removes the only public-report consumer and
then removes Inventory visibility from the Preferences payload, renderer, fallback, Manage journey,
service, and DAL. The regional profile, local-time/UTC-reference, atomic field writes, Accounts-owned
VIP journey, avatar, fallback, and attachment lifecycle remain authoritative.

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
  pre-commit, hosted quality checks.
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

### Phase 5C-5G — Premium Page Alignment And Surface Consolidation

Status: `Phases 5C Accounts, 5D Reminders, 5D.1 Next Alert, 5E Preferences, and 5F Inventory consolidation are complete and operator accepted; Phase 5G Account Data Export Consolidation is implemented on its working branch and is in validation/review before operator smoke and promotion`.

Accounts, Reminders, and Preferences share the accepted private standalone-card lifecycle.
The previously planned fifth summary card for Inventory has been cancelled because the selected-
governor dashboard and premium direct reports already provide the clearer product model. Phase 5F is
therefore an atomic command/UX/data-dependency cleanup rather than a new renderer.

Shared page contract that remains authoritative:

- Accounts, Reminders, and Preferences use standalone private attachments
  with same-authorized-payload fallbacks, off-event-loop rendering, deliberate attachment replacement,
  and complete file/stream cleanup.
- The invoking-user avatar, long/Unicode fitting, author gating, stale/foreign/forged/concurrent
  denial, selected-Dashboard return context, and graceful timeout rules remain unchanged.
- Discord-user/all-linked pages do not show `Change Governor`. Selected-governor dashboard,
  Resources, Speedups, Materials, and future History may use the author-gated paged selector with
  access recheck. Phase 5G locks Account Data downloads to all-linked scope with no governor dropdown.
- Phase 5F did not add a broad renderer/view framework. It removed the obsolete Inventory-specific
  generic path and left the remaining Exports migration to Phase 5G.
- Phase 5F landed command retirement and Preferences visibility removal together, so no dead setting
  or uncontrolled public legacy path remains.
- Current report, import, audit, export, filename, calculation, and Google Sheets contracts remain
  owned by their existing modules.

Remaining-phase consistency matrix:

| Phase | Parent scope | Output baseline | Governor routing | Product/behavior boundary |
|---|---|---|---|---|
| 5D Reminders | Discord user | Complete 1702x924 standalone card and same-payload fallback | No Change Governor | Complete and operator accepted; reminder semantics unchanged |
| 5D.1 Next alert | Discord user | Accepted Phase 5D card with authoritative projection | No Change Governor | Complete and operator accepted; shared scheduler parity, no side effects |
| 5E Preferences | Discord user | Accepted 1702x924 `me_preferences.png` card | No parent dropdown; Accounts owns VIP | Complete and deployed; Phase 5F retains regional profile/local-time and intentionally retires the transitional Inventory privacy feature |
| 5F Inventory consolidation | Commands, navigation, Preferences dependency, legacy controller | No new Inventory summary card; accepted Preferences card and existing 1400x980 reports retained | Direct report pages retain selected-governor resolver and Change Governor | Complete and operator accepted; four routes, public/All viewing and combined export retired; imports, audits, private reports, report-page exports, calculations, filenames, and dormant SQL table preserved |
| 5G Account Data Export Consolidation | All linked accounts under Account Summary | Full workbook, current snapshot CSV, raw history CSV | No Change Governor; active registry revalidation at Download | Implemented on working branch; `/me exports` and `/my_stats_export` removed, Download data canonical, identified output defects corrected, no SQL deployment; validation/operator acceptance pending |
| 6 Interactive Personal Stats Experience | `/my_stats` replacement/migration | Separately approved private interactive presentation | Decide `/me stats`, ALL/account selector, periods, channel policy, and migration | Personal downloads remain owned by Account Summary; remove `/my_stats` rather than retain a permanent redirect only after approval |
| 7 History | Selected governor | Accepted selected-governor standalone lifecycle | Paged Change Governor with access recheck | Preserve public/channel-gated `/kvk history`; add private `/me history` only |
| 8 Inspect | Explicit lookup target, inspect-safe | Private permission-gated premium output | Inspect lookup/ambiguity resolution | Approve permissions, safe fields/VIP, lookup, and telemetry first |
| 9 Migration review | Evidence only | No new renderer implied | No selector change implied | Review remaining legacy commands only; Phase 5F Inventory retirements are already separately evidenced and approved |

Every phase starts with repository inspection and an approval-gated implementation plan. Historical
phase records remain accurate for what was delivered at that time; later explicit product decisions
are recorded as supersessions rather than rewriting history.

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
  deferred backlog into the now-completed and archived Phase 5D.1 delivery record.
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

Status: `complete and operator accepted on 2026-07-15; task pack and starter archived`.

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

The authoritative implementation and escalation contract is retained in the archived Phase 5D.1
task pack and chat starter. Runtime uses one typed cross-system projection plus narrow KVK and Calendar pure
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
lead-time, cadence, command, SQL, or DM-content contract changed. The default KVK snapshot uses the
same injected `generated_at` UTC clock as the projection. Automated and native/desktop/mobile
visual validation passed, patch-based mirror/production promotion completed, and final operator
Discord smoke accepted the card on 2026-07-15. The final presentation makes the authoritative
event-start date-time bold gold; when several alerts are eligible, only the deterministic earliest
future candidate is shown, with KVK first on an exact tie.

#### Phase 5E - Premium Preferences Summary Card

Status: `complete and operator accepted; merged in mirror PR #224 and production PR #531 and deployed on 2026-07-16; task pack and chat starter archived`.

Approved product ownership:

- `/me preferences` remains private, author-gated, Discord-user scoped, and independent of any
  selected governor. Optional selected Dashboard context exists only for a validated Dashboard
  return and never filters Preferences content.
- The page becomes the **Personal Settings** centre for saved timezone, location, preferred-language
  metadata, derived local-time context, and Inventory privacy.
- Preferences is not a catch-all. Account data, reminder configuration, export controls, report
  controls, and unrelated defaults remain with their owning modules.
- Inventory visibility remains the single user-level privacy mutation owned by Preferences.
- Governor-specific VIP editing leaves Preferences and becomes an `Update VIP` task inside the
  existing `Manage Accounts` child journey. Existing VIP labels, range, not-set semantics,
  persistence, authorization, and read-only display elsewhere are preserved.

Approved output and visual hierarchy:

- Successful output is a standalone private `1702x924` PNG using the fully opaque runtime asset
  `assets/me/cards/me_preferences.png` and stable `me_preferences_<discord_user_id>.png` filename.
- Use the invoking user's bounded circular Discord avatar with the accepted safe fallback,
  long/Unicode fitting, and duplicate-safe Kingdom 1198 identity treatment.
- Retain the same-authorized-payload private fallback, off-event-loop rendering, deliberate
  attachment replacement, complete stream cleanup, and graceful timeout behavior established by
  Accounts and Reminders.
- The accepted card hierarchy is:

```text
PERSONAL SETTINGS                                      PRIVATE | PUBLIC
<Discord display name and Kingdom 1198>                <0-3 of 3 profile details set>

LOCAL TIME REFERENCE | UTC REFERENCE
<24-hour local time or UTC time>
<saved timezone and current DST-aware UTC offset, or set-timezone guidance>
<location and preferred-language context where available>

REGIONAL PROFILE                         PRIVACY & SHARING
Timezone                                 Inventory visibility: PRIVATE | PUBLIC
Location                                 Exact current visibility consequence
Preferred language

SETTINGS INSIGHT
<one deterministic sentence>

Manage settings
Update your regional profile and inventory privacy.

<local-time/reminder-UTC context>                       Refreshed <full UTC date-time>
```

- Header state is exactly `PRIVATE` or `PUBLIC`, based on Inventory visibility. `PUBLIC` is an
  amber/gold awareness state, not an error; `PRIVATE` uses the restrained positive treatment.
- Profile coverage counts recognised usable timezone, location, and preferred-language values.
  Optional unset fields are neutral. Do not invent READY/REVIEW/SETUP for this page.
- A valid saved timezone produces a 24-hour local-time snapshot and current UTC offset from one
  injected aware UTC timestamp, including daylight-saving and non-whole-hour offsets. The card is
  not a ticking clock and creates no timer, job, network call, or reminder behavior.
- Missing or unavailable timezone produces an honest UTC-reference hero. Do not infer timezone from
  location, language, Discord locale, device, or IP information.
- Reuse authoritative timezone/country/language catalogs and show friendly labels. Unknown legacy
  keys remain internal and are surfaced as reviewable unavailable values, not silently treated as
  valid or unset.
- Preferred language remains profile metadata; Phase 5E does not promise or implement full UI
  localization.
- Privacy copy must be traced to the exact existing Inventory visibility behavior and must not imply
  that private direct `/me resources`, `/me materials`, or `/me speedups` become public.
- Render exactly one deterministic Settings Insight using this priority: unavailable saved metadata;
  no usable timezone; public Inventory visibility; partial optional profile; complete/private
  neutral-positive guidance. Do not infer a location/timezone mismatch, nationality, fluency,
  favourite event time, or cross-player recommendation.

Approved components and child journey:

```text
Row 1: Accounts | Reminders | Preferences (active/disabled)
Row 2: Dashboard | Exports
Row 3: Manage settings
```

- Remove deprecated Inventory navigation from Preferences.
- Remove the direct `Set Public`/`Set Private`, `Update VIP`, and `Manage Profile` main buttons.
- `Manage settings` replaces the current private content in place and does not create duplicate
  child windows. It provides Regional Profile and Privacy & Sharing controls plus Back to
  Preferences.
- Preserve existing timezone/location/language catalogs, validation, save/autosave, clear/null, and
  persistence semantics. Move the three permanent top-level Clear buttons into the relevant
  field-specific update flow as a deliberate `Not set`/`Clear` choice.
- Inventory visibility changes are state-aware, explain the exact consequence, require explicit
  confirmation in both directions, revalidate current state at confirmation time, and refresh the
  parent so the privacy pill immediately reflects the saved result. Cancellation performs no write.
- Timeout preserves the last valid private content, disables controls, rejects late interactions,
  and does not refetch or rerender merely to mark timeout.

Approved VIP migration:

```text
Manage Accounts
-> Update VIP
-> explicitly select/resolve linked governor
-> select VIP level
-> save through existing service
-> recheck current linkage/access before write
-> refresh/return to Accounts management surface
```

- Add Update VIP at the current Manage Accounts task-selection level, not as a new Accounts main-card
  button.
- Zero linked governors receive register-account guidance and no write. Multiple and more-than-25
  governors use the accepted paged resolver where required. Retained Dashboard context never
  silently chooses the governor.
- Preserve existing find/register/replace/remove/confirm/cancel, slot, ownership, claim, registry,
  logging, and host-refresh behavior. Do not change Account Summary or Inventory VIP calculations.
- Preferences no longer displays or fetches per-governor VIP solely for rendering and contains no
  VIP action or governor selector.

Approved technical boundary and validation:

- Phase 5E may add a cohesive typed Preferences summary model/service and page-specific renderer,
  deterministic clock/label/coverage/insight helpers, and the narrow view refactor required for
  Manage Settings and the Accounts VIP handoff. Commands and views remain thin.
- Validate current profile, visibility, and `GovernorInventoryProfile` contracts against
  `C:\K98-bot-SQL-Server`; no SQL schema/table/view/index/procedure deployment, data migration, new
  persistence, or changed preference meaning is approved.
- No new command, grouped subcommand, redirect, default governor, time-format preference,
  application-wide local/UTC toggle, automatic detection, localization, visibility telemetry,
  broad renderer/view framework, Inventory report behavior, export behavior, or Google Sheets
  change is approved.
- Test direct entry, selected-Dashboard return, no/one/multiple/>25 linked governors, complete and
  partial profiles, DST and unusual UTC offsets, missing/unavailable saved values, public/private
  copy, deterministic insight priority, avatar/fallback, long/Unicode labels, same-payload fallback,
  render/edit/send failure, attachment cleanup, timeout/stale/foreign/forged/concurrent paths,
  Manage Settings save/clear/confirmation/cancel, and the complete VIP migration/Accounts regression.
- Produce original-size, Discord desktop, and mobile visual samples for private/public, complete,
  partial, unset-timezone, unavailable-value, long-name, and avatar-fallback states. Run focused and
  full repository validation, SQL-contract checks, Codex Security, K98 PR review, mirror deployment,
  operator Discord smoke, and production promotion checks before completion.

The authoritative implementation and escalation detail is retained in the archived Phase 5E task
pack and chat starter. Phase 5E delivered in mirror PR #224 and production PR #531 and was deployed
on 2026-07-16. Final repository validation recorded `2637 passed, 2 skipped`, with the architecture,
deferred-item, import-smoke, command-registration, log-hygiene, pre-commit, visual, security,
PR-review, and patch-based promotion gates complete. Runtime uses only the production-size backdrop
at `assets/me/cards/me_preferences.png`; no SQL deployment or data migration was required.


Phase 5F supersession decision on 2026-07-16: production usage showed no player dependency on the
only public-report consumer. Inventory visibility, the PRIVATE/PUBLIC badge, Privacy & Sharing panel,
and confirmation flow are therefore approved for coordinated retirement with `/myinventory`. The
accepted regional profile, LOCAL/UTC calculation, atomic profile writes, Accounts-owned VIP,
backdrop, avatar, fallback, attachment, and timeout contracts remain in force.

#### Phase 5F - Inventory Surface Consolidation and Legacy Retirement

Status: `complete and operator accepted after final Discord smoke on 2026-07-16; archived execution records`.

Phase 5F supersedes the previously proposed Premium Inventory Summary Card. No new Inventory summary
or backdrop will be created.

Confirmed evidence and decisions:

- `/myinventory` production usage after the replacement routes were live was two operator uses and no
  player use;
- public Inventory report posting is not required;
- the combined `All` viewing option is not required;
- `/inventory_preferences` is no longer required;
- `/me inventory` adds a redundant all-linked summary and legacy handoff rather than a better
  GovernorOS journey;
- all three routes are approved for final removal without a compatibility redirect.

Approved final Inventory model:

```text
/me dashboard -> selected-governor RSS | Speedups | Materials highlights and buttons
/me resources | /me speedups | /me materials -> private premium reports
/me exports -> private Stats exports only
/inventory import -> screenshot import
/inventory audit -> admin audit
```

Approved runtime scope:

- remove `/me inventory`, `PAGE_INVENTORY`, its navigation button, Open Report action, fallback/card
  branch, all-linked Inventory summary, and `assets/me/cards/me inventory.png`;
- remove `/myinventory`, its governor/output picker, All viewing option, public/private dispatch,
  first-use preference prompt, old range/export controller, and dedicated legacy tests;
- remove `/inventory_preferences` and its redirect;
- remove `/export_inventory`, the `/me exports` Inventory control/option window, and the combined/
  all-governor export route after successful smoke and explicit operator approval;
- remove Inventory visibility from Personal Settings and reflow the accepted
  `assets/me/cards/me_preferences.png` card around regional profile and LOCAL/UTC context;
- use `LOCAL` for a usable saved timezone and `UTC` for the honest fallback; these are derived display
  states, not new preferences;
- make `Manage settings` open the regional-profile journey directly where safe;
- remove the visibility enum, read/write service/DAL, confirmation service, and generic summary reads
  only after the exact caller audit proves no supported consumer remains;
- stop unrelated Reminders/Exports page loads from performing obsolete all-linked Inventory or
  visibility reads;
- reduce top-level command count from 42 to 39 and `/me` grouped subcommands from 9 to 8;
- resync Discord application commands after deployment.

Explicit preservation boundary:

- `/inventory import` and `/inventory audit`;
- selected-governor dashboard Inventory highlights;
- `/me resources`, `/me speedups`, and `/me materials`;
- access rechecks, tabs, 1M/3M/6M/12M, no-data guidance, Change Governor, Dashboard return, private
  report exports, attachment lifecycle, stable filenames, and premium 1400x980 backdrops;
- dashboard/Accounts latest Inventory snapshot and current-RSS helpers;
- Inventory calculations, imports, audits, and the three report-page export schemas, formats,
  windows, filenames, and Google Sheets behavior;
- `dbo.InventoryReportPreference` and existing rows, left dormant for rollback and a later separately
  approved SQL cleanup.

Phase 5F is one coordinated bot deployment with two implementation workstreams: Inventory command/
legacy-controller retirement and Personal Settings visibility removal. They must not be promoted as
independent production states. No SQL change, data migration, new asset, public sharing replacement,
or broad renderer framework is approved.

The authoritative completed implementation, audit, security-routing, test, rollback, and deployment
record is archived in:

- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5F Inventory Surface Consolidation and Legacy Retirement.md`
- `docs/task_packs/archive/Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5F Inventory Surface Consolidation and Legacy Retirement.md`

#### Phase 5G - Account Data Export Consolidation

Status: `working-branch implementation complete; final validation/review, operator smoke, and promotion pending`.

Approved canonical journey:

```text
/me accounts
-> Account Summary
-> Download data
```

Approved outputs:

- **Full workbook (`.xlsx`) - default:** `ACCOUNT_SUMMARY`, `README`, `ALL_DAILY`, then one sheet per
  linked governor. It is the single formatted file for Excel and Google Sheets compatibility.
- **Current snapshot (`.csv`):** the exact existing 29-column Account Summary contract, one row per
  linked governor, with no history query.
- **Raw stats history (`.csv`):** one row per distinct authorised linked governor per source date,
  using 30/60/90/180/360-day choices and a 90-day default.

Locked command and navigation outcome:

- remove `/me exports` rather than building another summary card;
- remove `/my_stats_export` rather than retaining a redirect-only route with discarded options;
- remove Exports navigation from Dashboard, Accounts, Account Summary, Reminders, Preferences, and
  every child/fallback path;
- retain `/my_stats` unchanged for Phase 6;
- target command counts are 38 top-level, 7 `/me`, and 2 `/inventory`.

Locked correctness work:

- use an exact inclusive N-day contract everywhere: start = latest source date - N + 1;
- filter `ALL_DAILY`, account tables, charts, and raw CSV to that same window;
- report rows actually written and exact earliest/latest dates;
- make Account Summary the first sheet and remove the weaker duplicate INDEX unless dependency audit
  requires an explicit compatibility escalation;
- calculate Forts using the selected period rather than a hidden fixed 180 days;
- apply formula-leading text protection consistently across CSV and workbook output;
- report Stats freshness, Inventory freshness, and generated UTC separately;
- replace separate Excel/Google Sheets choices with one truthful `.xlsx` compatibility option;
- preserve complete temporary-file, stream, Discord-file, cancel, timeout, and exception cleanup.

Scope remains all-linked and private. There is no selected-governor export mode, no Change Governor,
no dashboard Export Stats action, no central Inventory export, no live Google Sheets API, and no SQL
change/deployment. Resources, Speedups, and Materials retain their selected-governor report-page
exports unchanged.

Authoritative active records:

- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5G Account Data Export Consolidation.md`
- `docs/task_packs/Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5G Account Data Export Consolidation.md`

### Phase 6 — Interactive Personal Stats Experience And `/my_stats` Migration

Status: `proposed after Phase 5G acceptance; separate product workshop and task pack required`.

Goal: transform the current interactive `/my_stats` experience without reopening personal download
ownership.

Phase 6 must separately decide:

- the future `/me stats` grouped path and exact command-count effect;
- private/channel behavior and current channel-gate migration;
- ALL versus one-account selector semantics;
- Yesterday, This Week, Last Week, This Month, Last Month, Last 3M, and Last 6M behavior;
- presentation, chart, performance, fallback, timeout, and accessibility contracts;
- player communication, observation, final `/my_stats` removal rather than a permanent redirect,
  command resync, rollback, and smoke.

Account Summary remains the owner of current snapshot and downloadable history outputs. Phase 6 does
not create another download route unless a later explicit scope change demonstrates a distinct need.

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
- Separate player and leadership workflow analysis for `/my_stats`, `/stats player`,
  `/player_profile`, `/mykvkcrystaltech`, and `/kvk history`. Phase 5F Inventory retirements are
  already evidenced and approved and are not reopened here.
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
  private paginated Account Summary with canonical Download data outputs.
- Premium Discord-user Reminders summary with authoritative next-alert projection and unchanged
  Manage flow.
- Premium Discord-user Personal Settings summary with deterministic local-time/UTC reference,
  regional-profile coverage, one Settings Insight, and atomic field-specific profile management.
- Narrow migration of governor-specific VIP editing into Manage Accounts.
- Direct private selected-governor Resources, Speedups, and Materials reports.
- Phase 5F retirement of the redundant `/me inventory`, `/myinventory`,
  `/inventory_preferences`, public Inventory posting, combined All viewing, and obsolete visibility
  application dependency.
- Preservation of Inventory imports, audits, calculations, and report-page private exports,
  filenames, backdrops, and Google Sheets behavior.
- Phase 5G retirement of `/me exports` and `/my_stats_export`, removal of Exports navigation,
  Account-Summary-owned Full workbook/Current snapshot/Raw history outputs, and correction of the
  approved export-window, row-count, sheet, Forts, safety, freshness, and format-label defects.
- Private `/me` KVK history entry point.
- Leadership/admin `/me inspect`, later and separately permission-gated.
- Usage-based migration planning for remaining legacy/specialist commands.
- Documentation, tests, command reference updates, command-cache governance, and deferred
  optimisation capture.

## 14. Out of Scope for the First Implementation Build

- Redirecting or removing `/my_stats`, `/stats player`, `/player_profile`, `/mykvkcrystaltech`, or
  `/kvk history` without their own evidence and approval.
- Dropping or migrating `dbo.InventoryReportPreference` during Phase 5F.
- Adding a replacement public Share Report action.
- Adding Olympia fields.
- SQL schema changes unless a later phase explicitly approves them.
- Changing public/channel-gated KVK behavior.
- Changing Inventory import, audit, calculation, report, range, filename, export schema, or Google
  Sheets behavior.
- Folding CrystalTech into `/me`.
- Website or external dashboard work.
- Public launch comms before the visible dashboard is ready.
- New Preferences fields, automatic timezone/location detection, default governor, time-format
  preference, application-wide local/UTC toggle, or full localization without a separate approval.
- Broad renderer/view consolidation before Phase 5G Exports is complete.

## 15. Likely Source Commands and Areas

### Commands to audit or touch across the programme

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me resources
/me speedups
/me materials
/me exports
/my_stats
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
ui/views/inventory_report_views.py (Phase 5F retirement candidate)
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
- Preserve top-level command count unless explicitly approved. Phase 5F reduced the surface to 39 top-level and 8 `/me`; Phase 5G explicitly approves 38 top-level and 7 `/me` by removing `/my_stats_export` and `/me exports`. `/inventory` remains 2.
- Prefer grouped `/me` subcommands over new flat commands.
- Keep all player dashboard, direct Inventory report, and personal export output private unless a future separately approved sharing workflow says otherwise.
- Keep settings ownership singular: after Phase 5F, Preferences owns regional profile/local-time context and Accounts owns governor-specific VIP editing; no retained module owns an Inventory report visibility setting.
- Recheck access for governor-specific actions.
- Do not leak Discord-user private settings into leadership inspect mode.
- Avoid direct SQL in command and view layers.
- Validate SQL contracts against the SQL repo before relying on fields.
- Keep CrystalTech outside the programme until separately approved.
- Keep `/kvk history` unchanged when adding private `/me history`.
- Use `k98-security-review-routing` for phases touching permissions, SQL/data access, interaction
  state, or privacy-sensitive behavior. Run `codex-security:security-diff-scan` for the routine Git
  change target, or record a precise documented skip for documentation-only/mechanical work.

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
- A `k98-security-review-routing` decision when security-sensitive surfaces are touched, followed by
  `codex-security:security-diff-scan` for routine Git-backed changes or a precise documented skip.

Baseline commands to consider:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
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
- [x] Direct Resources, Materials, and Speedups paths exist and are operator accepted.
- [x] Phase 5F removes `/me inventory`, `/myinventory`, `/inventory_preferences`, and `/export_inventory` while preserving the modern private Inventory journey and report-page exports.
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
  into a completed and archived task pack/chat starter, with existing next-event reader evidence
  and strict scheduler-parity/no-side-effect boundaries recorded.
- [x] Phase 5D.1 delivers the authoritative NEXT/NO UPCOMING/UNAVAILABLE hero, deterministic shared
  clock and tie behavior, unchanged reminder contracts, final bold-gold event-start presentation,
  review/promotion evidence, and successful operator Discord smoke on 2026-07-15.
- [x] Phase 5E Preferences product/content/interaction contract, Governor's Accord backdrop, typed
  summary outline, one-action Manage Settings journey, Accounts-owned VIP migration, task pack, and
  implementation starter are recorded and approved.
- [x] Phase 5E runtime delivered the approved Personal Settings card, local-time/UTC fallback, regional
  profile, transitional Inventory privacy flow, deterministic insight, VIP migration, automated/visual
  validation, security review, and successful operator Discord smoke.
- [x] Phase 5F retains the accepted regional-profile/local-time experience while removing obsolete Inventory visibility, public posting, and legacy report controllers.
- [x] Phase 5G product, command, output, correctness, privacy, no-SQL, test, security-routing, rollback, and Phase 6 handoff decisions are recorded in the active task pack and starter.
- [x] Phase 5G working-branch runtime removes `/me exports` and `/my_stats_export`, delivers Account Summary Download data, and corrects the identified export issues.
- [ ] Phase 5G passes final validation/review, operator Discord smoke, promotion, deployment/resync, and production verification.
- [ ] A private `/me history` path exists while `/kvk history` remains unchanged.
- [ ] `/me inspect` is permission-gated, private by default, and excludes Discord-user private data.
- [x] Legacy commands are only redirected/removed after usage evidence and explicit operator approval; Phase 5F Inventory retirements meet that gate.
- [x] Documentation reflects completed phases through Phase 5F and records the accepted Inventory consolidation outcome.
- [x] Canonical command references and validators show the Phase 5G branch at 38 top-level commands, 7 `/me` subcommands, and 2 `/inventory` subcommands.
- [x] Phase 5C documentation, canonical references, automated validation, security review, visual
  samples, and successful operator Discord smoke are recorded.
- [x] Command registration validation remains green through Phase 5F.
- [x] No new direct SQL exists in command/view layers through Phase 5F.
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
- A default governor preference only after multiple GovernorOS modules have a proven need for it.
- A 12/24-hour display preference, application-wide local/UTC toggle, or full localization programme.

## 20. Suggested Next Action

```text
Execute Phase 5G Account Data Export Consolidation from the active task pack and chat starter.
Begin with repository/SQL read-only audit and exact manifest, then stop at the documented scope,
architecture, and implementation-plan approval gates.

Locked outcomes:
- /me accounts -> Account Summary -> Download data is canonical
- remove /me exports and /my_stats_export; do not retain redirect-only routes
- keep /my_stats unchanged for the separately task-packed Phase 6 redesign/migration
- provide Full workbook, Current snapshot CSV, and Raw stats history CSV
- make ACCOUNT_SUMMARY the first workbook sheet
- apply exact inclusive 30/60/90/180/360-day windows everywhere
- report actual written rows/date bounds and separate Stats/Inventory/generated freshness
- use selected-window Forts semantics and shared spreadsheet formula safety
- expose one truthful .xlsx option for Excel/Google Sheets compatibility
- preserve all three selected-governor Inventory report-page exports
- no SQL deployment, central Inventory export, selected-governor Stats export, or broad framework
```

Active Phase 5G records:

- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5G Account Data Export Consolidation.md`
- `docs/task_packs/Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5G Account Data Export Consolidation.md`

Completed Phase 5F and earlier execution records remain archived and are not rewritten.

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
| 2026-07-15 | Phase 5D.1 completed and Phase 5E handoff fixed | Recorded successful operator Discord smoke and final bold-gold event-start acceptance; retained the deterministic earliest-candidate/KVK-tie behavior and single injected UTC clock; archived the completed task pack/starter; and made Preferences the next separately scoped slice. Phase 5E keeps the accepted premium lifecycle, has no parent Change Governor, preserves current visibility/profile/VIP services, and resolves Update VIP through an explicit governor child journey. The operator will supply its task pack/background separately before runtime approval. |
| 2026-07-15 | Phase 5E Preferences contract, backdrop, task pack, and starter approved | Narrowed Preferences to Personal Settings for regional profile/local-time context and Inventory privacy; approved PRIVATE/PUBLIC state, three-field coverage, deterministic Settings Insight, one Manage Settings action, field-specific clears, deliberate privacy confirmation, and the fully opaque `assets/me/cards/me_preferences.png` Governor's Accord backdrop. Moved the existing Update VIP editor into Manage Accounts with explicit governor resolution and unchanged persistence/account rules. Runtime implementation is the next gated slice. |
| 2026-07-16 | Phase 5E completed, deployed, and archived | Recorded the accepted 1702x924 top-left-avatar Preferences card, DST-aware local-time/UTC fallback, regional profile, exact Inventory privacy flow, one Manage Settings journey, removal of deprecated Inventory navigation/VIP/Change Governor, Accounts-owned Update VIP migration, and atomic field-specific profile upsert. Mirror PR #224 and production PR #531 were merged and production deployment completed; final validation recorded 2637 passed and 2 skipped with no SQL deployment. The completed pack/starter moved to the archive and Phase 5F Inventory became the next separately task-packed slice. |
| 2026-07-16 | Phase 5F Inventory summary superseded by consolidation and retirement | Production evidence showed the only `/myinventory` user was the operator with two uses. The operator confirmed public posting, All viewing, `/inventory_preferences`, `/myinventory`, and `/me inventory` are not required. Approved one coordinated Phase 5F bot slice to remove those routes, simplify Personal Settings to regional profile plus LOCAL/UTC, delete directly orphaned code/asset/tests, reduce the command surface to 40 top-level and 8 `/me` subcommands, preserve modern private reports/imports/audits/exports, and leave `dbo.InventoryReportPreference` untouched for rollback and later SQL cleanup. |
| 2026-07-16 | Phase 5F post-smoke export and Preferences amendment | Initial Discord smoke passed. Three-month usage showed only the operator used the legacy combined Inventory export, so the operator approved removing `/export_inventory`, the `/me exports` Inventory control/window, and `InventoryReportView.ALL`, while preserving the three report-page exports. Preferences is rebalanced with Regional Profile primary, Local Time secondary, and profile coverage aligned beside LOCAL/UTC. The final command baseline is 39 top-level, 8 `/me`, and 2 `/inventory`. |
| 2026-07-16 | Phase 5F completed, operator accepted, and archived | Final Discord smoke confirmed all eight `/me` subcommands, retained reports/exports/import/audit paths, revised Personal Settings, and removal of all four retired Inventory routes. Mirror PR #225 delivered the accepted patch; production promotion branch commit `89f7da16` carries the exact patch. Final validation recorded 2590 passed and 2 skipped, zero Changes-security findings, no SQL change, and preserved dormant `dbo.InventoryReportPreference`. The task pack and starter moved to `archive/`; Phase 5G is the next slice (see next entry for its approved contract). |
| 2026-07-16 | Phase 5G Account Data Export Consolidation approved and task-packed | Confirmed the Phase 5F Inventory end state and current Stats/Accounts code. Approved Account Summary Download data as canonical, removal of `/me exports` and `/my_stats_export`, three output kinds, the full export correctness pass, no SQL deployment, and `/my_stats` redesign/migration as Phase 6. Created the active Phase 5G task pack and chat starter. |
