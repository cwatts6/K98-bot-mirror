# KVK Source Migration S7 — chat starter

## Current status — S7 approved; S8A pack prepared, 2026-09-12

Chris Watts approved the S7 contract and exact implementation manifests, then authorized
preparation of the next pack and starter. The approved technical direction includes initial
account serialization, durable legacy snapshots with worker affinity where needed, and the
stated quarantine/reserve allowance. Settled S7 decisions are not reopened.

**Next: S8A SQL Foundation, after separate file-implementation authorization.**
[Task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8A%20SQL%20Foundation.md); [implementation starter](Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8A%20SQL%20Foundation.md).
Preparation is documentation-only. No S8A SQL/runtime/config implementation, database
execution, Git publication or activation is authorized by this status. Preserve the full
27-path Bot carry-forward union, including both S6 archive move sides and both S7 outputs;
SQL implementation belongs in its own repository and review. Historical status blocks below
retain their original evidence; this latest status supersedes pending S7 review wording.

> S7 documentation/read-only approval was supplied and the planning outputs are
> delivered for review. This retained starter is not permission to execute S8–S11.
> [Contract](../reference/kvk_source_migration/integration_contract_and_consumer_matrix.md);
> [exact manifests](../reference/kvk_source_migration/integration_implementation_manifests.md);
> [validation](../reference/kvk_source_migration/post_s6_handoff_log.md#s7-documentation-delivery-and-validation).


Prepared 2026-09-12. Not invoked by creation. Use after explicit S7 planning approval.

I approve **S7 Integration Contract and Implementation Planning only**, following
[this pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md).
Complete its documentation/read-only scope and stop for review of the contract and
exact implementation manifests. Do not implement runtime/SQL/config changes or
execute rehearsal, predecessor, successor or live operations.

Read current AGENTS/core references, the approved architecture and EndScanID
amendment, Phase 2 implementation plan, post-S6 requirements, handoff and archived
S6 evidence. All S1–S5B and S6 evidence remain accepted. Mirror #272 and
production-repository #579 are merged; local deployment is operator-attested, not
production runtime deployment or fresh post-merge smoke.

Recheck both branches/HEADs/remotes/status; preserve all work. Entry Bot
`a2f148fa9bd4fb367fd46d0500a768c14fee915b`, SQL
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`, production/main
`a8c9c515066ca6ef079120b76dd160e3389badab` are anchors, not reset instructions.

Use settled S7-D01–D09: all affected KVK outputs use a fixed per-KVK source; matched
player + kingdom/camp pair before public publication/export; confirmed unchanged
counterpart reuse for correction; import-triggered export normally 1–2/day, peak
2–3/day; finish current then latest pending complete update; preserve accepted
input/publication history; common cross-consumer conflict protection; export-only
recovery; safe reuse of output files after each KVK without an archive requirement.
Do not re-ask these decisions. Resolve the technical contracts and exact test/file
manifests, then bring back only evidenced remaining design tradeoffs.

Preserve B0, UTC scan start, semantic deduplication, independent authoritative
aggregates/overall, daily SCANORDER and exact endpoints: 11−10, 12−10, 13−10 then
authorized EndScanID 14 permits 14−10 without another correction command. No public
routing exists merely because SourceRouting.Enabled can be updated. Carry
S6-OPS01/PERF01/CAP01 and retained uncertain publications with exact evidence.

Include every handoff path and both S6 archive move sides in the next separately
authorized slice PR, plus the two S7 Create outputs. Verify final Files changed,
or prove specific paths already merged. No commit/push/PR/merge/pull/reset,
production SQL, provider writes, real imports/exports, Discord, restart, deployment
or activation by this starter. Future required security reviews: Changes at exact
separate Bot/SQL targets, Deep off; no standard/deep scan or automatic new task.
