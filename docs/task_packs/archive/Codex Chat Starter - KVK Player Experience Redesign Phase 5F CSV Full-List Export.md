# Codex Chat Starter - KVK Player Experience Redesign Phase 5F-2 CSV Full-List Export

Status: complete. Phase 5F-2 was delivered in mirror PR #159 and production PR #467, pushed to
production, smoke tested successfully, and polished through review/smoke-test feedback.

Delivered summary:

- Added private `Full List CSV` export for current KVK, Honor, and PreKvK rankings.
- Preserved Top 100 exclusion, My Rank, Top 10 visual cards, Top 25/50 compact browser output,
  records Top 10-only controls, Honor channel gating, legacy ranking commands, and image-based
  legacy `/prekvk report`.
- Generated CSV in memory with deterministic filenames, formula-leading cell escaping, private
  failure handling, and clean leaderboard-only columns.
- Final CSV columns:
  - Honor: `Rank`, `GovernorID`, `GovernorName`, `Honor`, `KVK`.
  - KVK: `Rank`, `GovernorID`, `GovernorName`, `Power`, `Kills`, `PercentKillTarget`, `Deads`,
    `DKP`, `Acclaim`, `TankingScore`, `KillPoints`, `Healed`.
  - PreKvK: `Rank`, `GovernorID`, `GovernorName`, `Power`, `Stage1`, `Stage2`, `Stage3`,
    `Overall`.
- Restored KVK Top 10 `Kill Points` and `Healed` metric selection.

Next starter, now completed by Phase 5G:

`docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5G Rankings Wrap-up Polish.md`

Phase 5A, Phase 5B, Phase 5C, Phase 5D, Phase 5E, and Phase 5F-1 are complete.

- Phase 5A: mirror PR #152 and production PR #461 delivered
  `/kvk rankings type:records` as the KD98 Hall of Fame Top 10 all-time single-KVK records
  foundation.
- Phase 5B: mirror PR #153 and production PR #462 delivered the unified current-ranking browser
  for KVK, Honor, and PreKvK rankings. It was pushed to production and smoke tested successfully.
- Phase 5C: mirror PR #154 and production PR #463 delivered the current KVK Top 10 visual ranking
  card for `/kvk rankings type:kvk`. It was pushed to production, smoke tested successfully, and
  polished through production feedback.
- Phase 5D: mirror PR #155 and production PR #464 delivered the Hall of Fame records Top 10 visual
  cards for `/kvk rankings type:records`. It was pushed to production, smoke tested successfully,
  and polished through production feedback.
- Phase 5E: mirror PR #156 and production PR #465 delivered Honor and PreKvK Top 10 visual cards
  for `/kvk rankings type:honor` and `/kvk rankings type:prekvk`. It was pushed to production,
  smoke tested successfully, and completed review/smoke-test polish.
- Phase 5F-1: mirror PR #158 and production PR #466 delivered the private My Rank / Find Me flow
  for current KVK, Honor, and PreKvK rankings. It was pushed to production and smoke tested
  successfully.

Source programme documents:

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 5 Unified Rankings Visual UX Polish.md`
- `docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5E Honor and PreKvK Visual Ranking Cards.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Delivered Phase 5F-1 baseline:

- `/kvk rankings type` choices remain `kvk`, `honor`, `prekvk`, and `records`.
- Current-ranking modes use `kvk.models.kvk_rankings`, `kvk.services.kvk_rankings_service`,
  `kvk.rendering.kvk_rankings_embed`, `kvk.rendering.kvk_rankings_card_renderer`, and
  `ui.views.kvk_rankings_views.CurrentRankingsBrowserView`.
- Current KVK, Honor, PreKvK, and Hall of Fame records all have Top 10 visual cards with embed
  fallback.
- Top 25 and Top 50 remain compact unified browser output for current KVK, Honor, and PreKvK.
- Top 100 remains out of primary player controls.
- Records remain Top 10 only, single-KVK performances, not lifetime totals.
- Private My Rank is available for registered governors in current KVK, Honor, and PreKvK modes.
- My Rank supports single-account users, multi-account selection, not-ranked governors,
  unregistered users, missing source data, nearby rank context, and useful gap/context output.
- My Rank responses are private by default.
- My Rank text handling was hardened for registry/cache-sourced governor names, including
  whitespace/backtick normalisation and mention-token breaking.
- KVK current rankings are shaped from the stats cache with `STATUS = INCLUDED` and
  `Starting Power >= 40M`.
- Honor current rankings use latest imported Honor scan metadata and must preserve the
  no-admin-override KVK stats channel gate.
