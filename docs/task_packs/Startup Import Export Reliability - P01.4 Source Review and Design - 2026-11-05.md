# P01.4 source review and proposed design

> **Current E91, 5 November 2026:** The [complete local qualification receipt](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Complete%20Local%20Qualification%20-%202026-11-05.md) records the full original P01.4 design implemented and qualified locally, with both optional workers enabled in the unpublished candidate. Cost, physical-drain, diagnostic-priority, updater, regression and Changes-review gates passed. No CSV scope was deferred. Publication/deployment and natural-activity acceptance remain outstanding; earlier E88-E90 disabled/pending statements below are historical. Existing changes and archive moves are preserved.

> **E90, 5 November 2026:** The [whole-solution design](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Whole%20Solution%20Design%20-%202026-11-05.md) supersedes the recommendation to adopt SQL now and defer file logging. Preserve the full P01.4 scope: settle shared lifecycle and diagnostic isolation, then qualify both workers together. New controls identify a confound in the earlier file lag benchmark, not a qualification pass. Both workers remain disabled. Default recommendation is one complete deployment after validation; an earlier outcome/custody-only candidate remains an optional delivery choice. This review changes documentation only; implementation of the revised design and all publication/deployment remain pending.

> **E89, 5 November 2026:** The [adoption decision packet](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Adoption%20Decision%20-%202026-11-05.md) records completed SQL-worker qualification, startup/close-failure corrections and the concrete file-logging choices. Both worker gates remain off pending the decision. The failed file gate and updater release blocker remain visible; P01.4 is not complete under its original scope. No publication or deployment occurred.

> **E88, 5 November 2026:** Local P01.4 implementation and disposable development SQL qualification are recorded in the [implementation receipt](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Local%20Implementation%20and%20Qualification%20-%202026-11-05.md). Earlier approval-pending text is historical. Both optional workers remain disabled: file cost failed; SQL qualification/readiness is incomplete. P01.4 remains open, and updater source-pin tests block release. No publication or deployment occurred.

Date: 5 November 2026. **REVIEW COMPLETE; IMPLEMENTATION NOT APPROVED.**

## Scope summary and recommendation

F17 and F30 remain present in the pinned current source. Recommend three independently reviewable slices: **A, truthful upload outcomes; B, fallback download logging and callback ownership; C, bounded optional SQL audit**. A and B have direct correctness value. C removes awaited optional SQL from upload progress but introduces a physical worker and must pass native timeout, contention, resource and shutdown gates before adoption. None of these gates has passed merely because this design exists.

Use one small, pure outcome mapping through existing domain services. Keep confirmed ingestion, physical settlement, diagnostic availability, refresh/cache work, export handoff and notification evidence distinct. No generic workflow executor, automatic import retry, new provider probe or automatic audit reconciliation is proposed. Required immutable file, producer, capture and queue ownership receipts retain their existing authority.

This packet implements the documentation/review authority in the [handover](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Handover%20and%20Scope%20-%202026-11-05.md). It does not approve source/test/SQL edits, publication, merge, installation or live operations. The [P01.3 closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.3%20Closeout%20-%202026-11-05.md) remains settled; Report 75 and its complete-ZIP acceptance are not being rerun. Carry forward the [full documentation manifest](Startup%20Import%20Export%20Reliability%20-%20Documentation%20Carry-forward%20-%202026-11-05.md), including its five archive moves.

## Source authority and evidence limits

| Checkout | Observed HEAD | Status / use |
| --- | --- | --- |
| Root `C:/discord_file_downloader` | `a025adb7a69aac321fd62794b871ed5903338f44` | Intentional modified/untracked documentation; current phase authority only. Preserved. |
| `.codex_artifacts/a1b-updater-correction` | `65ad4fa6d765a88b45cfbb6bba8b6b32af802f6e` | Clean; primary runtime source inspected. |
| `.codex_artifacts/p1-mge-mirror-review` | `2f2883a98dfc30dff0373dd38800bb4795f1b652` | Clean; separate scrubbed history, comparison source. |
| `C:/K98-bot-SQL-Server` | `7e91989f619deb46836194c7e705b0a9eb2ebe11` | Clean; authoritative local SQL definitions. No SQL connection used. |

The private reviewed head and deployed merge `6ec393f71626d15fcb8c50c840854fb681d5f09e` have the same local Git tree, `dd775fb0c2b2775772de38905343ebb2cf0328f9`. This verifies available source equivalence, not a new production observation or a refreshed remote-main claim. Re-pin before implementation. The 27-file comparison finds one raw-byte difference (`core/owned_work.py`, line endings); Git's normalized comparison is empty. Do not describe raw checkout bytes as universally identical.

Private receipt directory: `.codex_artifacts/p014-scope-20261105/`. `source-and-boundary-receipt.json` contains heads/status, 27 source hashes, 20 SQL-definition hashes and isolated checks. `review_receipt.py` extracts only the named functions with inert dependencies; it does not import the bot or contact SQL/Discord. Results on unchanged code:

- CSV permission failure: **zero callback entries, one queue acknowledgement**, no active job remaining.
- Held CSV await: **zero callback entries while the processing lock is held**; releasing the fixture allows one callback and one acknowledgement.
- Two accepted attachments plus one unsupported attachment: route enqueues the same message twice. The worker's unfiltered attachment loop therefore has six attachment visits. This last count is composed source behavior, not six executed imports in the fixture.

