# B02 — scoped legacy KVK / ProcConfig content baseline

PROPOSED, NOT APPROVED OR EXECUTED. Chris Watts operator/reviewer/abort owner. Existing window expires2026-09-29T09:23:23Z. Single-account model unchanged. No production observations, deployment, migration, provider calls or Git publication.

## Scope decision from source and retained evidence

R01–R03 established successful historical chain application, final recovery and standard CHECKDB on development database22. B01 observed367tables,4994columns,316unique-key column rows. Many tables lack unique keys. The first content baseline covers all12 existing KVK-schema tables plus3ProcConfig tables,15total, approximate2,410,159rows. The remaining352tables are protected but OUTSIDE this content fingerprint; no whole-database row-preservation pass is claimed.

The S11 evidence migration20260924_001 declares zero existing application rows affected and requires S10 ownership prerequisites absent from the observed snapshot. The legacy permissions migration20260924_002 declares no application row changes, requires public-only signing inputs and explicitly rejects a database name other than ROK_TRACKER. Neither migration is executable here as-is, and this packet does not change guards, install prerequisites, rename databases or authorize broad source synchronization. Source module DML inside authored procedures is not evidence those procedures were invoked. An exact future install manifest remains necessary.

53source-only /38observed-only exact-name discrepancies from B01 are not a missing-object install list: dbo.ID_ versus observed dbo.ID#, and dbo.LATEST_T4_T5_KILLS versus dbo.LATEST_T4&T5_KILLS illustrate source-filename sanitization differences. Relevant KVK.Source*/dbo.Export*absence is recorded separately. All original source and retained fixture objects remain untouched.

## Exact proposed operation

File: C:\discord_file_downloader\.codex_artifacts\s11-g4-capture-preparation-20260926\commands\B02.sql

SHA256: ec3d86720f3a24dfe2f17761eb9235c0f479c5113ef793a4bc29cce4afd4f6af

One whole-file execution after approval in fresh SSMS localhost\K98DEV, master, Windows Authentication. Guards bind observed original login MicrosoftAccount\cwattsconsulting@outlook.com, server9SX2VF4\K98DEV, machine9SX2VF4, instanceK98DEV, sysadmin1 and exact engine16.0.1200.5 (native binary encoding domain). Target only databaseID22 S11_G4_Recovery_20260928_97337, same exact two paths/sizes, ONLINE, RESTRICTED_USER, read-only, Broker0. Fresh temp names and clear transaction state required. Each table checks observed object ID/name, ordinary table flags, exact column count, column IDs/names/system/user type IDs, length, precision, scale, collation/nullability and special flags before reading content. Literal SELECT queries only; no dynamic business SQL or stored procedures invoked.

| Table | B01 approximate rows (not a result expectation) | Columns |
|---|---:|---:|
| dbo.ProcConfig | 128 | 4 |
| dbo.ProcConfig_AuditLog | 392 | 7 |
| dbo.ProcConfig_Staging | 14 | 10 |
| KVK.KVK_AllPlayers_Raw | 2049960 | 51 |
| KVK.KVK_AllPlayers_Stage | 52668 | 51 |
| KVK.KVK_Camp_Windowed | 80 | 16 |
| KVK.KVK_CampMap | 128 | 4 |
| KVK.KVK_DKPWeights | 4 | 5 |
| KVK.KVK_Ingest_Diagnostics | 2 | 18 |
| KVK.KVK_Ingest_Negatives | 0 | 9 |
| KVK.KVK_Kingdom_Windowed | 920 | 17 |
| KVK.KVK_Player_Baseline | 33100 | 4 |
| KVK.KVK_Player_Windowed | 272474 | 20 |
| KVK.KVK_Scan | 253 | 13 |
| KVK.KVK_Windows | 36 | 7 |

The manifest binds all observed column descriptors and local authoritative source-file hashes. Every selected source table file exists and contains all observed column-name tokens. This validates source naming; full installed-source definition equality is NOT inferred. Runtime guards deliberately use the observed installed shape. No sql_variant, computed, encrypted or FILESTREAM columns occur in this scope; out-of-scope sql_variant fixture inventory remains protected and unscanned.

## Fingerprint representation

Version B02-native-varbinary-framed-v1, fixed engine16.0.1200.5. Each row starts binary0xB002. In column-ID order, NULL is byte00; non-NULL is byte01, eight-byte binary(bigint) byte length, then CONVERT(varbinary(max),the explicitly named typed column). Every concatenation starts/max-promotes to varbinary(max); no8000-byte implicit truncation. This preserves length, NULL-versus-empty, Unicode bytes, trailing spaces and SQL-native typed representations in the pinned engine. It is not a physical page hash or a portable cross-version value serializer.

