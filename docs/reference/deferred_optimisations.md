# Deferred Optimisations

Active deferred optimisation items are staged here before they are grouped, scored, or promoted
to GitHub issues/task packs.

Resolved historical notes moved to `archive/deferred_optimisations_resolved.md`.

### Deferred Optimisation
- Area: `commands/stats_cmds.py`, `commands/telemetry_cmds.py`, `commands/prekvk_cmds.py`, `scripts/validate_command_registration.py`, `docs/reference/canonical_command_reference.md`
- Type: cleanup
- Description: Phase 7 converted `/mykvkstats`, `/mykvktargets`, `/mykvkhistory`, `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` into tested deprecated redirect/help responses. The old command paths remain registered temporarily so players receive migration guidance, which means the command baseline, redirect helpers/tests, and compatibility docs still carry legacy surface area after the first deprecation rollout.
- Suggested Fix: After the agreed no-feedback window and operator approval, remove the deprecated command registrations and redirect-only tests, update `scripts/validate_command_registration.py::APPROVED_TOP_LEVEL_COMMANDS`, update `docs/reference/canonical_command_reference.md` and player/operator docs, and run command inventory, registration, focused KVK command tests, pre-commit, and full pytest before merge.
- Impact: medium
- Risk: medium
- Dependencies: Phase 7 redirect PR merged and deployed; player briefing posted; no actionable player feedback during the monitoring window; operator approval for final removal.

### Deferred Optimisation
- Area: `tests/test_ark_preference_service.py`, `tests/test_ark_bans_enforcement.py`, `tests/test_lock_timeout.py`, `tests/test_calendar_service.py`, `tests/test_calendar_pipeline.py`, remaining slow full-suite pytest paths
- Type: performance
- Description: After PR 107 resolved the original slow pytest offenders, the new duration audit `C:\Users\cwatt\Downloads\.codex_pytest_audit-new.log` shows the remaining full-suite outliers are concentrated in Ark preference/ban negative paths, lock-timeout coverage, calendar failure-path retries, live queue persistence, maintenance subprocess timeout/success coverage, and one inventory vision import case. The slowest current timings are `tests/test_ark_preference_service.py::test_set_preference_rejects_unknown_governor` at 7.33s, `tests/test_ark_bans_enforcement.py::test_admin_add_allows_when_override_on` at 5.23s, `tests/test_lock_timeout.py::test_remove_view_tracker_entry_returns_false_when_locked` at 5.06s, `tests/test_lock_timeout.py::test_save_view_tracker_raises_on_lock` at 5.06s, `tests/test_calendar_service.py::test_refresh_full_stops_on_sync_failure` at 3.02s, and `tests/test_calendar_pipeline.py::test_pipeline_stops_on_sync_failure` at 3.01s.
- Suggested Fix: Start a fresh audit from `.codex_pytest_audit-new.log` and classify each remaining slow path as intentional timeout coverage, missing test boundary, live dependency leakage, retry/backoff, or genuine defect. Preserve lock-timeout and subprocess timeout coverage, but replace real multi-second waits with patched timeout constants, fake clocks, controlled retry policies, or explicit service/DAL boundary fakes where safe. Keep the scope separate from PR 107 and validate with `pytest -vv tests --durations=30 --durations-min=1.0`, focused subsystem tests, `scripts/analyse_pytest_log_noise.py`, and `python -m pytest -q tests`.
- Impact: medium
- Risk: medium
- Dependencies: Use the post-PR-107 audit baseline (`1450 passed, 2 skipped, 19 warnings in 54.86s`); preserve genuine timeout, subprocess, lock, negative-path, and log-noise coverage.

### Deferred Optimisation
- Area: `commands/ark_cmds.py`, `ark/registration_flow.py`, `ark/confirmation_flow.py`, `ark/reminders.py`, `ark/dal/ark_dal.py`
- Type: refactor
- Description: The Ark create, amend, and cancel command handlers still contain substantial workflow orchestration, including config parsing, match validation, registration embed edits, JSON state lookup, reminder rescheduling/cancellation, audit logging, and cancel-DM dispatch coordination. Phase 4 intentionally preserved these bodies while moving command paths under `/ark` to avoid mixing command-surface migration with service extraction.
- Suggested Fix: Scope a follow-up Ark command orchestration extraction that moves create/amend/cancel workflow coordination into Ark services while leaving command handlers responsible for permissions, deferral, input collection, and response rendering. Preserve existing DAL contracts, restart-sensitive message/reminder state behavior, and modal/view callback behavior with focused regression tests.
- Impact: medium
- Risk: medium
- Dependencies: Phase 4 Ark command grouping is complete and smoke tested; validate service boundaries against existing Ark registration, confirmation, reminder, cancel, and audit tests.