The first unquoted PowerShell `HEAD^{tree}` read failed argument parsing; the quoted read above succeeded. Failed exploratory file searches and this shell error made no changes. No runtime pytest, native timing, schema application, permission check against a live database, or fresh whole-flow import/export was performed.

## Affected areas and current behavior

Paths/line numbers below refer to the pinned private source, unless marked SQL.

| Boundary | Source-confirmed behavior | Proposed disposition |
| --- | --- | --- |
| `DL_bot.py:355`, upload wiring at 530-667 | `_offload_callable` selects one backend before invocation; `prefer_process` is compatibility-only. It currently delegates to a thread helper whose cancellation can return before a thread ends. Configured KVK-source routing precedes legacy upload routing. | Preserve selection, arguments, source admission and one invocation. At affected upload service boundaries retain/drain already entered work using `core.owned_work`; do not add fallback execution after failure or rewrite every global offload caller. |
| `upload_routes/honor_route.py`, `honor_importer.py:162` | Honor commits header/raw rows before returning `(kvk_no, scan_id)`. Route sends success before terminal audit, then refreshes. Send failure enters the generic import-failure handler; refresh exception marks aggregate failed. Failed optional row-count preparse displays zero even if ingestion succeeds. | A: freeze confirmed import result first; counts unavailable remain unknown; audit/refresh/send cannot downgrade it. Keep actual parse/ingest validation. |
| `upload_routes/prekvk_route.py`, `prekvk_importer.py:220` | Metadata distinguishes accepted/duplicate/rejected/failed and carries scan/history identity. Refresh exception calls `fail_audit_batch`; success notification is also inside the outer import-error scope. Duplicate selection partly relies on note text. | A: use structured status when present, retaining legacy compatibility fallback; preserve duplicate semantics and skip downstream work for a genuine duplicate. Separate notification and refresh outcomes. |
| `upload_routes/player_location_route.py`, `services/location_import_service.py:259`, `commands/location_cmds.py:244` | Auto route replaces; manual command merges. Both can label the batch failed after a refresh signal exception while returning successful ingestion. Auto route's notification exception renders a false import failure. | A: include manual service and actual command result, not only auto upload. Keep merge/replace distinct, permission/size checks and caller results compatible. |
| `services/location_refresh_signal.py:23`, auto-route profile warming | The signal helper catches its own event-set failure; a normal return is not proof of cache refresh. Auto-route profile warming is a separate later operation. | A: distinguish signal attempted/acknowledged from actual profile refresh. Do not claim a successful cache rebuild from `None`. Add a compatible result/observation seam only for this caller family. |
| `upload_routes/weekly_activity_route.py`, `weekly_activity_importer.py:393` | Import transaction includes snapshot/rows/delta/daily rebuild/completion evidence. Route terminal success precedes notification and catches send failure. Audit calls still await `asyncio.to_thread`. Backup phase labels scheduling as completed. Returned row count counts delta rows. | A/C: reference for send isolation; do not assume audit latency is bounded. Keep snapshot-row counts distinct from delta-row counts and scheduling acceptance distinct from completed backup. |
| `kvk/dal/kvk_all_import_dal.py:325`, especially 541-568 | Stage has its own commit. Ingest/recompute and writer checkpoint precede final commit. Negative-count query then runs on the connection before success is returned. Query failure escapes; absent scalar becomes zero. | A: construct acknowledged commit evidence before optional diagnostic read; catch only that read/result-conversion failure, return nullable count plus diagnostic disposition. Do not catch a checkpoint or commit failure as success. |
| `kvk_all_importer.py`, `services/legacy_export_snapshot_service.py:432,506,1101` | `admitted_writer` returns only after `finish_writer`; capture/spool/close can fail after the business commit. `export_preparation_id` is added after successful finalisation. Negative-read failure currently also enters uncertainty handling. | A: a narrowly typed KVK result/exception must retain confirmed commit identity across finalisation failure. Keep original exception and owner disposition; never fabricate capture completion or export permission. Required capture recovery remains P03. |
| `upload_routes/kvk_all_route.py` | `int(result['negatives'])` requires a known count. A success-send exception prevents auto-export scheduling and still emits a red import failure, although its audit may remain completed. Task creation is recorded as export scheduling completed. | A: render unknown count explicitly; isolate summary send; existing enabled export handoff must not depend on notification success. Preserve exact preparation ID; distinguish task accepted, durable job acknowledgement and actual export. No new export retry. |
| Five domain audit adapters, `services/import_audit_service.py`, `stats/dal/import_audit_dal.py` | Exceptions usually become `None`/false; latency and physical lifetime are not isolated. Four adapters and KVK use awaited thread runners. DAL uses a shared five-second login factory and sets no statement timeout. | C: opt-in bounded transport, typed pending handles and dedicated connection policy; retain synchronous API for unmigrated callers. A changes outcome mapping without claiming C's latency gate is solved. |
| `utils.py:628`, `bot_helpers.py:291` | Downloader appends success/failure CSV before returning; queue appends success again under staging lock before active-job registration. The downloader catches I/O errors but still waits on slow logging. | B: retain one optional download row outside the processing lock through bounded admission; remove duplicate worker write. Do not change shared `append_csv_line` into a swallow-all helper. |
| `upload_routes/fallback_queue_route.py:32`, worker attachment loop | One whole message enqueued per accepted attachment; worker then iterates all attachments. Existing test explicitly expects two identical queued messages. Active-job key is only `(channel, filename)` and is removed before the next sequential visit. | B related correction, approval required: enqueue each message once and process only its accepted attachment snapshot, with one UI job per selected attachment. This closes immediate duplicate dispatch, not durable dedup across Discord redelivery/restart. |
| `services/fallback_upload_staging_service.py:69`, `services/fallback_import_service.py:99,141` | Unique private staging; processing lock; unconditional final cleanup. Required Ready publication uses unique filename, fsync, manifest and rename. | B: keep private bytes until actual reader settlement; keep required publication failures fatal. Audit loss cannot bypass Ready/claim/hash checks. |
| `processing_pipeline.py`, `services/processing_pipeline_receipts.py`, `stats_module.py:290`, `core/queue_lifecycle.py`, `bot_instance.py:1008` | Coordinated stages shield/drain work and preserve durable receipts. Compatibility offload paths have weaker cancellation/retry behavior. Queue drain deadline is not proof of physical settlement. Notification registration currently gates processing (F19). | Test both coordinated and compatibility boundaries; retain entered staged-input readers before cleanup. No blanket shield around admin prompts and no claim that `queue.join()` proves SQL completion. F19 stays P04; compatibility-wide executor redesign stays separately owned. |

