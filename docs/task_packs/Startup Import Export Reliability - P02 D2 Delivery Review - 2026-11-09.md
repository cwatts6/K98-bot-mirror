# P02 D2 delivery review

This is the implementation overlay for the approved
[remaining-work handover](Startup%20Import%20Export%20Reliability%20-%20P02%20Remaining%20Work%20Handover%20-%202026-11-09.md).
The integrated plan, original action census and delivered Phase 1 evidence remain
authoritative within their stated limits. Production deployment and retained-work
recovery are separate. This review does not authorize another full-scale rehearsal.

D2a–l is complete and promoted: mirror PRs 499–510 and test-hygiene PR 511 are merged; private PR 738 merged on 10 November at `cd04ed5e494adf5bf40f607798b38abb8df1b836`. All private checks and exact-head reviews passed. Final private local tests: 12,951 passed, 1,184 skipped, one warning, eight subtests; Linux CI: 12,772 passed, 1,363 skipped, 19 warnings, eight subtests. Both local log-isolation checks passed. Consolidated Changes scan `783aa032-d4d3-4b19-898f-ca2bd037ebcf` found zero issues. No D2 deployment occurred.

The [D3 handover](archive/Startup%20Import%20Export%20Reliability%20-%20P02%20D3%20Handover%20and%20Scope%20-%202026-11-10.md) records D3 source completion, combined private PR authorization and the remaining D4/D5 obligations. Deployment remains held until after D5. D4 must resolve the refused direct combined updater jump before the final candidate is deployable. Earlier per-slice pending promotion/qualification statements below are historical checkpoints; preserve their evidence and limitations.

## Refreshed caller, resource and SQL matrix

| Family | Owning paths and resource | Current disposition |
| --- | --- | --- |
| Connection selection | `core/export_sql_connection.py`, `file_utils.get_conn_with_retries`, `proc_config_import._get_import_connection_with_retry` | D2a binds the selected callable before connection attempts. Existing retry caps, credential validation and explicit operational routing remain. |
| Import/profile adapters | `stats/profile_cache_repository._connect`, `prekvk_importer._conn`, `honor_importer._conn` | Profile and pre-KVK execution/import-error fallbacks removed together; honor already uses the central helper without fallback. |
| Direct factories | `kvk/dal/kvk_all_import_dal.py`, `services/stats_import_outcome_service.py`; `weekly_activity_importer._cxn` | Producer wrapper retains its public call contract. Weekly activity's explicit override/import-time selection is distinct from execution-failure fallback; no credential-policy expansion. |
| Profile result lifecycle | `stats/profile_cache_repository.read_profiles`; `dbo.v_PlayerProfile`, `dbo.v_PlayerScanMeta`, `dbo.v_PlayerKVK_Last3` | D2b requires explicit rollback/close acknowledgement and retains uncertain connection custody in the cache owner. Mapping and SQL definitions are unchanged; separate cursor/connection regressions and disposable-driver qualification cover this slice. Combined lifecycle qualification remains D2/D5. |
| Qualified passive recovery | `core/recovery_sql_snapshot.py`; all-KVK, historical import, stats import outcome and stats-report continuation inspections | Retain the deployed three-second explicit snapshot contract and cleanup acknowledgement. No repeated completed rehearsal. |
| Recovery inspection | `services/unowned_sql_hold_dal.py`, `services/config_preparation_recovery_dal.py`, `services/export_coordination_dal.py`, `services/export_recovery_dal.py`, `kvk/dal/source_output_pool_dal.py` | D2d–g separate proved read-only snapshots from mutation locks. Complete tuples, original account/resource/preparation scope and fresh mutation checks are retained. |
| Capture/mutation custody | `services/import_capture_recovery_dal.py`, `kvk/dal/new_source_import_dal.py`, `services/legacy_export_snapshot_dal.py`, `services/legacy_export_snapshot_service.py` | D2i/l retain global/session guards, first failure and uncertain cursor/connection ownership; commit uncertainty cannot replay. Borrowed no-op close is not physical release. |
| Ordinary season reads | `kvk/dal/source_routing_dal.resolve_season_read`; KVK source selection/routing/configuration metadata | D2h uses one consistent owned snapshot for season routing, source and weight checks. Immutable payload reads stay outside the metadata transaction; mutation admission stays locked. |
| Authority dispatch | `scripts/run_export_authority.py:serve`, `services/authority_observation.py` | D2j admits exact proved read-only selectors to one worker plus one waiter, retaining original peer/reply/handle custody and physical drain. Saturation is busy; mutations and configuration reconciliation remain serial. |
| Holder evidence | `services/legacy_snapshot_admission.py`, `services/export_contention.py`, `services/sql_lock_holder_diagnostics.py` | D2k adds bounded refusal-triggered global-lock holder evidence, with birth/connection identity separate from the requester. Permission denial, races and truncated coordination names are explicitly unavailable. |
| Player report budgets | `player_stats_cache._execute_sp_with_retries`, `services/player_report_continuation.py`; `dbo.SP_Stats_for_Upload` | D2l applies a real driver limit capped at 15s and the existing 1s row-lock policy. Native timeout evidence proves a 60s nested lock wait cannot evade the enclosing statement limit; separate cancellation evidence proves rollback without replay. Ordinary/guided connections close explicitly; no replay/fallback after commit or cleanup uncertainty. |
| Shared file ownership | `file_utils.acquire_lock`; player cache/startup, Ark team/state, `services/tracked_view_store.py` | D3 must separate acquisition from body exceptions and release only the created generation in `finally`. Include foreign replacements and cancellation. |
| Maintenance | Stats import, configuration, player report, KVK output, final reports, explicit post-import upkeep | D3 retains all six boundaries. Required shape/index/receipt work stays atomic; eligible optional upkeep requires durable separate ownership and restart semantics. |
| Legacy/manual SQL | `UPDATE_ALL`, Rally and TEST entry points | D4 requires read-only installed-binding/use inventory. Used paths require input custody and propagated child errors; retirement needs explicit approval. Never execute business procedures merely to discover use. |

A tracked-Python AST census found 70 direct calls to the three existing connection
entry points in 44 non-test/non-script files. This is an impact inventory, not a
claim that every call executes under a producer context. Shared helper behavior
applies to their existing routing without changing transaction ownership. Direct
factories, retry wrappers and observation selectors also require semantic review;
text matches alone are not the full resource census.

## Original finding disposition

| Findings | Delivery boundary and remaining evidence |
| --- | --- |
| F01/F26 | D2a–c/i/l deliver stable selection, failure propagation, explicit operation budgets and affected resource custody, including real driver timeout/cancellation. Business workload performance remains D5. |
| F03/F09 | D2d–i/k/l deliver scoped passive readers, retained global/account/resource guards, CFG-51421 observed holder identity and uncertain acknowledgement custody. Both arrival orders and foreign owners are qualified in disposable fixtures; retained incidents remain P03. |
| F12 | D2j delivers bounded authenticated observation admission, busy replies, lost replies/reconnect and shutdown/drain. No arbitrary selector concurrency or new provider capacity. |
| F14 | D2h delivers consistent season metadata, sealed relationships, stale/partial tuple refusal and explicit snapshot prerequisites. |
| F16/F18/F21/F22 | D3 all six maintenance stages, real child procedures, durable due/outcome state, failure after business commit and restart. Raw-history/index-REBUILD SQL 3961 remains a required boundary. |
| F20 | D3 shared lock ownership across ordinary, guided, startup, Ark and tracked-view callers. Body FileExistsError is a body failure, not acquisition contention. |
| F31 | D4 legacy/manual input custody, parent rollback, direct invocation and child-error propagation; release/source/SQL compatibility. |
| Combined qualification | D5 final package correctness, concurrency, cleanup, restart and resource cost against retained Phase 1 evidence. Focused unit tests cannot close this gate. |

P03 must settle actual retained blockers and essential P04 convergence before the
first standard production import/export test; neither an incident count nor P02
unit-test success authorizes that test. P01.6 decode optimisation and unrelated
MGE/Ark performance remain deferred under the existing programme decisions.

## D2a first implementation slice

