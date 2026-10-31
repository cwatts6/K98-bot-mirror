# Deferred Optimisations

> **Current status - 28 October 2026, A1a deployed:** Mirror PR 454 and private
> PR 702 are merged; private `87c1b39325daaa0ca1a8c0cbca656df82d7fa46b` is deployed
> and Discord online. Signup/edit/withdraw are verified on this runtime. A1a qualified
> datasets and timing are delivered; the A1b design packet is prepared for approval.
> Rank confirmation still waits for board refresh. Report 62 queue closure, the older
> configuration decision and separate Discord lag remain follow-ups. Exact audit/cleanup,
> unexercised cases, fresh import/export, natural acceptance and P0 remain explicit.
> See [deployed closeout](../task_packs/P1%20MGE%20A1a%20-%20Deployed%20Closeout%20-%202026-10-28.md) and [A1b design packet](../task_packs/P1%20MGE%20A1b%20-%20Design%20and%20Delivery%20Packet%20-%202026-10-28.md).
> Earlier dated status and next-action text is historical where superseded.
> This documentation update requires no deployment, restart, SQL apply or repeat import.


26 October overlay: the six Startup Cache Foundations packages are delivered,
deployed and closed for exercised paths. The original eligible Ark callback passed.
Natural event transition and exact Daily KVK Overview disposition remain open.
See the [closeout / R01–R18 ledger](../task_packs/P1%20Startup%20Cache%20Foundations%20-%20Closeout%20-%202026-10-26.md) and
[next-phase scope](../task_packs/P1%20Startup%20Coordination%20and%20Background%20Delivery%20-%20Scope%20-%202026-10-26.md). Current P0 defects remain F03/F05;
this register does not turn them into optional debt or erase earlier accepted work.

### Deferred Optimisation
- Area: profile cache invalidation across process restart and remaining cache callers
- Type: consistency
- Description: Startup foundations protects in-process publication against an older candidate, but intentionally retains the existing disk envelope and non-forced post-import warm. It does not provide durable invalidation or prove a reused snapshot includes an upstream update. Other cache callers remain outside the selected startup scope.
- Suggested Fix: First inventory actual update/invalidation callers and required source revision evidence. Separately design durable invalidation or revision-bound refresh only where required, using the explicit fresh-request seam and existing owned workers; preserve fallback provenance and avoid replaying accepted imports.
- Impact: medium
- Risk: medium
- Dependencies: Separate source-revision contract and operator scope; this is not closure of WS2, WS4 or WS6. Do not treat a demonstrated current P0 pipeline defect as optional debt.


Active deferred optimisation items are staged here before they are grouped, scored, or promoted
to GitHub issues/task packs.

Resolved historical notes live in `archive/deferred_optimisations_resolved.md`.

The approved embed implementation programme closes through Phase 2K, whose merges and final
clean deployed-main/restart evidence are now recorded. Unresolved items below remain open.
[Bot Operational Reliability](../task_packs/Bot%20Operational%20Reliability%20-%20Programme%20Pack.md) groups ProcConfig WS1, remaining executors,
lifecycle, DM/JSON, durable dispatch and evidence-gated import admission as separate workstreams.
The [24 October P0/P1 reconciliation](P0%20delivery%20and%20P1%20recovery%20status.md)
supersedes historical design-only status: selected WS1–WS6 capabilities were delivered
in P0, while their residual scope remains open. Tracked-view restoration is the first
P1 slice; its approved runtime implementation and local review are complete, with
eligible original callback accepted on 26 October; exact overview disposition and other residuals remain open. Completed portions are recorded in the resolved history without closing
whole workstreams. Full P0 acceptance, including natural rollover, remains separate.
Natural Pre-KVK/off-season and Phase 2F public-save observations remain independent. The incoming
inventory upload privacy finding belongs in security triage, not this optimisation register.

### Deferred Optimisation
- Area: `services/export_reconciliation_service.py` publication history/readback and `services/export_request_budget.py`
- Type: performance
- Description: The confirmed 21 October KVK16 check took 715 seconds / 132 requests, down from 816.7 seconds / 170 requests. Existing timings attribute 130.032 seconds to retained history and 148.735 seconds to sealed history. Provider readback took 403.546 seconds including 258.027 seconds of budget waiting; sealed replay took 29.562 seconds. Detail intervals overlap. Batching improved the observed check, but substantial history and quota-wait time remains; the precise remaining history cost is not yet attributed.
- Suggested Fix: Use the saved timing evidence to scope history replay/SQL round-trip profiling and quota scheduling separately. Preserve complete sealed request membership, exact response replay, shared-account budgets and independent final verification. Benchmark changes with deterministic retained histories first; request a new provider measurement only for a materially changed candidate, not to repeat the already confirmed check.
- Impact: medium
- Risk: high
- Dependencies: Separate bounded performance work after P0 recovery correctness. Do not weaken budgets or evidence verification, and do not move unfinished P0 acceptance into this item.

### Deferred Optimisation
- Area: standalone/embedded KS claims and production Pre-KVK edit fallback
- Type: consistency
- Description: KS pre-send ping claims can remain consumed after send failure. Legacy non-durable Pre-KVK routes may replace after an ambiguous edit. Current diagnostic and P0 durable-processing routes instead propagate the failure and retain uncertainty; do not describe every production route as using the old fallback. Phase 2K did not itself change the two legacy policies.
- Suggested Fix: Review each policy in a separately bounded decision with failure/ambiguity and mention semantics, preserving existing reservations and diagnostic behavior until approved.
- Impact: medium
- Risk: medium
- Dependencies: Explicit policy approval and deterministic claim/edit/send ordering tests; no policy change in Phase 2K.

### Deferred Optimisation
- Area: services/honor_import_audit_service.py and services/prekvk_import_audit_service.py
- Type: consistency
- Description: SQL refresh/batch completion records workflow status and has no per-publication receipt contract. Phase 2K correlated outcome logs do not change its persisted meaning.
- Suggested Fix: Separately validate and design durable delivery details/status semantics without turning successful ingestion into a false delivery receipt or retrying imports.
- Impact: medium
- Risk: medium
- Dependencies: Authoritative SQL validation and separate contract approval; no SQL audit mutation in Phase 2K.

### Deferred Optimisation
- Area: `proc_config_import.py::run_proc_config_import`, subprocess result reporting and `processing_pipeline.py`
- Type: consistency
- Description: September operator logs established HY000 while restoring autocommit after targets, followed by reported success. The 24 October source reconciliation finds coordinated configuration/targets/checkpoint transaction ownership, result-set drainage, explicit lost-acknowledgement uncertainty and once-only participating offloads now implemented. Accepted startup configuration receipts support delivery. Remaining WS1 work is the legacy report/manifest and cleanup contract; the historical HY000 symptom must not be restated as an unchanged coordinated-path defect.
- Suggested Fix: Audit remaining entrypoints against the delivered transaction/result contract and existing tests. Reconcile legacy v1 reports, per-run artifact identity (including second-resolution naming), cleanup failures and truthful partial/unknown outcomes. Extend only demonstrated gaps; preserve accepted commits and do not rerun imports to reproduce historical evidence.
- Impact: medium
- Risk: medium
- Dependencies: Separate SQL-aware scope and source-of-truth verification before implementation; deterministic cursor/transaction/result and wrapper tests. No repair in Phases 2G–2J; separate from Phase 2K delivery outcomes.
- Status: WS1 partially delivered through P0; residual contract reconciliation required; owner Chris Watts
- Last verified: 2026-10-24

### Deferred Optimisation
- Area: `core/event_rehydration_lifecycle.py`, `bot_instance.py` tracked-view scheduling and `rehydrate_views.py`
- Type: architecture
- Description: Historical generic-view cancellation is fixed in merged #439/#688 and deployed private d127cb6e08aaecf0a397b9f5a3d41279280b245c. Successor logs and report 42 verify a complete 21-entry pass beyond the ten-second deadline: 20 attached, one inaccessible daily overview pruned, zero failed/unconfirmed/unattempted. The eligible original Ark local-time callback passed on 26 October; exact overview disposition and other historical-message eligibility remain open. Task completion and incident counts do not replace message evidence.
- Suggested Fix: Preserve the passed eligible original-message callback; do not repeat it. Assess other message families only when required by their own scope. The three operator-inspected Ark examples are historical closed/cancelled posts without buttons and are unsuitable tests. Confirm the overview disposition without automatic reposting or repeated imports. Retain handler-registration evidence and keep remaining WS3 readiness and scheduler work separate.
- Impact: medium
- Risk: medium
- Dependencies: Separate lifecycle scope; preserve view permissions, identity and shutdown semantics; not a Pre-KVK diagnostic dependency.
- Status: WS3 first slice deployed; source/startup and restoration inventory verified; eligible original callback passed 26 October; overview disposition and broader coverage remain open; owner Chris Watts
- Last verified: 2026-10-26
- Plan: [P1 tracked-view restoration](../task_packs/P1%20Tracked%20View%20Restoration%20-%20Architecture%20and%20Implementation%20Plan.md)

## Status model

- `implementation-ready`: the current defect or hardening opportunity is confirmed and bounded.
- `operator policy decision required` / `operator-gated`: no implementation starts without an explicit owner decision.
- `promoted task pack — refresh required before execution`: a task pack exists, but its evidence or object map must be refreshed.
- `evidence required` / `re-audit required`: collect current measurements before proposing implementation.
- `blocked`: a named prerequisite or source contract is missing.
- `later refactor`: valid architectural debt with no immediate correctness requirement.
- `proposed design programme`: product/design discovery is required before implementation.
- `watchlist` / `conditional watchlist`: retain for observation; do not treat as approved executable work.

`Last verified` records the most recent documentation/repository review date. It does not by itself
prove current Production behaviour; Production evidence remains an explicit dependency where required.

### Deferred Optimisation
- Area: stranded-export operator recovery helper, export child lifecycle and Recovery Centre closeout
- Type: architecture
- Description: The reviewed r3 operator helper is now delivered through #438/#687, merged, deployed and verified by the operator. The successful stranded-export recovery still required a separately prepared packet; routine operators need a supported workflow rather than bespoke preparation. The old export was abandoned, not delivered.
- Suggested Fix: Productize inspect/review/apply/verify using the delivered helper and existing exact custody, ownership, configuration, fence, sealed closure and closeout checks. Keep native privilege operations in the operator helper. Offer resume, reconcile or abandon only when supported evidence permits, retain explained blocks for missing evidence, and keep permission for subsequent work separate from old delivery status.
- Impact: high
- Risk: high
- Dependencies: Existing helper/runbook and SQL closure/closeout contracts; source delivery is satisfied, not a pending PR dependency. Separate architecture, SQL validation, restart/lost-acknowledgement/permission tests and bot/SQL Changes reviews when implementation touches them. Preserve URLs, committed outputs and historical receipts.
- Status: P1 architecture follow-up; owner Chris Watts
- Last verified: 2026-10-24

