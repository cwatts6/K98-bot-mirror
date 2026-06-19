# Resolved Deferred Optimisation History

This file preserves resolved deferred-optimisation notes that used to live in
`../deferred_optimisations.md`. It is historical context only.

### Phase 5F-1 Completed Item
- Area: `/kvk rankings` current-ranking browser, registry/account lookup, `kvk/services/kvk_rankings_service.py`, `ui/views/kvk_rankings_views.py`
- Type: architecture
- Description: Phase 5B established a unified current-ranking browser for KVK, Honor, and PreKvK with primary Top 10/25/50 controls, but it intentionally did not add deeper Top 100 player controls or a personalised "my rank" lookup. Phase 5E delivered Honor and PreKvK visual cards, leaving Phase 5F to provide a coherent way for players outside the public Top 50 to find their own current position without expanding the main browser surface.
- Resolution: Phase 5F-1 added a registry-aware private My Rank flow for current KVK, Honor, and PreKvK rankings. Ranking position lookup stays service-owned, multi-account users receive a private account selector, unregistered/not-ranked/missing-source states return private messages, and Top 100 remains absent from primary player controls.
- Validation: Focused service and browser tests cover registered users, unregistered/unauthorised selected accounts, multi-account selection, not-ranked governors, missing source data, internal full-rank lookup paths, Honor channel-gate preservation, and Top 100 exclusion.

### Phase 4 Completed Item
- Area: `commands/ark_cmds.py`, `docs/ark/`, Ark command tests
- Type: architecture
- Description: Phase 4 grouped all Ark commands under `/ark`, including `/ark reminder_prefs` and `/ark report_players`, while preserving permissions, options, versions, usage tracking, response visibility, modal/view flows, and command-cache semantics.
- Resolution: Added the `/ark` command group, updated Ark command docs/tests and command-platform docs, and added a post-merge Discord briefing note.
- Validation: Command registration reports `primary=62 grouped_subcommands_detected=43 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=62` in implementation validation.

## Command Platform Audit & Optimisation Programme

- Command Platform Phase 7, Governance And CI Guardrails, was completed in PR 139
  (`codex/command-platform-phase-7-governance`), merged, pushed to production on 2026-06-02, and
  closed the Command Platform Audit & Optimisation Programme.
- The resolved command-limit drift item covered `commands/` and
  `scripts/validate_command_registration.py`. Batch 1 command grouping had reduced the primary
  command surface from 100 to 82, Phase 3 reduced it to 75, Phase 4 reduced it to 62, and Phase 5A
  reduced it to the final active baseline of
  `primary=39 grouped_subcommands_detected=76 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=39`.
- Phase 7 added approved top-level command baseline enforcement, JSON/Markdown command inventory
  artifact output, focused command-governance CI, pre-commit command registration validation, and
  command-change checklist material for task packs, PRs, and promotion review.
- Player self-service workflow redesign and public calendar/KVK calendar redesign remain active
  separate deferred optimisation programmes, not additional command-platform phases.

## Stats Commands Full Optimisation

- Stats Commands Full Optimisation & Standardisation was implemented, merged, production promoted, and smoke-tested via PR #78.
- `commands/stats_cmds.py` no longer performs `/my_stats_export` SQL directly; export data access now lives in `stats/dal/stats_export_dal.py` and export orchestration lives in `services/stats_export_service.py`, resolving GitHub issue #46.
- Stats account resolution now routes through `services/stats_account_service.py`, which delegates to the SQL-backed registry service boundary and removes stats command/service traversal of the legacy registry dict shape, resolving the stats scope of GitHub issues #27, #29, #31, and #32.
- Stats-touched legacy registry view/account-selection paths were aligned with the current registry-service flow where touched by stats commands, resolving the stats scope of GitHub issue #28.
- KVK admin/stat command flows touched by the stats cleanup were reviewed and aligned with the current service/DAL boundaries used by the deployed implementation, resolving GitHub issue #42 for the stats command batch.
- Production deployment completed successfully and manual Discord command smoke tests passed after deployment.

## Telemetry Commands Full Optimisation

- Telemetry Commands Full Optimisation & Standardisation was implemented, merged, production promoted, and smoke-tested via PR #76.
- `commands/telemetry_cmds.py` no longer imports or wraps the KVK DAL current-KVK resolver, resolving GitHub issue #26.
- The telemetry scope of command-layer SQL separation is complete, resolving GitHub issue #33.
- CrystalTech governor session locking is now restart-safe and service/DAL-backed, resolving GitHub issue #47.
- `/mykvktargets` and `/mykvkcrystaltech` resolve linked accounts through `services/governor_account_service.py`, which delegates to `registry_service.get_user_accounts()`.
- CrystalTech governor session locking now routes through `services/governor_session_lock_service.py` and `registry/dal/governor_session_lock_dal.py` with UTC expiry, release, refresh, contention, and cleanup support.
- Player profile posting moved to `commands/player_profile_flow.py`.
- CrystalTech interaction orchestration moved to `commands/crystaltech_flow.py`.
- `account_picker.py`, `kvk_ui.py`, selected KVK personal views, selected registry views, and Ark registration account lookup were aligned away from direct registry dict traversal where touched.
- Final deployed validation: `python -m pytest -q tests` reported 1306 passed and 8 skipped; command registration and import smoke validation passed; post-deploy Discord smoke testing was completed.

## MGE Process Polish

- MGE Process Polish Phase 2 was implemented, production deployed, and smoke-tested via PR #75.
- `mge/mge_signup_service.py` self-signup account resolution now uses `registry_service.get_user_accounts()` instead of the legacy registry dict shape. Admin-add reverse owner lookup remains on `get_discord_user_for_governor()`.
- `mge/mge_publish_service.py` no longer performs direct Discord message fetch/send/edit/delete/DM IO. Publish, republish, reminder refresh, unpublish, award DM, and board refresh paths now route Discord operations through `mge/mge_publish_discord_adapter.py`.



### Deferred Optimisation
- Area: `commands/`, command documentation, `scripts/validate_command_registration.py`
- Type: architecture
- Description: The wider command-surface end state remains separate from startup lifecycle ownership. Grouping or retiring slash-command surfaces can reduce Discord's 100-command sync risk, but it affects public/operator command paths, documentation, tests, and rollout communication.
- Suggested Fix: Scope a standalone command-surface optimisation programme after the Phase 6 lifecycle slices. Group or retire command paths by domain only with operator-approved UX rules, update docs and tests for renamed paths, preserve permissions and autocomplete behaviour, and keep `scripts/validate_command_registration.py` enforcing command-count guardrails. Treat this as a separate wider task, not a startup lifecycle PR.
- Impact: high
- Risk: medium
- Dependencies: Operator approval for command path changes; command lifecycle admin tooling convergence can happen first but is not required for command-surface grouping.
