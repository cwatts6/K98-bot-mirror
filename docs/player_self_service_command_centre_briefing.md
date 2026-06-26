# Player Self-Service Command Centre Briefing

Last updated: 2026-06-26

Status: Phase 11A Shared Visual-Card Renderer Consolidation is delivered in mirror PR #173 and
production PR #481, and smoke tested successfully on 2026-06-26. The dashboard uses the same
full-bleed generated private card style as the Phase 6 subpages, with large row-based text
directly on the card background. Accounts, Reminders, Preferences, Inventory, and Exports use
generated private visual cards with safe embed fallback. `/me inventory` summarizes latest
approved inventory resources, speedups, and materials, and `/me exports` remains the preferred
private export route while legacy export commands remain live.

## Player Briefing

`/me dashboard` is the new private starting point for personal setup.

Use it to check:

- whether your main account is set
- how many accounts are linked
- whether KVK reminders and calendar reminders are on
- your inventory visibility preference
- where to manage inventory and exports

The dashboard includes a visual summary card when image rendering succeeds. If image rendering or
delivery fails, the bot falls back to the private embed dashboard. Phase 9 removes dashboard Quick
Launch links for `/kvk stats`, `/kvk targets`, `/kvk history`, and `/kvk rankings` because those
commands have channel and public-output rules that should stay exactly where players already use
them. The dashboard now keeps only safe private handoffs for Inventory and Exports.

The account centre supports account review, Governor ID lookup, registration, replacement, and
removal with confirmation through one primary Manage journey. Lookup results can continue into
register or replace without asking the player to remember or re-enter the selected Governor ID.
The reminder centre supports private KVK event reminder review, setup, automatic updates, and
remove-all/unsubscribe with confirmation through one primary Manage journey. The same Manage
journey can now open Calendar Settings for calendar reminder event types and lead times.
`/me preferences` can update inventory report visibility between private and public output and can
open the existing Governor VIP update flow. `/me inventory` shows a private summary of latest
approved resources, speedups, and materials for your registered governors. If no approved
inventory data exists yet, it points you toward the inventory upload process. Open Report keeps the
existing inventory report picker, range controls, visibility behavior, and export buttons.
`/me exports` can open private option windows for Stats and Inventory exports. Stats exports
support Excel, CSV, and Google Sheets formats plus 30, 60, 90, 180, and 360 day windows,
defaulting to Excel and 90 days. Inventory exports support format, view, registered-governor
scope, and day-window choices using the existing inventory export defaults. Existing
commands such as `/register_governor`, `/modify_registration`, `/my_registrations`,
`/mygovernorid`, `/subscribe`,
`/modify_subscription`, `/unsubscribe`, `/calendar_reminder_config`, `/inventory_preferences`,
`/my_stats_export`, and `/export_inventory` still work.

## Operator Briefing

Phase 10 adds `/me inventory` as the sixth private `/me` subcommand and makes dashboard Inventory
open that generated summary card instead of jumping directly into the report selector. It does not
remove, redirect, or change `/myinventory`, `/my_stats_export`, `/export_inventory`,
`/inventory_preferences`,
`/subscribe`, `/modify_subscription`, `/unsubscribe`, `/calendar_reminder_config`, or account
legacy commands.

The approved command group is:

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me inventory
/me exports
```

Expected command-registration impact:

```text
primary=41
grouped_subcommands_detected=86
```

Rollout checks:

- Confirm `/me dashboard` is private and shows the full-bleed generated card when rendering succeeds.
- Confirm dashboard falls back to the private embed if image rendering or delivery fails.
- Confirm the card is readable on desktop, mobile, and iPad.
- Confirm account, reminder, preference, inventory, and export pages remain private.
- Confirm account, reminder, preference, inventory, and export pages render generated cards or safe
  fallback embeds.
- Confirm `/me preferences` saves inventory report visibility through the existing service-backed
  path.
- Confirm `/me preferences` can open the existing Governor VIP update flow and that VIP writes
  remain owned by the inventory profile service path.
- Confirm `/me reminders` shows KVK-only, calendar-only, both, and neither states clearly.
- Confirm `/me reminders` KVK event type and reminder time selections save automatically.
- Confirm `/me reminders` Calendar Settings saves calendar reminder event types, lead times, and enabled/disabled state.
- Confirm `/me exports` shows only `Export Stats` and `Export Inventory` controls.
- Confirm `Export Stats` opens a private child window with Format and Days selectors, defaults to
  Excel and 90 days, and sends the selected export privately from Download.
- Confirm `Export Inventory` opens a private child window with Format, View, Governor, and Days
  selectors, defaults to the existing inventory export scope, and sends the selected export
  privately from Download.
- Confirm Cancel closes each export option window without sending a file.
- Confirm `/me exports` clearly disables or reports unavailable export actions when account data,
  linked accounts, or approved export data are unavailable.
- Confirm `/me dashboard` has Inventory and Exports buttons, not the old KVK Quick Launch menu.
- Confirm dashboard Inventory opens the private `/me inventory` summary card.
- Confirm `/me inventory` uses `assets/me/cards/me inventory.png` and falls back to a private
  embed if image rendering or delivery fails.
- Confirm `/me inventory` shows resources, speedups, and materials values from latest approved
  data where available.
- Confirm `/me inventory` no-account and no-approved-data states do not leak other player data and
  point players toward the inventory upload process.
- Confirm `/me inventory` Open Report opens the same private `/myinventory` selector/report
  journey and preserves the player's inventory report visibility setting.
- Confirm `/kvk stats`, `/kvk targets`, `/kvk history`, and `/kvk rankings` remain invoked through
  their existing command paths and channel rules.
- Confirm `/my_stats_export` and `/export_inventory` still work for their existing custom options.
- Confirm legacy player commands remain registered and usable.
- Monitor `/me` usage before approving any later legacy redirects.

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
- `/my_stats_export` and `/export_inventory` remain registered and live for compatibility. Any
  redirect, deprecation, or removal still requires a later operator approval and player
  communication/no-feedback window.
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

Next phase:

- Phase 11B is the active next slice and must migrate KVK stats, targets, rankings, and history
  renderers to `core.visual_text` while preserving KVK card dimensions, filenames, image output,
  fallback behavior, Unicode/player-name handling, and existing public/private command behavior.
- Phase 11C must migrate Inventory report rendering text primitives. Phase 11 should not be
  considered complete until KVK and Inventory renderer families are migrated or the operator
  explicitly re-scopes the phase.
- Broader preferences expansion and legacy export redirect/removal remain later Player
  Self-Service phases.
- Export schema/format redesign remains a separate export-output programme unless explicitly
  narrowed later.
