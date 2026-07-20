# Player Self-Service Command Centre Briefing

Last updated: 2026-07-19

GovernorOS v2 Phase 5 is complete and operator accepted through Phase 5G. Phase 5E shipped in mirror PR #224
and production PR #531 and was deployed on 2026-07-16. Phase 5F delivered in mirror PR #225, was
promoted at production-branch commit `89f7da16`, and passed final operator Discord smoke on
2026-07-16. It supersedes the proposed Premium
Inventory Summary Card and Phase 5E's Inventory-privacy ownership. Its coordinated bot release
retires `/me inventory`, `/myinventory`, and `/inventory_preferences`; removes public Inventory
posting and combined `All` viewing; and simplifies `/me preferences` to the three-field regional
profile plus derived DST-aware `LOCAL`/`UTC` context. The selected-governor dashboard and private
`/me resources`, `/me speedups`, and `/me materials` reports are the definitive viewing UX.
Inventory exports remain on the three selected-governor report pages. The legacy combined/all-governor
Inventory export, its then-current `/me exports` Inventory button, and `/export_inventory` are
retired. `/inventory import` and `/inventory audit` remain registered. No SQL change or deployment is part of Phase 5F;
`dbo.InventoryReportPreference` remains untouched for rollback.

Phase 5G Account Data Export Consolidation completed final review, command resync, and operator
Discord smoke on 2026-07-17 through mirror PR #227 and production PR #534. It replaces the old duplicate export homes
with `/me accounts -> Account Summary -> Download data`, removes both obsolete command routes and
every Exports navigation button, and keeps the output
all-linked and private. Download data offers a Full workbook, Current snapshot CSV, or Raw Stats
history CSV. The full export correctness pass is delivered, including exact inclusive windows,
filtered sheets, actual row/date metadata, Account Summary first, selected-window Forts, formula
safety, separate freshness, and one truthful Excel/Google Sheets-compatible workbook option. The
three retained Inventory report-page exports remain unchanged. Smoke accepted option reselection,
timeout, all three private files, and the restored governor-sheet workbook layout.

Phase 6 Interactive Period Performance is complete and operator accepted after final production
Discord smoke on 2026-07-18. Mirror PR #228 and production PR #535 carry the accepted bot result;
SQL PRs #43 and #44 deployed the bounded source contract first. Phase 6 adds private-anywhere
`/me stats`, adds Stats to selected-governor Dashboard row 0 after Preferences, and removes
top-level `/my_stats` without a redirect in the same bot patch. The route defaults to the selected
Dashboard governor, otherwise Main, otherwise the first valid canonical slot; All Linked is always
explicit. Overview, Activity, and Combat share the approved 1702x924 avatar-enabled card and expose
seven exact Stats-anchor periods, signed Growth/Activity/Fort/Combat metrics, truthful coverage and
state, integrated RSS/Fort trends, a same-payload accessible fallback, opaque paged selection, and
a 180-second preserve-and-disable timeout. `/stats player` and its legacy rendering stack remain.
The deployed additive SQL procedure `dbo.usp_GetPersonalStatsDaily` returns the latest anchor-date
`KingdomScanData4.ScanDate` as source refresh time; a new covering index remains deferred until
representative production plans/logical reads justify it.

Final Phase 6 operator smoke accepted every period, governor switching, All Linked, Dashboard
row-0 Stats navigation, source-correct data, the 180-second timeout, and the completed visual result.
The accepted visual refinement aligns the
card with Reminders through a bordered state pill, brighter/bolder typography, denser KPI use,
selected Governor ID, explicit Stats/Activity/Fort coverage, a Forts Total-only Activity KPI, and a
new T4+T5/Deads/Healed Combat trend. Totals and averages use consistent compact numbers; the right-
aligned pill/header stack is balanced; charts retain series names and consistent date axes without
repeating the KPI summary; `Data last refreshed` shows source time while the footer keeps generated
time. The completed task pack and starter are archived.

Phase 7 `/me` Visual Consistency, Content Audit and Programme Closeout is complete and operator
accepted after final Discord smoke on 2026-07-19. Mirror PR #229 and production PR #536 carry the
accepted bot result. It introduced only bounded shared primitives in `core/visual_contract.py` and
aligned the retained `/me` family without changing commands, SQL, payload data, metrics, formulas,
ranks, permissions, privacy, exports, or product ownership. State-pill text is now vertically
centred; Accounts, Reminders, Preferences, and Stats expose complete row-0 family navigation;
Stats Overview/Activity/Combat controls begin below that row; Accounts hero headings are
left-aligned; and Preferences now uses three regional-profile cards plus local-time,
settings-insight, and Manage panels. Dashboard and Inventory retain their specialist dimensions,
geometry, backdrops, charts, icons, ranges, exports, and category accents.

Validation passed with 120 focused tests, 143 deterministic visual renders, the full `2701 passed,
2 skipped` suite, repository validators, pre-commit/pyright, a five-receipt Codex Security Changes
scan with zero findings, and final Discord smoke. No command resync or SQL deployment was needed;
the baseline remains 37 top-level, 100 grouped, eight `/me`, and two `/inventory`. The Phase 7 task
pack and starter are archived.

Approved follow-on roadmap, updated after Phase 7 acceptance on 2026-07-19:

- The proposed `/me history` route is closed with no build. `/kvk history` remains the one
  canonical KVK-history command.
- Phase 7 is complete and archived. Its accepted visual/content/navigation/lifecycle contract is
  the baseline for later leadership cards, without transferring `/me` ownership.
- Phase 8 modernises the existing private leadership `/stats player`, adopts one canonical
  higher-is-better Tanking Score across every KVK/Account/leadership surface, adds the bounded
  leadership data/audit foundations, and removes `/player_profile` with no redirect.
