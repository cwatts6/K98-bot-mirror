# P02 D5a.2 bounded inventory result — 2026-11-11

Outcome: **inventory incomplete; retained input custody verified; SQL metadata
and authoritative closure verification blocked by session visibility**.

One approved attempt ran at `2026-11-11T13:46:21.2270625Z` through the operator's
existing elevated Windows PowerShell 5.1 console and authenticated PowerShell
Direct session. No automatic retry or permission change followed the stop.
This is not D5 acceptance or installation/replay/rehearsal authorization.

## Observed result

| Observation | Evidence/disposition |
| --- | --- |
| Host/VM/session | Collector's exact host, VM name/GUID and session InstanceId gates passed. Post-run VM identity and zero-adapter isolation verified. Borrowed session preserved. |
| Guest | `MINI_AMD`, Microsoft Corporation, Virtual Machine. Only the expected PowerShell and SQL Server processes appeared in the bounded relevant-process census; no Python producer observed. This is not proof of all possible guest activity. |
| Retained custody | **21 files / 1,638,735 bytes** independently compared with the pinned final inventory: one ready, zero claimed, 20 archived. Every filename, size and SHA-256 matched. No input was copied, claimed, imported or replayed. |
| SQL observations | **7 statements / 3 returned rows**, limited to session settings, the current work-session identity and visibility-permission checks on work/observer connections. The target database was not inspected. |
| Stop reason | `Session visibility unavailable; no target inventory attempted`, followed by `Closure observation failed`. |
| Cleanup | Both local SqlClient disposal paths completed according to the executed control flow. Server-side disappearance remains **unverified**; the collector does not convert permission-filtered absence into proof of closure. No KILL or owner repair attempted. |
| Bounds | **1.5584887 seconds**, **11,067-byte receipt**; within the approved time, statement, row and output caps. No retry, allowance increase or settings change. |

The host summary's empty `Errors` collection did not mean success: the guest's
two errors are nested in the receipt, whose overall phase correctly remained
`inventory incomplete`. The source was checked against the exact execution
hash; no diagnostic outcome is inferred only from the displayed summary.

The observer needs visibility of the prior session to prove its absence.
The collector checked the expected SQL 2022 permission
`VIEW SERVER PERFORMANCE STATE` before target inspection and again before its
closure query; both checks refused continuation. The raw check values and fresh
server version were not retained/reached, so this receipt cannot distinguish a
denied permission from an unsupported/indeterminate permission result. Treat it
as an unestablished visibility prerequisite, not proof of the exact grant needed.
It did not issue a grant, use a fallback privileged identity, run business SQL,
or silently weaken the closure requirement. This was an observed SQL visibility gap,
not an automatic approval-review rejection.

## Preserved evidence

Raw private receipt:
`.codex_artifacts/p025/d5a2-inventory-result-6ac0bdc278b94ce6a812c6d2a6a0a726.json`.
SHA-256:
`de124a7df3233d3ef56f73b98cb74b00070aad9a122a7003cc3a978e55a55e34`.
Its hash matches the operator's displayed receipt hash.

Independent local adjudication:
`.codex_artifacts/p025/d5a2-inventory-adjudicated.json`.
Pre-execution source/manifest/test binding:
`.codex_artifacts/p025/d5a2-inventory-prepared.json`.

Collector SHA-256:
`ad0e43e7f475bd4b2f97666190aecbf6f9f8d8659403a305f41309646e64d009`.
Manifest SHA-256:
`f8fe5c5291baa5baf86502c3924d10eb48200c2dcb0d0e84f5e8e1ff82a743f1`.
Offline test SHA-256:
`b5ab7e53a0af7151866605c896078a2fb05f4476255510ce906087311667c002`.

The observer's work-session ID/login time were local variables and were not
serialized into this receipt, nor was the permission's raw return value. This
is a specific collector observability gap;
do not reconstruct or guess an ID for cleanup. A later collector revision must
retain that identity plus the visibility result before another attempt. Preserve
this executed source/receipt as the failed-attempt evidence when revising it.

Original CI/local drain failures, the SQL 3961 history, the approved drain
correction and prior readiness/setup/startup receipts remain separate and
unchanged. The
[memory-gate correction](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a2%20Memory%20Gate%20Correction%20-%202026-11-11.md)
restores the original **pre-start host** requirement; it does not reduce a limit.

## Remaining feasibility and next concrete decision

The consumed **21-input allowance is unchanged**. Matching hashes establish
custody, not fresh runnable producer work. The last accepted completed/read-only
database remains historical evidence: this attempt did not reach its current
identity/settings, module/receipt/ledger or SQL-resource observations. The fixed
193-object allowlist includes the final 174-module historical baseline; none
of those current objects was inspected in this attempt.

Before a further native attempt:

1. Identify an **existing, explicitly approved observer identity or closure
   protocol** that can authoritatively verify SQL session disappearance on this
   isolated instance. Do not add broad grants, change accounts/ownership or use
   production credentials as a convenience. If no such access exists, return a
   separate least-privilege access proposal for review; do not execute it here.
2. Prepare a focused collector amendment retaining work-session ID/login time,
   current server identity/version and the raw permission result in the receipt,
   including the operator summary's
   nested failure reason. Preserve this source and failed receipt unchanged.
   Bind and review the amendment before any further native use.
3. Return the exact identity, queries, bounds and cleanup plan for the next
   attempt. No automatic replay of this inventory is authorized by its failure.

No SQL installation, business procedure, import/export, replay, rehearsal,
reset/restore, new input, schedule/VM setting change or production/provider action
was performed by the collector. D5b–f and separate D6 remain open, including the
six real maintenance children, both-order concurrency, faults/restart and five
balanced cost pairs. This result does not provide a mutable comparable pre-state.

## Validation and review

The collector's Windows PowerShell 5.1 syntax and offline inert-command tests
passed: accounting, per-query overflow, statement/aggregate admission, expired
deadline, disposal and independent worker cancellation. All selected ledger/
receipt columns and types were checked against the authoritative SQL repo;
the six manifest queries are bounded SELECTs. Architecture/security-routing/
whitespace passed; explicit-path test selection ran. Its broad Python suite,
smoke and registration suggestions were skipped because this isolated collector
does not change application runtime. Native permission/closure behavior is now
reported above, not replaced by offline tests.

Changes scan `cefaf945-3811-4eb3-9b1e-5333e2a8f4da` completed with zero security
findings for the final pinned source, manifest and offline tests, with independent
architecture review. The earlier draft scan is separate. The scan explicitly
did not certify native readiness or permissions. For the pinned manifest, fewer
than 900 SQL rows are possible even with the column-query refusal sentinel,
below the 2,048 total limit; do not reuse that bound for an expanded inventory.

This findings document and private adjudication add no further executable change.
Their security routing is a documented documentation/evidence-only skip. All
original seven source/test/failure hashes and the final collector/test/manifest
hashes were checked unchanged during adjudication.