### Deferred Optimisation
- Area: recovery observer, review SQL and Discord event-loop diagnostics
- Type: performance
- Description: Retained accepted-run logs contain transient observer unavailability, SQL 1222 review contention and 41.7/42.2-second websocket delays. The later complete recovery report is healthy. These observations do not establish one common cause or a current unresolved P0 defect.
- Suggested Fix: Perform bounded offline attribution using saved logs, distinguishing contention from provider failure. Capture missing timing boundaries before proposing focused instrumentation, and suppress repeated non-actionable alerts without hiding correctness failures. Return any demonstrated pipeline/monitor correctness defect to F03/F05.
- Impact: medium
- Risk: medium
- Dependencies: Retained logs and receipts; no repeated import/export, provider probe or production fault injection. Coordinate with, but do not duplicate, the existing publication timing item.
- Status: evidence required; bounded offline investigation
- Last verified: 2026-10-24

### Deferred Optimisation
- Area: `scripts/prepare_k98_update.py` protected updater transition registry
- Type: architecture
- Description: The reviewed registry now retains 42 exact transitions, including startup_cache_foundations_v1. Historical 40-entry capacity wording is superseded by delivered release support. General capacity management/receipt-compatible retirement remains a separate design question; no current exhaustion is established.
- Suggested Fix: Check actual occupancy before adding a transition beyond capacity. Design bounded growth or explicit compatible retirement while preserving old authenticated pins and resumable release receipts; do not silently discard entries.
- Impact: medium
- Risk: medium
- Dependencies: Next release requirements, protected package rehearsal and updater Changes review for any implementation.
- Status: conditional capacity follow-up
- Last verified: 2026-10-26

### Deferred Optimisation
- Area: SQL session-lock acquisition acknowledgement and connection cleanup
- Type: consistency
- Description: Retained qualification does not establish an actual transport break after the server grants a session lock but before the client receives its acknowledgement. A closed proxy alone is not proof of server-session cleanup.
- Suggested Fix: Reconcile current tests, then add a disposable restricted-user SQL/ODBC transport fixture that proves cleanup and no replay after acknowledgement loss. Preserve unknown outcomes if session termination cannot be established.
- Impact: low
- Risk: medium
- Dependencies: Disposable local SQL environment only, authoritative lock/connection contracts and separate test scope; no production fault injection.
- Status: retained qualification gap; separate from accepted production run
- Last verified: 2026-10-24

### Deferred Optimisation
- Area: `core/event_rehydration_lifecycle.py::wait_for_events` and dependent scheduler readiness
- Type: consistency
- Description: The former empty-result readiness defect is delivered through #441/#690 and #442/#691. Reports 43–45 naturally show loaded_empty, not stale, with registration loops running and data-dependent one-shots/DM restoration waiting_for_events. Natural empty-to-populated transition remains unobserved.
- Suggested Fix: Preserve the delivered distinction and deterministic tests. Accept the natural populated transition only with each deferred member and DM restoration completing without duplicate entry; do not force events, refresh or restart.
- Impact: medium
- Risk: medium
- Dependencies: Separate WS3/readiness slice after tracked-view restoration; preserve reminder eligibility and public-save semantics.
- Status: Deployed; natural loaded-empty behavior accepted, populated-transition acceptance pending. Retain [implementation history](../task_packs/P1%20Event%20Cache%20Readiness%20-%20Implementation%20and%20Acceptance.md) and remaining WS3 obligations separately.
- Last verified: 2026-10-26

### Deferred Optimisation
- Area: `event_calendar/reminder_state.py`, `player_self_service/service.py`, `event_calendar/reminder_candidates.py`
- Type: performance
- Description: Phase 5D.1 must read Calendar sent-key state to exclude already delivered alerts. The existing file-backed `CalendarReminderState` stores one global, append-only mapping and exposes only a full-file load, so each private summary request parses the complete history and the pure projection copies every sent key before applying user-scoped eligibility. Codex Security reproduced approximately linear cost with synthetic state: about 93 ms and 28 MB traced peak at 100,000 keys, and about 514 ms and 135 MB at 500,000 keys. Ordinary members cannot directly grow the state, and representative production size or material shared-service impact is not yet established, so this is not a reportable security finding or an approved Phase 5D.1 persistence change.
- Suggested Fix: First record production state byte/key count and growth rate, then run a controlled production-clone concurrency check at that observed size while measuring RSS, event-loop latency, scheduler health, and interaction failures. If evidence warrants a change, scope a separate Calendar-state lifecycle slice to define retention/pruning, user-scoped indexing or an equivalent bounded read contract, concurrency controls, restart behavior, migration/rollback, and dispatcher/projection parity without changing sent-key semantics.
- Impact: medium
- Risk: high
- Dependencies: Phase 5D.1 deployed baseline; production `event_calendar_reminder_state.json` size evidence; operator-approved controlled concurrency test; no persistence or sent-key contract change without a separate task pack.
- Status: evidence required
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: `ui/views/inventory_views.py`, `inventory/inventory_service.py`, inventory import lifecycle callbacks
- Type: architecture
- Description: Inventory import lifecycle coordination remains intentionally view-heavy. `ui/views/inventory_views.py` routes upload-first messages, command-session continuations, multi-governor selection, review interactions, correction modals, additional-material continuation, approval, rejection, cancellation, timeout, admin-debug posting, and original-upload cleanup. Task C Slice 8 adopted generic audit without redesigning this workflow and smoke testing confirmed the behavior-preserving audit contract.
- Suggested Fix: In a later inventory-only orchestration slice, audit inventory import view callbacks for service-extraction opportunities. Move only stable lifecycle transitions, admin-debug/reference updates, material-continuation coordination, and original-upload cleanup orchestration behind service helpers with focused interaction tests, preserving `/inventory import`, upload-first, correction, materials, admin debug, audit metadata, and user-facing behavior.
- Impact: medium
- Risk: medium
- Dependencies: Task C Slice 8 inventory generic audit adoption delivered and smoke tested on 2026-06-30; existing inventory route/view/service/DAL tests; no command UX or SQL schema changes without a separate approved slice.
- Status: later refactor
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: SQL repo `dbo.IMPORT_STAGING_PROC_CORE`, `dbo.IMPORT_STAGING_CSV_RAW`, `dbo.IMPORT_STAGING_CSV`, and `dbo.IMPORT_STAGING`
- Type: refactor
- Description: `dbo.IMPORT_STAGING_PROC` is now a narrow public wrapper that claims the immutable file and delegates to `dbo.IMPORT_STAGING_PROC_CORE`. The remaining mixed responsibilities live in the core procedure: digest-bound raw-file loading, raw-to-typed conversion, canonical staging mapping, cleanup/delta work, scan allocation, and committed receipt handoff. The earlier description that assigned all of this ownership to the public wrapper is no longer accurate.
- Suggested Fix: Audit the current `dbo.IMPORT_STAGING_PROC_CORE` phase boundaries after the KingdomScanData4 Phase 5/5.2 stabilisation work. Extract only proven stable internal phases or add clearly bounded internal sections and audit markers while preserving the public wrapper signature, claim/digest checks, database mutex, transaction ownership, staging tables, scan allocation, receipt/archive contract, return shape, and rollback posture. Keep data-contract changes out of the refactor unless separately approved.
- Impact: high
- Risk: high
- Dependencies: KingdomScanData4 Phase 5 immutable handoff and Phase 5.2 stabilisation/cleanup complete; durable import audit available; current wrapper/core SQL source and production smoke baseline; separate SQL task pack and owner approval before decomposition.
- Status: operator-gated
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: SQL repo `dbo.UPDATE_ALL2`, SQL repo `dbo.SUMMARY_PROC`, and downstream stats/dashboard rebuild procedures
- Type: performance
- Description: Task C Slice 13 refreshed the authoritative SQL map and reviewed nine completed post-August fallback batches (IDs 306–345). Every batch recorded 13 completed `update_all2_*` rows. `update_all2_summary_proc` dominated 9/9 batches at 62.1–75.8 seconds and averaged 93.8% of measured subphase time, while the coarse phase still exceeded emitted subphases by 35.9–62.2 seconds. This confirms the outer audit target but does not identify which `SUMMARY_PROC` helper or shared-state responsibility is expensive.
- Suggested Fix: Collect naturally occurring evidence for 10–14 days and at least 30 completed fallback batches, then run Task C Slice 14 as a read-only `SUMMARY_PROC` responsibility/performance audit. Use existing Query Store/DMV evidence only where helper attribution is reliable. If attribution remains inconclusive, prepare a separate non-invasive instrumentation proposal; do not tune or decompose from the outer duration alone.
- Impact: high
- Risk: high
- Dependencies: Task C Slice 13 complete; KingdomScanData4 Phase 5/5.2 and August follow-up migrations complete; at least 10 days and 30 completed fallback batches for the formal audit; SQL owner approval before state-changing instrumentation, plan experiments that execute stateful work, procedure design, tuning, or migration work.
- Status: promoted task pack — evidence collection active; target audit 2026-09-15
- Last verified: 2026-09-01
- Promoted task pack: `docs/task_packs/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 14 SUMMARY_PROC Responsibility and Performance Audit.md`

### Deferred Optimisation
- Area: MINI_AMD SQL Agent transaction-log backup job schedules and SQL backup-policy documentation
- Type: consistency
- Description: The KingdomScanData4 Phase 5.2 cleanup found that the production transaction-log backup job has both 15-minute and 5-minute schedules enabled. The current backup chain was healthy at cleanup, but the intended steady-state cadence and whether both schedules are deliberate have not been confirmed. Overlapping schedules are not automatically a defect, but leaving the policy ambiguous creates avoidable operational and recovery uncertainty.
- Suggested Fix: Inventory the job and schedule IDs, enabled state, ownership, next-run times, and 7-14 days of execution history. Record average, p95, and maximum job duration plus overlaps, skips, failures, log growth, backup size, recovery-point objective, and off-machine copy cadence. Approve one documented policy, then disable only a confirmed redundant schedule through a separate operator change. Verify the log chain and backup health after the change and document the exact rollback.
- Impact: high
- Risk: medium
- Dependencies: Operator backup-policy decision; current SQL Agent and `msdb` evidence; confirmed healthy Production full/differential/log chain; no schedule mutation in the documentation-only reconciliation task.
- Status: operator policy decision required
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: `stats_module.py`, import service modules, import DAL modules
- Type: refactor
- Description: Task C Slice 1 extracted fallback import file orchestration and DAL helpers, and Task C Slice 12 added UPDATE_ALL2 audit-output projection, but `stats_module.py` remains the compatibility entry point for the current worker/route/command flow and still owns mixed sequencing around Excel processing, secondary archive, SQL execution, audit phase projection, and result aggregation. The safe extraction boundary must be rechecked against the August KingdomScanData4 import changes.
- Suggested Fix: After the Slice 14 `SUMMARY_PROC` responsibility audit settles whether any additional instrumentation must pass through the fallback orchestration boundary, continue extracting residual orchestration from `stats_module.py` into import-specific services. Keep `stats_module.py` as a thin compatibility shim until each route or command caller is explicitly migrated, and preserve current result, audit, archive, retry, failure, and user-message contracts in every slice.
- Impact: medium
- Risk: medium
- Dependencies: Task C Slice 1 wrappers complete; durable audit foundation and Slice 12 projection deployed; KingdomScanData4 Phase 5/5.2 stabilised; Task C Slice 13 complete; avoid overlapping any Slice 14 instrumentation decision.
- Status: later refactor — sequence after Task C Slice 14 audit decision
- Last verified: 2026-09-01

