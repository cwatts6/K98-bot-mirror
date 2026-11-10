# D02 receipt — development directory ACL and capacity metadata

Operator-supplied D02 completed on 9SX2VF4: all six expected directory boundaries returned, no failure, reported elapsed 129 ms. Started 2026-09-28T11:08:44.7045627Z; finished 11:08:44.8315549Z. Within the approved maintenance window ending 2026-09-29T09:23:23Z. No repeat capture is required for these facts.

The supplied JSON is retained as a normalized transcription at `.codex_artifacts/s11-g4-capture-preparation-20260926/received-D02-20260928T110859Z.json`. This is not an independently acquired host observation or a byte-identical attachment. Its receipt seal binds the retained transcription and this reconciliation. Approved command SHA256: `d834141d5e3483bdca907601158ed41d07d6366e4a16c40f177a61c7c5452072`.

## Established observations

The six exact boundaries are C:\, C:\Program Files, C:\Program Files\Microsoft SQL Server, its MSSQL16.K98DEV child, that child's MSSQL directory, and MSSQL\DATA. All returned Directory attributes; none reported ReparsePoint. Owners and complete SDDL strings are retained in the receipt. This point-in-time metadata does not establish absence of path races or future ACL changes.

C:\ is reported Fixed / NTFS. Total capacity is 1,997,699,805,184 bytes; total free and available-to-observer capacity are both 1,747,644,268,544 bytes (about 1.75 TB decimal). This is free space at observation, not a reservation, an allocation test or a restore-size estimate. The source candidate's 2,815,180,800 bytes of backup files cannot substitute for expanded data/log file sizes and growth budgets.

MSSQL\DATA has a protected DACL containing full-access entries for SYSTEM, Administrators and SID S-1-5-80-2931557206-644353831-496829890-75705068-2459599927, plus an inherit-only Creator Owner entry. The enclosing MSSQL directory grants that SID read/execute. No service-account mapping, token inspection or effective-access test was performed; do not infer that the current SQL service can create proposed files from these strings alone. Ancestor permissions are preserved without an overall security-acceptance claim.

## Remaining preparation

The D01R1 exclusions remain authoritative retained exclusions: all 21 existing databases and all 49 catalog file paths are protected. D02 does not authorize reuse of any existing database/file or creation in the sampled directory.

The next grouped packet must specify distinct candidate database and file targets, compare them against those exclusions, and bound any remaining collision/service-identity observations. Source-media header and logical-file layout evidence, expanded size/growth budgets, and protection from the known source prune operation remain outstanding before an exact restore decision. No media read, copy, mkdir, ACL change, provisioning or restore follows from this receipt.

All seven typed G4 proofs and actual restore remain incomplete. S11 rollout and G5 remain unapproved. Preserve the isolated production hotfix, single-account/admin-owned model, deferred memory investigation, withdrawn collector and separate KVK/view-rehydration issues. Scheduling within the recorded window does not need reconfirmation; new operation scope remains separately bounded.

Validation: local JSON structure/count/path/attribute/capacity checks; proposal and approval seal checks; preservation check of the original 27 pending files and 394 evidence files. No live calls or runtime changes. Runtime tests and security discovery are inapplicable to this receipt-only addition.
