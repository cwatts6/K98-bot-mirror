# D5c grouped capture-failure reconciliation

Preparation within the existing grouped D5 approval. No runtime correction or native work.

## Scope

Run one isolated offline pass of 159 checks: 152 behavior cases across four producer families,
both queue-capture and resume-capture recovery, plus seven runner controls. The original
adapter, reconciliation service, producer session guards, final DAL scope/ownership checks
and failure-record compare-and-set bodies execute against labelled inert transports.

The group verifies deterministic missing-output and format failures, same-action reconciliation,
foreign and stale evidence, changed scope/resources/jobs/streams, final lock refusal and failed
compare-and-set. Timeout, general transport and storage IO failures must remain uncertain;
they cannot be converted to a deterministic failure marker. Classification must preserve
committed SQL evidence, retained bytes and every reservation rather than release them.

This closes a named follow-up within already accepted routes. It does not add accepted routes:
the final-action countdown remains 32/73 accepted, 41 remaining pending additional groups.

## Reuse and proof limits

Reuse the accepted capture-resumption, capture-queue and disposition fixtures and their source
loader, with a narrow additional SQL transport for the failure marker. No production method
is replaced. Output transport faults are injected at the actual read boundary. SQL and storage
are inert; this proves orchestration and final-action validation, not physical disk durability,
native SQL locking, installation guards, provider correctness or process cleanup. Same-marker
idempotence is checked within a single scenario, not a replay of an earlier qualification run.

Ownership-only producer validation and disabled retry scheduling match the earlier offline
scope. Commit uncertainty and cleanup-custody failures still require the separate fault group.
Pipeline lineage and pipeline-owned capture failure remain separate. No new refactor or
runtime defect has been established by this preparation.

## Limits and execution

One pass, 300 seconds, combined intent/result at most 1 MiB, stop at the first failure.
Use the inherited isolated Python runner with -I -S -B; no project startup or pytest bootstrap.
Exclusive intent/result writes prevent replay and preserve original receipts. All inherited
Bot and SQL source pins plus accepted evidence are checked before and after acceptance.

Balances are unchanged: 1,260 native seconds including the protected 1,000-second later-D5
reserve; 50 Windows-test seconds; 21 inputs consumed, zero new; 11/64 synthetic rows.
No SQL/VM/provider operation, input replay, permission change, deployment or runtime edit.
No limit extension is required. No operator PowerShell command is needed.

## Review and validation gates

Changes review only, Deep off, exact isolated Git snapshot of this test, runner, preparation,
packet and plan. Independent review must finish and the canonical review must be complete
before execution. Normal HEAD/index and existing evidence remain unchanged.

The test selector is emulated: test changes would normally recommend full pytest plus startup
and command-registration gates. Those broad startup gates and PR architecture/deferred/security
routing validators remain deferred to PR readiness: this is a bounded offline qualification
group, with no production implementation change or PR handoff. The meaningful checks are the
original-body behavior matrix, runner boundary controls, static compilation, source/SQL pins,
diff whitespace and independent review. No native acceptance is inferred from them.

Acceptance must verify all ordered case identities, no unexpected boundary event, no pending
task or extra thread, unchanged evidence, receipt ceiling, actual elapsed time and review-before-
execution. On failure retain intent/result and report the exact failed boundary; corrections
use a new packet under existing approval, never overwrite or rerun the original attempt.
