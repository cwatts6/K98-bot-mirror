# Remaining Batch A: A2 shared board and domain lifecycle

Current 29 October 2026: A1a and A1b plus the updater correction are delivered.
Read the [A1b deployed closeout](P1%20MGE%20A1b%20-%20Deployed%20Closeout%20-%202026-10-29.md).
The approved [MGE finalisation slice](P1%20MGE%20Finalisation%20and%20Shared%20Board%20Lifecycle%20-%202026-10-29.md)
owns MGE implementation and shared-contract validation. A2 adopts the resulting
contract in domain-sized changes; wholesale Ark/voting/calendar implementation is
not included in the MGE slice. Earlier scope and status below are historical.

## Current caller and ownership map

| Domain / current evidence | Required next boundary | Owner / policy |
|---|---|---|
| Ark `list_open_matches` selects Scheduled/Locked; scheduler's completion fallback is fed only already-Completed rows | Inventory past Scheduled/Locked matches explicitly; stop roster work at end while retaining late-result admission | A2 Ark; expected two or three active boards is not a cap and static code does not prove current old rows |
| Ark completed selector uses `CompletionEmbedPostedAtUtc < UpdatedAtUtc` and seven-day lookback | Version/identity-qualified final delivery for registration, confirmation and published team boards, without age-stranding | A2 Ark; preserve result/audit data and distinguish ended/awaiting-result from fully finalised |
| Ark tracked restoration uses `bot.add_view`; registration handlers reject Cancelled/Completed at their current checks | Verify final action-boundary rechecks as well as local handler restoration; do not claim visible-board edits from add_view | A2 Ark; original accepted callback remains accepted; admin-add response timeout is a separate observation |
| Voting/surveys close domain state then edit disabled board and send announcement; due selectors read Open only | Persist independent final edit and announcement outcomes; failed/unknown delivery survives close and restart | A2 votes/surveys; unknown sends are held, not blindly resent; include manual close/reopen/delete |
| Calendar pinned overview keeps a rolling 30-day window; broad fetch/edit failure can replace its tracked identity | Preserve identity on transient/unknown failures; distinguish confirmed deletion and intentional replacement | A2 calendar; overview stays active; event messages/reminders/private responses have different lifecycles |

Reuse the small `core/board_lifecycle.py` eligibility vocabulary, existing owned
execution, refresh coordination and delivery receipts. Domain services decide
completion; DAL stores generation, identities, final payload and outcome. A shared
contract is not a universal scheduler or a second retry framework. Test real caller
adapters and mismatched semantics before adoption, not helper tests alone.

Ark policy options for its implementation: (1) recommended ended/awaiting-result,
with roster refresh stopped and explicit result finalisation; (2) explicit no-result
finalisation with a durable operator reason. Do not silently choose a timeout or
erase the ability to record a late result. A correction after finalisation needs a
separate revision/message policy to preserve the immutable historical board.

## A2 acceptance and sequencing

1. Revalidate domain caller/SQL definitions and select one bounded domain slice.
2. Establish current active, awaiting-finalisation, held and retired inventory;
   explain old eligible rows. No blanket age deletion or live inventory mutation.
3. Cover stale controls, final edit interruption, partial targets, identity races,
   missing versus inaccessible messages, cancellation, restart and retirement.
4. Prove repeated restart causes zero network work for finalised history, while
   calendar's rolling overview remains live and Ark can accept late results.
5. Measure SQL reads and Discord fetch/edit counts, plus per-state inventory;
   qualify the actual native SQL contract and separate Changes review per repo.

Preserve CFG-51421/configuration choice, Report63 queue closure reconciliation,
audit/cleanup gaps, R12 atomic writers/cross-process IO ownership, receipt scaling,
A3 policy work, B/C, natural acceptance and P0. None is silently closed here.

## Historical A1b planning record


Date: 28 October 2026. **Current status: A1a deployed and exercised flows verified.**
Private runtime: `87c1b39325daaa0ca1a8c0cbca656df82d7fa46b`. Read the
[deployed closeout](P1%20MGE%20A1a%20-%20Deployed%20Closeout%20-%202026-10-28.md) and
[focused A1b scope/handoff](P1%20MGE%20A1b%20-%20Scope%20and%20Handoff%20-%202026-10-28.md) first.
This document retains the wider programme boundary. A1a dataset reuse/timing is
delivered; the [A1b architecture and delivery packet](P1%20MGE%20A1b%20-%20Design%20and%20Delivery%20Packet%20-%202026-10-28.md)
is now prepared for approval before runtime changes. Do not repeat deployment,
restart or accepted business actions. The handover documents are merged through
mirror PR 455/private PR 703; the new A1b design and subsequent amendments remain local.

## Historical A1: responsiveness and refresh proposal, now delivered

Use the retained production sample and deterministic fixtures. Instrument/measure
separately: interaction age at handler entry, initial response await, worker/event
ownership wait, DAL work, public/leadership payload reads, Discord fetch/edit, and
final response. Preserve a correlation reference without logging tokens or private payloads.
Do not equate nested acknowledged callbacks with fresh network acknowledgements.

A1a now reuses a qualified leadership dataset for rendering/readiness. Evaluate the boundary
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
remains open in Reports 61 and 62. Do not choose or execute that decision automatically.
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

## Historical handback requirements for the original A1b scope

Return evidence versus hypotheses; caller/ownership map; reusable architecture; bounded
PR order; measurable acceptance; test/security routing; SQL/deployment implications;
and disposition of every closeout ledger row. Include a read-only plan for missing
mandatory MGE audit/cleanup evidence, without treating its absence as retry authority.
Do not expand to all P1 implementation merely because the programme is approved.

After A: Batch B covers remaining writers/executors, singleton, cache/JSON/queue
ownership; Batch C covers external monitoring and supported recovery tooling.
R03/R04/R13 natural/historical checks and P0 R17 remain parallel acceptance lanes.
R18 on f6a929c remains accepted; new-runtime import/export evidence is separate.
