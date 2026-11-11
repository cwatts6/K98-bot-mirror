# P02 D4 scope and handover

> **D4 delivery, 11 November:** The [delivery and D5 handoff](Startup%20Import%20Export%20Reliability%20-%20P02%20D4%20Delivery%20and%20D5%20Handoff%20-%202026-11-11.md) records the completed source slices, approved decisions, validation and remaining owners. This original scope remains the historical obligation baseline; D5/D6 and operational acceptance are still open.

> **Scope review, 10 November:** Read the [independent obligation reconciliation](Startup%20Import%20Export%20Reliability%20-%20P02%20D4%20Scope%20Review%20-%202026-11-10.md)
> for the refreshed Bot/SQL caller matrix, F01-F32 and exact 73-pair action census,
> new direct-child/backup/legacy admission items, registry capacity and concrete D4a
> slice/test plan. D4a-e remains the sequence; installed evidence and D4/D5 closure
> are still outstanding. No runtime or production action occurred.

## Current decision and authority

On 10 November 2026 the operator requested: merge production PR739, prepare D4
scope/handover carrying all remaining obligations, keep deployment held until D4/D5
are complete, and start a new D4 chat with a scope review and missed/new-item check.

PR739 is merged at **5ec55e3bbfaaca020b6046e94d80bb7645736742** (17:41:51 UTC).
This is a repository merge only. No production SQL, deployment, restart, provider
action, backup dispatch, retained-work recovery or standard import/export was run.
The last accepted installed baseline remains Phase 1; this handover makes no fresh
live-host claim. D2 and D3 source merge does not establish installed acceptance.

The new chat's first deliverable is review/scope only. Carry forward the already
approved remaining-P02 direction and settled agreements; do not ask to reapprove
unchanged scope. Identify genuinely new decisions and evidence gaps before runtime
implementation. These proposed D4 slices are a review starting point, not an
instruction to execute migrations or an assertion that installed evidence exists.

## Exact starting evidence

| Item | Verified source or receipt |
| --- | --- |
| Private D3 reviewed head | cc549f45c58053c51d05560773a53372a630a85b; PR739 merged as above |
| D3 mirror delivery | PRs 513-519 and corrections 520-524; final merge 7b831f3171aa9cc0865195e83e69f660c403fa11 |
| Refreshed mirror base | 199c2d2f, scrubbed snapshot of private merge 5ec55e3b; verify current base before publication |
| SQL delivery | PRs 142-147 plus documentation 148-149; 2018ffe215138db363e62a5d6025a5407173b5e2 |
| Final local regression | 13,376 passed, 1,262 skipped, one existing warning, eight subtests; operational logs unchanged |
| Final private CI | Six checks passed; Linux 13,197 passed / 1,441 skipped, Windows updater 315 passed, release identity 111 passed, native file ownership on Windows/Ubuntu and secret scanning passed |
| Review | Final-head Codex review clear; zero unresolved Bot/SQL/private threads. Secondary Copilot review reported policy restrictions and is limited evidence, not an independent review pass |
| Promotion custody | All 128 changed paths authenticated against mirror preimages/postimages; unrelated private files preserved |

