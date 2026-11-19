> **Archived 9 November 2026:** Superseded or completed Phase 1 instructions. Preserve the dated evidence below; do not replay its commands. [Current P02 scope and dependencies](../Startup%20Import%20Export%20Reliability%20-%20P02%20Remaining%20Work%20Handover%20-%202026-11-09.md) govern remaining work. Deployment is verified; standard production import/export acceptance remains open.

# P02 clean-chat starter

Continue the K98 startup/import/export reliability programme at P02, review/design first. P01.6 was explicitly closed on 6 November with residual intermittent Stats latency, snapshot CPU cost, older fallback/acknowledgement behavior and SQL performance limits recorded for follow-up after P01-P05. Do not repeat accepted deployments or widen that deferral silently.

Use `C:/Users/cwatt/.codex/worktrees/p016-production/discord_file_downloader` as the initial source/documentation workspace; the project root may be older. Read AGENTS and the seven required core references, then:

1. [P02 handover and scope](Startup%20Import%20Export%20Reliability%20-%20P02%20Handover%20and%20Scope%20-%202026-11-06.md).
2. [Programme principles](../Startup%20Import%20Export%20Reliability%20-%20Programme%20Principles%20-%202026-11-06.md).
3. [P01.6 closeout](Startup%20Import%20Export%20Reliability%20-%20P01.6%20Closeout%20-%202026-11-06.md).
4. [Documentation carry-forward](Startup%20Import%20Export%20Reliability%20-%20Documentation%20Carry-forward%20-%202026-11-06.md), then active scope/tracker/census/tracing/coverage/final sweep and applicable runbooks.
5. Private `.codex_artifacts/p016-closeout-p02-20261106/P02-PRIVATE-HANDOFF.md` for exact evidence routes. Do not commit raw reports or incident identities.

Investigate Bot and SQL together, including stored-procedure rewrites, tables/indexes/statistics/isolation, transaction/lock lifetimes and SQL-originated signals versus repeated reads. Compare options with correctness, cost and restart evidence before choosing a design. No spot fixes: follow equivalent callers, shared helpers, related functionality and failure boundaries, then make PR-sized slices within the whole-programme plan. Reconcile scope as each stage advances.

P02 owns F01/F03/F09/F12/F14/F16/F18/F20/F21/F22/F26/F31. Start with a current-state dependency assessment of the six historical incidents: five were linked to one unfinished pipeline and one was an older cancellation projection. P02 prevention is not automatic P03 continuation or P04 convergence; identify exact blockers to the next import/export and prepare supported recovery only after fresh evidence and concrete authorization. Never replay committed imports/provider effects or clear rows merely to reach zero incidents.

Preserve ownership until actual physical completion; truthful separate business/audit/cache/delivery outcomes; passive bounded diagnostics; D01-D06 evidence; protected startup/SQL contracts; all changed-path and ancestor ACL/owner/metadata/custody checks; mirror/private separation; final-head tests/security review; staged private-main deployment and real rollback. Do not restart, deploy, mutate production, run provider probes or implement runtime changes from this starter.

Begin the agreed review now. Deliver the source-confirmed scope/SQL/resource matrix, evidence gaps, incident owner/dependency map, design alternatives, acceptance plan and coherent first implementation proposal. Preserve the local closeout/archive delta for the next authorized publication; no standalone documentation deployment is needed.
