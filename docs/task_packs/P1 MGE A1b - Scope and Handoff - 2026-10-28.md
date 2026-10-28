# P1 MGE A1b: scope and handoff

> **Design pass completed:** Read the [approval-ready design and delivery packet](P1%20MGE%20A1b%20-%20Design%20and%20Delivery%20Packet%20-%202026-10-28.md).
> It resolves the caller map, outcome wording, qualified-read prerequisites,
> refresh/recovery ownership, two-PR order and acceptance gates. The final framework
> review adds shared publication/refresh identity ownership and conditional ID writes;
> the revised scope awaits approval. This original handover remains evidence and scope history;
> the 28-document handover is merged through mirror PR 455/private PR 703.
> This design packet and subsequent amendments remain local. See its custody table
> for verified merge identities; the documentation merges did not restart the bot.

Date: 28 October 2026. Status: focused review/scope and architecture preparation
authorized. The operator wants the most effective complete A1b framework, with
documentation current and a new chat. This handoff does not authorize runtime
implementation, live SQL/provider work, deployment or another restart. Produce one
coherent approval-ready design and implementation packet; avoid fragmented approval
requests for routine choices that can be resolved from evidence.

Read the [A1a deployed closeout](P1%20MGE%20A1a%20-%20Deployed%20Closeout%20-%202026-10-28.md)
first, then the [A1a implementation record](P1%20MGE%20A1a%20-%20Implementation%20and%20Validation%20-%202026-10-28.md),
[shared contract](../reference/p1-operation-lifecycle.md),
[complete ledger](P1%20MGE%20Lifecycle%20-%20Accepted%20Closeout%20-%202026-10-28.md)
and [wider Batch A scope](P1%20Batch%20A%20Remaining%20Discord%20Domain%20-%20Scope%20-%202026-10-28.md).
Read AGENTS.md/core references and applicable specialist skills. Historical records
must not override the new checkpoint or erase outstanding evidence.

## Objective and measured starting point

Make MGE confirmation independent of slow board delivery while preserving truthful
mutation outcomes, valid datasets, original message identity and owned execution.
Start from private deployed `87c1b39325daaa0ca1a8c0cbca656df82d7fa46b`, with
mirror equivalent `1f072b6cae5342d0f6a1eafb98a6751db1703b2f`. Reconcile actual
checkout/history before work; do not mix private and mirror history.

The live rank callback took 11.311s, including sequential public/leadership refreshes
of 4.809s and 3.820s before the private reply. Its worker took 0.026s and its initial
acknowledgement 1.439s. The saved-response ordering is the actionable dependency;
neither these samples nor the separate 42s gateway warnings identify a global cause.
Signup/edit/withdraw already acknowledge and report independently of background
refresh in exercised paths: preserve those behaviours and reuse their contracts.

## Recommended bounded work packages

| Package | Scope and decision | Acceptance gate |
|---|---|---|
| B1: qualify public data | Adopt explicit valid-empty, valid-populated, unavailable and incomplete outcomes for every read required by public signup rendering; define invalid/cross-event handling without treating unavailable as empty | Failed preparation performs no Discord send/edit, ID replacement, notification or destructive cleanup; successful-empty policy remains intentional |
| B2: saved response | Map every simplified and legacy leadership mutation callback; report only the actual service result before waiting for board IO | A blocked refresh cannot block a confirmed-result reply; failed/unknown writes never claim saved or invite blind retry |
| B3: refresh coordination | Reuse/extend current request helpers and CoalescedWork only where needed; specify target keys, ownership, dirty follow-up and completion outcomes | Latest requested state eventually rendered; no lost dirty signal, duplicate send or incorrect cross-target coalescing; other events progress |
| B4: evidence and compatibility | Extend A1a harness and deterministic concurrency tests; validate a second real caller for any shared helper change | Same meaningful mutation/audit semantics with reduced response coupling and no extra unbounded work |

