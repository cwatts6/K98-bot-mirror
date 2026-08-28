# Codex Task Pack - KVK Post-Pass-4 Healed Troops and Provenance-Safe Stats Refresh

> Coordinated two-repository bug-fix pack for `K98-bot-mirror` and `K98-bot-SQL-Server`.
> This pack is intentionally implementation-ready but is **not one-pass approved**. Codex must complete the audit and architecture checkpoints, report its findings, and stop for approval before changing either repository.

## 1. Task Header

- Task name: `KVK post-Pass-4 healed troops and provenance-safe stats refresh`
- Date: `2026-08-27`
- Owner/context: `Chris Watts / KVK 16 King of All Britain pre-fighting stats investigation`
- Task type: `bug fix`
- One-pass approved: `no`
- Repositories:
  - Bot: `cwatts6/K98-bot-mirror`
  - SQL: `cwatts6/K98-bot-SQL-Server`
- Recommended branch name in each repository: `fix/kvk-healed-window-refresh-provenance`
- Coordinated deployment order: `SQL first, bot second`

## 2. Required Reading

Before implementation, read the current bot repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`. Do not load every reference document by default.

For the security-review decision, also read:

- the active bot repository `AGENTS.md`
- root and applicable nested `SECURITY.md` files in both repositories, when present
- the `k98-security-review-routing` skill

For SQL-facing work, validate every schema, procedure, view, index, transaction, lock and `ProcConfig` assumption against the authoritative local SQL repository:

`C:\K98-bot-SQL-Server`

Task-specific required review:

### SQL repository

- `sql_schema/dbo.UPDATE_ALL2.StoredProcedure.sql`
- `sql_schema/dbo.sp_ExcelOutput_ByKVK.StoredProcedure.sql`
- `sql_schema/dbo.SP_Stats_for_Upload.StoredProcedure.sql`
- `sql_schema/dbo.KVKFinalReportHeader.Table.sql`
- `sql_schema/dbo.usp_RecordKvkFinalReportCompletion.StoredProcedure.sql`
- `sql_schema/dbo.v_EXCEL_FOR_KVK_All.View.sql`
- `sql_schema/dbo.STATS_FOR_UPLOAD.Table.sql`
- `sql_schema/dbo.STAGING_STATS.Table.sql`
- `sql_schema/dbo.HealedTroopsDelta.Table.sql`
- `sql_schema/dbo.KingdomScanData4.Table.sql`
- `sql_schema/dbo.ProcConfig.Table.sql`
- `migrations/20260607_001_preserve_stats_for_upload_last_refresh_time.sql`
- the current migration, rollback, verification and release conventions

### Bot repository

- `player_stats_cache.py`
- `bot_instance.py`
- `processing_pipeline.py`
- `commands/stats_cmds.py`
- `kvk/services/kvk_admin_service.py`
- `kvk/services/kvk_stats_card_service.py`
- `kvk/services/kvk_rankings_service.py`
- `services/kvk_history_service.py`
- `kvk/combat_metrics.py`
- `tests/test_player_stats_cache.py`
- `tests/test_kvk_admin_service.py`
- `tests/test_kvk_combat_metrics.py`
- `tests/test_kvk_stats_card_payload.py`

## 3. Objective

Correct the KVK combat-stat source so `HealedTroopsDelta` contains only healing recorded **strictly after the configured `PRE_PASS_4_SCAN`**, matching the existing KVK kill, dead and Kill Point combat boundary. This must automatically correct downstream KP Loss and Tanking Score calculations without changing their formula.

Also make `STATS_FOR_UPLOAD` publication provenance-safe: an independently triggered cache refresh must never copy a stale `EXCEL_FOR_KVK_N` table and stamp it with the timestamp of a newer `KingdomScanData4` scan. Reuse the existing successful-output provenance in `dbo.KVKFinalReportHeader`, preserve the last known good output on failure, and make degraded cache refreshes visible to operators.

## 4. Background

### 4.1 Current KVK 16 evidence

At task creation, the connected KVK configuration showed:

| Setting | KVK 16 value |
|---|---:|
| `LASTKVKEND` | 952 |
| `DRAFTSCAN` | 1047 |
| `MATCHMAKING_SCAN` | 1059 |
| `PRE_PASS_4_SCAN` | 1095 |
| `PASS4END` | 1115 |
| `PASS6END` | 1165 |
| `PASS7END` | 1185 |
| `KVK_END_SCAN` | 1205 |

The latest scan visible during the audit was 1065. These values are evidence only: do not hard-code them into runtime logic. Re-query the live database before implementation and deployment.

Because scan 1065 is earlier than `PRE_PASS_4_SCAN` 1095, current-KVK combat healing must be zero at this point.

### 4.2 Confirmed healed-troop defect

`dbo.sp_ExcelOutput_ByKVK` currently treats the following metrics differently:

- T4/T5 kills: `DeltaOrder > @PRE_PASS_4_SCAN`
- deads: `DeltaOrder > @PRE_PASS_4_SCAN`
- Kill Points: `DeltaOrder > @PRE_PASS_4_SCAN`
- healed troops: `DeltaOrder > @Scan`

Once matchmaking is available, `@Scan` is the matchmaking scan. For KVK 16 this means healing from scans 1060 onward is currently included even though fighting does not begin until after scan 1095.

The bot's canonical combat helper calculates:

```text
KP Loss = HealedTroopsDelta × 20
Tanking Score = KillPointsDelta × 100 / (KP Loss + Deads_Delta)
```

Therefore pre-Pass-4 healing creates false KP Loss and distorts Tanking Score before fighting has started.

### 4.3 Confirmed but narrow `LAST_REFRESH` weakness

The normal successful import route is correctly ordered:

1. import the new scan;
2. refresh `EXCEL_FOR_KVK_N`;
3. run `SP_Stats_for_Upload`;
4. rebuild the JSON cache.

However, `UPDATE_ALL2` deliberately commits Phase A after the new scan is inserted into `KingdomScanData4`, before the non-critical Phase B downstream builds. Phase B performs several operations before reaching `sp_ExcelOutput_ByKVK`, including averages and dashboard rebuilds.

This creates a real partial-success state:

1. a new scan is durably committed to `KingdomScanData4`;
2. the archive handoff or any Phase B step fails, is cancelled, times out, loses its connection, or the process terminates before `sp_ExcelOutput_ByKVK` successfully commits;
3. `EXCEL_FOR_KVK_N` remains on the previous successful scan;
4. the bot later starts, an operator runs `/kvk_admin refresh_stats_cache`, `player_stats_cache.py` is run directly, or another independent cache build occurs;
5. the cache builder executes `SP_Stats_for_Upload`;
6. that procedure copies the old `EXCEL_FOR_KVK_N` rows but currently sets every row's `LAST_REFRESH` to global `MAX(KingdomScanData4.ScanDate)`.

The weakness does **not** occur on the normal happy path. It occurs only when `KingdomScanData4` advances without a matching successful KVK output publication, followed by an independent `SP_Stats_for_Upload` invocation.

### 4.4 Existing provenance must be reused

`sp_ExcelOutput_ByKVK` already calls `dbo.usp_RecordKvkFinalReportCompletion` inside the same transaction that builds and validates the KVK output. `dbo.KVKFinalReportHeader` records:

- `KVK_NO`
- `FinalDataAtUtc`
- `FinalScanOrder`
- `OutputRowCount`
- `Revision`
- `State`
- `FinalizationBasis`

This is the canonical successful-materialisation provenance. Do not add a duplicate output-provenance table unless the audit proves this contract cannot safely support the required validation.

### 4.5 Existing cache fallback is not transparent enough

`player_stats_cache.py` defaults to executing `SP_Stats_for_Upload` before reading `STATS_FOR_UPLOAD`. If that stored procedure fails, the builder logs the failure and continues with the existing SQL table.

That availability-first fallback is useful, but current metadata records only `sp_executed`, which reflects configuration/attempt rather than success. The async builder also does not return its structured output to the admin service, so `/kvk_admin refresh_stats_cache` can report a generic success even when it rebuilt from last-known-good SQL data after the source refresh failed.

## 5. Scope

### In Scope

#### SQL correctness

- Change `HealedTroopsDelta` in `sp_ExcelOutput_ByKVK` to use `DeltaOrder > @PRE_PASS_4_SCAN`.
- Preserve `Starting_HealedTroops` as the matchmaking/draft baseline from `@Scan`.
- Preserve the current KP Loss and Tanking Score formulas; correct their input rather than changing their calculation.
- Regenerate KVK 16 output after deployment so pre-Pass-4 healing is removed immediately.

#### SQL publication provenance and safety

- Reuse `KVKFinalReportHeader` to prove which final scan successfully produced `EXCEL_FOR_KVK_N`.
- Derive `STATS_FOR_UPLOAD.LAST_REFRESH` from the scan date corresponding to the proven `FinalScanOrder`, not global `MAX(ScanDate)`.
- Detect missing, stale or inconsistent output provenance before mutating `STATS_FOR_UPLOAD`.
- Make replacement of `STATS_FOR_UPLOAD` atomic.
- Preserve the current last-known-good `STATS_FOR_UPLOAD` contents on validation, population, row-count or transaction failure.
- Serialize concurrent publishers if no existing equivalent lock is found.
- Add stable, diagnostic SQL errors and logs for stale/missing provenance without exposing secrets.

#### Bot cache transparency

- Distinguish a successful SQL refresh from reuse of last-known-good `STATS_FOR_UPLOAD`.
- Do not replace a healthy JSON cache with an empty, cross-KVK or otherwise invalid SQL snapshot.
- Return structured cache-build metadata from the async builder so callers can inspect the outcome.
- Make `/kvk_admin refresh_stats_cache`, startup logs and telemetry report a degraded/last-known-good refresh as a warning rather than an unqualified success.
- Preserve existing availability-first behaviour when the existing SQL/cache snapshot is valid.

#### Delivery

- Create forward migration and rollback scripts using the next available `20260827_00x` migration identifier.
- Update authoritative SQL schema snapshots.
- Add SQL verification/rehearsal tooling appropriate to the repository.
- Add or update focused bot tests.
- Document deployment, data repair, smoke validation and rollback steps.
- Produce coordinated SQL and bot PR summaries.

### Out of Scope

- Changing the canonical `KP Loss = healed × 20` formula.
- Changing Tanking Score formula or engagement rules.
- Changing combat windows for kills, deads or Kill Points; they already use `PRE_PASS_4_SCAN`.
- Changing matchmaking-based windows for Power, Helps, RSS or Ranged Points.
- Adding a separate “healing outside KVK” metric.
- Bulk-regenerating every historical `EXCEL_FOR_KVK_N` table.
- Fixing the unrelated `HoH_Deads` current-KVK filtering issue in this task.
- Changing KVK target publication/state logic.
- Changing slash-command names, options, permissions, registration or response visibility.
- Redesigning KVK cards or their backgrounds.
- Broad `UPDATE_ALL2` refactoring beyond changes strictly required for this bug fix.
- Creating a new provenance table when `KVKFinalReportHeader` can provide the required contract.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation because this spans SQL materialisation, cache persistence, restart behaviour and two repositories. |
| `k98-discord-command-feature` | not applicable | No command surface or interaction contract is being changed; only the existing admin command's result wording may consume richer service metadata. |
| `k98-sql-validation` | use | Core task: stored procedures, dynamic output tables, `ProcConfig`, output provenance, transactions and cache source data. |
| `k98-test-selection` | use | Required to select SQL rehearsal checks and focused bot regression tests. |
| `k98-deferred-optimisation-capture` | use if needed | Capture only genuinely out-of-scope findings discovered during audit; do not expand this task. |
| `k98-pr-review` | use | Required independently for the bot and SQL diffs before handoff. |
| `k98-promotion-check` | use | Required because SQL must deploy before the coordinated bot promotion and current KVK data must be rebuilt. |
| `k98-security-review-routing` | use | Required for both affected repositories. Select diff-focused Changes reviews as recorded below. |

### Security Review Decision

| Repository | Routing outcome | Scan type | Deep scan | Target | Reason |
|---|---|---|---|---|---|
| `K98-bot-SQL-Server` | diff-focused Changes review | `Changes` | off | final approved base..head SQL branch diff | Runtime SQL, transactions, locks, dynamic object access and data-integrity behaviour change. |
| `K98-bot-mirror` | diff-focused Changes review | `Changes` | off | final approved base..head bot branch diff | Restart-sensitive cache persistence, SQL refresh failure handling, telemetry and operator status reporting change. |

Do not run a repository-wide Codebase scan. Do not run a deep scan. Correct the setup and stop if the review tool shows `Codebase`, a whole-repository target, or Deep enabled.

## 8. Mandatory Workflow

1. **Audit and scope review only.**
   - Inspect both current repositories and live configuration.
   - Confirm or correct every assumption in this pack.
   - Report exact affected objects, callers, transaction boundaries, cache routes and tests.
   - Stop for approval.

2. **Architecture and implementation design.**
   - Present the exact SQL provenance guard, transaction/locking strategy, cache outcome contract, migration/rollback plan and coordinated file manifest.
   - Explain any deviation from reusing `KVKFinalReportHeader`.
   - Stop for approval.

3. **Implementation plan.**
   - Provide ordered SQL and bot changes, validation fixtures, deployment repair commands and rollback sequence.
   - Stop for approval.

4. **Implementation after approval.**
   - Keep SQL and bot changes in separate repositories/PRs.
   - Keep both branches aligned to the same task name.
   - Do not mix unrelated cleanup.

5. **Validation and final review.**
   - Run selected tests and SQL rehearsals.
   - Run separate diff-focused Changes security reviews.
   - Complete PR review and promotion readiness checks.

6. **Handoff.**
   - Deliver exact deployment sequence, evidence, residual risks and rollback commands.

### First Codex response must contain

- confirmation of the current healed-troop lower bound;
- confirmation of every downstream consumer affected through `HealedTroopsDelta`;
- an exact normal-path versus partial-success refresh sequence;
- confirmation that `KVKFinalReportHeader` is updated atomically with `EXCEL_FOR_KVK_N`;
- the proposed stale-output validation rules;
- the proposed transaction and concurrency approach for `STATS_FOR_UPLOAD`;
- the proposed bot cache outcome contract;
- exact review/modify/create file manifests for both repositories;
- proposed migration and rollback filenames;
- focused test plan;
- explicit out-of-scope/deferred findings;
- no code changes yet.

## 9. Audit Requirements

### 9.1 SQL data-flow audit

Trace and document:

```text
KingdomScanData4
  -> CREATE_DELTA_TABLES
  -> HealedTroopsDelta
  -> sp_ExcelOutput_ByKVK
  -> EXCEL_FOR_KVK_N
  -> SP_Stats_for_Upload
  -> STATS_FOR_UPLOAD
  -> player_stats_cache.json
  -> stats/rankings/history consumers
