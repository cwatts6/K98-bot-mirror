> **E97, 5 November 2026:** P01.5 local implementation is authorized and implemented; qualification is recorded in the [local implementation packet](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Local%20Implementation%20and%20Qualification%20-%202026-11-05.md). Shared physical ownership, one bounded scheduled intent, independent optional audit, truthful effect/cleanup/delivery facts and combined-load qualification supersede E96 pending-approval wording. No publication or production action is authorized by this checkpoint. Earlier dated evidence remains historical.

> **E96, 5 November 2026:** P01.5 source review and [whole-solution design](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Whole%20Solution%20Design%20-%202026-11-05.md) are complete for implementation approval. Current-body offline probes reproduce F23/F24/F25; 44 existing focused tests pass without covering the missing physical/effect boundaries. The operator reports no known external index consumers; retain the index compatibly. The packet specifies shared ownership, one bounded optional audit task, truthful outcomes, fixed cost/native qualification gates and the implementation manifest. No P01.5 runtime implementation or production action is approved or performed. E95 predecessor acceptance and all natural follow-ups remain unchanged.

# P01.5 handover and scope: calendar ownership and outcomes

**E95, 5 November 2026. Begin review/scope now.** The operator requested this handoff and a new chat to begin P01.5. Documentation and source review are authorized; P01.5 runtime implementation has not yet been approved. Produce the complete solution design and qualification plan before asking for the implementation decision. Do not ask again whether to begin the agreed review.

## Starting state and accepted predecessors

P01.4 delivered and deployed; locally qualified across the full scope; production acceptance confirmed for exercised paths, with remaining natural-activity checks tracked explicitly. Both optional workers are delivered; no second file/SQL implementation is pending. P01.1/P01.2a/P01.3 remain accepted. P01.2b is closed by decision without the instrumentation feature; do not resurrect it.

Root checkout was clean at entry, `main` at `8806f7e96bfb32624e10029668c992a5c04651e1`, the mirror sync from deployed private `e3508d122c384bfc750b0e80231554d0d93d8d75`. This handoff introduces intentional uncommitted documentation and archive moves. Inspect current state before work and preserve every change; do not reset or copy over the checkout from older artifact checkouts. SQL source is `C:/K98-bot-SQL-Server`; recheck its current HEAD/status and definitions before implementation. Local development databases must be uniquely named disposable databases on `localhost\K98DEV`; restored/retained databases and production are not scratch space.

## Scope summary and affected areas

P01.5 owns calendar F23/F24/F25: optional EventSyncLog failures must not rewrite acknowledged sync outcomes; cancellation/timeout must not release physical mutation ownership; successful primary cache publication must be distinguished from an auxiliary index failure. Apply one whole-solution model across direct, admin, startup and scheduled callers. This is not a calendar rules/reminder/board redesign.

| Boundary | Starting source/callers | Review obligation |
| --- | --- | --- |
| Full refresh and direct mutations | event_calendar/service.py: refresh, generate, publish_cache, refresh_pipeline, _run_stage_with_policy | One shared mutation owner, private already-owned stages, truthful independent outcomes, no reentrant lock or second execution. |
| Sheets input sync/audit | event_calendar/sheets_sync.py: sync_sheets_to_sql, _insert_sync_log_start, _finish_sync_log | Separate fetch/parse/upsert/commit from optional audit start/finish. Preserve acknowledged counts and unknown commit outcomes. |
| Generated instances | event_calendar/event_generator.py | Preserve transactional replacement and physical SQL connection ownership. |
| Primary/index publication | event_calendar/cache_publisher.py, runtime_cache.py, cache_contract.py | Preserve primary schema and empty-cache protection; examine type-index consumers and generation alignment. |
| Entrypoints | commands/admin_cmds.py calendar_refresh/calendar_generate/calendar_publish_cache; bot_instance.py _run_pinned_calendar_refresh_once; event_calendar/scheduler.py | Existing differently named outer locks are not a shared business owner. Trace actual caller cancellation and shutdown through service entry. |
| Shared lifecycle/observations | core/owned_work.py and existing operation observations, task/shutdown registration | Reuse tested ownership and bounded safe evidence; inspect all direct/indirect callers before choosing changes. |

The handoff checked current source locations: audit start precedes sync's business block; completion logging follows commit; service stages use to_thread and wait_for; callers use distinct operation-lock names; cache publisher writes primary and type index separately. This is scoped source confirmation, not a completed P01.5 caller census or fresh reproduction. The new chat must validate the full paths and existing safeguards before finalizing design.

## Architecture direction and decisions to settle

