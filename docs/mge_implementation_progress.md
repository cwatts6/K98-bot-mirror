# MGE Implementation Progress

> **Living document** — updated after each task completion.
> Include this file in every new Codex/Copilot chat session for MGE work.
> Companion to: `MGE Sign-Up Tool.md` (task pack), `docs/mge_reference_model.md` (data model)

---

## Session Setup Instructions

When starting a new chat session for MGE tasks, provide these files in order:

1. `MGE Sign-Up Tool.md` — full task pack (feature spec)
2. `K98 Bot — Project Engineering Standards.md` — architecture rules
3. `coding execution guidelines.md` — agent workflow rules
4. `docs/mge_implementation_progress.md` — **this file** (confirmed state)
5. `docs/mge_reference_model.md` — data model reference

Then state: *"Continue with Task [X]. All prior tasks are complete and validated."*

---

| Task | Title | Status | Repo | Notes |
|------|-------|--------|------|-------|
| A | SQL schema | ✅ Complete | SQL Server | All 11 tables deployed and validated |
| B | Seed data & reference model | ✅ Complete | SQL Server + Bot | Variants seeded (IDs 1–4), default rules seeded, `mge_reference_model.md` committed |
| C | Commander cache pipeline | ✅ Complete | SQL Server + Bot | DAL-aligned cache pipeline shipped; commander + variant mapping seeds added |
| D | Event scheduler & creation | ✅ Complete | Bot | Implemented Task D scheduler lifecycle using existing startup/task monitor pattern in `bot_instance.py` |
| E | Main embed + open mode | ✅ Complete | Bot | Public embed + admin controls + safe open switch delivered and validated |
| F | Signup/edit/withdraw | ✅ Complete | Bot | Player signup/edit/withdraw flow delivered with one-active enforcement, lock rules, admin override surface |
| G | Optional DM follow-up for gear/armament attachments | ✅ Complete | Bot | Delivered + post-review hardening applied |
| H | Review dataset | ✅ Complete | SQL + Bot | `dbo.v_MGE_SignupReview` + DAL/service summary stack delivered; canonical sort in service; leadership-only read scaffold/command added |
| I | Leadership roster builder | 🔲 Pending | Bot | Task-H dataset/service contract ready for integration |
| J | Target generation + publish | 🔲 Pending | Bot | — |
| K | Rule editing | 🔲 Pending | Bot | — |
| L | Completion/freeze/report | 🔲 Pending | Bot | — |
| M | Results import scaffold | 🔲 Pending | SQL + Bot | Phase 2, non-blocking |
| N | Wiring & regression | 🔲 Pending | Bot | Include Task C startup refresh + rehydration-safe wiring |



---

## Confirmed Scope Summary

### Subsystems and existing modules involved

| Area | Existing module(s) | MGE interaction |
|------|-------------------|-----------------|
| Calendar / event source | `event_calendar/`, `event_scheduler.py`, `dbo.EventInstances` | MGE scheduler reads upcoming events to auto-create MGE events 7 days before start |
| Governor registry | `governor_registry.py`, `account_picker.py` | Signup flow reuses governor lookup + multi-account picker |
| Bot startup | `bot_loader.py`, `bot_instance.py` | MGE scheduler + view rehydration registered at startup |
| View rehydration | `rehydrate_views.py` | MGE embed message IDs stored in DB, views re-attached on restart |
| Graceful shutdown | `graceful_shutdown.py` | MGE background tasks must have cancellation handlers |
| Interaction safety | `core/interaction_safety.py` | All MGE views use safe interaction patterns |
| Permissions | `constants.py` (role IDs) | Admin/leadership checks on roster builder, open-mode switch, rule editing |

### Command and UI component map

| Component | Type | File | Task |
|-----------|------|------|------|
| `/mge` command group | Slash commands | `commands/mge_cmds.py` | N |
| Main signup embed | Persistent view | `ui/views/mge_signup_view.py` | E, F |
| Admin controls | View (role-gated) | `ui/views/mge_admin_view.py` | E |
| Signup modal | Modal | `ui/views/mge_signup_modal.py` | F |
| Edit request view | View | `ui/views/mge_edit_view.py` | F |
| DM attachment flow | DM view | `ui/views/mge_dm_attachment_view.py` | G |
| Leadership board | View (role-gated) | `ui/views/mge_leadership_board_view.py` | I |
| Roster builder | View (role-gated) | `ui/views/mge_roster_builder_view.py` | I |
| Publish view | View | `ui/views/mge_publish_view.py` | J |
| Rules editor | Modal/View | `ui/views/mge_rules_edit_view.py` | K |
| Completion controls | View (role-gated) | `ui/views/mge_admin_completion_view.py` | L |

### Service layer map

| Service | File | Responsibility | Task |
|---------|------|---------------|------|
| Event service | `mge/mge_event_service.py` | Event CRUD, mode switching, status transitions | D, E |
| Signup service | `mge/mge_signup_service.py` | Signup create/edit/withdraw, one-active enforcement, admin post-close override checks | F ✅ |
| Validation | `mge/mge_validation.py` | Input validation, heads range, mode/status/window locks | F ✅ |
| Signup DAL | `mge/dal/mge_signup_dal.py` | Signup/event context SQL access + audit writes | F ✅ |
| Cache pipeline | `mge/mge_cache.py` | SQL → JSON cache build with safe overwrite | C ✅ |
| Commander DAL | `mge/dal/mge_dal.py` | SQL data access for commanders + variant mappings (+ future overrides query) | C ✅ |
| Review service | `mge/mge_review_service.py` | Enriched applicant pool for leadership | H |
| Summary service | `mge/mge_summary_service.py` | Aggregated counts/stats for leadership | H |
| Roster service | `mge/mge_roster_service.py` | Award allocation, rank management, waitlist | I |
| Publish service | `mge/mge_publish_service.py` | Target generation, publish/republish, change-log | J |
| Rules service | `mge/mge_rules_service.py` | Rule text CRUD, audit logging | K |
| Completion service | `mge/mge_completion_service.py` | Event freeze, reopen, status transitions | L |
| Report service | `mge/mge_report_service.py` | Post-event internal summary generation | L |
| Embed manager | `mge/mge_embed_manager.py` | Embed rendering for main embed + published roster | D, E, J, K |
| Scheduler | `mge/mge_scheduler.py` | Auto-creation 7 days before start, follows `ark_scheduler.py` pattern | D |
| DM follow-up | `mge/mge_dm_followup.py` | DM-based attachment collection | G |
| Results import | `mge/mge_results_import.py` | Phase 2 scaffold | M |
| XLSX parser | `mge/mge_xlsx_parser.py` | Phase 2 scaffold | M |
| Constants | `mge/mge_constants.py` | Cache file path constants only (no SQL) | C ✅ |

