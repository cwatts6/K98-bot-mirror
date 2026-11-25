# D02 — development directory boundaries, ACLs and volume capacity

PREPARED, NOT APPROVED OR EXECUTED. Command `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/D02.ps1.txt`.

SHA256: `d834141d5e3483bdca907601158ed41d07d6366e4a16c40f177a61c7c5452072`.

## Exact targets

Operator uses Windows PowerShell on development host 9SX2VF4 under the existing Windows account reported as 9SX2VF4\cwatt, not MINI_AMD or SSMS. Local PowerShell executable/native identity has not been independently pinned; production H00's executable hash is not reused as development proof. No elevation/account/execution-policy change. Host-name gate is a wrong-host check, not token authentication. Chris Watts remains operator/reviewer/abort owner.

Six directory targets derived from D01R1's actual default/file parent: C:\; C:\Program Files; C:\Program Files\Microsoft SQL Server; C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV; its MSSQL child; its MSSQL\DATA child. Literal Get-Item attributes/type and Get-Acl owner/SDDL only. No child enumeration or database file opens. SDDL can contain account SIDs but no key/password bytes. Stop on reparse/non-directory/missing/inaccessible boundary, no traversal workaround.

After six successful checks, use .NET DriveInfo for exact C:\ root: readiness, drive type, filesystem, total size, total free space and available-to-observer bytes. No WMI enumeration, other volumes, network access or SQL. Results describe the observed C: and account, not SQL-service quota/capability, exclusive capacity, mount-volume identity, storage throughput or a reservation. Attribute checks are sampled and raceable; no race-free path/handle proof.

Purpose: inform later distinct destination path and capacity proposals. All 21 databases/49 files from D01R1 stay protected. The existing DATA directory is not a selected restore target. No new directory/name is reserved and no file collision test is implied before exact candidate paths exist.

## Budget and effects

One attempt/batch, six directory metadata/ACL reads plus one C: capacity query, ten-second cooperative deadline checked between targets, fifteen-second operator cancellation cutoff, 32 KiB maximum output. Blocking Get-Item/Get-Acl/DriveInfo calls can exceed cooperative budget; no hard syscall timeout claimed. Return only projected primitive fields, not recursive serialization of runtime objects. One JSON result with at most six directory records and one volume record. Exception type only on failure; no arbitrary error dump. No script-created evidence file, console/history effects remain.

Effects: filesystem/security/volume metadata access, ordinary audit/cache/resource activity and local scalar objects. No content read/hash, directory traversal/listing, SQL/backup-media access, ACL mutation, mkdir, copy/move/delete, database creation/restore, provisioning, task/job/process control, provider/Discord call or Git publication.

## Execution and stops after scope approval

Use existing maintenance window through 2026-09-29T09:23:23Z; no new scheduling approval. Run complete exact text once in Windows PowerShell on 9SX2VF4. If no suitable local shell is available, stop and report rather than change host/elevate or use SSMS. Do not dot-source unknown setup scripts or the supplied export scripts. Start timing before execution; cancel at fifteen seconds if still running and report interruption. No retry/automatic resumption or assumption cancellation completed a blocked call.

Accept only Operation D02, Host 9SX2VF4, Completed, six expected paths and nonnull volume root C:\ with plausible numeric sizes. Stop/reconcile on Stopped/error, count/path/type/reparse/access mismatch, missing volume, non-fixed/unexpected filesystem result, implausible sizes, timeout or oversized/truncated output. Never change permissions or delete files to pass a check. Preserve safe output/timing. No follow-up access to returned owners/SIDs/paths is authorized.

## Validation and proof status

Local static PowerShell parser passed; six paths verified against D01R1 parent hierarchy; no script execution. Fixed projections and bounded counts reviewed. Documentation/inert metadata preparation security-routing skip; no runtime implementation/PR, predecessor tests or security discovery. Candidate backup header/logical-file sizes, media integrity, prune protection and actual restore remain separate unresolved work.

All seven typed G4 proofs and actual restore remain incomplete; rollout/G5 unapproved. Preserve pending/recovered evidence, isolated hotfix, single-account/admin-owned model, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues.
