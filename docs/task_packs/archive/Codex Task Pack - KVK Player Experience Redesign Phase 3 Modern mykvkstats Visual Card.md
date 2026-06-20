# Codex Task Pack - KVK Player Experience Redesign Phase 3 Modern `/mykvkstats` / `/kvk stats` Visual Card

## 1. Task Header

- Task name: `KVK Player Experience Redesign - Phase 3 Modern /mykvkstats Visual Card`
- Date: `2026-06-04`
- Owner/context: `K98 Bot KVK Player Experience Redesign programme after Phase 1, Phase 2A, and Phase 2B completion`
- Task type: `feature / UX redesign / generated image renderer / Discord interaction polish`
- One-pass approved: `no`
- Status: `complete`

### Phase Completion Update

Phase 3 is complete and should remain closed. The delivered rollout intentionally keeps the
legacy `/mykvkstats` embed unchanged while `/kvk stats` produces the new visual card, allowing both
paths to run in parallel during user validation and communication.

Delivered outcomes:

- `/kvk stats` renders the modern Pillow-generated main card.
- Multiple registered governors are routed through the selected-account card posting path.
- The original `/mykvkstats` embed remains connected to the legacy output path.
- `Main Card`, `More Stats`, and `History` navigation exists on the new `/kvk stats` output.
- Embed-only fallback is preserved when card rendering or upload fails.
- KVK mode and camp are shown on the main card.
- Discord avatar support is included with a fallback identity marker.
- The main card now uses an 8-metric grid and no longer shows `Power Loss`.
- Follow-on visual polish and secondary-card work was completed in Phase 3B:
  `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3B Stats Card Polish and Secondary Cards.md`.
- Remaining overall-rank data contract and card polish work was completed in Phase 3C:
  `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3C Overall Rank and Card Polish.md`.
- The next active programme phase is Phase 4 targets/history modernisation:
  `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 4 Modern Targets and Full History.md`.

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`.

Also read these programme and command-surface documents:

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/task_packs/KVK Player Experience Redesign - Phase 1 Audit and Design Report.md`
- `docs/task_packs/KVK Player Experience Redesign - Phase 2 New /kvk Player Command Group Scaffold Task Pack - Draft.md` only as historical context
- `docs/reference/canonical_command_reference.md`
- current command platform docs if command registration validation points to them

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

```text
C:\K98-bot-SQL-Server
```

Important: Phase 1, Phase 2A, and Phase 2B are already complete and deployed. Do not re-open command-surface migration unless a defect is found.

## 3. Objective

Modernise the player-facing KVK stats output by replacing the current text-heavy `/mykvkstats` / `/kvk stats` result with a generated visual performance card using the new Tides battlefield card background asset.

The new default output should be a high-impact image card that answers "how am I doing in this KVK?" while preserving the most popular current features: kill-target progress, colour-coded achievement feedback, motivational quote text, and access to deeper details/history.

This phase must establish reusable KVK stats card primitives and a service payload contract without changing KVK calculations, SQL import/recompute/export behaviour, or legacy command availability.

Completion note: the approved implementation used a safer staged rollout than the original broad
objective. `/kvk stats` now owns the new visual card while `/mykvkstats` remains legacy for parallel
validation.

## 4. Background

The KVK Player Experience Redesign programme has already delivered:

- Phase 1 audit/design.
- Phase 2A separation of admin/operator KVK commands into `/kvk_admin`.
- Phase 2B player `/kvk` scaffold with `/kvk stats`, `/kvk targets`, `/kvk history`, and `/kvk rankings` while legacy flat commands remain live.

The current `/mykvkstats` embed is popular because it combines current KVK progress, target percentages, a kill-target dial, motivational quote, and historical KVK summary. However, the output is visually dated and too dense for the new KVK player experience.

The agreed Phase 3 direction is:

- Make the default result a modern generated image card.
- Keep only the highest-value current KVK metrics on the main card.
- Use three interaction views only:
  - `Main Card`
  - `More Stats`
  - `History`
- Keep one compact kill-target progress indicator, not a large separate dial.
- Move DKP, pass stats, Pre-KVK, Honor, and historical summaries behind buttons.

## 5. Scope

### In Scope

- Add the provided reusable card assets to the repo, preferably under a clear asset path such as:
  - `assets/kvk/cards/Tides_Stats_Card.png`
  - `assets/kvk/cards/History_Stats_Card.png`
  - optional design-only reference: `assets/kvk/reference/tides_sample.jpg`
- Build a KVK stats service payload/dataclass that normalises all data needed by the renderer and buttons.
- Build a Pillow-based image renderer for the main KVK stats card.
- Use the custom Tides battlefield background asset for the visual card, not the raw game screenshot.
- Update `/kvk stats` and legacy `/mykvkstats` so both can use the new output path, unless audit finds a safer staged rollout path.
- Preserve the existing account-selection behaviour:
  - private selector where currently used
  - selected single-account stats posting publicly where currently used
- Preserve existing command permissions, channel restrictions, versioning, usage tracking, and command-cache behaviour.
- Add a compact kill-target progress indicator using the current colour and quote rules from the existing embed/spec.
- Add or update the interaction view for three available views:
  - `Main Card`
  - `More Stats`
  - `History`
- Add fallback behaviour to the existing embed if image rendering fails.
- Add focused tests for payload construction, renderer output, interaction callbacks, fallback behaviour, and command registration.
- Update docs and command references only where visible behaviour or command output descriptions change.

### Out of Scope

- No SQL schema, stored procedure, view, function, index, or migration changes unless audit proves a missing field cannot be sourced safely.
- No changes to KVK import, recompute, export, Google Sheets tab names, or cache refresh scheduling.
- No removal of legacy commands.
- No deprecation messages for legacy commands unless separately approved.
- No redesign of `/kvk targets`, `/kvk history`, `/kvk rankings`, `/mykvktargets`, `/mykvkhistory`, or `/kvk_rankings` beyond the three-button support attached to this stats output.
- No large history chart redesign in this phase.
- No website implementation.
- No predictive "on track" modelling.
- No new command group or top-level command.
- No direct SQL in commands, views, or renderers.

## 6. Source Deferred Items

This work belongs to the active KVK Player Experience Redesign programme rather than a standalone deferred optimisation. Do not add a new deferred item for the main Phase 3 work unless scope is split or blocked.

Capture any newly discovered out-of-scope debt in `docs/reference/deferred_optimisations.md` using the structured deferred optimisation format.

Likely deferred items to capture if found:

```md
### Deferred Optimisation
- Area: <module/path>
- Type: architecture | refactor | cleanup | performance | consistency
- Description: <what was found>
- Suggested Fix: <future task direction>
- Impact: low | medium | high
- Risk: low | medium | high
- Dependencies: <dependencies>
```

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation because this touches command/view/service/renderer boundaries. |
| `k98-discord-command-feature` | use | Required because `/kvk stats`, `/mykvkstats`, Discord attachments, buttons, and response visibility are touched. |
| `k98-sql-validation` | use | Required because the card depends on SQL-backed stat/cache fields, even if SQL itself should not change. |
| `k98-test-selection` | use | Required before validation to select focused command, renderer, service, and regression tests. |
| `k98-deferred-optimisation-capture` | use | Required if audit finds out-of-scope service/DAL, cache, renderer, or command debt. |
| `k98-pr-review` | use | Required before PR handoff. |
| `k98-promotion-check` | use | Required before production promotion because this changes a high-traffic player command output. |
| `codex-security:security-scan` | use | Required because user-controlled names/avatars, Discord interactions, SQL-backed data, and file/image output are touched. |

## 8. Mandatory Workflow