### Restart and persistence plan

| State | Storage | Rehydration method |
|-------|---------|-------------------|
| MGE event records | `dbo.MGE_Events` | Loaded from DB on startup |
| Signup embed message/channel IDs | `dbo.MGE_Events.SignupEmbedMessageId/ChannelId` | `rehydrate_views.py` pattern — re-attach views to existing messages |
| Signup data | `dbo.MGE_Signups` | Loaded from DB on demand |
| Award/roster data | `dbo.MGE_Awards` | Loaded from DB on demand |
| Scheduler tasks | Registered at startup from DB state | Follow `ark_scheduler.py` pattern — query open events, schedule tasks |
| Commander cache | `data/mge_commanders_cache.json` | Rebuilt from SQL on startup if missing; safe read via `read_json_safe` |
| Variant commanders cache | `data/mge_variant_commanders_cache.json` | Same as above |

### Cache strategy

| Cache file | Source | Invalidation | First-run behavior |
|------------|--------|-------------|-------------------|
| `data/mge_commanders_cache.json` | `dbo.MGE_Commanders` | Refreshed on schedule or admin trigger | Created from SQL; if SQL empty/invalid, write skipped and prior cache preserved |
| `data/mge_variant_commanders_cache.json` | `dbo.MGE_VariantCommanders` + joins | Same | Same |

**Rules:** SQL is always source of truth. Never overwrite good cache with empty/invalid data. Use `atomic_write_json` for all writes. Use `read_json_safe` for all reads.

### Background processes

| Process | Trigger | Pattern to follow |
|---------|---------|------------------|
| MGE event auto-creation | Scheduler (runs periodically) | `ark/ark_scheduler.py` |
| Commander cache refresh | Startup + periodic or admin-triggered | `player_stats_cache.py` build pattern |
| Signup close enforcement | Checked at interaction time against `SignupCloseUtc` | No background task needed — compare timestamps |
| Event completion | Admin action or scheduled 6 days after start | Status transition in `mge_completion_service.py` |

---

## Task C Delivery Record (final)

### SQL Server repo (`cwatts6/K98-bot-SQL-Server`)

Added:

- `sql_schema/dbo.MGE_Commanders.Seed.sql`
- `sql_schema/dbo.MGE_VariantCommanders.Seed.sql`

Seed scope:

- Inserted 23 commanders into `dbo.MGE_Commanders` (idempotent by `CommanderName`)
- Inserted commander-to-variant mappings into `dbo.MGE_VariantCommanders` (idempotent by `(VariantId, CommanderId)`)
- `IsActive = 1`, `ReleaseStartUtc/ReleaseEndUtc = NULL`, `ImageUrl = NULL` for initial population

### Bot repo (`cwatts6/K98-bot-mirror`)

Added/updated:

- `mge/__init__.py`
- `mge/mge_constants.py` (cache path constants only)
- `mge/dal/__init__.py`
- `mge/dal/mge_dal.py` (SQL text + DB access)
- `mge/mge_cache.py` (cache build/read/validation/filtering)
- `tests/test_mge_cache.py`

Implementation details:

- DAL aligned to Ark approach (`ark/dal/ark_dal.py` style)
- SQL queries moved into DAL (not constants)
- Reused existing helpers from shared stack:
  - `stats_alerts.db.run_query`
  - `file_utils.atomic_write_json`
  - `file_utils.read_json_safe`
- Commander availability filtering implemented with UTC-aware handling of:
  - `IsActive`
  - `ReleaseStartUtc`
  - `ReleaseEndUtc`
- Cache writes are guarded:
  - Empty/malformed payload → skip write, preserve prior cache
- First-run safe read behavior confirmed via tests (`default=[]` fallback)

### Tests

`tests/test_mge_cache.py` now covers:

- Commander cache successful write
- Commander empty payload does not overwrite
- Commander malformed payload does not overwrite
- Variant cache successful write
- Variant empty payload does not overwrite
- Availability date-window logic
- Variant filter read helper
- Safe read default fallback

Status: ✅ Passed

---
### Task D Delivery Record (final)

#### Bot repo (`cwatts6/K98-bot-mirror`)

Added:

- `mge/dal/mge_event_dal.py`
- `mge/mge_event_service.py`
- `mge/mge_embed_manager.py`
- `mge/mge_scheduler.py`
- `tests/test_mge_event_service.py`
- `tests/test_mge_scheduler.py`

Modified:

- `bot_instance.py` (startup scheduler registration)
- `mge/dal/__init__.py` (DAL package wiring, if required)

#### Implementation summary

- Implemented Task D scheduler lifecycle using existing startup/task monitor pattern in `bot_instance.py`.
- Added periodic MGE sync loop (`schedule_mge_lifecycle`) that:
  - reads calendar candidates from `dbo.EventInstances`
  - enforces Task D 7-day creation window
  - resolves lowercase calendar `Variant` values (`infantry`, `cavalry`, `archer`, `leadership`) against seeded `dbo.MGE_Variants`
  - creates `dbo.MGE_Events` rows with defaults:
    - `EventMode='controlled'`
    - `RuleMode='fixed'`
    - `Status='signup_open'`
    - `RulesText` from `dbo.MGE_DefaultRules` (`fixed_mge_rules`)
    - `SignupCloseUtc = StartUtc - 1 hour`
- Duplicate prevention implemented via `CalendarEventSourceId` lookup (idempotent reruns).
- Added embed publish/refresh path for each scheduled event and persisted:
  - `SignupEmbedMessageId`
  - `SignupEmbedChannelId`