### Equivalent callers and shared-helper classification

All shared generic-audit consumers were searched: Honor, Pre-KVK, Location, Weekly, KVK-all, Rally, MGE results, Inventory and `stats_module.py`. Rally separates result/backup/notification; its F29 attempt/dedup problem remains P03. MGE audit wrappers are synchronous inside importer work. Inventory performs a latest-external-ID lookup across view lifetimes. Fallback stats audit includes SQL-owned phases. **Do not globally replace generic synchronous APIs or redefine these other domains' aggregate semantics** as a shortcut. Their adapters/tests must remain compatible; any opt-in later needs its own caller review.

`append_csv_line` consumers were classified:

| Caller | Role | P01.4 action |
| --- | --- | --- |
| Downloader and queue worker | Optional download projection; same CSV row duplicated | B owns removing duplication and decoupling latency. |
| `admin_helpers.py:176,188,287` | Input, processing-summary and failed-log projections; exceptions caught | Leave signatures and semantics; broader notification latency belongs P04/P01.6. |
| `core/restart_operations.py:114` | Optional restart CSV after fsynced restart flag/exit-code writes | Leave required writes and current error isolation; no restart redesign. |
| `bot_instance.py:1639` | Post-restart notification/audit projection | Leave current behavior. |
| `commands/admin_cmds.py`, startup/log-backup inventory | CSV readers/maintenance consumers | Preserve five-column download CSV shape and log-reader route. Do not treat CSV existence as custody proof. |

Reuse `core.owned_work.drain_awaitable`/`drain_thread` for finite entered work, `upload_routes.common.resolve_notify_channel` and `schedule_best_effort`, typed `DeliveryResult`/`DeliveryAttempt`, `core.operation_evidence.optional`, and existing diagnostic/report retention machinery. The existing diagnostic sink is a bounded file-projection writer, **not a SQL job executor**. The general logging `SimpleQueue` is unbounded; neither is a safe place to enqueue SQL callbacks. A bounded file-log worker and a bounded SQL writer are distinct optional owners, introduced only in B/C after qualification, at most one of each rather than a worker per upload/domain.

## Architecture direction and outcome contract

Put the pure representation/mapping in a small `services/upload_outcome_service.py` (proposed), used by existing domain services. It accepts primitive evidence and returns presentation/audit facts; it neither calls Discord nor executes work. Routes retain matching, access checks, attachment reads and rendering. DAL retains SQL. New bounded writer lifecycle belongs in service modules; root files only wire lifecycle/admission. Extract only outcome orchestration touched by this change, not the full importer estate.

The minimal result carries:

- Ingestion disposition: `not_started`, `rejected`, `duplicate`, `committed`, `failed_confirmed`, or `outcome_unconfirmed`; actual domain identity and nullable counts, with each count's meaning.
- Physical execution: queued/entered/draining/settled, plus original exception identity. Caller cancellation does not mean a database rollback.
- Optional audit: local correlation, pending/bound/unavailable/partial, dropped count, last confirmed SQL acknowledgement. SQL ID is absent until actually returned and validated.
- Independent phases: parse observation, refresh signal, profile/stat refresh, backup scheduling, negative-count diagnostic, summary delivery and export handoff. Stage `scheduled` is not `completed` work.

Freeze confirmed ingestion as soon as the importer acknowledges it. Complete the ingestion audit projection before notification; later phase writes must not set aggregate status back to `staged` or `failed`. Failed diagnostic serialization, clocks, hashing, enqueue, callbacks and logging must not escape into the ingestion exception scope. Preserve useful failure evidence without recursively logging sink failures.

Only use SQL-supported status values. Known committed ingestion maps to `completed`; duplicate to `duplicate`; confirmed failure/rejection to the appropriate existing failure/skipped value. Unknown commit has **no fabricated successful or failed terminal aggregate**: leave its last nonterminal batch status and attach bounded versioned details such as `business_outcome=outcome_unconfirmed`. A phase can be `failed` for an observation failure with the business uncertainty explicitly recorded; never invent an SQL `unknown` or `completed_with_warning` value. Apply this new aggregate contract only to the named P01.4 domain adapters.

Typed stats delivery can contain mixed component results. Preserve each attempt's acknowledged/unknown/failed/skipped evidence. A legacy `None` send result is unverified, not a delivered receipt. Do not send a second red import error after an uncertain success-send, and do not retry notification or ingestion from these observations. Refresh exceptions should be visible as a warning in the final summary when it can be sent; the primary line still says ingestion completed. Keep existing channel visibility and mention policy.

