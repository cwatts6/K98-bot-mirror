# Startup Runbook
## S11 readiness before caller admission — 2026-09-24

The existing runtime-services ready hook now prepares the protected export bundle before export
registration. It checks exact source/config, host/SIDs, all three SQL contracts, authority ready
handshake and spool custody. It opens no provider credentials and launches no authority. Failure
leaves actual export/capture roots closed; startup logs the failure type without private details.
A concurrent shutdown prevents late publication. G4 must separately provision/start the reviewed
authority and approve deployment; source authoring does not enable this hook's gated behavior.
See ENV_REFERENCE.md and the S11 release readiness packet for the exact manifest contract.


## S11 legacy permission prerequisite — authored 2026-09-24

The additional local permission work is approved; production startup remains closed. The Bot
machine has not pulled this work. No installation, key/proxy provisioning, restart or activation
is implied by the new SQL source or successful offline checks.

An eventual composed legacy producer with execution evidence must receive the protected version-1
legacy_sql_contract and pass its source/signature/permission checks on its own SQL session before
the producer is entered. Construction without that contract refuses. The gate checks exact target
and dbo default schema, source bodies and owners, public-only certificate mappings and signature
hashes, exact grants, absent inherited escalation/ownership and the migration receipt. It does
not commit, roll back, call a business procedure or open provider access. A refusal retains owned
work for reconciliation. The existing version-2 fixed coordination check is still separate.

G4 must first establish exact installed dependencies/output shapes, actual restricted-login and
nested transaction behavior, master/proxy/file ACLs, writer exclusion and protected receipt inputs.
Only after complete source composition, separate exact Bot/SQL Changes reviews (Deep off), delivery
approval and the operator's exact G4 actions can startup/activation be considered. G5 acceptance
remains separate. A permission check or migration-history row is never a release switch.

## S11 fixed SQL permission startup prerequisite — 2026-09-24

