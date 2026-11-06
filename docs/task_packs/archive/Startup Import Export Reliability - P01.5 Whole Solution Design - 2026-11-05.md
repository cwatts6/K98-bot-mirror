> **Archived at E100, 5 November 2026.** Delivered or superseded P01.5 record. Preserve the dated evidence below; earlier next-action/approval statements are historical. Current authority: [P01.5 closeout](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Closeout%20-%202026-11-05.md) and [P01.6 handover](../Startup%20Import%20Export%20Reliability%20-%20P01.6%20Handover%20and%20Scope%20-%202026-11-05.md).

# P01.5 calendar ownership and outcomes: whole-solution design

> **E97 local implementation amendment, 5 November 2026:** The operator accepted the additional design thinking and asked to begin local implementation and qualification. The following requirements refine E96 before coding. Local implementation/qualification proceeds; publication, merge, production promotion/deployment/restart, live provider/Discord calls and incident repair remain outside this work.
>
> **Scheduled busy handling:** admin/direct requests still receive an immediate truthful busy result. Startup/daily/interval callers may retain one shared deferred scheduled intent, with no new worker, timer or unbounded queue. The existing scheduled caller waits for the current physical owner, then revalidates admission and executes its own new refresh once. Additional scheduled requests receive an explicit already-deferred/not-admitted result. Shutdown/cancellation discards a deferred intent before physical entry; unconfirmed cleanup refuses it. Pending intent is visible in passive status. This supersedes E96's blanket zero-deferred-scheduled-work policy; capacity is one active mutation plus at most one scheduled waiter.
>
> **Combined-load qualification:** Q08–Q11 must additionally exercise calendar work beside the actual P01.4 optional file/SQL machinery and representative blocked read work, with equivalent controls. A separate audit task removes direct dependency but does not prove absence of shared executor, SQL, CPU or disk contention. Preserve existing workers' outcomes, bounds, history priority and drain behavior.
>
> **Unconfirmed cleanup:** status must separately show acknowledged business effects, the unresolved physical connection cleanup, refused subsequent work and remaining stages. It must explain that timeout, age, missing audit or an apparent idle thread cannot release ownership. Retain the exact local owner/error classification; no automatic retry/release or incident-repair API is added. Native qualification uses only a newly created `K98_P015_Disposable_20261105_01a1acb4` on `localhost\\K98DEV`, after exact new-target verification; retained databases are excluded.

**E96 historical review baseline, 5 November 2026; E97 authorizes local implementation and qualification.** This packet covers F23/F24/F25 together. It proposes Bot changes and local qualification, not publication, merge, deployment, restart, live provider calls or incident repair. No runtime, test-suite, configuration or SQL source was changed during this review.

Read with the [handover](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Handover%20and%20Scope%20-%202026-11-05.md), [P01 design](../Startup%20Import%20Export%20Reliability%20-%20P01%20Design%20-%202026-11-03.md), [tracker](../Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md), [carry-forward manifest](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Delivered%20Documentation%20Carry-forward%20-%202026-11-05.md) and [P01.4 natural acceptance](../Startup%20Import%20Export%20Reliability%20-%20P01.4%20Natural%20Acceptance%20-%202026-11-05.md).

## Scope summary and recommendation

E97 authorizes one complete local implementation and qualification of:

1. One calendar mutation owner shared by full refresh, direct sync, generation and publication. Retain it until physical work and connection/file cleanup settle, including repeated cancellation. Pipelines invoke private already-owned stages.
2. Independent optional EventSyncLog start/finish, with one bounded audit task and no queue or retry spool. Audit admission, SQL work, reporting and failure never gate business execution. Reuse the existing owned-work helpers; do not add a permanent audit worker or modify the delivered upload workers.
3. Separate input commit, generated-instance commit, primary cache replacement, index replacement, cleanup and response outcomes. Preserve acknowledged counts and unknown outcomes. Remove generic result/exception mutation retries.
4. Complete caller, shutdown, status, report and qualification coverage before choosing a release. Recommended eventual delivery is one complete Bot release, after the ordinary review and promotion gates.

The explicitly approved E97 behavior changes are cross-command busy refusal instead of waiting in different caller locks; observer deadlines that retain and observe the original work; asynchronous best-effort audit completion; truthful nullable unknown counts; and warning output for auxiliary failure after primary success. Event rules, scheduling times, horizons, empty-cache protection, permissions and cache schemas stay compatible.

## Evidence and limits

| Evidence | Current result |
| --- | --- |
| Bot source | Local main `8806f7e96bfb32624e10029668c992a5c04651e1`. The inherited Markdown changes and archive moves were present. Entry manifest records 42 Git paths, including removals; no source reset or checkout replacement. |
| SQL authority | Clean local `C:/K98-bot-SQL-Server` at `b1eeb8e894fec380c7a6d6c5cc5bbfd9dbc3470c`. All five calendar table definitions inspected. All three Python upsert column allowlists match source definitions. This is source alignment, not installed-schema verification. |
| F23 current-body probes | Synthetic audit-start failure prevents all three fetches. Synthetic finish failure after one acknowledged business commit returns `failed_fetch_or_validate`, zero counts, and attempts another failure audit write. |
| F24 current-body probe | Actual blocked thread entered; 30 ms observer timeout exits the caller lock; the same lock is reacquired while the thread remains blocked. The original thread is explicitly released and joined by the probe. |
| F25 current-body probe | Primary-write adapter is invoked successfully; index adapter fails; current result is `failed_publish`, `events_written=0`. No actual calendar files are written by this probe. |
| Existing regression baseline | Nine handoff suites: **44 passed in 22.61 s**. This establishes current tests pass, not that defects are fixed. |
| Index census | Repository-wide non-test search in both repositories finds the constant, publisher and documentation, but no application reader. `runtime_cache.list_event_types()` derives values from primary events. Operator states **“No known consumers outside the bot.”** |
| Connection semantics | Installed development pyodbc 5.3.0 documents `Connection.__exit__` as committing if necessary and `close()` as explicit closure rather than waiting for destruction. Calendar source has no explicit connection close. This is not proof of a currently leaked production connection; native cleanup qualification is required. |