### Deferred Optimisation
- Area: `commands/stats_cmds.py`, `commands/telemetry_cmds.py`, `commands/prekvk_cmds.py`, `scripts/validate_command_registration.py`, `docs/reference/canonical_command_reference.md`
- Type: cleanup
- Description: Phase 7 converted `/mykvkstats`, `/mykvktargets`, `/mykvkhistory`, `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` into tested deprecated redirect/help responses. The old command paths remain registered temporarily so players receive migration guidance, which means the command baseline, redirect helpers/tests, and compatibility docs still carry legacy surface area after the first deprecation rollout.
- Suggested Fix: After the agreed no-feedback window and operator approval, remove the deprecated command registrations and redirect-only tests, update `scripts/validate_command_registration.py::APPROVED_TOP_LEVEL_COMMANDS`, update `docs/reference/canonical_command_reference.md` and player/operator docs, and run command inventory, registration, focused KVK command tests, pre-commit, and full pytest before merge.
- Impact: medium
- Risk: medium
- Dependencies: Phase 7 redirect PR merged and deployed; player briefing posted; no actionable player feedback during the monitoring window; operator approval for final removal.
- Status: operator-gated
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: `tests/test_ark_preference_service.py`, `tests/test_ark_bans_enforcement.py`, `tests/test_lock_timeout.py`, `tests/test_calendar_service.py`, `tests/test_calendar_pipeline.py`, remaining slow full-suite pytest paths
- Type: performance
- Description: The July duration audit and its named slow-test timings are no longer a current prioritisation baseline. Since then the suite has expanded materially; the latest known full regression result records `2999 passed, 2 skipped`, but that total-suite result does not include a fresh `--durations` profile. The former 1450-test baseline and listed timings must therefore be treated as historical evidence until reproduced on current `main`.
- Suggested Fix: Run a fresh current-branch duration audit with `pytest -vv tests --durations=30 --durations-min=1.0` and save the artifact. Classify each current outlier as intentional timeout coverage, missing test boundary, live dependency leakage, retry/backoff, or genuine defect. Preserve real lock/subprocess/negative-path coverage, but replace unnecessary multi-second waits with patched constants, fake clocks, controlled retry policies, or explicit service/DAL boundary fakes where safe. Re-run focused subsystem tests, log-noise analysis, and the full suite after any optimisation.
- Impact: medium
- Risk: medium
- Dependencies: Use current `main` after documentation reconciliation; capture a new durations artifact rather than reusing `.codex_pytest_audit-new.log`; preserve genuine timeout, subprocess, lock, negative-path, and log-noise coverage.
- Status: re-audit required
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: `commands/ark_cmds.py`, `ark/registration_flow.py`, `ark/confirmation_flow.py`, `ark/reminders.py`, `ark/dal/ark_dal.py`
- Type: refactor
- Description: The Ark create, amend, and cancel command handlers still contain substantial workflow orchestration, including config parsing, match validation, registration embed edits, JSON state lookup, reminder rescheduling/cancellation, audit logging, and cancel-DM dispatch coordination. Phase 4 intentionally preserved these bodies while moving command paths under `/ark` to avoid mixing command-surface migration with service extraction.
- Suggested Fix: Scope a follow-up Ark command orchestration extraction that moves create/amend/cancel workflow coordination into Ark services while leaving command handlers responsible for permissions, deferral, input collection, and response rendering. Preserve existing DAL contracts, restart-sensitive message/reminder state behavior, and modal/view callback behavior with focused regression tests.
- Impact: medium
- Risk: medium
- Dependencies: Phase 4 Ark command grouping is complete and smoke tested; validate service boundaries against existing Ark registration, confirmation, reminder, cancel, and audit tests.
- Status: later refactor
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: remaining redirect-only account/reminder/KVK compatibility paths, `/mykvkcrystaltech`, command governance, and migration communications
- Type: cleanup
- Description: Completed Phases 5F, 5G, 6, and 8 removed their explicitly approved Inventory, export, `/my_stats`, and `/player_profile` routes. Phase 8 also established `/stats player` as the one canonical leadership player-review location, while `/me history` remains closed and `/kvk history` canonical. Those decisions are no longer part of this generic deferred item. Remaining redirected account/reminder/KVK paths and `/mykvkcrystaltech` still require route-specific usage, feedback, caller, and replacement evidence.
- Suggested Fix: Open a fresh Phase 10 qualified-usage and no-feedback review. Change one remaining route at a time only after explicit operator approval, communication, command-governance updates, resync, smoke, and rollback. Do not reopen the accepted `/stats player`/`/player_profile` decision, the completed Phase 8.1 no-command-change boundary, or canonical `/kvk history` placement through this generic item.
- Impact: medium
- Risk: medium
- Dependencies: Phase 8 and Phase 8.1 operator accepted and archived; Phase 9 has its own proposed task pack; fresh route usage/caller/feedback evidence; explicit operator approval for each retirement.
- Status: evidence and operator-gated
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: SQL repo `dbo.InventoryReportPreference`, `inventory/dal/inventory_reporting_dal.py`, `inventory/reporting_service.py`, and retired Inventory-visibility documentation/tests
- Type: cleanup
- Description: Phase 5F removed the final approved player-facing need for Inventory report visibility by retiring `/myinventory`, `/inventory_preferences`, public Inventory posting, and the Personal Settings Privacy & Sharing control. The application no longer reads or writes the preference, but the SQL table and existing rows were intentionally retained as rollback evidence. Dropping the table in the bot cleanup would have created an unnecessary irreversible SQL dependency outside the no-SQL-deployment Phase 5F boundary.
- Suggested Fix: After Phase 5F is deployed, command cache resynced, and the simplified private-only Inventory journey has completed an agreed observation period, run a SQL dependency and manual-consumer audit. If no external report, procedure, job, script, or rollback need remains, prepare a separate SQL task pack and migration to retire `dbo.InventoryReportPreference`, with production backup/evidence, deployment ordering, rollback, schema export, and bot compatibility checks. Otherwise document why the dormant table is retained.
- Impact: low
- Risk: medium
- Dependencies: Phase 5F operator smoke accepted on 2026-07-16; confirmed zero runtime reads/writes; an agreed post-release observation window; fresh SQL repository and production dependency checks; explicit destructive SQL approval.
- Status: destructive SQL audit-gated
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: `player_self_service/governor_dashboard_dal.py`, SQL repo `dbo.KingdomScanData4` dashboard-read indexes, optional dashboard read view
- Type: performance
- Description: Phase 3 reads one latest `KingdomScanData4` row per selected governor and joins primary-key lookup tables. The bot-side predicate was corrected to convert the parameter rather than wrap `GovernorID` in `TRY_CONVERT`. The earlier approximate table cardinality and index context predate the July/August KingdomScanData4 modernisation programme, so they are no longer a reliable basis for proposing a view, covering index, or maintained snapshot table.
- Suggested Fix: Recollect the current table cardinality, index definitions/usage, statistics state, and exact dashboard query shape. Then run representative early/middle/recent Governor IDs with actual plans and `SET STATISTICS IO, TIME ON`, including warm/cold reads and expected dashboard concurrency. Introduce a canonical view only for proven contract reuse, add the narrowest includes only when key-lookup cost is evidenced, and consider maintained state only when measured demand justifies explicit refresh, staleness, failure, deployment, and rollback contracts.
- Impact: medium
- Risk: medium
- Dependencies: Current post-KingdomScanData4-Phase-5 SQL schema and production statistics; representative Governor IDs; observed dashboard usage/concurrency; SQL owner-approved plan collection window; separate SQL review for any object change.
- Status: evidence required — rebaseline
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: SQL repo `dbo.usp_GetPersonalStatsDaily`, `dbo.KingdomScanData4`, Alliance Activity/Fort sources, and `stats/dal/personal_stats_dal.py`
- Type: performance
- Description: Phase 6 deployed one bounded set-based `dbo.usp_GetPersonalStatsDaily` contract for up to 26 deduplicated governors and 180 Stats-anchor days, with source-refresh provenance and bot-side timeouts, bounded concurrency, caching, and inflight deduplication. Functional smoke passed, but the earlier index/cardinality assumptions predate subsequent KingdomScanData4 migrations and no current actual-plan, logical-read, duration, memory-grant, or concurrent 26-account baseline proves that a new covering index is warranted.
- Suggested Fix: Reconfirm the current procedure and index definitions, then execute single-, multi-, and 26-account sets at 90/180 days with actual plans plus `SET STATISTICS IO, TIME ON`, cold/warm cache, and expected concurrency. Isolate the header freshness aggregate from daily payload cost. Add only the narrowest procedure refinement or supporting index demonstrated by the current hotspot, and retain independent correctness, performance, migration, and rollback evidence.
- Impact: high
- Risk: medium
- Dependencies: Phase 6 functional contract deployed; current post-August SQL schema/statistics; representative linked Governor IDs; SQL owner-approved measurement window; separate SQL Changes review for any index/procedure follow-up.
- Status: evidence required — rebaseline
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: `leadership_player_review` DAL/service/cache/render path and SQL leadership procedures
- Type: performance
- Description: Phase 8.1 was completed and operator accepted on 2026-07-23. It delivered stage-level diagnostics, a sequential cold/warm application harness, and a read-only SQL evidence harness without introducing a speculative table or index. The implementation pack is closed; the remaining item is evidence-only because no representative production actual plan, logical-read, CPU/elapsed, memory-grant, result-size, statistics-quality, or operational-wait record has yet justified a new SQL object.
- Suggested Fix: Run the delivered harness for recent/long-tenure, sparse/dense, one/three-KVK, and high-history governors in an approved production-safe window. Save actual plans and per-statement IO/time; compare estimated versus actual rows, spills, scans/lookups, residual predicates, memory grants, statistics sampling/age, and index usage/operational counters. Correct query/cardinality defects first, then assess consolidation or the narrowest supporting index against the full existing-index set and source write workload.
- Impact: high
- Risk: medium
- Dependencies: Phase 8.1 implementation deployed and archived; representative Governor IDs; SQL owner-approved plan collection window; no live load test without explicit approval; separate design approval, SQL PR, Changes review, and SQL-first deployment for any follow-up object.
- Status: evidence required
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: `player_self_service/governor_dashboard_models.py`, `player_self_service/governor_dashboard_dal.py`, `player_self_service/governor_dashboard_renderer.py`, SQL repo `dbo.KingdomScanData4`
- Type: consistency
- Description: Phase 4 operator smoke approved a visible `Last Login: TBC` placeholder on the governor card, but the current renderer-independent payload and authoritative SQL contract do not yet expose a last-login value. Guessing or deriving it in the renderer would violate the payload/DAL boundary.
- Suggested Fix: After the authoritative Last Login column and semantics are added to the SQL repo, validate its type, nullability, timezone, and freshness meaning; then extend the dashboard DAL row, payload model/service mapping, fallback embed, renderer, and complete/missing-value tests in one separately approved SQL-facing slice. Replace `TBC` only after deployment ordering and rollback are documented.
- Impact: medium
- Risk: medium
- Dependencies: Operator approval of the Phase 4 placeholder; authoritative `KingdomScanData4` SQL migration and source-population contract; `k98-sql-validation` before implementation.
- Status: blocked by source contract
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: broad cross-page renderer/view framework beyond Phase 7's narrow `/me` visual contract
- Type: architecture
- Description: Phase 7 completed the retained `/me` visual/content consistency pass and extracted only bounded, proven common primitives into `core/visual_contract.py`. Phase 8 and the completed Phase 8.1 refinement retain a separate leadership-specific renderer/payload/view contract. Dashboard, Inventory, summary payloads, selectors, data ownership, dimensions, and page-specific renderers remain deliberately independent. The delivered evidence still does not prove that one universal renderer/grid/payload/view framework would be safer.
- Suggested Fix: Observe the accepted Phase 8.1 renderer and the proposed Phase 9 leadership renderer after delivery. Reconsider a broader framework only with quantified identical duplication across at least two accepted consumers, a migration matrix, visual/fallback parity tests, Discord component-limit proof, lifecycle/timeout evidence, and a separately approved task pack. Do not consolidate self-view and leadership selectors or introduce a universal grid through Phase 9.
- Impact: low
- Risk: medium
- Dependencies: Accepted Phase 7/8/8.1 boundaries; proposed Phase 9 delivery evidence when available; no broad framework without quantified duplication and explicit approval.
- Status: watchlist
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: `services/stats_export_service.py`, `stats/dal/stats_export_dal.py`, `stats_exporter.py`, `stats_exporter_csv.py`, `player_self_service/accounts_export.py`, Inventory exports, SQL export views/tables, export docs/tests
- Type: architecture
- Description: Completed Phase 5G delivers the narrow all-linked Account Data output contract: Account-Summary-first full workbook, current snapshot CSV, raw Stats history CSV, exact windows/counts/Forts/safety/freshness, and truthful `.xlsx` Sheets compatibility. The three selected-governor Inventory report-page exports remain unchanged. Broader cross-domain export redesign is still not approved.
- Suggested Fix: Treat future changes spanning Inventory, KVK history, rankings, registry, leadership outputs, live Sheets creation, or new SQL views as a separate evidence-led export-output programme. Do not reopen Phase 5G or use Phase 6 interactive Stats as an export redesign vehicle.
- Impact: high
- Risk: high
- Dependencies: Phase 5G operator accepted after output-shape and Discord smoke on 2026-07-17; operator approval for any future cross-domain programme.
- Status: watchlist
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: `commands/calendar_cmds.py`, `commands/events_cmds.py`, `ui/views/calendar.py`, `ui/views/events_views.py`, public calendar/KVK calendar docs/tests
- Type: architecture
- Description: Generic public calendar and KVK calendar commands have inconsistent naming, visibility, scope, and interaction behavior. `/calendar` is an ephemeral calendar overview; `/calendar_next_event` is ephemeral and shows one next calendar event; `/next_kvk_fight` is public and shows one fight with controls for the next three fights; `/next_kvk_event` is public and shows one event with controls for the next five events. There is also no clearly named `/kvk_calendar` or equivalent KVK calendar overview, so grouping these commands now would tidy paths without resolving the user-facing model.
- Suggested Fix: Scope a dedicated public calendar/KVK calendar UX redesign outside the command-count programme. Review whether the end state should use grouped paths such as `/calendar overview`, `/calendar kvk_overview`, `/calendar next_event`, `/calendar next_kvk_fight`, and `/calendar next_kvk_event`; decide whether all public information commands should post publicly; define the missing KVK calendar overview behavior; align button counts and visibility; update docs/smoke references; and add focused command/view tests before implementation.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5A admin/leadership/operator grouping is complete; requires operator approval for public visibility changes and a fresh task pack. Phase 5A moved calendar admin/operator commands under existing `/ops calendar_*` paths so the flat public `/calendar` command remains untouched until this redesign.
- Status: proposed design programme
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: SQL repo `dbo.PreKvk_Phases` and compatibility-only PreKvK phase objects
- Type: cleanup
- Description: The legacy `dbo.PreKvk_Phases` table and any compatibility-only phase objects may remain after the active scan-window logic moved behind newer compatibility wrappers. Their exact current Production presence, dependencies, manual/report consumers, and rollback value have not been freshly verified, so destructive retirement is not yet justified.
- Suggested Fix: Run a current SQL-repository and live-Production object/dependency audit, including stored modules, jobs, reports, exports, manual scripts, permissions, extended properties, and rollback references. If all consumers are absent after an agreed observation period, prepare a SQL-repo-only retirement migration with backup, pre/post validation, schema export, and an explicit forward-fix or rollback decision.
- Impact: low
- Risk: medium
- Dependencies: Current Production object inventory and dependency evidence; at least one completed production cycle after the compatibility-wrapper deployment; production owner approval for destructive SQL cleanup.
- Status: SQL object revalidation required
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: `bot_helpers.py`, `utils.py`, `core/queue_lifecycle.py`, `upload_routes/fallback_queue_route.py`, queue runtime state
- Type: architecture
- Description: Phase 6K is intentionally limited to live queue persistence hardening. A fuller queue-domain redesign remains separate, including clearer ownership for queued message/job lifecycle, worker status transitions, display state, processing state, retry/drop semantics, and the boundary between fallback upload routing, `channel_queues`, and live queue UI state.
- Suggested Fix: Scope a dedicated queue-domain redesign audit as a new deferred optimisation batch. Map queue state sources, worker lifecycle, status transitions, user-visible embed updates, failure modes, and restart behavior before proposing any code movement. Keep upload-route behavior unchanged unless a later approved task explicitly includes it.
- Impact: medium
- Risk: medium
- Dependencies: Phase 6K live queue persistence hardening and Phase 6L lifecycle closure are complete; coordinate as a separate post-Phase 6 programme.
- Status: watchlist
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: queue persistence model, SQL repo `C:\K98-bot-SQL-Server`
- Type: architecture
- Description: Live queue persistence remains file-backed through `QUEUE_CACHE_FILE` after Phase 6K hardened the file-backed model. SQL-backed queue persistence may eventually provide a stronger source of truth for queued work, in-flight state, and recovery after crashes, but it requires a separate schema and contract design rather than being folded into Phase 6.
- Suggested Fix: If the hardened file-backed queue state proves insufficient in production, scope a SQL-backed queue persistence design task. Validate table/procedure/index needs against `C:\K98-bot-SQL-Server`, define migration and rollback plans, preserve existing operator behavior, and add restart/recovery tests before any implementation.
- Impact: medium
- Risk: high
- Dependencies: Requires explicit approval, `k98-sql-validation`, SQL repo changes, and production migration planning.
- Status: conditional watchlist
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: `decoraters.py`, `commands/admin_cmds.py`, `/ops usage`, `/ops usage_detail`, leadership-role configuration and permission tests
- Type: security
- Description: The Phase 5C Codex Security repository scan validated that the shared `is_admin_or_leadership` path treats an exact configured leadership role name as an independent authorization grant when no configured stable role ID matches. Both private SQL-backed usage commands inherit that decision. Accepted Phase 8 did not reuse this broad gate for `/stats player`; it delivered a dedicated stable-role-ID and Leadership/Notify channel matrix. The generic decorator and other commands remain a separate low/P3 hardening item.
- Suggested Fix: In a separate permission-hardening slice, decide whether role-name compatibility must remain. Prefer configured stable role IDs as authority; if names are retained for migration, make them warning-only or require a matching approved ID. Add regression coverage for unmatched ID plus matching name, allowed/disallowed channels, Discord administrator and fixed admin paths, both usage commands, and existing leadership workflows before deployment.
- Impact: medium
- Risk: medium
- Dependencies: Phase 8 dedicated authorization is deployed and operator accepted, but generic decorator consumers still need their own compatibility audit. Preserve intended admin/leadership access outside `/stats player`; run focused permission/telemetry tests, command registration, full pytest, and operator smoke before changing the shared decorator.
- Status: policy-gated
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: `DL_bot.py` fast-path attachment handlers, `upload_routes/`, `file_utils.py`, import worker admission and operational telemetry
- Type: security
- Description: The Phase 5C Codex Security repository scan validated that eight attachment fast paths can hand overlapping work directly to workbook parsing, worker subprocesses, audit writes, and SQL-backed imports without one shared in-flight bound, cooldown, or backpressure control. A bounded local harness observed two concurrent real-route importer handoffs. Discord limits and unknown production channel ACLs reduce likelihood, but they do not cap bot-side in-flight work; final severity is low/P3.
- Suggested Fix: Scope a dedicated upload-admission slice. Measure normal import duration and host/SQL headroom, then place every fast path behind a small shared semaphore or bounded queue with explicit busy/backpressure messaging, per-channel or import-key deduplication where safe, cancellation/timeout cleanup, and metrics for active, queued, rejected, and timed-out work. Preserve importer semantics and validate concurrency limits with deterministic two/many-task tests before live smoke.
- Impact: medium
- Risk: high
- Dependencies: Production upload-channel ACL review; measured host/process/SQL capacity and acceptable queue depth; coordinate with the existing queue-domain deferred item without broad redesign; no live load test without explicit operator approval.
- Status: evidence and design-gated
- Last verified: 2026-08-29

