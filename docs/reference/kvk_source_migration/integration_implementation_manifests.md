# S7 exact implementation manifests and delivery

## Current status — S7 approved; S8A pack prepared, 2026-09-12

Chris Watts approved the S7 contract and exact implementation manifests, then authorized
preparation of the next pack and starter. The approved technical direction includes initial
account serialization, durable legacy snapshots with worker affinity where needed, and the
stated quarantine/reserve allowance. Settled S7 decisions are not reopened.

**Next: S8A SQL Foundation, after separate file-implementation authorization.**
[Task pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8A%20SQL%20Foundation.md); [implementation starter](../../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8A%20SQL%20Foundation.md).
Preparation is documentation-only. No S8A SQL/runtime/config implementation, database
execution, Git publication or activation is authorized by this status. Preserve the full
27-path Bot carry-forward union, including both S6 archive move sides and both S7 outputs;
SQL implementation belongs in its own repository and review. Historical status blocks below
retain their original evidence; this latest status supersedes pending S7 review wording.

2026-09-12. **S7 documentation/read-only work only; stop for contract/manifests review.**
The [contract and complete consumer matrix](integration_contract_and_consumer_matrix.md)
defines semantics. These are proposed implementation boundaries, not runnable task packs,
standing approval, deployment steps to execute now, or claims that proposed tests passed.

## 1. Summary

Resolve the missing ordinary routing with a fixed season choice and complete paired public
selection. Add durable export intent/admission across three consumers, export-only recovery
and safe file reuse. Preserve B0, independent aggregates/overall, exact endpoints, UTC,
semantic deduplication, daily SCANORDER and accepted predecessor evidence. S7-D01–D09 are
settled; only the contract's three evidenced technical tradeoffs need design review.