Private evidence is under `.codex_artifacts/p015-review-20261105/`: `entry-manifest.json`, `reproduce.py`, `reproduction-results.json`, `sql-source-check.json` and the final documentation validation receipt. Probes compile selected unchanged AST bodies with inert SQL/provider/file boundaries; they are not a candidate implementation or native SQL rehearsal. No production inspection was performed. Cost thresholds below are proposed acceptance gates, not measured candidate results.

P01.4 remains delivered and deployed, locally qualified across its full scope, with production acceptance confirmed for exercised paths and remaining natural checks explicitly tracked. Private e3508d12, Activity 585 and Location 347 are carried evidence, not newly reverified here. Both upload workers are delivered. P01.2b stays closed without feature delivery.

## Current caller and ownership matrix

Line references below are to the pinned Bot source; re-resolve them after implementation.

| Entry or boundary | Current route and ownership | Required behavior |
| --- | --- | --- |
| `/ops calendar_refresh` | `commands/admin_cmds.py:1583`, admin/channel decorators, early ephemeral defer; outer `calendar_refresh` lock; service pipeline | Preserve authorization/defer. Service owns admission and mutations; render business, observer, audit and index separately. No replay from a failed response. |
| `/ops calendar_generate` | `commands/admin_cmds.py:1659`; distinct `calendar_generate` lock; direct service generation | Same shared owner as refresh/publish. Preserve 1–1825-day command bounds. |
| `/ops calendar_publish_cache` | `commands/admin_cmds.py:1711`; distinct `calendar_publish_cache` lock; direct publication | Same shared owner; preserve explicit `force_empty`. Primary success survives index failure. |
| Startup pinned refresh | `bot_instance.py:167,213`; `calendar_refresh` lock; full pipeline, then `update_calendar_embed` only if pipeline `ok` | Preserve immediate boot pass and configured-channel guard. A primary-success warning still permits the existing pinned-update intent if lifecycle permits. Delivery is a separate result. |
| Daily pinned refresh | Same helper, `scheduler_pinned_daily`, 08:05 UTC | Same owner and cancellation rules; no change to schedule. |
| Registration | `core/scheduler_lifecycle.py:333` registers `daily_pinned_calendar_refresh` after pinned rehydration; `bot_instance.py:493` supervises it | Preserve task identity and duplicate registration protection. Service admission blocks late task entries during drain. |
| Interval scheduler API | `event_calendar/scheduler.py:16`; `calendar_refresh` lock; default 900 s; no outer wait_for | No non-test registration callsite found. Cover the callable without enabling another scheduler. |
| Direct service API | `CalendarService.refresh`, `generate`, `publish_cache`, `refresh_pipeline`, `refresh_full` | Every public mutator enters the shared owner; `refresh_full` remains a pipeline alias with no second admission. Separate service instances must not create independent production owners. |
| SQL/file functions | `sync_sheets_to_sql`, `generate_calendar_instances`, `publish_event_calendar_cache` are passed to `to_thread` by service | No additional non-test direct callers found. Treat these as internal execution boundaries, not independently schedulable application entrypoints. Tests may invoke them with isolated factories. |
| Status/read consumers | `calendar_status`, runtime cache, commands/views/reminders/pinned presentation | Passive reads do not join the mutation owner or query providers. Snapshot claims must identify a single run and generation. Existing reader/reminder behavior remains compatible. |
| Shutdown | `_graceful_teardown` closes several other admissions before `TaskMonitor.stop`; calendar has no service drain | Close calendar business and audit admission before the first teardown await. Drain registered calendar work before task-monitor/client/diagnostic shutdown. |

The three outer operation-lock names are not a shared physical owner. Remove their calendar-specific use once service admission is in place, rather than retaining unbounded hidden waiters outside the service. Other users of `get_operation_lock` are unchanged. Competing direct requests receive `busy/not_admitted` with the current run reference. E97 scheduled callers may retain one waiting intent, revalidate admission and start one new refresh after settlement; all further scheduled requests are refused. This is not replay of the previous run.

## SQL and persistence review

**Verdict: existing definitions support a Bot-only design; not a deployment verdict.** No table, procedure, index, UDT, ProcConfig, permission or migration change is proposed. Searches find no calendar procedure/trigger consumer of EventSyncLog in the SQL source. Installed objects and manually maintained jobs are not independently inventoried.

