```markdown
# singleton_lock usage

This document describes the repository's singleton lock helper and how to use it.

## Purpose

The singleton lock file prevents more than one instance of the bot (or other process) from
running concurrently. The lock file contains minimal JSON metadata that can be inspected
by operators:

- pid: process id that created the lock
- created: epoch seconds when the lock was created
- exe: absolute path to the Python executable that created the lock
- cwd: working directory at the time of lock creation
- version: format version (currently `1`)

Lock files live under `LOG_DIR` by default (see `constants.py`), for example:
`<repo_root>/logs/BOT_LOCK.json`.

## API

Import:

```python
from singleton_lock import acquire_singleton_lock, release_singleton_lock
```

Acquire the lock:

```python
acquire_singleton_lock(BOT_LOCK_PATH)
```

Default behaviour is intentional for the bot startup path:
- If another instance is detected to be running, `acquire_singleton_lock` will
  call `sys.exit(0)` (so the process exits quietly).

If you need different behaviour in tests or libraries:

```python
# Do not exit on conflict; raise instead so tests can assert
try:
    acquire_singleton_lock(BOT_LOCK_PATH, exit_on_conflict=False, raise_on_conflict=True)
except RuntimeError:
    # handle conflict
    ...
```

Release the lock:

```python
release_singleton_lock(BOT_LOCK_PATH)
```

## Notes & recommendations

- The function uses `psutil` if available for robust process inspection; otherwise it falls
  back to `os.kill(pid, 0)` on platforms that support it.
- The lock file is written atomically when possible using `file_utils.atomic_write_json`.
- Calling code should keep the default behaviour for production (so the watchdog / launcher
  semantics remain unchanged). Use `exit_on_conflict=False` in tests to avoid `sys.exit`.
- The lock file format includes a `version` field to support future migrations.

## Testing

- Tests should use temporary directories and call `acquire_singleton_lock` with
  `exit_on_conflict=False` to avoid exiting the test runner.
- Use monkeypatching to simulate `psutil` behaviours if needed.

## Example (DL_bot.py)

`DL_bot.py` currently calls:

```python
from singleton_lock import acquire_singleton_lock, release_singleton_lock
acquire_singleton_lock(BOT_LOCK_PATH)
...
release_singleton_lock(BOT_LOCK_PATH)
```

This file kept default semantics to preserve previous behaviour — when the bot is started
without the watchdog, the existing checks will still trigger the same exit behavior.
```
