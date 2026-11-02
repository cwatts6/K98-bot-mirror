# PR 6C — Location UI extraction

Moved location-related UI classes from `Commands.py` to `ui/views/location_views.py`:

- `_LocationSelect`
- `LocationSelectView`
- `RefreshLocationView`

## Wiring approach

`ui/views/location_views.py` now uses callback/config injection through:

- `configure_location_views(...)`

Injected responsibilities include:

- profile selection rendering callback
- refresh trigger callback (`find-all` sender)
- refresh wait callback (event wait with timeout)
- refreshed embed builder callback
- permission/rate-limit/concurrency callbacks

This keeps runtime state and locks in `Commands.py` module scope while reusing one canonical location UI module.

## Validation

- `python -m py_compile Commands.py ui/views/location_views.py tests/test_location_views_smoke.py`
- `pytest -q tests/test_location_views_smoke.py tests/test_ui_imports.py tests/test_registry_views_smoke.py`
