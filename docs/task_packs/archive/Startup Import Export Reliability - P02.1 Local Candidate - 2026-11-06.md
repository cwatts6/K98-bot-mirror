> **Archived 9 November 2026:** Superseded or completed Phase 1 instructions. Preserve the dated evidence below; do not replay its commands. [Current P02 scope and dependencies](../Startup%20Import%20Export%20Reliability%20-%20P02%20Remaining%20Work%20Handover%20-%202026-11-09.md) govern remaining work. Deployment is verified; standard production import/export acceptance remains open.

> **P02 integrated reconciliation, 7 November 2026:** See the [complete analysis and delivery plan](../Startup%20Import%20Export%20Reliability%20-%20P02%20Integrated%20Analysis%20and%20Delivery%20Plan%20-%202026-11-07.md). P02.1 and the SQL summary rewrite are locally qualified components, not completion of P02. Original factory/observer/holder/maintenance/file/legacy obligations, numeric alignment, unchanged cost gates and P03/P04 recovery dependencies are now mapped to one delivery sequence. Underlying-data and external-consumer analysis inputs remain explicit; production is not approved. Earlier dated statuses below are retained history.

# P02.1: passive recovery snapshots and producer refusal attribution

6 November 2026. **Implementation approved; local candidate, not release-ready.**
This is the first bounded delivery slice of the approved [P02 scope](Startup%20Import%20Export%20Reliability%20-%20P02%20Handover%20and%20Scope%20-%202026-11-06.md).
The subsequent operator approval supersedes that handover's review-only boundary for this local implementation and qualification.
It does not authorize production configuration changes, deployment, recovery, provider requests or a new import/export.

## Behavior and boundaries

Previously, merely inspecting several recovery records acquired the same global/account/import guards or update locks needed by producers. An observer arriving first could therefore cause a healthy producer's zero-wait admission to fail.

The affected inspections now use one dedicated SNAPSHOT transaction. They read a consistent committed picture without taking those application or update locks. Non-owning application-lock grantability checks hide actions when known work is active. A preview is neither proof of physical closure nor authority to settle work: actual recovery actions retain their session guards, current-row locks, scope checks and evidence/version comparisons.

Stats reporting inspection no longer executes the validation procedure that acquires writer/season locks. The procedure remains mandatory inside the guarded continuation action. User-facing previews explain that final validation occurs when the action runs.

The existing global producer guard remains exclusive and zero-wait. A known native 51421 refusal now retains the actual application-lock return code, requester session, transaction state/count and admission duration. Holder identity is explicitly unknown. No retry, automatic release, replay or closure claim is added.

## File and caller manifest

| Layer | Files and coverage |
| --- | --- |
| Shared snapshot lifecycle | `core/recovery_sql_snapshot.py`: dedicated connection, isolation selection, three-second statement timeout, zero lock-wait timeout, rollback/isolation restore/cursor/connection cleanup; cleanup uncertainty preserves the first failure and cannot become ordinary busy |
| Passive producer recovery | `services/stats_import_outcome_dal.py`, `all_kvk_capture_recovery_dal.py`, `player_report_recovery_dal.py`, `historical_import_recovery_dal.py`, `stats_report_continuation_dal.py`; inherited unreceipted/configuration consumers use the same path |
| Preview explanations | `services/import_recovery_service.py`, `configuration_producer_recovery.py`, `player_report_recovery_service.py`, `stats_report_continuation.py` |
| Guard attribution and identity | `services/legacy_snapshot_admission.py`, `legacy_export_snapshot_dal.py`, `export_contention.py`, `export_coordination_dal.py`; account-lock names share the exact existing hash derivation |
| Startup | `services/export_runtime_composition.py`: additional snapshot-isolation prerequisite after all three existing protected SQL contract checks |
| Deterministic coverage | `tests/test_recovery_sql_snapshot.py`, `test_legacy_snapshot_admission.py`, existing caller/continuation/lifecycle tests |
| Native SQL coverage | `tests/test_recovery_snapshot_native_sql.py`, `sql_snapshot_fixture.py`, `conftest.py`, `test_checkpoint_observation_sql.py`, `test_import_capture_recovery_sql.py`, `test_stats_report_continuation_sql.py`; inherited player/configuration/historical/unreceipted tests exercise the shared fixture |

