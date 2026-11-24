# P02 D5b disposable copy packet — 2026-11-11

Status: **prepared and reviewed; operator execution pending**. The user already
authorized this one disposable copy and the qualification disk. No additional
permission is requested. D5b is not complete.

## Exact operation

`scripts/copy_p02_d5b_database.ps1`, SHA-256
`13af2b2015ee53330ab6dcda7ae0d35dc82ee911bbe2051356c533c661f30f80`, uses the same
elevated PS5.1 host and authenticated session. It binds the verified attachment
and format receipts, exact VHD/device/volume, VM isolation and resource settings.

Source remains `MINI_AMD` / `K98_P021_PreImport_20261107`, database ID 7,
creation time `2026-11-07 11:21:28.607`, READ_ONLY/RESTRICTED_USER, with the exact
original C: data/log files, owner/settings/collation and 80.9873 GiB allocation.
The sole target is the currently absent `K98_P025_D5b_20261111`.

Create the new, previously absent `Q:\D5b-20261111` directory with an exclusive
owner marker and these exact paths:

- `source-copyonly.bak`
- `K98_P025_D5b_20261111.mdf`
- `K98_P025_D5b_20261111_log.ldf`

The one-attempt sequence is:

1. Verify identity, current sysadmin/observer capability, target/directory
   absence, Q: capacity and original read-only state. No permission fallback.
2. Back up the original using COPY_ONLY and CHECKSUM. Retain the backup.
3. VERIFYONLY with CHECKSUM and the same two explicit MOVE destinations used
   for restore. Verify a single full copy-only/checksummed/non-damaged header
   and the exact two logical file identities/sizes in FILELISTONLY.
4. Recheck target/file absence; restore the one new database into those Q: files,
   without REPLACE. No source file is a destination.
5. Make only the disposable copy READ_WRITE/MULTI_USER; cap its data file at
   32 GiB with 64 MiB growth and log at 80 GiB with 512 MiB growth. Preserve
   snapshot ON/RCSI OFF and other required identity/settings.
6. Compare original metadata before/after, verify copy state/file caps/resources,
   dispose the owned SQL connection and verify exact session-id/login-time
   disappearance. Return a new receipt for adjudication before installation.

COPY_ONLY preserves the normal backup sequence/differential base. VERIFYONLY
checks readability and checksums; it does not establish application/report
correctness. Microsoft documents [copy-only behavior](https://learn.microsoft.com/en-us/sql/t-sql/statements/backup-transact-sql?view=sql-server-ver16)
and [VERIFYONLY with the restore MOVE map](https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/restore-a-database-to-a-new-location-sql-server?view=sql-server-ver16).
Normal SQL backup-history metadata may be recorded; no business/deployment
receipt is fabricated. No production backup job is dispatched.

## Bounds and failure handling

This native copy setup has a **900-second overall ceiling**, work statements at
most 300 seconds, three-second metadata statements/zero lock wait, five-second
connections, 48 SQL commands, 512 maximum rows per command, 2,048 total rows and
1 MiB receipts. The owned host watchdog waits 880 seconds plus at most ten for
stop acknowledgement. Guest work stops admitting steps after 800 seconds.

Host free disk must cover the full 256 GiB VHD maximum plus 8 GiB reserve;
guest C: and Q: retain 8 GiB each. Q: initially needs the 226 GiB planned peak
envelope. Storage is checked before and during asynchronous work. Backup bytes
are capped at 90 GiB; data/log at 32/80 GiB. Version store must remain below
512 MiB at the stage gates. No optional statistics run in this packet.
Backup/restore use eight 1 MiB transfer buffers; no memory/CPU increase occurs.

The original rehearsal statement ceiling is 1,800 seconds. This stage uses
tighter limits and also records a conservative remaining D5b native-execution
allowance of 1,800 minus the 8.8684387 seconds already spent on storage and this
copy's elapsed time, for subsequent packets. Offline preparation/user handoffs
are not benchmark intervals. No Bot timeout or D5e timing rule is changed.

Any error, timeout, existing destination or ambiguous outcome stops progression.
Retain files, database, receipts and the borrowed session. There is no retry,
overwrite, DROP, DELETE, forced rollback or cleanup of the new database/files.
Unsettled SQL cancellation retains its exact task/command/connection owner in
the guest session and reports closure unverified; the host retains an unknown
worker owner if it cannot acknowledge cancellation. Do not infer rollback or
successful restore from a released connection.

Original database/evidence, permissions and the consumed 21-input allowance are
preserved. No input import/replay, candidate installation, report recomputation
or maintenance child runs in this copy stage.

## Validation

Windows PowerShell 5.1 inert tests passed:
`tests/validate_p02_d5b_copy.ps1`, SHA-256
`052917aafbf63648e921e17704d57d8227926e95c4c480badb3585ef1ffe7d56`.
Metadata limits/disposal, exact source/file refusals and completed async task
cleanup were exercised without invoking the operational script.

Supplemental ignored `d5b-copy-async-validation.ps1` extracts the exact pinned
Execute-Step and guest finally block. Actual PS5.1 passed faulted-task handling,
pending cancellation with retained exact ownership/unverified closure, and a
finite delayed-task join/disposal in 6.05 seconds. No native operations occurred.

Changes review `820d44d9-c283-4cc1-88af-0556f3138403` completed with zero reportable
findings, Deep off; independent source review found no blocker. Snapshot digest:
`1bc9bc3d369870fa8ca2f97c360fb1ccee377c539cf74b88f32793ec49a46d8a`.
Findings SHA-256 `c7cbbeb816baa6b4fa38fbb84e9b1b6cc87d44f199b0e32530f81500e50646db`;
coverage SHA-256 `aa7204094d6b43d12afdbac9626c50fbdc736b413a940a1ee0f1aad90094add9`.
Existing source hashes and evidence remain unchanged. Routing/whitespace checks
passed. Test selection ran; broad Python/native fixtures are skipped for this
operator-only PowerShell addition, and the Python architecture checker is not
applicable. New SQL references are standard server catalogs/backup operations;
no business schema is inferred or changed. Candidate installation still needs
the authoritative SQL repository's complete structural pre/postimage checks.