1. Read the required docs and confirm Phase 1, Phase 2A, and Phase 2B are complete in the current branch.
2. Audit current `/kvk stats` and `/mykvkstats` implementation paths.
3. Audit current data fields and source objects for every metric listed in this task pack.
4. Audit current kill-target colour/quote rules and preserve them.
5. Propose the payload contract and renderer architecture, then stop for approval.
6. After approval, implement the service payload, renderer, and view updates.
7. Add/update tests.
8. Run focused validation and selected broader validation.
9. Run Codex Security review.
10. Produce PR summary, screenshots/artifacts for visual review, deployment notes, and rollback plan.

Proceed in one pass only if the operator explicitly approves one-pass implementation after reading the audit plan.

## 9. Audit Requirements

Before coding, identify and document:

- current `/kvk stats` callback path
- current `/mykvkstats` callback path
- current account selector and selected-account posting behaviour
- current renderer/embed function, likely `build_stats_embed`
- current data-loading functions, likely `load_last_kvk_map`, `load_stat_row`, `load_stat_cache`, and related helpers
- current cache file and payload shape for KVK player stats
- current source for `KVK_RANK`, `Governor_Name`, `Governor ID`, matchmaking power, kill targets, dead targets, DKP targets, pass stats, Pre-KVK, Honor, Healed, Acclaim, and history
- exact current colour and motivational quote rules for kill-target percentage
- existing avatar/profile image handling patterns from inventory/profile/prekvk renderers
- existing Pillow helpers, font fallback helpers, image export helpers, and deterministic renderer test patterns
- any direct SQL in command/view layers that should not be copied or expanded
- whether `History_Stats_Card.png` should be used in Phase 3 or simply staged as an asset for a later history visual phase

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | Existing `commands/kvk_cmds.py` and legacy path owner only as needed. Do not create new top-level commands. |
| Views/buttons | `ui/views/` or existing KVK personal stats view module. Keep callbacks thin. |
| Service payload | New or existing KVK stats service module, returning dataclasses independent of Discord and Pillow. |
| Renderer | New KVK stats card renderer module, likely under a `kvk/` or `image_renderers/` package following existing repo conventions. |
| Data access | Existing stats/cache/DAL modules only. No SQL in renderer/view/command. |
| Assets | `assets/kvk/cards/` or existing approved asset location. |
| Tests | Focused tests under `tests/` for payload, renderer, commands/views, and fallback. |
| Docs | `docs/reference/canonical_command_reference.md` only if output descriptions or command notes change. |

## 11. Likely Files

### Review

- `commands/kvk_cmds.py`
- `commands/stats_cmds.py`
- `embed_utils.py` or current stats embed builder module
- `ui/views/kvk_personal_views.py`
- `ui/views/stats_views.py` if used by current personal stats flow
- `player_stats_cache.py`
- `stats_cache_helpers.py`
- `stats_service.py`
- `utils.py` functions used by current KVK stats path
- inventory image renderer modules
- prekvk image renderer modules
- player profile card renderer modules
- existing tests for `/mykvkstats`, `/kvk stats`, KVK personal views, stats service, image renderers
- SQL repo output objects that produce current stats/cache fields

### Modify

Exact files should be decided after audit, but likely:

- `commands/kvk_cmds.py`
- `commands/stats_cmds.py`
- current KVK personal view module
- current stats embed builder or adapter
- stats/KVK service modules
- tests for KVK stats commands/views/service
- docs/reference command/output notes if applicable

### Create

Potentially:

- `kvk/models/kvk_stats_card.py`
- `kvk/services/kvk_stats_card_service.py`
- `kvk/rendering/kvk_stats_card_renderer.py`
- `ui/views/kvk_stats_card_views.py`
- `tests/test_kvk_stats_card_payload.py`
- `tests/test_kvk_stats_card_renderer.py`
- `tests/test_kvk_stats_card_views.py`

Use existing repo naming conventions if different.

## 12. Implementation Requirements

### 12.1 Asset Handling