No SQL repository source is modified. Canonical table/procedure definitions were checked in the independent SQL repository. Test fixtures formerly using global temporary tables now use ordinary objects inside uniquely owned disposable databases because tempdb fixtures cannot qualify this snapshot behavior.

## SQL prerequisite and lifecycle

The target database must already have `ALLOW_SNAPSHOT_ISOLATION` fully ON. The Bot checks `sys.databases.snapshot_isolation_state = 1`; it never enables the setting or falls back to locking reads. `READ_COMMITTED_SNAPSHOT` is not required or changed.

This database-wide setting can increase row-versioning/write/storage cost even though only these observers explicitly select SNAPSHOT. Representative import, report, maintenance and concurrent-observer costs, version-store headroom and long-reader behavior remain a release gate. The disposable fixture proves correctness and permissions, not representative production performance. Predeclare workload sizes, concurrency, cost denominators and acceptance thresholds before that comparison; do not label synthetic test elapsed time as a production budget.

ODBC qualification established that isolation must be selected before entering manual-commit mode: rollback newly owned factory setup, temporarily enter autocommit, set the SQL Server SNAPSHOT connection attribute, then enter manual-commit mode before creating the read cursor. There is no business commit. Cleanup attempts every phase even after failure, restores READ COMMITTED before closing, and preserves the original failure. The factory must supply a fresh dedicated connection, never a borrowed producer connection.

The three-second query timeout and zero lock-wait setting are statement budgets, not a hard total connection/cleanup deadline. Metadata/schema locks, connection failures and physical-close uncertainty remain explicit failure cases. Shared factory and end-to-end budget policy remains later P02 work.

## Local qualification checkpoint

- Expanded offline focused suite: **516 passed**; native tests: **122 passed across the completed runs**.
- The final twelve new native cases passed again after tightening the negative-permission assertion.
- Native evidence includes observer-first overlap, a producer committing between snapshot reads, producer-first busy results across consumer families, exact hashed account guarding, stale-token rejection, active-guard rejection, cross-scope refusal, read-only permission denial, disabled-isolation refusal, and actual 51421 attribution with distinct holder/requester sessions.
- Existing native recovery regressions preserve no-replay and stale-evidence safeguards. One unrelated existing reporting-monitor assertion fails because it omits the changing failure fingerprint; this is captured in the deferred register and was explicitly deselected only after observing the failure.
- Architecture, deferred-item and security-routing validators passed. Command registration reported 36 unique and 102 grouped commands without drift. Offline smoke imports passed with the repository's dummy CI configuration.
- Broader suite and final Changes security review are tracked in the delivery evidence; their completion is not asserted by this checkpoint. No PR, merge, deployment or whole-flow certification is implied.

Native work used the already-running local development instance, verified by server identity, and newly named disposable databases only. Existing local, restored and production databases/settings were not modified. Fixtures enable snapshot only on their newly created database and drop only that database without forced disconnection. SQL source remains independently versioned.

## Six-incident entry assessment

The operator ran the bounded private collector on 7 November 2026 at 08:13 UTC. All seven sections returned without errors or truncation. The six exact historical rows remain open at their previous revisions; five belong to the retained pipeline and one is an older projection. This does not represent six running jobs. Installed source/updater identities matched the P01.6 release. Snapshot isolation is currently OFF, so P02.1 cannot be installed yet.

The current receipt confirms the Stats import completed. Import, player cache, name cache and maintenance stages are observed; configuration remains unconfirmed and target cache/export are not started. No resource/execution-stream rows were linked to the four inspected preparations, but that is not account-wide absence of work or proof of physical closure. Captures, exact continuation inputs and closure evidence still need verification before an action. The private assessment records the exact identities and evidence; they are intentionally excluded from public source.

That first inventory is non-atomic and does not authorize recovery. Collect only missing exact receipt/capture/physical-closure evidence required by a supported action, close to its execution. Preserve committed Stats/player work. The existing pipeline-specific configuration continuation requires a verified cancelled predecessor and validated original request; the ordinary current-configuration action does not resume pipeline export. Prepare a separately authorized continuation or recovery plan where supported; retain P03/P04 dependencies otherwise. A cosmetic zero incident count is not the criterion for a new import/export.

## 7 November local qualification continuation

