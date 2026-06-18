# KVK Player Experience Redesign — Programme Pack

## 1. Programme Header

- Programme name: `KVK Player Experience Redesign`
- Date: `2026-06-03`
- Owner/context: K98 Bot command-surface and player-output modernisation
- Programme type: Product UX / Discord command architecture / visual output redesign / deferred optimisation programme
- One-pass approved: No

## 2. Programme Vision

Modernise the KVK player experience so the most-used KVK commands feel like a coherent product rather than a set of legacy data-dump embeds.

The end state should give players a clear `/kvk` command surface, modern generated visual cards, consistent terminology, and joined-up navigation between personal stats, targets, history, and rankings. The visual language should also prepare the bot for the longer-term KD98 website/webapp direction.

## 3. Why This Programme Exists

The current player-facing KVK outputs are useful but visually dated compared with the newer inventory image outputs. Commands such as `/mykvkstats`, `/mykvktargets`, `/mykvkhistory`, `/kvk_rankings`, `/honor_rankings`, PreKVK ranking/report commands, `/mygovernorid`, `/my_stats`, and `/player_profile` grew organically across several delivery phases.

The result is that players need to remember multiple command names, outputs are inconsistent, and KVK-specific journeys are not grouped around how users think:

- How am I doing in this KVK?
- What are my targets?
- What is my KVK history?
- Where do I rank?
- What should I do next?

This programme focuses first on the KVK-specific player surface because these commands are high-value, high-traffic during KVK, and closely related visually and functionally.

## 4. Target Command Model

### Player-facing command group

Target new player command group:

```text
/kvk stats
/kvk targets
/kvk history
/kvk rankings
```

Optional later expansion after the core group is stable:

```text
/kvk profile
/kvk help
/kvk settings
```

### Admin/operator command group

Delivered Phase 2A admin command group:

```text
/kvk_admin test_export
/kvk_admin refresh_stats_cache
/kvk_admin recompute
/kvk_admin export_all
/kvk_admin list_scans
/kvk_admin window_preview
/kvk_admin test_embed
```

The admin group is intentionally separated from the player `/kvk` group so player journeys remain clean and admin/operator tools do not clutter the public command surface. Phase 2A delivered this split in PR #140; `/kvk` is now reserved for the player scaffold.

## 5. Target User Journeys

### `/kvk stats`

Primary personal KVK dashboard.

Should answer:

- Who is this governor?
- Which KVK and scan is this based on?
- What is their KVK rank?
- How much KP have they gained?
- How much power have they gained/lost?
- How much Acclaim/contribution have they gained where the approved SQL output contract supports it?
- What is their likely playstyle?
- Are they performing well against expectations?

Target output style:

- modern generated image card
- KVK/camp themed background
- large headline metrics
- governor avatar/emblem
- rank badge
- colour-coded metric tiles
- scan freshness footer
- optional buttons to jump to targets/history/rankings

### `/kvk targets`

Personal KVK target and progress view.

Should answer:

- What are my active targets?
- How far through each target am I?
- What remains?
- Am I complete, on track, or behind?
- Is there a reason no target is set?

Target output style:

- progress-focused card or embed+image hybrid
- kill/dead/DKP progress blocks
- clear explanations for exempt, off-season, below-power, not-in-matchmaking, or unknown governor states

### `/kvk history`

Historical KVK performance view.

Should answer:

- How have I performed across recent KVKs?
- What was my rank, KP, deads, DKP, honor, and PreKVK performance?
- Am I improving?

Target output style:

- table/timeline first
- optional generated chart image later
- should preserve accessibility for longer historical data

### `/kvk rankings`

Unified KVK ranking browser.

Should replace or consolidate:

```text
/kvk_rankings
/honor_rankings
/prekvk ranking/report commands
```

Potential ranking modes:

- KVK overall
- kills / KP
- deads
- DKP
- honor
- PreKVK
- power
- pass windows
- acclaim/contribution where approved

Target output style:

- paginated embed first
- buttons/select menus for ranking type
- optional generated top-10/top-20 visual cards later

## 6. Visual Direction

The programme should move from traditional Discord text embeds toward generated image cards where the output benefits from layout, branding, visual hierarchy, and progress presentation.

The design direction should align with the modern inventory output approach and the planning mock-up shared during programme creation. The first implementation should define reusable visual primitives rather than hardcoding a one-off image.

Recommended reusable visual primitives:

- KVK card background provider
- governor identity block
- stat tile component
- progress bar / completion indicator
- rank badge
- freshness footer
- disclaimer/warning ribbon
- KVK phase/status chip
- metric colour policy
- image export helper with deterministic test mode

## 7. Design Principles

1. **Player-first command paths** — commands should map to player questions, not implementation history.
2. **Parallel migration** — new `/kvk` commands should be built alongside old commands until validated.
3. **No sudden removals** — legacy commands should remain during rollout, then redirect/deprecate later.
4. **Modern outputs without misleading metrics** — style must not hide unclear or unstable semantics.
5. **Preserve service/DAL boundaries** — commands and views stay thin.
6. **SQL source-of-truth validation** — KVK schema and procedure assumptions must be checked against `C:\K98-bot-SQL-Server`.
7. **Discord-safe UX** — button persistence, interaction safety, permissions, and command registration limits must remain protected.
8. **Website-ready thinking** — data shape and visual language should be reusable for the future KD98 webapp.

## 8. Programme Phases

### Phase 1 — Audit and Design Only

Audit the current KVK player commands, admin KVK commands, output formats, SQL/DAL/service dependencies, usage data, and visual generation options.

Deliver:

- current command map
- target command model
- player journey map
- admin command separation proposal
- output inventory
- metric/terminology review
- visual architecture proposal
- migration/deprecation plan
- implementation phase plan

No code changes.

### Phase 2A — Admin `/kvk` Collision Resolution

Status: complete. Delivered and merged in PR #140.

The former admin/operator `/kvk ...` commands were moved to `/kvk_admin ...` before the player scaffold was introduced:

```text
/kvk_admin test_export
/kvk_admin refresh_stats_cache
/kvk_admin recompute
/kvk_admin export_all
/kvk_admin list_scans
/kvk_admin window_preview
```

Old `/kvk ...` admin paths were intentionally removed from the active command surface. Permissions, channel restrictions, logging, usage tracking, service/DAL ownership, command-cache governance, and operator reference documentation were updated without changing SQL, import, recompute, export, or Google Sheets behaviour.

### Phase 2B — New `/kvk` Player Command Group Scaffold

Status: complete. Delivered, merged in mirror PR #141, and promoted to production.

Created the new `/kvk` player group in parallel with existing commands.

Initial subcommands:

```text
/kvk stats
/kvk targets
/kvk history
/kvk rankings
```

The first scaffold reused existing services and output behaviour as much as possible. The goal was safe command-surface migration, not visual redesign.

Legacy commands remain live.

Delivered Phase 2B details:

- `/kvk rankings` now includes KVK, honor, PreKvK, and Phase 5 Hall of Fame records modes; the first scaffold shipped KVK, honor, and PreKvK.
- `/kvk rankings type` is a required slash option with `kvk`, `honor`, `prekvk`, and `records` choices.
- `/kvk stats` keeps private account selection while posting selected single-account stats publicly.
- Legacy `/mykvkstats`, `/mykvktargets`, `/mykvkhistory`, `/kvk_rankings`,
  `/honor_rankings`, and `/prekvk report` paths remain live during rollout.
- No generated-card work, SQL/import/export/recompute behaviour, or Google Sheets contract changes
  were mixed into the scaffold.
- KVK targets service/DAL cleanup remains inside this programme and should be handled in the
  modern targets phase or a focused cleanup pack before that phase.
- Acclaim/contribution metrics remain inside this programme after source-of-truth validation.

### Phase 3 — Modern `/kvk stats` Visual Card

Status: complete. Delivered in mirror PR #142 and promoted to the production rollout branch.

