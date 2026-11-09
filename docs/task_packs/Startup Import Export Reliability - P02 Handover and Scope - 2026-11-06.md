> **P02 integrated reconciliation, 7 November 2026:** See the [complete analysis and delivery plan](Startup%20Import%20Export%20Reliability%20-%20P02%20Integrated%20Analysis%20and%20Delivery%20Plan%20-%202026-11-07.md). P02.1 and the SQL summary rewrite are locally qualified components, not completion of P02. Original factory/observer/holder/maintenance/file/legacy obligations, numeric alignment, unchanged cost gates and P03/P04 recovery dependencies are now mapped to one delivery sequence. Underlying-data and external-consumer analysis inputs remain explicit; production is not approved. Earlier dated statuses below are retained history.

# P02 handover: contention, observer isolation and producer budgets

**Next active stage, 6 November 2026. Review and design authorized; runtime implementation and production recovery are not implied.** P01.6 is [closed with explicit limitations](archive/Startup%20Import%20Export%20Reliability%20-%20P01.6%20Closeout%20-%202026-11-06.md). Proceed without asking whether to start the agreed review. Produce a concrete whole-solution design and focused delivery sequence before seeking implementation approval.

## Scope summary and outcome

P02 must explain and reduce avoidable contention across producers and observers, establish truthful resource/holder attribution, and define bounded connection/admission/execution policies. Assess Bot and authoritative SQL together, including procedure rewrites, table/index/statistics/isolation configuration and repeated polling alternatives. Preserve required ownership, fencing, exact completion and restart safety.

The intended administrator gain is fewer avoidable producer refusals and stalls, responsive passive status, clearer busy/unknown/actionable outcomes, and a supported route to the next import/export without replaying committed stages. These are acceptance targets, not delivered guarantees.

## Existing findings and package boundaries

| P02 family | Findings | Review coverage |
| --- | --- | --- |
| Shared SQL policy and factory selection | F01, F26 | All shared-factory consumers, direct/alternate factories, ordinary reads, first-failure preservation and explicit budgets |
| Coordination and observers | F03, F09, F12, F14 | Account/resource/global snapshot/season locking, ordering and lifetime, authority request scheduling, observer-first and producer-first overlap |
| Maintenance boundaries | F16, F18, F21, F22 | All six mapped maintenance stages, actual child procedures, required versus ancillary work, transaction/guard duration, commit/receipt and backup/headroom contracts |
| Shared cache and file ownership | F20 | Exception cleanup across direct/cache/Ark callers, sentinel ownership, physical completion and superseded observations |
| Legacy/manual invocation | F31 | Verify installed scheduled/manual use; either qualify input custody/error/commit semantics or propose explicitly approved retirement |

Use the existing [scope](Startup%20Import%20Export%20Reliability%20-%20Scope%20-%202026-11-02.md), [tracker](Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md), action census, tracing, coverage and final sweep; extend them rather than creating a competing programme. F10 crosses P02 passive snapshot design and P03 exact binding. P03 retains unfinished-stage continuation/settlement, cancellation convergence F28 and Rally identity F29. P04 retains actionable incidents/history/notification policy, including F19 and F27. P05 owns combined confirmation, not missing implementation.

The deferred snapshot decode/rebuild optimisation discovered during P01.6 remains after P01-P05 as requested. P02 must still measure observer cost and record any demonstrated prerequisite; overlap in files does not silently authorize that broader deferred rewrite. If the P02 design cannot meet its acceptance budget without it, present the exact dependency and bounded scope decision.

## Six incidents and the next import/export

The historical complete Report 68 described **six operational rows: five linked to one pipeline plus one older cancellation projection**. The overview is not a seventh job. Later Report 75 contained only 370 of 17,754 history records and cannot establish the six current dispositions. No new live inventory has been made for this handover.

| Historical record family | Last evidenced meaning | Required next assessment |
| --- | --- | --- |
| Configuration attempt | Failed at writer admission before writes may start, native 51421 | Confirm exact current attempt/preparation/ownership; address recurrence in P02 without claiming the historical holder is known |
| Configuration preparation | Not committed; offered rolled-back close/release | Revalidate exact rollback/release predicates; release alone does not complete pipeline/export |
| Pipeline | Stopped at configuration | Identify remaining stages and supported original-intent continuation; P03 dependency if unavailable |
| Stats preparation | Committed/captured; export unconfirmed | Preserve capture and bind to exact continuation; never repeat ingestion to repair handoff |
| Player preparation | Committed/captured, caches written; export unconfirmed | Preserve output/cache evidence; continue only unfinished authorized work |
| Older cancelled import projection | Linked producer cancelled before SQL; sibling row stayed open | P03/P04 terminal convergence; do not infer an active owner or clear by age |

**P02 owns the entry assessment and readiness dependency plan, not blanket resolution of six rows.** Obtain only the fresh bounded evidence needed: actual incident states, original stage receipts/captures, owner/fence/version, session/stream/physical closure, supported repair predicates, and active runtime/updater identity. Private identities and retained report routes are in the private handoff; keep them out of public source.