The protected updater now contains one exact 15-file P02.1 transition. Its 67 earlier entries are unchanged. Regression cases reject altered predecessors/successors, missing members, omitted inventory and an installed predecessor lacking the new family. The first focused updater run passed 275 tests. Historical source assertions authenticate the new successor before checking the unchanged earlier hashes.

A local updater installer/upgrade pair was built, never executed, bound to the observed P01.6 updater manifest. Compatibility against the observed deployed source classifies the current installed tool as `UPDATER_UPGRADE_REQUIRED` and the newly packaged tool as `ROUTINE_COMPATIBLE`. These are source-policy classifications, not SQL readiness or production approval. Exact candidate bytes and package hashes are retained privately; a final immutable release and host custody evidence remain required.

A predeclared local component study used two newly owned databases, 516,675 synthetic scan rows and the canonical table's 11 indexes. One warmup and five measured paired runs compared snapshot OFF/ON for 415-row append, 4,150-row update, full-history grouped reporting and a covering-index rebuild. All four median timings passed the declared OFF ×1.20 +50 ms screening limits. A held snapshot retained its original aggregate while another session committed the expected 4,150 increment. Observed database version-store retention was 42.2 MiB, below the declared 128 MiB bound; this total can include versions from preceding study operations. Both owned databases were dropped, with no SQL or cleanup errors.

This is component screening, not representative UPDATE_ALL2/report/maintenance qualification. The canonical table references `KS4_UNO_SEQ`, whose definition is absent from the SQL repository; the fixture used an explicitly synthetic sequence, never exercised because every SCAN_UNO was supplied. Five runs do not establish reliable tail percentiles. Allocation sizes include file/log growth and are not a storage-overhead measurement. Physical log write counters are observations, not transaction log generation. Full workflow cost, long-reader accumulation, production grants/profile/driver and headroom remain release gates. The private evidence contains the declaration, harness, hashes, measurements and limitations.

The full offline suite and refreshed Changes review are running against this continuation. Their final results belong in the private delivery receipt; this packet does not pre-claim a successful result.

## Related opportunities and remaining scope

This slice addresses the passive-observer portion of F03/F09 and the 51421 diagnostic gap. It does not close P02.

| Related work | Disposition |
| --- | --- |
| Other account/resource-owning observers, including unowned SQL holds and preparation/queue paths | Remain in the P02 caller/resource matrix; do not claim all observers are now non-interfering |
| F01/F26 factory policy and full connection/admission/execution/cleanup budgets | Later P02 slice; preserve first-failure and physical ownership semantics |
| F12 authority scheduling and F14 source-read contention | Later P02 qualification |
| All six maintenance stages, actual child procedures, legacy/manual paths and file/cache ownership | F16/F18/F20/F21/F22/F31 remain active |
| `ExportResource.ActivePreparationID` index candidate | Measure representative plans and write/maintenance cost before adding an index |
| SQL Agent legacy schedules and required `SUMMARY_PROC` calculations | Inventory current bindings/policy; do not silently retire required calculations or label them optional housekeeping |
| SQL notifications or completion signalling | No notification authority introduced; durability/reconnect/catch-up and cost evidence still required before selection |
| Retained pipeline continuation, terminal convergence and incident history | P03/P04, with exact dependencies carried into P02 readiness |
| P01.6 snapshot decode, Stats performance/SDK/ack and startup-warning follow-ups | Remain after P01-P05 unless a precise prerequisite is demonstrated and approved |

## Release order and rollback prerequisites

1. Finish local review and test disposition, including Changes security review of the exact Bot patch.
2. Qualify the database setting against representative workloads; establish the exact SQL setting/permission/install contract and independent SQL review target if a deployment artifact is introduced.
3. Prepare the Bot source-pin/updater transition and all three protected SQL contract checks. Obtain fresh affected-path and ancestor ownership/ACL evidence on the host.
4. Present the concrete installation order, verification and rollback for separate production approval. No current package should be deployed while the database prerequisite is absent.
5. On an approved release, qualify SQL configuration and all three protected SQL contracts before draining the old Bot or installing the dependent Bot. Startup refusal is a final safeguard, not a substitute for this pre-drain check. Reverting the Bot is the first rollback step; do not force-disable snapshot isolation or disconnect readers. Any later setting reversal needs drained readers and separate reviewed preconditions.

Production installation, fresh incident disposition and a normal whole-flow import/export remain outstanding and independently evidenced. Existing P01.6 closeout/archive edits in this worktree are preserved.