### Concrete before / after examples

| Trigger | Current result | Required result |
| --- | --- | --- |
| Honor commits scan `16:42`; success-send raises | Failed audit and attempted red import failure | Ingestion completed for `16:42`; summary delivery unconfirmed/failed according to receipt evidence; one ingest and no blind second send. |
| Pre-KVK accepted 800 rows; stats refresh throws | Batch failed | Completed ingestion, 800 rows and original scan; refresh failed separately, warning summary. |
| Location merge/replace returns counts; refresh signal fails | Successful user result with failed batch | Successful ingestion in both manual and automatic paths; signal failure separate; no assertion that profile cache refreshed. |
| Honor row-count preparse fails; real importer succeeds | Displayed zero rows | Committed scan retained; row count unavailable unless authoritative importer evidence supplies it. |
| Weekly backup task is accepted but later fails | Scheduling phase looks completed | Ingestion completed; scheduling accepted, actual backup outcome unknown until evidence exists. No new backup observer solely to fill this field. |
| KVK commits 1,000 rows; negative-count query raises or returns no scalar | Import call fails, or zero negatives inferred | 1,000 committed rows/scan retained; negative count unavailable. Capture/export remain separate required stages. |
| KVK commit succeeds but capture/spool finalisation fails | Exception can hide returned rows | Committed ingestion plus capture pending/unconfirmed, exact preparation when known; no export submission without existing required evidence; original failure retained. |
| Audit start reply lost after server insert | Caller has no batch ref | Local UUID remains; SQL audit unavailable. No new ID, replayed start or business delay. |
| CSV denied/slow/full | Callback absent or delayed under processing lock | Callback runs once with staged bytes; download audit unavailable/partial; one acknowledgement after callback settlement. |
| Two eligible files plus `notes.txt` | Message queued twice and every attachment visited | One message admission; two eligible callbacks, each once; no callback for `notes.txt`; one message acknowledgement. |

These are fixture examples, not production incidents or claimed new test results.

## SQL / persistence review

**Verdict: existing schema supports the proposed diagnostic separation; no SQL migration is recommended. Bot implementation and native connection qualification remain pending.** Local definitions establish schema shape, not installation, live privileges or latency.

| Authoritative object(s) | Contract and identity |
| --- | --- |
| `dbo.ImportAuditBatch` | `ImportAuditBatchId bigint IDENTITY`; `CorrelationId uniqueidentifier NOT NULL` with unique index/constraint `UQ_ImportAuditBatch_CorrelationId`. Actor/source IDs, filename/hash, external-table/id, nullable counts, UTC timestamps and JSON details exist. |
| `dbo.ImportAuditPhase` | Identity phase ID; FK to actual batch ID; phase name/status, nullable counts/timing/error/JSON. `IX_ImportAuditPhase_BatchPhase` supports batch history. Phase inserts are not idempotent by an event UUID. |
| `dbo.usp_ImportAudit_StartBatch` | Accepts supplied `@CorrelationId`; performs INSERT then returns SQL batch ID/correlation. It is not an upsert or retry protocol. A duplicate correlation raises; losing the result does not prove INSERT rolled back. |
| `dbo.usp_ImportAudit_RecordPhase` | Inserts phase and updates batch in one transaction. Optional `@SetBatchStatus` can overwrite a terminal status; P01.4 producer ordering and post-commit omission of that argument must prevent regression. |
| `dbo.usp_ImportAudit_CompleteBatch`, `dbo.usp_ImportAudit_FailBatch` | Updates by actual SQL batch ID. Counts/external identity/details use `COALESCE`; details replace rather than merge. FailBatch sets error fields; do not invoke it for optional failure after commit. |
| `dbo.KVK_Honor_Scan`, `dbo.KVK_Honor_AllPlayers_Raw` | Honor business key `(KVK_NO, ScanID)`; header `row_count` is authoritative. Audit external identity uses `kvk:scan`. |
| `dbo.PreKvk_Scan`, `dbo.PreKvk_Scores`, `dbo.PreKvk_ImportHistory` | Accepted scan uses KVK/ScanID; history has `HistoryID`, import status and optional scan. Do not equate a failed/duplicate history entry with a committed scan. Preserve current file-hash dedup. |
| `dbo.PlayerLocation_Staging`, `dbo.PlayerLocation`, `dbo.sp_ImportPlayerLocationFromStaging`, `dbo.sp_ReplacePlayerLocationFromStaging` | Manual proc returns `StagingRows,TotalTracked`; replace returns `ImportedRows,TotalTracked`, and no result for empty source. No durable import-batch identity exists here. Do not invent one or infer unchanged/zero from a missing result. Preserve empty-source refusal/no-replace behavior. |
| `dbo.AllianceActivitySnapshotHeader/Row`, `dbo.AllianceActivityDelta/Daily`, `dbo.usp_SetAllianceActivitySnapshotCompletion` | SnapshotId identity; week/file SHA1 uniqueness. Business completion counts/basis share the import transaction. Generic audit `completed` is not proof that data completeness is `COMPLETE`; preserve `PARTIAL` and missing/invalid evidence. |
| `KVK.KVK_AllPlayers_Stage`, `KVK.sp_KVK_AllPlayers_Ingest`, `KVK.sp_KVK_Recompute_Windows`, `KVK.KVK_Scan` | Staging token separate from final `(KVK_NO,ScanID)`; proc returns KVK/scan/row count. SQL checks outer transaction ownership; Python retains final ingest/recompute/checkpoint commit. Do not move that commit to protect a diagnostic read. |
| `KVK.KVK_Ingest_Negatives` | Exact query by KVK_NO/ScanID; supporting `IX_KVK_Negatives`. Failed query or missing scalar is unknown, not zero. Keep lookup optional; no extra producer-session lock or retry. |
| `dbo.ExportPreparation` and current snapshot DAL | PreparationID, owner/fence/version, GenerationJson, spool identity/hash/bytes and state distinguish committed output from captured/materialized output. Audit correlation is never a substitute for preparation authority. Schema snapshot itself says not to deploy it. |