Built the first modern KVK visual card for `/kvk stats`.

Delivered details:

- `/kvk stats` now uses a Pillow-generated visual card.
- `/mykvkstats` intentionally remains on the original legacy embed path so both outputs can run in parallel during validation and communication.
- The card established reusable card-generation primitives, KVK branding, metric tile patterns, asset handling, a renderer-independent payload contract, and tested fallback behaviour.
- Multiple registered governors route through the selected-account card posting path.
- `Main Card`, `More Stats`, and `History` buttons are available on the new `/kvk stats` output.
- SQL import, recompute, export, Google Sheets contracts, and KVK calculations were not changed.

### Phase 3B - Stats Card Polish and Secondary Cards

Status: complete. Delivered in mirror PR #143 and promoted to production.

Polished the delivered `/kvk stats` main card and extended the Phase 3 visual language to the
attached `More Stats` and `History` views.

Delivered details:

- Main-card compact stat values now use one decimal place.
- Card backgrounds are selected by KVK mode from `KVK_NAME`, with fallback/default handling.
- `Tides of War`, `Heroic Anthem`, `Storm of Stratagems`, and `Songs of Troy` card backgrounds are supported where assets exist.
- The main card rank marker uses the existing `KVK_RANK` value from the stats payload.
- The More Stats card shows `Overall KVK Rank` as `TBC` until Phase 3C provides a durable SQL-backed source.
- Kills and DKP progress ticks scale dynamically for high performers, including values around `225%`.
- `More Stats` and compact `History` are now Pillow-rendered secondary cards attached to `/kvk stats`.
- Matchmaking snapshot data is intentionally excluded from the compact History card.
- `/mykvkstats` remains legacy during parallel validation.

### Phase 3C - Overall KVK Rank Data Contract and Card Polish

Status: complete. Delivered in mirror PR #144 and pushed to production. Companion SQL PR #14 was
deployed and tested successfully before the bot rollout.

Delivered details:

- Added SQL-backed overall KVK rank data via `KVK.vw_Player_Overall_KVK_Rank`.
- The SQL contract exposes `overall_kvk_rank`, `overall_kvk_total_governors`, and
  `overall_kvk_top_percent`.
- Bot DAL/service/payload code reads the rank context through the KVK stats card layers, with a
  safe fallback when the SQL view is unavailable.
- More Stats now presents the rank context as:

```text
KVK Overall Rank
#41
Total 8.7k / Top 0.5%
```

- Main-card `Rank` remains sourced from existing `KVK_RANK`.
- Rank/title alignment was cleaned up on the main and More Stats cards.
- More Stats pass-window row values now use a shared fitted font size.
- Kills and DKP progress gold now share the same card gold.
- SQL review learnings were applied: the top-percent metric is named by meaning rather than as a
  conventional percentile, the DAL `TOP 1` lookup is deterministically ordered, and external SQL
  contract tests skip locally but fail in CI when the configured SQL file is missing.

### Phase 4A - Modern `/kvk targets`

Status: complete. Delivered in mirror PR #145 and promoted to production.

Applied the Phase 3 visual language to `/kvk targets` while preserving `/mykvktargets` as the
legacy output path.

Delivered details:

- Added renderer-independent target payload/model code.
- Added KVK target DAL/service/card-posting boundaries.
- Added a Pillow-rendered targets card with embed fallback.
- Matched the stats-card header, KVK-mode backgrounds, metric colours, footer freshness/state
  treatment, and performance-note style.
- Presented target values and Last KVK actual / target / percent comparisons in a clean 4-column
  grid.
- Kept Acclaim target as a `TBC` placeholder with next-KVK supporting copy.
- Preserved account selection, visibility, fallback behaviour, command registration, and legacy
  `/mykvktargets`.
- Added focused service, renderer, posting, and command tests.
- Ignored local `.codex_artifacts/` preview output.

Execution record:

`docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 4 Modern Targets and Full History.md`

### Phase 4B - Full `/kvk history` Audit, Optioneering, And Modern History Rollout