### Deferred Optimisation
- Area: `stats_module.py::_offload_callable_py` and its current callers
- Type: consistency
- Description: The coordinated Stats runtime now uses a single cancellation-draining worker under writer admission. The legacy branch of `_offload_callable_py` still catches a post-entry run_step exception, then tries run_blocking_in_thread and asyncio.to_thread; that branch can execute the callable up to three times. Audit actual caller reachability and side effects rather than labelling the protected P0 path unfixed.
- Suggested Fix: Scope a separate once-only audit for every `_offload_callable_py` caller. Reproduce the highest-risk real call shape deterministically, establish which executor contracts preserve its arguments/results/exceptions, then remove post-entry fallback and add cancellation/timeout coverage without changing SQL or cache behavior.
- Impact: medium
- Risk: medium
- Dependencies: Separate operator-approved task; complete caller/side-effect inventory; preserve Stats result normalization, SQL failure handling, cache behavior, and existing telemetry.
- Status: WS2 residual legacy-path audit; protected path partially delivered
- Last verified: 2026-10-24

### Deferred Optimisation
- Area: `ui/views/kvk_history_view.py::_offload_callable` and KVK History payload/export callers
- Type: consistency
- Description: Static review proves that `_offload_callable` catches an ordinary exception from `run_blocking_in_thread` and then invokes the same callable again through `asyncio.to_thread`. This has the same unsafe post-entry fallback shape as the corrected `DL_bot.py` helper, but the KVK History callers' read, rendering, export, timeout, and user-visible failure contracts have not been independently reproduced or calibrated.
- Suggested Fix: Scope a separate KVK History offload audit. Inventory each payload/export call shape, reproduce one post-entry failure with an invocation counter, then adopt a once-only executor-selection contract while preserving result extraction, interaction behavior, and existing error presentation.
- Impact: medium
- Risk: medium
- Dependencies: Separate operator-approved task; focused KVK History offload, payload, export, timeout, and interaction tests.
- Status: evidence required
- Last verified: 2026-08-31

