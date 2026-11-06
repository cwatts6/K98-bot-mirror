# PR 6E — Stats UI extraction

Moved stats ranking UI class from `Commands.py` to `ui/views/stats_views.py`:

- `KVKRankingView`

## Wiring

- `ui/views/stats_views.py` imports pure embed helpers from `build_KVKrankings_embed`:
  - `build_kvkrankings_embed`
  - `filter_rows_for_leaderboard`
- `Commands.py` now imports `KVKRankingView` from `ui.views.stats_views` and uses it in `/kvk_rankings`.

## Validation

- `python -m py_compile Commands.py ui/views/stats_views.py tests/test_stats_views_smoke.py tests/test_kvkrankingview.py`
- `pytest -q tests/test_stats_views_smoke.py tests/test_kvkrankingview.py tests/test_ui_imports.py`
