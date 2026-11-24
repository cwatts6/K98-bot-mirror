# B04 — finite raw-table keyset continuation

PROPOSED, NOT EXECUTED. Chris Watts operator/reviewer/abort owner. Existing window ends2026-09-29T09:23:23Z. Exact new approval required; B03success does not authorize continuation. Prior B02timeout correction1200seconds and the3completed ProcConfig results remain retained. No whole-table B02replay or rehash of the accepted pilot.

## Target and command

File C:\discord_file_downloader\.codex_artifacts\s11-g4-capture-preparation-20260926\commands\B04.sql

SHA256 213070e561b40ccc5d8d4a96adce52aaa24529f37389ef9e45ba270cb04dee46

One whole-file execution in a fresh existing SSMS localhost\K98DEV/master Windows Authentication query. Same observed server9SX2VF4\K98DEV, original login MicrosoftAccount\cwattsconsulting@outlook.com, sysadmin1, engine16.0.1200.5. Target only databaseID22 S11_G4_Recovery_20260928_97337 and KVK.KVK_AllPlayers_Raw object2087535066. Exact file sizes/paths and column/PK guards reused from B03. Database must remain ONLINE/RESTRICTED_USER/read-only/Broker0, with100GiB C: free at start and before each chunk. Clear transaction state/fresh temp names/expiry checks remain.

Accepted pilot covers first1024rows from(13,1,18075) through(13,1,44990547),436082canonical bytes, schemaC8874976547356BB3F070617A5CB10F96D42CC6E5A23C5C545BB9581169C6FBA and chunk digestE254FEA225469B28484B24222DD475533D546E3260AB4C92C0BD243FB7DA20E5. B04starts strictly AFTER its last tuple. One exact anchor-key existence check reads that key only; pilot business values are not reread.

## Finite algorithm and effects

Maximum2048source-chunk attempts, at most1024rows each (<=2,097,152additional rows; accepted totals also include pilot1024). Every query uses literal51columns, the observed clustered PK_KVK_AllPlayers_Raw and numeric ascending order KVK_NO,ScanID,governor_id, with the explicit lexicographic predicate greater than the last completed key. MAXDOP1 and RECOMPILE on source selection. Recompile/optimizer may still choose work beyond the row limit: returned/materialized rows are bounded, not physical page reads. There is no OFFSET rescan, global hash sort or whole-table exact COUNT.

Each source chunk is first copied into owned session #B04Sample; only that <=1024row copy is hashed. Each iteration clears only owned temporary sample/hash rows. All51columns have bounded lengths. Same native framed row encoding as B02 and same sorted-row-hash chunk digest as B03. At most1MiB framed bytes per row,8MiB per chunk and4GiB across all chunks including pilot; excess refuses acceptance after the bounded call. Tempdb holds one raw chunk, its hashes and <=2048compact manifest rows; query memory/I/O/sort grants are not hard quotas. No persistent target data or permissions change. SQL connection/audit/tempdb work occurs.

A successful chunk records previous exclusive key, first/last keys, row count, encoded bytes, chunk digest, rolling chain digest and duration. It advances only to its own last key. Any non-advancing boundary stops. An EMPTY subsequent source read is mandatory for completion; a short chunk alone is not used as final proof. Hitting chunk/time/byte caps leaves partial coverage and throws. No automatic next batch/resume/cleanup is authorized.

## Versioned digest and local reconciliation

B04-keyset-v1 seed SHA256 binds its ASCII version,32-byte observed schema hash, pilot row/byte counts encoded binary(8), first/last pilot key tuples encoded(binary4,binary4,binary8), and32-byte pilot chunk digest. Each chain update hashes prior32-byte chain, binary4 chunk number, previous/first/last key tuples, binary8 row/byte counts and32-byte chunk digest. Preserve original script as exact encoding reference.

Returned final digest is the final nonempty-chunk chain; the separate completed receipt must also prove empty-read observation, expected sequence, all boundaries/counts and unchanged state. Do not treat digest alone as coverage proof. Local reconciliation can recompute every chain update from retained pilot+manifest, reject missing/duplicate chunks, verify adjacency of previous and last tuples, and sum counts/bytes. Row keys are included in row hashes and key boundary output is explicitly authorized scope. Other row values are not printed. No mathematically collision-free claim or physical-page equality claim.

This version partitions by primary-key order and differs from B02's whole-table sorted-hash chunking. Do not mix the digest formats. Reuse of pilot relies on the retained read-only baseline and operator keeping it unchanged; there is no atomic/privileged-writer-proof snapshot fence across separate captures. Any suspected intervening write or state change stops comparison rather than silently adopting a new baseline.

## Budgets and operator handling

Query timeout600seconds; verify actual SSMS value before execution. Operator total cancellation610seconds. Per-chunk cooperative15seconds, operator20seconds from that chunk's progress line. Messages identify every starting chunk. Per-call checks cannot forcibly interrupt a blocked statement; wait for control after cancel, no process/service termination. At most2048chunks,4GiBcanonical bytes,4MiBreport output including formatting. A cap is a STOP, never permission to raise it or label the remaining table complete.

Require prior B03control returned; fresh query window. Execute once, capture all Results and Messages as one report, reset query timeout10seconds after control returns. The expected catalog estimate suggests around2002source reads including exhaustion, but this is NOT a required result count. Exact returned count may differ from approximate metadata and must be reconciled.

Errors/warnings, identity/schema/index/file/state drift, unexpected writer, free-space/time/row/byte/output limit or incomplete report stop. On catchable error retain partial manifest and last completed key; client cancellation can bypass CATCH and lose unreturned rows. No blind resume, no completed-range replay, no table/temporary-file manual cleanup. Next step requires exact evidence review. SQL recovery/files/media and existing tables remain retained.

## Remaining boundary / validation

Successful B04would complete this versioned raw-table content baseline only when pilot+all chunk receipts+empty probe reconcile. The other11unfinished KVKtables need their own suitable strategy (unkeyed Stage is not silently assigned this keyset algorithm). Other352tables stay outside content scope, and3ProcConfig fingerprints stay retained. No installation/prerequisite reruns, provider calls, production deployment, rollout or G5 follows. Seven typed G4proofs remain open.

Local static check confirms one exact source table, strict key predicate, finite2048loop,1024materialization, temp-only hashing, temp-only deletes, empty-read completion gate and no RESTORE/BACKUP/ALTER/DROP/UPDATE/EXEC/KILL. Five reference tests cover exact suffix/no-overlap coverage, chunk-cap refusal, empty tail, scan-boundary crossing and KVK-boundary crossing. SQL not live-compiled/executed; full-table throughput and plan behavior not established by the121ms pilot.

Preparation-only security-routing skip for generated operator-review artifacts; no deployed runtime/config/permission change, no PR handoff. No predecessor test runs or memory-cause investigation; withdrawn collector untouched. Source and prior sealed receipts unchanged.
