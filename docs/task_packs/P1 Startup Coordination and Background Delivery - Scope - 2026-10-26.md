# P1 Startup Coordination and Reliable Background Delivery — proposed scope

26 October 2026. **Review/scope only; implementation not approved.** Analyse this
proposal in a new chat, validate current sources and recommend the final bounded
architecture for agreement. No PR, merge, deployment, restart, SQL/provider operation,
activation change or manufactured acceptance is authorized by this document.

## Scope summary

Deliver a coherent next phase that makes selected startup/background work owned,
observable and safe to stop/recover, while reducing duplicated lifecycle logic.
Build on delivered cache ownership, result contracts, draining adapters and existing
SQL writer authority. The original six-package phase is closed for exercised paths;
do not repeat its implementation or tests merely to recreate evidence.

Recommended scope comprises N1–N5 below, split into reviewable PRs only after
architecture agreement. N1 is a mandatory evidence/design gate. N2 behavior depends
on a demonstrated cause; N3/N4 can make useful progress without knowing an external
SQL lock holder. Do not tie the phase to an invented diagnosis.

## Candidate packages and affected layers

| ID | Package / outcome | Initial source targets and boundaries |
|---|---|---|
| N1 | Caller, authority and lifecycle map | `bot_instance.py`, `core/startup_lifecycle.py`, startup diagnostics, recovery lifecycle, admin/pipeline/compatibility entrypoints; existing export coordination/legacy snapshot services and DAL. Map each enabled entrypoint, dependencies, admission, producer-entry boundary, owner lifetime, completion evidence, cancellation, recovery and side effects. Mark unknown/unreviewed paths explicitly. Full inventory is analysis, not permission to rewrite every writer. |
| N2 | Evidence-backed startup coordination | Correlate R01 startup admission and monitor discovery with local operation timelines. Reuse existing lifecycle and authority; propose dependency ordering or bounded admission handling only for a reproduced conflict. Preserve lock order, tokens, fences, transaction boundaries and fail-closed unknown outcomes. If holder evidence is absent, deliver honest attribution rather than claiming a fix. |
| N3 | Selected public-reminder/background child ownership | `event_scheduler.py`, `reminder_task_registry.py`, existing task monitor/shutdown ownership and tracker I/O helpers. Start with public send/delete/expiry children; map DM overlap but expand only where required by the same lifecycle contract. Track children through completion, observe original work after deadlines, close admission/drain and retain ambiguous external effects. Reuse EventTaskBundle/cache gates; no new universal scheduler. |
| N4 | Reliable operator status response | `commands/admin_cmds.py::status_command`, `core/interaction_safety.py`, existing health/recovery services and recovery view. Diagnose R02; separate private acknowledgement/rendering from bounded service work. Assess existing inline synchronous `SELECT 1` and active provider probe: move blocking work behind the existing service/DAL pattern if included, with owned cancellation and no hidden duplicate probe. Preserve permissions and private visibility; ambiguous response failure never triggers automatic public fallback. |
| N5 | Delivery evidence and targeted recovery disposition | `rehydrate_views.py`, existing event rehydration lifecycle, Daily KVK Overview tracker/publication path, recovery reports. Distinguish handler registration, eligible visible message, observed callback, missing/access denied and uncertain send. Resolve R04 only with exact evidence. Reuse durable publication/repair mechanisms where suitable; any new persisted contract requires explicit design. No automatic repost or reopening retired workflows. |

Initial static evidence: `status_command` defers privately, then performs its DB
connectivity work and an active Sheets health check before direct original-response
editing. The recorded 10015 occurs at the final edit; that fact alone establishes
neither expiry nor the health probe as root cause. Legacy `event_scheduler.py`
creates child tasks for send and expiry paths; ownership coverage must be traced
through their registries before declaring them orphaned. Existing startup lifecycle
already orders phases. New code should extend those owners, not create a competing
supervisor or global serialization queue.

## Architecture direction and future-phase foundations

Commands/views retain permission checks, safe acknowledgement, interaction routing
and rendering. Services own orchestration, cancellation and result meaning. DAL
owns SQL/resource/transaction rules; file helpers own safe persistence. Legacy root
modules become thin adapters for selected changes, not new homes for a framework.

