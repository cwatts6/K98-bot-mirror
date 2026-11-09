> **Archived at E104, 6 November 2026.** P01.6 is closed for its agreed scope. See [accepted closeout](Startup%20Import%20Export%20Reliability%20-%20P01.6%20Closeout%20-%202026-11-06.md) and [active P02 handover](../Startup%20Import%20Export%20Reliability%20-%20P02%20Handover%20and%20Scope%20-%202026-11-06.md). Dated approvals, candidate status and commands below are historical evidence, not instructions to replay deployment or recovery.

# P01.6 source review, design and qualification packet

**5 November 2026. Updated design, implementation and offline qualification approved by the operator, including creation/use of a disposable local development SQL database.** This packet retains the reviewed design and its original baseline evidence. Implementation includes the recommended passive Personal Stats Health line. Candidate results belong in the separate implementation receipt; this design packet alone does not claim completed qualification, publication, deployment or production acceptance. Earlier approval-pending wording below records the design-stage boundary and is superseded by this explicit authorization.

## Authority, source and preservation

The controlling handover is `docs/task_packs/Startup Import Export Reliability - P01.6 Handover and Scope - 2026-11-05.md` in `C:/Users/cwatt/.codex/worktrees/p015-production/discord_file_downloader`. Its E100 closeout, natural-acceptance register, tracker, P01 design and documentation carry-forward remain authoritative. P01.5 is CLOSED for its agreed engineering scope and observed normal calendar/pinned delivery at private `24bca82f0a23721c1428bfe4f0db2e120d5b7c34`. No accepted action needs replay.

Reviewed sources:

| Checkout | Observed local identity | Disposition |
| --- | --- | --- |
| Mirror `C:/discord_file_downloader` | `codex/p015-calendar-ownership`, `7ba6c535c83e91a2a03d3620e836ccd27bf09f6d`; clean at entry | Source review and this new packet; no branch switch or reset |
| Documentation/private worktree | `7455cb28a68c99b7dfbed558417a980ccc3f00b1` | Existing E100 delta preserved; 42 status entries inventoried, including deleted move sources and new destinations |
| SQL `C:/K98-bot-SQL-Server` | `b1eeb8e894fec380c7a6d6c5cc5bbfd9dbc3470c`; clean | Definitions only; no database connection |

All 32 inspected Bot runtime files in the retained source manifest have identical bytes in the two Bot checkouts. Local identities are source evidence, not fresh remote-main or installed-host evidence. Git inspection of the other worktrees used a command-local exact-path safe-directory setting; no global Git, ACL or ownership settings changed.

Private review evidence is in `.codex_artifacts/p016-review-20261105/` in the mirror: exact-body harnesses, reproduction results, source hashes and the E100 file inventory. Keep those artifacts and the predecessor `.codex_artifacts/p015-closeout-p016-20261105/` out of public commits. The first harness attempt failed before execution because generated AST nodes lacked line metadata; the corrected harness uses `ast.fix_missing_locations`. That harness correction changed no application source.

This new packet is an **additive carry-forward item**. During the next authorized mirror delivery, reconcile the entire E100 manifest from the documentation worktree by reviewed content/patch, include all six archive moves with both sides, then add this packet and update active navigation/tracker. Do not replace E100 with the older root documents or push private history to the mirror. No existing E100 file is edited by this review.

## Scope summary and source-confirmed findings

Recommended implementation: one small, event-loop-owned personal-stats runtime, retaining actual SQL/render workers through observer timeout and cancellation; strict cleanup evidence on the stats registry and dataset paths; fresh authorization at every delivery boundary; bounded cache, observer and admission state; fail-closed, repeatable shutdown integration. Keep metrics, periods, SQL result shapes, private visibility and command surface compatible.

| ID | Evidence | Consequence and disposition |
| --- | --- | --- |
| R01 / F24-B06 | `stats_service.py:145-201`: semaphore surrounds `wait_for(to_thread(loader), 9)`; task completion removes `_INFLIGHT` | Timeout can release logical capacity while native work continues. Fix in P01.6. |
| R02 | Same source: semaphore acquisition is outside the timeout; one task is created for every distinct key; no waiter limit | The nine-second limit is not a request/queue deadline; inflight/task retention can grow. Fix bounded admission, not a larger queue. |
| R03 | Cache publication belongs to observers after `shield(task)` | When all observers cancel, a successful late worker is removed without caching. Concurrent observers also own TTL publication. Move publication to the exact worker owner, independent of UI. |
| R04 | `personal_stats_dal.py:154-200` closes in nested `finally`; `registry/dal/registry_dal.py:270-297` suppresses connection-close failure | Dataset read error can be replaced by cleanup error; registry can return accounts despite unknown close. Preserve read and cleanup separately and retain custody. |
| R05 | DAL sets `cursor.timeout` only if present. Installed pyodbc 5.3.0 has `Connection.timeout`, no declared `Cursor.timeout` | Existing fake-cursor assertion does not establish a native query timeout. Set and qualify the real connection attribute for the scoped reads. |
| R06 | Stats service rechecks fingerprint before payload return; view then awaits avatar/render. `change_mode` reuses payload; scope paging reuses account options | Revalidate current account authority after preparation and immediately before new private output, including fallback, mode and picker edits. This is an in-scope authorization invariant, not deferred debt. |
| R07 | View uses a two-thread renderer executor but submits without admission bound, with `wait_for` cancellation | Running threads are capped, but outstanding submissions/lifetime and shutdown are not explicitly owned. Bound render submissions and drain actual completion; preserve same-payload fallback. |
| R08 | `bot_instance.py:1075-1088`: `_shutdown_once` is set before required drains; subsequent calls return immediately | A failed first drain can look complete to a second caller. Required shared prerequisite: memoize/reawait one actual teardown task/result; keep the flag only as admission/presentation state. |
| R09 | Installed Pycord `client._cancel_tasks` cancels all loop tasks. `core.owned_work.drain_thread` creates a separately cancellable `to_thread` task inside `drain_awaitable` | Global cancellation can cancel the inner task independently of its shield and finish the owner before the native thread. Reproduced; narrow shared-helper correction is required, with all-caller regression. |
| R10 | `DL_bot._quiesce_background_tasks` catches entered teardown failures and takes a fallback; `_graceful_shutdown` closes logging in `finally` | Preserve required-drain failure through signal shutdown and final process cleanup. A fallback must not certify native settlement or release process custody. |

The R08 finding is new concrete evidence in a shared boundary, not reopening P01.5's accepted calendar business behavior. Calendar ownership, optional audit and publication contracts remain unchanged.

## Executed offline evidence and its limits

Harnesses extract the named functions/classes from the current AST, execute unchanged function bodies, supply synthetic loaders/connections and use real Python threads. They do not import the Bot, connect to SQL, contact Discord, or run a provider request. All started synthetic workers are released and joined before exit.

| Reproduction | Observed result |
| --- | --- |
| Same key, two sequential requests, actual nine-second constant, blocked native loader | Both observers raised TimeoutError after approximately 18.031 seconds total. Two physical loaders remained active, `_INFLIGHT` was empty and all eight semaphore slots were available. |
| Sixteen distinct requests, only the observer timeout shortened to 50 ms | Twelve native loaders concurrently entered on this host before release; all sixteen observers timed out. Eight logical slots were available and inflight was empty while native loaders remained. The host executor limited entry; this is not a claim of sixteen physical entries. |
| Only observer cancelled, worker later succeeds | One worker remained owned initially; after settlement inflight was empty and cache count was zero. |
| Registry connection close raises | `get_by_discord_id` returned the synthetic account row and suppressed the close exception. |
| Two teardown calls, fake calendar reports unconfirmed cleanup | First raised RuntimeError; second returned without performing the drain. |
| Exact owned-work helper, native loader blocked, cancel every loop task except the harness | Two tasks cancelled; owner finished while physical completion was false. The harness then released/joined the worker. This mirrors the installed Pycord cleanup shape, not an actual Bot shutdown. |

