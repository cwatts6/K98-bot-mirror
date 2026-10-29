# P1 MGE A1b: design and delivery packet

Date: 28 October 2026. **Revised scope approved; local implementation in progress.**
The operator explicitly approved the revised scope including publication/refresh
identity protection, recovery progress and evidence mapping. Local implementation
and validation are authorized; remote
publication, merge, protected updater installation, deployment and live operations
remain separate. No production action was performed during this review.

**Final framework review, 28 October:** source review found a material
publication/refresh identity race. The operator subsequently approved the bounded
presentation ownership and conditional identity-write contract below, together with
recovery progress and requirement-to-evidence mapping. The earlier conditional
offer has been superseded by that explicit implementation approval.

## Scope summary and recommendation

Deliver two dependent Bot PRs: **B1 qualified presentation data**, then **B2/B3
truthful immediate results and owned refresh**, with B4 proof in both. Keep the
second package together: an early reply without owned follow-up and restart
reconciliation is incomplete. Prepare one combined production release after both
are reviewed, unless an intermediate release is separately requested and qualified.

The user-visible change is an immediate, accurate private action result after the
service settles. Board refresh follows independently. Explicit Refresh commands
still report actual refresh outcomes. Publication retains its own fresh admission,
notification and final-result contract. No new generic job system, SQL migration,
dependency, environment variable, activation change or top-level command is proposed.

The scoped service/DAL result corrections below are prerequisites, not a claim
to solve R12 cross-process atomicity. Roster policies, placement order, permissions,
existing message identity and uncertain-send fences remain unchanged.

The additional coordination covers publication's board identity transition only.
It does not redesign publication transactions, notifications, reminders or business
replay. Keep the two-PR structure; include the shared ownership integration in
PR 2 before enabling independent refresh/recovery.

## Verified baseline and custody