| Object | Verified contract and execution |
| --- | --- |
| `dbo.EventRecurringRules` | `RuleID nvarchar(128)` PK; active/all-day bits; required title/type/recurrence/first-start/duration; optional interval/end/max-occurrences and content; `SourceRowHash varbinary(32)`; created/modified defaults. Sync selects hash by key, then parameterized insert/update. Generator reads active rules. |
| `dbo.EventOneOffEvents` | `EventID nvarchar(128)` PK; required start/end with `EndUTC > StartUTC`; compatible content/hash/default columns. Same hash upsert; generator reads active rows. |
| `dbo.EventOverrides` | `OverrideID nvarchar(128)` PK; `TargetKind` constrained to rule/oneoff/instance; `ActionType` cancel/modify; optional replacement fields with conditional end-after-start check. Generator maps rule to recurring source kind. |
| `dbo.EventInstances` | `InstanceID bigint IDENTITY` PK; `SourceKind` recurring/oneoff; source ID, datetime2(0) times, content, cancellation, GeneratedUTC, EffectiveHash. Indexes on EventType, SourceID and StartUTC. Generator preserves matching identities by EffectiveHash, deletes/reinserts transactionally and uses IDENTITY_INSERT for preserved IDs. Publication reads noncancelled instances in the selected horizon with deterministic ordering. |
| `dbo.EventSyncLog` | `SyncID bigint IDENTITY`; started/completed datetime2(0), SourceName nvarchar(64), Status nvarchar(32), nullable integer read/upsert/generated counts, ErrorMessage nvarchar(max). Start returns OUTPUT INSERTED.SyncID; finish updates exactly that ID. There is no atomic business receipt, operation ID or actor column. |

All referenced select/insert/update columns were compared with these definitions, including implicit ModifiedUTC updates and identity-preserving inserts. Business SQL retains existing parameterization and identifier allowlists. No new SQL identifier is derived from user input. Optional audit errors are bounded/redacted before storage or display, despite the SQL max-length column.

Input upserts form one transaction; generated-instance replacement is a second. Primary and index file replacements and Discord delivery are later independent effects. None is one distributed transaction. Counts before commit acknowledgement are attempted counts, not confirmed writes. Lost commit acknowledgement remains unknown even if a subsequent rollback succeeds: rollback cannot undo a transaction already committed by the server.

Add a small calendar-local connection lifetime adapter, reused by sync, generation, publication and audit. It preserves the supplied factory, captures commit acknowledgement immediately, explicitly rolls back uncommitted work where possible, closes cursors and connections on the same worker thread, and records cleanup independently. It must not raise away an acknowledged business result because close later fails. Retain a strong reference to a connection whose close is unconfirmed; business owner enters `cleanup_unconfirmed` and refuses new mutations until authoritative settlement, rather than claiming a clean drain. No timed force-release or automatic reconnect-and-replay.

Avoid relying on pyodbc `with connection` as both transaction and close authority. In particular, an exception after a successful explicit commit or during context exit must not erase that acknowledgement. Preserve original error class/SQLSTATE/native code and subsequent rollback/close outcomes separately. Do not introduce a second commit through context-manager exit. Native tests must inspect actual rows and session closure; fake context managers cannot prove this contract.

The calendar-local adapter does not alter `file_utils.get_conn_with_retries`, producer connection routing, F26 fallback policy, or all DAL callers. Audit uses an independent connection created directly by the existing configured SQL-login factory `_conn`, not a borrowed producer session or the upload worker's Windows-authentication factory. This is an explicit audit connection choice, never fallback after another principal fails. No new credential, permission or plaintext connection logging is required. Validate this distinction in native qualification.

## Ownership, deadlines, cancellation and retry contract

### Admission and physical execution

Use one service-owned admission record for the Bot's event loop, shared across public calendar service instances. Admission/check/register is synchronous with no intervening await: one active operation plus at most one scheduled waiter under E97; direct mutations are never queued. A full pipeline owns the record from before sync submission through its last entered physical stage and cleanup. Generate and publish use the same record. Private stage functions accept only the current operation context and never reacquire admission.

Create one retained operation task per accepted mutation; observer lifetime is separate. Record `admitted`, executor `submitted`, actual thread `entered`, effect acknowledgement and physical settlement distinctly. Reuse `core.owned_work.drain_thread` at each real blocking boundary and `drain_awaitable` for joins. The generic helper does not interpret commits and does not automatically retain a domain dataclass for the service; an uncancelled service stage task must capture its returned structured outcome before releasing ownership.

Do not use `CoalescedWork` for these mutations: its documented purpose is replaceable reads/presentation and it intentionally performs another pass when a request arrives during execution. Do not use per-stage locks or a nested caller/service lock hierarchy.

### Deadline versus cancellation

Keep the configured 60/90/60-second stage observation budgets and `allow_timeout_retry=False`. Use non-cancelling observation of the retained stage task. Deadline expiry records `deadline_elapsed/physical_pending`, with current effects unknown where appropriate. The original task continues once. Default service calls continue waiting for settlement and may finish the original pipeline after a deadline while admission remains open; the passive status view can show the delay. No second execution is scheduled to satisfy a timeout.

An actual caller cancellation sets the operation's stop-after-current-stage flag, then joins the original owner through repeated cancellation. The currently entered worker drains; late commit/count/cleanup facts are saved; no later business stage starts. Propagate cancellation only after settlement, preserving the final snapshot for status. Cancellation before thread entry may prevent that stage only if the worker entry gate positively observes the stop flag; submission alone is not proof it did not enter.