### Deferred Optimisation
- Area: `singleton_lock.py::acquire_singleton_lock`, `release_singleton_lock`, and `DL_bot.py` process ownership
- Type: consistency
- Description: Phase 2F audit confirmed the singleton helper checks existing process metadata before writing a lock file; it does not exclusively acquire ownership. Simultaneous starts can both pass, and release unlinks without checking the owning PID. This is a process-lifecycle reliability observation, not a claim of an established production overlap or exploitable vulnerability.
- Suggested Fix: Separately design exclusive process acquisition and owner-checked release, including stale-process/error handling and watchdog restart compatibility. Do not treat unique JSON temporary names as protection against cross-process last-writer-wins snapshots.
- Impact: medium
- Risk: medium
- Dependencies: Separate operator-approved startup/shutdown task; deterministic simultaneous-start, ownership, stale-lock, process-check failure, and restart tests. No change in Phase 2F.
- Status: separate reliability follow-up after Phase 2G unless its audit proves a hard dependency; owner Chris Watts; separate implementation approval required
- Last verified: 2026-09-07

### Deferred Optimisation
- Area: `event_scheduler.py::schedule_event_reminders`, `send_reminder_at`, `expire_single_reminder`, `safe_delete_reminder`, and `bot_instance.py` teardown
- Type: architecture
- Description: Public send and expiry children use direct `asyncio.create_task`, outside individual TaskMonitor/DM registry supervision. Discord awaits also allow deletion, publication, and expiry workflows to overlap before synchronous tracker saves. Atomic replacement protects the file but does not make these workflows transactional or drain all public children during graceful teardown.
- Suggested Fix: Scope public-task ownership and cancellation separately, with deterministic send/delete/expiry interleavings and restart evidence before selecting any identity or scheduling change. Preserve current behavior until that design is approved.
- Impact: medium
- Risk: medium
- Dependencies: Separate operator-approved lifecycle task; exact message identity, mentions, cancellation, timing, shutdown and restart tests. No DM redesign, Phase 2G reservation, or Stats/KVK History executor work in Phase 2F.
- Status: separate reliability follow-up after Phase 2G unless its audit proves a hard dependency; owner Chris Watts; separate implementation approval required
- Last verified: 2026-09-07

### Deferred Optimisation
- Area: `ark/state/ark_state.py`, `ark/confirmation_flow.py`, and persisted `confirmation_updates`
- Type: architecture
- Description: Phase 2B proves that persisted confirmation update history is not render-bounded and can grow to high cardinality. Phase 2B safely packs or explicitly marks omitted render units, but changing retention or storage would alter restart-sensitive state and historical visibility.
- Suggested Fix: Gather production cardinality and operator-use evidence, define retention/archive and historical-visibility semantics, then decide whether updates remain in the current JSON shape or need a separately approved durable SQL contract. Include migration, restart compatibility, failure recovery, and rollback before changing persistence.
- Impact: medium
- Risk: medium
- Dependencies: Production state evidence; operator decision on historical visibility; `k98-sql-validation` and a separate SQL PR only if durable SQL storage is selected.
- Status: operator-approved defer in Phase 2E; keep-all behavior retained because the measured local copy was test-generated and no current production cardinality or historical-visibility evidence justifies mutation
- Last verified: 2026-09-03

### Deferred Optimisation
- Area: `ark/dal/ark_dal.py::replace_match_draft_rows`, `ark/ark_draft_service.py`, and `ark/team_builder_service.py`
- Type: architecture
- Description: Draft replacement uses separate delete and insert statements through the non-strict `execute_async` helper, then reports success even when a write helper returns its failure sentinel. A database write failure can therefore leave partial or absent draft state while the existing builder proceeds to its normal acknowledgement. The one-operator workflow makes simultaneous-builder races low likelihood, but it does not mitigate a database or connection failure.
- Suggested Fix: In a separately approved reliability slice, define one strict transactional draft-replacement contract that rolls back delete/insert together, returns or raises an unambiguous persistence result, and maps failure to an existing ephemeral builder error without changing permission, team, publish, or audit meaning. Add deterministic delete/insert failure, rollback, acknowledgement, and reopen-state tests.
- Impact: low
- Risk: medium
- Dependencies: Separate SQL/DAL transaction design and operator approval; authoritative `dbo.ArkMatchTeams` revalidation; focused service/view tests and a bot Changes-only security review. SQL review is required only if the SQL repository changes.
- Status: low-priority reliability debt; no production incident established
- Last verified: 2026-09-03


### Deferred Optimisation
- Area: `stats_alerts/interface.py` and `stats_alerts/db.py` executor fallback wrappers
- Type: consistency
- Description: Phase 2G source review found post-entry executor fallback in existing stats-alert read/orchestration helpers. A callable exception may cause another backend to invoke it again. Reservation transitions bypass these wrappers and use the existing once-only backend; other call shapes and side effects have not been independently reproduced.
- Suggested Fix: Separately inventory callers and prove argument, return, exception and cancellation semantics with invocation counters before removing fallback. Coordinate with existing Stats and KVK History audits without merging unrelated surfaces into Phase 2G.
- Impact: medium
- Risk: medium
- Dependencies: Separate operator-approved executor audit; preserve SQL/read behavior and telemetry; no SQL contract change approved.
- Status: evidence required; owner Chris Watts; not a Phase 2G dependency
- Last verified: 2026-09-08
## Phase 2H historical closure — 2026-09-08

Pre-KVK diagnostic delivery is accepted and moved to archive/deferred_optimisations_resolved.md.
Natural production calendar dispatch and Phase 2F's natural public-save observation remain pending
with Chris Watts. Existing lifecycle, executor, ProcConfig and other structured items remain open.

### Deferred Optimisation
- Area: stats_alerts/interface.py, stats_alerts/embeds/kvk.py, commands/admin_cmds.py
- Type: architecture
- Description: Production fighting check/send/claim has no durable reservation; swallowed renderer failures can report success without a send receipt. The former ops test entrypoint is removed by Phase 2J. Phase 2I preview intentionally does not alter these production semantics.
- Suggested Fix: Separately scope real fighting admission, all participating callers, cap/mutual exclusion, receipts and truthful public outcomes. Phase 2J command removal is delivered and smoke accepted. Phase 2K delivered truthful outcomes/receipts and passed operator smoke; durable admission/cap/mutual-exclusion changes remain a separately approved protocol extension.
- Impact: high
- Risk: high
- Dependencies: Explicit protocol approval; immutable baseline and production rollback evidence.

### Deferred Optimisation
- Area: `embed_offseason_stats.py`, `stats_alerts/embeds/offseason.py`
- Type: architecture
- Description: No isolated off-season/Kingdom Summary diagnostic exists. Legacy test rendering can claim live summary CSV keys despite ping suppression, and daily/weekly SQL reads remain synchronous in the async renderer. Phase 2J removes the ops entrypoint only.
- Suggested Fix: Scope a diagnostic only when needed; separate read/build/publication boundaries and prove isolation with existing helpers. Coordinate executor work with the existing Stats audit and preserve production defaults.
- Impact: medium
- Risk: medium
- Dependencies: Explicit diagnostic approval, authoritative SQL validation for any DAL change, independent production admission/outcome design and Changes review. No forced calendar or SQL data changes.

Phase 2J leaves existing production receipt/reservation, once-only executor, singleton/public-child,
generic-view timeout, DM/broad JSON and ProcConfig records separately scoped. Natural production
calendar admission and Phase 2F public-save observations remain pending.

## Phase 2J reconciliation — 2026-09-09

Completed Phase 2B/C/D and Phase 2I diagnostic items are moved to the resolved register; Phase 2J
command removal is accepted there. Phase 2E keep-all confirmation history is an approved defer,
not an unresolved rendering fix. ProcConfig, Stats and KVK History executors, stats-alert fallback,
singleton ownership and public-child supervision remain open. A duplicate stats-alert/offseason
entry was consolidated into the existing executor and isolated-offseason owners, not closed as fixed.

### Deferred Optimisation
- Area: `event_scheduler.py` DM sent/scheduled tracker writers and asynchronous offload wrappers; other JSON writers only after a separate inventory
- Type: consistency
- Description: The 24 October source review confirms the DM tracker I/O lock and asynchronous wrappers that select one helper and return without caught post-entry fallback. Phase 2F public-reminder atomic replacement and Phase 6K queue persistence are also delivered. Caller ordering, snapshot consistency, interruption and send-versus-disk uncertainty still require dedicated WS4 acceptance; a broad JSON audit has not been performed.
- Suggested Fix: Audit DM writer callers and invocation counts, ownership, failure/cancellation and restart contracts separately. Reuse existing atomic helpers; do not assume every JSON writer needs replacement or conflate atomic replacement with transactional workflow ownership.
- Impact: medium
- Risk: medium
- Dependencies: Separate scope and deterministic no-double-entry/restart tests; coordinate with executor and public-child work without expanding Phase 2K. No DM or broad JSON redesign approved.
- Status: WS4 partially delivered; ordering and uncertainty acceptance remains; owner Chris Watts
- Last verified: 2026-10-24

### Deferred Optimisation
- Area: production `stats_alerts/embeds/kvk.py`, off-season renderers and `mge/mge_content_renderer.py` final payload boundaries
- Type: consistency
- Description: The original payload audit classified these live contracts safe within existing bounds and deferred wider canonical adoption. Phase 2I validates isolated fighting preview publication, not every production send. No current production overflow is established; blanket canonical coverage must not be claimed.
- Suggested Fix: If evidence warrants a separate payload slice, measure real/pathological complete payloads and add canonical final validation at proven outbound boundaries while preserving appearance, mentions and route semantics. Keep MGE and off-season product changes independently approved.
- Impact: low
- Risk: medium
- Dependencies: Concrete current payload failure or measured convergence benefit; regression evidence and scoped Changes review. Not Phase 2K receipt/admission work.
- Status: optional convergence; no demonstrated incident; owner Chris Watts
- Last verified: 2026-09-09

