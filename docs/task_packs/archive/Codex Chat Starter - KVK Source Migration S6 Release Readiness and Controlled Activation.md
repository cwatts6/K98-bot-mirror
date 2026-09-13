# Codex Chat Starter — KVK Source Migration S6 Release Readiness and Controlled Activation

> **Archived 2026-09-12: S6 evidence delivery is merged and operator accepted.**
> This pack is retained history, not executable instructions. Public routing and
> residual release gates remain open; no activation is claimed.
> Next: [S7 planning](../Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md). Exact closeout: [handoff](../../reference/kvk_source_migration/post_s6_handoff_log.md).

> **2026-09-12 S6 authenticated rehearsal update:** The operator restored the ignored
> local credential and approved the 5,806-player × ten-period synthetic benchmark,
> confirming both other importers would remain idle. Actual Google write/readback
> and local K98DEV rehearsal evidence now supersedes the earlier credential blocker.
> S6-OPS01, S6-PERF01 and S6-CAP01 remain OPEN for operator acceptance and the exact
> unresolved operational gates recorded in the latest appendix of both release
> documents and the S6 pack. No production activation or G5 acceptance is claimed.


> **2026-09-12 S6 output-provisioning update:** Separate S6 output creation was
> approved and completed: one private index and eight private slots, owner and
> service-account Editor metadata verified. Operator expectation is 2–3 exports/day,
> with no fixed maximum duration. Code review found no common lock across S6,
> all-KVK export and scan-data import. Runtime Google rehearsal is currently blocked
> by the missing configured local service-account key; no provider interruption or
> representative-load pass is claimed. All three S6 gates remain OPEN. See the latest
> provisioning appendix in the two release documents and S6 pack.


> **2026-09-12 S6 rehearsal update:** Chris Watts subsequently approved a local
> K98DEV database and beginning rehearsal. Synthetic local SQL/process checks passed
> in `K98_S6_Disposable_20260912`; no production activation occurred.
> S6-OPS01, S6-PERF01 and S6-CAP01 remain OPEN pending provider evidence and operator
> acceptance. Earlier G3-only/no-rehearsal statements below describe the retained
> preparation checkpoint, not the subsequent local rehearsal. See the dated
> rehearsal appendix in both S6 release documents for exact outcomes and gaps.


> Current 2026-09-12: explicit S6 G3 approved documentation/evidence preparation only.
> Prepared release evidence; stop at G4, with OPS01/PERF01/CAP01 open and G5 operator-owned.
> Historical prepared/pending wording below is retained as the original template, not current status.
> See [canonical S6 delivery](../../reference/kvk_source_migration/release_evidence_log.md).


Prepared 2026-09-09 during Phase 2B. **Not executed; S6 G3 pending.**
Use this only when approving this slice; G2 alone does not approve implementation.

---

I approve G3 for **KVK Source Migration S6 only**, following
[this task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S6%20Release%20Readiness%20and%20Controlled%20Activation.md).
Prepare release evidence only and stop at G4; no live action.
Read current instructions/core references, approved architecture including EndScanID, Phase 2B plan
and pack. Verify both repos branches/HEADs/remotes/status; preserve all existing work.
Prerequisites: All preceding slices accepted; explicit S6 G3 authorizes evidence preparation only; separate G4 approval required for live actions.
Confirm evidence before edits; do not execute predecessor or later packs automatically.

Preserve B0 eligibility, exact endpoints, UTC scan start and semantic re-export deduplication.
Interim 11−10 then 12−10; final 13−10; authorized EndScanID update to 14 itself permits replacement
14−10 without a separate correction command. Aggregate reports and daily SCANORDER stay separate.
Use exact file/test/security manifests; report canonical delivery with actual outcomes and gaps.
No pull/reset/merge/push/PR, production SQL, real imports/exports, Discord actions, restarts,
deployment or activation. No private player data or credentials in Git. Required security reviews
use Changes at exact separate repo targets, Deep off; no standard/deep scan or automatic new task.


## Required carried-forward validation

Read the [S4B follow-up register](../../reference/kvk_source_migration/phase_2_implementation_plan.md#s4b-follow-ups) and this pack's 2026-09-11 handoff appendix. Track S6-OPS01, S6-PERF01 and S6-CAP01 explicitly through acceptance. Preserve exact evidence and unresolved gates. This reminder does not approve execution or expand the pack's operation/file permissions.


## S5B accepted closeout and S6 entry - 2026-09-12

S5B is complete, accepted, successfully smoke tested and merged (#271/#578). Read the
[archived S5B delivery](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S5B%20Endpoint%20Config%20and%20Recovery%20Integration.md).
Local mirror main/origin main is 85f303f6bd82bdc9a5cfc2d713da5480e1fa694a, synchronized from
production merge c7e063f02ebe8287a584d0054ea14f91a0c0ecc6 and containing review fix e5bbd8f7.
SQL main is 44afa315dd6cbfe9fec101f2a39a62e534f5b583. These are entry anchors, not instructions
to reset or overwrite work; recheck both repos and their remotes, branches, HEADs and status.
The operator confirms local pulls complete and **no bot-machine pull**. Smoke acceptance is
operator-reported with recorded local synthetic integration/import evidence; no fresh post-merge
or bot-machine smoke is claimed. All preceding slices stay accepted; S5B-REC01 is closed.
Retain the exact tested revisions, scan targets and disposable databases; do not rerun predecessors.

Start S6 in a new chat only after explicit S6 G3. That permits documentation/evidence preparation
only, not rehearsal execution. Carry S6-OPS01, S6-PERF01 and S6-CAP01 into both proposed release
documents as open gates until separately authorized evidence is measured and accepted. G4/exact
operations and G5 acceptance remain operator-owned. No live SQL, bot-machine update, restart,
real import/export, Discord action, deployment or activation is authorized by this handover.

Preserve every pending closeout documentation change, including untracked archive files and both
rename sides, from the pack's exact carry-forward manifest. Include these changes alongside S6's
new readiness documents in the eventual separately authorized S6 PR; do not omit them as pre-existing
work. Verify the final PR Files changed list contains the complete manifest (or prove specific paths
were already merged), repaired links and the updated evidence. Carry approved documentation through
later separately authorized production promotion as well. No PR is created by this handover.
