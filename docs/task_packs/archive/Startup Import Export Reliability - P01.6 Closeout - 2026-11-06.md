# P01.6 closeout: owned personal reads and SQL companion

**CLOSED by operator acceptance, 6 November 2026 (E104).** The agreed ownership, authorization, SQL companion and related corrective releases are implemented, reviewed, merged and deployed. Exercised Stats routes passed. This is scoped closure with residual intermittent performance and older interaction limitations explicitly deferred until after P01-P05; it is not a claim that every render timeout or SQL delay is eliminated.

## Delivered behavior

Personal Stats retains bounded physical ownership of SQL, registry and render work after UI timeout/cancellation, preserves inflight identity and drains actual work during shutdown. Late/cache delivery revalidates account access. The daily SQL rewrite and covering index preserve the public result contract. The related startup correction aligns the protected application SQL contract with the installed procedure/index and checks all three startup SQL contracts before drain. The rendering correction submits immediately to the dedicated executor, retains future-owned settlement and removes duplicate acknowledgement attempts.

## Installed identities and evidence

| Component | Recorded identity / result |
| --- | --- |
| SQL | `dad628c7a353cc6391868d097a6ae5fb7a8d9e84`; migration `20261106_001_personal_stats_daily_read_plan`; `dbo.usp_GetPersonalStatsDaily` and `IX_KS4_Governor_DayEnd` installed and independently verified, permissions unchanged |
| Initial Bot release | `8f1023e2d89e2d4da06ddde39da5b4b6df32ff03`; retained startup-contract failure evidence, not an accepted fallback baseline |
| Startup correction | `8032f740b12159ee6b721649580eeb656e26e1d6`; startup SQL contracts verified with SQL connected |
| Final rendering correction | [Mirror PR 493](https://github.com/cwatts6/K98-bot-mirror/pull/493), [private PR 732](https://github.com/cwatts6/K98-bot/pull/732); deployed private merge `6cb5d8ed532a8b1e34ad58ed230daa74d5ba77a3` |
| Final reviewed private source | `40215ae3a37fe6bcdecce587b240811678f73889`; tree matched the private merge |
| Protected deployment | Release `615838d7-d723-49d6-8b5b-91cf6525c226`, successor sequence 97; source/seed/start/readiness and SQL contracts verified; Discord ready at 18:21 UTC |
| Qualification | Final local full suite: 11,937 passed, 1,113 skipped, 8 subtests; focused 1,815 passed; seven native updater suites, 233 checks; final review group 127 passed; operational logs unchanged |
| Final CI/review | Private quality, native Windows updater and secret checks passed; runtime and updater Changes security scans completed with zero findings; later test/document-only delta had a precise review skip |

These are retained deployment/qualification receipts, not a new live inspection. The original implementation and correction packets retain their own test targets, adverse runs and limits. Runtime admission was corrected; lack of fresh whole-flow import/export evidence remained truthfully degraded.

## Functional acceptance and retained adverse evidence

The 18:32-18:35 capture showed a fresh Stats image rendered in 639.2 ms and an Activity transition in 541.4 ms. The later Accounts-to-Stats attempt reached Stats data/render work but fell back after a 4,346 ms render observation. This was not proof of a fresh navigation or Unknown Webhook failure.

The 20:42-20:43 capture and operator report confirmed both Accounts-to-Stats and fresh `/me stats` delivered images without fallback. Data/render/delivery observations were respectively 2,639.8/2,783.5/1,127.0 ms and 1,460.8/2,583.4/1,969.5 ms. The second data request was cached. These phase measurements are not a complete end-to-end stopwatch, pure SQL execution time or pure renderer CPU time.

The same profile retained 914 samples with four sampling errors; 883 samples were in one recovery worker decoding/reconstructing/encoding retained snapshots. Process CPU increased 86.484 seconds in 85.948 seconds of wall time. Sample fractions are not exact CPU percentages. The overlapping recovery cycle completed in 308.203 seconds with 211 checkpoints and no recorded failed/waiting checks. Busy recovery and successful rendering coexist; the exact contribution to each earlier timeout is not isolated. The sampled inspectors, snapshot service and renderer are unchanged from before P01.6.

Two earlier post-correction fresh procedure executions took 60.023 ms and 1,205.160 ms, with about 59 ms CPU each. Another passive capture observed result-consumption waits without a blocker. No nine-second server execution was reproduced in these captures; this does not certify all historical delays resolved. The latest profile makes no new SQL-duration claim. Approximately 5.1 GiB free memory and no paging at the earlier snapshots do not justify changing production memory policy from the local K98DEV trial.

## Explicit remaining owners

| Remaining item | Disposition |
| --- | --- |
| Repeated recovery snapshot CPU cost / intermittent Stats latency | Existing deferred optimisation after P01-P05; do not disable integrity checks or expand P01.6 into a recovery rewrite |
| Previous image retained above fresh text fallback | Older production SDK attachment behavior; separately qualify a supported clearing strategy or dependency change after P01-P05 |
| Rejected acknowledgement / Unknown Webhook handling | Older path remains deferred; corrected duplicate acknowledgement does not certify every expired interaction |
| Residual SQL/result-consumption performance | Keep measurements and representative account/write/concurrency limits with the SQL deferred item; no speculative extra indexes or memory-policy change |
| KVK cache warning | Cause remains unproven; last KVK data on 29 September and no active KVK/reminders are expected; startup-cache follow-up remains separate |
| Calendar reminders / earlier natural cases | P01.4/P01.5 active acceptance registers retain these; loop armed or pinned update is not dispatch proof |
| Six historical operational incidents / next import-export | P02 inventories exact current blockers; P03 owns unfinished-stage continuation, P04 convergence/history; no automatic clearance |
| Whole-flow import/export and combined acceptance | P03a.2 still lacks fresh whole-flow proof; P02-P05 and applicable P0 reconciliation remain open |

The [deferred backlog](../../reference/deferred_optimisations.md) owns the actionable residual items. The operator explicitly accepted this bounded disposition; no incident or business work was cleared to close P01.6.

## Lessons and archive

Carry the [programme principles](../Startup%20Import%20Export%20Reliability%20-%20Programme%20Principles%20-%202026-11-06.md) into every later packet. In particular, assess Bot and SQL together; include protected startup contracts in SQL change planning; compare whole affected caller families; measure queue/SQL/result-consumption/render/delivery separately; verify deployed SDK behavior and the final user-visible artifact; distinguish code qualification, host custody, deployment and functional acceptance.

The completed P01.6 starter, scope, design, qualification, release plan and both correction packets are archived with links rebased. Historical deployment commands are evidence, not instructions to run again. Active natural registers, programme scope/design/census/tracing/coverage/final sweep remain available for their cross-package obligations.

Private receipts and raw captures remain under `.codex_artifacts/p016-contract-repair/`, including `render-post-deployment-review.json`, `render-post-deployment-timing-analysis.json` and `render-post-deployment-profile-analysis.json`. The documentation preservation/validation manifest is under `.codex_artifacts/p016-closeout-p02-20261106/`. Raw reports and incident identities must not be copied into public commits.

Next: [P02 handover and scope](Startup%20Import%20Export%20Reliability%20-%20P02%20Handover%20and%20Scope%20-%202026-11-06.md), review/design first. This documentation closeout changes no runtime code, SQL, permissions, packages, startup policy or production state.