Existing baseline command: `.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider tests/test_player_self_service_stats_service.py tests/test_personal_stats_dal.py tests/test_player_self_service_stats_views.py tests/test_me_cmds.py tests/test_account_data_export_service.py`.

Result: **58 passed in 7.36 seconds**, one dependency FutureWarning. Existing tests prove ordinary deduplication, pre/post-load access checks, row mapping, private entry, stale transitions and export-file cleanup. They do not prove the new design, real SQL cancellation/timeout/cleanup, bounded pending render admission, final authorization after rendering, or shutdown settlement. No full-suite or native qualification pass is claimed.

## Caller, resource and ownership matrix

This census follows all production references to `build_personal_stats_payload`, `fetch_personal_stats_daily`, `send_personal_stats` and `show_personal_stats_for_interaction`, then the named adjacent paths. Searches explicitly included ignored source files; a default ignored-file search alone was insufficient in this checkout.

| Caller/resource | Current path and boundary | P01.6 decision |
| --- | --- | --- |
| Slash command | `commands/me_cmds.py:me_stats` -> `send_personal_stats` -> `show_personal_stats_for_interaction`; explicit ephemeral command defer | Route through owned/bounded service and final delivery gate. Command remains thin; no new command or resync requirement. |
| Shared Accounts/Reminders/Preferences page | `player_self_service_views.py:stats_button` -> same entry; generation callback passed as `can_edit` | Keep caller generation fence and recheck after final authorization. No separate dataset loader. |
| Selected-governor Dashboard | `player_self_service_governor_dashboard_views.py:open_stats` wraps same entry in its remaining transition timeout | Pass current transition predicate into stats delivery, alongside cancellation; preserve selected governor and timeout behavior. |
| Stats period / scope | `PersonalStatsView.change_period/change_scope` -> payload loader with expected registry fingerprint | Same physical owner/cache; expiry/replacement cancels observer only; late result never edits itself. |
| Stats Overview/Activity/Combat and scope page | `change_mode` / `change_scope_page`; currently no payload reload | Fresh registry check before revealing/re-editing payload or account options; no extra dataset query. |
| Stats navigation away / timeout | `open_dashboard`, `open_page`, `on_timeout` | Keep generation, author, expiry and private-navigation checks. Timeout only disables controls/preserves already delivered report; it must not publish a new late payload. |
| Dataset SQL | `stats_service` -> `personal_stats_dal.fetch_personal_stats_daily` | Owned read plus confirmed native cleanup, same-key identity, bounded publication. No other production caller of this DAL function found. |
| Registry before/after load and delivery | `governor_account_service` -> `registry_service.get_user_accounts` -> `registry_dal.get_by_discord_id` | Add explicit scoped cleanup/timeout plumbing for stats. Bound the complete synchronous call through the stats runtime, including connection creation, retries and close. Existing non-stats defaults remain compatible. |
| Render/avatar/files | `_run_renderer`, `_read_avatar_bytes`, `_initial_delivery`, `_edit_transition`, `_close_files` | Existing two render threads, at most two outstanding render jobs, no renderer queue. Keep three-second/2 MiB avatar limit, 3.5-second render observation and attachment cleanup; drain late renderer, discard unused bytes. |
| Teardown | `bot_instance._graceful_teardown` -> domain drains -> export drain -> client/task teardown; cooperative restart awaits it; `DL_bot` signal/final cleanup and installed Pycord all-task cancellation | Close stats admission before first await; drain actual stats reads/renders, then continue. Repeated teardown observes the same outcome; signal failure propagates; loop-wide cancellation cannot cancel the underlying executor future. No successful drain receipt or process-custody release on unknown cleanup. |
| Account Summary / portfolio | `accounts_service.build_accounts_portfolio_from_resolution` gathers `accounts_dal.fetch_latest_accounts_scan_rows` and Inventory reporting | Not a caller of personal-stats dataset/inflight/cache. Retain regression coverage; shared read-budget/cleanup policy remains P02. Do not silently claim it covered by the eight stats slots. |
| Governor Dashboard data | `_fetch_dashboard_data` -> `governor_dashboard_dal`; separate Inventory highlights | Independent data/authorization journey; only its Stats navigation is changed. DAL row shape reviewed; generalized ownership stays with P02. |
| Account Data download | `account_data_export_service`: registry, portfolio, `stats_export_dal` history, then per-export builder future | Existing writer callback protects temporary-file deletion after cancellation. It is not an eight-slot personal-stats reader and its per-request executor is not a reusable global admission design. Preserve tests; broader read/build drain belongs to P02. |
| KVK target cache | `targets_sql_cache` delegates to `TargetCacheRepository`; synchronous durable refresh token/file coordination and publication DAL | Not equivalent to transient personal stats; no adoption of its lease/takeover protocol. Producer-budget/file-lock work stays P02/F20; regression only. |
| Last-KVK cache helper | `stats_cache_helpers.load_last_kvk_map` -> existing blocking helper -> local JSON | No personal-stats SQL/dataset use. Preserve semantics; global helper migration is excluded. |
| Stats-alert DB wrappers | `stats_alerts/db.py` -> shared connection factory and blocking helper/fallback | Cleanup/timeout and fallback policies are P02/F26. No broad rewrite or connection-policy change here. |

No direct SQL was found in the stats command/view journey. The service owns authorization, selection, metrics and cache; the DAL owns queries, mapping and cleanup; views own acknowledgment, rendering and delivery.

## SQL / persistence review

**Verdict: source alignment supports a Bot-only change, subject to native qualification.** SQL schema/migration manifest is empty. No production installation, effective permission, actual plan or latency claim follows from source inspection.

| Owning SQL definition in `C:/K98-bot-SQL-Server/sql_schema` | Verified contract / use |
| --- | --- |
| `dbo.IntList.UserDefinedTableType.sql` | `ID int NOT NULL` primary key. Personal DAL binds 26 fixed parameter positions, deduplicates positive IDs, fills unused positions with NULL; SQL inserts distinct non-NULL values. Validate signed-int upper bound before submission; do not silently widen the UDT to registry's bigint. |
| `dbo.usp_GetPersonalStatsDaily.StoredProcedure.sql` | `@GovernorIDs dbo.IntList READONLY`, `@HistoryDays smallint=180`, EXECUTE AS CALLER; 1..26 IDs, 1..180 days; header plus daily result sets; empty anchor returns typed empty rows. No business writes; local temp tables and RECOMPILE. |
| `dbo.KingdomScanData4.Table.sql` | bigint GovernorID/metrics, datetime ScanDate, persisted date AsOfDate, SCANORDER/SCAN_UNO; nullable troop/healed fields retained. Global max AsOfDate and max ScanDate on that date supply source anchor/freshness; per-day ranking/LAG supply deltas. Existing date/governor and governor/scan indexes present. |
| `dbo.AllianceActivitySnapshotHeader.Table.sql`, `dbo.AllianceActivitySnapshotRow.Table.sql` | SnapshotId join; SnapshotTsUtc/WeekStartUtc; bigint GovernorID, integer BuildingTotal/TechDonationTotal; governor/snapshot and week/time indexes. Procedure uses raw snapshots, not a new completion filter. Preserve current metric semantics. |
| `dbo.cur_RallyDaily.Table.sql` | Table, not view: date AsOfDate, bigint GovernorID, non-null integer TotalRallies/RalliesLaunched/RalliesJoined; date/governor primary key and governor/date covering index. |
| `dbo.sp_Registry_GetByDiscordID.StoredProcedure.sql`, `dbo.DiscordGovernorRegistry.Table.sql` | bigint DiscordUserID, nvarchar(10) StatusFilter default Active; parameterized query returns slots/names/IDs/status and provenance. Active governor/slot unique indexes and supported Main/Alt/Farm constraints. Every fresh check uses active rows, never registry cache as authority. |
| `dbo.Civilization_Mapping.Table.sql`, `dbo.PlayerLocation.Table.sql`, `dbo.GovernorInventoryProfile.Table.sql` | Adjacent portfolio/dashboard join columns confirmed: Civilization/Civilization_Name, GovernorID/X/Y, VipLevelCode/VipLevelLabel. These are not personal-stats procedure dependencies. |
| `dbo.vDaily_PlayerExport.View.sql` | Adjacent download's named history columns align with the selected view output; KingdomScanData4, vDaily_AllianceActivity and cur_RallyDaily compose it. It is a separate history/metric contract, not a replacement for the period procedure. No export SQL change. |

