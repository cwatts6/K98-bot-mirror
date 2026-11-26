# D5d verified poststate and unfinished native continuation

## Accepted read-only diagnostic

The saved diagnostic receipt
`d5d-grouped-diagnostic-result-f78578827631465ab994794d68e17a79.json`
matches SHA-256
`a0a1a9398bc77da5abfcfcc20849c2310a62205041ff7e3d96615ebb404e9c87`.
It has no host or guest errors, reports all 63 original preservation comparisons
passed, confirms no Python actors or prior SQL observer/application owners remain,
and independently verifies the diagnostic observers' closure. The final collector
close acknowledgement remains a distinct acknowledgement, not recursive proof.

DB10 `K98_P025_D5d_Fault_20261115`, birth `2026-11-15 10:31:04.697`, remains the
approved disposable database with its expected safety options. All six maintenance
rows are pending generation 1 without claims, completion or error; the one
configuration row has DueRows/LastBatchRows 1; the backup row remains requested
generation 0. MaintenanceKvkWork, D5dEffect and D5dTransactionMarker are empty.
These exact row preimages are frozen for continuation. No seed is reset or
recreated. DB7 remains read-only/restricted; DB8 and DB9 preserve their accepted
identities and data. The original database, source packet, actor, guest result,
empty stdout/stderr files and absent assignment gate remain evidence.

The diagnostic took 0.7321521 host seconds and charged one second. Combined with
the failed packet's two-second charge, the native balance is now **1,245 seconds**.
Windows balance remains **50 seconds**; the later-phase reserve remains **1,000**.
Inputs remain **21 consumed, zero new**. Row accounting is verified at **75 of 83
attempted**, with **eight reserved** for unfinished marker/transaction cases.

## Failure cause and uncertainty

The immediate stop was the harness condition `Active(job) != 1`, after its
assignment call and before publishing the actor's assignment gate. That condition
does not establish that the actor was absent: the original packet recorded neither
the actual count nor exact membership, process signal or exit code at that point.
Both retained output files are empty. The earlier suggestion that the child had
already exited was an inference and is withdrawn. An underlying kernel/accounting,
console-child or startup explanation is **not proven** and is not labelled fixed.

The confirmed harness defects were nondeterministic running-process admission and
insufficient launch evidence. The continuation starts its exact child suspended
and without a console window or inherited handles, checks the exact process handle
with IsProcessInJob, checks unsignalled state and expected accounting, verifies its
actual TokenUser SID, publishes the bound gate and only then resumes its primary
thread. Membership, counts, token SID, birth, exit and bounded file output are
retained even when admission or a case fails. The admission count requirement is
not relaxed. A further mismatch stops the packet with concrete evidence.

This follows the documented purposes of
[IsProcessInJob](https://learn.microsoft.com/en-us/windows/win32/api/jobapi/nf-jobapi-isprocessinjob),
[CreateProcessW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw)
and the [suspended/no-window creation flags](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags).
Those API contracts do not retrospectively prove the reason for the first mismatch.

## Running totals

| Behavioral group | Expected | Accepted | Pending |
| --- | ---: | ---: | ---: |
| G1 | 47 | 47 | 0 |
| G2 native | 11 | 0 | 11 |
| G3 native | 9 | 0 | 9 |
| G4 native | 4 | 0 | 4 |
| G4 original offline restart variants | 21 | 0 | 21 |
| **Total** | **92** | **47** | **45** |

One failed native packet and one completed read-only diagnostic do not add accepted
behavioral cases. Original G1/D5c, custody and drain evidence is carried unchanged.
The continuation retains all 24 original native IDs. If all are independently
accepted, the total becomes 71/92; the 21 original offline restart variants still
remain, and broader D5d/D5e/D5f/D6 closure is not implied.

## Frozen continuation and scope

- Runner: `scripts/run_p02_d5d_continuation_packet.ps1`.
- Runner SHA-256: `b2c8d949aaaefa9223c253a386f8c6d389ac9ead58f7c39e0574440ebb82c2ca`.
- Manifest: `.codex_artifacts/p025/d5d-continuation-packet.json`, 172,105 bytes.
- Manifest SHA-256: `63d18a347aafe6b171e1fe15094907471a940b4d10da8bbf2a03cf7459a4edf7`.
- Fresh evidence directory only: `Q:\D5dContinuation-20261115`.
- Existing DB10 and its eight seed rows are reused; **no DDL or seed reset** runs.
- Nine existing procedure definitions and exact seed preimages are compared before
  cases. The previous guest evidence hashes/absence are checked again.
- 240-second native and 40-second Windows ceilings remain; after full reservation,
  at least 1,005 native seconds including the protected 1,000 remain. No extension
  is needed. The remaining eight attempted rows include the deliberately rolled-back
  transaction marker; no input is added.

Original packet sources and artifacts are preserved; separate continuation files
are necessary because frozen originals are evidence. AST comparison proves all
original behavioral functions/classes unchanged. Only actor entry/output handling
and the fresh evidence directory differ. The same labelled maintenance fault
substitutes remain; prior actual-child correctness is carried, not replayed.

Host custody and the full reservation are retained before remote dispatch until an
explicit physical-closure result is returned. A completed remote command alone
does not release either. Uncertain process, token, job or SQL cleanup sets a native
uncertainty flag. Failed actors also require absence of their unique SQL application
identity. No observers means no extra closure connection; an unbound observer
cannot be cleared by an empty birth list. Empty job creation transfers its handle
to the parent before limits are configured, so configuration failure keeps cleanup
owned. No automatic retry or evidence deletion is introduced.

## Preparation and review

Latest preparation: **4 Python groups and 66 Windows PowerShell 5.1 controls passed**.
These controls include unchanged behavior-body comparison, bounded create-new
output, retained startup errors, frozen consumed-row accounting, wrong identity
refusal, native cleanup uncertainty despite remote completion, one-shot refusal,
monotonic/UTC limits, and x64 native structure compilation/layout checks. They do
not call the native process/job APIs or execute SQL/VM qualification. Original
12 Python/45 PowerShell and diagnostic 26-control results remain separately carried.
The intermediate PowerShell preparation failure was a missing inert test-fixture
variable; its output remains retained and the corrected test passed.

Initial six-file Changes review: `128b00e7-579b-4911-b779-7871f92586fa`,
snapshot `11f62bac6a85d32ff778c3a5aeeeb28ddec0e662`. It found no reportable security
vulnerability but withheld handoff for physical-retention and actual-token checks.
Final three-file correction review: `9a4b2ba9-73de-468d-9f88-ac9c93d775c9`,
snapshot `8a05c7ad0713ad37cdd2b9137a2eed677032eb70`; complete, both blockers resolved,
no reportable security finding or remaining concrete handoff blocker. Deep was off.
Separate review indexes/unreferenced commits preserve the ordinary branch/index.

Ruff critical-error checks and explicit-path test selection passed. Broad pytest,
smoke/registration and release checks are skipped for qualification-only tooling:
no production module, registration, deployment or SQL source changed. Native
acceptance is still an operator receipt/adjudication step. No unrelated refactor
or deferred optimisation is introduced.

Final manifest bootstrap passed for all 15 selected modules with zero native
cases. Architecture (217 Python files), deferred-item (218 Markdown files) and
security-routing checks passed. Final source/evidence hash verification is recorded
in the continuation handoff receipt; no native continuation intent exists yet.

Tool-reported aggregate review counters: initial 2,620,066 total tokens (2,600,064
cached input); correction 1,383,968 (1,379,072 cached input). These are rollout
counters, not incremental billing, additive estimates or qualification time.
