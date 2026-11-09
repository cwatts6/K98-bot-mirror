# PR2 — Event view extraction (`NextFightView` / `NextEventView`)

## What changed
- Moved event view classes out of `Commands.py` into:
  - `ui/views/events_views.py`
- Added compatibility re-export in `Commands.py`:
  - `from ui.views.events_views import NextEventView, NextFightView`

## Compatibility guarantees
- `/nextfight` and `/nextevent` continue to instantiate the same class names.
- `command_regenerate.py` imports (`from Commands import NextEventView, NextFightView`) continue to work through re-export.
- `LocalTimeToggleView` remains in `embed_utils.py` (unchanged location).
- Custom ID/prefix path remains based on `LocalTimeToggleView` deterministic `"{sanitized_prefix}_local_time_toggle"` behavior.
- No tracker schema/key changes.

## Local deployment / validation
- Syntax check:
  - `python -m py_compile Commands.py ui/views/events_views.py command_regenerate.py`
- Focused tests:
  - `pytest -q tests/test_events_views.py`
- Optional runtime smoke:
  1. Start bot.
  2. Run `/nextfight` and `/nextevent`.
  3. Click toggle buttons to verify pagination/toggle behavior.
  4. Restart bot and confirm tracked nextfight/nextevent messages rehydrate normally.
