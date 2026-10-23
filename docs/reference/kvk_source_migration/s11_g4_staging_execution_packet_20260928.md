# ST01â€“ST04 and manual copy â€” exact staging proposal

PREPARED; awaiting approval of these new exact commands and effects. The operator's latest approval continued preparation from a non-executable draft. No command below has run. This packet is the proposed next effectful step, not actual restore or rollout approval. Existing maintenance window ends 2026-09-29T09:23:23Z; do not reconfirm scheduling inside it.

Chris Watts operates/reviews/cancels under the existing Windows accounts and RDP session. No new account/share, elevation, execution-policy change, job control or ACL editing. Access denial means stop and retain evidence, not fix permissions or elevate automatically.

## Targets and fixed data

Source host MINI_AMD; 119 literal files from full set 97337 and log sets 97338â€“97455. Retained actual lengths total 2,815,180,800 bytes. No wildcard selection, discovery, substitution, timestamp sorting or new backup. The sealed target manifest remains `staging-restore-targets-draft-20260928.json` SHA256 `0c4c49fe6cd5d8b7b36821021f6adf2bdb9c9a8d801de08a08b88976f28920cb` under `.codex_artifacts/s11-g4-capture-preparation-20260926`.

Development host 9SX2VF4. Only new root `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11_G4_20260928_97337`, its `media` child and `route-marker.txt` at the root may be created by ST02. The data child/database/files are not created in this packet. Existing 21 databases and 49 catalog files are untouched.

Manual destination from MINI_AMD is the corresponding `\\tsclient\C\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11_G4_20260928_97337\media`. Marker identity checks the reported RDP mapping before copying. It is a correlation marker written on the guarded development host, not cryptographic machine authentication or protection against deliberate marker duplication.

## Ordered commands and manual operation

All commands are complete text files under the evidence root's `commands` directory. Run each whole file once, in this order, only after this packet's exact approval. The hash table below is part of the seal. Stop the group on any failure, mismatch or incomplete output. Do not rerun, continue from a partial index or clean up.

1. **ST01.ps1.txt â€” MINI_AMD Windows PowerShell.** Four fixed source-directory boundary checks; hash the 119 literal files serially. Require the retained F01 length, regular non-reparse files and stable sampled length/mtime while each handle is held. Each FileShare.Read handle denies concurrent write/delete opens for that file during hashing; it is closed after its hash. Emit per-set path, length, SHA256 and mtime. Require Completed, 119/119 and BytesRead=2,815,180,800 before continuing.
2. **ST02.ps1.txt â€” 9SX2VF4 Windows PowerShell.** Check six existing ancestors for directory/non-reparse attributes, exact root absence and ready NTFS C: with at least 250 GiB available. Create only root and media, without Force/reuse; capture inherited owner/SDDL. Exclusively create the marker with the fixed 62-character ASCII value shown in the script. No explicit ACL changes. Require Completed, exactly those three new paths and both ACL records; keep partial creations on failure.
3. **ST03.ps1.txt â€” MINI_AMD Windows PowerShell in the existing RDP session.** Open only the new marker through the exact redirected path, bounded to the expected marker length; require Completed and MarkerMatched=true. Stop if the route is unavailable, wrong or inaccessible. No discovery or fallback share.
4. **Admin manual copy â€” same RDP session.** Copy only the 119 exact source/destination pairs in `manual-rdp-copy-checklist-draft-20260928.txt`. Use Copy, never Move/Cut. Do not copy entire FULL/LOG folders or extra files. Refuse overwrite/merge/replace/rename prompts, source errors or incomplete transfer; cancel and retain partial destination files. No retries. UI transfer is unthrottled: approval of this packet explicitly accepts that fact within the byte/time limits below. Do not disable prune jobs. No source retention guarantee spans the whole manual transfer; a source disappearing is a stop, not permission to substitute media.
5. **ST04.ps1.txt â€” 9SX2VF4 Windows PowerShell.** Check eight exact destination boundaries and the 100 GiB free-space floor. Enumerate only media's immediate children, stopping on the 120th or any unexpected name; require exactly the 119 listed entries. Hash those same files serially with the same length/stability/share checks and pacing as ST01. Sample the free-space floor before each file. Emit 119 per-file hashes. Assistant then compares every set ID, byte count and SHA256 with ST01; absence of a script error alone does not prove source/destination equality. No SQL read follows automatically.

## Effects, budgets and stops

