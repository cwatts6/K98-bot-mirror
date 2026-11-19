# P02 D5c configuration and read-continuation group

Prepare one offline group for the five outstanding configuration retry/export-continuation routes. The starting ledger is `d5c-capture-failure-closeout.json`: 32 of 73 final-action routes accepted, 41 remaining; 25 of 25 inspectors accepted; 9 of 12 D5c families closed. Existing operator approval covers this preparation, review and one bounded pass.

## Exact scope and evidence

Use the original ConfigurationContinuation service, its read and legacy subclasses, original DAL snapshot/record/child-request bodies, original serialization, and original runtime/capture/producer-intent context managers. Reuse the pinned keep-prior memory transport and original outcome validation. The worker callback is inert: it asserts the durable marker precedes exactly one invocation and verifies the precise action, source, runtime and export intent. It performs no configuration read/publication or provider request.

The five routes are retry_configuration for configuration_continuation, configuration_read_continuation and legacy_configuration_continuation, plus continue_configuration_export for the first two. Each checks exact current evidence, scope, closed original state, registration changes, conflicting work, lost compare-and-swap, racing versions/jobs/resources, invalid actor, duplicate dispatch, lost worker observation, inherited context conflicts, saved-action mismatches, child intent and complete cleanup. Pipeline eligibility is tested with a refreshed token after removing original pipeline intent, independently of stale-token refusal. Read and legacy original-state gates receive their own cases.

The runner permits only pinned source-body loading and two create-new receipts. Network, SQL/Discord/native imports, subprocesses, additional threads, unexpected file writes and swallowed boundary violations are refused. It stops at the first failed case. The 300-second and 1 MiB combined receipt limits are unchanged. Original packets, failures, receipts and all 18 authoritative SQL file pins remain intact. Re-read ExportPreparation and ExportResource definitions: parameterized identity, state, version and ownership fields used by this model match those source definitions. The same inherited execution/membership mappings remain pinned.

No native operation, new input, synthetic row or runtime change occurs. Balances remain 1,260 native seconds, including 1,000 protected for later slices; 50 Windows-test seconds; 21 inputs consumed; 11 of 64 synthetic rows. The group cannot replenish prior one-shot allowances.

## Review and execution

Security decision: Changes review of the five-file isolated snapshot, Deep off. Include runner, tests, preparer, packet and this plan, following only directly supporting code. Review the execution boundary and correctness independently before running. Do not modify ordinary Git HEAD/index or any prior artifact. No SQL repository change is proposed.

After a complete review, run `python -I -S -B scripts/run_p02_d5c_config_continuation.py` once. Adjudicate ordered cases, all pins, receipt size, elapsed time, boundary controls and cleanup before advancing any route. Preserve a failed attempt and diagnose rather than rerunning it. Existing operator approval permits a separately preserved corrected packet if needed.

Focused execution is the deterministic test selection for this isolated test-only packet. No PR or promotion is proposed; broad architecture/deferred/routing validators and normal pytest startup are skipped because they neither exercise this bounded harness nor replace its audit controls. No new deferred optimisation item is introduced.

## Proof limits and next work

Acceptance covers original service orchestration, durable approval CAS and context/intent guards with inert SQL transport and a no-effect worker. It does not prove actual configuration publication, provider behavior, successful child-outcome reconciliation, native lock scheduling, commit uncertainty or durable storage cleanup. Successful reconciliation/reservation/child closure and native worker effects remain named follow-ups; stale and mismatched reconciliation refusals are covered here. Some malformed state mutations are defensive fixtures and also invalidate the token; they do not individually isolate every deeper validation gate.

A fully accepted group advances the final-action countdown to 37 of 73 accepted, 36 remaining **within this offline proof scope**, while C04 native consistency, C05 queue/pool/hold exclusion and C06 final-action/native effects remain open. D5 completion and deployment are not claimed.