Header fields remain StatsAnchorDate, StatsSourceRefreshedAtUtc, WindowStartDate, WindowEndDate, RequestedGovernorCount. Daily mapping keeps the 25 identity/coverage/value/delta fields in `personal_stats_dal._map_daily_row`; one row per requested governor/date implies at most 4,680 daily rows. Validate duplicate identities and row limit as contract failures before retaining a dataset, with no changes to legitimate metric output.

The read path does not use ProcConfig, ingestion staging or output mutation procedures. No new index is justified: the existing deferred personal-stats actual-plan/cardinality item remains open. Read/UI/cache state does not authorize durable cross-restart continuation, exactly-once execution or replay.

Connection chain is `get_conn_with_retries(operational=False)` -> `producer_connection(_conn)` -> contextual S11 runtime DAL if present, otherwise ordinary `_conn`. Ordinary `_conn` uses autocommit=False and a five-second login timeout. Shared retry defaults are five attempts with exponential jitter; these are connection attempts, not a licence to repeat an entered statement. P01.6 counts their entire physical lifetime but leaves shared retry/fallback/credential selection to P02/F26. The ordinary Discord stats entry has no explicit S11 caller-runtime scope; regression must also test inherited-context routing without bypassing it.

Query timeout is set on the returned connection **before cursor creation**, to nine seconds for the scoped dataset and registry calls. This does not bound login, all fetch/nextset work, rollback or close; the UI deadline never asserts that it does. If factory-internal partial acquisition cannot establish cleanup, do not release on a generic exception: reconcile the concrete factory prerequisite with P02 before accepting that case. No guessed successful close or generic global factory rewrite is allowed.

## Architecture and lifecycle contract

### One narrow owner, separate observers

Add `player_self_service/stats_runtime.py`, instantiated per running loop using the delivered loop-local pattern. It owns physical read records, bounded observation leases, render records, lifecycle state and a passive redacted snapshot. `stats_service.py` retains its metric assembly and domain cache policy; no Discord types enter either service module.

Recommended fixed limits are **eight total stats SQL workers**, **32 observing stats requests**, **two outstanding renderer jobs**, and **zero application-level SQL/render waiters**. Stats SQL workers include its pre/post/delivery registry calls as well as its dataset calls. This deliberately strengthens the old dataset-only bound; it is not a global budget for unrelated readers. Slots are reserved synchronously before creating the owning task or submitting work. An executor-queued job already consumes its reservation. Saturation returns unavailable immediately, rather than accumulating semaphore tasks. Cache hits still require authorization capacity.

An observer lease is acquired after prompt private acknowledgment but before avatar-task creation, registry work or any other stats preparation, and spans the relevant stats preparation/delivery journey; nested service calls reuse it, never consume a second lease. No lease is transferable to a later callback or detached task. Distinct requests beyond 32 are refused before preparation/task allocation. Release the lease in one encompassing finally path, including acknowledgment/delivery failures and navigation cancellation; do not detach an avatar task when its observer leaves. Same-key observers may join only an already owned dataset, within that observer bound. Registry checks are fresh operations at their boundary, not cached or joined to an older precheck. No SQL worker awaits another SQL worker while holding a slot.

The existing nine seconds becomes one shared payload-observation budget covering pre-registry, dataset and post-registry, instead of an unbounded queue/registry interval plus nine seconds. Final delivery authorization gets at most two seconds after render; native query timeout remains nine, with late physical work retained. With avatar overlap and the existing 3.5-second render limit, local preparation is bounded by 14.5 seconds plus event-loop tolerance; Discord's own network acknowledgment is measured separately. These are intentional overload/deadline changes requiring approval, not claims of exact historic latency compatibility.

Carry the caller's absolute monotonic expiry into preparation and delivery. Each stage uses the smaller of its budget and the caller's remaining time; dashboard navigation near expiry cannot reset the clock by opening Stats. An expired caller starts no new read/render/final-check work and cannot receive a late edit. The dashboard forwards both its current-transition predicate and expiry. A Discord request already dispatched when expiry/cancellation occurs may have an unknown delivery outcome; do not claim it was withdrawn or resend it. The 14.5-second figure is a preparation ceiling for an otherwise live caller, not a promise that Discord delivery finishes within it.

| State / interruption | Mandatory owner behavior |
| --- | --- |
| Before admission | Refuse if closed, saturated, invalid input or stale authorization. Allocate no worker. |
| Reserved, before task creation/submission | Install exact run identity first; creation/submission failure releases only a definitely unsubmitted reservation. No detached completion callback task. |
| Submitted / executor queued | Reservation remains counted, even if thread has not entered. Cancellation does not discard the native future or create replacement work. |
| SQL executing / fetching / rollback / close | Owner uses `core.owned_work.drain_thread`; deadline is `wait_for(shield(owner_task), remaining)`, never `wait_for(to_thread(...))`. |
| Observer timeout or repeated cancellation | Release observer lease, retain physical slot and exact dataset key. No late Discord response and no automatic retry. |
| Physical success, cleanup confirmed | Owner publishes eligible immutable cache candidate once, then removes exact inflight record and releases slot in one event-loop turn. Observe exceptions even with no observers. |
| Read failure, cleanup confirmed | Preserve original exception/category and separate cleanup facts; no cache; exact identity release after settlement. A subsequent deliberate request may run anew. |
| Close unconfirmed | Retain handle/outcome and reservation; close all new stats admission, invalidate cache generation, discard deliverable candidate. Active siblings continue to drain. No automatic close retry, timeout release or silent recovery. |
| Shutdown | Close all stats admissions before first await, invalidate publication generation, join actual read/render tasks through repeated cancellation. Return unsuccessful for retained cleanup uncertainty; never certify drain merely because Python tasks ended. |

If a native thread never returns, shutdown remains incomplete and existing passive evidence identifies the active phase. An observation deadline may report pending; it may not abandon or force-release the drain. If the thread returns with unconfirmed close, shutdown produces an explicit unsuccessful result without a forever-running polling task. Retained handles remain private until an authorized reconciliation/process boundary; no automatic cross-restart adoption.

### Cleanup, outcome and helper reuse

Reuse `core.owned_work.drain_thread/drain_awaitable`, with one necessary shared correction: submit the blocking wrapper directly through `loop.run_in_executor(None, copied_context.run, wrapper)` and drain that Future, rather than creating an independently cancellable `asyncio.to_thread` Task. Copy context at the same execution point as the current helper, preserving evidence/caller ContextVars. The executor Future is shielded and is not in `asyncio.all_tasks`; loop-wide task cancellation must keep the owning coroutine draining it until native settlement. Preserve one submission, queue/execution evidence, return/exception identity and repeated cancellation behavior. Do not alter the global executor or add a pool. Scope the change to `drain_thread`; `drain_awaitable` cannot magically protect an arbitrary caller-supplied Task from independent cancellation. All users of that broader API retain their own child-lifetime contract.

Reuse `event_calendar.sql_lifecycle.SqlSession(read_only=True)` and its separate outcome/error/rollback/cleanup fields for these two DAL paths. This helper is generic in behavior despite its current location; direct reuse is preferable to copying it or expanding this slice into a framework relocation. Its read-only exit explicitly rolls back rather than using pyodbc's context-manager implicit commit, closes cursors and then connection, and retains a connection when close raises.

