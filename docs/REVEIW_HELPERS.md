# Helper Files Review Guide

Purpose
- Make reviews of core helper modules repeatable and thorough.
- Ensure duplication, inconsistent logic, and incorrect imports are caught.
- Provide a reference mapping of responsibilities so reviewers know where to put/fix functionality.

Core helper files (check these first)
- constants.py
- utils.py
- startup_utils.py
- file_utils.py
- bot_helpers.py
- target_utils.py
- embed_utils.py
- decoraters.py
- bot_config.py
- DL_bot.py
- bot_instance.py
- process_utils.py
- logging_setup.py

If the change touches scheduling/reminder logic, also check:
- event_scheduler.py
- event_embed_manager.py
- subscription_tracker.py
- reminder_task_registry.py

Review checklist (use for every PR touching helper code)
1. Responsibility
   - Does this function belong in the file where it was changed/added?
   - If not, where should it live? (utils.py/file_utils.py/process_utils.py are canonical for I/O/OS/DB/process helpers.)

2. Duplication
   - Is there an existing function that does the same or similar work?
   - If similar but not identical, are the differences intentional and documented?
   - Ensure only one canonical implementation remains; add thin wrappers if needed for backward compatibility.

3. Imports / circular dependencies
   - Are imports top-level? Could importing this module cause circular imports (common with bot_instance <-> utils)?
   - Prefer lazy imports (inside functions) where necessary to break cycles.
   - Check use of from X import Y vs import X — prefer module-level import when many symbols are needed.

4. Error handling and logging
   - Are exceptions handled consistently (log or re-raise with context)?
   - Avoid swallowing exceptions silently; follow repo patterns for logging.
   - Sensitive values (tokens, passwords) should not be logged.

5. API & signatures
   - Keep public helper function signatures stable; prefer adding new function rather than mutating an existing one in incompatible ways.
   - Add/maintain docstrings and type hints.

6. Timezones / datetime handling
   - Ensure consistent use of timezone-aware datetime objects (this repo uses UTC helpers).
   - Verify conversions use the shared helpers (utcnow(), ensure_aware_utc(), format_time_utc).

7. Concurrency safety
   - For file/lock operations, ensure atomic semantics are preserved (e.g., atomic_write_json, acquire_lock).
   - For shared state (caches, registries), ensure thread-safety or documented single-thread assumptions.

8. Tests & small examples
   - Add a unit test for new helper behavior (or at least a snippet) when logic is nontrivial.
   - Add a short changelog note in the PR describing the intended surface change.

Quick commands for reviewers
- Search for similar function names:
  - git grep -n "def <function_name>" or git grep -n "function_name("
- Search for duplicated code/token overlap:
  - git grep -n "some unique literal or regex"
- Run the included similarity script (repo root):
  - python3 scripts/find_similar_helpers.py --min-score 0.85

Automation recommendations
- Add CI job "helper-sanity" to run:
  - ruff/flake8 (style), mypy (types), bandit (security)
  - scripts/find_similar_helpers.py to detect suspicious duplicates
- Add CODEOWNERS entries for helper files so core reviewers are automatically requested.
- Add PR template reminding authors to run local checks and document helper file impacts.

Mapping & ownership (example)
- constants.py — environment & path constants, connection factories
- file_utils.py — atomic file I/O, locking, and process wrappers
- utils.py — general helpers (time, queues, formatting)
- process_utils.py — psutil/os wrappers for PID/process checks
- startup_utils.py — startup & migration helpers
- embed_utils.py — building/sending embeds and embed views
- bot_helpers.py — higher-level bot orchestration helpers
- target_utils.py — target lookups and name cache (SQL-backed)
- logging_setup.py — centralized logging/queue/listener handling
- reminder_* and event_* files — scheduling, persistence, DM/alert logic

How to handle discovered duplication
1. If duplicate exists:
   - Prefer migrating callers to the canonical helper.
   - Add a tiny shim (deprecated) that wraps the canonical implementation, log a TODO and add a test.
2. If both are kept for compatibility, document in the file why duplication exists and add a TODO/issue to consolidate.
