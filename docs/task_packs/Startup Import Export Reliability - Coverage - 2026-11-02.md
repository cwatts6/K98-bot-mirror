> **Current P02 checkpoint, 10 November 2026:** D2a–l is reviewed and merged in private PR 738 (`cd04ed5e`), not deployed. D3 has completed initial scope and defect reproduction only; D3a implementation is next. The [D3 handover, scope and authorizations](Startup%20Import%20Export%20Reliability%20-%20P02%20D3%20Handover%20and%20Scope%20-%202026-11-10.md) governs the new chat: refresh caller/edge-case coverage, then begin D3a without repeated approval. All six D3 maintenance stages, D4 legacy/final combined updater compatibility, and D5 isolated qualification remain open. Deployment is held until the planned step after D5; D2’s combined updater jump is not yet admitted and must be resolved in D4. Phase 1 remains deployed; P03 actual blockers plus essential P04 corrections precede the first standard import/export, without waiting merely for P05 or requiring zero incidents. Older dated status/approval text below is historical where superseded.

> **Current E104, 6 November 2026: P01.6 CLOSED with recorded limitations.** [Accepted closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.6%20Closeout%20-%202026-11-06.md); [P02 review/design handover](archive/Startup%20Import%20Export%20Reliability%20-%20P02%20Handover%20and%20Scope%20-%202026-11-06.md); [programme principles](Startup%20Import%20Export%20Reliability%20-%20Programme%20Principles%20-%202026-11-06.md); [documentation carry-forward](archive/Startup%20Import%20Export%20Reliability%20-%20Documentation%20Carry-forward%20-%202026-11-06.md). Final Bot `6cb5d8ed` and SQL companion are deployed. Residual intermittent Stats performance and older interaction issues are deferred until after P01-P05. P02 is next: Bot/SQL contention, observer isolation and producer budgets, plus a fresh exact dependency assessment of the six historical incidents. P03 continuation, P04 convergence, P05 combined acceptance and earlier natural observations remain open; zero incident count is not a safety gate. Earlier dated next-stage and release holds below are history. This closeout performs no production operation.

> **Historical E100, 5 November 2026: P01.5 CLOSED.** Private `24bca82f` deployed; exact custody repair, source/startup and observed normal calendar/pinned delivery accepted. See [closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.5%20Closeout%20-%202026-11-05.md), [retained natural observations](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Natural%20Acceptance%20-%202026-11-05.md) and [P01.6 handover/scope](archive/Startup%20Import%20Export%20Reliability%20-%20P01.6%20Handover%20and%20Scope%20-%202026-11-05.md). P01.6 read-worker ownership is next, review/scope only. P01.4/P01.5 natural limits, fresh whole-flow import/export and P02-P05 remain explicit. Earlier checkpoints below are historical; do not replay accepted work. Preserve this local delta through the [carry-forward manifest](archive/Startup%20Import%20Export%20Reliability%20-%20P01.6%20Delivered%20Documentation%20Carry-forward%20-%202026-11-05.md).

> **Historical E95 - 5 November 2026:** P01.4 delivered and deployed; locally qualified across the full scope; production acceptance confirmed for exercised paths, with remaining natural-activity checks tracked explicitly. See [closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.4%20Closeout%20-%202026-11-05.md), [acceptance register](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Natural%20Acceptance%20-%202026-11-05.md) and [P01.5 handover/scope](archive/Startup%20Import%20Export%20Reliability%20-%20P01.5%20Handover%20and%20Scope%20-%202026-11-05.md). P01.5 calendar ownership and outcomes (F23/F24/F25) is next, review/scope first. Earlier dated checkpoints below are historical. Carry this documentation delta through [the current manifest](archive/Startup%20Import%20Export%20Reliability%20-%20P01.5%20Delivered%20Documentation%20Carry-forward%20-%202026-11-05.md).

# Startup, import and export reliability: coverage ledger

> **Historical E91, 5 November 2026:** The [complete local qualification receipt](archive/Startup%20Import%20Export%20Reliability%20-%20P01.4%20Complete%20Local%20Qualification%20-%202026-11-05.md) records the full original P01.4 design implemented and qualified locally, with both optional workers enabled in the unpublished candidate. Cost, physical-drain, diagnostic-priority, updater, regression and Changes-review gates passed. No CSV scope was deferred. Publication/deployment and natural-activity acceptance remain outstanding; earlier E88-E90 disabled/pending statements below are historical. Existing changes and archive moves are preserved.

> **Historical E85/E86 - 5 November 2026: P01.3 CLOSED.** Passive health, persistent Refresh and the complete-ZIP correction are merged, deployed and live-validated at private `6ec393f71626d15fcb8c50c840854fb681d5f09e`. See [P01.3 closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.3%20Closeout%20-%202026-11-05.md) and [P01.4 handover/scope](archive/Startup%20Import%20Export%20Reliability%20-%20P01.4%20Handover%20and%20Scope%20-%202026-11-05.md). P01.4 (F17/F30) is next, review/scope only. P01.1/P01.2a remain accepted; P01.2b is closed by decision without feature delivery. P01.4-P01.6/P02-P05 and exact incident recovery remain open. Dated checkpoints below retain historical evidence, not current approval or scheduling authority. The [new documentation carry-forward manifest](archive/Startup%20Import%20Export%20Reliability%20-%20P01.4%20Delivered%20Documentation%20Carry-forward%20-%202026-11-05.md) covers this local closeout update.

