# P02 D5b qualification storage result — 2026-11-11

**The approved new disk is attached and formatted as Q:. D5b database-copy,
installation and workload qualification remain outstanding.** The two storage
operations used the operator's existing elevated console and authenticated
session. No SQL, retained-input processing or explicit permission change ran.

## Preserved evidence

Attachment receipt `d5b-disk-52c346e18065454eb10812deee179b9b-result.json`, SHA-256
`0642587a609114839e455394d1af5511ea8b2ad858c19ef3f05fc81a199fa7d8`, completed in
4.4836922 seconds without errors. Separate intent, created and attached receipts
remain under `.codex_artifacts/p025/`, with their hashes in the separate
attachment adjudication. The original system disk and four partitions match
their before-images; existing DVD slots are unchanged.

Host VHD identifier: `E65288F1-A566-46C6-AD4E-8D834543C4BC`.
Guest device identifier: `60022480F18852E666A58D834543C4BC`.
The sole new guest device appeared at LUN 3, corresponding to the sole new host
attachment at SCSI controller 0/location 3. Its device path, identifier, location,
256 GiB size and blank/non-system state were bound for formatting. Host GUID
text and guest VPD text are not assumed to be identical; the complete recorded
attachment transition and stable device identities establish the target.

Formatter `scripts/format_p02_d5b_disk.ps1`, SHA-256
`cc192c31633aa809273caf1e896a576d31c7f3533de41d3ca0a8ce39cdf74e85`, reads the
hash-pinned attachment receipt and rechecks both host and guest identities.
It initializes/partitions through the exact disk object, then formats only
the newly created partition object. It has no arbitrary disk-number/drive-letter
format selector, retry, deletion, SQL command or permission-grant path.

Format receipt `d5b-format-ce9209cc6bf64d56803793bb69f92785-result.json`, SHA-256
`0c26e1ad944594f09c8bfd208c497eb977dc5a4b7b2d134406c6f6c89fed5577`, completed in
4.3847465 seconds without host or guest errors. The exact volume is:

- Q:, label `K98_D5B_QUALIFICATION`, NTFS, 65,536-byte allocation units, Healthy.
- Volume/partition GUID `47cc6080-9e5f-447c-a9e2-dcc007b1e297`.
- Size 274,860,015,616 bytes; free 274,760,531,968 bytes (about 255.89 GiB).
- Host VHD physical allocation 406,847,488 bytes; host free 1,436,275,085,312 bytes.

The formatter verifies the original disk/partitions and C: reserve after the
operation. It records the new volume's inherited root ACL without modifying it.
Original RAM/CPU/network isolation, SQL rights, all time/resource bounds and the
consumed 21-input allowance remain unchanged. No copy or qualification pass is
inferred from successful storage setup.

## Offline validation

Actual Windows PowerShell 5.1 inert tests passed in
`tests/validate_p02_d5b_format.ps1`, SHA-256
`59d686001e9dbfabd42d081f389a6584e004c9955c3770f10f2c3f4e0b3d8a06`.
They cover wrong device identity, nonblank/system/offline/readonly disks,
original-disk and partition changes, object-scoped mutation sites and deadlines.
The first test run exposed a test-helper dynamic-scope collision: its Expected
argument shadowed the operational helper's expected fixture. Renaming only that
test argument fixed the harness; operational source and assertions were unchanged.

Changes review `654a7019-ab94-4c26-bf90-f4e16cbc7f69`, Deep off, completed with zero
reportable findings. Snapshot digest
`7799c1a88b29fd73bfbbaf4c7e8003be69e519317d9f5f15483878c37cbeb65c`.
Findings SHA-256 `2caebe753630813af57c058dd547787634246606d2749d8a3c8be27c178bd2ca`;
coverage SHA-256 `8ebfda42a2072b44b7cd663e2e55ff8620576e368f96cd6407de24e5e185ef55`.
Independent review found no blocker. Routing and whitespace checks passed;
test selection ran. Python-wide tests and architecture scanning are inapplicable
to these operator-only PowerShell additions; no Python runtime changed.

## Continuation

Prepare the exact single-copy packet on Q:, with source read-only identity and
custody, exclusive new backup/database paths, copy-only checksum backup and
verification, exact logical-file mapping, bounded copy growth and source/owned
session readback. Original database and evidence remain untouched. Existing
permissions must suffice; any failure stops with evidence retained.

The original Phase 1 implementation describes the 1,800-second rehearsal bound
as a **statement cap**, not a Bot timeout change. Later D5 documents preserve
the rehearsal ceiling. The native D5b packet must state its tighter operation
and overall bounds explicitly and must not silently reset or extend limits.
The storage steps remain separately bounded five-minute setup operations.

References:
[approved disk packet](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Approved%20Disk%20Attachment%20-%202026-11-11.md),
[native packet](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Native%20Qualification%20Packet%20-%202026-11-11.md),
[original Phase 1 bounds](archive/Startup%20Import%20Export%20Reliability%20-%20P02%20Phase%201%20Implementation%20-%202026-11-07.md).
