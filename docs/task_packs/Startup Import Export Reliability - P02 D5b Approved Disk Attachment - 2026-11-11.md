# P02 D5b approved qualification disk — 2026-11-11

Status: **storage exception approved; attachment packet ready for operator execution**.
D5b remains incomplete. No disk was created by preparation or offline validation.

## Authorization and bounds

The operator answered **“Approve the qualification disk and continue D5b”** to
the specific request for one new 256 GiB dynamically expanding VHDX at:

`C:\discord_file_downloader\.codex_artifacts\p025\d5b-native\D5b-Qualification-20261111.vhdx`

This supersedes only the no-storage-increase restriction in the earlier native
packet. Initialization/formatting of the verified new blank disk and use of Q:
if unused are authorized; no further approval is needed for that bounded scope.
Original disks/database/evidence, RAM, CPUs, isolation, SQL permissions, reserves,
time limits and the consumed 21-input allowance remain unchanged. No shrinking,
deleting retained data, new inputs or import replay. The existing VM must remain
running; no shutdown/restart or controller creation is included.

The verified capacity receipt remains unchanged at SHA-256
`30c4c9a7001906e6dbaf4d647b6cca721763e2bea2e0f007055cb99cb8451f48`.
Its 80.9873 GiB source allocation cannot fit on C: above the 8 GiB reserve.
The new disk does not waive C:/tempdb, log/version-store or rehearsal gates.

## First executable stage: attach and observe

Script: `scripts/attach_p02_d5b_disk.ps1`, SHA-256
`8d3f2c2719811bf9fd59434241c65064db4f7e382f8523bf3ff9331cb0ec4587`.
Inert tests: `tests/validate_p02_d5b_disk.ps1`, SHA-256
`4e69ea86f1437dfbbda2be78dcb093e3c725524e8c35ea9c49158c202600dd53`.

The operator must run the script once from the existing elevated Windows
PowerShell 5.1 console holding the authenticated session. The agent cannot
borrow that session from another process. This handoff requests execution and
the resulting receipt, not another authorization.

1. Verify host 9SX2VF4, PS5.1 Desktop/elevation, exact VM and borrowed session,
   Running/four CPUs/fixed 8 GiB/zero NICs. Require host free disk at least the
   full 256 GiB maximum plus the unchanged 8 GiB reserve. Preserve the original
   pre-start memory gate; do not invent a new post-start free-memory floor.
2. Read existing hard-disk/DVD SCSI slots and guest disk/partition/volume
   identities. Require Q: unused, C: reserve intact, no Python producer and
   bounded inventory. Select only an empty slot on an existing SCSI controller.
3. Write a unique exclusive intent receipt. Refuse an existing VHD path or
   reparse ancestor. Create exactly one dynamic 256 GiB VHDX, record its host
   identifier in a separate exclusive created receipt, then attach that file
   to the pinned slot and write an attached receipt.
4. Recheck all prior host attachments and guest disks/partitions, the exact
   new VHD and VM constraints. Record the single new blank guest disk's
   UniqueId/serial/path/location for adjudication. Do not initialize, partition,
   format, bring online, delete or detach any disk in this first stage.

The outer deadline is 260 seconds plus at most ten seconds waiting for worker
stop acknowledgement, within the five-minute envelope. Guest observations have
30-second waits. Each receipt is at most 1 MiB, uniquely named with a run ID;
unknown worker ownership is retained in the console. There is no automatic
retry or destructive cleanup. If guest enumeration lags after successful
attachment, preserve the incomplete result and inspect it; do not rerun.

## Adjudication and next stages

Verify the returned receipt hash, stage history, resource gates, exactly one new
attachment, unchanged original disks/partitions, and host-to-guest device
identity before preparing the format invocation. Disk number or size alone is
insufficient. Microsoft documents the host disk identifier as the SCSI VPD page
0x83 identity, and guest MSFT_Disk.UniqueId as information from that same page.
The actual receipt must establish the correspondence; do not assume display
format or byte ordering. See [VHD identifier documentation](https://learn.microsoft.com/en-us/powershell/module/hyper-v/set-vhd?view=windowsserver2025-ps)
and [MSFT_Disk properties](https://learn.microsoft.com/en-us/windows-hardware/drivers/storage/msft-disk).

After identity adjudication, prepare the already-authorized GPT/NTFS setup on
only that verified blank disk, label K98_D5B_QUALIFICATION, Q: if still unused.
Then continue the single disposable copy, labelled lab installation, retained
report/oracle comparison and real six-child maintenance qualification. Source
guards stay unchanged; no production-shaped false migration receipts or new
permissions. Preserve each failure and unknown result. Attachment success alone
does not establish format, copy, installation or D5b qualification success.

## Validation and review

Actual Windows PowerShell 5.1 passed inert parser/selector/refusal tests,
including DVD slot occupancy, full/no controllers, duplicate/empty disk IDs,
old disk/partition changes and nonblank/boot/system/wrong-size new disks.
AST checks restrict mutation sites and verify deadline/evidence controls.
No operational script was invoked by tests. Local cmdlet metadata confirms
the used VM-object/SCSI parameter sets; independent review found no blocker.

Changes review `ece56f22-3f83-4d03-8c00-8864308f05a6` completed with zero reportable
findings; Deep was off. Snapshot digest:
`640ab96a34cd72f477327c8064a3e5534ac418e3c9455d7f8f886a4b201f09a7`.
Findings SHA-256 `e779777215947cff41613f5889ec93c8ef430a9be3bfdd5cdb0c79216420c38b`;
coverage SHA-256 `4f993250f5b7b8125a13aaaa569afe32c6fc81d3e0dbee06b32cacfc79b9bd4f`.
Routing validation and whitespace checks passed. Sixteen original custody
records, eight correction artifacts and existing candidate runtime hashes were
verified unchanged. This documentation is added after the source review.

Test selection was run. Its generic full pytest/smoke/registration suggestions
are skipped: this change is an operator-only PowerShell storage packet with no
Python runtime/import/Discord changes; broad native fixtures would exceed this
stage's authorized actions. The architecture validator is Python-only, so it
is not applicable to these new PowerShell files. Focused inert PowerShell tests
cover the changed decisions. No unrelated deferred work was introduced.

References:
[capacity result](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Capacity%20Result%20and%20Storage%20Plan%20-%202026-11-11.md),
[native packet](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Native%20Qualification%20Packet%20-%202026-11-11.md).
