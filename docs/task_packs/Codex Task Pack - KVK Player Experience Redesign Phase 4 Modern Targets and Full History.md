# Codex Task Pack - KVK Player Experience Redesign Phase 4 Modern Targets and Full History

## 1. Task Header

- Task name: `KVK Player Experience Redesign - Phase 4 Modern Targets and Full History`
- Date: `2026-06-05`
- Owner/context: `K98 Bot KVK Player Experience Redesign programme after Phase 3C production rollout`
- Task type: `feature / UX redesign / generated image renderer / Discord interaction polish / service-DAL cleanup`
- One-pass approved: `no`
- Status: `complete - Phase 4A targets optimisation delivered in mirror PR #145 and promoted to production; history work moved to Phase 4B, with Phase 4Bi/4Bii/4Biii now delivered and Phase 4Biv remaining`

### Phase Split Update

Implementation was split after the initial audit:

- Phase 4A: fully optimise `/kvk targets` first, including target service/DAL/payload cleanup,
  modern generated target card output, clear progress/remaining-work states, and tested fallback
  behaviour. This is complete.
- Phase 4B: full `/kvk history` redesign was scoped separately. Phase 4Bi delivered the
  renderer-independent history payload/data/export foundation in PR #148. Phase 4Bii delivered the
  modern Last 3 and Summary cards and has been merged/pushed to production. Phase 4Biii delivered
  the Trends card and final visual/metric polish. Phase 4Biv remains for selector removal and CSV
  export polish.

Legacy `/mykvktargets` and `/mykvkhistory` remain live. `/kvk history` is now the modern
card-based history journey, while `/mykvkhistory` remains the legacy graph/table/CSV journey for
player comparison.

Do not continue history work from this combined Phase 4 pack. Use:

`docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 4B History Audit and Optioneering.md`

### Phase 4A Delivery Update

Phase 4A was completed in mirror PR #145 and promoted to production.

Delivered user-facing behaviour:

- `/kvk targets` now renders a modern generated targets card aligned with the Phase 3 stats-card
  visual language.
- `/mykvktargets` remains on the legacy output path for parallel rollout.
- The targets card uses the same mode-specific KVK background approach as the stats and secondary
  cards.
- Header layout now matches the stats card pattern: KVK context, camp where available, MM power,
  Discord avatar, governor name, and Governor ID.
- The card presents a clean 4-column target row and 4-column Last KVK comparison row.
- Kills, deads, DKP, and acclaim use the shared stats-card colour language: green, red, purple,
  and gold.
- Acclaim target is a placeholder until acclaim targets exist; it displays `TBC` plus supporting
  copy.
- Last KVK comparison values use actual / target / percent where targets exist.
- The Last KVK note uses performance-aware copy and colours only the note body by outcome.
- Footer shows target refresh time and source state.

Delivered architecture:

- Added renderer-independent target payload/model code.
- Added target DAL/service boundaries for card output.
- Kept command code thin and preserved fallback behaviour.
- Added generated-card rendering with embed fallback.
- Kept `/mykvktargets` live and unchanged.
- Added focused service, renderer, posting, and command tests.
- Ignored local `.codex_artifacts/` generated preview output.

Validated delivery:

- Focused target tests passed.
- Full test suite passed during PR validation.
- Pre-commit, architecture validation, deferred-item validation, smoke imports, and command
  registration validation passed.

Still to do:

- Phase 4Biii: add the `/kvk history` Trends card using `history_card3.PNG` and polish the final
  modern history navigation.
- Preserve the delivered Phase 4Bii baseline: Last 3 card, redesigned Summary card, blank
  handling for historically uncollected Acclaim/healed values, overall Summary ranks, and the
  delivered tanking-score formula.
- Keep `/mykvkhistory` as the legacy graph/table/CSV path unless a later phase explicitly changes
  that rollout decision.

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by
`docs/reference/README.md`.