Select the factory before the first connection attempt and retain it across all
bounded retries. Do not retry selection failures, change credentials after an
execution failure, replay statements, or use the runtime guard connection as a
work connection. Preserve the existing explicit operational route. Keep the
single-call `producer_connection` adapter compatible with its direct callers.

The two broad adapter fallbacks and both reselecting retry loops are one root-cause
family. No SQL definitions, schema, grants, command registrations or timeout
values change in this slice. The authoritative profile views and importer
contracts remain the same. The profile physical-close issue is explicitly owned
by the next D2 lifecycle slice rather than concealed by the factory correction.

Policy retained: dedicated login 5 s; default statement 15 s; metadata row lock
1 s; coordination horizon 15 s; producer admission zero wait; recovery snapshot
statement 3 s with zero row-lock wait. Existing explicit import/maintenance
overrides remain operation-specific. No global timeout increase.

Regression tests change runtime context after the first refused connection in both
directions, exhaust retry caps, preserve the original exception, retain operational
routing, fail closed on missing helper imports, and propagate cancellation without
another attempt. All connection factories are inert; these tests cannot establish
native SQL timing or physical cleanup. First-failure evidence is retained privately.

Changes security review is required for the exact Bot patch (credentials and
SQL-access routing). Deep scan is off. SQL security review is skipped for D2a
because there is no SQL-repository diff; later SQL slices require separate targets.

### Release compatibility included in D2a

The first full local suite exposed stale historical source assertions: four
failures and 270 setup errors, with 11,994 passes. Those results remain retained;
they are not an unrelated failure waiver. D2a now adds the exact
`p02_d2a_connection_selection_v1` seven-member source transition: the five changed
runtime files plus unchanged `constants.py` and runtime-context service. All 69
prior transition definitions and their predecessor/successor hashes remain
immutable. The installed registry still has its original byte bound; its entry
count admits precisely the one additional reviewed transition.

Historical tests authenticate current D2a bytes before checking prior-release
assertions. Exact current bytes must never masquerade as deployable historical
bytes. Negative controls cover every changed/unchanged member, omitted inventory,
foreign/partial registry entries, LF/CRLF representations and an old reader that
must refuse the successor. This is source compatibility preparation only: no
installed updater, startup policy, deployment, SQL contract or privileges change.
Any later deployment still requires the reviewed updater bootstrap and current
source/SQL/ownership checks. The original factory-only security scan completed;
the expanded final patch requires its own exact Changes review.

Qualification retains >=8 GiB free host memory/disk reserve, version store <512 MiB,
sampled log use <70%, and existing balanced cost limits where comparable work is
required (overall ON <= OFF x1.20 +1,000 ms; stage ON <= OFF x1.20 +250 ms).
Development SQL identity was checked after the crash; retained VM readiness is
unverified. Existing 21 inputs and earlier failures remain untouched.

## D2b profile SQL custody slice

D2a merged into mirror main as PR 499. D2b addresses the adjacent profile leak:
driver context exit could commit without closing the connection, and the cache
owner cleared its refresh slot despite uncertain cleanup. Scope is the profile
DAL, compatibility facade and existing cache service. No SQL definitions,
credentials, query text, timeout policy, TTL or command behavior change.

The DAL now requires its caller's explicit `SqlOutcome` and reuses the existing
`SqlSession` without changing the shared helper. It acknowledges rollback and
physical close separately, preserves statement exceptions, and retains the actual
handle if cleanup is interrupted. The facade supplies the outcome to the cache
owner. A failed or unconfirmed close prevents candidate publication and further
SQL refreshes, including force/fresh requests and requests after invalidation.
Last-known-good profiles remain readable. Passive health reports unknown cleanup;
public cache results never expose the retained handle or driver messages.

A confirmed close permits a later refresh after a statement or rollback failure.
Cursor-close failure cannot prevent an attempted connection close. Ordinary
observer cancellation drains the worker through physical cleanup before returning.
This process-local hold has no timer, automatic repair, retry or restart claim:
it retains an uncertain live handle for the owning process lifetime. D5 still
qualifies combined process shutdown/restart and retained-state boundaries.
If connection creation itself fails, the profile owner closes admission but cannot
retain a handle the factory never returned. Allocation/initialization cleanup inside
shared factories remains part of the existing D2 lifecycle work, not a claim that
this profile slice repairs every connection failure boundary.

The authoritative `dbo.v_PlayerProfile`, `dbo.v_PlayerScanMeta` and
`dbo.v_PlayerKVK_Last3` definitions were checked in the SQL repository. Existing
required/optional-view mapping and KVK-only rows are preserved. The only production
caller of `read_profiles` is the updated facade; tests now use distinct cursor and
connection objects so closing a cursor cannot falsely prove connection cleanup.

Regression coverage includes original-error identity, rollback/cursor/connection
cleanup failures, abrupt cleanup interruption, factory failure, cached availability,
invalidation, shutdown retention, fresh requests joining an entered worker, and
repeated async cancellation during physical close. The initial 11 failing tests
are retained privately. Focused owner/DAL/shared-helper coverage passed before the
expanded cancellation cases and final whole-suite run.

One native test uses the existing uniquely owned disposable local database fixture
with driver pooling disabled,
synthetic view projections and a SELECT-only database user. It verified real-driver
mapping, rollback acknowledgement, closed-handle refusal and retained ownership
after an injected physical-close failure. A separate observer saw that exact live
test connection identity disappear only after explicit close; a reusable session
number alone is not the final assertion. This does not establish production pool
behavior. The first two test assertions
incorrectly required no transaction after rollback; the driver's continued session
made that assumption invalid. Those failures remain retained, and the corrected
test verifies the actual physical-close contract. Fixture teardown passed without
forced eviction. No retained rehearsal input or production data was used.

Preflight recorded more than 8 GiB free host RAM/disk, zero version-store use and
tempdb log use below 70%; the new database also checked log use below 70%. This is
bounded driver qualification, not D5 whole-pipeline cost or production readiness.

Release compatibility adds the exact six-member
`p02_d2b_profile_sql_custody_v1` transition: three changed profile files plus unchanged
SQL-session, thread-drain and runtime-context dependencies. All 70 prior transition
entries and source hashes remain immutable. The registry count becomes 71 and its
byte bound increases by 2 KiB to 179,200 for the additional fixed package. Historical
tests authenticate the successor before checking unchanged release assertions.
Negative controls reject partial inventories, every changed/unchanged member's
drift, foreign entries and old readers. This does not install or deploy an updater.

Changes security review is required for the exact Bot patch, with Deep scan off.
SQL-repository review is skipped because there is no SQL-repository diff. The full
suite, architecture/deferred/security-routing checks, test selector, formatting,
smoke imports and command registration are the delivery gates. Final results and
the exact scan/PR identities are retained with the delivery receipt.

The exact executable patch passed Changes scan
`161b01be-8778-418f-a6b8-d6d523dbc648` with zero findings and complete coverage.
Subsequent changes only remove two test-fixture mutable-class defaults, bind the
native assertion to the unique connection ID, update the historical one-byte-over
registry-bound assertion to the new fixed limit, and clarify this delivery record.
Those deltas were inspected separately: fixed test-only metadata SQL remains
parameterized and opt-in; no production/runtime/tooling bytes changed. A new scan
is skipped for that test/document-only delta. Final fixture and native rechecks
passed; the full-suite result is recorded in the delivery receipt and PR.

Final full-suite evidence: 12,352 passed, 1,127 skipped, eight subtests passed,
one existing dependency warning, and one obsolete registry-bound test failed.
The test still used the old limit plus one byte; it now uses 179,201 bytes.
All 580 related boundary/transition tests passed after correction, and the exact
previously failing case passed again after the full run finished. Both rechecks
passed operational-log isolation. A second full run was not repeated for this
test-only constant correction: executable/runtime/tooling bytes were unchanged,
and all other full-suite cases passed. The original failure remains retained.

### Deployment checkpoint

The default deployment decision follows remaining D2 lifecycle work, D3 maintenance
and shared-lock work, D4 legacy/manual input custody, then D5 combined isolated
qualification. An earlier deployment requires a separately justified operational
benefit and complete source/SQL/updater, ownership/ACL, rollback and native evidence
for that smaller package. Mirror merges alone are not deployment readiness.

