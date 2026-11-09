# P02 D2 delivery review

This is the implementation overlay for the approved
[remaining-work handover](Startup%20Import%20Export%20Reliability%20-%20P02%20Remaining%20Work%20Handover%20-%202026-11-09.md).
The integrated plan, original action census and delivered Phase 1 evidence remain
authoritative within their stated limits. Production deployment and retained-work
recovery are separate. This review does not authorize another full-scale rehearsal.

## Refreshed caller, resource and SQL matrix

| Family | Owning paths and resource | Current disposition |
| --- | --- | --- |
| Connection selection | `core/export_sql_connection.py`, `file_utils.get_conn_with_retries`, `proc_config_import._get_import_connection_with_retry` | D2a binds the selected callable before connection attempts. Existing retry caps, credential validation and explicit operational routing remain. |
| Import/profile adapters | `stats/profile_cache_repository._connect`, `prekvk_importer._conn`, `honor_importer._conn` | Profile and pre-KVK execution/import-error fallbacks removed together; honor already uses the central helper without fallback. |
| Direct factories | `kvk/dal/kvk_all_import_dal.py`, `services/stats_import_outcome_service.py`; `weekly_activity_importer._cxn` | Producer wrapper retains its public call contract. Weekly activity's explicit override/import-time selection is distinct from execution-failure fallback; no credential-policy expansion. |
| Profile result lifecycle | `stats/profile_cache_repository.read_profiles`; `dbo.v_PlayerProfile`, `dbo.v_PlayerScanMeta`, `dbo.v_PlayerKVK_Last3` | D2b requires explicit rollback/close acknowledgement and retains uncertain connection custody in the cache owner. Mapping and SQL definitions are unchanged; separate cursor/connection regressions and disposable-driver qualification cover this slice. Combined lifecycle qualification remains D2/D5. |
| Qualified passive recovery | `core/recovery_sql_snapshot.py`; all-KVK, historical import, stats import outcome and stats-report continuation inspections | Retain the deployed three-second explicit snapshot contract and cleanup acknowledgement. No repeated completed rehearsal. |
| Remaining recovery inspection | `services/unowned_sql_hold_dal.py`, `services/config_preparation_recovery_dal.py`, `services/export_coordination_dal.py` | Inspection currently shares account/resource/preparation/queue locks with mutation helpers. Separate only proven read-only entry points. Mutation snapshots retain locks and current-state revalidation. |
| Capture/mutation custody | `services/import_capture_recovery_dal.py`, `kvk/dal/new_source_import_dal.py` | Global/session guards can protect physical capture and mutation. An observation label alone is insufficient to remove them. Review first-error/cleanup handling with each affected caller. |
| Ordinary season reads | `kvk/dal/source_routing_dal.resolve_season_read`; KVK source selection/routing/configuration metadata | Replace exclusive read admission only after validating the complete consistent tuple and current SQL definitions. Immutable payload reads remain outside the metadata transaction. |
| Authority dispatch | `scripts/run_export_authority.py:serve`, `services/authority_observation.py` | Synchronous observations occupy the authenticated accept loop. Proposed one worker plus one waiting request requires selector-by-selector proof, original peer/reply ownership and physical drain. Mutations stay serial. |
| Holder evidence | `services/legacy_snapshot_admission.py`, `services/export_contention.py` | Current refusal carries requester facts, not a proven holder. Add only bounded refusal-triggered evidence with connection identity; permission denial/races remain explicitly unavailable. |
| Player report budgets | `player_stats_cache._execute_sp_with_retries`, `services/player_report_continuation.py`; `dbo.SP_Stats_for_Upload` | Python's 300-second setting currently changes row-lock wait, not the dedicated 15-second query timeout; SQL children request 60-second locks. Resolve this policy within current limits before qualification. |
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
| F01/F26 | D2a connection selection and failure propagation; remaining operation budgets, lifecycle and native timeout/cancellation qualification stay open. |
| F03/F09 | D2 passive reader census, original global/account/resource guards, CFG-51421 actual-holder evidence and uncertain lock acknowledgement. Test both arrival orders and foreign owners. |
| F12 | D2 bounded authenticated observation admission, busy replies, lost replies, reconnect and shutdown/drain. No arbitrary selector concurrency. |
| F14 | D2 consistent season-read metadata, sealed relationships, stale/partial tuples and snapshot refusal. |
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