```

For each stage record:

- owner object/module;
- transaction ownership;
- lower and upper scan boundaries;
- source and target row identity;
- refresh/provenance metadata;
- failure behaviour;
- retry behaviour;
- concurrency controls;
- whether last-known-good data is preserved.

### 9.2 Live configuration audit

Query the deployed database rather than relying on task-pack constants:

- latest eligible KVK;
- `DRAFTSCAN`;
- `MATCHMAKING_SCAN`;
- `PRE_PASS_4_SCAN`;
- `KVK_END_SCAN`;
- current `MAX(KingdomScanData4.SCANORDER)`;
- current and expected output final scan;
- current `KVKFinalReportHeader` row;
- current `EXCEL_FOR_KVK_N` row count;
- current `STATS_FOR_UPLOAD` row count and `LAST_REFRESH`;
- distinct `HealedTroopsDelta` values/counts before Pass 4.

Confirm whether KVK 16 is still pre-Pass-4 at execution time. The implementation must remain generic if fighting has begun before deployment.

### 9.3 `UPDATE_ALL2` failure-window audit

Identify every point after Phase A's durable commit but before successful KVK output publication, including at minimum:

- immutable archive handoff;
- `CREATE_THE_AVERAGES`;
- `sp_Rebuild_ExcelForDashboard`;
- `CREATE_DASH2`;
- `sp_ExcelOutput_ByKVK`;
- connection loss, timeout, cancellation or process termination.

Confirm whether any existing recovery job automatically resumes Phase B. Do not assume it does.

### 9.4 Independent cache-refresh audit

Identify every caller of:

- `build_player_stats_cache`;
- `_build_cache_sync`;
- `SP_Stats_for_Upload`.

At minimum inspect:

- bot startup scheduling;
- `/kvk_admin refresh_stats_cache`;
- post-import processing;
- direct module execution;
- tests and operational scripts.

Confirm which paths can execute after a partial SQL import and how their result is currently reported.

### 9.5 Existing provenance audit

Verify that:

- `sp_ExcelOutput_ByKVK` updates `KVKFinalReportHeader` only after the output table and union view are valid;
- the header write participates in the same transaction as output materialisation;
- `FinalScanOrder` represents `@LatestScanToUse`;
- `OutputRowCount` corresponds to the current KVK output;
- `Revision`, `State` and `FinalizationBasis` can be consumed without changing leadership-history semantics.

If any statement is false, stop and propose the smallest safe provenance alternative before implementation.

### 9.6 Cache validity audit

Define the minimum conditions under which existing `STATS_FOR_UPLOAD` can be reused after a source refresh failure:

- non-empty;
- exactly one intended/current KVK;
- valid Governor IDs;
- coherent `LAST_REFRESH`;
- no cross-KVK mix;
- no schema/mapping failure.

If those conditions are not met, preserve the existing JSON cache rather than writing a bad replacement.

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Scan-window business rule | `dbo.sp_ExcelOutput_ByKVK` |
| Successful output provenance | existing `dbo.KVKFinalReportHeader` contract |
| Projection/publication into `STATS_FOR_UPLOAD` | `dbo.SP_Stats_for_Upload` |
| SQL publication serialization | existing SQL lock helper or a narrowly scoped `sp_getapplock` inside the publication procedure |
| Cache build and persistence ownership | `player_stats_cache.py` |
| Operator cache-refresh result shaping | `kvk/services/kvk_admin_service.py` |
| Slash command | existing thin handler in `commands/stats_cmds.py`; no new SQL or business logic |
| Combat formulas | existing `kvk/combat_metrics.py`; unchanged |
| SQL migration and rollback | SQL repository `migrations/` and `migrations/rollback/` |
| SQL operational validation | existing SQL repo deploy/release verification convention |
| Bot tests | `tests/` |
| Task/closeout documentation | `docs/task_packs/` or current indexed task location |

## 11. Likely Files

The audit must confirm the final manifest before implementation.

### SQL repository - Review

- `sql_schema/dbo.UPDATE_ALL2.StoredProcedure.sql`
- `sql_schema/dbo.sp_ExcelOutput_ByKVK.StoredProcedure.sql`
- `sql_schema/dbo.SP_Stats_for_Upload.StoredProcedure.sql`
- `sql_schema/dbo.KVKFinalReportHeader.Table.sql`
- `sql_schema/dbo.usp_RecordKvkFinalReportCompletion.StoredProcedure.sql`
- `sql_schema/dbo.v_EXCEL_FOR_KVK_All.View.sql`
- `sql_schema/dbo.STATS_FOR_UPLOAD.Table.sql`
- `sql_schema/dbo.HealedTroopsDelta.Table.sql`
- `migrations/20260607_001_preserve_stats_for_upload_last_refresh_time.sql`
- current migration and deploy verification conventions

### SQL repository - Modify

- `sql_schema/dbo.sp_ExcelOutput_ByKVK.StoredProcedure.sql`
- `sql_schema/dbo.SP_Stats_for_Upload.StoredProcedure.sql`

Modify `dbo.UPDATE_ALL2` only if the audit proves a small caller-level change is necessary after hardening the two owning procedures. Do not refactor Phase B generally.

### SQL repository - Create

Use the next available suffix at implementation time:

- `migrations/20260827_00x_align_kvk_healed_window_and_stats_refresh_provenance.sql`
- `migrations/rollback/20260827_00x_align_kvk_healed_window_and_stats_refresh_provenance_rollback.sql`
- one focused verification/rehearsal script following the current repository convention, for example:
  - `deploy/Test-KvkHealedWindowAndStatsRefreshProvenance.ps1`, or
  - an equivalently named SQL verification script if that is the active convention

### Bot repository - Review

- `player_stats_cache.py`
- `bot_instance.py`
- `processing_pipeline.py`
- `commands/stats_cmds.py`
- `kvk/services/kvk_admin_service.py`
- `kvk/services/kvk_stats_card_service.py`
- `kvk/services/kvk_rankings_service.py`
- `services/kvk_history_service.py`
- `kvk/combat_metrics.py`
- related tests

### Bot repository - Modify

Expected:

- `player_stats_cache.py`
- `kvk/services/kvk_admin_service.py`
- `tests/test_player_stats_cache.py`
- `tests/test_kvk_admin_service.py`

Modify the following only if focused regression coverage or status propagation requires it:

- `processing_pipeline.py`
- `bot_instance.py`
- `commands/stats_cmds.py`
- `tests/test_kvk_stats_card_payload.py`
- `tests/test_kvk_combat_metrics.py`

### Bot repository - Create

- None expected.
- A new focused test file is acceptable only when it produces a cleaner contract than extending the existing tests.

## 12. Implementation Requirements

### 12.1 Correct the healed-troop combat window

In `sp_ExcelOutput_ByKVK`:

- change only the current-KVK healed aggregation lower bound from `@Scan` to `@PRE_PASS_4_SCAN`;
- retain the configured upper bound and existing Governor filtering;
- retain the baseline `Starting_HealedTroops` value from the snapshot at `@Scan`;
- ensure no pre-Pass-4 healing leaks into `HealedTroopsDelta`;
- ensure the procedure remains generic across every KVK and does not contain KVK 16 constants;
- preserve all unrelated metric windows.

Required semantic contract:

```text
HealedTroopsDelta =
  SUM(HealedTroopsDelta rows
      where DeltaOrder > PRE_PASS_4_SCAN
        and DeltaOrder <= KVK_END_SCAN)