S7 actual edits are Markdown only. Bot entry/final target is the uncommitted handoff plus
S7 patch against `a2f148fa9bd4fb367fd46d0500a768c14fee915b`. SQL has no changes at
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`; local production/main remains
`a8c9c515066ca6ef079120b76dd160e3389badab`. No reset/pull/fetch, commit/push/PR/merge,
SQL connection, provider write, real import/export, Discord, restart, deployment or activation.

## 2. File manifest

### S7 actual deliverable and future PR carry-forward

The exact 23 paths and actions in [handoff section 2](post_s6_handoff_log.md#2-exact-next-slice-carry-forward-file-manifest)
plus the two Create paths below form a **25-path union**, counting archive deletions and
destinations separately. No path may be omitted as pre-existing work. Both S6 archive source
deletions and both destinations remain mandatory. Final local status is checked against this
union, including untracked files and empty index. No path is claimed already merged.

The next separately authorized slice PR must compare its actual Files changed (filename
and previous_filename) against this union plus its separately approved implementation manifest.
Any omitted path requires exact merge/ancestor/content evidence. No PR exists for this S7
delta, so remote Files changed verification is a future gate, not a claimed current result.

### Ordered PR-sized implementation boundaries

Effort is an engineering estimate in focused working days, including focused tests and review
fixes, excluding approval/provider/SQL-environment wait. It is based on the actual missing
seams and accepted reuse, not measured implementation throughput. Risk remains high for
concurrency/old-worker recovery. Do not execute multiple boundaries under S7 approval.

| Boundary | Result and dependency | Estimate / principal risk |
|---|---|---|
| S8A SQL | Add fixed source, update/public pointer and immutable intent schema; review migration classification separately | 2–3 days; existing mixed-history classification |
| S8B Bot | DAL/services enforce source/pair/publication/intent, preserve endpoint chain and accepted calculations | 3–5 days; partial selection bypass and stale builders |
| S8C Bot | Intake/admin pairing and source onboarding UX using S8B; no new top-level command | 1–2 days; stale/unauthorized confirmation |
| S9A Bot | Ordinary reporting/dispatch resolver and availability/caches; S8B/C | 2–3 days; mixed blocks/legacy normalization |
| S9B Bot | Stats/target card context and grouped admin source dispatch; S9A | 2–3 days; legacy camp leakage or wrong cohort |
| S10A SQL | General export jobs/resources/budget/attempt-part schema; S8A intent contract | 2–3 days; lock/state integrity |
| S10B Bot | Queue worker, pinned generations and durable budget; S10A and S8B | 3–5 days; latest-selection checks currently abort A when B arrives |
| S10C Bot | Legacy/scan automatic/manual adapters, immutable snapshots and common provider client pacing; S10B | 3–5 days; mutable per-tab SQL and detached timeout threads |
| S10D SQL | Pool/slot/disposition schema; S10A | 1–2 days; occupied/uncertain file identity |
| S10E Bot | Export-only/status/reconcile/rebuild and rollover; S10B/C/D and S9B | 3–4 days; public ACL uncertainty and late old writes |
| S11 docs/release | Exact environment/operation plan and new evidence, after all preceding integration slices accepted | 1–2 days preparation; execution duration only after exact G4 targets/operations are approved |

Total proposed engineering range: 23–37 focused days plus separately authorized operational
evidence. S10C may be reviewed as two commits within its bounded PR (snapshot capture and
provider adapters); if its verified surface grows, stop to amend that exact manifest instead
of expanding into general reliability WS1. Additive schema may deploy inertly before Bot,
but no source serving/queue activation before all required compatibility gates are complete.

### Exact source/test paths by boundary

`Create` names below are deliberate proposed files, currently absent; `Modify` names are
current files verified by local inventory. Tests in this table are edits, not just tests to run.
Unlisted runtime, SQL or config files remain outside each proposed boundary. The S7 handoff
union accompanies the first separately authorized slice PR; later PRs prove those paths merged.

#### S8A

| Repository | Action | Exact path |
|---|---|---|
| SQL | Create | `migrations/20260912_001_kvk_season_complete_updates.sql` |
| SQL | Create | `sql_schema/KVK.SeasonSource.Table.sql` |
| SQL | Create | `sql_schema/KVK.SourceUpdate.Table.sql` |
| SQL | Create | `sql_schema/KVK.SourceCompleteSelection.Table.sql` |
| SQL | Create | `sql_schema/KVK.SourceExportIntent.Table.sql` |
| SQL | Create | `sql_schema/KVK.SourceExportIntentPublication.Table.sql` |
| SQL | Create | `validation/kvk_source/s8_season_complete_updates.sql` |
| SQL | Modify | `docs/SQL_DELIVERY_LOG.md` |

#### S8B

| Repository | Action | Exact path |
|---|---|---|
| Bot | Create | `kvk/models/source_integration.py` |
| Bot | Create | `kvk/dal/season_source_dal.py` |
| Bot | Create | `kvk/dal/source_update_dal.py` |
| Bot | Create | `kvk/services/season_source_service.py` |
| Bot | Create | `kvk/services/source_update_service.py` |
| Bot | Create | `tests/test_kvk_season_source.py` |
| Bot | Create | `tests/test_kvk_source_pairs.py` |
| Bot | Modify | `kvk/dal/new_source_import_dal.py` |
| Bot | Modify | `kvk/dal/kvk_all_import_dal.py` |
| Bot | Modify | `kvk/dal/new_source_publication_dal.py` |
| Bot | Modify | `kvk/dal/new_source_recovery_dal.py` |
| Bot | Modify | `kvk/dal/new_source_config_dal.py` |
| Bot | Modify | `kvk/services/new_source_publication_service.py` |
| Bot | Modify | `kvk/services/new_source_recovery_service.py` |
| Bot | Modify | `kvk/services/new_source_config_service.py` |
| Bot | Modify | `tests/test_kvk_source_publication.py` |
| Bot | Modify | `tests/test_kvk_source_recovery.py` |
| Bot | Modify | `tests/test_kvk_source_config_service.py` |
| Bot | Modify | `tests/test_kvk_source_sql_integration.py` |
| Bot | Modify | `tests/test_kvk_all_import_dal.py` |

#### S8C

| Repository | Action | Exact path |
|---|---|---|
| Bot | Modify | `commands/stats_cmds.py` |
| Bot | Modify | `ui/views/kvk_source_import_view.py` |
| Bot | Modify | `upload_routes/kvk_source_route.py` |
| Bot | Modify | `upload_routes/kvk_all_route.py` |
| Bot | Modify | `kvk/services/new_source_admin_service.py` |
| Bot | Modify | `kvk/dal/new_source_admin_dal.py` |
| Bot | Modify | `proc_config_import.py` |
| Bot | Modify | `docs/reference/canonical_command_reference.md` |
| Bot | Modify | `tests/test_kvk_source_admin.py` |
| Bot | Modify | `tests/test_kvk_source_import_view.py` |
| Bot | Modify | `tests/test_kvk_source_upload_route.py` |
| Bot | Modify | `tests/test_kvk_all_upload_route.py` |
| Bot | Modify | `tests/test_kvk_source_config_hook.py` |

#### S9A

| Repository | Action | Exact path |
|---|---|---|
| Bot | Create | `kvk/dal/source_routing_dal.py` |
| Bot | Create | `kvk/services/source_routing_service.py` |
| Bot | Create | `tests/test_kvk_public_routing.py` |
| Bot | Create | `tests/test_kvk_source_independent_consumers.py` |
| Bot | Modify | `kvk/models/source_integration.py` |
| Bot | Modify | `kvk/dal/new_source_reporting_dal.py` |
| Bot | Modify | `kvk/dal/kvk_reporting_dal.py` |
| Bot | Modify | `kvk/services/kvk_reporting_service.py` |
| Bot | Modify | `kvk/services/new_source_reporting_service.py` |
| Bot | Modify | `stats_alerts/allkingdoms.py` |
| Bot | Modify | `stats_alerts/embeds/kvk.py` |
| Bot | Modify | `stats_alerts/kvk_diagnostics.py` |
| Bot | Modify | `stats_alerts/kvk_diagnostic_sessions.py` |
| Bot | Modify | `tests/test_kvk_reporting_service.py` |
| Bot | Modify | `tests/test_kvk_source_reporting.py` |
| Bot | Modify | `tests/test_kvk_source_reporting_models.py` |
| Bot | Modify | `tests/test_kvk_embed.py` |
| Bot | Modify | `tests/test_kvk_embed_diagnostics.py` |
| Bot | Modify | `tests/test_kvk_embed_diagnostic_lifecycle.py` |
| Bot | Modify | `tests/test_stats_alerts_fighting_lifecycle.py` |

#### S9B

| Repository | Action | Exact path |
|---|---|---|
| Bot | Modify | `kvk/services/kvk_stats_card_service.py` |
| Bot | Modify | `kvk/dal/kvk_stats_card_dal.py` |
| Bot | Modify | `kvk/models/kvk_stats_card.py` |
| Bot | Modify | `kvk/rendering/kvk_stats_card_renderer.py` |
| Bot | Modify | `commands/kvk_stats_card_posting.py` |
| Bot | Modify | `ui/views/kvk_stats_card_views.py` |
| Bot | Modify | `kvk/services/kvk_admin_service.py` |
| Bot | Modify | `kvk/dal/kvk_admin_dal.py` |
| Bot | Modify | `commands/stats_cmds.py` |
| Bot | Modify | `tests/test_kvk_source_card_context.py` |
| Bot | Modify | `tests/test_kvk_stats_card_payload.py` |
| Bot | Modify | `tests/test_kvk_stats_card_dal.py` |
| Bot | Modify | `tests/test_kvk_stats_card_posting.py` |
| Bot | Modify | `tests/test_kvk_stats_card_views.py` |
| Bot | Modify | `tests/test_kvk_admin_service.py` |
| Bot | Modify | `tests/test_kvk_embed_diagnostic_command.py` |
| Bot | Modify | `kvk/services/kvk_targets_card_service.py` |
| Bot | Modify | `kvk/models/kvk_targets_card.py` |
| Bot | Modify | `kvk/rendering/kvk_targets_card_renderer.py` |
| Bot | Modify | `tests/test_kvk_targets_card_service.py` |
| Bot | Modify | `tests/test_kvk_targets_card_renderer.py` |
| Bot | Modify | `tests/test_kvk_targets_card_posting.py` |

#### S10A

| Repository | Action | Exact path |
|---|---|---|
| SQL | Create | `migrations/20260912_002_shared_export_coordination.sql` |
| SQL | Create | `sql_schema/dbo.ExportJob.Table.sql` |
| SQL | Create | `sql_schema/dbo.ExportJobResource.Table.sql` |
| SQL | Create | `sql_schema/dbo.ExportResource.Table.sql` |
| SQL | Create | `sql_schema/dbo.ExportRequestBudget.Table.sql` |
| SQL | Create | `sql_schema/dbo.ExportAttempt.Table.sql` |
| SQL | Create | `sql_schema/dbo.ExportAttemptPart.Table.sql` |
| SQL | Create | `validation/kvk_source/s10_export_coordination.sql` |
| SQL | Modify | `docs/SQL_DELIVERY_LOG.md` |

#### S10B

| Repository | Action | Exact path |
|---|---|---|
| Bot | Create | `services/export_coordination_service.py` |
| Bot | Create | `services/export_request_budget.py` |
| Bot | Create | `services/export_coordination_dal.py` |
| Bot | Create | `services/export_snapshot_store.py` |
| Bot | Create | `tests/test_kvk_export_coordination.py` |
| Bot | Create | `tests/test_kvk_export_sql_integration.py` |
| Bot | Modify | `kvk/services/new_source_recovery_service.py` |
| Bot | Modify | `kvk/services/new_source_export_service.py` |
| Bot | Modify | `kvk/services/new_source_delivery_service.py` |
| Bot | Modify | `kvk/dal/new_source_delivery_dal.py` |
| Bot | Modify | `kvk/dal/source_update_dal.py` |
| Bot | Modify | `bot_instance.py` |
| Bot | Modify | `bot_config.py` |
| Bot | Modify | `docs/reference/ENV_REFERENCE.md` |
| Bot | Modify | `docs/reference/runbook_startup.md` |
| Bot | Modify | `docs/reference/runbook_shutdown.md` |
| Bot | Modify | `tests/test_kvk_source_exports.py` |
| Bot | Modify | `tests/test_kvk_source_delivery.py` |
| Bot | Modify | `tests/test_kvk_source_recovery.py` |

#### S10C

| Repository | Action | Exact path |
|---|---|---|
| Bot | Create | `services/legacy_export_snapshot_service.py` |
| Bot | Create | `services/legacy_export_snapshot_dal.py` |
| Bot | Create | `services/export_provider_adapter.py` |
| Bot | Create | `tests/test_legacy_export_snapshot.py` |
| Bot | Create | `tests/test_export_provider_adapter.py` |
| Bot | Modify | `gsheet_module.py` |
| Bot | Modify | `processing_pipeline.py` |
| Bot | Modify | `stats_module.py` |
| Bot | Modify | `kvk_all_importer.py` |
| Bot | Modify | `upload_routes/kvk_all_route.py` |
| Bot | Modify | `commands/admin_cmds.py` |
| Bot | Modify | `commands/stats_cmds.py` |
| Bot | Modify | `kvk/services/kvk_admin_service.py` |
| Bot | Modify | `kvk/dal/kvk_admin_dal.py` |
| Bot | Modify | `kvk/dal/kvk_all_import_dal.py` |
| Bot | Modify | `proc_config_import.py` |
| Bot | Modify | `services/export_coordination_service.py` |
| Bot | Modify | `tests/test_gsheet_module.py` |
| Bot | Modify | `tests/test_gsheet_helpers.py` |
| Bot | Modify | `tests/test_gsheet_sorting.py` |
| Bot | Modify | `tests/test_kvk_all_upload_route.py` |
| Bot | Modify | `tests/test_kvk_all_import_dal.py` |
| Bot | Modify | `tests/test_processing_pipeline.py` |
| Bot | Modify | `tests/test_processing_pipeline_run_step_and_normalization.py` |
| Bot | Modify | `tests/test_proc_config_import.py` |
| Bot | Modify | `tests/test_kvk_export_coordination.py` |

#### S10D

| Repository | Action | Exact path |
|---|---|---|
| SQL | Create | `migrations/20260912_003_kvk_output_pool_rollover.sql` |
| SQL | Create | `sql_schema/KVK.SourceOutputPool.Table.sql` |
| SQL | Create | `sql_schema/KVK.SourceOutputSlot.Table.sql` |
| SQL | Create | `sql_schema/KVK.SourceOutputDisposition.Table.sql` |
| SQL | Create | `validation/kvk_source/s10_output_pool_rollover.sql` |
| SQL | Modify | `docs/SQL_DELIVERY_LOG.md` |

#### S10E

| Repository | Action | Exact path |
|---|---|---|
| Bot | Create | `kvk/dal/source_output_pool_dal.py` |
| Bot | Create | `kvk/services/source_output_pool_service.py` |
| Bot | Create | `kvk/services/source_export_operator_service.py` |
| Bot | Create | `ui/views/kvk_source_export_view.py` |
| Bot | Create | `tests/test_kvk_export_operator.py` |
| Bot | Create | `tests/test_kvk_output_rollover.py` |
| Bot | Modify | `commands/stats_cmds.py` |
| Bot | Modify | `kvk/services/new_source_admin_service.py` |
| Bot | Modify | `kvk/services/new_source_export_service.py` |
| Bot | Modify | `kvk/services/new_source_delivery_service.py` |
| Bot | Modify | `kvk/dal/new_source_delivery_dal.py` |
| Bot | Modify | `services/export_coordination_service.py` |
| Bot | Modify | `services/export_coordination_dal.py` |
| Bot | Modify | `docs/reference/canonical_command_reference.md` |
| Bot | Modify | `docs/reference/ENV_REFERENCE.md` |
| Bot | Modify | `docs/reference/runbook_diagnostics.md` |
| Bot | Modify | `tests/test_kvk_source_admin.py` |
| Bot | Modify | `tests/test_kvk_source_delivery.py` |
| Bot | Modify | `tests/test_kvk_export_sql_integration.py` |
| Bot | Modify | `tests/test_kvk_export_coordination.py` |

#### S11

| Repository | Action | Exact path |
|---|---|---|
| Bot | Modify | `docs/reference/kvk_source_migration/release_readiness_and_rollback.md` |
| Bot | Modify | `docs/reference/kvk_source_migration/release_evidence_log.md` |
| Bot | Modify | `docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md` |
| Bot | Modify | `docs/reference/kvk_source_migration/integration_implementation_manifests.md` |
| Bot | Modify | `docs/reference/kvk_source_migration/post_s6_handoff_log.md` |
| Bot | Modify | `docs/reference/local_sql_development.md` |
| Bot | Modify | `README-DEV.md` |
| Bot | Modify | `docs/reference/README.md` |


## 3. New files

Only these two repository files are created by S7:

- `docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md`
- `docs/reference/kvk_source_migration/integration_implementation_manifests.md`

All runtime/test/SQL Create paths above are planning only. Local scratch backup/check scripts
are outside Git at `C:/Users/cwatt/AppData/Local/Temp/k98-s7-docs-9ib_g9cd`.

## 4. Modified files

S7 updates these six existing handoff documents, in addition to its two Create outputs:

- `docs/reference/kvk_source_migration/phase_2_acceptance_scenarios.md`
- `docs/reference/kvk_source_migration/phase_2_implementation_plan.md`
- `docs/reference/kvk_source_migration/post_s6_handoff_log.md`
- `docs/reference/kvk_source_migration/post_s6_integration_requirements.md`
- `docs/task_packs/Codex Chat Starter - KVK Source Migration S7 Integration Contract and Implementation Planning.md`
- `docs/task_packs/Codex Task Pack - KVK Source Migration S7 Integration Contract and Implementation Planning.md`

Existing handoff edits remain; measured S6 evidence,
release files and both archived S6 bodies are preserved byte-for-byte from S7 entry.
Historical pending/next-slice statements retain their dates; latest S7 status controls.
Runtime helpers, SQL, test files, configuration and source workbooks are unchanged.

## 5. SQL changes — proposed only

No SQL changes executed. Read source definitions from authoritative SQL repository; no live
rows, SQL Agent jobs, deployed migration state, permissions or provider identity checked.
No new UDTs or numerical calculation stored procedures. Use the existing versioned
observation/config/result schemas; never widen legacy facts to store new-source results.

New definitions below use UUID=uniqueidentifier, hash=binary(32), UTC=datetime2(0) except
budget scheduling=datetime2(3), positive bigint counters, positive int KVK_NO, enums with
explicit BIN2 comparison and DATALENGTH checks, actors nvarchar(128), reasons nvarchar(1024).
All FK scope keys carry SourceKey/KVK_NO/PeriodID where applicable. No cascading deletes.
JSON has ISJSON and explicit byte bounds, never private data in public diagnostic payloads.

Interface ownership is explicit: `season_source_dal` creates/reads a choice and lifecycle CAS;
`source_update_dal` associates accepted revisions using expected update version, seals them,
and commits complete selection plus intent in one transaction. `source_update_service`
validates pairing/counterpart authority and invokes the accepted calculation service.
`source_routing_dal` returns the complete read token; `source_routing_service` dispatches
legacy/V2/unavailable without consulting upload order. `export_coordination_dal` owns job,
resource, budget and attempt CAS; the service owns coalescing, fairness and recovery policy.
`legacy_export_snapshot_dal` reads result sets under producer admission; its service/spool
store verifies immutable bytes and provenance before recording the job. Provider adapters
require a live job/epoch token at every mutation boundary. Pool DAL owns slot/disposition CAS;
pool service owns lifecycle and privacy/readback policy. No command invokes SQL directly.

S10B config addition is `EXPORT_COORDINATION_ENABLED`, default false; it enables the common
coordinator only after all adapters are deployed. A registered durable snapshot root and
storage-owner identity are passed through `EXPORT_SNAPSHOT_ROOT` and
`EXPORT_STORAGE_OWNER`. Use the existing configured SQL connection factory for the single
coordinator database; no parallel default SQL server or new embedded credentials. Extend
existing source export registrations to validated account/destination/pool identities; legacy
title discovery resolves to registered file IDs. Missing schema, unsupported worker protocol,
unregistered destination or missing durable storage blocks the affected job. No new dependencies
or edits to actual `.env`/`config/sheet_config.json` are planned. Environment provisioning is S11.

| Proposed object | Exact required key, columns and constraints |
|---|---|
| KVK.SeasonSource | PK KVK_NO; UQ(KVK_NO,SourceKey,ChoiceID); SourceKey varchar(32) allowlists legacy_full_data/snapshot_report_v1; ChoiceID; ChosenBy/ChosenUTC/Reason/ProvenanceJson <=65536 bytes; SeasonState planned/open/closing/closed; SeasonVersion; optional compatibility provenance. DAL exposes create/read/lifecycle CAS, no source update/delete. Migration rejects ambiguous historical scopes |
| KVK.SourceUpdate | PK UpdateID; UQ(source/KVK/period/UpdateID); ChoiceID FK; ConfigVersionID/RosterID; start/end revision and logical scan IDs; AggregateReportID/AggregateRevisionID; CoverageStartUTC/CoverageEndUTC/AsOfUTC; UpdateKind fight/overall/no_fight; UpdateState waiting_player/waiting_aggregate/ready/selected/superseded/rejected; BaseUpdateID; CounterpartRevisionID/ConfirmedBy/ConfirmedUTC/ConfirmationJson <=65536; RequestID FK SourceConfigRequest; ContentHash, Version. Nullable stream fields only while waiting; sealed tuple immutable; same-source scoped FKs; no-fight explicitly forbids aggregate |
| KVK.SourceCompleteSelection | PK(source/KVK/period); UpdateID scoped FK; PublicationID scoped FK; PublicSelectionVersion; SelectedUTC. Unique update/publication association checked against candidate manifest in commit; no ordinary unpaired pointer |
| KVK.SourceExportIntent | PK IntentID; source/KVK/ChoiceID; CommitSequence bigint unique per season; VectorHash; ExportSchemaVersion; IntentState pending/waiting_destination/materialized/coalesced/confirmed/blocked; CreatedUTC; SupersededByIntentID nullable same-season FK. UQ(source/KVK/VectorHash/ExportSchemaVersion); never delete accepted intent history |
| KVK.SourceExportIntentPublication | PK(IntentID,PeriodID); source/KVK/UpdateID/PublicationID/PublicSelectionVersion/ConfigVersionID; scoped immutable FKs; selected vector row count/hash verified before commit; unchanged periods copied into each vector |
| dbo.ExportJob | PK JobID; ConsumerKind new_source/all_kvk/scan_data; optional IntentID FK; AccountKey varchar(128), DestinationSetHash, InputHash/SpoolKey/SpoolBytes/StorageOwner, KVK_NO nullable, PoolEpoch nullable, RepairID nullable; EnqueueSequence; State waiting/ready/running/confirmed/failed/uncertain/coalesced/cancelled; OwnerID/Fence; CreatedUTC/UpdatedUTC; SupersededByJobID; Actor/Reason/ProvenanceJson. UQ replay key includes consumer/input/destination/epoch/repair; no replay collision between distinct damage repairs |
| dbo.ExportJobResource | PK(JobID,ResourceKey); ResourceKey varchar(256) FK; resource set frozen before running; sorted deterministic acquisition |
| dbo.ExportResource | PK ResourceKey varchar(256); ResourceKind account/destination/sql_snapshot; ActiveJobID nullable FK, OwnerID/Fence, BlockedReason, Version; owner and job nullability paired; CAS updates; job state alone cannot release uncertain resource |
| dbo.ExportRequestBudget | PK(AccountKey,BudgetKind); NextAllowedUTC datetime2(3); CooldownUntilUTC; Version; interval/policy version; request reservation uses server UTC, waits outside transaction; no SQL transaction during provider request |
| dbo.ExportAttempt | PK AttemptID; JobID FK, AttemptNo UQ per job, OwnerID/Fence, Epoch, Phase private_started/verified/publication_pending/published/failed/uncertain/retired; RemoteSequence; timestamps; ManifestHash; legacy SourceDelivery key reference optional; bounded receipt metadata; append-only attempts, phase CAS |
| dbo.ExportAttemptPart | PK(AttemptID,PartNo); FileID nvarchar(128), role, manifest hash, grid/row/cell counts, verified/ACL state and UTC, quarantine disposition; unique assigned file per attempt; preflight maximum parts/count/receipt fields, never truncate evidence |
| KVK.SourceOutputPool | PK PoolID; stable IndexFileID UQ; ActiveKVK/ChoiceID; Epoch; PoolState active/closing/closed/setup/blocked; OwnerID/Fence; Version; expected account/owner/audience metadata, lifecycle audit |
| KVK.SourceOutputSlot | PK FileID nvarchar(128); PoolID FK; State free/staging/active/quarantined/retired; Epoch; AttemptID nullable; PartNo; Version; unique assignment under pool lock; file cannot belong to another pool |
| KVK.SourceOutputDisposition | PK DispositionID; PoolID/FileID/AttemptID; OldEpoch/NewEpoch; Action retire/quarantine/clear/assign; actor/reason/UTC; evidence hash and bounded JSON; append-only record so old receipt is never rewritten to look absent |

Migration paths in the exact manifest reserve the 20260912 date for review. SQL convention
requires actual creation date; if authored on another day, revise the three exact migration
filenames during the separately approved slice scope before writing them. Never rename a
merged migration. Include normal metadata, backup/data-safety and forward-fix notes.

S8A classification backfill is DataChange: Yes and requires an exact row preview/allowlist,
conflict rejection and backup authorization later; do not auto-classify all observed new-source
seasons as activated. Existing partial SourceSelections stay private until an explicit reviewed
pair is sealed; S6 databases are not migration targets by default. No live execution now.

Order: S8A schema and constraints → S8B/C writers → S9 readers; S10A schema → S10B/C
coordinator/adapters → S10D pool schema → S10E rollover. S10A/D are additive; old receipts
are imported into references only when unambiguously mapped, preserving bytes. Unknown
claims remain blocked. Do not turn on new queue writers while any old writer bypasses admission.
Reversible application rollout uses disabled admission/serving; rollback keeps schema/history
and fences. Drop-table rollback after data exists is not safe. Old-bot downgrade requires
draining/blocking all affected writers first; it cannot reinterpret a new-source KVK as legacy.

## 6. Helpers reused

Reuse `PublicationService.build_candidate`, `calculate_period`, `resolve_window`, semantic
digest/artifact store and existing import replay logic; extend selection validation for a sealed
pair rather than choosing globally newest unpaired input. Reuse `load_report_v2`/`card_context`
and V2 rendering, but give them the ordinary resolver token and exact immutable selection.
Reuse export generation partitioning, RAW values, full readback, quarantine and reconciliation;
replace latest-selection publication checks only for a valid running job/epoch. Existing receipt
uncertainty is never downgraded to failure based on time.

Reuse `file_utils.run_blocking_in_thread` for offload/telemetry, not ownership; shared locks or
offload registries do not provide a durable export queue. Reuse established atomic file helpers
for spools, verifying digest before SQL intent; do not introduce filename-driven paths.
Use `core/interaction_safety.py`, existing decorators and operator diagnostic packing/redaction
in commands/views. Reuse target-cache versioning pattern and CSV literal protection without
moving independent cache/data ownership. No helper implementation changed in S7.

## 7. Refactor findings

Required integration work: extract new queue/snapshot/provider-admission policy into services
and DAL; keep gsheet_module/processing_pipeline/kvk_all_importer compatibility wrappers thin.
Current account pacer is process-local; current export publication gate spans provider work;
current scan exporter reads SQL per tab and timeout can outlive its caller. These are bounded
S10 dependencies, not deferred optimizations or a general reliability WS1 programme.
No new SQL/business policy in commands or views. No unrelated helper cleanup, SQL rewrite,
dead-code deletion or new dependency is proposed. No unrelated actionable debt is captured.

## 8. Test plan with actual outcomes

### Required new scenarios and exact owners

| Scenario | Boundary | Exact test files | Required assertion |
|---|---|---|---|
| S7-T01 | S8A/B/C | `tests/test_kvk_season_source.py`; `tests/test_kvk_all_import_dal.py`; `tests/test_kvk_source_admin.py` | Concurrent same/different source, absent choice, restart and historical conflict migration |
| S7-T02 | S9A/B | `tests/test_kvk_public_routing.py`; `tests/test_kvk_source_card_context.py` | Ordinary calls without injection; legacy/new/unavailable/disabled/capability states |
| S7-T03 | S8B/C | `tests/test_kvk_source_pairs.py`; `tests/test_kvk_source_upload_route.py` | Both upload orders; first side cannot select publicly/enqueue; exact complete UpdateID |
| S7-T04 | S8A/B | `tests/test_kvk_source_pairs.py`; `tests/test_kvk_source_sql_integration.py` | Wrong source/KVK/period/coverage/roster/config/revision; SQL scoped FKs and stale CAS |
| S7-T05 | S8B/C | `tests/test_kvk_source_pairs.py`; `tests/test_kvk_source_import_view.py`; `tests/test_kvk_source_import_dal.py` | Explicit retained counterpart/actor, semantic alias/correction replay; no extra aggregate ScanID |
| S7-T06 | S8B/S9A | `tests/test_kvk_source_pairs.py`; `tests/test_kvk_public_routing.py`; `tests/test_kvk_source_recovery.py` | Failed second side preserves previous label; first pair waiting; desired14 old13 not current final |
| S7-T07 | S8B | `tests/test_kvk_source_pairs.py`; `tests/test_kvk_source_window_resolver.py`; `tests/test_kvk_source_config_service.py` | B0, no-fight absent members, separate overall, config-only and 11/12/13/14 exact sequence |
| S7-T08 | S8A/B | `tests/test_kvk_source_sql_integration.py`; `tests/test_kvk_source_pairs.py` | Kill before/after complete-selection/intent commit and lost acknowledgment |
| S7-T09 | S10A/B | `tests/test_kvk_export_coordination.py`; `tests/test_kvk_export_sql_integration.py` | Immutable running A then latest C; B history retained; fairness ticket not reset |
| S7-T10 | S10A/B/C | `tests/test_kvk_export_coordination.py`; `tests/test_export_provider_adapter.py`; `tests/test_legacy_export_snapshot.py` | Three consumers/manual/automatic/two processes; alias IDs, shared budget/cooldown; no SQL transaction over API |
| S7-T11 | S10B/C | `tests/test_kvk_source_delivery.py`; `tests/test_kvk_export_coordination.py`; `tests/test_kvk_export_sql_integration.py` | Worker loss/late effects; timeout thread retains ownership; uncertain blocks advance |
| S7-T12 | S10E | `tests/test_kvk_export_operator.py`; `tests/test_kvk_source_admin.py` | Export-only no parser/calculator; duplicate zero-API no-op; wrong actor/guild/role rejected |
| S7-T13 | S10E | `tests/test_kvk_export_operator.py`; `tests/test_kvk_source_delivery.py` | Explicit damage confirmation/RepairID; same inputs; old receipt retained; uncertain rebuild denied |
| S7-T14 | S10D/E | `tests/test_kvk_output_rollover.py`; `tests/test_kvk_export_sql_integration.py` | Drain/epoch/late writer; private clear/readback uncertainty; retired links and history |
| S7-T15 | S10D/E | `tests/test_kvk_output_rollover.py`; `tests/test_kvk_source_delivery.py` | P=2/larger partitions/quarantine exhaustion; receipt limit; no mutation before capacity |
| S7-T16 | S9A/B/S10C | `tests/test_kvk_source_independent_consumers.py`; `tests/test_stats_alerts_fighting_lifecycle.py`; `tests/test_kvk_public_routing.py` | C01-C65/N01-N12 covered; daily claims/SCANORDER/targets/history unchanged; precision and views |

Original T01–T70 remain accepted at their original revisions. Rerun only affected regression
coverage in implementation, never call this a predecessor reapproval:

| Original contracts | Exact existing test files to run/update where the changed behavior requires it |
|---|---|
| T01–T20 parser/digest/metadata | `tests/test_kvk_new_source_schema.py`, `tests/test_kvk_new_source_parser.py`, `tests/test_kvk_new_source_metadata.py`, `tests/test_kvk_new_source_digest.py`; run as intake boundary regressions, parser semantics unchanged |
| T21–T34, T68–T70 endpoints/B0/no-fight | `tests/test_kvk_source_calculation.py`, `tests/test_kvk_source_window_resolver.py`, `tests/test_kvk_source_config_service.py`, `tests/test_kvk_source_config_hook.py`; pair gating must preserve 11−10, 12−10, 13−10, authorized 14−10 |
| T35–T45 authoritative reports/finality/correction | `tests/test_kvk_source_publication.py`, `tests/test_kvk_source_reporting.py`, `tests/test_kvk_source_pairs.py`; T36/T40 private component behavior retained, public partial exposure superseded by S7 |
| T46–T51 atomicity/CAS/config races | `tests/test_kvk_source_sql_integration.py`, `tests/test_kvk_source_pairs.py`, `tests/test_kvk_export_sql_integration.py`; real two-connection disposable tests required after exact target approval |
| T52–T55 caches/views/availability | `tests/test_kvk_public_routing.py`, `tests/test_kvk_source_reporting_models.py`, `tests/test_kvk_embed_diagnostic_lifecycle.py`, `tests/test_kvk_stats_card_views.py` |
| T56–T59 multipart, coalescing and uncertainty | `tests/test_kvk_source_exports.py`, `tests/test_kvk_source_delivery.py`, `tests/test_kvk_export_coordination.py`; T58 pending B coalesces but running A may finish; T59 existing Discord uncertainty/caps unchanged |
| T60–T64 mixed card/independent/security boundaries | `tests/test_kvk_source_card_context.py`, `tests/test_kvk_source_independent_consumers.py`, `tests/test_kvk_source_admin.py`, `tests/test_kvk_source_import_view.py`, `tests/test_stats_alerts_guard.py` |
| T65–T67 rollback/history basis | `tests/test_kvk_source_recovery.py`, `tests/test_kvk_public_routing.py`, `tests/test_kvk_source_reporting.py`; T66 fixed-source disable is unavailable, never switch to legacy |

Each Bot runtime boundary: exact-path selector, focused pytest on its manifest's test files,
architecture/deferred/routing validators, smoke imports, command-registration validator where
command/lifecycle wiring changes, lint/type checks per repository hooks. Full suite through
`python scripts/analyse_pytest_log_noise.py` before broad integration handoff; record actual
count/skips and unchanged operational logs. Preserve existing legacy SQL contract tests.
Registration stays within the existing `kvk_admin` group, <=25 children; validate actual counts,
no assumed historical 36/101 result for changed code. No top-level allowlist expansion.
S9B renderer changes require synthetic visual samples for both stats and target cards,
including missing/stale context and long Unicode names; existing target numbers must stay
identical. The text-only S7 plan creates no sample or runtime renderer test now.

SQL schema slices: static snapshot/migration shape tests, then independently approved disposable
installation twice (idempotence), historical/mixed-state migration rejection, same/different-source
concurrent onboarding, pair FKs, two builders/commit acknowledgment loss, one owner per resource,
deadlock ordering and normalized receipt capacity. Mocks cannot close transaction/restart gates.
S11 exercises only newly affected provider/ACL/queue/rollover cases at approved exact targets;
retains S6 benchmark without rerunning it automatically. Real SQL/provider/Discord execution
requires a later exact operation/target approval; no connection strings to defaults in tests.

### S7 actual local checks

Recorded after final edits in [handoff S7 validation](post_s6_handoff_log.md#s7-documentation-delivery-and-validation).
Runtime pytest/full-suite/log-noise, smoke imports and command registration are skipped because
the actual delta is Markdown-only and no runtime/test/config source changed. Proposed tests
above have not run. No staging or staged-secrets scan authorized; no blanket hook pass claim.

## 9. Security review decision and evidence

Use k98-security-review-routing: **Bot documented skip**, exact 25-path Markdown-only patch
against `a2f148fa9bd4fb367fd46d0500a768c14fee915b`; no executable permission/input/network/
SQL/config/persistence change. **SQL separate no-change skip**, HEAD
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Root SECURITY.md supplies policy context;
no scan started. The final manifest/status/whitespace/link/evidence checks support the skip.

Every future runtime/SQL slice above requires a separate **Changes** review, **Deep off**, at
that repository's exact verified base/head or immutable working patch. Future SHAs do not yet
exist: resolve and record them immediately before review, do not reuse S7 anchors as invented
future targets. Store scan ID, manifest/findings/coverage, all reviewed paths and dispositions;
re-review relevant changed scope after fixes. Bot/SQL histories are never one combined target.
S11 documentation-only evidence may use a precise skip if it remains non-executable. No
standard/deep audit, automatic new task, PR, merge or live action follows from this plan.

## 10. Deployment/rollback

Nothing deployed. Future releases need repository-reviewed migrations before dependent Bot,
verified schema/backup/audit state, all participating writers on coordinated versions, exact
account/destination IDs and capability manifest, then separate G4 operations and G5 acceptance.
SourceRouting.Enabled alone is not activation. Mirror #272 and production #579 are merged;
local deployment is operator-attested only, not production runtime or fresh post-merge smoke.

Rollback means disable new admission/serving, retain fixed choice, finish/reconcile pinned jobs,
advance fences for explicitly selected older complete publication and report stale/unavailable.
Do not mutate accepted facts, delete receipts, reclaim uncertain files, reimport or silently route
to another source. Spreadsheet retirement is explicit and audited; no historical archive is required.
Preserve all S6 databases/files/uncertain states with their exact evidence references.

## 11. Follow-ups and approval

Stop for Chris Watts's review of the contract and exact manifests. S8–S11 implementation and
each operational action need separate approval. Remaining finite work is the eleven boundaries
in section 2, deployment/external-consumer inventory, exact SQL/provider operation plans,
S6-OPS01/PERF01/CAP01 integration evidence and operator G5 acceptance. No repeated product
decisions. Technical recommendations: initial account serialization, durable legacy spool with
worker affinity where needed, and one-generation quarantine/reserve allowance.

Completed-documentation review uses k98-pr-review for the local delta, not promotion readiness.
No runtime readiness or PR merge verdict can substitute for contract review, future security
reviews, actual deployed parity or Files changed verification after a PR is separately authorized.
