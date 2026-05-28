# Archived Task Packs

This folder keeps completed task packs and chat starters for historical reference.

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