B1 is a prerequisite for public refresh-policy changes, not optional polish. B2/B3
must be designed together so an early reply does not orphan the refresh. B4 accompanies
each package. Prefer one coherent PR if small enough; otherwise sequence B1 then B2/B3
with explicit dependency and independent tests. Do not split by file count alone.

Indicative planning scores (1-5; judgement, not measured frequency): B1 impact 5,
frequency 4, risk reduction 5, effort 3 = 11; B2 5/4/4/3 = 10; B3 4/4/5/4 = 9;
B4 4/4/5/3 = 10. Dependency/safety gates take precedence over scores.

## Caller and architecture review required

Verify actual callers and produce a matrix covering entry/ack, permission/form
ownership, mutation authority/outcome, locks, saved response, refresh targets,
delivery evidence and shutdown/restart disposition. Include:

- `ui/views/mge_simplified_leadership_view.py`: rank, targets, admin add, reject,
  promotion, reset and confirmations; distinguish calls that already queue refresh.
- `ui/views/mge_roster_builder_view.py` and other discovered legacy roster callers;
  `ui/views/mge_signup_view.py`, `mge_simplified_signup_form_view.py` and modal paths.
- `commands/mge_cmds.py`, `mge/mge_scheduler.py`, publication and manual refresh.
- `mge/mge_embed_manager.py`: `request_signup_refresh`, `request_board_refresh`,
  `_serialize_board`, `refresh_mge_boards`, individual board sync and `drain_refreshes`.
- `core/coalesced_work.py`, `core/owned_work.py`, `core/interaction_safety.py`,
  `core/operation_outcome.py`, `core/operation_timing.py`, `mge/mge_roster_execution.py`
  and the existing event-delivery journal/identity service.

Views route interactions. Domain services determine outcomes. DAL owns persistence.
The existing board coordinator owns presentation work; do not introduce a general
job framework or another detached-task path. Shared abstractions need a second real
consumer test; that does not authorize rewriting unrelated domains.

Specify before coding:

1. Which existing service result is sufficient to say saved for each operation.
   Legacy Boolean roster paths are not automatically atomic durable-receipt contracts.
2. How the owned refresh is registered once the result is known, including private
   reply failure/cancellation. Reply failure must not lose necessary refresh work;
   background failure must not revoke a committed result or rerun the mutation.
3. A minimal outcome vocabulary separating mutation saved/failed/unknown from board
   pending/delivered/failed/unknown. Do not promise board delivery when merely queued.
4. Keys including bot/event/destination/board kind as required by current semantics;
   preserve notification identity, mention policy and publication boundaries.
5. Dirty-during-run sequencing: use current authoritative data for a follow-up, never
   a retained stale form snapshot; preserve later requests on failure/cancellation.
6. Shutdown ownership and restart recovery. SQL and journal remain authoritative;
   in-memory coalescing is not a durable queue. Identify how normal startup/scheduler
   reconciles missing presentation without replaying a business mutation.
7. Lock ordering and bounded work: release mutation ownership after its entered worker
   drains; no SQL/event thread owner held across Discord awaits; per-target board
   serialization and unknown-send fence remain intact.

## SQL and refactor boundaries

Validate all read/identity contracts against `C:\K98-bot-SQL-Server` before implementation:
MGE events, signup review, signups, awards, relevant audit/cleanup and persisted message
identities. A1a source authority revision is historical, not proof of current SQL state.
No schema/index migration, admission-policy change or new transaction model is presumed.

Classify touched direct SQL, view business rules, duplicate helpers, dead branches,
fragile state and missing error logs as fix-now/defer/not-applicable. Keep broader
R12 cross-process roster atomicity and R16 receipt-query scaling separate. Preserve
A1a hidden automatic-placement writer ownership and qualified readback. Publication
still performs fresh validation; displayed readiness never grants publication authority.

## Required proof matrix