- Existing event rows are refreshed (not duplicated) on repeated scheduler runs.
- Logging added for create/existing/skip/error scheduler paths.

#### Architecture & standards compliance

- DAL split preserved: commander cache DAL remains in `mge/dal/mge_dal.py`; Task D event/calendar SQL lives in `mge/dal/mge_event_dal.py`.
- Service layer is Discord-agnostic (`mge_event_service.py`).
- Discord I/O isolated to embed manager + scheduler orchestration.
- UTC discipline followed (`datetime.now(UTC)`).
- No prohibited patterns introduced (`logging.basicConfig`, bare `print`, `except: pass`).

#### Tests

Added/updated unit coverage for:

- exact 7-day creation window behavior
- duplicate scheduler runs do not create duplicate rows
- signup close time = start minus 1 hour
- fixed rules template load path
- scheduler loop invokes embed sync for returned event IDs

Status: ✅ Passed (`black`, `ruff`, `pyright`, `pytest`)

### Task E Delivery Record (final)

#### Bot repo (`cwatts6/K98-bot-mirror`)

Added:

- `ui/views/mge_signup_view.py`
- `ui/views/mge_admin_view.py`
- `tests/test_mge_embed_manager.py`
- `tests/test_mge_open_mode_switch.py`

Modified:

- `mge/mge_event_service.py`
- `mge/mge_embed_manager.py`
- `mge/dal/mge_event_dal.py`
- `mge/dal/__init__.py` (DAL package wiring, if required)
- `rehydrate_views.py` (view re-attach wiring only if required by current startup path)

#### Implementation summary

- Implemented Task E main public MGE embed interaction model, aligned to existing Task D embed lifecycle.
- Added main signup view controls:
  - user-facing: `Sign Up`, `Withdraw`, `View / Edit My Request`
  - admin controls: `Switch to Open`, `Edit Rules`, `Refresh Embed`, `Open Leadership Board`
- Implemented destructive open-mode switch flow with confirmation:
  - admin-gated interaction path
  - hard delete of existing event signups (per approved Task E decision)
  - event mode/rule transition:
    - `EventMode='open'`
    - `RuleMode='open'`
    - `RulesText` loaded from active `open_mge_rules` template
  - audit writes for mode switch and bulk signup removal action
  - embed refresh/update after successful transition
- Added status guardrails:
  - open-mode switch blocked when `Status IN ('published','completed')`
- Public embed content now includes:
  - title, variant, start/end, signup close, mode
  - public signup count
  - governor-name-only pre-allocation signup list
  - event rules text
- Public privacy constraints preserved:
  - no requested commander/request priority shown pre-publish
  - no Discord mentions in public signup list

#### Architecture & standards compliance

- Kept SQL text in DAL (`mge/dal/mge_event_dal.py`) — no SQL in constants.
- Service layer remains Discord-agnostic (`mge_event_service.py`).
- Discord interaction handling remains in view layer (`ui/views/mge_*`) with safe interaction wrappers.
- Reused existing helpers/patterns:
  - `embed_utils.fmt_short`
  - `core/interaction_safety.py`
  - `stats_alerts.db.run_query`
  - module logger pattern (`logger = logging.getLogger(__name__)`)
- No prohibited patterns introduced (`logging.basicConfig`, bare `print`, `except: pass`).
- UTC discipline preserved (`datetime.now(UTC)`).

#### Tests

Added/updated unit coverage for:

- controlled embed render
- open embed render
- switch-to-open hard deletes signups and updates mode/rules
- switch-to-open blocked for `published`
- switch-to-open blocked for `completed`
- public signup list governor-name-only behavior

Status: ✅ Passed (`black`, `ruff`, `pyright`, `pytest`)

#### Task E Post-Review Hardening (2026-03-12)

Applied code-review corrections after initial Task E delivery:

- Scheduler hardening:
  - validated `MGE_SIGNUP_CHANNEL_ID` once at scheduler startup
  - aborts scheduler with clear log when channel ID is missing/invalid
- Interaction helper alignment:
  - removed dependency on non-existent `safe_reply` / `safe_ack` in MGE views
  - switched to existing safe ephemeral response pattern compatible with current repo helpers
- Admin safety controls:
  - added admin gating on all admin actions in signup view (`Switch to Open`, `Edit Rules`, `Refresh`, `Leadership Board`)
  - non-admins now receive ephemeral denial before any admin workflow is shown
- Persistent view reliability:
  - added explicit stable `custom_id` values for admin buttons to support rehydration-safe routing
- DAL write correctness:
  - removed DML usage via `run_query` for open-switch path
  - implemented atomic open-switch DB operation using existing DB transaction/cursor pattern (`exec_with_cursor`)
  - ensured hard-delete rowcount is captured correctly
- Embed robustness:
  - capped public signup field rendering to Discord 1024-char field limit with overflow handling
- Path stability:
  - updated MGE cache paths to resolve from `constants.DATA_DIR` instead of CWD-relative paths
- Scheduler resilience:
  - widened sync query window to avoid missed MGE creations after temporary scheduler downtime, relying on source-id idempotency

Validation re-run: ✅ `black`, `ruff`, `pyright`, `pytest`

---

## Task F Delivery Record (final)

### Bot repo (`cwatts6/K98-bot-mirror`)

Added:

- `mge/dal/mge_signup_dal.py`
- `mge/mge_signup_service.py`
- `mge/mge_validation.py`
- `ui/views/mge_signup_modal.py`
- `ui/views/mge_edit_view.py`
- `tests/test_mge_signup_service.py`
- `tests/test_mge_signup_views.py`

Modified:

- `ui/views/mge_signup_view.py`
- `mge/dal/__init__.py`

### Implementation summary

- Implemented Task F player-facing flow for controlled MGE events:
  - Sign Up
  - View/Edit My Request
  - Withdraw
- Reused account/governor helpers per requirement:
  - `account_picker.build_unique_gov_options` for player governor selection
  - `governor_registry.load_registry` path through service for linked-governor checks / admin usage
