# Phase 2K — Production Stats Delivery Outcomes

Status: combined design and implementation approved on 2026-09-09; locally tested, not deployed.
Mirror PR creation as ready for review is authorized. Natural Pre-KVK is not expected for about
two months; retain automated tests and the existing diagnostic command as interim evidence,
without treating diagnostic publication as natural production admission.
The operator requested receipts across all seasonal adapters plus correction of fighting claims
after send errors. The revised design below supersedes the initial fighting/KS-only proposal and
its proposal to preserve claims after swallowed send errors. The design text below records the
approval checkpoint historically; the subsequent explicit operator approval authorizes implementation.

## Implementation record — current

Implemented the 11-runtime-file combined slice. Added immutable DeliveryAttempt/DeliveryResult and
an explicitly passed in-memory observer; no global context/store or additional dispatch lifetime.
Default direct adapter returns remain compatible. Opt-in wrappers return results, while the
seasonal interface shares one observer through adapters so cancellation retains partial receipts.
This is the implementation refinement to the design's interface opt-in: it prevents a nested
cancelled adapter from losing its acknowledged message before aggregation.

Receipt-only fighting claims, KS-first outcomes, Pre-KVK edit/fresh receipts and independent
off-season periods are implemented. DispatchAttempt exposes commit/finalization observations only;
schema, transitions, locks and recovery are unchanged. Import audit SQL calls retain their meaning.
Reporting handler failure cannot erase a receipt or change import completion.

Actual test changes: the three proposed new suites plus test_prekvk_embed,
test_stats_alerts_offseason_flow, test_embed_offseason_stats, test_prekvk_reservation,
test_honor_upload_route and test_prekvk_upload_route. Existing test_kvk_embed and
test_stats_alerts_fighting_lifecycle were run unchanged; their new outcome cases live in
test_stats_delivery_outcomes. The obsolete KS manual tester remains untouched.

Validation: 275 focused/regression tests passed, including H/I invocation/lifecycle and existing
reservation/state coverage. Full pytest: 3508 passed, 2 skipped; operational logs unchanged.
An initial full run hit WinError 5 in the existing atomic-write reservation test; isolated and full
reruns passed without changing the filesystem helper. Imports and registration passed
(36 primary/100 grouped/24 ops). Ruff, Black, architecture/deferred/security-routing checks and
selector passed. Applicable pre-commit checks passed; mixed-line-ending normalization was skipped
to preserve the immutable reviewed bytes, and staged-only gitleaks was skipped because no files
were staged and no commit/PR is being produced. YAML and command-registration hook path filters
did not apply; registration was run separately. Standalone Pyright had zero errors and five
missing-import warnings in unchanged files; the configured Pyright hook passed.

PR preparation closeout: all applicable staged hooks now pass, including gitleaks, mixed-line-ending,
Ruff, Black and Pyright. The first hook run normalized CRLF to LF in 11 runtime files; Git's
normalized diff against the previously staged content was empty. No behavioral change followed the
security review. The post-review delta is documentation plus line-ending normalization, so further
security discovery and full pytest are skipped for that delta. Mirror main was rechecked at the
reviewed baseline before commit/push. Natural Pre-KVK remains pending for its real calendar window.

Current security receipt (2026-09-09): fresh user-authorized Changes-only, Deep-off scan
`9884a327-68c2-48ff-9ff9-f548bec39b88` re-reviewed all 11 runtime, nine test and five documentation
files. Base/head `2ed5513e49e4d34e3c3cd198517b3bc5dc6f1598`; final reviewed snapshot
`codex-security-snapshot/v1:sha256:95449a58874ac0ff705216f065bd4d3a53e5a58b6bce618961cb9f6df68691dd`.
Both pre-seal inspection and sealed readback confirm complete coverage, zero deferred entries and
zero findings. The sealed status is completed. This closes the coverage evidence discrepancy for
this patch; the earlier sealed report remains unchanged and is superseded for handoff.

