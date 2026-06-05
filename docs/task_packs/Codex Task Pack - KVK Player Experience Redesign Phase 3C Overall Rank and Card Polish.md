# Codex Task Pack - KVK Player Experience Redesign Phase 3C Overall Rank and Card Polish

## 1. Task Header

- Task name: `KVK Player Experience Redesign - Phase 3C Overall Rank and Card Polish`
- Date: `2026-06-05`
- Owner/context: `K98 Bot KVK Player Experience Redesign programme after Phase 3B production rollout`
- Task type: `feature / SQL data contract / generated image renderer polish / data-source audit`
- One-pass approved: `no`
- Status: `ready for task execution`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`.

Also read:

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3 Modern mykvkstats Visual Card.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3B Stats Card Polish and Secondary Cards.md`
- `docs/reference/canonical_command_reference.md` if command output descriptions or command-surface validation are touched

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

```text
C:\K98-bot-SQL-Server
```

## 3. Objective

Replace the More Stats card's temporary `Overall KVK Rank: TBC` placeholder with a durable SQL-backed rank derived from `KVK.KVK_Player_Windowed`, then polish the remaining Phase 3B visual issues.

This phase should add the missing overall-rank data contract in the SQL repo, retrieve that value through the bot DAL/service layers, populate the More Stats card, make More Stats typography consistent, and audit the History card acclaim discrepancy before agreeing any data or formatting fix.

## 4. Background

Phase 3B delivered the modern More Stats and History Pillow cards. During final production review, the rank semantics were clarified:

- Main-card `Rank` should use existing `KVK_RANK`; this is the KVK rank for our kingdom.
- More Stats needs an `Overall KVK Rank`, but no direct DB column currently exists.
- The desired overall rank can be derived from `KVK.KVK_Player_Windowed` for the current KVK where `WindowName = 'Full'`, ordered by `kp_gain_recalc DESC`.
- Phase 3B therefore shipped `Overall KVK Rank` as `TBC` and split durable data work into this Phase 3C task.

Two additional visual/data issues were observed from production screenshots:

- More Stats values use inconsistent fitted font sizes in the same row, especially Pass 4 versus Pass 6.
- History card `Highest Acclaim` and `Last KVK Acclaim` can display different rounded values even when the last KVK acclaim appears to be the governor's highest acclaim. Example: GovernorID `4677418` has `STATS_FOR_UPLOAD.HighestAcclaim = 4744606`, which should display as `4.7M`, while the screenshot shows `Last KVK Acclaim = 4.6M`.

## 5. Scope

### In Scope

- Audit the current Phase 3B `/kvk stats` card payload, renderer, DAL, and cache/source flow.
- Create a SQL view in `C:\K98-bot-SQL-Server` that derives overall KVK rank from `KVK.KVK_Player_Windowed`.
- Use `WindowName = 'Full'` for overall rank.
- Rank by `kp_gain_recalc DESC` and use a deterministic tie-breaker such as `governor_id ASC`.
- Retrieve the overall rank through bot DAL/service code; do not query SQL from commands, views, or renderers.
- Add an optional payload field for overall KVK rank.
- Populate the More Stats card top-right `Overall KVK Rank` value when available.
- Preserve the Phase 3B `TBC` or clear fallback when the view/value is missing.
- Keep main-card `Rank` sourced from existing `KVK_RANK`.
- Make More Stats card row typography consistent, especially pass-window values.
- Audit and document the `Highest Acclaim` versus `Last KVK Acclaim` data-source discrepancy.
- Implement an acclaim fix only if the audit identifies a low-risk source/formatting correction and the operator approves it.
- Add or update SQL, DAL/service, renderer, and view tests as appropriate.
- Generate updated visual review samples for main, More Stats, and History where relevant.

### Out of Scope

- No new slash commands or command groups.
- No removal or deprecation of `/mykvkstats` or other legacy paths.
- No changes to KVK import/recompute/export semantics unless explicitly required for the approved SQL view.
- No mutation of `KVK.KVK_Player_Windowed` table shape unless the SQL audit proves a view is insufficient and the operator separately approves table changes.
- No broad History card redesign or full `/kvk history` redesign.
- No website implementation.
- No predictive "on track" modelling.
- No direct SQL in command modules, Discord views, or renderers.

