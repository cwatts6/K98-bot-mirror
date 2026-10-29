# P1 Startup Cache Foundations — closeout, 26 October 2026

> **Current status - 28 October 2026, A1a deployed:** Mirror PR 454 and private
> PR 702 are merged; private `87c1b39325daaa0ca1a8c0cbca656df82d7fa46b` is deployed
> and Discord online. Signup/edit/withdraw are verified on this runtime. A1a qualified
> datasets and timing are delivered; the A1b design packet is prepared for approval.
> Rank confirmation still waits for board refresh. Report 62 queue closure, the older
> configuration decision and separate Discord lag remain follow-ups. Exact audit/cleanup,
> unexercised cases, fresh import/export, natural acceptance and P0 remain explicit.
> See [deployed closeout](P1%20MGE%20A1a%20-%20Deployed%20Closeout%20-%202026-10-28.md) and [A1b design packet](P1%20MGE%20A1b%20-%20Design%20and%20Delivery%20Packet%20-%202026-10-28.md).
> Earlier dated status and next-action text is historical where superseded.
> This documentation update requires no deployment, restart, SQL apply or repeat import.


## Decision and evidence boundary

The operator agreed closure of this bounded phase after deployment and the supplied
functional checks. Status: **delivered, deployed and verified for exercised paths**.
All six agreed packages are delivered. Negative, concurrency and fault cases retain
their deterministic validation; they are not all claimed as production observations.
Full P1, complete WS1–WS6 and P0 acceptance remain open. This documentation closeout
does not authorize runtime changes or repeat accepted operations.

This is the current acceptance overlay. Older architecture, implementation and release
packets retain their dated evidence, including initial failed tests and superseded
packages. Their statements that this phase is not deployed, or that no eligible
original-message callback has passed, are superseded here only to the stated extent.

## The six agreed packages

These are the six packages named in the approved 25 October architecture, not the
six wider Reliability workstreams. Location adapters, name projections and the exact
updater transition are supporting parts of this delivery, not invented extra packages.

| Package | Delivered capability | New status and evidence limit |
|---|---|---|
| 1. Startup ownership/outcomes | Profile/name owned refreshes, draining async adapters, original-work observation after deadlines, invocation/generation outcomes and shutdown admission handling. | **Delivered; observed startup completion accepted.** Report 45 retains profile/name `completed_after_deadline`, successful original results. Cancellation, reconnect and shutdown races retain automated coverage, not blanket live acceptance. |
| 2. Profile integrity/responsive reads | Service/DAL extraction; separate refresh/publication/reader locks; coherent copied snapshots; atomic persistence without truncating fallback; narrow name projections; compatible Location/Ark/upload adapters. | **Delivered; exercised persistence and interaction paths accepted.** Startup saved 2,444 profiles with original-snapshot verification; later report shows saved generation 2, memory reuse. Governor ID, name lookup, ambiguous picker, private result and requested public result passed. Persistence failure and concurrent invalidation remain deterministic evidence. No production percentage speedup claimed. |
| 3. Startup dependency/duplicate-work cleanup | Coherent name publication and invocation-bound main/last-KVK composition; reuse exact nested result, preserve eligible pre-entry fallback and standalone APIs. | **Delivered; observed composition accepted.** Startup main and nested last-KVK share the invocation; main 415 rows and last-KVK 411 rows, with one post-startup last-KVK write in supplied logs. Unknown entered work is not replayed; failure variants remain test evidence. |
| 4. SQL admission attribution | Bounded passive operation/origin/stage/attempt/release correlation; requesting-session role explicitly distinguished from blocker identity. | **Delivered; diagnostic behavior verified.** Report 45 retains startup `CoordinationLockRefused`, SQL 51400, request stage, attempt 3, acknowledged transaction release. **Contention cause and competing holder remain unresolved.** No lock-order, retry-budget, fencing or SQL procedure change was delivered. |
| 5. Passive reporting | Additive `cache_outcomes_v1` and `admission_observations_v1`, source/execution/persistence/verification separation, split timings and preserved event/startup semantics. | **Delivered; report evidence accepted.** Report 45 is complete and shows a healthy finished monitor cycle at 09:03:50 UTC. Prior Report 44 monitor refusal remains historical evidence. Passive report generation is distinct from the active `/ops dl_bot_status` health probes. Healthy monitoring is not export certification. |
| 6. Shared tests/documentation | Ownership, persistence, no-reentry, permission/visibility and report regressions; mirrored/private review and CI; exact updater support, operator release bundle and this closeout/handoff. | **Delivered; validation and supporting documentation complete for this checkpoint.** Preserve skipped integration cases, service review failures and limits below. Next scope remains unapproved implementation. |