### Deferred Optimisation
- Area: `commands/registry_cmds.py`, `commands/telemetry_cmds.py`, `commands/stats_cmds.py`, `commands/inventory_cmds.py`, `commands/subscriptions_cmds.py`, `commands/calendar_cmds.py`, player self-service command docs/tests
- Type: architecture
- Description: Player self-service commands are still split across development-era entry points instead of being designed as complete user workflows. The affected paths include `/register_governor`, `/modify_registration`, `/my_registrations`, `/mygovernorid`, `/my_stats`, `/my_stats_export`, `/mykvkcrystaltech`, `/myinventory`, `/inventory_preferences`, `/export_inventory`, `/subscribe`, `/modify_subscription`, `/unsubscribe`, and `/calendar_reminder_config`. Phase 7 has already moved `/mykvkstats`, `/mykvktargets`, and `/mykvkhistory` into deprecated redirect-only compatibility paths with final removal tracked separately, so those paths are no longer part of the future self-service redesign scope. These remaining commands are high-discoverability, likely high-traffic commands that players use for critical self-service tasks, and simple path grouping could preserve a fragmented user model while still forcing players to relearn command names.
- Suggested Fix: Scope a dedicated player self-service workflow redesign outside the command-count programme. Review each block as a user journey before choosing command paths. For registry/account flows, specifically evaluate whether lookup, register, review, and modify should be consolidated into a coherent Governor ID/account command surface rather than four separate commands. Review SQL-backed command usage, transition/announcement needs, Discord alias limitations, docs/smoke references, permission and channel behavior, and focused regression tests before any implementation.
- Impact: high
- Risk: medium
- Dependencies: Phase 5A admin/leadership/operator grouping is complete; requires operator approval, SQL-backed usage review, user-facing briefing, and a fresh task pack.

### Deferred Optimisation
- Area: `player_self_service/account_service.py`, `ui/views/player_self_service_account_views.py`, `/me accounts` player workflow
- Type: consistency
- Description: Phase 3 smoke testing showed that the path from `Find ID` to `Register` is still too manual. A player can search by name or partial name and receive a Governor ID, but then must click into register/replace separately and remember or manually re-enter the 9-digit ID. This preserves a legacy-command style memory step inside the otherwise modern account centre.
- Suggested Fix: Scope a later account-centre UX optimisation that lets lookup results carry forward into register and replace flows. Options include lookup-result action buttons, a select menu of matches that opens slot selection with the selected Governor ID already bound, or a combined register/replace flow that accepts a name search and then confirms the selected Governor before write. Preserve duplicate/claim protection, stale confirmation checks, service-owned confirmation models, and Discord select-option limits.
- Impact: medium
- Risk: medium
- Dependencies: Phase 3 Modern Account Centre smoke tested successfully and merged/deployed or otherwise operator-approved for follow-up; operator approval for account-centre UX optimisation after Phase 4 reminder centre or another approved process-simplification phase.

### Deferred Optimisation
- Area: `commands/subscriptions_cmds.py`, `player_self_service/reminder_service.py`, `ui/views/subscription_views.py`
- Type: refactor
- Description: Phase 4 adds a service-backed `/me reminders` centre while intentionally leaving legacy `/subscribe`, `/modify_subscription`, and `/unsubscribe` command handlers live and behavior-compatible. Those legacy handlers still own duplicated validation, normalization, DM confirmation wording, and unsubscribe cleanup orchestration that now has a cleaner service-owned equivalent.
- Suggested Fix: After Phase 4 is smoke tested and operator-approved, scope a follow-up consolidation that routes the legacy reminder commands through `player_self_service/reminder_service.py` without changing their registered paths or user-visible behavior. Keep duplicate subscription protection, DM confirmation behavior, unsubscribe tracker cleanup, scheduler/restart behavior, and focused legacy command/view tests green before considering later redirects or removal.
- Impact: medium
- Risk: medium
- Dependencies: Phase 4 Modern Reminder Centre delivered and smoke tested successfully; operator decision on whether legacy paths should be service-rerouted before any redirect/removal phase.

### Deferred Optimisation
- Area: `commands/calendar_cmds.py`, `commands/events_cmds.py`, `ui/views/calendar.py`, `ui/views/events_views.py`, public calendar/KVK calendar docs/tests
- Type: architecture
- Description: Generic public calendar and KVK calendar commands have inconsistent naming, visibility, scope, and interaction behavior. `/calendar` is an ephemeral calendar overview; `/calendar_next_event` is ephemeral and shows one next calendar event; `/next_kvk_fight` is public and shows one fight with controls for the next three fights; `/next_kvk_event` is public and shows one event with controls for the next five events. There is also no clearly named `/kvk_calendar` or equivalent KVK calendar overview, so grouping these commands now would tidy paths without resolving the user-facing model.
- Suggested Fix: Scope a dedicated public calendar/KVK calendar UX redesign outside the command-count programme. Review whether the end state should use grouped paths such as `/calendar overview`, `/calendar kvk_overview`, `/calendar next_event`, `/calendar next_kvk_fight`, and `/calendar next_kvk_event`; decide whether all public information commands should post publicly; define the missing KVK calendar overview behavior; align button counts and visibility; update docs/smoke references; and add focused command/view tests before implementation.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5A admin/leadership/operator grouping is complete; requires operator approval for public visibility changes and a fresh task pack. Phase 5A moved calendar admin/operator commands under existing `/ops calendar_*` paths so the flat public `/calendar` command remains untouched until this redesign.

