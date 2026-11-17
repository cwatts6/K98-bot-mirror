# P02 D5e approved cost setup handoff

The operator approved one new disposable database, one retained COPY_ONLY backup
capped at 32 GiB, and twelve additional row attempts, raising the ceiling from
83 to 95. This dated approval supersedes the pending-approval wording in the
retained readiness/extension proposal; that reviewed proposal is unchanged.

## Current accounting

| Scope | Completed | Expected |
| --- | ---: | ---: |
| D5d behavioural cases | 92 | 92 |
| D5d final accounting | 1 | 1 |
| D5e readiness | 7 | 7 |
| Accepted fixed subtotal | 100 | 100 |
| Fresh cost arms, including two warmups | 0 | 12 |
| Total including cost arms | 100 | 112 |

Setup acceptance is separately 0/1. Offline preparation controls are separate:
51/51 base PowerShell controls, 13/13 cleanup-fault controls, 3/3 async scenarios,
and 16/16 cost-plan controls. They do not establish native setup or cost acceptance.

Before execution: 1,235 native seconds and 49 Windows seconds remain. Row attempts
are 83/95 used, 12 remaining; the consumed 21-input allowance is unchanged. One
new database and one backup are approved and unused. No accepted work was replayed.
Setup reserves at most 450 native seconds, with 600 reserved for later cost arms;
at both maxima at least 185 remain for D5f. Proven closure permits actual elapsed
charging; unknown closure retains the full applicable reservation. Setup consumes
zero additional synthetic rows, zero inputs and zero cost arms.

## Packet and execution

Run once in the existing elevated native Windows PowerShell 5.1 console holding
the original `$global:D5bReportSession`. The packet verifies the exact session,
VM, disk, source files and database identities; do not create a replacement session.

```powershell
& 'C:\discord_file_downloader\scripts\copy_p02_d5e_cost_database.ps1' `
  -Session $global:D5bReportSession `
  -RunnerSHA256 '999c853b6b04da7b6550f0c8cc0afe1bbf9b22fea918f021088b2c0a03fec645' `
  -ApprovedCostCopy
```

The grouped setup creates only `K98_P025_D5e_Cost_20261115` from the accepted
`K98_P025_D5b_20261111`, retaining its one copy-only backup under
`Q:\D5eCost-20261115`. It verifies the backup, restores with exact new file paths,
checks source preservation and the copied ledger/modules, captures dependencies,
and checks closure. The prior proposal describes all space and command bounds.

Keep the printed receipt path and SHA-256. Any failure or unknown outcome means
preserve the database, files, intent, session and retained owners; do not retry,
delete, reset, or create another copy. The fixed create-only intent prevents replay.
No production operation, import, grant, service stop or deployment is included.

This is the reviewed setup packet. The grouped measurement runner follows receipt
adjudication, using the new database's actual birth, owner and dependency bindings.
Those bindings cannot be asserted before the database exists. The twelve approved
row attempts remain reserved for that later cost packet; they are not consumed here.

## Review and evidence

Initial five-file Changes review `f4c0c7a7-a2a3-4fa7-b11d-3c10976cce62` covered
the complete setup and plan. Two timing/cleanup correctness blockers were fixed.
Final four-file correction review `6d3b8c1c-44cc-4c86-ab72-6ca7dc3e974e` covers
`65f4ac92aa07f301123955c4a0f70e66ec53225a` through
`cb9093991835e4e2974a020d4ebbe49828993bd7`; it is sealed and read back complete,
with no reportable findings or remaining concrete handoff blockers. Deep scan was
off. The prior field-validation and missing-manifest errors remain in history.
Repair corrected the record fields in the same scan; no source or review outcome
was substituted. The incorrect-target setup scan is not acceptance evidence.

The recovery record and create-only handoff manifest under `.codex_artifacts/p025`
retain exact hashes, review locations, measured usage, approval and allowances.
Final review reported 1,779,353 total tokens, 1,772,053 input and 1,696,896 cached
input. This is aggregate review usage, not qualification time or incremental billing.

Runtime tests were not repeated: the reviewed source and both tests still match
the frozen review blobs, and all existing passing evidence is retained. Full pytest,
smoke imports and command registration are skipped because this continuation changes
only approval/review/handoff records, with no application or packet-source change.
Documentation/architecture/deferred/security-routing gates and test selection are
recorded in the handoff. No SQL source change or new deferred item is introduced.

All 2,403 G1 preserved files, 61 catalog packet pins, seven SQL pins, 14 prior
accounting-handoff pins and ten readiness-handoff pins must remain unchanged.
Raw files use exact SHA-256; only CRLF-to-LF transport comparison is used against
Git blobs. Existing receipt files and the earlier proposal are never rewritten.