- PreKvK current rankings wrap `prekvk.report_service` for unified browser output.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` commands remain live.
- Legacy `/prekvk report` remains image-based.

## Copy/Paste Starter

```text
Codex, start Phase 5F-2 of the KVK Player Experience Redesign: CSV/full-list export polish for /kvk rankings.

Phase 5A is complete: mirror PR #152 and production PR #461 delivered `/kvk rankings type:records`
as the KD98 Hall of Fame Top 10 all-time single-KVK records foundation.

Phase 5B is complete: mirror PR #153 and production PR #462 delivered the unified current-ranking
browser for `/kvk rankings type:kvk`, `honor`, and `prekvk`, pushed it to production, and smoke
tested it successfully.

Phase 5C is complete: mirror PR #154 and production PR #463 delivered the current KVK Top 10
visual ranking card for `/kvk rankings type:kvk`, pushed it to production, smoke tested it
successfully, and completed follow-up polish.

Phase 5D is complete: mirror PR #155 and production PR #464 delivered the Hall of Fame records
Top 10 visual cards for `/kvk rankings type:records`, pushed them to production, smoke tested them
successfully, and completed follow-up polish.

Phase 5E is complete: mirror PR #156 and production PR #465 delivered Honor and PreKvK Top 10
visual cards for `/kvk rankings type:honor` and `/kvk rankings type:prekvk`, pushed them to
production, smoke tested them successfully, and completed review/smoke-test polish.

Phase 5F-1 is complete: mirror PR #158 and production PR #466 delivered private My Rank / Find Me
for current KVK, Honor, and PreKvK rankings, pushed it to production, and smoke tested it
successfully.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/reference/K98 Bot - Project Engineering Standards.md
- docs/reference/K98 Bot - Coding Execution Guidelines.md
- docs/reference/K98 Bot - Testing Standards.md
- docs/reference/K98 Bot - Skills & Refactor Triggers.md
- docs/reference/K98 Bot - Deferred Optimisation Framework.md
- docs/task_packs/KVK Player Experience Redesign - Programme Pack.md
- docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 5 Unified Rankings Visual UX Polish.md
- docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5E Honor and PreKvK Visual Ranking Cards.md
- docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5F CSV Full-List Export.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Current delivered context:
- `/kvk rankings type` choices are `kvk`, `honor`, `prekvk`, and `records`.
- Current-ranking modes use `kvk.models.kvk_rankings`, `kvk.services.kvk_rankings_service`,
  `kvk.rendering.kvk_rankings_embed`, `kvk.rendering.kvk_rankings_card_renderer`, and
  `ui.views.kvk_rankings_views.CurrentRankingsBrowserView`.
- Current KVK, Honor, PreKvK, and Hall of Fame records all have Top 10 visual cards with embed
  fallback.
- Top 25 and Top 50 remain compact unified browser output for current KVK, Honor, and PreKvK.
- Top 100 remains out of primary player controls.
- Records remain Top 10 only, single-KVK performances, not lifetime totals.
- Private My Rank is available for registered governors in current KVK, Honor, and PreKvK modes.
- My Rank responses are private by default.
- KVK current rankings are shaped from the stats cache with `STATUS = INCLUDED` and
  `Starting Power >= 40M`.
- Honor current rankings use latest imported Honor scan metadata and must preserve the
  no-admin-override KVK stats channel gate.
- PreKvK current rankings wrap `prekvk.report_service` for unified browser output.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` commands remain live.
- Legacy `/prekvk report` remains image-based.

Phase 5F-2 objective:
Design and implement the approved CSV/full-list export slice for `/kvk rankings` so players and
leadership have a clear deeper access path without reintroducing Top 100 as a primary player
control.

Scope:
1. Start with audit/scope and a proposed Phase 5F-2 implementation plan.
2. Confirm the first implementation slice before coding unless the operator explicitly approves
   one-pass delivery.
3. Audit current ranking payload/service support for full-list export in KVK, Honor, and PreKvK
   current rankings.
4. Validate SQL/cache/source assumptions against C:\K98-bot-SQL-Server where data contracts are
   SQL-backed or ambiguous.
5. Add a private-by-default CSV/full-list export path for current KVK, Honor, and PreKvK rankings.
6. Prefer an in-browser `Export CSV` or `Full List CSV` action over a new top-level command.
7. Keep Top 100 out of primary player controls.
8. Preserve private My Rank / Find Me from Phase 5F-1.
9. Preserve current KVK, Honor, PreKvK, and Hall of Fame Top 10 visual cards.
10. Preserve Top 25 and Top 50 compact browser output.
11. Preserve records Top 10 only. Records export is out of scope unless explicitly approved after
    audit.
12. Preserve Honor's no-admin-override KVK stats channel gate at command entry, browser refresh,
    and export interaction time.
13. Preserve legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report`.
14. Preserve image-based legacy `/prekvk report`.
15. Keep SQL/data access in service/DAL/cache layers. Do not put SQL in command, view, renderer,
    or export formatting modules.