### Deferred Optimisation
- Area: SQL repo legacy PreKvK phase object retirement
- Type: cleanup
- Description: After Phase 2B compatibility wrappers remove active scan-window logic, `dbo.PreKvk_Phases` and any compatibility-only phase objects may remain as unused legacy SQL surface.
- Suggested Fix: Run a later Option C retirement audit after at least one production cycle, re-check live SQL dependencies and manual/report usage, then prepare a SQL-repo-only drop plan with rollback scripts if no consumers remain.
- Impact: low
- Risk: medium
- Dependencies: Phase 2B compatibility wrapper deployment completed and smoke tested; live dependency checks confirm no references beyond the objects being retired; production owner approves destructive SQL cleanup.

### Deferred Optimisation
- Area: `C:\K98-bot-SQL-Server` SQL development and deployment workflow
- Type: architecture
- Description: SQL schema changes can now be developed through Git PRs, but the existing production export routine can still overwrite Git-driven SQL changes because it syncs production schema back to the repository as the main routine.
- Suggested Fix: Use `C:\Users\cwatt\Downloads\sql_deploy_route_task_pack.md` to create a PR-based SQL promotion workflow with guarded deploy scripts, migration history, a safe production schema export branch, `migrations/` conventions, and `docs/SQL_PROMOTION_GUIDE.md`.
- Impact: high
- Risk: medium
- Dependencies: DL_bot upload-routing and Phase 6 lifecycle work are complete; preserve current production schema export as a drift/safety mechanism while preventing direct overwrite of `main`.

### Deferred Optimisation
- Area: `bot_helpers.py`, `utils.py`, `core/queue_lifecycle.py`, `upload_routes/fallback_queue_route.py`, queue runtime state
- Type: architecture
- Description: Phase 6K is intentionally limited to live queue persistence hardening. A fuller queue-domain redesign remains separate, including clearer ownership for queued message/job lifecycle, worker status transitions, display state, processing state, retry/drop semantics, and the boundary between fallback upload routing, `channel_queues`, and live queue UI state.
- Suggested Fix: Scope a dedicated queue-domain redesign audit as a new deferred optimisation batch. Map queue state sources, worker lifecycle, status transitions, user-visible embed updates, failure modes, and restart behavior before proposing any code movement. Keep upload-route behavior unchanged unless a later approved task explicitly includes it.
- Impact: medium
- Risk: medium
- Dependencies: Phase 6K live queue persistence hardening and Phase 6L lifecycle closure are complete; coordinate as a separate post-Phase 6 programme.

### Deferred Optimisation
- Area: queue persistence model, SQL repo `C:\K98-bot-SQL-Server`
- Type: architecture
- Description: Live queue persistence remains file-backed through `QUEUE_CACHE_FILE` after Phase 6K hardened the file-backed model. SQL-backed queue persistence may eventually provide a stronger source of truth for queued work, in-flight state, and recovery after crashes, but it requires a separate schema and contract design rather than being folded into Phase 6.
- Suggested Fix: If the hardened file-backed queue state proves insufficient in production, scope a SQL-backed queue persistence design task. Validate table/procedure/index needs against `C:\K98-bot-SQL-Server`, define migration and rollback plans, preserve existing operator behavior, and add restart/recovery tests before any implementation.
- Impact: medium
- Risk: high
- Dependencies: Requires explicit approval, `k98-sql-validation`, SQL repo changes, and production migration planning.

### Deferred Optimisation
- Area: `event_calendar/pinned_embed.py`
- Type: refactor
- Description: Pinned calendar tracker persistence currently uses direct `Path.write_text()` JSON writes in `_save_tracker()`, unlike other restart-sensitive tracker files that use atomic JSON helpers and clearer failure boundaries.
- Suggested Fix: Move pinned calendar tracker persistence to the established atomic JSON helper pattern, preserve tracker shape and missing-message recovery behavior, and add focused tests for successful save, failed/partial write protection, missing tracker, and rehydration after restart.
- Impact: medium
- Risk: low
- Dependencies: Keep this separate from Phase 6F unless a later pinned-calendar persistence task is approved.
