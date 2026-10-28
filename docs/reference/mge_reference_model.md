# MGE Reference Model

The delivered MGE lifecycle implementation is described in the
[implementation and evidence packet](../task_packs/P1%20MGE%20Lifecycle%20-%20Implementation%20and%20Evidence.md).
Use the [shared P1 adoption contract](p1-operation-lifecycle.md) for acknowledgement,
owned execution, transaction outcomes and refresh/delivery evidence. Native SQL,
deployment and operator acceptance remain separate gates.

> **Current status - 28 October 2026, MGE closeout:** The bounded MGE phase is
> delivered and accepted for exercised signup/edit/withdrawal and leadership flows
> on private `4c8ca0d5fada35c7a32d31846bad6cc492aa92a9`. Next: remaining Batch A
> Discord/domain scope, starting with measured MGE responsiveness/refresh work.
> ProcConfig cancellation is verified; its continuation choice and separate reliability
> follow-ups remain open. Exact audit/cleanup readback and unexercised MGE cases remain
> explicit. Full P1, natural acceptance and P0 rollover are not closed.
> See [accepted closeout and complete ledger](../task_packs/P1%20MGE%20Lifecycle%20-%20Accepted%20Closeout%20-%202026-10-28.md),
> [next scope](../task_packs/P1%20Batch%20A%20Remaining%20Discord%20Domain%20-%20Scope%20-%202026-10-28.md) and [chat starter](../task_packs/P1%20Batch%20A%20Remaining%20Discord%20Domain%20-%20Chat%20Starter%20-%202026-10-28.md).
> Earlier dated status and next-action text is historical where superseded.
> This documentation update requires no deployment, restart, SQL apply or repeat import.


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
