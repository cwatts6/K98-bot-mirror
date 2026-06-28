# Archived Task Packs

This folder keeps completed task packs and chat starters for historical reference.

Player Self-Service Command Centre completed Phase 1 audit/design, Phase 2 `/me` shell
foundation, Phase 3 Modern Account Centre, Phase 4 Modern Reminder Centre, Phase 5 Visual
Dashboard Card and Preferences Hub, Phase 6 Guided Management Cards and Workflow Simplification,
and Phase 7 Unified Reminder Centre and Dashboard Card Alignment execution records are archived
here. The active programme pack and next-phase task pack remain in `docs/task_packs/`.

Archived packs include completed registry/account-resolution, telemetry, stats, pytest
log-isolation and original slow-pytest optimisation, high-priority KVK state, MGE Phase 1 polish,
PreKvK schema standardisation, completed KVK Player Experience Redesign execution phases,
completed KVK_ALL phase initiation statements, and the DL_bot upload-routing and startup/lifecycle
programmes.

Import pipeline archives include Task A Import Process Schema Resilience and Shield Time Support,
which delivered fallback `Credit` / `Conduct Score` compatibility, interim auto partial fallback
overlay support, player-location shield timestamp persistence, and the temporary ASCII-safe SQL
bulk CSV hotfix. The active follow-up is Task B in `../Codex Task Pack - Import Pipeline Deferred
Optimisation Task B.md`.

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