P02 fixes may deploy before P03 retained-work recovery. The first standard production
import/export test still waits for actual P03 blockers and essential P04 convergence;
it need not wait for every P05 item or a zero incident count. Promotion, deployment,
restart, recovery and provider actions remain separate concrete authorizations.

## D2c dedicated connection setup custody

D2b merged into the mirror as PR 500 after GitHub's exact-commit code review
completed without findings. D2c addresses F01/F26's setup boundary in
`core/export_sql_connection.connect`: after receiving a driver handle, timeout,
cursor, session-setting or autocommit setup could fail; cleanup could mask the first
failure or discard an unclosed handle. A concurrent setup could still hand out a
new connection after that uncertainty became known.

The existing dedicated factory now owns failed setup through physical close. It
reuses `SqlOutcome` and sanitized `error_facts`; the shared lifecycle helper stays
unchanged. Failed setups publish private custody before cursor/connection cleanup.
A short process-local lock protects admission and custody metadata only, never
driver I/O. Normal setups remain concurrent. New attempts and late handoffs are
refused while cleanup is pending or unconfirmed. Confirmed physical close removes
only that setup's hold; failed close retains the handle indefinitely in this
process. There is no timer, automatic repair, reset API or cleanup retry.

Every cleanup step still runs after ordinary or abrupt setup failure. The first
failure's sanitized facts remain distinct from cleanup failure, and cancellation
identity propagates after cleanup. Public exceptions retain the existing sanitized
configuration-error boundary. The new passive snapshot reports only admission,
pending and unconfirmed counts; it does not expose handles, targets or driver prose.
An underlying driver allocation exception that returns no handle retains its
existing sanitized contract: this slice cannot take custody of an unreturned
driver-internal allocation.

Affected direct callers are the application-profile authority connection factory
and SQL headroom preflight. Producer wrappers and both retry adapters continue to
use their existing selected factories. No credential fallback, broader retry,
global timeout increase, business SQL, command/view change or SQL-repository change
is introduced. The only setup statement remains `SET LOCK_TIMEOUT 1000`; no schema
object assumption or migration is added. Once a connection has been handed out,
its existing consumer still owns its operation and cleanup.

This hold owns a live process resource before any business work is admitted. It
does not replace durable workflow reservations or authorize restart/recovery.
Cross-process startup/drain and combined performance remain D5 gates. Legacy
factories, passive recovery previews, authority dispatch, holder attribution,
season-read consistency and remaining operation budgets retain their D2 owners.

Regression-first evidence records ten failures and five passes on the predecessor.
Coverage includes all five setup failure phases, failed physical close, first-error
preservation, cancellation, blocking cleanup, late concurrent handoff, two competing
uncertain owners, normal parallel setup, sanitized allocation failure and reopening
only after acknowledged close. The expanded factory/selection set passed 77 tests.

One native test uses only the existing explicitly opted-in unique disposable local
database, a SELECT-only user and pooling-disabled driver. It checks real setup
settings, successful handoff, failed-setup close, an injected refused close, exact
connection identity and explicit test-owned final cleanup. The test passed and its
database teardown completed without forced eviction. Host memory/disk and test
database log headroom were checked; the immediate post-test development SQL sample
recorded zero version-store use and log usage below 70%. No retained rehearsal,
production database or provider operation was used.

The exact `p02_d2c_sql_setup_custody_v1` transition includes the changed factory plus
five unchanged caller/helper dependencies. All 71 earlier entries and source hashes
remain immutable. The registry count becomes 72; the 179,200-byte bound is unchanged.
Current source is authenticated before historical assertions, with no production
admission bypass. This is source compatibility preparation, not updater installation.

The exact Bot patch requires a Changes security review with Deep off. No SQL diff
exists to scan. Focused release/source tests precede the full regression suite,
architecture/deferred/security-routing/test-selection checks, formatting, type,
smoke and registration validation. Final results belong in the delivery receipt
and PR. Production promotion and deployment remain separate.

### D2c delivery validation

The final combined connection/release set passed 226 tests. Architecture,
deferred-item, security-routing, test selection, formatting/lint, smoke imports
and command registration passed. A new release-test assertion initially asked
the per-path checker to reject an empty inventory; the outer release planner
owns that rejection. The test was corrected to exercise that boundary, the first
full run was stopped, and the final full run started after the correction.
Original evidence is retained privately; final full-suite results are recorded
in the delivery receipt and PR.

The final full suite passed: **12,403 passed, 1,128 skipped, 8 subtests passed**
in 20 minutes 9 seconds, with one existing Google/Python dependency warning.
Both the repository log-noise check and independent before/after snapshot
confirmed that production operational logs were unchanged. The native opt-in
test passed separately; its normal full-suite skip does not replace that evidence.

Changes security scan `e5d36f4c-8e9c-456f-b186-1d5e78c12672` completed with
zero findings and complete coverage against base
`2bd3fbfd2a41203ff2fa0c1122a8214c22e345b8`, working-tree digest
`aeac53b2ccddaf650321dfea5cf7b79df2c25c49edf5e68c9e953ab71682208f`.
Deep was off. The subsequent evidence-only documentation delta was inspected;
another scan is skipped because no executable, dependency, input, persistence
or release-authority behavior changed. The SQL repository remains unchanged.

Pyright reports three errors in the unchanged mixed integer/string settings
dictionary. All three reproduce on the exact base source; no new errors arise
in the changed setup logic. Dependency-resolution warnings also remain.
Current and baseline type-check output are retained privately.

### Deferred Optimisation
- Area: `core/export_sql_connection.py::settings`
- Type: consistency
- Description: Existing mixed settings dictionary inference causes three Pyright errors, reproduced on the exact base.
- Suggested Fix: Add precise settings typing in a separate configuration-focused change, preserving validation and secret handling.
- Impact: low
- Risk: low
- Dependencies: Existing configuration tests and an exact updater successor if executable bytes change.

## D2d unowned SQL-blocker observations

D2c merged as mirror PR 501 at `4dc966926947702e0da6e927275c1bc5f03a0a58`.
Its exact-head Codex review was clean. Copilot's cancellation comment was a false
positive: Python 3.11.9 reports `asyncio.CancelledError` as a direct `BaseException`
subclass, and both existing cancellation identity/cleanup cases passed again.
The evidence was recorded on the PR and the thread resolved without a code change.

D2d is limited to `UnownedSqlHoldDAL` discovery, preview and saved-action reads.
These now reuse the deployed `recovery_snapshot` contract: a dedicated consistent
snapshot, three-second statement limit, zero row-lock wait, rollback and physical
close acknowledgement. There is no locking-read fallback, retry loop or commit on
these observation paths. Missing snapshot support, permission failure and unknown
cleanup propagate through the established helper. Its implementation is unchanged.

The shared row mapping and queries retain the same scope, foreign/detached producer
checks, global active-stream count, 101-row producer bound and receipt validation.
Only the passive call opts out of account/resource mutexes and update/hold hints.
`clear` retains the default locked snapshot, all physical worker guards, exact
evidence digest, owner/fence/version predicates and atomic audit/flag update. A
preview is never physical-termination evidence or permission to clear a blocker.
No command, recovery service, restart state, SQL repository, schema, grant,
credential or production timeout policy changes. No provider or retained work runs.

The six source table definitions and `ACQUIRE_KS4_IMPORT_LOCK` were checked against
the authoritative SQL repository. The new native fixture creates only a unique
disposable database, uses source columns/checks and a SELECT-only preview user,
and omits external foreign keys/unrelated ownership objects. Nine checks passed:
both reader/writer arrival orders, a consistent tuple across a real commit,
detached foreign owners, stale-token refusal, a fresh exact receipt, active
physical guards and permission failure with closed connection. Non-forced teardown
passed. This is bounded metadata/confirmation evidence, not D5 cost or production
permission qualification. Host free memory exceeded 8 GiB, disk reserve exceeded
8 GiB and the test database log-use check was below 70%.