The authored authority and enrollment entries now require the nested SQL installation contract
and observation at version 2. A missing required budget/origin capability, unexpected evidence
column write, incomplete inventory or metadata mismatch blocks startup before session transition,
evidence-store creation or provider-child construction. The fixed map is a source prerequisite;
actual installed grants, all broader application SQL dependencies and complete runtime/issuer
composition remain unproven. Version 1 is not a fallback. See the
[version distinction](ENV_REFERENCE.md#s11-sql-permission-contract-version-2--2026-09-24)
and [offline evidence](kvk_source_migration/release_evidence_log.md#s11-fixed-coordination-permission-contract--2026-09-24).

This local authoring does not install or invoke either entry, provision credentials, register a
pool or activate the Bot. Preserve the exact separately approved G4 operations and G5 acceptance
boundary described below, including old-writer exclusion, private readback and retained uncertainty.

## S11 fresh-file enrollment gate — 2026-09-24

Enrollment is an explicit authority-side G4 operation, never Bot startup. Before any invocation,
approve the exact SQL installation/permissions, identities/builds, protected manifest/plan/credential
paths, owner consent/project/client, new file count and full writer/credential exclusion inventory.
Use the separate narrow creation profile described in [ENV_REFERENCE](ENV_REFERENCE.md#s11-enrollment-profile-contract--2026-09-24).
The authored entry is scripts/enroll_export_output_pool.py, requiring --manifest, --plan, --actor,
--reason and --authorize-operation S11_CREATE_PRIVATE_OUTPUT_POOL. This syntax is documentation,
not permission to execute it now. No token, target or real invocation is provided here.

The entry verifies protected source/plan/SQL contract before starting a session or child. It creates
private blank files and records eligibility; it does not register or activate a pool. Exact later
G4 registration uses the complete sealed origin set and must preserve pool/alias/protected-file
bounds. Missing history or an unresolved existing account blocks enrollment, without using a new
account/pool to bypass uncertainty. Trusted issuer/caller readiness must also be complete before
normal admission. Initial SQL-authoring/offline passes establish none of these runtime premises.


## S11 implementation status — 2026-09-24

Do not start the S11 provider child directly or activate the incomplete authority foundations. Launcher, immutable manifest readiness, SQL installation/permissions and all-writer composition still require completion and operator-owned G4 evidence. No automatic service installation is provided. See [checkpoint](kvk_source_migration/release_evidence_log.md#s11-approved-implementation-checkpoint--2026-09-24).


## Current status — S10E merged; S11 review/scope next, 2026-09-15

S10E Bot [mirror #280](https://github.com/cwatts6/K98-bot-mirror/pull/280),
[production #587](https://github.com/cwatts6/k98-bot/pull/587) and
[SQL #88](https://github.com/cwatts6/K98-bot-SQL-Server/pull/88) are merged and locally pulled.
Bot main/origin main `721ad7e0cd6b160ddddad328c2338a98bdfb6e0a`; production/main `3dbe63e7a47175df85ed17814ea06f9dd3d130b7`; SQL main/origin main `2352a898881d4b74d6eec153bb3cb381d6162041`.
**No changes have been pulled to the bot machine.** Repository delivery is complete;
SQL installation, real provider/Discord execution, runtime acceptance and activation remain unproven.

Next: **S11 Controlled Release and Acceptance, initial review/scope only**:
[task pack](../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md) and [starter](../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md).
Read the [S10E closeout and exact next-PR manifest](kvk_source_migration/s10e_closeout_and_s11_handoff.md).
S11 starts from S7's eight-document release proposal plus mandatory carry-forward docs;
reconcile real composition/installation/operational gaps before proposing any runtime scope.
Its eventual authorized Bot PR MUST include every listed pending document, both S10E archive
move identities, this closeout and S11 pack/starter. Verify filename AND previous_filename,
exact content and absent-at-base proof; counts are insufficient. No standalone docs PR,
mixed repositories or manufactured implementation. Pending SQL closeout edits belong only
in the next genuine authorized SQL implementation PR; otherwise carry them forward.

Preserve all recovered documentation evidence, S6-OPS01/PERF01/CAP01, both uncertain publications
and retained data. S8A six scripts, S8B 50 cases/actual restore versus offline history, and S8C
seven local checks remain distinct. S10C/D/E static authoring is not installation/provider proof.
No predecessor rerun, SQL/provider/Discord operation, bot-machine pull/restart/deployment,
activation, new task creation or Git publication is authorized by this documentation closeout.
Earlier dated pending/next-slice instructions are historical and do not reopen accepted work.

## Historical S10D closeout — 2026-09-15

SQL #87 is merged and locally pulled at `80353a6280e523f30c27e724f71e7b47dadadd16`.
Bot main/origin main remains `bf3eccf964601e2975dd86eefe96f7b0153be3bb`; production/main remains
`aa1821adbde9ccda47797caa83b5d5a9958bfce9`. **No changes have been pulled to the bot machine.**
S10D authoring, offline checks and Changes security review are complete; SQL installation and
provider/Discord execution are not established. S10C remains source/static SQL evidence too.
See [S10D closeout and exact carry-forward manifests](kvk_source_migration/s10d_closeout_and_s10e_handoff.md).

Next: **S10E Export Operator UX and Rollover, initial review/scope only**:
[task pack](../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md) and [starter](../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md).
The eventual authorized S10E Bot implementation PR MUST include every pending Bot document in
that closeout, this pack/starter and all required archive identities. Verify filename AND
previous_filename, or exact merged/content and absent-at-base proof. No standalone docs PR,
repository mixing, manufactured implementation or renewed predecessor/grouping approval.
Both SQL documents were delivered in #87; their new closeout edits stay in SQL for the next
actual authorized SQL implementation PR. S10E scope must assess any genuine SQL delta separately.

Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and every retained database/file.
S8A six scripts, S8B 50 cases/actual restore versus offline history, and S8C seven local checks
remain distinct; none is new live Discord or deployment evidence. Shutdown stops admission and
drains owned delivery; uncertainty retains claims. No lease-age/job-state release.
This documentation closeout authorizes no implementation, Git publication, SQL/provider/Discord
execution, real import/export, bot-machine action, deployment, activation, predecessor rerun or
new task. Earlier dated checkpoints are historical; the current closeout controls the next step.

Purpose: describe the bot startup sequence, guardrails, logging setup, and common failures.

## High-Level Startup Flow

1. `DL_bot.py` starts.
2. `logging_setup.py` initializes queue/file logging.
3. Environment and watchdog checks run.
4. Singleton lock and PID file are created.
5. The configured bot instance is imported.
6. Commands are registered locally.
7. Discord client starts.
8. `bot_instance.on_ready()` runs the full startup sequence.
   - `ready_runtime_bootstrap` installs the running-loop exception handler and final console
     handler cleanup.
   - `ready_runtime_services` starts heartbeat, health dashboard, offload monitor, image-show
     safety patching, legacy lock cleanup, the shared usage tracker and usage JSONL prune loop,
     daily summary, activity tracking, and server status channel loops.
   - `ready_command_sync` owns slash-command signature inventory, command-cache comparison,
     scoped command sync when signatures change, timeout telemetry, and loaded-command logging.
     Phase 6E also converged `/ops` command lifecycle admin tooling onto the same command
     lifecycle helpers while keeping Discord admin UX in `commands/admin_cmds.py`.
   - `ready_event_cache_rehydration` owns active reminder loading, event cache disk load,
     stale/empty cache refresh, and one-shot refresh scheduling.
   - `ready_event_scheduler_tasks` owns event-readiness-gated startup for live event embed
     updates, daily KVK overview updates, event reminders, reminder format refresh,
     live-event view rehydration, and event embed expiry.
   - `ready_event_cache_refresh_loop` starts the long-running event cache refresh loop at the
     existing point before tracked view rehydration.
   - `ready_view_rehydration` schedules tracked persistent view rehydration.
   - `ready_domain_scheduler_tasks` starts the Ark lifecycle scheduler, MGE cache warm, and MGE
     lifecycle scheduler.
   - `ready_queue_lifecycle` starts queue workers, awaits persisted live queue state load/apply,
     refreshes the live queue embed best-effort, and starts queue cleanup/watchdog tasks at the
     existing `full_startup_sequence()` point.
   - `ready_pinned_calendar_rehydration` schedules pinned calendar view rehydration at the
     existing later startup point after `full_startup_sequence()`.
   - `ready_calendar_scheduler_tasks` starts the daily pinned calendar refresh and calendar
     reminder loop after pinned calendar rehydration.
9. Caches, rehydration, background tasks, heartbeat, and admin notification start.

## Main Files

- `DL_bot.py` - process entrypoint, logging/env/watchdog guards, child singleton/PID setup,
  authoritative command registration, upload/message listener ownership, process signal wiring,
  and `bot.run()`.
- `bot_loader.py` - sole owner of bot singleton construction and Discord intents.
- `bot_instance.py` - lifecycle event owner for `on_ready()`, reconnect/disconnect events,
  interaction usage listening, named startup phases, task supervision, and bot-side graceful
  teardown.
- `bot_startup_gate.py`
- `boot_safety.py`
- `startup_utils.py`
- `logging_setup.py`
- `singleton_lock.py`
- `Commands.py`
- `core/command_lifecycle.py`
- `core/queue_lifecycle.py`
- `core/scheduler_lifecycle.py`

## Startup Guards

Important checks include:

- `WATCHDOG_RUN=1` for normal supervised startup
- `DISCORD_BOT_TOKEN` presence
- Windows virtualenv executable checks
- singleton lock acquisition
- PID file write
- Discord UI shadowing check
- smoke/import flags that suppress side effects during validation

## Logging

`logging_setup.py` configures:

- `logs/log.txt`
- `logs/error_log.txt`
- `logs/crash.log`
- `logs/telemetry_log.jsonl`
- `flush_logs()`
- `shutdown_logging()`

`LOG_TO_CONSOLE=1` adds console output for local debugging.

## Rehydration And Background Work

Startup may rehydrate or start:

- named lifecycle phases from `core/startup_lifecycle.py`
- command signature cache
- live queue state
- event views
- event calendar cache/runtime state
- subscription reminder tasks
- maintenance/health tasks
- heartbeat file updates

Phase 6A and 6B introduced named `on_ready()` startup phases for initial runtime bootstrap and
runtime services/observability startup. Phase 6C consolidated usage tracking onto the shared
`usage_tracker.py` singleton, with tracker startup and usage JSONL pruning owned by
`ready_runtime_services`. The unified tracker intentionally uses the previous command/decorator
cadence of a 5-second flush interval or 20-event batch size for command, component, metric, and
alert usage events. Phase 6D moved startup command signature/cache/sync handling behind
`ready_command_sync` and `core/command_lifecycle.py`. Phase 6E reused that lifecycle owner from
`/ops resync_commands`, `/ops validate_command_cache`, and `/ops show_command_versions`; production
smoke on 2026-05-28 confirmed those commands loaded, executed, flushed usage telemetry, and manual
scoped command resync completed successfully. Phase 6F completed in PR 123
(`codex/dlbot-phase-6f-event-rehydration`), was smoke tested cleanly, merged, and pushed to
production: event cache, reminder loading, tracked view rehydration, and pinned calendar
rehydration now have explicit startup lifecycle boundaries. Phase 6G completed in PR 124
(`codex/dlbot-phase-6g-scheduler-lifecycle`), was smoke tested cleanly, merged, and pushed to
production: scheduler and task-supervision startup now runs through `core/scheduler_lifecycle.py`
while preserving event readiness gating, task names, duplicate prevention, and the existing
Ark/MGE/calendar ordering. Review follow-up kept `refresh_event_cache_task` at its prior point
before tracked view rehydration via `ready_event_cache_refresh_loop` and changed Ark scheduler
registration failures to `logger.exception()` for traceback parity. Production smoke confirmed all
new scheduler phases, Ark/MGE scheduler ticks, `full_startup_sequence()`, reminder cleanup, pinned
calendar rehydration, daily pinned refresh, and calendar reminder loop startup with no startup
phase failure or `on_ready()` critical exception. Phase 6H completed in PR 125
(`codex/dlbot-phase-6h-queue-lifecycle`), was smoke tested cleanly, merged, and pushed to
production: queue worker/live queue startup now runs through `core/queue_lifecycle.py` and the
`ready_queue_lifecycle` phase while preserving the existing `full_startup_sequence()` ordering,
`TaskMonitor` duplicate prevention, live queue recovery, best-effort queue embed refresh, queue
cleanup startup, and connection watchdog startup. Production smoke confirmed the new queue phase
ran after `ready_domain_scheduler_tasks`, started workers for configured monitored channels, loaded
live queue state before embed refresh, started queue cleanup and connection watchdog once, and
allowed `full_startup_sequence()`, reminder cleanup, pinned calendar rehydration, and calendar
scheduler startup to continue normally. Phase 6I completed in PR 126
(`codex/dlbot-phase-6i-shutdown-recovery`), was merged and pushed to production: shutdown now
routes through bot-side graceful teardown before `bot.close()`, briefly drains configured
`channel_queues`, persists live queue state, cancels supervised tasks, and stops usage tracking.
Production `/ops force_restart` smoke confirmed restart recovery and startup continuity, but it did
not prove the in-process graceful shutdown log trail because `force_restart` remains a break-glass
path. Phase 6J completed in PR 127 (`codex/dlbot-phase-6j-graceful-restart-starter`), was merged,
pushed to production, and smoke tested successfully: `/ops graceful_restart` is now the preferred
safe restart path, `/ops force_restart` remains the emergency path, `/ops restart_bot` is retired,
restart marker writing and cooperative restart invocation are centralized in
`core/restart_operations.py`, and `graceful_shutdown.py` now uses a configurable cooperative
fallback timeout that defaults to 15 seconds. The 2026-05-28 smoke log confirmed queue drain, live
queue persistence, task cancellation, usage tracker stop, watchdog recovery, and startup return
through `ready_calendar_scheduler_tasks`. Phase 6K completed in PR 128
(`codex/dlbot-phase-6k-queue-persistence`), was merged, pushed to production, and smoke tested
successfully: `ready_queue_lifecycle` now awaits persisted live queue load/apply before best-effort
embed refresh, queue cache writes use the established atomic JSON helper, sync/offloaded queue
saves remain thread-safe without awaiting the main-loop lock, stale queue message metadata is
cleared/replaced during startup embed refresh, and later startup phases continue normally.
Phase 6L closed the startup/lifecycle programme by confirming the final ownership model:
`DL_bot.py` remains the process-entry and message/upload owner, `bot_loader.py` remains the bot
construction owner, and `bot_instance.py` remains the lifecycle owner. The Phase 6L code cleanup is
intentionally narrow: process PID publication and signal registration in `DL_bot.py` are wrapped in
named helpers without changing startup order, command registration, event registration, shutdown
semantics, or `bot.run()` flow.

When changing startup, verify restart safety and avoid duplicate task creation. Live queue startup
must keep the Phase 6K ordering contract: workers register first, persisted state is applied before
the embed refresh runs, and cleanup/watchdog tasks start after the best-effort refresh.

## Phase 6 Closure

The DL_bot upload-routing and startup/lifecycle optimisation programme is complete after Phase 6L.
Historical task packs and chat starters live under `docs/task_packs/archive/`. Pinned calendar
tracker atomic-write hardening was delivered independently through mirror PR #250 and production
PR #557 and passed production restart smoke on 2026-09-01. The remaining post-Phase 6 programmes
are the wider command-surface migration, queue-domain redesign, optional SQL-backed queue
persistence, disabled secondary command-surface cleanup, and SQL deployment workflow; each needs
its own scope and validation plan.

## Common Startup Failures

| Symptom | Check |
|---------|-------|
| exits immediately | `WATCHDOG_RUN`, `DISCORD_BOT_TOKEN`, venv path |
| duplicate process warning | `BOT_LOCK_PATH`, process list |
| no command sync | `GUILD_ID`, command cache, registration logs |
| no logs | `LOG_DIR`, permissions, `DISABLE_FILE_LOGGING`, smoke flags |
| rehydration fails | persisted JSON state, message/channel permissions |

## Validation

```powershell
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
python scripts/config_self_test.py
```

## S10B shared export startup boundary

The ready lifecycle calls register_exports. EXPORT_COORDINATION_ENABLED defaults false; production composition also refuses admission when the flag is true because S10C adapters and deployment attestations are not present. Startup does not open export SQL, credentials, provider clients or create spool directories through this path. Recovery completion only wakes durable export discovery.

An explicitly injected worker discovers committed intents in bounded pages and claims the oldest eligible account ticket using SQL owner/fence/version CAS over the full ordered resource set. Running A keeps its pinned vector when B arrives. A blocked/uncertain resource cannot be released by observing a terminal job state. Before any future activation, separately verify external account consumers, pool registrations, storage permissions and the retained S6/S8/S11 gates. No activation is authorized by this documentation.
