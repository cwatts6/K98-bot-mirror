# Repository Threat Model

K98 Bot is a Discord bot with SQL-backed game, registration, reporting, scheduler, command-cache, and operational workflows. Important assets include Discord command permissions, leadership/admin-only actions, SQL-backed match and player data, reminder and restart-sensitive state, command-cache integrity, and user-visible Discord responses.

Primary trust boundaries:
- Discord users invoke slash commands, buttons, selects, and modals.
- Permission decorators and channel gates decide whether leadership/admin workflows may run.
- Public commands must not mutate protected state or expose non-public data.
- Command lifecycle/cache code syncs and validates Discord command metadata.
- Ark services and DAL persist match, roster, reminder, ban, and audit state.

Attacker-controlled inputs include slash-command options, modal text, component interactions, Discord user/channel/guild context, uploaded files in other domains, and any user-controlled identifiers that reach DAL/service code.

Security invariants for this diff:
- Moving commands into a group must not remove existing permission decorators or channel restrictions.
- Public Ark commands must remain public only where already intended and must preserve response visibility.
- Grouped command names must be reflected in cache/version validation without creating duplicate active commands.
- Restart-sensitive Ark message, reminder, and view flows must retain their existing service/DAL behavior.
