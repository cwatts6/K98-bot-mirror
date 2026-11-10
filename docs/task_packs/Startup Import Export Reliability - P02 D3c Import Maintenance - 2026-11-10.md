# P02 D3c: import maintenance and managed reader exclusion
- Extract only KS5 sampled stats and conditional KS4 index/stats upkeep from UPDATE_ALL2. Preserve required Refresh_PlayerScanMeta, typed/history data, file/digest/scan allocation, receipts and archive, byte-for-byte outside the two upkeep blocks and transactional due statement.
- Keep six fixed maintenance kinds. Add import-specific KS4 due/completed generations, coalesced with import generations; only a promotion requests KS4 upkeep. A captured generation cannot acknowledge a later request. No per-import queue.
- Add fixed import child with existing four-index whitelist and unchanged <10/<30 thresholds, SAMPLE20/SAMPLE25; no added nightly rebuild or widened MAXDOP policy.
- One dedicated maintenance-schema guard: managed SNAPSHOT readers take Shared/Transaction; actual maintenance worker takes Exclusive/Session before claim. Producer admission remains independent; all maintenance including sp_updatestats respects it. Reader rollback releases its transaction guard; uncertain rollback retains open custody. Maintenance release is explicitly acknowledged before pooled return.
- Reuse existing worker, transaction due record and explicit post-import route, process both import and post_import before finite receipt. No new scheduler or forced work.
- Bot changes belong in core observation helper and maintenance DAL only; SQL remains authoritative in SQL repository. No Discord UI or command changes.
- Separate Changes reviews Bot/SQL, Deep off. Targeted regression, native actual fragmented index/raw-history reader overlap both orders, rollback/cancel/pool cleanup, generation/conditional scope and byte-preserved business sections; exact updater transition/history and SQL historical source checks. Existing failure evidence retained.
- Native surrogate qualifies controlled managed readers only; D4 installed/manual/legacy census and permissions, D5 scale/cost remain open. RCSI off; no timeout/headroom/backup-policy change. No further approval required under current all-D3 instruction.

Qualification checkpoint (10 November 2026):

- D3a mirror PR 513 and D3b mirror PR 514 are merged; D3b SQL companion PR 142 is merged. D3c starts at Bot f910fa83 and SQL 8ba5850.
- Five native import cases execute the extracted sampled statistics and actual fragmented-index rebuild. Both managed raw-history reader arrival orders pass; a reader leaves producer admission available, and a later due generation remains pending after the first claim completes. Twenty-eight combined native maintenance and existing snapshot cases passed. The broader focused selection passed 63 cases; all nine caller expectations were updated to permit only the exact Shared/Transaction maintenance guard while continuing to reject producer/row locks (41 passed).
- SQL business-preservation test compares all retained UPDATE_ALL2 bytes to the immutable predecessor after removing only the two maintenance blocks and the new transactional due statement. Refresh_PlayerScanMeta and IMPORT_STAGING_PROC_CORE remain required and unchanged. Child maintenance statements, samples, index whitelist and thresholds are preserved. Archive, typed data, allocation, receipts and report arguments are untouched.
- The exact updater family has seven members, two changed, with 84 entries. All 83 predecessors retain digest df7b4614082c0688afccaf3a425f43f52a9fc2d1e17dd112fa4fb8b389fe94a7. Registry byte bound and combined-jump refusal remain unchanged. 178 focused updater cases passed.
- Native fixture preparation exposed insufficient log headroom when reusing a small disposable database. Tests now create a separately owned database per import case, retain the unchanged <70% gate, and close setup failures safely. The exact leaked failed fixture was removed only after checking it had no connected sessions; no forced disconnection or retained database mutation occurred. This is fixture qualification, not a production-scale cost result.
- Historical source checks authenticate the exact D3 candidates before testing immutable pre-D3 contracts. Runtime installed-source admission remains unchanged and intentionally refuses this coordinated release until D4. No production SQL, provider, restart, deployment or retained recovery occurred.

Status: implementation, targeted qualification and review complete. D3d-g and D4/D5 remain open. Unmanaged raw-history SNAPSHOT readers are not qualified by the managed helper tests; D4 must reconcile manual and legacy consumers before installation. D5 must measure the deferred maintenance cost against existing budgets.

Final review and qualification:

The broad regression selection passed 2,064 cases, with 28 opt-in/platform skips,
12,285 deselected and one existing Google Python-version warning (370.78 seconds).
The final default-pooling check passed both success/failure cases with all three
session guards available before child process exit. Architecture, deferred,
selector, security-routing, pre-commit and both SQL CI runs passed. Repeating the
full repository suite for this bounded slice was not required after the D3b full
pass and the affected caller/native/updater selection; D5 combined qualification
remains mandatory.

Bot Changes scan 436d1ab6-d2ad-44db-a541-9f116cfb21d7 covered all 44 changed paths;
SQL Changes scan 97a2fbe6-c6e9-4345-89d1-1dcc9959f658 covered all 16. Both completed
with zero findings, and GitHub code reviews at f2fa758e and 4b6961b reported no
findings or open threads. Each scan reports the same overlapping rollout usage:
1,913,398 tokens (1,908,933 input, 1,890,816 cached input, 4,465 output); do not add
these as independent costs. The immutable SQL encoding baseline intentionally
retains historical whitespace; new executable SQL passes whitespace checks.

SQL PR 143 merged at faddbd12. Bot mirror PR 515 is ready for the authorized merge.
D3c qualifies managed reader exclusion and source separation, not installed/manual
compatibility or production-scale cost. D3d-g, D4 and D5 remain open.