- Add `Tides_Stats_Card.png` as the primary card background.
- Add `History_Stats_Card.png` only if used or clearly staged for a future history card.
- Treat `tides sample.jpg` as design/reference-only if added; do not use it as the production output background unless explicitly approved.
- Do not store raw game UI screenshots as production backgrounds.
- Add asset existence validation in tests or a lightweight runtime fallback.
- If an asset is missing in production, fall back to the existing embed rather than failing the command.

### 12.2 Service Payload Contract

Create a renderer-independent payload model with clear optional fields and warning states.

Minimum main-card payload fields:

| Card label | Source / calculation |
|---|---|
| Governor name | current stats row `Governor_Name` or equivalent |
| Governor ID | current stats row `Governor ID` / `GovernorID` |
| KVK number / mode | current KVK context, e.g. `KVK 15`, `Tides of War` |
| Camp badge | current camp mapping, e.g. `Wind`, if available |
| Last updated / scan freshness | current scan/cache freshness source |
| Map / kingdom context | keep if currently available and useful, but lower priority than core stats |
| Rank | `KVK_RANK` or current KVK rank field |
| Matchmaking Power | matchmaking power field used by the current embed, not current live power unless current behaviour already uses that |
| KP Gain | `KillPoints` |
| Kills Gain | `T4_Kills + T5_Kills` or existing combined field used by current embed |
| Kills target | current kill target |
| Kills target % | `Kills Gain / Kills Target * 100` or existing validated percentage |
| Deads | `Deads_diff` |
| Deads target | current deads target |
| Deads target % | `Deads_diff / Deads Target * 100` or existing validated percentage |
| Power Loss | `Troop_Power_Diff` |
| KP Loss | `Healed * 20` |
| Healed | current `Healed` / `Healed Δ` value used by existing embed |
| Tanking Score | `(KP Loss / KP Gain) * 100` |
| Playstyle | derived from Tanking Score |
| Acclaim | current numeric Acclaim field from DB/cache |
| Kill progress quote | existing current embed quote policy |
| Kill progress colour | existing current embed colour policy |

Do not let the renderer recalculate values that the service can safely provide. The renderer should format and draw values only.

### 12.3 Main Card Layout

The main image card should approximate the agreed modern design:

```text
MY KVK
Last updated <x> ago | <kingdom/KVK context> | <KVK mode>

<avatar> <Governor name>
ID <Governor ID>
<Camp badge>

RANK
#<rank>

KP GAIN          MM POWER          POWER LOSS
<value>          <value>           <value>

KILLS GAIN       DEADS             KP LOSS
<gain>/<target>  <deads>/<target>  <value>
(<percent>)      (<percent>)

HEALED           TANKING SCORE     PLAYSTYLE
<value>          <percent>         <label>

ACCLAIM
<value>

KILLS TARGET PROGRESS
<compact colour-coded bar> <percent> - <quote>
```

Layout guidance:

- Use the Tides battlefield background.
- Use a dark overlay/vignette if required for readability.
- Avoid a text wall.
- Keep large values prominent.
- Make the card readable at Discord mobile size.
- Keep long governor names safe with truncation, wrapping, or smaller font.
- Support non-ASCII governor names using existing font fallback patterns.
- Use consistent colour policy for percentage achievement.
- Do not show DKP, passes, Pre-KVK, Honor, or history on the main card.

### 12.4 Kill Target Progress Indicator

Preserve the current popular kill-target feature but make it compact.

Requirements:

- One kill-target progress indicator only.
- No large separate dial.
- Use the current embed/spec colour rules and quote rules.
- Include the percentage and quote text.
- Support values above 100% without breaking the visual. Cap the drawn bar at 100% but show the true percentage.
- Suggested conceptual colour bands if the current implementation needs confirming:
  - `< 50%` = red
  - `50-74%` = amber
  - `75-99%` = green
  - `100%+` = gold

