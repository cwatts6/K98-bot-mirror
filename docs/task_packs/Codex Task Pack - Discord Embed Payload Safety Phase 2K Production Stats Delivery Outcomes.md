# Phase 2K — Production Stats Delivery Outcomes

Status: proposed next Phase 2 slice; audit/scope and architecture only. Implementation is NOT
approved. Preparation follows successful Phase 2J delivery/smoke, not permission to change code.

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

Can the production fighting publication path and affected callers preserve actual channel/message
identity and truthful outcome reporting without changing eligibility, appearance, mention defaults,
admission or retry behaviour? Audit all seasonal routes to protect compatibility; propose the
smallest coherent adapter/interface/caller slice. If legacy Pre-KVK/offseason/KS lack receipts,
report unverified/unknown explicitly or request separately scoped adapter changes. Do not fabricate
sent results to satisfy a new common return type. Do not reuse isolated diagnostic receipt roots
as production stores or claim that a new result object is a durable reservation.

Changing when claims occur, consuming caps after failure, retries, recovery, or concurrent sends
can change the production protocol. Identify any required semantic change explicitly and stop for
approval rather than smuggling it into logging repair. No durable fighting reservation extension,
cap/mutual-exclusion redesign or exactly-once promise is part of this preparation.

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