Current report: `C:\Users\cwatt\AppData\Local\Temp\codex-security-scans-NZk6F5\discord_file_downloader\2ed5513e49e4d34e3c3cd198517b3bc5dc6f1598_20260909T101735Z_26n06xp8\report.md`.
Fresh scan meter: 1,632,652 total tokens, including 1,597,568 cached input tokens; separate goal
meter: 37,642 tokens and 119 seconds. Preflight ready; TAC granted at tac1. No runtime changes
or full-suite rerun were needed for this evidence repair. Post-seal edits only update four Markdown
status records (this pack, starter, README-DEV and deferred register); additional security discovery
and pytest are skipped for that documentation-only delta. Existing test evidence remains applicable.

Historical Changes-only, Deep-off scan `15456f8f-8289-4d0d-a556-455c0b642cb3` reviewed all 11 runtime files
plus nine test and five documentation files, with no candidates. Base/head:
`2ed5513e49e4d34e3c3cd198517b3bc5dc6f1598`, working-tree snapshot:
`codex-security-snapshot/v1:sha256:b6d8f921069f8f9acc6f342e89053eb8336db5702e074aa126b45b40b2474f0d`.
The completed readback retained the early `remaining-runtime` deferred marker and
`completeness=partial` despite the final complete draft and completed five-file review. The sealed
artifact is preserved unchanged. It was not used as a clean handoff gate; the fresh review above
now supplies the complete receipt. Do not relabel this historical receipt or overwrite its canonical
documents. No SQL scan: SQL/DAL/migration diff is empty.

Report: `C:\Users\cwatt\AppData\Local\Temp\codex-security-scans-NZk6F5\discord_file_downloader\2ed5513e49e4d34e3c3cd198517b3bc5dc6f1598_20260909T100301Z_ilkscqaq\report.md`.
Tool-reported scan usage: 5,031,642 total tokens, including 4,770,048 cached input tokens;
goal accounting separately reported 187,696 tokens and 379 seconds. These are different meters.

Post-scan delta: validation documentation and one test-fixture correction from a None-returning
claim stub to literal False. No runtime change. These changes receive focused test/docs validation;
additional security discovery is skipped because they add no runtime or security-sensitive behavior.
Post-scan validation passed: all 13 outcome tests, architecture/deferred/security-routing validators,
git diff --check and applicable changed-file hooks with the same documented skips.
No production promotion, deployment, runtime-state mutation or natural smoke has been performed.
Final Phase 2J deployed-SHA/clean checkout/restart association remains pending operator evidence.

## Entry and evidence

First verify operator merges of mirror #261 and production #568, final main/deployed heads, clean
worktree and restart evidence. Preserve reviewed Phase 2J runtime dd9ad0c8 and equivalent production
candidate 1639e90c; final closeout heads must be read from the merged PRs, not guessed. Review the
archived Phase 2J pack/starter, updated original audit and active/resolved deferred registers.
Phase 2J smoke proves removal/sync/36 primary/100 grouped/24 ops; existing H/I behaviour is operator
accepted. Raw H/I session receipts and an immutable running SHA were not supplied with that log.

At 2026-09-09 07:16 the natural post-import route selected ACTIVE KVK 16/scan 1121, empty reporting
blocks, skipped already-sent KS and claimed legacy KVK 2/3. Generic success had no message identity.
Earlier cap skip also logged success. These are actual outcome gaps; do not force dispatch to
reproduce them. Natural calendar Pre-KVK admission and Phase 2F public save stay separately pending.

## First response: audit, scope and architecture only

Trace every live caller of the seasonal interface and direct adapters, including
`admin_helpers.py::log_processing_result`, `upload_routes/honor_route.py`,
`upload_routes/prekvk_route.py`, `stats_alerts/__init__.py` and any additional callers found.
Follow real is_test/default/season selectors, KS-first side effect, destinations, sends/edits,
guards/caps/mutual exclusion, state/locks, return values, exception swallowing, cancellation and
offloads. Verify the claim return itself and the ordering relative to Discord; do not infer receipt
from a CSV slot, logging success, None return or aggregate workflow success.

