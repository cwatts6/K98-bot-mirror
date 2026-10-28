# P1 monitoring and import/export reliability: accepted closeout

> **Current status - 28 October 2026, A1a deployed:** Mirror PR 454 and private
> PR 702 are merged; private `87c1b39325daaa0ca1a8c0cbca656df82d7fa46b` is deployed
> and Discord online. Signup/edit/withdraw are verified on this runtime. A1a qualified
> datasets and timing are delivered; next is focused A1b scope/design in a new chat.
> Rank confirmation still waits for board refresh. Report 62 queue closure, the older
> configuration decision and separate Discord lag remain follow-ups. Exact audit/cleanup,
> unexercised cases, fresh import/export, natural acceptance and P0 remain explicit.
> See [deployed closeout](P1%20MGE%20A1a%20-%20Deployed%20Closeout%20-%202026-10-28.md) and [A1b scope/handoff](P1%20MGE%20A1b%20-%20Scope%20and%20Handoff%20-%202026-10-28.md).
> Earlier dated status and next-action text is historical where superseded.
> This documentation update requires no deployment, restart, SQL apply or repeat import.

Date: 28 October 2026. **Status: COMPLETE for this bounded phase, including production acceptance.**
The operator confirms that the deployed bot is online, standard imports/exports completed,
the data looks correct and `/stats player` works. MGE signup/withdrawal remains a separate
open issue. This closes the monitoring/checkpoint/health-probe/ProcConfig/Alliance Activity
correction phase; it does not close every WS1-WS6 obligation, all P1, or P0 rollover acceptance.

This is the current overlay over the 26 October foundation and event-delivery checkpoints.
Older dated receipts remain valid history. The stable R01-R18 ledger below supersedes their
status columns without erasing their original acceptance requirements.

## Delivered source and review