The audit schema's batch values are queued/started/staged/converted/procedure_started/downstream_rebuild_started/completed/failed/skipped/duplicate/cancelled/rolled_back. Phase values are started/completed/failed/skipped/duplicate/cancelled/rolled_back. JSON must be valid. No new ProcConfig row, UDT, staging column, view or index is needed for the proposed audit query/mapping. Business object names were checked against SQL sources; this is not a fresh exhaustive correctness audit of every column or procedure body.

**Correction to the design assumption:** the exact correlation column/index exists, but `stats/dal/import_audit_dal.py` has no correlation reader. Its only lookup selects the newest batch by import kind/external table/external ID. If a later explicit audit investigation needs lookup, add a parameterized `WHERE CorrelationId = ?` DAL read, validate returned correlation/kind/source identity, and never use the latest-external-ID reader for rebinding. Do not automatically query or retry on the upload path. C may include the read contract and unit tests; no new operator command or recovery operation is required.

Location normalises result values and closes its connection after `commit()` inside a broad error path; malformed count/close failures can therefore mask commit. A should prepare typed result interpretation before commit where possible and preserve an acknowledged commit with counts unavailable/cleanup unconfirmed afterward. Do not infer success from merely reaching `commit()`, swallow a required cleanup failure, or redesign the transaction. If this cannot be done locally without changing the importer contract, split it as an explicit A sub-slice rather than silently declaring caller coverage complete.

## C: bounded optional audit design and cost gate

Recommended transport is **opt-in** for the five named upload families plus manual Location. Keep generic direct writers for Inventory/MGE/Rally/fallback callers until separately migrated. DAL offers a dedicated audit connection factory with unchanged authentication selection, proposed login/statement limits of 2 seconds each, and no changes to `_conn_trusted` globally. Autocommit setup failure must stop this audit operation; never continue with an unknown transaction policy. No business connection, writer session or application lock is borrowed.

1. Allocate a UUID local handle before first offer. Handle stores no invented integer SQL ID. Bound, validate and copy primitive metadata before offer; no arbitrary callback, workbook/DataFrame or Discord object enters the writer queue.
2. One physical SQL writer consumes start/phase/terminal envelopes in per-handle sequence. Start binds only the acknowledged, validated SQL ID and exact correlation. Start acknowledgement uncertainty makes dependent writes unavailable for that attempt. No automatic start replay, phase retry or reconnection replay.
3. Admission is nonwaiting: full queue, lock contention, closed service, invalid payload or serialization failure changes diagnostic availability only. Lost intermediate phase can yield partial history while a later genuine terminal record still carries true business counts; expose the loss. A lost start suppresses dependent writes; a terminal cannot overtake earlier admitted events.
4. Before optional I/O, retain a bounded local projection with first meaningful failure, latest outcome and loss counts. Reuse existing diagnostic persistence/report paths with a small explicit schema extension; report reads remain passive. Local admission is not durable acknowledgement, and process death can lose unwritten optional audit. No audit queue replay on restart. Restore historical projections as historical, not active handles or work.
5. Hash work remains off the event loop, reusing bytes already read. Do not retain upload bytes in the SQL queue or synchronously hash an unbounded workbook in the offer path. Prefer fingerprint work in the existing finite parse/offload boundary. If unavailable within that boundary/budget, audit hash is null with an explicit diagnostic reason; required immutable business hashes are never omitted.
6. Shutdown closes business admission and drains entered business work first; then closes audit admission, marks discarded unstarted envelopes, and joins the one entered writer. A timeout does not certify physical closure. Failure to meet qualified shutdown bounds blocks adoption; no daemon-only escape, untracked executor task or replacement writer while one is still alive.

Proposed budgets to approve and measure, not measured results:

| Resource/boundary | Limit / acceptance |
| --- | --- |
| SQL queue | 128 envelopes maximum, <=8 KiB each, <=1 MiB encoded queued payload; one physical writer total. |
| Local handles | 256 active diagnostic contexts; refusing a new context does not refuse business work. Reclaim terminal contexts after delivery/unavailability, never evict active business ownership. |
| Optional projections | Reuse existing <=512 operations, <=32 KiB per operation / 16 MiB total and 30-day/capacity retention. Explicit loss/coverage markers; no separate unlimited history store. |
| Download CSV worker (B) | At most 64 detached five-column rows, <=2 KiB each, one physical file writer; no source-file content/handle retained. Reject oversize diagnostic row, not upload. Preserve CSV quoting. |
| Offer path | p95 <=1 ms, p99 <=5 ms; no SQL/network/filesystem and no waiting mutex. Full/closed/error offer has the same bound. |
| Matched business workload | At least 30 paired repetitions per important path; <=2% median and <=5% p95 added elapsed time; <=5 ms p95 loop-lag increase. Include both cold setup and sustained pressure. |
| Physical optional I/O | Proposed SQL login 2 s and statement 2 s; entered operation plus close must settle within a measured 5 s envelope in bounded failure fixtures. File write/close likewise <=5 s in qualified environment. No queued-work drain proportional to all 128 timeouts: discard unstarted optional writes at shutdown with loss evidence. |
| External cost | No extra business/provider requests, imports, retries or owner-lock hold. SQL write count no greater than existing phases plus explicitly approved outcome phase records; no polling or automatic lookup. |