### Deferred Optimisation
- Area: natural seasonal stats delivery and Phase 2F public reminder save evidence
- Type: consistency
- Description: Phase 2K smoke proves natural fighting receipt/claim and isolated Pre-KVK send/status/edit. Natural Pre-KVK and off-season routes and Phase 2F's next natural public-save path have not been independently observed.
- Suggested Fix: Retain matching destination/receipt and state evidence on the next naturally eligible run; Pre-KVK is about two months away. Keep the Phase 2F observation separate. Do not force dispatch, mutate calendars or reset state.
- Impact: low
- Risk: low
- Dependencies: Natural calendar opportunities and operator evidence; not blockers to accepted Phase 2K smoke and not Phase 2L implementation.
- Status: observation pending; owner Chris Watts

### Deferred Optimisation
- Area: independent ProcConfig admin/startup/pipeline invocations and offload ownership
- Type: architecture
- Description: Protected P0 paths now use shared writer admission, exact owner context and matching nested tokens, with fail-closed checks for incomplete protected activation. Reports alone remain non-authoritative. Independent admin/startup/pipeline compatibility entrypoints still require a complete coverage audit; no unprotected live overlap is established by this reconciliation.
- Suggested Fix: Map each entrypoint to existing authority and worker lifetime, then test overlap, lost acknowledgement and cancellation at uncovered boundaries. Reuse the delivered admission protocol and preserve committed receipts. Missing reports must not initiate replay or a new competing recovery protocol.
- Impact: medium
- Risk: high
- Dependencies: Separate source-of-truth SQL validation, scope and operator approval; outside WS1; preserve committed effects and existing dispatch policy.
- Status: WS6 partially delivered; entrypoint coverage audit required; owner Chris Watts
- Last verified: 2026-10-24

### Deferred Optimisation
- Area: `gsheet_module.py::_aggregate_windowed_dfs` and `create_additional_kvk_spreadsheets`
- Type: consistency
- Description: KVK Source Migration Phase 1 at bot `1a3a5de3` confirms generic numeric summation across windows includes `starting_power`, while player grouping includes `name` and camp attributes. Repeated starting power can be added across windows and a label change can split one governor's export grouping. This is a static legacy export observation, not evidence of a measured deployed incident.
- Suggested Fix: In a separately approved legacy export slice, define metric-specific aggregation and stable-ID grouping with an explicit label-selection policy; test two windows and a renamed governor using synthetic records. Coordinate with new-source period selection without changing legacy behavior in the Phase 1 audit.
- Impact: medium
- Risk: medium
- Dependencies: Operator-approved legacy export scope; current `gsheet_module.py` export and compatibility tests; source-period architecture decision for new-source adaptation.

### Deferred Optimisation
- Area: `scripts/install_s11_source_boundary.ps1` operational limit declarations
- Type: consistency
- Description: PR review identified repeated receipt, file-size and operation-time limits. They are currently explicit and regression-tested, but repeated literals could diverge during future maintenance. Three review comments describe this same optional refactor.
- Suggested Fix: Consolidate bounds into named reviewed constants in a separate installer-maintenance slice, preserving the current per-operation supervision and output limits; test the native helper extraction and public entry point together.
- Impact: low
- Risk: medium
- Dependencies: Existing native Windows installer regressions; no changed limits or fixed overall workload duration; outside the first production rollout.

### Deferred Optimisation
- Area: `services/export_contention.py::retry_coordination` structured outcome logging
- Type: consistency
- Description: Private PR616 identified three similar log payloads for recovered, exhausted and non-retryable coordination outcomes. Current behavior is tested; no schema drift or runtime defect was identified.
- Suggested Fix: During the next logging-focused change, consider a small shared outcome emitter while preserving severity, optional sanitized error facts, timing and exactly one summary per retry operation.
- Impact: low
- Risk: low
- Dependencies: Existing contention redaction and bounded-volume regressions; optional maintenance, not a blocker to the first contention slice.

### Deferred Optimisation
- Area: S11 release authoring around `scripts/prepare_k98_release.py` and `core/export_release_seed.py`
- Type: architecture
- Description: Automatic preparation and coordinated source/seed/start/readiness deployment are delivered and verified on 24 October through the fixed updater command. The old per-release manual assembly requirement is superseded. An existing archive directory needed a separately reviewed fresh-object custody repair; protected staging inherited NotContentIndexed and required a scoped metadata allowance. A subsequent stream gate needed SQL-only diagnosis before successful retry. These are remaining usability/diagnostic gaps, not permission to weaken protections or proof of an updater-created stream.
- Suggested Fix: Productize bounded inspect/review/repair/resume for supported existing-directory custody cases, retaining originals, exact inventories/hashes, handle protections and receipts. Improve errors with owner/ACL/attribute context and exact stream state. Design waiting/quiet-period coordination separately with bounded waits, no force closure, automatic claim release or age-based recovery. Keep the fixed operator command and authenticate installed tool capabilities.
- Impact: high
- Risk: medium
- Dependencies: Follow the Windows ownership and access contract; actual elevated PowerShell 5.1 inheritance/resume/handle tests and Changes review for runtime implementation. The one-time repair is not a general installed updater feature.
- Status: Automatic preparation/deployment delivered; residual directory-custody productization and stream diagnostics remain open; owner Chris Watts
- Last verified: 2026-10-24

### Deferred Optimisation
- Area: `commands/stats_cmds.py::kvk_source`, `ui/views/kvk_source_import_view.py`, source receipt/review services and DAL
- Type: architecture
- Description: During the 2026-10-12 deployed receipt smoke check, the operator could recover the last accepted import only because they had separately saved its receipt UUID. Private ephemeral responses are not a durable discovery surface, and requiring administrators to retain and manually enter UUIDs makes routine status/resume error-prone. The durable receipt survives but is difficult to find through Discord.
- Suggested Fix: Design an owner-scoped recent receipt/review browser reachable from the existing source command without a UUID. Provide a paginated select/search flow with recognizable season, original filename, input kind, scan time, state and creation time, plus explicit View status / Resume controls for the selected durable item. Preserve private responses, original owner/guild/channel restrictions, fresh authorization and version checks; keep raw UUID input as an advanced fallback. Reopening the browser after ephemeral dismissal or restart must rediscover durable records. Never silently select the latest receipt or replay an import. Review receipt/review distinctions and Discord option limits before implementation.
- Impact: high
- Risk: medium
- Dependencies: Separate operator-approved UX/implementation slice; authoritative SQL validation for discovery queries/indexes; bounded pagination and ownership/isolation tests; restart/expired-view tests; Changes security review. Capture only during deployed receipt verification; no runtime or production changes authorized by this entry.

### Deferred Optimisation
- Area: `ui/views/kvk_source_import_view.py::SourceUploadStartView` and `SourceUploadSeasonModal.callback`
- Type: consistency
- Description: On 2026-10-12, the September 3 workbook produced receipt d5302ad3-4a38-407b-8fa0-e6597e35d036, but the original season-review message still displayed active-looking Confirm/change season and Cancel upload review buttons. Current successful modal submission disables and stops the in-memory view without editing the original Discord message; cancellation likewise leaves the original controls visually unchanged. Opening the modal alone also leaves the initial buttons available. This invites repeated clicks and makes admins unsure which message owns pending work. Actual concurrent/repeated-click effects have not been tested in production and must not be inferred from appearance alone.
- Suggested Fix: Update the original season-review message after successful staging or cancellation to disable/remove its controls and show its terminal state, with a clear pointer to the retained receipt where appropriate. Define recoverable behavior when an opened modal is dismissed; do not strand intake by permanently disabling the only entry point on modal open. Review busy/completed handling, already-open modal submissions and receipt deduplication for repeated or concurrent actions. Cover success, cancellation, modal dismissal, timeout, partial multi-attachment staging, message-edit failure and duplicate/concurrent callbacks with automated tests. A cosmetic edit failure must not replay committed staging or acceptance.
- Impact: medium
- Risk: medium
- Dependencies: Separately scoped Discord UX fix and Changes review; preserve receipt-picker backlog entry, owner/access checks and accepted scans. Operator requested capture only during onboarding; no live failure injection or runtime changes.

### Deferred Optimisation
- Area: `ui/views/kvk_source_import_view.py::KvkSourceImportView.confirm_button` and original receipt message lifecycle
- Type: consistency
- Description: During September 3 KVK16 acceptance on 2026-10-12, the operator reported about a minute waiting for the confirmation response; the original validated receipt retained active-looking Confirm reviewed action and other controls. Receipt d5302ad3-4a38-407b-8fa0-e6597e35d036 subsequently confirmed accepted ScanID 9 with 5779 players. The handler defers, awaits service.confirm, then disables/stops the in-memory view without editing the original message. There is no immediate visible busy state on that receipt, inviting another click because the operator cannot tell whether the first was registered. This is not evidence of duplicate acceptance.
- Suggested Fix: Promptly acknowledge confirmation with a visible Processing state and disable conflicting actions on the original receipt while work is in progress, then visibly retire the old controls on completion. Preserve service/DAL ownership, version checks and durable idempotency; a UI busy flag alone is insufficient. Determine safe recovery using the saved receipt when a response or message edit fails or the result is uncertain; never automatically retry a mutation or re-enable stale approval. Cover slow confirmation, duplicate/concurrent confirm, cancel/prepare races, expiry during processing, message-edit failure and restart with automated tests. Keep production failure injection out of the onboarding walkthrough.
- Impact: medium
- Risk: medium
- Dependencies: Separately approved focused interaction UX work and Changes review; coordinate with the season-prompt lifecycle item and preserve the recent-receipt-picker entry. Capture only; no runtime changes.

