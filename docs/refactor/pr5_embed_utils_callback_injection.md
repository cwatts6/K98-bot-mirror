# PR5 — Break `embed_utils` → `Commands` dependency

## Change summary
- Refactored `embed_utils.TargetLookupView` to use injected callback pattern.
- Constructor now takes:
  - `on_lookup: Callable[[discord.Interaction, str], Awaitable[None]]`
- Replaced internal direct import/call:
  - Removed `from Commands import mykvktargets`
  - Replaced with `await self.on_lookup(interaction, governor_id)`

## Why
This removes UI dependency on the command module and prevents circular-import coupling while preserving target lookup behavior.

## Behavioral expectations
- No label changes.
- No target lookup logic changes.
- No persistence schema changes.

## Local validation
- `pytest -q tests/test_embed_utils_target_lookup_injection.py`
- `python -m py_compile embed_utils.py`
- Manual flow checks:
  - `/mykvktargets`
  - fuzzy lookup selection
  - post-selection actions
