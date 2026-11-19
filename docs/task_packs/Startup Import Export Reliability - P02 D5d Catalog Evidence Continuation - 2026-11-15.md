# P02 D5d catalog evidence reconciliation and continuation

## Verified outcome and proven cause

Receipt `d5d-verified-continuation-result-9ce4630f75924e94aa33bcf12bec51b2.json`
matches SHA-256 `3acec35e0ace9b5b4bbbf266cba91fe62f45775bb111b51e7659deb75bd05ae2`.
The packet stopped before staging or actor launch. Cases, collected results and
launches are empty. Physical and exact observer closure are verified, with no
native or Windows uncertainty. Earlier preservation queries and six seed-table
preimages passed; the full packet's `preserved` and `closed` flags remain false.

The stored definitions for `usp_RunMaintenance`, `usp_MaintenanceBackupClaim` and
`usp_MaintenanceBackupAcknowledge` start with **CREATE followed by three spaces,
then PROCEDURE**. Their submitted definitions start with `CREATE OR ALTER PROCEDURE`.
The comparison helper allowed only single-space header alternatives, so it
incorrectly refused these observed definitions. This is a confirmed preparation
defect. The entire remaining text of each procedure matches the submitted source
after the existing CRLF normalization; there are no body, signature or comment
differences. The other six definitions and all nine metadata records match.
The earlier initial job-count failure remains a separate, historically unproven
failure; this receipt diagnoses the procedure gate only.

The next builder proves each whole observed definition against the originally
submitted SQL using only that exact observed leading-header substitution, checks
its digest, length and metadata, then pins the verified complete catalog text.
It retains the original submitted definitions and all prior evidence. The runtime
comparison helper and native actor/closure code are unchanged. No SQL definition
is altered, no seed is reset, and no accepted case is replayed.

## Totals and allowances

| Behavioral group | Expected | Accepted | Pending |
| --- | ---: | ---: | ---: |
| G1 | 47 | 47 | 0 |
| G2 native | 11 | 0 | 11 |
| G3 native | 9 | 0 | 9 |
| G4 native | 4 | 0 | 4 |
| Original offline restart variants | 21 | 0 | 21 |
| **Total** | **92** | **47** | **45** |

This is the third failed native packet, alongside one completed read-only
diagnostic. None adds a behavioral acceptance. Earlier G1 controls, D5c, custody
and drain evidence remains accepted and unchanged, outside this denominator.
Accepting all 24 native cases in the next receipt would raise the total to 71/92;
the original 21 offline restart variants and later D5e/D5f/D6 obligations remain.

The latest 0.7637201 seconds of host elapsed time costs **one native second**.
No synthetic row, input or Windows time was consumed.

| Allowance | Current balance | Next maximum reservation |
| --- | ---: | ---: |
| Native seconds | 1,243, including 1,000 protected | 240 |
| Windows seconds | 50 | 40 |
| Synthetic row attempts | 75/83 used; 8 remain | 8 |
| New disposable databases | Approved database already created | 0 |
| New inputs | 21 consumed; no new inputs | 0 |

Full reservation leaves **1,003 native seconds**, including the protected 1,000.
No extension is needed. Physical uncertainty retains the full reservation; remote
command completion alone cannot refund it. Any later increase requires approval.

## Reviewed packet

- Runner: `scripts/run_p02_d5d_catalog_continuation_packet.ps1`.
- Runner SHA-256: `246fdf6fbc536d458741586527f894d6b8071372dc17047093780d0f7c9b62ef`.
- Manifest: `.codex_artifacts/p025/d5d-catalog-continuation-packet.json`, 189,887 bytes.
- Manifest SHA-256: `661e4f3e6a94ae983b88ebf49f92d4c1e3b1a862a5f68fdfa82ae3f3528c0056`.
- New create-only intent: `d5d-catalog-continuation-intent.json`.
- Existing DB10 with birth `2026-11-15 10:31:04.697` and exact seed preimages required.
- Guest folder `Q:\D5dContinuation-20261115` must still be absent; refuse if present.
- All previous manifests, scripts, receipts, intents and accepted evidence remain.

The packet retains all 24 original native case IDs in one group. Definitions,
identities and preservation must pass before actor staging. No database creation,
definition rewrite, fixture cleanup, retry or session replacement is introduced.

## Preparation and review

Passed **4 Python groups and 246 PowerShell 5.1 controls**, plus **one final-manifest
integration control** exercising the actual comparison loop and gate against all
nine saved catalog rows. All nine returned `exact_normalized`. Changed bodies,
metadata and unobserved header spacing are rejected. The final manifest also
passed the 15-module bootstrap with zero native cases. These preparation results
are separate from 47/92 behavioral acceptance and do not replace native execution.

Architecture validation passed for 221 Python files; Ruff critical checks and
explicit-path test selection passed. Security routing passed. Deferred-item
validation is recorded in the final handoff. Full pytest, application smoke,
command-registration and release checks are skipped because only qualification
tooling changed; no application, deployment or authoritative SQL source changed.
The frozen downstream loop retains its prior single trailing space for exact
source equality. No unrelated cleanup or refactor is included.

Changes review `ba10530c-cf08-41a1-b995-282e4cbfafe9` completed with zero findings
and no concrete handoff blocker. Exact range:
`f26df67995f652961e0b8cfde7553722a5dc7fca..b94503b0ae27ad77b8e1f280e57321663cba6942`.
All four files were reviewed, including both test files; Deep was off. The separate
review index and unreferenced snapshot preserve the ordinary branch/index.
Tool-reported aggregate usage: 893,793 tokens, including 885,248 cached input;
these are rollout counters, not incremental billing or qualification time.

Run once in the existing elevated Windows PowerShell session:

```powershell
& 'C:\discord_file_downloader\scripts\run_p02_d5d_catalog_continuation_packet.ps1' `
  -Session $global:D5bReportSession `
  -PacketSHA256 '661e4f3e6a94ae983b88ebf49f92d4c1e3b1a862a5f68fdfa82ae3f3528c0056' `
  -RunnerSHA256 '246fdf6fbc536d458741586527f894d6b8071372dc17047093780d0f7c9b62ef' `
  -ContinuationApproved
```

Retain the result and consumed intent even on failure. Do not rerun the packet.