- Phase 9 adds private `/stats kingdom` with current kingdom totals, twelve-month dynamic-roster
  trends, and the latest four completed KVKs. Participants are governors with final-event
  Acclaim greater than zero, and Acclaim per Participant is included.
- Phase 10 remains a usage-led review of other compatibility routes; Phase 11 remains a future
  candidate feature programme.

Phase 8 is implemented on dedicated bot and SQL branches and is in final correction validation.
SQL-first deployment, resync, and operator acceptance remain pending; Phase 9 must wait for that
acceptance.
Locked follow-on consistency:

Phase 7 proved the accepted visual hierarchy across every retained `/me` card/fallback. Core
`1702x924` summaries align closely; Dashboard retains `1180x760`; Inventory retains `1400x980` and
report-specific accents. `core/visual_contract.py` owns only proven identical primitives; a broad
renderer/grid/payload/view framework remains outside scope.

Phase 8 and Phase 9 are leadership `/stats` products, not `/me` pages. They reuse accepted
private attachment/fallback/lifecycle patterns but use dedicated stable-role-ID/channel
authorization, neutral leadership identity, their own typed payloads, and no self-view
governor picker or All Linked scope.

Both leadership phases inherit the centred top-right state pill, row-0 page-family navigation,
blue neutral/selection/UTC semantics, compact formats, accepted missing-value vocabulary,
source/generated separation, same-payload fallback, latest-transition-wins, preserve-and-disable
timeout, and cleanup. Phase 8 Change Player/linked-governor controls use exact Governor IDs or
opaque duplicate-safe tokens, page when needed, preserve page/period, disable the current choice
in blue, and revalidate permission/target access before every read; they expose no Discord account
metadata or All Linked option. Phase 9 has no governor dropdown, player picker, All Linked, or
arbitrary kingdom selector.

Canonical combat metric for every current/future surface:

```text
KP Loss = Healed Troops * 20
Tanking Score = Kill Points / (KP Loss + Deads) * 100
```

Higher is better. Phase 8 owns the coordinated correction of old KVK formulas, labels, ranking
direction, trends, exports, and playstyle copy.

The following earlier phase notes remain as historical delivery context where they describe the
state accepted at that time; Phase 5F's current surface above supersedes their legacy-route wording.

GovernorOS v2 status: Phase 4 Premium Governor Dashboard Renderer is complete and operator smoke
passed on 2026-07-11. `/me dashboard` is governor-first: no linked governor shows setup
guidance, one opens directly, and multiple use a private author-gated selector before dashboard
data is fetched. Every selected governor is checked again against the active registry. The
operator approved that registry authority based on Discord onboarding audit, monthly in-game
reconciliation, and owner-approved transfer controls. Mirror PR #217 and production PR #524 carry
the completed Phase 3 implementation and recorded smoke evidence. Mirror PR #218 carries the
Phase 4 premium PNG renderer and final smoke evidence.
Leadership review is implemented under the existing `/stats player` command with a dedicated
stable-role-ID/channel gate and private output. The coordinated branch removes `/player_profile`
without a redirect and does not create `/me inspect`; deployment and operator acceptance remain
pending.

GovernorOS v2 Phase 5A is complete in mirror PR #219 and production PR #526. Automated validation
and operator Discord smoke passed on 2026-07-13.
It delivered private selected-governor `/me resources`, `/me materials`, and `/me speedups` reports,
keeps `/me inventory` and `/myinventory` behavior unchanged, and removes the selected-dashboard
Inventory button in favor of direct RSS/Speedups/Materials actions. The selected dashboard grew
to 1180x760 and adds latest approved RSS, combined Speedups days, and legendary-equivalent
Materials totals for the selected governor only. Multiple-governor entry is governor-selector
only. Populated and honest native no-data report journeys, private exports, Dashboard navigation,
and report-preserving Change Governor controls all passed smoke. The existing 1400x980 Inventory
report renderer remained visually unchanged in Phase 5A.

Status: Phase 11A Shared Visual-Card Renderer Consolidation is delivered in mirror PR #173 and
production PR #481, and smoke tested successfully on 2026-06-26. Phase 11B KVK Renderer Migration
is delivered in production PR #482 and smoke tested successfully on 2026-06-26, moving the KVK
renderer family to the shared `core.visual_text` primitive path while preserving KVK output
contracts. Phase 11C Inventory Renderer Migration is delivered in production PR #483 and smoke
tested successfully by the operator on 2026-06-26, moving Inventory report text primitives to
`core.visual_text` while preserving report output contracts, filenames, visibility behavior,
range controls, and export buttons. Phase 11 is complete. Phase 12 Preferences Hub Expansion
Slice 1 is delivered in mirror PR #176 and smoke tested successfully by the operator on
2026-06-26, keeping `/me preferences` focused on service-backed Inventory Preferences for report
visibility and Inventory VIP. The dashboard uses the same full-bleed generated private card style
as the Phase 6 subpages, with large row-based text directly on the card background. Accounts,
Reminders, Preferences, Inventory, and Exports use generated private visual cards with safe embed
fallback. `/me inventory` summarizes latest approved inventory resources, speedups, and materials,
and `/me exports` is the preferred private export route.
Phase 12B is delivered in mirror PR #177, SQL PR #20, and production PR #485, and smoke tested
successfully by the operator on 2026-06-27. It adds SQL-backed Discord-user-level timezone,
location country, and preferred language profile preferences to `/me preferences`; country is
stored as a two-letter code and displayed with a derived readable name. Manage Profile uses guided
dropdowns and replaces the private child window after updates so repeated changes do not create
duplicate windows.
Phase 13 legacy redirect planning started with audit/scope only. After reviewing the classifications and updated usage evidence, the operator approved lightweight redirects for selected legacy player self-service commands. Production PR #486 delivered those redirects, and operator smoke testing on 2026-06-27 confirmed all approved redirects are correct. Those commands remain registered but now send private guidance to the matching `/me` centre; no command has been removed from Discord. Final command-registration removal still requires player communication, a no-feedback monitoring window, production usage review, and operator approval. The original Player Self-Service Command Centre programme is complete; remaining stats/profile/detailed-inventory alignment starts in the v2 audit/design programme.

