# P1 Startup Cache Foundations — implementation and acceptance

25 October 2026. Operator-approved local implementation; not deployed or runtime accepted.
Mirror baseline: `cb723927b5a68da733ad19fc9878743978bcf2f3`, the scrubbed snapshot of
private deployed `35d8b7e58a5c248c22552b8ae506e1d03ccc6afe`. Do not reapply the
delivered event-cache feature/compatibility work. Development uses an isolated
mirror worktree and its interpreter; protected production source/ACLs are untouched.

## Delivered local design

1. Profile SQL mapping lives in `stats/profile_cache_repository.py`. Required view
   failure remains failure; optional scan/KVK enrichment omissions are explicit.
   The existing columns, nullable mappings, NOLOCK policy and KVK-only rows remain.
2. `ProfileCacheService` separates refresh ownership, publication and reader locks.
   Equivalent overlapping observers join one future. SQL, JSON and worker waits
   never hold the reader lock. Reads copy only the requested profile where possible.
   Invalidation supersedes an in-flight candidate; publication and invalidation
   serialize. Async callers use draining adapters, including invalidation if needed.
3. Persistence uses the existing unique-temp `atomic_json_write` with `json_default`.
   There is no truncating fallback. A failed save preserves prior bytes and explicitly
   reports memory-only availability. The `{generated_at, players}` envelope and TTL
   remain unchanged. Legacy `force=True` still permits fresh disk reuse; the new
   explicit `fresh=True` request waits for an older worker then owns a new build.
   This does not claim durable invalidation across restart.
4. Profile/name startup observes the original operation after its deadline. Shutdown
   closes admission and cancellation drains entered workers. Reconnect remains under
   the existing startup-once gate. Name rows/maps publish as one snapshot; failed
   refresh does not advance the snapshot. Legacy sync/async facades remain available.
5. Stats composition records main and nested last-KVK subresults in a process-local
   context, propagated into draining threads. Startup/admin reuse the exact nested
   result. Main failure before last-KVK entry permits the independent fallback;
   entered/unknown last-KVK work is never replaced. Separate requests never share
   ownership. Existing cache JSON, standalone APIs, source selection and SQL authority
   are unchanged. Last-KVK remains a non-fatal subresult, not main execution proof.
6. Passive reporting adds `cache_outcomes_v1` and `admission_observations_v1`.
   Cache identity, execution, availability, source, persistence, verification and
   timings remain separate. Startup observer state supplies deadline/cancellation
   disposition. Profile timings split build/validation/persistence. SQL contention
   retains attempt/elapsed/stage/release facts plus process-local correlation and
   startup origin. The bounded 32-record buffer requires no query or provider call.

The Location lookup acknowledges privately before blocking work, keeps ambiguity
and errors private, and delivers a successful result with the requested visibility.
Permission decorators still run before lookup. Ark and post-location-import cache
calls use draining workers. The post-import warm keeps its existing non-forced
semantics; it neither repeats an import nor claims post-update SQL execution.

## Evidence interpretation

The 25 October startup `SP_Stats_for_Upload` path observed
`CoordinationLockRefused` / SQL 51400 at preparation request admission. The requesting
SQL session is not evidence identifying the blocker. Process singleton acquisition
succeeded earlier; exclusive singleton ownership remains a different residual.
No lock ordering, retry budget, fence, writer token, SQL procedure, permission or
provider protocol changes are included. No demonstrated ordering defect justified
behavioral SQL changes. External blocker identity remains unknown.

The separate profile discrepancy was build/memory completion versus a cancelled
startup observer reporting unconfirmed. Source inspection establishes blocking
reader-lock and persistence-reporting defects; it does not establish a shared root
cause with SQL contention or historical websocket timings.

End-of-KVK scan 1193, source `2026-09-29 14:44:00`, is expected unchanged off-season
data. Retained 415-row KVK16 readback is last-known-good provenance, not a freshness
defect, new SQL execution or export receipt. Process-local generation/correlation
does not become durable business evidence. Existing report fields retain meaning.

## Test and review contract

New tests cover single flight, concurrent readers, invalidation, distinct explicit
fresh requests, copy isolation, failed serialization/fsync/replace and unique-temp
cleanup, prior-process/generation rejection, required/optional SQL mapping, repeated
cancellation/drain, closed admission, exact main/last subresults, fallback eligibility,
passive reports, private acknowledgement/public result visibility and permission
denial. Existing startup, event, source-fallback, contention and caller suites are
regression boundaries. Use barriers and temporary files; no live SQL/provider calls.

Acceptance mapping:

| Plan cases | Evidence owner |
|---|---|
| A01–A06 | Profile/name ownership tests, startup-diagnostics and startup lifecycle tests; exact-generation startup verifier tests |
| A07–A14 | Profile ownership and repository contract tests; unique-temp writer failure tests |
| A15–A16 | Location callback permission/visibility tests, Ark and upload-route regression suites |
| A17–A19 | Stats composition, admin service and existing player-stats suites |
| A20–A22 | Existing export contention/legacy snapshot tests and additive admission correlation tests |
| A23–A26 | Passive report tests, event-startup regressions, existing off-season source verification and structured timing assertions |

Record actual runs separately; a mapped or skipped case is not automatically passed.
Mandatory local gates: focused and full pytest with operational-log isolation,
Black/Ruff, architecture/deferred/security-routing validators, test selector,
synthetic-config smoke imports and command-registration audit.

Security routing: Changes, Deep off, exact mirror baseline to final working-tree
patch including new files. Root SECURITY.md applies. Review permission/visibility,
file preservation, cancellation/ownership, SQL extraction and diagnostic privacy.
SQL repository has no diff; no SQL security review or migration is implied. Production
updater/source-transition qualification remains a separate gate; never weaken source
hash tests or custody requirements to make this runtime change deployable.

