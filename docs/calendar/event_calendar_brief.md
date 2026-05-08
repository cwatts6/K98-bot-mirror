We are building a resilient Event Calendar feature for the K98 Discord bot.

Target architecture:
Google Sheets -> SQL -> JSON cache -> Bot

Goals:
1. Google Sheets remains the easy online editing interface for now.
2. SQL becomes the local resilient operational source of truth.
3. JSON cache becomes the fast bot runtime source for commands and embeds.
4. The calendar must continue working even if Google Sheets is unavailable on a given day.
5. A failed Google Sheets refresh must not wipe working SQL/JSON data.
6. This design prepares us for a future SQL-only world.

Data model already defined in 3 input tabs:
- recurring_rules
- oneoff_events
- overrides

Need production-quality implementation with validation, logging, graceful fallback behaviour, and admin refresh/status controls.

K98 Bot – Event Calendar System
System Architecture
Google Sheets
      ↓
Sheet Sync Module
      ↓
SQL Tables (persistent)
      ↓
Event Generator
      ↓
EventInstances table
      ↓
JSON Cache
      ↓
Discord Bot commands + calendar embed

Key design rules:
Commands never query Google Sheets
SQL remains usable if Sheets fails
JSON cache is runtime source
Pipeline must degrade gracefully


## Implementation progress

### Task 1 (Completed)
- SQL schema and indexes created (idempotent)
- Verification scripts added
- Initial cache/service scaffolding added with pytest coverage

### Task 2 (Completed)
- Google Sheets CSV fetch + parsing for:
  - `recurring_rules`
  - `oneoff_events`
  - `overrides`
- Validation and normalization pipeline implemented
- SHA-256 row hash based upsert logic implemented
- Sync run logging via `EventSyncLog`
- Graceful failure behavior enforced (no source table clobber)
- Admin controls wired:
  - `/calendar_refresh`
  - `/calendar_status`

### Next: Task 3
- Generate event instances into `EventInstances`
- Apply overrides during generation
- Publish runtime JSON cache from SQL
- Add status/reporting around generation + publish