## Player Briefing

`/me dashboard` is the private starting point for your linked governor overview.

Use it to check:

- governor identity, account type, and optional VIP
- alliance, Civilisation, `X:Y` Location, Conduct Score, and data freshness
- power, Kill Points, Highest Acclaim, Dead, Helps, and Healed
- Ark joined, won, win ratio, Times Named Autarch, and Times Autarch Participated
- where to manage Accounts, Reminders, and Preferences, or open RSS, Speedups, and
  Materials directly

The governor dashboard now uses a dedicated 1180x760 premium PNG governor card as the primary
successful presentation, with the invoking player's Discord avatar in the medallion where
available. The operator-approved private embed remains the fallback when avatar retrieval,
rendering, file creation, or image delivery fails. The successful card is delivered as a
standalone attachment for the wider KVK-style Discord presentation. Multiple-governor cards use a
Change Governor dropdown below the blue primary navigation row. `Last Login: TBC` is presentation
only until its separately approved dataset/SQL contract is delivered. Accounts, Reminders, and
Preferences now use their accepted premium presentations; the Inventory summary is retired, and
Account Data downloads now live under Account Summary. Quick
Launch links for
`/kvk stats`, `/kvk targets`,
`/kvk history`, and `/kvk rankings` remain absent because those commands have channel and
public-output rules that should stay exactly where players already use them. The dashboard keeps
only safe private handoffs for the currently delivered direct Inventory reports.

The account centre supports account review, Governor ID lookup, registration, replacement, and
removal with confirmation through one primary Manage journey. Lookup results can continue into
register or replace without asking the player to remember or re-enter the selected Governor ID.
The reminder centre supports private KVK event reminder review, setup, automatic updates, and
remove-all/unsubscribe with confirmation through one primary Manage journey. Its premium hero
shows the authoritative earliest future KVK or Calendar alert when one exists, otherwise clearly
distinguishes healthy no-upcoming state from a request-level unavailable schedule. It uses friendly
labels and absolute UTC times, highlights the event start, and never claims that Discord delivery
has occurred. The same Manage journey can open Calendar Settings for calendar reminder event types
and lead times.
`/me preferences` shows Personal Settings for saved timezone, location country, preferred-language
metadata, and a DST-aware local-time reference. Its header is `LOCAL` when the saved timezone is
usable and `UTC` otherwise. One Manage settings action opens Regional Profile directly; the field
catalogs, paging, atomic save/clear, Back navigation, timeout, avatar, fallback, and cleanup remain.
There is no Inventory visibility or Privacy & Sharing setting. VIP remains managed from Manage
Accounts -> Update VIP.
Use the selected-governor dashboard buttons or `/me resources`, `/me speedups`, and `/me materials`
for private detailed Inventory viewing. Reports retain tabs, 1M/3M/6M/12M ranges, private exports,
Dashboard return, Change Governor paging, honest no-data guidance, fallback, and cleanup. There is
no public Inventory report path and no combined `All` viewing page.
The approved Phase 5G player journey is `/me accounts -> Account Summary -> Download data`.
Players choose a formatted Full workbook, the exact Current snapshot CSV, or Raw Stats history CSV
for 30, 60, 90, 180, or 360 days. The Full workbook is the one `.xlsx` file for Excel or Google
Sheets import and starts with Account Summary. `/me exports` and `/my_stats_export` are removed rather
than kept as redirects. Resources, Speedups, and Materials retain their own private selected-governor report-page
exports. At the accepted Phase 7 production baseline, `/stats player`, `/player_profile`, and
`/mykvkcrystaltech` remain live. The Phase 8 implementation branch modernises `/stats player` and
removes `/player_profile` with no redirect; `/mykvkcrystaltech` remains outside that phase. The
production runtime changes only after SQL-first deployment, bot rollout, resync, and smoke.

Use `/me stats` for private Period Performance from any guild channel or thread. It defaults to the
current selected Dashboard governor where available and otherwise Main/first valid account. Choose
All Linked explicitly when portfolio activity is required. The report has Overview, Activity, and
Combat modes and Yesterday, This Week, Last Week, This Month, Last Month, Last 90 Days, and Last 180
Days. Exact dates and coverage appear on every result. Missing source rows are not treated as zero,
and corrections may be negative. `/me stats` has no Ark or download/export action; Account Summary
continues to own personal data downloads.

Historical Phase 13 player message draft:

```text
Personal setup is moving to /me dashboard.

Use /me dashboard as your private starting point for accounts, reminders, preferences, inventory,
and exports. The older account, reminder, preference, and export commands now point you to /me, which is the preferred place to manage personal setup.

No command has been removed from Discord yet. Please report anything you still need from an older command before final cleanup.
```

## Operator Briefing

Phase 5G completion confirms the accepted state:

- Phase 5F removed central Inventory export, `/export_inventory`, and the `/me exports` Inventory
  control; only Resources, Speedups, and Materials report-page exports remain.
- `/me exports` and `/my_stats_export` registrations are removed.
- Account Summary exposes `Download data` from the authorised all-linked payload.
- `/my_stats` remains the separate interactive command.

Completed Phase 6 deployment:

- added `/me stats` and selected-Dashboard Stats, private/ephemeral from any guild channel/thread;
- removed `/my_stats` without redirect while preserving `/stats player`;
- deployed additive `dbo.usp_GetPersonalStatsDaily` and its source-refresh result extension before
  the dependent bot patch;
- resynced to 37 top-level, 100 grouped, eight `/me`, and two `/inventory` commands;
- announced the retirement to the existing Stats-channel audience before deployment; and
- passed single, multi, 26-account, period, access-change, fallback, timeout, mobile/desktop, source-
  freshness, and `/stats player` smoke before final acceptance.

Approved next phases:

- Phase 7: no command or SQL change; visually align all retained `/me` cards/fallbacks against
  `/me stats`, preserve Dashboard/Inventory specialist layouts, and complete contact-sheet plus
  desktop/mobile review.
- Phase 8: dedicated Leadership-channel role-ID gate; admin additionally allowed in Notify;
  private `/stats player` only; 30/90/180/360 periods; Scan Presence, source coverage, ranks,
  Activity Index v1, latest/last-three completed KVK, linked governors, aliases, alliance
  history, location/shield, dedicated 90-day audit; global Tanking correction; remove
  `/player_profile`; deploy SQL before bot; resync to 36 top-level.
- Phase 9: add private `/stats kingdom`; dynamic-roster monthly final scans, current totals,
  Total Kingdom Acclaim as `SUM(HighestAcclaim)`, last four completed KVKs, KVK Acclaim as
  `SUM(Acclaim)`, participants as distinct governors with Acclaim > 0, Acclaim per Participant,
  and ratio-of-sums Tanking; resync grouped commands to 101.
Phase 6 pre-deployment Stats-channel announcement used for the accepted rollout:

```text
Personal Period Performance is moving to /me stats.

The new report is private, works from any server channel or thread, and supports Overview,
Activity, Combat, seven exact periods, your selected governor, and explicit All Linked activity.
The old /my_stats command will be removed in this deployment rather than kept as a redirect.
Personal data downloads remain under /me accounts -> Account Summary -> Download data.
Leadership /stats player is not changing. Please report any issue with /me stats in this channel.
```

Accepted Phase 5G surface:

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me resources
/me speedups
/me materials
```

Retire:

```text
/me exports
/my_stats_export
```

Validated command-registration impact:

```text
accepted Phase 5F: primary=39, /me=8, /inventory=2
accepted Phase 5G: primary=38, /me=7, /inventory=2
```

Final acceptance confirmed:

- `/me accounts -> Account Summary -> Download data` is the only central personal-data journey;
- Full workbook is default, Account Summary is first, and current/history CSV grains remain separate;
- exact 30/60/90/180/360-day inclusive filtering is identical in CSV and every workbook history
  table/chart;
- actual written row counts/date bounds, Stats freshness, Inventory freshness, and generated UTC are
  truthful;
- Forts uses the selected period;
- spreadsheet formula safety covers user-controlled text without converting negative numbers;
- Excel and Google Sheets are one `.xlsx` compatibility option;
- active registry linkage is revalidated at Download;
- no Exports button/custom ID/page/fallback/retry copy remains;
- `/my_stats` behavior, channel gate, selectors, periods, charts, and telemetry are unchanged;
- all three Inventory report-page exports remain unchanged;
- command resync removed both retired routes;
- no SQL deployment occurred.

Archived implementation records:

- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5G Account Data Export Consolidation.md`
- `docs/task_packs/archive/Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5G Account Data Export Consolidation.md`

Phase 5G final smoke-test result:

- `/me exports`, `/my_stats_export`, and all Exports navigation were absent after command resync.
- `/my_stats` remained available and behavior-compatible.
- Account Summary Download data remained private/ephemeral and produced the Current snapshot CSV,
  Raw Stats history CSV, and Full workbook successfully.
- Output and days selectors could switch away from and back to their defaults; the displayed choice
  matched the downloaded file; Cancel/download disabled the child controls; untouched views timed
  out and disabled as designed.
- The Full workbook retained the accepted KPI, sparkline, chart, and Daily table geometry on every
  governor sheet, including safe links for apostrophes in governor/sheet names.
- Resources, Speedups, and Materials retained their selected-governor report-page exports.

Phase 5F final smoke-test result:

- `/me dashboard`, accounts, reminders, preferences, resources, speedups, materials, and exports
  all worked; Accounts retained its expected data.
- `/me inventory`, `/myinventory`, `/inventory_preferences`, and `/export_inventory` were absent
  after command resync.
- Resources, Speedups, and Materials retained their private selected-governor report exports.
- `/inventory import` and `/inventory audit` remained available.
- Personal Settings retained Regional Profile and LOCAL/UTC behavior with its accepted profile-first
  reflow and direct Manage settings journey.
- No public or combined `All` Inventory viewing/export route remained. The operator confirmed the
  consolidation complete on 2026-07-16.

Phase 2 smoke-test result:

- `/me dashboard` responded privately with expected controls.
- Dashboard Quick Launch showed guidance for each linked command family.
- `/me exports` opened the exports page with page navigation only; dashboard Quick Launch remains
  dashboard-only by design.
- Existing commands continued working.

Phase 3 smoke-test result:

- `/me accounts` was private and opened the modern account centre.
- Governor ID lookup, registration, replacement, removal with confirmation, and return navigation
  were smoke tested successfully.
- Legacy account commands remained registered and usable.
- Review-feedback hardening preserved interaction defer fallback, timeout message references, all
  26 account slots, and stale-removal confirmation safety.

Known follow-up from Phase 3 smoke, addressed in Phase 6:

- The player path from `Find ID` to `Register` still has too much friction. A player can look up a
  Governor ID by name or partial name, but then needs another click and must remember or manually
  re-enter the 9-digit ID to register the account.
