# ENV_REFERENCE — Environment variables & runtime configuration

File: `docs/ENV_REFERENCE.md`  
Location: docs/ENV_REFERENCE.md  
Last updated: 2025-10-19

Purpose
- A single authoritative reference for environment variables used by the K98 bot.
- Describe type, required/optional status, example values, security notes, and where each variable is consumed in the codebase.
- Use this doc to build `.env` files, systemd unit EnvironmentFile entries, or container environment specifications.

How to read this file
- Variables are grouped by importance: Required, Recommended, Optional, Debug/Test.
- Each entry shows: name, type, example, default (if any), where used (code pointers), and notes (security/format).
- For variables not listed here consult `bot_config.py` and `constants.py` for additional constants (these files define runtime file paths and many internal constants).

Quick summary — most important variables
- DISCORD_BOT_TOKEN (required) — the bot token (secret).
- WATCHDOG_RUN (strongly recommended in production) — ensures the bot is launched under the project's watchdog wrapper; prevents accidental unattended runs.
- LOG_DIR / DATA_DIR (configured in constants.py) — locations where logs and JSON caches are stored (typically set in constants, not as envs).
- ADMIN_USER_ID (recommended) — Discord ID of the operator/admin who will receive startup/shutdown DMs and serious alerts.

IMPORTANT: NEVER commit secrets (DISCORD_BOT_TOKEN, GOOGLE credentials) to source control. Store in a secrets manager or secure file on the host and reference using EnvironmentFile/secret injection.

Required variables
- DISCORD_BOT_TOKEN
  - Type: string (secret)
  - Example: DISCORD_BOT_TOKEN=MzI0... (do not paste real tokens)
  - Where used: DL_bot.py, bot_instance.py, discord client login
  - Notes: If missing, DL_bot.py will exit early. Keep this in a secure secret store. Rotate if compromised.

Recommended / Production variables
- WATCHDOG_RUN
  - Type: "1" | "0"
  - Default: not set (DL_bot.py will exit if WATCHDOG_RUN != "1" in normal run-mode)
  - Example: WATCHDOG_RUN=1
  - Where used: DL_bot.py startup guard
  - Notes: The repository expects WATCHDOG_RUN=1 in production so the process is supervised by the project's watchdog or systemd wrapper.

- ADMIN_USER_ID
  - Type: integer (Discord user ID)
  - Example: ADMIN_USER_ID=123456789012345678
  - Where used: notify admin on start/critical alerts; Tasks that need admin confirmation

- GUILD_ID
  - Type: integer (Discord guild/server ID)
  - Example: GUILD_ID=987654321098765432
  - Where used: command syncing during development (guild-scoped sync is faster and safe)
  - Notes: If not set, the bot may perform global command syncs (slower); recommended for local testing.

- GOOGLE_CREDENTIALS_FILE
  - Type: path to JSON file (service account credentials)
  - Example: GOOGLE_CREDENTIALS_FILE=/etc/k98/creds/google-credentials.json
  - Where used: gsheet_module, gsheet access; referenced by gsheet_module.check_basic_gsheets_access()
  - Notes: File should be readable by the service user only.

- ADMIN_USER_MENTION (optional convenience)
  - Type: string (e.g., "<@123456789012345678>")
  - Where used: embeds and status messages when available.

Useful optional / feature flags
- LOG_TO_CONSOLE
  - Type: "1" | "0"
  - Default: 0
  - Example: LOG_TO_CONSOLE=1
  - Where used: logging_setup.py / DL_bot.py when adding console StreamHandler that writes to original stdout (logging_setup.ORIG_STDOUT)
  - Notes: Useful for debugging in non-daemonized runs. May cause console blocking; avoid in heavy production use.

- CONFIG_STRICT
  - Type: "1" | "0"
  - Purpose: When enabled, more validation errors are treated as fatal (if implemented in validation code)
  - Where used: environment checks / validation helpers

- LOG_LEVEL
  - Type: string (DEBUG | INFO | WARNING | ERROR)
  - Default: INFO
  - Where used: logging configuration to control root logger minimum level
  - Notes: Use DEBUG for development only.

- DOWNLOAD_FOLDER
  - Type: path
  - Default: constants.DOWNLOAD_FOLDER or project default
  - Where used: processing_pipeline.py, stats_module.py (temporary storage for uploaded files)

- GOOGLE_* sheet IDs (optional per-feature)
  - GOOGLE_KINGDOM_SUMMARY_ID, GOOGLE_KVK_LIST_ID, GOOGLE_TARGETS_ID, GOOGLE_TIMELINE_ID, GOOGLE_STATS_ID, KVK_SHEET_ID, KVK_SHEET_NAME
  - Type: spreadsheet ID string or sheet name
  - Where used: gsheet_module and KVK reporting pipelines
  - Notes: If features dependent on these are not used, these may be unset.

- ODBC_DRIVER / DB CONNECTION variables
  - ODBC_DRIVER (string) - system ODBC driver name if using a SQL backend
  - DB connection strings or individual credentials (if using DB)
  - Where used: code that writes to DB; check code paths that use pyodbc or other DB libs
  - Notes: Use least privilege DB account.

