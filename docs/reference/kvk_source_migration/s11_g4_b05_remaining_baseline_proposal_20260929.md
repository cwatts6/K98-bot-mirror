# B05 remaining scoped table fingerprints — proposed, not executed

## Exact approval target

One manual execution of `C:\discord_file_downloader\.codex_artifacts\s11-g4-capture-preparation-20260926\commands\B05.sql` (232624 bytes), SHA256 `6fa329a2f8f2931d0ac77545efefb26247bad8c4e10652a432815fde035801de`. SQL text is the exact command; do not paste snippets or change limits. Open in a fresh SSMS query connected through `localhost\K98DEV`, Windows Authentication, database `master`. Expected server `9SX2VF4\K98DEV`, original login `MicrosoftAccount\cwattsconsulting@outlook.com`, sysadmin1, SQL16.0.1200.5. Do not connect to MINI_AMD.

Target only recovered database ID22 `S11_G4_Recovery_20260928_97337`; exact two data/log paths and page sizes are guarded, as in the accepted restore packet. ONLINE, RESTRICTED_USER, read-only1, Broker0 are mandatory. No restore, recovery, installation, permissions, persistent row changes, provider call, deployment or activation.

Existing approved maintenance window ends 2026-09-29T09:23:23Z (10:23:23 BST). **Start before 09:13:13Z (10:13:13 BST)** so the 610-second operator cutoff fits. Script refuses later starts and checks the original expiry between work units. No extension is implied. Approval applies to these bytes/targets for one attempt only.

## Scope and retained results

B04R1 plus B03 already cover 2,049,960 raw rows; three ProcConfig fingerprints were retained from B02. Neither is reread. Eleven remaining tables, all in KVK:

| Table | Object ID | B01 approximate rows | Maximum accepted rows |
|---|---:|---:|---:|
| KVK.KVK_AllPlayers_Stage | 2071535009 | 52668 | 65536 |
| KVK.KVK_Camp_Windowed | 804054496 | 80 | 2048 |
| KVK.KVK_CampMap | 660053983 | 128 | 2048 |
| KVK.KVK_DKPWeights | 612053812 | 4 | 2048 |
| KVK.KVK_Ingest_Diagnostics | 663998488 | 2 | 16 |
| KVK.KVK_Ingest_Negatives | 84051931 | 0 | 2048 |
| KVK.KVK_Kingdom_Windowed | 756054325 | 920 | 2048 |
| KVK.KVK_Player_Baseline | 52051817 | 33100 | 40000 |
| KVK.KVK_Player_Windowed | 708054154 | 272474 | 300000 |
| KVK.KVK_Scan | 2135535237 | 253 | 2048 |
| KVK.KVK_Windows | 532053527 | 36 | 2048 |

The other352 tables remain excluded from content scope. Counts above are approximate planning observations, not expected-result assertions. Exact observed schema descriptors and source paths/hashes are in `b05-scope-manifest-20260929.json`. All11 authoritative source files still match their retained SHA256; column tokens were checked. Installed columns/types/nullability/identity/collation and table identity are guarded by copied B02 predicates, rather than assuming source equals installation.

## Algorithm and effects

For each table, select at most its cap+1 rows, using every explicitly listed column, into a unique owned session temporary table. More than cap refuses acceptance. Fewer than cap+1 establishes that this unchanged read-only table fits the cap; no OFFSET, guessed unique key or deduplication. A new temp identity ordinal is only a processing locator. Existing identity values are copied using same-type CONVERT expressions to avoid inheriting a second identity property. No identity column values are changed.

The two unkeyed tables (Stage and Ingest_Negatives) use this same complete capped materialization. A temporary ordinal index supports disjoint 1024-row ranges. Each range's inserted-hash count must equal its expected range count. Maximum419888 accepted rows across all11 tables, maximum412 hashing iterations. TOP bounds returned/materialized rows, not physical I/O or optimizer work.