Add explicit optional `sql_outcome`/query-timeout plumbing through the canonical synchronous account-summary -> registry-service -> registry-DAL path; only stats opts into this contract. Default non-stats calls remain compatible. The caller-owned outcome is populated through the existing session object; close failure cannot be flattened by `AccountResolutionSummary.ok` or its generic exception handling. Service code inspects both outcome and returned data. Preserve the original read exception privately even when rollback/close also fails; expose only bounded error type/SQLSTATE/native code. Success data with unconfirmed close is a known read plus unavailable delivery, not a failed read or a reusable success.

A failed cursor close followed by confirmed connection close is settled physical connection custody with a separate cursor-cleanup warning. A failed rollback followed by confirmed connection close remains a recorded rollback uncertainty, not a commit claim; this read-only path has no business commit. Native tests must verify the relevant driver behavior. No transaction is committed by this change.

Reuse `governor_account_service.summarize_accounts` and canonical slot ordering, immutable stats models, `_close_files`, generation predicates and existing safe private acknowledgment patterns. Do not replace all shared helpers. `CoalescedWork` is unsuitable: a request during execution schedules another pass and it has no capacity bound. Calendar `MutationOwner` serializes mutations and carries scheduled intent; it is unsuitable for independent eight-way reads. The Account Data per-request executor/file-cleanup callback is not an admission pool. No new global executor, polling observer, persistent journal or retry scheduler is proposed.

### Cache and authorization

Keep the `(Discord user ID, sorted distinct governor IDs)` key, 30-second TTL and 32-entry LRU. Publish only complete immutable contract-valid datasets, once per physical completion. Record monotonic data-ready time after fetch/validation, separately from cleanup settlement; the 30-second cache reuse window starts at data-ready time. Slow cleanup must not grant an old result a new 30 seconds: skip cache publication if that window has expired by confirmed settlement. Keep the launch fingerprint and cache-generation epoch as metadata. Explicit cache clear, observed account change and shutdown prevent an older worker repopulating an invalidated generation. Expired cache entries are never served. Cache clear never deletes active physical ownership.

Keep invalidation identities on existing owner/cache records, with a runtime-wide epoch for global clear/shutdown; do not introduce an ever-growing per-user generation dictionary. Remove per-key metadata when its last owner/cache reference disappears. Optional cache insertion/eviction failure must still release a physically settled worker in finally, preserving the original read/cleanup facts. TTL is a reuse limit, not a guaranteed physical-erasure timer: expired entries are removed during normal cache access/eviction, bounded by 32 entries, without a new background sweeper.

A late successful dataset may enter the private bounded cache even after every observer left, provided cleanup is confirmed and its epoch is still valid. **Cache presence grants no access.** Every subsequent consumer checks current active registry, matching fingerprint and selected IDs before and after obtaining data, and again before final delivery. Fingerprint mismatch evicts/rejects the candidate and invalidates the relevant generation. No completion callback queries authorization or sends output. Late failure or unknown cleanup is never cached. No cross-user dataset sharing is added.

Keep service-level final authorization for non-UI callers. Add `assert_personal_stats_access` in the service for the UI's final fresh check; reuse registry/fingerprint logic without reloading the dataset. Invoke it after avatar/render/fallback preparation and under the final delivery sequencing guard. After the await, recheck author, expiry, generation and caller `can_edit`; then issue the private edit without another preparatory await. Mode changes and governor-picker paging receive the same check. Scope paging must acknowledge promptly before awaiting SQL.

Do not let a broad render exception handler catch access rejection and publish the same data via fallback. Authorization failure/unavailability exits both image and text paths. Every fallback attempt gets its own current authorization check; an ambiguous Discord delivery failure is reported separately and does not trigger a second data send or reload. Fallback is for definite preparation/render failure or a positively rejected attachment, not an unknown accepted edit. This cannot make a distributed SQL-check/Discord-send atomic: access is checked at dispatch, not claimed to retract an already accepted message after a later revocation.

The existing private report may remain visible after controls expire, as already accepted. No public posting, proactive deletion, late push notification or new access policy is introduced. Account selection changes must never be treated as permission from the old view.

### Rendering, shutdown and passive evidence

Keep the existing two-thread renderer executor. Add a two-job nonwaiting admission bound before submission, retain the native future through timeout, and release only on native completion. Saturated/expired render observation selects the same-payload accessible fallback after final authorization. Owner callbacks discard unused late bytes; no second image edit. Shut the executor down only after owned work settles, off the event loop where joining is required.

In `bot_instance.py`, preserve `_shutdown_once` as the early closing flag, but store one teardown task separately. All calls join that task via `drain_awaitable`; a cached failure remains a failure on repeated calls. The actual implementation body owns all existing domain drains. Close stats admission before the first calendar/upload await; verify the stats drain before generic cancellation, export final release or client close. Existing cooperative restart and protected issuer quiescence must propagate the same result. The event handler's logging cannot create a success receipt.

Update `DL_bot._quiesce_background_tasks` so an entered required-drain failure is re-raised rather than converted into successful fallback cleanup. Import-unavailable fallback remains explicitly incomplete, not proof of stats settlement. `_graceful_shutdown` must not close the client/logging as though required cleanup succeeded after that failure. After `bot.run` returns and the loop is closed, inspect a retained, already-created stats runtime's settlement verdict before releasing PID/singleton custody; do not create an empty runtime on a new loop and call that a drain. Retain the runtime strongly until confirmed settlement, with no unbounded per-loop history. The corrected executor-Future path must survive the real installed Pycord all-task-cancellation cleanup in an isolated subprocess test. Abrupt process/OS termination is outside graceful guarantees; missing acknowledgment remains unknown, never a successful receipt.

Expose a passive `stats_runtime.snapshot()` through the existing `diagnostic-health.json` collection in `services/recovery_evidence_bundle.py`, using `loaded_call` so collection cannot import/start the runtime. Snapshot contains counts/closed state, at most eight active read records, two render records and 32 terminal summaries; no user IDs, governor IDs, names, rows, connection reprs or driver messages. Records distinguish read outcome, cleanup, observer deadline/cancellation, cache disposition and delivery known/unknown; retain first failure and later settlement with source/capture UTC times. Limit the projected stats section to 8 KiB with explicit omitted/coverage metadata. Mandatory owner state is not stored in an optional diagnostics sink. No new thread, timer or sink is required; P01.2b remains closed.

Within that byte limit, emit the admission/cleanup verdict and aggregate counts first, then compact unresolved/active work, then recent terminal detail. Truncation must never hide the fact that cleanup is unconfirmed or shutdown is incomplete; individual omitted records have explicit counts. No loaded runtime means unobserved, not healthy. Closed admission because shutdown began is distinct from closed admission because cleanup is uncertain. Dataset source dates, local data-ready time and report capture time are different facts and must remain labelled separately.

## Before / after examples and tradeoffs

| Situation | Current | Proposed |
| --- | --- | --- |
| SQL still running at nine seconds | Timeout frees slot/key; next request can duplicate native work | Private unavailable/pending result; exact owner remains. Same-key demand joins or is refused, never replaces physical work. |
| All observers cancel | Late success is dropped from cache; physical ownership can later be lost at timeout | Owner settles and optionally caches once; no late delivery. |
| Eight long reads, ninth distinct request | Ninth task waits without its nine-second timer running | Immediate unavailable; no application queue. |
| Registry changes during image rendering | Service's earlier check is the last SQL check | Fresh final check rejects new image and fallback output. |
| Read succeeds, close fails | Error may replace dataset outcome or registry close is suppressed | Known read / unknown cleanup; admission held, no delivery/cache, drain unsuccessful. |
| Teardown requested twice after failure | Second call can return immediately | Both calls observe the same incomplete/failed drain. |

Tradeoffs: fail-fast overload may reject a request that previously waited; registry checks share the eight SQL slots; the final authorization adds one normal registry query per successful delivery (three rather than two for payload-based delivery, one for mode/picker-only actions). Unknown cleanup stops new stats work until investigated. Bounded late caching avoids needless rereads; its reuse window stays at 30 seconds, with bounded lazy removal rather than timed physical erasure. All require measured qualification below.

## Second review: scope coverage, refinements and admin outcome