Before another import/export, establish whether any exact retained work or active claim blocks it, whether the relevant contention prevention is qualified, and how unfinished work will reach a truthful terminal state. Do not demand cosmetic zero counts. Where existing supported recovery is sufficient, prepare an exact separately authorized operator plan. Where continuation/convergence code is missing, make the P03/P04 dependency explicit and adjust delivery order only by a concrete scope decision. Never rerun committed stats/player stages, replay a provider mutation, force-clear claims or use missing receipts as success.

## Architecture and SQL review deliverables

1. A source-confirmed caller/resource/SQL matrix from input and startup through calculation, publication, observation, settlement, cleanup and delivery. Include direct helpers, every related writer/reader and actual enabled legacy paths. Identify current owners, helper reuse and all six maintenance stages.
2. A Bot/SQL timeline separating connection, admission, lock wait/hold, execution, transfer/result consumption, commit, cleanup and user observation. Record original return/native codes and requester versus actual holder. Keep genuinely missing historical attribution explicit.
3. Compare targeted optimisation, procedure/flow rewrite, narrower coordination, cheaper passive snapshots and SQL-originated update/completion signalling versus bounded polling. Verify server/driver support, permissions, transaction/write costs, durable cursor/acknowledgement, loss/duplicates/reorder, reconnect/catch-up, cleanup and fallback before selecting a push mechanism. No blind notification-based authority or provider calls inside transactions.
4. Evaluate table/index/statistics/isolation options from authoritative SQL source and representative plans/workloads. Measure read benefit against write/log/storage/maintenance cost and concurrency; do not add indexes, NOLOCK, remove fences or increase timeouts speculatively.
5. Produce a complete final file/object/contract manifest, shared-helper decisions, related/deferred classifications, old/new behavior examples, implementation slices, migration/updater order and concrete rollback. Check all three protected startup SQL contracts before a deployment plan is called ready.

Commands/views stay thin; services own policy/orchestration; DAL owns persistence and SQL lifecycle. Durable receipts remain authoritative. Reuse delivered P01 ownership/evidence/passive-health foundations and accepted P03a behavior. No new general framework without an evidenced need.

## Qualification and approval gates

Predeclare representative work, denominators and acceptance budgets before measurement. Required cases include both observer/producer arrival orders, controlled known holders, multiple contenders, cancellation before/after physical entry, unknown close/commit, real maintenance child failures, restart/reconnect, alternate factories, direct helpers, installed legacy bindings, custody and negative permissions. Test optional diagnostic failure/saturation without changing primary results. Native isolated SQL qualification must complement mocks; do not experiment against retained restores or production.

Read `local_sql_development.md` and reconfirm current local instance/database suitability before creating a uniquely named disposable fixture under the existing authorized local-development scope. Prior K98DEV elevation/memory changes are historical facts, not instructions to repeat them or apply them to MINI_AMD.

Before each slice and at PR/promotion/acceptance, recheck the whole-programme matrix for missed callers and changed assumptions. Separate source qualification, host ownership/ACL readiness, exact installed source/SQL, exercised functionality and whole-flow/provider acceptance. Use per-repository Changes security review after routing; no inferred full/deep scan. Tests do not replace review.

Production recovery, provider requests, SQL changes, deployment and restart require the concrete authorized action and fresh preconditions. This handover authorizes review/design and local documentation, not execution of historical commands.

## Reading and working context

Read AGENTS.md and all seven core references, then the [programme principles](Startup%20Import%20Export%20Reliability%20-%20Programme%20Principles%20-%202026-11-06.md), closeout, scope/tracker and [carry-forward manifest](Startup%20Import%20Export%20Reliability%20-%20Documentation%20Carry-forward%20-%202026-11-06.md). Conditional references: REVIEW_HELPERS, local SQL development, startup/shutdown, diagnostics, singleton locking, Windows ownership/access contract, Promotion Guide and S11 release contract as applicable. Use architecture-scope, SQL-validation, test-selection and security-review-routing skills at their actual boundaries.

Reuse the current P01.6 worktree for initial review: `C:/Users/cwatt/.codex/worktrees/p016-production/discord_file_downloader`. It contains the unpublished closeout/archive delta and private evidence. The project root checkout can be older; do not infer current code from it. Local HEAD `40215ae3a37fe6bcdecce587b240811678f73889` matches the deployed final merge tree; verify drift before implementation. SQL source is `C:/K98-bot-SQL-Server`. Preserve unrelated edits and independent Git histories. A new chat does not require a new worktree.

First response should present verified P02 coverage, the incident dependency assessment with freshness limits, the Bot/SQL options and a proposed coherent review/design sequence. Continue useful source review without asking to reconfirm the start; seek approval only for the concrete next implementation or operational action when needed.

## Subsequent implementation approval

The operator approved the scope/approach and instructed implementation to proceed.
The first local slice and its unresolved release gates are recorded in the
[P02.1 local candidate](Startup%20Import%20Export%20Reliability%20-%20P02.1%20Local%20Candidate%20-%202026-11-06.md).
The review-only statements above describe this handover's original boundary; they do not rescind that subsequent local implementation approval. Production operations retain their separate concrete approval requirement.
