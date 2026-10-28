# MGE Reference Model

> **Current status - 28 October 2026:** Monitoring and import/export reliability is
> accepted and complete for the deployed private `f6a929c0597ce257ce18380af1ab6f7ad8ddcc5d`
> runtime. Report 59, correct-data confirmation and `/stats player` acceptance close
> fresh-runtime R18. MGE signup/withdrawal remains open and leads the next Discord/domain
> scope. Full P1, natural event/publication checks and P0 rollover acceptance remain separate.
> See the [accepted closeout and complete remaining ledger](../task_packs/P1%20Monitoring%20and%20Import%20Export%20Reliability%20-%20Closeout%20-%202026-10-28.md),
> [next scope](../task_packs/P1%20Discord%20Domain%20Completion%20and%20MGE%20-%20Scope%20-%202026-10-28.md) and [new-chat starter](../task_packs/P1%20Discord%20Domain%20Completion%20and%20MGE%20-%20Chat%20Starter%20-%202026-10-28.md).
> Earlier dated status/next-action statements below are historical where superseded.
> This documentation update requires no bot restart, repeat import/export or SQL apply.


Purpose: provide a quick model reference for MGE work. Validate all SQL object and column details
against `C:\K98-bot-SQL-Server` before implementation.

## Main Bot Areas

- `mge/` contains MGE services, cache, DAL, reporting, signup, publish, rules, roster, and scheduler logic.
- `mge/dal/` contains SQL access.
- `commands/mge_cmds.py` exposes MGE commands.
- `ui/views/` contains MGE interaction views.
- `tests/test_mge_*.py` covers MGE behaviour.

## Core SQL Objects

Common MGE objects include:

- `dbo.MGE_Variants`
- `dbo.MGE_Commanders`
- `dbo.MGE_VariantCommanders`
- `dbo.MGE_EventCommanderOverrides`
- `dbo.MGE_DefaultRules`
- `dbo.MGE_Events`
- `dbo.MGE_Signups`
- `dbo.MGE_Awards`
- `dbo.MGE_RuleAudit`
- `dbo.v_MGE_SignupReview`

Do not add or rename columns based on Python usage alone. Search the SQL repo first.

## Variants

The standard variants are:

| VariantId | VariantName | SortOrder |
|-----------|-------------|-----------|
| 1 | Infantry | 1 |
| 2 | Cavalry | 2 |
| 3 | Archer | 3 |
| 4 | Leadership | 4 |

## Commander Availability

Commanders are stored in `dbo.MGE_Commanders`. Typical fields used by the bot:

- `CommanderId`
- `CommanderName`
- `IsActive`
- `ReleaseStartUtc`
- `ReleaseEndUtc`
- `ImageUrl`
- `CreatedUtc`
- `UpdatedUtc`

Availability rules:

- `IsActive = 0` means retired/unavailable for new selection.
- `ReleaseStartUtc` gates future availability.
- `ReleaseEndUtc` gates sunset availability.
- Commanders should not be hard-deleted when historical signups or awards may reference them.

## Variant Commander Mapping

`dbo.MGE_VariantCommanders` maps commanders to variants. A commander may appear in multiple
variants. `IsActive` controls whether a mapping is currently available.

## Event Commander Overrides

`dbo.MGE_EventCommanderOverrides` supports event-scoped commander additions without changing
global variant mappings.

## Rules

`dbo.MGE_DefaultRules` stores default rule templates. Rule text, including point-cap wording,
should stay data-driven instead of hardcoded into command/view logic.

## Helper Expectations

Use existing helpers where possible:

- `file_utils.atomic_write_json`
- `file_utils.read_json_safe`
- `file_utils.get_conn_with_retries`
- `core/interaction_safety.py` helpers for Discord interactions

## Tests

For MGE changes, run focused tests for the touched area, usually from:

```powershell
python -m pytest -q tests/test_mge_*.py
```

Narrow the command further when only a specific service/DAL/view changed.