- Enforced one-active-signup per `(EventId, GovernorId)` through service/DAL checks.
- Added full policy lock handling:
  - block signup/edit/withdraw when `EventMode='open'`
  - block signup/edit/withdraw when `Status IN ('published','completed')` regardless of time
  - self-service edits/withdrawals blocked after `SignupCloseUtc`
  - admin override surface enabled post-close (while still blocked for published/completed)
- Commander eligibility is cache-driven:
  - variant commander options resolved from Task C cache readers
  - no free-text commander path
- Signup snapshots persisted:
  - governor snapshot
  - requested commander snapshot
  - priority/rank/heads and optional text fields
- Added audit writes for create/edit/withdraw/admin actions in `dbo.MGE_SignupAudit`.
- Kept SQL in DAL (`mge/dal/mge_signup_dal.py`) and service Discord-agnostic.
- Corrected DAL DML to use transaction-aware cursor execution (`exec_with_cursor`) instead of `run_query`.
- Upgraded modal UX to Discord-compliant 2-step flow:
  - `MgeSignupPrimaryModal` (required/core fields)
  - `MgeSignupOptionalModal` (optional kingdom role/gear/armament fields)

### Architecture & standards compliance

- No legacy root module expansion.
- DAL/service/UI boundaries preserved.
- Reused existing helper stack (`stats_alerts.db`, `account_picker`, `governor_registry`, `core/interaction_safety`).
- UTC discipline maintained (`datetime.now(UTC)`).
- No prohibited patterns introduced (`logging.basicConfig`, bare `print`, `except: pass`).

### Tests

Added/updated unit coverage for:

- successful signup
- duplicate active signup rejected
- invalid heads range rejected
- close-lock behavior for self-service
- open-mode block behavior
- published/completed lock behavior (regardless of time)
- admin override allowed post-close (when status permits)
- signup view button handlers (signup/edit/withdraw/admin gating)
- modal-open behavior using lightweight interaction doubles

Status: ✅ Passed (`black`, `ruff`, `pyright`, `pytest`)


### Task G Delivery Record (final, refreshed)

#### Files added

- `mge/mge_dm_followup.py`
- `ui/views/mge_dm_attachment_view.py`
- `tests/test_mge_dm_followup.py` (expanded with DM routing/session tests)

#### Files modified

- `ui/views/mge_signup_modal.py`
- `ui/views/mge_signup_view.py`
- `mge/mge_signup_service.py`
- `mge/dal/mge_signup_dal.py`
- `DL_bot.py`
- `tests/test_mge_signup_views.py`

#### Delivered functionality

- Optional DM follow-up prompt after successful signup create/edit.
- DM attachment workflow supports:
  - **Upload Gear Image**
  - **Upload Armament Image**
  - **Skip / Done**
- Attachments persist to signup record (latest upload wins per kind).
- Audit details include:
  - `discord_url`
  - `filename`
  - `content_type`
  - `size`
- Signup remains valid whether or not attachments are provided.

#### Critical wiring now in place

- Added active DM session registry in `mge_dm_followup`.
- Added DM message router (`route_dm_message`) and integrated into `DL_bot.py` `on_message`.
- Router now **only handles DM messages with attachments**, preventing accidental swallowing of normal DM text/commands.
- Session cleanup on skip/done and timeout.

#### Post-review hardening applied

- Corrected py-cord button callback signature order in DM attachment view.
- Defensive UTC normalization for naive datetimes in:
  - `mge_signup_service._now_utc`
  - `mge_dm_followup._now_utc`
- Explicit Commander ID integer validation UX in signup modal.
- Fixed `current_heads` parse bug (`heads` undefined) with explicit integer parsing.
- `sign_up` linked-governor lookup moved to `asyncio.to_thread(...)` to avoid blocking event loop.
- Multi-signup support for same user/event:
  - withdraw now selects among multiple active signups
  - edit now selects among multiple active signups
- Improved admin/self-linked `DiscordUserId` handling behavior.
- Added logging usage for DM open result (`ok`) to avoid unused variable and improve diagnostics.
- Added protective try/except in DM routing block in `DL_bot.py` to preserve bot resilience.

#### Testing status

- ✅ `pytest tests/test_mge_dm_followup.py -vv` passing (including new routing/session tests)
- ✅ `pytest tests/test_mge_signup_views.py -vv` passing (updated for list-based DAL methods)
- ✅ prior Task G and related MGE tests remain green

#### Notes

- No DB migration required for Task G.
- Architecture boundaries preserved (DAL SQL, service logic, view interaction flow).
- Runtime behavior now matches PR claim: DM follow-up is offered and attachment messages are actually persisted through live message routing.

## Task H Delivery Record (final)

### SQL Server repo (`cwatts6/K98-bot-SQL-Server`)

#### Files added
- `sql_schema/dbo.v_MGE_SignupReview.View.sql`

#### Implementation summary
- Added leadership review dataset view `dbo.v_MGE_SignupReview`.
- View returns one row per **active** signup (`MGE_Signups.IsActive = 1`) with:
  - event/signup identity fields
  - governor snapshot + requested commander + request fields
  - text/attachment presence flags
  - source + signup timestamp
  - enrichment fields for latest power and KVK performance
  - prior award aggregates
  - warning flags (informational only)
- Enrichment logic follows/copies established global-latest pattern to reduce dependency risk on external view lifecycle changes.

#### Warning flags included
- `WarningMissingKVKData` (NULL/0-safe)
- `WarningHeadsOutOfRange` (defensive)
- `WarningNoAttachments`
- `WarningNoGearOrArmamentText`

#### SQL standards compliance
- File naming follows `sql_schema/<schema>.<ObjectName>.<Type>.sql`
- Includes `SET ANSI_NULLS ON` and `SET QUOTED_IDENTIFIER ON`
- No schema changes were inlined in Python code

---

### Bot repo (`cwatts6/K98-bot-mirror`)

#### Files added
- `mge/dal/mge_review_dal.py`
- `mge/mge_review_service.py`
- `mge/mge_summary_service.py`
- `ui/views/mge_leadership_board_view.py` *(Task-I-ready read scaffold)*
- `commands/mge_cmds.py` *(leadership command scaffold)*

