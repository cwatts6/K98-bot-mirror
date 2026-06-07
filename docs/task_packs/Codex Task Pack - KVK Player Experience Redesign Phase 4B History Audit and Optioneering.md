# Codex Task Pack - KVK Player Experience Redesign Phase 4B History Audit and Optioneering

## 1. Task Header

- Task name: `KVK Player Experience Redesign - Phase 4B History Audit and Optioneering`
- Date: `2026-06-06`
- Owner/context: `K98 Bot KVK Player Experience Redesign programme after Phase 4A targets rollout`
- Task type: `feature discovery / UX audit / architecture scope / Discord interaction design`
- One-pass approved: `no`
- Status: `ready for audit and analysis`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by
`docs/reference/README.md`. Do not add every reference document by default.

Also read:

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/task_packs/KVK Player Experience Redesign - Phase 1 Audit and Design Report.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3 Modern mykvkstats Visual Card.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3B Stats Card Polish and Secondary Cards.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3C Overall Rank and Card Polish.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 4 Modern Targets and Full History.md`
- `docs/reference/canonical_command_reference.md` if command descriptions or command-surface notes change

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

`C:\K98-bot-SQL-Server`

## 3. Objective

Audit and redesign the full `/kvk history` and `/mykvkhistory` player journey. The first delivery
stage is analysis and optioneering only: understand the existing data, chart, table, account
selection, metric-selection, and export behaviours before choosing an output model.

The final solution should help players understand historical KVK performance clearly, without
forcing all data into a card if a chart/table/hybrid journey is more effective.

## 4. Background

Phase 4A completed the modern `/kvk targets` journey in PR #145 and promoted it to production.
History was deliberately deferred because the existing output is a different kind of experience:

- A chart embed with dual-axis metric plotting.
- A generated chart image.
- A separate data/table image.
- Account selection.
- Metric buttons such as `Kills vs %`, `Deads vs %`, `DKP vs %`, and `Custom...`.
- CSV export.
- Last 3 / Last 6 / Last 10 table-range controls.

The user-provided current-output screenshot should be used as design input. It shows the existing
layout and confirms that the graph is central to the current history experience, but may not fit
the same card treatment as the stats and targets cards.

The compact History card attached to `/kvk stats` is already modernised. Phase 4B is only about the
full history command journey.

## 5. Scope

### In Scope

- Audit `/kvk history` and `/mykvkhistory` end to end.
- Audit the current chart, table image, CSV export, account picker, metric buttons, custom picker,
  and range buttons.
- Validate the current history data contract and SQL source objects.
- Identify which metrics are available, reliable, readable, and useful.
- Compare output options before implementation.
- Produce a recommended solution design with trade-offs and a staged implementation plan.
- Preserve existing command paths during design and rollout.
- Preserve CSV export unless a better approved replacement exists.
- Preserve account selection and multi-account overlay behaviour unless an approved design replaces
  it.
- Decide how the full history command should relate to the compact `/kvk stats` History card.
- Identify test coverage and visual/manual validation needed for the chosen option.

### Out of Scope

- No immediate implementation before audit and option approval.
- No removal or deprecation of `/mykvkhistory`.
- No removal of CSV export without explicit approval.
- No new top-level command or command group.
- No broad `/kvk rankings` redesign; that remains Phase 5.
- No changes to KVK import, recompute, export, Google Sheets tab names, or cache refresh semantics
  unless a defect is found and separately approved.
- No website implementation.
- No direct SQL in command modules, Discord views, or renderers.
- No predictive trend or "on track" modelling unless separately approved.

## 6. Source Deferred Items

This task is a planned programme phase, not a standalone deferred optimisation batch.

If audit finds out-of-scope debt, capture it in `docs/reference/deferred_optimisations.md` using:

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

Likely audit candidates:

```md
### Deferred Optimisation
- Area: ui/views/kvk_history_view.py / kvk_history_utils.py
- Type: architecture
- Description: The current full-history flow may mix Discord view interaction state, chart/table generation, pandas dataframe shaping, and output composition more tightly than the Phase 3/4A renderer-independent pattern.
- Suggested Fix: Audit whether a history payload/service boundary should be introduced before any visual redesign, keeping the view responsible only for interaction flow.
- Impact: medium
- Risk: medium
- Dependencies: Phase 4B audit and approved output option
```

## 7. Codex Skills To Use

### Skill Decisions

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation; first stage is audit/scope only. |
| `k98-discord-command-feature` | use | History is a Discord command/view journey with buttons, selects, generated images, and CSV export. |
| `k98-sql-validation` | use | History data is SQL-backed through `dbo.v_EXCEL_FOR_KVK_Started` and related KVK metadata. |
| `k98-test-selection` | use | Required before validation to select history, command, view, renderer, and export tests. |
| `k98-deferred-optimisation-capture` | use if needed | Required if audit finds out-of-scope debt in history utilities, views, services, or DAL. |
| `k98-pr-review` | use | Required before PR handoff after implementation. |
| `k98-promotion-check` | use | Required before production promotion or bot-machine deployment. |
| `codex-security:security-scan` | use for implementation | Required if implementation touches Discord interactions, SQL/data access, file export, or user-controlled input. Skip is acceptable for audit/docs-only output with stated reason. |

## 8. Mandatory Workflow

Phase 4B must start with audit and analysis:

1. Audit current `/kvk history` and `/mykvkhistory` behaviour, then stop for review.
2. Validate SQL/data contracts against `C:\K98-bot-SQL-Server`, then stop if ambiguity exists.
3. Produce output options with trade-offs, including at least the options in section 12.
4. Recommend one solution or staged solution.
5. Stop for approval before implementation.
6. Implement only the approved option.
7. Add or update focused tests.
8. Generate visual/manual review samples for chart/table/card changes.
9. Run focused validation and selected broader validation.
10. Run or document the Codex Security review gate.

Do not proceed directly from audit into implementation without explicit approval.

## 9. Audit Requirements

Review and document:

- `/kvk history` command path in `commands/kvk_cmds.py`.
- `/mykvkhistory` command path in `commands/stats_cmds.py`.
- `ui/views/kvk_history_view.py` interaction state, account select, metric buttons, custom picker,
  CSV export, and table-range controls.
- `services/kvk_history_service.py` account ordering, governor ID normalization, dataframe shaping,
  and missing-KVK backfill.
- `kvk/dal/kvk_history_dal.py` SQL contract and current embedded queries.
- `kvk_history_utils.py` chart, table, CSV, and metric helper ownership.
- `embed_kvk_history.py` chart embed copy and legend/axis description.
- Existing tests for history service, offload/utils, view behaviour, command registration, and
  `/kvk` command routing.
- Current generated chart readability on desktop and mobile.
- Current generated table readability for Last 3, Last 6, Last 10, and likely full-history lengths.
- Empty history, missing governor, multi-account, and overlay behaviours.
- Whether chart/table generation should remain matplotlib/table-image based, move to a card
  wrapper, or be split into summary card plus detail outputs.
- Whether the current right-axis `% of target` design is the clearest comparator for every metric.
- Whether history should include or exclude Acclaim, overall rank, honor, PreKVK, pass-window, or
  personal-best metrics in Phase 4B.

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | Keep existing `/kvk history` and `/mykvkhistory`; no new command group. |
| Service/payload | Prefer renderer-independent service/payload boundaries if output composition changes. |
| DAL | Keep SQL/data access in `kvk/dal/` or service-owned data access; no SQL in commands/views/renderers. |
| View | `ui/views/kvk_history_view.py` owns controls and interaction flow only. |
| Chart/table rendering | Keep rendering helpers separate from SQL and Discord state. |
| Export | Preserve CSV export and test generated filename/content behaviour. |
| Assets | Use `assets/kvk/cards/` only if a card or wrapper image is approved. |
| Tests | Focused tests under `tests/` for service, view, output shape, export, and selected rendering. |
| Docs | Update programme/task-pack docs after delivery. |

## 11. Likely Files

### Review

- `commands/kvk_cmds.py`
- `commands/stats_cmds.py`
- `services/kvk_history_service.py`
- `kvk/dal/kvk_history_dal.py`
- `kvk_history_utils.py`
- `embed_kvk_history.py`
- `ui/views/kvk_history_view.py`
- `ui/views/kvk_stats_card_views.py`
- `kvk/rendering/kvk_stats_card_renderer.py`
- `tests/test_kvk_history_service.py`
- `tests/test_kvk_history_offload_and_utils.py`
- `tests/test_kvk_cmds.py`
- `tests/test_kvk_stats_card_views.py`
- `tests/test_validate_command_registration.py`
- SQL repo objects for `dbo.v_EXCEL_FOR_KVK_Started`, `dbo.KVK_Details`, and history source tables/views

### Modify

Decide after audit. Likely candidates if implementation is approved:

- `services/kvk_history_service.py`
- `kvk_history_utils.py`
- `embed_kvk_history.py`
- `ui/views/kvk_history_view.py`
- `commands/kvk_cmds.py` only if visible command behaviour changes
- focused history tests
- programme/task-pack docs

### Create

Only if the approved option needs them:

- `kvk/models/kvk_history_payload.py`
- `kvk/services/kvk_history_card_service.py`
- `kvk/rendering/kvk_history_renderer.py`
- `tests/test_kvk_history_renderer.py`
- `tests/test_kvk_history_payload.py`

## 12. Optioneering Requirements

Produce at least these options before implementation:

### Option A - Polish Existing Journey

Keep the current chart embed, chart image, data image, account selector, metric buttons, custom
picker, and CSV export. Improve labels, spacing, copy, empty states, and reliability without a new
card layer.

Best when:

- The graph remains the primary value.
- Current controls are broadly useful.
- Risk should stay low.

Trade-offs:

- Less visual alignment with stats/targets.
- Existing chart/table image limitations remain.

### Option B - Hybrid Summary Card Plus Existing Detail Flow

Add a modern summary card for the selected governor/account and preserve the existing chart/table
and CSV detail flow. The summary card could show last KVK, personal bests, KVK count, standout
metrics, and trend direction, while the existing graph/table remains the detailed analysis view.

Best when:

- The card is useful for quick understanding.
- The graph/table remains necessary for real comparison.
- Visual alignment matters but data density is too high for one card.

Trade-offs:

- More moving parts and more tests.
- Needs careful interaction design so players know where detail lives.

### Option C - Modern Chart/Table Wrapper

Keep matplotlib/table generation, but wrap the chart and data table in a cleaner Phase 3-style
layout with consistent header, governor identity, legend, footer, and controls. This may be a
single generated image or two coordinated images.

Best when:

- The current chart is valuable but visually disconnected.
- The chart can remain readable after applying the card language.

Trade-offs:

- Risk of making the graph smaller or less readable.
- Needs visual validation across long names, long histories, and mobile Discord.

### Option D - Data-First Interactive History Browser

Move away from a graph-first presentation and provide a paginated/table-first Discord view with
metric toggles, personal-best callouts, and CSV export. Use cards only for optional summaries.

Best when:

- The graph is hard to read on mobile.
- Players mostly need exact KVK-by-KVK values.

Trade-offs:

- Less visually striking.
- May not satisfy users who like trend graphs.

### Option E - Defer Visual Redesign, Improve Data Contract First

If audit finds that the data contract is ambiguous or missing key metrics, defer output redesign
and first build a history payload/data-contract pack.

Best when:

- Metric semantics are unclear.
- Acclaim/rank/honor/PreKVK inclusion needs SQL or product decisions.

Trade-offs:

- No immediate UX improvement.
- Avoids reworking the output twice.

## 13. Data And Metric Questions To Answer

Answer before implementation:

- Which metrics should Phase 4B display by default?
- Should the default remain `T4&T5 Kills` vs `% of Kill target`?
- Should deads and DKP each continue to pair with their own `% of target` right axis?
- Should Acclaim appear in full history now, later, or never?
- Should KVK rank or overall rank history be included?
- Should honor and PreKVK history remain outside this command?
- Should pass-window kills/deads remain custom-only or become selectable presets?
- Should multiple selected governors remain capped at three overlays?
- What is the right empty-state for KVKs with no row versus zero-filled started KVKs?
- Which labels need renaming to avoid confusion between highest-ever, last-KVK, target percent, and
  current-KVK stats?

## 14. Implementation Requirements

Once an option is approved:

- Keep commands and views thin.
- Put data shaping and comparison rules in service/model code.
- Keep SQL/data access in DAL/service layers.
- Keep renderers free of SQL and Discord objects.
- Preserve existing account selection, visibility, metric controls, and CSV export unless the
  approved option says otherwise.
- Preserve fallback behaviour if chart/card/table generation fails.
- Keep chart/table/card output readable on Discord mobile.
- Add or update focused tests for every changed behaviour.
- Generate visual samples for at least one single-account and one multi-account history.

## 15. Command Surface Governance

- [ ] No new top-level command.
- [ ] No new grouped subcommand unless separately approved.
- [ ] Preserve `/kvk history` and `/mykvkhistory` registrations.
- [ ] Preserve decorators, permissions, response visibility, options, usage tracking, and command
  cache behaviour unless explicitly approved.
- [ ] Run or justify skipping `scripts/validate_command_registration.py`.
- [ ] Update `docs/reference/canonical_command_reference.md` only if command descriptions or visible
  behaviour notes change.

## 16. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| Full history may be too dense for a single stats-card-style image | decide during optioneering | Readability and graph utility matter more than visual uniformity. |
| History view may own too much output composition | audit first | Extract only if approved option requires clearer service/payload boundaries. |
| CSV export remains useful | preserve by default | Removal would reduce current functionality. |
| Legacy `/mykvkhistory` still lives | not applicable | Parallel rollout is intentional. |
| `/kvk rankings` polish | defer | Phase 5 owns rankings. |

Add further rows based on actual findings. Deferred items must use the structured format from
`docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 17. Testing Requirements

