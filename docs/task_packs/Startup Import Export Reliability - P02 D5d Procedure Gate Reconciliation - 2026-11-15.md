# P02 D5d procedure gate reconciliation and grouped continuation

## Receipt and cause

Verified receipt `d5d-continuation-result-5c0fed5d62e940bbb8edc4610972671f.json`
has SHA-256 `2eba8a784ce4a948bb0aeecfc73a42569f315df6eff86604d2fc51a0696ed571`.
It stopped at **Retained procedure definition differs**, before staging or launching
an actor. Cases, collected results and launches are empty. Exact observer closure
and physical closure are true, with neither native nor Windows uncertainty.
The original preservation queries and all six seed-table comparisons preceded
this gate and passed. The full packet's `preserved` and `closed` flags are false;
they must not be represented as successful end-to-end qualification.

Elapsed host time was 0.7692337 seconds, charged as **one native second**.
No row or Windows time was consumed. This is the second failed native packet;
the successful read-only diagnostic remains separate. No accepted case is replayed.
The original job-count failure also remains historically unexplained.

The failed comparison retained neither the actual text nor the procedure name.
Therefore the precise text difference is **not proven**. SQL header rewriting is
only a possible explanation, not a finding. The new packet captures all nine
bounded definitions, hashes, names, execution contexts and metadata before
deciding whether any actor may run.

## Running behavioral totals

| Group | Expected | Accepted | Pending |
| --- | ---: | ---: | ---: |
| G1 | 47 | 47 | 0 |
| G2 native | 11 | 0 | 11 |
| G3 native | 9 | 0 | 9 |
| G4 native | 4 | 0 | 4 |
| Original offline restart variants | 21 | 0 | 21 |
| **Total** | **92** | **47** | **45** |

Preparation checks, observer queries and failed attempts do not add behavioral
acceptances. Successful execution and independent acceptance of all 24 pending
native cases would raise the total to 71/92. The original 21 offline restart
variants and wider D5e/D5f/D6 obligations remain open. Prior G1 controls, D5c,
custody and drain evidence is carried unchanged, outside this denominator.

## Remaining allowances and next reservation

| Allowance | Remaining before next run | Next maximum reservation |
| --- | ---: | ---: |
| Native seconds | 1,244, including 1,000 protected | 240 |
| Windows seconds | 50 | 40 |
| Synthetic row attempts | 8 of the 83 ceiling | 8 |
| New disposable databases | 0; approved DB10 already exists | 0 |
| New inputs | 0; prior 21 remain consumed | 0 |

Rows remain **75/83 attempted**. Full reservation leaves 1,004 native seconds,
including the protected 1,000. No extension is necessary for this packet. Unknown
physical closure retains the full reservation; a completed remote command alone
does not release it. Any subsequent increase must be requested before use.

## Frozen next packet

- Runner: `scripts/run_p02_d5d_verified_continuation_packet.ps1`.
- Runner SHA-256: `32e0a936c2d40cb055394f43cf839ed5d9a04081791feb84d585a091cd10281a`.
- Manifest: `.codex_artifacts/p025/d5d-verified-continuation-packet.json`, 173,199 bytes.
- Manifest SHA-256: `a1acfff67a7d320e24b8e003d2e62137802cfcc0f26f1d0d3b83bbdfe457ce65`.
- New create-only intent: `d5d-verified-continuation-intent.json`.
- Previous runner, actor, launcher, manifests, intents and receipts remain unchanged.
- Existing DB10, exact birth and seed preimages are required. No database creation,
  stored-procedure rewrite, seed reset, cleanup deletion or accepted replay occurs.
- `Q:\D5dContinuation-20261115` must still be absent. The failed attempt stopped
  before creating it; the next packet checks absence and refuses if it exists.

All nine comparisons must pass before staging. Beyond existing CRLF and outer
whitespace normalization, only the exact leading verbs `CREATE`, `ALTER` or
`CREATE OR ALTER` may differ. Everything from `PROCEDURE` onward must match,
including names, signatures, comments and bodies. Schema, SQL-procedure type,
ANSI NULLS, quoted identifier, execution context, schema binding and recompilation
settings must also match the submitted source. Any other difference retains all
nine comparisons and stops before native tests. Oversized or unavailable text is
refused; a truncated diagnostic is explicitly marked, never accepted as equality.

The catalog fields and stored-definition semantics are documented in Microsoft's
[sys.sql_modules reference](https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/sys-sql-modules-transact-sql?view=sql-server-ver16).
The accepted DDL verbs are described in the
[procedure syntax reference](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-procedure-transact-sql?view=sql-server-ver16).
These references do not establish which difference occurred in the failed run.

## Validation and review

Final preparation passed **3 Python groups, 225 Windows PowerShell 5.1 controls**,
and the final manifest bootstrap of **15 modules with zero native cases**.
The new tests cover unchanged downstream actor/closure code, all prior pins,
receipt tamper refusal, header variants, changed bodies and metadata, missing or
oversized definitions, and collecting all nine mismatches before refusing staging.
All earlier preparation evidence is retained separately, not added to 47/92.

Architecture validation (219 Python files), deferred-item validation (218 Markdown
files), security routing and explicit-path test selection passed. Ruff critical
checks passed using the existing repository environment; the first attempt with
the system interpreter reported Ruff unavailable. Full pytest, application smoke
imports, command registration and release checks are skipped: this changes only
qualification tooling and does not alter application, deployment or SQL source.
The new runner carries one trailing space from the frozen actor loop; diff-check
reports that inherited formatting issue, with no behavioral impact. It is retained
to keep the downstream comparison byte-identical.

Changes review **8136e37f-084a-480f-96fa-4387ddda1d9a** completed with zero findings
and no concrete handoff blocker. Exact range:
`8a05c7ad0713ad37cdd2b9137a2eed677032eb70..f26df67995f652961e0b8cfde7553722a5dc7fca`.
All four files were reviewed; Deep was off. A separate review index and unreferenced
commit leave the ordinary branch/index unchanged. Native acceptance is pending.
Tool-reported review usage: 986,372 aggregate tokens, including 966,912 cached input;
these are rollout counters, not incremental billing or qualification time.

Run once in the existing elevated Windows PowerShell session:

```powershell
& 'C:\discord_file_downloader\scripts\run_p02_d5d_verified_continuation_packet.ps1' `
  -Session $global:D5bReportSession `
  -PacketSHA256 'a1acfff67a7d320e24b8e003d2e62137802cfcc0f26f1d0d3b83bbdfe457ce65' `
  -RunnerSHA256 '32e0a936c2d40cb055394f43cf839ed5d9a04081791feb84d585a091cd10281a' `
  -ContinuationApproved
```

Retain any result and intent, including failures. Do not rerun a consumed packet.
