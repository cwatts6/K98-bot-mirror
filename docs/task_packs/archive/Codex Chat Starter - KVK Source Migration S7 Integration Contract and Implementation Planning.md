# KVK Source Migration S7 — chat starter

> **Archived 2026-09-13: S7/S8A complete, smoke accepted and merged.**
> Retained preparation and approval text below is history, not instructions to execute.
> [Closeout and limits](../../reference/kvk_source_migration/s8a_closeout_and_s8b_handoff.md); [next S8B pack](../Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8B%20Bot%20Source%20and%20Matched%20Update%20Services.md).

## Current status — S7/S8A complete and merged; S8B next, 2026-09-13

S7's approved contract/manifests and S8A's SQL foundation are complete and merged.
The operator confirms successful smoke acceptance and local pulls; **no changes have
been pulled to the bot machine**. Retained S8A evidence includes six successful disposable
scripts; the later runner input fix has offline validation only. No fresh post-merge
SQL run, production runtime deployment or activation is claimed.

**Next: start S8B Bot Source and Matched Update Services in a new chat, review/scope first.**
Use the [S8B pack](../Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8B%20Bot%20Source%20and%20Matched%20Update%20Services.md) and [starter](../Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8B%20Bot%20Source%20and%20Matched%20Update%20Services.md).
Read the [canonical closeout, merge evidence and exact S8B carry-forward manifest](../../reference/kvk_source_migration/s8a_closeout_and_s8b_handoff.md).
Do not reopen settled S7 decisions or repeat S8A implementation. Further SQL execution
requires exact target/backup/row-preview/operation approval; S8B implementation needs its
own approval after scope review. Public routing remains S9 work; SourceRouting.Enabled
alone does not implement it. S6-OPS01/PERF01/CAP01, both uncertain publications and all
retained databases/files remain preserved. Earlier dated sections are historical evidence.

> S7 documentation/read-only approval was supplied and the planning outputs are
> delivered for review. This retained starter is not permission to execute S8–S11.
> [Contract](../../reference/kvk_source_migration/integration_contract_and_consumer_matrix.md);
> [exact manifests](../../reference/kvk_source_migration/integration_implementation_manifests.md);
> [validation](../../reference/kvk_source_migration/post_s6_handoff_log.md#s7-documentation-delivery-and-validation).


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