Do not invent new quote text unless the existing implementation has no quote source. If no quote rules are found, stop and ask for the current spec or preserve the existing embed output in the More Stats view until the quote policy is confirmed.

### 12.5 Tanking Score and Playstyle

Use the approved definitions:

```text
KP Loss = Healed * 20
Tanking Score = (KP Loss / KP Gain) * 100
```

Playstyle labels:

| Tanking Score | Label |
|---:|---|
| `< 80%` | `Sniping Kills` |
| `80-110%` | `Objective Focusing` |
| `> 110%` | `Going All Out Fighting` |

Guardrails:

- If `KP Gain` is `0` or missing, display `N/A` for Tanking Score.
- If Tanking Score is `N/A`, display `Not enough data` or omit Playstyle according to the approved card layout.
- If Healed is missing, do not show a misleading KP Loss or Tanking Score.
- Keep all calculations in service/payload code, not in the renderer.

### 12.6 More Stats Button

The `More Stats` view should show deeper current-KVK details without crowding the main card.

Minimum content:

```text
DKP
65.1M / 55.0M - 118%

Passes
Pass 4 Kills: 14.3M
Pass 6 Kills: 4.6M
Pass 4 Deads: 1.1M

Pre-KVK
Rank: 22
Points: 2.8M

Honor
Rank: 16
Points: 67.2k
```

Requirements:

- Can be a clean Discord embed in Phase 3.
- Do not build a second complex image renderer unless it is low-risk and follows the same payload boundary.
- Reuse the selected governor/account context from the main card interaction.
- Include a `Main Card` button to return.
- Include a `History` button if all three buttons are kept visible.

### 12.7 History Button

The `History` view should preserve the popular historical context without overloading the main card.

Minimum content:

```text
Historic KVK Data

Summary
Autarch: 3
KVK Played: 10
Highest Acclaim: 10.0M

Personal Bests
Most Kills: 53.4M
Most Deads: 2.0M
Most Heal: 36.8M

Last KVK Summary - KVK 14
Kills: 36.3M / 15.0M - 242%
Deads: 1.9M / 1.2M - 150%
DKP: 124.0M / 55.0M - 226%
KP: 696.5M
Acclaim: 10.0M

Matchmaking Snapshot
MM KP: 7.9B
MM Kills: 477.4M
MM Deads: 25.0M
MM Healed: 331.8M
```

Requirements:

- Can be a clean Discord embed in Phase 3.
- Do not replace the full `/kvk history` command.
- Do not rebuild the full KVK history chart/table output.
- Use existing history service/data sources where possible.
- If history data is unavailable, show a clear empty state and keep the Main Card button available.

### 12.8 Button Model

Use only three views:

```text
[Main Card] [More Stats] [History]
```

Requirements:

- Avoid five or more buttons.
- Keep all three buttons visible if simpler and consistent.
- Respect existing view timeout conventions.
- Disable or gracefully handle stale interactions.
- Preserve restart-safety assumptions of the current stats views. Do not introduce persistent views unless explicitly designed and tested.
- The button callbacks should not fetch raw SQL or perform heavy rendering directly in the event loop.

### 12.9 Rendering and Performance

- Use Pillow unless the audit proves an existing renderer abstraction should be used.
- Render in `asyncio.to_thread` or the existing off-thread rendering helper.
- Keep renderer functions deterministic where possible.
- Return `BytesIO` or bytes plus a stable filename.
- Keep file size Discord-safe.
- Add fallback to existing embed when rendering fails.
- Log rendering failures with enough detail for operators, without leaking sensitive or excessive user data.

### 12.10 Fallback and Rollout

- The existing embed output must remain available as a fallback.
- If the image card fails for one user, the command should still respond with useful stats.
- If the new output causes production issues, rollback should be possible by switching the command/view back to the existing embed path.
- Consider a feature flag or config toggle such as `KVK_STATS_CARD_ENABLED` if consistent with repo standards.