ST01 and ST04 each read exactly 2,815,180,800 content bytes on success plus bounded filesystem metadata. One 1 MiB buffer, one open file/hash at a time, application-level pacing approximately 10 MiB/s with a one-chunk burst; no hard disk/cache throughput ceiling. 180 seconds cooperative per file, 600 seconds cooperative total, operator cancellation at 610 seconds or if an individual file exceeds 190 seconds. Blocking opens/reads/metadata calls are not forcibly time-bounded by the script. No loops retry failed reads. Hash output is projected primitive fields only, capped at 64 KiB and 119 rows; on excess, stop and report rather than paste an oversized dump. Expected hash duration at the pacing rate is roughly 4.5 minutes per pass, not the earlier 15-second metadata cutoff.

ST02 and ST03: 10-second cooperative budgets, 15-second operator cancellation; output ceilings 16 KiB and 4 KiB respectively. ST02 creates two directories and one small marker file, consuming space and inheriting ACLs; this is provisioning of a staging location and therefore a new explicit effect. ST03 reads that marker over the existing RDP redirected drive. Marker match does not establish SQL service effective access. Creation/access failures retain partial artifacts; no cleanup is authorized.

Manual transfer: 119 new files, 2,815,180,800 bytes, one attempt per file, maximum 30 minutes aggregate copying. No throttle claim; no parallel copy batches. Monitor transfer status and existing C: free-space display at least every five minutes during copying; stop if free space falls below 100 GiB, on errors, or at 30 minutes. The ST02 250 GiB preflight and ST04 free-space checks are guards, not quotas/reservations or proof of continuous capacity.

Aggregate expected hash/copy I/O is approximately 11,260,723,200 bytes (source hash read, copy source read and destination write, destination hash read), excluding metadata/cache/transport overhead. Maximum phase time is 51 minutes including hash/metadata cutoffs, excluding operator host-switching and receipt review. Do not start if that execution budget crosses the existing maintenance-window expiry.

Hash handles may briefly conflict with prune/write attempts against the currently hashed file. No files or jobs are modified to suppress that conflict. Source hashes bind bytes observed before copying; matching destination hashes later bind copied bytes to that observation, not an atomic multi-file production snapshot. Retained SQL LSN/header chain remains a separate requirement. Hash mismatches, missing/extra files, access/reparse/type errors, low space, time/output limit or marker mismatch stop without retry. No permissions/elevation workaround, source deletion, rename or replacement.

## Evidence and completion

Retain all four JSON receipts, start/end/operator cancellation information, manual-copy completion/count/error status and the existing marker. Prefer supplying hash outputs as text attachments so 119 rows are not truncated. No key bytes, credentials, backup content or private prune command rows are requested.

Successful staging requires ST01/ST04 Completed with all 119 exact members and equality for every SHA256/length after local reconciliation, ST02/ST03 complete receipts, and manual-copy completion attestation. Do not label staged files immutable: no write-protection policy is installed. Hashes and revalidation before later restore protect the evidence boundary, not future writes. Later header/layout/media integrity checks and actual restore still require exact approval.

No SQL/provider/Discord call, backup/restore, data-directory creation, database creation, runtime deployment/restart, G4 proof issuance, rollout, G5 decision or Git publication. Preserve every partial result and the withdrawn collector/deferred memory scope.

## Local validation and review

Static PowerShell parsing, literal manifest/path/length equality, fixed row/byte budgets, directory-creation effects and fail/retain behavior reviewed locally. No production/development command executed. Original pending and retained evidence hashes verified. Local generator syntax error was corrected before any command was authored or run; it caused no live attempt.

Security-routing decision: documented skip for additive inert approval artifacts, with explicit review of file-read/share modes, new-directory creation, output projections and no overwrite/delete. No runtime integration, existing permission/configuration change or PR is involved. No broad security scan or predecessor rerun. Actual restore scripts remain guarded drafts. Runtime tests and pre-PR validators are inapplicable; local parser/manifest/hash checks are the relevant validation here.

## Sealed command hashes

| Command | SHA256 |
|---|---|
| ST01.ps1.txt | `422b2726c910d74ba83572cf5a4699eb60d9e15ca274380d8c6a564dec2c2fa3` |
| ST02.ps1.txt | `e2ef9c499ab6149046ea4a282ceefb5afc3dc342365fb5b8f065f0df8c08a087` |
| ST03.ps1.txt | `092c4dcca5c90f4bd8a25d9450b10465797d53937c14c66b0f4c0ecdfa042a8d` |
| ST04.ps1.txt | `65899aafd070bf1b3fc001fc51115645d980d5238afa05b7dd0e8003c7bc6e3c` |