### Local validation record, 25 October

- Initial full suite: **9,318 passed, 1,081 skipped, 11 failed, 25 setup errors**,
  plus eight passing subtests, in 17m26s. This is retained as a failed initial run,
  not relabelled a clean final full-suite result.
- Failures were historical source-image expectations, a teardown fixture leaking
  closed cache admission, and PyWin32 subdirectories missing from the isolated
  environment's dependency path. The test-only successor bridge authenticates an
  immutable mapping and exact current bytes before retaining original predecessor
  assertions. Negative tests reject modified source and mapping data. Production
  updater scripts, registry and previous fixtures remain unchanged.
- Every original failure/error family passed its **164-test recheck**. Teardown
  fixtures isolate profile/name ownership; production shutdown still closes admission.
  PyWin32 checks use the worktree interpreter with the existing development package
  paths, and disposable native Windows fixtures, not the running bot or production.
- Final consolidated affected run: **908 passed**, one dependency deprecation
  warning, across 95 test files. The log-isolation harness confirmed production
  operational logs unchanged. This includes corrected metadata, timestamp corruption,
  source-stamp verification, Discord protocol sequencing and no duplicate Ark fallback.
- Architecture, deferred-item, security-routing, command-registration and synthetic
  import checks passed. Pre-commit includes Ruff, Black, secret detection and Pyright;
  automatic line-ending fixes were followed by passing checks. Pyright's optional
  dependency warnings are distinct from errors; no dependency versions were changed.
- The full suite was not rerun after the bounded corrections; the consolidated final
  affected run and explicit failure-family recheck qualify those changes. Existing
  skipped integration/runtime cases remain skipped, not accepted.
- A final review then tightened startup readback comparison to reject non-finite
  source timestamps. Its profile ownership and cache-contract recheck passed all
  **30 tests**, including NaN and both infinities; operational logs were unchanged.
  This is a subsequent focused result, not an additional full-suite claim.

Changes security reports and exact final patch identity are retained in the local
handoff. Initial reviews found no reportable vulnerabilities and identified ordinary
correctness issues that were repaired and tested. A security result never establishes
runtime acceptance, deployment compatibility or measured production speedup.

## Remaining acceptance and programme scope

### Subsequent PR and release preparation

The operator subsequently authorized both PRs, review-comment management and full
deployment support. The [release instructions](P1%20Startup%20Cache%20Foundations%20-%20Release%20Instructions.md)
add one exact updater transition and its package upgrade. This later release-support
delta supersedes the earlier statement that updater files are unchanged; it preserves
the original 41 transitions and every source/custody guard. It does not install the
package or authorize deployment. The final PR handoff records full-suite, final-head
review/security and private-history compatibility results separately.

Fresh PR validation passed: mirror **9,434 passed, 1,080 skipped** and private
**9,435 passed, 1,079 skipped**, each with eight passing subtests and one dependency
warning. Mirror operational-log isolation passed; private operational logs remained
absent. These runs covered mirror `1cee8975` and its private equivalent `2f0cfe61`.
The subsequent review correction changes only name-builder comments/docstring and
its exception log label, with the exact transition pin and package hashes updated.
Its focused name-cache/transition recheck passed **152 tests** with operational logs
unchanged. Final heads, CI and review receipts are in the release handoff; no further
full-suite claim is made for that bounded follow-up.

All three P1 families remain: Discord/domain delivery and missing posts; non-P0
files/archives/caches/queues; independent outage monitoring and enabled-writer census.

| Stream | Separate residual |
|---|---|
| WS1 | Legacy ProcConfig reports/manifests, unique artifacts, cleanup and truthful partial/unknown results |
| WS2 | Legacy Stats fallback, KVK History and stats-alert side-effect/no-reentry inventory |
| WS3 | Exclusive singleton after launcher review; public-reminder send/delete/expiry children; historical tracker eligibility; original-message and natural runtime acceptance |
| WS4 | Other DM/JSON callers, snapshot ordering, shutdown and send-versus-disk uncertainty; no blanket closure from profile persistence |
| WS5 | Fighting admission/caps, KS preclaim, ambiguous legacy Pre-KVK replacement, memory delivery trackers and publication audits |
| WS6 | Remaining independent admin/startup/pipeline/compatibility writers against existing authority; selected cache coverage is not a full census |

Retain the natural loaded-empty → populated event transition, both deferred one-shots
and DM restoration without duplicate entry. Eligible original-message visible controls
and a safe private local-time callback after a legitimate restart remain unaccepted;
historical closed/cancelled Ark posts are unsuitable. Exact Daily KVK Overview
inaccessible/deleted/access disposition remains unresolved; do not repost automatically.
Natural Pre-KVK/off-season dispatch and Phase 2F public-save checks remain separate.

P0 remains open: F01 publication/repair; F02 custody/evidence; F03 pipeline receipts;
F04 genuine eligible rollover (drain, old/new pool epoch, independent verification,
settlement and claim release); F05 controls/monitoring and final **every-row F01–F05**
reconciliation. A demonstrated current admission/cache/pipeline defect stays F03,
monitor correctness stays F05. Preserve accepted scans/imports/reports and scan1233
export plus 11-sheet operator visual confirmation, URLs and original receipts.
Abandoned export stays abandoned. Fresh-runtime evidence unavailable neither revokes
earlier acceptance nor certifies a new run. No replay, age-based release or forced rollover.

Updater productization/custody/stream diagnostics, SQL1222/websocket attribution,
history/quota optimization and session-lock lost-ack qualification remain separately
scoped. The reviewed 41st updater transition is delivered; older 40-entry wording is
historical. Deployment, restart, activation and provider acceptance require their own
authorization and evidence. No operational acceptance is manufactured here.
