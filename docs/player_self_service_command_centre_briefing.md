# Player Self-Service Command Centre Briefing

Last updated: 2026-06-22

## Player Briefing

`/me dashboard` is the new private starting point for personal setup.

Use it to check:

- whether your main account is set
- how many accounts are linked
- whether KVK reminders are on
- your inventory visibility preference
- where to go for KVK stats, targets, history, rankings, inventory, and exports

The first version is read-only. Existing commands such as `/register_governor`,
`/modify_registration`, `/subscribe`, `/modify_subscription`, `/unsubscribe`,
`/inventory_preferences`, `/my_stats_export`, and `/export_inventory` still work.

## Operator Briefing

Phase 2 introduces `/me` in parallel with legacy commands. It does not remove, redirect, or mutate
existing account, reminder, preference, export, KVK, stats, or inventory behavior.

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

Later mutation gates:

- Account writes wait for account centre service ownership.
- Reminder writes wait for reminder centre service ownership.
- Preference writes require an existing service-backed persistence path.
- Dashboard quick launch must not bypass existing channel or visibility rules.