Status: complete. Phase 4B audit, optioneering, and all implementation sub-phases are delivered,
merged in mirror and production, pushed to production, and smoke tested successfully.
Phase 4Bi was delivered in mirror PR #148, smoke tested successfully, merged, and pushed to
production. Phase 4Bii completed the modern `/kvk history` Last 3 and Summary journey and has
also been promoted to production. Phase 4Biii added the Trends card journey, was smoke tested,
merged in both mirror and production, and deployed to production. Phase 4Biv removed the
command-level history selector inconsistency, polished CSV export data, was smoke tested, merged in
mirror and production, and pushed to production.

The full `/kvk history` / `/mykvkhistory` journey has completed audit and optioneering. The
approved staged direction is:

- `/kvk history` becomes the modern card-based past-performance and trend-analysis journey.
- `/mykvkhistory` remains the legacy graph/table/CSV journey during player validation.
- CSV export remains the deeper detail path.
- No `/kvk history_chart` command is added in Phase 4B.

Delivered Phase 4Bi details:

- Added renderer-independent KVK history payload models and service shaping.
- Added the expanded, null-preserving modern history DAL/export contract.
- Validated the existing SQL history source through `dbo.v_EXCEL_FOR_KVK_Started`.
- Prepared `/kvk history` for shared single-governor account picker flow and explicit
  `governor_id` lookup.
- Kept `/mykvkhistory` unchanged on the legacy chart/table/CSV path.
- Preserved and expanded CSV export for deeper history review.
- Included the three history card background assets:
  - `assets/kvk/cards/history_card1.PNG`
  - `assets/kvk/cards/history_card2.PNG`
  - `assets/kvk/cards/history_card3.PNG`
- Addressed review and smoke-test hardening, including exact BIGINT-safe parsing, no-account
  picker ephemeral consistency, and trimming SQL-padded governor names in display/export paths.

Delivered Phase 4Bii details:

- Built the modern `/kvk history` Last 3 KVK card using `history_card1.PNG`, with newest-started
  KVK first, the title `Last 3 KVKs`, card-native text styling, and a visual kills-trend indicator.
- Last 3 rows now show KVK, rank, kills, deads, healed, DKP, and acclaim. Missing or historically
  uncollected acclaim/healed values stay blank instead of displaying misleading zeroes.
- Moved and redesigned the compact stats History summary into `/kvk history` using
  `history_card2.PNG`.
- Summary now uses a 3x4 record layout: Highest Rank, Autarchs, KVK Played, Highest Acclaim; Most
  Kills, Most KillPoints, Most Deads, Most Heals; Most DKP, Lowest Tanking Score, Most Pre-KVK,
  and Most Honor.
- Summary record values include the KVK achieved in, and rankable records also include overall
  rank across all players/every KVK where available. Highest Rank, Autarchs, and KVK Played remain
  personal-context metrics without overall rank.
- Lowest Tanking Score is displayed as a percent and is calculated as
  `(HealedTroopsDelta * 20) / KillPointsDelta`, skipping rows where kill points or healed troops
  are missing or zero.
- Added modern History, Summary, and Export CSV controls for `/kvk history`.
- Hardened Summary/History button switching for ephemeral responses and deleted/missing host
  messages, and ensured export success/failure paths are user-visible.
- Removed the `History` button from `/kvk stats`, leaving `Main Card` and `More Stats`.
- Preserved `/mykvkhistory` on the legacy chart/table/CSV journey during validation.
- Completed the Codex Security diff scan with no reportable findings.

Delivered Phase 4Biii details:

- Built the `/kvk history` Trends card using `history_card3.PNG`.
- Added a `Trends` control alongside `History`, `Summary`, and `Export CSV`.
- Trends covers all collected KVK history, shows the count of KVKs with available data, and uses
  non-duplicative over-time signals rather than repeating the Last 3 rows or Summary grid.
