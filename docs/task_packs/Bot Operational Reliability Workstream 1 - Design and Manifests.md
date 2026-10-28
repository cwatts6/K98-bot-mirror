# WS1 — ProcConfig import reliability and truthful completion

Programme ownership updated on 2026-09-09: **Bot Operational Reliability WS1**, formerly
Discord Embed Payload Safety Phase 2L. [Programme deliverables and priority gate](Bot%20Operational%20Reliability%20-%20Programme%20Pack.md).
Technical design and runtime/test/SQL manifests are proposals awaiting approval. This documentation
update does not approve them or select WS1 ahead of other programmes. The completed
[backlog assessment](Backlog%20Priority%20Assessment%20-%202026-09-09.md) records the operator's
order: KVK Source Migration first, private inventory second, WS1 third. Any proved KVK prerequisite
exception needs approval. References to
completed audit checks describe the original audit baseline, not fresh implementation validation.
The documentation manifest below is adjusted for the canonical programme paths.

Audit and design for approval, 9 September 2026. Implementation is not approved.

This repository copy preserves the completed audit/design, originally prepared as a standalone artifact. The 2026-09-09 programme-boundary update changes documentation only; no runtime, test, SQL, configuration, calendar, queue, dispatch or deployment behavior changed. The user's audit-only instruction is authoritative; implementation instructions in historical packs are historical context, not current authorization.

## 1. Entry evidence and limits