The second source pass confirms that the proposal addresses the controlling F24/B06 slice as a whole: physical ownership and bounded admission, cleanup evidence, late/cache authorization, every Stats entrypoint, render/delivery separation, shutdown and passive evidence. The proposed changes to shared owned-thread and shutdown helpers are concrete prerequisites established by reproductions, not a reopening of accepted calendar business behavior. Adjacent export, dashboard dataset, target-cache and global SQL-budget work remains classified under its existing owners.

Four refinements are incorporated into the contracts above without adding runtime files or background machinery:

1. Acquire admission before avatar work, and inherit the caller's expiry as well as its current-generation check. Source currently starts the avatar task before the payload loader; dashboard currently wraps the whole call in its remaining timeout without forwarding that lifetime into the Stats entrypoint.
2. Age late cache results from data readiness rather than delayed cleanup completion, and bound invalidation metadata as well as cache entries. These are design ambiguities prevented before implementation, not newly reproduced production failures.
3. Guarantee physical release after confirmed cleanup even if optional cache bookkeeping fails. This complements, rather than weakens, retention when cleanup is unknown.
4. Preserve the unresolved-cleanup/admission verdict when the diagnostic byte limit truncates details, and distinguish unobserved, busy, shutting down and cleanup-uncertain states.

One cost/progress question needs explicit qualification: the shared eight-slot pool can be fully occupied by datasets when a completed request needs its final registry check. The intended behavior is a prompt unavailable result, no unauthorized delivery, no ninth SQL slot and no queued retry. Test mixed cache hits/misses, joins, mode/picker changes and a noisy single user against other users; report refusal rates by stage and successful completions as well as latency. Bounds alone do not prove useful service. If representative native workload shows repeated final-check refusals preventing useful progress, stop and review a reserved-capacity policy within the same eight slots before accepting the design. Do not silently add another pool, relax authorization, introduce a retry queue or add an unbounded per-user limiter map. This review does not assert fair scheduling under sustained overload.

Expected user-visible behavior:

| Situation | Player / admin experience |
| --- | --- |
| Ordinary successful request | Same private report, periods, figures and controls. No new command to learn; no claim of faster SQL. |
| Capacity unavailable | Prompt private busy/unavailable explanation; the request is not secretly queued for later delivery. |
| Observation deadline expires | Explain that the report was not delivered within the allowed time and work may still be finishing. Do not promise cancellation or encourage rapid repeated clicks. No automatic late response. |
| Image preparation fails or is busy | Existing accessible text fallback can still be used after a fresh access check. Unknown Discord acceptance does not cause a duplicate send. |
| Account permissions change | Newly prepared output is withheld; the user returns through the existing account flow to obtain current choices. An already accepted report is not retroactively retracted. |
| Cleanup cannot be confirmed | New Stats work is unavailable; the diagnostic report distinguishes this from ordinary load. There is no automatic reset/retry button or claim that all bot services are unhealthy. |
| Restart requested | Completion is reported only after required work actually settles; a failed/incomplete drain stays visible on subsequent requests. Restart may take longer while real work finishes. |

For admins, the direct gains are bounded resource use, fewer duplicate reads after timeouts, fewer confusing duplicate/stale responses, trustworthy restart outcomes and an existing downloadable report that distinguishes request timeout from read, cleanup and delivery outcomes. Public stats features, new metrics, automatic incident repair and whole-system SQL contention fixes are not delivered by this slice.

**Optional usability addition, not included in the approved-size implementation manifest:** a compact Personal Stats line in the existing passive Health detail/card, sourced from the same snapshot: unobserved / available / busy / shutting down / cleanup uncertain, counts and evidence age. The current proposal adds report evidence only, so do not promise that line as delivered. `operator_status_service.snapshot()` currently projects a fixed component list and typed observations; adding a runtime snapshot alone would not make a card appear. This addition needs its projection and renderer caller review, manifest/test extension and the same no-probe rule. It is the most useful small admin-facing enhancement if included in the implementation decision; new monitoring, alerts or repair controls are not justified here.

Remaining acceptance uncertainties are explicit: real-driver timeout/close behavior, factory partial-acquisition custody, representative final-check availability, shared-helper regressions, final artifacts and actual-host release readiness. Passing source-baseline tests does not settle those candidate gates.

## Exact proposed implementation manifest

These are proposed paths, not changed runtime files. Additional paths require a documented manifest amendment if qualification proves a prerequisite.

| Path | Intended change |
| --- | --- |
| `player_self_service/stats_runtime.py` (new) | Loop-local SQL/observer/render admission, physical ownership, exact identities, close/drain and bounded passive snapshots |
| `player_self_service/stats_service.py` | Replace timeout-owned semaphore/inflight flow; owner cache publication/epochs; bounded default registry loader; reusable final access check; unchanged metrics |
| `player_self_service/stats_models.py` | Narrow typed busy/cleanup/unavailable dispositions if needed by the service/UI; preserve payload fields and immutable data |
| `stats/dal/personal_stats_dal.py` | Reuse SQL lifecycle, caller-owned cleanup outcome, connection timeout, int/row/duplicate validation, original-error preservation |
| `services/governor_account_service.py` | Explicit opt-in synchronous stats read context; preserve canonical account mapping and ordinary callers |
| `registry/registry_service.py` | Forward the scoped read outcome/timeout without SQL in service |
| `registry/dal/registry_dal.py` | Strict opt-in get-by-user lifecycle/timeout; default APIs unchanged |
| `ui/views/player_self_service_stats_views.py` | Bounded render owner, final authorization for every output, prompt picker defer, safe fallback/delivery classification, current-generation checks |
| `ui/views/player_self_service_governor_dashboard_views.py` | Forward final Stats navigation validity predicate |
| `bot_instance.py` | Close/drain stats before teardown; share actual teardown task/outcome across repeated callers |
| `DL_bot.py` | Preserve required drain failure on signal/fallback paths; inspect retained settlement before final process-custody release |
| `core/owned_work.py` | Direct, context-preserving executor Future for blocking work; protect native ownership during loop-wide task cancellation |
| `services/recovery_evidence_bundle.py` | Passive loaded-runtime stats projection in existing bounded member |
| `scripts/prepare_k98_update.py` | Exact P01.6 source-transition declaration/compatibility validation once final bytes are pinned; do not revise old P01.4/P01.5 receipts |

Reuse-only files: `core/interaction_safety.py`, `event_calendar/sql_lifecycle.py`, `event_calendar/mutation_owner.py` pattern, `services/health_observation.py`. No planned changes to calendar semantics, shared factory/fallback, metric renderer, command registration, export builder, global task registry, SQL definitions, dependencies or config. The shared owned-thread correction requires reviewing every direct `drain_thread` caller and the `legacy_export_snapshot_service` compatibility adapter against final bytes, covering calendar, upload/processing, MGE, startup, cache, recovery and explicit observation paths. If existing updater validation supports the candidate without a new declaration, record a justified no-change verdict for that proposed path after checking the final artifact.

Documentation updates after approval: this packet, the E100 handover/tracker/P01 design/carry-forward and task-pack index, `docs/player_self_service_command_centre_briefing.md`, `docs/reference/runbook_shutdown.md`, `docs/reference/runbook_diagnostics.md`; stage the classified deferred items with existing owners. Carry the entire prior documentation delta before reconciling these updates.

## Qualification cases and exact tests

