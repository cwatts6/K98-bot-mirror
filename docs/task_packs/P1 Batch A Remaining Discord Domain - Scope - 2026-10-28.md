# Remaining Batch A: Discord/domain lifecycle completion

Date: 28 October 2026. **Status update: amended A1a local implementation and
validation approved.** See the [A1a implementation packet](P1%20MGE%20A1a%20-%20Implementation%20and%20Validation%20-%202026-10-28.md).
The original scope below remains the wider programme boundary; other slices and
promotion/deployment are not included in A1a approval.
Read the [accepted MGE closeout and complete ledger](P1%20MGE%20Lifecycle%20-%20Accepted%20Closeout%20-%202026-10-28.md)
first. The operator accepts the exercised MGE flows and requests a new focused chat.
Start from current verified mirror/private source; deployed runtime is private
`4c8ca0d5fada35c7a32d31846bad6cc492aa92a9`. Do not repeat deployment, restart or accepted tests.

## A1: focused MGE responsiveness and refresh proposal

Use the retained production sample and deterministic fixtures. Instrument/measure
separately: interaction age at handler entry, initial response await, worker/event
ownership wait, DAL work, public/leadership payload reads, Discord fetch/edit, and
final response. Preserve a correlation reference without logging tokens or private payloads.
Do not equate nested acknowledged callbacks with fresh network acknowledgements.

Evaluate one reusable leadership dataset for rendering/readiness, and the boundary
between a saved mutation result and pending/failed board delivery. Inventory scheduler,
manual and mutation refresh callers before changing serialization or coalescing.
Existing event-scoped ownership, current-state rereads, original message identity,
dirty-during-run behavior and unknown-send protection remain required.

Acceptance: repeated before/after representative fixtures, per-stage p50/p95 where
sample size is sufficient, query/connection/edit counts and event-loop delay. Include
ordinary and overlapping scheduler/user work, delayed Discord, a newer refresh during
an in-flight pass, cancellation and failed refresh after committed mutation. The
one production rank action is not enough for a p95 or universal speedup claim.
Do not replay production mutations or induce provider failure for measurement.

## A2: related Discord/domain adoption

Map remaining Ark, voting and calendar command/view/modal/publication paths. Classify
each as already protected, proven gap, evidence missing, policy decision or deferred.
Reuse private acknowledgement, owned worker, mutation-outcome and refresh/delivery
contracts only where domain semantics fit; do not create another retry framework.
Test a second concrete caller for each shared helper change. Keep domain-sized PRs.
Preserve original accepted Ark callback and MGE flow evidence.

## A3: bounded policy and persistence gaps

Scope R11 fighting admission/caps, KS preclaim and ambiguous legacy Pre-KVK replacement
separately from responsiveness changes. Agree domain policy before implementation.
Carry broader roster atomic-write/receipt adoption and MGE receipt-query scaling as
distinct proposals; current process-local ownership is not a cross-process contract.
Do not presume an index or schema migration is needed from small fixture timings.

## Independent reliability lane

CFG-51421: correlate the startup import's durable admission, session applock and
cleanup boundaries with the actual blocking owner if evidence permits. The exact
attempt was cancelled and released, but its keep-prior/fresh-publication decision
remains open in Report 61. Do not choose or execute that decision automatically.
Review the existing ProcConfig entrypoint census before adding another backlog item.
Only propose bounded waiting/retry after non-entry, cleanup and ownership are proven;
never replay an uncertain write. Distinguish this from the prior 51400 and deployment
provider-stream refusal. CFG-OVERVIEW: determine whether summary/detail mismatch is
collection timing or a reporting defect and test continuation creation after closure.
Keep these corrections in separate reliability PRs if warranted, not in the MGE refresh PR.

## Architecture, SQL, security and testing

Views own response routing; services own business decisions; DAL owns SQL/transactions.
Review `core/interaction_safety.py`, `core/owned_work.py`, MGE board/roster helpers,
`services/event_delivery_service.py` and existing refresh coordination before new abstractions.
Validate proposed SQL-facing changes against `C:\K98-bot-SQL-Server` before coding.
No migration, activation change, domain policy rewrite or new top-level command is presumed.

Required tests follow the actual scoped change: current permissions/form owner, stale
event/signup, duplicate click, cancellation without abandoned worker, saved write with
failed reply/refresh, rollback/unknown commit, ordered/coalesced refresh and restart
message recovery. Keep realistic second-caller compatibility and measured costs.
Run architecture, deferred, selector and security-routing gates; focused/full runtime
tests as justified, smoke/registration when applicable and protected log isolation.
Use per-repository Changes security review for sensitive diffs, Deep off, or a precise
documented skip. Mirror-first PRs and patch-based private promotion remain separate.

## Required handback before implementation

Return evidence versus hypotheses; caller/ownership map; reusable architecture; bounded
PR order; measurable acceptance; test/security routing; SQL/deployment implications;
and disposition of every closeout ledger row. Include a read-only plan for missing
mandatory MGE audit/cleanup evidence, without treating its absence as retry authority.
Do not expand to all P1 implementation merely because the programme is approved.

After A: Batch B covers remaining writers/executors, singleton, cache/JSON/queue
ownership; Batch C covers external monitoring and supported recovery tooling.
R03/R04/R13 natural/historical checks and P0 R17 remain parallel acceptance lanes.
R18 on f6a929c remains accepted; new-runtime import/export evidence is separate.
