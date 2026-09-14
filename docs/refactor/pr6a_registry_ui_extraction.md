# PR6A — Registry UI extraction to `ui/views/registry_views.py`

## Scope completed
Moved registry-related UI classes from `Commands.py` to `ui/views/registry_views.py`:
- `MyRegsActionView`
- `GovNameModal`
- `RegisterStartView`
- `ModifyStartView`
- `EnterGovernorIDModal`
- `GovernorSelect`
- `GovernorSelectView`

## Wiring approach
- `Commands.py` now imports the classes from `ui.views.registry_views`.
- `ui/views/registry_views.py` uses callback/config injection (`configure_registry_views(...)`) for command-layer dependencies.
- No `Commands` imports exist in any `ui/` module.

## Behavior notes
- Author gating, ephemeral responses, timeout disable behavior, and labels were preserved.
- Governor ID normalization in modal/select uses `normalize_governor_id`.

## Validation
- `pytest -q tests/test_registry_views_smoke.py tests/test_ui_imports.py tests/test_commands_ui_helpers_present.py tests/test_events_views.py tests/test_embed_utils_target_lookup_injection.py`
- `python -m py_compile Commands.py ui/views/registry_views.py tests/test_ui_imports.py tests/test_registry_views_smoke.py`