### 12.11 Command Surface Governance

- [ ] This task should not add a new top-level command.
- [ ] This task should not add a new grouped subcommand unless audit proves a small helper/admin test command is required and separately approved.
- [ ] Preserve `/kvk stats` and `/mykvkstats` registration.
- [ ] Preserve `@versioned()`, `@safe_command`, `@track_usage()`, permission decorators, response visibility, autocomplete/options, usage-log identity, and command-cache behaviour.
- [ ] Update `docs/reference/canonical_command_reference.md` only if descriptions/output notes change.
- [ ] Run or justify skipping:
  - `scripts/validate_command_registration.py`
  - `tests/test_validate_command_registration.py`
  - `tests/test_command_inventory.py`
  - `tests/test_command_registration_smoke.py`

## 13. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| Current embed builder has reusable formatting helpers | reuse or extract | Avoid duplicate number formatting/quote rules. |
| Current command handler contains business/data logic | extract if required for payload, otherwise defer | Keep command/view thin without over-expanding Phase 3. |
| Missing clean KVK stats payload contract | fix now | Required before safe rendering. |
| Direct SQL in command/view path | do not duplicate; extract only if needed | Renderer must not depend on direct SQL. |
| History view needs full redesign | defer | Phase 3 history button is summary only; full `/kvk history` redesign is later. |
| Targets output needs redesign | defer | This is Phase 4 or later. |
| New quote/colour policy requested beyond current spec | defer or stop for approval | Current policy must be preserved. |
| Website/shared component abstraction | defer | Website implementation is out of scope. |

Add further rows based on actual findings.

## 14. Testing Requirements

Cover or justify:

- main payload happy path
- missing optional fields
- zero `KP Gain` Tanking Score guardrail
- missing background asset fallback
- renderer produces non-empty PNG bytes
- long governor name rendering/truncation
- non-ASCII governor name rendering
- kill progress colour band/quote mapping
- percentage above 100% display with capped visual bar
- More Stats button content
- History button content and empty state
- stale/timeout interaction behaviour
- command permissions and response visibility unchanged
- legacy `/mykvkstats` remains live
- `/kvk stats` remains live
- fallback to existing embed when renderer raises
- command registration unchanged

Suggested focused tests, adapt to actual repo file names:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_mykvkstats.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_cmds.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_personal_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_stats_service.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_payload.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_renderer.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_views.py
```

Suggested validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m ruff check commands kvk ui tests
.\.venv\Scripts\python.exe -m black --check commands kvk ui tests
.\.venv\Scripts\python.exe -m pyright commands kvk ui tests
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_inventory.py tests\test_command_registration_smoke.py
```

Run full tests if practical before promotion:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

Visual validation:

- Save at least one generated sample card from test/dev data for PR review.
- Include screenshots or generated PNG artifacts in the PR description if repo process allows.
- Manually inspect readability at Discord desktop and mobile-like sizes.
- Confirm no text overlaps, clipping, unreadable colours, or missing glyphs.

## 15. Acceptance Criteria

