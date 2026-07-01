# Environment Reference

Purpose: document the environment variables and runtime configuration points used by the bot.

Primary code sources:

- `bot_config.py` for typed Discord/config environment variables
- `constants.py` for path, SQL, and file constants
- `logging_setup.py` for logging-related environment handling
- `scripts/config_self_test.py` and `scripts/validate_env.py` for validation examples

## Required

### DISCORD_BOT_TOKEN

- Type: string secret
- Used by: `bot_config.py`, `DL_bot.py`, Discord client startup
- Notes: Required for normal bot operation. Never commit real tokens.

## Required For Normal Bot Startup

### WATCHDOG_RUN

- Type: `1` for supervised bot startup
- Used by: `DL_bot.py`, `scripts/smoke_imports.py`
- Notes: Normal bot startup exits when this is missing. Smoke/import validation sets it safely.

## Common Production / Local Variables

### GUILD_ID

- Type: Discord snowflake integer
- Used by: command registration/sync paths
- Notes: Recommended for local and production command sync behaviour.

### ADMIN_USER_ID

- Type: Discord snowflake integer
- Used by: startup/shutdown/admin notification flows

### GOOGLE_CREDENTIALS_FILE

- Type: filesystem path
- Default in `constants.py`: `credentials.json`
- Used by: Google Sheets access
- Notes: Keep credential files outside source control.

### ODBC_DRIVER

- Type: ODBC driver name
- Default in `constants.py`: `ODBC Driver 17 for SQL Server`
- Used by: SQL connection strings in `constants.py`

### CONFIG_STRICT

- Type: boolean-like (`1`, `true`, `yes`)
- Used by: `bot_config.py`
- Notes: Makes bad list/integer environment values fail loudly where strict parsing applies.

## Logging / Validation Variables

### LOG_TO_CONSOLE

- Type: `1` to mirror logs to console
- Used by: `logging_setup.py`
- Notes: Useful in local debugging; avoid noisy console logging for unattended production runs.

### DISABLE_FILE_LOGGING

- Type: `1` to avoid creating file handlers
- Used by: validation/smoke import paths

### SMOKE_IMPORTS

- Type: `1` during import-only validation
- Used by: `scripts/smoke_imports.py` and startup guards

### NO_DISCORD_LOGIN

- Type: `1` to prevent Discord login during validation/import tests

### DISABLE_STARTUP_TASKS

- Type: `1` to prevent background startup tasks during validation/import tests

## Channel / Feature IDs

Defined through `bot_config.py` and validated by `scripts/config_self_test.py` where relevant:

- `PLAYER_LOCATION_CHANNEL_ID`
- `PREKVK_CHANNEL_ID`
- `HONOR_CHANNEL_ID`
- `ACTIVITY_UPLOAD_CHANNEL_ID`
- `FORT_RALLY_CHANNEL_ID`
- `PROKINGDOM_CHANNEL_ID`
- `KVK_EVENT_CHANNEL_ID`
- `KVK_NOTIFICATION_CHANNEL_ID`
- `LEADERSHIP_CHANNEL_ID`
- `NOTIFY_CHANNEL_ID`
- `OFFSEASON_STATS_CHANNEL_ID`

Use `bot_config.py` as the exact source for exported names and types.

## Voting Configuration

### VOTE_OPTION_LABEL_MAX_LENGTH

- Type: integer from `1` to `80`
- Default: `20`
- Used by: `voting.service`, `/vote_admin create`
- Notes: Caps vote option labels for Discord slash-command validation, SQL validation, button
  labels, and result-card readability. Values above `80` are rejected because Discord button
  labels cannot exceed 80 characters.

## Runtime Path Constants

These are primarily configured in `constants.py`, not usually as environment variables:

- `LOG_DIR`
- `DATA_DIR`
- `QUEUE_CACHE_FILE`
- `COMMAND_CACHE_FILE`
- `LAST_SHUTDOWN_INFO`
- `BOT_LOCK_PATH`
- `BOT_PID_PATH`
- `RESTART_EXIT_CODE`
- `EVENT_CALENDAR_CACHE_FILE_PATH`

## Validation Commands

```powershell
python scripts/config_self_test.py
python scripts/validate_env.py
python scripts/smoke_imports.py
```

## Adding A New Variable

1. Add typed parsing in `bot_config.py` or `constants.py`.
2. Add validation to `scripts/config_self_test.py` or `scripts/validate_env.py` when practical.
3. Update this file with type, default, usage, and security notes.
4. Add tests if behaviour changes.

## Security Notes

- Do not commit secrets.
- Redact tokens and credentials in logs, diagnostics, and PR output.
- Use least-privilege SQL and Google credentials.
- Keep credential files readable only by the bot service user where possible.