The older unowned-hold tests intentionally borrow one session containing temporary
tables. Their fixture uses its existing transaction helper for reads and continues
to test query/CAS/containment/receipt behavior; it cannot prove dedicated-session
snapshot isolation or physical cleanup. The new native tests own that evidence.
Four predecessor regressions failed before the implementation; final focused
connection, observation and release checks passed 297 tests.

The exact seven-member `p02_d2d_unowned_hold_observation_v1` transition includes
the changed DAL and six unchanged lifecycle/diagnostic/mutation/service dependencies.
All 72 previous entries remain immutable; registry count becomes 73. Its byte bound
increases by 4 KiB to 183,296 for this fixed package. Historical assertions first
authenticate the current successor. No updater installation is performed.

The Bot patch requires a Changes security review with Deep off, against the D2c
merge above. There is no SQL-repository diff to scan. Final full-regression,
log-isolation, review and validation receipts belong in the PR and private delivery
record. Configuration/queue previews, capture custody, authority dispatch, holder
evidence, season tuples and budgets remain with their existing D2 owners; D3-D5
and the deployment checkpoint are unchanged.

Changes review `28f1853f-2f51-436a-85e6-c64f9e5c6442` completed with zero
findings and complete coverage at working-tree digest
`a07adaed75d64fc57d996db64cf9e9fe51e2c1985420140922768b60c6e02940`.
Subsequent evidence documentation and three test-only registry-limit constants
are separately inspected and skipped for another scan: no application runtime,
tooling, dependency, persistence or release-authority delta.
Architecture, deferred-item, security-routing, lint, smoke and registration checks
passed. The DAL's 17 Pyright diagnostics reproduce on the exact predecessor with
the same diagnostic messages; they are not introduced by this patch.

### Deferred Optimisation
- Area: `services/unowned_sql_hold_dal.py`, existing `one`/`_wire` result typing
- Type: consistency
- Description: Seventeen pre-existing Pyright diagnostics arise from optional/heterogeneous row-mapping types; exact-base comparison reproduces the same messages.
- Suggested Fix: Define precise row/result types in a separate DAL typing change while retaining query, validation and receipt semantics.
- Impact: low
- Risk: low
- Dependencies: Row-mapping and receipt regressions; exact updater successor for executable changes.

The full run recorded 12,444 passes, 1,137 skips, eight passing subtests and one
existing Google/Python dependency warning. Three old release-size assertions
still padded to 179,200 bytes rather than the new 183,296-byte limit. Those test
constants were corrected; no application or tooling bytes changed. The original
failure output is retained, and final related-suite results are in the delivery
receipt and PR. Independent before/after checks confirmed unchanged operational
logs even though pytest reported those failures. A second full run is unnecessary
for these test-only constants after all three failed cases and their related
release-boundary suite pass; other full-suite cases already passed.

The final related recheck passed **2,043 tests**, including all three corrected
cases, with operational-log isolation passing. No runtime/tooling change was
needed after the full run or sealed security review.
## D2e configuration recovery observations

D2d mirror PR 502 merged as `55919d93a1b6901941f122cbdbe15598659e2430`
after exact-head Codex review completed with no findings. Copilot reported a
plan/model restriction, not a completed independent review; no inline issues
were submitted. Production qualification remains a later gate.

The operator authorized continuing all remaining D2 slices without another
per-slice approval. Keep focused mirror PRs, their reviews and validation; provide
a full D2 summary when the remaining matrix is closed. Deployment is separate.

D2e separates `ConfigPreparationRecoveryDAL.identity`, `pending_recovery`,
`target_data` and `snapshot` into the unchanged dedicated `recovery_snapshot`
contract: three-second statements, zero row-lock wait, explicit snapshot
isolation, rollback/physical-close acknowledgement, no commit or retry fallback.
The default `_snapshot` still takes account/resource mutexes and UPDLOCK/HOLDLOCK;
`settle` retains that default, complete fresh-state equality, owner/fence/version
CAS and atomic containment. The complete result still includes unexpected owned
resources, immutable membership, related/active foreign streams and request/event
counts. Queries and shapes were checked against the six authoritative SQL tables;
there is no SQL schema, permission, source-selection or credential change.

`config_recovery_authority._inspect` can recover owned/abandoned closures. It is
not made passive or concurrent: each new DAL observation closes before that
existing mutation or the next observation begins. The service, authority and
snapshot helper remain unchanged. No command/view changes or new helper are
needed. Existing SQL-authoritative persistence and restart predicates remain.

Regression evidence: five new tests failed against the predecessor, four passed.
After implementation, 80 focused recovery/helper checks and nine native checks
passed. The native tests use a new uniquely owned local disposable database,
source columns/checks and SELECT-only preview principal, with external FKs omitted.
They prove both arrival orders, complete old/new tuples across a writer commit,
foreign-stream/unexpected-resource/provider-ledger conflict retention, stale-state
settlement refusal, fresh settlement fence/membership preservation, account-scope
refusal and physical closure after permission denial. Teardown does not force
eviction. The older single-session temporary-table fixture remains query/CAS
proof only and explicitly uses its borrowed transaction wrapper.

Release transition `p02_d2e_config_observation_v1` authenticates six exact members
(one runtime DAL changes). Prior 73 entries remain immutable; canonical hash
`a7f129167373c974554b14066a456e55bebe546458803abaa98a066b7665f378`.
Registry count is 74 and bounded bytes 187392. Historical tests authenticate the
successor before projecting earlier identities; no historical entry is rewritten.

Security routing: exact Bot Changes review against merged D2d, Deep off, required
for DAL and updater behavior. SQL review is separately skipped because its tree
is unchanged. Broad transition/configuration/cleanup regression and deterministic
gates are required before PR. Run the full suite at the combined D2 checkpoint;
for this isolated DAL slice, unchanged shared helper/service/command behavior is
covered by focused and broad related regressions plus native SQL. This avoids
repeating the full suite solely for registry-count constants, while retaining
D2d's full-suite result and its corrected-assertion rerun as prior evidence.
### D2e inherited row-mapping typing debt

### Deferred Optimisation
- Area: `services/config_preparation_recovery_dal.py`
- Type: consistency
- Description: Ten existing row-mapping type diagnostics reproduce with the same messages on the exact D2d base; the observation change does not introduce them.
- Suggested Fix: Introduce precise row/result shapes in a separately scoped typing cleanup while preserving wire output and receipt equality.
- Impact: low
- Risk: medium
- Dependencies: Existing recovery/containment contract and native regression evidence.

D2e Changes scan `73266969-dd1f-4f52-9f1f-1d9274e398cc` completed with zero
findings and all three executable inventory items reviewed. Digest:
`f532da2bfb01272ff8bc6762776ad00108ca6f2e69e191e9c09ed8db90e26bb8`.
Post-scan changes are evidence documentation and test-only lint/assertion cleanup;
application/tooling bytes remain unchanged. Architecture, deferred, routing,
Ruff, import smoke and command registration passed. An additional 111 release
identity/schema regressions passed. Full-suite-at-D2-close decision remains above.
D2e broad related run: 2153 passed, 55 opt-in SQL skips, one existing dependency
warning and one historical recovery-transition assertion failure. The assertion
now uses the authenticated D2e predecessor bridge; prior registry entries stay
unchanged. This is a test-only post-scan correction, inspected separately; no
runtime or updater behavior changed. The final affected checks and log-isolation
result are recorded in the private validation receipt and PR. Ten inherited
Pyright diagnostics match the exact base. Native final rerun: nine passed.
## D2f queue discovery and operator observations

D2e PR 503 merged as `19367f9076042e86722078cdfac19c3abd8dd244` after exact-head
Codex review completed without findings or inline issues. D2f builds on that merge.

Scope: `ExportCoordinationDAL.pending_intents`, `accounts`, `pending_source_jobs`,
`repair_receipt` and `operator_snapshot` use the existing owned recovery snapshot.
The nested operator tuple includes job, resources, attempt/part receipts, unique
pool, slots, related jobs, legacy receipts and retirement evidence. Nested
`read_coordinated_receipts` and `SourceOutputPoolDAL._snapshot` were traced and
remain unchanged: their hash, membership and registration checks are read-only.
Only `_job` gains a fixed passive lock choice, defaulting to original locks;
`_operator_snapshot` forwards it only from the public owned preview context.
Reconcile/admit/claim paths retain account/resource locks and fresh-state checks.
No service/command, schema, permission, retry or credential changes are included.

