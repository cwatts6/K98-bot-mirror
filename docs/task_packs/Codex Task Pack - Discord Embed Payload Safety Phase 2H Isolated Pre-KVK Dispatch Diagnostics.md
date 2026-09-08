# Codex Task Pack - Discord Embed Payload Safety Phase 2H Isolated Pre-KVK Dispatch Diagnostics

## 1. Status and objective

- Date: 2026-09-08
- Owner: Chris Watts
- Status: operator-approved next task; first response audit/scope and architecture only, then approval before implementation.
- Repositories: K98-bot-mirror first; production patch promotion after validation; SQL separately gated.
- Objective: enable an operator to exercise the real Pre-KVK reservation protocol against Discord outside the calendar window, with isolated durable diagnostic state and mentions disabled. This is a Phase 2 validation extension, not a change to production eligibility or payload policy.

Phase 2G is complete as an accepted implementation and bounded-validation delivery. Its archived
pack owns the delivered protocol and limitations. Mirror #258 and production #565 were OPEN at
preparation; operator merges and final verification remain pending. Revalidate actual states,
production-main head, deployed head, worktree, mirror base and Phase 1–2G source presence before
coding. Do not assume archival status proves deployment or that a restart log proves a Git head.

Reviewed Phase 2G runtime: mirror `bd99ea1421286ddb152f7729e11de664116d7e47`, production
`fea2767f52f345450225bcdf0c1f03f3d5e3dc4c`; Python trees match. Later closeout changes are docs-only.
Validation: 3314 passed / 2 skipped full, 91 pinned-filelock focused, 67 production focused,
log-noise/hooks/validators/import/registration passed. Separate mirror/production Changes-only,
Deep-off reviews completed without findings; exact IDs remain in archived Phase 2G closure.

## 2. Evidence and required reading

Read AGENTS.md, README-DEV.md, docs/reference/README.md and its required core standards. Apply
architecture-scope, discord-command-feature, test-selection and security-review-routing guidance.
Conditional references: command/canonical registration guidance, interaction safety, events and DM
reminders, REVIEW_HELPERS, startup operations; Promotion Guide only for delivery. Read applicable
SECURITY.md context. Consult authoritative C:\K98-bot-SQL-Server before any SQL-facing change.

Historical evidence:

- `archive/Codex Task Pack - Discord Embed Payload Safety Phase 2G Atomic Pre-KVK Reservation.md`
- `archive/Discord Embed Payload Safety Audit Findings.md`
- `archive/Codex Task Pack - Discord Embed Payload Safety Phase 2F Active Reminder Tracker Atomic Persistence.md`

The supplied 2026-09-08 log shows graceful restart, full startup at 09:17:05 and normal fighting-KVK
daily-cap skip at 09:21:50. It contains no reservation/commit receipt. The generic success line after
the skip is not delivery proof. Pre-KVK is outside its current calendar window. Existing
`/ops test_embed` follows current season; `/kvk_admin test_embed post_here:true` forces fighting KVK,
not Pre-KVK. `send_prekvk_embed(..., is_test=True)` bypasses reservation but still reads/writes the
shared message reference, so direct invocation is not isolated protocol validation.

## 3. First-response scope and architecture gate

Map command permission/defer/error/usage/version/registration patterns; scheduled/manual/test
callers; calendar routing; Pre-KVK build/edit/fresh paths; the real reserve/start/receipt/finalize
lifetime; every journal/CSV/message-state/lock producer; offloads, cancellation, shutdown/restart,
content sources, views/buttons and potential mentions. Distinguish singleton metadata from actual
ownership. Classify safe / fix now / defer / not runtime with concrete source evidence.

Propose one subcommand in an existing admin group (provisional name `/ops prekvk_dispatch_test`;
final spelling/options require architecture approval). Preserve the existing admin AND notify-channel
invocation boundary. Require an explicit validated guild text destination; no silent stats-channel
fallback or arbitrary path input. Explain destination eligibility, bot permissions, requester
authority, prevention of concurrent command spam and where acknowledgements are ephemeral.
No new top-level group or broadening of existing command permissions is approved.

The command must be thin: permission/input checks, safe defer, service invocation, truthful bounded
result. A service owns diagnostic orchestration and a repository/context owns persistence paths.
Reuse the real Phase 2G transitions and canonical renderer; do not duplicate the reservation engine
or call the existing bypass and describe it as reservation testing. No temporary global monkeypatch,
production date/SQL edits or runtime state-file swapping on a running bot.

## 4. Isolation contract to prove before implementation

- Isolate journal, CSV, message reference, all corresponding locks and generation counters together.
  `ReservationStore(log_path=...)` alone is insufficient: current message projection uses global
  state paths. Trace every read/write, including stale clear, test send, receipt recovery and views.
- Use trusted fixed-root paths and validated opaque session identity. Define guild/channel/session
  namespace, durable reopening after restart, owner access, retention, cleanup and rollback. No
  command-supplied filesystem paths or silent new schema/SQL selection.
- Keep production adapters/defaults compatible. Do not alter production quota, eligibility,
  timestamps, off-season exclusion, identity, payload, mentions, executor or uncertainty semantics.
