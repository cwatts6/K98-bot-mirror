# 🧭 Startup Runbook — Bot Boot Sequence & Logging Initialization

File: `docs/runbook_startup.md`  
Audience: Developers & maintainers of the K98 Discord Bot  
Last Updated: 2025-10-19

---

Purpose
- Describe the exact startup sequence implemented in the repository.
- Document logging initialization, early guards, and lock/marker files.
- Provide troubleshooting steps and operational guidance for starting the bot safely.

Summary (one-line)
- Process start → logging_setup import (queue logging) → env & watchdog checks → singleton lock + pid write → import bot instance → register commands → bot.run() → bot_instance.on_ready() → full startup sequence (caches, background tasks, TaskMonitor).

Quick start (how ops typically launch)
- Production: launch via the project's watchdog wrapper (WATCHDOG_RUN=1). It ensures supervised restarts and sets the expected environment.
- Developer local: set WATCHDOG_RUN=1 for parity or run smoke-imports for import-only checks.

1) Import-time logging initialization
- logging_setup is imported early. It:
  - Ensures LOG_DIR exists and initializes file handlers:
    - log.txt (INFO+)
    - error_log.txt (WARNING+)
    - crash.log (ERROR+)
  - Attaches a QueueHandler to route logs to a QueueListener that writes to files.
  - Replaces sys.stdout / sys.stderr with StreamToLogger so print() goes to the logging queue.
- DL_bot.py will add an explicit console handler that writes to logging_setup.ORIG_STDOUT when LOG_TO_CONSOLE is enabled.

2) Environment & preflight checks (DL_bot.py)
- Loads .env with dotenv early.
- WATCHDOG_RUN guard: process exits if WATCHDOG_RUN != "1" unless running in SMOKE_IMPORTS / DEBUG mode.
- TOKEN presence: DISCORD_BOT_TOKEN is required for normal operation; DL_bot.py will exit if missing.
- IDLE detection: prevents accidental runs from IDLE (idlelib present).
- Windows venv check: on Windows, DL_bot.py compares sys.executable against the project's venv path and exits if mismatch.
- Discord UI shadowing check: code verifies discord.ui.Button is a class to detect accidental name collisions.
- PID file: DL_bot.py writes a pid file atomically (tmp + os.replace). Location: constants.BOT_PID_PATH (see constants.py).

3) Singleton lock
- acquire_singleton_lock(BOT_LOCK_PATH) prevents concurrent bot processes.
- On shutdown, release_singleton_lock is invoked; if a lock remains after crash, boot_safety will log warnings and throttle certain startup behaviors.

4) Bot object and command registration
- DL_bot.py imports the preconfigured bot instance from bot_instance (from bot_instance import bot).
- register_commands(bot) is called before bot.run() to register command handlers locally and update the command cache (constants.COMMAND_CACHE_FILE).
- On start, bot_instance.on_ready() compares signatures and optionally syncs commands to a GUILD_ID.

5) Fast-path message handlers (DL_bot.py)
- Several ingestion fast-paths run in on_message to accept file uploads without the full command flow:
  - PLAYER_LOCATION_CHANNEL_ID
  - PREKVK_CHANNEL_ID
  - HONOR_CHANNEL_ID
  - ACTIVITY_UPLOAD_CHANNEL_ID
  - FORT_RALLY_CHANNEL_ID
  - PROKINGDOM_CHANNEL_ID
- These handlers enqueue work into per-channel queues (live_queue/QUEUE_CACHE_FILE) monitored by queue_worker tasks.

6) on_ready / full startup (bot_instance.py)
- full_startup_sequence runs under a claim_once gate.
- Key actions:
  - Install asyncio loop exception handler.
  - Start heartbeat task (LOG_DIR/heartbeat.json).
  - Start health dashboard and probe tasks (DB, GSheets).
  - Refresh and load event cache (event_cache.refresh_event_cache()).
  - Rehydrate live event views if present (rehydrate_live_event_views()).
  - Start TaskMonitor tasks: queue workers, daily summary, reminder cleanup, connection watchdog, cache warmers.
  - Notify ADMIN_USER_ID via DM that the bot started.

7) Task supervision (TaskMonitor)
- TaskMonitor creates named tasks (task_monitor.create(name, factory)) and auto-restarts with backoff on unhandled exceptions.
- On shutdown the TaskMonitor is stopped and tasks are cancelled/cooperatively awaited.

8) Logging & STDOUT handling
- logging_setup provides:
  - logging_setup.flush_logs() — wait for the queue to drain (safe to call before stopping listener).
  - logging_setup.shutdown_logging() — stop QueueListener and close file handlers (idempotent).
- DL_bot.py registers safe excepthooks to avoid recursive logging during process-level failures.

9) Common startup issues & actions
- Missing WATCHDOG_RUN — set WATCHDOG_RUN=1 or run the watchdog wrapper.
- Missing DISCORD_BOT_TOKEN — add to .env or vault.
- Stale BOT_LOCK_PATH — ensure no process running and remove lock file.
- Command sync skipped — set GUILD_ID to enable guild-scoped sync or review COMMAND_CACHE_FILE.
- No logs — inspect LOG_DIR, ensure file permissions, call logging_setup.flush_logs() to force disk writes.

10) Operational tips
- For debug: set LOG_TO_CONSOLE=1 to add an ORIG_STDOUT console handler (be careful: console echo may block).
- For CI/validation: use scripts/smoke_imports.py which sets protective env flags to prevent side effects.
- To validate environment variables locally: run scripts/config_self_test.py which reports missing/invalid values.

Appendix: Files & constants to inspect
- constants.BOT_LOCK_PATH, constants.BOT_PID_PATH, constants.COMMAND_CACHE_FILE, constants.QUEUE_CACHE_FILE, constants.LAST_SHUTDOWN_INFO, LOG_DIR, DATA_DIR.

Recommended improvements (short list)
- Centralize env validation in a single validate_env() helper and call it at DL_bot.py start.
- Document the watchdog wrapper and include a sample systemd/service file.
- Add a short "preflight" script that validates the runtime environment and permissions.
