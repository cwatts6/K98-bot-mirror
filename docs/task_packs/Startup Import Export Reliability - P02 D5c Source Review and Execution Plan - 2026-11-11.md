# P02 D5c source review and execution plan — 2026-11-11

Status: **source review complete; execution is not authorized by this packet.**
The operator requested the review and concrete plan before any further native
work. No SQL connection, VM operation, native test, permission change, runtime
correction or workload ran. This packet proposes the next preparation step and
the gates for subsequent execution; it does not mark D5c qualified.

## Scope and starting evidence

D5c owns observation and competing-owner qualification: both arrival orders at
global, account, season, schema, delta, player and file boundaries; known-holder
attribution; alternative factories/rights; saturation; serial mutation progress;
disabled isolation; stale tuples and action-time validation. It retains F03/F04,
F07/F09-F12/F14/F20/F26/F27, C05-C08/C11/C13/C15/C16 and A02/A03/A07/A13/A14 from
the [obligation reconciliation](Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Obligation%20Reconciliation%20-%202026-11-11.md).
Broader lost-acknowledgement, process-death/restart and cleanup-fault schedules
remain D5d; measured balanced costs remain D5e. Their boundaries are not waived.

[D5b closed](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Closeout%20-%202026-11-11.md)
with all 42 states, 14 exports and six real maintenance children qualified.
The 21-input allowance is consumed; **1,480 seconds remain** in the carried native
rehearsal budget. This source review consumes neither inputs nor native budget.
The previous one targeted post_import recovery retry is consumed and cannot be
reused. All D5b completed claims and original failures remain evidence.

Current source heads were read locally: Bot
`e7443e37212ca91e20d531b3684cc369d0fe1505`, SQL
`b924cedd53e29dd88c0e9e7b66208b4fdc1e53ba`; fixed D4 payload remains
`ba5c6acbefba0eb89cb18842a7f6c6811096759b`. Existing uncommitted D5a/Q05 corrections
and qualification packets are preserved. A source digest is not installed-host
proof. No publication, merge or deployment is proposed.

Private `C:\discord_file_downloader\.codex_artifacts\p025\d5c-source-review.json`
binds 52 relevant source/test/schema files, inventories **35 direct managed
snapshot call sites in 11 files**, and re-enumerates **73 action pairs in 22 kinds,
including four empty kinds** using AST reads without importing application code.
This is a direct-call census, not proof that dynamic or inherited paths are absent.
The existing equivalent-caller register remains binding. Six D5b success/failure
and closeout receipt hashes were freshly verified. Original CI drain and raw
SQL 3961 evidence remain retained; neither is relabelled by this review.

## Source findings and architecture direction

1. `core/recovery_sql_snapshot.py` owns a dedicated connection, selects ODBC
   SNAPSHOT before manual-commit entry, and acquires shared transaction resource
   `K98:maintenance-schema:v1` with zero wait. It does not take the producer's
   global lock. It retains cleanup uncertainty and distinguishes 51966 busy from
   other failures. Reuse this helper in tests; a .NET SQL imitation cannot qualify
   its actual pyodbc isolation or physical connection lifecycle.
2. `dbo.usp_RunMaintenance` acquires session guards in order: worker
   `K98:post-import-stats:v1`, global `k98-legacy-output-snapshot`, delta
   `K98:TargetPublication:DeltaPreprocessing`, player `K98:StatsForUpload:Publish`,
   then exclusive `K98:maintenance-schema:v1`. It reaches those downstream guards
   only for pending work. All six retained D5b rows are complete: a plain rerun
   would not qualify pending-work contention. Test demand must be separately
   authorized, precisely identified and distinguished from the consumed recovery.
3. `services/sql_lock_holder_diagnostics.py` supports the exact short global
   resource. It uses the existing requester connection, a one-second diagnostic
   cursor and SQL-version-specific metadata permission. Long hashed account
   resources truthfully return `resource_name_truncated`; they must not be
   attributed from a DMV prefix. A controlled fixture can know its own holder,
   but that is distinct from production diagnostic coverage.