Use safe/fix-now/defer/not-runtime findings with line evidence and exact manifests. Distinguish
normal skip, unavailable data, definite failure, successful send/edit and uncertain delivery. Empty
fighting data currently still renders in production: do not silently adopt diagnostic unavailable
semantics. A KS success followed by primary skip/failure needs per-attempt truth; avoid a single
Boolean that erases partial results. Define whether adapters return typed outcomes, raise known
errors or use existing result helpers, and show each caller's handling before recommending a shape.

## Proposed bounded implementation question

Expose actual send/edit receipts from fighting, standalone KS, Pre-KVK and daily/weekly off-season
publication through the seasonal interface and its existing callers. Preserve partial results and
distinguish successful delivery from unsuccessful or unconfirmed bookkeeping. Do not fabricate a
receipt from a CSV claim, action string, diagnostic session or aggregate workflow completion.

The one proposed protocol correction is explicit: production fighting calls claim_send only after
a positive Discord send receipt. Preparation failure, send exception, missing receipt or cancellation
before acknowledgment does not consume a success slot. The cap remains three recorded successes;
existing prechecks, mutual exclusion and concurrent check/send/claim behavior are otherwise unchanged.
This changes later eligibility after an unsuccessful or ambiguous call and requires approval of the
revised design before implementation. No durable fighting reservation or exactly-once promise is added.

## Architecture and helper reuse

Keep command/route code thin; outcomes belong to the stats subsystem/adapters and are propagated
to existing orchestration. Inspect existing Phase 2H/2I outcome/receipt and delivery-result patterns
before adding types; reuse vocabulary only where semantics match. Preserve owner/guild/channel/
season-bound diagnostic state, v1/v2 sessions, retention, restart reopening, explicit destination
and all-mentions-disabled diagnostic publication. Production mention defaults remain unchanged.
No new slash command or revival of `/ops test_embed`; baseline stays 36/100/24.

## Manifests and SQL gate

Audit candidates (not an implementation manifest): `admin_helpers.py`, `stats_alerts/interface.py`,
`stats_alerts/__init__.py`, `stats_alerts/embeds/kvk.py`, KS/offseason/Pre-KVK adapters, relevant upload
routes, guard/state/offload helpers and tests. Inspect unmodified supporting code only as needed.
The first response must name exact runtime/test/docs/tooling/config/dependency/startup/state files
proposed, with every new file justified. No files are approved for runtime/test implementation yet.
Expected SQL/DAL/migration manifest is empty. If any SQL contract becomes necessary, validate it
against C:\K98-bot-SQL-Server and present a separately gated SQL manifest/review; never infer it from
Python alone. ProcConfig repair is explicitly excluded.

## Selector and risk tests to propose (do not implement yet)

Run the selector on the proposed exact manifest and add deterministic tests for sent/message ID,
edit identity, cap/exclusivity skips, no destination, swallowed/raised Discord error, KS-only success,
primary failure, empty reports, selector boundary, claim failure after send, partial/unknown outcome,
and cancelled/timeout work. Prove no automatic second publication, no fabricated receipts and no
unexpected changes to guards/state. Use invocation counters at existing test boundaries, not a
runtime monkeypatch or live state swap. Regress H/I real Pycord options/invocation, retained sessions
and mention/destination behaviour; do not write tests for a removed ops callback.
Existing anchors include tests/test_kvk_embed.py, test_stats_alerts_fighting_lifecycle.py,
test_stats_alerts_guard.py, test_stats_alerts_offseason_flow.py, test_prekvk_embed.py, H/I diagnostic
tests, and actual upload-route/orchestration tests found by the audit. Add exact selectors after
source inspection. For approved changes: applicable hooks, architecture/deferred/security-routing,
imports, registration and full pytest with operational-log isolation as risk/selector requires.

## Security, smoke and rollback

