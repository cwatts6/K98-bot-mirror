# Player Self-Service Command Centre Briefing

Last updated: 2026-06-24

Status: Phase 6 Guided Management Cards and Workflow Simplification is in implementation. The
dashboard keeps the Phase 5 generated private visual card with embed fallback. Accounts, Reminders,
Preferences, and Exports are moving to generated private visual cards with safe embed fallback.

## Player Briefing

`/me dashboard` is the new private starting point for personal setup.

Use it to check:

- whether your main account is set
- how many accounts are linked
- whether KVK reminders are on
- your inventory visibility preference
- where to go for KVK stats, targets, history, rankings, inventory, and exports

The dashboard includes a visual summary card when image rendering succeeds. If image rendering or
delivery fails, the bot falls back to the private embed dashboard. Dashboard Quick Launch is
available only on the dashboard page.

The account centre supports account review, Governor ID lookup, registration, replacement,
and removal with confirmation through one primary Manage journey. Lookup results can continue into
register or replace without asking the player to remember or re-enter the selected Governor ID. The
reminder centre supports private KVK event reminder review, setup, updates, and remove-all/
unsubscribe with confirmation through one primary Manage journey. `/me preferences` can update
inventory report visibility between private and public output and can open the existing Governor
VIP update flow. Existing commands such as `/register_governor`, `/modify_registration`,
`/my_registrations`, `/mygovernorid`, `/subscribe`, `/modify_subscription`, `/unsubscribe`,
`/inventory_preferences`, `/my_stats_export`, and `/export_inventory` still work.

## Operator Briefing

Phase 5 extended `/me dashboard` and `/me preferences` in parallel with legacy self-service
commands. It did not remove, redirect, or change `/inventory_preferences`, `/subscribe`,
`/modify_subscription`, `/unsubscribe`, or account legacy commands.

The approved command group is:

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me exports
```

Expected command-registration impact:

```text
primary=41
grouped_subcommands_detected=85
```

Rollout checks:

- Confirm `/me dashboard` is private and shows the generated card when rendering succeeds.
- Confirm dashboard falls back to the private embed if image rendering or delivery fails.
- Confirm the card is readable on desktop, mobile, and iPad.
- Confirm account, reminder, preference, and export pages remain private.
- Confirm `/me preferences` saves inventory report visibility through the existing service-backed
  path.
- Confirm `/me preferences` can open the existing Governor VIP update flow and that VIP writes
  remain owned by the inventory profile service path.
- Confirm dashboard Quick Launch remains dashboard-only and `/me exports` does not gain the
  dashboard Quick Launch menu.
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
- Reminder changes can still leave an older dashboard card visible above the reminder page until
  the player returns to Dashboard. This is deferred to Phase 6 with the broader guided-management
  and card-refresh work.

Phase 6 planning notes:

- Replace account button sprawl with a single Account `Manage` journey that can find a Governor
  ID, carry the selected result into register/replace, and remove accounts with confirmation.
- Replace reminder top-level `Manage` plus separate `Unsubscribe` controls with one Reminder
  `Manage` journey that supports save/update and remove-all/unsubscribe actions.
- Convert Accounts, Reminders, Preferences, and Exports pages to generated cards with safe embed
  fallback.
- Discord image areas cannot be clicked directly; use native buttons/selects aligned to the card
  sections instead.
- Phase 6 reminder work is limited to KVK event reminder subscriptions. Calendar reminders remain
  a distinct code path through `/calendar_reminder_config`, but should be revisited in a later
  unified reminder-centre phase because players experience KVK and calendar reminders as one
  reminder domain.
