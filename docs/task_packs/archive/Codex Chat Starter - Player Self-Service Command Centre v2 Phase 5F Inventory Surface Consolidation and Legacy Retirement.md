# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5F Inventory Surface Consolidation and Legacy Retirement

Status: completed and archived execution starter. Phase 5F delivered in mirror PR #225, was promoted
to production branch `prod/phase-5f-inventory-consolidation` at commit `89f7da16`, and was operator
accepted after final Discord smoke on 2026-07-16. Do not reuse this starter as an active task.

The accepted result also includes the post-smoke retirement of `/export_inventory` and the combined
Inventory export, the Stats-only `/me exports` state, and the Personal Settings visual reflow. The
three selected-governor report-page exports remain. No SQL change or deployment occurred.

## Copy/Paste Starter

```text
Codex, begin Player Self-Service Command Centre v2 Phase 5F: Inventory Surface Consolidation and Legacy Retirement.

Approval state:
- GovernorOS v2 Phases 1-5E are complete and operator accepted
- Phase 5E Preferences delivered in mirror PR #224 and production PR #531 and was deployed on 2026-07-16
- Phase 5F Premium Inventory Summary Card is superseded and must not be built
- the approved Phase 5F outcome is Inventory surface consolidation and legacy retirement
- remove /me inventory
- remove /myinventory
- remove /inventory_preferences
- public Inventory report posting is not required
- the combined All report viewing option is not required
- the selected-governor dashboard plus /me resources, /me speedups, and /me materials are the definitive report UX
- remove the Export Inventory control/option window from /me exports; keep /me exports Stats-only
- remove /export_inventory
- preserve private Excel/CSV/Sheets exports on /me resources, /me speedups, and /me materials
- /inventory import and /inventory audit remain unchanged
- Personal Settings no longer needs Inventory visibility and must be simplified to regional profile plus LOCAL/UTC context
- no new backdrop is required; reuse assets/me/cards/me_preferences.png
- assets/me/cards/me inventory.png is approved for deletion after reference audit
- no SQL deployment or destructive SQL cleanup is approved
- runtime implementation is approved subject to the normal audit, architecture, and plan gates
- one-pass execution is not approved

Production usage evidence supplied by the operator:
UserId              UserDisplay       Uses   LastSeenUtc
559076207627468807  Chrislos (1198)   2      2026-07-15 15:36:31.378

The only /myinventory user was the operator. The operator has explicitly confirmed that public posting,
the All viewing route, and /inventory_preferences are not required.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5F Inventory Surface Consolidation and Legacy Retirement.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5E Premium Preferences Summary Card.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5B Premium Inventory Report Backdrops and Visual Alignment.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5A Direct Inventory Reports and Governor Context.md
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

If the completed Phase 5E task pack or starter is still under docs/task_packs/ rather than archive/,
record that mismatch in the audit and include the archive move in the exact manifest. Do not create a
duplicate archive copy if the local checkout already moved it.

Follow the conditional reading order in docs/reference/README.md for command removal, Discord views,
rendering/file handling, SQL-backed preferences, testing, security routing, and promotion.

Validate the existing SQL contract read-only against:
C:\K98-bot-SQL-Server

At minimum inspect dbo.InventoryReportPreference and search the SQL repository for every dependency.
No SQL schema/table/view/index/procedure/data/permission change or deployment is approved.

Use these skills:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review
- k98-promotion-check only at the later production-promotion gate
- k98-security-review-routing

Security routing:
- bot repository: provisional Changes review against the final intended base..head or working-tree diff
- use $codex-security:security-diff-scan only after the final diff exists
- verify Scan type: Changes and Deep: Off
- SQL repository: documented skip because this task performs read-only contract/dependency validation and no SQL diff
- do not start a standard or deep codebase audit without a separate explicit operator request

Mandatory workflow:
1. Audit and scope review, then stop for approval.
2. Record the provisional security-routing decision and exact target; do not start a scan.
3. Architecture validation and exact file manifest, then stop for approval.
4. Implementation plan, including deployment and command-resync order, then stop for approval.
5. Implement only after approval.
6. Run focused/full validation, visual QA, command registration, SQL read-only validation, K98 PR review, and the bot Changes security review.
7. Create/review the mirror PR and complete operator Discord smoke.
8. Run promotion check, production promotion, deployment, command resync, and post-deploy verification only after acceptance.

Do not deploy Phase 5F as two independent production states. Command retirement and Personal Settings
visibility removal must land together so there is never a dead privacy setting or a remaining public
legacy report without its controlling setting.

First audit and report, with repository evidence:

Command surface:
- exact registration/decorator/version/usage chain for /me inventory
- exact registration/decorator/version/usage chain for /myinventory
- exact registration/decorator/version/usage chain for /inventory_preferences
- exact current command counts and every hard-coded baseline/test/doc that must change
- exact command resync/cache procedure needed so removed guild commands disappear
- confirmation that /inventory import, /inventory audit, and the /inventory group remain and /export_inventory is removed

Old summary route:
- /me inventory command -> PAGE_INVENTORY -> summary service -> renderer/fallback -> asset -> Open Report
- every Inventory navigation button and custom_id
- every Inventory-only renderer branch/helper/test
- every reference to assets/me/cards/me inventory.png
- whether the asset can be deleted with zero retained runtime/test references

Legacy detailed-report route:
- every import/caller of ui/views/inventory_report_views.py
- /myinventory visibility read/default prompt
- governor/output selector and All viewing option
- public/private dispatch behavior
- old range/export controller
- every test/string that directs users to /myinventory or /inventory_preferences
- whether ui/views/inventory_report_views.py can be deleted in full

Modern report route to preserve:
- /me dashboard RSS/Speedups/Materials buttons
- /me resources, /me speedups, /me materials
- selected-governor resolver/access recheck
- report tabs and 1M/3M/6M/12M
- private Excel/CSV/Sheets exports
- Dashboard return
- Change Governor and >25 paging
- no-data guidance
- same-payload fallback and attachment/file cleanup
- report renderer, payload, dimensions, filenames, icons, dates, calculations, VIP use, and backdrops

Export boundary:
- every retained InventoryReportView.ALL consumer
- remove InventoryReportView.ALL when its combined export consumer is removed
- prove the three report-page exports remain selected-governor/private
- preserve their export schemas, windows, filenames, formats, and Google Sheets behavior

Dashboard/Accounts boundary:
- every consumer of build_latest_inventory_snapshot and current-RSS helpers
- preserve selected-governor Inventory highlights
- preserve Accounts portfolio RSS and Account Summary Inventory As Of
- identify helpers that look legacy but are shared by retained surfaces

Visibility dependency map:
- every reference to InventoryReportVisibility
- every visibility read/write/default/resolve/confirmation API
- every DAL query/MERGE to dbo.InventoryReportPreference
- every Preferences payload/renderer/fallback/view/test/doc dependency
- every generic PlayerSelfServiceSummary dependency
- SQL-side dependency search
- whether player_self_service/preference_service.py becomes fully orphaned
- whether the visibility enum/service/DAL methods can be removed completely
- confirm dbo.InventoryReportPreference itself remains untouched for rollback

Preferences simplification:
- exact current preferences_summary.py profile and visibility responsibilities
- exact current preferences_renderer.py PRIVATE/PUBLIC and Privacy & Sharing geometry
- exact Manage settings -> Regional profile / Privacy & sharing journey
- exact profile field catalogs, paging, atomic save/clear, superseded/concurrent handling, Back, refresh, timeout, avatar, fallback, and stream lifecycle to preserve
- exact safe route for Manage settings to open Regional Profile directly
- exact derivation of LOCAL versus UTC from the existing TimeReferenceSummary
- exact renderer/fallback/copy changes needed to remove all privacy content without inventing a replacement metric
- native, Discord desktop, and mobile reflow plan using the existing me_preferences.png asset

Generic Player Self-Service summary:
- exact live callers of PlayerSelfServiceSummary.preferences and .inventory
- exact eager reads currently performed for Reminders, Exports, Accounts child refresh, and any fallback
- which obsolete visibility/profile/VIP/all-linked Inventory reads can be removed safely
- call-count/fake-loader tests proving retained pages no longer invoke removed readers
- pre-existing generic renderer/view debt that is unrelated and should remain deferred until Phase 5G

Documentation state:
- verify Phase 5E active-versus-archive file placement
- list current canonical docs that must change
- leave historical archived execution records intact where they accurately describe the old delivery

Do not code during the first response. Stop after:
1. audit findings;
2. exact Review / Modify / Delete / Move / Create manifest;
3. architecture recommendation;
4. command-count before/after;
5. risk and rollback boundary;
6. test-selection proposal;
7. security-routing proposal;
8. approval checkpoint.

Locked final command model:

/me dashboard
/me accounts
/me reminders
/me preferences
/me resources
/me speedups
/me materials
/me exports

/inventory import
/inventory audit

Retired:
/me inventory
/myinventory
/inventory_preferences
/export_inventory

Expected command-count result:
- top-level commands: 42 -> 39
- /me grouped subcommands: 9 -> 8
- /inventory grouped subcommands: remains 2

Locked Inventory UX:
- selected dashboard shows latest RSS, Speedups, and Materials for the selected governor
- dashboard report buttons open the matching private premium report
- direct /me report commands remain available
- report pages retain tabs, ranges, private exports, Dashboard, and Change Governor
- no public Inventory report path
- no combined All viewing route
- /me exports is Stats-only and combined/all-governor Inventory export is absent
- private Resources/Speedups/Materials report-page exports remain
- no replacement Share/Public action

Locked Personal Settings outcome:
- remains private, author-gated, Discord-user scoped
- retains saved timezone, location, and preferred-language metadata
- retains one generated-at UTC clock, local-time conversion, DST-aware offset, honest UTC fallback, three-field coverage, and one deterministic Settings Insight
- header state becomes LOCAL when the saved timezone is usable, otherwise UTC
- LOCAL/UTC is derived display state, not a new saved preference
- remove PRIVATE/PUBLIC state
- remove Privacy & Sharing panel
- remove Inventory visibility consequence copy
- remove privacy-specific warning/insight priority
- remove Privacy & sharing child journey and confirmation flow
- Manage settings should open the Regional Profile field-selection journey directly when architecture permits
- preserve profile catalogs, paging, atomic per-field save/clear, superseded/concurrent safety, Back, avatar, fallback, attachments, cleanup, and graceful timeout
- reuse assets/me/cards/me_preferences.png at 1702x924
- keep stable filename me_preferences_<discord_user_id>.png
- do not create a new backdrop or invent a new metric to fill the removed panel
- make Regional Profile the larger primary block above the smaller Local Time Reference
- align the profile coverage text beside the LOCAL/UTC pill at top-right

Recommended profile-only Settings Insight priority:
1. unavailable saved metadata needs review
2. no usable timezone
3. timezone ready but optional location/language incomplete
4. all three profile details available

Locked removal boundary:
- remove InventoryCategoryStatus, InventoryStatus, all-linked summary builders/loaders, PAGE_INVENTORY, Open Report, legacy selector/controller, visibility model/service/DAL, and directly owned tests only when exact reference audit proves no retained caller
- remove player_self_service/preference_service.py only if fully orphaned
- remove ui/views/inventory_report_views.py only if fully orphaned
- remove assets/me/cards/me inventory.png only after zero active references
- stop Reminders and Exports from paying for obsolete visibility/all-linked Inventory reads

Locked preservation boundary:
- keep /inventory import and /inventory audit
- keep ui/views/player_self_service_inventory_report_views.py
- keep inventory/report_image_renderer.py and all three premium report backdrops
- keep report payloads, calculations, ranges, filenames, charts, dates, icons, VIP calculations, no-data behavior, and exports
- keep build_latest_inventory_snapshot and current-RSS helpers used by dashboard/Accounts
- keep /me exports Stats option window
- keep dbo.InventoryReportPreference and existing rows unchanged for rollback
- keep unrelated legacy command removals and broad generic-renderer consolidation out of scope

Architecture rules:
- commands and Discord views stay thin
- no new direct SQL in commands or views
- remove dead service/DAL code only after caller proof
- do not copy report, export, access, or Inventory calculation logic
- preserve author gating, access rechecks, stale/foreign/forged/concurrent denial, timeouts, and stream cleanup
- no SQL deployment
- no data migration
- no new command
- no broad framework

Likely files to audit:
- commands/me_cmds.py
- commands/inventory_cmds.py
- scripts/validate_command_registration.py
- ui/views/player_self_service_views.py
- ui/views/inventory_report_views.py
- ui/views/player_self_service_inventory_report_views.py
- ui/views/player_self_service_preference_views.py
- ui/views/player_self_service_export_views.py
- ui/views/player_self_service_governor_dashboard_views.py
- player_self_service/service.py
- player_self_service/page_cards.py
- player_self_service/dashboard_card.py
- player_self_service/preferences_summary.py
- player_self_service/preferences_renderer.py
- player_self_service/preference_service.py
- player_self_service/governor_dashboard_service.py
- inventory/models.py
- inventory/reporting_service.py
- inventory/dal/inventory_reporting_dal.py
- inventory/report_image_renderer.py
- inventory/export_service.py
- assets/me/cards/me inventory.png
- assets/me/cards/me_preferences.png
- command, Player Self-Service, Preferences, Inventory report, export, dashboard, and import tests
- README-DEV.md
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md
- docs/task_packs/README.md
- docs/task_packs/archive/README.md
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- SQL repo sql_schema/dbo.InventoryReportPreference.Table.sql and repository-wide references

Testing expectations after implementation:
- command registration and cache removal
- Preferences LOCAL/UTC complete/partial/unavailable states
- Manage settings direct Regional Profile journey and all field mutations
- renderer/fallback/native/desktop/mobile output with no privacy content
- direct report no/one/multiple/>25 journeys
- tabs, ranges, private exports, Dashboard, Change Governor, no-data, timeout, cleanup
- dashboard Inventory highlights
- Accounts RSS and Inventory As Of
- /me exports Stats-only and each direct report private export
- /inventory import and audit regressions
- proof that retained pages do not read obsolete visibility/all-linked Inventory summary sources
- architecture, deferred, selector, security-routing, command-registration, import-smoke, pre-commit,
  full pytest, log-noise, diff-check, K98 PR review, and Changes security review

Before PR handoff:
- use k98-security-review-routing
- run the final bot diff as Changes with Deep off
- record the exact base/head
- record a precise SQL-repo skip with read-only validation evidence
- update all canonical command counts and docs

Deployment and smoke requirements:
- promote the exact accepted mirror patch to production
- restart/deploy normally
- resync application commands
- verify /me inventory, /myinventory, and /inventory_preferences are absent
- smoke /me dashboard RSS/Speedups/Materials
- smoke each direct /me report and private export
- smoke /me preferences LOCAL/UTC and Manage settings
- smoke /me exports Stats-only plus each direct report private export
- smoke /inventory import and /inventory audit
- verify no public Inventory report can be produced

Rollback:
- restore the prior accepted bot patch and command registrations
- resync commands
- redeploy
- reuse the untouched dbo.InventoryReportPreference rows

Do not implement SQL table retirement in this task. Capture a later deferred SQL cleanup requiring a
fresh dependency audit, observation window, explicit approval, migration, and rollback.
```

## Expected First Response

The first Codex response should contain only:

1. confirmed repository/branch/base state;
2. required-reading completion;
3. current command and dependency audit;
4. modern-report preservation map;
5. Preferences and visibility dependency map;
6. SQL read-only validation result;
7. exact Review / Modify / Delete / Move / Create manifest;
8. architecture and atomic-deployment recommendation;
9. command-count before/after;
10. test-selection proposal;
11. provisional security-routing decision;
12. risks, rollback, and deferred boundaries;
13. an explicit stop for approval.

It must not modify runtime code during that first response.