The SQL source definitions for ExportJob, ExportJobResource, ExportResource,
ExportAttempt/Part, SourceOutputPool/Slot/Disposition, SourceDelivery,
SourceOutputOperation and SourceExportIntent were inspected. The native fixture
uses their columns/checks with external FKs omitted in a new uniquely owned
local database. SELECT-only previews pass while a writer holds the job and intent;
an observer-first writer commit leaves the complete old job/resource/pool/slot
tuple visible, then a new observation sees the new tuple. A stale reconciliation
is refused. Corrupt manifest hash, missing parts and corrupt registration remain
refused; permission failure physically closes the reader. Six native tests passed.

Seven meaningful predecessor regressions failed, two passed after correcting the
initial fixture's missing preparation-contract flag. After implementation and an
older scripted query-fixture context correction, 128 focused queue/release tests
passed. The first broader subsystem run had 242 passes and that one old scripted
fixture failure. The fixture is explicitly query-only; borrowed temporary SQL
containment tests likewise retain their transaction wrapper, while the dedicated
native fixture proves isolation and cleanup. Full suite remains due at D2 closure.

Release family `p02_d2f_queue_observation_v1` has six exact members and one changed
runtime file. Prior 74 entries are immutable, canonical hash
`e9182e4391687572ee4db3166e204e0a84297986c833c35203ff50eccb468595`.
Count 75; byte bound 191488. Authenticated historical bridges retain prior pins.
Security routing is exact Bot Changes review against merged D2e; Deep off. SQL
review is skipped only because its repository is unchanged. No production action.

The discovery weight gate still calls locked season helpers and stays with F14's
complete season/config tuple work. ExportRecoveryDAL and standalone pool/recovery
previews remain in the D2 reader census, not silently closed by this queue slice.
Capture/session cleanup, authority admission, holder evidence and budgets remain
separate D2 owners. No snapshot result authorizes provider effects or release.
### D2f inherited coordination typing debt

### Deferred Optimisation
- Area: `services/export_coordination_dal.py`
- Type: consistency
- Description: Fifty-one existing row/result type diagnostics match the exact D2e base; no new type diagnostic is introduced by passive observations.
- Suggested Fix: Give coordination rows and result tuples explicit types without changing wire identities, receipt bytes or mutation predicates.
- Impact: low
- Risk: medium
- Dependencies: Coordination and receipt regressions plus authoritative SQL shapes.

D2f exact Changes scan `08210d7b-e513-4241-b4a2-5b87f6a86fdf` completed with
zero findings and complete three-source-item coverage; Deep off. Digest
`4bab1f1cfdd4ddd39de8f46358f0dcf1b0e1c4d094605b6360b79db79b14b5e9`.
Architecture, deferred/routing, import smoke and command registration passed.
Full suite remains scheduled for combined D2; broad affected regressions are the
slice gate. Production permissions, installed source and D5 are not claimed.

D2f broad run: 2215 passed, one failed and 126 setup errors. All failures were
historical release assertions for the changed coordination DAL. The tests now
authenticate the actual D2f successor before projecting immutable D2d/Phase 1
postimages; no historical release pin changed. All 215 affected rechecks passed,
with production operational logs unchanged. These test-only corrections were
inspected after the completed Changes scan; executable scan inventory is unchanged.

## D2g recovery listings and standalone pool observations

Scope reviewed before implementation: ExportRecoveryDAL's five SQL entry points
and SourceOutputPoolDAL's standalone reads use the existing owned snapshot helper.
Recovery pagination and repair membership checks share the same cursor as their
parent observation. Drain previews read operation and pool in one transaction.
This removes nested connections and inconsistent multi-transaction tuples without
changing wire fields or registration/account/storage/resource membership checks.
Pool retirement, claim, ready, reconciliation and admission retain their owned
locks, durable receipts and fresh-state comparisons. Registered publication and
rollover wrappers retain their protected-registration checks; neither grants write
authority. No schema, permission, provider, retry or command changes are intended.

The source-defined job/attempt/resource/containment/closeout/replacement/stream,
season, pool/slot/disposition/delivery/intent/operation and operation-resource
tables are the SQL contract. Tests must cover owned context cleanup, both writer
arrival orders, complete old/new tuples, corruption and foreign registration
refusal, plus related recovery/pool/release regressions. Borrowed temporary-table
fixtures remain explicitly query-only. Changes review is required for the Bot
patch, Deep off; SQL review is skipped only while that repository is unchanged.
F14 season routing and the discovery weight gate remain the next coherent slice.

D2g validation: 16 new predecessor regressions failed and one passed; all 17 pass
after implementation. Nine native checks passed using a new disposable database:
all 16 public read routes are nonblocking behind an uncommitted writer, recovery
and operation/pool tuples stay consistent across commit, foreign account/membership
and corrupted plan/registration hashes are refused, permission failures close the
reader, and a stale pool preview cannot close admission or create an operation.
No historical evidence database or retained input was used.

The seven-member release successor authenticates two runtime changes and retains
all 75 earlier entries, canonical hash
`c04e0177ab4beb5e34f7611f05b1a3cbcb559c5a381516c4b688246698af60d6`.
Registry count 76, byte bound 195584. A generator encoding error ran no tests;
the corrected release tests exposed an overly specific one-file error assertion,
now corrected for this two-file package. Historical pins remain immutable.

Exact Changes scan `7025a344-b0cf-44c7-a896-05a82543b956` completed with zero
findings and all four executable inventory items reviewed; Deep off. Digest:
`49917c93c0d8a57cc9c92a3ebecb2dd72d9972bd370188248e8bc9ac9d5aba59`.
Supporting native/borrowed-fixture assertions were reviewed before completion.
Architecture, deferred and routing checks passed. Full-suite execution remains
reserved for combined D2, with broad affected regressions required for this slice.

D2g broad results: 3022 passed, 464 opt-in skips, one dependency warning and the
already-corrected partial-package error-message assertion (the running process
had loaded its predecessor). The separate subsystem run passed 330 checks;
final affected recheck passed 53. Both broad and final log-isolation checks passed.
Import smoke, command registration and lint passed. Exact-path base comparison
reproduced all 210 Pyright diagnostics with identical messages; no new diagnostics.

### D2g inherited row-shape typing debt

### Deferred Optimisation
- Area: `services/export_recovery_dal.py`, `kvk/dal/source_output_pool_dal.py`
- Type: consistency
- Description: The 210 row/result typing diagnostics reproduce with identical messages on the exact D2f source at its original paths. A copied-file baseline had a different import graph and was superseded by this exact-path comparison.
- Suggested Fix: Give recovery and pool row/wire shapes precise types in a separate focused cleanup while retaining the current serialization and receipt checks.
- Impact: low
- Risk: medium
- Dependencies: Recovery, pool ownership and native tuple/cleanup regression coverage.

## D2h consistent season metadata

Scope reviewed before coding: resolve_season_read, SeasonSourceDAL.read and the
export discovery weight gate use owned snapshots. A small read_season helper
shares the existing mapped row contract; require_source keeps its locked default
and permits passive reads only when explicitly requested inside the new owned
gate. Writer lock_scope/lock_season and lifecycle CAS stay unchanged. The resolver
retains every complete-selection/update/publication/hash/config relationship check,
previous-complete behavior and failure-to-unavailable behavior. Its discarded
component-pointer lock query can be removed; it conveys no publication authority.
Heavy immutable facts remain outside metadata transactions.

SQL definitions inspected: SeasonSource, SourceRouting, SourceCompleteSelection,
SourceUpdate, SourcePublication, SourceConfigVersion/Request, intent-publication,
SourceWeightConfig and the imported configuration tables/read helper. Imported
configuration verification performs only parameterized reads and validates the
retained payload hash and legacy/source weight relationship. No SQL schema or
permission change. Scope includes unit/native consistency, corruption, refusal,
close and writer-default tests, existing public report/lifecycle/weight tests,
exact release admission and Bot Changes review with Deep off.

