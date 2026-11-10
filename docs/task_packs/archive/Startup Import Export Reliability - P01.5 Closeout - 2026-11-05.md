# P01.5 closeout: calendar ownership and outcomes

**E99/E100, 5 November 2026: CLOSED for the agreed P01.5 scope.** Implementation, review, mirror/private merge, protected deployment and observed normal calendar behavior are accepted. The operator supplied deployment/startup evidence and screenshots, then requested closure, documentation/archive reconciliation and a new P01.6 chat. This does not close all P01/P02-P05 work or certify unexercised production failures.

## Delivered scope and provenance

F23 isolates optional EventSyncLog from business outcomes; the calendar part of F24 retains physical ownership through deadlines, cancellation, cleanup and shutdown; F25 distinguishes successful primary publication from auxiliary-index failure. Existing calendar rules, schedules, permissions, schemas and empty-cache protection remain compatible. The index is retained; the operator identified no known external consumer. There is no atomic two-file publication promise, distributed ownership claim or automatic cross-restart replay authority.

- Mirror [PR #489](https://github.com/cwatts6/K98-bot-mirror/pull/489) merged as `0bf4a14ee8f6e23d9b1f45ad22cb790732d9b22a`.
- Private [PR #729](https://github.com/cwatts6/k98-bot/pull/729) merged and deployed as `24bca82f0a23721c1428bfe4f0db2e120d5b7c34`; predecessor `e3508d122c384bfc750b0e80231554d0d93d8d75`.
- Reviewed private head `7455cb28a68c99b7dfbed558417a980ccc3f00b1` has the released merge tree. Final mirror/private Changes reviews completed with zero reportable findings: `a67d3e2b-1f24-4eb8-ab6c-91e690dccec4` / `4faf85d7-ffe1-436d-92da-c32b336ed3cd`.
- Final hosted Linux regression: 11,601 passed / 1,280 skipped; Windows updater: 315 tests and seven native suites passed. Keep the archived local qualification's adverse runs and environment limitations; do not rewrite them as all-green runs. Later affected native-suite rerun passed 148 tests after local interpreter-path correction.
- SQL source was `b1eeb8e894fec380c7a6d6c5cc5bbfd9dbc3470c`; this release required no SQL migration.

## E99 deployment and functional evidence

| Boundary | Supplied evidence | Accepted meaning |
| --- | --- | --- |
| Calendar directory custody | Helper preview CHECK_PASSED; apply and repeat both REPAIR_VERIFIED; twelve hashes/permissions verified, original retained | Exact scoped repair succeeded; no recursive ACL reset or source deployment by the helper |
| Preparation | Exact predecessor and target accepted; source custody/preflight succeeded | Earlier calendar-directory refusal is resolved |
| Protected release | `96c6ffed-122d-4425-93e3-b2208e0920a4`; package directory `e6b589cb-66c0-43c1-b5d3-9b8d0fef811b`; manifest SHA-256 `ff731492740b2e5922a44a2520ae3a9a98c7f122957ca4990b88c22d625dbdf9` | Source, seed, start and readiness stages verified; exact private target installed |
| Restart/readiness | One operator graceful restart at 21:05:52 UTC; bot ready at 21:10:24; updater reports deployment complete | Installed source/startup accepted; retained work and activation flags preserved |
| Calendar business | Status at 21:13: sync/generate/publish success at 21:10:28; pipeline success at 21:10:33, run `d3b503856a214083bb5890a43f3022d5` | Observed normal calendar pipeline accepted; 320 cached events, 365-day horizon, stale/degraded false |
| Pinned delivery | 21:10:34 log: `ok=True`, `status=edited`, 26 events | Acknowledged update of the existing calendar message, distinct from cache/business completion |
| Optional calendar audit | Status settled; report calendar worker settled, zero failure/drop/unavailable counters | Positive optional-worker observation; not proof of a particular SQL audit-row ID/finish binding |
| Runtime and monitoring | 21:42 screenshot: connected, 24 tasks running, zero crashes/task restarts; report last completed monitor success 21:39:25, no current check/notification failure | Positive retained observations at their stated times, not whole-system health certification |

Operator transcript: `C:\ProgramData\K98\S11\updates\update-20261105T210309458.txt`. Retain failed preparation `aa781dec-e84a-4c29-9451-289b14de75d5` and its transcript, the successful deployment packet, and `calendar-custody-e3508d12-p015-v1` with original/prepared/completed evidence. No further restart, cleanup, replay or repair is required solely for this closeout.

Private source attachments, hashes and before-edit copies are preserved under `.codex_artifacts/p015-closeout-p016-20261105/` in the documentation worktree. Raw reports contain private operational information and are not publication content. The report is `K98-recovery-report-part-1 (9).json`, generated 21:42:44 UTC; it is part 1 with 100 resolved historical incidents, `complete=false`, `more_parts=true`. Its 17,761 total is recorded history, not an unresolved-incident count. Operation preview includes 2 of 512 available operations. Do not claim complete incident or calendar-operation coverage.

## Limits and remaining owners

The updater explicitly reported `fresh_import_export_health_evidence_unavailable`. Source/startup and the observed calendar path are accepted; fresh whole-flow import/export and P03a.2 acceptance remain open. Amber passive SQL/Sheets status means no retained configured-check observation; it is not a failed probe. Successful configuration import at 21:13:12 does not prove export delivery. Its 51400 contention observations ended recovered; P02 still owns systemic contention and holder attribution. A shutdown notification SourceConflict was logged; the later report has no current notification failure, without proving the historical cause resolved permanently.

Unexercised cancellation/commit-unknown/close-failure/index-failure cases retain local qualification, not invented live acceptance. The active P01.5 natural-acceptance register retains optional audit binding, index details, due reminder delivery and later physical-drain observations. These are observation limits, not a deferred P01.5 implementation tranche. P01.4 natural follow-ups remain open; its new-worker drain cannot be certified solely from a successful graceful restart without exact worker evidence. Event-dependent startup waiting on an empty separate event cache is not proof the 320-event calendar failed.

P01.6 owns remaining personal-read F24/B06 capacity and authorization-safe late results. P02 owns F09/F20/F26 and shared contention/budget/fallback policy. P03 owns original-intent durable continuation and unfinished-stage recovery, P04 convergence/history/notification policy, and P05 cross-package/repository-wide confirmation. Preserve P03a.1 accepted recovery; never replay committed work to manufacture acceptance.

## Custody lesson and accountable correction

The supplied metadata showed an application-owned `docs/calendar` directory with read/execute application ACEs. Owner authority is separate from DACL permissions; changing parent ownership does not change existing children. The evidence does not establish which earlier operation created that owner. The guard correctly refused it. The delivery handoff failed to convert an already documented custody requirement into a fresh, release-specific host ancestor inventory; historical scoped repairs were insufficient evidence for a new path.

The reviewed repair created final-ACL protected objects before copying exact predecessor bytes and retained the original objects/evidence, avoiding in-place owner adoption and surviving old-handle authority. Sixty native fixture checks passed; surrogate administrative ownership was clearly separated from the subsequent operator host verification. Repair Changes scan `7a3163ff-1e42-4ebe-9826-6863ab0927fb` completed with no reportable findings. A suspected null-DACL bypass was falsified using the actual Windows/.NET predicate, rather than accepted by reviewer vote. ZIP hash: `411210eaa3c6301bc97d8306b3da9df6fbee85f4a20447627e5e160570141030`.

The Windows ownership/access contract and Promotion Guide now require a dated per-release host custody inventory before handoff readiness: exact changed paths plus every existing ancestor, including documentation/archive directories; actual owner/ACL/inheritance, attributes, reparse/link/stream and byte checks as applicable; installed tool/source identities; and separate code, host, deployment and functional-acceptance verdicts. This documentation does not claim an automated inventory capability was added.

## Navigation

[P01.5 Natural Acceptance - 2026-11-05](../Startup%20Import%20Export%20Reliability%20-%20P01.5%20Natural%20Acceptance%20-%202026-11-05.md); [P01.6 Handover and Scope - 2026-11-05](Startup%20Import%20Export%20Reliability%20-%20P01.6%20Handover%20and%20Scope%20-%202026-11-05.md); [P01.6 Chat Starter - 2026-11-05](Startup%20Import%20Export%20Reliability%20-%20P01.6%20Chat%20Starter%20-%202026-11-05.md); [Tracker - 2026-11-02](../Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md); [P01 Design - 2026-11-03](../Startup%20Import%20Export%20Reliability%20-%20P01%20Design%20-%202026-11-03.md); [Documentation Carry-forward - 2026-11-05](Startup%20Import%20Export%20Reliability%20-%20P01.6%20Delivered%20Documentation%20Carry-forward%20-%202026-11-05.md).