Cover or justify:

- `/kvk history` happy path.
- `/mykvkhistory` happy path.
- registered-account and explicit Governor ID paths.
- empty history / missing governor path.
- single-account chart/table output.
- multi-account overlay output.
- metric preset buttons.
- custom metric picker.
- Last 3 / Last 6 / Last 10 table range buttons.
- CSV export content and filename.
- fallback behaviour when chart/table/card generation fails.
- command registration unchanged.
- renderer/payload output shape if a new payload or renderer is added.

Suggested focused tests after audit:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_history_service.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_history_offload_and_utils.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_cmds.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py
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
.\.venv\Scripts\python.exe -m pytest -q tests
```

For docs-only audit/optioneering output, runtime pytest may be skipped with a documented reason.

## 18. Acceptance Criteria

Audit/optioneering acceptance:

- [ ] Current `/kvk history` and `/mykvkhistory` behaviours are mapped.
- [ ] Current data contract and SQL source objects are validated or ambiguities are documented.
- [ ] Current screenshot/output is used as design input.
- [ ] At least four viable output options are compared with trade-offs.
- [ ] A recommended option or staged solution is proposed.
- [ ] Implementation plan is separated from audit findings.
- [ ] No implementation occurs before approval.

Implementation acceptance, after approval:

- [ ] Approved output model is implemented without removing legacy commands.
- [ ] Existing useful controls/export remain or are deliberately replaced.
- [ ] Output is readable on Discord mobile.
- [ ] Commands/views remain thin.
- [ ] No new direct SQL exists in command, view, or renderer modules.
- [ ] Focused tests pass.
- [ ] Visual/manual review samples are generated where output changes.
- [ ] Codex Security review is run or explicitly skipped based on risk triggers.
- [ ] Programme/task-pack docs are updated after delivery.

## 19. Required Delivery Output

For the audit/optioneering stage:

1. Summary
2. Current Behaviour Map
3. Data Contract Findings
4. UX Findings From Existing Screenshot/Output
5. Architecture Findings
6. Option Matrix
7. Recommended Option
8. Implementation Plan
9. Test Strategy
10. Risks / Open Questions
11. Deferred Optimisations

For the implementation stage, use:

1. Summary
2. File Manifest
3. SQL Changes
4. Command Surface Changes
5. User-Visible Behaviour Changes
6. Data Contract / Payload Summary
7. Renderer / Output Summary
8. Refactor Findings
9. Test Plan and Results
10. Visual Review Evidence
11. AI Review Gates
12. Deployment Steps
13. Rollback Plan
14. Deferred Optimisations

## 20. PR Summary Template

```md
## Summary

