# P01.1 closeout: startup results and diagnostic safety

> **Current programme checkpoint - 4 November 2026 (E68/E69):** P01.2a is deployed and accepted for its declared reporting/evidence scope at private `67c4e12a8ecf0c25280770860480ac65a6826602`.
> Read the [P01.2a closeout](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Closeout%20-%202026-11-04.md) for delivered corrections, evidence limits, learnings and remaining owners; [P01.2b handover](Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Handover%20and%20Scope%20-%202026-11-04.md) is the next review/design task.
> Earlier dated statuses, holds and next-action instructions in this document are retained history and are superseded for current scheduling. P01.3-P01.6/P02-P05 and exact incident recovery remain open; no replay of accepted work.

Date: 3 November 2026. Status: delivered, deployed and accepted for the declared
P01.1 scope and exercised production paths. E53/E54 record implementation/review;
E55 records operator deployment and live validation. E56/E57 carry the learning and
the approved P01.2a scope into a focused new chat. This closeout does not close P01
as a whole, F09/P02, retained continuation/P03 or combined acceptance/P05.

## Delivery and qualification

- Mirror PRs [480](https://github.com/cwatts6/K98-bot-mirror/pull/480) and
  [481](https://github.com/cwatts6/K98-bot-mirror/pull/481), and private PR
  [721](https://github.com/cwatts6/k98-bot/pull/721), were merged.
- Deployed private target: `0247371d90ec88d4c0639e9200164f4256086037`.
- Final qualified private candidate: `e03f5208f2fc9a56ec3e70fda1ed5370d1f7c995`;
  retained merge qualification verifies the deployed tree matches the candidate.
- Final Windows full suite: 11,057 passed, 1,112 skipped, 8 subtests; operational
  logs unchanged. Final focused follow-up: 79 passed. Skips are not executed proof.
- Review comments were addressed/resolved. Final CI and exact Changes security
  reviews passed; retained manifests cover the final original/follow-up changes.
- Matched synthetic sink-cost qualification and bounded overflow/drain cases pass.
  This is controlled cost evidence, not a production performance benchmark.
- The exact installed updater upgrade and recovery/deployment assessment were
  prerequisites within P01.1, completed before the operator stopped the bot.

See the private [merge/qualification receipt](../../../.codex_artifacts/startup-import-export-review-20261102/p011-merge-qualification.json),
[scope review](../../../.codex_artifacts/startup-import-export-review-20261102/p011-final-scope-review.md)
and [final delivery receipt](../../../.codex_artifacts/startup-import-export-review-20261102/p011-final-delivery-receipt.json).
These are retained local artifacts, not remotely published documentation or current
production observations. No SQL migration was part of P01.1.

## Requirement and task disposition

| Obligation | Disposition | Evidence and limit |
|---|---|---|
| F08 startup deadline/result preservation | Complete for P01.1 | Original work remains owned; late return and completion verification are retained. Production configuration import crossed its 180-second observation deadline and completed with its original recorded successful attempt. |
| F32 optional diagnostic failure isolation | Complete for qualified shared callers | Controlled failures preserve original result/exception, once-only entry and physical drain. Production sink was healthy; no deliberate live logging/disk fault was injected. |
| Shared callers and cancellation | Qualified | Startup/configuration, player/profile/name, MGE/private callback and event/legacy drain boundaries covered by retained tests and review. Production startup evidence is not a claim that every interactive caller was manually exercised. |
| Restart-readable bounded diagnostics | Qualified; current persistence observed | Controlled restore/corruption/retention/first-failure cases covered. Production file persistence was verified; restoration of this new history at the next necessary restart remains a natural watchpoint, not a reason to restart now. |
| Updater and deployment dependencies | Complete for this release | Exact updater prerequisite, retained-work preflight, protected drain/source/seed/start/readiness receipts and successor observed. Do not rerun the old deployment package. |
| Production startup/diagnostic acceptance | Complete for supplied evidence | Eight startup references correlate with saved observations; diagnostics worker alive; all four reported sink counters zero. |
| Evidence usability improvements | Required P01.2a scope | Combined collection, child/parent outcome clarity, explicit stage names and key milestones. These have named ownership and tests in the amended design; they are not unowned deferred debt. |
| Fresh whole-flow import/export | Open outside P01.1 | Deployment's degraded import/export warning is not cleared by startup success. F09/P02, retained continuation/P03 and later provider/combined acceptance remain separate. |

## Production evidence

The user supplied the completed updater output, Report 69, the graceful-restart/startup
log, ordinary recovery-report part 1 and the persisted observations file. Source/startup
deployment was verified, Discord returned online, and the user checked command versions.
The runtime configuration import completed after its observation deadline with its
original attempt receipt. Player cache and tracked-view work also completed after their
observation budgets; tracked-view feature verification reported 21/21 attached.

The later diagnostic snapshot contained 23 settled operations, one process incarnation,
and zero dropped/sink-failure/eviction/context-loss counters. All eight startup references
matched persisted records. The bounded report listed 12 operations, explicitly omitted
8, and the later file included 3 subsequent operations. The tracked-view row accounted
for 313 coalesced/trimmed transitions; that is distinct from ingress loss or writer failure.

The tracked-view child-worker boolean was false while its checked aggregate feature
receipt succeeded. Preserve that evidence as recorded; P01.2a must make the distinction
clear rather than reinterpret historic booleans as authoritative business outcomes.

Private input hashes, correlations and limitations are retained in the
[Report 69 assessment](../../../.codex_artifacts/startup-import-export-review-20261102/p011-report69-review.json)
and [live diagnostic validation](../../../.codex_artifacts/startup-import-export-review-20261102/p011-live-diagnostics-validation-20261103.json).
The ordinary report part is not a complete current incident census. No new repair,
replay, SQL/provider mutation or production restart was performed for this review.

## Next delivery

Use the [P01.2a scope and handoff](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Scope%20and%20Handoff%20-%202026-11-03.md).
P01.2a is the next independently deliverable increment; protected early-issuer work
remains P01.2b. P01.3-P01.6 and P02-P05 extend and qualify the same evidence contract.
Preserve this closeout and its limits; do not repeat accepted work to refresh evidence.