### Deferred Optimisation
- Area: `ui/views/kvk_source_import_view.py::SourceConfigurationModal`, `kvk/services/new_source_admin_service.py::prepare_configuration`, `kvk/dal/new_source_admin_dal.py::onboard`, and Windows import/recovery integration
- Type: architecture
- Description: On 2026-10-12 KVK16 onboarding, baseline receipt ee46876c-b5bc-473b-b36b-6819fbbb6c87 version 4 prepared Pass 4 scans 12 to 18 while the operator reported differing imported window endpoints. Initial setup retypes the window label and endpoints even though KVK.KVK_Windows contains them. Confirmation writes a separate versioned SourceWindowConfig, without updating the imported table or upstream sheet. With source recovery enabled, a later successful configuration import can request different endpoints for an onboarded period matched by WindowName. The UI does not explain this precedence or reconcile the mismatch. The proposal remains unconfirmed; no fresh live Windows read or resulting override is claimed.
- Suggested Fix: Design a single operator workflow that selects an imported window, prefills its endpoints and resolves their accepted scan UTCs, and shows imported, proposed, desired and published values with provenance. On 2026-10-12 the operator explicitly requested selecting scan IDs once and deriving their already-confirmed UTC timestamps, with no duplicate timestamp entry. For scan-bounded coverage such as Pass 4 scans 12 to 18, derive and display coverage from those bindings for confirmation; provide a clearly distinguished explicit override only when a report genuinely covers a different interval. Retain explicit initial period identity and coverage approval because KVK.KVK_Windows lacks those fields. Detect conflicting sheet/imported/source settings and require a clear reconciliation choice before confirmation; define where intentional edits persist so a later import cannot unexpectedly reverse the operator's intent. Preserve versioning, frozen B0/map/weights, immutable accepted scans and exact matched-pair publication. Test initial onboarding, unchanged imports, conflicting imports, pending endpoints, stale review and approved retrospective endpoint changes. Do not invent period mappings or counterpart attestation.
- Impact: high
- Risk: medium
- Dependencies: Separate approved scope/design before implementation; validate Bot and authoritative SQL contracts plus importer source and enabled recovery behavior. Coordinate with captured onboarding UX items. Current walkthrough must reconcile the real Pass 4 source row before confirming this proposal; no production edits or runtime changes authorized by capture.

### Deferred Optimisation
- Area: `proc_config_import.py` KVK_DKPWeights import and `kvk/dal/new_source_admin_dal.py::onboard`
- Type: consistency
- Description: Blocking KVK16 onboarding defect observed 2026-10-12. Pass 4 configuration confirmation on baseline receipt ee46876c-b5bc-473b-b36b-6819fbbb6c87 version 5 rejected with "A new period must retain the season's approved map and weights." Operator SQL evidence shows approved SourceConfigVersion 1 / 50C398B0-2859-4FF5-A8C6-4A96B5C5875C weights 10/20/40 with EffectiveFromUTC 2026-10-11 14:02:35; latest imported weights remain 10/20/40 but EffectiveFromUTC is 2026-10-12 10:19:48. The importer uses delete_by_kvk and supplies only the season and three coefficients, so SQL's UTC default assigns a fresh effective timestamp. New-period onboarding compares that timestamp exactly with the frozen source weight configuration. This verified difference is sufficient to reject the proposal; it does not prove the absence of additional map differences. SQL evidence shows only baseline config version 1. Pass 4 source onboarding and first aggregate/publication/export remain incomplete.
- Suggested Fix: Scope an idempotent unchanged-weight import and safe new-period reuse of the season's approved weight identity. Distinguish import observation time from a genuine weight effective-time change. Handle already-existing timestamp drift without rewriting frozen configurations, weakening real coefficient/map-change checks, or silently approving historical recalculation. Review exact source decimal tokens as well as legacy float storage. Show the specific differing fields in preparation and failure responses so a proposal cannot look identical yet fail only at confirmation. Cover unchanged repeated import, initial baseline followed by new-period onboarding, existing drift, genuine coefficient/map changes, transaction rollback and stale confirmation with offline tests before separately approved deployment.
- Impact: high
- Risk: medium
- Dependencies: Blocker to the current walkthrough, not an optional post-export cleanup. Focused review/scope and operator approval before runtime changes; validate authoritative SQL defaults and persistence contracts and route Changes security review. Preserve accepted scans 1-18, baseline/configuration history, Pass 4 imported endpoints 12-18, aggregate file and all prior backlog entries. No direct production timestamp patch, re-baselining, repeated import or live failure injection as a workaround.
- Status: Operator approved the focused current-weight/window fix and configuration UX for local implementation and validation on 2026-10-12. Current coefficients supersede the earlier frozen-weight identity proposal above; import timestamps remain provenance. See [scope and behaviour](kvk_source_migration/current_weights_windows_20261012.md). Receipt UX items remain deferred. PRs, deployment and production changes are outside this approval; live walkthrough completion is not claimed.
# Publication transition test maintenance

### Deferred Optimisation
- Area: tests/test_*transition.py
- Type: consistency
- Description: Historical runtime-pin tests repeat explicit successor lists across several files; each reviewed protected transition needs the same list maintenance.
- Suggested Fix: In a separate test-only change, centralize exact transition-chain traversal while retaining historical endpoint and missing/foreign-member rejection checks.
- Impact: medium
- Risk: low
- Dependencies: Preserve the protected updater acceptance tests and immutable deployed transition hashes.


### Deferred Optimisation
- Area: rehydrate_views.py Ark restoration, ark/registration_messages.py retirement and tracked-view reporting
- Type: consistency
- Description: The 24 October startup registers handlers for retained historical Ark message IDs and reports them as attached even when Discord has no visible controls. The operator verified three closed/cancelled examples on 25 October. This is a lifecycle/reporting gap, not a demonstrated failed callback or permission bypass: the normal add_view path does not edit public messages or reopen registration.
- Suggested Fix: Reconcile tracker retirement with authoritative domain state and observed components; distinguish handler registration, eligible interactive restoration and historical/inactive retention in diagnostics. Preserve historical messages and identity/concurrency protections; do not infer eligibility solely from age. Review the compatibility edit fallback against the same lifecycle contract before changing behavior.
- Impact: medium
- Risk: medium
- Dependencies: Separate WS3/P1 lifecycle slice; domain-state/component validation, permissions and restart/concurrency tests, and Changes review for implementation. This entry authorizes no production mutation.
- Status: Captured; no runtime change; owner Chris Watts
- Last verified: 2026-10-25

## 26 October follow-ups linked to the closeout

### Deferred Optimisation
- Area: startup player-stats admission, services/export_contention.py, services/legacy_export_snapshot_dal.py, services/export_coordination_dal.py and recovery discovery in services/unowned_sql_hold_dal.py (R01)
- Type: architecture
- Description: Startup SP_Stats_for_Upload-path admission retained CoordinationLockRefused / SQL 51400 before producer entry; Report 44 separately recorded a recovery discovery refusal. Report 45 monitoring recovered. The requesting session and nearby activity do not establish the blocker, shared cause or a corrected contention defect. This is not process singleton locking.
- Suggested Fix: In N1/N2, map callers, resource/owner order and exact entry boundaries using retained timelines and static SQL definitions. Propose ordering or bounded handling only after deterministic causal evidence, retaining existing authority, budgets, no-reentry and unknown outcomes. No live probes or lock bypass.
- Impact: high
- Risk: high
- Dependencies: Next-phase architecture agreement; authoritative SQL repository; return demonstrated current pipeline/monitor correctness defects to F03/F05.
- Status: evidence review required; diagnostic attribution delivered, cause unresolved

### Deferred Optimisation
- Area: commands/admin_cmds.py::status_command and core/interaction_safety.py (R02)
- Type: consistency
- Description: On 26 October at 09:02:46 UTC the status command failed its original-response edit with HTTP 404 / Discord 10015 Unknown Webhook; a later request succeeded. This is separate from successful Location tests. Source still does synchronous connectivity work and an active provider health check before the edit; no causal attribution to either is established.
- Suggested Fix: In N4, trace defer/acknowledgement and response ownership, timing and helper behavior. Reuse private safe-response helpers and service/DAL ownership for blocking work where appropriate; add deterministic unavailable-response, permission/privacy and no-duplicate-probe tests. Preserve uncertainty rather than blindly retrying or publishing a private result publicly.
- Impact: medium
- Risk: medium
- Dependencies: R01 correlation only if evidence connects it; proposed N4 scope agreement. No token-expiry assumption and no claim the successful retry fixed the cause.
- Status: observed failure; root cause and implementation pending

### Deferred Optimisation
- Area: ExportResource ActivePreparationID lookup and recovery discovery (checkpoint lifecycle, 2026-10-27)
- Type: performance
- Description: The canonical schema lacks an ActivePreparationID index and successful discovery cycles can exceed 90 seconds. The checkpoint correction removes blocking observer waits and separates progress from completed-check freshness; query-plan performance has not been measured in production.
- Suggested Fix: Collect bounded wait/index observations and actual plan/row-count evidence before selecting a narrow index or discovery batching change. Keep uncertain outcomes and ownership checks intact.
- Impact: medium
- Risk: medium
- Dependencies: Production measurement; separate SQL contract and deployment review for any index change. See checkpoint-observation-lifecycle.md for the audited conflict map.

### Deferred Optimisation
- Area: `mge/mge_roster_service.py`, `mge/mge_simplified_leadership_service.py`, `mge/dal/mge_roster_dal.py`
- Type: architecture
- Description: The MGE lifecycle change gives both roster UIs whole-operation ownership per event before off-loop entry and rechecks insertion rank/capacity under SQL locks. A1a also identifies leadership preparation as a writer through automatic placement and shares its process thread owner with roster workers. Legacy roster add/audit and swap/reset paths still contain multiple database calls with their existing Boolean outcomes; process ownership does not make those writes atomic or establish cross-process settlement. The new strict signup transaction does not automatically upgrade these separate writers.
- Suggested Fix: In the remaining R12 writer census, map every roster writer and conflict order. Adopt one narrowly scoped atomic writer family at a time, grouping required audit and domain changes and distinguishing rollback from lost commit acknowledgement. Prove stale snapshots, competing writers, second-caller participation and unknown outcomes with native SQL qualification; preserve existing rank and publication policy.
- Impact: high
- Risk: high
- Dependencies: MGE lifecycle source and tests; authoritative SQL schema; explicit bounded writer scope and native qualification target; Changes-only review. A1b proposes exposing acknowledged steps, zero-row updates, audit failures and partial/unknown outcomes without claiming atomicity; see the A1b design packet. The cross-process/transaction redesign remains here. No production or policy change is authorized by this capture.

### Deferred Optimisation
- Area: `mge/dal/mge_signup_mutation_dal.py::SQL_RECEIPT` and `dbo.MGE_SignupAudit`
- Type: performance
- Description: Approved native qualification on 28 October chose a clustered scan for exact JSON operation-receipt lookup despite the existing EventId index. At 0/100/1,000 event audit rows, actual plans read 15/17/31 pages across 142/242/1,142 total rows. The atomic writer reduced connections/commits while adding checks and logical reads. These small warm-cache results establish a scaling question, not a production regression or index prescription.
- Suggested Fix: Measure representative event/total cardinalities and hit/miss distributions in a separately bounded synthetic target; compare existing plans with an explicit receipt-key/index design and retention constraints. Preserve exact operation identity, fingerprint checks and unknown-outcome handling. Select a schema change only from measured reads, write overhead and plan stability.
- Impact: medium
- Risk: medium
- Dependencies: R16 performance work; authoritative SQL contract and independent migration review; retained `docs/benchmarks/p1_mge_native_sql_20261028.json` evidence; approved fixture bounds. No schema or production operation authorized by this capture.

## 28 October MGE acceptance and remaining Batch A follow-ups

