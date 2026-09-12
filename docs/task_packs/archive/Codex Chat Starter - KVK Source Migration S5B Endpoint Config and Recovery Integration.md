# Codex Chat Starter — KVK Source Migration S5B Endpoint Config and Recovery Integration

> Archived 2026-09-12: S5B completed, accepted, smoke tested and merged (#271/#578).
> Historical execution record only; pending approvals and next-slice language below are dated history.
> Current handover is the active S6 pack/starter; do not re-execute this slice.

Prepared 2026-09-09 during Phase 2B. **Not executed; S5B G3 pending.**
Use this only when approving this slice; G2 alone does not approve implementation.

---

I approve G3 for **KVK Source Migration S5B only**, following
[this task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S5B%20Endpoint%20Config%20and%20Recovery%20Integration.md).
Implement and validate its exact boundary, then stop for review.
Read current instructions/core references, approved architecture including EndScanID, Phase 2B plan
and pack. Verify both repos branches/HEADs/remotes/status; preserve all existing work.
Prerequisites: S3B, S4B and S5A accepted; explicit S5B G3; disposable SQL for transaction-hook integration.
Confirm evidence before edits; do not execute predecessor or later packs automatically.

Preserve B0 eligibility, exact endpoints, UTC scan start and semantic re-export deduplication.
Interim 11−10 then 12−10; final 13−10; authorized EndScanID update to 14 itself permits replacement
14−10 without a separate correction command. Aggregate reports and daily SCANORDER stay separate.
Use exact file/test/security manifests; report canonical delivery with actual outcomes and gaps.
No pull/reset/merge/push/PR, production SQL, real imports/exports, Discord actions, restarts,
deployment or activation. No private player data or credentials in Git. Required security reviews
use Changes at exact separate repo targets, Deep off; no standard/deep scan or automatic new task.


## Required carried-forward validation

Read the [S4B follow-up register](../../reference/kvk_source_migration/phase_2_implementation_plan.md#s4b-follow-ups) and this pack's 2026-09-11 handoff appendix. Track S5B-REC01 and the S4B-MP01 component-test handoff explicitly through acceptance. Preserve exact evidence and unresolved gates. This reminder does not approve execution or expand the pack's operation/file permissions.


## S5A accepted handoff - 2026-09-12

S5A is accepted, successfully smoke tested (operator reported) and merged (#270/#577); local pulls
are complete and no changes have been pulled to the bot machine. Read the archived S5A delivery
linked from the S5B pack; preserve the exact 15-path documentation carry-forward manifest, including
untracked Markdown, both S5A archive rename sides and repaired links. Include it alongside the
approved S5B execution manifest in any separately authorized PR and later authorized promotion.

This starter is prepared for a new chat; S5B G3 is still pending until the operator actually grants it.
Use mocks/fake destinations unless an exact disposable SQL target and operations are authorized;
required transaction-hook SQL evidence remains mandatory for acceptance. Preserve retained databases.
Either endpoint may change; supplied EndScanID >= StartScanID. Equal endpoints mean zero supported
fight scores for all B0 members and aggregates not applicable. Distinct scans increase ScanID and
UTC; ordinary missingness stays explicit. Keep daily SCANORDER separate and every command group
within 25 children. S5B-REC01 and S6-OPS01/PERF01/CAP01 remain open. Routing stays disabled;
no bot-machine action, restart, deployment or activation. Do not automatically execute another pack.
