# 🧭 Repository Structure — Where things live and why

File: `docs/runbook_structure.md`  
Audience: New developers and maintainers  
Last Updated: 2025-10-19

---

Purpose
- Map the repo layout and describe responsibilities of top-level modules to speed onboarding and reduce navigation time.

Top-level (important files & directories)
- DL_bot.py — process entrypoint, signal wiring, singleton lock and PID management, some on_message fast-paths.
- bot_instance.py — bot object, on_ready lifecycle, full_startup_sequence, TaskMonitor orchestration, client teardown.
- logging_setup.py — queue-based logging initialization and helpers (flush/shutdown), log file paths.
- boot_safety.py — headless mode patches for matplotlib/PIL and stale-lock detection.
- bot_config.py — environment loader, typed env helpers, default config and __all__ exports.
- Commands.py / cogs/ — slash commands and command registration.
- event_cache.py / event_scheduler.py / event_embed_manager.py — event & reminder pipelines.
- docs/ — textual runbooks (startup, shutdown, devops, diagnostics, structure, honor_scan).
- scripts/ — utility scripts such as smoke_imports.py and config_self_test.py.
- constants.py — paths & filenames (LOG_DIR, DATA_DIR, QUEUE_CACHE_FILE, COMMAND_CACHE_FILE, BOT_LOCK_PATH, etc.)

Module guide (short)
- logging_setup.py
  - Creates LOG_DIR and sets up SafeRotatingFileHandler handlers.
  - Starts a QueueListener; provides flush_logs() and shutdown_logging() helpers.
- bot_instance.py
  - Creates the Bot instance, registers cogs, and defines on_ready and shutdown handlers.
  - Manages TaskMonitor and background loops.
- DL_bot.py
  - Process-level tasks: preflight checks, lock acquisition, pid write, wiring signals, final logging shutdown.

Where to look for specific behaviors
- Command sync and signature persistence: Commands.py and constants.COMMAND_CACHE_FILE.
- Per-channel ingestion logic: DL_bot.py (on_message fast-paths and queue enqueuing).
- Event rehydration: event_cache.py, event_embed_manager.py, and event_scheduler.py.

Developer onboarding checklist
1. Clone repo and create virtualenv: python -m venv venv && . venv/bin/activate
2. Install dev requirements: pip install -r requirements.txt
3. Run smoke imports locally: python scripts/smoke_imports.py
4. Set WATCHDOG_RUN=1 and DISCORD_BOT_TOKEN for local integration or use NO_DISCORD_LOGIN env for offline tests.
5. Read docs/runbook_startup.md and runbook_shutdown.md for lifecycle expectations.