Review type: Changes, Deep off, immutable base/head for each changed Git history. Markdown-only
preparation is a documented skip: no runtime/config/dependency/permission/input/SQL/state effect.
Never use Codebase or Deep as a routine PR gate. Preserve prior sealed reports at their exact heads.

Propose concrete smoke with deployed SHA/restart, natural eligible run and actual destination/
message identity correlated to its outcome. Use existing isolated diagnostics for preview checks
only; they do not prove natural admission. Capture skips without forcing another send or exhausting
caps. No SQL/calendar manipulation, resets, lock removal or forced duplicates. If a suitable natural
run is unavailable, mark that observation pending rather than claim completion. Rollback must
preserve existing production/diagnostic state and describe any reintroduced misleading logging;
any new persistence would require a separately approved migration/recovery contract.

## Explicitly separate

Durable reservation extensions; singleton/watchdog ownership; public-child supervision; generic view
timeout/resume; DM/broad JSON; Stats, KVK History and stats-alert once-only executor audits; ProcConfig;
offseason diagnostic framework; MGE/payload appearance redesign; Ark retention/transaction debt.
Capture dependencies without implementing them. Finish the first response with a concrete proposed
design and approval checkpoint. No command or test implementation before approval.

## Revised combined design — 2026-09-09

### Evidence and authorization

The operator approved expanding scope and requested this design revision, not implementation.
The earlier read-only audit verified mirror #261 merged at
`d9138053ce7d88a9a89fefeda6f5c9173f52fd2b` and production #568 merged at
`cf21039d68f912e0a4fa17f379c312f30741a8b3`. Observed mirror main/local HEAD was
`2ed5513e49e4d34e3c3cd198517b3bc5dc6f1598`; production main was
`cf21039d68f912e0a4fa17f379c312f30741a8b3`. These are dated source observations, not deployment proof.
The local mirror was clean at revision entry. Final bot-machine checkout cleanliness, deployed SHA
and associated restart/PID evidence remain pending. The archived 08:40 restart lacks immutable SHA.
Revalidate source heads before implementation; do not reopen Phase 2J removal or relabel old reviews.

### Outcome ownership and shape

Add `stats_alerts/delivery_outcomes.py` for dependency-light immutable records and shared result
normalization/logging. It must not import Discord, SQL, state stores, or diagnostic repositories.
Adapters extract primitive identity; the interface aggregates; upload/admin helpers report.

A workflow result contains ordered publication attempts, selected route, is_test and correlation
context. Each attempt contains component (standalone KS, fighting, Pre-KVK, off-season daily/weekly),
operation (send/edit), outcome, bounded reason, requested channel, actual channel/guild/message IDs
where observed, send-entry/acknowledgment evidence, data availability and bookkeeping observations.
Correlation IDs are log identifiers only, not reservation tokens or durable ownership.

| Outcome | Meaning |
| --- | --- |
| sent | The send returned a positive message ID; retain actual destination from the returned message. |
| edited | Edit await completed successfully for the fetched message identity. |
| skipped | Explicit branch performed no publication, with the actual guard/schedule/no-data reason. |
| failed | Failure is known to precede publication, or non-delivery is otherwise proved. |
| unknown | Publication entered but no acknowledgment is available, or a legacy/injected result cannot prove delivery. |

Known identity is not proof that an edit succeeded: retain the target message ID alongside unknown
when an edit fails after entry. Missing primary destination is failed before send; KS is skipped
because the existing interface exits before attempting it. Off-season weekly on non-Monday is an
explicit not-scheduled skip. Distinguish DispatchGuarded from other DispatchUnavailable errors;
do not call a corrupt/unreadable store a normal cap skip. Keep reasons no more precise than evidence.

Delivery and bookkeeping are independent. Record legacy claim as confirmed, not-confirmed or
not-attempted, without interpreting False as a specific cap or disk failure. Record reservation
commit/projection as confirmed, unconfirmed or not-applicable. A positive receipt remains sent even
when persistence is unconfirmed. Do not overwrite receipt evidence with a subsequent logging error.
Expose bookkeeping errors separately and never turn them into a publication retry.