Shutdown closes business and audit admission before any unrelated drain await, sets the same stop-after-current-stage flag and drains accepted work. It may complete cleanup and an already-admitted audit's terminal write; it does not start the next sync/generate/publish business stage. Use an idempotent retained shutdown task so repeated cancellation of the teardown observer cannot abandon the join. An unconfirmed close is a failed/incomplete drain, not success through `gather(return_exceptions=True)`.

The returned service result can arrive after the Discord interaction expires. This is an explicitly retained limitation: a response failure is independent of business success, does not resubmit work and leaves the outcome available through passive status. This proposal does not add automatic late-message sends or a new notification worker.

### Retry authority

Remove generic mutation retries driven by `failed_service`, `timeout`, arbitrary exception class, or telemetry failure. Current `_result_retryable` and the generic exception retry branch cannot distinguish pre-entry failure from a lost acknowledgement. Existing retry config remains parse-compatible, but must not authorize a second entered mutation; document this semantic restriction rather than silently promising configured retries.

Retain safe internal GET fetch retries and existing connection-acquisition policy only where no business SQL has been invoked. The owner remains held while those finish. A deterministic parse/validation failure does not retry; an unknown commit, entered SQL failure, partial publication, index failure or delivery error never retries the whole stage. No new replay/recovery API is introduced. If future mutation retry is needed, it requires explicit proof of no effects, completed rollback/cleanup and a separately reviewed predicate.

## Optional EventSyncLog design and cost decision

### Selected mechanism: one task, no backlog

Service orchestration offers an audit at sync admission. A calendar-local audit owner accepts at most **one** active context; otherwise it returns `audit_skipped_busy` immediately. Its task performs the existing start insert through `drain_thread`, closes that connection, waits asynchronously for the immutable business result, then attempts the existing finish update once on a new connection. It never holds a SQL connection or executor thread while waiting for the sync result. Business fetch/parse/upsert runs independently and never awaits start/finish.

Bind a finish only after the exact returned SyncID and start commit acknowledgement are known. Start failure or lost acknowledgement suppresses finish; do not query latest rows, invent an ID, rebind, retry start or create a replacement row. Finish failure retains the acknowledged business result and the first audit failure. If business finishes before start, retain one bounded result until that same start settles. If admission is closed or busy, record loss without creating a task.

Keep SourceName and running/success status meanings compatible; add only bounded failure/unknown classifications fitting nvarchar(32), with nullable counts. `InstancesGenerated` remains the sync-stage value, not a claim that later generation ran. A started row may remain running after a crash or lost finish; document this as incomplete optional telemetry, not an active-worker or failed-commit proof. Record captured sync timestamps rather than delayed audit-write time where the existing columns permit it.

Audit close failure retains its single slot and connection reference and prevents further audit admission, but cannot seize the calendar business owner. Global graceful drain must still disclose that optional physical cleanup is unconfirmed. Accepted audit completion may finish during shutdown using its original context; new audit offers are rejected. There is no durable spool or restart replay and therefore no guaranteed audit delivery.

### Why this choice

Current normal full refresh uses five connection acquisitions: two for audit, one for input upserts, one for generation and one for publication. Audit is 40% of these acquisitions and both are on the critical path. Default audit connection retries alone allow five 5-second login attempts plus backoff ceilings of 1+2+4+8 seconds: about **40 seconds nominal budget per acquisition**, before SQL execution/commit/cleanup. Query and close are not hard-bounded by the current calendar code. This arithmetic is a configuration envelope, not a measured production duration or universal driver guarantee.

Wrapping audit in try/except fixes classification but leaves those stalls ahead of business progress. A new permanent worker/queue or an extension of the import-audit worker adds coupling, queue/drain policy and context handling that this low-concurrency flow does not need. The selected task preserves start/finish compatibility using existing executor/drain machinery, with one extra concurrent offload at most and unchanged successful SQL statement/connection counts. It must be measured, not presumed cheap.

Audit uses one connection attempt, existing 5-second login timeout, connection-level 2-second statement timeout before cursor creation and a 250 ms lock timeout on its private session. These limit ordinary faults, not arbitrary driver/OS hangs or a guaranteed commit/close duration. Never return the audit slot while its physical thread remains active. This is fault containment, not a hard real-time promise.

## Primary cache and auxiliary index outcomes

Keep `event_calendar_cache.json` and `event_type_index.json` at their current paths and retain their payload schemas. The operator's no-known-external-consumer answer plus source census supports treating the index as auxiliary. Removal and atomic-pair publication are **not** part of this design. The local runbook's manual validation of both files is a known operational use and will be updated to inspect their separate outcomes.

Build and validate primary payload, apply existing empty-cache protection, then replace primary and immediately freeze its success/count/generation. Build and replace the index in a separate guarded effect boundary; index construction failure must not prevent primary publication. Preserve old index bytes on failure. A successful primary with failed index returns business success with warning and the actual published count. Do not roll back primary or rerun SQL/generation to repair the index.