The final [PR739 receipt](https://github.com/cwatts6/k98-bot/pull/739#issuecomment-6773271380)
retains exact checks, review dispositions, scan usage and superseded runs.
The [D3 delivery review](Startup%20Import%20Export%20Reliability%20-%20P02%20D3%20Delivery%20Review%20-%202026-11-10.md)
and its archived slices remain evidence. Earlier failed, stopped and superseded
runs are not acceptance. No completed D3 slice is to be replayed merely for freshness.

## Proposed D4 sequence and closure matrix

| Slice | Scope and accountable owner | Required closure evidence |
| --- | --- | --- |
| D4a: installed and consumer census | SQL/release reviewer plus operator: actual UPDATE_ALL, Rally import paths, TEST, scheduled/manual/direct callers, cache readers and external consumers; F31 input/archive/error contract | Bounded installed bindings and permissions, source-to-caller matrix, explicit used/unused/unknown classification. Qualify each active path or obtain named retirement approval. Static absence, empty restored jobs and no-known-use are not proof of no installed/external use. No business execution to discover use. |
| D4b: dependency and permission contracts | SQL and security/release owners: missing sequence/wrapper source, direct child admission, four maintenance ledgers, six kinds, restricted diagnostics, configured backup dispatch route | Authoritative definitions and dependency closure; exact supported permission/profile/signature expectations and denied-principal cases. Preserve direct_application_v1 where approved and historical signed profiles. EXECUTE AS OWNER is not blanket proof of cross-database/DMV access. No automatic profile fallback, new broad grants or TRUSTWORTHY. |
| D4c: versioned SQL release and rollback | SQL/release owner: D2/D3 changes over accepted Phase 1, producer/child/table dependencies and source/permission identities | Explicit-target, predecessor/postimage-checked installer and durable migration/resume receipts; exact order and compatible switchover. Preserve old captures, outstanding claims and backup rows. Prove rollback/forward recovery without destroying new committed data. Disposable K98DEV installers are not production installers. |
| D4d: combined Bot/updater/startup integration | Bot and release owners: actual installed-to-final combined jump, all three protected startup contracts and final SQL/profile pins | Demonstrated resolution of COORDINATED_RELEASE_REQUIRED for the exact final tuple; positive and missing/stale/foreign/partial dependency refusals. Preserve historical transition hashes and source/permission fingerprints. Qualify Windows PowerShell 5.1 and interrupted/resumed preparation. Per-slice transitions or CI source classification cannot stand in for installed admission. |
| D4e: integration audit and D5 handoff | Bot/SQL reviewers and test owner | Every original finding, equivalent caller and late D3 correction mapped to evidence or a named remaining owner; no unowned closure item. Fixed final candidate, validation matrix, release order/rollback and proposed D5 resource/cost plan. No production-ready claim until D5 and separate D6 release gates. |

D4a evidence constrains D4b/c; D4d binds the final c contracts, and D4e closes the
cross-repository review. Independent source analysis may proceed together, but do
not pin a hypothetical final candidate or assume unknown installed contracts.

## Missed/new-item check required at entry

The preliminary handover reconciliation identified these concrete carry-forwards:

1. The old D3 handover said 87 transitions. Final source has **88**, including
   p02_d3_cleanup_custody_v1 with eight members. The prior 87 digest remains
   3f164e60c4398e9f4b1f2404b15cc0863b97ee658572824dd02b3e67f9597879;
   registry cap remains 232448 bytes. Authenticate final occupancy and all old
   entries; do not increase the cap or redesign the registry without evidence.
2. Include the late cleanup correction across snapshot, maintenance, player,
   import-capture, source transaction and legacy writer owners. Unknown rollback,
   isolation reset, cursor/guard release or close retains exact nested resources
   and prevents pooling. Preserve first failure and UncertainCommit; a closed
   proxy, elapsed deadline or reused SPID does not establish physical closure.
   D4 covers contract integration; D5 covers final combined fault/restart behavior.
3. Repository search finds dbo.KS4_UNO_SEQ referenced by KingdomScanData4's default
   but no authoritative sequence definition. The installed msdb wrapper
   usp_start_rok_tracker_log_backup also lacks authoritative SQL source here.
   Read installed definitions/permissions only through an appropriately bounded
   approved inventory; do not synthesize definitions from fixtures or call a backup
   merely to test whether it exists. Reconcile the configured wrapper/job dispatch
   route, cross-database identity and acknowledgement contract.
4. All four ledgers require coordinated release treatment: MaintenanceWork,
   MaintenanceConfigurationWork, MaintenanceKvkWork and MaintenanceBackupWork.
   Include due/claim/ACK routines, all six children, producer transactional intent,
   dynamic KVK output identity and every direct caller; table snapshots alone are
   not an installer. Historical LogBackupTriggerQueue rows remain protected.
5. Backup relief remains eligible from committed summary demand when high log use
   defers optional statistics. Requested is not completed backup. Lost ACK, absent
   owner and failed/unknown dispatch cannot lead to fallback or replay by age.
6. Preserve Phase 1 numeric/export and permission-order lessons. SQL native
   permission grouping/inner order and visible schema column order must remain
   authenticated; do not accept live hashes merely to silence startup refusals.
   Old queued serialized captures remain immutable. Reverse bigint-to-float
   conversion is unsafe after writes beyond exact float range; use a proved
   write boundary and forward recovery/backup strategy where needed.
7. The mirror refreshed after PR739 and omitted the private native file-lock
   workflow. Private main retains it. Check all actual private CI results and
   preserve private-only files during patch promotion. Mirror CI absence and
   clean Git status do not establish deployment custody or remote check enforcement.
8. Keep the unrelated opt-in test_stats_report_continuation_sql diagnostic
   fingerprint assertion visible; do not weaken it or count it as a D3 failure.
   Native cases used actual guards/receipts with simulated large calculations and
   provider delivery where recorded. These limits must enter D5's matrix.

The new chat must independently double-check this list against source, the D2/D3
reviews, original F01-F32/action census, integrated plan and remaining-work lessons.
Record any new item with source evidence, owner, disposition, prerequisite and
acceptance proof. Do not silently move a required P02 obligation into P05 or debt.

## Architecture and source entry points

Commands/views remain thin; service orchestration and DAL transaction boundaries
retain their roles. Reuse existing lifecycle/custody/release tooling; no new general
scheduler, outbox or diagnostics framework is implied. Inspect all equivalent
callers rather than patching one visible refusal. This packet changes prose only.

Bot entry points: core/sql_connection_custody.py, core/recovery_sql_snapshot.py,
services/maintenance_dal.py, services/maintenance_service.py, maintenance_worker.py,
log_backup.py, services/player_report_sql.py, services/import_capture_recovery_dal.py,
services/legacy_export_snapshot_dal.py, services/legacy_export_snapshot_service.py,
kvk/dal/new_source_import_dal.py, scripts/prepare_k98_update.py,
scripts/k98_update_transitions.json, scripts/validate_k98_update_compatibility.py,
scripts/verify_k98_update_pair.py and deploy/k98-release.json. Read the current
protected release/startup contract and Windows ownership/access contract before
designing operational commands; exact final affected files must come from census.

Authoritative SQL is C:/K98-bot-SQL-Server. Start with
docs/p02-integrated-sql-delivery-plan.md, docs/p02-d3-maintenance-ownership.md and
docs/p02-d4-scope-handover.md; then the actual sql_schema producers, ledgers and
children, migrations/20261109_001_p02_phase1_sql_exports.release.json,
qualification/p02_phase1 and deploy permission manifests. Do not infer schema
from Python, use obsolete original profiles, or treat historical counts as live facts.

## D5, D6/D7 and cross-package obligations

D5 must qualify the final combined D1-D4 candidate against the accepted baseline:
all 14 output sets and detailed state, exact numeric/rounding deltas and old queued
payloads; actual relevant maintenance children; both ownership orders, observer
saturation and known holders; real faults, lost ACK, cancellation before/after
native entry, commit/rollback/close uncertainty, restart and scheduling. Retain
first-failure evidence separately from recovery. Compare only controlled arms;
simulated delivery is not provider acceptance.

Keep RCSI off. Preserve free memory and disk reserves of at least 8 GiB, sampled
log below 70 percent for optional statistics and version store below 512 MiB.
Warmup then at least five balanced OFF/ON measured pairs: overall median
ON <= OFF * 1.20 + 1000 ms and each report-stage median <= OFF * 1.20 + 250 ms.
Retain the actual short observer's three-second statement budget, zero row-lock
wait and bounded 30-second held metadata snapshot. The 1800-second rehearsal cap
is not a Bot timeout increase. The single 21-input allowance is consumed; no new
copy, larger allowance or backup-schedule change is authorized. Revalidate test
host/VM/session readiness after the prior development-PC crash before future runs.

SQL 3961 from raw-history SNAPSHOT across index REBUILD remains failed evidence.
Managed metadata-reader exclusion does not qualify arbitrary readers or ad-hoc DDL.
Retain equal-score/tied-zero ranking as an explicit policy question, and compare
date-window reports against actual report execution time rather than collection time.

D6 requires separate coordinated release authorization after D4/D5, fresh exact
installed Bot/SQL/updater/startup identity and changed-path/ancestor custody, safe
drain, migration/resume and rollback preserving committed work. SQL may have
committed before later startup verification failed: inspect receipts and resume
only supported remaining steps. Never reapply SQL or start a second Bot to repair
an uncertain start. Production uses Windows PowerShell 5.1 and private main.

D7/P05 retain exercised whole-flow/provider and natural acceptance. P03 owns actual
retained-work blockers and continuation; essential P04 cancellation, incident,
history and notification convergence corrections precede the first normal
import/export. Neither zero incidents nor waiting merely for P05 is a prerequisite.
Refresh exact request/capture/claim/stream predicates at action time; never replay
committed business/provider effects or clear ownership from age or historical counts.

Broader datatype conversion, snapshot decode/rebuild optimisation, broad import
orchestration extraction, Stats UI/SDK acknowledgement, unrelated MGE/Ark
performance and standalone pre-KVK/weekly physical-close debt retain their existing
owners. Bring work forward only for a demonstrated dependency. Existing P01.4/P01.5
natural observations and P01.6 limitations remain open where recorded.

## Validation, publication and first new-chat deliverable

This handover is Markdown only: no runtime, SQL definition, migration, permission,
configuration or deployment behavior changes. Run architecture/deferred/security-
routing/test-selection, introduced-link and whitespace checks plus pre-commit.
Runtime pytest, native SQL, imports and registration are skipped for this prose-only
delta; previous final-head receipts remain evidence for their own source. Formal
security scan is skipped precisely for the documentation delta. Future executable
Bot and SQL changes need separate Changes reviews of their exact diffs, Deep off;
no standard/deep repository audit is authorized by this scope request.

Prepare focused documentation branches/draft PRs for this scope review. They are
not runtime implementation or a new deployment approval. The D4 owner must carry
the reviewed documentation through mirror merge, identical private file-patch
promotion and the SQL companion, preserving private-only workflows and archive
evidence. Do not present an unpublished local handover as remotely delivered.

First new-chat output: refreshed cross-repository caller/dependency/ownership matrix;
disposition of every inherited and newly found item; review of D4a-e order and scope;
concrete first slice, tests, evidence sources, remaining decisions and cost limits.
Begin the review immediately rather than only acknowledging this handover. Preserve
existing approvals and distinguish review completion, implementation readiness,
source merge, installed qualification and deployment acceptance.
