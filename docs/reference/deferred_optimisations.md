# Deferred Optimisations

Active deferred optimisation items are staged here before they are grouped, scored, or promoted
to GitHub issues/task packs.

Resolved historical notes live in `archive/deferred_optimisations_resolved.md`.

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
- Description: Static review proves that `_offload_callable_py` catches an ordinary exception from `run_step`, then invokes the same callable through `run_blocking_in_thread`, catches again, and finally invokes it through `asyncio.to_thread`. A callable exception after entry can therefore cause up to three executions. The current call sites include SQL- and cache-related operations, but their exact production argument shapes, idempotence, and side-effect boundaries have not been audited to the standard completed for `DL_bot.py`.
- Suggested Fix: Scope a separate once-only audit for every `_offload_callable_py` caller. Reproduce the highest-risk real call shape deterministically, establish which executor contracts preserve its arguments/results/exceptions, then remove post-entry fallback and add cancellation/timeout coverage without changing SQL or cache behavior.
- Impact: medium
- Risk: medium
- Dependencies: Separate operator-approved task; complete caller/side-effect inventory; preserve Stats result normalization, SQL failure handling, cache behavior, and existing telemetry.
- Status: evidence required
- Last verified: 2026-08-31

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
- Area: `event_scheduler.py::save_active_reminders`, `REMINDER_TRACKING_FILE`, and active public-reminder restart restoration
- Type: consistency
- Description: Phase 2A preserved the existing `active_reminders` tracker contract, but `save_active_reminders()` still writes JSON directly rather than using the repository's atomic replacement helper. A process interruption during the write could leave restart-sensitive public-reminder message identity unavailable or malformed.
- Suggested Fix: Scope a separate restart/persistence slice that reproduces interrupted-write and save-failure behavior, then adopts atomic replacement while preserving the exact tracker path/shape, message IDs, event fallback metadata, cleanup, rehydration, scheduler timing, mention behavior, and non-raising failure boundary.
- Impact: medium
- Risk: medium
- Dependencies: Separate operator approval; focused tracker round-trip, interrupted-write, failure, missing-message, cleanup, and restart/rehydration tests. No payload-policy change.
- Status: assigned to Discord Embed Payload Safety Phase 2F; evidence and design-gated
- Last verified: 2026-09-02

### Deferred Optimisation
- Area: `ark/embeds.py`, `ark/ark_scheduler.py`, `ark/team_publish.py`, `ark/reminders.py`, selected Ark registration/confirmation renderers, and focused Ark payload tests
- Type: consistency
- Description: Ark roster fields are locally split to the field-value limit, but dynamic alliance titles, notes, updates, result notes, team descriptions, field count, and aggregate payload size are not modeled together across scheduled posts, DMs, registration messages, and team publication edits.
- Suggested Fix: First add payload measurements and deterministic pathological tests, then use the canonical embed contract to fix only proven failing builders. Approve product-specific choices for large rosters and notes, including pagination, additional embeds, attachments, or explicit omission markers, while preserving the existing first-publication mention and SQL-backed publication/message-ID behavior.
- Impact: medium
- Risk: medium
- Dependencies: Phase 1 canonical primitive; production-representative payload evidence; separate Ark presentation approval and Changes security review.
- Status: delivered and operator candidate-smoke accepted in Phase 2B; PR merges and final
  production-main verification pending
- Last verified: 2026-09-02
- Archived task pack: `docs/task_packs/archive/Codex Task Pack - Discord Embed Payload Safety Phase 2B Evidence-Led Ark Payload Hardening.md`

### Deferred Optimisation
- Area: `ark/state/ark_state.py`, `ark/confirmation_flow.py`, and persisted `confirmation_updates`
- Type: architecture
- Description: Phase 2B proves that persisted confirmation update history is not render-bounded and can grow to high cardinality. Phase 2B safely packs or explicitly marks omitted render units, but changing retention or storage would alter restart-sensitive state and historical visibility.
- Suggested Fix: Gather production cardinality and operator-use evidence, define retention/archive and historical-visibility semantics, then decide whether updates remain in the current JSON shape or need a separately approved durable SQL contract. Include migration, restart compatibility, failure recovery, and rollback before changing persistence.
- Impact: medium
- Risk: medium
- Dependencies: Production state evidence; operator decision on historical visibility; `k98-sql-validation` and a separate SQL PR only if durable SQL storage is selected.
- Status: assigned to Discord Embed Payload Safety Phase 2E; evidence and product-policy gated
- Last verified: 2026-09-02