Availability is not an eligibility rule: fighting continues to send the existing empty report.
Where loaders conflate empty data and errors, use empty-or-unavailable rather than inventing a cause.
Do not copy preview text saying no publication into a successful production outcome.

### Adapter contracts and compatibility

Use additive `return_outcome=False` options on existing seasonal senders. The interface opts in;
default direct-caller return and ordinary exception behavior remain compatible. H/I callers do not
opt in, and their strings, callbacks, session versions, permissions, destinations and stores remain
unchanged. Keep one underlying publication implementation per adapter, not duplicated legacy/new
send paths. Unknown remains a defensive result for malformed/missing receipts, not the planned
normal outcome for production Pre-KVK or off-season success.

| Boundary | Revised behavior |
| --- | --- |
| Fighting adapter | Capture returned message immediately. Report positive receipt or stage-aware failure/unknown; preserve payload, mentions and empty-data behavior. |
| Seasonal fighting branch | Claim only a confirmed sent result in production. Record claim return separately. Tests/default is_test never claim. Never claim for None/unknown/failed/skipped. |
| Standalone KS | Capture actual message and existing pre-send claim result. Keep its pre-send ping claim, fail-open guard behavior and no-data skip; moving this claim is not approved by this scope. |
| Pre-KVK same-day edit | Return edited with fetched identity after acknowledgment. Do not add a fresh-send claim or reservation to the edit path. |
| Pre-KVK fresh send | Capture identity before existing accept/state update. Expose delivery and commit/projection separately; preserve reservation order and legacy test-state behavior. |
| Pre-KVK production edit fallback | Preserve the existing fallback, but retain the unknown/failed edit attempt before any fresh-send result. Do not collapse unknown edit plus sent replacement into unqualified success. Diagnostic failure still never falls through to replacement. |
| Off-season renderer | Expose an opt-in outcome with actual destination/receipt and any embedded KS claim observation. Keep existing return_receipt behavior for compatibility; reject simultaneous incompatible result options before work. |
| Off-season wrapper | Retain independent daily and Monday weekly results. Daily ordinary failure does not suppress the existing weekly operation. Record included KS as part of that grouped message, not as a second message receipt. |
| DispatchAttempt | Expose in-memory commit/finalization observations without changing return contracts, stored schema, locks, transitions or recovery behavior. Capture ordinary accept failure as unconfirmed; callers can inspect after context exit. |

Keep exceptions visible to the reservation context manager before normalizing them; otherwise a
new result layer could accidentally change release/uncertain finalization. Preserve cancellation
propagation. Capture the message receipt before awaiting accept. If cancellation occurs during
commit, retain sent evidence and mark persistence unconfirmed in partial-result logging, then
re-raise CancelledError. Do not add shielding/draining beyond the existing reservation _io helper.
An already confirmed commit is not erased by a later finalization error; log that error separately.
No runtime reads of diagnostic receipt stores or global state swapping are needed.

### Fighting ambiguity and later invocations

| Situation | Delivery | Fighting success claim | Further publication in this invocation |
| --- | --- | --- | --- |
| Cap/exclusion blocks | skipped | Not attempted | None |
| Build fails before send | failed | Not attempted | None |
| Send returns valid message | sent with identity | Attempt once; preserve True/False | None |
| Send raises after entry, including timeout | unknown unless non-delivery proved | Not attempted | None |
| Send returns no usable receipt | unknown | Not attempted | None |
| Cancellation before receipt | Stage-aware failed/unknown in logs; cancellation propagated | Not attempted | None |
| Receipt exists but claim returns False | sent; bookkeeping not confirmed | Already attempted once | None |

