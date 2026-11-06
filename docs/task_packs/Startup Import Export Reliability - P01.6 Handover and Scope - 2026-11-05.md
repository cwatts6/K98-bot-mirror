> **P01.6 implementation update, 5 November 2026.** Updated design, implementation and offline/disposable-local-SQL qualification are approved. The local candidate and current qualification verdict are in the [implementation receipt](Startup%20Import%20Export%20Reliability%20-%20P01.6%20Implementation%20and%20Qualification%20-%202026-11-05.md). P01.6 is not deployed; P01.5 E100 closure and retained natural observations are unchanged. Earlier review-only approval wording below is historical.

# P01.6 handover and scope: read-worker ownership and safe late results

**E100, 5 November 2026. Begin review/scope now.** The operator requests this handoff and a new chat after P01.5 closure. Produce the complete source-confirmed solution design and qualification plan. This authorizes read-only source/evidence review and scope/design documentation, not runtime implementation, PR publication/merge, deployment, restart, production probes/mutations or incident recovery. Do not ask again whether to begin review. Present any implementation decision only after the design is concrete and reviewable.

## Starting state and evidence

P01.5 is closed: private `24bca82f0a23721c1428bfe4f0db2e120d5b7c34` deployed through protected updater, release `96c6ffed-122d-4425-93e3-b2208e0920a4`, normal calendar pipeline and pinned-message edit accepted. P01.1/P01.2a/P01.3 remain accepted; P01.4 delivered with natural follow-ups. P01.2b proactive instrumentation remains declined/closed. No calendar stage or accepted business action needs replay.

Authoritative local closeout documents and uncommitted archive changes are in `C:/Users/cwatt/.codex/worktrees/p015-production/discord_file_downloader`, branch `codex/prod-p015-calendar-ownership`, base `7455cb28a68c99b7dfbed558417a980ccc3f00b1`. This base has the released merge tree but is not the private-main merge commit. Root mirror checkout `C:/discord_file_downloader` was clean at `7ba6c535c83e91a2a03d3620e836ccd27bf09f6d` when preparing this handoff. Recheck status/branch before work; do not reset either checkout or replace it from old artifacts. The new chat may read source in the suitable existing checkout but must carry the full current documentation delta, including both sides of archive moves, through the next authorized mirror PR/private promotion. Do not push private history to the mirror. No new worktree is requested.

The supplied recovery report is partial; amber SQL/Sheets observations are unknown, not failed checks. The startup configuration import completed after recovered 51400 contention. Neither fact certifies fresh export or clears retained incidents. Keep these limits and the active P01.4/P01.5 natural registers.

## Scope and current source confirmation

P01.6 owns the remaining **F24/B06 personal-read physical capacity and authorization-safe late results**. The programme P01 design already identifies this slice. In the inspected source, `player_self_service/stats_service.py` has an eight-slot `_DATA_SEMAPHORE`, nine-second `_DATA_TIMEOUT_SECONDS`, 30-second/32-entry cache, and per-user/sorted-governor `_INFLIGHT` key. `_fetch_dataset` holds the semaphore around `wait_for(to_thread(loader), 9s)`; `_authorized_dataset` shields that task but removes its identity when the timed task finishes. The final account fingerprint is rechecked before payload return. These are source observations, not a new real-thread reproduction or finished caller census.

The gap to verify: a timed-out awaitable may release its slot and inflight identity while its thread continues. A second same-key request may then start duplicate physical work. The change must retain ownership until actual read/cleanup settlement while keeping UI observation bounded and authorization independent.

| Boundary | Starting source | Review obligation |
| --- | --- | --- |
| Dataset ownership/cache | player_self_service/stats_service.py | Physical slot and exact inflight identity survive timeout/repeated cancellation; bounded admission, no duplicate same-key worker; cache publication independent of UI |
| SQL execution and cleanup | stats/dal/personal_stats_dal.py; player_self_service/accounts_dal.py and governor_dashboard_dal.py | Verify actual SQL objects, connection lifetime, cleanup/unknown-close behavior and helper call chain |
| Authorization | services/governor_account_service.py; stats_service registry/fingerprint checks | Revalidate current user/account access for late/cache results; no cross-user/account cache leak or stale callback authority |
| User entrypoints | commands/me_cmds.py; ui/views/player_self_service_stats_views.py | Early acknowledgement, private response, safe cancellation and meaningful pending/unavailable result; trace all equivalent callers |
| Physical helpers/shutdown | core/owned_work.py; current bot teardown/task registry and observation helpers | Reuse delivered ownership/drain mechanisms where suitable; avoid per-caller duplicate executors/registries and early drain |
| Adjacent readers/downloads | services/account_data_export_service.py; kvk/target_cache_repository.py; targets_sql_cache.py; stats_cache_helpers.py; stats_alerts/db.py | Follow directly related physical-worker/cleanup paths; classify complete caller coverage and dependencies without silently absorbing P02 fallback/budget work |