| Scenario | Required observation |
|---|---|
| Slow/blocked board IO after known success | Private saved result delivered before releasing a deterministic board barrier; later original-board refresh completes |
| Reply fails after mutation | No duplicate mutation; owned refresh remains tracked; uncertainty concerns the response, not an invented rollback |
| Failed or unknown mutation | Accurate private result, no success claim, no mutation retry; refresh policy explicitly justified |
| Public read fails/partial/wrong event | Prior board/IDs retained; unavailable cannot become empty; no delivery side effects |
| Valid empty/populated | Existing content/lifecycle/mentions preserved; intentional empty handling tested |
| Concurrent scheduler/manual/user refresh | Compatible requests coalesce; target distinctions retained; a later dirty request produces a fresh follow-up |
| Different events/targets | No accidental global lock; independent progress with correct identity |
| Cancellation during worker/refresh | Entered worker drains; owner not released early; presentation cancellation/failure remains observable |
| Restart with pending or unknown delivery | Existing journal and startup reconciliation preserve identity/uncertainty; no blind resend or business replay |
| Permissions, stale forms, duplicate clicks | Current authorization and owner checks preserved; rejected inputs cannot enter a mutation |
| Shared helper change | Existing event-delivery or another actual caller passes compatibility/concurrency tests |

Use deterministic barriers/fake clocks for ordering assertions, not sleep-based timing
tests. Extend existing tests rather than duplicating implementation. Select actual
MGE dataset/board/signup/leadership/roster tests, coalesced/owned-work tests and event
delivery tests after the caller inventory. Required pre-PR gates: architecture,
deferred register, security routing, test selector; focused/full pytest as selected,
smoke imports and registration where applicable. Keep production logs unchanged.

Benchmark sequential baseline/candidate runs on the same host with the same frozen
harness, at least 30 samples per representative 0/4/15/30-row and overlap case.
Record source/harness hashes, raw samples, p50/p95, dataset/connection/edit counts,
mutation/reply counts, worker/owner waits, response and end-to-end delivery timing,
and event-loop lag. Do not buy shorter private latency by dropping refresh, hiding
failure, adding unbounded tasks or worsening retained work. Compare structural
ordering and counts first; avoid arbitrary production SLA or speedup claims.

## Explicit exclusions and evidence follow-ups

- Report 62 queue closure: existing-incident recheck only as an operator follow-up;
  no automatic release/cancel/replay. Older configuration choice remains operator-owned.
- Gateway lag: bounded separate investigation. Reuse passive evidence where possible;
  no causal claim from concurrent recovery activity. Only bring a proven A1b-path
  blocking operation into scope with explicit evidence and review.
- Priority selection: unresolved ordering/observability question. Compare dispatch,
  component state, form identity and telemetry batching; add an implementation fix
  only after reproduction/evidence and scope review. No speculative default selection.
- Ark admin-add, voting/calendar, R11 policy, R12 atomic writers, R16 scaling, Batch
  B/C, natural event acceptance and P0 F04/F01-F05 remain separate.
- Missing mandatory MGE audit/cleanup evidence gets an exact read-only reconciliation
  plan, not a new signup/withdrawal/restart to manufacture acceptance.

## Security, release and first handback

Scope/docs-only change: documented security skip. Runtime implementation will touch
Discord/DAL/restart-sensitive work: use k98-security-review-routing, then exact Bot
Changes review, Deep off. Separate SQL diff review only if SQL changes are approved.
Retain current permissions, data privacy and redacted operation references.

Check updater source protection early in the design. A1a introduced an exact 12-file
bundle; changed protected source may require a separately validated updater addition.
Never rewrite historical pins, relax admission checks or assume ordinary source
promotion suffices. Inspect the actual protected file inventory before planning release.
Mirror-first PR, equivalent patch promotion, review/comment resolution, final-head
checks and deployment instructions follow only after implementation authorization.

The new chat's first completed deliverable is one approval-ready packet: verified
baseline/caller map, concrete UX/outcome contract, package boundaries, SQL/refactor
decisions, refresh ownership/state transitions, failure matrix, benchmarks, security
and updater implications, and disposition of every carried ledger row. Recommend
routine choices with reasons; ask only for material product/policy decisions. Do not
implement runtime changes while preparing that packet or repeat accepted deployment.