Use barriers to prove processing progresses while sinks are blocked, not a sleep-based test that assumes it. Measure object retention/RSS as well as encoded payload; the byte caps do not bound arbitrary Python overhead by themselves. A shared SQL queue may lose audit across domains during outage; that is an explicit optional-evidence tradeoff, preferable to five blocked writer threads. Do not promise no database contention: RecordPhase does update audit rows. Bound it on its own connection and qualify overlap with business work.

Native timeout/connection-close behavior cannot be established from source or mocks. C must stop before rollout if the real driver fixture cannot prove it. Do not increase limits, weaken assertions, put SQL into the existing diagnostic sink, or fall back to synchronous audit to make acceptance pass. Retain adverse runs. The rejected P01.2b observer remains rejected.

## B: queue ownership and acknowledgement design

Keep one message queue item with a frozen list of eligible attachment identities, or an equivalent immutable selection attached to the item; adapt worker/tests explicitly. Prefer that small item over a generic queue engine. Enqueue once, produce one UI row per selected attachment, and process each selection once under the existing serialization lock. Same-filename attachments keep distinct staging paths/attachment identity. Active-job lifetime covers actual callback work, not optional logging.

Move download-row construction/offer after download completion and outside `processing_lock`; downloader returns based on download result even if logging fails, saturates or stalls. Remove the second queue write. File-log writer never opens the staged input. CSV record failure must not initiate another download. Keep the existing download failure return and notification distinct from processing errors.

One successful `queue.get()` has exactly one `task_done()` in its `finally`, including callback failure/cancellation. A cancelled `get()` has none. A queue acknowledgement means this in-memory item was handled; it is not proof of business success or durable exactly-once delivery. After a callback error, remaining selected attachments must have an explicit skipped/unattempted outcome, not disappear as implied success; no automatic retry policy is introduced.

Cancellation before callback entry can clean an unused staged file. Cancellation during an actual file reader must retain the staging owner/lock/active-job entry until that reader settles, then clean and acknowledge once. Use finite owned-work boundaries in the existing pipeline; do not shield the whole `handle_file_processing` call, which includes admin prompts and notifications. Test runtime-enabled and compatibility behavior. If the existing stage receipt already drains, reuse it instead of nesting a competing owner. Do not delete in-use input merely because the outer coroutine ended.

Restart does not reconstruct optional log/audit queues as business work. Required Ready manifest, receipt, source hash and producer state remain unchanged. Durable cross-message redelivery deduplication and full queue redesign remain P03/the existing queue backlog; fixing the immediate double-enqueue must not be sold as exactly-once processing across crashes.

## Refactor triggers and related corrections

Fix within approved P01.4 slices: shared outcome mapping instead of repeated broad exception scopes; manual Location parity; KVK nullable diagnostics and post-commit result preservation; notification-independent enabled export handoff; accurate scheduled-versus-delivered wording; duplicate download logging; duplicate message admission/attachment selection; local physical ownership before staging cleanup; exact audit correlation/real ID binding; tests that currently assert misleading failure or duplicate admission.

SQL stays in DAL/importer data-access seams. There is no new direct command/view SQL. Existing root importers contain legacy SQL and orchestration; do not relocate their entire transaction bodies in this slice. The selected service extraction is for outcome mapping and optional scheduling. No dead-code removal is justified by this review. Existing unknown/error/cleanup branches remain meaningful.

The following captures use the deferred-capture skill's required structure. They are scope records, not new security findings or newly authorized backlog implementation.

### Deferred Optimisation
- Area: `stats_module.py:_offload_callable_py`, compatibility pipeline/offload callers
- Type: consistency
- Description: Coordinated runtime uses drain_thread once, while the compatibility path catches execution failures and falls through to another backend. The current upload adapter is already once-only. A P01.4 outcome fix must not silently certify the wider compatibility estate.
- Suggested Fix: P03/shared execution follow-up should select one backend before invocation and qualify real caller cancellation/drain and repeated side effects. P01.4 must repair any directly exercised staged-input boundary needed for its own acceptance, without a global helper rewrite.
- Impact: high
- Risk: high
- Dependencies: Original-intent recovery ownership, existing pipeline receipts, deterministic pre/post-entry tests; no production replay.

### Deferred Optimisation
- Area: `services/mge_results_import_audit_service.py`, `services/inventory_import_audit_service.py`, `services/rally_forts_import_audit_service.py`, fallback audit callers
- Type: performance
- Description: Other generic-audit clients still perform synchronous or awaited optional writes and have distinct importer/view-lifetime contracts. A global API conversion would mix these lifecycles into P01.4.
- Suggested Fix: After C qualification, assess each family for opt-in bounded audit with caller-level outcome, correlation, shutdown and retention tests. Retain P03's Rally F29 ownership and Inventory's existing orchestration deferred item.
- Impact: medium
- Risk: high
- Dependencies: C transport qualification and a separately approved domain slice; do not rebind Inventory with a pending local handle.