4. `services/authority_observation.py` allows one active and one waiting
   observation; excess admission refuses. `inspect_configuration_recovery`
   remains serial because inspection can reconcile a stream. Execute/reconcile,
   context/sealing and proof publication are not passive selectors. Authentication
   in `scripts/run_export_authority.py` must precede observation admission.
5. Season routing reads a consistent metadata tuple before payload loading;
   mutation retains season locks, scope and current-version checks. Account
   coordination hashes exact resource keys. Global zero-wait admission, account
   waits up to 1,000 ms and the existing season-writer 10,000 ms wait are distinct
   contracts; do not replace them with a single observer timeout.
6. Existing native fixtures are **not reusable as runners** here. For example,
   `tests/test_recovery_snapshot_native_sql.py` creates a database on host K98DEV,
   grants a reader identity, seeds/deletes rows and toggles SNAPSHOT.
   Season/queue/configuration/unowned-hold fixtures inherit that setup and add
   permissions/objects. Their assertions are useful design inputs, not authority
   to run their setup against the retained VM or an unrelated host instance.

No production defect or runtime correction is newly established by these findings.
The gaps are qualification and fixture-readiness requirements. Keep services/DALs
and SQL as owners of orchestration, transactions and fencing. Proposed tooling
belongs in `scripts/`, tests in `tests/`, and private receipts under `p025`.
Do not move SQL into commands/views or add another lock/custody framework. Reuse
`recovery_snapshot`, `ObservationProgress`, `coordination_lock_name`, existing
SQL custody, `core/file_lock.py` and their caller tests. No new index, telemetry,
permission profile, automatic retry or deferred optimisation is justified here.

SQL validation is source-aligned for the reviewed guards and metadata contracts:
`ExportPreparation`, `ExportPreparationResource`, `ExportResource` and
`StatsImportExecution` retain exact membership/owner/fence/version relationships;
`MaintenanceWork` retains claim and due/claimed/completed generations;
`KVK.SeasonSource`, `SourceRouting`, `SourceCompleteSelection`, `SourceUpdate`
and `SourcePublication` retain source/season/period and version relationships.
Installed availability, permissions and suitable fixture tuples are readiness
gates, not inferred from these definitions. No schema installation is proposed.

## Case matrix and required evidence

For every overlap row, register separate reader-first and owner-first case IDs.
Missing overlap, a skipped prerequisite or an unavailable result is not a pass.
Keep actor, requester, logical owner, actual holder, resource, session birth,
connection identity, phase, monotonic times and original native error distinct.

