# D5c worker package failure and V2 continuation

The first reviewed pass stopped before case 1 with BoundaryViolation unlisted_read.
It loaded new_source_import_dal, then attempted recovery_execution_guard. The
packet omitted that file, core/sql_observation.py and services/recovery_dal.py from
its read allowlist. The earlier load-only preflight compiled definitions but did
not run with the read boundary installed; it therefore missed this packaging error.
No behavioral result is accepted. The failed intent/result and all original
packet, runner, preparer, tests and plan bytes remain untouched. The failed receipt
confirms 660 unchanged pins, no pending tasks or extra threads and zero native
operations/new inputs. This is a harness packaging defect, not a runtime defect.

## Correction and verification

V2 derives every r.load source path from the fixed test AST and adds exact SHA256
pins for the three missing sources. It asserts all selected load paths are pinned
and preserves all 660 old pins plus the original failed intent/result/packet.
The runner changes output/packet identity only and reuses the unchanged tests.
The read allowlist is not broadened to a directory or wildcard.

Before qualification, a guarded load-only preflight must install the actual audit
and import guards, compile/load the entire selected dependency closure, execute
zero cases and confirm zero boundary events. Then independently review the frozen
V2 Changes diff and complete its review before running the new create-only pass.

The operator has already approved additional bounded runs. This uses one new
pass of the same 28 scenarios plus seven controls, 300-second ceiling and 1 MiB
combined intent/result. No limit increase, new input, native operation, production
change or app startup is required. Failure stops the pass; no automatic rerun.
Balances remain 1305 native seconds (1000 protected), 50 Windows-test seconds,
11/64 synthetic rows and 21 consumed inputs. No exhausted native allowance resets.

Proof limits are unchanged: Python orchestration with inert stores and cursors;
historical locked-reread refusal, evidence-group inserts and simulated rollback.
No successful historical approval or SQL Server atomicity is established. C04,
C05 and C06 remain open. Full pytest, smoke imports and release validators remain
outside this scoped packet; no PR, promotion or runtime refactor is delivered.