## 6. Source Deferred Items

This task is a planned programme sub-phase, not a deferred optimisation batch.

If audit finds out-of-scope debt, capture it in `docs/reference/deferred_optimisations.md` using the required structure:

```md
### Deferred Optimisation
- Area:
- Type: performance | architecture | cleanup | refactor | consistency
- Description:
- Suggested Fix:
- Impact: low | medium | high
- Risk: low | medium | high
- Dependencies:
```

## 7. Codex Skills To Use

### Skill Decisions

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation to keep SQL, DAL, service, renderer, and tests properly layered. |
| `k98-discord-command-feature` | use | Required because `/kvk stats` button-attached cards and user-visible Discord output are touched. |
| `k98-sql-validation` | use | Required because this phase creates a SQL view and changes the bot's SQL-backed card payload contract. |
| `k98-test-selection` | use | Required before validation to select SQL contract, payload, renderer, and view tests. |
| `k98-deferred-optimisation-capture` | use if needed | Required if audit finds broader renderer, cache, SQL, or history-source debt. |
| `k98-pr-review` | use | Required before PR handoff. |
| `k98-promotion-check` | use | Required before SQL/bot production promotion or bot-machine deployment. |
| `codex-security:security-scan` | use | Required before PR handoff because SQL/data access, Discord interactions, and generated image output are touched. |

## 8. Mandatory Workflow

1. Audit and scope the Phase 3C work, then stop for approval.
2. Validate SQL source objects in `C:\K98-bot-SQL-Server`.
3. Propose the SQL view name, columns, indexes/dependencies, and deployment order, then stop for approval.
4. Propose the bot DAL/service/payload/renderer implementation plan, then stop for approval.
5. Implement the approved SQL view and bot code.
6. Add/update tests.
7. Generate visual review artifacts.
8. Run focused validation and selected broader validation.
9. Run Codex Security review before PR handoff.
10. Prepare promotion notes that cover SQL deployment order before bot rollout.

Proceed in one pass only if the operator explicitly approves one-pass implementation.

## 9. Audit Requirements

Review and document:

- current `/kvk stats` posting path
- current Phase 3B payload fields for `kvk_rank`, `kingdom_rank`, and More Stats rank display
- current SQL source for `KVK.KVK_Player_Windowed`
- whether `kp_gain_recalc` is the approved ranking metric for overall KVK rank
- whether `WindowName = 'Full'` is unique enough for one row per `KVK_NO`/`governor_id`
- how ties should be handled for stable rank output
- whether `KVK_NO` should be passed from the current stats row or resolved from `ProcConfig`
- current data freshness behaviour for `KVK_Player_Windowed` versus `STATS_FOR_UPLOAD`
- current `kvk_stats_card_dal.fetch_kvk_stats_card_context` query pattern
- current `KvkStatsCardPayload` and renderer fallback behaviour
- current More Stats font fitting behaviour and why same-row values use inconsistent sizes
- current History card `Highest Acclaim` source from `STATS_FOR_UPLOAD`
- current `last_kvk_summary` source, likely `player_stats_cache.lastkvk` built from `EXCEL_FOR_KVK_<N>`
- raw acclaim values for GovernorID `4677418` across `STATS_FOR_UPLOAD`, the last KVK cache/source table, and any view/procedure used by history summaries
- whether the acclaim discrepancy is a rounding issue, stale/source mismatch, or legitimately different source value
- existing renderer tests and visual artifact patterns

## 10. Architecture Targets

| Concern | Target |
|---|---|
| SQL schema | SQL repo: `C:\K98-bot-SQL-Server\sql_schema\KVK.<ViewName>.View.sql` |
| Bot DAL | `kvk/dal/kvk_stats_card_dal.py` |
| Service/payload | `kvk/services/kvk_stats_card_service.py`, `kvk/models/kvk_stats_card.py` |
| Renderer | `kvk/rendering/kvk_stats_card_renderer.py` |
| Views/buttons | Existing `ui/views/kvk_stats_card_views.py` only if fallback output changes |
| Commands | No command changes expected |
| Tests | Existing KVK stats card tests under `tests/` plus SQL/DAL-focused tests where practical |
| Docs | Programme/task-pack updates only unless command output descriptions change |