Produce a reusable, small contract only after fitting at least two actual consumers:
operation identity; not-entered/entered/completed/failed/unconfirmed; observation
deadline distinct from execution; expected waiting versus failed dependency; source
and persistence evidence; lifecycle owner and recovery policy. Reuse
`services/cache_outcomes.py`, startup diagnostics, existing drain helpers and task
registries where their semantics fit. Process-local IDs remain process-local.
Critical send/delivery state cannot be certified by an in-memory task registry alone.

Foundations that reduce later effort:

- One explicit caller-to-authority map with coverage gaps, reused by WS1/WS2/WS6.
- Shared deterministic lifecycle contract tests for selected adapters, avoiding
  duplicated timeout/cancellation/reentry tests and bespoke recovery semantics.
- Additive passive evidence adapters that distinguish monitor health, admission,
  workflow completion, persistence and independently verified delivery.
- A documented extension checklist: owner, identity, entry point, durable authority,
  pre/post-entry retry policy, shutdown, privacy, outcome and acceptance evidence.
- A disposition model for missing/inaccessible/retired/uncertain messages that can
  later support Ark/MGE/voting/calendar without implementing every domain now.

Avoid speculative schema abstraction, global executor rewrites, universal workflow
engines and blanket startup serialization. These increase later coupling without
an evidenced need. Do not alter force/TTL/source-season semantics for cache reuse.

## SQL and persistence review

Authoritative definitions are in `C:\K98-bot-SQL-Server`. Static source confirms
`dbo.SP_Stats_for_Upload` has its own import/publication locks and validation, while
`dbo.ExportPreparation` carries existing coordination state. The observed SQL 51400
request refusal is in Bot coordination admission before producer execution; it is
not proof the procedure itself ran or that its own internal lock failed. Read the
actual `export_coordination_dal`, `legacy_export_snapshot_dal` and
`unowned_sql_hold_dal` paths and corresponding SQL contracts before any design change.

Validate exact resource/order/owner boundaries against current definitions. Do not
infer a blocking session from the requester's session. The recovery discovery path
also takes account admission: correlate separately from startup. No new SQL objects,
permission grant or migration is presently justified. If needed by evidence, return
an explicit Bot/SQL contract and ordered rollout proposal for approval. Static source
is not proof of installed production definitions. No live queries/probes in scope.

For reminder persistence, identify existing message/tracker identity, atomic write,
sent-versus-scheduled authority and readback. Send succeeded plus persistence failed
must stay uncertain, never eligible for automatic duplicate send. Drain must not
erase entered work; a missing callback or task handle is not proof of absence.

## Refactor decisions and exclusions

Investigate direct SQL/blocking work in status command and interaction error handling
as N4, reusing existing helpers. Investigate child ownership/persistence as N3.
Diagnostic blind spots belong in N1/N2/N5, with redacted structured outcomes.
No dead-code removal or duplicate-helper rewrite without actual caller evidence.

Carry R05 singleton exclusivity as separate protected-launcher analysis; include a
fix only if the new chat demonstrates and bounds the defect. R08/R09 broad legacy
report/executor fixes, R10 durable profile invalidation, R11 dispatch-policy changes,
R14 independent external monitoring, R15 updater/recovery productization and R16
history/quota/transport work remain separate. N1 inventories their interfaces but
does not claim implementation. P0 R17/R18 remain acceptance duties, not P1 features.

## Test strategy and measurable acceptance