A failed await does not prove Discord did not accept the message. A later independent natural
invocation may send because an unknown attempt has no success claim. Existing check/send races and
receipt-before-claim process crashes also remain possible. The design improves truthful accounting
and avoids charging known failures, but does not guarantee a limit on all actual Discord deliveries.
No in-memory ambiguity fence, new durable reservation, timer, automatic retry, recovery command or
manual retry recommendation is introduced. Existing client-level retries remain unchanged.
Approval of this design includes this explicit tradeoff. Preventing later ambiguous duplicates
requires a separately approved durable fighting admission protocol.

### Caller handling and SQL boundary

- `admin_helpers.log_processing_result`: preserve all-five-success gate, current selector and return
  contract; replace unconditional sent text with ordered attempt and bookkeeping reporting.
- Honor route: preserve is_kvk=True and filename/message test selection; return the refresh outcome
  from its helper and log it with existing source message/channel and import context.
- Pre-KVK upload: preserve nonduplicate-only refresh and is_test=False; propagate/log the same
  outcome. Its upload name does not force the Pre-KVK seasonal branch when fighting is ACTIVE.
- Both routes retain handled booleans and import acknowledgment ordering. No second notification
  or refresh is added on failed/unknown outcomes. Existing SQL audit exception/status behavior is
  preserved: completed means workflow completion, never proof of Discord receipt.
- Package facade already forwards the return; no edit is needed. Processing pipeline and manual
  SQL command need no change; the latter passes None flags and does not enter seasonal publication.

SQL/DAL/migration manifest is empty. Persisting the new outcome into ImportAudit rows, changing
refresh/batch status interpretation or moving SQL reads requires a separately validated contract and
approval. Current truthful delivery evidence is the adapter/interface result and correlated log,
not a new SQL record. Existing SQL-backed reads are unchanged; this does not certify all SQL paths.

### Findings and helper reuse

| Disposition | Scope |
| --- | --- |
| Fix now after design approval | Receipts for every seasonal route; partial attempts; discarded claim/commit observations; unconditional success; fighting claim after unconfirmed send. |
| Safe to preserve | Existing builders, production mentions/empty-data output, selectors, existing reservations, daily/weekly sequencing, H/I isolation and command surface. |
| Defer | Durable fighting ownership, pre-send KS ping-claim redesign, production Pre-KVK edit-replacement policy, SQL audit delivery persistence, executor/DAL extraction and broader lifecycle work. |
| Not runtime | Removed ops callback, archived instructions and obsolete manual KS tester; no replacement callback tests. |

Reuse existing builders, run_blocking_in_thread, DispatchAttempt and its _io lifecycle, module
logging, and existing test injection boundaries. H/I DiagnosticResult is session-specific; Ark
RegistrationDeliveryResult has different action/state semantics. Reuse their explicit-outcome
pattern without importing either type or adding production data to diagnostic stores. The shared
embed sender's Boolean/fallback contract cannot preserve these adapters' sends/edits/mentions.
Direct SQL and blocking work in KS/off-season remain captured under existing executor/architecture
work; no new DAL abstraction or executor fallback change is folded into receipt propagation.

### Exact proposed implementation manifest

Paths are repository-relative under `C:\discord_file_downloader`; all implementation remains gated.

Runtime existing:
- `admin_helpers.py`
- `stats_alerts/interface.py`
- `stats_alerts/embeds/kvk.py`
- `stats_alerts/embeds/kingdom_summary.py`
- `stats_alerts/embeds/prekvk.py`
- `stats_alerts/embeds/offseason.py`
- `stats_alerts/dispatch_reservations.py` (observation only, no protocol/schema change)
- `embed_offseason_stats.py`
- `upload_routes/honor_route.py`
- `upload_routes/prekvk_route.py`

Runtime new:
- `stats_alerts/delivery_outcomes.py` (Discord-independent outcome records and shared reporting)

Tests existing:
- `tests/test_kvk_embed.py`
- `tests/test_stats_alerts_fighting_lifecycle.py`
- `tests/test_prekvk_embed.py`
- `tests/test_stats_alerts_offseason_flow.py`
- `tests/test_embed_offseason_stats.py`
- `tests/test_prekvk_reservation.py`
- `tests/test_honor_upload_route.py`
- `tests/test_prekvk_upload_route.py`

