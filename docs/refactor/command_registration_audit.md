# Command registration audit (Task 3)

## Scope audited
- `Commands.py`
- `cogs/commands.py`
- `subscribe.py`
- Cog module directory scan (`cogs/*.py`) for slash-command decorators

## Authoritative registration path
- **Primary/authoritative:** `Commands.register_commands(bot)` in `DL_bot.py`.
- **Secondary paths (disabled by default):**
  - `cogs/commands.py` (`SummaryCommands`)
  - `subscribe.py` (`Subscribe` cog)

`DL_bot.py` now gates secondary paths with environment flag:

- `ENABLE_SECONDARY_COGS=false` (default)

This keeps one authoritative registration flow in production and avoids double registration.

## Duplicate command names found

These command names are declared in more than one source module:

- `/summary` → `Commands.py`, `cogs/commands.py`
- `/weeksummary` → `Commands.py`, `cogs/commands.py`
- `/history` → `Commands.py`, `cogs/commands.py`
- `/failures` → `Commands.py`, `cogs/commands.py`
- `/ping` → `Commands.py`, `cogs/commands.py`
- `/subscribe` → `Commands.py`, `subscribe.py`

## Startup guard behavior
At startup, `DL_bot.py` now:
1. Audits decorator-declared slash command names in primary + secondary modules.
2. Logs a registration summary (counts + total unique).
3. Logs warnings when duplicates are detected.
4. Keeps `Commands.py` as the only active registration path by default.

## Local deployment / test / validation checklist

### Environment
- Ensure (or omit) this flag in production:
  - `ENABLE_SECONDARY_COGS=false`

### Validation commands
- Static command inventory check:
  - `python scripts/validate_command_registration.py`
- Syntax check for startup guard:
  - `python -m py_compile DL_bot.py`

### Manual runtime validation
1. Start bot.
2. Confirm startup logs include `[COMMAND AUDIT] registration summary`.
3. Confirm duplicate warnings are informational only (no startup failure).
4. In Discord slash command UI, verify there is exactly one instance per command name.
