# Codex Chat Starter — KVK Source Migration S2B SQL Publication State

**Historical S2B starter: G3 approved, implementation and local validation completed.**
The operator authorized separate SQL and mirror PRs for review on 2026-09-10.
Do not rerun this starter or execute successor slices. The requests below are retained history.
Use the scope-only request first if approval is not yet intended. The implementation request
below explicitly grants S2B G3 and a named disposable target only when the operator sends it.

## Scope-only request

Review and scope S2B using its existing task pack, current core instructions, accepted S2A
merge/evidence and `docs/reference/local_sql_development.md`. Verify both repositories and
preserve existing work. Explain the exact manifest, dependencies, proposed disposable target
and migration date/sequence. Do not implement, execute SQL or create another task. Stop for G3.

## Implementation approval request

---

I approve G3 for **KVK Source Migration S2B only**, following
[this task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S2B%20SQL%20Publication%20State.md).
Implement and validate its exact boundary, then stop for review.
Read current instructions/core references, approved architecture including EndScanID, Phase 2B plan
and pack. Verify both repos branches/HEADs/remotes/status; preserve all existing work.
S2A is accepted and merged (SQL #78, mirror #264); verify its final evidence and current HEADs.
Read `docs/reference/local_sql_development.md`. I explicitly authorize the local server
`9SX2VF4\K98DEV` and disposable database `K98_S2B_Disposable_20260910` for S2B only:
create that database with compatibility 160 and collation `Latin1_General_CI_AS`, install the
accepted S2A schema prerequisites, then run the approved S2B migration and synthetic FK/state
checks. Start the local K98DEV service if stopped. Preserve the separate S2A evidence database.
No production target or data is authorized. Recheck migration date/sequence before authoring.
Confirm evidence before edits; do not execute predecessor or later packs automatically.

Preserve B0 eligibility, exact endpoints, UTC scan start and semantic re-export deduplication.
Interim 11−10 then 12−10; final 13−10; authorized EndScanID update to 14 itself permits replacement
14−10 without a separate correction command. Aggregate reports and daily SCANORDER stay separate.
Use exact file/test/security manifests; report canonical delivery with actual outcomes and gaps.
No pull/reset/merge/push/PR, production SQL, real imports/exports, Discord actions, restarts,
deployment or activation. No private player data or credentials in Git. Required security reviews
use Changes at exact separate repo targets, Deep off; no standard/deep scan or automatic new task.
