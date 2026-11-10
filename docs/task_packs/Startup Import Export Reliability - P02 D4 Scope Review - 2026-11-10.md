# P02 D4 scope review and obligation reconciliation

10 November 2026. Review baseline: Bot `d4169d7`, SQL `eeefd6f`.
This is the source-review supplement to the
[canonical D4 handover](Startup%20Import%20Export%20Reliability%20-%20P02%20D4%20Scope%20and%20Handover%20-%202026-11-10.md),
not a competing programme or a runtime implementation receipt.

## Verdict and verified entry state

Retain D4a-e, with the explicit additions below. D4a should first deliver the
consumer inventory and F31 contract; D4b must close direct-child admission and
effective-principal dependencies before D4c/d pin a final release. D4e audits
coverage; it cannot defer missing functional work to D5 or P05. Existing remaining-
P02 approval stands. This first task performs scope/documentation work only.

Both existing checkouts were clean on `codex/p02-d4-scope`. Remote PR metadata
verified during this review:

| Repository | Draft head | Actual main base | State |
| --- | --- | --- | --- |
| [Bot mirror PR525](https://github.com/cwatts6/K98-bot-mirror/pull/525) | d4169d7ab6142aabaec4ebe1c0216deec34bb11c | 199c2d2fdda50095802fd7de207bdd7b029c0e46 | Open draft |
| [SQL PR150](https://github.com/cwatts6/K98-bot-SQL-Server/pull/150) | eeefd6ff52ea1513cebe8766a3fed2955785b53b | 2018ffe215138db363e62a5d6025a5407173b5e2 | Open draft |

Private PR739 is independently confirmed merged at `5ec55e3b`, reviewed head
`cc549f45`, 17:41:51 UTC. Local Bot origin fetches the mirror but its push URL is
intentionally disabled; production points to private K98-bot. SQL origin points
to its separate authoritative repository. Preserve these settings and independent
histories. No worktree was created. No installed-host, SQL-session, provider,
backup, restart, replay or deployment action was performed.

The current release descriptor still selects `p02_phase1_v1`, SQL `a202a514`,
and migration `20261109_001_p02_phase1_sql_exports`; it is not a D2/D3 installer.
The three protected contracts are `sql_contract`, `legacy_sql_contract` and
`application_sql_contract`. Each needs an explicit unchanged/changed disposition
and independently verified before/after evidence in D4d.

## Cross-repository caller and dependency matrix

SQL names below refer to authoritative `sql_schema` definitions. Runtime presence,
grants, jobs and manual/external use remain separate installed evidence.

| Boundary / callers | SQL and persistence dependencies | D4 owner and required proof |
| --- | --- | --- |
| Legacy stats: `dbo.UPDATE_ALL`, installed/manual/Agent callers | `CLAIM_KS4_IMPORT_FILE`, `ACQUIRE_KS4_IMPORT_LOCK`, `IMPORT_STAGING_PROC_CORE`, `KS4_ImportFileClaim`, `ARCHIVE_IMPORT_STAGING_FILE`, legacy output/report children; nested `UPDATE_RALLY_DATA` | D4a SQL/operator: classify use, exact arguments/configuration, input identity, transaction mode, child failure and output/maintenance overlap. KS4 claim does not claim Rally CSV. D4b/c qualify or explicitly retire the complete route. |
| Legacy Rally CSV: `UPDATE_RALLY_DATA`, including direct invocation | Fixed CSV, `RallyData_Raw`, `RallyData`, Rally outputs, naming helper, bulk/file identity and shell deletion | D4a/b: independent content-bound custody; no deletion before durable parent commit; original child error reaches caller; missing input has an explicit disposition; direct call and restart/unknown commit cannot replay. Preserve file evidence. |
| Rally XLSX: `upload_routes/rally_forts_route.py` -> `forts_ingest.py` | `sp_Import_Rally_Daily`, `sp_Import_Rally_AllTime`, staging/current tables, `IngestionLog` unique `(Source, FileName)` | Census as active source callers. F29 remains P03: failed attempt occupies filename identity. D4 must not mark all Rally paths closed by fixing the CSV child, or silently change XLSX deduplication. |
| `dbo.TEST`, ad-hoc/report/cache consumers | Destructive `DROP TABLE DEADSSUMMARY`, persistent DALL/D12/D6/D3 intermediates; retired-refresh history caches, direct summary calls, broad existing SELECT audiences | D4a operator/SQL: installed use, callers, permissions and output metadata. No execution for discovery. Active paths need supported exact semantics; retirement is a named decision. Static absence and restored empty jobs are insufficient. |
| Modern import: `processing_pipeline.py`, `update_all2_log_manager.py`, import capture/legacy writer DALs | `UPDATE_ALL2`, `IMPORT_STAGING_PROC_CORE`, `usp_MaintenanceDue`, KS4/KS5 and `KS4_UNO_SEQ`, committed import/continuation/file receipts | D4b/c: producer intent and actual sequence definition/permission dependencies. Preserve first error, exact captured inputs, uncertain commit and post-commit archive; do not replay Phase 1. |
| Configuration: `proc_config_import.py`, configuration producer/recovery | `sp_TARGETS_MASTER` -> `CREATE_DELTA_TABLES` -> `usp_MaintenanceConfigurationDue`, `MaintenanceConfigurationWork`, `MaintenanceWork`, optional `DeltaProcessingLog` | D4b/c: typed outer transaction, delta mutex, rows/large-batch generations and 168-hour/5000-row eligibility. Optional log failure cannot erase committed work or first failure. |
| Ordinary/guided/startup player report/cache | `services/player_report_sql.py`, `SP_Stats_for_Upload`, naming/provenance/capture, `usp_MaintenancePlayerReport` | D4b/d: publication guard, 15-second enclosing driver statement cap and 1-second row-lock policy, dedicated cleanup and no cache fallback after uncertain commit/close. D5 measures actual business completion. |
| KVK output and direct SQL callers | `sp_ExcelOutput_ByKVK`, required unique indexes/views, `usp_MaintenanceKvkDue`, `MaintenanceKvkWork`, optional nonunique upkeep | D4b/c: exact database/schema/table/object/header identity, one target per pass, partial target progress and stale-output refusal. Required output shape and receipt remain atomic. |
| Final reports/continuation, including legacy report entry | `usp_S11ValidateStatsReportStage`, `usp_S11CompleteStatsReportsCore`, stage receipts, final dashboard/summary due generations, `usp_MaintenanceFinalStats` | D4b/c: all protected source pins, exact eight-column success contract, metadata-reader exclusion and transactional intent. Preserve SQL 3961 as failed raw-history/index-DDL evidence. |
| Explicit maintenance: `file_utils.py`, `maintenance_worker.py`, `services/maintenance_dal.py` | `usp_update_stats` -> `usp_RunMaintenance`; six kinds and six children; four ledgers including backup | D4b/c: five ordered session guards, autocommit/implicit-transaction refusal, direct-child admission, finite receipts and all result-set draining. Lost release/rollback/cursor close retains connection and admission. |
| Backup dispatch: `services/maintenance_backup_dal.py`, `log_backup.py`; upload callbacks in `DL_bot.py` and seven route modules; pre-admission log relief | `usp_MaintenanceBackupClaim/Acknowledge`, `MaintenanceBackupWork`; separate msdb connection, configured wrapper/job and its principal; historical `LogBackupTriggerQueue` routines | D4a/b: distinguish each trigger and principal, effective metadata visibility, exact configured dispatch route, requested versus completed and failed/unknown ACK. Preserve schedules. Queue read/mark/cleanup/direct Agent callers require disposition, even though Python's old processor now returns held. |
| Passive recovery/season/queue/pool observers and authority | `core/recovery_sql_snapshot.py`, D2 recovery DALs, `source_routing_dal.py`, `authority_observation.py`; committed metadata and schema guard | D4b/d: SQL snapshot prerequisite, exact allowlisted observation selectors and source pins. Configuration reconciliation remains serial. D5 tests both ownership orders, one active/one waiting observer, busy replies, known holders and physical drain. |
| Factory and nested cleanup owners | `core/export_sql_connection.py`, profile/pre-KVK adapters, capture/source/legacy DALs, `core/sql_connection_custody.py` | D4d pins the complete final package. Preserve selected factory, retry policy, nested cursors/connections/guard generators and primary `UncertainCommit`; no proxy close, reused SPID or deadline proves termination. |
| File publication/readback | `file_utils.acquire_lock`, ordinary/guided/startup player cache, Ark state/team, tracked views | D3 accepted source; D4d pins exact successor dependencies and D5 retains failure/cancellation/foreign sentinel coverage. No Ark redesign or decode/rebuild expansion. |
| Release and startup | Bot descriptor, installed updater/registry and all three startup contracts; SQL profile/runner, source hashes, schema and permission fingerprints | D4c/d: exact installed-to-final tuple, Windows 5.1, authentic predecessor/postimage, interrupted/resumed SQL/source/seed/start/readiness. Private-only native workflow survives patch promotion. |

The final `usp_RunMaintenance` acquisition order is post-import, legacy snapshot,
delta publication, player publication, maintenance schema; the DAL verifies zero
transaction depth and all five locks released before pool return. The ledger
contract is four distinct tables, not just six rows in `MaintenanceWork`.
Inventory grants and direct table writers as well as EXECUTE callers.

## New or sharpened review items

These are required P02 review/implementation obligations, not new deferred debt.
Confirmed source facts are separated from missing installed or native evidence.

| ID | Evidence and consequence | Owner / disposition | Prerequisite and acceptance proof |
| --- | --- | --- | --- |
| D4-R01 | `usp_MaintenancePostImport` checks four guards then calls database-wide `sp_updatestats`; it does not check `K98:StatsForUpload:Publish`. `usp_RunMaintenance` takes all five. Import/configuration child checks also omit the player guard. A direct caller able to hold the other guards does not get the normal worker's complete admission protection. | D4b SQL: close the concrete post-import direct-child gap and audit each child's exact required guards, transaction mode and effective callers. No claim the normal worker lacks its lock. | Confirm direct rights/profile. Native two-session test: hold player publication elsewhere and invoke child with the other guards; it must refuse before upkeep. Also omit each mandatory guard in turn; valid owned worker still works and cleanup preserves first failure. Import/configuration requirements follow actual touched objects, not assumed uniformity. |
| D4-R02 | `UPDATE_ALL` lines 20-72 rejects existing transactions, claims only the canonical stats input, then invokes Rally. Rally deletes its separate fixed CSV at line 192 and PRINTs caught failure at line 203. UPDATE_ALL also writes shared outputs without the new maintenance calls/guard names. | D4a/b SQL: F31 needs two input identities, complete legacy output/maintenance overlap and direct invocation coverage; not merely replacing PRINT. Qualify used route or seek explicit retirement. | Source/installed caller closure; fail after Rally but before parent commit; commit succeeds/archive fails; lost commit ACK; same filename/different bytes; direct/outer/implicit transaction modes; concurrent modern writer/maintenance/reader. Input survives rollback; committed work resumes archive only. No existing KS4 claim is relabelled as Rally custody. |
| D4-R03 | `log_backup.request_once` selects wrapper versus Agent by `OBJECT_ID`; NULL can mean metadata is hidden. Maintenance owns a claim on one session, while dispatch opens a separate msdb connection using monitor/import credentials. | D4b SQL/release: qualify both identities and route visibility. An inaccessible wrapper is not proven absent. Preserve one attempted dispatch and no fallback after uncertainty. | Bounded definitions/permissions/configuration inventory; disposable restricted-principal tests for visible wrapper, proven absent wrapper, hidden/inaccessible wrapper, denied job rights and lost reply. Require supported route evidence before dispatch; no real backup to discover it. |
| D4-R04 | Upload routes still schedule `DL_bot.trigger_log_backup_background`; the old Python queue processor is held, but SQL GetPending/MarkProcessed/Cleanup routines remain. Cleanup deletes processed rows by age, with no new maintenance claim predicate. | D4a/b: include independent triggers, callable legacy mark/cleanup and installed job steps in backup coexistence. This is an unqualified entry point, not proof any current historical row was deleted. | Identify actual bindings/permissions; prove no old/unknown outcome can be adopted, marked or expired through an alternate consumer. Retain request/completion distinction and current schedule. Active conflicting consumers need compatible behavior or explicit retirement before release. |
| D4-R05 | Registry has 88 entries at its current entry ceiling; LF size 214882, CRLF size 219407, byte cap 232448. Windows headroom is 13041 bytes. Prior 87 digest matches `3f164e60c4398e9f4b1f2404b15cc0863b97ee658572824dd02b3e67f9597879`; cleanup has eight exact members. | D4d release: measure final combined representation early; the byte cap alone is not the entry-count gate. Preserve all 88 entries and historical checks. | Exact final inventory and smallest justified release-policy successor; reject missing/extra/foreign members in LF and CRLF. No byte-cap increase or registry redesign authorized; a needed entry-policy change must be explicit, bounded and reviewed. |
| D4-R06 | `MaintenanceWork.Table.sql` is CREATE plus seed INSERT; other new ledgers are source snapshots. Existing Bot descriptor points to Phase 1. There is no D2/D3 release profile in the inspected migrations delta. Generic module/additive profiles do not describe this whole migration. | D4c/d SQL/release: build one versioned combined migration/admission contract; do not deploy snapshots individually or replay Phase 1. | Authentic accepted Phase 1 predecessor and source/profile/permission pins; new table initialization only once; existing pending/running/unknown generations and receipts preserved; fault before/after SQL commit and interrupted source/seed/start; verifier must distinguish not applied, committed and unresolved. |
| D4-R07 | `forts_ingest` still has error-row/filename uniqueness behavior; the original handover assigns F29 to P03. Action census has exactly 73 pairs, 52 action names and 22 kinds, four empty; current policy adds/removes none. Group approval, generic Recheck and outcome-worker paths sit outside that count. | D4e: explicitly preserve F29/P03 and F27/P04; retain outside-policy operations in integration audit. No new automatic actions or blanket reapproval. | Per-family mapping below plus original dispositions. Recheck may reconcile; neither a policy count nor empty action set proves passivity. Exact mutation prerequisites remain action-time checks. |

R03 follows SQL Server's documented
[metadata visibility rules](https://learn.microsoft.com/en-us/sql/relational-databases/security/metadata-visibility-configuration).
The initial investigation considered whether Rally's `ANSI_WARNINGS OFF` leaks to
its parent; that is **not** a finding. Procedure-local SET options are restored on
return under the documented [SET contract](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-statements-transact-sql?view=sql-server-ver16).
The confirmed F31 failure/custody problems remain independently supported.

Inherited open requirements remain: authoritative `KS4_UNO_SEQ` and msdb wrapper
definitions; all four ledgers, due/claim/ACK and exact KVK identities; restricted
diagnostics and direct versus historical signed profiles; native permission order
and visible column order; immutable old captures; lossless rollback/write boundary;
high-log backup relief independent of optional statistics; late nested cleanup;
private workflow preservation; native fixture limitations and unrelated opt-in
diagnostic fingerprint assertion. None is closed by this source review.

## Original findings and source-census disposition

Read with the original [tracker](Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md)
and [action census](Startup%20Import%20Export%20Reliability%20-%20Action%20Census%20-%202026-11-02.md).
Accepted work remains accepted within its recorded limits. D5 integration evidence
does not reopen a completed slice without a demonstrated defect.

| Finding | Current owner and D4 consequence |
| --- | --- |
| F01 | D2a-l factory/budget source delivered; D4 pins it, D5 actual player workload and cost. |
| F02 | P03 exact provider-result/closure settlement; D4 migration preserves held stream evidence, no resend. |
| F03 | D2 scoped passive reads and required mutation locks delivered; D4 permissions/dependencies, D5 both orders. |
| F04 | P03/P04 passive versus active recovery semantics; D4e includes Recheck/batch/accepted-action reconciliation. |
| F05 | P04 original failure/history/report convergence; preserve evidence through D4 migration. |
| F06 | P03 exact completed-stage binding, P04 projection; no replay to repair observation. |
| F07 | P01.2a evidence and D2k bounded holder diagnostics; D4 restricted rights, D5 known holder; historical attribution stays unknown. |
| F08 | P01.1 accepted startup result/physical drain; D4d startup integration and D5 regression only. |
| F09 | D2 observers/global ownership/holder delivery; D4 identity and permission closure, D5 contention; retained CFG-51421 work remains P03. |
| F10 | D2 passive pipeline/recovery reads; P03 exact binding. D4 keeps action checks independent from previews. |
| F11 | P01.3 accepted passive status/Refresh; D4 adds no provider checks; broader P04 remains. |
| F12 | D2j observation lane delivered; D4 pins selectors/authentication, D5 saturation and shutdown. |
| F13 | P04 meaningful incident/waiting/progress classification; no age-based maintenance/recovery release in D4. |
| F14 | D2h consistent season metadata delivered; D4 SQL prerequisites, D5 stale tuple/both-order regression. |
| F15 | P03 original-intent cache continuation; D4 preserves report/capture generation, no second production run. |
| F16 | D3 committed import versus backup/upkeep delivered; D4 alternate dispatch/caller/profile audit, D5 cost/faults. |
| F17 | P01.4 accepted import/audit/refresh/delivery separation; natural evidence still tracked; no broad importer rewrite. |
| F18 | D3g final-stage receipts/optional upkeep delivered; D4 exact migration and legacy callers, D5 real combined work. |
| F19 | P04 notification-journal admission/capacity/history; no D4 deletion to free capacity. |
| F20 | D3a shared file ownership delivered; D4 final package pins, D5 equivalent-caller physical failure/restart. |
| F21 | D3d configuration upkeep/log separation delivered; D4 direct/typed callers and ledgers, D5 actual child. |
| F22 | D3 all six maintenance boundaries delivered; D4 direct-child/profile closure including R01, D5 cost/overlap. |
| F23 | P01.5 calendar audit separation accepted; retain natural limits, no D4 calendar scope. |
| F24 | P01.5 calendar and P01.6 read-worker custody accepted; D2/D3 SQL adoption plus D5 combined drain, deferred performance unchanged. |
| F25 | P01.5 primary/auxiliary calendar outcome accepted; no D4 cache redesign. |
| F26 | D2 factory fallback correction delivered; D4 unchanged profiles/no fallback, D5 alternative factory failures. |
| F27 | P04 report-validator waiting versus real conflict; D4 carries actual 51961/51966 contracts, no blanket retry. |
| F28 | P03 saved cancellation proof and linked projection, with P04 convergence; D4 preserves exact receipts. |
| F29 | P03 Rally XLSX attempt versus successful identity; D4a census includes it but F31 does not absorb or close it. |
| F30 | P01.4 optional CSV isolation delivered; required custody remains mandatory; natural limits retained. |
| F31 | D4a/b legacy/manual input, error, commit/archive and coexistence contract; qualify active paths or explicit retirement. |
| F32 | P01.1 primitive accepted, P01.2a evidence adopted; D4/D5 must preserve first failures and qualify their own cleanup/diagnostic use. |

All original source families C01-C16 are accounted for: C01/C08/C14 retain P01
acceptance; C02/C03/C05/C13/C15 map to the player/configuration/factory/custody rows;
C04/C11 map to import/report/maintenance and D4 legacy consumers; C06 retains P03
result/closure and D2 scheduling; C07/C10 include recovery, scheduled/manual and
shutdown callers; C09/C12 retain P04 history/notifications and P01.4 outcomes;
C16 retains D2 snapshots plus P04/F27 classification. Gaps in installed bindings
are D4a evidence gaps, not silent closure of the original dynamic-edge census.

## Slice order and concrete first slice

1. **D4a, census and F31 contract.** Produce a source-root inventory of legacy
   UPDATE_ALL/Rally/TEST, active XLSX routes, cache/summary consumers, every
   maintenance/backup direct entry and scheduled/external binding. Each row records
   source hash, caller, target, effective identity/profile, arguments/configuration,
   input/output identity, transaction/guard owner, outcome and cleanup, used/unused/
   unknown, evidence time, owner and qualify/retire/hold disposition. Unknown stays
   included. Trace transitive/dynamic names, synonyms, cross-database calls and
   permissions; distinguish permission-hidden, encrypted/unreadable and absent.
2. **D4b, contracts and necessary behavior.** Close F31 for active paths, R01 child
   admission, missing dependencies, exact direct/signed permission contracts and
   backup-route/alternate-consumer behavior. Keep commands/views thin; reuse
   existing service/DAL/custody contracts and SQL claim/archive patterns. Do not
   add a general queue, scheduler or outbox. Commit source/profile dependencies
   together in bounded Bot/SQL slices where needed.
3. **D4c, migration and recovery.** Derive the exact Phase 1-to-final SQL delta,
   order dependencies/ledgers/children/producers/grants, bind explicit target and
   pre/post checks, preserve committed work and durable resume. Determine whether
   coexistence is proved or a drained window is necessary. Reverse numeric types
   only across a proved lossless write boundary; otherwise forward/backup recovery.
4. **D4d, final combined integration.** Start registry sizing/compatibility analysis
   during a/b, but pin only the final c candidate. Bind actual private Bot predecessor,
   SQL main commit/profile, installed updater and all three startup contracts. Prove
   the combined transition and negative controls; retain Windows 5.1, interrupted
   preparation and private-file promotion custody.
5. **D4e, obligation audit and D5 handoff.** Reconcile this matrix, original findings,
   action census, deferred owners, all review corrections and release tests. Supply
   fixed final heads, remaining limitations and D5 scenario-to-evidence plan.

First implementation-sized deliverable is **D4a's bounded inventory tooling and
F31 contract tests/design**, not installation. Reuse retained read-only collectors
where their fixed targets and result shapes fit. Prepare a finite query/object/job
allowlist and a reviewed Windows 5.1 collector with explicit host/database/principal,
timeouts, row/byte caps, private output and partial/unavailable results. Inventory
SQL Agent and Windows-task bindings, service identities, relevant source definitions,
grants/signatures and configured job dispatch without executing business procedures,
`NEXT VALUE FOR`, backup, provider probes or reconciliation. Metadata collection
is not PrepareOnly: the latter can create deployment artifacts.

Installed execution needs its exact current target/access evidence before it runs;
this review has not established host readiness or reused a pre-crash session.
Source-only inventory and synthetic collector tests can proceed independently.
Legacy retirement needs operator disposition after the evidence; until then qualify
active/unknown paths by default. F29 stays P03 unless a concrete D4 dependency is
demonstrated and agreed. No blanket scope approval is being requested.

## Validation and evidence plan

| Gate | Meaningful evidence / existing test anchors |
| --- | --- |
| D4a collector | Offline known binding, dynamic/unresolved caller, hidden metadata, empty-versus-unavailable jobs, duplicate/oversized/truncated rows, wrong host/database/principal, cancellation and partial collection; PowerShell 5.1 scalar/array shapes. No business invocation in collector. |
| F31 | Disposable fixtures only after exact target authority/readiness: independent Rally/stats input digests, parent failure after child, direct and nested invocation, implicit mode, missing/changed file, file replacement, commit/archive split, lost ACK/restart and modern maintenance overlap. Preserve original errors and no replay. Existing `tests/test_forts_ingest.py` is XLSX/F29 context, not F31 proof. |
| Direct children/profiles | Extend `tests/test_maintenance_owned_native.py`, six maintenance-native families and SQL `tests/test_maintenance_session_contract.py`; omit each required guard, use denied/restricted callers, retain successful owned worker and cleanup. No sysadmin-only success substituted for runtime principal. |
| Backup | `tests/test_final_stats_maintenance_native.py`, backup DAL and dispatch tests: dual principal/visibility, separate upload/pre-admission paths, high-log deferred stats with eligible relief, orphan/failed/unknown/no retry, exact claim ACK, no actual Agent/provider call. |
| Migration | Extend SQL release runner/profile tests for exact predecessor, partial/drifted tables, preserved outstanding generations/claims/old queue rows, receipt atomicity, before/after-commit process loss, supported resume, source rollback compatibility and denied permissions. Do not alter historical manifests. |
| Bot/updater/startup | `tests/test_prepare_k98_update.py`, `test_combined_k98_update.py`, `test_p02_phase1_release.py`, `test_p02_phase1_permission_repair.py`, `test_p02_d3_cleanup_update_transition.py`; final tuple plus old/missing/stale/foreign/partial pins, Windows LF/CRLF capacity, native permission ordering and real visible-column drift. Source capability is not installed admission. |
| D5 final combined | All 14 outputs/detailed state, exact names/numeric/rounding/old-payload fidelity, real children, observer and producer first, known holders, scheduling saturation, failure/lost ACK/cancellation before and after native entry, restart, nested cleanup and balanced cost. Distinguish simulated calculations/provider delivery from actual exercised work. |

D5 keeps RCSI off, free memory/disk >=8 GiB, optional-statistics log <70%, version
store <512 MiB; warmup plus at least five balanced measured pairs, overall median
ON <= OFF*1.20+1000ms and each stage <= OFF*1.20+250ms. Preserve three-second
snapshot statements, zero row-lock wait and bounded 30-second metadata snapshot.
The 1800-second rehearsal cap is not a production timeout change. The 21-input
allowance is consumed; no new copy, schedule change or larger allowance is implied.
Recheck host/VM readiness before any later authorized run. SQL 3961, tied-zero
ranking policy, report execution-clock comparisons and the unrelated diagnostic
fingerprint assertion remain explicit. No additional full rehearsal runs here.

## Decisions, exclusions and publication

Outstanding evidence: installed consumer/permission/job bindings; missing sequence
and wrapper source; restricted runtime capability; exact installed combined tuple;
approved test-host readiness. Outstanding decisions arise only if evidence calls
for legacy retirement, consumer compatibility, a different permission mechanism,
unsupported release-policy/capacity change or a lossless rollback alternative.
No new broad grant, TRUSTWORTHY, automatic profile fallback or scope-wide reapproval.

Broader numeric conversion, snapshot decode/rebuild, broad orchestration extraction,
Stats UI/SDK acknowledgement, unrelated MGE/Ark performance and standalone pre-KVK/
weekly physical-close debt retain their existing owners. No new deferred item is
created: R01-R07 are integration obligations or clarified existing boundaries.

P03 actual blockers and essential P04 corrections precede the first normal
import/export. Neither zero incidents nor waiting merely for P05 is a prerequisite.
D6/D7 retain separate release/recovery and provider/natural acceptance authority.

This delta is Markdown only. Architecture, deferred-item, security-routing,
test-selection, local-link/whitespace and scoped pre-commit checks are required.
Runtime/native tests, imports, registration and formal security scanning are skipped
for this documentation-only patch: executable, SQL, permission and deployment bytes
are unchanged. Future executable Bot and SQL patches need separate exact Changes
reviews, Deep off. No repository-wide security audit is selected.

Reviewed documentation must be published through existing mirror PR525, identical
private file-patch promotion and SQL PR150. Draft update, accepted scope, source
merge, installed qualification and deployment remain distinct. Preserve private-only
workflows and private inventories; do not call local or draft text merged delivery.

## Action-policy reconciliation

The source policy was parsed without importing Bot code and compared as exact
source/action pairs with the original action census: **73/73 equal, zero missing,
zero extra; 52 distinct actions across 22 kinds, four without individual actions**.
The rows below enumerate every pair while preserving the original per-action
classification in that census. P03 owns exact settlement/continuation; P04 owns
convergent presentation/history; D4 preserves contracts and D5 tests integration.
This does not enable automation or certify state-specific runtime eligibility.

| Source kind | Count | Exact actions; original dispositions unchanged |
| --- | --- | --- |
| `evidence_batch` | 0 | No individual action; associated workflow is not thereby passive. |
| `historical_batch` | 0 | No individual action; associated workflow is not thereby passive. |
| `export_rollover` | 10 | `activate_replacements`, `choose_replacements`, `continue_unstarted_rollover`, `discard_replacement_check`, `finish_replacement_check`, `isolate_targets`, `start_replacement_rollover`, `verify_replacement_rollover`, `verify_replacements`, `verify_rollover` |
| `recovery_overview` | 0 | No individual action; associated workflow is not thereby passive. |
| `queue_admission` | 3 | `close_withdrawn_read`, `withdraw_health_probe`, `withdraw_queued` |
| `unowned_sql_hold` | 1 | `clear_unowned_hold` |
| `player_report` | 5 | `abandon_capture`, `cancel_report`, `complete_cache_only`, `queue_capture`, `resume_capture` |
| `all_kvk_capture` | 3 | `abandon_capture`, `queue_capture`, `resume_capture` |
| `export_job` | 14 | `activate_replacements`, `allow_next_export`, `choose_replacements`, `discard_replacement_check`, `finish_replacement_check`, `isolate_targets`, `publish_replacement`, `rebuild_damaged`, `retire_failed_export`, `retry_absent`, `retry_unstarted`, `skip_unstarted`, `verify_publication`, `verify_replacements` |
| `private_evidence` | 4 | `attest_containment`, `attest_registration`, `protect_evidence`, `restore_evidence` |
| `configuration_attempt` | 0 | No individual action; associated workflow is not thereby passive. |
| `configuration_read` | 2 | `contain_read`, `release_read` |
| `producer_refusal` | 4 | `cancel_saved_stage`, `close_unstarted_admission`, `resume_current_registration`, `resume_sql_stage` |
| `configuration_producer` | 5 | `abandon_capture`, `cancel_configuration`, `complete_configuration_only`, `queue_capture`, `resume_capture` |
| `configuration_continuation` | 3 | `continue_configuration_export`, `keep_prior`, `retry_configuration` |
| `configuration_read_continuation` | 3 | `continue_configuration_export`, `keep_prior`, `retry_configuration` |
| `player_report_continuation` | 3 | `keep_prior`, `refresh_cache`, `refresh_report` |
| `stats_report_continuation` | 1 | `continue_reports` |
| `processing_pipeline` | 3 | `continue_stage`, `retain_stage`, `verify_stage` |
| `unreceipted_producer` | 1 | `retain_unknown` |
| `legacy_configuration_continuation` | 2 | `keep_prior`, `retry_configuration` |
| `stats_import` | 6 | `abandon_capture`, `queue_capture`, `release_failure`, `resume_capture`, `retire_historical_export`, `supersede_partial` |

Outside-policy operations remain explicit: generic Recheck and accepted-action
reconciliation; evidence/historical group approvals (up to 25 members); inherited
producer/replacement/rollover adapters; processing outcome-worker settlement and
live writer exact-completion capture. D4 adds no observer selector for those mutations.
