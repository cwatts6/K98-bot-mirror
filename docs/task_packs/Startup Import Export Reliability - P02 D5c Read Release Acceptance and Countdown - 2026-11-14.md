# P02 D5c read-release and containment acceptance

The corrected grouped offline pass completed **146/146 checks**: 139 behavioral cases and seven runner controls. Both `configuration_read/release_read` and `configuration_read/contain_read` are accepted within the original-code, simulated-transport scope below. The final-action countdown is **39/73 accepted, 34 remaining**. Inspector checks remain 25/25; D5c family closure remains 9/12. D5c is not complete and this is not deployment acceptance.

## Evidence and review

- [Frozen V2 packet](../../.codex_artifacts/p025/d5c-read-release-v2/packet.json), SHA256 `9014923efbe06b94d74e89a56d7a194f158940ba11eaddda56f808601d0e0bd5`.
- [One-pass result](../../.codex_artifacts/p025/d5c-read-release-v2/result.json), SHA256 `e5a6b0629da86dc0f1d33ba90e2215cc240b54770a98d7079ccd3bb5a33f9dac`.
- [Adjudication](../../.codex_artifacts/p025/d5c-read-release-acceptance.json) and [current countdown/remaining obligations](../../.codex_artifacts/p025/d5c-read-release-closeout.json).
- Changes review `5dd0e50c-93b2-458f-9c7d-b1a4b77d42ac`, Deep off, frozen five-file range `2b52dd9823fc3cc4237f3cdd2b135093348b13b9..b2c6ea488aabf2489b55b92ed4f7aab9026c9409`; completed before execution, no reportable security findings or remaining execution blockers. Parent and independent reviews included tests and documentation.

Independent review found an extra-stream fixture mismatch in V1 before execution. V1 remains frozen and unexecuted. V2 assigns a conflicting owner to the additional stream so original validation refuses it before the single-stream test transport is used. No application guard or runtime code changed. Original review and snapshot-preparation failure evidence remain preserved.

The accepted pass took 0.516 seconds against 300 seconds and produced 21,943 combined intent/result bytes against 1 MiB. All 909 preservation hashes, 23 authoritative SQL source hashes and five frozen review-file hashes matched afterward. The ordered results and seven expected boundary refusals matched the packet. There were no unexpected boundary attempts, pending tasks, extra threads or captured output. Ordinary Git HEAD and index remained unchanged. No extra pass was run.

## Scope and limits of proof

The checks exercised original adapter, authority, service, closure-verification, containment and final preparation/resource update code. They covered approved release, safe containment, unstarted reads, stale/foreign claims, partial-update rollback, modeled lost acknowledgement and reconciliation without repeated settlement. All five supported read-event prefixes were checked for containment.

SQL, private storage and transaction effects were simulated. The containment procedure was checked against authoritative SQL source but never executed. This does not qualify native locks, permissions, physical durability, actual lost acknowledgements, provider payload release or process custody. `reconcile-settled` repeats the valid setup; 146 distinct case identifiers do not imply 146 independent branches. Some changed-state refusals also invalidate the snapshot token and do not isolate every deeper gate. These limitations and all inherited obligations remain in the current closeout.

No SQL/VM operations, new inputs, new synthetic rows, provider calls, permission changes or runtime corrections occurred. Allowances remain: **21 inputs consumed, zero new; 1,260 native seconds including the protected 1,000-second reserve; 50 Windows-test seconds; 11/64 synthetic rows**. No limit extension or replenished native retry allowance was used.

## Remaining work

The 34 final-action routes comprise 14 export-job routes, 10 rollover routes, four private-evidence routes and six remaining report/producer/pipeline continuation routes. Continue these in reviewed offline groups without replaying accepted work. Named downstream and native proof gaps stay open alongside this route count.

The three open D5c families remain C04 native season/routing/weight consistency, C05 native queue/pool/hold exclusion and C06 remaining final actions/native effects. Later D5 slices and the separate release stage remain outstanding. No PowerShell step is required for this completed offline group.
