# Player Self-Service Command Centre Briefing

Last updated: 2026-06-22

Status: Phase 3 Modern Account Centre is delivered and smoke tested successfully. Phase 4 Modern
Reminder Centre is the next active implementation phase.

## Player Briefing

`/me dashboard` is the new private starting point for personal setup.

Use it to check:

- whether your main account is set
- how many accounts are linked
- whether KVK reminders are on
- your inventory visibility preference
- where to go for KVK stats, targets, history, rankings, inventory, and exports

The account centre now supports account review, Governor ID lookup, registration, replacement,
and removal with confirmation. Existing commands such as `/register_governor`,
`/modify_registration`, `/my_registrations`, `/mygovernorid`, `/subscribe`,
`/modify_subscription`, `/unsubscribe`, `/inventory_preferences`, `/my_stats_export`, and
`/export_inventory` still work.

## Operator Briefing

Phase 3 extends `/me accounts` in parallel with legacy commands. It does not remove, redirect, or
change reminder, preference, export, KVK, stats, or inventory behavior.

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

- Confirm `/me dashboard` is private and understandable as a status dashboard.
- Confirm account, reminder, preference, and export pages are read-only.
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
- Confirm subscribe, modify, and unsubscribe flows are service-backed.
- Confirm unsubscribe requires confirmation.
- Confirm legacy reminder commands remain registered and usable.

Later mutation gates:

- Reminder writes wait for reminder centre service ownership.
- Preference writes require an existing service-backed persistence path.
- Dashboard quick launch must not bypass existing channel or visibility rules.