Use `file_utils.atomic_json_write` with explicit compatibility arguments: `ensure_ascii=True`, `sort_keys=False`, `default=None`, and `replace_retries=1` to preserve current serialization and no-new-retry behavior. This removes the publisher's duplicate writer and supplies invocation-owned temporary-file cleanup on handled failure. Hard-crash temporary files remain non-authoritative. Failure before replacement preserves the previous target; successful return from replacement is the primary acknowledgement. Tests compare exact bytes and both surviving files, not merely helper calls.

Use the existing generated_utc in each file as descriptive generation evidence, not a unique transaction token. Track primary `new/preserved/unknown` and index `same_payload/old_or_unknown/not_attempted` from this invocation's actual writes; never assert a prior index generation without reading evidence. Empty preservation keeps both files untouched and must not claim a new cache generation. No additional full-file readback is needed on the normal publish path solely for diagnostics.

If a later identified consumer requires an atomic pair, stop F25 closure and review immutable generation files plus one atomic pointer, consumer migration, retention and rollback before changing the contract. Two successful os.replace calls are never described as atomic together.

## Outcome model and user-visible examples

Retain existing dictionary entrypoints as adapters, with a versioned bounded per-run snapshot. `ok` means requested business effects acknowledged (or the established explicit empty-preserve policy); it does not mean all optional evidence or delivery succeeded. `severity` separately exposes warning, pending and failure. No formatter uses `int(value or 0)` for unknown counts.

Each run records observer state; physical stage entry/settlement; sync and generation commit state; primary and index states; attempted versus confirmed counts; cleanup; audit; remaining stages; first failure and latest settlement. Stage states distinguish not_started, not_admitted, running, committed, rolled_back, failed_before_effects and unknown. Unknown counts are null with a reason. Cleanup failure cannot rewrite committed to failed; it can stop continuation and admission.

| Scenario | Current result | Proposed result |
| --- | --- | --- |
| Audit start denied | Sync never fetches; service failure may retry | Business executes once; audit unavailable; genuine counts and continuation preserved. |
| Input commit succeeds, finish audit fails | Failed-fetch/validate, zero counts, generation skipped | Sync committed with actual counts; audit warning; original generation/publication proceeds while lifecycle permits. |
| Commit reply lost | Generic failed-fetch/validate or failed-generate | Commit unknown; attempted counts retained separately; later business stages not started; no automatic retry. |
| Deadline during real SQL work | Caller releases lock; worker still active | Deadline observed, original owner retained; competitors refused; late result captured; no timeout retry. |
| Repeated cancellation during generation | Awaiter can disappear while SQL continues | Original physical generation drains; commit/cleanup captured; publication not started; cancellation propagates afterward. |
| Primary writes 12 events, index fails | Failed publication, zero events | Primary committed, 12 events, index warning; normal pinned-update intent remains eligible. |
| Empty source with existing cache | Accepted preserve policy | Same policy, zero newly written events, preserved generation explicitly distinct from a fresh publish. |
| Pinned edit or admin response fails | Broad caller failure logging | Business result remains; delivery failed/unknown as supported by actual evidence; no cache or SQL replay. |
| Independent direct sync/generate/publish calls | Health can synthesize full pipeline success from three unrelated successes | Full-pipeline success timestamp comes only from one complete run; direct-stage timestamps remain separate. |

The last row is a source-confirmed related correction in `CalendarService._calendar_health`: it currently combines unrelated `_last_*` flags. Likewise, it currently looks for horizon in `meta` while the actual cache contract puts `horizon_days` at the top level. Correct these touched status projections and tests without changing cache schema or freshness policy.

## Diagnostics and reporting

Reuse `core.operation_evidence`, `operation_timing` and the existing bounded diagnostic sink. Add narrow calendar stage labels and fixed primitive outcome fields to the producer **and** sink validation/projection allowlists together. No raw Sheets content, SQL strings, connection strings or arbitrary exception payloads. Diagnostic IDs correlate observations only; they are not receipts.

Keep a bounded latest service snapshot (one active plus the existing latest per-operation summaries); copy returned dictionaries so callers cannot mutate retained facts. Optional audit has one context, one pending terminal result, at most 8 KiB total serialized content, bounded error text and saturating loss counters. Preserve first error alongside later success. Optional audit state must update after physical settlement, including when no further operation occurs.

Calendar business boundary observations remain in the existing bounded operation history. Optional audit summaries must use a separate bounded optional slot, adapting the existing optional-observation mechanism where suitable, rather than generating an unbounded series of business-history entries. At most one retained calendar audit summary plus counters; full/busy/disabled sinks cannot block service outcomes. Native SQL audit and diagnostic retention are independent.

The current telemetry helper already catches ordinary emission exceptions; no live throwing telemetry incident is asserted. Nevertheless, current service try blocks include post-effect rendering/timing/telemetry and generic retry classification. Qualification must inject failures at these boundaries and prove they cannot discard an outcome or cause a second execution. Reuse safe clock/optional helpers for diagnostics; a missing clock yields unavailable timing, not a failed commit. Required business timestamps or validation failures before execution still fail normally.

Verify passive status, ordinary recovery report and downloaded ZIP. Inspect actual serialized fields, schema acceptance, hashes/sizes, first-failure/late-settlement transitions and missing/partial coverage. Do not infer artifact parity from collector unit tests. P01.3's provider freshness and passive status rules are unchanged.

## Qualification plan and fixed cost gates