### Deferred Optimisation
- Area: ARK-A2-ADMIN-ADD; ui/views/ark_views.py slot selection and ark/registration_flow.py admin-add response
- Type: architecture
- Description: Operator evidence on 28 October confirms a player appeared in the roster while the private slot-selection interaction timed out. Supplied logs show an existing registration message edited successfully at 18:08:06.971, followed at 18:08:07.552 by Discord 404/10062 Unknown interaction from the final response.edit_message in the admin-add callback. The earlier identity_not_found entry and scheduler overlap do not establish the delay cause. Exact SQL commit/audit, callback-entry time and acknowledgement timing were not supplied. This is separate from the already accepted original Ark callback.
- Suggested Fix: In A2 map admin-add slot callback admission, response ownership, worker/SQL duration, roster mutation receipt and registration refresh. Establish early private acknowledgement and independent mutation/presentation outcomes only after domain and cancellation review. Test committed add with failed response/refresh, failed acknowledgement with non-entry, duplicate clicks, delayed IO and expiry. Reconcile the existing roster entry before any retry; do not replay the operation for measurement.
- Impact: high
- Risk: medium
- Dependencies: Sanitized operator screenshot/log evidence; Ark eligibility and permissions; authoritative SQL contracts; A1a lifecycle/adoption framework. A2 implementation requires its own bounded approval.
- Status: Captured for A2; no Ark runtime change or proven latency root cause.

### Deferred Optimisation
- Area: MGE-PERF; core/interaction_safety.py, ui/views/mge_simplified_leadership_view.py and mge/mge_embed_manager.py
- Type: performance
- Description: Earlier production rank selection measured ack 3.091s/total 6.410s and submission ack 0.974s/total 16.834s. A1a removed duplicate leadership preparation and deployed stage timing. The new 87c1b393 rank callback took 11.311s including sequential public/leadership refreshes of 4.809s/3.820s before replying. Single samples do not establish a speedup, p95 or global contention cause.
- Suggested Fix: Preserve accepted A1b qualified reads, truthful saved responses and refresh-coordinator delivery. Use the separate finalisation pack for historical board policy and A2 for remaining callers. Any further performance claim needs repeated stage measurements with materially different callers; do not replay accepted live operations for measurement.
- Impact: medium
- Risk: medium
- Dependencies: Accepted MGE closeout and remaining Batch A scope; receipt-query scaling and cross-process roster contracts stay separately scoped.
- Status: A1a/A1b exercised delivery and the updater correction are accepted in the [29 October deployed closeout](../task_packs/P1%20MGE%20A1b%20-%20Deployed%20Closeout%20-%202026-10-29.md). B1 qualified data, B2/B3 exact results, owned refresh/recovery and shared publication identity safeguards are delivered. Report63 supports response-before-refresh ordering, not production percentiles or a general speedup. Historical Windows validation and the unavailable Linux check remain in the [implementation record](../task_packs/P1%20MGE%20A1b%20-%20Implementation%20and%20Validation%20-%202026-10-28.md). Only the new finalisation follow-up retains separate publication/deployment gates; residual performance acceptance remains open.

### Deferred Optimisation
- Area: CFG-51421; proc_config_import.py and services/legacy_export_snapshot_service.py::begin_writer / legacy_export_snapshot_dal.py::session
- Type: architecture
- Description: Startup import on the deployed MGE runtime passed durable writer admission but session applock acquisition refused with SQL 51421 before yielding the guard. Report 61 verifies cancellation and exact reservation release. Blocking owner is unknown; earlier 51400 and provider-stream preflight are distinct observations.
- Suggested Fix: Extend the existing ProcConfig entrypoint/owner audit with this timeline; map lock order and actual blocking ownership. Reproduce startup overlap deterministically. Consider bounded waiting only with verified non-entry/cleanup, preserving cancellation, unknown outcomes and no write replay. Keep the operator continuation decision separate.
- Impact: medium
- Risk: high
- Dependencies: Existing ProcConfig caller census and authoritative SQL validation; separate reliability PR if warranted.
- Status: Original attempt resolved; continuation decision remains open in Report 62. A separate new startup configuration import reported success; it does not select or close the older continuation.

### Deferred Optimisation
- Area: CFG-OVERVIEW; services/recovery_runtime.py, services/recovery_report.py and configuration continuation reporting
- Type: consistency
- Description: Report 61 contains a resolved clear overview and one open configuration-continuation decision. Collection is nontransactional, so this is not yet proof of a persistent reporting defect. Historical startup failure correctly remains recorded after cancellation.
- Suggested Fix: Trace overview refresh and continuation creation ordering; reproduce with deterministic fixtures. Distinguish an active failure, recovered historical failure and pending operator choice. Explain collection timestamps and keep outstanding decisions visible without replaying imports.
- Impact: medium
- Risk: low
- Dependencies: Report 61 and configuration recovery lifecycle; separate from MGE performance and actual SQL blocker diagnosis.
- Status: Captured; evidence reconciliation pending


## A1a deployed observations carried into A1b handoff

### Deferred Optimisation
- Area: MGE-SELECTION-OBSERVATION; ui/views/mge_simplified_signup_form_view.py dropdown callbacks and telemetry batching
- Type: consistency
- Description: The 21:14 screenshot displays a priority while the first submit reports missing priority. The refusal precedes any mutation worker; priority usage flushes in a later telemetry batch after the successful creation log. Batched logs do not prove callback arrival or state order, and the screenshot does not establish an A1a regression.
- Suggested Fix: Review actual select/submit dispatch, form identity and state mutation with deterministic ordering fixtures. Preserve missing-selection refusal. Add minimal redacted state/sequence observations only if evidence warrants; propose a fix after reproduction rather than choosing a default or replaying signup.
- Impact: medium
- Risk: medium
- Dependencies: A1b caller review and existing form-owner/private-response checks; no proven cause yet.
- Status: Evidence question, not an accepted defect; separate from committed signup acceptance.

### Deferred Optimisation
- Area: RECOVERY-QUEUE-62; services/queue_admission_recovery.py, services/player_report_recovery_service.py and recovery observation ordering
- Type: consistency
- Description: Report 62 retains a startup queue incident last checked at 21:14:30, while the exact linked cache-only player report resolves at 21:16:52. Collection is nontransactional; the saved queue state predates domain closure. This does not prove an active blocker or a persistent reconciliation defect.
- Suggested Fix: Recheck the existing incident once through the normal operator flow. If still open, correlate exact post-completion preparation/domain state and check timestamps, then reproduce ordering deterministically. Preserve durable receipts and ownership; no forced release, cancellation or business replay.
- Impact: medium
- Risk: medium
- Dependencies: Exact linked operation evidence in private Report 62; distinct from CFG-OVERVIEW and the older configuration decision.
- Status: Queue closure not yet verified; linked cache-only outcome verified.

### Deferred Optimisation
- Area: GATEWAY-LAG-62; Discord event loop, recovery/report observation and callback responsiveness
- Type: performance
- Description: Supplied post-deployment logs show gateway delays of 41.7s and 42.4s at 21:16:33 and 21:17:16. Report 62's monitoring cycle completed in 216.875s and was fresh/healthy at collection. These observations do not establish a common cause or implicate the MGE callback.
- Suggested Fix: Conduct a bounded passive-evidence review of loop-blocking work, scheduling and diagnostic/report callers. Identify exact stacks or deterministic reproductions before remediation. Separate network delay, off-loop work duration and event-loop starvation; do not increase timeouts, repeat status probes or restart to manufacture a clean sample.
- Impact: high
- Risk: medium
- Dependencies: Separate reliability scope; only proven directly related blocking work belongs in A1b. SQL 51400, singleton ownership and earlier configuration 51421 remain distinct.
- Status: Confirmed delay observation; cause unassigned. No runtime fix authorized by the documentation handoff.


## 29 October shared board lifecycle follow-ups

### Deferred Optimisation
- Area: MGE-RELEASE-CAPABILITY; scripts/prepare_k98_update.py, installed source-transition registry, deploy/k98-release.json and SQL deploy/SqlDeploy.*Release.ps1
- Type: architecture
- Description: The completed local MGE finalisation schema requires rowversion/defaults, an ordinary work index and three new triggers, which neither existing combined-updater profile represents. There is no MGE release profile or installed exact source transition. This is a release blocker, not a security finding or optional cleanup.
- Suggested Fix: Implement the bounded release-authoring slice and native checks in the [qualification packet](../task_packs/P1%20MGE%20Finalisation%20-%20Native%20SQL%20and%20Updater%20Qualification%20Packet%20-%202026-10-29.md), reusing existing ownership, ledger, atomicity and resume contracts. Bind actual predecessor/tool/environment observations before packaging; preserve historical registry entries and uncertain outcomes.
- Impact: high
- Risk: high
- Dependencies: Explicit release-authoring scope approval, disposable native target approval, separate Bot/SQL Changes reviews, actual installed-tool bindings and coordinated drained rollout.
- Status: Captured and implementation-ready for approval; no updater capability or live SQL change made by packet preparation.

### Deferred Optimisation
- Area: A2-ARK-FINAL; ark/ark_scheduler.py, ark/dal/ark_dal.py, registration/confirmation/team delivery and rehydrate_views.py
- Type: architecture
- Description: Past Scheduled/Locked rows can remain refresh-eligible because the fallback completion call is fed only Completed rows. Final delivery uses timestamps and a seven-day lookback, with no per-target generation proof. Static source evidence does not establish live old-record counts.
- Suggested Fix: In a bounded Ark slice, inventory eligibility, separate ended/awaiting-result from finalised, and persist all target identities/revisions/outcomes. Preserve late results, original handlers and result/audit data; do not use expected two or three active boards as a cap.
- Impact: high
- Risk: medium
- Dependencies: A2 Ark result policy and SQL validation; shared MGE contract evidence; no live cleanup authorized.

### Deferred Optimisation
- Area: A2-VOTE-FINAL; voting/scheduler.py, voting/dal.py, voting/survey_dal.py and manual close/reopen/delete services
- Type: architecture
- Description: Domain closure precedes final board edit and announcement, while due selectors include only Open records. Failed final delivery can be stranded after closure.
- Suggested Fix: Persist generation-qualified board edits and independent announcement outcomes across deadline/manual closure and restart. Hold unknown sends; retain response and audit history during retirement.
- Impact: high
- Risk: medium
- Dependencies: A2 voting/survey slice; authoritative 20260701_002 and 20260702_003 SQL migrations; separate bot/SQL Changes review.

### Deferred Optimisation
- Area: A2-CALENDAR-IDENTITY; event_calendar/pinned_embed.py
- Type: consistency
- Description: Broad fetch/edit failures can create a replacement overview or clear its tracker. Transient/inaccessible/unknown outcomes are not confirmed deletion.
- Suggested Fix: Preserve the original identity and durable uncertainty until an explicit disposition. Keep the rolling 30-day overview active and distinguish historical event messages, reminders and private responses.
- Impact: high
- Risk: medium
- Dependencies: Bounded A2 calendar caller/receipt design and negative tests; no automatic historical cutoff or replacement.