```

For a current KVK where `MAX(SCANORDER) <= PRE_PASS_4_SCAN`, every output row must have `HealedTroopsDelta = 0`.

### 12.2 Preserve downstream formula ownership

Do not change:

```text
KP Loss = healed × 20
Tanking Score = Kill Points × 100 / (KP Loss + deads)
```

The SQL source correction must flow naturally into:

- `/kvk stats`;
- KVK rankings;
- KVK history;
- leadership/self-service consumers that use the canonical combat helper.

Add regression tests that prove the formulas remain unchanged and that zero pre-fight healing yields zero KP Loss.

### 12.3 Make KVK output freshness provable

Before `SP_Stats_for_Upload` mutates `STATS_FOR_UPLOAD`, it must resolve and validate:

- latest eligible KVK;
- current max scan;
- configured `KVK_END_SCAN`;
- expected materialised final scan:

```text
ExpectedFinalScan = MIN(CurrentMaxScan, KVK_END_SCAN)
```

- matching `KVKFinalReportHeader` row;
- `State = OUTPUT_COMPLETE`;
- header `FinalScanOrder = ExpectedFinalScan`;
- source `EXCEL_FOR_KVK_N` exists;
- source row count is positive;
- source row count matches the proven header row count;
- source rows belong to the selected KVK;
- the scan date for `FinalScanOrder` exists and is coherent.

Use the repository's current numeric/config types and defensive `TRY_CONVERT` conventions. Do not silently coerce invalid configuration.

### 12.4 Correct `LAST_REFRESH` semantics

`LAST_REFRESH` must remain the source scan time, consistent with the existing column purpose.

Set it from the `KingdomScanData4.ScanDate` associated with the **proven successful `FinalScanOrder`**.

Do not use:

```sql
SELECT MAX(ScanDate) FROM dbo.KingdomScanData4
```

as the output timestamp unless the provenance guard has already proved that the KVK output was generated from that same scan.

`FinalDataAtUtc` may be logged or exposed in cache metadata as output-generation provenance, but it must not silently replace the source-scan meaning of `LAST_REFRESH`.

### 12.5 Fail closed before destructive publication

On any missing/stale/inconsistent provenance condition:

- raise a stable diagnostic SQL error before truncating or replacing `STATS_FOR_UPLOAD`;
- include KVK, expected scan, proven scan and object identity where safe;
- leave the existing `STATS_FOR_UPLOAD` untouched;
- make the failure retryable by the independent cache route after `sp_ExcelOutput_ByKVK` has completed.

Do not use `CHECKPOINT` plus a fixed delay as proof that a logical output is current. A checkpoint concerns durability, not whether the downstream materialisation ran.

Audit the existing checkpoint/delay calls. Remove them only where provenance validation makes them redundant and there is no separate operational dependency; otherwise document why they remain.

### 12.6 Make replacement atomic

The current truncate-plus-insert sequence must be made atomic.

Required outcomes:

- readers never observe an intentionally empty table between truncate and insert;
- an insert, row-count, index/statistics or validation failure does not destroy last-known-good rows;
- concurrent startup/admin/import publishers cannot interleave destructive operations.

Use the smallest repository-consistent approach, such as:

- build/validate in a staging or temporary structure and swap/project under a transaction; and/or
- an explicit transaction with correct ownership/savepoint handling; and
- an exclusive application lock scoped to `STATS_FOR_UPLOAD` publication when no equivalent lock exists.

Document:

- lock resource name;
- lock owner;
- timeout;
- transaction owner;
- behaviour inside and outside caller-owned transactions;
- rollback behaviour.

Do not create broad database-level locks.

### 12.7 Verify publication row shape

After the candidate population is built and before commit:

- row count must be positive;
- row count must match the selected `EXCEL_FOR_KVK_N` source;
- Governor IDs must be valid and unique under the existing contract;
- all rows must contain the selected `KVK_NO`;
- all rows must share the proven `LAST_REFRESH`;
- exemption status logic must remain unchanged.

### 12.8 Expose cache refresh outcome honestly

In `player_stats_cache.py`, track a structured source refresh outcome. Exact naming may follow local style, but it must distinguish at least:

- `refreshed`: `SP_Stats_for_Upload` completed and the SQL snapshot was read;
- `last_known_good`: the procedure failed, but the existing SQL snapshot passed validity checks and was reused;
- `skipped`: refresh was disabled by configuration;
- `failed`: no valid SQL snapshot could safely replace the existing JSON cache.

Recommended `_meta` fields:

```json
{
  "source_refresh_status": "refreshed|last_known_good|skipped|failed",
  "source_refresh_succeeded": true,
  "source_kvk_no": 16,
  "source_last_refresh": "2026-08-26T21:24:00",
  "source_row_count": 1234
}
```

Use `null` where a boolean does not apply. Error details must be bounded and safe; credentials, connection strings and secrets must never be written to cache files or Discord.

Correct or replace the existing ambiguous `sp_executed` field. If retained for compatibility, define it as “attempted” and add an unambiguous success/status field.

### 12.9 Preserve valid cache and reject invalid fallback data

If the SQL refresh fails:

- validate existing `STATS_FOR_UPLOAD` before reusing it;
- reuse only a coherent non-empty snapshot;
- mark the JSON cache and telemetry as `last_known_good`;
- if SQL data is empty, mixed-KVK, malformed or does not meet the intended KVK contract, raise so `_build_and_persist_cache_sync` preserves the existing JSON file;
- do not overwrite a healthy JSON cache with an invalid SQL result.

### 12.10 Return structured outcomes to callers

`build_player_stats_cache()` must return the worker's structured result rather than discarding it. Existing callers that ignore the return value must continue to work.

Update `kvk_admin_service` so `/kvk_admin refresh_stats_cache` can report:

- success when SQL source refresh succeeded;
- warning when the cache was rebuilt from last-known-good SQL;
- failure/preserved-existing when no safe replacement was available.

Do not move SQL or cache business logic into `commands/stats_cmds.py`.

### 12.11 Logging and telemetry

SQL logs/errors must identify:

- KVK;
- expected final scan;
- proven final scan;
- header revision;
- source row count;
- publication row count;
- lock/transaction failure stage.

Bot logs/telemetry must identify:

- source refresh status;
- cache path;
- source KVK;
- source last refresh;
- row count;
- whether existing SQL or JSON data was preserved.

Do not log player row payloads or secrets.

### 12.12 Migration requirements

The forward migration must:

- follow the current migration header and safety conventions;
- use `CREATE OR ALTER`/`ALTER` consistently with the repository;
- update both authoritative procedure snapshots;
- avoid permanent KVK 16 constants;
- be idempotent where repository standards require;
- include pre/post validation queries;
- include a data-safety plan;
- state deployment order and required current-output rebuild.

The rollback must:

- restore the exact prior stored-procedure definitions;
- preserve table data;
- state that regenerated current output/cache will be required after rollback;
- include rollback verification.

### 12.13 Current KVK repair

After SQL deployment, use live configuration to resolve KVK and baseline scan. For the known KVK 16 case the expected repair shape is:

```sql
EXEC dbo.sp_ExcelOutput_ByKVK
    @KVK = 16,
    @Scan = 1059;