These gates are declared before implementation. Do not relax a failing threshold or discard adverse runs. Candidate measurements and native execution are authorized by E97; results belong in the local qualification record.

| Gate | Required cases and acceptance |
| --- | --- |
| Q01 caller parity | Full pipeline, direct sync/generate/publish/alias, all three admin commands, immediate/daily pinned helper and callable interval loop. Same normal counts/order, permissions, horizons and force-empty policy. Refused requests do no physical work. |
| Q02 ownership | All 16 ordered pairs of sync/generate/publish/pipeline while the admitted operation is blocked; repeat pipeline contention with each of its three physical stages blocked. Deadline and repeated cancellation in both overlap orders; cancellation before executor entry; no overlap, queue growth or reentrant lock. Test separate service instances. |
| Q03 audit isolation | Start denied, start commit acknowledgement lost, terminal before start settles, finish denied/lost, busy admission, full diagnostics, close failure and disabled diagnostics. Business counters/effects unchanged; exact SyncID only; no duplicate start/finish or background backlog. |
| Q04 SQL boundaries | Successful input and generation commits; error before first statement; error after writes with confirmed rollback; lost commit acknowledgement; rollback failure; close failure after known commit; close stall; identity-preserving replacement and IDENTITY_INSERT failure. Actual state and connection settlement are independently checked. |
| Q05 files | Primary serialization/write/replace failure; index build/write/replace failure; empty-preserve and forced-empty; Unicode and strict invalid values; temporary cleanup; old primary/index bytes and new generation facts. Real disposable files, not just mocked writers. |
| Q06 lifecycle | Close both admissions before other teardown awaits; stop after current entered stage; admitted audit finish drains independently; repeated teardown cancellation; no monitor restart admits work while closed; no late pinned update after shutdown. Process restart does not resume a diagnostic run. |
| Q07 outcomes/artifacts | Inject timing/telemetry/projection/redaction/report failures; service and rendered messages retain acknowledged counts; no generic retry. Separate direct-stage history from full-pipeline success. Verify actual report/ZIP members and hashes after late settlement. |
| Q08 resource bounds | One active mutation, at most one scheduled waiter (E97), one audit context/task, at most one audit thread at a time and one extra audit connection concurrently with business. Audit terminal envelope <=8 KiB, optional retained summary <=8 KiB, no business-history displacement from a 10,000-offer audit storm. Cleanup-unknown objects remain owned and visible. |
| Q09 latency | Equal-window baseline/candidate comparisons with audit off/on/blocked, empty/representative/large synthetic calendars (0/1,000/10,000 generated instances), same file and SQL fixtures. Added healthy business completion p95 <=max(20 ms, 5% of baseline); owner admission/result bookkeeping p95 <=5 ms; audit offer p95 <=1 ms and max <=5 ms. |
| Q10 loop/drain cost | Five alternating 10-second control/treatment windows after warm-up; same timer source and 10 ms heartbeat, record wake lateness and callback delivery. Added lag p99 <=5 ms and max <=20 ms; deliberate 50 ms loop stall must be detected. After releasing blocked finite work, owner/drain settlement p95 <=100 ms and max <=500 ms. Measure audit healthy start/finish separately (p95 <=250 ms each); slow audit must not fail Q09. |
| Q11 failure limits | Exercise native 250 ms lock/2 s statement timeout and denied audit access in both overlap orders. Measure login/commit/close separately; do not assert timeouts bound arbitrary hangs. A deliberately unresolved driver/close remains owned and fails clean-drain qualification; no force-release to meet timing. |
| Q12 release checks | Full regression/log hygiene, lint/type/format, architecture/deferred/routing checks, explicit selector, smoke/registration, exact Changes review, immutable final head/CI and protected-updater compatibility. Canonical formatting precedes source pins. |

Use fixed deterministic fixtures and enough samples to report p50/p95/p99/max with sample counts. Keep raw controls, treatment order, timer calibration and failed runs. If the cost gates fail, revise the mechanism before considering deployment; do not deliver an unqualified optional path and call the scope complete.

### Test selection and native SQL packet

Extend the nine baseline suites: `test_calendar_pipeline.py`, `test_calendar_service.py`, `test_sheets_sync_flow.py`, `test_calendar_publish_cache.py`, `test_admin_calendar_commands_task3.py`, `test_calendar_scheduler.py`, `test_calendar_runtime_cache.py`, `test_event_generator.py`, `test_calendar_service_telemetry_task3.py`. Replace tests that merely expect `failed_service` retries and mocks of public pipeline stages with effect-boundary assertions. Retain negative coverage rather than deleting it.

Add `tests/test_calendar_owned_mutations.py`, `tests/test_calendar_sync_audit.py`, `tests/test_calendar_sql_lifecycle.py` and `tests/test_calendar_outcome_artifacts.py`. Add native cases through a guarded `scripts/qualify_calendar_ownership.py`. Extend existing status/cache-contract/schema/parsers/sourcekind/owned-operations/graceful-shutdown/startup/scheduler/diagnostic tests where affected. Review reminders and pinned embeds as downstream consumers without redesigning them. Full suite is necessary because lifecycle and diagnostic schemas are shared.

The selector maps `event_calendar/` to `tests/test_calendar_*.py`; that misses `test_sheets_sync_*`, `test_event_generator*`, admin and shared lifecycle tests. Explicitly include those additions. Expand globs using the shell's discovered paths on Windows rather than assuming pytest expands them.