## Source, review and deployment

- Mirror #443 and private #692 merged on 26 October. Deployed private source:
  `a68089b6bccf766e9aabb182c582d486130145dc`; predecessor
  `35d8b7e58a5c248c22552b8ae506e1d03ccc6afe`.
- Reviewed private head `169d164c7bd8a030fb4308fa484cfe533b398e0a` has the same
  tree as the deployed merge. Reviewed mirror head was
  `1d47fb6d82e5623f40feb295cdf0ad345cddaa30`. Current scrubbed mirror baseline for
  this documentation is `563b681bd15524ff0103ffe27b49221bb82d1b96`, published from
  the deployed private source; there was no file delta from the reviewed mirror head.
- Operator updater transcript verifies source, seed, start and Discord readiness,
  successor sequence 70. Repeated native-pair checks are not repeated starts and
  their `discord_ready_verified:false` is not the later readiness result.
- The updater retained `fresh_import_export_health_evidence_unavailable`.
  Deployment is complete; new-runtime end-to-end import/export remains unproven.
  Raw protected `verified.json`/`readiness-status.json` were not independently supplied.
- Final private CI: 9,299 passed, 1,220 skipped, eight passing subtests, 19 warnings.
  Earlier local full runs: mirror 9,434 passed/1,080 skipped and private
  9,435 passed/1,079 skipped. Those were earlier heads; final correction had
  95 focused passes on each branch. Do not collapse these into one final local run.
- Final Codex code reviews completed with no findings. Earlier actionable review
  comments were fixed/replied/resolved. Final Copilot re-review failed at the service,
  including a retry; it is not recorded as a passing approval.
- Final Changes security reviews, Deep off: mirror
  `69d1bc61-3884-4eff-9228-94b2687c694a`; private
  `4b161090-2abb-4845-bb27-ceea032be135`; each 21/21 changed source coverage,
  zero reportable findings. No SQL repository diff/migration was part of delivery.
- Release-v3 is the final retained release packet; earlier release-final/v2 and
  superseded ZIPs are not deployment inputs. Its exact 42nd transition preserves
  all previous 41 transitions. This is not general updater productization.

## Runtime and operator acceptance

Report 45 generated 2026-10-26 09:03:50.885414 UTC contains all 17,626 recorded
incidents through its cutoff, resolved; it is not a transactional all-writer census.
Monitor cycle finished at 09:03:50.631096 UTC with no check/notification failure.
Report 44's earlier discovery refusal was followed by recovery; recovery does not
identify the blocker or establish that recurrence is impossible.

The historical profile build-versus-cancelled-observer discrepancy is addressed by
the new ownership/reporting path and positively verified at this startup: original
profile/name results survive the observer deadline. Keep it separate from SQL 51400.
The original eligible Ark message's visible local-time control produced the private
follow-up after the legitimate deployment restart, confirmed by logs and operator
screenshots. That specific callback acceptance is **passed**, not pending; this does
not certify every tracked message or button. Report 45's 21/21 registrations alone
would not have established callback success.

End-of-KVK scan 1193 at 2026-09-29 14:44:00 is expected unchanged off-season data.
The retained 415-row KVK16 cache is valid last-known-good evidence and explicitly
has `sql_execution_receipt=false`; neither a freshness defect nor a fresh SQL/export
receipt follows. No cache refresh or import is required to close this checkpoint.

## Complete carry-forward ledger

Owner for acceptance/policy decisions: Chris Watts. Investigation owner: the next
approved task. IDs below stay stable across follow-ups; none is silently closed by
this phase. Confirmed P0 correctness defects route back to F03/F05 immediately.

