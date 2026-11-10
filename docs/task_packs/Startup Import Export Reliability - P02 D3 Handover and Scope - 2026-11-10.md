# P02 D3 closeout and remaining-work handover

D3a-D3g source delivery is complete and individually merged in Bot mirror PRs
513-519; SQL companions 142-147 are merged. The operator also authorized the combined
private production PR and its review/comment cycle. Production merge, deployment,
restart, SQL apply, provider actions and retained recovery are separate. Deployment
remains held until the planned step after D5. Phase 1 remains the installed release.

Use the [D3 delivery closeout](Startup%20Import%20Export%20Reliability%20-%20P02%20D3%20Delivery%20Review%20-%202026-11-10.md)
for all seven slices, exact merge/review evidence, final tests, coverage and impact.
Completed slice packs and original scope evidence are archived, not discarded.
The original D3a-first instructions are historical and must not restart completed work.

## Next work and closure owners

| Obligation | Owner | Required evidence |
| --- | --- | --- |
| D4 installed/manual/legacy alignment | SQL and release owners | Fresh installed bindings for UPDATE_ALL/Rally/TEST and direct children; qualify actual use or obtain explicit retirement approval; no business execution merely to discover use. |
| D4 final release compatibility | Bot/SQL release owners | Exact final combined installed-source/updater transition, complete dependency rejection, startup/source pins, permissions/signing and coordinated SQL migration/rollback. Per-slice transitions do not admit the combined jump. |
| D4 unresolved source dependencies | SQL owner | Authoritative KS4_UNO_SEQ and installed msdb backup-wrapper definition/permissions; reconcile retained historical backup queue outcomes without replay by age. |
| D5 final qualification | Bot and SQL test owners | Balanced scale/cost, actual relevant children, output equivalence, scheduling, both ownership orders, faults, cancellation, restart and cleanup; unchanged resource limits. |
| D6 release readiness | Release owner and operator | After D5, refresh installed identities and actual changed-file/ancestor custody; separately controlled coordinated deployment with rollback preserving committed work. |
| First normal import/export | P03/P04 owners and operator | Settle actual blockers and essential P04 corrections. Do not require zero incidents or wait merely for P05. |

The installed-to-combined transition previously returned COORDINATED_RELEASE_REQUIRED.
It is still an explicit D4 obligation; do not bypass it or deploy intermediate slices.
The current updater contains 87 fixed entries, with historical definitions preserved.

## Invariants and acceptance limits

Keep RCSI off. Preserve 8 GiB free memory and disk reserve, sampled log below 70 percent
for optional statistics, version store below 512 MiB, and balanced overall median
ON<=OFF*1.20+1000ms and stage<=OFF*1.20+250ms where applicable. The single 21-input
rehearsal allowance is consumed. No timeout, input-cap or backup-schedule increase.

Keep business receipts distinct from optional maintenance and backup request evidence.
Requested backup is not completed backup. Never replay unknown/failed work, adopt a
historical queue row or release ownership by age. Preserve immutable first failure.
The raw-history SNAPSHOT/index REBUILD failure SQL 3961 remains evidence; managed
reader exclusion does not qualify arbitrary uncoordinated readers or ad-hoc DDL.

Do not replay deployment, imports, exports, recovery or provider effects to refresh
evidence. Broad datatype conversion, cache decode/rebuild optimisation, wider
orchestration extraction, Stats UI/SDK acknowledgement, unrelated MGE/Ark performance,
standalone pre-KVK/weekly physical-close debt and tied-zero ranking policy retain
their existing ownership and scope. No new chat is created by this handover.
