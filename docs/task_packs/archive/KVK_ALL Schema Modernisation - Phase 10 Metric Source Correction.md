# KVK_ALL Schema Modernisation - Phase 10 Metric Source Correction

Status: archived completed reference. Phase 10 is complete and smoke tested, and the overall
KVK_ALL Schema Modernisation programme is closed through Phase 11. This file is retained as
historical metric source-correction context.

## Purpose

Phase 10 corrects the Full Data v2 recompute source rules after production smoke showed
zero diff fields masking changed cumulative endpoint values across scans.

The authoritative workbook tab remains `Full Data`. `Basic Data` remains intentionally
ignored.

## Corrected Source-Of-Truth Decisions

### Configured Windows

For `kvk_all_full_data_v2` rows, configured windows such as Pass 4 use cumulative
endpoint deltas across the configured scan range:

- `max_kill_points`
- `max_kills_iv`
- `max_kills_v`
- `max_dead`
- `max_units_healed`
- `max_max_contribute`
- `max_cur_contribute`

For example, Pass 4 `kp_gain` is `End.max_kill_points - Start.max_kill_points`
when both endpoint values are available.

Legacy diff fields remain fallback inputs for older rows where the endpoint columns are
not available:

- `kill_points_diff` / `points_difference`
- `kills_iv_diff`
- `kills_v_diff`
- `dead_diff`
- `healed_troops` / `max_units_healed_diff`
- `max_contribute_diff`
- `cur_contribute_diff`

Zero diff fields are not authoritative for Full Data v2 configured windows when
cumulative endpoints are present.

### Baseline

`Baseline` output rows remain validation rows with zero gains and fixed
`starting_power`.

### Full

`Full` output rows represent baseline-to-latest values. For Full Data v2 rows, `Full`
uses the player's baseline scan endpoint and latest scan endpoint when both are
available. If endpoint values are unavailable, the legacy latest-snapshot diff fields
remain the compatibility fallback.

## Compatibility

Older 22-column Full Data workbooks do not contain raw endpoint families. Those rows
continue to use legacy diff fields, preserving existing pre-v2 recompute semantics.