| Repository | Delivered change | Status |
|---|---|---|
| Bot mirror | [PR #450](https://github.com/cwatts6/K98-bot-mirror/pull/450), reviewed head `895b48cc7db0424d84812b5b76df71e84a707c12` | Merged |
| Private bot | [PR #698](https://github.com/cwatts6/k98-bot/pull/698), reviewed head `d271af5cc001bd759d69da231df2bda0026d00a4` | Merged and deployed as `f6a929c0597ce257ce18380af1ab6f7ad8ddcc5d` |
| SQL | [PR #133](https://github.com/cwatts6/K98-bot-SQL-Server/pull/133), merge `7e91989f619deb46836194c7e705b0a9eb2ebe11` | Read-only checkpoint blocking diagnostic; no migration/apply required |

Private source was patch-promoted from private main with the reviewed mirror changes.
The scrubbed mirror and private repository retain different baseline-only files. The deployed predecessor was `756cbd18d7044897783d01f3a0093aaf6e2d03a7`.
The preceding ProcConfig failure recording, safe health-probe cleanup/reconciliation and
row-based Alliance Activity completion changes are included in the accepted deployed baseline.

Final private CI passed: 9,895 tests passed, 1,240 skipped, 19 warnings and 8 subtests.
[Exact-head quality run](https://github.com/cwatts6/k98-bot/actions/runs/40595406042).
Focused lifecycle/native validation, architecture/deferred/security-routing checks and
mirror/private Changes reviews were retained with the release. Review comments were addressed;
these historical runtime checks are not newly rerun by this documentation closeout.

## Corrections and causal boundaries

- Stats observation now follows the coordinated lock order and uses nonblocking observation.
  Busy is reported only after transaction rollback/close is acknowledged.
- A completed UPDATE_ALL2 can retry its short checkpoint/capture metadata step within bounds,
  with ownership, fence, version and exact completion revalidated. Business SQL and provider
  delivery are not replayed to repair a metadata/observation failure.
- Pending checkpoint/capture and progressing/waiting recovery are represented truthfully.
  Observer contention after business completion does not invent a failed import or false success.
- Notification reconciliation retains exact pipeline/cache/export evidence. An observation
  outage does not suppress independently verified stats delivery; a binding mismatch fails closed.
- Monitor health distinguishes active progress, completed-check freshness and failed cycles,
  retaining failed-stage/cause evidence. Active work precedes the bounded historical sweep.
- Health-probe request/withdrawal uses safe retry and reconciliation. ProcConfig failures before
  inputs are recorded as attempts and can reconcile when exact later evidence resolves them.
- Alliance Activity completion compares imported rows with its own source snapshot. It covers
  the top ten alliances, whose membership and online population vary. A different report's
  filters/governor population is not a valid completeness denominator.

The lock-order conflict family was established in code and deterministic native two-connection
rehearsals. The exact holder of the historical production refusal was not captured. Two
connections alone are normal and are not a root cause. SQL 51400, 51700, 1222, process singleton
locking and Discord response errors remain distinct unless exact evidence connects them.
The [conflict map](../reference/checkpoint-observation-lifecycle.md) retains the audited paths.
The optional SQL observer captures waiter/blocker evidence; it does not change production state.

## Production acceptance evidence

All times below are UTC on 28 October 2026. Evidence: operator updater transcript, supplied bot
log, complete Recovery Report 59 and the operator's final visual/data/command confirmation.
Raw logs, Discord identifiers and runtime ownership identifiers remain local/private.

| Check | Observed result |
|---|---|
| Protected deployment | Source, seed, start and readiness verified; successor sequence 77; Discord ready at 07:25:54 |
| Stats import | 411/411 source rows; UPDATE_ALL2 succeeded; checkpoint commit acknowledged at 07:33:00 and snapshot capture at 07:33:05 |
| ProcConfig | Startup and subsequent run completed; later snapshot capture acknowledged at 07:34:39 |
| Alliance Activity | Snapshot 576: 854 source/stored rows; COMPLETE; expected=observed=854; missing governors/metrics and invalid metrics all zero |
| Export and final reporting | Export confirmed at 07:48:10; final confirmed summary acknowledged at 07:48:14, sheet confirmation at 07:48:17 |
| Health-probe cleanup | Observed request/withdrawal contention recovered through bounded retries, with transaction release acknowledged; no unresolved cleanup incident in Report 59 |
| Recovery report | Generated 08:11:46; complete 17,672-record report: all resolved, zero pending verification; successful monitor completion at 08:11:16 |
| Operator acceptance | Data visually correct; `/stats player` worked; operator accepts phase completion |

The updater's `fresh_import_export_health_evidence_unavailable` warning described the startup
readiness instant. The later correlated import/export and operator checks close R18 for this
runtime; the earlier warning should not be rewritten as if it never occurred.
No ERROR/CRITICAL appears in the supplied post-restart log segment. Startup deadline warnings
subsequently completed. Resource-owned health probes deferred while real work retained authority.
This is expected waiting, not proof of failed delivery.

Limits: the main successful import did not need a live checkpoint retry; that branch's evidence
is deterministic/native testing. No global SQL pending-probe inventory was queried for this
closeout. Report resolution is not an exhaustive enabled-writer census. The event cache remained
valid `loaded_empty`; 21/21 tracked views attached is not acceptance of every visible callback.
No repeat import, export, restart, reconciliation apply or cleanup is required for this phase.

## Remaining programme: stable carry-forward ledger

Owner for policy/acceptance: Chris Watts. Investigation owner: the next scoped task.
These rows mix implementation, investigation and natural acceptance; they are not eighteen bugs.

| ID | Current disposition | Remaining obligation / route |
|---|---|---|
| R01 | Bounded conflict correction delivered and accepted | Historical exact blocker remains unknown. Investigate recurrence with retained diagnostics; do not reopen successful runs or equate all refusals. |
| R02 | Status response ownership/diagnostics delivered; broader acceptance retained | Preserve historical 10015 evidence. Audit related response lifecycle in batch A; MGE 10062 is a separate observation, not an established shared cause. |
| R03 | Natural acceptance pending | Loaded-empty to populated event transition, deferred rehydration and subscribed DM restoration without duplication. No synthetic event/forced refresh/restart. |
| R04 | Historical disposition unresolved | Establish exact Daily KVK Overview missing/deleted/access/stale identity. New journals do not retroactively prove the historical message; no automatic repost. |
| R05 | Audit open | Protected launcher coverage and exclusive process singleton ownership, separate from SQL coordination. Batch B. |
| R06 | Selected event delivery implemented; broader persistence coverage partial | Remaining public/DM child ordering, JSON snapshots, drain and send-versus-disk uncertainty. Batches A/B and natural acceptance. |
| R07 | Original eligible Ark callback accepted; broader domain coverage open | Historical tracker eligibility, actual controls and domain workflows. MGE first in batch A; do not repeat the accepted Ark callback. |
| R08 | ProcConfig attempt/reporting and health cleanup corrections accepted | Audit remaining legacy report/manifest/artifact uniqueness and ambiguous cleanup paths; do not restate fixed coordinated paths as unchanged defects. Batch B. |
| R09 | Audit open | Remaining Stats fallback, KVK History and stats-alert caller/side-effect inventory with no-reentry evidence. Current successful route is accepted. Batch B. |
| R10 | Open | Durable profile invalidation/source revisions across restart and other cache callers. Successful current cache startup does not prove all invalidation paths. Batch B. |
| R11 | Policy/persistence scope open | Fighting admission/caps, KS preclaim, ambiguous legacy Pre-KVK replacement, in-memory trackers and audit semantics. Batch A, policy agreement before changing behavior. |
| R12 | Selected writer/conflict map delivered; complete census open | Remaining enabled admin/startup/pipeline/compatibility/domain writers and authority contracts. Batches A/B; implement only demonstrated gaps. |
| R13 | Natural acceptance pending | Natural Pre-KVK/off-season dispatch and Phase 2F public-save evidence; current stats notification proves its own route only. |
| R14 | Open | Independent out-of-process monitoring and outage recovery. Healthy in-process monitoring does not replace it. Batch C. |
| R15 | Protected updater working; remaining productization partial | Supported custody/provider-stream diagnostics and guarded stranded-export recovery; preserve exact receipts. Current transition registry has 48 entries. Batch C. |
| R16 | Deferred performance/qualification | History/readback/quota profiling, measured ActivePreparationID lookup plan/cost, and lost-acquisition-ack transport fixture. No unmeasured index or speedup claim; not a current acceptance blocker. |
| R17 | P0 acceptance remains separate | Genuine eligible F04 rollover and final every-row F01-F05 reconciliation. Preserve drain/epochs/settlement/claim-release and uncertain-outcome boundaries; do not manufacture eligibility. |
| R18 | CLOSED for deployed f6a929c runtime | Fresh correlated import/export plus operator visual confirmation and `/stats player` acceptance. Earlier accepted receipts and abandoned/uncertain work retain their own dispositions. |
| MGE-01 | Confirmed user-visible issue; cause investigation next | Signup logged, then withdrawal interaction failed with Discord 10062. Determine committed state and acknowledgement ownership; audit submit/edit/withdraw together. Batch A first. |

## How much remains

Plan three further delivery batches, with scope-sized PRs within each, plus a separate acceptance
lane. This is a sequencing estimate, not a fixed PR count or a percentage-complete claim.

1. **A: Discord/domain completion, MGE first.** Resolve the reported MGE lifecycle defect and
   inspect related interaction/publishing paths. Then bound remaining domain/publication policy
   gaps across Ark/MGE/voting/calendar and WS3/WS5. Do not combine unrelated policy rewrites.
2. **B: Remaining execution and persistence coverage.** Complete the writer/caller census,
   singleton and cache/JSON/queue ownership checks; fix demonstrated residual WS1/WS2/WS4/WS6 gaps.
3. **C: Independent operations and recovery tooling.** External monitoring/outage recovery and
   remaining supported operational recovery flows. Keep evidence-led performance work separate.

In parallel, retain R03/R04/R13 natural/message-disposition checks and the separate P0 R17
acceptance lane. MGE is the currently reported active user-facing defect; open audits are not
proof of more faults. Effort and completion percentage need the next bounded census first.

## Documentation validation and security routing

This closeout and its linked scope/starter update prose, status and navigation only. The owned
file manifest consists of README-DEV, reference/status/programme indexes, the dated closeout and
handoffs, monitoring/event/checkpoint references, MGE reference and deferred register overlays.
No runtime, SQL, config, permission, dependency, deployment policy or persistence behavior changes.
Security routing: documented skip for this exact Markdown-only delta. Runtime pytest, imports,
command-registration and native SQL tests are skipped because no executable behavior changes.
Run architecture, deferred-item, security-routing, test-selection, local-link and diff checks.
Selector generic runtime suggestions do not override this documented scope-based test decision.
No bot deployment or restart is needed for this documentation change. Revert its documentation
commit if correction is needed; runtime/source acceptance remains tied to f6a929c above.

Related: [accepted closeout](P1%20Monitoring%20and%20Import%20Export%20Reliability%20-%20Closeout%20-%202026-10-28.md) | [next scope](P1%20Discord%20Domain%20Completion%20and%20MGE%20-%20Scope%20-%202026-10-28.md) | [chat starter](P1%20Discord%20Domain%20Completion%20and%20MGE%20-%20Chat%20Starter%20-%202026-10-28.md).