> **Historical programme checkpoint - 4 November 2026 (E68/E69):** P01.2a is deployed and accepted for its declared reporting/evidence scope at private `67c4e12a8ecf0c25280770860480ac65a6826602`.
> Read the [P01.2a closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Closeout%20-%202026-11-04.md) for delivered corrections, evidence limits, learnings and remaining owners; [P01.2b handover](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Handover%20and%20Scope%20-%202026-11-04.md) is the next review/design task.
> The earlier checkpoint is retained history. Current remaining implementation is P01.5/P01.6/P02-P05 and exact incident recovery; P01.4 natural acceptance is tracked separately at E95. Do not replay accepted work.

Date: 2 November 2026. Main first-pass dispositions recorded; final outlier sweep not started.

This ledger attaches review evidence to all 371 historical candidate paths. It is not a
whole-module approval, test pass or production qualification. `reviewed scoped edge` means
the relevant path described by the linked finding/disposition was inspected; other paths
in large modules can remain. `boundary disposition` records inspected dependencies,
SQL/store ownership and the reason that deeper independent-domain semantics remain P1;
it is not a whole-module review or a claim that an ordinary reader cannot contend.
B01-B15 are explained in the tracing report. `action policy mapped` covers necessity, not all DAL
branches. `pending evidence reconciliation` can include earlier inspected code whose
coverage has not yet been attached; it does not mean a defect was found.

[Tracing and finding IDs](Startup%20Import%20Export%20Reliability%20-%20Tracing%20-%202026-11-02.md) |
[Action dispositions](Startup%20Import%20Export%20Reliability%20-%20Action%20Census%20-%202026-11-02.md) |
[Progress tracker](Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md)

## Reconciliation state

| State | Historical paths |
|---|---:|
| boundary disposition | 129 |
| reviewed scoped edge | 242 |

Counts measure recorded coverage, not percentage completion. Current files outside the
old seed (including the SQL dependency graph) remain part of G01 and the final fresh
inventory sweep. No path is excluded merely because it belongs to another domain.

## Historical paths

