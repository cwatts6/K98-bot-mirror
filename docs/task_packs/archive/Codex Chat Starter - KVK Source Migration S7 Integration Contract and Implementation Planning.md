# KVK Source Migration S7 — chat starter

## Current status — S10A accepted and merged; S10B scope next, 2026-09-14

S10A SQL #85 is merged and locally pulled at `3776dfa6b0892a8800d236fdf111c4d2f93c3813`.
All five disposable fixture modes, 76 unique cases in install and constraints, direct apply/rerun,
backup/actual restore and final preservation checks passed; final CI passed. Results accepted.
No changes have been pulled to the bot machine; no production SQL deployment or activation.
S9B mirror #277, production #584 and SQL #84 remain delivered. Bot comparison anchors are unchanged.

Next: **S10B Shared Export Coordination Worker and Durable Budget, initial review/scope only**.
Use the [S10B task pack](../Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10B%20Shared%20Export%20Coordination%20Worker%20and%20Durable%20Budget.md) and [starter](../Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10B%20Shared%20Export%20Coordination%20Worker%20and%20Durable%20Budget.md).
The [S10A closeout and exact carry-forward manifest](../../reference/kvk_source_migration/s10a_implementation_and_s10b_handoff.md) controls delivery.
Completed S10A and S9B packs/starters are archived; retained execution/operator evidence stays available.
Every pending Bot document and archive destination belongs in the eventual S10B implementation PR.
Check exact filename AND previous_filename, with explicit absent-at-base proof for never-committed
S10A source paths. No standalone documentation PR or repository mixing; grouping is settled.
Both mandatory SQL delivery documents were included and merged in SQL #85.

Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and all retained databases/files.
S8B accepted smoke/50-case and actual-restore evidence remains distinct from offline runner history,
S8A six-script evidence and S8C seven local checks; S8C is not live Discord acceptance.
No S10B implementation, Git publication, runtime execution, deployment, activation or automatic new task
is authorized by this closeout. SourceRouting.Enabled alone never enables source activation.
Earlier dated checkpoints below are historical.


## Historical S8B closeout status — 2026-09-13

S8B is complete, operator accepted, successfully smoke tested and delivered through merged
production #581 and SQL #81. Local pulls are complete; **no changes have been pulled to the
bot machine**. Mirror #274 is closed without a merge record; its delivered content is verified
in synchronized mirror main. See the [canonical closeout and exact carry-forward manifest](../../reference/kvk_source_migration/s8b_closeout_and_s8c_handoff.md)
for merge/content proof, final offline tests and the distinct historical disposable/runner evidence.
No fresh post-merge SQL or bot-machine smoke, deployment or activation is claimed.

**Next: S8C Intake and Admin Pairing UX in a new chat, initial review/scope only.**
Use the [S8C pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8C%20Intake%20and%20Admin%20Pairing%20UX.md) and [starter](Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8C%20Intake%20and%20Admin%20Pairing%20UX.md).
The eventual separately authorized S8C Bot PR must include all closeout documentation and both
sides of both S8B archive moves, checking actual filename and previous_filename; SQL delivery-log
carry-forward is separate. S7 decisions and predecessor acceptance remain settled. S9 public
routing and S10 export coordination remain later work; SourceRouting.Enabled alone is insufficient.
Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and all retained databases/files.
Earlier dated scope/approval/next-slice statements are historical and do not reopen accepted work.

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
