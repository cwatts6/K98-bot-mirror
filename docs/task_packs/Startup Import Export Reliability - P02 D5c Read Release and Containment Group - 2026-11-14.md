# P02 D5c grouped configuration read release and containment

## Scope and existing authorization

Prepare, independently review and execute one bounded offline pass for `configuration_read/release_read` and `configuration_read/contain_read`. The user's continuing approval covers this group and related packet corrections. Preserve every predecessor receipt, all consumed allowances and all runtime files. Current ledger: `d5c-continuation-outcomes-closeout.json`, 37/73 final-action routes accepted, 36 remaining; 25/25 inspectors; 9/12 D5c families closed.

## Behavior and boundaries

Exercise the original adapter, authority investigation/apply, recovery validation, closed-stream verification, typed read-ledger containment, private receipt verification and final preparation/resource DAL compare-and-set. The three profiles are a privately closed empty abandoned read, a frozen read requiring containment, and an unstarted read without a stream. Cover exact ownership/membership, registration, stale decisions, actor/reason bounds, unexpected data, lost compare-and-set, atomic rollback after partial mutation, acknowledgement loss followed by reconciliation, and no repeated settlement after restart. All five allowed typed read-event prefixes are included for containment. Seven runner controls deny network, SQL/native/Discord imports, subprocesses, outside writes and swallowed active-work violations.

SQL transport, transaction durability, private storage and process closure are explicitly inert. The original stored procedure is source-validated; its returned transition is modeled, not executed. Authority process-closure recovery is a no-op and does not prove OS custody. Closure-byte verification uses the original verifier but a labelled private document. Release-with-provider-read payload verification and queue/continuation delegation are outside this group. Containment proves dispatch fencing intent and discarded results, never provider health or process termination. Native locks, privileges, actual commit uncertainty and physical durability remain separate. Invalid fixture states are defensive, not assertions that SQL constraints permit them.

## Fixed limits and evidence

Use the existing isolated `python -I -S -B` runner design, 300-second total and 1 MiB combined intent/result ceilings, first failure stops, create-new receipts only. Freeze the ordered case list and all source/evidence hashes before review. No SQL/VM work, input consumption, provider requests, runtime correction or synthetic-row additions. Preserve 1,260 native seconds (including the protected 1,000-second later-D5 reserve), 50 Windows-test seconds, 21 consumed inputs and 11/64 synthetic rows. No extension or replenished native retry allowance is used.

The runner and packet live at `scripts/run_p02_d5c_read_release.py` and `.codex_artifacts/p025/d5c-read-release/packet.json`; behavioral cases at `tests/test_p02_d5c_read_release.py`. Copy the runner only under the new identity; never modify a previously pinned packet. Admission requires completed review and unchanged hashes. Accept only the frozen ordered pass, all preservation pins, expected boundary events and cleanup. A failure keeps its original intent/result and does not advance the countdown. If both routes pass adjudication, the countdown becomes 39 accepted / 34 remaining; D5c family closure is not automatic.

## SQL and test selection

Read authoritative `C:/K98-bot-SQL-Server/sql_schema` contracts for ExportPreparation, ExportPreparationResource, ExportResource, ExportExecutionStream, ExportProviderRequest/Event and usp_ExportExecutionStreamTransition. Validate exact ownership columns, stream action parameters, original-session identity, typed read operations/events and transaction coupling. No schema change or SQL repository diff is proposed. Include these contracts in the source pins.

Reuse the frozen isolated runner and original source bodies; do not create application helpers or refactor runtime code. The independent fixture is necessary to model this distinct multi-resource settlement and verify partial rollback rather than borrowing unrelated producer fixture behavior. No new runtime deferred item is identified. Existing unresolved native and downstream obligations remain in the ledger.

Test selection is emulated for the two new test/tool paths: a general selector recommends full pytest and startup/registration smoke checks, but those are skipped for this bounded qualification-only change because they import application/bootstrap code and expand beyond the inert boundary. Architecture/deferred/security-routing validators are deferred to PR handoff; this is no PR or promotion. Compile selected bodies and review the exact packet statically before the one behavioral run. Record the bounded result rather than treating static compilation as behavioral evidence.

Security decision: Changes review, Deep off, exact five-file review snapshot (test, runner, preparer, manifest and this plan). Review filesystem/import guards and allowed source execution, actual handler/DAL bindings and honest acceptance claims. Use the supplied canonical historical threat model unchanged with its scope limitation, plus repository SECURITY.md. No codebase scan or production review is requested. Review completion precedes behavioral execution.

## Next step

Offline execution is performed by Codex after review; no PowerShell handoff is required. Continue to the next grouped final-action routes after recording this group's adjudication. D5d/D5e/D5f and separate D6 release remain outside this acceptance.
