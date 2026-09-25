# Codex Chat Starter - KVK Targets Quality Phase 2

Status: archived completed starter. Phases 2A-2F shipped through mirror PRs #237-#242,
production PRs #544-#549, and Phase 2A SQL PR #74. Final Phase 2F production smoke was operator
accepted on 2026-08-28 after history, targets, stats, CrystalTech, and shared account-picker flows
passed with clear logs. The docs-only closeout found no new Phase 2 requirement or active
target-subsystem deferred optimisation. This prompt is retained as historical execution context;
future target work requires a fresh task pack.

## Copy/Paste Starter (Historical)

Codex, continue the final Phase 2F wrap-up defined in:

`docs/task_packs/archive/Codex Task Pack - KVK Targets Quality Phase 2.md`

Phases 2A through 2E are deployed, smoke tested, and operator accepted. Preserve their complete
contract: immutable target rows, the single service-owned target payload, cache schema version 2,
bounded crash-recoverable target single-flight coordination, explicit fighting-lifecycle names,
and lifecycle SQL ownership under `kvk/dal/kvk_lifecycle_dal.py`.

Phase 2F is the separately approved final runtime and documentation closeout. Its runtime PR must:

1. Fix `/kvk history` summary-rank retrieval so the Python batch uses `SET NOCOUNT ON` and advances
   through bounded non-row result sets before `fetchall()`, while preserving the current rankless
   card/embed fallback on a genuine SQL failure.
2. Remove the proved-unused `last_kvk_map` compatibility parameter and `_last_kvk_map` field only
   from `AccountPickerView` and the KVK targets selector path. Do not change the separate,
   live `/kvk stats` last-KVK comparison state.
3. Move the root `kvk_ui.py` KVK targets selector implementation to
   `ui/views/kvk_targets_views.py`, update the command import, and preserve account selection,
   direct lookup, registration, refresh, timeout, visibility, and error behavior.
4. Add focused DAL, service-fallback, account-picker, targets-view, and command-boundary tests.
5. Update active delivery documentation to record Phases 2A-2E as accepted and Phase 2F as pending
   production review/smoke.

Non-negotiable constraints:

- Do not change target formulas, values, thresholds, populations, exemptions, publication states,
  fixed Official identity, cache schema, or cache safety behavior.
- Do not change `DRAFT / ACTIVE / ENDED` values, Pass 4/end thresholds, broad-window semantics, or
  any stats-alert, daily-overview, history-finalisation, or leadership-finalisation timing.
- Preserve `/kvk targets` arguments, decorators, permissions, channel, visibility, command count,
  registration, numeric/name behavior, account selection, modern image, and fallback embed.
- Make no SQL repository change. Validate the existing
  `dbo.usp_GetKvkHistorySummaryMetricRanks` contract and record a SQL documented skip.
- Run the bot `Changes review` with `Deep Off`; do not start a standard or deep codebase audit.
- Do not archive this starter/task pack or remove the deferred item in the runtime PR.

After the runtime PR was promoted, deployed, and its Discord smoke was operator accepted, the
approved separate docs-only closeout:

- archives this task pack and starter under `docs/task_packs/archive/`;
- removes the resolved account-picker/targets `_last_kvk_map` item from the active deferred register;
- records Phase 2 completion in `docs/reference/archive/deferred_optimisations_resolved.md`;
- updates the developer quickstart, publication contract, and active/archive task-pack indexes with
  the final mirror PR, production PR, deployment, and smoke evidence;
- completes a follow-up target-scope review and states whether any new Phase 2 requirement or active
  target deferred optimisation remains.

This historical starter's stop point was satisfied. The runtime and docs-only closeout gates are
complete; do not continue the programme as Phase 2G.
