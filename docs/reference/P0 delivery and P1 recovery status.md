# P0 delivery and P1 recovery status

Reconciled 24 October 2026. Owner: Chris Watts. This is the current status overlay
for the dated P0, recovery and Reliability programme packs; their original receipts
and qualification matrices remain evidence. It does not supersede engineering,
security or promotion requirements.

## Delivered and verified P0

| Evidence | Accepted result | Boundary |
|---|---|---|
| Earlier protected deployment, private `cdefe54bb8a2464c8fe8d36a529db798ced550a1` | Source, startup and readiness accepted; original repair PRs #437/#686 delivered. | Preserve the original updater's functional classification. |
| Normal scan 1233, 413 input rows | SQL/report/capture/export chain accepted; export independently confirmed; final notifications acknowledged; operator confirmed new data in all eleven existing spreadsheets. | 899 seconds is end-to-end duration, not provider-only time. This run belongs to the earlier deployed revision. No repeat is needed. |
| Recovery-source PRs [mirror #438](https://github.com/cwatts6/K98-bot-mirror/pull/438) / [private #687](https://github.com/cwatts6/k98-bot/pull/687) | Operator confirms both merged, deployed, verified and working. Supplied updater/runtime receipts verify subsequent private `3a33062cc102e17e5d18d530fb700534d3a661bd` source/startup. Mirror merge also checked on GitHub during this reconciliation. | The newer updater retained `fresh_import_export_health_evidence_unavailable`. Earlier normal-run acceptance is preserved without attributing a new provider run to this revision. Private merge metadata was not independently refreshed. |
| Complete report (40), generated 24 October at 17:21:37 UTC | Retained verification reconciles all 17,612 incident records: resolved, zero pending verifications, monitor healthy. Startup configuration/cache-only completions are verified dispositions. | Supplied dated report, not a new live query; recorded-incident coverage is not proof every possible write path is healthy. Supersedes report (39) for this checkpoint. |
| Original stranded export | Explicitly abandoned/resolved; committed import/reports and existing URLs preserved. | Abandonment is not retrospective delivery success. |
| Earlier publication and cache receipts | Accepted 715-second / 132-request check; verified 415-row KVK16 cache with 29 September source. New startup log also shows completion after the observation deadline and successful configuration import after contention. | Do not repeat these checks. Overlapping history/readback timings must not be added or recast as a new measurement. |

Basis: operator acceptance and the retained private `P0-accepted-P1-handoff-20261024`
bundle: `ACCEPTANCE.json`, `DEPLOYMENT-438-687-VERIFIED.txt`,
`REPORT40-VERIFICATION.txt` and supporting scan acceptance records. These contain
operational identifiers and must not be copied into public documentation unchanged.
The latest supplied runtime log still records tracked-view cancellation and a
successful event fetch with zero upcoming events being treated as not ready.
Neither is repaired by #438/#687.

## P0 acceptance still carried forward

**Deployment accepted; normal import/export accepted; natural rollover pending;
full P0 closeout pending.** No P0 obligation is moved into P1.

| Family | Retain and reconcile at final sign-off |
|---|---|
| F01 — publication and repeated repair | Existing uncertain-write, absent/damaged-output, retained-input, repeated-repair and independent delivery receipts, plus the accepted normal export. |
| F02 — evidence and ownership recovery | Exact ownership/custody/closure, lost evidence and containment qualifications. Preserve historical uncertainty and explicit abandonment separately from new confirmed delivery. |
| F03 — pipeline continuation | Accepted normal import/report/configuration/capture/export chain and earlier partial/failure/remaining-stage qualifications. Committed imports, stage receipts and accepted captures are immutable; an audit row or released reservation is not downstream completion proof. |
| F04 — rollover | Genuine eligible production rollover remains outstanding: none is due. On the natural transition retain old/new pool and epoch, old-writer drain/closure, independently verified private/clear/setup outcomes, final settlement and exact claim release. Verify one settled transition and intended current pool; use supported recovery if interrupted. Do not manufacture eligibility. |
| F05 — control and monitoring | Exact deployed-source/startup evidence, complete diagnostic report and final notifications, alongside permission/concurrency/lost-reply qualifications. Reconcile every row of the coordinated F01–F05 matrix before final closure. |

The [coordinated qualification matrix](../task_packs/P0%20Coordinated%20Completion.md)
and [final acceptance pack](../task_packs/P0%20Final%20Recovery%20Acceptance.md) remain
the obligation owners. A newly demonstrated pipeline admission/cache/receipt or
monitor correctness defect stays F03/F05. Do not replay scans 1231/1232/1233,
resolve work by age, clear claims, change activation flags, replace the eleven
URLs, or remove recovery evidence to make a report look clean.

## Full P1 scope retained

1. **Discord delivery and domain publication:** reconcile existing posts, guided
   missing-post repair, expired-reminder policy, Ark/MGE/voting/calendar coverage,
   restart restoration, public-reminder child supervision and ambiguous send/edit
   outcomes. Workflow status and independently confirmed delivery remain distinct.
2. **Files, archives, caches and queues outside the P0 pipeline:** identity-checked
   continuation, preservation of conflicting files, ordered durable state,
   restart-safe queues and prevention of post-entry executor replay. Existing P0
   cache/admission correctness remains F03.
3. **Independent monitoring, outage recovery and complete write-path inventory:**
   detect outages when the bot cannot report, guide host recovery, and identify each
   enabled writer's authority, outcome evidence, recovery and restart policy.
   Distinguish empty-but-ready event data from unavailable data. P0 monitor
   correctness remains F05.

The six existing Reliability workstreams remain within this programme. The first
runtime slice is tracked-view restoration under WS3; that ordering does not drop
the rest of P1.

| Workstream | Delivered capability to reuse | Remaining scope |
|---|---|---|
| WS1 — ProcConfig lifetime and truthful outcomes | Coordinated configuration writes, targets and checkpoint share transaction ownership; result sets are drained; lost acknowledgements retain uncertainty; participating offloads execute once. | Reconcile legacy report/manifest and cleanup semantics, including unique per-run artifacts and truthful partial/unknown outcomes. The September HY000 observation is historical evidence, not proof the coordinated path remains unfixed. |
| WS2 — executor replay prevention | Coordinated Stats path uses the admitted runtime and a cancellation-draining worker. | Legacy Stats fallback, KVK History and stats-alert wrappers still need caller/side-effect inventory and deterministic no-reentry tests. Fix only the tracker adapters necessary for the first WS3 slice. |
| WS3 — process/task ownership and restoration | P0 startup diagnostics can observe the original task past a deadline and drain on shutdown. | Generic tracked views still select cancellation at ten seconds; empty-event readiness, singleton ownership and public-reminder child supervision remain separate slices. Assess protected-launcher coverage before changing legacy singleton logic. |
| WS4 — DM/JSON ordering | DM tracker I/O lock and single backend selection exist; Phase 2F public-reminder atomic replacement and Phase 6K queue persistence are delivered. | Verify caller ordering, snapshot consistency, shutdown/cancellation and send-versus-disk uncertainty; broader JSON inventory remains. The old claim that current DM wrappers automatically fall back after entry is superseded. |
| WS5 — dispatch ownership/policy | Pre-KVK reservations and diagnostic isolation exist; P0 processing delivery uses durable enter/ack receipts and retains uncertain outcomes. | Reconcile fighting admission/caps, KS preclaim, legacy ambiguous Pre-KVK edit replacement, general in-memory delivery trackers and publication audit semantics separately. Do not extend P0 durable behavior to every route by assumption. |
| WS6 — independent ProcConfig admission | Shared writer runtime, owner context, nested token matching and fail-closed protected activation exist. | Audit all independent admin/startup/pipeline and compatibility entrypoints against the existing authority. Missing report evidence never authorizes replay; do not design a duplicate admission protocol. |

Natural Pre-KVK, off-season and Phase 2F public-save observations remain open and
separate from accepted diagnostic smoke. Their old estimated calendar dates are
historical, not current schedules.

## Additional retained work

- Productize the now-delivered guarded stranded-export helper into a supported
  inspect/review/apply/verify workflow. Reuse exact custody, ownership, fences,
  sealed closure and explicit closeout; keep admission of subsequent exports separate from
  delivery of an abandoned export. Missing evidence retains an explained block.
- Bound offline attribution of SQL 1222 contention, observer unavailability and
  41.7/42.2-second websocket delays. The logs do not prove one common cause.
- Review the protected updater's 40-transition registry before exceeding capacity;
  preserve authenticated predecessors and resumable receipts.
- Retain the disposable SQL transport fixture for a session lock granted before a
  lost acquisition acknowledgement; no production fault injection.
- Keep the existing bounded history/readback/quota optimisation item and its
  accepted measurements. Do not repeat provider checks for documentation work.

These are captured in the [active deferred register](deferred_optimisations.md).
Partial delivery is reconciled there, not treated as closure of whole workstreams.

## Approved tracked-view implementation

The operator approved architecture, implementation and validation, including the
first-phase documentation update. The first runtime slice is implemented locally in the
[tracked-view plan](../task_packs/P1%20Tracked%20View%20Restoration%20-%20Architecture%20and%20Implementation%20Plan.md).
Review and production acceptance follow that staged plan. Local restoration tests
do not close full P1 or the outstanding P0 acceptance items above.
The [mirror PR review](../task_packs/Mirror%20PR%20Cleanup%20-%202026-10-24.md)
separates obsolete review branches from remaining product acceptance.
