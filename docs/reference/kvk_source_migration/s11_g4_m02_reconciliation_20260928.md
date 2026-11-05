# M02 staged-media reconciliation — 2026-09-28

All supplied media evidence matches: 119 headers, 238 file rows, 357 total JSON records. The first attachment is the query text, byte-identical to sealed M02.sql (36,645 bytes); it is not the first identity result. The second attachment contains all 357 complete JSON rows (148,731 bytes). Both originals are preserved byte-for-byte, with the supplied completion row separately transcribed, under `.codex_artifacts/s11-g4-capture-preparation-20260926`:

- `received-M02-query-20260928T142935Z.sql`
- `received-M02-evidence-20260928T142935Z.txt`
- `received-M02-completion-20260928T142935Z.json`
- `m02-local-analysis-20260928.json`

Completion reports 2026-09-28T14:28:56.0300406Z, M02 staged media metadata completed, 119 checked sets, 357 evidence rows, elapsed 1,318 ms. Within the query's batch budget and maintenance window. The timing covers M02's internal stopwatch, not independently measured total client execution. Receipt recorded 14:29:35Z. Re-serialized compact JSON UTF-16 payload is 296,008 bytes, below the 512 KiB budget.

## Independently reconciled returned fields

Every header's set ID/order, BackupSetGUID, type, first/last LSN, recovery fork and checksum flag matches the retained manifest. All identity_status values are matched. The first log covers the full-backup end; all 117 following adjacent log boundaries are exactly contiguous. Tail LSN remains 19088000155032800001. Full checksum flag is true, all 118 log checksum flags false; those are backup metadata flags, not a newly performed integrity scan.

Every set returns the same two file records, including file ID, logical name, physical source path, type, Size, MaxSize, UniqueID, creation/drop LSN, IsPresent and IsReadOnly. Data is 18,239,979,520 bytes; log is 68,719,476,736 bytes. Combined expanded allocation remains **86,959,456,256 bytes**. No file additions, path/GUID changes or recorded size growth appear across this candidate chain. Both files are present, not read-only, with zero creation/drop LSN fields. Original source physical paths are not destination targets.

This supports the proposed two MOVE mappings and initial capacity arithmetic. Header fields checked only inside the guarded SQL, such as BindingID/family/encryption flags, are evidenced by the matched result and submitted unchanged query, not separately emitted raw values. Do not fabricate extra result columns or an execution trace.

## Small receipt gaps — no rerun

The actual first identity result (observed_utc/server/database/login/machine/instance/version/sysadmin), Messages output and confirmation that the query timeout returned to ten seconds were not supplied. The submitted query text does not substitute for the observed identity row. Request only those already-visible results/settings confirmation; do not rerun M02 or any media read to obtain them. Successful completion is consistent with the accepted query guards, but the missing displayed result remains explicitly unrecorded until supplied.

## Proof boundary and next preparation

Staged metadata can be read according to the operator-supplied successful batch. ST04 previously matched all staged bytes to ST01R1. Neither result verifies every backup page/checksum or proves an actual restore, SQL service create/write rights, immutable media, allocated growth headroom or final recovered-data correctness. No VERIFYONLY or restore has occurred in this operation.

The next exact packet can now use the confirmed 119-set metadata chain and unchanged two-file layout to specify media verification and actual-restore guards/budgets, retaining checksum-free log limitations. Final recovery and post-restore acceptance remain explicit decisions, not implied by this receipt. Do not execute the unconditional-THROW restore draft, create data files/database, remove temporary objects or clean up media.

All seven G4 typed proofs and actual restore remain incomplete; rollout/G5 unapproved. Preserve source/staged copies, ST03 denial/manual-route history, LG01 provenance gap and all original evidence. Memory investigation deferred, historical collector withdrawn, KVK/view issues separate.

Validation: local JSON parsing/counts, exact manifest UUID/LSN/type/fork comparisons, complete per-set layout equality, storage arithmetic, query-byte equality, proposal/approval seals and original 27 pending/394 evidence preservation. No live SQL or filesystem-media call by assistant; receipt-only addition requires no runtime tests or broader discovery.