- Final Trends metrics are Rank, Kills, Deads, Healed, DKP, Acclaim, KillPoints, and Tanking
  Score. Target-percent trend rows were intentionally removed because target changes over time can
  make the percentage trend misleading.
- Missing values remain missing rather than zero. Historically uncollected Acclaim and healed
  values remain blank unless confirmed as true data.
- Healed and Tanking Score both treat lower values as better.
- Trend direction compares against the same rounded/compact display precision shown on the card,
  so values that render the same, such as `1.1M to 1.1M`, display as `Flat`.
- The Last 3 History-card kills trend remains scoped to Last 3, while the Trends card uses the
  full collected history.
- No graph/table output was added to `/kvk history`; `/mykvkhistory` remains the legacy
  graph/table/CSV path during player validation.

Delivered Phase 4Biv details:

- Removed the `/kvk history` command-level ephemeral selector option, aligning the default
  registered-account path with `/kvk stats` and `/kvk targets`.
- Preserved explicit `/kvk history governor_id:<id>` lookup for admin, leadership, support, and
  direct inspection workflows.
- Preserved private account-selection/error handling where a private picker or private guidance is
  still needed, while selected/default single-account history output posts publicly.
- Preserved modern `History`, `Summary`, `Trends`, and `Export CSV` controls.
- Audited the deployed/current CSV export, local `HISTORY_EXPORT_COLUMNS`, and the sample
  `kvk_history (1).csv` that lacked healed and KillPoints data.
- Confirmed the export includes `HealedTroopsDelta`, `KillPointsDelta`, `Max_PreKvk_Points`, and
  `Max_HonorPoints`, and added derived `TankingScorePct` while preserving existing raw export
  column names.
- Preserved missing/null semantics so historically uncollected Acclaim and healed values remain
  blank/null rather than zero.
- Preserved `/mykvkhistory` unchanged as the legacy graph/table/CSV path.
- Addressed review feedback for private defer visibility before account-picker/error followups,
  vectorized `TankingScorePct` export calculation, and simplified redundant picker branching.
- Validation included focused command/export tests, the focused history suite, standard
  architecture/deferred/select-tests/smoke-imports/command-registration validators, pre-commit,
  full pytest, Codex Security review, and successful production smoke testing.

Use:

`docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 4B History Audit and Optioneering.md`

### Phase 5 — Unified `/kvk rankings` Visual/UX Polish

Status: in progress. Phase 5A and Phase 5B are complete, smoke tested, merged to mirror, promoted
through production, and pushed to production.

Phase 5A delivered the first rankings hub foundation:

- `/kvk rankings type:records` now exposes the KD98 Hall of Fame under the existing `/kvk rankings`
  command surface, with no new top-level command.
- Hall of Fame records show Top 10 all-time single-KVK performances, not lifetime totals.
- Supported first-release record metrics are Kills, KillPoints, Deads, DKP, Healed, Acclaim,
  Honor, and PreKvK where the existing history source returns qualifying values.
- Records allow the same governor to appear more than once when they hold multiple all-time
  performances.
- Records remain Top 10 only in the first release; there are no Top 25, Top 50, or Top 100 record
  controls.
- Missing/uncollected historical metrics are excluded by the SQL-backed DAL filter rather than
  displayed as misleading zero records.
- Shared ranking constants, payload models, Hall of Fame service/DAL boundaries, embed rendering,
  and view refresh/error handling were added under `kvk/` and `ui/views/`.
- KVK and Honor ranking primary controls now use the Top 10, Top 25, and Top 50 policy; Top 100 is
  not a primary player button.
- Legacy ranking commands remain live.

Phase 5B delivered the unified current-ranking browser foundation in mirror PR #153 and production
PR #462:

- `/kvk rankings type:kvk`, `honor`, and `prekvk` now use the shared ranking payload/service,
  unified embed renderer, and `CurrentRankingsBrowserView`.
- The public browser has mode and metric selectors plus Top 10, Top 25, and Top 50 controls.
- Top 100 remains out of the primary player controls.
- `/kvk rankings type:prekvk` now uses the unified public embed browser, while legacy
  `/prekvk report` remains the image-based report flow.
