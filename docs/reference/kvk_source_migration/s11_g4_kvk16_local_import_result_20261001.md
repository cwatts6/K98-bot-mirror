# KVK16 local imports and scan remapping completed

The user-approved three-file import and post-import test-window mapping completed on `localhost\K98DEV`, canonical server `9SX2VF4\K98DEV`, new `ROK_TRACKER` database **24**. An independent readback verified the accepted revisions, original file hashes, row counts, two configuration versions, disabled source routing and DB22 protection. This is a direct DAL development exercise, not a Discord command, full runtime installation, provider export or G4/G5 acceptance.

## Actual inputs and assigned IDs

| Role | Original retained file | Rows | Returned logical ScanID |
|---|---|---:|---:|
| Baseline | `C:\Users\cwatt\Downloads\KVK_16_Baseline.xlsx` | 5,806 | 1 |
| Pass 4 start | `C:\Users\cwatt\Downloads\1198_auto_pass_lvl4_before_2026-09-05_1526.xlsx` | 5,729 | 2 |
| Pass 4 end | `C:\Users\cwatt\Downloads\1198_end_of_zone_5_2026-09-07_0721.xlsx` | 5,720 | 3 |

The complete previously accepted file SHA256 values are retained in `accepted-retained_b0.json`, `accepted-start.json`, `accepted-end.json` and the independent SQL readback. All 17,255 player snapshot rows are present. Formula cells remain unavailable according to the unchanged parser contract; no workbook was resaved or normalized.

The new importer uses `KVK.SourceLogicalScan` and versioned `KVK.SourceWindowConfig`, not the legacy `KVK.KVK_Scan` numbering. The configuration was created from the actual returned acceptance IDs:

- Baseline **1→1**, config `8f115be0-2fd0-431e-b1ac-e43b59b0f7c5`, period `b36a7d5f-f497-4172-82d3-44cec384c23c` (`fight:baseline`, equal endpoints).
- Pass 4 **2→3**, config `ee295e19-7d26-4e8b-abc7-6ae5c52fe01c`, period `73797117-b108-4e5a-9c6e-889226c028fb` (`fight:pass_4`).

Both configurations retain the original B0 cohort of 5,806 governors, weights **10/20/40** and all 36 kingdom/camp mappings extracted from DB22. No other windows were configured. The historical 15→24 window and original backup rows remain untouched. The observation times use the retained file contract (2026-08-26 04:07Z, 2026-09-05 15:26Z, 2026-09-07 07:21Z) as explicitly labelled development-test metadata, not a newly observed production intake timestamp.

## New target and installation scope

Creation used dedicated previously absent files:

- Data: `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11G4_ROK_TRACKER_20261001.mdf`, 512 MiB fixed.
- Log: same directory, `S11G4_ROK_TRACKER_20261001_log.ldf`, initially 256 MiB fixed, subsequently expanded to **1,024 MiB fixed** as described below.

Final reserved maximum is 1,536 MiB with growth disabled. SIMPLE recovery, compatibility 160, Broker disabled, TRUSTWORTHY off and database chaining off. No shared signing certificate, login, grant, proxy or server feature was created/enabled. The existing local per-connection encrypted TrustServerCertificate exception was retained.

Installed only the KVK scan prerequisite and source observation/publication/season foundations needed for these DAL operations: reviewed bootstrap, 20260909_001, 20260910_001 and a new-target zero-choice preview/apply of 20260912_001. The preview returned `preview_rolled_back`; apply then completed. This was required installation on the new empty database, not a replay against DB22/DB23 or a waiver of their existing S6/S8 gates. No 540-object blanket installation or full legacy signing installation occurred.

The development DAL chose `snapshot_report_v1` for KVK16 and used clearly labelled local test admission identities (`local-dev-test`, `local-no-discord`), not fabricated Discord invocations. B0/config onboarding moved the local season lifecycle from planned to open while **SourceRouting.Enabled remained 0**. No publications were created; no export destination was registered or written. The open local data lifecycle is not Bot activation or serving permission.

Originals were copied by the existing ArtifactStore to `C:\K98-S11-Validation\kvk16-import-20261001-originals`, outside Git beneath the existing protected development root. Their bytes/hashes are retained; the old production credential path was not recreated. No key content was read. The import verified all 549 workspace source members against the existing source plan before application imports.

## Resolved failure and recovery

Baseline and start committed successfully. The end-file transaction encountered SQL error 9002: the fixed 256 MiB transaction log was full due to ACTIVE_TRANSACTION. The DAL explicitly acknowledged rollback. The first attempt and stack trace remain preserved, with a nonzero child exit; it is not described as an uninterrupted pass.

A separate guarded operation reconciled two logical scans, exactly 11,535 committed player rows, the two exact accepted revision/hash pairs, zero configs and no end-file revision. Only then did it CHECKPOINT DB24 and expand its exact log file to 1 GiB with growth still disabled. No other database/file was altered. The continuation skipped the two successful admissions, reverified original bytes/semantic digests, accepted only the end file and then created the two configurations. It completed in 25.641 seconds with child exit 0 and no timeout. No blind import retry or cleanup was used.