1. Keep orchestration and shared mutation ownership in CalendarService, SQL in calendar data-access code, and Discord acknowledgement/rendering in commands. Preserve useful outer debounce behavior while ensuring direct callers cannot bypass the shared owner. A pipeline invokes already-owned stages instead of reacquiring its own lock.
2. Bind physical ownership at actual thread entry and retain it through observer timeout, repeated cancellation, cleanup and late completion. Preserve no-timeout-retry (`allow_timeout_retry=False`); review result-based retries as well, so uncertain commit/entered work cannot become replay authority. Define whether shutdown permits remaining stages versus closes admission, and how late stage facts are retained.
3. EventSyncLog is optional telemetry, not a commit receipt. Acknowledged sync survives audit failure with actual counts; continuation follows the existing intended pipeline only when allowed by lifecycle state. Lost commit acknowledgement stays unknown. Do not invent SQL IDs or claim exactly-once restart continuation without an atomic per-run business receipt.
4. Treat primary JSON and auxiliary type index as distinct effects. Retain compatible index writing until all installed/manual consumers are checked. Prior census found no Python consumer; that is not proof of no external consumer. A consumer requiring atomic pairing is a design gate: review versioned-generation/pointer options before claiming F25 complete. Do not silently remove the index or pretend two replacements are atomic.
5. Prefer simple existing helpers. Do not add another audit worker, queue, lock hierarchy or retry spool merely because P01.4 has one. Quantify optional audit blocking/cost and decide its mechanism from evidence. Bound every new queue/context/projection and preserve mandatory receipts and business-history priority.
6. Design the complete solution first. Delivery may later use one or two deployments only if exact contracts/compatibility allow both without duplicate architecture or avoidable rework. Present value, cost, failure boundaries and what each candidate would and would not qualify.

## SQL / persistence review

Authoritative source objects to inspect: `sql_schema/dbo.EventSyncLog.Table.sql`, `dbo.EventRecurringRules.Table.sql`, `dbo.EventOneOffEvents.Table.sql`, `dbo.EventOverrides.Table.sql`, `dbo.EventInstances.Table.sql` in the SQL repository. EventSyncLog source checked for this handoff has identity SyncID, start/completion UTC, source, status, read/upsert/generated counts and error text; it has no operation/actor/atomic business-commit receipt column. Validate all parameters, constraints, transaction/connection lifetimes and query shapes against actual SQL before coding. The design presently anticipates Bot-only changes, not a promise that no SQL change can be needed. Any new durable receipt requires an explicit SQL design and separate review/deployment order.

Calendar input commit, generated-instance commit, primary file replace, auxiliary file replace and notification are separate boundaries. No diagnostic UUID, status card, reservation release or missing audit row establishes a business commit or rollback. Preserve source identifiers, first failure and later settlement; temporary files and local tasks are not durable recovery authority.

## Qualification plan to make concrete

| Cases | Required evidence |
| --- | --- |
| Normal full pipeline and each direct/admin/startup/scheduled entry | Same business counts and intended stage order, one owner/entry, actual final user result and persisted effects. |
| Audit start/finish failure before/after acknowledged commit | Business result unchanged; optional failure explicit; no false zero counts, failed-fetch label or replay to repair logging. |
| SQL failure / lost commit acknowledgement | Correct failed versus unknown outcome, no unsafe continuation/retry, connection ownership retained until physical settlement. |
| Deadline, repeated cancellation, both overlap orders | Real blocked thread remains owned; competing generate/publish/refresh cannot overlap; no reentrant deadlock or early drain. |
| Primary success/index failure; index consumer requirement | Primary success survives auxiliary failure; old/new generation distinction; preserve empty protection and schema. Escalate atomic-pair requirement before implementation. |
| Telemetry/clock/report/notification failure | Cannot replace authoritative stage outcome or create a second execution. Final reports/ZIP and rendered messages reflect independent dimensions and partial coverage. |
| Resource and cost qualification | Predeclare latency/loop-lag, lock-hold, retention and drain budgets; calibrated equal-window controls and deliberate stall detection; no threshold relaxation after failure. |
| Restart/late settlement | Correct shutdown admission, task/worker ownership, truthful historical evidence; no fabricated exactly-once resume guarantee. |

Starting tests: tests/test_calendar_pipeline.py, test_calendar_service.py, test_sheets_sync_flow.py, test_calendar_publish_cache.py, test_admin_calendar_commands_task3.py, test_calendar_scheduler.py, test_calendar_runtime_cache.py, test_event_generator.py, test_calendar_service_telemetry_task3.py (resolve each under tests and discover additional current tests). Cover shared helper callers when altered. Native SQL cases use disposable local databases, actual methods and verified cleanup, with offline provider/Discord boundaries. No production fault injection, probe or artificial upload is part of qualification.

Before an eventual PR: appropriate focused/full tests, operational-log hygiene, Black/Ruff/type checks, architecture/deferred/security-routing validators, explicit-path test selection, smoke/registration when affected, final immutable-head review/CI and exact updater compatibility. Freeze canonical formatting before source pins. A focused green suite is not a substitute for the complete caller/concurrency/restart review or P05 confirmation.

