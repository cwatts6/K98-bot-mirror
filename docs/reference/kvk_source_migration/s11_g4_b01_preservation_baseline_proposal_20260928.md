# B01 — preservation baseline discovery packet

PREPARED FOR APPROVAL, NOT EXECUTED. Local preparation only. Operator/reviewer/abort owner Chris Watts; single Windows-account model unchanged. Existing window ends 2026-09-29T09:23:23Z. Final recovery and standard CHECKDB are accepted from R01–R03 receipts; original row/receipt/fence preservation and overall G4 acceptance remain open.

## Facts and limits

Database22 S11_G4_Recovery_20260928_97337 is ONLINE, RESTRICTED_USER, read-only, Broker disabled. Two exact restored files and allocations remain bound in B01 guards. All13 R03 queried source/export tables were absent under sysadmin visibility. This does not establish absence of every KVK table or of legacy business data. No production source implementation is missing merely because these objects are not installed in the restored historical snapshot.

A local manifest hashes382 SQL source table files under C:\K98-bot-SQL-Server\sql_schema. These are reference files, not382 installed objects. dbo.ProcConfig source, for example, defines a composite KVKVersion/ConfigKey key; that definition must be compared to actual metadata before a row query is generated. KVK.SourceRouting and SourceSelection also have source definitions but their installation remains unknown here. No source migration is executed.

## Exact B01 operation

Command: C:\discord_file_downloader\.codex_artifacts\s11-g4-capture-preparation-20260926\commands\B01.sql

SHA256: bb961df9fcb1513301e449af5916dac99fe486864d6c50164cfe9a3704e86ec8

Run once, after exact approval, as a whole file in fresh existing SSMS development localhost\K98DEV, master, Windows Authentication. Required observed binding: server9SX2VF4\K98DEV, machine9SX2VF4, instanceK98DEV, original login MicrosoftAccount\cwattsconsulting@outlook.com, sysadmin1, major16. Standalone transaction-state guards, expiry, databaseID22/name, exact two file paths/sizes, restricted/read-only/Broker-disabled state and100GiB C: free floor are reused. No new credentials or authentication changes.

Reads system catalogs only in that restored database:

1. All non-MS-shipped user table identities and flags (temporal/memory-optimized/filetable), approximate base-index row totals and partition counts from sys.partitions.
2. Their column names/type/schema/IDs/length/precision/scale/collation/nullability and identity/computed/FILESTREAM/sparse/generated/encryption flags.
3. Their unique index key columns/order/direction, PK/unique-constraint/filter/disabled flags. No filter expressions or module/default/computed definitions are read.

Fixed bounds: <=512 table rows, <=8192 column rows, <=4096 key rows. Bounds checked before metadata result sets are returned. On exceeded bounds, stop and prepare a narrower exact packet; no automatic truncation or follow-up scan. Output ceiling16MiB including report formatting; retain a larger accidental output privately and stop acceptance, do not truncate it into a complete-looking receipt.

Query timeout60seconds, cooperative elapsed check60seconds, operator cancellation70seconds. One attempt; no retry. Normal connection/audit/catalog reads and bounded session-local temp tables are the only effects. No business table rows, secrets, key bytes, receipt payloads, SQL migration, provider/Discord access, backup/restore, DBCC rerun or persistent change. Metadata reads can acquire locks and use tempdb; no production call. No hard memory/I/O guarantee is implied by a timeout. Reset query timeout to10seconds after control returns.

Catalog row totals are approximate metadata, not exact COUNT_BIG queries or cryptographic row digests. Missing/unsupported partition metadata (including memory-optimized cases) must not be interpreted as proof that a table is empty. Key candidates may be filtered, disabled or nullable: emitted metadata lets local review reject unsuitable ordering keys. Tables without a safe unique order need a separately designed duplicate-preserving representation; do not invent a key or use a lossy aggregate checksum.

## Evidence / stop

Retain complete identity, catalog count-semantics row, all three metadata result sets, completion counts/elapsed and all Messages/client completion in one report attachment. Reconcile returned cardinalities against completion counts before treating it complete. Wrong identity, state/path/size drift, unsupported schema, output/time/space bounds, error/warning or incomplete output stops; preserve state and report, no cleanup, permissions changes or retry.

## How this leads to preservation comparisons

After B01, locally reconcile actual table/column/key shapes to the sealed source manifest and identify exact legacy data and migration-affected existing tables. Name-only source inventory is not enough. Prepare B02 with literal tables/columns, type-aware unambiguous byte encoding, NULL and length framing, deterministic duplicate-preserving ordering, exact row counts and SHA256 evidence. Resource limits must follow observed sizes and datatype risks; unsupported types stop rather than silently dropping/truncating columns. No CONCAT/CHECKSUM_AGG shortcut will be called byte-exact evidence. Avoid raw sensitive row output; any required retained bytes need their own explicit scope and protected path.

Preserve the read-only recovered database as the historical baseline unless a later exact decision changes that. No current production data is treated as the same historical endpoint. Read-only state is not an immutable cryptographic fence against an administrator. Future install/test target and changes must be separately scoped; no broad install-every-source-only-table policy. Source schema/table absence must be recorded as ABSENT before mutation, not zero rows in an invented table. Source/history/receipt/fence comparisons in retained S6/S8 databases remain separate protected evidence and are not authorized by B01; neither uncertain publication is relabeled resolved by absence in this snapshot.

This packet requests approval only for B01 metadata. It does not execute row fingerprints or complete preservation acceptance, seven typed G4 proofs, S11 installation, rollout or G5. Memory cause stays deferred; withdrawn collector never runs. KVK report/view-rehydration issues remain separate.

## Local validation

B01 static check confirms system-catalog reads/session-temp materialization only, no RESTORE/BACKUP/DBCC/ALTER/DROP/UPDATE/DELETE/EXEC/INSERT operations, exact guards and row/time caps. SQL not compiled/executed against a server. Original27 pending files and394 retained evidence files rehashed unchanged. Source manifest generated by local file reads only.

Security routing: documented preparation-only skip for generated operator-review artifacts, no deployed runtime/config/permission change. No broad audit or PR handoff. Runtime pytest and PR validators skipped for this metadata-capture proposal; no application implementation changed. Preserve earlier seals rather than rewriting their statuses.