- Selected lookup results now carry into register/replace slot selection instead of asking the
  player to copy or remember the ID.
- Apply the same product principle to later phases: fewer buttons, fewer repeated inputs, fewer
  memory steps.

Phase 4 reminder-centre checks:

- Confirm `/me reminders` remains private.
- Confirm players can review current reminder setup.
- Confirm players can subscribe and update event types/timings through the Manage flow.
- Confirm unsubscribe requires confirmation.
- Confirm legacy reminder commands remain registered and usable.
- Confirm reminder changes send a best-effort confirmation DM and preserve scheduler/tracker
  behavior.
- Confirm reminder event categories use the delivered logic:
  - `Ruins`: non-fight ruins events.
  - `Altars`: altar fights.
  - `Major`: all major timeline events.
  - `Fights`: altar fights plus major events marked `FIGHT`.
  - overlapping choices are normalized to avoid duplicate DMs.

Phase 5 dashboard/preference checks:

- Dashboard Quick Launch remains dashboard-only and must not bypass existing channel or visibility
  rules.
- Inventory visibility writes use the existing inventory reporting service/DAL path.
- No additional preference categories should be exposed until a reliable service-backed
  persistence path exists.

Phase 5 smoke-test result:

- `/me dashboard` remained private and displayed the generated visual card.
- Card rendering was corrected for desktop, mobile, and iPad.
- The dashboard now shows one primary visual summary instead of duplicate embed and image content.
- The card copy is simplified to account status, reminder status, inventory preference status, and
  private export delivery.
- Accounts, Reminders, and Preferences opened private pages as expected.
- Reminder changes could still leave an older dashboard card visible above the reminder page until
  the player returned to Dashboard. Phase 6 addressed non-misleading refresh behavior for the
  guided card pages.

Phase 6 smoke-test result:

- `/me accounts`, `/me reminders`, `/me preferences`, and `/me exports` rendered generated visual
  cards with safe embed fallback.
- Account names and preference VIP levels wrapped readably on the generated cards.
- Account `Manage` handled Governor ID lookup, carry-forward into register/replace, early
  duplicate/invalid ID feedback, replacement, and removal confirmation.
- Reminder `Manage` auto-saved event type and reminder time changes, refreshed the card, preserved
  Phase 4 KVK reminder semantics, and supported remove-all/unsubscribe confirmation.
- Main cards and child reminder selector windows timed out gracefully with disabled controls.
- `/me preferences` used one visibility toggle and opened the existing Governor VIP update flow.
- `/me exports` remained a private guidance page without dashboard Quick Launch.
- Legacy account, reminder, inventory preference, calendar reminder, VIP update, and export
  commands remained live.

Phase 8 implementation notes:

- `/me exports` launches only validated default personal exports: Stats Excel, Stats CSV,
  Inventory Excel, and Inventory CSV.
- Stats exports reuse `services.stats_export_service.build_personal_stats_export`.
- Inventory exports reuse `inventory.export_service.build_inventory_export_file` for the player's
  registered governors, approved records, and default all-inventory view.
- Export file generation, authorization, SQL/DAL access, and cleanup remain in existing services;
  the `/me` view layer only adapts Discord button interactions to those services.
- Quick Launch expansion and legacy export redirect/removal are captured as later Player
  Self-Service programme work.
- Export schema and format redesign is captured as a separate export-output programme unless a
  later approved slice is intentionally narrow and backwards-compatible.
- Smoke testing confirmed Stats Excel, Stats CSV, Inventory Excel, and Inventory CSV all work from
  `/me exports`; all outputs are ephemeral/private; `/me dashboard` does not have a direct export
  button; dashboard Quick Launch `Exports` opens the exports card correctly; and legacy export
  commands still work.

Phase 9 implementation notes:

- `/me dashboard` no longer offers dashboard Quick Launch guidance for `/kvk stats`,
  `/kvk targets`, `/kvk history`, or `/kvk rankings`; those commands keep their existing
  channel-gated/public-output journeys.
- `/me dashboard` now offers private Inventory and Exports buttons. Inventory opens the existing
  `/myinventory` selector/report journey, including the player's current visibility preference.
  Exports opens `/me exports`.
- `/me exports` is the preferred export path and now opens option child windows for Stats and
  Inventory exports instead of showing separate fixed-format buttons.
- Phase 13 later redirected `/my_stats_export` and `/export_inventory` privately to `/me exports`
  after explicit operator approval. Final command-registration removal still requires player
  communication, no-feedback monitoring, production usage review, and operator approval.
- Smoke testing confirmed Inventory opens the existing report journey correctly and produces cards
  as expected, but the `/me` Inventory path now needs its own summary card so Inventory is not only
  represented as an export/report handoff.

Phase 10 implementation notes:

- `/me inventory` is now a sixth private `/me` subcommand.
- Dashboard Inventory opens the `/me inventory` summary card.
- The Inventory card uses the prepared `assets/me/cards/me inventory.png` background.
- The card summarizes latest approved resources, speedups, and materials across the player's
  registered governors.
- No-account and no-approved-data states stay private and point players toward inventory upload.
- Open Report preserves the existing `/myinventory` selector, report visibility behavior, range
  controls, generated report cards, and export buttons.
- `/inventory import`, `/myinventory`, `/inventory_preferences`, `/export_inventory`, and
  `/me exports` remain live and behavior-compatible.
- Smoke testing confirmed all Phase 10 cards and commands are working. A final layout polish moved
  the Inventory action block clear of the Materials row on partial-data cards.

Phase 10 smoke-test result:

