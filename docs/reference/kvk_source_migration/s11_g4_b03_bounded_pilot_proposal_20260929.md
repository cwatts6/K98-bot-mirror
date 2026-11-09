# B03 — bounded first-key-range pilot

PROPOSED, NOT EXECUTED. User's timeout correction is retained separately: B02 was configured1200seconds rather than approved900, explaining the20-minute client timeout. This does not identify why the large step was slow or waive the earlier table cutoff. Preserve original timeout evidence and the3completed ProcConfig digests. No unchanged B02 replay, global timeout increase, or repeat of those completed tables.

## Exact operation

One B03.sql execution, after exact approval, on development localhost\K98DEV in a fresh master query window with existing Windows Authentication. Operator/reviewer/abort owner Chris Watts. Existing window expires2026-09-29T09:23:23Z. Do not start while the prior B02 execution/cancellation still has not returned control; do not terminate server/process or manually clean its temporary state.

File: C:\discord_file_downloader\.codex_artifacts\s11-g4-capture-preparation-20260926\commands\B03.sql

SHA256: 1cbdb08c60b461008621bf4c88647120eca5157ea2f875f6eb6e98a2fca00123

Same guarded identity, exact SQL16.0.1200.5, databaseID22 S11_G4_Recovery_20260928_97337, exact2files/sizes, ONLINE/RESTRICTED_USER/read-only/Broker0, clear transaction state and100GiB start free space. Exact raw table objectID2087535066 and all51observed column shapes are checked. Source PK and B01 agree on enabled unfiltered unique clustered PK_KVK_AllPlayers_Raw, index1, ascending columnIDs1,2,3: KVK_NO, ScanID, governor_id. Index shape is checked before reading.

1. SELECT TOP(1024) the51literal columns, ordered by that primary key and using the named clustered index, INTO owned session #B03Sample, MAXDOP1. The source query has no hashing or global hash sort. This limits materialized source rows; engine page reads/locks are not a hard quota. All51columns have bounded declared lengths; no max-length column in this pilot.
2. Hash only #B03Sample using the same B02 row framing, max-promoted binary concatenation and SHA2_256. No return to the source table for more rows. At most1024accepted rows,1MiB framed bytes per row and8MiB combined framed bytes. Per-row NULL hash/oversize refuses acceptance.
3. Sort only those <=1024row hashes and return a pilot SHA256 over their uppercase64-character hex encodings. Return first/last key tuples (KVK_NO, ScanID, governor_id), count/encoded bytes/schema digest and separate materialize/hash/aggregate timing. No other raw business row values returned. These key identifiers are new explicit output scope. Pilot digest is a chunk-style digest, NOT B02's full table digest and not interchangeable with it.

No loop, offset pagination, follow-on chunk, whole-table count or full scan requested. No remote production operation, provider/Discord call, new database, persistent write, backup/restore, migration or install. Actual source row copies exist transiently in tempdb, unlike B02's hash-only scratch: this is disclosed and limited to1024rows. Keep the existing SQL/admin access model; no permissions changes or scratch export.

## Limits and evidence

SSMS query timeout60seconds, cooperative60seconds, operator cancel70seconds; verify the query's actual timeout is60before execution. One attempt. Maximum output16KiB. Return all Results/Messages and client completion; require identity, both key bounds (unless table empty), pilot count/digest/stage timings and overall completion. New errors, warnings, target/schema/index/state drift, byte/time/output limit or incomplete receipt stop; no retry, continuation or raised timeout. Wait for control after cancellation; reset timeout10seconds afterward. No claimed hard I/O/memory or instantaneous cancellation bound.

Success informs a later explicitly approved keyset-chunk design. It does not establish full-table completeness, identify the earlier20-minute bottleneck with certainty, or justify extrapolating unlimited throughput. Later chunking must prove strictly increasing key bounds, no gaps/overlap, duplicate handling where keys are absent, and a final exhaustion check. Different digest schemes need versioned manifests and cannot be mixed silently. Large unkeyed Stage and other unfinished tables need separate handling. All12unfinished B02tables and352out-of-scope tables remain unaccepted; seven typed G4 proofs and G5 stay open.

## Local validation

Read authoritative KVK.KVK_AllPlayers_Raw.Table.sql and retained B01column/index metadata. Reused exact B02row encoding expression but replaced its source with the bounded materialized temp table. Static check: one source TOP1024 materialization, one temp-only hash query, MAXDOP1, no loop/restoration/update/delete/alter/drop/exec. SQL has not been compiled or run; no performance claim. An initial local generator typo failed before writing files; corrected locally, no live effect.

Preparation-only security-routing skip retained for generated exact operator-review artifacts; no deployed code/config/permission changes, no PR handoff/runtime tests. No source or historical sealed artifact overwritten. This SQL pilot is separate from the deferred production memory investigation; the withdrawn collector is untouched.