EXEC dbo.SP_Stats_for_Upload;
```

Do not execute hard-coded values without confirming the live database still matches them.

Then rebuild the bot cache through the supported operator route and smoke-test affected cards.

### 12.14 Historical behaviour

The corrected procedure is generic, so any historical KVK explicitly regenerated later will also use the correct post-Pass-4 healing window.

Do not bulk-regenerate all historical outputs in this task. Document the potential historical effect and capture a separate decision if leadership wants historical correction.

## 13. Refactor Decisions

| Issue | Decision | Reason |
|---|---|---|
| Healing uses matchmaking rather than Pass-4 boundary | fix now | Direct source of false KP Loss and Tanking Score. |
| `LAST_REFRESH` uses global latest scan instead of successful output scan | fix now | Can falsely advertise freshness after a partial import. |
| `STATS_FOR_UPLOAD` truncate/insert is not demonstrably last-known-good safe | fix now | Same publication boundary and failure mode; must be atomic. |
| Cache metadata records attempted SP execution rather than success | fix now | Operator/admin route can report degraded refresh as success. |
| Async cache builder discards structured result | fix now | Prevents correct operator reporting and is backward-compatible to return. |
| New output-provenance table | not applicable | Reuse `KVKFinalReportHeader` unless audit disproves suitability. |
| Broad `UPDATE_ALL2` Phase B recovery/resume redesign | defer | Larger operational resilience project; provenance guard protects this surface now. |
| Historical bulk output regeneration | defer | Separate data-correction decision with wider validation impact. |
| `HoH_Deads` KVK filtering | defer | Valid but unrelated issue; do not mix into this PR. |
| Other matchmaking-based deltas | not applicable | Their business rules are unchanged by this task. |
| Card/UI redesign | not applicable | Correct source data and status wording only. |

Any newly discovered deferred item must use the structured format in `docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 14. Testing Requirements

