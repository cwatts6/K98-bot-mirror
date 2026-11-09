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
| Profile result lifecycle | `stats/profile_cache_repository.read_profiles`; `dbo.v_PlayerProfile`, `dbo.v_PlayerScanMeta`, `dbo.v_PlayerKVK_Last3` | SQL definitions verified in the authoritative repository. Mapping is unchanged. Driver context-manager exit does not itself prove physical close; lifecycle correction remains D2, with independent cursor/connection doubles required. |
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
