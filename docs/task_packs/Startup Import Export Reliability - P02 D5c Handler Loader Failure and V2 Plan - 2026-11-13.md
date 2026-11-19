# D5c handler loader failure and V2 plan

The review-record repair and exact producer-refusal assertion correction completed.
Initial Changes review `24fc9132-d62b-4dec-bc48-096627a1df5c` and correction review
`e800f0cc-5189-44f0-80d5-bc0bb013e921` are finalized. The original review finalization
error was an unsupported repository-relative receipt reference; the semantic draft
was repaired without replacing the original scan.

The authorized single offline pass then stopped in preparation with `ValueError:
empty body on ClassDef`, before any of its 46 cases ran. The selected subclasses
`ConfigurationReadContinuationDAL` and `LegacyConfigurationContinuationDAL` have
no class constants or selected methods of their own: their record guard is inherited.
The test loader removed their other methods but failed to give the empty class a
valid Python suite. This is a test-loader defect, not a demonstrated application defect.

The failed packet, test, runner, intent and receipt remain untouched. Receipt:
`.codex_artifacts/p025/d5c-handler-safeguards/result.json`, SHA256
`cad380bd7a43fb325486c6ca1e3b0e85b71ec1ac83d1e9c9db24d716e8067d0f`.
It records 0.391 seconds, zero cases, no pending tasks/extra threads/boundary events,
and all 611 preservation pins unchanged. Independent rehashing confirmed those pins
and the intent/packet linkage. The intent and receipt total 4,743 bytes.

V2 adds only a labelled inert `pass` suite when an inherited-only class selection
would otherwise be empty. It changes no selected production method or inherited
base. The source-only preparer compiles every one of the 35 selected class ASTs
without executing them; exactly two require the scaffold. V2 keeps all 46 case IDs,
assertions, effect boundaries and limits. It uses new create-only evidence paths
and pins the entire original failed packet as well as the original evidence.

Before execution, the V2 runner/test/packet/preparer and this plan require a frozen
Changes review (Deep off). One additional offline pass requires operator approval
because the original one-pass allowance is consumed, despite zero cases running.
No automatic retry is permitted. The concrete command after approval is the existing
Python 3.11 interpreter with `-I -S -B scripts/run_p02_d5c_handler_safeguards_v2.py`.
This remains one group, capped at 300 seconds and 1 MiB combined diagnostics, stopping
at the first unexpected result. No SQL, VM, application startup, provider or retained
input work occurs. No runtime change is proposed.

Balances remain 1,305 native seconds, including the protected 1,000-second reserve;
50 Windows-test seconds; 11/64 synthetic rows; 21 inputs consumed and zero new.
D5c remains 9/12 families closed, with C04/C05/C06 open. The representative family
routes do not certify every action or close C06. Original failures and exhausted
native retry allowances remain unchanged.