16. Generate CSV in memory where practical; avoid temporary files unless justified.
17. Escape CSV cells that could be interpreted as formulas by spreadsheet software.
18. Keep CSV text safe for user-controlled governor names and source labels, including
    backticks/newlines/mentions/angle brackets where they appear in response text.
19. Include useful export context: mode, metric, generated timestamp/source freshness, rank,
    governor id, governor name, selected metric value, and mode-specific supporting values.
20. Handle missing source data, empty rankings, oversized exports, and Discord upload failures with
    private user-visible errors.
21. Capture any out-of-scope findings structurally.

Known out-of-scope follow-up already captured:
- Phase 5G wrap-up polish is complete:
  - Honor Top 25/Top 50 compact output displays values.
  - PreKvK Top 25/Top 50 compact output uses fixed-width alignment.
  - Compact rows preserve near-billion value units and align wide/special-character governor
    names by display width.
  - Current KVK Top 10 card podium ranks/text are centered to match Records, Honor, and PreKvK.
- Phase 5H performance optimisation remains active:
  - Ranking-card render/load latency should be profiled and optimised before Phase 5 closes.
- Legacy-ranking consolidation/deprecation remains separate and requires usage evidence plus
  rollout approval.
- Records export/detail output remains out of scope unless explicitly approved.
- Public scheduled exports, admin-only export reports, and website/webapp export surfaces are out
  of scope for this slice.

Likely touched areas:
- commands/kvk_cmds.py
- kvk/models/kvk_rankings.py
- kvk/services/kvk_rankings_service.py
- a new or existing KVK rankings CSV/export helper in the kvk service/rendering boundary
- kvk/rendering/kvk_rankings_embed.py only if response wording changes
- ui/views/kvk_rankings_views.py
- prekvk/report_service.py only if current full-list payload support needs a narrow adapter
- tests/test_kvk_cmds.py
- tests/test_kvk_rankings_service.py
- tests/test_kvk_rankings_browser_view.py
- tests/test_honor_rankings_view.py
- tests/test_prekvk_embed.py
- nearest CSV/export tests selected during audit
- docs/reference/canonical_command_reference.md if visible behaviour changes
- docs/reference/deferred_optimisations.md if new deferred work is found

Mandatory workflow:
1. Start with audit/scope and a proposed Phase 5F-2 implementation plan.
2. Confirm the implementation slice before coding unless the operator explicitly approves
   one-pass delivery.
3. Validate SQL/cache/source assumptions against C:\K98-bot-SQL-Server where data contracts are
   SQL-backed or ambiguous.
4. Implement only the approved Phase 5F-2 slice.
5. Add/update focused tests for KVK/Honor/PreKvK CSV exports, CSV content and filename shape,
   formula-injection escaping, missing/empty/oversized data paths, Discord file failure fallback,
   private response default, mode/metric switching, Honor channel-gate preservation, Top 100
   exclusion, My Rank preservation, records Top 10-only preservation, and legacy command
   preservation.
6. Run focused tests and standard validators.
7. Run or justify skipping Codex Security before PR handoff. This slice touches Discord
   interactions, file generation, user-controlled text, and export behavior, so Codex Security is
   expected unless the implementation is documentation-only.
8. Open a ready-for-review PR against `K98-bot-mirror`.

Suggested validation after implementation:
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_cmds.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_service.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_browser_view.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_honor_rankings_view.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_prekvk_embed.py
- nearest CSV/export tests selected during audit
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pre_commit run -a
- .\.venv\Scripts\python.exe -m pytest -q tests

Acceptance criteria:
- CSV/full-list export is delivered only for the approved Phase 5F-2 slice.
- Players have a clear deeper access path without reintroducing Top 100 as a primary control.
- Export responses are private by default.
- CSV output is deterministic, useful, and safely escaped for spreadsheet formula-leading cells.
- KVK, Honor, and PreKvK ranking semantics remain service-owned.
- Honor no-admin-override KVK stats channel gate remains preserved.
- Private My Rank / Find Me remains stable.
- Current KVK, Honor, PreKvK, and Hall of Fame records Top 10 cards remain stable.
- Top 25 and Top 50 compact browser output remains available.
- Records remain Top 10 only.
- Legacy ranking commands remain live.
- Legacy `/prekvk report` remains image-based.
- Commands and views stay thin.
- No SQL is added to command, view, renderer, or export formatting modules.
- Focused tests and standard validators pass.
- Codex Security is run or explicitly justified.
- Remaining Phase 5H deferred work stays captured structurally.
```