Debug/test flags (useful in CI or developer environment)
- SMOKE_IMPORTS
  - Type: "1" | "0"
  - Example: SMOKE_IMPORTS=1
  - Purpose: set by scripts/smoke_imports.py to prevent network login, file logging, and background tasks during an import-only smoke test (safe local validation).

- NO_DISCORD_LOGIN
  - Type: "1" | "0"
  - Purpose: Prevents the bot from calling client.run() for integration-testing import-only checks.

- DISABLE_STARTUP_TASKS
  - Type: "1" | "0"
  - Purpose: Prevent long-running background initializers during tests (cache warmers, health probes).

- DISABLE_FILE_LOGGING
  - Type: "1" | "0"
  - Purpose: When set logging_setup avoids creating rotating file handlers; useful for CI where file writes are not desired.

Ingress channel / feature enabling envs (IDs used by fast-path handlers)
- PLAYER_LOCATION_CHANNEL_ID — channel for player location CSV ingest (integer)
- PREKVK_CHANNEL_ID — pre-KVK snapshots channel (integer)
- HONOR_CHANNEL_ID — honour ingestion channel (integer)
- ACTIVITY_UPLOAD_CHANNEL_ID — weekly activity ingest channel (integer)
- FORT_RALLY_CHANNEL_ID — rally forts ingest channel (integer)
- PROKINGDOM_CHANNEL_ID — all-kingdom KVK ingest channel (integer)

Other envs exported by bot_config.py (common list — confirm in bot_config.py)
- ADMIN_USER_MENTION, CHANNEL_IDS, DELETE_AFTER_DOWNLOAD_CHANNEL_ID, FORT_RALLY_CHANNEL_ID, GUILD_ID, HONOR_CHANNEL_ID, KVK_EVENT_CHANNEL_ID, KVK_NOTIFICATION_CHANNEL_ID, LEADERSHIP_CHANNEL_ID, LEADERSHIP_ROLE_IDS, LEADERSHIP_ROLE_NAMES, LOCATION_CHANNEL_ID, NOTIFY_CHANNEL_ID, OFFSEASON_STATS_CHANNEL_ID, PLAYER_LOCATION_CHANNEL_ID, PREKVK_CHANNEL_ID, PROKINGDOM_CHANNEL_ID, etc.
- Notes: these come from bot_config and many are optional; check bot_config.py and __all__ exports for the full list and types.

File & path constants (from constants.py)
- LOG_DIR — location where logs are written (log.txt, error_log.txt, crash.log)
- DATA_DIR — persisted JSON caches and runtime files (QUEUE_CACHE_FILE, COMMAND_CACHE_FILE, LAST_SHUTDOWN_INFO, DM_SCHEDULED_TRACKER_FILE, etc.)
- QUEUE_CACHE_FILE — persisted live queue cache
- COMMAND_CACHE_FILE — saved command signatures used for detecting command changes
- LAST_SHUTDOWN_INFO — final shutdown summary JSON
- BOT_LOCK_PATH — path to the singleton lock file
- RESTART_EXIT_CODE — exit code used to request a restart by the watchdog

Example `.env` for production (DO NOT CHECK IN)
```
# Production .env (example - secrets omitted)
DISCORD_BOT_TOKEN=__REDACTED__
WATCHDOG_RUN=1
ADMIN_USER_ID=123456789012345678
GUILD_ID=987654321098765432
GOOGLE_CREDENTIALS_FILE=/etc/k98/google-credentials.json
LOG_TO_CONSOLE=0
LOG_LEVEL=INFO
```

Example `.env` for local development
```
DISCORD_BOT_TOKEN=__REDACTED__
WATCHDOG_RUN=1
GUILD_ID=987654321098765432  # use a test guild for commands sync
LOG_TO_CONSOLE=1
SMOKE_IMPORTS=0
NO_DISCORD_LOGIN=0
```

Validating your environment
- Use scripts/config_self_test.py to validate common envs & presence of required files (Google creds, ODBC driver, list-type envs).
  - Example: python scripts/config_self_test.py
- Use scripts/smoke_imports.py for a safe import-only smoke test:
  - python scripts/smoke_imports.py

Security practices
- Keep DISCORD_BOT_TOKEN and GOOGLE_CREDENTIALS_FILE out of the repo.
- Limit filesystem permissions for LOG_DIR and DATA_DIR to the service user.
- Rotate DISCORD_BOT_TOKEN if it may have been exposed.

How to add a new env variable (developer workflow)
1. Add the variable to bot_config.py with a typed accessor (e.g., _env_int/_env_str/_env_bool).
2. Add it to the ENV_REFERENCE.md with usage, type, and example.
3. If it affects persisted behavior, add a default in constants.py or migration/rehydration logic if necessary.
4. Update scripts/config_self_test.py to include it in automated checks.

Where to look in the code
- bot_config.py — typed env helpers and canonical list of exported configs
- DL_bot.py — startup guards (WATCHDOG_RUN) and pid/lock handling
- logging_setup.py — file logging and debug flags (LOG_TO_CONSOLE, DISABLE_FILE_LOGGING)
- scripts/smoke_imports.py and scripts/config_self_test.py — examples of defensive test-mode env flags

If you'd like I can:
- Generate a complete machine-readable YAML file describing all envs and their types and defaults (useful for CI and Vault templating).
- Add an .env.example file based on this reference (redacting secrets) and a systemd EnvironmentFile template.