Tests new:
- `tests/test_stats_delivery_outcomes.py` (result/aggregation and compatibility contracts)
- `tests/test_admin_helpers_stats_delivery.py` (real caller reporting and all-five gate)
- `tests/test_kingdom_summary_delivery.py` (KS receipts/claims/skips, not obsolete manual tester)

Documentation:
- `README-DEV.md`
- `docs/reference/runbook_diagnostics.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/Codex Task Pack - Discord Embed Payload Safety Phase 2K Production Stats Delivery Outcomes.md`
- `docs/task_packs/Codex Chat Starter - Discord Embed Payload Safety Phase 2K Production Stats Delivery Outcomes.md`

Tooling, config, dependency, command, view, startup, SQL/DAL/migration and state-format manifests:
empty. The observation change in dispatch_reservations.py is runtime code, not a persistence
migration. Preserve guard.py, state.py, diagnostic/session modules and their paths/schemas.
This design revision changes only the task pack and starter; the implementation manifest is a plan.

### Deterministic tests and gates

Run scripts/select_tests.py on the full manifest above. Tests-path changes require the full suite,
imports and registration in addition to these focused behavior checks:

1. Positive fighting receipt triggers exactly one claim; caught send exception/no receipt triggers
   zero claims. False claim retains sent identity. Preserve cap=3, exclusion and test bypass.
2. Distinguish preparation failure from entered-send uncertainty, including cancellation/timeout.
   After an unknown fighting attempt, an independent second invocation remains eligible under
   existing counts; prove this limitation with counters without introducing an automatic retry.
3. KS sent then primary skipped/failed/unknown; KS failed then primary sent. Preserve KS preclaim,
   false-claim silent send, no-data skip, missing destination ordering and actual IDs.
4. Pre-KVK fresh send and same-day edit return actual identities. Test accept/projection failure
   after receipt, cancellation during accept, and unknown edit followed by legacy fresh fallback.
   Keep both attempts and existing reservation/clear order, never infer receipt from state.
5. Off-season daily/weekly independent outcomes, Monday boundary, actual resolved destination,
   embedded KS inclusion/claim identity, no destination, guarded versus storage-unavailable failure,
   no-data formatting and thrown send. Preserve legacy return_receipt and default None contracts.
6. Reservation exceptions still reach __aexit__; journal/CSV/projection transitions are unchanged.
   Commit observability must not add I/O, retries or drain changes; confirmed receipt survives
   bookkeeping failure and uncertainty remains blocked by existing Pre-KVK/off-season protocol.
7. Upload selectors, nonduplicate gate, handled returns, import acknowledgments and SQL audit calls
   are unchanged; delivery logs include partial outcomes without relabelling import rows as receipts.
8. Compare complete production payloads/mentions; empty fighting reports still send. Regress H/I
   real Pycord invocation/options, v1/v2 retained sessions, ownership, historical selection, explicit
   destination, restart, cancellation and mention suppression. Default direct adapters stay compatible.

Run existing `tests/test_kvk_embed_diagnostics.py`, `tests/test_kvk_embed_diagnostic_command.py`,
`tests/test_kvk_embed_diagnostic_lifecycle.py`, `tests/test_prekvk_diagnostics.py`,
`tests/test_prekvk_dispatch_diagnostics.py`, `tests/test_prekvk_dispatch_diagnostic_lifecycle.py`,
`tests/test_prekvk_dispatch_diagnostic_view.py`, `tests/test_stats_alerts_guard.py`,
`tests/test_stats_alerts_state.py` and processing-pipeline regressions unchanged.
Use temporary stores and injected fake Discord calls/counters only; no live failures, global
monkeypatch, state swapping, forced duplicates or removed-ops callback coverage.