Confirm command/view/DAL/test filenames and all indirect callers before the final manifest. Do not apply a calendar mutation lock mechanically to independent read workloads.

## Design questions and expected outcome

1. Separate physical task lifetime, UI deadline, semaphore admission, inflight deduplication, cache publication, authorization and delivery. A caller timeout means observation ended, not SQL stopped.
2. Define ownership before executor submission, while queued, during read/close, after repeated cancellation and during shutdown. Retain exact object identity; stale callbacks must not remove a replacement task. Decide fail-closed behavior for unconfirmed cleanup without orphaning capacity or hanging teardown unobservably.
3. Preserve current compatibility unless evidence justifies a scoped change: eight physical reads, existing UI budget, cache key/TTL/count, immutable payloads, account fingerprint revalidation, authorization and private delivery. Decide when a late dataset may enter cache, when it may be reused, and when it must be discarded.
4. Bound both running and waiting work. Do not solve physical capacity with an unbounded task/waiter registry, retry loop, global executor replacement or extra permanent observer. Reuse the simplest existing helper that meets the actual contract.
5. Preserve business/read outcome independently from diagnostic, cache and Discord delivery failures. No late result may silently send a second response or gain authority from an old account selection.
6. Carry P01's known/unknown outcomes, original failure, later settlement, source/capture timestamps and evidence coverage through existing bounded report machinery. Diagnostics remain passive and best effort; required ownership/receipt checks do not become optional.

## SQL and persistence gate

Before implementation, inspect actual DAL queries and authoritative definitions in `C:/K98-bot-SQL-Server`; validate names, parameter/row shapes, permissions/factory selection and transaction/connection ownership. No table/procedure names or migration requirement are guessed here. Bot-only delivery is a hypothesis until source review completes. F26 connection fallback and shared producer budgets remain P02 unless a concrete prerequisite requires explicit scope reconciliation. Use uniquely named disposable local SQL databases on `localhost\K98DEV` for authorized qualification, never retained restores or production. No SQL experiment is authorized by this review-only handoff.

Read requests and UI/cache state are not durable cross-restart continuation authority. Do not invent exactly-once recovery guarantees or use diagnostic UUIDs as business receipts.

## Qualification plan to make concrete

| Case | Required proof |
| --- | --- |
| Normal/cache hit/miss and all entrypoints | Compatible payload/count/TTL and authorization; actual physical entry/completion observed |
| Real blocked loader exceeds UI deadline | Caller returns bounded pending/unavailable; slot/inflight remain owned; repeated same key does not create a second worker |
| Capacity and overlap | At most eight actual physical reads under many distinct/same-key requests; bounded queued state; both overlap orders |
| Cancellation before submission/while queued/during work/repeated | No leaked slot, early release, duplicate worker or unobserved exception; exact cleanup callback identity |
| Late success/failure/cleanup unknown | Truthful independent outcomes and intended cache policy; no stale authorization or extra response; ownership retained when physical close is unconfirmed |
| Registry/access change and privacy | Cache and late responses revalidate caller/account fingerprint; no cross-user or revoked-account disclosure |
| Shutdown/restart | Admission closes before drain; native thread completion and resource cleanup precede verified release; no forced release or invented resume |
| Optional diagnostics/delivery faults | Cannot turn read success into retry authority or change mandatory lifecycle controls |
| Cost and regression | Predeclared matched-control latency/loop-lag/retention/drain budgets; deliberate stall calibration; final artifact/report and adjacent caller regressions |

Starting tests: `tests/test_player_self_service_stats_service.py`, `test_personal_stats_dal.py`, `test_player_self_service_stats_views.py`, `test_me_cmds.py`, `test_account_data_export_service.py`; discover current owned-work/shutdown/cache/fallback suites. Real blocked-thread tests are required; raising TimeoutError alone does not prove physical ownership. Source review must determine native SQL qualification and the exact final test manifest. Keep failed/adverse results; do not relax gates after measurement. Qualify the final formatted/pinned artifact and user-visible result, not only helpers.