#### Files modified
- `mge/dal/__init__.py`
- `tests/test_mge_review_service.py`
- `tests/test_mge_summary_service.py`
- `tests/test_mge_leadership_board_view.py`
- `tests/test_mge_cmds_register.py`

#### Implementation summary
- Added DAL read path for leadership review rows:
  - `fetch_signup_review_rows(event_id)`
- Added review service sorting logic in service layer (not SQL ordering), per Task H:
  1. High > Medium > Low
  2. commander name
  3. fewer prior same-commander awards
  4. fewer prior total awards in last 2 years
  5. signup timestamp ascending
- Added Task-I-ready adapter:
  - `get_review_pool_with_summary(event_id)` → returns sorted rows + summary bundle
- Added summary service helpers:
  - counts by priority
  - counts by commander
  - counts by role
  - warning totals
- Added read-only leadership board view scaffold to consume Task H dataset/service.
- Added leadership-only command scaffold (`/mge_leadership_board`) with standard decorator stack and safe defer pattern.

#### Architecture & standards compliance
- SQL access kept in DAL modules (`mge/dal/*`)
- Business logic in service layer (`mge/*_service.py`)
- Command layer thin, delegates to service
- UI layer is read-only scaffold (no destructive actions)
- Logging pattern: `logger = logging.getLogger(__name__)`
- No `logging.basicConfig()`, no bare `print()`, no `except: pass`
- UTC/time standards preserved (`datetime.now(UTC)` where applicable)

#### Helpers/patterns reused
- `stats_alerts.db.run_query`
- `core.interaction_safety.safe_command`
- `core.interaction_safety.safe_defer`
- `core.interaction_safety.send_ephemeral`
- `decoraters.py` permission/channel/usage decorators
- `versioning.versioned`

---

### Testing status

#### Targeted tests
- `tests/test_mge_review_service.py` ✅
- `tests/test_mge_summary_service.py` ✅
- `tests/test_mge_leadership_board_view.py` ✅
- `tests/test_mge_cmds_register.py` ✅

#### Quality gates
- `python -m black --check .` ✅
- `python -m ruff check .` ✅
- `python -m pyright` ✅
- `python -m pytest -q` ✅

---

### Task H acceptance mapping

- Leadership has an enriched applicant pool dataset: ✅
- Sorting behavior matches required precedence: ✅
- Summary counts and warning totals implemented: ✅
- Null-safe handling for optional enrichment fields: ✅
- Review detail remains leadership/internal (not public embed output): ✅

---

## Follow-ups required in later tasks (updated)

### Task N reminder

- Add integration test for startup + view rehydration with Task F components attached.
- Add regression coverage ensuring Task F does not regress Task E open-mode controls.

---

## Confirmed Schema Contract (PascalCase)

All deployed tables use **PascalCase** column names with no underscores.
Python code must reference these exact names when reading SQL results.

> **All 11 tables verified** against deployed `CREATE TABLE` scripts — 2026-03-11.

### dbo.MGE_Variants ✅ Verified

```
VariantId       INT IDENTITY(1,1) PK
VariantName     NVARCHAR(50)
IsActive        BIT
SortOrder       INT
CreatedUtc      DATETIME2(7)
UpdatedUtc      DATETIME2(7)
```

### dbo.MGE_Commanders ✅ Verified

```
CommanderId     INT IDENTITY(1,1) PK
CommanderName   NVARCHAR(100)
IsActive        BIT
ReleaseStartUtc DATETIME2(7) NULL
ReleaseEndUtc   DATETIME2(7) NULL
ImageUrl        NVARCHAR(500) NULL
CreatedUtc      DATETIME2(7)
UpdatedUtc      DATETIME2(7)
```

### dbo.MGE_VariantCommanders ✅ Verified

```
VariantCommanderId  INT IDENTITY(1,1) PK
VariantId           INT                FK → MGE_Variants (unique pair with CommanderId)
CommanderId         INT                FK → MGE_Commanders (unique pair with VariantId)
IsActive            BIT                DEFAULT 1
CreatedUtc          DATETIME2(7)       DEFAULT SYSUTCDATETIME()
```

**No `UpdatedUtc` column** — this is a junction table; rows are added or deactivated, not updated.

Indexes:
- `UX_MGE_VariantCommanders_Pair` — UNIQUE on `(VariantId, CommanderId)`
- `IX_MGE_VariantCommanders_Variant` — on `(VariantId, IsActive) INCLUDE(CommanderId)`

### dbo.MGE_Events ✅ Verified

```
EventId                 BIGINT IDENTITY(1,1) PK
VariantId               INT                  FK → MGE_Variants
EventName               NVARCHAR(200)
StartUtc                DATETIME2(7)
EndUtc                  DATETIME2(7)
SignupCloseUtc          DATETIME2(7)
EventMode               VARCHAR(20)          -- 'controlled' | 'open'
Status                  VARCHAR(20)          -- 'created','signup_open','signup_closed','published','completed','reopened'
RuleMode                VARCHAR(20)          -- 'fixed' | 'open'
RulesText               NVARCHAR(MAX) NULL
PublishVersion          INT
LastPublishedUtc        DATETIME2(7) NULL
SignupEmbedMessageId    BIGINT NULL
SignupEmbedChannelId    BIGINT NULL
CalendarEventSourceId   BIGINT NULL
CreatedByDiscordId      BIGINT NULL
CompletedAtUtc          DATETIME2(7) NULL
CompletedByDiscordId    BIGINT NULL
ReopenedAtUtc           DATETIME2(7) NULL
ReopenedByDiscordId     BIGINT NULL
CreatedUtc              DATETIME2(7)
UpdatedUtc              DATETIME2(7)
```

### dbo.MGE_EventCommanderOverrides ✅ Verified

```
OverrideId          INT IDENTITY(1,1) PK
EventId             BIGINT             FK → MGE_Events (unique pair with CommanderId)
CommanderId         INT                FK → MGE_Commanders (unique pair with EventId)
IsAdded             BIT                DEFAULT 1  -- 1 = add to event pool
Reason              NVARCHAR(500) NULL -- why this override exists
CreatedByDiscordId  BIGINT NULL        -- who added the override
CreatedUtc          DATETIME2(7)       DEFAULT SYSUTCDATETIME()
```