- [x] Phase 1, Phase 2A, and Phase 2B completion is confirmed.
- [x] The provided Tides card background asset is added to the repo and used by the main stats card.
- [x] The production card does not use raw game UI screenshots as the background.
- [x] A renderer-independent KVK stats card payload contract exists.
- [x] Commands/views do not calculate complex metrics inline.
- [x] Renderer does not fetch SQL/cache data and does not depend on Discord types.
- [x] `/kvk stats` can return the new main visual card.
- [x] `/mykvkstats` remains legacy as the documented safe parallel rollout path.
- [x] Main card includes Governor name, Governor ID, KVK mode, camp, rank, MM Power, Kills Gain + target %, Deads + target %, Healed, KP Gain, KP Loss, Tanking Score, Playstyle, and Acclaim.
- [x] Main card includes one compact kill-target progress indicator using current colour and quote rules.
- [x] Main card does not include DKP, Passes, Pre-KVK, Honor, or history details.
- [x] `More Stats` view includes deeper current-KVK details.
- [x] `History` view includes historical summary, personal bests, last KVK summary, and matchmaking snapshot where data is available.
- [x] Button set is limited to `Main Card`, `More Stats`, and `History`.
- [x] Existing permissions, channel restrictions, registration paths, versioning, usage tracking, and response visibility are preserved.
- [x] Existing embed fallback remains available and is tested.
- [x] Missing data and zero-division cases are handled safely.
- [x] No SQL schema/procedure/view/function changes are made unless separately approved.
- [x] No new direct SQL is added to commands, views, or renderers.
- [x] Focused tests pass.
- [x] Command registration validation passes or any skip is justified.
- [x] Codex Security review gate was considered for the implementation PR.
- [x] Rollback plan is documented.
- [x] Out-of-scope follow-on work is split into Phase 3B.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. Asset Files
6. SQL Changes
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

- Added the modern KVK stats visual card for `/kvk stats` and the legacy `/mykvkstats` path.
- Added a renderer-independent KVK stats card payload and Pillow renderer using the Tides battlefield background asset.
- Added `Main Card`, `More Stats`, and `History` interaction views while preserving existing command permissions and fallback output.

## Changes

- Added KVK stats card assets under `<asset path>`.
- Added `<payload/service modules>`.
- Added `<renderer module>`.
- Updated `<command/view modules>`.
- Added focused tests for payload, renderer, view callbacks, and fallback behaviour.

## User-visible behaviour

- `/kvk stats` and `/mykvkstats` now show a generated KVK performance card by default.
- Players can use `More Stats` for DKP, pass, Pre-KVK, and Honor details.
- Players can use `History` for compact historical KVK context.
- Legacy command paths remain live.

## SQL Changes

- None.

## Tests

- `<commands/results>`

## Visual Review

- Generated sample card reviewed at Discord desktop and mobile-like sizes.
- No clipping, overlap, unreadable text, or missing glyphs found.

## AI Review Gates

- Codex Security: `<run/skipped with reason>`

## Deferred Optimisations

- `<none or structured items>`

## Risk / Rollback

- Risk: high-traffic player stats command now depends on image rendering and asset availability.
- Mitigation: existing embed fallback remains available and renderer failure is logged.
- Rollback: disable card feature flag or revert command/view wiring to existing embed output; legacy data and commands remain unchanged.
```

## 18. Codex Chat Starter

Phase 3, Phase 3B, and Phase 3C are complete. Use the Phase 4 task pack for the targets and full
history modernisation work.

Historical Phase 3 starter:

```text
Codex, start Phase 3 of the KVK Player Experience Redesign: Modern /mykvkstats / /kvk stats Visual Card.

Phase 1 audit/design, Phase 2A /kvk_admin separation, and Phase 2B player /kvk scaffold are complete and deployed.

Before implementation, read:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/KVK Player Experience Redesign - Programme Pack.md
- docs/task_packs/KVK Player Experience Redesign - Phase 1 Audit and Design Report.md
- docs/reference/canonical_command_reference.md
- this Phase 3 task pack

Use the K98 repo workflow and required skills. First audit the existing /kvk stats and /mykvkstats paths, current data fields, current kill-target colour/quote policy, and existing image-renderer patterns. Then propose the payload contract and renderer architecture before implementing.

The new output should use the Tides_Stats_Card.png background asset, keep only the main KVK performance metrics on the default image card, preserve one compact colour-coded kill-target progress indicator with the existing quote policy, and expose only three views/buttons: Main Card, More Stats, and History.

Do not change SQL, KVK recompute/import/export, Google Sheets contracts, or remove legacy commands. Preserve existing permissions, channel restrictions, response visibility, versioning, usage tracking, and command-cache behaviour. Include embed fallback if rendering fails.
```
