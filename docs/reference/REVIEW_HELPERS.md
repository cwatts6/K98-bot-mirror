# Helper Files Review Guide

Note: some helper filenames in this codebase intentionally retain legacy naming quirks (for example, `decoraters.py`); treat those names as canonical unless the change explicitly renames them.

Purpose: make reviews of shared helper modules repeatable and prevent duplicate utility code.

## Core Helper Files

Check these before adding or changing helper logic:

- `file_utils.py`
- `utils.py`
- `startup_utils.py`
- `bot_helpers.py`
- `target_utils.py`
- `embed_utils.py`
- `decoraters.py`
- `bot_config.py`
- `constants.py`
- `process_utils.py`
- `logging_setup.py`
- `account_picker.py`
- `core/interaction_safety.py`

If the change touches reminders or scheduling, also review:

- `event_scheduler.py`
- `event_calendar/`
- `subscription_tracker.py`
- `reminder_task_registry.py`

## Review Checklist

1. Responsibility
   - Does the helper belong in the file being changed?
   - Should it live in `core/`, `file_utils.py`, `process_utils.py`, or a subsystem service instead?

2. Duplication
   - Search for existing functions with similar names or literals.
   - Reuse or consolidate before adding a new helper.

3. Imports
   - Watch for circular imports around `bot_instance.py`, `DL_bot.py`, and `utils.py`.
   - Prefer local imports only when they intentionally break a cycle.

4. Error handling and logging
   - Use module loggers.
   - Do not swallow exceptions silently.
   - Do not log secrets.

5. API stability
   - Preserve public helper signatures where practical.
   - Prefer adding a compatible wrapper over breaking existing callers.

6. Time handling
   - Persist UTC.
   - Use `datetime.now(UTC)`.
   - Format for Discord at the rendering boundary.

7. Concurrency and file safety
   - Preserve atomic writes and lock semantics.
   - Avoid blocking I/O inside async functions unless offloaded.

8. Tests
   - Add focused unit tests for non-trivial helper behaviour.
   - Update existing tests when helper ownership changes.

## Useful Searches

```powershell
rg "def <function_name>" .
rg "<unique literal or behaviour>" .
python scripts/find_similar_helpers.py --min-score 0.85
```

## When Duplication Is Found

- Prefer migrating callers to the canonical helper.
- Keep a thin compatibility wrapper only when needed.
- Capture broader cleanup through the Deferred Optimisation Framework when consolidation is too large for the task.