Also read:

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/task_packs/KVK Player Experience Redesign - Phase 1 Audit and Design Report.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3 Modern mykvkstats Visual Card.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3B Stats Card Polish and Secondary Cards.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3C Overall Rank and Card Polish.md`
- `docs/reference/canonical_command_reference.md` if command output descriptions or command-surface validation are touched

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

```text
C:\K98-bot-SQL-Server
```

## 3. Objective

Modernise the full `/kvk targets` and `/kvk history` player journeys so they visually and
architecturally align with the completed Phase 3 stats-card experience.

Targets should quickly answer "what do I need to do next?" with progress, remaining work, target
state, and clear explanations for missing or exempt targets. Full history should help players
compare KVK performance over time without losing the accessibility and data density of the current
history command.

## 4. Background

Phase 1 identified `/mykvktargets` and `/mykvkhistory` as core KVK player journeys that should be
available under the new `/kvk` player command group. Phase 2B scaffolded `/kvk targets` and
`/kvk history` while preserving legacy commands. Phase 3 through Phase 3C then built the modern
visual-card language for `/kvk stats`, including:

- renderer-independent payload models
- Pillow cards with embed fallback
- mode-specific KVK backgrounds
- thin view callbacks and off-thread rendering
- SQL-backed rank context through DAL/service layers
- review hardening around SQL naming, deterministic ordering, and external SQL contract tests

Phase 4 should apply those lessons to targets and full history. In particular, the Phase 1 audit
called out `target_utils.py` as mixed responsibility code that combines SQL-backed lookup/fallback
logic with Discord response helpers. Phase 4 should introduce a clear target payload/service/DAL
boundary before rendering, rather than copying that shape into new cards.

## 5. Scope

### In Scope

- Audit current `/kvk targets`, `/mykvktargets`, `/kvk history`, and `/mykvkhistory` paths.
- Preserve legacy flat commands during rollout.
- Preserve existing command permissions, channel restrictions, response visibility, account
  selection, and fallback behaviour.
- Define a renderer-independent KVK targets payload contract.
- Move or wrap target data access behind service/DAL boundaries where required for the visual
  output.
- Modernise `/kvk targets` output using a generated card or embed+image hybrid, depending on audit
  findings and data density.
- Show target progress, remaining work, completion state, exempt/no-target explanations, and next
  action copy clearly.
- Review and modernise the full `/kvk history` output.
- Decide deliberately whether full history should stay table-first, become a generated card, or use
  a hybrid summary card plus detailed table/export.
- Preserve the compact stats-card History button from Phase 3B/3C unless a direct integration fix is
  required.
- Reuse Phase 3 visual primitives and formatting where appropriate.
- Add or update focused tests for target payload/service, renderer/fallback, history output shape,
  and command/view behaviour.
- Generate visual review samples when any card/image output changes.
- Update programme/task-pack docs with the delivered Phase 4 outcome.

### Out of Scope

- No removal, redirect, or deprecation of legacy `/mykvktargets` or `/mykvkhistory`.
- No redesign of `/kvk rankings`; that remains Phase 5.
- No new top-level command group.
- No changes to KVK import, recompute, export, Google Sheets tab names, or scheduled cache refresh
  semantics unless a defect is found and separately approved.
- No predictive "on track" modelling based on scan cadence unless explicitly approved.
- No website implementation.
- No direct SQL in command modules, Discord views, or renderers.
- No broad player-profile or global `/my` redesign.

## 6. Source Deferred Items

This task is a planned programme phase, not a standalone deferred optimisation batch.

Known programme finding to address or explicitly defer:

```md
### Deferred Optimisation
- Area: target_utils.py / KVK targets command path
- Type: architecture
- Description: Current targets lookup/output flow mixes SQL-backed lookup/fallback logic with Discord response helpers, making it awkward to build modern renderer-independent target payloads.
- Suggested Fix: Introduce KVK target DAL/service payload boundaries and keep Discord rendering/view code thin before modernising `/kvk targets`.
- Impact: medium
- Risk: medium
- Dependencies: SQL target-source validation in `C:\K98-bot-SQL-Server`
```

If audit finds additional out-of-scope debt, capture it in
`docs/reference/deferred_optimisations.md` using the required structured format.

## 7. Codex Skills To Use

### Skill Decisions

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation to scope command, service, DAL, renderer, history, SQL, and fallback boundaries. |
| `k98-discord-command-feature` | use | Required because `/kvk targets`, `/kvk history`, legacy paths, embeds/cards, and interaction flow are touched. |
| `k98-sql-validation` | use | Required because target and history data are SQL-backed and the target source contract must not be inferred from Python alone. |
| `k98-test-selection` | use | Required before validation to choose focused target/history, renderer, command, and regression tests. |
| `k98-deferred-optimisation-capture` | use if needed | Required if audit finds larger service/DAL, cache, history, or target cleanup outside the approved Phase 4 scope. |
| `k98-pr-review` | use | Required before PR handoff. |
| `k98-promotion-check` | use | Required before production promotion or bot-machine deployment. |
| `codex-security:security-scan` | use | Required before PR handoff if implementation touches SQL/data access, Discord interactions, generated files, user-controlled input, or restart-sensitive persistence. |

## 8. Mandatory Workflow

1. Audit and scope `/kvk targets`, `/mykvktargets`, `/kvk history`, and `/mykvkhistory`, then stop
   for approval.
2. Validate target and history SQL/source contracts against `C:\K98-bot-SQL-Server`.
3. Propose the Phase 4 split:
   - whether targets and full history fit in one PR
   - whether full history should be card, table-first, or hybrid
   - what target service/DAL cleanup is required before rendering
4. Stop for approval before implementation.
5. Implement the approved target/history payload, renderer/view, and fallback changes.
6. Add or update tests.
7. Generate visual review artifacts if any generated output changes.
8. Run focused validation and selected broader validation.
9. Run or document the Codex Security review gate.
10. Prepare PR and promotion notes.

Proceed in one pass only if the operator explicitly approves one-pass implementation.

## 9. Audit Requirements

Review and document:

- current `/kvk targets` command path
- current `/mykvktargets` command path
- current `/kvk history` command path
- current `/mykvkhistory` command path
- current account selection and `only_me` / ephemeral visibility behaviour
- current target lookup flow, likely including `target_utils.py`, `targets_sql_cache.py`, and
  `targets_embed.py`
- current target empty states: no target, exempt, off-season, below power, missing governor, not in
  matchmaking, stale cache, or SQL/cache failure
- current target data fields: kills, deads, DKP, targets, percent complete, remaining amount, KVK
  number/context, and target exemption state
- SQL repo objects that define target tables/views/procedures, including `CURRENT_TARGETS`,
  `EXEMPT_FROM_STATS`, and KVK target export/output objects
- current history service/DAL path, likely `services.kvk_history_service`,
  `kvk/dal/kvk_history_dal.py`, `kvk_history_utils.py`, and `ui/views/kvk_history_view.py`
- current full-history table/chart/image/CSV behaviour
- current compact stats-card History button behaviour from Phase 3B/3C and whether it shares any
  source with the full history command
- whether History card `Highest Acclaim` versus `Last KVK Acclaim` wording needs clearer labels in
  the full history command
- existing image renderer helpers and Phase 3 KVK card primitives to reuse
- existing tests for target lookup, target embeds, history service/DAL, history views, and command
  registration
- direct SQL in command/view paths or mixed responsibilities that should be fixed now or captured
  as deferred debt

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | Existing `commands/kvk_cmds.py`, `commands/telemetry_cmds.py`, and `commands/stats_cmds.py` only as needed. Do not create new command groups. |
| Target service/payload | New or existing KVK target service module returning dataclasses independent of Discord and Pillow. |
| Target DAL | `kvk/dal/` or an existing target DAL/cache module; no SQL in commands/views/renderers. |
| History service/payload | Existing history service/DAL where possible, with renderer-independent payload additions if needed. |
| Views/buttons | `ui/views/` modules should own interaction flow only. |
| Renderer | Reuse or extend KVK/PreKVK/Pillow renderer patterns; keep SQL and Discord types out of renderers. |
| Assets | `assets/kvk/cards/` where visual output uses KVK card backgrounds. |
| Tests | Focused tests under `tests/` for target payload/service, renderer, history output, fallback, and command/view behaviour. |
| Docs | Programme/task-pack docs and canonical command reference only if visible command descriptions change. |

## 11. Likely Files

### Review

- `commands/kvk_cmds.py`
- `commands/telemetry_cmds.py`
- `commands/stats_cmds.py`
- `target_utils.py`
- `targets_sql_cache.py`
- `targets_embed.py`
- `kvk_state.py`
- `services/kvk_history_service.py`
- `kvk/dal/kvk_history_dal.py`
- `kvk_history_utils.py`
- `ui/views/kvk_history_view.py`
- `ui/views/kvk_stats_card_views.py`
- `kvk/rendering/kvk_stats_card_renderer.py`
- `kvk/models/kvk_stats_card.py`
- `kvk/services/kvk_stats_card_service.py`
- existing target/history tests
- SQL repo target and history source objects

### Modify

Exact files should be decided after audit, but likely:

- target service/DAL or cache adapter modules
- target embed/card renderer modules
- `commands/kvk_cmds.py` if `/kvk targets` or `/kvk history` wiring changes
- legacy command modules only if needed to preserve parallel rollout/fallback
- history service/view modules where full-history output changes
- focused tests for target/history behaviour and renderer output
- programme/task-pack docs after delivery

### Create

Potentially:

- `kvk/models/kvk_targets_card.py`
- `kvk/services/kvk_targets_card_service.py`
- `kvk/dal/kvk_targets_dal.py`
- `kvk/rendering/kvk_targets_card_renderer.py`
- `tests/test_kvk_targets_card_payload.py`
- `tests/test_kvk_targets_card_renderer.py`
- additional full-history renderer/service tests if a new payload/card is created

Use existing repo naming conventions if audit points to a better local pattern.

## 12. Implementation Requirements

### 12.1 Targets Payload Contract

Create or refine a renderer-independent target payload before building new output.

Payload should be able to represent:

- governor identity and governor ID
- KVK number/mode/context where available
- target state: active, complete, exempt, no target, off-season, missing governor, stale data, or
  source unavailable
- kill target, current kills, percent, remaining
- dead target, current deads, percent, remaining
- DKP target, current DKP, percent, remaining
- target reason or exemption reason where available
- last refreshed / data freshness where available
- optional account-selection context

Do not let the renderer query SQL or calculate source-of-truth target semantics that belong in the
service.

### 12.2 Targets Visual Direction

Targets output should prioritise action:

```text
KVK Targets
Governor name | KVK 54 | Tides of War