| Family | Cases and assertions | Proposed execution and limits |
| --- | --- | --- |
| C01 global/account | Reader-first permits producer admission without owning its global/account guard. Owner-first full inspectors report active/busy where their contract probes live ownership; passive tuple reads may return the old committed tuple. Exact account key/hash and foreign account rejection required. | Actual Python helpers/DALs, two owned SQL sessions; acquisition-only producer control, no import/report execution. Include unreceipted, stats, player, configuration and all-KVK inspector variants. |
| C02 schema / Q06 | Managed reader-first excludes optional maintenance DDL; maintenance-first reader returns typed 51966 busy after clean rollback/close. Subsequent admitted reader sees coherent state. Historical raw-reader 3961 remains an unsupported-combination failure. | First prove exact lock protocol without DDL. Full actual-worker overlap needs the separately approved new demand below. Do not rerun the raw-history REBUILD failure or claim guard-only evidence proves actual-child overlap. |
| C03 delta/player/worker | A holder of each exact guard prevents optional work before child entry or claim completion; reverse order preserves the contender's existing refusal semantics. No stale completed generation or released-before-close assertion. | Fixed resource allowlist; two actor sessions plus at most one evidence/cleanup session. For worker calls, fresh approved pending demand is mandatory. |
| C04 season/weights | Choice, routing, complete selection, desired configuration and weights stay one coherent committed tuple in both orders; partial, foreign season/period, stale version and hash mismatches refuse. Payload reads occur after metadata scope closes. | Reuse season observation assertions. Real committed tuple transitions require explicitly owned synthetic rows; retained real rows cannot be used as mutation fixtures. |
| C05 queue/pool/configuration | Preparation/job/resources/pool/slots and configuration/execution receipts remain consistent across owner commit; denied/missing metadata is unavailable, not empty/success. | Queue, pool, configuration and unowned-hold DAL routes; exact synthetic IDs and full FK closure reviewed before use. No queue dispatch or provider effect. |
| C06 current action boundary | All 73 policy pairs retain per-kind authority/current-token checks; changed version/fence/owner, active physical worker and foreign scope cannot release or settle work from a preview. Cover Recheck, accepted-action reconciliation, group/batch, inherited adapters and outcome worker outside the count. | Offline inert-effect matrix for every pair/path, followed by representative native CAS cases only on approved synthetic rows. No retained recovery action is executed. |
| C07 holder evidence | Known global holder matches fixture session birth/connection, requester differs, refusal code/return remain primary; holder-disappeared, ambiguity, denied metadata and long resource names remain explicit. | One optional diagnostic per refusal, one-second timeout, no alternate login. Do not infer a historical production holder. Missing known-holder proof fails that case. |
| C08 authority saturation | Exact allowlisted reads only; one active/one waiting, third refused; serial mutation still progresses; authentication before admission; configuration inspection remains serial. | Offline controlled worker first; later unique local Windows pipe with inert dispatcher, exact SID/PID and no SQL/provider. Lost reply/death schedules remain D5d. |
| C09 factories/rights | Chosen factory called once; factory/permission failure preserves first error and no direct/legacy fallback. Wrong principal/account/storage owner refuses. Cleanup uncertainty is not ordinary busy. | Offline failures now proposed; native restricted identity only if an existing suitable principal and authenticated path are proven. No GRANT, CREATE USER or unapproved impersonation. |
| C10 isolation disabled | Startup/read admission refuses when SNAPSHOT is unavailable, with no locking fallback or automatic enablement. RCSI remains off. | Offline configuration/error injection is feasible. Native disabled-isolation proof cannot be obtained by toggling this copy under unchanged limits; retain historical evidence and an explicit native gap unless separately authorized. |
| C11 file/cache | Both writer arrival orders, path aliases and foreign sentinel rejection; readers release physical lock before decode. Ordinary/guided/startup, Ark team/state and tracked-view callers preserve primary result and exact object ownership. | Offline doubles first. Later native test-owned temporary directories only; no live cache, sentinel deletion or ACL change. Process death and uncertain-close recovery remain D5d. |
| C12 presentation/non-interference | Status/card/Refresh/report remain retained reads, never SQL/provider probe or recovery dispatch. Busy/missing evidence stays honestly stale/unavailable. | Offline spies across actual service/view handoff, no Discord client. Classify recovery controls by effect rather than their display label. Native SQL observations must leave protected data/claims and evidence unchanged. |

## Staged execution plan

### D5c.1 — bounded offline preparation, next proposed step

Prepare test-only cases and a static manifest for C01-C12. Do not edit runtime or
SQL definitions. Bind all 35 direct call sites to the family matrix and resolve
inherited/dynamic routes from the existing register. Enumerate exact pytest node
IDs, parameter cases and actual import graph before running; whole modules with
native fixtures or top-level side effects are excluded.

Use inert SQL/provider/Discord adapters and controlled events, not arbitrary
sleeps. Deny network, real SQL, provider imports, subprocess and native pipe/file
entry. Tests needing real Windows handles move to D5c.4. Permit only bounded
test-owned temporary files for ordinary fixture data. Use the existing pinned
venv without installation. One selected pass, five-minute ceiling and 1 MiB new
diagnostic output; stop dependent work on first failed safety assertion. Preserve
the failed trace before proposing a runtime correction. No retry to obtain green.

Primary existing assertion sources: `test_recovery_sql_snapshot`,
`test_legacy_snapshot_admission`, `test_authority_observation_dispatch`,
`test_season_observation`, `test_recovery_release_policy`, and the non-native
portions of file-lock/caller tests. Add explicit negative controls for wrong
resource/identity, fabricated holder, missing tuple member, denied factory and
each effectful selector. Do not run the historical native fixture setup.