## 11. Likely Files

### Review

- `commands/kvk_stats_card_posting.py`
- `commands/kvk_cmds.py`
- `kvk/dal/kvk_stats_card_dal.py`
- `kvk/models/kvk_stats_card.py`
- `kvk/services/kvk_stats_card_service.py`
- `kvk/rendering/kvk_stats_card_renderer.py`
- `ui/views/kvk_stats_card_views.py`
- `player_stats_cache.py`
- `stats_cache_helpers.py`
- `utils.py`
- SQL repo: `sql_schema/KVK.KVK_Player_Windowed.Table.sql`
- SQL repo: `sql_schema/KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql`
- SQL repo objects for `STATS_FOR_UPLOAD`, `SP_Stats_for_Upload`, and `EXCEL_FOR_KVK_<N>`

### Modify

- SQL repo: add `sql_schema/KVK.vw_Player_Overall_KVK_Rank.View.sql` or an approved equivalent name
- `kvk/dal/kvk_stats_card_dal.py`
- `kvk/models/kvk_stats_card.py`
- `kvk/services/kvk_stats_card_service.py`
- `kvk/rendering/kvk_stats_card_renderer.py`
- focused KVK stats card tests
- programme/task-pack docs if implementation changes the approved plan

### Create

- SQL repo view file for the overall KVK rank.
- Optional bot test file only if existing KVK stats card test files become crowded.

## 12. Implementation Requirements

### 12.1 Overall KVK Rank SQL View

Create a SQL view rather than adding a physical column to `KVK.KVK_Player_Windowed` unless audit proves a view is unsuitable.

Proposed view shape:

```sql
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE OR ALTER VIEW [KVK].[vw_Player_Overall_KVK_Rank]
AS
SELECT
    p.KVK_NO,
    p.WindowName,
    p.governor_id,
    p.name,
    p.kingdom,
    p.campid,
    p.kp_gain_recalc,
    ROW_NUMBER() OVER (
        PARTITION BY p.KVK_NO, p.WindowName
        ORDER BY p.kp_gain_recalc DESC, p.governor_id ASC
    ) AS overall_kvk_rank,
    p.last_scan_id,
    p.computed_at_utc
FROM KVK.KVK_Player_Windowed AS p
WHERE p.WindowName = N'Full';
```

Audit before finalising:

- whether `kp_gain_recalc` can be null and should sort last
- whether `governor_id ASC` is the approved tie-breaker
- whether the view should filter `WindowName = N'Full'` internally or expose all windows
- whether duplicate rows can exist for one `KVK_NO`/`WindowName`/`governor_id`
- whether an index already supports `KVK_NO`, `WindowName`, `kp_gain_recalc`, and `governor_id`

### 12.2 Bot Retrieval And Payload

- Add a DAL helper or extend `fetch_kvk_stats_card_context` to retrieve `overall_kvk_rank`.
- Query by `KVK_NO`, `governor_id`, and `WindowName = 'Full'`.
- Do not add SQL to commands, views, or renderers.
- Add `overall_kvk_rank: int | str | None` to the stats card context/payload as appropriate.
- Preserve existing `kvk_rank` from `KVK_RANK`; this remains the main-card rank.
- Preserve `kingdom_rank`/`Rank` only if it is still useful elsewhere; do not use it for either card rank unless separately approved.
- If the view or value is unavailable, keep More Stats display safe with `TBC` or `N/A` according to the approved copy.

### 12.3 More Stats Card Rank Display

- Replace the Phase 3B top-right placeholder with the SQL-backed overall rank when available.
- Keep the label clear, for example `Overall KVK Rank`.
- Keep trophy/rank styling consistent with the main card.
- If no value exists, display `TBC` rather than a misleading fallback to `KVK_RANK` or `Rank`.

### 12.4 More Stats Font Consistency

Audit and fix inconsistent row typography on the More Stats card.

Observed issue:

- Pass 4 value `14.3M / 1.1M` and Pass 6 value `4.6M / 0` can render with visibly different font sizes in the same row.

Requirements:

- Same-row metric values should use consistent typography unless a value would otherwise clip.
- Prefer a row-level fitted font size for pass-window values instead of fitting each metric independently.
- Keep labels, values, and sublabels readable at Discord desktop and mobile-like sizes.
- Add a focused renderer/helper test where practical and include visual sample review.

### 12.5 History Acclaim Discrepancy Audit

Audit before changing behaviour.

Known example:

- GovernorID: `4677418`
- `dbo.STATS_FOR_UPLOAD.HighestAcclaim`: `4744606`
- Expected compact display for that raw value: `4.7M`
- Production screenshot shows `Highest Acclaim = 4.7M` and `Last KVK Acclaim = 4.6M`, even though the last KVK appears to be the highest acclaim event for this governor.

Audit questions:

- What raw source populates `history_summary["Highest Acclaim"]`?
- What raw source populates `last_kvk_summary["Acclaim"]`?
- Is the last KVK source the prior `EXCEL_FOR_KVK_<N>` table, `v_EXCEL_FOR_KVK_All`, `player_stats_cache.lastkvk`, or another cached/derived object?
- Are the two raw values actually different?
- If different, is that expected because current highest acclaim is from current KVK, last finished KVK, or a different KVK?
- If the raw values match, is a formatter discrepancy causing one-decimal display drift?
- Should History card display `Last KVK Acclaim`, `Highest Acclaim`, or both with clearer labels?

Do not silently force the last KVK acclaim value from `HighestAcclaim`. Produce the source analysis and recommended fix first.

### 12.6 Command Surface Governance

- [ ] No new top-level command.
- [ ] No new grouped subcommand.
- [ ] Preserve `/kvk stats` registration and legacy `/mykvkstats`.
- [ ] Preserve decorators, permissions, response visibility, usage tracking, and command-cache behaviour.
- [ ] Run or justify skipping `scripts/validate_command_registration.py`.

## 13. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| Overall KVK Rank missing from SQL output contract | fix now | Required to replace the More Stats `TBC` placeholder without guessing in Python. |
| Physical rank column on `KVK_Player_Windowed` | defer unless view is insufficient | A view is lower impact and avoids table-shape downstream risk. |
| More Stats same-row font inconsistency | fix now | Visible production polish issue. |
| History acclaim source discrepancy | audit first | Need source-of-truth evidence before changing display or data logic. |
| Main-card `Rank` semantics | not applicable | Phase 3B clarified and fixed this to use existing `KVK_RANK`. |
| Broader `/kvk history` redesign | defer | Phase 3C only audits the compact History card discrepancy. |

Add further rows based on actual findings.

## 14. Testing Requirements

Cover or justify:

- SQL view returns one row per `KVK_NO`/`WindowName = Full`/`governor_id`
- SQL view ranks by `kp_gain_recalc DESC`
- SQL view rank tie-breaker is deterministic
- DAL returns `overall_kvk_rank` for a known row
- DAL handles missing view/value safely
- payload includes `overall_kvk_rank`
- main-card rank still uses `KVK_RANK`
- More Stats card displays SQL-backed overall rank when present
- More Stats card displays `TBC` or approved fallback when rank is missing
- More Stats pass-window typography is visually consistent
- History acclaim source audit has documented raw values for GovernorID `4677418`
- any approved acclaim fix has regression tests
- command registration unchanged

Suggested focused tests, adapt to actual files:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_payload.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_renderer.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_posting.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_theme.py
```

Suggested validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

SQL validation in `C:\K98-bot-SQL-Server`:

```powershell
rg "KVK_Player_Windowed|kp_gain_recalc|WindowName" C:\K98-bot-SQL-Server\sql_schema
rg "vw_Player_Overall_KVK_Rank" C:\K98-bot-SQL-Server\sql_schema
```

Example DB verification query after SQL deployment:

```sql
SELECT TOP (20)
    KVK_NO,
    WindowName,
    governor_id,
    name,
    kingdom,
    kp_gain_recalc,
    overall_kvk_rank