| Case | Required assertions / tests |
| --- | --- |
| Q01 Normal + source contract | All seven periods, three modes, selected/All Linked, 1/26 governors, empty/null/invalid/out-of-range/duplicate rows; unchanged coverage, timestamps, metrics, image and fallback. Update `tests/test_player_self_service_stats_service.py`, `tests/test_personal_stats_dal.py`. |
| Q02 Real thread deadlines | Block native loader past real nine seconds plus accelerated deterministic barriers; one same-key submission, <=8 physical SQL workers, no free slot/key until actual close; old regression must fail before fix. New `tests/test_personal_stats_owned_reads.py`. |
| Q03 Admission + cancellation | At least 1,000 concurrent arrivals: <=32 observer leases, <=8 owned SQL jobs including executor-queued work, zero application waiters. Before avatar/task creation, before thread entry, during query/fetch/close, repeated cancellation; both overlap orders and exact stale callback identity. Caller near-expiry cannot reset stage budgets or start late work. Mixed/noisy-user workloads report stage refusals and useful completions, including final-check saturation. |
| Q04 Late/cache lifecycle | Success/failure with zero/one/many observers; publish once; 30-second data-ready reuse window/32-entry LRU; delayed cleanup beyond TTL skips publication; clear/revoke/shutdown during flight; old completion cannot repopulate or remove replacement; cache failure cannot turn read into retry authority or prevent settled release. Many distinct expired/evicted keys leave no growing invalidation map. |
| Q05 Native-shaped DAL failures | Cursor creation/execute/fetch/nextset/row-map/rollback/cursor-close/connection-close faults; initial error and cleanup error both retained; success-plus-close-failure never delivered; real pyodbc attribute rather than fake-only cursor timeout. Update DAL tests and `tests/test_registry_dal.py`. |
| Q06 Authority + privacy | Cross-user, forged token, changed slot/main/account set, registry unavailable, revoke during read/render/final check; test image, fallback, modes, picker paging, command/page/dashboard routes. No data edit after rejection; author/generation rechecked after awaiting final auth. Update stats-view, shared-page, Dashboard and governor-account tests. |
| Q07 Render ownership | Real blocked render exceeds 3.5 seconds; <=2 submitted jobs across many views; no unbounded native queue; late bytes discarded, attachment streams closed; fallback same payload and fresh access; no duplicate ambiguous send. |
| Q08 Shutdown | New admissions rejected before first await; actual read/render cleanup precedes verified drain; repeated caller/cancellation shares one task; retained cleanup fails every caller. Real installed Pycord cleanup in an isolated subprocess cancels both parent/child tasks while blocked thread remains; native Future stays owned until release. Verify ContextVar propagation and cancellation before executor entry. Signal fallback/final-exit paths cannot certify failed drain. Update `tests/test_startup_lifecycle.py`, `tests/test_restart_operations.py`, `tests/test_p1_owned_operations.py`; new `tests/test_personal_stats_shutdown.py`. Run predecessor calendar/drain/diagnostic suites. |
| Q09 Optional evidence | Clock/redaction/snapshot/sink/delivery exceptions cannot skip mandatory lifecycle or replace original outcome. Status/Refresh/complete report use fail-on-call SQL/provider spies. Verify final ZIP actual member bytes, hashes, descriptors, 8 KiB bound, redaction and incomplete coverage. Update `tests/test_recovery_evidence_bundle.py`, `tests/test_p013_complete_archive.py`. |
| Q10 Native SQL | Authorized fresh disposable fixture only; actual driver timeout, locked reader, fetch/result-set processing, transaction rollback, close/session settlement and query counts; both acquisition orders, caller cancellation while SQL continues, genuine unavailable connection. No fake-only acceptance. |
| Q11 Final artifacts | Inspect final 1702x924 card and fallback for normal/partial/no-data; exact private command plus navigation, expired and pending result; no payload/mention limits or attachment leak. Retain representative synthetic rendered bytes and report ZIP. No new pinned Stats message exists; predecessor pinned-calendar behavior remains regression scope. |
| Q12 Candidate/release | Final formatted immutable Bot head, updater transition/native checks, documentation links, targeted suite then broad regression/log hygiene. No repeat broad tests without changed bytes/failure/concern. Fresh actual-host custody inventory is a later release gate. |

New test files: `tests/test_personal_stats_owned_reads.py`, `tests/test_personal_stats_shutdown.py`, `tests/test_personal_stats_cost.py`, `tests/test_p016_update_transition.py`. New offline qualification tool: `scripts/qualify_p016_personal_stats.py` (synthetic default; explicit disposable-target guard for optional native mode). It must not read production configuration as a fixture default.

Existing tests to update where their contract changes: `tests/test_player_self_service_stats_service.py`, `tests/test_personal_stats_dal.py`, `tests/test_player_self_service_stats_views.py`, `tests/test_governor_dashboard_discord_views.py`, `tests/test_governor_account_service.py`, `tests/test_registry_service.py`, `tests/test_registry_dal.py`, `tests/test_startup_lifecycle.py`, `tests/test_restart_operations.py`, `tests/test_recovery_evidence_bundle.py`, `tests/test_p013_complete_archive.py`, `tests/test_p1_owned_operations.py`, `tests/test_operation_boundary_evidence.py`.

Read/regression set: `tests/test_me_cmds.py`, `tests/test_player_self_service_views.py`, `tests/test_player_self_service_stats_renderer.py`, `tests/test_player_self_service_visual_contract.py`, `tests/test_account_data_export_service.py`, `tests/test_player_self_service_account_data_export_views.py`, `tests/test_player_self_service_accounts_service.py`, `tests/test_player_self_service_accounts_dal.py`, `tests/test_governor_dashboard_service.py`, `tests/test_governor_dashboard_dal.py`, `tests/test_kvk_target_cache_repository.py`, `tests/test_p1_owned_operations.py`, `tests/test_calendar_owned_mutations.py`, `tests/test_calendar_sql_lifecycle.py`, `tests/test_prekvk_dispatch_diagnostic_lifecycle.py`, `tests/test_p015_update_transition.py`, `tests/test_graceful_shutdown.py`.

Before PR: architecture, deferred-item, security-routing and explicit-path test selection validators; appropriate Ruff/format/type hooks; smoke imports and command registration; focused suites plus full pytest/log-isolation qualification on supported environments. Record failures and environment skips individually. Tests do not substitute for source/caller review or security routing.

### Native fixture boundary

Proposed future target: uniquely named `K98_P016_Disposable_<UTC>_<nonce>` on `localhost\K98DEV`, with identity guard before every operation, Broker disabled, no provider jobs, synthetic IDs/rows, explicit file paths outside retained restores. Install only the reviewed dependency graph: IntList, KingdomScanData4 plus its KS4_UNO_SEQ/default dependency, Activity header/rows, cur_RallyDaily, personal-stats procedure, DiscordGovernorRegistry and its get-by-user procedure. Use source definitions, not guessed column stubs; dependencies/permissions and database scope are verified before execution. Preserve the named fixture and adverse receipts until approved cleanup.

Use a restricted fixture principal for the actual caller-permission test; do not treat an administrator connection as proof of application grants. Exercise 1/26 IDs and 180 days, real lock waits in both orders, driver query timeout, login failure, rollback/close, and server-side session/request evidence tied to that fixture. A proxy can inject close-ack failure, but label it injected uncertainty; it does not prove a native driver close failure. Never open a retained restore or production database to obtain these results. Native execution is not authorized by this packet or by the earlier review-only handoff.

## Predeclared cost and complexity gates

Freeze these before candidate measurement. Baseline and candidate use identical interpreter/dependencies, synthetic data, worker count, warmup and sample order; retain hashes, all samples and adverse results. Three alternating control/candidate runs, 100 warmup requests then at least 1,000 measured mixed requests each; separately include maximum 26 x 180 payloads, cache hit/miss, saturated/blocked paths and cancellation. Report p50/p95/p99/max, CPU, traced allocations and live task/thread counts. Do not compare a warm candidate against a cold baseline or weaken thresholds after measuring.