Independent final readback returned 10 rows / 3,045 JSONL bytes in 0.1723563 seconds and confirmed:

- Scan 1 / revision `abca60a7-1642-43f3-8d7e-2f900edbdfd3`: 5,806 rows and exact baseline hash.
- Scan 2 / revision `c66cb76a-cfd1-42bf-bcbb-70a95948455d`: 5,729 rows and exact start hash.
- Scan 3 / revision `2638ce0f-120f-4bec-8e54-6d79707ad30a`: 5,720 rows and exact end hash.
- B0 membership 5,806; two windows; 36 mappings per config; weights 10/20/40; zero publications; source routing disabled.
- DB22 remains ONLINE / RESTRICTED_USER / read-only / Broker-disabled / TRUSTWORTHY off / chaining off. No restore or baseline rerun.

## Commands, bounds and retained evidence

Packet roots under `.codex_artifacts`:

1. `s11-kvk16-import-20261001`: preparation source, CREATE/BASE/S8A preview/apply working and sealed scripts, fresh operation bindings, SQL receipts, import scripts, accepted IDs, failure/continuation logs and result.
2. `s11-kvk16-log-repair-20261001`: exact reconciliation and guarded file expansion.
3. `s11-kvk16-final-readback-20261001`: independent readback.

SQL stages use the retained pinned runner/launcher and exact server/original-login guards. Every stage's manifest and SQL SHA256 are in its preparation seal. Each operation uses a fresh bounded approval reference to the user's current local completion instruction, not an old maintenance window. CREATE manifest SHA256 `598667580e3d6abd3f13ae180a426c585d565055d7775120fd258c7b28e1b902`; log repair SQL `3d30caef530730005f6c34ec1b0b28f375b5e3231abc030d5265737acb98ed7c`; final verification SQL `0cfa70636e44ffc1f078ceea8707fea522c43562fe58421953f5fbf98244e411`.

Python import command: protected interpreter `C:\K98-S11-Validation\python-env\Scripts\python.exe -I -B` followed by the sealed script path. First script SHA256 `76aaf8a63908bbc4f76a37430f4bf58e417333d0906b09cebd8d9737bf85786d`; continuation `67ad68c1eca93f087b200a5aeb64d01fb06b78708dd1815cad13bda98c9655ed`. First launcher was an inline PowerShell tool command whose exit/stdout/stderr receipts are retained; unlike the continuation launcher, it was not separately saved as a script before dispatch. Preserve that command-copy qualification. Do not retroactively label a reconstructed launcher as the executed file.

SQL stage limits: 5-second connect timeout, no automatic retry/pooling, 1-second lock timeout; batch timeout 30 seconds (60 for creation), 120-second stage wall bound plus the retained launcher allowance; 500 rows / 256 KiB evidence maximum. Log repair uses 30-second query / 60-second runner wall / 40-row / 64-KiB limits. Final readback uses 10-second query / 30-second runner wall / 40-row / 64-KiB limits.

Import controls: exact server/database ID 24/login check on every injected connection, 5-second connect and 15-second command timeouts, connection pooling/retry disabled, 270-second cooperative script deadline and 300-second external process timeout. Source application locks retain their source-defined 10-second bound, separate from SQL lock timeout. At most 30,000 SQL calls per attempt. Actual first-attempt calls 12,760; continuation 11,672. The three expected source row counts and hashes are checked before intake; existing store/state refuses the initial script. Continuation is specific to the reconciled two-import state. Per-journal-entry bound 32 KiB; the existing launch capture has no hard combined stream/memory cap. No global host-memory or disk quota is claimed. Input originals total 4,617,754 bytes; SQL fixed storage caps are recorded above.

Stops include source/input drift, unexpected target/state, count mismatch, SQL failure, quota or timeout. Each commit is acknowledged separately. Unknown commit is not replayed; new-target partial state and all receipts remain retained. No drop/restore rollback is supplied. The final seal binds both successes and failures, source commands, document and exact retained private originals; no receipt is overwritten.

## Acceptance boundary

This completes the requested **local three-file import and test ScanID remapping**. It does not yet calculate/publish a report or demonstrate Google Sheets fixed-file reuse. The full application schema/permission gate, seven typed G4 proofs, actual two-export demonstration, production rollout and G5 remain separate. Existing/historical Sheets, both uncertain publications, S6/S8, DB23, DB22 and all 119 media files remain preserved. No Git publication, production change, Bot launch/restart or provider request occurred.

No Bot/SQL runtime source was changed. This exercised existing parser/DAL/onboarding code against a minimal new installation, using a privileged local validation connection; it is not restricted-principal permission acceptance. Preparation performed source review and syntax checks; no new canonical security Changes scan was completed for these artifact-only operational commands. This review limitation remains explicit. Prior source test and security-review evidence stays bound to its earlier snapshots. No predecessor-wide tests were rerun merely to label these imports complete.
