# D5c offline worker and group-approval packet

The operator approved preparing, testing and reviewing the 28-scenario group, with
additional bounded runs or limit extensions if needed. This packet needs no
extension: 28 behavioral scenarios plus seven runner controls, one 300-second
pass, 1 MiB combined intent/result, first failure stops. Original evidence remains
immutable. Corrections require a new preserved attempt, never an overwrite.

## Execution and scope

Runner: `scripts/run_p02_d5c_worker_groups.py`.
Tests: `tests/test_p02_d5c_worker_groups.py`.
Frozen manifest: `.codex_artifacts/p025/d5c-worker-groups/packet.json`.
Command after completed review:
`C:/Program Files/Python311/python.exe -I -S -B scripts/run_p02_d5c_worker_groups.py`.

This runs on the development host only. It needs no elevated console or VM
connection. The original no-site runner denies network, SQL/provider/native
imports, subprocesses, additional threads and writes outside create-only receipts.
Original selected function/class bodies are compiled without application startup.
Canonical/digest/document helpers and original execution/observation guards are
retained. The worker sees bounded inert pages and controlled monotonic time.

The 14 worker cases exercise accepted-repair priority, deduplication, missing
adapters, busy/failure retention, scoped cursors, automatic routing, history budget
and clean sweep, registration failure and persisted failures. The 14 membership
cases exercise exact selection and original locked DAL guards, including a change
after service verification. Only SQL transport/transaction effects are inert.
The valid control must reach labelled inserts; injected failure must discard all
staged inserts. This proves Python orchestration, not SQL Server atomicity.

## Review and preservation

Before the qualification pass, compile and load the complete selected dependency
closure without running cases. Review the frozen runner, tests, preparer, manifest
and this plan as a Changes diff, Deep off. Inspect all tool results before sealing
the review. Keep the normal Git index and branch unchanged with a review-only
snapshot. Tests are not a replacement for that review.

No runtime/SQL change or production refactor is included. Existing selected-code
loader, no-site boundary controls, source/evidence hashing and create-only receipt
helpers are reused; no new production helper or deferred optimisation is proposed.
Full pytest, smoke imports and native fixture modules are excluded because their
startup/effect scope exceeds this offline packet. No PR/promotion is handed off;
architecture/deferred/security-routing/selector release gates remain later work.

Adjudicate exact case IDs/outcomes, expected boundary refusals, physical absence of
extra threads/pending tasks, unchanged preservation hashes, complete first-failure
record and elapsed/output bounds. A failed group cannot authorize its successor.

The 21-input allowance stays consumed; this packet uses zero new inputs and zero
native operations. Balances remain 1,305 native seconds including the protected
1,000-second reserve, 50 Windows-test seconds and 11/64 synthetic rows. Existing
failed receipts and exhausted native retry allowances are not reset. The user's
broader approval is retained; any future extension must be recorded explicitly
against its own packet rather than silently changing these limits.

All 25 inspectors, the 42 orchestration cases and the combined 46 representative
handler safeguards retain their prior proof boundaries. This batch does not prove
the remaining final action routes, native C04/C05 fixtures, D5d faults, D5e cost,
D5f readiness or D6 deployment. D5c remains 9/12 families until those obligations
have qualifying evidence.