| Gate | Acceptance |
| --- | --- |
| Physical/admission invariants | <=8 total scoped SQL jobs and <=2 renderer jobs outstanding; <=32 observers; zero application waiters, <=8 dataset inflight identities, <=32 cache entries and <=32 terminal summaries. No additional permanent thread/task beyond the existing renderer executor. |
| Observer deadlines | Payload <=9.1 seconds in a healthy-loop fixture; render observation <=3.6 seconds; final authorization <=2.1 seconds; saturated refusal p99 <=50 ms. Separate explicit loop-stall calibrations must fail these gates as expected. |
| Loop responsiveness | Candidate p99 loop-lag increase <=5 ms and max increase <=25 ms versus matched control. Inject a 100 ms event-loop stall and require detector failure. |
| Service overhead | Synthetic cache-hit p95 increase <=5 ms, cold service orchestration increase <=10 ms excluding the explicitly measured extra registry call/render/SQL duration. End-to-end native p95 increase <=max(250 ms, 20% of matched baseline). All deadline gates still apply. |
| SQL cost | No additional personal-dataset statement per cache miss; no statement on cache hit/mode/picker. Normal delivery adds at most one final registry query beyond existing pre/post checks. Final fallback may require a separately counted recheck; ambiguous sends have no fallback retry. Native logical reads per unchanged dataset query <=5% over control, with row/plan identity recorded. |
| CPU/retention | Total synthetic workload CPU increase <=10%; residual coordinator allocations <=8 MiB over matched baseline after warm caches and full settlement. Exclude neither leaked tasks nor retained handles. Large payload/render bytes are reported separately with identical cache populations. Ten repeated stress cycles must show no monotonically growing residual task/handle/record count. |
| Drain | After last physical cleanup acknowledgment, coordinator drain completes within 250 ms (healthy loop). Blocked worker never yields success; unknown close always yields unsuccessful drain on repeated calls. No fixed total shutdown deadline claims to kill native SQL. |
| Diagnostics | Stats snapshot <=8 KiB, p99 copy <=2 ms at maximum records; report omission/truncation explicit; zero SQL/provider calls or background observer tasks. |

If a functional, native, cost or final-artifact gate fails, keep P01.6 open and return with evidence and a concrete design adjustment. Do not silently ship only the semaphore fix or disable final authorization to pass latency. The existing broader production-plan/index item is not closed by small synthetic native fixtures.

## Refactor and deferred dispositions

Fix in the proposed slice: read/inflight ownership, registry cleanup acknowledgment for stats, driver timeout, late authorization, render queue/drain, observer admission, cache publication races, repeatable teardown, signal failure propagation and the shared owned-thread global-cancellation gap. Preserve original failures and independent cleanup/delivery outcomes. No dead-code removal, metric refactor, persistent cache, SQL procedure rewrite or shared executor replacement is justified.

Use the K98 deferred-optimisation-capture structure below. These are reliability/architecture scope dispositions, not a substitute for security triage. Authorization findings above remain active P01.6 requirements. Existing P02/F20/F26 and the personal-stats SQL performance record retain their owners; reconcile these descriptions into existing tracking rather than create duplicate programme issues.

### Deferred Optimisation
- Area: `player_self_service/accounts_service.py`, `player_self_service/governor_dashboard_service.py`, `services/account_data_export_service.py`, their DALs and `stats_alerts/db.py`
- Type: architecture
- Description: Independent adjacent readers use unbounded/shared offloads or suppress close failures; the Account Data writer protects temporary-file cleanup but lacks a shared process-wide read/build admission and shutdown proof. These are not callers of personal-stats inflight ownership and must not be labelled covered by P01.6.
- Suggested Fix: Under P02 shared producer/read-budget and F26 ownership, inventory these operations, define physical admission and cleanup outcomes for each, retain the existing download writer's file custody and qualify real blocked threads before any common migration.
- Impact: high
- Risk: medium
- Dependencies: P02 scope and explicit implementation approval; existing Account Data/private-download contract; separate security routing for its eventual diff.

### Deferred Optimisation
- Area: `kvk/target_cache_repository.py:_active_owner_is_current`, `_wait_for_owner`; P02/F20 shared cache/file ownership
- Type: consistency
- Description: Target refresh ownership uses a persisted token and lease/process checks; lease expiry can make a live owner's claim ineligible and permit follower refresh. This source observation is not a fresh cross-process reproduction and is not a suitable model for personal-read physical ownership.
- Suggested Fix: Reconcile with P02's existing file/producer ownership census, reproduce expiry with a genuinely live blocked owner in both overlap orders, and select a physically confirmed release/fencing policy before changing target publication semantics.
- Impact: medium
- Risk: high
- Dependencies: P02/F20 owner, target publication contract, cross-process fixture and explicit approval; no target-cache runtime change in P01.6.

### Deferred Optimisation
- Area: `event_calendar/sql_lifecycle.py` reused by personal stats and registry strict reads
- Type: refactor
- Description: Generic SQL lifecycle behavior is currently located in the calendar package. Reusing it avoids duplicate rollback/close/error handling, but introduces a documented cross-domain helper dependency.
- Suggested Fix: If a later shared-DAL package adopts this contract, relocate it once with a compatibility re-export and complete existing calendar/read caller regression. Do not copy it per subsystem or change its semantics merely to improve placement.
- Impact: low
- Risk: medium
- Dependencies: Existing SqlSession/SqlOutcome contract and P01.5 tests; migration is not required for this bounded slice.

P03 owns original-intent continuation/unfinished-stage recovery and Rally F29; P04 owns convergence/history/notification policy; P05 owns cross-package confirmation. P01.4/P01.5 natural observations, fresh import/export/P03a.2 acceptance and partial incident history remain explicit. No closure is inferred from diagnostics, a released reservation or this passing baseline.

## Security review and approval gates

Current change: precise **documentation-only skip** via `k98-security-review-routing`. This packet changes no runtime, SQL, configuration, dependencies, permissions, deployment mechanism or persistence. Private synthetic harnesses are evidence, not product changes; no scan has been started. Applicable root SECURITY.md was reviewed; no nested security policy was found in the inspected source paths.

Future implementation touches private interactions, authorization, SQL, threads and shutdown: require `codex-security:security-diff-scan` on the exact final Bot base/head or frozen working patch, **Scan type: Changes; Deep off**. Reconfirm the actual mirror base when implementation begins; today's `7ba6c535...` is a source pin, not a promised future merge base. Review promoted private range separately where required; SQL has a documented no-diff skip unless its manifest changes. Do not infer a broader audit. Any captured security candidate follows triage; do not use the deferred list to accept it.

Four later release verdicts remain distinct: source qualification, actual-host custody readiness, installed release/startup and observed feature acceptance. Before a release handoff, derive exact changed paths and every existing ancestor from the immutable predecessor/target delta, including docs/archive. Collect fresh actual-host owner/ACL/inheritance/metadata/hash and applicable reparse/link/stream evidence; old repairs and clean Git do not establish custody. Preserve originals and resumable receipts. Use reviewed private main and protected updater only; no deployment/restart/recovery action is authorized here.

**Requested next decision:** approve the concrete Bot implementation and offline qualification scope above, including bounded fail-fast admission, stats registry cleanup, final delivery authorization, render ownership, shared owned-thread cancellation correction and teardown-result/signal prerequisites. Disposable SQL execution remains a separate exact-target approval after its guarded fixture is prepared. Publication/merge, live probes, deployment/restart and recovery remain outside this decision.

## Documentation validation receipt

Second-review amendment (5 November): architecture validation passed with zero Python changes; deferred-item validation passed for this packet; security-routing validation passed with zero errors/warnings. The routing validator initially rejected a positional filename (unsupported CLI argument); rerunning its supported repository invocation passed. Explicit-path test selection recommends generic smoke-import and command-registration checks; both are skipped for these prose-only amendments, which change no imports or commands. No runtime tests or native experiments were rerun. All 42 retained E100 document inventory entries remain unchanged; the only visible worktree change is this additive packet. The earlier packet-byte count/hash receipt predates this amendment.

Architecture validation passed (zero Python files changed); structured deferred validation passed for this packet; security-routing validation passed with zero errors/warnings; explicit-path test selection completed. Its generic smoke-import/command-registration recommendations are skipped for this prose-only change. Full pytest, native SQL, cost, security Changes scan and production actions are not needed to validate prose and have not been represented as candidate qualification. The separately executed 58-test source baseline and isolated reproductions are recorded above. After the shared shutdown findings, a justified additional baseline ran owned-operation/evidence, calendar SQL/ownership, startup/restart and final ZIP suites: **95 passed in 4.99 seconds**. These 153 existing passing tests are baseline evidence, not proof that the reproduced gaps are fixed.