| Check | Evidence and verdict |
|---|---|
| Mirror PR #262 | GitHub connector independently reports merged at 2026-09-09 12:06:38 UTC, merge commit `134fcee529766cb258fb644b5ca0a9bad47af226`. |
| Production PR #569 | Independently reports merged at 12:07:06 UTC, merge commit `1e72949dc69f1a1e5a529dbf1951039fe0ba74a6`. |
| Current remote mirror main | `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`, message `Mirror: 2026-09-09T12:07:31Z from 1e72949d`. This later mirror publication is different from the PR merge commit. |
| Current remote production main | `1e72949dc69f1a1e5a529dbf1951039fe0ba74a6`. |
| Local bot workspace | `C:\discord_file_downloader`, branch `main`, HEAD `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; empty `git status --porcelain=v1`. This is the mirror checkout, not proof of the bot-machine checkout. |
| SQL source | `C:\K98-bot-SQL-Server`, branch `main`, HEAD `fc0e94ebd2e0a98286069c8a8b71365dd5178657`; empty status. Local `origin/main` points there. Live database definitions were not queried. |
| Deployed SHA, clean bot checkout and restart association | Closed by operator-supplied deployment records in this conversation: bot-machine `git rev-parse HEAD` = `1e72949dc69f1a1e5a529dbf1951039fe0ba74a6`, matching verified production main; `git status --short` has no output. Associated 2026-09-09 logs show graceful restart invoked 12:08:56.672, teardown 12:08:57.530, queues drained and state persisted, new child PID 4800 and singleton lock 12:09:05.143, Discord ready 12:09:10.755, full startup completed 12:09:15.539. Times are recorded as supplied; contemporaneous clock/UTC scheduler records align with UTC. This is operator-supplied host evidence, not a separate remote shell inspection. Implementation approval remains pending. |

Sources: [mirror PR #262](https://github.com/cwatts6/K98-bot-mirror/pull/262), [production PR #569](https://github.com/cwatts6/K98-bot/pull/569). CLI access failed with Git credential and GitHub authentication errors; the connected GitHub API supplied the successful independent checks. The old PR bodies and archived documents still say merges pending; their live merge fields supersede that historical text.

Phase 2K remains delivered and operator-smoke accepted on production candidate `36208765bf7200fa6855f3892e6b32d43b23bccf`, mirror `2d892cefcfdfa0a8263efe69997bf292503b23aa`. Its 3514 passed / 2 skipped result is historical accepted evidence, not a WS1 test run. Preserve Phase 2J removal, H/I sessions/defaults, K's receipt/claim distinction and no automatic retry. The final documentation promotion's interrupted redundant pytest rerun is disclosed in the PR; it is not a new passing run.

Read context: current core engineering/execution/testing/refactor/deferred references, WS1 pack, archived Phase 2K pack/starter, original embed audit, active/resolved deferred records, helper review guide, diagnostics/startup runbooks, promotion guide, target publication contract, root security policy, and applicable skill checklists. No nested bot security policy or SQL AGENTS/SECURITY file was found by the scoped inventories.

Post-merge natural startup observation supplied by the operator: registration reported primary=36, grouped_subcommands_detected=100, no duplicate slash names, secondary command paths disabled, and unchanged command cache. ProcConfig background import started 12:09:14.890; callable entry 12:09:16.190; all seven table insert messages appeared; incremental KVK 16 target execution was logged at 12:09:30.102; manifest persistence and import success were logged at 12:09:30.498; the parent reported `success=True report_keys=None` at 12:09:30.764. No HY000 appears in this supplied run. This is a clean natural observation under the existing implementation, not evidence that WS1 is fixed or that nested SQL completion has been independently established. The missing structured report at the parent remains consistent with the audited transport/reporting gap. Preserve the separate 11:46:51 HY000 failure evidence and the accepted Phase 2K smoke provenance.

The supplied restart also shows tracked-view rehydration cancelled at 12:09:24.054 after its 10-second timeout, followed by a monitor completion line. Record this under the separately captured lifecycle/timeout truthfulness work; do not broaden WS1 or claim all startup background jobs completed successfully from the full-startup marker. This does not reopen the accepted Phase 2K smoke gate. No live rerun or state repair was requested or performed.

## 2. Findings and current execution path

### Caller and transport matrix

All paths below are runtime unless explicitly marked otherwise. The source search found no implementation of `run_maintenance_step`; that name occurs only as a task-pack helper suggestion.

| Entry / source | Input and execution boundary | Current return / handling | Required correction |
|---|---|---|---|
| `proc_config_import.py:582`, direct Python API | `dry_run: bool=False`; synchronous importer | `(bool, dict)`. Several early paths omit `report.success`; some failures bypass manifest and terminal telemetry. | Keep the tuple API but make its first value an actual bool derived from one finalized v2 report. |
| `commands/admin_cmds.py:1000`, `/ops import_proc_config` | Existing admin-notify-channel decorator and administrator permission; ephemeral defer; `dry_run=False`, process preferred | Unpacks offload return, uses truthiness; assumes failure report supports `.get`. | Consume explicit normalized outcome; bounded private status; preserve decorators/options/destination. Notification failure cannot rerun import. |
| `bot_instance.py:2035`, startup wrapper | `schedule_bg`, jitter, 180-second `_with_timeout`; process-preferred async wrapper | Logs `success=ok`. Only if wrapper unavailable before invocation, uses `run_blocking` executor; fallback accepts tuple first element or truthiness. | Strict result; maintain one startup submission; surface unknown cancellation and possible surviving worker. Do not claim `orphaned_offload_possible=False` for this import when not proven. |
| `processing_pipeline.py:515`, SQL-success branch | Only when `success_excel`; preflight through local `run_step`, outer 180 seconds, then named `proc_import` maintenance step with `PROC_IMPORT_TIMEOUT` | Headroom failure/timeout/error skips import; normal result coerced with `bool(ok)`. Failure text used to guess orphan status. | Typed failed/not-started preflight result, then normalized import result; status must not depend on matching the word timeout. |
| Same module:690, SQL-not-success branch | Still requires `success_excel`; skips external headroom wait, runs same named maintenance operation | Same bool coercion; separate duplicated presentation code. | Same ProcConfig normalization/presentation as other branch. Preserve existing branch admission. |
| `file_utils.py:2039`, maintenance isolation | String `proc_import`, importer callable or `module:function`; normalizes scalar args to list; configured thread/process | Process returns transport's pair; thread ProcConfig special case calls importer with no args, uses `bool(res)`, returns text. Thus false tuple is true and dry-run is lost. | ProcConfig-only strict adapter, preserve args including bool dry-run, preserve domain report and backend evidence. |
| `file_utils.py:1831`, maintenance subprocess | Builds argv / serialized arguments, then `create_subprocess_exec`; communicates with timeout | Parses first plausible JSON event, considers rc 0 success, may return `(worker_result, envelope)`; nonzero loses structured report into text. Large native result may disappear behind `result_summary`. | Strict terminal ProcConfig envelope selected by identity, version and marker, independent of log snippets; reconcile rc with domain status on both zero/nonzero paths. |
| `maintenance_worker.py:268`, `do_proc_import` | Imports callable then invokes sync/async once in nominal path | Any non-raising value is logged/emitted as success, exit 0, including `(False, report)`. | Domain normalization before success log/telemetry/exit. |
| `maintenance_worker.py:514`, callable spec | Allowlist check, module import, reconstruct args, sync/async invocation | Any return means success / exit 0. `_run_coroutine_safely` recreates and reruns the callable after any RuntimeError. | ProcConfig result contract; correct shared coroutine helper to choose loop before execution and never recreate after entry. Preserve allowlist. |
| `proc_config_import.py:1162`, async offload API | Chooses isolation helper, then nominal callable starter, then thread, then `asyncio.to_thread` | Assumes isolation returns native tuple. Starter fallback is called/awaited with an incompatible API: actual starter is synchronous, takes module/function and returns process metadata, not completion. | Resolve compatible backend before submission. Use awaited callable subprocess helper when appropriate; never await or interpret a launch receipt as import completion. |
| `scripts/callable_worker.py`, standalone callable worker | Module/function plus JSON args; sync invocation or `asyncio.run` | Always success for non-raising return; uses key `return`, while parent extracts only `result`. | ProcConfig-specific canonical envelope/exit; unrelated generic callable behavior remains compatible. |
| `file_utils.py:1172`, callable subprocess | Builds callable worker argv then spawns | Waits before draining pipes; potential pipe backpressure. rc-only success and key mismatch lose domain meaning. Cancellation rethrows without confirmed child shutdown. | ProcConfig strict mode drains pipes concurrently, preserves report/exit and bounded cleanup. Test generic compatibility. |
| `file_utils.run_step` / `run_blocking_in_thread` | Sync offload or await coroutine; native returns; `wait_for` optional | No automatic retry here. Thread cancellation/timeout does not stop synchronous work. | Reuse; classify transport completion separately from import success. Add scoped ProcConfig handling only where transport status otherwise misleads. |
| `processing_pipeline.run_step` | Separate local adapter; sync optional offload, async/awaitable support | Different signature from shared `run_step` (`offload_sync_to_thread` is consumed locally). | Retain existing external preflight adapter; do not blindly swap helpers or forward that flag to the SQL callable. |
| `process_utils.py` | PID identity/liveness helpers, re-exported by file_utils | No import execution or result parsing. | Review-only; process disappearance is not SQL rollback proof. |

The direct API is not a standalone `__main__` CLI. The actual CLI entrypoints are the two worker scripts. Generic launch/offload helpers also serve unrelated functions; a nonempty generic return is not globally redefined as a ProcConfig result.

### Import, resources and commits

1. Configuration validation and optional required-preflight availability checks precede work. Dry-run reads/validates Sheets and does not intentionally open SQL. Current thread argument loss violates this boundary.
2. Real import reads `ProcConfig!A1:J`, requires nonempty data and `KVK_NO`, then opens `_conn_import()` with autocommit false (configured driver, five-second connection timeout). The retry decorator retries connection establishment only; Sheets helpers separately retry reads. Neither is authorization to replay import SQL.
3. `preflight_or_raise` checks log health; unreadable health is currently tolerated, while known high usage or LOG_BACKUP can reject. `log_backup_context` and optional DBCC snapshots use SQL cursors. Pipeline preflight is distinct: `preflight_from_env_sync` can start the approved log-backup job and poll. It is not a read-only smoke command and was not executed here.
4. Transactional mode writes staging/upsert, target bands, exemptions, KVK details, weights, windows and camp map, then commits. Empty auxiliary dataframes currently mean helper no-op, not truncate; preserve that behavior. Preserve modes: bands/exemptions/details truncate; weights/windows/camp map delete-by-KVK. `_tx_tables` is computed but does not drive this fixed implementation.
5. Nontransactional mode currently writes only ProcConfig staging/upsert. The staging pre-delete commits independently; insertion/upsert then depend on final caller commit. This mode does not import the six auxiliary tables. Do not silently expand it.
6. `sheet_importer.write_df_to_staging_and_upsert` reports execute success before draining; nontransactional caller does not validate returned stage errors. `write_df_to_table` catches exceptions into dictionaries, its TRUNCATE fallback includes the commit inside the catch boundary, and `executemany_batched` suppresses commit failures. These patterns cannot establish committed work. ProcConfig must use strict helper semantics; unrelated consumers need compatibility tests rather than a global silent policy change.
7. `committed_tables` is never populated. The transaction error block unconditionally resets `partial_commits=[]`, even if rollback failed or the nontransactional pre-delete committed. Post-commit failures later bypass even that projection. This is an accounting defect.
8. Latest-KVK selection goes through `stats_alerts.kvk_meta` -> `kvk_state.get_latest_kvk_details` -> lifecycle DAL; it also reads maximum scan for fighting-state derivation, although import only uses KVK number/name. Fallback is max KVK in the imported ProcConfig frame, then full target refresh. Preserve selection, not incidental fighting-state work. The existing latest-detail DAL query and mapper are reusable.
9. Target refresh reuses the import connection/cursor, switches autocommit true, executes master, sets `targets_master_executed=True`, and restores mode in `finally` without consuming all results. Restoration can override the earlier exception. This directly matches the reported HY000 location. Root cause is strongly supported by source and ODBC contract; the exact live token sequence/driver trace at 11:46:51 has not been reproduced.
10. Normal finalization computes success and writes timestamp-to-the-second manifest; several exceptional paths only update last report. Persistence errors are suppressed, `persisted_to` is added after serialization, and cleanup happens after the returned result is decided. Cursor/connection close failures disappear. Reports can collide or refer to stale runs.

ODBC requires progressing through the result stream; an execute return or cursor close alone is not a completion receipt. The nested diagnostic rowset/error case is concrete. [Microsoft SQLMoreResults](https://learn.microsoft.com/en-us/sql/relational-databases/native-client-odbc-api/sqlmoreresults?view=sql-server-ver15). Pyodbc documents multiple-set traversal and distinguishes PRINT diagnostics from data; its context managers must not be assumed to explicitly close cursors/connections. [Pyodbc Cursor documentation](https://github.com/mkleehammer/pyodbc/wiki/Cursor).

## 3. Authoritative SQL contract

SQL verdict: **safe after bot-side fixes and deployment evidence checks; SQL change manifest empty**. No live SQL verification or execution is claimed.

| Procedure | Parameters, nested work and completion meaning |
|---|---|
| `dbo.sp_Upsert_ProcConfig_From_Staging` | No parameters; EXECUTE AS OWNER; NOCOUNT ON; MERGE pairs update/insert config keys from staging, OUTPUT INTO `ProcConfig_AuditLog` (not a returned success rowset). No autonomous transaction; belongs to caller transaction. |
| `dbo.sp_TARGETS_MASTER` | `@KVK int=NULL`, `@ForceRepublish bit=0`, `@RepublishReason nvarchar(400)=NULL`, EXECUTE AS CALLER. Rejects any ambient transaction; validates selectors/force semantics; retains same Python parameterized incremental call or parameterless full call. No force/reason is added. |
| `dbo.CREATE_DELTA_TABLES` | No parameters. Session applock nested under master's delta lock; independently commits delta inserts before later maintenance/log writes. Missing/out-of-sync prerequisites raise. The out-of-sync branch returns `TableName, MaxDeltaOrder, TotalRows` before RAISERROR. No-new-scan branch returns normally without new delta writes. Index maintenance errors may be PRINT-only warnings. |
| Master per-KVK loop | Transaction applock; configured scan selection; existing Official publication is preserved while Excel output refreshes. New publication generates targets/output/export, validates rows, appends publication/header rows, switches IsCurrent, updates legacy view, validates bot view, then commits that KVK. Full mode can commit earlier KVKs before a later failure. |
| `dbo.sp_Prep_TargetTable` | `@KVK int, @Scan int`. Dynamic quoted `dbo.TARGETS_<KVK>` create/truncate and parameterized insertion from `KingdomScanData4`, bands and exemptions. No client success rowset or independent commit. |
| `dbo.sp_ExcelOutput_ByKVK` | `@KVK int, @Scan int`. Reads window ConfigKeys, validates source scans, begins nested transaction, truncates `STAGING_STATS`, builds ranking/snapshot/output, indexes and statistics, refreshes views, records final output completion; commits nested transaction, catches and rolls back on error. A nested commit is not an independent outer publication commit. |
| `dbo.sp_Build_Prekvk_And_Honor_Rankings` | No parameters; rebuilds ranked PreKvk/Honor tables with SELECT INTO, indexes, RETURN 0. These SELECTs are data writes, not client receipts. |
| `dbo.sp_Create_Excel_For_Kvk_Indexes` | `@FullTableName nvarchar(260), @TableBase sysname`; dynamic index DDL, PRINT, RETURN 0; bad parameters raise/RETURN 1. Missing table has a documented normal skip. No additional nested application procedure. |
| `dbo.sp_Refresh_View_EXCEL_FOR_KVK_All` | No parameters; constructs All/Started views through dynamic SQL. Embedded SELECT text defines views, not a client result set. Empty-source branch creates empty views and returns. |
| `dbo.usp_RecordKvkFinalReportCompletion` | `@KVKNo int, @FinalScanOrder int, @FinalizationBasis nvarchar(24)=LIVE_OUTPUT, @FinalDataAtUtc datetime2(0)=NULL`. Validates final output rows; updates/inserts `KVKFinalReportHeader`; owns a transaction only if none exists. No client completion receipt. |
| `dbo.sp_Prep_ExcelOutputTable` | `@KVK int, @Scan int`; creates/inserts `EXCEL_OUTPUT_KVK_TARGETS_<KVK>` using special KVK 3/4 branches or prior-two-KVK outputs. No independent commit. |
| `dbo.sp_Prep_ExcelExportTable` | `@KVK int`; create/truncate from export template, positional INSERT SELECT TOP 350 with exemptions; no independent commit. |

System procedures reached: `sys.sp_getapplock`, `sys.sp_releaseapplock`, `sys.sp_executesql` (some unqualified spellings). Dynamic statements are DDL, INSERT/SELECT INTO, metadata assignments/output parameters and view definitions. PRINT, RETURN codes and row-count tokens do not by themselves prove successful completion. Master has no durable per-stage receipt exposed to this caller. A successful full stream means the procedure completed according to its current skip/warning rules, not that every KVK was republished. No per-KVK committed list will be invented from PRINT text, generated rows before outer commit, or current tables after another run.

Important output effects are `STAGING_STATS`, ranked PreKvk/Honor tables, `TARGETS_<KVK>`, `EXCEL_FOR_KVK_<KVK>`, `EXCEL_OUTPUT_KVK_TARGETS_<KVK>`, `EXCEL_EXPORT_KVK_TARGETS_<KVK>`, All/Started/legacy views, `KVKFinalReportHeader`, and `KVK_Target_Publication` / `KVK_Target_Publication_Row`. `v_KVK_TARGETS_FOR_BOT` joins the current publication and rows using PublicationId and exposes publication version/signature. Its contract is not changed.

Exact imported schema alignment:

| Table | Relevant verified columns / constraints |
|---|---|
| `dbo.ProcConfig_Staging` | Ten nullable ints: KVK_NO, LASTKVKEND, MATCHMAKING_SCAN, PRE_PASS_4_SCAN, PASS4END, PASS6END, PASS7END, KVK_END_SCAN, CURRENTKVK3, DRAFTSCAN. |
| `dbo.ProcConfig` | PK `(KVKVersion int, ConfigKey varchar(50))`; ConfigValue float nullable, LastUpdated datetime nullable; key/version indexes. This is key/value configuration, not a guessed procedure dispatch table. |
| `dbo.ProcConfig_AuditLog` | Identity AuditID; OperationType, KVKVersion, ConfigKey, OldValue, NewValue; ChangeDate default. Upsert audit belongs to same transaction. |
| `dbo.KVKTargetBands` | PK KVKVersion/MinPower; MinPower bigint; KillTarget, MinKillTarget, DeadTarget ints. |
| `dbo.EXEMPT_FROM_STATS` | GovernorID bigint NOT NULL, GovernorName nchar(255), Exempt bit, KVK_NO float. Preserve bigint identity and existing exemption semantics. |
| `dbo.KVK_Details` | Eleven imported fields including KVK_NO, KVK_NAME, registration/start/end dates, MATCHMAKING_SCAN, KVK_END_SCAN, NEXT_KVK_NO, MATCHMAKING_START_DATE, FIGHTING_START_DATE, PASS4_START_SCAN. CreatedAt has UTC default. |
| `KVK.KVK_DKPWeights` | KVK_NO; three float weights; EffectiveFromUTC default; composite PK. |
| `KVK.KVK_Windows` | KVK_NO/WindowName PK; WindowSeq tinyint, StartScanID/EndScanID ints, Notes nvarchar(200); UpdatedAtUTC default; scan range checks. |
| `KVK.KVK_CampMap` | KVK_NO/Kingdom PK; CampID tinyint checked 1..8, CampName nvarchar(40) NOT NULL. |

No new UDT, columns, indexes, configuration rows or schema assumptions are required. Live Sheets headers/values and deployed SQL definition parity remain outside this read-only source audit. Preserve existing coercion and empty-input policies; actual database rejection becomes truthful failure.

## 4. Proposed complete architecture

The public root importer stays a compatibility adapter and retains existing Sheet parsing/coercion helpers. New orchestration belongs in `services/proc_config_import_service.py`; pure contract/normalization/presentation in `services/proc_config_import_outcomes.py`; connection, writes, transaction evidence and master execution in `stats/dal/proc_config_import_dal.py`. A small `core/sql_results.py` drains results and is reusable by these SQL boundaries. It has no connection factory, retries, logging of row data, or commit ownership.

The service receives explicit dependencies from the root adapter for configuration, Sheet reads and legacy test seams; it does not import the root module back. Avoid circular root/service/file_utils imports. Worker recognition uses fixed ProcConfig operation/spec identities and imports the dependency-light outcome module only. No universal result framework or whole-module rewrite.

### Resource sequence

1. Make one report and server-generated UUID run ID before validation; allocate resource references immediately so all acquired handles have a finally owner. Validate actual bool dry_run before submission.
2. Preserve preflight policy and read retries. Explicitly close the cursors opened in `log_health.get_log_health` and `preflight_from_env_sync`; expose cleanup failures separately to the ProcConfig caller through an opt-in cleanup observer. Do not convert optional unreadable health into a false passed check. Do not change backup thresholds/job policy.
3. Import DAL opens the existing import connection factory and owns the connection. All its cursors close explicitly, including diagnostic cursors. Drain pending successful statements before the next statement, commit, or any mode transition; use `description` to decide whether to fetch, bounded `fetchmany(1000)` until exhausted, then `nextset()` until false. Do not swallow later fetch/nextset errors. On an error, stop consuming as a success path, retain the primary exception and attempt cleanup without re-executing the batch.
4. Use strict opt-in Sheet-writer behavior for ProcConfig: propagate commit failures, retain statement/batch commit evidence, check both staging/upsert outcomes in both modes, and do not let a commit exception trigger DELETE fallback. In this strict mode do not try destructive TRUNCATE-to-DELETE fallback after an ambiguous statement error. Record failure and let the owning transaction rollback once. Generic other-consumer defaults remain compatible.
5. For transactional import, mark attempted table stages staged until the final commit returns successfully. Only then record the committed unit containing staging, ProcConfig/audit and actual nonempty auxiliary writes. A thrown commit is unknown even if a subsequent rollback call returns; that rollback cannot prove that the server did not already commit before the connection error.
6. For nontransactional import, retain the confirmed staging-clear commit separately from final insertion/upsert commit. A later rollback applies only to remaining work; committed deletion is still real work even when zero rows were inserted. Do not call the six auxiliary imports in this mode.
7. Resolve latest KVK using the existing latest-details query and mapper under an explicitly owned read connection in the lifecycle DAL; expose the strict resource observation needed by this importer without changing default lifecycle/H/I semantics. The ProcConfig service uses only the number/name and existing DataFrame/full fallback. Do not perform unrelated fighting-state/MAX-scan work merely to select a target KVK. Retain the same connection principal used by the existing metadata read.
8. Target EXEC uses a separately owned fresh import-principal connection. Set autocommit true before its first statement/cursor execution. The import commit must already be confirmed; never put master into an ambient transaction. Execute exactly the existing parameterized incremental or full form, drain through terminal no-more-results, then mark target procedure completed. There is no need to restore autocommit on this exclusively owned connection, which is closed rather than reused. This removes the unsafe shared-connection restoration entirely; no MARS/configuration workaround.
9. On target execute/fetch/nextset error after entry, mark completion unknown unless evidence specifically proves not-started or failed completion. Preserve import commit and record that delta/earlier KVK commits may exist. Never invoke master again. Close target cursor then connection; close the import connection independently in outer finalization. No rollback of the import connection is described as undoing autonomous target work.
10. Finalize only after resource cleanup has been observed. Preserve primary SQL exception, rollback failure, cursor-close failure and connection-close failure as separate safe records; cleanup does not overwrite the primary error or erase confirmed commits. If a failed resource makes it unsafe to continue before target entry, stop and mark target not-started. Required cleanup failure after known completion makes overall partial, not success.

The fresh target connection adds one connection establishment per real import. Keep the configured driver/principal and connection-only retry policy; retrying connection acquisition before any target statement is not replaying target work. Failure to establish that connection means import committed, target not-started, overall partial.

### One execution after submission

Resolve availability and call signature before work submission. Safe fallback is limited to a helper/backend proven unavailable before submitting work (for example missing helper or worker file); malformed arguments fail validation rather than being guessed. The preferred maintenance backend remains the normal route. The callable alternative must use `run_callable_subprocess(module, function, args)`, not `start_callable_offload` launch metadata.

Once subprocess creation or thread scheduling may have entered, there is one selected backend execution and no fallback/recreation on false result, exception, RuntimeError, timeout, cancellation, serialization failure, missing envelope, or broken notification. A spawn await failing without a trustworthy pre-submission classification is unknown. A missing module reported by an already-spawned child does not trigger another backend in this invocation.

Choose event-loop execution before calling an async callable. `_run_coroutine_safely` must not catch a callable RuntimeError and recreate it. A synchronous callable returning an awaitable is awaited once where the adapter supports that contract; it is never invoked again to obtain another awaitable.

On timeout/cancellation, mark the observer's outcome unknown after submission, retain any already observed commit/result evidence, and propagate CancelledError. Process mode makes a bounded terminate/kill/reap attempt (five seconds graceful plus five seconds forced maximum); incomplete cleanup remains unknown and is reported. Thread mode cannot kill synchronous work: retain its task/future for observational late-result logging, do not reuse the SQL handles from the cancelling thread, and do not start a replacement. The worker owns its eventual cleanup. A late result is a separate observation for the same run ID; it does not initiate downstream publication, retry, or silently rewrite an already returned unknown into success.

These are per-invocation guarantees, not global exactly-once processing. Independent admin/startup/pipeline invocations can still overlap; restart can initiate its normal independent startup import. No durable import admission, deduplication, retry queue, recovery command, reservation or global monkeypatch is introduced.

## 5. Exact outcome and transport contract

Use a frozen `ProcImportOutcome` record internally, serialized to plain JSON primitives. Do not let implicit bool of the record grant success; require `.success`. Public importer and offload API remain `(success: bool, report: dict)`.

Required v2 report fields:

```text
version: "proc_import_v2"
run_id: UUID string
timestamp: UTC ISO-8601 start; finished_at: UTC ISO-8601
dry_run: bool; transactional: bool; duration_sec: nonnegative number
success: bool
status: "success" | "failed" | "partial" | "unknown"
reason: bounded stable code
submission: "not_submitted" | "submitted" | "entered" | "unknown"
preflight: "passed" | "failed" | "unavailable" | "not_run"
import_state: "not_started" | "validated_only" | "committed" |
              "rolled_back" | "partial" | "unknown"