### 14.1 SQL preflight evidence

Capture before-state evidence without changing production data:

- live `ProcConfig` boundaries;
- max scan and scan date;
- `KVKFinalReportHeader`;
- `EXCEL_FOR_KVK_N` count;
- `STATS_FOR_UPLOAD` count and timestamp;
- number/sum of pre-Pass-4 healed rows;
- procedure definitions/hashes;
- existing indexes and transaction settings.

### 14.2 SQL healed-window tests

Cover:

1. **Pre-Pass-4 current KVK**
   - when max scan is at or below `PRE_PASS_4_SCAN`, every output `HealedTroopsDelta` is zero.

2. **Boundary exclusion**
   - a delta at exactly `PRE_PASS_4_SCAN` is excluded.

3. **First eligible scan**
   - a delta at `PRE_PASS_4_SCAN + 1` is included.

4. **Upper bound**
   - deltas after `KVK_END_SCAN` are excluded.

5. **Multiple scans**
   - eligible healed deltas sum exactly once per governor.

6. **Baseline preservation**
   - `Starting_HealedTroops` still comes from the configured snapshot scan.

7. **Unrelated metrics**
   - kills, deads, Kill Points, Power, Helps, RSS and Ranged windows remain unchanged.

### 14.3 SQL provenance tests