## Learnings and principles to preserve

- Required business receipts, journals, hashes, manifests and ownership are distinct from optional audit, diagnostics, backup/refresh requests and notifications. Accepted/requested is not completed; unknown is not zero or healthy.
- Observation is passive. P01.3 status/Refresh rereads retained evidence, without provider probes or new background observers. Preserve 60-minute provider freshness and separate recovery-monitor progress/completed-cycle rules; no automatic log scans or whole-bot detector were adopted.
- P01.2b's observer changed child exit 37 to 120; the replacement cost 3,443.3 ms cold attach against 500 ms and about 496 ms setup p95 against 50 ms. Keep that declined feature closed. Evidence improvements must be proportionate and incident-driven.
- Physical thread/connection/file ownership outlives asyncio cancellation. Close admission before independent drains; preserve ownership on uncertain close. Do not force-kill/release to make the dashboard green.
- Evaluate the whole solution and equivalent callers before slicing. P01.4 included manual Location, staged callback custody and duplicate admission/CSV, not only the first observed route.
- Retain adverse experiments. Timer-source variance can invalidate a benchmark; calibrate wake lateness and event-loop delivery under equal windows, retain failed runs and keep budgets unchanged. An injected close wrapper is not a natural driver failure.
- Test the final artifact and user-visible result: P01.3's collector passed while the delivered ZIP omitted a member; P01.4's worker summary was stale until actual settlement. Verify member hashes/sizes and late summary transitions, not just helper success.
- First failure, latest outcome, source/capture age, coverage/loss and continuation have separate meanings. Optional storms must not displace authoritative business history. Report 76's partial history does not resolve all incidents.
- Persistent interactions acknowledge early, retain actor/context binding and exact message identity, and distinguish refused/deleted from uncertain send. Unknown delivery never authorizes duplicate sends.
- Reviews are evidence, not votes: reproduce findings against the exact code/runtime; retain service limitations honestly. Separate immutable mirror/private heads, historical pins and private-only files. Deploy only reviewed private main via protected updater.
- Capture related durability corrections within scope; record unrelated work structurally. No broad cleanup, hidden deferral, retesting accepted production actions, or reopening settled decisions without new evidence.

## Boundaries, refactor triggers and first deliverable

Fix-now candidates after approval: shared service ownership, truthful stage/audit/index classification and directly related telemetry/cancellation bugs. Assess touched SQL placement/helper duplication/stale tests; extract only where justified. F20 shared file-lock cleanup and F26 connection fallback belong to P02 unless a concrete dependency blocks P01.5 and the scope is explicitly reconciled. P01.6 owns personal-read capacity. P02 owns contention/holder evidence, maintenance and F09; P03 owns original-intent durable continuation and Rally F29; P04 owns notification-journal F19 and broader convergence/history; P05 final repository-wide confirmation remains mandatory. P03a.1 recovery must not be replayed; P03a.2 fresh whole-flow acceptance remains open. Calendar event-rule/reminder/board changes stay in their separate P1 scope.

The updater CLI per-blob performance issue found during P01.4 is a separate deferred tooling item, not missing P01.4 work or an implicit P01.5 addition.

Read the current core standards plus events_and_dm_reminders.md, REVIEW_HELPERS.md and applicable startup/shutdown/diagnostic contracts. If protected files/updater paths are touched, read the Windows ownership/access contract; if SQL qualification is planned, read local_sql_development.md. Follow current AGENTS and applicable skills rather than historical archive instructions.

Security decision: this handoff/closeout is Markdown-only and has a documented skip. Future P01.5 runtime changes touch SQL, files, network, interactions and shutdown and require k98-security-review-routing, normally separate exact Bot/SQL Changes targets where changed, Deep off. Do not substitute tests for review or infer a broad repository scan.

First deliverable: a source-confirmed whole-solution packet with caller matrix, authoritative SQL checks, stage/ownership/commit model, before/after examples, index-consumer disposition, cost/risk evidence, concrete test gates, related/deferred findings, exact implementation manifest and delivery options. Make unresolved decisions explicit and obtain implementation approval for that concrete design. The present request authorizes starting review, not implementation, publication, merge, deployment, restart, production mutation or incident recovery.

## Required carry-forward

Read [P01.4 closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.4%20Closeout%20-%202026-11-05.md), [natural acceptance register](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Natural%20Acceptance%20-%202026-11-05.md), [P01 design](Startup%20Import%20Export%20Reliability%20-%20P01%20Design%20-%202026-11-03.md), [tracker](Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md) and [documentation manifest](Startup%20Import%20Export%20Reliability%20-%20Documentation%20Carry-forward%20-%202026-11-05.md). Preserve every listed destination and both sides of all archive moves in the next appropriate authorized reliability PR/private promotion. No extra deployment is required solely for documentation.