D2g merged as mirror PR 505 at `24b09ddada48d5ed2b1a7c575aa63998c56ba26d`
after exact-head review completed without findings. D2h's four predecessor
regressions failed, one passed; 55 focused public-routing/lifecycle checks then
passed. Five additional season-input cases preserve the old positive-integer
boundary. The nine-member release/precedessor checks passed 122 cases.

Native D2h: ten passed. Both arrival orders preserve the choice/routing/complete
selection tuple; an observer-first weight change cannot mix current configuration
with its earlier season read. A fresh observation correctly refuses stale weights.
Partial/cross-choice/config/hash mismatches, permission denial and snapshot-off
remain unavailable without legacy/locking fallback, and all readers physically
close. An initial synthetic fixture omitted required PeriodKind; supplying the
source-defined field corrected setup before the meaningful run. These tests use
only new disposable databases, source checks and SELECT-only reader permissions.

Release `p02_d2h_season_observation_v1` preserves 76 prior entries, canonical hash
`bedacf8c4bb61e186e5af770fe5b5e799f694ec9e8eb6c08ca7d58c5d795969d`.
Count 77; byte bound 199680. Security Changes scan
`d8451ddd-ea8f-4baa-8a28-4045f5d9f84b` completed with no findings, all five
executable inventory items reviewed, Deep off. Digest:
`0993bffee9ddec1ba16e67e4777c7061390db1abcff28c52290294cde63c0305`.
Architecture, deferred/routing, lint, imports and command registration passed.
Combined full suite remains due at D2 closure; no production readiness claimed.

### D2h inherited metadata typing debt

### Deferred Optimisation
- Area: `kvk/dal/season_source_dal.py`, `kvk/dal/source_routing_dal.py`, `services/export_coordination_dal.py`
- Type: consistency
- Description: All 63 current row/result type diagnostics reproduce with identical messages on the exact previous source at its original paths.
- Suggested Fix: Add precise metadata/result types separately without changing source choice, sealed tuple validation or writer ownership predicates.
- Impact: low
- Risk: medium
- Dependencies: Public routing, lifecycle, weight and native consistency regressions.

D2h broad regression: 3467 passed, 79 opt-in skips, one dependency warning and
two old mocked discovery assertions that omitted the new explicit passive flag.
Their expectations now require that flag; all 141 affected rechecks passed.
Broad and final operational-log isolation passed. The post-scan change is one
test assertion plus evidence documentation; runtime and updater bytes are unchanged.

## D2i SQL cleanup and retained physical custody — scoped before coding

The source transaction helper currently lets rollback/close errors replace the
first failure; capture session release can skip later guards and cursor cleanup;
capture adopt/conclude and producer verification can likewise mask their first
failure. Existing recovery snapshots acknowledge failures but do not retain an
unclosed connection. These are one lifecycle boundary, including the contention
retry wrapper and all capture descendants (stats, all-KVK, player/config reports).

Reuse the existing SqlOutcome/error-facts shape in a core custody owner. Retain
unacknowledged physical connections strongly and expose only safe process-local
counts/outcomes. Once close fails, refuse new source/capture/observation admission
instead of dropping the handle or replaying work. Already-running owners retain
their original completion duty. No automatic retry/force-close/release/repair is
added; process-local custody is not a durable SQL resolution or health proof.

Source transactions must attempt rollback on pre-commit failure, always attempt
close, preserve the first cause and separate unknown commit from cleanup. Busy or
retry eligibility requires acknowledged rollback and close; borrowed transactions
cannot assert physical release. Closing an owning connection closes its cursors;
do not close the cursor borrowed from an outer admin transaction. Capture sessions
retain the original global/session guard order; attempt every release even after
lost grant acknowledgement, then cursor and connection cleanup. Short capture
transactions preserve commit uncertainty and all existing durable CAS predicates.

Check factory/setup, body, rollback, release, cursor-close, connection-close,
commit acknowledgement and cancellation independently, plus actual timeout and
guard release in uniquely owned disposable SQL. Review existing callers and
capture descendants; run broad lifecycle/recovery regressions and full suite at
combined D2. No SQL schema, grants, business procedure or provider execution.
Bot Changes review required, Deep off; the unchanged SQL repo requires no diff scan.

D2h merged as mirror PR 506 at `b307fcc72ff554d0dd67b568236ddd7ecb59cb3d`
after exact-head review completed without findings. D2i now retains the first
body/setup/commit failure through every attempted cleanup. Borrowed admin adapters
cannot claim physical release, and retry/ordinary-busy classification requires
acknowledged owned cleanup. Capture checks every intended guard after a lost grant
reply and retains uncertainty even after driver close when explicit release was
not acknowledged (pooling can retain a session). No automatic cleanup retry or
admission-reset API is introduced.

D2i focused/release gate: 132 passed. Native: five new driver/lifecycle checks
passed, plus 36 existing capture checks across stats, all-KVK and player-report
families. The cancellation check observes the exact owned query in a server wait
before cancelling and requires HY008; a timeout cannot satisfy it. Lost grant,
release and close acknowledgements use uniquely owned local guards and verify
explicit release from a second connection. No retained database/input or business
procedure is used. Eight old contention assertions were corrected to expect the
new cleanup-uncertain wrapper and its original cause; 103 focused checks passed.

Release `p02_d2i_sql_lifecycle_v1` has eleven exact members, seven changed (one new
custody module), and preserves all 77 prior entries, canonical hash
`d0d4240d8f57c2c5ea3983b930418797166df5854344043702e6fd1e12501857`.
Registry count 78; byte bound 207872. Architecture, deferred/routing checks, import
smoke and command registration passed. Security Changes scan
`a031af81-4183-4748-aa34-d364a3bf707b` completed with no findings and all nine
executable inventory items reviewed; Deep off. Exact patch digest:
`829ef4f6eb4ccf557d3e997a7317bedb693d4d2aaa03a75cda10dbbe66d2173c`.
Broad lifecycle regression: 4336 passed, 467 opt-in skips, one dependency warning;
operational-log isolation passed. Exact-path type comparison reproduces all 24
diagnostics with identical messages. Full suite remains due at the combined D2
checkpoint; native fixture evidence is not production qualification.

### D2i inherited source-row typing debt

### Deferred Optimisation
- Area: `kvk/dal/new_source_import_dal.py`, `kvk/dal/new_source_admin_dal.py`, `services/export_contention.py`, `services/import_capture_recovery_dal.py`
- Type: consistency
- Description: All 24 current row/result typing diagnostics reproduce on the exact prior source at its original paths; lifecycle ownership introduces no new diagnostic.
- Suggested Fix: Add precise source row and timing/result types separately while preserving receipt and retry predicates.
- Impact: low
- Risk: medium
- Dependencies: Source import/admin, capture and contention regression coverage with authoritative SQL shapes.

## D2j bounded authority observation dispatch — scoped before coding

The authenticated accept loop currently waits for each observation's SQL/private
I/O. Exact read-only selectors may move to one owned observation worker with one
waiting request. Excess observations return the existing busy wire response.
Mutations, configuration inspection (which may close/reconcile), context sealing,
proof/provider actions and unknown selectors retain the authoritative dispatcher.
The worker must independently validate its allowlist; the original broker still
validates deployment, exact fields, protected registration and scoped identifiers.

Read-only failed-export, replacement/rollover, target and evidence inspections
currently take the same in-process authority lock as mutations. Remove that lock
only inside the independently admitted read-only context, including authenticated
registration reconstruction; preserve it for every mutation and ordinary caller.
All reconstructed registrations and service instances remain local to the request;
previews grant no authority and mutations repeat current ownership/receipt checks.
SQL metadata reads keep their existing owned transaction/snapshot contracts; no
query budget, SQL schema, provider capacity or persistent scheduler is added.

Each admitted request owns its original peer, pipe and (for shared identity) a
separate pinned Bot handle until reply I/O and cleanup finish. A lost reply cannot
replay dispatch or move a response onto a reconnected request. Shutdown closes
admission, cancels queued observations without dispatch, and drains the active
owner. Unconfirmed SQL or transport cleanup retains custody and prevents a clean
authority-session close; elapsed deadlines do not prove physical completion.