| Repository | Path | Review state | Evidence / remaining work |
|---|---|---|---|
| bot | `DL_bot.py` | reviewed scoped edge | B07: startup/shutdown physical drain and process identity are distinct from export account locks; preserve receipt-based release |
| bot | `ark/ark_preference_service.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ark/dal/ark_dal.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ark/dal/rehydration_dal.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ark/registration_flow.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ark/state/ark_state.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ark/team_state.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `bot_helpers.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `bot_instance.py` | reviewed scoped edge | F01/F08/F15/F20 |
| bot | `bot_startup_gate.py` | reviewed scoped edge | Startup scheduling/monitor boundary; no whole-domain qualification |
| bot | `commands/admin_cmds.py` | reviewed scoped edge | F11; indirect queued/typed-result safeguards |
| bot | `commands/import_resolution.py` | reviewed scoped edge | B15 / F04/F11/F28: recovery UI routes to adapters, recheck cannot invent terminal evidence; observed no-action state is a projection of closure failure |
| bot | `commands/kvk_cmds.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `commands/kvk_history_card_posting.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `commands/kvk_stats_card_posting.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `commands/kvk_targets_card_posting.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `commands/location_cmds.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `commands/mge_cmds.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `commands/prekvk_admin_cmds.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `commands/prekvk_cmds.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `commands/registry_cmds.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `commands/stats_cmds.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `commands/telemetry_cmds.py` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| bot | `constants.py` | reviewed scoped edge | B07: startup/shutdown physical drain and process identity are distinct from export account locks; preserve receipt-based release |
| bot | `core/command_lifecycle.py` | reviewed scoped edge | Startup scheduling/monitor boundary; no whole-domain qualification |
| bot | `core/export_sql_connection.py` | reviewed scoped edge | F02/F03/F09/F12 |
| bot | `core/interaction_safety.py` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| bot | `core/recovery_lifecycle.py` | reviewed scoped edge | Startup scheduling/monitor boundary; no whole-domain qualification |
| bot | `core/restart_operations.py` | reviewed scoped edge | B07: startup/shutdown physical drain and process identity are distinct from export account locks; preserve receipt-based release |
| bot | `core/scheduler_lifecycle.py` | reviewed scoped edge | Startup scheduling/monitor boundary; no whole-domain qualification |
| bot | `core/startup_diagnostics.py` | reviewed scoped edge | F01/F08/F15/F20 |
| bot | `crystaltech_service.py` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| bot | `crystaltech_ui.py` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| bot | `daily_KVK_overview_embed.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `embed_offseason_stats.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `event_cache.py` | reviewed scoped edge | Cache ownership/readback dispositions; preserve existing safeguards |
| bot | `event_calendar/cache_publisher.py` | reviewed scoped edge | F25; primary cache versus auxiliary index outcome |
| bot | `event_calendar/event_generator.py` | reviewed scoped edge | Cache ownership/readback dispositions; preserve existing safeguards |
| bot | `event_calendar/reminder_metrics.py` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| bot | `event_calendar/service.py` | reviewed scoped edge | F23/F24; explicit no-timeout-retry safeguard |
| bot | `event_calendar/sheets_sync.py` | reviewed scoped edge | F23/F24; explicit no-timeout-retry safeguard |
| bot | `event_data_loader.py` | reviewed scoped edge | Cache ownership/readback dispositions; preserve existing safeguards |
| bot | `event_embed_manager.py` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| bot | `event_scheduler.py` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| bot | `file_utils.py` | reviewed scoped edge | F01/F08/F15/F20 |
| bot | `forts_ingest.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `graceful_shutdown.py` | reviewed scoped edge | B07: startup/shutdown physical drain and process identity are distinct from export account locks; preserve receipt-based release |
| bot | `gsheet_module.py` | reviewed scoped edge | F11; indirect queued/typed-result safeguards |
| bot | `honor_importer.py` | reviewed scoped edge | F16/F17/F19 |
| bot | `inventory/audit_service.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `inventory/dal/inventory_audit_dal.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `inventory/dal/inventory_dal.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `inventory/dal/inventory_export_dal.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `inventory/dal/inventory_material_dal.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `inventory/dal/inventory_profile_dal.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `inventory/dal/inventory_reporting_dal.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `inventory/export_service.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `inventory/inventory_service.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `inventory/material_service.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `inventory/profile_service.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `inventory/reporting_service.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `kvk/dal/kvk_admin_dal.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `kvk/dal/kvk_all_import_dal.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `kvk/dal/kvk_history_dal.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `kvk/dal/kvk_lifecycle_dal.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `kvk/dal/kvk_rankings_dal.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `kvk/dal/kvk_reporting_dal.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `kvk/dal/kvk_stats_card_dal.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `kvk/dal/kvk_stats_dal.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `kvk/dal/kvk_target_publication_dal.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `kvk/dal/kvk_targets_dal.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `kvk/dal/new_source_admin_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/new_source_config_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/new_source_delivery_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/new_source_history_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/new_source_import_dal.py` | reviewed scoped edge | Recovery follow-through: clean refusal, bounded retry and exact result pacing |
| bot | `kvk/dal/new_source_publication_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/new_source_recovery_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/new_source_report_context_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/new_source_reporting_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/season_source_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/source_admin_review_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/source_calculation_refresh_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/source_output_pool_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/source_reader_activation_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/source_routing_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/source_sql_diagnostics.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/source_update_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/dal/source_weight_dal.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/services/kvk_admin_service.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `kvk/services/kvk_rankings_service.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `kvk/services/kvk_stats_card_service.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `kvk/services/kvk_targets_card_service.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `kvk/services/new_source_export_service.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/services/new_source_recovery_service.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/services/source_admin_review_service.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/services/source_export_operator_service.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/services/source_weight_service.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `kvk/target_cache_repository.py` | reviewed scoped edge | B06 / F24/F26: shared SQL fallback and physical reader lifetime; owned download worker cleanup; cache metadata and generation fencing |
| bot | `kvk_all_importer.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `leadership_player_review/dal.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `leadership_player_review/service.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `location_importer.py` | reviewed scoped edge | F16/F17/F19 |
| bot | `log_backup.py` | reviewed scoped edge | F16/F17/F19 |
| bot | `log_health.py` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| bot | `logging_setup.py` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| bot | `maintenance_worker.py` | reviewed scoped edge | F11; indirect queued/typed-result safeguards |
| bot | `mge/dal/mge_commander_dal.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `mge/dal/mge_completion_dal.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `mge/dal/mge_event_dal.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `mge/dal/mge_publish_dal.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `mge/dal/mge_results_dal.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `mge/dal/mge_roster_dal.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `mge/dal/mge_rules_dal.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `mge/dal/mge_signup_dal.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `mge/mge_publish_service.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `mge/mge_roster_service.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `player_self_service/account_service.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `player_self_service/accounts_dal.py` | reviewed scoped edge | B06 / F24/F26: shared SQL fallback and physical reader lifetime; owned download worker cleanup; cache metadata and generation fencing |
| bot | `player_self_service/accounts_service.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `player_self_service/dal/user_profile_preference_dal.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `player_self_service/governor_dashboard_dal.py` | reviewed scoped edge | B06 / F24/F26: shared SQL fallback and physical reader lifetime; owned download worker cleanup; cache metadata and generation fencing |
| bot | `player_self_service/governor_dashboard_service.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `player_self_service/profile_preference_service.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `player_self_service/service.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `player_self_service/stats_service.py` | reviewed scoped edge | B06 / F24/F26: shared SQL fallback and physical reader lifetime; owned download worker cleanup; cache metadata and generation fencing |
| bot | `player_stats_cache.py` | reviewed scoped edge | F01/F08/F15/F20 |
| bot | `prekvk/dal/import_history_dal.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `prekvk/dal/report_dal.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `prekvk/report_service.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `prekvk_importer.py` | reviewed scoped edge | F16/F17/F19 |
| bot | `proc_config_import.py` | reviewed scoped edge | F11; indirect queued/typed-result safeguards |
| bot | `processing_pipeline.py` | reviewed scoped edge | F04/F05/F06/F10/F13 |
| bot | `profile_cache.py` | reviewed scoped edge | Cache ownership/readback dispositions; preserve existing safeguards |
| bot | `registry/dal/governor_session_lock_dal.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `registry/dal/registry_dal.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `registry/registry_cache.py` | reviewed scoped edge | Cache ownership/readback dispositions; preserve existing safeguards |
| bot | `rehydrate_views.py` | reviewed scoped edge | B07: startup/shutdown physical drain and process identity are distinct from export account locks; preserve receipt-based release |
| bot | `reminder_task_registry.py` | reviewed scoped edge | B07: startup/shutdown physical drain and process identity are distinct from export account locks; preserve receipt-based release |
| bot | `run_bot.py` | reviewed scoped edge | B07: startup/shutdown physical drain and process identity are distinct from export account locks; preserve receipt-based release |
| bot | `scripts/Deploy-K98Release.ps1` | reviewed scoped edge | B07: startup/shutdown physical drain and process identity are distinct from export account locks; preserve receipt-based release |
| bot | `scripts/Update-K98.ps1` | reviewed scoped edge | B07: startup/shutdown physical drain and process identity are distinct from export account locks; preserve receipt-based release |
| bot | `scripts/prepare_k98_update.py` | reviewed scoped edge | B07: startup/shutdown physical drain and process identity are distinct from export account locks; preserve receipt-based release |
| bot | `scripts/prepare_s11_sql_account.py` | boundary disposition | B08: explicit disposable SQL rehearsals or grant text renderer; not scheduled import/export entrypoints; do not execute to refresh acceptance |
| bot | `scripts/rehearse_p0a_dependency_order.py` | boundary disposition | B08: explicit disposable SQL rehearsals or grant text renderer; not scheduled import/export entrypoints; do not execute to refresh acceptance |
| bot | `scripts/rehearse_p0a_installation_contract.py` | boundary disposition | B08: explicit disposable SQL rehearsals or grant text renderer; not scheduled import/export entrypoints; do not execute to refresh acceptance |
| bot | `scripts/rehearse_p0a_sql_image_grants.py` | boundary disposition | B08: explicit disposable SQL rehearsals or grant text renderer; not scheduled import/export entrypoints; do not execute to refresh acceptance |
| bot | `scripts/rehearse_p0a_startup_contracts.py` | boundary disposition | B08: explicit disposable SQL rehearsals or grant text renderer; not scheduled import/export entrypoints; do not execute to refresh acceptance |
| bot | `scripts/rehearse_p0a_target_business.py` | boundary disposition | B08: explicit disposable SQL rehearsals or grant text renderer; not scheduled import/export entrypoints; do not execute to refresh acceptance |
| bot | `scripts/retry_phase52_stats_import.py` | reviewed scoped edge | Indirect manual/compatibility disposition |
| bot | `scripts/run_export_authority.py` | reviewed scoped edge | B07: startup/shutdown physical drain and process identity are distinct from export account locks; preserve receipt-based release |
| bot | `scripts/smoke_kvk_source_intake.py` | boundary disposition | B08: explicit disposable SQL rehearsals or grant text renderer; not scheduled import/export entrypoints; do not execute to refresh acceptance |
| bot | `scripts/verify_k98_readiness_closeout.py` | reviewed scoped edge | B07: startup/shutdown physical drain and process identity are distinct from export account locks; preserve receipt-based release |
| bot | `server_activity/activity_store.py` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| bot | `services/account_data_export_service.py` | reviewed scoped edge | B06 / F24/F26: shared SQL fallback and physical reader lifetime; owned download worker cleanup; cache metadata and generation fencing |
| bot | `services/all_kvk_capture_recovery_dal.py` | reviewed scoped edge | F03/F09/F10; recovery snapshot and mutation-time validation matrix |
| bot | `services/all_kvk_capture_recovery_service.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/cache_admission_diagnostics.py` | reviewed scoped edge | Cache ownership/readback dispositions; preserve existing safeguards |
| bot | `services/config_preparation_recovery_dal.py` | reviewed scoped edge | F03/F09/F10; recovery snapshot and mutation-time validation matrix |
| bot | `services/config_read_recovery_adapter.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/configuration_attempt_recovery.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/configuration_continuation.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/configuration_continuation_dal.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/configuration_producer.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/configuration_read_continuation_dal.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/event_cache_service.py` | reviewed scoped edge | Cache ownership/readback dispositions; preserve existing safeguards |
| bot | `services/event_delivery_service.py` | reviewed scoped edge | B05 / F19: required entered-send evidence versus passive projections; bounded journals, physical child drain and separate SQL notification reads |
| bot | `services/event_delivery_store.py` | reviewed scoped edge | B05 / F19: required entered-send evidence versus passive projections; bounded journals, physical child drain and separate SQL notification reads |
| bot | `services/export_authority_diagnostics.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_configuration_preflight_dal.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_containment_attestation_dal.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_contention.py` | reviewed scoped edge | Recovery follow-through: clean refusal, bounded retry and exact result pacing |
| bot | `services/export_coordination_dal.py` | reviewed scoped edge | Recovery follow-through: clean refusal, bounded retry and exact result pacing |
| bot | `services/export_coordination_service.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_enrollment_service.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_evidence_catalog_dal.py` | reviewed scoped edge | Recovery follow-through: retained reads versus polling writes and action validation |
| bot | `services/export_evidence_recovery.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_execution_authority.py` | reviewed scoped edge | F02/F03/F09/F12 |
| bot | `services/export_execution_dal.py` | reviewed scoped edge | F02/F03/F09/F12 |
| bot | `services/export_execution_lock.py` | reviewed scoped edge | F02/F03/F09/F12 |
| bot | `services/export_failure_diagnostics.py` | reviewed scoped edge | F27; validator contention loses typed waiting; original diagnostics retained |
| bot | `services/export_proof_progress.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_provider_adapter.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_recovery_dal.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_recovery_service.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_registration_attestation_dal.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_replacement_activation_dal.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_replacement_authority.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_replacement_dal.py` | reviewed scoped edge | Recovery follow-through: retained reads versus polling writes and action validation |
| bot | `services/export_replacement_delivery_dal.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_replacement_recovery_adapter.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_replacement_verification_dal.py` | reviewed scoped edge | Recovery follow-through: retained reads versus polling writes and action validation |
| bot | `services/export_replacement_verification_service.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_replacement_waiting.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_replacement_workflow.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_request_budget.py` | reviewed scoped edge | Recovery follow-through: clean refusal, bounded retry and exact result pacing |
| bot | `services/export_runtime_composition.py` | reviewed scoped edge | F02/F03/F09/F12 |
| bot | `services/export_sql_health_dal.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_startup_reconciliation.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_target_admission_dal.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/export_target_containment_dal.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/failed_export_closeout.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/failed_export_closeout_dal.py` | reviewed scoped edge | F03/F09/F10; recovery snapshot and mutation-time validation matrix |
| bot | `services/failed_export_recovery_authority.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/governor_account_service.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `services/governor_lookup_service.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `services/governor_session_lock_service.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `services/gsheets_health_service.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/historical_import_recovery_dal.py` | reviewed scoped edge | F03/F09/F10; recovery snapshot and mutation-time validation matrix |
| bot | `services/historical_import_recovery_service.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/historical_retirement_group_dal.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/honor_import_audit_service.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `services/import_capture_recovery_dal.py` | reviewed scoped edge | F03/F09/F10; recovery snapshot and mutation-time validation matrix |
| bot | `services/import_recovery_service.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/inventory_import_audit_service.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `services/kvk_all_import_audit_service.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `services/kvk_personal_service.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `services/legacy_configuration_continuation.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/legacy_export_closeout.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/legacy_export_closeout_dal.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/legacy_export_snapshot_dal.py` | reviewed scoped edge | F02/F03/F09/F12 |
| bot | `services/legacy_export_snapshot_service.py` | reviewed scoped edge | F02/F03/F09/F12 |
| bot | `services/location_import_service.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `services/location_refresh_signal.py` | reviewed scoped edge | B05 / F19: required entered-send evidence versus passive projections; bounded journals, physical child drain and separate SQL notification reads |
| bot | `services/operator_status_dal.py` | reviewed scoped edge | F11 historical finding; passive presentation delivered/accepted E85, explicit write-boundary checks retained |
| bot | `services/operator_status_service.py` | reviewed scoped edge | F11 historical finding; passive presentation delivered/accepted E85, explicit write-boundary checks retained |
| bot | `services/overview_delivery_service.py` | reviewed scoped edge | B05 / F19: required entered-send evidence versus passive projections; bounded journals, physical child drain and separate SQL notification reads |
| bot | `services/pipeline_capture_handoff_dal.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/player_report_continuation_dal.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/player_report_recovery_dal.py` | reviewed scoped edge | F03/F09/F10; recovery snapshot and mutation-time validation matrix |
| bot | `services/player_report_recovery_service.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/player_stats_cache_service.py` | reviewed scoped edge | F01/F08/F15/F20 |
| bot | `services/player_stats_startup.py` | reviewed scoped edge | F01/F08/F15/F20 |
| bot | `services/prekvk_import_audit_service.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `services/processing_notification_dal.py` | reviewed scoped edge | B05 / F19: required entered-send evidence versus passive projections; bounded journals, physical child drain and separate SQL notification reads |
| bot | `services/processing_notification_service.py` | reviewed scoped edge | B05 / F19: required entered-send evidence versus passive projections; bounded journals, physical child drain and separate SQL notification reads |
| bot | `services/processing_notification_store.py` | reviewed scoped edge | F16/F17/F19 |
| bot | `services/processing_outcome_worker.py` | reviewed scoped edge | F04/F05/F06/F10/F13 |
| bot | `services/processing_pipeline_receipt_dal.py` | reviewed scoped edge | F04/F05/F06/F10/F13 |
| bot | `services/processing_pipeline_receipts.py` | reviewed scoped edge | F04/F05/F06/F10/F13 |
| bot | `services/processing_pipeline_recovery.py` | reviewed scoped edge | F04/F05/F06/F10/F13 |
| bot | `services/producer_refusal_dal.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/profile_cache_service.py` | reviewed scoped edge | Cache ownership/readback dispositions; preserve existing safeguards |
| bot | `services/profile_cache_startup.py` | reviewed scoped edge | Cache ownership/readback dispositions; preserve existing safeguards |
| bot | `services/queue_admission_recovery.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/queue_admission_recovery_dal.py` | reviewed scoped edge | F03/F09/F10; recovery snapshot and mutation-time validation matrix |
| bot | `services/rally_forts_import_audit_service.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `services/recovery_backlog_dal.py` | reviewed scoped edge | Recovery follow-through: retained reads versus polling writes and action validation |
| bot | `services/recovery_dal.py` | reviewed scoped edge | Recovery follow-through: retained reads versus polling writes and action validation |
| bot | `services/recovery_execution_guard.py` | reviewed scoped edge | Recovery follow-through: clean refusal, bounded retry and exact result pacing |
| bot | `services/recovery_health.py` | reviewed scoped edge | F04/F05/F06/F10/F13 |
| bot | `services/recovery_publication_result.py` | reviewed scoped edge | B05 / F19: required entered-send evidence versus passive projections; bounded journals, physical child drain and separate SQL notification reads |
| bot | `services/recovery_report.py` | reviewed scoped edge | F04/F05/F06/F10/F13 |
| bot | `services/recovery_runtime.py` | reviewed scoped edge | F04/F05/F06/F10/F13 |
| bot | `services/recovery_service.py` | reviewed scoped edge | F04/F05/F06/F10/F13 |
| bot | `services/replacement_admission_dal.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/rollover_containment_dal.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/rollover_replacement_adapter.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/rollover_replacement_dal.py` | reviewed scoped edge | B02 / F02/F10/F12: provider outside SQL transactions; exact settlement, containment and repeated locking snapshots distinguished |
| bot | `services/stats_import_outcome_dal.py` | reviewed scoped edge | F02/F03/F09/F12 |
| bot | `services/stats_report_continuation_dal.py` | reviewed scoped edge | F27; validator contention loses typed waiting; original diagnostics retained |
| bot | `services/stranded_export_recovery_dal.py` | reviewed scoped edge | F03/F09/F10; recovery snapshot and mutation-time validation matrix |
| bot | `services/tracked_view_store.py` | reviewed scoped edge | F01/F08/F15/F20 |
| bot | `services/unowned_sql_hold_dal.py` | reviewed scoped edge | F03/F09/F10; recovery snapshot and mutation-time validation matrix |
| bot | `services/unowned_sql_hold_recovery.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/unreceipted_producer_recovery.py` | reviewed scoped edge | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| bot | `services/weekly_activity_import_audit_service.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `sheet_importer.py` | reviewed scoped edge | Indirect manual/compatibility disposition |
| bot | `singleton_lock.py` | reviewed scoped edge | B07: startup/shutdown physical drain and process identity are distinct from export account locks; preserve receipt-based release |
| bot | `stats/dal/fallback_import_dal.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `stats/dal/immutable_import_dal.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `stats/dal/import_audit_dal.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `stats/dal/personal_stats_dal.py` | reviewed scoped edge | B06 / F24/F26: shared SQL fallback and physical reader lifetime; owned download worker cleanup; cache metadata and generation fencing |
| bot | `stats/dal/stats_export_dal.py` | reviewed scoped edge | B06 / F24/F26: shared SQL fallback and physical reader lifetime; owned download worker cleanup; cache metadata and generation fencing |
| bot | `stats/profile_cache_repository.py` | reviewed scoped edge | F26; fallback connection policy and retained first failure |
| bot | `stats_alerts/db.py` | reviewed scoped edge | B06 / F24/F26: shared SQL fallback and physical reader lifetime; owned download worker cleanup; cache metadata and generation fencing |
| bot | `stats_alerts/diagnostic_sessions.py` | reviewed scoped edge | B05 / F19: required entered-send evidence versus passive projections; bounded journals, physical child drain and separate SQL notification reads |
| bot | `stats_alerts/dispatch_reservations.py` | reviewed scoped edge | B05 / F19: required entered-send evidence versus passive projections; bounded journals, physical child drain and separate SQL notification reads |
| bot | `stats_alerts/embeds/kingdom_summary.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `stats_alerts/embeds/kvk.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `stats_alerts/embeds/offseason.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `stats_alerts/embeds/prekvk.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `stats_alerts/guard.py` | reviewed scoped edge | B05 / F19: required entered-send evidence versus passive projections; bounded journals, physical child drain and separate SQL notification reads |
| bot | `stats_alerts/honors.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `stats_alerts/interface.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `stats_alerts/kvk_diagnostic_sessions.py` | reviewed scoped edge | B05 / F19: required entered-send evidence versus passive projections; bounded journals, physical child drain and separate SQL notification reads |
| bot | `stats_alerts/offseason_dal.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `stats_alerts/processing_delivery.py` | reviewed scoped edge | B05 / F19: required entered-send evidence versus passive projections; bounded journals, physical child drain and separate SQL notification reads |
| bot | `stats_alerts/processing_notifications.py` | reviewed scoped edge | F16/F17/F19 |
| bot | `stats_alerts/recovery_notifications.py` | reviewed scoped edge | B05 / F19: required entered-send evidence versus passive projections; bounded journals, physical child drain and separate SQL notification reads |
| bot | `stats_alerts/state.py` | reviewed scoped edge | B05 / F19: required entered-send evidence versus passive projections; bounded journals, physical child drain and separate SQL notification reads |
| bot | `stats_cache_helpers.py` | reviewed scoped edge | B06 / F24/F26: shared SQL fallback and physical reader lifetime; owned download worker cleanup; cache metadata and generation fencing |
| bot | `stats_module.py` | reviewed scoped edge | F16/F17/F19 |
| bot | `target_utils.py` | reviewed scoped edge | Cache ownership/readback dispositions; preserve existing safeguards |
| bot | `targets_sql_cache.py` | reviewed scoped edge | B06 / F24/F26: shared SQL fallback and physical reader lifetime; owned download worker cleanup; cache metadata and generation fencing |
| bot | `telemetry/dal/command_usage_dal.py` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| bot | `ui/views/kvk_history_card_views.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `ui/views/kvk_history_view.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `ui/views/kvk_personal_views.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `ui/views/kvk_rankings_views.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `ui/views/kvk_source_export_view.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `ui/views/kvk_source_import_view.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `ui/views/kvk_stats_card_views.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `ui/views/leadership_player_review_views.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `ui/views/mge_admin_completion_view.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ui/views/mge_commander_admin_view.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ui/views/mge_leadership_board_view.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ui/views/mge_publish_view.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ui/views/mge_results_import_view.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ui/views/mge_results_overwrite_confirm_view.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ui/views/mge_roster_builder_view.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ui/views/mge_rules_edit_view.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ui/views/mge_signup_view.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ui/views/mge_simplified_leadership_view.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ui/views/mge_simplified_signup_view.py` | boundary disposition | B11: Ark/MGE own domain rows and board workflows; shared DB, helper cleanup and startup read edges included; detailed lifecycle acceptance stays P1 |
| bot | `ui/views/player_self_service_account_summary_views.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `ui/views/player_self_service_account_vip_views.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `ui/views/player_self_service_governor_dashboard_views.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `ui/views/player_self_service_inventory_report_views.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `ui/views/player_self_service_preference_views.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `ui/views/player_self_service_stats_views.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `ui/views/player_self_service_views.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `ui/views/prekvk_report_views.py` | boundary disposition | B13: ordinary report/read/render entrypoints use mapped KVK/profile/target DALs; no provider account settlement authority; read cost and cancellation remain A02/A04/A10 |
| bot | `ui/views/recovery_view.py` | reviewed scoped edge | B15 / F04/F11/F28: recovery UI routes to adapters, recheck cannot invent terminal evidence; observed no-action state is a projection of closure failure |
| bot | `ui/views/registry_views.py` | boundary disposition | B12: inventory/registry/preference transactions and governor leases use separate domain rows; common SQL policy/observer cost included; no export-claim TTL inference |
| bot | `update_all2_log_manager.py` | reviewed scoped edge | F16/F17/F19 |
| bot | `upload_routes/kvk_source_route.py` | reviewed scoped edge | B03 / F14: season metadata locks, immutable publication/vector validation, destination session lock committed before provider I/O; preserve exact claims |
| bot | `upload_routes/mge_results_route.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `upload_routes/player_location_route.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `upload_routes/prekvk_route.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `upload_routes/rally_forts_route.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `upload_routes/weekly_activity_route.py` | reviewed scoped edge | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| bot | `usage_tracker.py` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| bot | `utils.py` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| bot | `verify_cityhalllevel_cache.py` | reviewed scoped edge | Indirect manual/compatibility disposition |
| bot | `voting/dal.py` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| bot | `voting/survey_dal.py` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| bot | `weekly_activity_importer.py` | reviewed scoped edge | F16/F17/F19 |
| sql | `sql_schema/KVK.sp_KVK_AllPlayers_Ingest.StoredProcedure.sql` | reviewed scoped edge | B10: SQL business and completion receipts remain atomic; session execution/maintenance guards and date replacement lock have separate purposes |
| sql | `sql_schema/dbo.ACQUIRE_KS4_IMPORT_LOCK.StoredProcedure.sql` | reviewed scoped edge | Custody integrity and separate archive transaction |
| sql | `sql_schema/dbo.ARCHIVE_IMPORT_STAGING_FILE.StoredProcedure.sql` | reviewed scoped edge | Custody integrity and separate archive transaction |
| sql | `sql_schema/dbo.CLAIM_KS4_IMPORT_FILE.StoredProcedure.sql` | reviewed scoped edge | Custody integrity and separate archive transaction |
| sql | `sql_schema/dbo.CREATE_DELTA_TABLES.StoredProcedure.sql` | reviewed scoped edge | F18/F21/F22; atomic data/receipt versus maintenance |
| sql | `sql_schema/dbo.FIX_IMPORT_STAGING.StoredProcedure.sql` | reviewed scoped edge | B10: SQL business and completion receipts remain atomic; session execution/maintenance guards and date replacement lock have separate purposes |
| sql | `sql_schema/dbo.IMPORT_STAGING_PROC_CORE.StoredProcedure.sql` | reviewed scoped edge | Custody integrity and separate archive transaction |
| sql | `sql_schema/dbo.SP_Stats_for_Upload.StoredProcedure.sql` | reviewed scoped edge | F18/F21/F22; atomic data/receipt versus maintenance |
| sql | `sql_schema/dbo.UPDATE_ALL2.StoredProcedure.sql` | reviewed scoped edge | F18/F21/F22; atomic data/receipt versus maintenance |
| sql | `sql_schema/dbo.sp_Import_Rally_Daily.StoredProcedure.sql` | reviewed scoped edge | B10: SQL business and completion receipts remain atomic; session execution/maintenance guards and date replacement lock have separate purposes |
| sql | `sql_schema/dbo.sp_TARGETS_MASTER.StoredProcedure.sql` | reviewed scoped edge | F18/F21/F22; atomic data/receipt versus maintenance |
| sql | `sql_schema/dbo.usp_BackfillRallyDailySnapshotCompletion.StoredProcedure.sql` | reviewed scoped edge | B10: SQL business and completion receipts remain atomic; session execution/maintenance guards and date replacement lock have separate purposes |
| sql | `sql_schema/dbo.usp_ExportExecutionSessionTransition.StoredProcedure.sql` | reviewed scoped edge | B09: authority SQL exact-role/version/resource gates; zero-wait mutation admission is not a one-second execution budget; caller transaction ownership explicit |
| sql | `sql_schema/dbo.usp_ExportExecutionStreamTransition.StoredProcedure.sql` | reviewed scoped edge | B09: authority SQL exact-role/version/resource gates; zero-wait mutation admission is not a one-second execution budget; caller transaction ownership explicit |
| sql | `sql_schema/dbo.usp_ExportJobContainTargets.StoredProcedure.sql` | reviewed scoped edge | B09: authority SQL exact-role/version/resource gates; zero-wait mutation admission is not a one-second execution budget; caller transaction ownership explicit |
| sql | `sql_schema/dbo.usp_ExportLegacyCloseout.StoredProcedure.sql` | reviewed scoped edge | B09: authority SQL exact-role/version/resource gates; zero-wait mutation admission is not a one-second execution budget; caller transaction ownership explicit |
| sql | `sql_schema/dbo.usp_ExportManualOutputEnrollmentTransition.StoredProcedure.sql` | reviewed scoped edge | B09: authority SQL exact-role/version/resource gates; zero-wait mutation admission is not a one-second execution budget; caller transaction ownership explicit |
| sql | `sql_schema/dbo.usp_ExportOutputEnrollmentTransition.StoredProcedure.sql` | reviewed scoped edge | B09: authority SQL exact-role/version/resource gates; zero-wait mutation admission is not a one-second execution budget; caller transaction ownership explicit |
| sql | `sql_schema/dbo.usp_ExportProviderRequestEventAppend.StoredProcedure.sql` | reviewed scoped edge | B09: authority SQL exact-role/version/resource gates; zero-wait mutation admission is not a one-second execution budget; caller transaction ownership explicit |
| sql | `sql_schema/dbo.usp_ExportReconciliationProofIssue.StoredProcedure.sql` | reviewed scoped edge | B09: authority SQL exact-role/version/resource gates; zero-wait mutation admission is not a one-second execution budget; caller transaction ownership explicit |
| sql | `sql_schema/dbo.usp_ExportReplacementActivate.StoredProcedure.sql` | reviewed scoped edge | B09: authority SQL exact-role/version/resource gates; zero-wait mutation admission is not a one-second execution budget; caller transaction ownership explicit |
| sql | `sql_schema/dbo.usp_ExportReplacementPlanCreate.StoredProcedure.sql` | reviewed scoped edge | B09: authority SQL exact-role/version/resource gates; zero-wait mutation admission is not a one-second execution budget; caller transaction ownership explicit |
| sql | `sql_schema/dbo.usp_ExportReplacementVerificationTransition.StoredProcedure.sql` | reviewed scoped edge | B09: authority SQL exact-role/version/resource gates; zero-wait mutation admission is not a one-second execution budget; caller transaction ownership explicit |
| sql | `sql_schema/dbo.usp_ExportRolloverContainTargets.StoredProcedure.sql` | reviewed scoped edge | B09: authority SQL exact-role/version/resource gates; zero-wait mutation admission is not a one-second execution budget; caller transaction ownership explicit |
| sql | `sql_schema/dbo.usp_PurgeLeadershipPlayerReviewAudit.StoredProcedure.sql` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| sql | `sql_schema/dbo.usp_RecordKvkFinalReportCompletion.StoredProcedure.sql` | reviewed scoped edge | B10: SQL business and completion receipts remain atomic; session execution/maintenance guards and date replacement lock have separate purposes |
| sql | `sql_schema/dbo.usp_S11CompleteStatsReportsCore.StoredProcedure.sql` | reviewed scoped edge | F18/F21/F22; atomic data/receipt versus maintenance |
| sql | `sql_schema/dbo.usp_S11RunStatsImport.StoredProcedure.sql` | reviewed scoped edge | B10: SQL business and completion receipts remain atomic; session execution/maintenance guards and date replacement lock have separate purposes |
| sql | `sql_schema/dbo.usp_S11ValidateStatsReportStage.StoredProcedure.sql` | reviewed scoped edge | F27; validator contention loses typed waiting; original diagnostics retained |
| sql | `sql_schema/dbo.usp_SetAllianceActivitySnapshotCompletion.StoredProcedure.sql` | reviewed scoped edge | B10: SQL business and completion receipts remain atomic; session execution/maintenance guards and date replacement lock have separate purposes |
| sql | `sql_schema/dbo.usp_UpsertGovernorNameHistoryForScan.StoredProcedure.sql` | reviewed scoped edge | B10: SQL business and completion receipts remain atomic; session execution/maintenance guards and date replacement lock have separate purposes |
| sql | `sql_schema/dbo.usp_VoteSurveyAdminDelete.StoredProcedure.sql` | boundary disposition | B14: local telemetry/reminders/voting/CrystalTech have separate stores and identities; shared delivery/drain/file helpers included, domain redesign excluded |
| sql | `sql_schema/dbo.usp_update_stats.StoredProcedure.sql` | reviewed scoped edge | B10: SQL business and completion receipts remain atomic; session execution/maintenance guards and date replacement lock have separate purposes |

