# MGE Reference Model

> **Version:** 1.1 — 2026-03-11
> Column names match deployed PascalCase schema exactly.

## Variants

MGE events have exactly **4 variants** — no others are valid:

| VariantId | VariantName | SortOrder |
|-----------|------------|-----------|
| 1         | Infantry   | 1         |
| 2         | Cavalry    | 2         |
| 3         | Archer     | 3         |
| 4         | Leadership | 4         |

Seeded via `sql_schema/dbo.MGE_Variants.Seed.sql`.

## Commander Availability Model

Commanders are stored in `dbo.MGE_Commanders` with these columns:

| Column           | Type          | Notes |
|------------------|---------------|-------|
| `CommanderId`    | `INT IDENTITY`| PK    |
| `CommanderName`  | `NVARCHAR(100)` | Display name |
| `IsActive`       | `BIT`         | 0 = retired from future events |
| `ReleaseStartUtc`| `DATETIME2(7) NULL` | Available from this date |
| `ReleaseEndUtc`  | `DATETIME2(7) NULL` | Available until this date |
| `ImageUrl`       | `NVARCHAR(500) NULL` | Optional commander image |
| `CreatedUtc`     | `DATETIME2(7)`| Row creation timestamp |
| `UpdatedUtc`     | `DATETIME2(7)`| Last update timestamp |

### Availability rules

- A commander with `ReleaseStartUtc = NULL` and `ReleaseEndUtc = NULL` and `IsActive = 1`
  is **always available** for selection.
- `ReleaseStartUtc` only → available from that date onward, no end.
- `ReleaseEndUtc` only → available until that date (legacy/sunset).
- Both set → available within the date range only.

### Filtering logic (Python-side cache builder)

```python
from datetime import UTC, datetime


def is_commander_available(commander: dict, as_of: datetime | None = None) -> bool:
    """Check if a commander is available at a given point in time."""
    if not commander.get("IsActive", False):
        return False
    now = as_of or datetime.now(UTC)
    start = commander.get("ReleaseStartUtc")
    end = commander.get("ReleaseEndUtc")
    if start and now < start:
        return False
    if end and now > end:
        return False
    return True
```

### Key design principles

- Commanders are **never hard-deleted** from history — `IsActive = 0` marks retirement.
- New commanders can be added at any time by inserting into `dbo.MGE_Commanders`.
- Commander lists are **not hardcoded** in the bot — they are data-driven from SQL → JSON cache.

## Variant-to-Commander Mapping

The `dbo.MGE_VariantCommanders` table maps commanders to variants (many-to-many):

| Column             | Type  | Notes |
|--------------------|-------|-------|
| `VariantCommanderId` | `INT IDENTITY` | PK |
| `VariantId`        | `INT` | FK → `MGE_Variants.VariantId` |
| `CommanderId`      | `INT` | FK → `MGE_Commanders.CommanderId` |
| `IsActive`         | `BIT` | Controls whether this mapping is live |

- A commander can appear in **multiple** variants (e.g., a universal commander).
- The mapping is data-driven — no hardcoded lists.
- `IsActive` on the mapping row controls whether a specific variant assignment is live.

## Event Commander Overrides

`dbo.MGE_EventCommanderOverrides` supports one-off additions at the event level:

- An admin can add a commander to a specific event's dropdown even if the global mapping
  wouldn't normally include it.
- Overrides do not alter the global mapping — they are event-scoped only.
- The override UI is **not implemented in v1** but the schema supports it.

## Default Rule Templates

Two default rule templates are seeded via `sql_schema/dbo.MGE_DefaultRules.Seed.sql`:

| RuleKey            | RuleMode | Purpose                          |
|-------------------|----------|----------------------------------|
| `fixed_mge_rules` | `fixed`  | Default rules for controlled MGE |
| `open_mge_rules`  | `open`   | Default rules for open MGE       |

### Rule text flexibility

- The point cap text (e.g., "8,000,000") is embedded in the rule text, **not** in bot logic.
- To change the cap for a specific event, edit the event's `RulesText` column directly.
- Rule edits are audited in `dbo.MGE_RuleAudit`.

## Key Column Reference for Python Cache (Task C)

When building the JSON cache from SQL results, use these **exact** column names:

### MGE_Commanders columns
`CommanderId`, `CommanderName`, `IsActive`, `ReleaseStartUtc`, `ReleaseEndUtc`, `ImageUrl`, `CreatedUtc`, `UpdatedUtc`

### MGE_VariantCommanders columns
`VariantCommanderId`, `VariantId`, `CommanderId`, `IsActive`, `CreatedUtc`, `UpdatedUtc`

### MGE_Events columns
`EventId`, `VariantId`, `EventName`, `StartUtc`, `EndUtc`, `SignupCloseUtc`, `EventMode`, `Status`, `RuleMode`, `RulesText`, `PublishVersion`, `LastPublishedUtc`, `SignupEmbedMessageId`, `SignupEmbedChannelId`, `CalendarEventSourceId`, `CreatedByDiscordId`, `CompletedAtUtc`, `CompletedByDiscordId`, `ReopenedAtUtc`, `ReopenedByDiscordId`, `CreatedUtc`, `UpdatedUtc`

### MGE_Signups columns
`SignupId`, `EventId`, `GovernorId`, `GovernorNameSnapshot`, `DiscordUserId`, `RequestPriority`, `PreferredRankBand`, `RequestedCommanderId`, `RequestedCommanderName`, `CurrentHeads`, `KingdomRole`, `GearText`, `ArmamentText`, `GearAttachmentUrl`, `GearAttachmentFilename`, `ArmamentAttachmentUrl`, `ArmamentAttachmentFilename`, `IsActive`, `Source`, `CreatedUtc`, `UpdatedUtc`

## Existing Helpers for Task C (Cache Pipeline)

These helpers from `file_utils.py` should be reused — **do not recreate**:

| Function | Purpose |
|----------|---------|
| `atomic_write_json(path, obj, ...)` | Atomic temp-file + `os.replace` with Windows retry |
| `read_json_safe(path, default=None)` | Safe JSON read with fallback default |
| `get_conn_with_retries(...)` | DB connection with exponential backoff + jitter |

## Deployment Order

1. Deploy Task A schema tables first (all `dbo.MGE_*.Table.sql` files).
2. Run `dbo.MGE_Variants.Seed.sql` — seeds the 4 variants with stable IDs.
3. Run `dbo.MGE_DefaultRules.Seed.sql` — creates the default rules table and seeds templates.
4. Populate `dbo.MGE_Commanders` with your kingdom's commander list (manual or future import).
5. Populate `dbo.MGE_VariantCommanders` to map commanders to variants.

Steps 4–5 are data-entry tasks specific to your kingdom and will be done separately.