- `/me inventory` remained private and rendered the generated card successfully.
- The card summarized latest approved resources, speedups, and materials.
- Partial coverage was shown conservatively and did not imply full governor coverage.
- No-account and no-approved-data states kept private guidance and pointed players toward upload.
- `Open Report` preserved the existing `/myinventory` report selector, range controls, visibility
  behavior, and export buttons.
- `/me dashboard`, `/me accounts`, `/me reminders`, `/me preferences`, `/me exports`, and legacy
  self-service commands continued working.

Phase 7 validation notes:

- Calendar reminders still use the event-calendar preference/state files and scheduler, but
  `/me reminders` now surfaces and manages those preferences through the same service-backed save
  path as `/calendar_reminder_config`.
- KVK event reminders still use the legacy subscription tracker, scheduled/sent DM trackers, and
  Phase 4 event semantics. KVK autosave and remove-all behavior should be smoke tested unchanged.
- `/me dashboard` now matches the full-bleed visual style of the Phase 6 Accounts, Reminders,
  Preferences, and Exports cards while preserving dashboard-only Quick Launch.
- Smoke testing confirmed the Phase 7 card direction is good. Follow-up polish increased
  dashboard and reminder card text size, changed the dashboard to three row groups, capped long
  calendar event lists with a `plus X more events` summary, and kept text directly on the card
  without black boxes or borders.
- The KVK and calendar reminder child windows now use the same switch-in-place journey. KVK
  reminder management can switch to calendar reminders, calendar reminder management can switch
  back to KVK reminders, and the switch/remove buttons share one row in both child windows.

Phase 11A implementation notes:

- Shared glyph-safe Pillow text primitives now live in `core.visual_text`.
- `/me` page cards use the shared text primitives directly.
- PreKvK compatibility wrappers remain in place so existing PreKvK and KVK imports keep working
  while later slices migrate away from the old helper ownership.
- The local `phase11_me_dashboard_smoke.png` artifact was rendered and inspected before handoff.
- Smoke testing confirmed `/me dashboard`, `/me inventory`, `/me accounts`, `/me reminders`,
  `/me preferences`, `/me exports`, a representative PreKvK report image path, and a representative
  KVK visual card path still worked.

Phase 11B implementation notes:

- KVK stats and targets now import `core.visual_text` directly instead of routing shared text
  primitives through `prekvk.report_image_renderer`.
- KVK history and rankings keep their KVK-local helper import path, but those helpers now resolve
  drawing through the shared primitive layer rather than the old PreKvK compatibility wrappers.
- KVK stats, targets, and rankings now measure fit widths through `core.visual_text.text_width`
  with bold-aware paths where needed, so glyph-safe clustered drawing and fitting stay aligned.
- Focused ownership regression tests prevent the KVK renderer family from reintroducing the
  PreKvK text-helper dependency.
- The local `phase11b_kvk_stats_smoke.png` artifact was rendered and inspected before handoff.
- Operator smoke validation confirmed `/kvk stats`, `/kvk targets`, `/kvk rankings`, and
  `/kvk history` visual-card paths on 2026-06-26. Special-character governor names rendered
  correctly; `phase11b_kvk_rankings_smoke.png` captures the Top 10 rankings evidence.
- Smoke validation preserves KVK image dimensions, filenames, fallback behavior, Unicode/player
  name handling, and public/private command behavior.

Phase 11C implementation notes:

- Inventory report rendering now imports `core.visual_text` directly instead of owning separate
  font loading, text width, fit-to-width, wrapping, and drawing primitives.
- Inventory chart layout, panel styling, footer generation, PNG export, filenames, report
  visibility, range controls, export buttons, fallback/no-data messages, SQL/data contracts, and
  public/private command behavior remain unchanged.
- Focused renderer tests cover shared helper ownership, glyph-safe wrapping, PNG dimensions, and
  special-character governor-name rendering.
- The local `phase11c_inventory_resources_smoke.png` artifact was rendered and inspected before
  handoff.
- Operator smoke testing completed successfully on 2026-06-26, including special-character
  rendering. Phase 11 is complete.

Phase 12 implementation notes:

- `/me preferences` is now explicitly framed as Inventory Preferences.
- The page continues to use the existing service-backed Inventory report visibility and Inventory
  VIP update paths only.
- Export defaults, stats output/privacy defaults, reminder preferences, calendar reminder
  preferences, and main-account behavior remain in their existing domain centres.
- Timezone, location country, and preferred language are confirmed as valuable future
  Discord-user-level profile settings rather than governor-level settings.
- These future values should use a dedicated SQL-backed Discord user preference/profile store, not
  duplicated columns on `dbo.DiscordGovernorRegistry`.
- The current session-based local-time toggle must remain unchanged; it supports players away
  from their usual location and should not be replaced by stored timezone metadata.

Phase 12 smoke-test result:

- `/me preferences` remained private and rendered the generated Inventory Preferences card.
- Inventory visibility saved and refreshed correctly.
- Inventory VIP update handoff worked.
- `/inventory_preferences`, `/myinventory`, `/me inventory`, `/me dashboard`, `/me accounts`,
  `/me reminders`, and `/me exports` remained behavior-compatible.
- No timezone, location country, preferred language, export-default, stats-privacy, reminder, or
  main-account controls were exposed.

Phase 12B implementation notes:

- Phase 12B adds `dbo.DiscordUserProfilePreference` in the SQL repo as the Discord-user-level
  profile preference store, keyed by Discord user ID.
- Timezone is stored as an IANA timezone name. Location country is stored as a two-letter code
  and rendered with a derived readable name. Preferred language is stored as a normalized language
  tag and rendered with a readable primary language name.
- `/me preferences` adds Manage Profile controls to set and clear the delivered profile fields,
  while preserving Inventory report visibility and Inventory VIP behavior.