After approval: applicable hooks; architecture/deferred/security-routing validators; selector;
focused tests; full pytest with operational-log isolation/log-noise verification; imports and
registration 36/100/24. Tests are not implemented or executed as part of this design revision.
The Markdown-only revision gets documentation validation and a precise no-runtime security skip.
Runtime review remains Changes-only, Deep off, immutable separate bot-history ranges; SQL no-diff
skip. Do not reuse a previous sealed result for the new expanded runtime manifest.

Design-revision validation: selector ran against all 11 proposed runtime, 11 test and five docs
paths and recommended full pytest, smoke_imports and validate_command_registration. Architecture
validation passed with zero changed Python files; deferred validation passed for both changed
Markdown files; security-routing validation passed with zero errors/warnings; git diff --check
passed. Runtime pytest/imports/registration and runtime security discovery are intentionally not
run for this documentation-only design. Applicable hooks remain an implementation/PR handoff gate.

### Natural smoke, rollback and approval

Before rollout establish the final Phase 2J production checkout/deployed SHA/restart evidence.
For Phase 2K capture approved deployed SHA, clean checkout and associated restart, plus existing
production/diagnostic state baselines. Observe natural eligible fighting and seasonal routes when
available, correlating each outcome with actual destination/message identity and independent
claim/commit result. Observe same-day Pre-KVK edit and Monday daily/weekly only when natural;
unavailable calendar opportunities stay pending. Capture skips without forcing another send.
H/I previews do not close production admission; Phase 2F public-save remains separately pending.

Rollback reverts only the Phase 2K delta through reviewed production deployment, retaining Phase 2J
removal and all CSV/journal/reference/diagnostic state. No reset, deletion, migration, quota repair or
manual lock removal. Restart on the rollback SHA. Rollback restores lost outcome reporting and
the old fighting claim-after-swallowed-error behavior. Unclaimed ambiguous attempts cannot be
reconstructed into safe claims automatically; no backfill or replay is authorized.

Approve this complete design, including the positive-receipt-only fighting claim and later-natural-
invocation ambiguity tradeoff, before runtime/test implementation. No KS claim timing change,
Pre-KVK replacement-policy change or durable fighting admission change is bundled implicitly.

### Deferred Optimisation
- Area: fighting dispatch in stats_alerts/interface.py and stats_alerts/guard.py
- Type: architecture
- Description: Positive-receipt-only claims remove false success accounting but leave ambiguous sends, receipt-before-claim crashes and concurrent check/send races without durable fighting ownership.
- Suggested Fix: Extend the existing separately approved fighting admission investigation with an explicit reservation, ambiguity, recovery and migration contract before attempting duplicate prevention.
- Impact: high
- Risk: high
- Dependencies: Separate operator approval, production overlap evidence or deterministic tests, restart/recovery design and Changes-only review; no protocol implementation in Phase 2K.

### Deferred Optimisation
- Area: standalone/embedded KS claims and production Pre-KVK edit fallback
- Type: consistency
- Description: KS pre-send ping claims may remain consumed after failure; production Pre-KVK can replace after an ambiguous edit. This design observes both accurately but preserves these existing policies.
- Suggested Fix: Review the two policies in separately bounded decisions, preserving ping eligibility and existing reservation behavior until their failure/ambiguity semantics are approved.
- Impact: medium
- Risk: medium
- Dependencies: Explicit policy approval and deterministic claim/edit/send ordering tests; keep H/I behavior unchanged.

### Deferred Optimisation
- Area: services/honor_import_audit_service.py and services/prekvk_import_audit_service.py
- Type: consistency
- Description: SQL refresh/batch completion records workflow status but has no per-publication delivery/receipt contract; correlated Phase 2K logs do not change that persisted meaning.
- Suggested Fix: Separately validate and design durable delivery details/status semantics without converting successful ingestion into a false delivery receipt or retrying imports.
- Impact: medium
- Risk: medium
- Dependencies: Authoritative SQL validation and separate contract approval; no SQL/audit mutation in Phase 2K.
