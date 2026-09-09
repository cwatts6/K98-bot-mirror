# Codex Chat Starter — KVK Source Migration S2A SQL Observation Facts

Refreshed 2026-09-09 after accepted S1 candidate smoke. **Prepared only; S2A G3 pending.**
S1 packs are archived. PRs #263/#570 await operator merge/final verification before the next handoff.
Use this only when approving this slice; G2 alone does not approve implementation.

---

I approve G3 for **KVK Source Migration S2A only**, following
[this task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S2A%20SQL%20Observation%20Facts.md).
Implement and validate its exact boundary, then stop for review.
Read current instructions/core references, approved architecture including EndScanID, Phase 2B plan
and pack. Verify both repos branches/HEADs/remotes/status; preserve all existing work.
Prerequisites: S1 typed schema/digest accepted; S2A G3; explicit disposable SQL target before integration acceptance.
Confirm evidence before edits; do not execute predecessor or later packs automatically.
Read the archived S1 delivery and verify its accepted/merged revision after the operator completes
PRs #263/#570. S1 passed 200 bot-machine tests and restart/startup; this does not execute S2A SQL.
Keep the existing twelve-table/migration/static-validator/constraint-test manifest unchanged.
Resolve migration date/sequence before authoring. No disposable SQL target is supplied here:
after G3, offline authoring/static checks may proceed, but SQL execution requires an explicitly
named authorized disposable server/database. Otherwise report integration validation pending.
S2B publication state remains separate and requires its own approval.

Preserve B0 eligibility, exact endpoints, UTC scan start and semantic re-export deduplication.
Interim 11−10 then 12−10; final 13−10; authorized EndScanID update to 14 itself permits replacement
14−10 without a separate correction command. Aggregate reports and daily SCANORDER stay separate.
Use exact file/test/security manifests; report canonical delivery with actual outcomes and gaps.
No pull/reset/merge/push/PR, production SQL, real imports/exports, Discord actions, restarts,
deployment or activation. No private player data or credentials in Git. Required security reviews
use Changes at exact separate repo targets, Deep off; no standard/deep scan or automatic new task.