**No `IsActive` column** — uses `IsAdded` instead (semantically: "add this commander to the event").
**No `UpdatedUtc` column** — overrides are created or deleted, not edited.

Indexes:
- `UX_MGE_EventCommanderOverrides_EventCmd` — UNIQUE on `(EventId, CommanderId)`

### dbo.MGE_Signups ✅ Verified

```
SignupId                    BIGINT IDENTITY(1,1) PK
EventId                     BIGINT              FK → MGE_Events
GovernorId                  BIGINT
GovernorNameSnapshot        NVARCHAR(128)
DiscordUserId               BIGINT NULL
RequestPriority             VARCHAR(10)         -- 'High','Medium','Low'
PreferredRankBand           VARCHAR(20) NULL    -- '1-5','6-10','11-15','no_preference'
RequestedCommanderId        INT                 FK → MGE_Commanders
RequestedCommanderName      NVARCHAR(100)
CurrentHeads                INT
KingdomRole                 NVARCHAR(100) NULL
GearText                    NVARCHAR(1000) NULL
ArmamentText                NVARCHAR(1000) NULL
GearAttachmentUrl           NVARCHAR(500) NULL
GearAttachmentFilename      NVARCHAR(255) NULL
ArmamentAttachmentUrl       NVARCHAR(500) NULL
ArmamentAttachmentFilename  NVARCHAR(255) NULL
IsActive                    BIT
Source                      NVARCHAR(20)        -- 'discord' | 'admin'
CreatedUtc                  DATETIME2(7)
UpdatedUtc                  DATETIME2(7)
```

### dbo.MGE_SignupAudit ✅ Verified

```
AuditId             BIGINT IDENTITY(1,1) PK
SignupId            BIGINT              (no FK — allows audit to survive signup deletion)
EventId             BIGINT              FK → MGE_Events
GovernorId          BIGINT
ActionType          VARCHAR(30)         -- CHECK: 'create','edit','withdraw','admin_add','admin_edit','admin_remove','bulk_delete_open_switch'
ActorDiscordId      BIGINT NULL         -- who performed the action
DetailsJson         NVARCHAR(MAX) NULL  -- CHECK: ISJSON — structured change details
CreatedUtc          DATETIME2(7)        DEFAULT SYSUTCDATETIME()
```

Indexes:
- `IX_MGE_SignupAudit_Event` — on `(EventId, CreatedUtc)`
- `IX_MGE_SignupAudit_Governor` — on `(GovernorId, CreatedUtc)`

Constraints:
- `CK_MGE_SignupAudit_ActionType` — enforces allowed action values
- `CK_MGE_SignupAudit_DetailsJson` — enforces valid JSON when not NULL

### dbo.MGE_Awards ✅ Verified

```
AwardId                 BIGINT IDENTITY(1,1) PK
EventId                 BIGINT              FK → MGE_Events
SignupId                BIGINT              FK → MGE_Signups
GovernorId              BIGINT
GovernorNameSnapshot    NVARCHAR(128)       -- denormalized for display
RequestedCommanderId    INT                 FK → MGE_Commanders
RequestedCommanderName  NVARCHAR(100)       -- denormalized snapshot
AwardedRank             INT NULL            -- CHECK: 1–15 or NULL
TargetScore             BIGINT NULL
AwardStatus             VARCHAR(20)         DEFAULT 'pending' -- CHECK: 'pending','awarded','waitlist','rejected','removed'
WaitlistOrder           INT NULL
InternalNotes           NVARCHAR(1000) NULL -- leadership notes (not public)
PublishVersion          INT NULL
AssignedByDiscordId     BIGINT NULL         -- who assigned the award
CreatedUtc              DATETIME2(7)        DEFAULT SYSUTCDATETIME()
UpdatedUtc              DATETIME2(7)        DEFAULT SYSUTCDATETIME()
```

Indexes:
- `UX_MGE_Awards_EventGovernor` — UNIQUE on `(EventId, GovernorId)` — one award per governor per event
- `IX_MGE_Awards_EventRoster` — on `(EventId, AwardStatus, AwardedRank) INCLUDE(...)` — fast roster render
- `IX_MGE_Awards_Commander` — on `(RequestedCommanderId, GovernorId) INCLUDE(...)` — prior-award history lookup

Constraints:
- `CK_MGE_Awards_AwardStatus` — enforces: `'pending'`, `'awarded'`, `'waitlist'`, `'rejected'`, `'removed'`
- `CK_MGE_Awards_AwardedRank` — enforces 1–15 range or NULL

### dbo.MGE_AwardAudit ✅ Verified

```
AuditId             BIGINT IDENTITY(1,1) PK
AwardId             BIGINT              (no FK — allows audit to survive award cleanup)
EventId             BIGINT              FK → MGE_Events
GovernorId          BIGINT
ActionType          VARCHAR(30)         -- action performed
ActorDiscordId      BIGINT NULL         -- who performed the action
OldRank             INT NULL
NewRank             INT NULL
OldStatus           VARCHAR(20) NULL
NewStatus           VARCHAR(20) NULL
OldTargetScore      BIGINT NULL
NewTargetScore      BIGINT NULL
DetailsJson         NVARCHAR(MAX) NULL  -- CHECK: ISJSON — structured overflow details
CreatedUtc          DATETIME2(7)        DEFAULT SYSUTCDATETIME()
```

Indexes:
- `IX_MGE_AwardAudit_Event` — on `(EventId, CreatedUtc)`
- `IX_MGE_AwardAudit_Award` — on `(AwardId, CreatedUtc)`

Constraints:
- `CK_MGE_AwardAudit_DetailsJson` — enforces valid JSON when not NULL

### dbo.MGE_RuleAudit ✅ Verified

```
AuditId             BIGINT IDENTITY(1,1) PK
EventId             BIGINT              FK → MGE_Events
ActorDiscordId      BIGINT NULL         -- who made the change
ActionType          VARCHAR(30)         -- e.g. 'edit', 'mode_switch'
OldRuleMode         VARCHAR(20) NULL
NewRuleMode         VARCHAR(20) NULL
OldRulesText        NVARCHAR(MAX) NULL
NewRulesText        NVARCHAR(MAX) NULL
CreatedUtc          DATETIME2(7)        DEFAULT SYSUTCDATETIME()
```