### Deferred Optimisation
- Area: `ui/views/team_builder_views.py`, Ark team-review orchestration, and audit logging
- Type: architecture
- Description: The pre-existing team-builder view imports `insert_audit_log` directly from `ark.dal.ark_dal`. Phase 2B touches only its embed rendering and retains a narrow architecture-validator exception; extracting audit orchestration would expand the approved payload slice and risk changing interaction sequencing.
- Suggested Fix: In a separate Ark architecture slice, inventory assign/remove/reset/auto-balance audit ownership, move the audit coordination behind an Ark service boundary, and preserve actor IDs, action names, detail JSON, error behavior, permissions, webhook refresh, and interaction acknowledgement order.
- Impact: medium
- Risk: medium
- Dependencies: Separate operator approval; focused team-builder action, permission, audit, failure, and webhook/ephemeral interaction tests.
- Status: assigned to Discord Embed Payload Safety Phase 2E from Phase 2B architecture validation
- Last verified: 2026-09-02

### Deferred Optimisation
- Area: `build_KVKrankings_embed.py`, `embed_kvk_history.py`, `ui/views/kvk_history_view.py`, related rankings/history views, exports, and tests
- Type: architecture
- Description: Player-facing rankings and history outputs use bounded page counts and local clipping but do not uniformly prove title, field, footer, embed-count, and combined-character limits across charts, tables, multiple embeds, files, and interaction edits.
- Suggested Fix: Scope a player-facing payload slice that measures realistic and pathological rows, applies the canonical final validator, and chooses pagination or existing export paths rather than silent list truncation. Preserve canonical `/kvk history` placement, visibility, interaction ownership, chart/table meaning, files, and existing offload contracts.
- Impact: medium
- Risk: medium
- Dependencies: Phase 1 canonical primitive; separate product/output review; coordinate with the existing KVK History offload deferred item without combining unrelated executor work.
- Status: delivered and operator smoke accepted in Discord Embed Payload Safety Phase 2C; no runtime correction was required; mirror PR #254 and production PR #561 await manual merge and final production-main verification
- Last verified: 2026-09-03

### Deferred Optimisation
- Area: `commands/admin_cmds.py`, processing history/failure views in `embed_utils.py`, bot-health, queue, maintenance, and log-oriented diagnostic output
- Type: consistency
- Description: Operator diagnostics use mixed description slicing, field clipping, pagination, and log attachment behavior. Long paths, filenames, errors, or log summaries can still require output-specific handling beyond the same-root shared-helper corrections delivered in Phase 1.
- Suggested Fix: Audit live diagnostic routes separately from player-facing rankings. Use attachments plus short bounded summaries for log/export-like content, canonical final validation for every send/edit path, explicit omission markers for non-file lists, and focused privacy/redaction and fallback tests.
- Impact: medium
- Risk: medium
- Dependencies: Phase 1 shared sender correction; operator-output inventory; separate diagnostics scope so private logs and player-facing pagination are not mixed in one PR.
- Status: assigned to Discord Embed Payload Safety Phase 2D; review/scope approval required
- Last verified: 2026-09-03

### Deferred Optimisation
- Area: `stats_alerts/guard.py`, `stats_alerts/embeds/prekvk.py`, stats-alert state, and dispatch concurrency tests
- Type: architecture
- Description: The preserved Pre-KVK guard sequence checks the daily log, sends to Discord, then records the post-success claim. Concurrent dispatches can theoretically pass the read before either claim is recorded, although normal singleton-process controls reduce the known frequency and no production duplicate from this race has been established.
- Suggested Fix: Treat this as a separate reliability design, not embed Phase 2. Gather overlap evidence, then define reserve/commit/release semantics, Discord-failure release, uncertain-send reconciliation, stale-reservation recovery, lock contention, restart behavior, and migration/rollback before changing the current CSV or introducing a sidecar.
- Impact: medium
- Risk: high
- Dependencies: Production or deterministic concurrency evidence; explicit persistence-contract approval; restart/recovery tests and a separate Changes security review.
- Status: assigned to Discord Embed Payload Safety Phase 2G; evidence and design-gated
- Last verified: 2026-09-02

### Deferred Optimisation
- Area: `ark/registration_flow.py`, `ark/registration_messages.py`, and registration upsert outcome logging
- Type: consistency
- Description: Phase 2B candidate smoke confirmed a successful in-place registration edit while `ensure_message_result` logged `delivered=False`. The first returned value is the existing move/repost outcome, not overall delivery success, and the same boolean pair can also accompany a caught edit failure. The nearby exception log distinguishes failure operationally, but the field name alone is ambiguous for dashboards and incident review.
- Suggested Fix: In the Phase 2E Ark observability slice, define an explicit outcome value or narrowly rename the tuple and structured log fields to distinguish edited-in-place, moved/reposted, recreated, and failed outcomes. Preserve the existing send/edit/recreate calls, exception boundary, message references, state writes, announcement decision, and return behavior; add focused log-contract tests.
- Impact: medium
- Risk: low
- Dependencies: Delivered Phase 2B baseline; operator approval of the Phase 2E outcome vocabulary; focused successful-edit, move/repost, missing-message recreation, and failure-path tests.
- Status: assigned to Discord Embed Payload Safety Phase 2E; semantics-only planning, no Phase 2B runtime change
- Last verified: 2026-09-02
