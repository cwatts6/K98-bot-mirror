# PR1 — Interaction safety extraction

## Overview
This PR extracts cross-cutting interaction reliability helpers from `Commands.py` into `core/interaction_safety.py` with no intended behavior changes.

## New module API (`core/interaction_safety.py`)
- `safe_defer(ctx, ephemeral=True) -> bool`
  - Best-effort defer helper.
  - Returns `True` when defer call is made, `False` when interaction is already done/expired or defer is unavailable.
- `safe_command(fn)`
  - Decorator wrapper for command handlers.
  - Catches unexpected exceptions, logs `[CMD ERROR]`, and sends the same ephemeral fallback user message used previously.
- `global_cmd_error_handler(ctx, error)`
  - Global command error listener body used by command registration.
- `get_operation_lock(key) -> asyncio.Lock`
  - Shared lock registry accessor for operation-scoped serialization.
  - Preserves lock behavior previously provided by `_op_locks`.

## Commands integration
- `Commands.py` now imports these helpers from `core.interaction_safety`.
- Existing command definitions and decorator usage remain unchanged (`@safe_command`, `await safe_defer(...)`).
- Global error listener wiring now references `global_cmd_error_handler`.
- Existing operation lock usage for resync flow is routed via `get_operation_lock("resync")`.

## Behavioral guarantees
- No command names/options changed.
- No persistence paths/schemas changed.
- No user-facing fallback error/defer messaging changed.


## Local deployment/test/validation quickstart
- Validate syntax: `python -m py_compile Commands.py core/interaction_safety.py`
- Run focused tests: `pytest -q tests/test_interaction_safety.py`
- Optional broader checks (requires `pytest-asyncio` in environment):
  - `pytest -q tests/test_mykvktargets.py tests/test_mykvkstats.py`