Indexes:
- `IX_MGE_RuleAudit_Event` — on `(EventId, CreatedUtc)`

### dbo.MGE_DefaultRules ✅ Verified

```
RuleKey         NVARCHAR(50) PK
RuleMode        NVARCHAR(20)        -- 'fixed' | 'open'
RuleText        NVARCHAR(MAX)
IsActive        BIT
CreatedUtc      DATETIME2(7)
UpdatedUtc      DATETIME2(7)
```

### Audit table naming conventions (consistent across all 3)

| Pattern | Convention |
|---------|-----------|
| Actor tracking | `ActorDiscordId` |
| Action column | `ActionType` VARCHAR(30) |
| Before/after columns | `Old*` / `New*` prefix |
| Structured overflow | `DetailsJson` NVARCHAR(MAX) with `ISJSON` check |
| Timestamps | `CreatedUtc` only (append-only, no `UpdatedUtc`) |
| Parent FK | FK to `MGE_Events` only; child FKs intentionally omitted for durability |

---

## Confirmed Helper Reuse Registry

These existing helpers have been verified in the codebase and **must be reused** (not recreated):

### file_utils.py

| Function | Import | Purpose |
|----------|--------|---------|
| `atomic_write_json(path, obj, ...)` | `from file_utils import atomic_write_json` | Atomic temp + `os.replace` with Windows WinError32 retry |
| `read_json_safe(path, default=None)` | `from file_utils import read_json_safe` | Safe JSON read, returns default on missing/corrupt |
| `get_conn_with_retries(...)` | `from file_utils import get_conn_with_retries` | DB connection with exponential backoff + full jitter |

### Other confirmed helpers

| Function / Module | Import | Purpose |
|-------------------|--------|---------|
| `run_query(...)` | `from stats_alerts.db import run_query` | Canonical sync query helper used by MGE DAL |
| `execute(...)` / `exec_with_cursor(...)` | `from stats_alerts.db import execute, exec_with_cursor` | Canonical DML/transaction path for MGE DAL writes |
| `safe_defer(ctx)` | `from bot_helpers import safe_defer` | Deferred Discord response |
| `@versioned()`, `@safe_command`, `@track_usage()` | `from decoraters import versioned, safe_command, track_usage` | Command decorators (note: `decoraters` is intentionally misspelled) |
| `fmt_short()` | `from embed_utils import fmt_short` | Datetime display formatting |
| `core/interaction_safety.py` | `from core.interaction_safety import ...` | Safe Discord interaction wrappers |
| `account_picker.py` | `from account_picker import ...` | Multi-account governor selection UI |
| `governor_registry.py` | `from governor_registry import ...` | Governor lookup/registration |
| `constants.py` | `from constants import GUILD_ID, ...` | Channel IDs, role IDs, shared constants |
| `logging_setup.py` | `import logging; logger = logging.getLogger(__name__)` | Module-level logger pattern |

### Cache pattern to follow

The established pattern from `player_stats_cache.py` and `event_calendar/cache_publisher.py`:

1. Fetch data from SQL via `get_conn_with_retries()`
2. Validate payload is non-empty and has required shape
3. Write via `atomic_write_json()` (temp file → atomic replace)
4. On SQL failure or empty result: **preserve existing cache**, log warning
5. On first run (no prior cache): create new cache file
6. `read_json_safe()` for reading cache with safe fallback

---

## Architecture Validation (confirmed)

| Element | Location | Confirmed |
|---------|----------|-----------|
| MGE subsystem package | `mge/` (top-level, like `ark/`) | ✅ |
| Slash commands | `commands/mge_cmds.py` | ✅ |
| Discord UI views | `ui/views/mge_*.py` | ✅ |
| SQL schema files | `sql_schema/dbo.MGE_*.sql` (flat, no subdirs) | ✅ |
| Cache files | `data/mge_*.json` (runtime, gitignored) | ✅ |
| Tests | `tests/test_mge_*.py` | ✅ |
| Documentation | `docs/mge_*.md` | ✅ |
| No `bot/` wrapper | Repo root = application root | ✅ |
| No legacy module expansion | New code in target architecture dirs only | ✅ |

---

## Key Decisions Log

| # | Decision | Rationale | Decided |
|---|----------|-----------|---------|
| 1 | PascalCase column names throughout | Matches deployed schema; avoids SQL↔Python mismatches | Task A |
| 2 | `SET IDENTITY_INSERT ON/OFF` for variant seeds | Ensures stable FK-safe IDs (1–4) across environments | Task B |
| 3 | Dedicated `dbo.MGE_DefaultRules` table (not ProcConfig) | Rule templates are multi-line text with mode association; cleaner separation | Task B |
| 4 | Point cap (8m) in rule text, not bot logic | Allows per-event text edits without code changes | Task B |
| 5 | Commander availability is date-driven (`ReleaseStartUtc`/`ReleaseEndUtc`) | Supports future additions without code changes | Task A/B |
| 6 | Cache files in `data/` (gitignored), paths in `mge/mge_constants.py` | Follows existing patterns; runtime-only files not committed | Task C spec |
| 7 | Reuse `file_utils.atomic_write_json` + `read_json_safe` | Verified in codebase; avoid duplication (review blocker per standards) | Task C prep |
| 8 | Audit tables use `ActorDiscordId`, `ActionType`, `Old*/New*`, `DetailsJson` | Consistent naming verified across all 3 audit tables | Schema verification |
| 9 | Audit tables FK to `MGE_Events` only; child FKs omitted | Durability — audit survives if parent records are cleaned up | Schema verification |
| 10 | `AwardStatus` values: `pending`, `awarded`, `waitlist`, `rejected`, `removed` | Note: `waitlist` not `waitlisted`; `pending` is the default | Schema verification |
| 11 | `MGE_EventCommanderOverrides` uses `IsAdded` not `IsActive` | Semantically clearer for override intent | Schema verification |
| 12 | Task F write path uses DB transaction/cursor helper for DML (`exec_with_cursor`) | `run_query` is select-oriented; DML commit safety required | Task F |
| 13 | Task F modal UX moved to 2-step flow | Discord modal input cap is 5 components; preserves all requested fields | Task F |

