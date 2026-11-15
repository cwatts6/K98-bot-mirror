# D5c capture-failure reconciliation acceptance

The single reviewed offline pass passed all **159 checks**: 152 behavior cases and seven
runner controls. The named deterministic failed-capture reconciliation follow-up is accepted
within the original-body, inert-transport scope. No runtime implementation changed.

## Countdown

- Final-action routes: **32/73 accepted; 41 remaining**. This group closes a known gap in
  accepted capture routes and does not count those routes again.
- Inspector checks: **25/25 accepted**.
- D5c families: **9/12 closed**. C04 native season/routing/weight consistency, C05 native
  queue/pool/hold exclusion and C06 remaining final-action/native effects remain open.
- D5d fault/restart/custody, D5e balanced cost qualification and D5f final readiness remain.
  Deployment is the separate D6 gate.

## Accepted behavior and limits

Four producer families were checked for both queue-capture and resume-capture reconciliation.
Deterministic missing-output and format exceptions receive the exact action's failure marker
only after original producer exclusion, scope and ownership validation. Records, reservations,
committed SQL evidence and retained bytes are preserved. Same-action reconciliation performs
no second output attempt or marker write. Stale/foreign evidence, competing work, conflicting
ownership, guard refusal and failed compare-and-set preserve state. Timeouts, general transport
errors and uncertain storage IO propagate without a deterministic failure marker.

Faults were injected into inert output/file transports. This is not proof of actual parser
failure production, native SQL scheduling, physical cleanup, filesystem durability, installation
validation or pipeline lineage. Some conflicting rows deliberately represent malformed evidence
that SQL constraints would prevent; they prove defensive refusal, not native race reachability.
Commit uncertainty and cleanup-custody faults remain separate. Earlier proof qualifications and
every original failed receipt remain preserved.

## Evidence

- [Packet](../../.codex_artifacts/p025/d5c-capture-failure/packet.json), SHA256
  `6b118133a6b9012936eee2203e3c28760b0f59fc0076780fc25aacb112ae420b`.
- [Result](../../.codex_artifacts/p025/d5c-capture-failure/result.json), SHA256
  `a219d7ac9003473414a099b99b7fbe7fe3eb636a9ee9961f3334fdea630e9058`.
- [Acceptance](../../.codex_artifacts/p025/d5c-capture-failure-acceptance.json) and
  [current countdown](../../.codex_artifacts/p025/d5c-capture-failure-closeout.json).
- 0.594 seconds; 33,938 combined intent/result bytes, below 300 seconds and 1 MiB.
- 871 preserved-source/evidence pins and 18 SQL source pins verified unchanged.
- No unexpected boundary event, pending task, extra thread or captured output.
- Normal Git HEAD/index and all five reviewed file hashes unchanged.

Changes review `d206a48b-682e-4127-ad78-6136e8cbd807` completed with zero findings and
independent review ready. Base `350fe9da625bae23afab9b408fb08a2b7a90515b`, head
`2d89d2ee28e7e190c2e3ed5682ee98c892cc92db`. The review was sealed at
`2026-11-14T20:18:29.239405Z`, before execution. Reported review usage: 4,350,949 tokens
(4,344,617 input, including 4,243,200 cached; 6,332 output; 852 reasoning output).

## Preserved allowances and continuation

Native allowance remains **1,260 seconds**, including the protected 1,000-second later-phase
reserve; Windows-test allowance **50 seconds**; inputs **21 consumed, zero new**; synthetic
rows **11/64**. One offline pass consumed for this group, zero native operations, no extension.

Continue with grouped configuration/read-continuation final-action checks and their exact
original-body dependencies. The remaining native fixture and queue/pool/hold proofs require
separate reviewed packets; do not change the retained canonical owner or repeat accepted work.
No PowerShell batch is ready or required for this completed group.

Full pytest/startup imports/command-registration and PR architecture/deferred/security-routing
validators remain deferred to PR readiness for the reasons recorded in the reviewed group plan.
This handoff is neither a PR readiness claim nor deployment approval.