Cover:

1. successful header matches expected scan;
2. missing header;
3. stale header scan;
4. header scan newer than expected;
5. missing source table;
6. zero source rows;
7. header/source row-count mismatch;
8. invalid/mixed KVK rows;
9. missing source scan date;
10. successful atomic replacement;
11. forced candidate insert failure;
12. lock timeout/concurrent publisher;
13. rollback preserves prior rows;
14. `LAST_REFRESH` equals the scan date for the proven `FinalScanOrder`;
15. completed-KVK case where global max scan exceeds `KVK_END_SCAN`.

For every negative test, prove that the pre-existing `STATS_FOR_UPLOAD` row count, KVK and timestamp remain unchanged.

Use rollback-contained fixtures or a disposable test database. Do not damage production data to simulate failure.

### 14.4 Bot unit tests

Update/add focused tests for:

- SP success produces `source_refresh_status=refreshed`;
- SP failure plus valid SQL snapshot produces `last_known_good`;
- SP disabled produces `skipped`;
- SP failure plus invalid SQL snapshot raises/preserves existing JSON;
- no credentials or unbounded SQL error text enters JSON metadata;
- async `build_player_stats_cache()` returns its structured result;
- telemetry carries refresh status;
- admin service formats success, warning and failure distinctly;
- existing cache lock and atomic file-write behaviour remains intact;
- current integer/date parsing remains intact;
- canonical combat formula remains `healed × 20`;
- zero healed delta gives zero KP Loss;
- positive healed delta still gives the expected KP Loss and Tanking Score.