---

## Prohibited Patterns (quick reference)

- ❌ `logging.basicConfig()` — blocked by pre-commit
- ❌ Bare `print()` — blocked by tests
- ❌ `except: pass` — always log
- ❌ `datetime.utcnow()` — use `datetime.now(UTC)`
- ❌ snake_case SQL column names — schema uses PascalCase
- ❌ Recreating helpers that exist in `file_utils.py`
- ❌ Adding code to legacy root modules
- ❌ `from datetime import datetime` without `UTC` — use `from datetime import UTC, datetime`

---

## Deployment Log

| Date | Task | Action | Status |
|------|------|--------|--------|
| 2026-03-11 | A | Deployed all 11 `dbo.MGE_*` tables to SQL Server | ✅ |
| 2026-03-11 | B | Ran `dbo.MGE_Variants.Seed.sql` — 4 variants seeded | ✅ |
| 2026-03-11 | B | Ran `dbo.MGE_DefaultRules.Seed.sql` — fixed + open rules seeded | ✅ |
| 2026-03-11 | B | Committed `docs/mge_reference_model.md` to bot repo | ✅ |
| 2026-03-11 | B | Synced Task A+B SQL files to `cwatts6/K98-bot-SQL-Server` | ✅ |
| 2026-03-11 | C | Added commander and variant mapping seed scripts | ✅ |
| 2026-03-11 | C | Implemented `mge/dal/mge_dal.py` + `mge/mge_cache.py` cache pipeline | ✅ |
| 2026-03-11 | C | Added `tests/test_mge_cache.py` and validated passing tests | ✅ |
| 2026-03-11 | — | Full schema contract verified (all 11 tables) | ✅ |
| 2026-03-12 | D | Implemented Task D scheduler/event pipeline (`mge_event_dal`, `mge_event_service`, `mge_embed_manager`, `mge_scheduler`) | ✅ |
| 2026-03-12 | D | Registered MGE scheduler in `bot_instance.py` using existing TaskMonitor startup pattern | ✅ |
| 2026-03-12 | D | Added Task D unit tests (`tests/test_mge_event_service.py`, `tests/test_mge_scheduler.py`) | ✅ |
| 2026-03-12 | D | Verified quality gates (`black`, `ruff`, `pyright`, `pytest`) | ✅ |
| 2026-03-12 | E | Implemented Task E main embed + admin control interactions (`mge_embed_manager`, `mge_event_service`, `ui/views/mge_*`) | ✅ |
| 2026-03-12 | E | Added destructive Switch-to-Open confirmation flow with hard signup delete + mode/rule transition | ✅ |
| 2026-03-12 | E | Added Task E unit tests (`tests/test_mge_embed_manager.py`, `tests/test_mge_open_mode_switch.py`) | ✅ |
| 2026-03-12 | E | Verified quality gates (`black`, `ruff`, `pyright`, `pytest`) | ✅ |
| 2026-03-12 | E | Applied post-review hardening fixes (transactional open-switch, admin gating, persistent custom IDs, scheduler/channel guard, embed length cap, path stability) | ✅ |
| 2026-03-12 | F | Implemented signup/edit/withdraw flow + validation + DAL (`mge_signup_dal`, `mge_signup_service`, `mge_validation`, `ui/views/mge_signup_modal.py`, `ui/views/mge_edit_view.py`) | ✅ |
| 2026-03-12 | F | Added post-close admin override surface and published/completed hard lock enforcement | ✅ |
| 2026-03-12 | F | Updated signup modal UX to 2-step flow to satisfy Discord modal field limits while preserving all Task F fields | ✅ |
| 2026-03-12 | F | Added Task F tests (`tests/test_mge_signup_service.py`, `tests/test_mge_signup_views.py`) and verified all quality gates | ✅ |
| 2026-03-12 | G | Implemented optional DM follow-up workflow (`mge_dm_followup`, `ui/views/mge_dm_attachment_view.py`) for gear/armament uploads | ✅ |
| 2026-03-12 | G | Wired DM session routing into `DL_bot.py` `on_message` and added active session registry/cleanup | ✅ |
| 2026-03-12 | G | Persisted gear/armament attachment metadata + audit details (`content_type`, `size`, URL, filename) with latest-upload-wins behavior | ✅ |
| 2026-03-12 | G | Applied review fixes (button callback signature order, non-attachment DM pass-through, naive UTC hardening, commander/heads validation, multi-signup edit/withdraw selection, async offload in signup view) | ✅ |
| 2026-03-12 | G | Expanded tests for DM routing/session behavior and updated signup view tests for plural DAL flow; all targeted pytest suites passing | ✅ |
| 2026-03-12 | G | Verified quality gates after fixes (`ruff`, `pytest`; Task G regressions resolved) | ✅ |
| 2026-03-13 | H | Added SQL review dataset view `sql_schema/dbo.v_MGE_SignupReview.View.sql` with active-signup scope, enrichment fields, prior-award aggregates, and warning flags | ✅ |
| 2026-03-13 | H | Added DAL/service stack (`mge/dal/mge_review_dal.py`, `mge/mge_review_service.py`, `mge/mge_summary_service.py`) including canonical Task-H sort and summary helpers | ✅ |
| 2026-03-13 | H | Added Task-I-ready adapter `get_review_pool_with_summary(event_id)` and leadership read scaffold (`ui/views/mge_leadership_board_view.py`) | ✅ |
| 2026-03-13 | H | Added leadership command scaffold (`commands/mge_cmds.py`) with standard decorators, `safe_defer`, and channel/permission gating aligned to project patterns | ✅ |
| 2026-03-13 | H | Added/updated tests (`test_mge_review_service.py`, `test_mge_summary_service.py`, `test_mge_leadership_board_view.py`, `test_mge_cmds_register.py`) and resolved interface drift | ✅ |
| 2026-03-13 | H | Verified full quality gates (`black`, `ruff`, `pyright`, `pytest`) | ✅ |

---