## Principles and lessons that must carry forward

- Review the whole affected solution, shared helpers and equivalent callers before implementation; fix tightly related durability issues in scope, capture unrelated debt structurally. Do not silently narrow scope to the first failing line.
- Preserve separate accepted/requested/completed/unknown business, cleanup, audit, cache and delivery facts. Unknown is not success, failure or zero. Optional telemetry cannot gate or erase business work; mandatory ownership and commit evidence remain mandatory.
- Async cancellation does not stop a native thread. No blind timeout retry, forced release, duplicate send or replay of committed work. Trace first failure and later settlement separately.
- Passive status/Refresh rereads evidence without provider probes, automatic log scans or new background observers. P01.2b was declined because measured cost/risk outweighed value; do not resurrect it through this slice.
- Reuse P01.1/P01.2a evidence and owned-work foundations, P01.3 passive health, P01.4 physical drains/optional isolation, and P01.5 adversarial concurrency/cost tests where appropriate. Do not duplicate calendar-specific policy for reads.
- Verify final ZIP/member bytes, late result rendering and exact immutable heads. Reviewer statements are hypotheses until checked against the actual runtime; the null-DACL concern was falsified by native .NET behavior. Keep test limitations explicit.
- Windows owner, ACL/inheritance, attributes, hashes, parent custody and prior handles are separate facts. Development access/elevation does not establish production custody. Never use blanket ownership/ACL changes or delete evidence to pass a guard.
- **Before every release handoff**, inventory the exact release delta and every existing source ancestor on the actual host, including docs/archive paths. Old scoped repairs and clean Git status are insufficient. Record code qualification, host readiness, installed release and functional acceptance separately. Use protected fresh replacements for required custody repair, retain originals and resume receipts, then normal updater preflight.
- Deploy only reviewed private main via protected updater; one graceful restart when directed. No live Git pull, manual task start, broad SQL/data repair or provider probe to make a dashboard green.
- Preserve originals, partial reports, adverse tests, known limitations and explicit package owners. No whole-programme closure from a successful slice or incomplete report.

## Boundaries and first deliverable

P02 retains F09/F20/F26, SQL holder attribution, contention prevention and shared factory/admission/cost policies. P03 retains original-intent durable continuation/unfinished-stage recovery and Rally F29. P04 retains notification journal F19, convergence/history/retention/escalation. P05 retains cross-package and repository-wide confirmation. P03a.2 fresh whole-flow acceptance and P01.4/P01.5 natural observations stay explicit. Calendar rules, reminder redesign, new stats features, dataset metric changes and generic framework rewrites are outside P01.6.

First deliverable: source-confirmed caller/SQL/resource matrix, exact failure reproduction plan or bounded offline reproduction, ownership/admission/authorization/cache model, before/after examples, cost/complexity tradeoffs, complete implementation/test manifest, related/deferred findings and qualification/release gates. Then request the implementation decision for that concrete design. Current work begins review without repeating the start question.

Read AGENTS and the seven core references, plus REVIEW_HELPERS.md, relevant player-self-service documentation, startup/shutdown/diagnostic contracts and Windows ownership/access contract. Use local_sql_development.md when SQL qualification applies. Current documentation changes have a precise prose-only security skip; future permissions/SQL/worker/shutdown changes require k98-security-review-routing and exact Bot/SQL Changes review as applicable, Deep off. Tests do not substitute for review. No broad security scan is inferred.

## Navigation

[P01.5 Closeout - 2026-11-05](archive/Startup%20Import%20Export%20Reliability%20-%20P01.5%20Closeout%20-%202026-11-05.md); [P01.5 Natural Acceptance - 2026-11-05](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Natural%20Acceptance%20-%202026-11-05.md); [P01.6 Chat Starter - 2026-11-05](Startup%20Import%20Export%20Reliability%20-%20P01.6%20Chat%20Starter%20-%202026-11-05.md); [Tracker - 2026-11-02](Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md); [P01 Design - 2026-11-03](Startup%20Import%20Export%20Reliability%20-%20P01%20Design%20-%202026-11-03.md); [Documentation Carry-forward - 2026-11-05](Startup%20Import%20Export%20Reliability%20-%20Documentation%20Carry-forward%20-%202026-11-05.md).