Authorized native fixture policy under E97: a newly created, uniquely suffixed `K98_P015_Disposable_20261105_<run>` on `localhost\K98DEV`, containing only these five authoritative tables and synthetic data. Verify server identity, database name/ID, paths, empty/new provenance and permissions before writes. Use injected fixture connection factories for actual methods; offline Sheets and Discord boundaries. Exercise two connections for blocking, explicit rollback and same-process close; record observed sessions and actual final rows. A lost-ack wrapper is a controlled simulation, not a naturally occurring driver fault. Do not modify production, retained restores or predecessor test databases. Cleanup only the exact verified disposable target after its evidence is saved; never broaden to neighboring databases/files. E97 names the initial exact target. Every invocation must independently verify absence before creating it and preserve its receipt before removing only that newly created fixture.

## Implementation manifest and delivery order

| Planned path | Purpose |
| --- | --- |
| `event_calendar/service.py` | Shared owner, retained operation/observer lifecycle, private stages, independent result projection, conservative retry policy, audit integration and passive status corrections. Reduce duplicated success/failure assembly rather than expanding the monolith with another state machine per caller. |
| `event_calendar/sheets_sync.py` | Separate business parse/upsert/commit from audit; explicit attempted/confirmed counts and SQL cleanup contract. |
| `event_calendar/event_generator.py` | Preserve deterministic transactional replacement; capture commit and cleanup outcomes separately. |
| `event_calendar/cache_publisher.py` | Primary/index separation, shared atomic writer and exact result facts. |
| New `event_calendar/mutation_owner.py` | Shared loop owner and one scheduled intent, separated from result projection to keep the service readable. |
| New `event_calendar/sql_lifecycle.py` | Small calendar-local connection/cursor/transaction cleanup adapter; no global connection-policy change. |
| New `event_calendar/audit_dal.py` | Existing EventSyncLog SQL, bounded errors, explicit independent connection limits and exact ID acknowledgement. |
| New `event_calendar/sync_audit.py` | One retained optional task/context, no queue, separate lifecycle and settlement/loss summary. |
| `commands/admin_cmds.py` | Remove redundant calendar caller locks; preserve access/defer; render truthful busy, unknown, warning, counts and cleanup. Keep SQL/orchestration out of commands. |
| `bot_instance.py` | Calendar admission close/drain and startup/daily result handling; preserve normal pinned update boundary. |
| `event_calendar/scheduler.py` | Service admission/results and cancellation; no new scheduler registration. |
| `core/operation_evidence.py`, `services/operation_diagnostics.py`, `services/optional_upload_observations.py` | Narrow calendar boundary fields and independent bounded optional summary, coordinated schema/projection handling; preserve upload semantics and history priority. |
| `scripts/qualify_calendar_cost.py` | Matched offline cost controls, real disposable JSON writes, both existing upload transports, blocked reads and a calibrated independent heartbeat. Native SQL costs remain separately measured. |
| Tests and native runner named above | Final-effect, real-thread, native SQL, real-file, user-output and artifact qualification. |
| `docs/reference/events_and_dm_reminders.md`, `docs/reference/runbook_shutdown.md`, `docs/reference/ENV_REFERENCE.md`, `docs/calendar/task4_runbook_local_validation.md` | Actual ownership/outcome/timeout/retry/audit semantics after implementation, plus local validation instructions. |
| `scripts/k98_update_transitions.json` and exact transition tests/fixtures selected by installed compatibility | Reviewed successor for changed protected source, including bot lifecycle. Determine actual pin family from the final canonical tree; preserve every historical transition. No speculative edit to unrelated updater behavior. |
| Existing carry-forward destinations and this packet | Include every pending closeout document and both sides of all nine archive moves in the next authorized reliability PR/private promotion. |

Read-only compatibility targets: `runtime_cache.py`, `cache_contract.py`, `core/owned_work.py`, `core/operation_timing.py`, `core/scheduler_lifecycle.py`, `file_utils.py`, `constants.py`, the existing report/ZIP collectors and protected updater verifier. Change these only if an exact in-scope dependency is demonstrated and record any manifest amendment. No shared owned-work helper change is currently needed.

Implement in this order: result/connection contracts and failing regressions; service owner with all caller/shutdown wiring; audit isolation and cache split; final status/report projections; native and cost qualification; complete regression and immutable review. These are development steps in one design, not independent claims of delivered fixes.

Preferred release: one complete qualified Bot change. A two-release option could ship the complete ownership/outcome/caller contract first, keeping inline audit only as an explicitly incomplete F23 containment, then audit isolation. It would retain audit latency, require two full lifecycle/updater/review/deployment cycles and not close P01.5 after the first release. It is therefore not recommended. No SQL release order is needed under the selected design; any discovered need for a durable receipt/atomic pair returns for an exact schema/consumer design and separate SQL review.

Rollback remains a separately authorized reviewed Bot release after all old physical work is settled. Existing SQL and JSON are compatible, but old code reintroduces these ownership/outcome defects. Do not roll back during an unconfirmed SQL close, infer rollback from absent audit rows, or deploy mixed writers. No automatic cross-restart continuation or exactly-once guarantee is claimed. Ordinary startup/daily refresh remains a new convergent refresh of current inputs, not recovery or proof of a previous run's result.