SHA2_256 hashes each complete framed row. Sort all32-byte row hashes in binary order, retaining repeated hashes. Split into chunks of4096rows using ROW_NUMBER over row_hash; ties contain identical hashes, so their arbitrary internal order cannot change chunk bytes. For each chunk, hash ASCII uppercase hexadecimal concatenation (64characters per row hash). Final table digest hashes:32-byte schema-domain SHA256 + eight-byte exact total row count + ordered uppercase hexadecimal chunk hashes. Empty table has zero chunks and an explicit zero row count. This is a duplicate-preserving cryptographic multiset fingerprint, not a unique-key assumption or a collision-free mathematical proof. Schema-domain hash binds table/observed column manifest and algorithm/version; future legitimate shape/ID changes require an explicit comparison plan rather than silently recomputing expectations.

Only15compact digest/count result rows plus progress/completion are returned. Raw rows and individual row/chunk hashes stay in session tempdb, not report output. A digest still represents potentially sensitive data: retain it in local task evidence. Diagnostic ContextJson values are hashed only, never printed. No key/token/config-file bytes are read.

## Budgets / effects

Query timeout900seconds; operator cancel910seconds overall. Each table has300-second cooperative limit, operator310seconds from its progress line. Checks do not interrupt blocked statements; cancellation may take time. One attempt only. Output ceiling64KiB. At most2,500,000accepted rows per table; TOP2500001 detects overrun and fails, never accepts a truncated sample. At most1MiB framed bytes per row,4GiB aggregate framed bytes per table,8GiB across packet. Over-limit rows emit NULL hash internally and cause refusal; no partial fingerprint accepted. Source scans may consume resources before aggregate bounds are evaluated; these are acceptance/cooperative limits, not engine I/O quotas.

MAXDOP2 on row hashing/chunk sorting. Temporary indexed row hashes and per-chunk/result tables consume tempdb and memory; no persistent database changes or business writes. Approximate scratch usage sampled from session plus task counters, stop above2GiB incremental retained allocation; counters are not a peak-memory/tempdb quota and can be conservative. C:100GiB floor checked before each table and at final completion. Peak sorts/grants and LOB reads are not hard-capped. Rows limited to this allowlist; no whole-database scan. Delete operations apply only to owned session temp row/chunk tables between tables; no user data cleanup.

No new account, ACL change, restore/backup, DBCC rerun, NOLOCK, migration, grants or Bot action. Tempdb scratch and ordinary read/audit activity occur. Keep target unused by other privileged writers. Read-only guards cannot fence an administrator intentionally changing the state. No forced session termination.

## Evidence / stops

Require approved identity;15per-table result rows with exact counts, canonical bytes, chunk counts, schema and content hashes, elapsed values; final15-table/count/byte/elapsed summary; all Messages/client completion. Save complete report before leaving SSMS. Runtime exact counts may differ from B01 catalog estimates and must be reconciled, not automatically labeled corruption. NOLOCK or catalog counts must not replace exact row counts.

Any error/warning, hash/identity/schema/state/path drift, time/space/row/byte/output limit or incomplete report stops. Preserve partial reports; no retry, cleanup or changing budgets mid-run. Do not turn a partial table list into a preservation pass. Wait for control after cancellation and reset query timeout to10seconds. Operation expires with existing window; no silent extension.

## Remaining gate

Successful B02 would establish a reusable baseline for these15tables only. It does not compare against an unavailable historical source-row digest, prove remaining352tables unchanged, test S11 receipt/fence preservation in absent tables, or accept G4/G5. Retained S6/S8 fixture receipts and uncertain publications remain separate protected evidence. No current-production row scan is implied. Keep this restored copy read-only; future mutation or separate test-copy choice requires an exact operator decision. Installation must preserve this scoped baseline and provide additional evidence for every other affected existing surface before acceptance.

## Local validation

Static checks bind15literal table reads,15result emissions, observed metadata guards, exact engine and30MAXDOP2 query options. Source-column token cross-check found no missing names. Eight pure reference-algorithm invariants passed: NULL/empty, ambiguous concatenation boundaries, trailing spaces, row reorder invariance, duplicates, >8000-byte tail sensitivity,4096/4097chunk boundary, empty input. These are offline reference tests, NOT live SQL encoding or performance proof. No SQL compiled/executed on a server. Full source definition equality and query performance remain unproven until bounded authorized execution/review.

Security routing: preparation-only documented skip for generated operator-review artifacts, not blanket rollout clearance. No deployed implementation or persistent permission changes during authoring, no PR handoff; runtime/PR validators not applicable to this local preparation. Exact scripts/manifests sealed; earlier sealed evidence unchanged. Memory incident investigation remains deferred; withdrawn collector untouched.