Suggested focused commands, subject to `k98-test-selection`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_player_stats_cache.py `
  tests/test_kvk_admin_service.py `
  tests/test_kvk_combat_metrics.py `
  tests/test_kvk_stats_card_payload.py
```

### 14.5 Bot quality gates

Run or justify skipping:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe scripts\smoke_imports.py
```

Run the broader pytest suite when selected by risk or explain any unrelated failure precisely.

Command registration validation should be a documented skip because no command registration/decorator surface changes.

### 14.6 Integration and smoke validation

After coordinated deployment:

- refresh the current KVK output;
- refresh `STATS_FOR_UPLOAD`;
- rebuild player stats cache;
- verify the admin refresh response reports `refreshed`;
- inspect at least three known players who previously showed pre-fighting healing/KP Loss;
- confirm current `HealedTroopsDelta = 0` and `KP Loss = 0` while still pre-Pass-4;
- confirm Starting Healed remains populated;
- confirm Kills, Deads, Kill Points and target fields are unchanged;
- confirm `LAST_REFRESH` matches the proven output scan date;
- verify startup rebuild is safe;
- verify a simulated stale-output condition warns/reuses last-known-good rather than restamping.

### 14.7 AI-assisted review gates

Before PR handoff:

- run `k98-pr-review` independently for each repository;
- run SQL repository diff-focused Changes security review, Deep off;
- run bot repository diff-focused Changes security review, Deep off;
- triage and resolve accepted findings within scope;
- rerun affected tests after any fix;
- report base/head and review outcome for both repositories.

## 15. Acceptance Criteria

### Healed troops and combat metrics

- [ ] `HealedTroopsDelta` includes only rows with `DeltaOrder > PRE_PASS_4_SCAN`.
- [ ] A current pre-Pass-4 KVK produces zero current healing for every player.
- [ ] `Starting_HealedTroops` remains the snapshot baseline.
- [ ] KP Loss formula remains unchanged.
- [ ] Tanking Score formula remains unchanged.
- [ ] Pre-Pass-4 healing no longer creates KP Loss or Tanking Score.
- [ ] Other metric windows are unchanged.

### Provenance and SQL publication safety

- [ ] `KVKFinalReportHeader` is reused as canonical successful-output provenance.
- [ ] No duplicate provenance table is introduced.
- [ ] `SP_Stats_for_Upload` validates expected versus proven final scan before mutation.
- [ ] Source object, KVK identity, row count and scan date are validated.
- [ ] `LAST_REFRESH` is derived from the proven output scan date.
- [ ] Global max scan cannot be applied to an older materialised output.
- [ ] Missing/stale provenance fails before destructive publication.
- [ ] `STATS_FOR_UPLOAD` replacement is atomic.
- [ ] Concurrent publishers are serialized or otherwise proven safe.
- [ ] Last-known-good SQL rows survive every tested negative path.
- [ ] Completed KVKs work when global max scan is later than `KVK_END_SCAN`.

### Cache and operator behaviour

- [ ] Cache metadata distinguishes refreshed, last-known-good, skipped and failed outcomes.
- [ ] `sp_executed` is removed or explicitly redefined as attempted.
- [ ] Invalid SQL fallback data cannot overwrite a healthy JSON cache.
- [ ] The async builder returns structured metadata.
- [ ] Startup logs and telemetry report degraded refreshes.
- [ ] `/kvk_admin refresh_stats_cache` warns when using last-known-good data.
- [ ] No command surface or permission contract changes.
- [ ] No secrets enter logs, cache metadata or Discord output.

### Delivery and validation

- [ ] Forward and rollback SQL migrations exist and follow repository standards.
- [ ] Authoritative SQL schema snapshots match the migration.
- [ ] Focused SQL verification tooling exists and passes.
- [ ] Focused bot tests pass.
- [ ] Architecture, deferred-item and security-routing validators pass.
- [ ] Separate diff-focused Changes reviews complete for SQL and bot.
- [ ] SQL deployment and current-KVK rebuild precede bot deployment.
- [ ] Post-deployment smoke evidence is captured.
- [ ] Rollback steps are tested or rehearsed.
- [ ] Out-of-scope findings are captured without expanding the PRs.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. Confirmed root causes
3. Final architecture
4. SQL file manifest
5. Bot file manifest
6. New files
7. Modified files
8. SQL changes
9. Cache/status contract
10. Helpers and provenance reused
11. Refactor findings
12. Test evidence
13. AI review gates
14. SQL deployment steps
15. Current-KVK data repair
16. Bot promotion/deployment steps
17. Smoke-test evidence
18. Rollback steps
19. Deferred optimisations
20. Residual risks

For every repository include:

- branch;
- base and head;
- changed files;
- test commands;
- security review route/result;
- PR-ready summary.

## 17. PR Summary Template

### SQL PR

```md
## Summary

