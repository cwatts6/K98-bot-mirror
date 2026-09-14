# PR6 — UI domain-module extraction (phase)

## What this PR does
- Adds requested domain modules:
  - `ui/views/registry_views.py`
  - `ui/views/stats_views.py`
  - `ui/views/admin_views.py`
  - `ui/views/location_views.py`
- Moves the following classes out of `Commands.py`:
  - `LogTailView` -> `ui/views/admin_views.py`
  - `OpenFullSizeView`, `ProfileLinksView` -> `ui/views/location_views.py`
- Updates `Commands.py` imports to consume moved classes from UI modules.
- Adds `tests/test_ui_imports.py` to:
  - import all domain view modules
  - ensure import graph is healthy in test env
  - instantiate moved views successfully

## Notes
- Persisted view classes remain unchanged (`LocalTimeToggleView` path and event views remain stable).
- No tracker schema/key changes.
- This is a phased extraction; additional `Commands.py`-embedded classes remain and are addressed in follow-up slices.

## Local validation
- `pytest -q tests/test_ui_imports.py tests/test_events_views.py tests/test_embed_utils_target_lookup_injection.py`
- `python -m py_compile Commands.py ui/views/admin_views.py ui/views/location_views.py ui/views/registry_views.py ui/views/stats_views.py tests/test_ui_imports.py`