| ID | Required evidence before declaring the next package complete |
|---|---|
| B01 | Every selected entrypoint maps to an existing authority/owner and explicit evidence; remaining census gaps are listed. No unreachable/disabled path counted as production coverage. |
| B02 | A coordination change has a deterministic before/after conflict reproduction; unrelated work can still progress and authority checks/budgets are preserved. Unknown external holder remains labelled unknown. |
| B03 | Refused-before-entry work does not execute; entered/unknown work does not replay; independent requests cannot borrow owner tokens. |
| B04 | Child send/delete/expiry tasks are supervised; repeated cancellation drains or records the exact unresolved operation; reconnect/startup does not duplicate registration or children. |
| B05 | Send success/persistence failure, lost acknowledgement, missing/access-denied message and stale/retired tracker remain distinct; no blind resend/repost or age-based settlement. |
| B06 | Status acknowledges privately before slow work; deterministic acknowledgement/edit/follow-up failures including 10015 preserve privacy and error truthfulness. The response cannot trigger duplicate health work or duplicate side effects. |
| B07 | Passive report reads issue zero SQL/provider/refresh/recovery operations, redact IDs/secrets/payloads, and distinguish stale/unavailable/healthy observations. Active probes remain explicit. |
| B08 | Delivered cache original-result semantics, Location paths, event loaded-empty behavior and original-message callback contracts remain regressions. Source scan 1193 stays expected off-season data. |
| B09 | Each claimed speed improvement has a comparable controlled before/after measurement with workload and timings; correctness does not depend on claimed performance. |
| B10 | Later authorized deployment has exact source/readiness evidence plus naturally exercised feature receipts. Unexercised natural transition/rollover remains pending; local tests and a healthy report do not manufacture acceptance. |

Likely existing suites: `test_startup_lifecycle.py`, `test_monitor_startup_diagnostics.py`,
`test_player_stats_startup.py`, `test_export_contention.py`,
`test_legacy_export_snapshot.py`, `test_unowned_sql_hold_sql.py`,
`test_event_startup_recovery.py`, `test_event_scheduler_active_reminders.py`,
`test_reminder_task_registry.py`, `test_interaction_safety.py`, applicable admin
command/recovery-view suites. Confirm exact current names before selecting tests.
Use barriers/fakes/temp files, not sleep-sensitive races or production fault injection.
Add regressions for observed causes only after establishing them. Run focused suites,
architecture/deferred/security-routing validators and selector; full offline suite,
log isolation, formatting/type checks, synthetic imports and command registration
at runtime PR handoff as selected by the test skill. Skips retain their reasons.

## Security routing

This proposal and closeout are documentation-only: documented scan skip. Future
runtime diffs touch interactions, SQL admission and restart-sensitive persistence:
use `k98-security-review-routing`, then Changes review, Deep off, exact recorded
base/head for each Bot repository target. Separate SQL Changes review only if SQL
changes. Root/nested SECURITY.md are policy context, not scan launch instructions.
No repository-wide/deep audit is requested. Suspected vulnerabilities go to private
triage rather than deferred-optimisation scoring.

## Priority and sequence for agreement

Provisional planning scores (1–5; not measured failure frequency and not security
severity): score = impact + frequency + risk reduction - effort. Refresh estimates
after N1; dependency and risk gates take precedence over totals.

| Package | Impact | Frequency | Risk reduction | Effort | Score |
|---|---:|---:|---:|---:|---:|
| N1 inventory/evidence map | 5 | 4 | 5 | 3 | 11 |
| N2 startup coordination | 4 | 3 | 4 | 4 | 7 |
| N3 selected child ownership | 5 | 4 | 5 | 4 | 10 |
| N4 operator status reliability | 3 | 3 | 3 | 2 | 7 |
| N5 delivery disposition/evidence | 4 | 4 | 4 | 3 | 9 |

1. New chat reviews latest baseline, closeout and evidence; creates N1 caller map,
   bounded cause assessment and concrete affected-file/SQL contract list.
2. Agree the final architecture and package boundaries. Decide whether N2 has enough
   causal evidence for behavior changes and whether N5 needs durable schema work.
3. After implementation approval, deliver independent reviewable increments: N4
   response/service correction; N2 justified coordination; N3 ownership with N5
   evidence adapters. Shared contract goes first only when multiple consumers fit.
4. Reconcile contract tests, docs and security at each PR, then integrated acceptance.
   Deployment and operational acceptance remain separately authorized.

First new-chat output: a substantial but bounded recommendation, options/tradeoffs,
affected layers, established versus unknown causes, tests, security, acceptance,
sequencing and complete residual crosswalk. Do not stop at a list of tiny patches;
also do not widen this into all P1. Ask for agreement on that concrete proposal.

Obligation owner: [phase closeout and R01–R18 ledger](P1%20Startup%20Cache%20Foundations%20-%20Closeout%20-%202026-10-26.md).