Kills        current / target        remaining left
Deads        current / target        remaining left
DKP          current / target        remaining left

Status: complete / push now / no target / exempt / not in matchmaking
Next action: short, non-predictive guidance
```

Guidance:

- Use progress bars and concise status labels rather than dense embed text.
- Keep percentage copy factual; do not introduce predictive "on track" claims without approval.
- Preserve existing special states and explanations.
- If an image card is too dense, use a hybrid: image summary plus embed details.
- Keep layout readable at Discord mobile size.
- Use the same gold/progress colour policy where it matches Phase 3 card language.

### 12.3 Full History Direction

The full `/kvk history` command may be better as table-first or hybrid rather than a single dense
image card. Audit before choosing.

Options:

1. Preserve existing table/chart output and polish navigation/copy only.
2. Add a generated summary card plus keep the detailed table/export.
3. Build a full generated history card only if it remains readable and testable.

History output should support:

- KVK-by-KVK comparability
- rank/KP/kills/deads/DKP/honor/PreKVK where supported
- personal bests
- clear distinction between highest-ever metrics and last-KVK metrics
- empty-state handling for new or unmatched governors
- accessibility for longer histories

Do not remove existing CSV/export/detail affordances unless separately approved.

### 12.4 Legacy Rollout

- Keep `/mykvktargets` and `/mykvkhistory` live.
- Prefer `/kvk targets` and `/kvk history` as the modern paths.
- Do not add deprecation messaging unless separately approved.
- Preserve account picker and visibility semantics from current behaviour.
- If a modern card fails, return the existing embed/table output or a clear fallback.

### 12.5 SQL And Data Source Discipline

- Validate target and history source fields against the SQL repo before implementation.
- Do not infer column names from Python usage when SQL definitions exist.
- If SQL ambiguity exists, report missing objects explicitly and do not guess.
- If SQL changes are required, split them into a SQL companion PR with deployment order and rollback
  notes, following the SQL repo process.
- If no SQL changes are required, document the validated source objects and explain why.

### 12.6 Command Surface Governance

- [ ] No new top-level command.
- [ ] No new grouped subcommand unless separately approved.
- [ ] Preserve `/kvk targets`, `/kvk history`, `/mykvktargets`, and `/mykvkhistory` registrations.
- [ ] Preserve decorators, permissions, response visibility, autocomplete/options, usage tracking,
  and command-cache behaviour.
- [ ] Run or justify skipping `scripts/validate_command_registration.py`.
- [ ] Update `docs/reference/canonical_command_reference.md` only if command descriptions or visible
  behaviour notes change.

## 13. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| `target_utils.py` mixes target data lookup and Discord response concerns | fix now if required for payload; otherwise capture structured deferred item | Phase 4 target rendering should not depend on mixed command/view/data responsibilities. |
| Missing renderer-independent target payload | fix now | Required before modern targets output. |
| Targets special states are scattered or poorly documented | fix now if in touched path | Missing/exempt/off-season states are central to target UX. |
| Full history is too data-dense for one card | choose table-first or hybrid | Readability is more important than forcing every output into an image. |
| Compact stats-card History and full `/kvk history` share confusing labels | fix now if low risk | Phase 4 is the right time to clarify full-history copy. |
| Legacy commands still live | not applicable | Parallel rollout is intentional. |
| `/kvk rankings` polish | defer | Phase 5 owns ranking browser UX. |

Add further rows based on actual findings.

Deferred items must use the structured format from
`docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 14. Testing Requirements