- `/kvk rankings type:records` remains the Phase 5A Hall of Fame Top 10 records mode and was not
  expanded to Top 25/50/100.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` remain live during rollout.
- Honor mode's stricter no-admin-override channel gate is enforced both at command entry and when
  switching modes inside the shared browser.
- KVK current-ranking output was smoke-polished to reuse the legacy fixed-width table budget so
  Top 10 rows stay one line per row in Discord.
- PreKvK unified output shows `Showing: Top N` instead of implying a full total when only a limited
  report payload is available.
- SQL/cache assumptions were validated against the SQL source repository, and Codex Security found
  no validated findings.

Phase 5C delivered the current KVK Top 10 visual ranking card in mirror PR #154 and production
PR #463:

- `/kvk rankings type:kvk` now has a generated Top 10 spotlight card for current KVK rankings.
- The card supports Kills, % Kill Target, Deads, DKP, Acclaim, and Tanking Score.
- Current KVK rankings now default to Kills.
- Power remains available for Top 25/50 compact browser analysis, but is not a Top 10 card metric.
- Tanking Score ranks lower scores first and requires positive KillPoints and positive healed
  troops, matching the history-card semantics.
- Top 25 and Top 50 remain compact embed/browser output.
- Renderer failures fall back to the unified embed output.
- Top 100 remains out of primary player controls.
- Records remain Top 10 only and continue to use the Phase 5A embed path until the records visual
  card sub-phase.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` remain live.
- Legacy `/prekvk report` remains image-based.
- Production smoke testing and visual polish are complete.

The next sub-phase is Phase 5D: add Hall of Fame records Top 10 visual cards while preserving the
stable current KVK card, Phase 5B unified browser, records Top 10-only policy, and all legacy
commands.

### Phase 6 — Admin Command Hardening And Legacy Operator Cleanup

Harden the delivered `/kvk_admin` operator command surface after Phase 2A.

This phase should preserve all permissions, channel restrictions, logging, and existing service/DAL ownership.

### Phase 7 — Legacy Command Deprecation and Removal

After a usage-review period:

1. announce new commands
2. change old commands to redirect/help responses
3. monitor usage
4. remove old paths only after approval

## 9. Likely Source Commands and Areas

### Player commands to audit

- `/mykvkstats`
- `/mykvktargets`
- `/mykvkhistory`
- `/mygovernorid`
- `/my_stats`
- `/my_stats_export`
- `/player_profile`
- `/player_stats`
- `/kvk_rankings`
- `/honor_rankings`
- PreKVK ranking/report commands

### Admin/operator commands to audit

- `/kvk_recompute`
- `/kvk_export_all`
- `/kvk_list_scans`
- `/kvk_window_preview`
- any KVK cache/diagnostic/import/export commands

### Likely modules to audit

- `commands/stats_cmds.py`
- `commands/registry_cmds.py`
- `commands/telemetry_cmds.py`
- `commands/calendar_cmds.py`
- `commands/events_cmds.py`
- `kvk/`
- `stats_alerts/`
- `gsheet_module.py`
- `target_utils.py`
- `governor_registry.py`
- `player_stats_cache.py`
- `ui/views/`
- `image_utils` / inventory image-generation modules if present
- command registration validation scripts

### SQL repo areas to validate

- KVK schema objects
- KVK export procedures
- KVK aggregate functions/views
- PreKVK and honor ranking objects
- player profile/latest stats views
- any cache-refresh dependencies

Validate against:

```text
C:\K98-bot-SQL-Server
```

## 10. Cross-Programme Constraints

- Do not remove old commands until explicitly approved.
- Do not change KVK import/recompute/export semantics during command scaffold work.
- Do not change Google Sheets tab names or spreadsheet contracts unless a specific phase approves it.
- Do not introduce Basic Data or summary-tab ingestion.
- Display Acclaim/contribution metrics only after metric naming and source-of-truth rules are approved and validated.
- Do not put SQL in command or view modules.
- Do not add a new top-level command group without command registration governance approval.
- Do not break existing KVK season workflows during active KVK.

