# P02 D5d native acceptance, offline restart results and final accounting

## Latest native receipt

Receipt `d5d-catalog-continuation-result-2a459e53deef4ce18aa11f31f923780f.json`
matches SHA-256 `fb10c0843685e491533725354a3aedc53c5e9841b4fda6fe68bd40afabaa69f1`.
All 24 actors finished successfully. Each result has its exact identity, matching
retained stdout hash, joined process, empty job and absent SQL ownership. The
individual transaction checks observed the committed marker and absence of the
rolled-back marker before accepting those cases. Original preservation checks and
database-identity comparisons passed. Physical and exact observer closure are
verified; no native or Windows uncertainty remains.

The subsequent aggregate count query used the unquoted alias `backup`. SQL Server
rejected that reserved keyword. Consequently the full packet reports incomplete
and `closed=false`, despite 24 individually accepted cases and `preserved=true`.
This is a final reporting-query defect. The accepted cases must not be replayed.
The final aggregate fixture counts remain a separate open accounting gate.

The run consumed 5.4062915 seconds of host elapsed time, charged as **6 native
seconds**, and 0.500945 Windows seconds, charged as **1 Windows second**. Six
committed effect markers plus two attempted transaction markers used the remaining
eight row attempts. One transaction marker rolled back; the ceiling counts attempts.

Individual acceptance and evidence checks are retained in
`.codex_artifacts/p025/d5d-native-cases-acceptance-20261115.json`.

## Original offline restart checks

The one-shot isolated runner executed the **21 original offline variants**, using
their original test assertions and selected source bodies. All passed, together
with seven isolation controls. No accepted G1, custody, drain or native case was
replayed. No native operation, SQL row, provider call or new input was used.
The separate real Windows lifecycle test was explicitly excluded.

Result: `.codex_artifacts/p025/d5d-restart-qualification/result.json`.
SHA-256: `a2b54e6c53820f372999c80111f7c2b6b6c0d5dc78f8e92cb79bea74e5f4551c`.
Acceptance: `.codex_artifacts/p025/d5d-restart-acceptance-20261115.json`.
Elapsed local time: 0.625 seconds; native and Windows balances unchanged.

The runner uses the already reviewed source loader and refusal boundary, isolated
Python flags, original source/runtime hashes, create-only intent/result files,
a 60-second watchdog, bounded output and blocked additional threads. SQL, network,
provider, native and unlisted filesystem access are refused. Windows observation
uses only the original mocked API fixtures. No project startup imports or pytest
autouse fixtures are executed. Both preparation attempts contain zero behavioral
cases; the final qualification intent is consumed and cannot be reused.

## Running totals

| Behavioral group | Expected | Accepted | Pending |
| --- | ---: | ---: | ---: |
| G1 | 47 | 47 | 0 |
| G2 native | 11 | 11 | 0 |
| G3 native | 9 | 9 | 0 |
| G4 native | 4 | 4 | 0 |
| Original offline restart variants | 21 | 21 | 0 |
| **Behavioral total** | **92** | **92** | **0** |
| **Final aggregate accounting gate, separate** | **1** | **0** | **1** |

Preparation and runner-control totals are separate from the 92 behavioral cases.
This does not close wider D5e/D5f/D6 obligations or retrospectively explain the
initial job-count mismatch. Labelled maintenance-child boundary substitutions and
their original proof limits remain explicit; accepted actual-child evidence is
carried rather than replayed.

## Remaining allowances

| Allowance | Remaining | Next read-only maximum |
| --- | ---: | ---: |
| Native seconds | 1,237, including 1,000 protected | 15 |
| Windows seconds | 49 | 0 |
| Synthetic row attempts | 83/83 used; 0 remain | 0 |
| New databases | No new database needed | 0 |
| Inputs | 21 consumed; 0 new | 0 |

No extension is needed for the read-only packet. Any further row attempt requires
an approved extension. Unconfirmed observer closure retains the 15-second native
reservation; it is never refunded merely because a remote command returned.

## Permanent procedure-comparison regression

The core `K98 Bot - Coding Execution Guidelines.md`, section 7, now requires
header-only comparison for `CREATE`, `CREATE OR ALTER`, `ALTER` and keyword spacing,
including the observed three-space form. It requires raw text/hash retention,
exact name/signature/body/comment/literal comparison and separate metadata checks.
`scripts/sql_module_definition.py` supplies the reusable conservative comparator;
`tests/test_sql_module_definition.py` supplies three portable regression groups.
Body whitespace and line endings are not silently normalized. The guidance also
requires delimited diagnostic SQL aliases and forbids replay after reporting errors.

## Reviewed read-only packet

`scripts/observe_p02_d5d_postcase_accounting.ps1` is pinned at SHA-256
`4a6fae56d586a20e85d1d0d08822dd43046f88b8b87094a46b567b21f5406777`.
It checks the existing session/VM/database identities, retained packet/actor and
all 24 stdout hashes, previous observer absence, current owner absence, six fixture
tables, final aggregate counts and original preservation queries. All aggregate
aliases are delimited, including `[backup]`. It has no actor launch or mutation loop.

The packet requires the exact offline receipt hash above before displaying 92/92.
The paired handoff pins this hash and the command because the native diagnostic
receipt does not itself echo the offline receipt hash. This preserves the linkage
between the separate native and offline evidence chains.

Preparation passed 41 PowerShell 5.1 controls, three header-regression groups,
seven offline boundary controls and fixture startup checks. Critical Ruff checks,
architecture validation (225 Python files), security routing and explicit-path
test selection passed. Deferred-item validation is recorded in the final handoff.
Initial Ruff findings were missing standard-library imports in the AST-loaded
selection module; corrected imports passed and do not alter selected test bodies.
Full application pytest, startup imports, command registration and release tests
are skipped: no application, deployment or authoritative SQL source changed.
The final read-only query was checked structurally; live SQL acceptance is pending.

Changes review `050bccc0-f72f-44ed-82fb-3d82781641f6` completed with zero findings
and no concrete handoff blocker, covering all seven files, Deep off. Exact range:
`b94503b0ae27ad77b8e1f280e57321663cba6942..05fae3f8fd26640102f25b265dc86f5f8a89c2a1`.
Separate review storage preserved the ordinary branch/index. Tool-reported usage
was 1,671,072 aggregate tokens, including 1,662,080 cached input; these are rollout
counters, not incremental billing or qualification time.

Run once in the existing elevated Windows PowerShell session:

```powershell
& 'C:\discord_file_downloader\scripts\observe_p02_d5d_postcase_accounting.ps1' `
  -Session $global:D5bReportSession `
  -RunnerSHA256 '4a6fae56d586a20e85d1d0d08822dd43046f88b8b87094a46b567b21f5406777' `
  -OfflineReceiptSHA256 'a2b54e6c53820f372999c80111f7c2b6b6c0d5dc78f8e92cb79bea74e5f4551c'
```

Retain the result and intent. Do not rerun any consumed behavioral packet.