- Align KVK healed-troop deltas with the configured post-Pass-4 combat window.
- Make STATS_FOR_UPLOAD publication provenance-validated and last-known-good safe.

## Changes

- Use PRE_PASS_4_SCAN as the healed lower boundary.
- Reuse KVKFinalReportHeader to validate the successful EXCEL_FOR_KVK output scan.
- Derive LAST_REFRESH from the proven output scan date.
- Make STATS_FOR_UPLOAD replacement atomic and concurrency-safe.
- Add migration, rollback and verification tooling.

## Tests

- <SQL preflight/rehearsal commands>
- <post-migration verification>
- <rollback verification>

## AI Review Gates

- Codex Security routing: diff-focused Changes review
- Scan type: Changes
- Deep: off
- Target: <base>..<head>
- Result: <result>

## Deferred Optimisations

- <none or structured items>

## Risk / Rollback

- SQL deploys before bot.
- Rollback restores prior procedure definitions and requires current output/cache regeneration.
```

### Bot PR

```md
## Summary

- Report whether player stats cache data was freshly published or reused from last-known-good SQL.
- Prevent invalid SQL fallback data from replacing a healthy JSON cache.

## Changes

- Add structured source refresh status to player stats cache metadata.
- Return cache build outcome to callers.
- Make admin/startup/telemetry reporting distinguish success, degraded reuse and failure.
- Add focused regression tests.

## Tests

- <focused pytest commands>
- <architecture/deferred/security routing validators>
- <pre-commit/smoke evidence>

## AI Review Gates

- Codex Security routing: diff-focused Changes review
- Scan type: Changes
- Deep: off
- Target: <base>..<head>
- Result: <result>

## Deferred Optimisations

- <none or structured items>

## Risk / Rollback

- Bot deploys only after SQL migration and KVK output repair.
- Rollback restores prior cache reporting; SQL remains source of truth.
```

## Appendix A - Expected Failure Model

### Normal successful import

```text
new scan
  -> UPDATE_ALL2 Phase A commits KS4
  -> Phase B succeeds
  -> sp_ExcelOutput_ByKVK commits EXCEL_FOR_KVK_N + KVKFinalReportHeader
  -> SP_Stats_for_Upload validates provenance and atomically publishes
  -> cache rebuild reports refreshed
```

### Partial SQL success followed by independent cache refresh

```text
new scan
  -> Phase A commits KS4
  -> archive/Phase B/output refresh fails before KVK output commit
  -> KVKFinalReportHeader remains on previous final scan
  -> startup/admin cache refresh invokes SP_Stats_for_Upload
  -> procedure detects expected scan != proven scan
  -> STATS_FOR_UPLOAD remains unchanged
  -> cache reuses valid last-known-good SQL or preserves existing JSON
  -> operator receives warning, not false success
```

## Appendix B - Deployment Sequence

1. Back up/record current procedure definitions and live evidence.
2. Deploy the SQL migration.
3. Run SQL post-validation.
4. Resolve live current KVK and baseline scan.
5. Execute `sp_ExcelOutput_ByKVK` for that KVK.
6. Verify `KVKFinalReportHeader` final scan and row count.
7. Execute `SP_Stats_for_Upload`.
8. Verify `LAST_REFRESH`, KVK identity and healed values.
9. Deploy/promote the bot PR.
10. Restart the bot through the supported process.
11. Run `/kvk_admin refresh_stats_cache`.
12. Smoke-test KVK stats/rankings/history for selected players.
13. Capture evidence and close out.

## Appendix C - Rollback Sequence

1. Stop new bot deployment/promotion.
2. Roll back bot PR if already deployed.
3. Apply the SQL rollback migration.
4. Resolve the live KVK and baseline scan.
5. Regenerate `EXCEL_FOR_KVK_N`.
6. Repopulate `STATS_FOR_UPLOAD`.
7. Rebuild player stats cache.
8. Verify table/cache row counts and timestamps.
9. Restart/smoke-test the bot.
10. Document why rollback was required and capture any follow-up work.