| ID | Status / routing | Evidence required or next action |
|---|---|---|
| R01 | Open; next scope N1/N2, WS3/WS6 | Correlate startup SP_Stats_for_Upload-path SQL 51400 admission refusal and Report 44 recovery-discovery refusal separately. Identify holder only from evidence; own session is not blocker. No shared cause with SQL 51700/1222 or singleton is established. |
| R02 | Open; next scope N4 | At 09:02:46 UTC `/ops dl_bot_status` failed editing its original response with HTTP 404 / Discord 10015 Unknown Webhook at `commands/admin_cmds.py:1199`. Later request succeeded. Determine acknowledgement/response ownership and bounded health-work behavior; do not assume token expiry or blame Location. |
| R03 | Natural acceptance pending; N3 regression boundary | Loaded-empty to populated event cache; `refresh_reminder_format`, `rehydrate_live_event_views` and DM restoration must enter without duplication. Report 45 remains valid loaded-empty, waiting-for-events. Do not synthesize events, force refresh or restart. |
| R04 | Exact disposition unresolved; N5 | Daily KVK Overview: distinguish deleted/missing/access-denied/stale identity using exact tracker/message evidence. Historical inaccessible prune and scheduler liveness do not decide it. No automatic repost. |
| R05 | Open; WS3 separate investigation | Protected-launcher coverage and exclusive process singleton ownership. Successful acquisition does not prove exclusivity; SQL 51400 is a different mechanism. |
| R06 | Open; N3, WS3/WS4 | Public-reminder send/delete/expiry child supervision; broader DM/JSON ordering, snapshot consistency, drain and send-versus-disk uncertainty. Preserve Phase 2F atomic replacement and Phase 6K queue work. |
| R07 | Open; N5, WS3 | Historical tracker eligibility and truthful registration versus visible-message reporting. Closed/cancelled Ark posts are not failed callback examples. The eligible Ark callback already passed and must not be repeated. |
| R08 | Open; WS1 | Legacy ProcConfig report/manifest/cleanup semantics, unique per-run artifacts and truthful partial/unknown outcomes. Coordinated transaction/lost-ack fixes remain delivered. |
| R09 | Open; WS2 | Legacy Stats fallback, KVK History and stats-alert side-effect/caller inventory with deterministic no-reentry tests. Selected cache adapters do not prove all wrappers. |
| R10 | Open; WS4/WS6 | Durable profile invalidation/source revisions across restart and remaining cache callers. Existing force/non-forced reuse semantics are preserved; generation is not a durable update receipt. |
| R11 | Open; WS5 | Fighting admission/caps, KS preclaim, ambiguous legacy Pre-KVK edit replacement, in-memory delivery trackers and publication-audit semantics; policy approval before changing behavior. |
| R12 | Open; N1, WS6 | Complete enabled admin/startup/pipeline/compatibility writer inventory against existing authority. Broad inventory is in scope for analysis; each implementation batch is bounded. |
| R13 | Natural acceptance pending | Natural Pre-KVK/off-season dispatch and Phase 2F public-save checks remain separate from diagnostic smoke. No manufactured eligibility or sends. |
| R14 | Open; separate programme | Independent out-of-process monitoring/outage recovery remains distinct from healthy in-process recovery monitoring. |
| R15 | Open; separate programme | Updater productization, existing-directory custody, provider-stream diagnostics and guarded stranded-export workflow; preserve exact protected transitions and receipts. Old 40-entry-capacity wording is historical; actual registry is now 42 entries. |
| R16 | Open; separate optimisation/qualification | Retained history/readback/quota timing, SQL 1222/websocket attribution and session-lock lost-acquisition-ack transport fixture. No common cause or measured percentage speedup established. |
| R17 | Open; P0 F01–F05 | Genuine eligible F04 rollover plus final every-row reconciliation: publication/repair; custody/evidence; pipeline receipts; rollover drain/epochs/verification/settlement/claim release; controls/monitoring. None due is not acceptance. |
| R18 | Retained evidence limit | Fresh new-runtime end-to-end import/export evidence remains unavailable. Preserve earlier accepted scan 1233 and eleven-sheet operator confirmation, URLs, original receipts, imports and captures. Abandoned export stays abandoned, not delivered; no replay, forced release, age settlement or activation change. |

All three P1 families are retained: (1) Discord/domain delivery and missing posts,
including Ark/MGE/voting/calendar and ambiguous sends/edits; (2) non-P0 files,
archives, caches and queues; (3) independent monitoring/outage recovery and complete
writer census. R01–R18 refine these obligations without replacing the programme's
original matrices or moving P0 duties into optional P1 debt.

## Handoff and documentation validation

Read the linked next-phase scope and starter. The proposal is for analysis and
agreement; it is not implementation approval. The local closeout bundle retains
input hashes/copies, a full documentation snapshot and the Git patch, allowing a
new chat to proceed without relying on old chat context or temporary screenshots.
Raw evidence remains private/local; tracked docs omit Discord/user/session IDs.

This change is prose/status/backlog only. Security routing: documented skip, no
runtime/config/permissions/SQL/deployment-policy changes. Runtime pytest, smoke
imports and command registration are unnecessary for this documentation delta.
Architecture, deferred-item, security-routing, test-selection, link and diff checks
are recorded in the local VALIDATION.md. Previous runtime tests remain preserved.

Next: [scope](P1%20Startup%20Coordination%20and%20Background%20Delivery%20-%20Scope%20-%202026-10-26.md) and [new-chat starter](P1%20Startup%20Coordination%20and%20Background%20Delivery%20-%20Chat%20Starter%20-%202026-10-26.md).