- Manage Profile uses guided dropdowns for timezone, location country, and preferred language so
  players do not need to know IANA timezone keys, country codes, or language tags.
- Profile save/clear actions refresh the main generated card and replace the active private child
  window instead of sending additional child windows.
- The current session-based local-time toggle remains unchanged; saved timezone remains
  planning/profile metadata until a later approved feature uses it.

Phase 12B smoke-test result:

- `/me preferences` remained private and rendered the generated Preferences card.
- SQL deployment completed and `dbo.DiscordUserProfilePreference` was available in the live DB.
- Timezone, location country, and preferred language saved, updated, cleared, and reloaded through
  fresh interactions.
- Dropdowns worked correctly for all three profile fields.
- The generated main card refreshed after profile updates.
- The private dropdown child window was replaced correctly after updates; no additional child
  windows were created.
- Existing Inventory visibility and Inventory VIP flows remained behavior-compatible.

Current status:

- The first Player Self-Service Command Centre programme is complete after Phase 13 production
  smoke on 2026-06-27.
- Legacy account, reminder, preference, and export entry points now redirect privately to the
  matching `/me` centre.
- Final command-registration removal remains deferred until player communication, a no-feedback
  monitoring window, production usage review, and operator approval.
- GovernorOS v2 Phase 1 blueprint/audit and Phase 2 governor context/data foundation are complete
  and archived as execution records.
- GovernorOS v2 Phase 3 is complete in mirror PR #217 and production PR #524 with a
  dashboard-specific private selector, no/one/multiple/unavailable/denied journey, fallback shell,
  and in-place Change Governor behavior; operator smoke passed on 2026-07-10.
- The generic `AccountPickerView` was not wired into the dashboard; the new view reuses Phase 2
  options/access services and supports safe in-place context switching.
- Existing registry linkage is approved for Phase 3 self-view access under the operator's onboarding,
  monthly reconciliation, and transfer-control process.
- Initial Phase 3 smoke corrections cover graceful expiry, clean in-place page switching, retained
  selected-governor context, latest-scan acclaim/Ark/Autarch values, civilisation-name mapping,
  compact numbers, and removal of scan order.
- Second-pass smoke adds `KvKPlayed` participation, indexed `PlayerLocation` coordinates, clearer
  VIP wording, and a seekable governor lookup. Mixed page-card/embed visuals are parked for the
  Phase 4-6 renderer upgrades; SQL plan/IO measurement is captured before any new read model.
- Final operator smoke passed the no-governor, single-governor, multiple-governor, Change Governor,
  and corrected dashboard-data journeys on 2026-07-10.
- GovernorOS v2 Phase 4 is complete. The premium PNG governor dashboard uses the approved `me.png`
  background, optional invoking-player Discord avatar, fixed renderer/payload boundary, fallback,
  attachment lifecycle, and no-SQL/no-new-action scope. Operator smoke on 2026-07-11 exercised all
  governor options, confirmed the gated Change Governor dropdown, and accepted the materially
  larger, easier-to-read standalone image.
- GovernorOS v2 Phase 5A is complete. It delivered private direct selected-governor Resources,
  Materials, and Speedups using the existing 1400x980 standalone Inventory renderer, report
  ranges, private exports, honest native no-data output, and the author-gated paged Change Governor
  control. It preserves report type/range while switching, increases `/me` grouped subcommands
  from 6 to 9, and keeps the top-level count at 42. Operator smoke passed on 2026-07-13.
- GovernorOS v2 Phase 5B is complete. Operator smoke and final visual acceptance passed on
  2026-07-13; the operator described the finished reports as premium. The shared Inventory renderer
  uses the three supplied 1400x980 premium
  production backdrops for Resources, Speedups, Materials, and honest native no-data output. The
  2800x1960 masters remain source-only, and filenames, data, calculations, ranges, exports,
  privacy, controls, attachment lifecycle, and `/myinventory` behavior remain unchanged. Operator
  visual review accepted the premium theme/content direction and requested a presentation follow-up:
  the supplied Resources, Speedups, and Materials item icons are restored to populated and native
  no-data KPI shells, the invoking player's Discord avatar replaces the top-left report logo when
  available, and fitted KPI/chart typography is modestly larger. The final chart presentation pass
  replaces the fixed first/middle/last date labels with up to six evenly spaced genuine upload
  dates and adds density-aware diamond markers for every plotted upload. Automated validation
  passed 255 focused Inventory/dashboard tests and the full suite (`2503 passed, 2 skipped`). The
  completed Phase 5B task pack and starter are archived.
- Phase 5C Premium Accounts Summary Card is complete and operator accepted in mirror PR #221 and
  production PR #528 after final smoke on 2026-07-14. The
  avatar-enabled 1702x924 Accounts portfolio uses all linked registry entries, earned scan-health and
  coverage states, the four approved metrics, canonical current Inventory RSS, deterministic
  insight, standalone private delivery, and same-payload fallback. The unchanged guided Manage
  journey refreshes the new payload after successful mutations. Private Account Summary provides
  larger Overview, Combat, and Economy pages for every linked entry, VIP, compact Power/Troop
  Power, KP Loss and percentage-labelled Tanking Score, with Conduct grouped under Economy. The
  main roster uses a two-column governor-tile grid with prominent Power values and no redundant
  Main-governor header line. The invoking-user avatar is retained across all three summary
  sections. UTC date-times, graceful timeout controls, and a complete formula-safe CSV are retained;
  coordinates remain private. There is no Change Governor, and optional selected-governor context
  exists only for a validated Dashboard return. The completed Phase 5C task pack and starter are
  archived.