## Separate final sweep

The [final sweep ledger](Startup%20Import%20Export%20Reliability%20-%20Final%20Sweep%20-%202026-11-02.md)
records the independent current-inventory challenge and 322 additional candidate
dispositions. The 371 historical rows above remain unchanged and are not counted again
as newly reviewed whole modules. F31 and F02's precise closure extension are recorded
in tracing; installed enablement and native qualification remain explicit boundaries.

## Additional inspected paths outside the historical seed

| Path | Evidence |
|---|---|
| `core/startup_lifecycle.py` | F01/F08/F15/F20 |
| `event_calendar/scheduler.py` | F23/F24; explicit no-timeout-retry safeguard |
| `event_calendar/runtime_cache.py` | F25; primary cache versus auxiliary index outcome |
| `services/stats_report_continuation.py` | F27; validator contention loses typed waiting; original diagnostics retained |
| `core/sql_observation.py` | Recovery follow-through: clean refusal, bounded retry and exact result pacing |
| `sql_schema/dbo.sp_ExcelOutput_ByKVK.StoredProcedure.sql` | F18/F21/F22; atomic data/receipt versus maintenance |
| `sql_schema/dbo.HASH_KS4_IMPORT_ARCHIVE_FILE.StoredProcedure.sql` | Custody integrity and separate archive transaction |
| `sql_schema/dbo.sp_Prep_TargetTable.StoredProcedure.sql` | Dynamic publication disposition; parent checks and rollback |
| `sql_schema/dbo.sp_Prep_ExcelOutputTable.StoredProcedure.sql` | Dynamic publication disposition; parent checks and rollback |
| `sql_schema/dbo.sp_Prep_ExcelExportTable.StoredProcedure.sql` | Dynamic publication disposition; parent checks and rollback |
| `sql_schema/dbo.sp_Rebuild_ExcelForDashboard.StoredProcedure.sql` | Dynamic publication disposition; parent checks and rollback |
| `sql_schema/dbo.sp_refresh_view_EXCEL_FOR_KVK_ALL.StoredProcedure.sql` | Dynamic publication disposition; parent checks and rollback |
| `services/capture_recovery_context.py` | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| `services/producer_refusal_recovery.py` | B01 / F28: exact cancellation receipt versus stale import projection; preserve original execution/custody proof |
| `services/fallback_upload_staging_service.py` | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| `services/import_audit_service.py` | B04 / F17/F29/F30: committed business outcome separate from diagnostics/audit; Rally error receipt blocks filename retry; CSV gates staging callback |
| `sql_schema/dbo.IngestionLog.Table.sql` | B10: SQL business and completion receipts remain atomic; session execution/maintenance guards and date replacement lock have separate purposes |