## Refactor decisions, boundaries and approval

Fix within P01.5: audit/business coupling; missing shared mutation ownership; retry eligibility without effect evidence; primary/index coupling; explicit calendar connection custody; duplicate JSON writer; false aggregate pipeline health and top-level horizon projection; outcome loss from optional formatting/report boundaries. Update associated tests. No direct SQL was found in these calendar command paths, so no command-to-DAL SQL extraction is needed.

Reuse `drain_thread`, `drain_awaitable`, safe observation/timing, diagnostic redaction, atomic JSON writing and the optional-summary retention pattern. Reusing the upload audit transport itself is unsuitable: its domains, identity binding and connection factory are upload-specific, and a calendar SQL stall should not queue ahead of optional upload audit. No generic worker framework, incident store, repair command or broad cleanup is proposed.

F20 file-lock cleanup and F26 shared connection fallback remain P02; P01.6 owns personal-read capacity; P02 owns contention/holder evidence and F09; P03 owns original-intent durable continuation and Rally F29; P04 owns notification journal F19 and broader convergence/history; P05 repository-wide confirmation remains mandatory. Calendar rules/reminders/board redesign and the updater per-blob tooling optimization retain their existing owners. These are already captured programme items; no duplicate deferred entry is needed. No newly discovered unrelated debt is being used to defer an in-scope fix.

Historical E96 security routing used `k98-security-review-routing`: **documented skip for that Markdown design/navigation delta**, with no runtime/configuration/dependency/permission/data-access/deployment change. The ignored offline review harness is not shipped. Future implementation requires `codex-security:security-diff-scan`, **Changes**, exact Bot base/head, **Deep off**; a genuine SQL diff gets its own target/review. No codebase/deep audit was requested or run.

Required references applied: current AGENTS and core engineering/execution/testing/refactor/deferred guidance; events/reminders, helper review, startup/shutdown/singleton/diagnostic contracts; local SQL development and Windows ownership/access boundaries. The handover's explicit documentation authorization supersedes the architecture skill's default no-document-edit checkpoint; E97 subsequently authorizes the selected local implementation and qualification.

**E97 approval recorded:** implement and locally qualify the complete selected design, including the explicit busy/deadline/audit/retry/output behavior above and guarded disposable SQL qualification. Publication, merge, private promotion, deployment, restart, live provider/Discord activity and incident recovery remain separate. The known index-consumer decision is settled for this design; no removal or atomic-pair migration is proposed. Candidate cost and native cleanup evidence are required before any delivery claim.

## Review delivery validation

Architecture, deferred-items, security-routing and diff whitespace checks passed. The prospective runtime selector recommends calendar tests, smoke imports and registration; the risk-based additions above are mandatory because its mapping is narrower than this change. The unchanged nine-suite review baseline passed 44 tests. Full runtime suite, fresh smoke/registration, native SQL, cost qualification and a Changes scan are not rerun for the Markdown delivery; they remain candidate gates after implementation approval.

All 35 current changed/new Markdown destinations have 759 valid relative links. All 42 inherited Git paths are preserved: 36 have unchanged bytes/absence and six have only additive design navigation/tracker/manifest updates checked against saved before-copies. All nine inherited archive moves remain intact; the old manifest path intentionally remains reused. Only one new tracked-delivery candidate, this Markdown packet, was added. Ignored offline review evidence remains private. No runtime code, SQL source, configuration, production state, deployment package or accepted predecessor evidence was changed.

## E97 implementation refinements and adverse evidence

The shared owner is factored into `event_calendar/mutation_owner.py`; public service APIs still own every application mutation. Command delivery observations are recorded separately and cannot change business success. Unknown primary replacement acknowledgement yields nullable written counts. SQL diagnostic extraction is bounded and includes only error class, SQLSTATE and numeric native code.

Combined-load qualification demonstrated that the existing diagnostic sink's `time.sleep(0)` batches could reacquire execution repeatedly on Windows. A 1 ms finite pause is now used only on the existing sink thread at its existing batch boundaries; producers do not wait. This is a directly demonstrated dependency in an already planned diagnostics file. Complete history/ZIP behavior, existing upload workers and physical drain must be requalified; no queue/retention limit or cost threshold is relaxed.

Retained adverse evidence includes the original invalid Windows heartbeat cadence, corrected-cadence lag failures before the sink correction, a disposable cache replacement PermissionError, and a later measurement contaminated by overlapping local formatter/validation work. None is a pass. The timer now uses the previously qualified Python 3.11 Windows sleep source on an independent thread, with delivery measured against the same monotonic clock. Final acceptance requires a quiet matched run with all original gates, plus separate native SQL receipts. File sharing policy F20 remains with P02; no retries were added to calendar mutations or primary replacement.

Local qualification results and the final checkpoint are recorded in the linked E97 implementation packet below. Publication, merge, promotion, deployment, restart, live provider/Discord operations and incident repair remain outside E97.

## E97 implementation evidence

See the [local implementation and qualification packet](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Local%20Implementation%20and%20Qualification%20-%202026-11-05.md) for results, adverse runs, limits and remaining release gates. E96 current-body/baseline sections above remain historical; they do not describe the final candidate. Busy refusals expose a separate blocking-run reference and cannot overwrite another operation's delivery.