Only the materialized temp rows are hashed. Exact B02 native varbinary framing (0xB002, NULL marker, native value byte lengths and values) remains unchanged. Row SHA256 values, including duplicates, are globally sorted into4096-hash chunks and the whole-table SHA256 binds the observed schema digest, exact row count and ordered chunk digests. Thus B05 remains comparable to B02 format, unlike B04-keyset-v1. Temporary processing order does not affect the multiset digest. SQL16.0.1200.5/native representation binding remains; no portable/collision-free claim.

The only unbounded declared column, diagnostics ContextJson, has a TOP17 DATALENGTH-only precheck capped at1MiB/value before copying. The table itself allows16 rows, so overflow stops and cannot produce acceptance. Each encoded row is capped at1MiB; table canonical bytes512MiB, total1GiB. Duplicate rows and NULL values are preserved. Empty table produces an explicit zero-row digest. No business row values or keys are printed.

Tempdb receives raw copies, hashes and compact results. Owned temp copies are dropped after their table; hash/chunk temp rows are cleared between tables. No existing persistent object is modified or dropped. Connection/audit/CPU/I/O/cache and tempdb effects occur. Sampled session/task scratch limit2GiB and C: free floor100GiB are checked; these and byte/time limits are cooperative, not hard memory, physical I/O or tempdb quotas. Client cancellation can bypass CATCH. Never terminate SQL service or delete retained data/media.

## Budgets, evidence and stop conditions

- Set and verify this query's SSMS execution timeout **600 seconds**, not1200. Connection timeout stays10seconds. MAXDOP1, lock timeout1000ms, deadlock priorityLOW.
- Operator cancel at610seconds total, or the maintenance expiry, whichever is earlier. Per-table180seconds cooperative/operator190seconds. Materialization (including ordinal index) and final aggregation30seconds cooperative/operator40seconds from their progress message. Hash chunk15seconds cooperative/operator20seconds. If a phase stops progressing, cancel at its bound; wait for control to return.
- At most256KiB combined rendered Results/Messages. Output: identity, progress table/phase/offset,11 schema/count/byte/chunk/digest/duration rows and final totals/completion, or error metadata. Save **all Results and Messages** together as B05.rpt and return the file. Completion must report11 tables; retain any warning/error too. Reset execution timeout10seconds after control returns.
- Stop for warning/error, timeout, cap, missing output, identity/file/shape/state mismatch, unexpected writer or other data change. Do not retry, increase limits, switch databases, manually clean temp objects or resume automatically. Retain the report and return it for reconciliation.

An individual table result can appear before a later stop check; final full-operation acceptance requires clean completion and evidence reconciliation. Suspected write/state change invalidates comparison even if final read-only status matches. This remains an operator-controlled historical baseline, not an atomic fence across separate captures or evidence of current production rows.

## Local validation and gate limits

23 static/reference checks pass in `b05-local-validation-r1-20260929.json`: exact11 scope, cap+1 refusal/count matching, temp-only row hashing, finite ranges, unchanged row encodings, correct C:\ volume literal, temp-only mutations, completion gate and multiset duplicate/order/empty/boundary invariants. Initial checker counted 'execute' in an approval comment; its result is retained separately, then corrected by stripping comments/literals. No script change followed that checker correction. SQL was not live-compiled or run; actual execution plans/throughput remain unproven.

All27 originally pending files and394 retained evidence files match the before-inventory. B04R1 drift copy and recovered approved copy remain untouched. Preparation-only security-routing skip for this local generated operator-review packet; no deployed code/config/permission change or PR handoff. Pytest/architecture/deferred/PR checks skipped because no application implementation or PR is being prepared; targeted static and reference validation performed instead. No full/deep security scan or predecessor replay.

Successful B05 plus accepted earlier fingerprints would close this15-table historical content baseline only. It does not supply lost original receipts/fences, install missing source implementations, complete all seven typed G4 proofs or authorize rollout/G5.