### Deferred Optimisation
- Area: Honor/Pre-KVK/Location/Weekly root importer data-access modules
- Type: architecture
- Description: Legacy importers retain SQL/orchestration and inconsistent result/cleanup boundaries. Location's directly relevant post-commit interpretation belongs in A; broader extraction and general scan-concurrency changes would alter transaction contracts beyond this review.
- Suggested Fix: Domain-specific service/DAL extraction after P01.4, retaining exact transaction/identity/completeness semantics and testing post-commit logging/cleanup failure separately from business failure.
- Impact: medium
- Risk: high
- Dependencies: Authoritative SQL review and separate domain scope; no inferred rollback or new idempotency policy.

Existing programme ownership is unchanged: P02 holder/contention/F09; P03 durable intent/recovery and Rally F29; P04 F19 journal admission/retention and delivery convergence; P05 final whole-repository confirmation; P01.5 calendar; P01.6 other diagnostics. Six incidents and fresh whole-flow acceptance remain open. Do not relabel them all P02 or clear them to satisfy these gates.

## Test strategy and acceptance gates

| Gate | Required negative-path / delivered-outcome assertion |
| --- | --- |
| A1 route matrix | Actual Honor/Pre-KVK/Location/Weekly/KVK handlers plus manual Location command/service. Precommit rejection/failure, duplicate, acknowledged commit, unknown commit, optional audit exception, refresh exception, typed mixed/unknown delivery, summary send failure. Assert final message title/fields, emitted audit parameters, domain identity/counts and exactly one importer invocation. |
| A2 KVK layered result | Real DAL with fake transaction cursor through importer/writer wrapper and route: negative query execute/fetch/conversion failure and no scalar after confirmed commit; no count becomes zero. Separate checkpoint failure, commit-ack loss, postcommit capture/spool/close failure, scheduler admission failure and durable handoff acknowledgement. Verify owner retained/disposed by existing authority and no export without exact preparation. |
| A3 Location / counts | Merge and replace result shapes; no-row return; missing/malformed count; close failure after commit; signal failure and profile refresh failure independently. Original commit stays known where acknowledged; no invented total or receipt. Weekly snapshot rows and delta rows retain different meanings. |
| A4 observation versus physical work | Cancel before dispatch and after a barrier proves physical entry; hold thread until released; competitor excluded while owned; cancellation propagates only after settlement. Preserve exact return/original exception. No alternate backend execution. |
| B1 full queue caller | Real route + worker + staging composition with temporary files. CSV raise/slow/full/closed/oversize; handler starts once despite audit trouble; active job removal/ack/cleanup order; actual input bytes correct. |
| B2 multiplicity and shutdown | Two supported plus unsupported attachments, same filename/different bytes, callback failure mid-message, cancellation while get/waiting for lock/inside reader, failed download, cleanup failure. Each selected callback once; unsupported zero; ack once per get; no delete before physical reader ends. Preserve live-queue save/restore behavior. |
| B3 required custody | Missing/invalid Ready manifest, interrupted rename, bad immutable identity/hash/receipt still refuses unsafe SQL entry. Diagnostic loss cannot suppress these failures. |
| C1 identity and ordering | Delayed start, lost acknowledgement after simulated insert, failed start, mismatched correlation/SQL ID, interleaved batches, phase/full-queue loss, terminal ordering. No dependent SQL write without actual binding; no duplicate start/phase replay; last committed business result stays intact. |
| C2 transport isolation | Hold SQL writer and file writer independently; prove business callback/offload still runs. Max queue/context/payload/object retention, nonwaiting offer, no upload bytes retained, one physical writer, no spawning on overload. |
| C3 persistence/report | First failure then successful later observation; restart with partial/malformed/missing diagnostic state; no replay. Actual ordinary and complete reports preserve bounded projection, source/age/partial flags, redaction, existing component priority, final ZIP member hashes/sizes and frozen continuation. Test delivered ZIP, not collector alone. |
| C4 native cost/drain | Driver login/statement/close refusal/timeout plus contention fixtures on separately authorized disposable SQL; file writer failure/close fixture. Matched workload budgets above; physical thread count, SQL sessions, queue high-water, loss and memory bounded; no false drain receipt. |
| Compatibility | Unmigrated MGE/Inventory/Rally/stats audit tests retain signatures/results; existing delivery, offload, KVK source-admission, receipts, live-queue and archive tests pass. |

Existing tests to extend/run from the **current implementation checkout**, not the old root runtime:

```text
tests/test_honor_upload_route.py
tests/test_prekvk_upload_route.py
tests/test_player_location_upload_route.py
tests/test_location_import_service.py
tests/test_weekly_activity_upload_route.py
tests/test_kvk_all_upload_route.py
tests/test_kvk_all_import_dal.py
tests/test_kvk_all_importer.py
tests/test_import_audit_service.py
tests/test_import_audit_dal.py
tests/test_honor_import_audit_service.py
tests/test_prekvk_import_audit_service.py
tests/test_weekly_activity_import_audit_service.py
tests/test_kvk_all_import_audit_service.py
tests/test_bot_helpers_fallback_worker.py
tests/test_fallback_queue_route.py
tests/test_fallback_upload_staging_service.py
tests/test_fallback_import_service.py
tests/test_fallback_import_dal.py
tests/test_utils_live_queue.py
tests/test_live_queue_persistence.py
tests/test_dl_bot_offload_callable.py
tests/test_stats_delivery_outcomes.py
tests/test_processing_pipeline_receipts.py
tests/test_processing_pipeline_run_step_and_normalization.py
tests/test_processing_pipeline.py
tests/test_stats_module.py
tests/test_stats_module_cancelled.py
tests/test_stats_module_timeout.py
tests/test_coordination_lifecycle.py
tests/test_p013_complete_archive.py
tests/test_p012a_evidence_contract.py
tests/test_p012a_recoverable_reports.py
```

