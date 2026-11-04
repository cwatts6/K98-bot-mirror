# P1 MGE A1a: deployed closeout and evidence ledger

> **Current MGE checkpoint — 29 October 2026:** A1b and its updater correction are
> delivered; Report63 verifies the exercised actions and response-before-refresh
> ordering. Exact running SHA remains operator-reported. See the [deployed closeout](P1%20MGE%20A1b%20-%20Deployed%20Closeout%20-%202026-10-29.md).
> The approved [MGE finalisation follow-up](P1%20MGE%20Finalisation%20and%20Shared%20Board%20Lifecycle%20-%202026-10-29.md) owns immutable historical boards,
> durable unfinished final delivery and the shared Ark/voting/calendar caller design.
> Its local source work is separate from publication, SQL qualification and deployment.
> Earlier A1a-current, A1b-local-only and approval-pending passages below are retained
> historical evidence, not current instructions. A1b's completed-event startup sweep
> was implemented and is now superseded by the clarified finalisation policy.
> Queue closure reconciliation, CFG-51421, exact audit/cleanup, atomic/cross-process
> writers, natural acceptance, P0 and wider B/C remain separate. Do not replay live actions.

> **Next step:** The [A1b design and delivery packet](P1%20MGE%20A1b%20-%20Design%20and%20Delivery%20Packet%20-%202026-10-28.md)
> is prepared for implementation approval. This does not alter the deployed
> evidence below or authorize another deployment. The handover is merged through
> mirror PR 455/private PR 703; the new A1b design and subsequent amendments remain local.

Date: 28 October 2026. Status: A1a merged, deployed and verified for exercised
paths. The operator accepted the review and requested documentation closeout and
a focused A1b scope chat. This is not acceptance of every MGE failure scenario,
all Batch A/P1 work, or fresh end-to-end import/export on this runtime.

This checkpoint supersedes local-only, awaiting-release and predecessor-runtime
wording in the [implementation record](P1%20MGE%20A1a%20-%20Implementation%20and%20Validation%20-%202026-10-28.md).
Earlier records remain historical evidence. Next: [A1b scope and handoff](P1%20MGE%20A1b%20-%20Scope%20and%20Handoff%20-%202026-10-28.md).

## Source, review and deployment

