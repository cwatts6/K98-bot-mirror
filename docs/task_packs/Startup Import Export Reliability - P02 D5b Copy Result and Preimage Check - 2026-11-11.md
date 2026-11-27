# P02 D5b copy result and prerequisite observation — 2026-11-11

Status: disposable copy verified; read-only prerequisite packet ready for one
operator execution. Candidate installation and D5b qualification remain pending.

## Copy adjudication

Receipt `d5b-copy-987ce8c949d5477f91f7cb3632c66b23-result.json`, SHA-256
`1bf30b8b572e28658f10eb5f1646894c7ade4f3e6f02a0ed1c2092032bd0e568`,
completed in 242.6257779 seconds with 22 SQL commands, 16 rows and no errors.
COPY_ONLY checksum backup, checksum verification and the single restore passed.
Original database identity, settings and file metadata matched before/after;
the source remains READ_ONLY/RESTRICTED_USER. The owned SQL work connection was
disposed and its exact session/login-time pair was independently absent.

The one disposable target is `K98_P025_D5b_20261111`, ID 8, created
`2026-11-11 17:00:42.830`, with its MDF/LDF under `Q:\D5b-20261111`.
The owned backup and all stage receipts remain retained. Final observed free
space was 11,383,435,264 bytes on guest C:, 177,697,521,664 on Q: and
1,339,086,016,512 on host C:. No candidate installation, report recomputation,
maintenance child, input replay or permission change occurred in the copy stage.

The original copy receipt rounded its remaining native budget upward to 1549
through an integer Math.Max overload. Preserve that receipt unchanged; the
separate adjudication records the conservative floor of **1548 seconds** after
storage and copy execution. Subsequent native elapsed time is deducted from that
floor. This adds no time, changes no original rehearsal/statement or Bot timeout,
and does not count offline preparation or user handoffs as benchmark intervals.

## Exact next packet

`scripts/collect_p02_d5b_preimages.ps1`, SHA-256
`4ce29c623a3d31aa4da55ef226ba677df56f18988acd978a9b4e4984c01d9e39`.
Pinned private manifest `.codex_artifacts/p025/d5b-preimage-manifest.json`, SHA-256
`15a227f7487e04ad5d2f5ce2ab17807631d01e95e89b6ffa7c8080b62f0e3f7c`.

The collector verifies the existing exact host, isolated VM, borrowed session,
Q volume, copy identity/settings/files and preserved source protection. Existing
sysadmin and VIEW DEFINITION visibility must be observed before structural
absence can be interpreted. No rights are granted.

It compares 30 structural hashes with the fixed D4 profile using the exact
canonical query from the authoritative SQL repository's
`deploy/SqlDeploy.RecoveryRelease.ps1`. It also observes the daily-report index
and procedure, KS4 sequence, configuration maintenance eligibility aggregates,
completed canonical KVK outputs and summary checkpoints. These observations
determine whether a bounded test installation and actual six-child work have
the required starting state. Hash mismatches require adjudication, not adoption
of the observed values or automatic installation.

Bounds: one attempt; 300 seconds overall; 3-second metadata commands; zero lock
wait; 48-command, 2,048-row and 1 MiB receipt caps; unchanged 8 GiB disk reserves
and 512 MiB version-store limit. Successful source path is 47 commands with at
most 90 accepted result rows. No retained-input file is read or consumed. The
21-input allowance remains consumed. Cleanup requires owned work disposal and
observed exact session absence. Errors or unknown cleanup stop progression;
retain receipts/session and do not retry automatically.

## Validation and review

Windows PowerShell 5.1 inert tests passed for query limits, timeout/disposal,
permission allow/deny/NULL/invalid results, raw owner evidence, server-version
refusal, nested errors, all copy identity/settings gates and conservative
fractional budget subtraction. Test file `tests/validate_p02_d5b_preimages.ps1`
SHA-256 `6eae6942d2cff3537d96fbf18499f60df489138d56e98e2e34d7f98ad3a1b574`.
Canonical query equality/source hash and 30 unique object bindings were checked.
Routing and whitespace checks passed. Test selection ran; broader Python smoke,
registration and native fixtures are not applicable to this operator-only
PowerShell addition. Existing Python changes retain their prior focused test
evidence. No new deferred optimisation item or Python architectural change.

Changes review `09807776-0590-45ba-a831-6f4bbd4fb912` finalized with zero reportable
findings, Deep off. All eight changed source inventory files were accounted for;
seven unchanged sources were hash-verified against prior completed reviews.
Independent source review found no blocker. Snapshot digest
`46d6b220888afa6ced4d8b354505f47520d418e10e678df6975af8173966b04b`.
Findings digest `84d12e971a04a10c593bfc6fda38bb5e18ea2ea053977914ffc1d3b0f81cb2d7`;
coverage digest `2db8081bc86afa244833aa96bc846678eb7db7254f6c00b3ea738f46a0af44ac`.
The initial final-draft submission used unsupported disposition `reviewed` and
was rejected; premature completion then failed because the saved draft remained
partial. After the operator requested continuation, the same scan was resumed,
the disposition corrected to `no_issue_found`, the accepted complete draft
verified, and completion succeeded. No new scan, source change, approval change
or native retry was used to resolve this review-record error.

Original custody checks (16), D5a receipts (3) and D5b correction artifacts (8)
were rehashed unchanged. D5b remains incomplete until the authorized installation,
report/oracle checks and six actual maintenance children have admissible evidence.

## Following execution plan

1. Adjudicate the new read-only receipt against fixed structural prerequisites,
   actual retained eligibility, resources, limits and connection closure.
2. Prepare the exact test-only installation adapter on this sole copy, preserving
   production guards, structural pre/postimages and honest test receipts. Do not
   invent formal Applied migration rows or grant missing rights.
3. Run bounded report recomputation with controlled clock/cursor stimuli and the
   independent numeric/name oracle for 42 states and 14 exports; preserve original
   immutable queued bytes and accepted tied-zero-rank adjudication.
4. Exercise six real maintenance children using legitimate retained-data demand
   and physical-work evidence. Empty queues or ineligible work cannot count as a
   pass; no original/production backup job may be dispatched as a substitute.
5. Verify original preservation, owned cleanup and all remaining acceptance
   obligations. Stop and report any scope or resource limit that prevents completion.
