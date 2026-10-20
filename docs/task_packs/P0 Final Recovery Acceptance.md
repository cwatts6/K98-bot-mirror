# P0 final recovery acceptance

## Current boundary — 20 October 2026

The operator requests completion of P0 as the next work package, retaining focused
PRs where they reduce deployment risk. This is the finite completion checklist for
that package. It does not authorize an agent to merge, deploy, execute production
repairs or simulate production failures. Existing implementation and disposable
testing approval carries forward. P0 is **not complete**.

Replacement and publication recovery have now been deployed. The supplied
complete report (20 October, 08:25 UTC) includes 17,500 incidents, all resolved,
and healthy monitoring after guided withdrawal of an unstarted probe ticket.
Fresh publication verification failed earlier and is not certified by that
healthy snapshot. Preventing the recurring ticket and resolving the publication
stall remain required; `P0 Probe Admission and Publication Stall.md` records this
focused work. Retired historical imports still have unknown original SQL outcomes.

The probe-admission prevention release (#407/#659) is now merged and deployed.
The 20 October 09:46 UTC complete report again contains all 17,500 recorded
incidents resolved, with healthy monitoring. Startup logs show ProcConfig waiting
for the active writer and then committing successfully. This does not manufacture
an active-stream refusal or certify fresh publication. The player-stats cache
deadline remains a P0-F03 observation; the separately scoped tracked Discord view
deadline remains P1. `P0 Publication Check Progress.md` owns the next focused
publication race, authority responsiveness and guided progress release.

The original scope remains in `guided_recovery_delivery.md` and
`guided_recovery_release_split.md`. Their dated implementation checkpoints are
history, not separate additional tasks. The remaining obligations below reconcile
those documents with `P0b Monitor and Admission Closeout.md`; none moves to P1.

## Completion workstreams

| ID | Remaining outcome | Current evidence and gap | Acceptance required |
| --- | --- | --- | --- |
| P0-F01 | Unknown/failed spreadsheet writes and still-needed captures | Replacement delivery and publication/absence/damage actions are deployed. Production fresh checking encountered a stall and remains unverified. Historical retirement covers obsolete output only. | Resolve the stalled check; admin identifies input, original/current configuration and known/unknown fault; chooses the applicable replacement, verified retry or disposition; final receipt and ownership are independently verified. No committed import or uncertain write is replayed. Cover another failure during replacement. |
| P0-F02 | Missing evidence and configuration/ownership conflicts | Exact-byte evidence repair is deployed; lost proposals/read checks have backend recovery. Loss of all valid containment/active-registration history and unattributed holds remain explicit gaps. | Guided evidence collection and comparison, exact verified restoration or a separately verified superseding repair. Preserve unverifiable history and foreign/live ownership. A terminal disposition must not claim a recovered original receipt. No indefinite generic Recheck-only workflow. |
| P0-F03 | Interrupted producers and remaining import pipeline | Atomic configuration/report receipts, captured-output continuation and saved-admission decisions exist. Historical partial configuration, partial UPDATE_ALL2 reporting, remaining durable pipeline stages and failures before durable request creation remain required. | Resume only unfinished stages from durable receipts, or guide a separately confirmed superseding/disposition decision. Original input/configuration details, partial results, caches/maintenance/publication state and missing-input collection remain visible. Restart and lost acknowledgements cannot repeat committed work. |
| P0-F04 | Rollover and cross-workflow access | Rollover containment/replacement backends exist but the deployed action policy withholds the family. Some blockers already link to their owning incident. | Qualify every interrupted rollover phase through real admin callbacks, authority journals, temporary SQL and worker settlement. Guided blocker navigation must return to the original repair. Prove exact release and independently verified final continuation. |
| P0-F05 | Complete exposure, diagnostics and acceptance | Reports, bounded alerts, grouped repairs, admission monitoring and startup observations are deployed. Zero current incidents is insufficient coverage evidence. | Every supported failure family has detection, a concise decision, executable action or specific guided evidence collection, audit and final verification. Exercise permissions, stale/concurrent clicks, restart, lost replies, changed configuration, live old writers and failure during repair. Qualify protected updater package and then separately verify natural production admission and provider outcomes. |

## Delivery sequence

1. Qualify and expose complete replacement/delivery workflows (P0-F01) using the
   actual deployed policy. Follow with rollover (P0-F04) once its complete chain
   passes. Keep unfinished or unqualified actions withheld.
2. Finish missing-evidence/conflict and producer/pipeline gaps (P0-F02/F03).
   Existing safe backends are reused, not reimplemented. Split PRs at coherent
   workflow boundaries; do not publish backend-only foundations as completed fixes.
3. Close P0-F05 against the final matrix and exact package. Implementation readiness,
   deployment and live functional acceptance are separate recorded results.

Each implementation row must retain its source files, tests, Changes review and
operator verification evidence before being marked complete. No percentage or
single-release completion promise is inferred from the cleared incident backlog.

## Delivered milestone — replacement action qualification

The deployed change enables the seven existing replacement steps for `export_job`:
isolate targets, save replacement links, verify files, finish/discard a read check,
activate replacements, publish retained input. It does not enable unqualified
publication rebuild/absence actions, rollover, or partial-import acceptance.

The new SQL regression first failed against the deployed policy: replacement
input was unavailable and the incident carried the P0a release notice. The test
uses the real recovery service, production presentation policy, authority broker,
typed messages, SQL transactions and final private verifier. Provider child and
pipe transport are simulated; live HTTP is forbidden. Button tests check separate
confirmation, reopening/restart and repeated confirmation after delivery. Original
unknown jobs remain uncertain in history.

The candidate now preserves a bounded decision summary in the private incident and
complete report: retained input filename when recorded, creation time, original/
current configuration comparison and saved failure context. A configuration
difference is not presented as the cause. Missing historical input/fault details
remain explicitly unknown; output links use the existing private review.

Validation on 19 October: 73 affected replacement-chain, shared-configuration,
source-pool and guided UI tests passed, including three new production-policy SQL
cases. Another 30 diagnostic, adapter and policy tests passed after the final
partial-availability wording change. The preceding 54-test run validated the
initial exposure candidate before the additional summaries; it is not counted
again as final unique coverage. The new regression first failed twice against the
unchanged deployed policy, then passed after enabling the bounded replacement steps.
Architecture, deferred-item, security-routing, test selection, lint, command
registration and synthetic-config import smoke passed. Black explicit-content
checks used the repository's line length and Python target; normal Black CLI runs
were interrupted after remaining active unusually long. No operational runtime or
provider acceptance is inferred from these disposable tests.

The six production-policy SQL tests now also cover isolation through real admin
confirmation, stale isolation refusal, and finishing a complete saved read journal
without a new provider request. No old uncertain write is replayed. The updater
has an exact three-file runtime transition for this release.

Replacement PRs #405/#657 are merged and deployed. Their exact package passed
the protected Windows rehearsal; the operator report confirms the observed backlog
is resolved. Fresh import/export health remains unconfirmed by the updater.
No new SQL schema
is proposed; contracts are checked against the authoritative SQL repository's
reviewed `b663308a` checkout used by the installed migration profile.

## Current focused candidate — publication verification and physical repair

`P0b Verified Publication Recovery.md` owns the next P0-F01/F05 release. It adds
private retained-publication selection, explicit current-output checks, separate
repairs for proven absence/content damage, and original/repair navigation with
independent delivery verification. The latest production report has no open
incidents, so validation must not manufacture a production fault.

All P0-F02/F03/F04 and unfinished P0-F01/F05 acceptance remains required. Missing
permissions, registration, pointer evidence or all valid private copies are not
classified as content damage. Closed seasons and foreign/live ownership remain
protected. Pipeline startup `build_player_stats_cache` deadline observations
remain in P0-F03; view rehydration is separately scoped below.

## P1 — wider bot recovery, as originally scoped

P1 is required programme work after P0, not a destination for unfinished P0 gaps:

- **Discord deliveries and domain publication:** reconcile existing posts, guided
  missing-post repair, expired-reminder policy, Ark/MGE/voting/calendar coverage.
- **Files, archives, caches and queues:** identity-checked continuation, preservation
  of conflicting files, and no duplicate timeout fallback outside the P0 import/
  export pipeline. P0 pipeline caches and admission stay in P0-F03.
- **Independent monitor/outage recovery and complete write inventory:** detect
  outages even when the bot cannot report them, guided host recovery, and classify
  every enabled write path across the bot. Existing P0 monitor correctness remains
  P0-F05.

Tracked Discord view restoration timing out at `arkmatch_48` belongs to the wider
restart/Discord recovery assessment. The latest report exposes it; it is not proof
of successful restoration and must not be silently marked fixed by P0 diagnostics.

## Engineering and validation

Services own recovery decisions and release exposure; the existing DAL and private
authority retain transaction/ownership proof. Views reuse safe defer, private
responses and evidence-bound confirmations. No SQL is added to UI modules; no new
helper abstraction or unrelated refactor is needed for action qualification.

Use K98 test selection plus affected recovery, replacement, configuration, source
pool, policy, permission and restart tests. Temporary SQL fixtures use local K98DEV
only and preserve production operational logs. Security route: **Changes**, final
mirror/private base-to-head diffs, Deep off. Runtime policy changes require that
review; prior backend reviews do not alone qualify new exposure. Run architecture,
deferred-item, routing, test selection, smoke, registration and formatting gates.