Output: sealed case/node manifest, current-source digests, test result and first
failure record, plus a proposed native runner with exact SQL, statement counts,
allowed row IDs and cleanup. Review its Changes diff and actual PowerShell 5.1
remoting/serialization behavior offline before any manual console handoff.

### D5c.2 — later read-only readiness, separately authorized

Proposed target remains host `9SX2VF4`, VM
`2ac1b401-7076-4965-af71-de36ee0f9f9c`, guest `MINI_AMD`, SQL `lpc:localhost`,
copy `K98_P025_D5b_20261111` (recorded ID 8), Q: qualification volume.
The last reported session was `$global:D5bReportSession`, instance
`67caa9aa-5bb2-466c-991d-26ab8e1a2fc6`; that is historical, not current readiness.
Do not automatically recreate it or start the VM if unavailable.

Read exact VM/isolation/resource identity, source/candidate/ownership/permission
preimages, all six completed maintenance rows and backup-demand state. Check
existing Python/pyodbc/ODBC availability and executable location without import
of application startup, installation or environment activation. Prove a bounded
read-only factory can reach only this copy with pooling off before dependent
tests. If no suitable existing guest runtime exists, report the missing dependency;
do not substitute the host K98DEV server or silently qualify a different driver.

Inventory only required catalog/permission/tuple metadata. Select at most one
exact eligible tuple per family, with explicit absent/unusable outcomes. Reader
rights must already exist; no permission or ownership repair. Use bounded
aggregates/digests for large permission sets rather than raising row caps. This
step produces readiness evidence for review, never automatic workload dispatch.

### D5c.3 — later SQL overlap packet, separately authorized

Start with lock-only C01-C03/C07 cases on the retained copy. No installation,
second database/copy, input replay or setting change. A session taking a test
lock is an active native operation even though it performs no business write.

For native tuple and action-time cases, propose only fresh labelled synthetic
IDs/keys in existing tables, with a reviewed FK graph and a maximum of **64 new
fixture rows in total**. Pin every inserted key and original absence. Do not
alter retained application rows to create stale tokens. Commit only the exact
fixture transitions required to prove snapshot consistency; rollback-only
writers cannot prove observation across a committed change. Retain final fixture
rows as evidence; no broad DELETE/reset cleanup. If the dependency graph cannot
fit this ceiling, stop and return the exact missing prerequisites.

Actual-worker schema overlap requires one **new D5c post_import demand**, not a
retry of D5b. Before seeking that approval, prepare exact CAS from the adjudicated
D5b post_import preimage to the next generation, labelled request/claim identity,
and an immutable preimage/history receipt. Preserve first error 15247 and all five
other completed rows. Reader-first worker invocation must defer without child
entry; after release, admit at most one actual post_import child execution for
this new demand. No six-child repeat, report recomputation or backup dispatch.
If observed scheduling fails to establish actual overlap, record unexercised;
do not loop or infer it from timestamps. The precise worker-first barrier and
connection ownership must be demonstrable without modifying candidate procedures;
otherwise that actual-worker case remains blocked at packet review.

This new demand and committed synthetic rows are proposed scope additions beyond
the completed D5b work. They need explicit approval after their concrete packet
is reviewable. Permission-denial and SNAPSHOT-off native cases remain blocked if
the unchanged environment cannot support them. Passing offline substitutes does
not close those native rows. No permission/isolation exception is requested now.

### D5c.4 — later Windows contention and adjudication

Run only reviewed unique-pipe and test-directory cases for C08/C11, with real
physical handle closure and caller parity. No service start, production directory,
registry/task/ACL update or public endpoint. Preserve the original CI drain
failure; D5a's accepted mechanism/correction is prior evidence, not a reason to
repeat that run. Compare poststates, receipt bytes, grants, modules, ledgers and
known fixture effects; mark each case passed, failed, not run or unresolved.
Close D5c only after all required rows have valid evidence, with permission and
isolation coverage explicitly resolved. This plan alone cannot close those gaps.

