# P1 Discord/domain completion and MGE: next phase scope

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

> **Historical status - 28 October 2026, A1a deployed:** Mirror PR 454 and private
> PR 702 are merged; private `87c1b39325daaa0ca1a8c0cbca656df82d7fa46b` is deployed
> and Discord online. Signup/edit/withdraw are verified on this runtime. A1a qualified
> datasets and timing are delivered; the A1b design packet is prepared for approval.
> Rank confirmation still waits for board refresh. Report 62 queue closure, the older
> configuration decision and separate Discord lag remain follow-ups. Exact audit/cleanup,
> unexercised cases, fresh import/export, natural acceptance and P0 remain explicit.
> See [deployed closeout](P1%20MGE%20A1a%20-%20Deployed%20Closeout%20-%202026-10-28.md) and [A1b design packet](P1%20MGE%20A1b%20-%20Design%20and%20Delivery%20Packet%20-%202026-10-28.md).
> Earlier dated status and next-action text is historical where superseded.
> This documentation update requires no deployment, restart, SQL apply or repeat import.

Date: 28 October 2026. **Stage: review/scope only.** The previous monitoring/import/export
phase is accepted at private `f6a929c0597ce257ce18380af1ab6f7ad8ddcc5d`.
MGE-01 is first in delivery batch A. Do not reopen completed imports or the original Ark callback.

## Established observation and unresolved cause

The supplied 27 October log records simplified signup submitted at 07:26:07 UTC, a review
count of four, and an updated event embed. `mge_withdraw` follows at 07:26:17. At 07:26:20,
`core.interaction_safety` fails sending an ephemeral response with Discord 404/10062,
Unknown interaction. A later review count of three and event-embed update follow.
This suggests a failed confirmation around withdrawal; it is not proof that signup or withdrawal
failed to persist. Correlate exact signup/audit state before deciding which mutation succeeded.

The simplified signup submit callback currently invokes synchronous service work before its
initial interaction response. That is a candidate late-acknowledgement risk, not a proven cause
of the observed withdrawal failure. Trace the actual withdrawal path and response ownership.
Historical status 10015, Ark timeout-disable warnings and SQL contention are distinct observations.
Include a shared helper only if evidence establishes the same lifecycle defect.

## Required scope investigation

1. Revalidate deployed/main source and the complete MGE command/view/service/DAL call graph.
2. Map submit, edit, withdraw, administrator variants, modal/select callbacks, repeat clicks,
   stale events and persistent-view restoration: acknowledgement, validation, SQL ownership,
   commit receipt, user confirmation, embed refresh, cancellation and restart.
3. Establish when the interaction is acknowledged, which task owns each response, whether
   blocking service work occupies the event loop, and what happens if response/edit/refresh fails.
4. Correlate available exact MGE signup/audit rows with the reported attempt using read-only
   evidence. If unavailable, retain that limitation and distinguish deterministic reproduction
   from historical production attribution. Never manufacture a new signup to diagnose history.
5. Inventory same-pattern callers beyond the reported button. Classify each as proven defect,
   already protected, evidence missing, unrelated or deferred, with file/line and test evidence.
6. Produce a bounded correction proposal and implementation/test/acceptance plan. Stop for
   scope agreement before implementation, PR writes, SQL/provider operations or production changes.

## Affected layers and authoritative contracts

| Layer | Candidate inspection / responsibility |
|---|---|
| Commands and views | `commands/mge_cmds.py`, MGE views/modals in `ui/views/`; acknowledge promptly and own one response lifecycle; no business SQL in callbacks |
| Service | `mge/mge_signup_service.py` and refresh/publication services; validation, mutation outcome and separately retryable presentation |
| DAL | MGE repository/DAL; exact commit/rollback, idempotency and audit contract; no automatic replay on uncertain write outcome |
| Shared interaction helpers | `core/interaction_safety.py` and callers; inspect response/followup ownership, failure classification and cancellation before changing shared behavior |
| Persistence | SQL source of truth `C:\K98-bot-SQL-Server`: `dbo.MGE_Signups`, `dbo.MGE_SignupAudit`, `dbo.MGE_Events`, `dbo.v_MGE_SignupReview` |

The SQL definitions include a filtered active-signup uniqueness constraint for event/governor.
Verify current definitions, permissions and audit semantics before design. A unique index alone
does not prove lost-response retry safety. No SQL migration is presumed necessary.

## Correction acceptance criteria to refine after diagnosis

- Acknowledge interaction before potentially slow work where the Discord flow allows it;
  define one owner for initial response, defer, followup and edit.
- Keep acknowledgement retry, read-only reconciliation, business mutation and embed refresh
  separate. A confirmed mutation followed by lost reply must not become a duplicate mutation.
- Reconcile ambiguous commit with exact durable evidence; use bounded pause/retry only where
  non-entry/rollback or idempotency is established. Retain uncertainty otherwise.
- Show truthful saved/withdrawn/waiting/unknown/failed states and a safe next action. A late
  message refresh must not falsely report a failed signup or overwrite a newer event state.
- Preserve permissions, user/governor ownership, event eligibility, limits, original audit
  receipts, persistent-view behavior and existing user-facing semantics unless approved.

## Tests, refactor triggers and PR boundaries

Select focused MGE/interaction/service/DAL tests from the actual changed paths. Cover slow SQL,
reply failure after commit, failure before mutation, concurrent/repeated clicks, stale view,
unauthorized actor, event closure, cancellation, restart and refresh failure independently.
Prove one mutation/audit effect where appropriate; do not merely mirror implementation.
Use deterministic fixtures first. Live acceptance follows an approved normal operator workflow,
with visible reply, exact state/audit and refreshed embed, without replaying an ambiguous attempt.

Review MGE subsystem and shared-helper refactor triggers. Reuse existing service/DAL and
interaction ownership helpers if they fit; do not add a second retry/transaction framework.
Keep unrelated domain policy changes and durable-delivery redesign in separate scope-sized PRs.
Inventory related paths now so a fix does not merely move the failure to the next callback.

Before PR: architecture/deferred/test-selection/security-routing checks; command registration,
smoke imports and focused/full tests as justified by the resulting change. Interaction/data-access
changes require a per-repository Changes review, Deep off, or a precise documented routing skip.
SQL changes, if justified, need a separate SQL diff and deployment order. Patch-promote to private
main only after mirror review/validation. Deployment and actual operator acceptance are distinct.

## Required handback

Return: cause/evidence and uncertainty; complete same-family conflict/lifecycle map; scoped
files/contracts; implementation batches; tests; rollback and operator smoke steps; exact ledger
rows closed, still open and deferred. Preserve the full R01-R18/MGE-01 ledger and all three P1
families. No claim that completing MGE alone completes batch A or the programme.

Related: [accepted closeout](P1%20Monitoring%20and%20Import%20Export%20Reliability%20-%20Closeout%20-%202026-10-28.md) | [next scope](P1%20Discord%20Domain%20Completion%20and%20MGE%20-%20Scope%20-%202026-10-28.md) | [chat starter](P1%20Discord%20Domain%20Completion%20and%20MGE%20-%20Chat%20Starter%20-%202026-10-28.md).
