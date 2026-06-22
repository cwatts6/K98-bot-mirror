# Archived Task Packs

This folder keeps completed task packs and chat starters for historical reference.

Player Self-Service Command Centre completed Phase 1 audit/design and Phase 2 `/me` shell
foundation execution records are archived here. The active programme pack and Phase 3 account
centre task pack remain in `docs/task_packs/`.

Archived packs include completed registry/account-resolution, telemetry, stats, pytest
log-isolation and original slow-pytest optimisation, high-priority KVK state, MGE Phase 1 polish,
PreKvK schema standardisation, completed KVK Player Experience Redesign execution phases,
completed KVK_ALL phase initiation statements, and the DL_bot upload-routing and startup/lifecycle
programmes.

The DL_bot upload-routing and startup/lifecycle optimisation programme is complete through
Phase 6L:

- `DL_bot.py` remains process-entry, command-registration, signal, and message/upload owner.
- `bot_loader.py` remains bot construction owner.
- `bot_instance.py` remains lifecycle event, startup phase, task-supervision, and bot-side graceful
  teardown owner.

Remaining related work is tracked in `docs/reference/deferred_optimisations.md` as separate future
programmes, including command-surface migration, queue-domain redesign, optional SQL-backed queue
persistence, disabled secondary command-surface cleanup, and pinned calendar tracker atomic-write
hardening.