## 11. Programme-Level Validation Strategy

Each implementation phase should include:

- command registration validation
- focused command tests
- permission tests
- output-shape tests
- service/DAL contract tests where touched
- SQL validation where SQL-backed contracts are changed or depended on
- architecture boundary validation
- deferred item validation
- screenshot or generated-image artifact review for visual phases

Baseline commands to consider:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

## 12. Programme Acceptance Criteria

The programme is complete when:

- players can use the new `/kvk` command group for stats, targets, history, and rankings
- KVK player outputs have a consistent modern style
- `/kvk stats` has a modern generated card output
- targets and history are visually aligned with the new style
- rankings are unified behind a coherent browser
- admin KVK commands are separated from player KVK commands
- Acclaim/contribution metrics are included where the approved SQL output contract supports them
- legacy commands are safely deprecated or removed after approval
- command registration validation remains green
- all data/SQL assumptions are validated against the SQL repo
- no new direct SQL exists in command/view layers
- documentation and command references are updated

## 13. Deferred / Future Opportunities

Do not include these in the early phases unless separately approved:

- full `/my` or `/player` global self-service redesign outside KVK
- full website implementation
- live web dashboard
- image-card generator shared across every bot feature
- advanced charting for historical KVK trends
- personalised recommendations based on remaining targets
- predictive “on track” modelling using scan cadence
- public player profile redesign outside KVK
- off-season stats redesign

## 14. Suggested Next Action

Proceed with:

```text
KVK Player Experience Redesign - Phase 5 Unified /kvk rankings Visual/UX Polish
```

Phase 1 audit/design, Phase 2A admin collision resolution, and Phase 2B player `/kvk` scaffold are
complete. Phase 3 has delivered the modern `/kvk stats` visual card while preserving the legacy
`/mykvkstats` embed during rollout. Phase 3B has polished the card, added KVK mode-specific
background selection, improved high-progress target scaling, and moved the attached `More Stats`
and `History` views to Pillow-rendered cards. Phase 3C has delivered the SQL-backed overall KVK
rank source, total-governor/top-percent context, rank alignment, progress-gold consistency, and
review hardening. Phase 4A has delivered modern `/kvk targets` in PR #145 and promoted it to
production. Phase 4B audit and optioneering are complete, and Phase 4Bi has delivered the
history payload/data-contract/picker/export foundation in PR #148, smoke tested and pushed to
production. Phase 4Bii has implemented the modern `/kvk history` Last 3 card, moved the compact
history summary into `/kvk history`, added the expanded Summary records/ranks/tanking-score model,
blanked historically uncollected acclaim/healed values, removed the History button from
`/kvk stats`, and has been merged and pushed to production. Phase 4Biii has delivered the Trends
card, added Trends switching, clarified all-history trend scope with KVK count, removed confusing
target-percent trend rows, and deployed to production after smoke testing. Phase 4Biv has removed
the stale command-level selector option, preserved explicit governor lookup, polished CSV export
with healed, KillPoints, PreKVK, Honor, and derived `TankingScorePct` data, preserved null
semantics, and passed production smoke testing. Phase 4 is complete. Phase 5A has delivered the
`/kvk rankings type:records` Hall of Fame foundation and pushed it to production after smoke
testing. Phase 5B has delivered the unified current-ranking browser in mirror PR #153 and
production PR #462, passed production smoke testing, and preserved the legacy ranking paths.
Phase 5C has delivered the current KVK Top 10 visual ranking card in mirror PR #154 and production
PR #463, including Kills default, KVK card metrics for Kills, % Kill Target, Deads, DKP, Acclaim,
and Tanking Score, embed fallback, Top 25/50 compact browser preservation, Top 100 exclusion,
legacy command preservation, production smoke testing, and visual polish. Start the next chat from
the Phase 5D starter:

`docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5D Hall of Fame Records Visual Cards.md`