Update old expectations explicitly: Honor success-send failure -> failed terminal; Pre-KVK refresh -> failed batch; Location refresh -> failed batch; Honor unavailable preparse -> zero; fallback two accepted attachments -> two identical queue entries. Preserve old failing runs before correction. Add proposed `test_upload_outcome_service.py`, `test_optional_import_audit_worker.py` and file-log worker coverage only when implementation is approved. Discover actual command integration, pipeline, owned-work, diagnostic/archive test names from the final checkout and include them in the per-PR manifest.

Use `python scripts/select_tests.py` with explicit proposed/changed paths, then add this risk matrix; path selection alone does not cover these root/upload modules. After implementation: focused regressions, scoped lint/format/type, architecture/deferred/security-routing validators, smoke imports and command registration with synthetic test configuration, then full pytest/log-hygiene for shared helper/lifecycle changes. Re-run only affected checks after fixes, and require final-head CI/review disposition before release. No test should contact a production provider or use live credentials.

For this documentation deliverable, runtime tests/type/smoke/registration and native probes are skipped: no runtime/test/config/SQL edits. Documentation/link/path checks and inert boundary checks are the evidence. No green claim about proposed behavior is made.

## Security review decision

Current target: this packet and its handover/tracker/carry-forward links, Markdown only. **Documented skip** under `k98-security-review-routing`: no executable, permissions, config, dependency, input, data-access or persistence behavior changed; no scan launched.

For A/B/C source changes, use `codex-security:security-diff-scan` with **Scan type: Changes, Deep off**, separate exact Bot mirror/private base/head or uncommitted patch targets. Upload input, SQL values, file custody, diagnostic redaction, actor visibility and restart ownership are sensitive. Pin final changes then route; this packet does not supply a fictitious future head. A SQL repository Changes review is needed only if a later approved design actually changes SQL. No routine codebase audit is selected.

## Recommended PR slicing and approval decisions

1. **A: outcomes and direct postcommit boundaries.** Five upload routes plus manual Location; pure mapping; KVK/Location result preservation; accurate summary/refresh/scheduling semantics; targeted owned-work adoption. No new audit worker in this PR. Include the complete prior documentation carry-forward. If KVK capture finalisation preservation materially changes shared writer authority, split it into an A2 dependency with its own review; do not widen shared behavior silently.
2. **B: fallback admission and optional download logging.** One admission per message/eligible selection; remove duplicate CSV; one bounded optional file writer with lifecycle owner; staging-reader cancellation and ack invariants. No durable redelivery dedup or notification-journal redesign. Its file-writer cost/drain gate is required independently of C.
3. **C: optional SQL audit.** Opt-in domain adapters, pending-handle/SQL-ID distinction, exact correlation DAL contract, connection budgets, local projection and actual report artifacts, lifecycle/cost qualification. Do not call P01.4 complete if this remains unqualified. No SQL migration expected.

Decisions requested together before implementation:

- Approve ingestion-only aggregate semantics and the proposed warning/unknown wording across automatic and manual callers, including nullable diagnostic counts and truthful scheduled-versus-delivered stages.
- Approve the related B correction from per-attachment message enqueue to one selected-message item. Preserve legacy single-file behavior; explicitly change the existing test that enshrines duplicate admission.
- Approve **two maximum new physical optional writers across B+C**, the stated bounds and failure policy, subject to native cost/drain gates. If costs fail, stop that slice and return with retained evidence; A can remain independently reviewable. Do not silently discard requested diagnostic availability or replace it with unbounded background tasks.
- Approve only implementation/qualification of these local slices. Publication, merge, SQL application, incident repair and deployment require their own current authorization. Later natural-activity acceptance should compare actual user summary, business receipt, audit phases and delivered reports without replaying a committed upload.

No approval to start the review is needed. The pause now is for the requested concrete P01.4 implementation decision, as required by the handover and architecture-scope workflow.

## Conditional references and validation receipt

Applied architecture-scope, SQL-validation, test-selection, security-routing and deferred-capture skills. Read core engineering/execution/testing/refactor/deferred guidance; helper review, Honor/Weekly import references, shutdown/diagnostic ownership sections, Windows custody contract and root security context. Programme Scope/Tracker/P01 Design, F17/F30 tracing, action census, coverage, final sweep and delivery boundaries were reconciled with the P01.3 closeout/design/implementation/ZIP correction. No promotion procedure was executed or production-state claim refreshed.

Documentation validation results and exact changed-file hashes are retained in `.codex_artifacts/p014-scope-20261105/document-validation.json`. Pre-edit copies preserve the three existing documents amended for navigation. The older E86 receipt remains intact. Source checkouts and SQL remain unmodified.

Validation completed: four Markdown files; 77 relative links and 33 existing test paths resolve; architecture (zero Python files), deferred format (four documents), explicit-path test selection, security routing (zero errors/warnings), and diff whitespace checks pass. Selected source files remain unchanged; all 27 mirror/private comparisons match after newline normalization. Runtime/native tests remain explicitly unrun. The selector's generic smoke/registration recommendations are skipped for this prose-only delta.