targets: {state: "not_started" | "completed" | "failed" | "unknown" | "not_required",
          mode: "incremental" | "full" | null, kvk: int | null,
          entered: bool, completion_evidence: "results_exhausted" | "none",
          internal_commits: "not_applicable" | "not_individually_observed"}
committed_units: ordered list of {unit, objects: [fixed object names], rows: int | null,
                                evidence: "commit_acknowledged"}
rollback: {attempted: bool, state: "not_needed" | "confirmed" | "failed" | "unknown",
           unit: string | null}
tables: fixed-name keyed legacy-compatible rows/status/error plus write/commit state
errors: bounded sanitized string list (legacy projection)
primary_error: null | {stage, type, code, message}
cleanup_errors: list of {resource, stage, type, code, message}
artifact_errors: list of {artifact, type, code, message}
warnings: bounded records; backend: name, offload_id/pid where observed
artifacts: {manifest: {state, path | null}, last_report: {state, path | null}}
partial_commits: legacy projection of confirmed import objects only
targets_master_executed: bool (true only after full target completion, never merely execute return)
targets_master_mode / targets_master_kvk: legacy projections
manifest_path / persisted_to: set only when corresponding write is confirmed
```

Allowed artifact states: `written`, `failed`, `not_attempted`. Paths are generated locally under DATA_DIR; errors and stdout do not supply arbitrary paths to follow. Rows are count evidence, never raw Sheet/SQL values. Optional diagnostic timing/log-space fields may be retained. SQL-native error details are sanitized and bounded; no connection strings, credentials, full rows or unbounded SQL PRINT output enter the domain envelope.

Overall mapping, in precedence order:

| Condition | Report / bool / worker exit |
|---|---|
| Unknown commit or required stage after entry; worker lost, timeout or malformed/contradictory transport without sufficient proof | `unknown`, false, 3 when a worker can emit/exit normally. Preserve all independently known commits. OS timeout/kill exit is recorded separately, never fabricated as 3. |
| Required stage, cleanup or manifest fails after known committed work | `partial`, false, 3. Import may be committed and target may be completed; neither fact is erased. |
| Validation/preflight/import failure before any confirmed commit, or confirmed rollback before commit was attempted | `failed`, false, 3; import_state distinguishes not_started/rolled_back. |
| All required SQL or dry-run validation stages, cleanup and manifest publication confirmed | `success`, true, 0. Dry-run says validated_only and targets not_required, never imported. |
| Optional last-report/telemetry failure only | Keep domain success with explicit warning/artifact failure. No claim that optional evidence was saved. |

A target SQL error can be a known failed operation while internal committed scope remains uncertain; overall remains unknown if that uncertainty matters. Do not turn a server exception into a global rollback claim. Successful target completion describes completion of the existing procedure contract, including legitimate skips, not proof of fresh target publication or Discord delivery.

### Worker wire format and compatibility

ProcConfig worker terminal envelope:

```text
worker_result: true
schema: "proc_import_worker_v2"
command: "proc_import"
run_id: same UUID
status: same terminal domain status
returncode: 0 only for success, otherwise 3
result: [exact bool, finalized compact v2 report]
```

Both maintenance named/spec paths and standalone callable worker produce this same envelope for ProcConfig. Parent-generated run ID travels as explicit recognized ProcConfig operation metadata, not an arbitrary SQL argument; direct CLI invocation generates one when absent. Existing no-argument CLI remains supported. Validate supplied run ID and dry-run before invocation.

The status/result core is never placed in `result_summary` or truncated by MAINT_WORKER_RESULT_SNIPPET. Bound diagnostics separately and emit explicit omission counts. Set a 64 KiB terminal envelope budget; oversized/non-JSON domain material fails serialization conservatively with a small valid error envelope preserving safe stage facts. Do not stringify an object into apparent success. Non-ProcConfig worker formats remain compatible.

Parent parsing requires exactly one matching terminal envelope, marker true, supported schema, matching run ID/command, actual bool, report version/status consistency and rc agreement. Ignore telemetry JSON as a terminal candidate. Multiple matching terminal records, missing core, mixed `return`/`result`, invalid field types or status/rc disagreement cannot be success. A valid failed report survives nonzero exit. OS rc zero alone cannot establish domain success; nonzero rc cannot erase a valid known committed unit. Preserve transport error separately.

Legacy tuple/list transport shapes are accepted only by an explicit bounded compatibility normalizer, never recursively by truthiness. `(False, report)` always remains nonsuccess. A v1 report or `(True, {})` without required completion evidence cannot establish a new v2 success; classify as unknown compatibility result. Old persisted v1 reports remain historical readable artifacts, not current-run completion evidence. Update test doubles to real v2 reports instead of making the parser permissive to fit old fakes.

### Artifacts and telemetry

Required artifact: per-run manifest `DATA_DIR/imports/proc_import_manifest_<run_id>.json`. Unique identity replaces second-resolution names. Best-effort optional compatibility snapshot: `DATA_DIR/last_proc_import_report.json`, still containing a complete report; module `last_import_report` contains the actual latest locally observed report, including failed persistence. Callers use their returned report/run ID, never a global/latest file to infer their outcome.

Finalize after cleanup. Attempt manifest on every reachable terminal path, including preflight/dry-run/SQL failures. Build the complete body before serialization, using `atomic_json_write` and strict primitive data. Successful atomic replacement is the manifest receipt; failure clears the path projection and makes the returned report failed/partial/unknown by stage evidence. Then attempt last-report snapshot and emit terminal telemetry. Optional last-report failures need not rewrite the immutable SQL/cleanup manifest: it records the required run outcome; the returned report and terminal event separately record optional delivery failures. Do not pretend all artifacts transactionally commit together.

Hard kill or machine loss may prevent any terminal artifact or event. Absence is unknown; the design cannot promise a terminal manifest after an uncatchable termination. No startup scan of reports initiates repair/replay. Existing per-run SQL facts in trusted observations are retained; facts lost with the worker are not invented.

Avoid circular persistence receipts: prepare a separate candidate manifest value with its own manifest projection set to `written` and the intended path. Those bytes become a receipt only when atomic publication succeeds, or when a reader validates the complete file at that exact run-ID path. Do not publish the candidate value to callers or telemetry before the write returns successfully. On a write exception, return the actual failed/unknown persistence observation, not the candidate success; a later-discovered complete file cannot retroactively change the caller's result. The candidate leaves the optional last-report state `not_attempted`, since that separate write has not yet occurred. This requires one per-run manifest publication, not a second self-confirmation write or a multi-artifact transaction.

Reuse unique-temp `atomic_json_write` rather than the fixed `.tmp` helper. Existing bounded file-replacement retries are retries of identical artifact bytes only, not backend/SQL re-execution. Concurrent runs may finish out of order; the last snapshot means last writer, not authoritative newest-started run. Run IDs prevent stale snapshot substitution without adding a durable admission/CAS protocol.

Emit a single domain terminal event with run ID, status, success, import/target state, committed units, cleanup/artifact state and backend identity. Transport events may say process exited, but must not label an explicit failed ProcConfig result success. Notification/optional telemetry failure stays separate from SQL work.

## 6. Downstream and operator-visible behavior

| Surface | Proposed behavior requiring approval |
|---|---|
| Pipeline exports | Preserve execution after ProcConfig failed/partial/unknown; warn that output may reflect previous/partial data. Do not certify export freshness from import failure. |
| Name/target cache warming | Preserve current continuation and cache repository's existing last-known-good/provenance policy; no forced refresh, invalidation or state reset. |
| Post-import stats maintenance / player caches | These run earlier in the pipeline under existing gates. A later ProcConfig failure cannot undo or relabel them. |
| Pipeline return | Keep six-element legacy return by default. Add keyword-only `return_details=False`; true returns that legacy tuple plus a detail record containing ProcConfig v2 outcome. `handle_file_processing` opts in. No caller receives a dict in a Boolean slot. |
| `admin_helpers.log_processing_result` | Optional keyword-only `proc_import_report=None`, preserve CSV column shape and strict bool in old ProcConfig column. Add run ID and explicit outcome to structured log/summary embed; no schema migration. |
| Stats publication | Retain existing all-five-success gate. Corrected false/partial/unknown imports no longer accidentally pass it. This is the explicit consequence of truthful failure, not a change to Phase 2K admission/claim rules. Independent honor/Pre-KVK routes remain unchanged. |
| Queue status / final DONE log | No unqualified green all-complete text for a known ProcConfig nonsuccess. Keep archive/export status basis but display a ProcConfig failed/partial/unknown qualifier; do not redesign queue state. |
| Input-log, failure-log and admin-channel upload deletion | Preserve existing order/policy; log failures separately. Message cleanup is not import completion and cannot trigger retry. |
| Admin command | Same command/options/permissions/ephemeral flow. Version advances from v1.03 to v1.04 for truthful reporting. Examples: “Import completed”; “Configuration committed; target refresh completion unknown”; “SQL work completed; required report could not be saved”; “Validation failed; no import started.” Use existing safe diagnostic content/mention neutralization. No raw exception concatenation or retry recommendation. |
| Startup | Same scheduling/timeout budget and independent normal startup invocation. Domain result and surviving-work uncertainty are visible; cancellation rethrows. No restart-triggered recovery replay. |

Approval explicitly includes strict nonsuccess mapping, disabling ambiguous destructive Sheet-writer fallback for ProcConfig, required-manifest failure preventing full success, and the resulting suppression by the existing all-five publication gate. It does not authorize changing export/cache continuation, seasons/defaults, caps or dispatch ownership.

## 7. Exact proposed manifests

Paths below are exact and relative to `C:\discord_file_downloader`. They are a proposed implementation ceiling, not edits already made. Any additional runtime/test/SQL path requires a manifest/design delta before editing.

### Runtime — modify (11)

| Path | Bounded responsibility |
|---|---|
| `proc_config_import.py` | Compatibility APIs; delegate orchestration, retain Sheet parsing helpers; normalize offload and correct backend selection. |
| `maintenance_worker.py` | ProcConfig named/spec result handling, terminal wire/exit, once-only coroutine execution. |
| `scripts/callable_worker.py` | ProcConfig wire/exit and serialization failure; keep unrelated callable format. |
| `file_utils.py` | ProcConfig-aware maintenance/thread/process adapters and strict result selection; bounded process cleanup/pipe draining; leave generic defaults compatible. |
| `sheet_importer.py` | Strict opt-in error/commit evidence and result drainage for ProcConfig; no replay after ambiguous destructive failure. |
| `log_health.py` | Explicit cursor lifetime in participating entrypoints; optional cleanup observation; no thresholds/backup-policy redesign. |
| `processing_pipeline.py` | Both ProcConfig branches, detailed return opt-in, terminal summary/queue wording and detail handoff. |
| `admin_helpers.py` | Optional ProcConfig detail presentation; preserve all-five gate and Phase 2K log_delivery. |
| `commands/admin_cmds.py` | Existing import command v1.04 response mapping only. |
| `bot_instance.py` | ProcConfig startup adapter and import-specific timeout/orphan observations; no general lifecycle rewrite. |
| `kvk/dal/kvk_lifecycle_dal.py` | Latest-details read explicit resource ownership / opt-in strict cleanup evidence for import; same query/mapper and ordinary lifecycle behavior. |

### Runtime — create (4)

| Path | Why new |
|---|---|
| `services/proc_config_import_service.py` | One Discord-independent owner for import orchestration, terminal finalization and report artifacts. |
| `services/proc_config_import_outcomes.py` | Pure outcome model, mapping, strict compatibility/wire validation and concise summaries. Existing delivery/session types describe different contracts. |
| `stats/dal/proc_config_import_dal.py` | Uses existing stats DAL package for import writes, exact commit ledger and independent target connection. No new root monolith/package needed. |
| `core/sql_results.py` | Small strict drain primitive without DataFrame materialization or swallowed cleanup. Existing readers stop at selected sets or own unrelated output transformations. |

Runtime delete: none. Configuration/dependency/deployment-script/view/new-command manifests: empty.

### Tests — modify (13)

```text
tests/test_proc_config_import.py
tests/test_proc_config_import_phase2.py
tests/test_proc_config_import_offload.py
tests/test_sheet_importer.py
tests/test_maintenance_suite.py
tests/test_worker_module.py
tests/test_integration_end_to_end_fake_worker.py
tests/test_processing_pipeline.py
tests/test_processing_pipeline_context.py
tests/test_processing_pipeline_build_cache.py
tests/test_processing_pipeline_run_step_and_normalization.py
tests/test_admin_helpers_stats_delivery.py
tests/test_kvk_lifecycle_dal.py
```

`test_worker_module.py` is a subprocess fixture module, not currently a suite of worker assertions. Extend it with safe deterministic callable fixtures. Existing pipeline tests return `True, "OK"`; migrate just their ProcConfig seam to the truthful contract.

### Tests — create (7)

```text
tests/test_proc_config_import_outcomes.py
tests/test_proc_config_import_dal.py
tests/test_sql_results.py
tests/test_proc_config_worker_contract.py
tests/test_proc_config_admin_command.py
tests/test_proc_config_startup.py
tests/test_proc_config_log_health_lifecycle.py
```

Tests delete: none. Runtime review-only inventory: `process_utils.py`, `gsheet_module.py`, `constants.py`, `kvk_state.py`, `stats_alerts/kvk_meta.py`, `target_utils.py`, `targets_sql_cache.py`, `kvk/target_cache_repository.py`, `core/startup_lifecycle.py`, `startup_utils.py`, `core/interaction_safety.py`, `core/operator_diagnostic_payloads.py`, `utils.py`, `embed_utils.py`, `bot_helpers.py`, `logging_setup.py`, `registry/governor_registry.py`, `account_picker.py`, `prekvk_importer.py`, `stats_module.py`, `stats_alerts/interface.py`, `stats_alerts/delivery_outcomes.py`, `stats_alerts/dispatch_reservations.py`, `upload_routes/honor_route.py`, `upload_routes/prekvk_route.py`, `scripts/offload_monitor.py`, `offload_monitor_lib.py`, `scripts/select_tests.py`. No root `governor_registry.py` exists; use the registry package path.

Review/run unchanged tests: `tests/test_run_step.py`, `tests/test_process_utils.py`, `tests/test_file_utils.py`, `tests/test_file_utils_2.py`, `tests/test_file_utils_build_cmd.py`, `tests/test_file_utils_atomic_write_retry.py`, `tests/test_run_maintenance_buildonly.py`, `tests/test_run_maintenance_args.py`, `tests/test_offload_serialization.py`, `tests/test_offload_callable_integration.py`, `tests/test_cancel_offload.py`, `tests/test_offload_monitor_once.py`, `tests/test_offload_registry_rotation.py`, `tests/test_startup_lifecycle.py`, `tests/test_kvk_state_open_window.py`, `tests/test_prekvk_importer.py`, `tests/test_stats_delivery_outcomes.py`, and existing H/I/guard/state/registration tests. Broaden to full pytest as required below.

### Documentation — modify for WS1 delivery after approval (14)

```text
README-DEV.md
docs/reference/runbook_diagnostics.md
docs/reference/runbook_startup.md
docs/reference/canonical_command_reference.md
docs/reference/deferred_optimisations.md
docs/reference/archive/deferred_optimisations_resolved.md
docs/kvk/target_publication_contract.md
docs/task_packs/archive/Discord Embed Payload Safety Audit Findings.md
docs/task_packs/archive/Codex Task Pack - Discord Embed Payload Safety Phase 2K Production Stats Delivery Outcomes.md
docs/task_packs/archive/Codex Chat Starter - Discord Embed Payload Safety Phase 2K Production Stats Delivery Outcomes.md
docs/task_packs/Codex Task Pack - Bot Operational Reliability Workstream 1 ProcConfig Import Reliability and Truthful Completion Reporting.md
docs/task_packs/Codex Chat Starter - Bot Operational Reliability Workstream 1 ProcConfig Import Reliability and Truthful Completion Reporting.md
docs/task_packs/Bot Operational Reliability - Programme Pack.md
docs/task_packs/Bot Operational Reliability Workstream 1 - Design and Manifests.md
```

The target publication contract currently documents restoration of the shared connection mode; update only that connection-lifetime paragraph. Archived Phase 2K edits append verified final merge/deployment evidence, retaining candidate smoke provenance. Active/resolved records move the ProcConfig item only when actually delivered; leave seasonal/Phase 2F and policy debt open. Command reference updates outcome wording, not command inventory.

Documentation create/delete during implementation: none. After accepted delivery only, archive WS1 pack and starter by exact moves from their active paths above to the same basenames under `docs/task_packs/archive/`; repair active links and both legacy Phase 2L redirects, update the programme status, and retain this design/evidence record. That final archival is conditional on completion, not authorized by approving code alone.

### SQL — separately gated

Modify/create/delete: **EMPTY**. No migration, SQL data change, ConfigKey update, force-republish, SQL Agent/calendar mutation or operational procedure execution is proposed.

Exact procedure review files under `C:\K98-bot-SQL-Server\sql_schema`:

```text
dbo.sp_Upsert_ProcConfig_From_Staging.StoredProcedure.sql
dbo.sp_TARGETS_MASTER.StoredProcedure.sql
dbo.CREATE_DELTA_TABLES.StoredProcedure.sql
dbo.sp_Prep_TargetTable.StoredProcedure.sql
dbo.sp_ExcelOutput_ByKVK.StoredProcedure.sql
dbo.sp_Prep_ExcelOutputTable.StoredProcedure.sql
dbo.sp_Prep_ExcelExportTable.StoredProcedure.sql
dbo.sp_Build_Prekvk_And_Honor_Rankings.StoredProcedure.sql
dbo.sp_Create_Excel_For_Kvk_Indexes.StoredProcedure.sql
dbo.sp_Refresh_View_EXCEL_FOR_KVK_All.StoredProcedure.sql
dbo.usp_RecordKvkFinalReportCompletion.StoredProcedure.sql
```

Exact schema contract review files:

```text
dbo.ProcConfig.Table.sql
dbo.ProcConfig_Staging.Table.sql
dbo.ProcConfig_AuditLog.Table.sql
dbo.KVKTargetBands.Table.sql
dbo.EXEMPT_FROM_STATS.Table.sql
dbo.KVK_Details.Table.sql
KVK.KVK_DKPWeights.Table.sql
KVK.KVK_Windows.Table.sql
KVK.KVK_CampMap.Table.sql
dbo.STAGING_STATS.Table.sql
dbo.EXCEL_EXPORT_KVK_TARGETS_TEMPLATE.Table.sql
dbo.DeltaMetrics.Table.sql
dbo.KVKFinalReportHeader.Table.sql
dbo.KVK_Target_Publication.Table.sql
dbo.KVK_Target_Publication_Row.Table.sql
dbo.v_KVK_TARGETS_FOR_BOT.View.sql
dbo.v_TARGETS_FOR_UPLOAD.View.sql
```

Generated per-KVK table/view definitions come from the generator procedures, not a guessed deployed season. The legacy view export happens to point to KVK15; runtime master can change it, so that export does not identify today's live target.

If deterministic/live-parity evidence later proves a SQL change necessary, stop and propose exact SQL files with a separate SQL PR, immutable Changes review, compatibility/order and rollback. No implicit SQL authorization follows from this bot design.

## 8. Testing, selectors and review

| Changed caller/boundary | Required proof and test ownership |
|---|---|
| Direct import/service | Existing ProcConfig suites plus outcome tests: every early path, real bool, dry-run no SQL, optional health unavailable, transaction/nontransaction mode, empty auxiliary no-op, metadata/DataFrame/full selector parity. |
| SQL drain/DAL | New sql_results and DAL tests: faithful fake refuses mode change with pending tokens; no rows, row counts, multiple sets, PRINT, nested diagnostic rows then late error, execute failure, fetchmany/nextset failure, no second execute; bounded memory. Assert old failure reproduces before replacing it. |
| Commit/resource lifetime | Transactional commit before separate autocommit target connection; import rollback before commit; staging-clear partial commit; commit acknowledgment lost followed by successful rollback remains unknown; target failure with known import commit; errors on every close and on rollback; primary error preserved. |
| Shared writers/readers | Sheet suite plus PreKvk unchanged regression; log-health lifecycle suite; latest-detail DAL suite. No commit swallowing on ProcConfig strict path, no DELETE after ambiguous truncate/commit, no resource leaks or false completed status. |
| Named worker / callable specs | Worker contract suite and maintenance suite: true/false tuples, legacy incomplete reports, contradictory bool/report/rc, malformed/multiple/event JSON, missing result, large diagnostics, serialization failure, sync/async/sync-returning-awaitable, RuntimeError after side effect exactly once. |
| Offload/transport | Existing offload suite plus worker integration: direct/thread/process equivalence, dry_run preserved, launcher metadata rejected, availability-only fallback, spawn uncertainty, pipe pressure, cancellation/timeout/late result, PID/registry/output cleanup errors. Domain counters remain one after entry. |
| Real subprocess to pipeline | Extend fake-worker integration using test-only fake SQL/Sheets dependency injection into the actual import service and actual worker/parent parser; never load live credentials or hit DB/Sheets. Both pipeline branches receive false/partial/unknown. |
| Pipeline summary/admin helper | All four existing pipeline suites plus admin helper suite: exports/cache continuation, strict all-five gate, legacy six-tuple default and opt-in detail, same CSV shape, partial/unknown queue qualifier, no false DONE or ProcImport=True, message cleanup errors separate. |
| Admin command | New command suite invokes registered command with existing decorators/permissions, defer/edit/followup behavior, safe bounds/mentions, success/partial/unknown/malformed result, notification failure with one execution. |
| Startup | New startup suite with injected scheduler/offload dependencies: wrapper available/unavailable, 180-second outer timeout, cancellation, orphan uncertainty, no second backend or success log after false result. General startup suite unchanged. |
| Reports | Missing/unwritable directory, every reachable terminal path, unique same-second run IDs, malformed serialization, stale last report, per-run lookup identity, optional last-report/telemetry failures, no raw row/credential leakage. Hard-kill test asserts unknown/missing evidence, not impossible finalization. |
| Phase 2K/H/I/J | Existing receipt/claim, stats delivery, admin helper, H/I lifecycle/defaults, guard/state and command-registration suites. No removed-ops callback or forced duplicate tests. |

Read-only selector was run with all 15 proposed runtime and 20 proposed test paths. It recommended full `python -m pytest -q tests`, `python scripts/smoke_imports.py`, and `python scripts/validate_command_registration.py`. The selector does not infer this failure matrix; the matrix is additional required coverage.

After implementation: run focused tests for all modified/new suites first, then architecture/deferred/security-routing validators, explicit selector over actual final paths, smoke imports, command registration (expected 36 primary / 100 grouped / 24 ops), applicable pre-commit hooks, and full pytest with log-noise verification. Use `python scripts/analyse_pytest_log_noise.py` for full-suite operational-log isolation; any separate tee output belongs in a non-production audit file. Fix related failures only; record unrelated failures without broadening scope.

Audit validations actually run: architecture pass with **0 changed Python files**, deferred pass with **0 changed Markdown files**, security-routing pass **0 errors / 0 warnings**, `git diff --check` pass, explicit test selector run. These are no-diff governance checks, not proof of runtime correctness. Runtime pytest, smoke imports, command registration execution, hooks and SQL integration were deliberately not run during this design-only audit.

Security decision: no scan now because no executable/configuration/permission/data-access/deployment change exists. Future bot diff requires `$codex-security:security-diff-scan`: **Scan type Changes, Deep off**, frozen mirror base/head (current candidate base `1a3a5de3...`, refresh on actual branch creation), plus separate production base/head after patch-based promotion (current production base `1e72949d...`). Preserve security findings/coverage/manifest and post-scan delta disposition. SQL no-diff skip remains separate. Do not reuse Phase 2K's sealed review as a WS1 review; do not launch Codebase/Deep scans. Existing vulnerability backlog is not reprioritized through these reliability findings.

## 9. Classification, reuse and deferred capture

| Classification | Decision |
|---|---|
| Safe to preserve | SQL parameters, transaction ownership, data formulas, empty-table behavior, nontransactional scope, read/connection-only retries, export/cache continuation, admin authorization, K's delivery/claim rules and H/I storage/defaults. |
| Fix now after approval | Full result lifecycle; strict commit evidence; independent target connection; cleanup/artifact reporting; all native/worker/transport/caller outcomes; dry-run forwarding; async RuntimeError re-entry; ProcConfig pipe/timeout cleanup; misleading queue/DONE wording. |
| Defer | Broader executor consolidation, generic process ownership, cross-invocation import admission, durable publication policies, general view/lifecycle, DM/JSON, unrelated SQL modernization/performance and durable delivery audit adoption. |
| Not runtime | Retired `/ops test_embed`, archived superseded instructions, obsolete helper name `run_maintenance_step`; no new implementation or callback tests for them. Process-utils is runtime but review-only, not a ProcConfig executor. |

Reuse `sheet_importer` parameterized/batched writes and row conversion, existing connection factories/principals, latest-detail query/mapper, `run_blocking_in_thread`, correct maintenance/callable command builders, argument serialization, offload registry identity helpers, unique-temp `atomic_json_write`, telemetry emitter and existing safe diagnostic/interaction helpers. Existing `gsheet_module._dfs_from_proc` demonstrates result traversal but materializes DataFrames and suppresses cleanup errors; do not reuse it as a strict mutation completion owner. Existing DAL result readers intentionally select particular result sets and do not provide the complete mutation-stream contract. Phase 2K delivery and H/I diagnostic types cannot represent SQL commit boundaries.

The following captures retain existing owners rather than silently folding them into WS1. They are proposed backlog wording, not repository edits.

### Deferred Optimisation
- Area: `stats_module.py::_offload_callable_py`, `ui/views/kvk_history_view.py::_offload_callable`, and `stats_alerts/interface.py` / `stats_alerts/db.py`
- Type: consistency
- Description: Existing unrelated executor fallback paths can re-enter work after an exception; their full caller and side-effect contracts remain outside the ProcConfig adapters.
- Suggested Fix: Preserve the separate existing Stats, KVK History and stats-alert executor items; audit each with real call shapes and invocation counters before selecting a once-only backend contract.
- Impact: medium
- Risk: medium
- Dependencies: Separately approved scopes and deterministic exception/cancellation tests; no generic executor rewrite in WS1.

### Deferred Optimisation
- Area: `singleton_lock.py`, generic tracked-view rehydration, public-reminder child tasks, `event_scheduler.py` DM writers
- Type: architecture
- Description: Process ownership, generic rehydration timeout, public child supervision and DM write ordering are distinct lifecycle problems; atomic JSON replacement or ProcConfig cleanup does not resolve them.
- Suggested Fix: Retain the existing separate lifecycle and DM/JSON records and design ownership/shutdown/restart behavior in their own bounded slices.
- Impact: medium
- Risk: high
- Dependencies: Operator-approved scopes, exact state identity and restart evidence; preserve Phase 2F public-save observation.

### Deferred Optimisation
- Area: fighting dispatch admission, KS ping claims, production Pre-KVK ambiguous-edit fallback, persistent delivery audits
- Type: architecture
- Description: Phase 2K truthfully reports delivery but intentionally leaves durable fighting ownership, KS preclaim timing, ambiguous edit replacement and durable SQL delivery records as separate policies.
- Suggested Fix: Retain each existing policy owner and design explicit ambiguity, migration and rollback contracts before changing admission or persistence.
- Impact: high
- Risk: high
- Dependencies: Separate policy/SQL approval and deterministic concurrency/restart evidence; WS1 cannot alter receipts or retry dispatch.

### Deferred Optimisation
- Area: independent ProcConfig admin/startup/pipeline invocations and generic offload ownership
- Type: architecture
- Description: One backend per invocation does not prevent overlapping independent imports or reconstruct lost commit evidence after process death. Current manifests/offload records are observations, not durable admission authority.
- Suggested Fix: If actual overlap evidence warrants it, separately scope admission and provenance with SQL ownership/compatibility requirements; do not infer an automatic replay or recovery mechanism from missing reports.
- Impact: medium
- Risk: high
- Dependencies: Separate operator approval, measured overlap evidence and source-of-truth SQL validation; no reservation or recovery protocol in WS1.

Natural Pre-KVK (approximately two months away), off-season production observations and Phase 2F natural public-save evidence remain independent follow-ups. They neither block accepted Phase 2K smoke nor become completed through WS1.

## 10. Natural smoke, rollout, rollback and approval

After approval and implementation, review the whole bot diff with K98 PR review, then promotion-check skills. Promote the validated file delta from the mirror onto a branch based on production/main through the documented patch workflow. Do not push unrelated mirror history to production. SQL deployment order is not applicable with an empty SQL manifest.

Before WS1 deployment, retain the now-supplied final Phase 2K bot-machine SHA/clean checkout/restart evidence above, recheck the then-current deployment baseline, and capture the WS1 candidate SHA. Rehearse failures only with deterministic fake drivers or separately approved isolated SQL. Never call live master, backup-trigger preflight, forced republish or a calendar/state mutation to manufacture audit/smoke evidence.

Observe the next legitimate import. Correlate deployed SHA/restart, trigger/run ID, one worker/PID, actual exit, complete domain result, acknowledged import commit, terminal target result-stream completion, cleanup and required manifest, pipeline status and downstream continuation. Check no false success follows a failed report. Existing production failure evidence plus deterministic negative tests covers failure presentation without a live forced failure. One clean import alone does not prove intermittent remediation; retain subsequent natural observations and absence/presence of the old HY000 signature. Reconfirm registration and unchanged Phase 2K receipt/claim behavior where naturally exercised.

Bounded rollback: stop admitting new WS1 work during the approved deployment window, allow active work to finish or classify unresolved work without replay, then revert only the WS1 bot delta through reviewed production deployment. Preserve every report, manifest, cache, CSV, journal and H/I session. Verify rollback SHA, clean checkout and restart. Reverting Python does not undo configuration, delta preprocessing, per-KVK publications, final report revisions or export effects already committed. Rollback reintroduces the old unreliable result/reporting behavior; no data rollback, quota repair, automatic rerun, state deletion or downgrade rewrite is authorized. Any future SQL delta needs its own independently approved rollback.

Approval requested for this complete design and exact manifests, including: strict v2 success criteria, separate target connection, required per-run manifest policy, conservative ambiguous outcomes, ProcConfig-only strict writer behavior, once-only worker execution, and preserving export/cache continuation with the corrected existing publication gate. The deployed-SHA/clean-checkout/restart entry evidence gap is closed by the operator records above. Implementation remains stopped until explicit approval; supplying deployment evidence does not itself approve the design or manifests.