FROM KVK.vw_Player_Overall_KVK_Rank
WHERE KVK_NO = 15
ORDER BY overall_kvk_rank ASC;
```

Visual validation:

- Generate updated `More Stats` sample showing a real overall rank.
- Generate updated `More Stats` sample with missing rank fallback.
- Generate updated `History` sample for GovernorID `4677418` if test data permits.
- Inspect Discord desktop and mobile-like sizes for label clipping, font mismatch, and value readability.

## 15. Acceptance Criteria

- [ ] Scope is confirmed before implementation.
- [ ] SQL source objects are validated against `C:\K98-bot-SQL-Server`.
- [ ] A SQL view derives overall KVK rank from `KVK.KVK_Player_Windowed`.
- [ ] Rank ordering uses `kp_gain_recalc DESC` and a deterministic tie-breaker.
- [ ] Bot code retrieves overall KVK rank through DAL/service layers.
- [ ] More Stats card displays the derived overall KVK rank when available.
- [ ] More Stats card keeps a safe placeholder when rank is unavailable.
- [ ] Main-card rank remains sourced from existing `KVK_RANK`.
- [ ] More Stats same-row font sizing is consistent and visually reviewed.
- [ ] History acclaim discrepancy is audited with raw source values and a recommended fix.
- [ ] Any approved acclaim fix is implemented with regression coverage.
- [ ] No direct SQL is added to commands, views, or renderers.
- [ ] Existing command registration, permissions, response visibility, and fallback behaviour are preserved.
- [ ] Focused tests pass.
- [ ] SQL validation evidence is documented.
- [ ] Visual review artifacts are generated.
- [ ] Codex Security review is run before PR handoff or explicitly justified.
- [ ] SQL deployment order and rollback notes are documented.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. SQL Validation Evidence
7. Command Surface Changes
8. User-Visible Behaviour Changes
9. Data Contract / Payload Summary
10. Renderer Summary
11. Helpers Reused
12. Refactor Findings
13. Test Plan and Results
14. Visual Review Evidence
15. AI Review Gates
16. Deployment Steps
17. Rollback Plan
18. Deferred Optimisations

## 17. PR Summary Template

```md
## Summary

- Added SQL-backed overall KVK rank support for the More Stats card.
- Polished More Stats typography consistency.
- Audited the History card acclaim source discrepancy and implemented the approved fix, if applicable.

## Changes

- Added `KVK.vw_Player_Overall_KVK_Rank` in the SQL repo.
- Added DAL/service/payload support for overall KVK rank.
- Updated More Stats rendering to show the derived overall rank.
- Updated renderer tests and visual samples.

## SQL Changes

- New view: `<view name>`.
- Deployment order: SQL view before bot code using it.

## Tests

- `<commands/results>`

## Visual Review

- `<sample paths/results>`

## AI Review Gates

- Codex Security: `<run/skipped with reason>`

## Risk / Rollback

- Risk: SQL view or rank semantics mismatch could show misleading overall rank.
- Mitigation: SQL validation, deterministic ordering, fallback display, focused renderer/payload tests.
- Rollback: deploy previous bot code or keep More Stats fallback as `TBC`; SQL view can remain unused or be dropped if necessary.
```

## 18. Codex Chat Starter

```text
Codex, start Phase 3C of the KVK Player Experience Redesign: Overall Rank and Card Polish.

Phase 3B is complete, merged, and promoted to production. The More Stats card currently shows Overall KVK Rank as TBC because no durable SQL-backed source existed in Phase 3B.

Before implementation, read:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/KVK Player Experience Redesign - Programme Pack.md
- docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3B Stats Card Polish and Secondary Cards.md
- this Phase 3C task pack

Use the K98 repo workflow and required skills. First audit the SQL source and propose the view contract before coding.

Overall rank requirement:
- create a SQL view over KVK.KVK_Player_Windowed
- use KVK_NO for the current KVK
- use WindowName = Full
- rank by kp_gain_recalc DESC with deterministic tie-breaker
- retrieve the value through bot DAL/service code
- populate the More Stats card Overall KVK Rank
- keep main card Rank sourced from KVK_RANK

Card polish requirements:
- make More Stats same-row font sizes consistent, especially Pass 4 vs Pass 6 values
- audit the History Highest Acclaim vs Last KVK Acclaim discrepancy for GovernorID 4677418 before agreeing the fix

Do not add direct SQL to commands, views, or renderers. Do not change KVK import/recompute/export semantics or legacy command rollout behaviour unless separately approved.
```
