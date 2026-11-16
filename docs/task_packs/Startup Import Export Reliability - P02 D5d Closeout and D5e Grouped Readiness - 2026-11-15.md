# P02 D5d closeout and D5e grouped readiness

## Accepted receipt and final accounting

The read-only receipt `d5d-postcase-accounting-result-00bc40373de54c1c8f8ad6b18797caa0.json`
matches SHA-256 `dfcff82159f0cf425673dde9298bc50a96e0e76d2f06084d7fddd0f282e43969`.
Its final fixture counts are maintenance 6, configuration 1, backup 1, effects 6,
and committed markers 1. The committed marker is `commit_lost`; the rollback
marker is absent. The intentional failed maintenance rows and unknown backup
claim remain retained, with their original generations and errors. These states
are expected fault-test evidence, not pending work to repair or retry.

Both receipt error lists are empty. All four exact collector births closed,
the final collector acknowledged disposal, and no prior actors/observers remain.
The database identities, isolation, 24 stdout hashes and original preservation
checks match. Host adjudication separately verified 2,403 G1 preserved files,
61 packet pins, seven authoritative SQL pins and all 14 previous handoff pins.
No original source, failed receipt, intent or accepted packet was rewritten.

Acceptance is recorded in
`.codex_artifacts/p025/d5d-final-accounting-acceptance-20261115.json`.
The host-only adjudicator is `accept_d5d_final_accounting.py` in that directory;
it performs no native or application operation. The previous accounting defect
was the unquoted `backup` alias after all 24 native cases completed; the read-only
follow-up closes that accounting gap without replay.

## Counts and allowances

| Tracked scope | Completed | Expected | Remaining |
| --- | ---: | ---: | ---: |
| D5d G1 | 47 | 47 | 0 |
| D5d G2 native | 11 | 11 | 0 |
| D5d G3 native | 9 | 9 | 0 |
| D5d G4 native | 4 | 4 | 0 |
| Original offline restart variants | 21 | 21 | 0 |
| **D5d behavioural subtotal** | **92** | **92** | **0** |
| D5d final accounting, separate | 1 | 1 | 0 |
| Next D5e readiness group | 0 | 7 | 7 |
| **Currently fixed checks including readiness** | **93** | **100** | **7** |

All four D5d groups are closed within their documented proof limits. D5a–d are
accepted; D5e measured costs and D5f integration closeout remain open. This table
is the current fixed D5d/readiness denominator, not an invented all-programme test
count. Preparation controls are separate. The future cost schedule requires two
warmup arms and ten measured arms; none has run or been accepted.

The receipt elapsed 0.3413763 seconds, charged as one native second:
**1,237 → 1,236 native seconds**. Windows remains **49 seconds**. All **83/83
synthetic row attempts** are consumed, with 82 durable rows and one rolled-back
attempt. The 21-input allowance remains consumed; no new input was used. The
previous one-database extension has been consumed by the preserved D5d database.

The protected 1,000-second later-D5 reserve is retained within 1,236. This readiness
packet reserves at most 20 of the 236 seconds above that reserve. No Windows,
row, input, database, storage-size, permission or timeout extension is requested
for this packet. Unconfirmed closure retains the reservation rather than refunding
it. Future D5e cost setup needs a concrete authorization decision; the packet
only collects the facts needed to specify it and cannot create a copy or demand.

## Shared reserved-identifier regression

The existing ROWCOUNT incident reference is
`docs/reference/kvk_source_migration/s11_attempt_part_sql_syntax_20261007.md`, with
the emitted-DAL regression in `tests/test_export_attempt_sql_syntax.py` and a
preview alias regression in `tests/test_kvk_source_window_preview_sql.py`.
The S11 reference and the same test module now cover BACKUP too. New pure source
assertions read the actual PowerShell queries and require delimited aliases.
The core Coding Execution Guidelines already require `[backup]`, header-only
procedure comparison and no replay after accounting failure; their accepted
bytes remain unchanged. The shared incident reference links that core rule.

Two new source assertions plus eleven negative/missing-query controls passed
(13/13). Bare aliases fail with mixed case, multiple spaces and tabs. These are
offline regressions, not a general SQL grammar parser. The existing development
compiler opt-in remains disabled on MINI_AMD. The new read-only native packet
separately uses `sys.sp_describe_first_result_set` for its exact SELECT containing
both `[RowCount]` and `[backup]`, then executes only that SELECT.

## Next grouped packet

`scripts/observe_p02_d5e_grouped_readiness.ps1` uses the same borrowed, exact
PowerShell Direct session and zero-NIC qualification VM. It accepts only the
session and its frozen runner hash. The D5d accounting acceptance and receipt,
old catalog packet, source pins and prior actors' evidence are all required.
Its fresh create-only intent prevents automatic retry. It uses seven groups:

1. Exact host, VM, SQL, database, volume and resource identities.
2. Existing retained-copy logical files and sizes, proposed cost-target database
   and path absence. No backup, restore, copy or creation is performed.
3. Current retained maintenance/configuration/backup/KVK ledger and source-row
   provenance, to determine fresh demand and fixture requirements.
4. Complete raw definitions and execution metadata for the actual six children
   and maintenance dispatcher, without executing any child.
5. Report dependency catalog, raw module definitions, log use and version store.
6. Bound metadata compilation and a read-only count using both reserved aliases.
7. Preserved accepted preimages, absent old actors and exact collector closure.

The script reports behavioural `Completed/Expected` as the retained 92/92 and
`ReadinessCompleted/ReadinessExpected` separately as up to 7/7. Collection is not
cost acceptance. Raw definitions are retained for comparison against authoritative
SQL source; merely finding a definition is not approval of its body.

Its limits are 20 host native seconds reserved, a 15-second guest envelope,
two-second SQL commands, zero lock wait, 180 operations, 512 returned rows and
a 1 MiB receipt. Host C: and guest C:/Q: retain 8 GiB free; version store remains
below 512 MiB. Log use is collected for the later optional-statistics gate, not
used to run statistics. The original pre-start host-memory requirement is not
reinterpreted as a new post-start requirement.

## Cost continuation prepared for adjudication

Carry the original same-candidate, same-data workload and report equality gates.
Use equal OFF/ON warmup, then five measured pairs with alternating first arm:
OFF/ON, ON/OFF, OFF/ON, ON/OFF, OFF/ON. Only the reviewed observation condition may
differ. The future executable manifest must bind each fresh request/generation,
observer schedule and per-arm ceiling after the readiness receipt establishes
the real current fixture and copy requirements.

Actual maintenance, each report stage, physical cleanup and observer cost belong
inside the eventual timed interval. Preserve raw output evidence and apply the
existing exact equality policy, including documented clock/tie handling. Overall
median ON must be <= OFF * 1.20 + 1,000 ms; each report-stage median ON must be
<= OFF * 1.20 + 250 ms. Missing/failed/skipped arms are not zero-duration passes.
Do not reuse the consumed D5c demand/claim, reset a source database, dispatch a
backup job or mutate an accepted D5d fixture. No cost run is issued here.

## Preparation and review

PowerShell 5.1 preparation passed 46/46 controls: inherited receipt/path/query/
closure boundaries, unique readiness counts, correct allowances, delimited aliases,
bound compiler parameters, absent mutation/actor commands and receipt comparison
with real SQL DateTime/Guid shapes. An initial local test-fixture conversion
misread a DateTime as text; the fixture was corrected and the controls passed.
No native operation or allowance was consumed by preparation.

Architecture validation, deferred-item validation, security-routing validation,
explicit-path test selection, critical Ruff checks and frozen-diff whitespace
checks passed. Ruff used the existing repository `.venv` after the system Python
reported no Ruff module. Broad pytest, smoke imports, registration and release
tests are skipped because they would start unrelated application fixtures; no
application runtime, release identity, authoritative SQL or registration changed.
The exact new source assertions ran through an isolated standard-library AST
selection, without application imports or accepted-case replay.

The reviewed source range and final review result, file hashes, test evidence and
command are recorded in the create-only
`.codex_artifacts/p025/d5e-readiness-handoff-20261115.json`.
D6 production readiness/deployment remains separate. No new deferred optimisation
item is introduced; D5e and D5f retain their existing programme obligations.

Changes review `2f7af21f-e3e3-4844-8af1-32f68875b2ab` completed with zero reportable
findings and no concrete handoff blocker across all four changed files, Deep off.
Frozen range: `05fae3f8fd26640102f25b265dc86f5f8a89c2a1..f2f9fa7d85f0aa073a5b71c4f1086dc93f544dcb`.
The separate review snapshot preserves the ordinary branch and index. Tool-reported
usage: 1,169,764 aggregate tokens, including 1,153,152 cached input; these rollout
counters are not incremental billing or qualification time. Live catalog availability
and query duration remain unverified until the one-shot receipt is adjudicated.

Run once in the existing elevated Windows PowerShell 5.1 console on 9SX2VF4,
using the existing `$global:D5bReportSession` object (instance
`b09386eb-cc29-40b3-8f31-75636e9fe3da`). Do not reconstruct the session by numeric ID.

```powershell
& 'C:\discord_file_downloader\scripts\observe_p02_d5e_grouped_readiness.ps1' `
  -Session $global:D5bReportSession `
  -RunnerSHA256 'af5c738c4b794c87950d8dfb558ae6153b2078480b94dc079414e811f2948019'
```

Retain the resulting receipt and fresh intent. Any incomplete result is reviewed
without automatically rerunning the packet. This handoff authorizes no cost
workload or further database/fixture mutation.