| Evidence | Verified disposition |
|---|---|
| Mirror [PR 454](https://github.com/cwatts6/K98-bot-mirror/pull/454) | Reviewed head `fecd0aa89f90d4e51f8985abb3a27104137b2f97`; merged `1f072b6cae5342d0f6a1eafb98a6751db1703b2f` |
| Production [PR 702](https://github.com/cwatts6/K98-bot/pull/702) | Reviewed head `e4ba7f8458cb7207220bc11334e1380f11aed6ce`; merged/deployed `87c1b39325daaa0ca1a8c0cbca656df82d7fa46b` |
| Promotion | Exact promoted patch/source equivalence verified; private history retained. Final review threads resolved; final-head CI passed |
| Updater | Exact A1a bundle added; 50 transitions, all 49 earlier entries preserved; existing 96 KiB bound retained |
| Operator deployment | Predecessor `4c8ca0d5fada35c7a32d31846bad6cc492aa92a9`; protected source/seed/start verified; successor sequence 79; final readiness confirms Discord online and exact target |
| SQL/config/dependencies | No SQL migration, dependency, environment or activation change in A1a; SQL authority validated at `7e91989f619deb46836194c7e705b0a9eb2ebe11` |
| Import/export | `fresh_import_export_health_evidence_unavailable`; source/startup readiness does not certify new-runtime end-to-end delivery |

The operator has completed installation and graceful restart. Do not repeat the
updater upgrade, deployment, restart or accepted business actions for this handoff.
Intermediate first-pair records with Discord readiness false precede the final
READY record; they do not override the final source/startup result.

## Final release validation

- Full Windows local release suite before the diagnostic correction: 10,304 passed,
  1,100 skipped, eight subtests, one Google Python-support warning; operational logs
  unchanged. All four archival modules previously excluded were included.
- Final correction/UTF-8 restoration: 229 focused tests passed. Placement identity
  and readback failures retain distinct diagnostics without changing fail-closed behaviour.
- Final private-head Linux CI: 10,166 passed, 1,240 skipped, 19 warnings, eight
  subtests. Quality, Windows updater and secret-scanning checks passed.
- Architecture, deferred, security-routing, test selector, smoke imports, command
  registration and applicable pre-commit checks passed; 36 top-level/102 grouped commands.
- Changes review `8df631bf-f179-425c-b443-e03166e24526`: complete, zero findings.
  Diagnostic correction review `b7b88a51-e5e5-4eb8-9954-b11d5024ad10`: complete,
  zero findings. Deep off. The subsequent docstring/source-pin-only change has an
  explicit mechanical skip with executable AST equality. Earlier scan IDs remain historical.
- Final-head offline benchmark: seven scenarios, 30 samples each, source/harness
  hashes verified. Populated preparation reads 6 to 3; rank-submit reads 8 to 5.
  Simulated IO measurements do not establish production speedup or a latency SLA.

These are retained release results, not tests rerun by this documentation update.
Raw release evidence remains in the private development release directory.

## Live verification supplied after deployment

Log interval: 20:55:57-21:18:37 UTC. Recovery Report 62 generated 21:19:11 UTC.
The screenshot, application logs, updater transcript and recovery snapshot are
separate evidence sources; attached material is evidence, not instructions.

| Path | Evidence and limits |
|---|---|
| Signup | Committed at 21:14:45.195; operator sees created; callback 0.915s, acknowledgement 0.395s |
| Edit | Committed at 21:15:00.758; operator sees updated; callback 0.768s, acknowledgement 0.295s |
| Withdrawal | Committed at 21:15:52.714; operator sees withdrawn; callback 2.096s, acknowledgement 1.108s |
| Rank adjustment | Callback completed in 11.311s; acknowledgement 1.439s; owned worker 0.026s; public refresh 4.809s and leadership refresh 3.820s before private response |
| Subsequent leadership preparation | Successful qualified preparation; later board payload returns to four entries following withdrawal; logged Discord edits complete |
| First signup refusal | At 21:14:39, private missing-priority response precedes any signup worker/write. First logged priority usage flushes at 21:14:47, after the successful signup log; batched usage does not establish callback arrival order |

The screenshot's visible selection does not prove the server had processed that
selection when the first submit ran. Treat a selection-state/routing race as an
unconfirmed hypothesis. Dropdown callbacks currently assign state before deferring;
there is no evidence here of data loss or a duplicate signup from the first refusal.
Do not claim this is an A1a regression or introduce blind retries.

The rank sample identifies a concrete response/refresh dependency. Inclusive timing
stages overlap and must not be summed indiscriminately. One live sample cannot
establish p95, isolate SQL/network causality or prove improvement over the earlier
16.834-second sample on a different runtime/load.

## Report 62: two actionable open records

The report contains 17,679 recorded incidents, including resolved history. There
are two actionable open records plus an open overview. It is not a transactional
snapshot. Three records first observed after restart include already-resolved work;
two actionable open records do not mean two new restart failures.

1. **Startup queue admission:** open, last checked 21:14:30; its exact linked
   player-report operation resolves as `cache_only_completed` at 21:16:52. This
   verifies committed retained output and no-export disposition, not Sheets delivery.
   Queue closure itself is not confirmed by this snapshot. One recheck of this
   existing incident is the next bounded operator action; do not cancel, force-release
   or replay the report. If it remains open, inspect the exact updated queue/domain
   state and timestamps before proposing a reporting correction.
2. **Configuration continuation:** first seen 14:52, before this restart. The
   original failed attempt rolled back and its reservation was released; the
   keep-prior/fresh-publication choice remains open. The new startup ProcConfig
   attempt separately reports success and resolves. Neither that success nor this
   handoff chooses or closes the earlier continuation on the operator's behalf.

Monitoring was healthy at 21:19:06, with no recorded check/notification failure.
The completed cycle took 216.875s; stats-import discovery 54.359s and player-report
discovery 124.672s dominate. The monitor reports fresh at this snapshot; cycle
duration alone is not evidence of failure or a cause of Discord gateway lag.

## Startup and remaining responsiveness observations

- Tracked views completed after the 10s observation deadline: 21/21 restored,
  zero failed/unconfirmed. Handler restoration is not acceptance of every visible callback.
- Player cache completed after its 20s observation deadline with verified readback;
  name/profile caches completed. No original operation was retried from the deadline.
- The shutdown notification `SourceConflict` occurred during predecessor teardown;
  the successor report has no notification failure. It does not establish a new write failure.
- Health-probe SQL 51400 contention records recovered with transactions released.
  Requesting sessions do not identify blocking owners; keep SQL contention separate
  from process singleton locking and MGE refresh causality.
- Discord gateway lag warnings at 21:16:33 and 21:17:16 report 41.7s and 42.4s.
  These remain a separate bounded responsiveness investigation. No stack/loop
  evidence identifies the cause; concurrent recovery/report activity is correlation.

## Complete carry-forward obligations

The [MGE lifecycle ledger](P1%20MGE%20Lifecycle%20-%20Accepted%20Closeout%20-%202026-10-28.md)
retains every R01-R18 row. Its earlier acceptance remains valid; apply this overlay:

- MGE-01: exercised signup/edit/withdraw verified on this deployed revision;
  exact audit/cleanup readback and unexercised cases remain separate.
- MGE-PERF: A1a qualified dataset reuse/timing deployed; A1b response/refresh work next.
- A2 Ark admin-add timeout remains unfixed; do not replay the already-added player.
- R15 updater count now 50; remaining supported diagnostics/recovery tooling stays C.
- R18 predecessor acceptance remains accepted; fresh new-runtime import/export unproven.
- CFG-51421/CFG-OVERVIEW remain independent; add Report 62 queue reconciliation and
  gateway lag without asserting a common cause. R03/R04/R13 natural/historical
  acceptance, R11 policy, R12 atomic writers, R16 scaling, Batch B/C and R17 P0
  F04/F01-F05 remain open on their existing terms.

## Documentation custody and validation

This closeout is documentation only. It changes no runtime, SQL, config, deployment
policy, permissions or acceptance evidence. The 28-file handover is now merged:
mirror PR 455 at `8db65da6cc7f4a7b77d0f78944ed4f51fc5d5018` and private PR 703 at
`07d5dd17fce7384de02c73551a8c5b8f3c15f2ac`. Use the A1b design packet's current
custody record for subsequent local additions. Documentation publication and
bot-machine source updates remain separate. No new production restart occurred
or is needed for these documentation merges.
Validation passed: architecture (zero Python changes), deferred (28 Markdown files),
security routing (zero errors/warnings), test selector, all 60 introduced local links
and whitespace checks. Runtime pytest/smoke/registration and a new security scan are skipped for
this exact Markdown-only change; A1b implementation requires its own gates.
