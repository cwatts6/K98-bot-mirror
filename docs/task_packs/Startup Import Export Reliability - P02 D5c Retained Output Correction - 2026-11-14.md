# D5c retained-output V2 correction

The operator authorized correction, completed review and execution of the grouped batch. Preserve the original V1 packet and source bytes: it never ran and has no intent/result receipt. All previously consumed allowances remain consumed; no native allocation or retained input is used here.

## Review-record repair

Original review `6bd9b389-0a5e-4f27-b136-e1f2de3f1373` at `c94fa3920be991c31ed74c81394d4e79e5cbb979` found no security candidates and two operational blockers. The final draft was initially rejected because coverage surfaces used `title/status` instead of required `label/disposition`. Completion then failed because the saved draft was incomplete. On the operator's explicit continuation, the same review record was corrected, its final draft acknowledged, completion succeeded and the sealed result was retrieved. No replacement scan was used to hide that failed finalization.

## Exact packet corrections

1. Add exact source hashes for `services/export_snapshot_store.py` and `services/legacy_export_snapshot_dal.py` while retaining every original pin. The loader previously would have refused those reads before behavioral execution.
2. Both inert preparation-update paths now record a deterministic labelled decision timestamp. The positive assertion permits only State, Version, GenerationJson and UpdatedUTC changes and separately requires the exact timestamp. This matches the original SQL's `UpdatedUTC=SYSUTCDATETIME()` effect; immutable request, ownership, spool and execution evidence remain compared exactly.

No scenario or production body changes. All 126 fixed checks remain: 119 behavioral scenarios across three routes and seven runner controls. Original adapter, snapshot read/decoder/store path/read and final DAL bodies remain authoritative; SQL and filesystem transports remain inert. Private spool provisioning, native locking/isolation/permissions, crashes and real timestamp semantics remain outside this offline proof.

## Execution gate and accounting

Freeze the five V2 files (test, runner, preparer, packet, this plan) in an isolated review commit based on the original review head. Changes review only, Deep off; retain independent source review before one 300-second, first-failure-stop pass, with 1 MiB combined intent/result limit. Do not run the original V1. Never modify frozen evidence or reuse an intent path. Further corrections use separate versions under existing approval.

Countdown before execution: 13/73 final recovery routes accepted, 60 remaining; 25/25 inspectors accepted. If all 126 checks pass adjudication, add the three named routes for 16/73 and 57 remaining. D5c still has native and other recovery obligations and is not complete.

Balances unchanged: 1,302 native seconds with 1,000 reserved for later D5, 50 Windows-test seconds, 11/64 synthetic rows, 21 inputs consumed and zero new. No runtime correction, VM work, import, provider request, permission change or deployment. Broad repository validators remain deferred to overall handoff for the same test-only rationale recorded in the original plan.