Validation covers slow active work, one queued request, saturation, serial mutation
progress, exact-selector refusal, original authentication/reply ownership, lost
reply/reconnect, cancellation and shutdown/cleanup failures. Existing broker,
registration/evidence, native Windows pipe and release checks remain relevant.
Bot Changes review required, Deep off; SQL source repository remains unchanged.

D2i merged as mirror PR 507 at `5e2f539f013e40860ed28a3c13aaf5464e9cfc17`
after exact-head review completed without findings. D2j's 13 initial worker
regressions fail on that predecessor. The implemented worker and broker/transport
checks pass 251 cases (one opt-in skip); shared-identity/shutdown rechecks pass 237.

Native Windows qualification exposed two adjacent transport defects: a single
pipe instance cannot accept work while its old reply remains owned, and legacy
token impersonation was attempted before any message was read. The authority now
keeps one reserved successor listener, authenticates a bounded received frame
before admission on that token path, and retains pre-read process authentication
plus post-read incarnation verification on the shared-account path. The fixed
four-instance maximum covers active observation, one waiter, current request and
reserved listener; only the first instance uses first-instance creation. Every
successor is created while an owned instance still protects the namespace. Normal
single-instance provider/other pipe callers retain their defaults.

A lost native reply also exposed a wait on an OVERLAPPED event for a WriteFile
operation that Windows had synchronously refused. Such errors now preserve their
original failure without waiting for unissued I/O. Actual pending operations still
cancel and obtain their terminal result. Unconfirmed completion retains the exact
operation, event, buffer closure and pipe strongly; cleanup cannot free them or
close the authority session. This follows Microsoft's
[asynchronous I/O lifetime contract](https://learn.microsoft.com/en-us/windows/win32/fileio/synchronous-and-asynchronous-i-o)
and [completion/cancellation contract](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-getoverlappedresult).

Both real-pipe tests now pass, including saturation, independently progressing
serial mutation, original replies, a disconnected original peer and fresh
reconnection. They use unique local pipe names, current-user/exact-PID fixture
authentication and inert requests; they do not claim production token provisioning
or execute SQL/provider work. Failed fixtures were diagnosed with timed stacks;
only their verified test processes were stopped. Fixture shutdown now retains the
original failure and exits its owned server reliably.

Final worker review also reproduced interruption both before and after thread
creation. The worker is now retained before start; interrupted acknowledgement
closes admission and wakes any started worker, without transferring the request.
An unacknowledged launch cannot be reported as a clean drain.

Broad D2j regression: 3661 passed, 305 opt-in skips, one dependency warning, with
21 setup errors from D2c's obsolete literal authority postimage. That fixture now
authenticates the complete successor chain before using its inert historical
image; all 128 final worker, historical/new release and reader-capability checks
pass. Operational-log isolation passed. Architecture, deferred-item, routing,
selection, lint, imports and command-registration gates passed. Exact-path type
comparison retains the same 21 errors and 32 warnings, with no new diagnostics.

The 13-member, seven-change `p02_d2j_observation_dispatch_v1` package preserves all
78 predecessor entries. Registry count is 79 and its bounded size is 216064 bytes.
The first Changes review found no security issue; the subsequent lifecycle fix
was separately reviewed in final Changes scan
`d0f1ad35-c6b1-4f27-bc83-38040a9ca59a`, complete with zero findings, snapshot
`03f22f49cae70a1742cdb56cf8021cee0f4031d68f85f4f2ba26025362fdaef7`.
No production release, restart, provider execution or retained recovery occurred.

## D2k refusal-triggered holder evidence — scoped before coding

Add a bounded read-only diagnostic to the two exactly attributed admission
refusals. The global legacy snapshot resource has a fully visible name; observe
only granted holders in the current database and public-principal namespace,
retaining requester identity separately from holder session birth and physical
connection identity. Evidence is explicitly observed after refusal, not proof of
the historical blocking owner or physical closure. Missing permission, vanished
holders, ambiguous connections and truncated coordination names remain unavailable.
No broad server grant, provider call, retry, force release or background poll is
introduced. Existing error codes and original failure remain authoritative.

Use one diagnostic cursor with a one-second statement timeout on the original
failed connection, restore its prior timeout, and close the cursor. Cleanup
uncertainty retains the connection and cannot erase the original refusal. The
source-of-truth SQL definitions remain unchanged; Microsoft DMV contracts and an
owned disposable native fixture establish the queried system columns and exact
resource representation. Test positive holder identity, foreign resources,
disappearing/ambiguous holders, denied access, bounded timeout and failed cleanup.
Bot Changes review required, Deep off; combined D2 caller census remains due.

D2j merged as mirror PR 508 at `2d533f799bf0d3f1bbf7b14395ed6a9021590845`
after exact-head review completed without findings. D2k implements the scoped
diagnostic with one one-second cursor and at most three rows; no SQL repository
change or permission grant is required. Its exact resource representation was
checked against [SQL lock DMV documentation](https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-views/sys-dm-tran-locks-transact-sql?view=sql-server-ver17),
[connection identities](https://learn.microsoft.com/sql/relational-databases/system-dynamic-management-views/sys-dm-exec-connections-transact-sql),
and [server permission checks](https://learn.microsoft.com/en-us/sql/t-sql/functions/has-perms-by-name-transact-sql?view=sql-server-ver17).
Coordination's longer hashed resource is explicitly unavailable; it is not matched
from a truncated prefix. No login/host/query text is returned.

Four new native cases pass: session and transaction holders, disappearance with a
similarly named foreign resource, a caller without server-view permission, and a
real driver timeout preserving 51421 and restoring the original query limit.
They use only new disposable databases; permission testing uses a local user
without login and grants nothing. The first fixture attempt exposed parameterized
batch transaction-count handling and the native check caught an invalid server
permission-class argument; both were corrected before qualification. Resource
preflight retained >8 GiB RAM/disk, zero version store and tempdb log use 27.7%; no
retained database was modified. An initial overbroad all-database log check was
replaced with the plan's tempdb/new-fixture check before creating any fixture.

Validation: 73 focused/native checks, 221 caller regressions (21 opt-in skips),
and 175 final release/reader checks pass; operational logs unchanged. Architecture,
deferred, routing, selection, lint, imports and registration pass. Type comparison
retains 52 inherited diagnostics and removes one; the new helper has none.
Changes scan `0f358018-cd7c-4898-a5ba-9ebd3b4af5e3` completed with zero findings,
snapshot `da400ee7b9dc970e3ac89facbfb7fea777e12de83ab113016b9f5aafc0891e08`.
The eight-member/four-change `p02_d2k_holder_diagnostics_v1` family adds one helper,
preserves all 79 predecessors (canonical digest
`dbde06387dd0a3e437dd778bdbf168f5a04546b6188c0e2216276279758c29ef`), and bounds
the registry to 80 entries/224256 bytes. Full-suite and final caller/resource
census remain at the combined D2 checkpoint; no production action occurred.

## D2l operation budgets and final lifecycle census — scoped before coding

Name the existing login/default/metadata/coordination/snapshot budgets without
raising them. Player reports must set the actual driver statement limit before
cursor creation, bounded by the existing 15-second default and any smaller valid
request. Replace the misleading 300-second row-lock assignment with the existing
one-second metadata row-lock policy. SQL's import/publication application-lock
children still request 60 seconds internally, but the enclosing ODBC statement
deadline cancels earlier. This is a caller-budget correction, not a SQL schema
or procedure contract change; existing explicit import/report-continuation and
maintenance overrides remain distinct. Native fixture SQL will prove the nested
lock wait cannot evade the enclosing statement limit.

The final affected-caller census found player report cursors can escape on error,
legacy connection context exit does not physically close, and writer guard/close
failures can lose first-error or handle custody. Correct these directly related
boundaries while preserving acknowledged business commits and durable receipts.
No retry after commit attempt/acknowledgement or unconfirmed cleanup; cancellation
retains ownership until driver work and cleanup finish. Test ordinary, guided and
startup callers, lost commit reply, rollback/close failure, session grant/release
acknowledgement and no implicit commit on context exit. Shared file locking and
maintenance restructuring remain D3. Changes review required, Deep off.

D2k's initial mirror review identified two cleanup details before merge:
process interrupts must propagate after cleanup, and simultaneous cleanup failures
must retain one cursor/connection owner. Both are corrected and tested. The final
complete range through `2aa9230d053578072b291c45d9e6fc20a69a4514` passed Changes
scan `c22ff387-9c1b-484a-9447-4a3037a473a7` without findings, 63 correction/release
checks and all four native cases. Its exact-head mirror review then completed
without findings; PR 509 merged at `43a0e793ff1e1bcdade77fdb6d222d7345585eda`.

D2l's native tests prove the requested 300-second player setting remains capped
by the actual 15-second statement budget even when an inner application lock asks
for 60 seconds. Cancellation returns HY008, does not replay, rolls back the
fixture insert and physically closes its connection. A lost writer guard-grant
reply is cleaned up on the original session, and an independent fixture session
can subsequently acquire that guard. The original refusal/error remains the
cause; unknown release/cursor/connection cleanup retains custody and closes
admission. This does not certify that the real business report completes within
15 seconds; changing that budget still requires measured qualification.

Initial caller regressions passed 149; new lifecycle/policy/native checks passed 31;
the final release/focused package passed 111. Exact-path type comparison reproduces
18 errors and two warnings with identical messages; both new modules have none.
Architecture, deferred, routing, selection, lint, imports and command registration
passed. Final Changes scan `c8861513-ee84-43ed-91a7-ec62ec58cc4f` completed with
zero findings, snapshot
`989f66e67534d072be5d2837c081ae3a0b1340c5adcd8110ac29ea83dfb15d77`.

Combined-suite follow-up corrected older fixture assumptions about cleanup
exception custody, sealed-bundle dependencies and acknowledged guard release.
The mirror filter now explicitly includes the two inert D2j authority test files;
broad credential exclusions are unchanged. These four affected test files pass
136 checks, with two platform/tooling skips and eight subtests. Historical source
comparison now authenticates D2 successors before comparing the original P0a
image. The process-identity dependency test rejects unreviewed content through
its exact reviewed family, matching the existing constants dependency test.
Those two release files pass all 170 checks. No runtime or registry source changed
for these regression corrections.

Final Changes scan `62a41a80-61f2-4101-9186-455b46ae5232` includes the publication
filter correction and completed without findings, snapshot
`8e42b394d24e7f8f207b25df7fbf8460d9126b137dcf31b8f2aae4f081701173`.
Its measured usage is 969925 tokens including 958848 cached-input tokens.
The later edits to `tests/test_p0a_release.py` and
`tests/test_prepare_k98_update.py` only correct historical fixture expectations;
they preserve exact successor authentication and negative rejection checks.
Additional security scanning is skipped for those two test-only corrections
and delivery-document updates: runtime, permissions, configuration, release
admission and publication filter bytes remain unchanged from the final scan.

The complete combined pytest checkpoint finished with 12942 passed, 1185 skipped,
one dependency warning and eight subtests passed in 1284.65 seconds. Its eight
failures were exactly the six test-file corrections described above; there were
no additional failures. A single final run of all six corrected files passed
306 tests, with two platform/tooling skips and eight subtests passed. The broad
run and final correction run both verified unchanged production operational logs.
The original failed result remains retained. A second whole-suite run is not
required for these fixture corrections: all affected files were rerun together,
and the runtime/package bytes retain the completed full and native coverage.

The `p02_d2l_operation_policy_v1` package has 15 members/nine changed sources,
including two new modules. All 80 prior entries retain their original definitions,
canonical digest `e553ee1fbc4cd7480574bdc6890c4e1d17e565de71a09b0c3d3e39a38f83e00e`.
The registry is bounded to 81 entries/232448 bytes. Every historical bridge checks
the exact successor before using an inert earlier image in a test.

## Final D2 caller and resource census

The refreshed tracked-source AST inventory explicitly includes `_conn`,
`_conn_trusted`, `_conn_import`, `get_conn_with_retries`, `producer_connection`
and `producer_connection_factory`: 77 call sites in 49 non-test/non-script files.
It also finds 35 direct `recovery_snapshot` calls in 11 owning modules and the two
ordinary/guided `player_connection` callers. These are call-site counts, not
claims that all paths execute under an admitted producer. The expanded six-name
inventory is not directly comparable with the earlier three-entry-point count.

| Resource boundary | Final owner and disposition |
| --- | --- |
| Factory selection and retries | D2a selects the callable before attempts; profile/pre-KVK adapter import/execution fallback is removed. Explicit operational routes and weekly-activity explicit/import-time factory selection retain their separate contracts. |
| Profile read / factory setup | D2b/c own rollback/physical close and retain uncertainty. Real-driver qualification covers both; no implicit context commit is treated as cleanup. |
| Previously qualified recovery | All-KVK capture, historical import, stats import outcome and stats-report continuation `inspect` methods retain their existing owned snapshot contract. |
| Unowned/configuration recovery | Unowned `pending/snapshot/action`; configuration `identity/pending_recovery/target_data/snapshot` are passive. Confirmation/adoption/closure retain current locks and CAS. Configuration authority inspection is deliberately not a parallel selector because it can reconcile. |
| Queue/recovery/pool metadata | Queue `pending_intents/accounts/pending_source_jobs/operator_snapshot/repair_receipt/check_intent_weights`, five export-recovery readers, and 11 standalone pool readers use complete owned snapshots. Pool methods with an existing mutation cursor preserve that transaction's ownership. |
| Season/weights | Season source `read`, routing `resolve_season_read` and queue weight validation retain coherent committed tuples. Stale identity/configuration/receipt checks still refuse mutation. |
| Capture and writers | Source transactions and capture sessions preserve first cause and unknown commit; lost grant/release and close uncertainty retains custody. Live writer sessions now verify actual guard release and cannot withdraw while cleanup is unconfirmed. |
| Authority transport | Exact read-only selectors only; one active/one waiting observation. Original handles/replies, authentication, process incarnation, namespace ownership, cancellation and drain remain owned. No queued mutation or provider replay. |
| Player report/cache | Ordinary build, guided report and startup worker use the bounded report statement and explicit connection cleanup. Old-cache fallback is forbidden after uncertain commit or cleanup; acknowledged rollback remains distinct from business completion. |
| Operation overrides | Login 5s/default statement 15s/metadata row lock 1s/coordination horizon 15s/global admission 0/snapshot statement 3s and row wait 0 are retained. Existing stats-import/report-continuation 595s and explicit maintenance budgets are separate; D3 owns their stage restructuring. |

The combined final native run passed 59 cases across profile/setup custody,
unowned/configuration/queue/pool/season observations, transaction lifecycle,
holder attribution, player deadline/cancellation and Windows pipe dispatch.
Resource preflight recorded 9.69 GiB free RAM, ample disk, zero version store and
27.7% tempdb log use. Every SQL fixture creates and normally drops its own unique
local database; pipe fixtures use unique names and inert requests. No retained
21-input rehearsal, real business import/report/provider operation, production
database, service or deployment was used. Real business cost and production
qualification remain D5 and the later approved promotion gate.

### Separate standalone-importer custody debt

### Deferred Optimisation
- Area: `prekvk_importer.import_prekvk_bytes`, `weekly_activity_importer` SQL import context
- Type: cleanup
- Description: The final shared-factory census confirms these standalone upload paths still use pyodbc connection context exit without explicit physical close, and pre-KVK does not separately close its cursor. They do not run through the D2 scan-data writer/authority resource owner. D2a corrected factory selection, not these importers' transaction/outcome contracts.
- Suggested Fix: Deliver a separate bounded importer lifecycle patch with explicit cursor/connection cleanup, preserved acknowledged commits and unknown outcomes, and duplicate/history/result-contract regressions. Reuse the established custody outcome pattern after checking each importer caller; do not make all shared factories implicitly own caller transactions.
- Impact: medium
- Risk: medium
- Dependencies: Existing pre-KVK/weekly upload outcome and history tests, authoritative SQL definitions, and focused native physical-close evidence. This is separate cleanup debt, not a retained P02 incident or evidence of production failure.
