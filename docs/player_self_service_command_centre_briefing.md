# Player Self-Service Command Centre Briefing

Last updated: 2026-06-23

Status: Phase 5 Visual Dashboard Card and Preferences Hub is implemented for local validation.
The dashboard now has a generated private visual card with embed fallback, and `/me preferences`
can update inventory visibility through the existing service-backed persistence path.

## Player Briefing

`/me dashboard` is the new private starting point for personal setup.

Use it to check:

- whether your main account is set
- how many accounts are linked
- whether KVK reminders are on
- your inventory visibility preference
- where to go for KVK stats, targets, history, rankings, inventory, and exports

The dashboard includes a visual summary card when image rendering succeeds. If image rendering or
delivery fails, the bot falls back to the private embed dashboard.

The account centre supports account review, Governor ID lookup, registration, replacement,
and removal with confirmation. The reminder centre supports private reminder review, setup,
updates, and unsubscribe with confirmation. `/me preferences` can update inventory report
visibility between private and public output. Existing commands such as `/register_governor`,
`/modify_registration`, `/my_registrations`, `/mygovernorid`, `/subscribe`,
`/modify_subscription`, `/unsubscribe`, `/inventory_preferences`, `/my_stats_export`, and
`/export_inventory` still work.

## Operator Briefing

Phase 5 extends `/me dashboard` and `/me preferences` in parallel with legacy self-service
commands. It does not remove, redirect, or change `/inventory_preferences`, `/subscribe`,
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
- Confirm account, reminder, preference, and export pages remain private.
- Confirm `/me preferences` saves inventory visibility through the existing service-backed path.
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

Known follow-up from Phase 3 smoke:

- The player path from `Find ID` to `Register` still has too much friction. A player can look up a
  Governor ID by name or partial name, but then needs another click and must remember or manually
  re-enter the 9-digit ID to register the account.
- Capture this for a later account-centre optimisation: selected lookup results should carry into
  register/replace flows instead of asking the player to copy or remember the ID.
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
