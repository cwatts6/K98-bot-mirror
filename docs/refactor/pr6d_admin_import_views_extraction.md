# PR 6D — Admin/import confirmation views extraction

Moved admin/import confirmation UI classes from `Commands.py` to `ui/views/admin_views.py`:

- `ConfirmRestartView`
- `ConfirmImportView`

## Wiring details

- `ConfirmRestartView` now lives in `ui/views/admin_views.py` and retains admin-only gating via `ADMIN_USER_ID`.
- `ConfirmImportView` now accepts an injected async callback `on_confirm_apply(interaction)` so command-layer import application logic remains in `Commands.py`.
- `Commands.py` imports these classes from `ui.views.admin_views` and no longer defines local duplicates.

## Validation

- `python -m py_compile Commands.py ui/views/admin_views.py tests/test_admin_views_smoke.py`
- `pytest -q tests/test_admin_views_smoke.py tests/test_location_views_smoke.py tests/test_subscription_views.py tests/test_registry_views_smoke.py tests/test_ui_imports.py`
