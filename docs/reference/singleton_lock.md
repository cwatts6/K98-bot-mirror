# Singleton Lock

Purpose: document the lock helper that prevents concurrent bot/watchdog instances.

## Main API

```python
from singleton_lock import acquire_singleton_lock, release_singleton_lock
```

Acquire:

```python
acquire_singleton_lock(BOT_LOCK_PATH)
```

Release:

```python
release_singleton_lock(BOT_LOCK_PATH)
```

## Behaviour

- Default production behaviour exits quietly on conflict.
- Tests can use `exit_on_conflict=False`.
- Callers can use `raise_on_conflict=True` when they need an exception.
- Lock metadata includes PID, executable, working directory, creation time, and format version.
- The helper uses `psutil` when available and falls back to platform process checks.
- The lock file is written atomically when possible.

## Runtime Use

- `DL_bot.py` uses `BOT_LOCK_PATH`.
- `run_bot.py` uses the watchdog lock path.
- Constants are defined in `constants.py`.

## Testing

Use temporary paths and avoid default `sys.exit` behaviour:

```python
meta = acquire_singleton_lock(path, exit_on_conflict=False)
release_singleton_lock(path)
```

Relevant tests include `tests/test_singleton_lock_Version2.py`.

## Operational Notes

If startup reports a stale lock:

1. Confirm no bot/watchdog process is running.
2. Preserve lock metadata if it may help diagnose a crash.
3. Remove the stale lock only after process state is understood.
