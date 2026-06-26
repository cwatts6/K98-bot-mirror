# Resolved Deferred Optimisation History

This file preserves resolved deferred-optimisation notes that used to live in
`../deferred_optimisations.md`. It is historical context only.

### Phase 11C Completed Item
- Area: `inventory/report_image_renderer.py`
- Type: refactor
- Description: Phase 11A extracted shared glyph-safe text primitives into `core.visual_text`, and Phase 11B migrated the KVK renderer family away from the old PreKvK helper path. The inventory report renderer still owned local font loading, text measurement, fit-to-width, wrapping, panel drawing, and PNG export helpers.
- Resolution: Phase 11C migrated Inventory report font loading, glyph-safe text width, fit-to-width sizing, wrapping, and text drawing to `core.visual_text` while keeping Inventory-local chart layout, panel styling, footer generation, PNG export, filenames, dimensions, report visibility behavior, range controls, export buttons, and generated report contracts unchanged.
- Validation: Focused renderer tests cover shared helper ownership, glyph-safe wrapping, filename preservation, PNG dimensions, and special-character governor-name rendering. The local `phase11c_inventory_resources_smoke.png` artifact was rendered and inspected before handoff.

### Phase 7 Completed Item
- Area: `build_KVKrankings_embed.py`, `ui/views/stats_views.py`, `honor_rankings_view.py`, `commands/stats_cmds.py`, legacy player ranking command compatibility paths
- Type: refactor
- Description: Phase 5 intentionally preserved the legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` paths during rollout. With Phase 5 complete, the legacy KVK and Honor ranking commands still retain older builders/views and duplicated presentation semantics while the unified `/kvk rankings` path uses the shared current-ranking payload/browser foundation.
- Resolution: Phase 7 replaced `/mykvkstats`, `/mykvktargets`, `/mykvkhistory`, `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` with tested deprecated redirect/help responses to the canonical `/kvk` command surface. The inline legacy command bodies were removed from the redirect handlers, player and canonical command docs were updated, and `/kvk` channel limits were aligned across the new commands.
- Validation: Automated validation passed during PR preparation, including full pytest (`1820 passed, 2 skipped`), pre-commit, architecture/deferred/select-tests validators, command registration validation, and smoke imports. Manual Discord smoke testing confirmed old command redirects and new command channel consistency. Final removal after the no-feedback window is tracked as a new active deferred cleanup item.

### Phase 5H Completed Item
- Area: `kvk/rendering/kvk_rankings_card_renderer.py`, ranking-card render/send path
- Type: performance
- Description: Phase 5E smoke testing found that visual ranking cards can take multiple seconds to render/load in Discord. The full ranking visual surface now exists, so render latency needed profiling before Phase 5 closed.
- Resolution: Phase 5H profiled representative current KVK, Honor, PreKvK, and Hall of Fame records Top 10 card renders, then cached resized ranking-card backgrounds, cached the current-card overlay, reused the existing cached records overlay, and switched ranking-card PNG output away from Pillow's expensive `optimize=True` path while keeping PNG output and embed fallback behaviour unchanged.
- Validation: Baseline medians across eight warm renders were KVK 1375.3 ms, Honor 1458.6 ms, PreKvK 1282.0 ms, and records 1449.4 ms. Final medians were KVK 95.6 ms, Honor 105.9 ms, PreKvK 259.3 ms, and records 319.1 ms. Focused renderer tests passed and local visual samples were generated for all four card families.

### Phase 5G Completed Items
- Area: `/kvk rankings type:honor`, `kvk/rendering/kvk_rankings_embed.py`
- Type: consistency
- Description: Phase 5E smoke testing found that Honor Top 25 and Top 50 compact browser output listed the correct ranked governors but no ranking values were displayed.
- Resolution: Phase 5G added an Honor compact value column so Top 25 and Top 50 embed/browser rows display the selected Honor value, then smoke-test polish made compact row fitting display-width aware for names with wide/special characters. The Honor Top 10 visual card, Honor no-admin-override channel gate, and legacy `/honor_rankings` were preserved.
- Validation: Focused compact embed tests cover Honor Top 25 value rendering and fixed-width row alignment, including wide-character governor names.

- Area: `/kvk rankings type:prekvk`, `kvk/rendering/kvk_rankings_embed.py`
- Type: consistency
- Description: Phase 5E smoke testing found that PreKvK Top 25 and Top 50 compact browser output had column alignment drift similar to the earlier KVK Top 25/50 issue. Long names and multi-metric columns could wrap or shift values onto confusing lines.
- Resolution: Phase 5G tightened PreKvK compact fixed-width formatting with short stage headers, preserved near-billion value units by normalising rounded `1000.0M` output to `1.0B`, and made compact row fitting display-width aware for names with wide/special characters. Overall, Stage 1, Stage 2, Stage 3, Power, freshness/source footer, and image-based legacy `/prekvk report` were preserved.
- Validation: Focused compact embed tests cover PreKvK Top 50 fixed-width row shape, long-name truncation, near-billion Power values, and wide-character governor names.

- Area: `/kvk rankings type:kvk`, `kvk/rendering/kvk_rankings_card_renderer.py`
- Type: consistency
- Description: Phase 5E smoke testing confirmed the current KVK Top 10 visual card still left-aligned the top-three podium text, while Records, Honor, and PreKvK cards centered podium ranks/names/values.
- Resolution: Phase 5G moved the current KVK Top 10 podium into the shared centered rendering path while preserving existing KVK card metrics, support values, footer/filter wording, and embed fallback.
- Validation: Focused renderer tests verify the KVK podium uses centered text rendering, and a local card sample was generated for visual inspection.

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