- Explicitly suppress all allowed mentions for diagnostic sends and edits. If a visible diagnostic
  label is proposed, fit it within canonical budgets and document the limited payload difference.
  Local-time controls must not escape to shared production state or acquire broader authority.
- Preserve once-only offloads and cancellation drainage. Do not hold filesystem locks over Discord
  awaits. Fail closed on invalid state, contention, uncertain receipt or failed persistence; never
  retry a possibly delivered send merely to make the smoke pass.
- Separate same-day edit from fresh admission: a second renderer invocation may edit and therefore
  does not prove reservation rejection. Provide a bounded read-only admission/receipt observation
  or deterministic companion test that proves guard behavior without forcing a live duplicate.
- Define status output from actual outcome: sent / edited / guarded / uncertain / failed, with
  positive message receipt, destination and durable phase where appropriate. A returned coroutine
  or generic success log is not proof of publication or persistence.

The operator has approved this diagnostic direction, not an exact storage format, retention policy,
new SQL object, production reset/delete capability or general-purpose forced-send command. The first
response must make those decisions reviewable and request approval before runtime or test edits.

## 5. Candidate manifests — exact paths must be finalised in scope response

Runtime candidates: `commands/admin_cmds.py`, a small `stats_alerts/diagnostics.py` service (proposed),
`stats_alerts/dispatch_reservations.py`, `stats_alerts/state.py`, `stats_alerts/guard.py` and
`stats_alerts/embeds/prekvk.py` only where dependency injection is required. Identify whether any
view/registration helper actually needs modification; do not pre-authorise unrelated rewrites.

Test candidates: a new `tests/test_prekvk_dispatch_diagnostics.py`, existing reservation, Pre-KVK
embed, state, guard, fighting lifecycle and command registration/permission suites selected by
actual paths. Docs: this pack/starter, task indexes, canonical command reference, command versions
and operational smoke/recovery guidance where required by grouped-command conventions.

SQL manifest: **empty unless independently justified and approved**. Existing report reads reuse
the current service/DAL. A no-diff skip requires no schema/procedure/view/index/UDT/ProcConfig,
embedded query, DAL result-shape or SQL deployment delta. If any changes emerge, inspect the SQL
source repository, produce a separate exact manifest, validation and Changes review target.

## 6. Validation and smoke acceptance

Run selector with actual changed paths; architecture/deferred/security-routing validators, focused
pytest, smoke imports, registration and pre-commit. Run the full suite/log-noise check for changed
tests and persistence/command integration. Document justified skips. Tests must prove:

- Admin/notify boundary, wrong guild/channel, missing permissions, invalid session and no arbitrary
  destination/path escape; mention suppression for sends, edits, errors and component callbacks.
- Real protocol entry, positive receipt projection, isolated paths/locks and byte-for-byte unchanged
  production state across success, clear, failure, cancellation, restart and concurrent sessions.
- Same-session contention, distinct-session behavior, owner checks, existing edit vs guard semantics,
  UTC rollover, unknown/stale owners, accepted/uncertain recovery and fail-closed corrupt state.
- One worker invocation, loop responsiveness and cancellation drainage; existing production default
  paths/behavior and all Phase 1–2G payload/permission/visibility/mention contracts preserved.

Security gate: bot **Scan type: Changes; Deep off**, exact immutable base/head or docs-only skip as
applicable. New command, network destination and restart-sensitive paths require a scoped diff
review; no routine Codebase/Deep scan. SQL history receives a separate review only if changed.

After approved implementation, review, merges and production-main deployment, operator smoke:

1. Record deployed head; inspect isolated session identity and production state baseline.
2. Invoke in the permitted admin location with the explicit diagnostic destination. Observe one
   mention-neutral Pre-KVK message, valid payload/buttons and matching committed receipt/CSV/reference.
3. Reinvoke same session; verify expected edit/guard outcome without another fresh publication.
4. Gracefully restart; reopen the same durable session and verify identity/receipt retention and
   repeat behavior. Compare production state to baseline accounting for independent natural traffic.
5. Exercise permission rejection without sending. Record UTC times, message link, outcome and logs.

Do not inject live crashes, ambiguous Discord failures, simultaneous bot processes, forced mentions
or delete/reset uncertain records. Deterministic tests own those failure boundaries. Diagnostic
protocol smoke and natural production calendar/scheduler dispatch are separate acceptance rows.
The diagnostic enables broader validation now; it does not promise exactly-once or complete live
failure coverage. Carry any unobserved natural window into a named operator observation with owner.

## 7. Separate work and closure

Keep singleton repair, public child-task lifecycle, generic tracked-view timeout, DM redesign,
broad JSON consolidation, Stats/KVK History executor audits and ProcConfig pending-result/error
propagation repair separate. The 09:20:17 ProcConfig error and misleading pipeline success require
their own SQL-aware scope; the transient Sheets 503 recovered and does not justify a retry redesign.
The Phase 2F next-natural-public-save observation stays separate. Explain a hard dependency if one
is proved; do not silently expand this task.

Phase 2H closes only after its approved command, isolation and deterministic gates pass and operator
Discord protocol/restart smoke is recorded. Preserve any remaining natural production-window gate
honestly. Archive this pack only on explicit acceptance; leave operator merges/deployed-head
verification visibly pending until evidenced.