Cover or justify:

- target payload happy path
- missing governor / unlinked account path
- no target / exempt target path
- complete target path
- partial progress and remaining-work formatting
- zero or missing target values without division errors
- stale/source unavailable fallback
- `/kvk targets` response visibility
- `/mykvktargets` remains live
- target renderer returns non-empty image bytes if a card is implemented
- target embed fallback if rendering fails
- full history happy path
- empty history path
- long history data shape and pagination/table accessibility
- highest-ever versus last-KVK label clarity
- `/kvk history` response visibility
- `/mykvkhistory` remains live
- command registration unchanged

Suggested focused tests, adapt to actual files after audit:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_mykvktargets.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_ui_rebuild_options.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_history_offload_and_utils.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_history_view.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_cmds.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_views.py
```

Suggested validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
```

Run full tests before promotion if practical:

```powershell
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Visual validation if image output changes:

- Generate at least one active-target sample.
- Generate at least one complete-target sample.
- Generate at least one no-target/exempt sample.
- Generate at least one full-history sample with multiple KVKs.
- Inspect desktop and mobile-like readability.
- Confirm no clipping, overlapping text, unreadable progress labels, or misleading empty states.

## 15. Acceptance Criteria

- [ ] Scope is confirmed before implementation.
- [ ] Target and history source objects are validated against `C:\K98-bot-SQL-Server`.
- [ ] `/kvk targets` has a renderer-independent payload/service boundary.
- [ ] No new direct SQL exists in command, view, or renderer modules.
- [ ] Target output clearly shows progress, remaining work, completion state, and missing/exempt explanations.
- [ ] Target output preserves existing permissions, channel restrictions, account selection, and visibility behaviour.
- [ ] `/mykvktargets` remains live.
- [ ] Full `/kvk history` output is deliberately modernised as card, table-first, or hybrid according to audit findings.
- [ ] Full history preserves long-history accessibility and existing useful detail/export behaviour.
- [ ] Highest-ever and last-KVK history labels are clear and not misleading.
- [ ] `/mykvkhistory` remains live.
- [ ] Existing command registration and command-surface baselines are preserved.
- [ ] Fallback behaviour remains useful if generated output fails.
- [ ] Focused tests pass.
- [ ] Visual review artifacts are generated when image output changes.
- [ ] Codex Security review is run before PR handoff or explicitly justified.
- [ ] Deferred optimisations are captured structurally.
- [ ] Programme/task-pack docs are updated after delivery.

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
10. Renderer / Output Summary
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

- Modernised `/kvk targets` and/or `/kvk history` according to the approved Phase 4 scope.
- Added renderer-independent target/history payload boundaries where needed.
- Preserved legacy command paths and fallback behaviour during rollout.

## Changes

- Added or updated target service/DAL/payload code.
- Updated target/history rendering or output composition.
- Updated focused tests and programme documentation.

## SQL Changes

- None, or list companion SQL PR and deployment order.

## Tests

- Focused pytest, validators, and any full-suite or log-noise result.

## Visual Review

- Generated sample paths and desktop/mobile readability notes, if image output changed.

## AI Review Gates

- Codex Security: run when risk triggers apply, or skipped with a documented reason.

## Deferred Optimisations

- None, or include structured deferred items using the repository framework.

## Risk / Rollback

- Risk: high-traffic player target/history outputs can regress visibility, readability, or fallback behaviour.
- Mitigation: payload boundaries, focused tests, visual review samples, and legacy command preservation.
- Rollback: revert `/kvk targets` and/or `/kvk history` wiring to the existing embed/table output while leaving legacy paths live.
```

## 18. Historical Codex Chat Starter

```text
This pack is closed as the Phase 4A targets execution record.

Do not start new history work from this file. Use:

docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 4B History Audit and Optioneering.md
```