- Phase 5D Premium Reminders Summary Card is complete and operator accepted after final smoke on
  2026-07-15. The standalone 1702x924 card uses the invoking Discord avatar
  with a safe fallback and earns ACTIVE/REVIEW/OFF from the
  existing KVK and Calendar settings, presents friendly event labels, canonical alert-time labels,
  genuine counts and deterministic overflow, saved inactive choices, compact coverage, and exactly
  one priority-ordered Reminder Insight. Repository inspection found no reusable side-effect-free
  cross-system next-alert projection, so runtime uses the approved REMINDER COVERAGE hero and records
  projection extraction separately instead of copying scheduler rules. KVK autosave/update wording
  and confirmation DM, Calendar Settings, Remove All revalidation, persistence, restart/rehydration,
  duplicate-send protection, retries, schedulers, event sources, and dispatch remain unchanged.
  Delivery remains private, author-gated, same-payload on fallback, and has no Change Governor;
  selected Dashboard governor context is return-only. Focused tests passed 147, selected reminder/
  scheduler tests passed 193, and full pytest passed 2551 with 2 skipped. The ten-state native,
  desktop, and mobile visual matrix passed local review. The final host-refresh path now explicitly
  closes regenerated attachment streams in `finally`; 108 focused tests, full pytest, log-noise
  validation, and pre-commit passed on the corrected tree. Codex Security scan
  `8fcf96f6-44e0-4d87-8521-7de721444ef7` sealed with 85/85 review receipts and 42/42 candidate
  ledgers. It found no Phase 5D security issue; its 20 reportable findings (16 Medium, 4 Low) belong
  to pre-existing authorization/import/Ark/MGE repository surfaces.
  Final operator smoke accepted Manage refresh, reflected updates, graceful timeout, the invoking-
  user avatar, duplicate-safe `(1198)` identity, removal of deprecated Inventory navigation,
  right-aligned state support, and the split UTC footer with a full refreshed date-time. The
  completed Phase 5D task pack and starter are archived.
- Phase 5D.1 Authoritative Next Scheduled Alert Projection is complete and operator accepted after
  final Discord smoke on 2026-07-15. Existing `/calendar_next_event`,
  `/next_kvk_event`, and `/next_kvk_fight` remain unchanged reader-path evidence rather than reminder
  eligibility contracts. Narrow pure KVK and Calendar helpers now own the live and read-only
  eligibility semantics, while Player Self-Service bulk-loads each source/config/tracker once and
  chooses one deterministic earliest future alert. Healthy empty inputs show `NO UPCOMING ALERT`;
  required source/projection failure shows `SCHEDULE UNAVAILABLE` without turning valid saved
  configuration into REVIEW. Projection creates no tasks, DMs, acknowledgements, refreshes, network
  calls, or writes. During the section 16 audit, the operator explicitly authorised correcting the
  KVK zero-duration truthiness bug: saved `now` is now genuinely at-start eligible through the
  existing task/tracker/rehydration/retry/duplicate-send machinery. No Calendar, persistence, event
  source/type, lead-time, cadence, SQL, command-registration, or DM-content contract changed. The
  default KVK snapshot uses the same injected UTC clock as projection; the final card highlights
  `Event starts` in bold gold. Mirror PR #223 and production PR #530 carry the reviewed delivery,
  and the completed task pack/starter are archived.
- Phase 5E Preferences is complete, accepted, and deployed from mirror PR #224 and production
  PR #531. Phase 5F supersedes only its Inventory-privacy panel/journey while preserving the
  accepted 1702x924 backdrop, invoking-user avatar, standalone private attachment, same-payload
  fallback, graceful timeout, profile catalogs, atomic save/clear, and Accounts-owned VIP flow.
- Phase 5F Inventory consolidation is complete and operator accepted. It removed the legacy summary,
  public/combined viewing routes and export, visibility application code, directly orphaned
  tests/controller, `me inventory.png`, and all four retired command routes in one bot patch. It
  preserved modern selected-governor reports, dashboard highlights, Accounts RSS/Inventory As Of,
  report-specific private exports, imports, audits, and the dormant SQL table for rollback. The final
  baseline is 39 top-level while `/me` remains 8 and `/inventory` remains 2. The completed task pack
  and starter are archived.
- Phase 5G Account Data Export Consolidation is complete and operator accepted after final Discord
  smoke on 2026-07-17. It removes both obsolete export routes, keeps all personal downloads
  all-linked under Account Summary, and introduces no governor selector, Change Governor control,
  dashboard Export Stats action, or live Google Sheet. GovernorOS v2 Phase 5 is now complete.
- Phase 6 Interactive Personal Stats Experience and `/my_stats` Migration is complete and archived.
  `/me stats` owns the accepted private Period Performance format, opaque 24-governor-per-page picker
  plus explicit All Linked, exact periods, source/coverage semantics, final premium card, and safe
  lifecycle. `/my_stats` is removed without a redirect; Account Summary retains all downloads.
- The KVK history placement decision is closed: `/kvk history` remains canonical and `/me history`
  will not be implemented.
- Phase 7 completed the `/me` visual consistency, content audit, and programme closeout on
  2026-07-19, preserving the Dashboard and Inventory specialist dimensions and behaviour.
- Phase 8 modernises the existing private `/stats player`, introduces the approved leadership data,
  permission, audit, source, and canonical Tanking contracts, and removes `/player_profile` without a
  redirect. It does not create `/me inspect`.
- Phase 9 adds private `/stats kingdom` with dynamic-roster 12-month trends and the latest four
  completed KVK summaries, including Acclaim-based participants and Acclaim per Participant.
- Phase 10 is the later usage-led migration review; Phase 11 sticky features remain a future programme
  candidate rather than a committed implementation slice.
- Any broader export schema/format redesign beyond the explicitly approved Phase 5G Stats scope
  remains a separate export-output programme.