| Evidence | Disposition |
|---|---|
| Current Bot base | Clean `main` at `51cab280aaaaf62b2d3a8d1fe17ee92442aaed34` before this documentation work; local scope branch `codex/p1-mge-a1b-design` |
| Preserved handover | Source worktree clean at immutable `4c77c9291e0aa1f44f64c2602ac0633cf8717b7e`; read only; its 28 Markdown changes imported by exact patch, without importing private ancestry |
| Patch custody | SHA256 `c4b4a9e1c302944739178bc6a6f56c6eb43d1ae9a2f02e3db87ef60cf1ecd6ef`; patch passed `git apply --check` before application |
| Remote protection | `origin` fetches mirror, but push is disabled with `no-push://private-checkout-mirror-disabled`; `production` points to private repository. Preserve this setup. Future mirror PR work needs a suitable mirror checkout; do not bypass the push guard |
| Runtime baseline | Handover verifies mirror PR 454 / `1f072b6c`, private PR 702 / deployed `87c1b393`, protected successor 79 and Discord online; no fresh host interrogation in this task |
| SQL source | Clean `C:\K98-bot-SQL-Server` at `7e91989f619deb46836194c7e705b0a9eb2ebe11`, rechecked in this task; source verification is not a live database inspection |
| Merged handover baseline | [Mirror PR 455](https://github.com/cwatts6/K98-bot-mirror/pull/455), merge `8db65da6cc7f4a7b77d0f78944ed4f51fc5d5018`; [private PR 703](https://github.com/cwatts6/K98-bot/pull/703), merge `07d5dd17fce7384de02c73551a8c5b8f3c15f2ac`. All 28 handover Markdown blobs match between those merges and fetched mirror `main` at `8ce3234c54fccebea018ac95f49a2d5076db68c5` |
| Local additions | This design packet, scope findings and navigation/status amendments remain local. The already-merged handover must not be published again as new work |
| Live measurements | Rank callback 11.311 s; worker 0.026 s; public/leadership refresh 4.809/3.820 s before reply. One observation establishes ordering, not p95, regression or global causality |

Initial custody recheck: the source chat independently moved its clean handover
worktree to `f6c358046e69cd214c022f4c9ea9d779480e1157` during this review. Its
complete tree diff against the pinned `4c77c9291e0aa1f44f64c2602ac0633cf8717b7e`
is empty. This task used the exact pinned patch and did not modify that worktree;
the changed commit identity supplies no additional runtime or acceptance evidence.

Subsequent merged-baseline reconciliation supersedes that initial publication state.
Fetched both exact merges without resetting or changing the local branch ancestry.
Both merged trees match their reviewed heads (`bde814c7` mirror, `8ca8df07` private).
The refreshed mirror has a new snapshot history; content comparison, not ancestry,
establishes equivalence. Its Python sources match the source-review base above.
Applied the two merged runbook heading corrections and preserved all local design
additions. Future implementation must start from the current suitable mirror base
and carry only the remaining design delta, not repeat the 28-file publication.
The handoff chat reports final production Quality of 10,166 passed, 1,240 skipped,
19 warnings and eight subtests, plus passing secret scan and clean final reviews.
These are supplied publication receipts, not tests rerun for A1b. Git content was
verified here; an independent GitHub API metadata check was unavailable. No new
deployment/restart accompanied these documentation merges. Deployed runtime remains
`87c1b39325daaa0ca1a8c0cbca656df82d7fa46b` according to the handoff evidence.

The [deployed closeout](P1%20MGE%20A1a%20-%20Deployed%20Closeout%20-%202026-10-28.md)
supersedes pre-deployment wording in retained release artifacts. Keep the
[handover](P1%20MGE%20A1b%20-%20Scope%20and%20Handoff%20-%202026-10-28.md),
[A1a validation](P1%20MGE%20A1a%20-%20Implementation%20and%20Validation%20-%202026-10-28.md)
and [accepted ledger](P1%20MGE%20Lifecycle%20-%20Accepted%20Closeout%20-%202026-10-28.md).
Raw reports, screenshot, deployment transcript and operational identifiers remain
in private evidence storage. No raw evidence is part of this documentation patch.

## Findings that determine the design

| Source at base | Finding and consequence |
|---|---|
| `mge/mge_simplified_flow_service.py::get_public_signup_rows` | Review plus award reads use legacy fallback contracts. Failed review can look empty; failed award read can expose rejected entries. Both inputs must qualify before rendering |
| `mge/dal/mge_event_dal.py::fetch_event_for_embed` | Exception and absent event both return `None`. Add strict qualification; valid missing event is not valid empty signup data |
| `mge/dal/mge_event_dal.py::fetch_public_signup_names` | Unlike simplified reads, SQL exceptions already propagate through `run_query`. Preserve that; qualify shape and identity before reducing rows to names |
| `file_utils.py::fetch_all_dicts` | Missing cursor metadata becomes `[]`, even through a strict caller that only propagates exceptions. Adopted DAL reads must qualify result-set metadata before accepting an empty result |
| `mge/dal/mge_leadership_dal.py::fetch_leadership_embed_state` | A second event read can turn failure into zero IDs. Use the first qualified event snapshot for identity, or a strict identity read; never treat a failed read as permission to create |
| `mge/dal/mge_publish_dal.py::fetch_awards_with_signup_user` | Awards read catches exceptions as an empty list. Targets currently refresh awards too, so its qualification belongs in B1 before those callers are queued |
| `mge/dal/mge_roster_dal.py::update_award` | Returns `True` for any non-None affected count, including zero. A Boolean alone cannot justify saved-result text |
| `mge/mge_roster_service.py` | Add and move-to-waitlist ignore audit return values; rejection can save status then fail audit. Multi-step outcome needs confirmed-step evidence |
| `mge/mge_simplified_leadership_service.py` | Swap/reset perform separate writes; target regeneration failures are ignored. Partial completion must not be described as complete or rolled back |
| `ui/views/mge_simplified_leadership_view.py` | Rank, targets, waitlist, promotion, rejection and reset await boards before private result. Target generation/override use `drain_thread`, bypassing the roster async owner |
| `ui/views/mge_roster_builder_view.py` | Nine mutation paths load a private roster snapshot before replying; they do not currently refresh public boards. Do not silently add public refresh or audit-only rejection effects |
| `core/interaction_safety.py::send_ephemeral` | Returns `None` and logs ordinary send errors. Such errors usually allow existing signup refresh registration to continue; cancellation/escaping errors still require explicit finally ownership. A returned call is not proof the reply was delivered |
| `core/coalesced_work.py` | Existing revision loop handles newer requests and failure followed by dirty work. Raw task cancellation can bypass that loop; protect shared ownership. A dictionary of false board results is not `False` and escapes its failure counter |
| `mge/mge_event_service.py::sync_mge_events_from_calendar` | Only calendar starts in `[now, now + 7 days)` feed normal board refresh. This is not complete crash recovery for started/completed or calendar-missing events |
| `bot_instance.py::_graceful_teardown` | Private operations drain before refreshes, but direct scheduler refresh can still enter until task cancellation later. Close background admission first while allowing already admitted action follow-up |

## B1: qualified presentation contract

Use existing `MgeDatasetError` and A1a availability vocabulary: `loaded_empty`,
`loaded`, `unavailable`, `incomplete`. New MGE-specific preparation belongs in
`mge/mge_board_preparation.py`; DAL executes parameterized reads, service preparation
validates/combines them, embed manager performs Discord IO. No Discord types in
the preparation or business services. Reuse current renderers and ordering helpers.
Strict DAL reads must verify the expected result-set columns before mapping rows,
including zero-row results. Use a small MGE DAL-local qualified-read helper with
explicit columns and existing connection custody; do not change global row helpers
or accept a missing result set as valid empty. Cover both public read branches.

| Board/dependency | Qualification and policy |
|---|---|
| Public event/variant/rules/lifecycle/IDs | Strict event read, exactly matching positive EventId, required lifecycle values and valid paired persisted IDs. Missing event is explicit unavailable-to-render; nullable rules remain supported. Invalid date/status must not default to open controls |
| Simplified public signup rows | Strict review and award reads, matching EventId, positive SignupId/GovernorId, unique join identities, valid persisted status and required fields. Keep ordering, rejected filtering and Unicode names. No automatic placement in this read path |
| Legacy public names | Read EventId/SignupId with name before projection to names so identity/duplicates can be checked. Required identity failure blocks render. Preserve existing successful ordering and non-disclosure behavior |
| Leadership | Preserve A1a strict preparation/hidden-writer owner and freshness. Obtain saved identity from qualified event data; do not reintroduce empty-on-failure identity reads |
| Awards | Strict publication-context plus awards/signup-user reads, event membership, status, target and identity validation. Preserve announced-versus-silent semantics and publication version |
| Views and final payload | An expected active view that fails construction is incomplete, not intentional removal. Validate complete payload before channel fetch/send/edit or ID updates |

Valid empty includes all-active-signups-filtered-as-rejected for public rendering.
It keeps the existing empty content and lifecycle controls. Missing optional KVK
rank/gear data remains a supported warning, not a dataset outage. An award for an
inactive signup can legitimately be absent from the active review view; do not
reject all such historical rows as corruption. Conflicting matches or malformed
required identities are incomplete. No global transaction/snapshot claim is made
for separate reads; signup writers and other processes remain competing writers.

On any failed qualification: preserve prior content and SQL IDs, issue no Discord
fetch/send/edit, no notification, no destructive cleanup and no business retry.
Return stage and safe reason for the caller. A later independent refresh can reread.
Do not cache a prepared dataset across requests or reuse it as publication authority.

## Caller, response and owner matrix

All mutated callback paths retain early private acknowledgement, final role/actor/
target checks and owned off-loop execution. Modal openers keep prepared-modal
semantics. Selectors and confirmations retain their actor binding and duplicate
guards. Symbols P/L/A below mean public signup / leadership / awards board.

| Entry points | Current service/evidence | A1b response and refresh disposition |
|---|---|---|
| Simplified `_AdjustRankModal.callback` | `set_rank` / atomic rank writer with audit | Qualified rank result first; P+L owned request |
| `_GenerateTargetsModal.callback`, override nested modal | `generate_targets_from_rank1`, `override_target_score`; target writer groups target/audit, generated count may be partial | Route through `run_roster_mutation(event_id, ...)`; verify event membership/counts; result first, P+L+A as today |
| `move_waitlist` notes submit | `move_to_waitlist`; update then separate audit | Preserve confirmed primary/audit evidence separately; P+L after settled change |
| `move_roster` free-slot and full-roster swap confirms | `move_waitlist_to_roster_with_optional_demote`; atomic free-slot promotion, multi-call swap, optional regeneration | Complete/partial/unknown result first; P+L; do not retry demotion/promotion or hide regeneration failure |
| `reject_signup` notes submit | `reject_signup`; status/insert then audit | State changed with audit failure is partial; qualified P+L follow-up, no duplicate rejection |
| `_ResetRanksConfirmView.confirm` | `reset_active_ranks`; per-row writes and regeneration | Report exact confirmed count or uncertainty; P+L; consume confirmation after entered/unknown work, not only success |
| `admin_add_signup` | Simplified form or legacy admin-add/final modal calls atomic signup service; dependencies already request boards | Preserve path-specific P+L versus P-only target; register regardless of private response outcome; preserve DM policy |
| Simplified form, legacy `MgeSignupFinalModal`, edit view/forms | `create_signup`/`edit_signup` and existing `ServiceResult.outcome` | Committed-only saved result; P or P+L from dependencies; keep simplified DM suppressed, legacy DM contract separate |
| `MGESignupView.withdraw` single row and nested multi-select | `withdraw_signup`; atomic signup/audit/award cleanup | Committed-only withdrawn reply; existing target set; no retry on unknown |
| Legacy roster builder add, set rank, to waitlist, move to roster, set waitlist order, notes, remove, undo, audit-only reject | Corresponding `mge_roster_service` calls; `_load_embed` follows most successful results | Immediate qualified text result without waiting for `_load_embed`; retain existing Show Roster action for the optional snapshot. Do not add public refresh or change audit-only reject to status rejection |
| Rules edit modal / reset | `mge_rules_service`, then awaited signup refresh at persisted channel | Qualified rules result first; silent P request at same persisted destination; preserve rule-length and leadership checks |
| Mode-switch open/fixed confirmations | `switch_event_to_open/fixed`; existing atomic DAL and callback request | Preserve destructive confirmation and final service policy; use same result/follow-up adapter; do not change data deletion policy |
| Simplified manual Refresh; signup Refresh; signup leadership-center opener; `/mge` leadership-center command | Explicit request to refresh a selected target | Await that target's qualified outcome; never say refreshed merely because queued; acknowledgement remains early |
| `MGELeadershipBoardView.refresh_pool` and launch roster builder | Private review/summary reads, no persistent board delivery | Preserve read-only behavior; use qualified data/error output where touched; no success mutation language |
| Scheduler `schedule_mge_lifecycle` | Calendar sync then direct P and optional L sync | Keep 300-second cadence and existing creation notification semantics. Reuse refresh ownership for compatible silent requests; report real results, not unconditional `synced += 1` |
| Publication/unpublication via both UI variants and `MgePublishDiscordAdapter` | Fresh readiness, publication writes, publication-specific messages/DMs, awaited P+L+A refresh | Keep publication awaited and outside mutation-refresh coalescing. Qualify shared rendering; distinct notification/version semantics must not be overwritten by silent refresh requests |
| Manual award-reminder command | Separate reminder refresh with existing recovery/repost rules | Compatibility tests only. Do not generalize its explicit policy into board replacement |
| Completion/reopen, commander admin, imports, DM attachments | Other MGE workflows outside the identified ordinary board-refresh adoption | Inventory retained; no result-contract or domain rewrite in A1b. Existing shared-helper compatibility required |

Commands/services/views outside the changed rows are not silently adopted merely
because they are MGE. Re-run the reference search before coding to catch new callers.

## B2: exact action result and user-facing contract

Preserve global `MutationOutcome` for evidence-backed transaction settlement.
Introduce an MGE domain result envelope in `mge/mge_action_result.py`, consumed by
the adopted services and a small Discord adapter in `mge/mge_action_response.py`.
It carries action disposition (`completed`, `not_entered`, `rolled_back`, `partial`,
`unknown`), confirmed primary steps/counts, audit outcome, required secondary-work
outcome and refresh eligibility. It is not a durable receipt or replay key.
Existing public result fields can remain compatible, but no generic conversion
from `success=True` to `MutationOutcome.COMMITTED` is permitted.

| Evidence | Allowed statement / example |
|---|---|
| Atomic signup service `COMMITTED` | "Signup saved. Board refresh is pending." / "Signup withdrawn. Board refresh is pending." |
| Rank transaction returned success after commit context; required audit included | "Rank updated. Board refresh is pending." |
| Every required legacy write positively acknowledged, expected affected rows and required audit accounted for | Exact action result; no assertion of one atomic transaction or durable operation receipt |
| Validation refused before any writer, including preparation writers | Specific refusal, with "No change was made" only where non-entry is proven |
| Confirmed rollback with no earlier committed step | "The change was not saved." |
| Known primary save but later audit/target step failed | "The roster change was saved, but its audit or target update could not be confirmed. Please have leadership check it before trying again." Name only the actual incomplete step |
| Some reset/swap steps confirmed, others failed | "Some changes were saved, but the action did not finish. Please have leadership check it before trying again." Include a count only when exact |
| Entered writer with lost acknowledgement / undifferentiated legacy false | "The outcome could not be confirmed. Do not repeat the action until leadership has checked it." |
| Mutation confirmed; refresh request refused | "Rank updated. The board refresh could not be scheduled; leadership can refresh the board." No claim of queued work |
| Explicit Refresh success | "Leadership board refreshed." Only after successful edit/send plus required identity persistence |
| Explicit Refresh pending/failed/held | "Refresh is still running" / "The board could not be refreshed; its saved identity has been retained." Unknown send remains held |

No default green tick for partial/unknown results. No automatic later DM or second
private success notification is added. Retain a refresh handle's delivery outcome
in operational diagnostics; the original result does not promise Discord delivery.

Required bounded corrections after approval:

1. Add opt-in typed DAL evidence for adopted roster/target writes: distinguish
   positive affected rows, zero affected rows, known refusal and unconfirmed error.
   Keep the shared `stats_alerts.db` behavior unchanged; do not invent rollback
   evidence from its `None` result. Validate each positive result exits its commit
   context before reporting completion. Unknown rowcounts require qualified evidence.
2. Check existing audit return values and propagate target regeneration outcomes.
   Preserve completed prior steps on later failure. Target generation reports exact
   expected/touched/missing members; a positive subset is not complete success.
3. For reset, no-op rows and preparation-driven placement, distinguish requested
   business mutation from earlier side effects. A1a incomplete preparation is never
   downgraded to not-entered. Retain the existing required audit policy; creating a
   new global audit/transaction model belongs to R12.
4. Put target generation/override under the same process event owner as roster
   preparation, with current event/award identity checked by the service/DAL. This
   is local owner consistency, not new cross-process serialization.
5. Adopt the same evidence boundary for rules and open/fixed switches. Their
   current failure text invites retry despite collapsed DAL errors. Preserve
   existing atomic grouping, distinguish an already-correct mode from a new save,
   and replace retry invitations on an entered/unconfirmed write. This is outcome
   classification, not a new mode-switch policy or transaction redesign.

## B3: ownership, keys and execution sequence

Keep `CoalescedWork` as the sole coalescing executor and current owned-worker helpers.
Prefer no core change: MGE wrappers provide typed delivery results while each
coalesced factory returns a real Boolean so failed-pass accounting is meaningful.
Do not expose cancellable shared Tasks to callbacks. Return an MGE refresh handle
whose await observes owned work through `drain_awaitable`; waiter abandonment cannot
cancel the shared pass. A shared task completes when its key becomes idle, which
may include newer requests; explicit refresh wording must reflect that limit.

**Sequence for an adopted action:** acknowledge and admit -> run owned service ->
capture actual result -> synchronously register eligible refresh with a reply-release
gate -> attempt private result -> release gate in `finally` -> return callback.
Registration must occur without a Discord await and after the mutation owner is
released. The factory waits for that gate before its new preparation/board IO.
An already running independent scheduler/manual pass is allowed to continue; A1b
does not promise that no other board work occurs while a reply is sent.
For coalesced requests, accumulate unreleased reply gates for the pending generation;
replacing a factory must not discard another action's gate. A pass waits for its
captured gates, then rereads; a newer request still forces a fresh follow-up. Gates
are released in each action's finally and removed after observation, not retained
as an unbounded per-interaction history.

The gate releases on reply success, failure or cancellation. Use a compatible
optional delivery-result helper in `core/interaction_safety.py` if needed to observe
actual send success; keep `send_ephemeral` behavior for other callers. Test the real
signup and leadership callers for this shared change. No private response is retried
automatically. Registration failure is recorded independently of mutation outcome.

| Coordination element | Concrete rule |
|---|---|
| Request key | Bot identity, EventId, board kind, resolved destination and semantic class. Silent refresh, scheduler first-create announcement, publication/version and recovery-existing-only must not overwrite each other's factories |
| Delivery lock | Retain current `(bot identity, EventId)` serialization across board kinds because identity/placement dependencies are shared. Target-specific request keys deduplicate work; changing to parallel same-event board IO is not required |
| Target resolution | Resolve configured versus persisted destination using the caller's existing policy; reread and revalidate before IO. If saved channel and requested destination conflict, retain identity and report disposition required; no automatic migration or replacement |
| Aggregate request | Expand P/L/A to target handles; await all requested targets for manual calls, with per-target outcomes. Omitted targets are `not_requested`, not failures. Partial registration is observable |
| Manual observation deadline | After 10 s, an explicit Refresh may return pending while the owner keeps running. Use a non-cancelling observation such as `asyncio.wait`, not cancellation of the shared task. Do not report success or detach ownership to meet the deadline |
| Dirty request | Requests before start share a pass; a request during preparation/IO advances revision and forces a fresh read in a later pass. Newer state is never a captured form payload |
| Failed pass | Observe exception/false result; newer dirty revision still runs. Without a newer request, stop; no automatic immediate retry loop |
| Partial/unknown mutation | Never replay it. A presentation-only, non-mutating qualified reread may update known messages. Leadership reconciliation must disable automatic placement; missing placements are incomplete and preserve the board |
| Creation | Existing journal fence precedes send. Only ordinary callers already authorized to create retain that authority. Reconciliation never creates a new board |
| Unknown edit/send | Retain IDs and evidence. Known-ID edits can be reread/refreshed by a later independent request; an entered/unknown send never permits another send |
| Bounds | At most one owned task/pass per semantic target key; no per-click detached task or retry timer. Startup work pages 50 events at a time with at most two distinct events active; release completed handle state rather than keeping an unbounded history |

Lock order: optional async roster owner -> reentrant event thread owner -> DAL
transaction, then release all mutation owners before response/refresh. A board
pass takes event board lock -> owned preparation thread -> event thread owner only
when placement is enabled -> DAL; releases the thread/SQL owner before Discord IO.
Journal operation lock is acquired only during delivery after preparation. Never
hold a SQL transaction or thread owner across await. No callback awaits a board
while retaining a roster owner. Different events must make independent progress.

### Additional prerequisite: publication and refresh identity ownership

Static source evidence at runtime base `51cab280aaaaf62b2d3a8d1fe17ee92442aaed34`:
`sync_event_awards_embed` serializes other embed-manager passes, but publication's
direct send and unpublication's delete use a different adapter path.
`update_award_embed_ids` updates by EventId alone and returns true without checking
affected rows. An older refresh can therefore edit message A, pause before its ID
save, and then save A after publication has persisted newer message B. Likewise,
an old save can restore IDs after unpublication cleared them. This is a source-
supported interleaving, not a reproduced production incident or an attribution of
the observed latency. Separate coalescing keys do not prevent it.

Required bounded implementation:

1. Extract the existing event presentation owner into an MGE-local boundary shared
   by embed-manager delivery and publication/unpublication's primary board transition.
   Start that ownership before the relevant publication state/identity transition;
   retain it through primary send/delete and identity settlement. Release it before
   calling the normal refresh API or sending unrelated DMs/reminders. Do not acquire
   the same non-reentrant owner recursively. Services use an adapter/context protocol,
   not Discord types. Publication remains awaited and semantically distinct.
2. Prepared presentation carries its qualified EventId, lifecycle, PublishVersion and
   relevant channel/message binding. Revalidate eligibility after obtaining the owner.
   If they changed, discard the prepared result and report stale/held or let an
   already admitted newer pass reread; no tight retry loop. Preserve the documented
   owner order, never acquire the board owner while retaining a roster owner, and
   retain the entered transition during cancellation/shutdown.
3. Give adopted identity writes an explicit expected binding and lifecycle/version
   predicate, with NULL-safe matching and positive affected-row evidence. A stale
   write must never restore a cleared or superseded pointer. Zero matched rows are
   a conflict, not success; an entered error remains unknown. SQL stays in DAL using
   existing `MGE_Events` columns, with no migration or shared database-helper rewrite.
   Revalidate every adopted ID writer, including acknowledged-journal recovery.
4. An acknowledged historical send alone does not authorize restoring a currently
   cleared identity. Require evidence that the receipt still belongs to the current
   lifecycle and binding. If lost ID persistence cannot be distinguished from
   intentional clearing/supersession, hold for operator disposition. Never revive
   an unpublished award board, replace a current binding or delete an orphan
   automatically. Acknowledged send plus rejected ID save retains both facts.

The process owner coordinates adopted in-process paths; conditional SQL writes
protect the saved pointer from competing writers. Neither creates a transaction
across SQL and Discord, detects every external ABA transition, nor guarantees a
globally consistent multi-query snapshot. External edits can still race delivery;
report that limit and retain uncertainty. A stronger cross-process fencing token
or durable lifecycle intent would require separate SQL design under R12.

Use barriers to prove refresh/publish, refresh/unpublish and recovery/republish in
both completion orders: current IDs survive, stale saves fail visibly, cleared IDs
stay cleared, no replacement/mention replay occurs and the final eligible request
converges. Include duplicate same-event publication admission, cancellation inside
the owned transition, and refresh invoked afterward without deadlock. These are
required integration tests, not helper-only mocks.

## Shutdown and restart reconciliation

Keep durable state in existing SQL and delivery journal. In-memory dirty work is
not durable. Do not claim the current calendar loop or tracked-view attachment
alone repairs every pending board.

Proposed lifecycle in the existing bot teardown integration:

1. Close new private-action admission and background MGE refresh admission together.
   Already admitted private operations receive a scoped continuation path to register
   their settled refresh. Stop new scheduler/manual roots without cancelling entered
   workers. This continuation is internal ownership, not a user-controlled bypass.
2. Drain admitted private operations, then close continuation admission and drain
   the registered refreshes. Keep event-delivery admission open until that drain
   settles. Include direct/manual/scheduler entries in the MGE owner inventory.
3. Bound observation, not ownership: report still-draining stage/counts every 10 s
   while an entered worker remains. After the existing restart controller's allowed
   wait expires, return/report incomplete there and retain ownership; never cancel
   a thread, close the client underneath it or report a successful restart. No
   guarantee of bounded total shutdown is possible for a stuck external driver.
   Do not introduce a competing hard-kill timeout or relax protected drain checks.

Add presentation reconciliation to the existing MGE lifecycle task, independent
of calendar discovery success. No new general job framework:

- At process startup, keyset-page SQL events with persisted P/L/A message identities,
  including started/completed and calendar-missing events. Capture a finite EventId
  high-water mark for the sweep; retain cursor progress across ticks in process.
  Read existing `receipt_rows()` once for acknowledged MGE sends whose SQL ID save
  was lost. Validate exact event/kind/channel/message binding before recovery.
- Recovery updates existing messages only, without mentions, business mutations,
  automatic placement, publication, DMs or message replacement. Required source
  data failing qualification preserves the message. Entered/unknown send receipts
  remain held and visible for operator reconciliation.
- Continue regular reconciliation of non-completed persisted targets on the existing
  300-second cadence. A failed page does not advance its cursor or become an empty
  page; other known targets can proceed. A new process safely starts the finite
  sweep again. Completed historical targets receive one startup sweep, not recurring
  background rewrites. Exact absent/deleted messages remain operator-disposition items.
- Crash before registration, during reply, after acknowledged send/before SQL ID save
  and during shutdown use SQL/journal state to reconcile eligible known boards.
  Ambiguous or superseded receipt bindings remain held under the identity contract
  above. This is eventual board convergence where authority is established, not
  durable proof that every individual in-memory request was delivered.

Recovery completion means the finite candidate sweep was examined, not that every
board was successfully delivered. Report scanned, eligible, refreshed, held, failed
and outstanding separately, together with cursor/high-water progress and last safe
failure stage. A target failure in a successfully read page must not prevent the
other targets or later pages from being examined. A failed SQL page read preserves
its cursor and makes the scan incomplete; do not skip unknown rows to claim success.
Retain failed/held target dispositions in existing bounded diagnostics; completed
historical targets are not silently retried forever after their one startup attempt.
Before starting each recovery page, respect foreground admission and existing
two-event bounds. Do not enqueue the whole history or let a failed recovery target
create an immediate retry loop. A truly stuck entered worker may still block its
event owner; expose that limit without releasing ownership or claiming fairness
that the driver cannot provide. Test a failing early target, a failed page read,
foreground work arriving mid-sweep and shutdown with a partial sweep.

This recovery policy is included in the approval requested below. If the product
requires automatic recovery of new-board creation with no persisted identity and
no acknowledged journal receipt, that requires a separate durable intent design;
A1b must hold that case instead of guessing.

## SQL and persistence review

Source definitions inspected in the authoritative repository at the revision above:

| Object | Verified contract used by A1b |
|---|---|
| `dbo.MGE_Events` | bigint EventId; non-null lifecycle dates/status/mode; nullable signup/leadership/award message and channel IDs; PublishVersion, LastPublishedUtc, UpdatedUtc. Existing EventId PK supports keyset paging; status/start indexes exist |
| `dbo.MGE_Variants` / event join | Event VariantId FK; VariantName remains required for public rendering |
| `dbo.MGE_Signups` | bigint SignupId/EventId/GovernorId; non-null name, priority, commander and IsActive; nullable DiscordUserId/rank band; filtered unique active EventId/GovernorId; Event_Active index |
| `dbo.v_MGE_SignupReview` | EventId/SignupId/GovernorId and requested display/rank/warning fields; active signup view with optional KVK data. Missing optional KVK values are not read failure |
| `dbo.MGE_Awards` | EventId/SignupId/GovernorId, AwardStatus, rank/waitlist, target and manual-override fields; event/governor uniqueness. Allowed persisted statuses differ from display aliases; normalize deliberately |
| `dbo.MGE_SignupAudit` | AuditId, SignupId/EventId/GovernorId, ActionType, actor, DetailsJson and UTC; existing receipt JSON remains authoritative for adopted signup operations |
| `dbo.MGE_AwardAudit` | AuditId, AwardId/EventId/GovernorId, action, old/new rank/status/target, DetailsJson and UTC; ordinary legacy entries are not operation-id receipts |
| `dbo.MGE_RuleAudit` / `dbo.MGE_DefaultRules` | Rule audit event/action/actor, old/new mode/text and UTC; defaults keyed by RuleKey with RuleMode/RuleText/IsActive. Preserve rules/switch audit grouping and default selection |

New SQL text, if needed, stays in Bot DAL and references these existing objects.
No procedure, ProcConfig, UDT, staging/output table, permission or schema change is
required by this proposal. No live SQL or query-plan claim is made. Revalidate
exact changed queries and source head before coding. If schema/index changes
become necessary, stop that delta for a separate SQL proposal and diff review.

Read-only audit/cleanup follow-up, not executed: use the private manifest to bind
each accepted signup/edit/withdraw operation to original runtime, event, signup,
governor and operation/fingerprint. Read only those signup audit rows and relevant
award audit rows; compare action and prior snapshot to the current signup and
required withdrawal deletion. Later edits must not invalidate earlier commit
receipts. An awarded-withdrawal case not exercised stays unexercised. Retain redacted
counts/hashes and exact private evidence; absence is unknown evidence, never replay
authority. Do not run a new signup/award/withdrawal to create a missing receipt.

## Refactor decisions and file boundaries

| Trigger | Disposition |
|---|---|
| Direct DAL reads in touched views | Fix where needed for new result/identity contract by using service methods; no new embedded SQL in UI. Unrelated form-option code stays unchanged |
| Business state/result logic in views | Fix: MGE action result/response adapters own common sequencing; services classify actual outcomes, views route inputs and display text |
| Duplicate refresh wrappers | Consolidate into existing embed-manager request APIs; keep compatible sync entry points. No second background executor |
| Session undo buffer | Preserve its explicitly session-only contract. No persistent-undo feature is proposed; broader writer atomicity stays R12 |
| Multi-call roster atomicity | Defer transactional redesign under existing R12 item; A1b must expose partial/unknown evidence now |
| Hidden preparation writes | Preserve A1a owner in ordinary preparation; explicitly non-mutating recovery path needed now |
| Weak delivery/result logs | Fix: action disposition, reply outcome, target/revision, pass outcome, outstanding ownership and safe stage timings. No token, payload or SQL exception text in new structured fields |
| Dead branches / broader helper cleanup | No deletion justified by this scope review. Legacy flow remains a supported caller |
| Tests coupled to old awaited refresh | Update behavioral assertions to commit/result/owned-refresh order; preserve historical source pins |

Expected runtime manifest: new MGE preparation/result/response modules; existing
`mge_embed_manager`, `mge_scheduler`, `mge_simplified_flow_service`, roster and
simplified-leadership services, target service section of `mge_publish_service`,
relevant event/review/roster/leadership/publish DALs; listed signup/leadership/roster/
rules/admin view adapters; affected manual command routing; minimal bot teardown
wiring. `core/interaction_safety.py` gets only compatible result-observation support
if required. Keep `core/coalesced_work.py` unchanged unless tests demonstrate a
necessary ownership fix. Any core change needs two actual caller paths, not just
two synthetic factories. Signup and leadership are real reply consumers; scheduler
and signup are real coalescing consumers. Event delivery qualifies owned-work or
journal changes if either changes. Do not adopt Ark merely to obtain a second caller.
Rules and mode-switch outcome classification also touches `mge_rules_service.py`,
`mge_event_service.py` and `mge/dal/mge_rules_dal.py`. The qualified-reader helper
stays under `mge/dal/`. No global database-helper rewrite is part of this manifest.

## Test and benchmark acceptance

Maintain one compact acceptance table alongside implementation evidence, with
stable requirement IDs: Q1 qualified data, O1 exact action outcome, R1 reply-independent
refresh, C1 coalescing, I1 lifecycle/identity ownership, L1 drain/recovery and E1
measurement/release evidence. For each adopted caller/board target, link its
requirement, production entry point, deterministic test, exact tested commit and
result or explicit gap. No caller is accepted solely because its shared helper
passes. Preserve this mapping in the follow-on handoff so A2/B/C can reuse proven
test patterns without inheriting unearned acceptance. Reuse existing evidence
documents and test fixtures; no new generic framework or mandatory tracking tool.

| Test group | Required deterministic evidence |
|---|---|
| B1 failure matrix | Fail each event/review/award/identity/payload dependency independently; absent cursor metadata/result set; malformed/duplicate/wrong-event rows; valid empty and all-rejected; no Discord/ID side effects on failure; prior board bytes/IDs retained |
| Action result | Every row of the service map: positive, zero-row, absent target, audit failure, partial swap/reset/generated target count, regeneration failure and lost acknowledgement. Failed/unknown cannot claim complete or invite blind retry |
| Reply ordering | Hold board preparation and edit with barriers; known result arrives before releasing either. Mutation count exactly one. Same proof for both leadership UIs, signup/edit/withdraw and rules |
| Reply failure | Ordinary send failure, exception, cancellation and repeated cancellation still settle registration/gate; response failure cannot alter saved outcome. No double reply or duplicate mutation |
| Coalescing | Before-start burst, dirty during read, dirty during edit, failed old pass plus newer request, failure with no newer request, waiter cancellation, shutdown admission. Latest final state and bounded request/pass/edit counts |
| Identity/semantics | Distinct bots/events/channels/board kinds; conflicting channel, NotFound, forbidden, acknowledged send + failed ID save, entered send after restart; no replacement or mention replay. Publication cannot merge with silent refresh |
| Lifecycle overlap | Publication/unpublication versus refresh/recovery in both completion orders; conditional ID writes reject stale/cleared bindings; ambiguous historical receipt held; direct adapter paths participate in ownership; post-transition refresh cannot deadlock |
| Recovery | Restart outside calendar window, completed event, missing calendar source, zero SQL IDs with acknowledged journal, invalid journal, failed scan page, crash before registration and during reply. Recovery never places awards or mutates signup state |
| Permissions | Non-leader/admin, cross-user form, stale event/award, duplicate confirmation, expired opener, missing selection; final service authority retained. No speculative priority default |
| Ownership | Same-event mutation versus preparation/target writer; other-event progress; no thread owner across await; scheduler stopped before refresh drain; incomplete drain never releases entered work |
| Compatibility | Existing publication freshness, reminder policy, signup atomic audit/cleanup, event delivery and protected updater historical tests remain passing |

Extend existing tests: `test_mge_dataset_validity.py`, `test_mge_public_signup_embed.py`,
`test_mge_embed_manager.py`, `test_mge_board_delivery.py`,
`test_mge_simplified_leadership_view.py`, `test_mge_simplified_leadership_service.py`,
`test_mge_simplified_leadership_admin_add.py`, `test_mge_roster_service.py`,
`test_mge_roster_rank_waitlist_notes.py`, `test_mge_roster_delete_undo_audit.py`,
`test_mge_signup_mutation_contract.py`, `test_mge_signup_views.py`,
`test_mge_simplified_signup_form_view.py`, `test_mge_rules_edit_view.py`,
`test_mge_scheduler.py`, `test_mge_rehydrate_and_regression.py`,
`test_mge_publish_service.py`, `test_mge_lifecycle_review_regressions.py`,
`test_p1_owned_operations.py` and `test_operation_timing.py`. Add a distinct A1b
recovery/result test file only where extending existing coverage would obscure it.

Use fake clocks/barriers, not sleep-race assertions. Freeze one harness revision
based on `scripts/benchmark_mge_refresh.py` and run baseline/candidate sequentially
on the same host, at least 30 samples per 0/4/15/30-row case and mutation plus
scheduler/manual overlap. Include slow boards, rapid repeated refresh requests,
partial result and reply failure. Record raw samples, source/harness SHA256,
p50/p95 with sample counts, ack/result/end-to-end latency, loop lag, SQL read/
connection counts, audit/mutation/response counts, refresh requests/passes/edits
and outstanding tasks. Inclusive stages cannot be summed.

Acceptance is structural first: result independent of board barrier; no dropped
latest-state refresh; exact authorized mutation/audit effects; zero pending work
after successful drain; compatible requests produce bounded passes. A request
arriving during a pass requires a follow-up, so universal edit-count reduction is
not promised. Explain every extra read/connection; reject accidental duplicate
reads and unbounded work. Publish measured differences, not an invented production
SLA. A proposed performance improvement fails if it merely hides incomplete work.

Implementation gates per PR: architecture, deferred items, security routing,
selector; selected subsystem tests, smoke imports, command registration, lint and
format checks. Full repository pytest and protected-log isolation before final
release because ownership/startup/shared helpers are affected. Record Windows
and Linux results separately; never rewrite an old release result as current proof.

## PR, security and updater order

1. **Documentation custody (this task):** use the 28 handover documents already
   merged in PRs 455/703; preserve this local packet/navigation/backlog delta on top.
   No repeat handover publication, standalone runtime or live action.
2. **PR 1 / B1:** strict public, leadership identity and awards preparation; payload
   guard; tests; carry-forward documentation union. Preserve refresh policy and UX
   ordering until PR 2. Review independently against its mirror base.
3. **PR 2 / B2+B3:** result evidence corrections, early replies, target requests,
   admitted-action continuation, shutdown observation and existing-message recovery.
   Include shared publication/refresh presentation ownership and conditional ID writes.
   Depends on reviewed B1. Include tests and frozen before/after benchmarks. Result
   and refresh ownership ship together.
4. **Release qualification:** final exact updater transition and historical test
   bridge for the composed candidate, reviewed before production promotion. Include
   this necessary release change in the final implementation PR when possible;
   otherwise use a narrowly dependent tooling PR. No intermediate deployment implied.

Updater source protection is a known dependency now: `MGE_A1A_PATHS` authenticates
12 files; lifecycle protection includes embed manager, scheduler, views, core and
bot teardown. Registry currently has 50 transitions and a 96 KiB byte limit. Add
an exact successor transition for the reviewed final source; do not modify any of
the 50 historical entries or tests' original source pins. Derive the required file
bundle and count/size changes from the actual final diff; no invented hashes or
blanket allowlist. Prove full bundle, every missing/tampered member, unknown/partial
source rejection, source/seed pairing, historical compatibility and installed-tool
authority. Test fixture bridges authenticate new bytes before historical assertions.

Future release order: validated mirror PRs -> equivalent patch promotion to private
history -> final checks/review -> separately authorized updater upgrade if required
-> protected private-main deployment and graceful restart. Ordinary pull/restart is
insufficient. Rollback uses an explicitly authenticated supported source/seed pair;
never reset live source or erase receipts. No rollback of confirmed business data.

**Security decision now: documented skip** for this Markdown-only patch. No executable,
SQL, permission, dependency, config, deployment-policy or persistence behavior is
changed. **Implementation decision: Changes review, Deep off**, each immutable Bot
base/head plus directly supporting source; record exact heads and coverage. Separate
private promotion review or exact-equivalence qualification follows policy. SQL
repository scan is inapplicable without a SQL diff. Standard/Deep codebase audits
are not routine gates. Keep potential security findings in the security workflow,
not in deferred optimisation scoring.

## Complete carried-item disposition

Acceptance/policy owner remains Chris Watts. None of these rows is closed by this
design or by a future source merge alone.

| Item | Disposition / next action |
|---|---|
| MGE-01 | Exercised A1a signup/edit/withdraw remains accepted; exact audit/cleanup read-only reconciliation and unexercised cases stay separate |
| MGE-PERF | A1a delivered; this A1b proposal owns response/refresh work, not production speedup proof |
| R01 | Prior bounded conflict correction accepted; CFG-51421 separate with unknown blocker |
| R02 | Delivered status correction retained; A1b adopts only mapped MGE callbacks; other Discord lifecycle work remains A |
| R03 | Natural empty-to-populated transition, deferred views and subscribed DMs await natural evidence |
| R04 | Exact historical Daily KVK Overview disposition unresolved; no repost |
| R05 | Protected-launcher/singleton census remains B |
| R06 | A1b owns selected MGE refresh/recovery; remaining public/DM ordering, JSON/drain and uncertain-send coverage stays A/B |
| R07 | Accepted Ark callback and exercised MGE actions retained; remaining eligible-message/domain coverage stays A |
| R08 | Prior reporting/cleanup acceptance retained; artifact uniqueness and ambiguous cleanup audit stays B |
| R09 | Stats fallback, KVK History and alert no-reentry/caller audit stays B |
| R10 | Durable profile invalidation/source revisions and remaining cache callers stay B |
| R11 | Fighting caps/admission, KS preclaim and Pre-KVK replacement policy need separate bounded A scope |
| R12 | A1b exposes legacy partial outcomes and fixes local owner gaps; atomic writer families, cross-process conflicts and session undo persistence remain separate A/B |
| R13 | Natural Pre-KVK/off-season and Phase 2F public-save evidence pending |
| R14 | Independent external monitoring/outage recovery stays C |
| R15 | Existing 50-transition updater acceptance retained; candidate compatibility required for A1b. Provider-stream diagnostics/stranded-export tooling stays C |
| R16 | Receipt-query scaling, history/readback/quota and ActivePreparationID plan/acquisition acknowledgement work remain separate measurements/design |
| R17 | P0 natural F04 rollover and every-row F01-F05 reconciliation remain open |
| R18 | Predecessor acceptance stands; fresh current `87c1b393` import/export still unproven; do not repeat accepted predecessor work |
| CFG-51421 | Original attempt closed; keep-prior/fresh-publication choice remains operator-owned. Later startup success does not choose it |
| CFG-OVERVIEW | Separate collection-time/detail reconciliation; no assumed reporting defect |
| RECOVERY-QUEUE-62 | One normal recheck of the existing incident is the bounded operator follow-up; linked cache-only report completed, queue closure unconfirmed. No release/cancel/replay |
| GATEWAY-LAG-62 | Separate bounded passive/stack evidence lane; 41.7/42.4 s warnings have no assigned cause. Healthy 216.875 s monitor cycle does not identify causality |
| MGE-SELECTION-OBSERVATION | Pre-write refusal; compare dispatch/form state and batched telemetry in deterministic fixtures. No default selection or regression claim without evidence |
| ARK-A2-ADMIN-ADD | Added player plus timed-out private reply remains A2; reconcile original mutation, never replay |
| Startup observers | Tracked views 21/21 and cache readback completed after observer deadlines; no retry/restart needed |
| B/C and WS1-WS6 | Retain remaining programme work and natural acceptance; no whole-workstream closure from this packet |

## Approved scope and limits

The operator approved the two-PR local implementation with these choices included:

- Ordinary actions return truthful saved/partial/unknown text immediately; board
  refresh is explicitly pending. Legacy roster snapshots move to the existing
  Show Roster action. Explicit Refresh and publication remain outcome-aware waits.
- Restart repairs only known original boards from qualified SQL/journal evidence,
  including a bounded one-pass sweep of historical persisted targets; it never
  creates replacements, announces again or runs placement/business mutations.
- Extend coordination into publication/unpublication's primary board transition
  and require conditional ID persistence, so stale refreshes cannot overwrite a
  newer or deliberately cleared saved binding. Hold ambiguous historical receipts.

These are the approved material behavior choices, including the third item identified
by the final framework review.
Module placement, helper reuse, test
selection, target keys, package ordering and source-protection work are recommended
engineering decisions, not separate approval requests. Approval does not choose
the older configuration continuation or authorize R11/R12 redesign, production
queries, Git publication, merge or deployment.

## Historical validation of the scope-only documentation packet

Local validation passed: architecture (zero Python changes), deferred register
(29 Markdown files), security routing (zero errors/warnings), test selector,
70 introduced local links, referenced test-file existence, UTF-8 replacement-character
check and Git whitespace check. The selector recommends smoke imports and command
registration generically; both are skipped with runtime pytest and a new security
scan because this exact patch changes Markdown only. Proposed runtime tests and
benchmarks above have not been run and are not represented as passing.

Final framework review validation: architecture, deferred-item validation, security
routing, test selection and Git whitespace checks passed again after the scope
addition. The amendment changes Markdown only; runtime tests, smoke imports,
registration and Changes security scanning remain skipped for that reason. The
publication overlap is static source evidence with proposed barrier tests, not a
claimed live reproduction. SQL column availability was rechecked in the authoritative
`dbo.MGE_Events.Table.sql`; no database was queried and no SQL source was changed.

At the scope-only checkpoint, the design branch retained the complete imported handover documentation plus the new
packet and current navigation/backlog amendments. That scope-only task did not modify the
source handover worktree, runtime files, SQL repository or remote push protections.