## Hard ceilings and stop/cleanup rules

All original limits remain. The following are proposed stricter execution
allocations, not extensions or approval: D5c.2 up to 60 seconds; D5c.3 up to
360 seconds across separately bounded packets; D5c.4 up to 60 seconds. Thus at
most **480 of the remaining 1,480 native seconds**, leaving at least 1,000 if
all allocations were used. Debit actual elapsed time, including refusals and
cleanup, rounded up as in D5b. Do not reset the counter at a new packet. This
allocation does not prove that later D5d/e work fits; that feasibility remains
an explicit later gate. No packet may exceed the existing five-minute host cap.

- Keep VM at fixed 8 GiB/4 CPUs, zero network adapters, existing disk only.
  RCSI off; SNAPSHOT on for the managed native reader cases. No owner/grant,
  TRUSTWORTHY, chaining, backup schedule or production changes.
- Each relevant disk retains at least 8 GiB free; log below 70% for optional
  statistics and version store below 512 MiB. The 8 GiB host memory floor is
  **before startup**, not an additional post-start/guest-free-memory requirement.
- Three-second observation statements, zero row-lock wait; one-second optional
  holder diagnostic. Holds at most 30 seconds. Existing producer/metadata budgets
  remain unchanged; the harness cannot raise an application timeout.
- At most two concurrent SQL actors plus one evidence/closure observer. Each
  native packet is limited to 48 client commands across all connections,
  512 metadata rows per command, 2,048 overall and a 1 MiB receipt. Count both
  actors and cleanup; freeze the command ledger before execution. Split by case
  only during preparation, never to evade a failed cap or refresh a retry.
- Read-only preflight precedes each packet. Failed identity, changed source,
  exhausted budget, missing metadata, capacity failure or unconfirmed cleanup
  stops admission. No automatic retry, credential fallback, grant or setting fix.
- Every connection/transaction/lock has one owner and explicit reverse-order
  cleanup. Roll back owned transactions, acknowledge only owned releases, then
  prove physical session absence by birth/connection identity, not SPID alone.
  Preserve any cleanup uncertainty and first failure; never clear registries,
  reset work, kill unrelated sessions or delete a foreign sentinel to pass.
- Barrier cleanup releases only test-owned signals and joins entered workers.
  A watchdog cancellation/termination is failure, not successful drain. Unknown
  native effects remain unresolved; no subsequent dependent packet is admitted.

## Validation, review and decision

This deliverable changes documentation and generated source-review metadata only.
Security routing: documented skip for this delta because no runtime, SQL, access,
dependency, deployment or persistence behavior changes. The future Bot harness
needs a bounded Changes review with Deep off; any future SQL-repository executable
delta needs its own separate target. Existing D5b reviews do not cover new code.

Architecture/deferred/security-routing validators, test selection and link/hash/
whitespace checks apply to this packet. Runtime pytest, native fixtures, smoke
imports, command registration and broad pre-commit execution are skipped for the
source-only documentation delta. No application import is needed to enumerate
callers or the 73 actions. Conditional references are local SQL development,
Windows custody and security policy; release/deployment runbooks do not authorize
operations here. No new optimisation is deferred: the outstanding cases above
are required D5c acceptance, with D5d/e/f and P03/P04/D6/D7 ownership retained.

Recorded checks: architecture passed with zero applicable Python files;
deferred-item validation passed for both documents; security routing passed with
zero errors/warnings. The test selector completed. Its release-identity, export
schema, permission-repair and application-contract test recommendations are
skipped because this packet changes none of those executable contracts. Local
links, whitespace and the 52 source bindings are checked in the private
`d5c-plan-validation.json` receipt. These are document/source-custody checks,
not new concurrency test passes.

**Recommended next decision:** approve D5c.1 bounded offline test-only preparation.
Bring back its findings and the exact readiness/native packet before any native
work, fixture writes, new maintenance demand, permission change or runtime fix.
