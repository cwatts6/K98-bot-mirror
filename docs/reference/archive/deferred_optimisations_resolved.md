# Resolved Deferred Optimisation History

This file preserves resolved deferred-optimisation notes that used to live in
`../deferred_optimisations.md`. It is historical context only.

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
