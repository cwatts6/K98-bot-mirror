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


## KVK source private intake (S5A)

| Variable | Default | Meaning |
|---|---|---|
| KVK_SOURCE_INTAKE_ENABLED | false | Enables private admission and manual receipt controls only. Does not activate serving. |
| KVK_SOURCE_RECOVERY_ENABLED | false | Enables the S5B recovery worker; independent of serving activation. See recovery configuration below. |
| KVK_SOURCE_CHANNEL_ID | 0 | Dedicated private intake channel; must differ from every legacy upload and monitored fallback channel. |
| KVK_SOURCE_UPLOADER_ROLE_IDS | empty | Explicit guild uploader role IDs; fresh membership is checked in handlers and callbacks. |
| KVK_SOURCE_ARTIFACT_ROOT | unset | Absolute private service-owned directory outside Git for content-addressed originals. |

No real channel, role, root or enabling flag is supplied by this change. Disabled intake creates
no directory or connection and preserves legacy routing. Verify channel membership/ACLs and
private-root filesystem permissions before enabling. Existing GUILD_ID and ADMIN_USER_ID define
the guild/admin boundary; ordinary uploaders cannot finalize/correct/configure. The existing
NOTIFY_CHANNEL_ID is also allowed for that admin's private command responses. SourceRouting.Enabled
is independent and remains off. Keep originals and receipts when disabling intake; no cleanup
or retained-database deletion is part of rollback.

## KVK source recovery (S5B)

| Variable | Default | Contract |
|---|---|---|
| KVK_SOURCE_RECOVERY_INTERVAL_SECONDS | 30 | Integer seconds, 1-300 inclusive. |
| KVK_SOURCE_RECOVERY_BATCH_SIZE | 8 | Integer periods per worker batch, 1-32 inclusive. |
| KVK_SOURCE_EXPORT_REGISTRATIONS | [] | JSON array of zero to eight explicit registrations, validated before SQL or credential access. Empty means no automatic export destination. |

KVK_SOURCE_RECOVERY_ENABLED defaults false. Enabling it registers one off-event-loop worker;
it does not enable SourceRouting or authorize Discord publication. Invalid interval/batch bounds
fail registration. Invalid export configuration fails closed before opening SQL/credentials;
the worker records the exception type and retries on its interval. Validate the configuration
before separately authorized activation; do not infer permission to enable it from this example.

Synthetic JSON example (all identifiers are placeholders):

```json
[{"kvk_no":1,"index_file_id":"synthetic_index","slot_file_ids":["synthetic_slot_a","synthetic_slot_b"],"owner_email":"owner@example.invalid","service_account_email":"bot@synthetic.iam.gserviceaccount.com","audience":"private"}]
```

Required keys are kvk_no, index_file_id, slot_file_ids, owner_email and service_account_email.
Only audience is optional; unknown keys are rejected. kvk_no is an integer 1-2147483647
(booleans are rejected). IDs are strings matching `[A-Za-z0-9_-]{3,128}`. Each registration
requires 2-16 slot IDs; the index and every slot must be distinct across the entire configuration
and cannot equal KVK_SHEET_ID or ALL_KVK_SHEET_ID. The durable receipt size may require fewer
slots; S4B returns setup-required if the registration plus quarantine exceeds receipt capacity.

owner_email must be a nonempty string containing @. service_account_email must end in
`.iam.gserviceaccount.com` and differ from the owner. Runtime provider checks verify actual
ownership and editor permissions; syntax validation does not establish ownership.
audience defaults to `private`; the only other value is `public_viewer`, which requires explicit
operator approval for that audience. Use dedicated pre-provisioned My Drive workbooks. Existing
S4B permission, protected-file, manifest, receipt and quarantine checks still apply.
Credentials come from the existing CREDENTIALS_FILE reference; never put keys or tokens in
this JSON or Git. An empty registration list loads no export credentials. No workbook discovery,
creation, automatic Discord send or uncertain/private-slot reclamation is authorized here.

When MAINT_SPEC_ALLOWLIST is explicitly configured, permit the exact callable
`proc_config_import:run_proc_config_import_payload` for process-mode ProcConfig imports.
The worker still enforces its configured allowlist; this change does not broaden it automatically.
Thread mode preserves the same actor/provenance without using the process callable allowlist.
