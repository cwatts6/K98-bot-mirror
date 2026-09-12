# KVK_ALL Schema Modernisation - Phase 4 Metric Source Rules

## Purpose

Phase 4 modernises recompute behaviour for the Full Data v2 workbook while preserving current export, Google Sheets, and Discord reporting contracts.

The authoritative workbook tab is `Full Data`. `Basic Data` remains intentionally ignored.

## Source-Of-Truth Decisions

### Kill Points

`kill_points_diff` is the Full Data v2 semantic source for cumulative kill points.

`points_difference` is retained as the legacy compatibility field. Phase 4 recompute may use `points_difference` as a fallback when `kill_points_diff` is null so older staged rows remain compatible.

The sample workbook shows `points_difference` and `kill_points_diff` matching across all inspected Full Data rows.

### Healed Troops

`healed_troops` is the Full Data v2 semantic source for cumulative healed troops displayed downstream.

`max_units_healed_diff` is retained as the legacy compatibility field. Phase 4 recompute may use `max_units_healed_diff` as a fallback when `healed_troops` is null.

The sample workbook shows `max_units_healed_difference`, `max_units_healed_diff`, and `healed_troops` matching across all inspected Full Data rows after numeric coercion.

### Raw Min/Max Metrics

Raw min/max metric columns are validation and reconciliation inputs in Phase 4, not replacements for established downstream output fields.

Where legacy diff columns are present, recompute keeps the current downstream semantics. Raw min/max pairs may be used as fallback inputs only when the matching diff field is null and both endpoints are present.

This applies to:

- `min_kill_points` / `max_kill_points`
- `min_dead` / `max_dead`
- `min_units_healed` / `max_units_healed`
- `min_kills_iv` / `max_kills_iv`
- `min_kills_v` / `max_kills_v`
- `min_max_contribute` / `max_max_contribute`
- `min_cur_contribute` / `max_cur_contribute`

### Contribution Metrics

Contribution metrics are recomputed into internal windowed SQL outputs in Phase 4:

- `max_contribute_gain`
- `cur_contribute_gain`

They are not added to Discord reporting display, Google Sheets tab names, or export result-set ordering in Phase 4. Reporting and export presentation changes remain assigned to later programme phases.

## Performance Rule

Phase 4 keeps the existing full-refresh recompute model but preserves the current batched delete for `KVK_Player_Windowed`, which is the largest output table. Any broader incremental recompute design remains outside Phase 4.
