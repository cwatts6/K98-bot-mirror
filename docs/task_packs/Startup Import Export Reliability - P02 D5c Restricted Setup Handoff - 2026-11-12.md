# P02 D5c restricted setup handoff

The completed preflight is accepted with its NULL creation-authority result
preserved, not treated as permission. The corrected authority lookup must return
1 in Setup before password generation or account creation. No new preflight is
needed. Native balance remains **1,412 seconds**, restricted scope **179 seconds**,
Windows allocation **50 seconds**, and **21 inputs consumed / zero new inputs**.

The complete Setup/Positive/Finish sequence and its failure cleanup paths are
implemented, tested and reviewed before this first account mutation. Eight
offline Python tests and 164 PowerShell checks passed, including PS5.1 execution.
Architecture validation passed for 50 Python files, deferred validation for 84
documents and security routing with zero warnings/errors. Application startup,
full pytest and release/schema-repair suites were skipped for the focused
operational harness reasons recorded in the sequence plan. No runtime or
authoritative SQL source changed.

The initial complete review `3a45b03c-da7a-41cd-bd89-51aa1b937f8e` is preserved
with three pre-native correctness blockers. The correction Changes review
`aa05d09f-05cf-4164-89cb-4d0294f525dc` completed with full six-file coverage,
zero reportable security findings and independent confirmation that all three
blockers are resolved. Its sealed result was read back at
`2026-11-12T20:14:46.287948Z`. Review range:
`32b43b30ece2e1c32e66205aacd7d8ecefe17cd0` to
`43188e0f7153b65887afd0dc1d0c05625716a5fc`.
Ordinary HEAD remains `e7443e37212ca91e20d531b3684cc369d0fe1505`; isolated review
snapshots did not change the normal branch/index. Correction review measured
1,900,387 total tokens, including 1,889,408 cached input tokens. The original
complete review's separate measured usage is retained in the correction note.

## Frozen execution identities

| Artifact | SHA256 |
| --- | --- |
| scripts/run_p02_d5c_restricted_sequence.ps1 | ad9854413ce6af95ada67bfef04b254e17853c426608773ecdc1bc2561319a0b |
| scripts/p02_d5c_restricted_reader.py | aabeba76b82bb7f90fc7146bc62722706af47fe08cc809f8489b98270cf9869f |
| .codex_artifacts/p025/d5c-restricted-sequence-execution-packet.json | 4258810e35e9d573c0440772956a6c44ff379ea6fd86161d4eb609e2192c00c6 |

Manifest size 130,912 bytes remains below 131,072. Setup intent was confirmed
absent at handoff. No account, password or native setup has been created by the
agent. The existing elevated PS5.1 console holding `$global:D5bReportSession`
runs the wrapper once with `-Stage Setup`, the exact manifest and hash above.
Return summary, ReceiptPath and whole HostPacketElapsedSeconds. Stop on errors
or incomplete output, without retry or manual account changes. Cancel/report a
hang before 45 seconds. Keep the console open: subsequent stages use the guest's
memory-only credential; it is never requested in chat or written to an artifact.

Setup creates only the approved new login/user and CONNECT plus SELECT on
ExportPreparation, ExportResource and ExportExecutionStream in the disposable
copy. It runs neither reader case nor any business producer. After receipt
adjudication, Positive runs once; after its acceptance, Finish performs one
denial test and removes the exact account. If an earlier stage fails, only the
already-reviewed Finish CleanupOnly path may be handed off after evidence
review and identity/custody confirmation. No replay, password reset or deletion
of an uncertain identity is authorized.

This handoff preserves original failures, seven fixture rows, completed
maintenance, all resource/time/row caps and no-retry limits. D5c is not complete;
remaining D5 qualification and separate D6 release authorization remain open.