- Audited and/or modernised the full `/kvk history` journey according to the approved Phase 4B scope.

## Changes

- <audit docs or implementation changes>

## SQL Changes

- None, or list companion SQL PR and deployment order.

## Tests

- <focused pytest/validators/manual visual checks>

## AI Review Gates

- Codex Security: <run | skipped, with reason>

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Risk: full history is a high-traffic player output with chart/table/export interaction complexity.
- Rollback: preserve or restore the existing chart/table/CSV output while keeping legacy commands live.
```

## 21. Codex Chat Starter

```text
Codex, start Phase 4B of the KVK Player Experience Redesign: History Audit and Optioneering.

Phase 4A targets is complete, merged, and promoted to production. Do not change targets except to
preserve compatibility. The task is to audit /kvk history and /mykvkhistory, validate the history
data contract, use the current screenshot/output as design input, and produce solution options
before implementation.

First stage only: audit and analysis, then optioneering. Do not implement until the option is
approved.

Read:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/KVK Player Experience Redesign - Programme Pack.md
- docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 4B History Audit and Optioneering.md

Review:
- commands/kvk_cmds.py
- commands/stats_cmds.py
- services/kvk_history_service.py
- kvk/dal/kvk_history_dal.py
- kvk_history_utils.py
- embed_kvk_history.py
- ui/views/kvk_history_view.py
- existing history tests

Validate SQL assumptions against C:\K98-bot-SQL-Server.

The card approach may work for summary data, but the graph may need a different treatment. Compare
chart-first, hybrid summary-plus-detail, modern wrapper, data-first interactive browser, and
data-contract-first options. Preserve CSV/export/account controls unless the approved design
deliberately replaces them.
```
