# P02 D5b capacity result and storage exception — 2026-11-11

**The approved read-only probe passed; the disposable copy cannot fit on the
guest's current volume. No copy or installation was attempted.** A separate
qualification disk requires a specific exception to the operator's current
no-VM-resource-increase limit.

## Verified result

Receipt `d5b-capacity-result-2ab0866628e74f2bbd56d111a30183d6.json` remains unchanged
in `.codex_artifacts/p025/`, SHA-256
`30c4c9a7001906e6dbaf4d647b6cca721763e2bea2e0f007055cb99cb8451f48`.
It records 17 SQL commands, 13 rows, 0.9826771 seconds and 11,377 bytes, with no
host/guest errors. Script, manifest, source identity/settings/files, borrowed
session and post-observation isolation match. Work disposal and the exact
session/login-time absence were verified; observer disposal is local evidence.

Existing sysadmin/create/backup permission observations equal one. Thus the
proposed target `K98_P025_D5b_20261111` is confirmed absent with sufficient
catalog visibility. No new permission is required by these observed facts;
later application least-privilege qualification remains separate.

| Storage | GiB |
| --- | ---: |
| Source data file allocation | 16.9873 |
| Source log file allocation | 64.0000 |
| Total source allocation | **80.9873** |
| Guest C: free, both samples | **10.6082** |
| Mandatory unchanged reserve | **8.0000** |
| Usable above reserve | **2.6082** |
| Additional space needed for a copy alone | **78.3791** |

Backup staging and workload growth are additional. Low used-log percentage
(2.402443%) does not remove the restored log's 64 GiB allocation. Even the data
file alone exceeds available space above the reserve. Do not shrink the source,
delete retained evidence, assume compression solves restore allocation, or move
the qualification to another server.

Adjudication is stored separately as
`.codex_artifacts/p025/d5b-capacity-adjudication-2ab0866628e74f2bbd56d111a30183d6.json`.
There were zero input reads/consumption and zero native writes.

## Concrete proposed storage exception

Permit **one new 256 GiB dynamically expanding VHDX** for D5b only, attached to
the existing isolated VM. Proposed host path:

`C:\discord_file_downloader\.codex_artifacts\p025\d5b-native\D5b-Qualification-20261111.vhdx`

A fresh read-only host check found 1,436,746,690,560 free bytes on C: (about
1,338 GiB); this exceeds the entire 256 GiB maximum allocation plus the existing
8 GiB host reserve. The proposed file does not exist, and the existing storage
ancestors have no reparse point. Recheck immediately before creating anything.
Dynamic allocation does not reserve physical host space, so later host-space
gates remain mandatory.

After approval, the storage packet must:

1. Verify host `9SX2VF4`, elevated PS5.1, exact VM
   `2ac1b401-7076-4965-af71-de36ee0f9f9c`, Running, four CPUs, fixed 8 GiB RAM and
   zero network adapters. Read existing disk/controller/guest-volume identities
   before choosing an unused SCSI attachment slot. No shutdown/restart implied.
2. Create the new VHDX with exclusive new-path semantics and record its identity.
   Refuse an existing file, ambiguous target, reparse path or unexpected device.
   Attach only that file; do not alter any existing disk or its size.
3. Match the newly attached guest disk to that VHDX using device identity and
   before/after inventory. Initialize/format **only the proven new blank disk**
   as GPT/NTFS, label `K98_D5B_QUALIFICATION`, proposed drive Q: if unused.
   Do not select a disk merely by number/size or reuse another drive letter
   silently. Stop on ambiguity or an occupied Q:.
4. Use the new volume only for the owned D5b backup staging, disposable copy and
   qualification artifacts. Preserve original C: database files, settings and
   evidence. Retain the disk/artifacts at closeout; deletion is not part of this
   approval request.

Provisional peak allocation envelope for the new volume:

| Owned purpose | Maximum GiB |
| --- | ---: |
| Copy-only backup staging | 90 |
| Disposable database data/log allocation, including bounded growth | 112 |
| Qualification working files | 16 |
| Mandatory free reserve | 8 |
| Total planned envelope | **226** |

The remaining approximately 30 GiB provides filesystem/envelope margin, not
permission for unbounded growth. Exact backup/copy and workload caps must be
encoded and checked before execution. The unchanged original C:/tempdb disk
reserve, version-store/log gates and workload time limits still apply; adding
this volume does not waive them or move/reconfigure tempdb.

This exception changes **storage only**. RAM, CPUs, network isolation, SQL rights,
production guards, time/resource floors, original database/evidence protection,
one-copy scope and the consumed 21-input allowance remain unchanged. No new
input or import replay is included.

## Next step

Obtain the specific storage exception, then prepare/validate the exact storage
setup and continue the already approved D5b packet. No disk has been created,
attached or formatted. If approval is declined, native D5b remains blocked by
this verified capacity deficit; offline success cannot substitute for it.

References:
[approved native packet](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Native%20Qualification%20Packet%20-%202026-11-11.md),
[offline correction](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Receipt%20Correction%20and%20Validation%20-%202026-11-11.md).
