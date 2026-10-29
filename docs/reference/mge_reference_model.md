# MGE Reference Model

> **Approved local A1b implementation:** The revised scope is implemented locally and validated on Windows. See the [implementation and evidence record](../task_packs/P1%20MGE%20A1b%20-%20Implementation%20and%20Validation%20-%202026-10-28.md). Publication, merge and deployment remain separate. Earlier scope-only approval wording below is historical.

## Local A1b implementation contract

Ordinary adopted MGE actions report explicit completed, not-entered, rolled-back,
partial or unknown outcomes. A confirmed private reply and a delivered public board
are separate facts. Registered refreshes survive reply failure and cancellation;
compatible target requests coalesce, and newer work receives a fresh pass. Explicit
Refresh observes the selected target and reports pending after ten seconds.

Public, leadership and award payloads qualify required data and identity before
Discord IO. Publish/unpublish primary board transitions share event presentation
ownership with refresh. Conditional ID persistence compares lifecycle, publication
version, full SQL revision and previous IDs. Ambiguous or superseded receipts cannot
restore cleared bindings. This ownership is process-local, not a cross-process
transaction guarantee.

Startup reconciles known original message IDs through finite high-water pages of
fifty, at most two event tasks at once, including completed/calendar-missing events.
Periodic reconciliation covers noncompleted events. Recovery edits existing boards
only; no replacement, placement or announcement is implied. Failed pages retain the
cursor; failed targets remain visible while later events progress. Read the counters
alongside the completion flag. Historical-target completion does not mean delivery
acceptance. Current implementation evidence and later production acceptance are
separate; the deployed A1a record below remains the deployed baseline.

The delivered MGE lifecycle implementation is described in the
[implementation and evidence packet](../task_packs/P1%20MGE%20Lifecycle%20-%20Implementation%20and%20Evidence.md).
Use the [shared P1 adoption contract](p1-operation-lifecycle.md) for acknowledgement,
owned execution, transaction outcomes and refresh/delivery evidence. Native SQL,
deployment and operator acceptance remain separate gates.

> **Current status - 28 October 2026, A1a deployed:** Mirror PR 454 and private
> PR 702 are merged; private `87c1b39325daaa0ca1a8c0cbca656df82d7fa46b` is deployed
> and Discord online. Signup/edit/withdraw are verified on this runtime. A1a qualified
> datasets and timing are delivered; the A1b design packet is prepared for approval.
> Rank confirmation still waits for board refresh. Report 62 queue closure, the older
> configuration decision and separate Discord lag remain follow-ups. Exact audit/cleanup,
> unexercised cases, fresh import/export, natural acceptance and P0 remain explicit.
> See [deployed closeout](../task_packs/P1%20MGE%20A1a%20-%20Deployed%20Closeout%20-%202026-10-28.md) and [A1b design packet](../task_packs/P1%20MGE%20A1b%20-%20Design%20and%20Delivery%20Packet%20-%202026-10-28.md).
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