Initial path verification caught an incorrect proposed existing complete-report test filename; the manifest now names the actual `tests/test_p013_complete_archive.py`. Final path/preservation checks passed: 33 unique test paths, including four explicitly new files and no missing existing tests; all 42 E100 status entries byte-identical or still absent for move sources. The expanded source parity inventory covers 86 files, all identical across the two Bot checkouts. No runtime/SQL files changed. This packet is the sole tracked-content candidate added by the review. No commit or publication occurred.


## Shared owned-thread caller appendix

Static import/call census identifies **53 production modules and 158 direct calls**, including the compatibility adapter. No additional module-qualified call pattern was found by the companion text search. Generic injected functions in bot startup, Stats, event loader and upload routing remain polymorphic; the helper must preserve their supplied arguments, ContextVars, return and exception identity. This is a source caller census, not a claim that all 158 runtime paths have been executed. The final candidate requires full regression plus barrier-based representative mutation/read/file/lifecycle cases; accepted business operations are not replayed in production.

| Source module | Direct calls | Behavior families to retain |
| --- | ---: | --- |
| `ark/ark_preference_service.py` | 1 | `get_profile_cached` |
| `ark/dal/rehydration_dal.py` | 1 | `_load_registration` |
| `bot_instance.py` | 2 | `func`, `install_configured_runtime` |
| `commands/import_resolution.py` | 1 | `call_recovery` |
| `commands/location_cmds.py` | 1 | `resolve_profile_lookup` |
| `core/recovery_lifecycle.py` | 1 | `observe_recovery` |
| `daily_KVK_overview_embed.py` | 4 | `load_existing_daily_KVK_overview_id`, `save_daily_KVK_overview_id`, `atomic_json_write` |
| `event_cache.py` | 1 | `save_event_cache` |
| `event_calendar/service.py` | 1 | `enter` |
| `event_calendar/sync_audit.py` | 2 | `audit_dal.start`, `audit_dal.finish` |
| `event_data_loader.py` | 1 | `sync_fn` |
| `event_scheduler.py` | 6 | `_read_dm_snapshot`, `save_dm_sent_tracker`, `save_dm_scheduled_tracker`, `delivery.store.rows` |
| `mge/mge_embed_manager.py` | 9 | `fetch_event_for_embed`, `public_names`, `update_event_embed_ids`, `fetch_event_publish_context`, `fetch_awards_with_signup_user`, `update_award_embed_ids`, `get_leadership_board_payload`, `update_leadership_embed_state` |
| `mge/mge_finalisation.py` | 25 | `manager.public_names`, `manager.get_leadership_board_payload`, `fetch_awards_with_signup_user`, `dal.transition`, `dal.targets`, `complete_event`, `fetch_event_for_embed`, `mge_completion_dal.fetch_due_event_ids_for_completion`, `dal.pending_events`, `dal.event_counts`, `dal.counts` |
| `mge/mge_publish_service.py` | 7 | `mge_publish_dal.fetch_event_publish_context`, `mge_publish_dal.apply_publish_atomic`, `mge_publish_dal.fetch_awards_with_signup_user`, `mge_publish_dal.update_award_embed_ids`, `mge_publish_dal.apply_unpublish_atomic` |
| `mge/mge_recovery.py` | 3 | `mge_recovery_dal.recovery_high_water`, `mge_recovery_dal.recovery_page`, `fetch_event_for_embed` |
| `mge/mge_roster_execution.py` | 1 | `_run_owned` |
| `mge/mge_scheduler.py` | 1 | `sync_mge_events_from_calendar` |
| `player_stats_cache.py` | 2 | `_build_and_persist_cache_sync`, `_build_last_kvk_cache_sync` |
| `proc_config_import.py` | 1 | `run_proc_config_import` |
| `processing_pipeline.py` | 3 | `register_run`, `notification_store().get` |
| `profile_cache.py` | 3 | `refresh_result`, `invalidate_one`, `get_profile_cached` |
| `rehydrate_views.py` | 1 | `save_view_tracker` |
| `services/event_delivery_service.py` | 4 | `store.get`, `store.begin`, `store.finish`, `store.rows` |
| `services/export_runtime_composition.py` | 2 | `drain_reports`, `bundle.drain` |
| `services/legacy_export_snapshot_service.py` | 1 | `function` |
| `services/operator_status_service.py` | 1 | `check_connection` |
| `services/optional_upload_lifecycle.py` | 2 | `owner.wait_closed`, `operation_diagnostics.shutdown` |
| `services/overview_delivery_service.py` | 1 | `delivery.store.rows` |
| `services/player_stats_cache_service.py` | 1 | `_verify_last` |
| `services/player_stats_startup.py` | 1 | `_verify_completion` |
| `services/processing_notification_service.py` | 1 | `notification_store().patch` |
| `services/processing_outcome_worker.py` | 1 | `recover_failures` |
| `services/processing_pipeline_receipts.py` | 10 | `dal.create`, `dal.start`, `result_evidence`, `dal.observe`, `guard.__enter__`, `guard.__exit__`, `sync_refresh_worker`, `get_default_target_cache_repository().refresh`, `run_post_import_stats_update` |
| `services/profile_cache_startup.py` | 1 | `_verify` |
| `services/tracked_view_store.py` | 4 | `self.read`, `enter`, `lock.__exit__`, `atomic_write_json` |
| `stats_alerts/processing_delivery.py` | 3 | `self.store.enter`, `self.store.acknowledge`, `self.store.update` |
| `stats_alerts/processing_notifications.py` | 14 | `is_currently_kvk`, `_current_cache_generation`, `store.patch`, `store.enter`, `store.acknowledge`, `store.update`, `notification_store().get`, `store.all`, `validate_runtime_scope`, `observe_pipeline`, `store.get`, `observe_export` |
| `stats_alerts/recovery_notifications.py` | 3 | `alert_rows`, `claim_alert`, `record_alert` |
| `stats_module.py` | 1 | `fn` |
| `target_utils.py` | 1 | `_refresh_name_owned` |
| `ui/views/mge_admin_completion_view.py` | 1 | `mge_report_service.build_post_event_summary` |
| `ui/views/mge_admin_view.py` | 2 | `switch_event_to_open`, `switch_event_to_fixed` |
| `ui/views/mge_commander_admin_view.py` | 2 | `mge_commander_service.save_commander_assignment`, `mge_commander_service.list_commanders_by_variant` |
| `ui/views/mge_publish_view.py` | 5 | `mge_publish_dal.fetch_awards_with_signup_user`, `mge_publish_service.generate_targets_from_rank1`, `mge_publish_service.override_target_score`, `mge_publish_dal.fetch_event_publish_context`, `mge_publish_dal.fetch_default_award_reminders_text` |
| `ui/views/mge_roster_builder_view.py` | 3 | `mge_roster_service.load_roster_state`, `get_signup_review_pool`, `mge_roster_service.mge_roster_dal.fetch_award_by_id` |
| `ui/views/mge_rules_edit_view.py` | 3 | `mge_rules_service.update_event_rules_text`, `mge_rules_service.get_event_rules_context`, `mge_rules_service.reset_event_rules_to_mode_default` |
| `ui/views/mge_signup_modal.py` | 3 | `mge_signup_service.create_signup`, `mge_signup_service.edit_signup`, `mge_signup_service.get_event_context` |
| `ui/views/mge_signup_view.py` | 2 | `mge_signup_service.withdraw_signup` |
| `ui/views/mge_simplified_leadership_view.py` | 2 | `mge_simplified_leadership_service.get_leadership_board_payload`, `mge_signup_dal.fetch_event_signup_context` |
| `ui/views/mge_simplified_signup_form_view.py` | 2 | `mge_signup_service.create_signup`, `mge_signup_service.edit_signup` |
| `ui/views/recovery_view.py` | 2 | `call_recovery`, `unavailable_report` |
| `upload_routes/player_location_route.py` | 1 | `deps.warm_profile_cache` |
