# MGE Sign-Up Tool — Task Pack (v2)

## Context

We are building a new Mightiest Governor Event (MGE) sign-up and allocation system for the Discord bot, modelled similarly to the completed Ark tool but adapted for MGE workflows.

### Repository mapping

| Artefact | Repository | Location |
|----------|-----------|----------|
| Python subsystem | `cwatts6/K98-bot-mirror` | `mge/` (top-level package, matching `ark/` pattern) |
| Discord UI views | `cwatts6/K98-bot-mirror` | `ui/views/mge_*.py` (matching `ui/views/ark_views.py` pattern) |
| SQL schema | `cwatts6/K98-bot-SQL-Server` | `sql_schema/` (flat, no subdirectories) |
| Runtime cache files | `cwatts6/K98-bot-mirror` | `data/` (local only, `.gitignore`'d — NOT committed to git) |
| Tests | `cwatts6/K98-bot-mirror` | `tests/test_mge_*.py` |

### `data/` folder rules

The `data/` directory exists at runtime but is excluded from git via `.gitignore`:
- `data/*.json` — all JSON files are ignored
- `data/offload_tmp/` — temp workspace ignored
- `data/imports/` — import files ignored

**For MGE cache files:**
- Cache JSON files (e.g., `data/mge_commanders_cache.json`) are **runtime-generated**, never committed
- Cache path constants should be defined in `mge/mge_constants.py`
- The `data/` directory itself must exist locally; document this in deployment notes
- Never assume `data/` contents are present on fresh clone — the bot must create cache files on first run

### Key confirmed requirements

MGE events are one of 4 variants only:

- Infantry
- Cavalry
- Archer
- Leadership

Events are auto-created 7 days before start.

MGE always starts on a Monday.

Sign-up closes 1 hour before event start.

Sign-ups are per GovernorID.

One Discord user may sign up multiple linked governors.

Only one active request per GovernorID per MGE event.

Admin can manually add a governor if the GovernorID exists in known DB data.

Player request captures:

- GovernorID
- request priority: High / Medium / Low
- optional preferred rank band: 1–5 / 6–10 / 11–15 / no preference
- requested commander
- current heads owned (0–680)
- optional kingdom role
- optional gear text
- optional armament text
- optional gear + armament images via DM follow-up

Leadership uses Option B roster builder UI, not per-signup action buttons.

Leadership sets:

- awarded rank
- target score

Rank 1 target auto-generates descending defaults by -1m per rank, but manual override is allowed.

Max awarded ranks = 15.

Requested commander is never overwritten by leadership.

Public pre-allocation signup display shows governor name only.

Public embed must not show requested commander/rank request before publish.

Waitlist is supported.

Unlimited republishes with version number, timestamp, and change summary.

Event completion must not depend on result-file upload.

Open MGE mode exists:

- admin-only switch on main embed
- disables signup
- deletes existing signups for that event
- no allocation/publish workflow
- results import still allowed later for activity tracking

Rule text defaults exist for both:

- Fixed MGE
- Open MGE

Rules must be editable per event.

Results reconciliation is Phase 2, not critical path.

---

## Task A — Add SQL schema for MGE reference, event, signup, award, rules, and audit storage

**Task:** Create the SQL schema required for the MGE system.

**Do:**
- Add new tables for:
  1. MGE_Variants
  2. MGE_Commanders
  3. MGE_VariantCommanders
  4. MGE_Events
  5. MGE_EventCommanderOverrides
  6. MGE_Signups
  7. MGE_SignupAudit
  8. MGE_Awards
  9. MGE_AwardAudit
  10. MGE_RuleAudit
- Add sensible PKs, FKs, `created_utc`/`updated_utc` columns, and `is_active`/`status` fields where appropriate.
- Add `event_mode` to MGE_Events with allowed values `controlled`/`open`.
- Add lifecycle status to MGE_Events (e.g., `created`, `signup_open`, `signup_closed`, `published`, `completed`, `reopened`).
- Add `rules_text` and `rule_mode` to MGE_Events.
- Add publish version tracking to MGE_Events (`publish_version INT`, `last_published_utc DATETIME2`).
- Add optional `waitlist_order` to MGE_Awards.
- Add source markers for admin/manual vs discord signups (`source NVARCHAR(20)` with values `discord`/`admin`).
- Add attachment metadata columns to MGE_Signups for gear and armament images (`gear_attachment_url`, `gear_attachment_filename`, `armament_attachment_url`, `armament_attachment_filename`).
- Add indexes for:
  - event lookups
  - governor/event uniqueness
  - status lookups
  - award roster lookups
  - commander mapping lookups
- Enforce one active signup per GovernorID per event at DB level with a unique filtered index where possible.
- Follow existing SQL conventions: include `SET ANSI_NULLS ON` / `SET QUOTED_IDENTIFIER ON` headers.
- Store `signup_embed_message_id` and `signup_embed_channel_id` on MGE_Events for rehydration.

**Do not:**
- Do not build results import tables in this task.
- Do not build stored procedures unless strictly needed for schema bootstrap.
- Do not hardcode commander lists in the bot.
- Do not create subdirectories under `sql_schema/`.

**Files (SQL Server repo):**
- `sql_schema/dbo.MGE_Variants.Table.sql`
- `sql_schema/dbo.MGE_Commanders.Table.sql`
- `sql_schema/dbo.MGE_VariantCommanders.Table.sql`
- `sql_schema/dbo.MGE_Events.Table.sql`
- `sql_schema/dbo.MGE_EventCommanderOverrides.Table.sql`
- `sql_schema/dbo.MGE_Signups.Table.sql`
- `sql_schema/dbo.MGE_SignupAudit.Table.sql`
- `sql_schema/dbo.MGE_Awards.Table.sql`
- `sql_schema/dbo.MGE_AwardAudit.Table.sql`
- `sql_schema/dbo.MGE_RuleAudit.Table.sql`

**Tests:**
- Validate all scripts deploy cleanly to a dev database.
- Validate FK relationships.
- Validate index creation.
- Validate one-active-signup rule via filtered unique index.
- Validate allowed status/mode values.

**Acceptance:**
- Schema deploys without errors.
- Tables cover controlled and open MGE modes.
- One active signup per GovernorID per event is enforceable.
- Award, publish version, and audit storage are all supported.
- File naming matches existing `sql_schema/` flat convention exactly.

---

## Task B — Seed variants, default rule templates, and commander model support

**Task:** Add seed/reference data support for MGE variants and default rule templates, and prepare commander availability model.

**Do:**
- Seed the 4 valid variants only:
  - Infantry
  - Cavalry
  - Archer
  - Leadership
- Add a seed script for default event rule templates:
  - Fixed MGE rules
  - Open MGE rules
- Ensure commander records support:
  - permanent additions over time
  - optional `release_start_utc`
  - optional `release_end_utc`
- Ensure variant-to-commander mapping is data-driven.
- Design event commander override support for one-off additions at event level.

**Do not:**
- Do not hardcode the 8m cap into bot logic.
- Do not assume commanders are ever deprecated permanently from history.
- Do not implement event override UI yet.

**Files (SQL Server repo):**
- `sql_schema/dbo.MGE_Variants.Seed.sql`
- `sql_schema/dbo.MGE_DefaultRules.Seed.sql`

**Files (Python repo, optional):**
- `docs/mge_reference_model.md`

**Tests:**
- Verify only 4 variants are seeded.
- Verify default fixed and open rules can be retrieved.
- Verify commander availability model supports future date-based additions.

**Acceptance:**
- Variant and default rule seeds exist and are reusable.
- Commander availability is fully data-driven.
- Event-level overrides are structurally supported.

---

## Task C — Build commander cache pipeline from SQL to JSON with safe overwrite protection

**Task:** Build a JSON cache for MGE commanders and variant mappings for fast dropdown population.

**Do:**
- Load commander master list from SQL.
- Load variant-to-commander mappings from SQL.
- Apply date-validity filtering where relevant.
- Write JSON cache files to `data/` directory used by the bot for dropdown population.
- Use safe cache refresh rules per Engineering Standards §9:
  - validate non-empty
  - validate required fields/shape
  - write temp file first
  - atomic replace only on success
- Log and preserve prior cache if SQL returns blank or invalid data.
- Add helper functions to read the cache in bot code.
- Handle first-run gracefully when `data/` directory exists but cache files don't yet.
- Define cache paths as constants in `mge/mge_constants.py`.

**Do not:**
- Do not overwrite good cache with blank/invalid cache.
- Do not make the bot depend on live SQL for every dropdown interaction.
- Do not hardcode commanders in Python.
- Do not commit cache files to git (they are `.gitignore`'d under `data/*.json`).

**Files (Python repo):**
- `mge/mge_cache.py`
- `mge/mge_commander_repository.py`
- `mge/mge_constants.py`

**Runtime files (not committed — `data/` is `.gitignore`'d):**
- `data/mge_commanders_cache.json`
- `data/mge_variant_commanders_cache.json`

**Helpers to reuse (check before creating):**
- `file_utils.py` — SQL connection helpers, file I/O
- Any existing cache patterns (check `*_cache.py` files at root for atomic-replace patterns)

**Tests:**
- Unit test successful cache build.
- Unit test blank SQL response does not overwrite cache.
- Unit test malformed payload does not overwrite cache.
- Unit test dropdown loader reads from cache correctly.
- Unit test first-run creates cache when no prior file exists.

**Acceptance:**
- Valid cache files are generated from SQL into `data/`.
- Bad refreshes do not destroy previous good cache.
- Bot-side dropdown data can be loaded from JSON without SQL roundtrips.
- First-run scenario works without crashing.

---

## Task D — Add MGE event scheduler and event creation flow from calendar

**Task:** Auto-create MGE events from calendar data 7 days before start.

**Do:**
- Read upcoming MGE events from the existing event source.
  - Check `dbo.EventInstances`, `dbo.EventRecurringRules`, `dbo.EventOneOffEvents` in the SQL repo.
  - Check `event_calendar/` and `event_scheduler.py` in the Python repo for existing calendar integration patterns.
- Identify MGE events and their variant.
- Create `dbo.MGE_Events` rows 7 days before event start.
- Default new events to:
  - `event_mode = 'controlled'`
  - `rule_mode = 'fixed'`
  - `rules_text` = default fixed rules
  - `status = 'signup_open'` at creation time
  - `signup_close_utc` = start time minus 1 hour
- Prevent duplicate creation for the same event.
- Post the main MGE signup embed in the MGE signup channel (channel ID from `constants.py`).
- Store the posted `message_id` and `channel_id` in `dbo.MGE_Events` for rehydration.
- Refresh/update the embed if the event already exists.
- Register the scheduler task following `ark/ark_scheduler.py` patterns.

**Do not:**
- Do not require manual creation in the normal path.
- Do not create duplicate events if the scheduler runs more than once.
- Do not guess the variant outside the calendar source.

**Files (Python repo):**
- `mge/mge_scheduler.py`
- `mge/mge_event_service.py`
- `mge/mge_embed_manager.py`
- Modify bot startup files to register the MGE scheduler

**Tests:**
- Unit test event creation exactly 7 days before start.
- Unit test duplicate scheduler runs do not create duplicate DB rows or duplicate embeds.
- Unit test signup close time is start minus 1 hour.
- Unit test default fixed rules are loaded into new event.

**Acceptance:**
- Upcoming MGE events are created automatically.
- Each event has a DB record and a signup embed.
- Duplicate creation is prevented.
- Scheduler follows existing `ark_scheduler.py` patterns.

---

## Task E — Build main public MGE embed with admin controls and Open-mode switch

**Task:** Build the main MGE embed and its interaction model, including admin-only Switch to Open.

**Do:**
- Build a public embed showing:
  - event title
  - variant
  - start/end time (use `fmt_short()` from `embed_utils.py` for display)
  - signup close time
  - current mode (controlled/open)
  - public signup count
  - governor-name-only signup list before allocation
  - event rules text
- Add user-facing buttons:
  - Sign Up
  - Withdraw
  - View / Edit My Request
- Add admin-only controls (check role IDs from `constants.py`):
  - Switch to Open
  - Edit Rules
  - Refresh Signups / Refresh Embed
  - Open Leadership Board
  - optionally Close Signup if needed
- When Switch to Open is pressed:
  - require admin confirmation (use confirmation pattern from `ark/confirmation_flow.py`)
  - delete existing signups for that event
  - disable signup/withdraw/edit
  - disable controlled roster actions
  - set `event_mode = 'open'`
  - set `rule_mode = 'open'`
  - load default open rules text
  - update embed accordingly
  - audit the change
- Block switching to open after published/live in v1.
- Use `core/interaction_safety.py` patterns for safe interaction handling.

**Do not:**
- Do not allow accidental one-click destructive switch without confirmation.
- Do not keep old signups when switching to open.
- Do not show requested commander or requested priority publicly before publish.
- Do not show Discord mentions in the public signup list.

**Files (Python repo):**
- `ui/views/mge_signup_view.py`
- `ui/views/mge_admin_view.py`
- `mge/mge_embed_manager.py`
- `mge/mge_event_service.py`

**Tests:**
- Unit test controlled embed render.
- Unit test open embed render.
- Unit test Switch to Open deletes signups and updates mode/rules.
- Unit test Switch to Open is blocked after publish/live.
- Unit test public list shows governor name only.

**Acceptance:**
- Main embed supports both controlled and open modes.
- Open switch is safe, admin-only, and destructive by design.
- Public display rules are correct.
- Views are in `ui/views/` following existing convention.

---

## Task F — Build player signup, edit, withdraw flow with one-active-signup enforcement

**Task:** Implement player signup/edit/withdraw for controlled MGE events.

**Do:**
- On Sign Up:
  - Reuse `account_picker.py` for governor selection where applicable
  - Use `governor_registry.py` for governor lookup/validation
  - If only one linked governor exists, preselect it
  - Validate GovernorID exists and is linked to the user
  - Enforce one active signup per GovernorID per event
- Collect:
  - request priority (High / Medium / Low)
  - preferred rank band (1–5 / 6–10 / 11–15 / no preference)
  - requested commander dropdown from cache (loaded from `data/mge_commanders_cache.json`)
  - current heads owned, integer 0–680
  - optional kingdom role
  - optional gear text
  - optional armament text
- Save signup to SQL.
- Store snapshot fields such as governor name and requested commander display text.
- Support View / Edit My Request before close.
- Support Withdraw before close.
- After close:
  - player self-edit/withdraw blocked
  - admin override still allowed
- If `event_mode = 'open'`:
  - block signup/edit/withdraw entirely
- Use `core/interaction_safety.py` for safe interaction handling.

**Do not:**
- Do not allow free-text commander entry.
- Do not allow more than one active signup per governor per event.
- Do not allow player changes after lock.
- Do not require attachments to complete signup.
- Do not recreate governor selection logic if `account_picker.py` already provides it.

**Files (Python repo):**
- `ui/views/mge_signup_modal.py`
- `ui/views/mge_edit_view.py`
- `mge/mge_signup_service.py`
- `mge/mge_validation.py`

**Helpers to reuse:**
- `account_picker.py` — multi-account selection UI
- `governor_registry.py` — governor lookup/registration
- `core/interaction_safety.py` — safe interaction handling

**Tests:**
- Unit test successful signup.
- Unit test duplicate active signup rejected.
- Unit test invalid heads range rejected.
- Unit test edit before close works.
- Unit test withdraw before close works.
- Unit test signup blocked after close.
- Unit test signup blocked when event mode = open.

**Acceptance:**
- Controlled event signup flow works end-to-end.
- One-active-signup rule is enforced.
- Event lock rules behave correctly.
- Existing helpers (`account_picker.py`, `governor_registry.py`) are reused.

---

## Task G — Add DM-based attachment follow-up flow for gear and armament images

**Task:** Add optional DM follow-up flow for gear and armament screenshots after signup.

**Do:**
- After successful signup, optionally offer DM follow-up for attachments.
- In DM, guide the user to submit:
  - one gear image
  - one armament image
- Store per Execution Guidelines §14:
  - Discord attachment URL
  - filename
  - content type / size if useful
  - attachment metadata as needed
- Link attachments back to the active signup record.
- Allow signup to remain valid even if no attachments are sent.
- Handle closed DMs gracefully with a clear user-facing fallback message.

**Do not:**
- Do not make attachments mandatory.
- Do not download/store binary files locally in v1.
- Do not clutter the signup channel with public attachment uploads.

**Files (Python repo):**
- `mge/mge_dm_followup.py`
- `ui/views/mge_dm_attachment_view.py`
- `mge/mge_signup_service.py` (modify)

**Tests:**
- Unit test DM follow-up is initiated after signup.
- Unit test gear attachment stored correctly.
- Unit test armament attachment stored correctly.
- Unit test closed DMs handled gracefully.

**Acceptance:**
- Optional attachment workflow works through DM.
- Signup remains valid with or without images.
- Attachment metadata is stored and linked to the signup.

---

## Task H — Build leadership review board data query/view and summary dataset

**Task:** Build the SQL review dataset and bot service layer used by leadership to evaluate applicants.

**Do:**
- Create a SQL view named `dbo.v_MGE_SignupReview`.
- Include for each active signup:
  - event_id, signup_id
  - governor_id, governor_name
  - requested commander
  - request priority, preferred rank band
  - current heads
  - kingdom role
  - gear/armament text presence
  - attachment presence
  - signup timestamp
  - source (discord/admin)
  - current/latest power (from `dbo.LATEST_POWER` or `dbo.v_PlayerLatestStats`)
  - last KVK rank (from `dbo.PlayerKVKHistory` or `dbo.v_PlayerKVK_Last3`)
  - last KVK kills (from `dbo.v_PlayerKVK_Last3`)
  - prior awards for requested commander
  - prior awards overall
  - prior awards overall in last 2 years
  - warning flags / eligibility indicators
- Add bot-side summarisation helpers:
  - counts by priority
  - counts by commander
  - counts by role
  - warning totals
- Sort leadership pool by:
  1. High > Medium > Low
  2. commander name
  3. fewer prior same-commander awards first
  4. fewer prior total awards in last 2 years first
  5. signup timestamp ascending

**Do not:**
- Do not expose this review detail publicly.
- Do not make warnings hard blockers.
- Do not require all enrichment fields to exist if some are null.

**Files (SQL Server repo):**
- `sql_schema/dbo.v_MGE_SignupReview.View.sql`

**Files (Python repo):**
- `mge/mge_review_service.py`
- `mge/mge_summary_service.py`

**Tests:**
- Validate view/query returns expected fields.
- Validate sorting order.
- Validate summary counts.
- Validate null-safe handling for optional enrichment data.

**Acceptance:**
- Leadership has a reliable enriched applicant pool.
- Sorting and summary data match agreed rules.
- Review data is separated cleanly from public display.

---

## Task I — Build leadership roster builder UI (Option B) for award allocation and waitlist

**Task:** Implement the leadership roster builder interface for MGE allocations.

**Do:**
- Build a leadership-only roster builder with two logical sections:
  1. applicant pool
  2. awarded roster builder
- Support leadership actions:
  - add signup to roster
  - assign rank 1–15
  - move ranks up/down
  - remove from roster
  - send signup to waitlist
  - set optional `waitlist_order`
  - reject/remove from consideration
  - add optional internal reason free text
- Keep requested commander fixed from the signup and display it in the roster.
- Prevent more than 15 awarded ranks.
- Ensure one governor cannot occupy multiple awarded ranks in the same event.
- Support loading current roster from DB and editing it safely over time.
- Use `core/interaction_safety.py` for safe interaction handling.

**Do not:**
- Do not let leadership overwrite the requested commander.
- Do not exceed 15 awarded places.
- Do not expose the roster builder outside leadership/admin roles.

**Files (Python repo):**
- `ui/views/mge_leadership_board_view.py`
- `ui/views/mge_roster_builder_view.py`
- `mge/mge_roster_service.py`

**Tests:**
- Unit test add to roster.
- Unit test move rank up/down.
- Unit test duplicate governor in roster blocked.
- Unit test max 15 ranks enforced.
- Unit test waitlist placement.

**Acceptance:**
- Leadership can build and maintain an awarded roster from the signup pool.
- Waitlist is supported.
- Requested commander remains fixed.

---

## Task J — Add target generation, manual override, publish, republish, and change-log flow

**Task:** Implement target generation and public roster publication.

**Do:**
- Allow leadership to set rank 1 target in millions.
- Auto-generate default targets descending by 1m per rank.
- Allow manual override of any individual rank target.
- Publish one main public awarded-list embed showing:
  - governor name
  - requested commander
  - awarded rank
  - target score
- Tag/mention awarded players where possible in the published list.
- On each publish:
  - increment version number
  - store published timestamp (UTC)
  - generate change summary
- Support unlimited republishes.
- Post follow-up change-log messages on republish rather than overloading the main embed.
- Record publish version per award row or equivalent structure.

**Do not:**
- Do not make descending target values mandatory after generation.
- Do not publish applicants who were not awarded/waitlisted appropriately.
- Do not lose history of previous publish versions.

**Files (Python repo):**
- `mge/mge_publish_service.py`
- `ui/views/mge_publish_view.py`
- `mge/mge_embed_manager.py` (modify)

**Tests:**
- Unit test target generation from rank 1 target.
- Unit test manual override persists.
- Unit test publish increments version.
- Unit test republish generates a change summary.
- Unit test public embed content is correct.

**Acceptance:**
- Leadership can generate, adjust, and publish the final awarded roster.
- Publish versioning and change-log are fully supported.

---

## Task K — Add rule editing support with per-event overrides

**Task:** Support default rule templates plus editable per-event rule overrides.

**Do:**
- On event creation:
  - controlled event gets default fixed rules
- On switch to open:
  - event gets default open rules
- Add admin-only Edit Rules action.
- Allow editing the rules text stored against the event.
- Refresh the public embed after rule edits.
- Audit old vs new rule text in `dbo.MGE_RuleAudit`.
- Keep the design flexible so point-cap text can be changed per event, e.g. 8m to 10m.

**Do not:**
- Do not require code changes for simple rule-text changes.
- Do not hardcode fixed/open wording in the embed renderer only.
- Do not lose previous versions of edited rules in audit.

**Files (Python repo):**
- `ui/views/mge_rules_edit_view.py`
- `mge/mge_rules_service.py`
- `mge/mge_embed_manager.py` (modify)

**Tests:**
- Unit test fixed rules loaded on creation.
- Unit test open rules loaded on switch.
- Unit test rule edit updates event and embed.
- Unit test rule audit entry written.

**Acceptance:**
- Each event can carry its own editable rules text.
- Rule edits are auditable and reflected publicly.

---

## Task L — Add event completion, freeze, reopen, and post-event internal summary

**Task:** Close the event cleanly at the end of 6 days without depending on a results upload.

**Do:**
- At event end:
  - freeze the final roster state
  - mark event `status = 'completed'`
  - prevent further normal edits
- Support admin-only reopen action for correction if needed.
- Generate an internal post-event summary/report containing:
  - total signups
  - signups by commander
  - signups by priority
  - awarded count
  - waitlist count
  - number of republishes / changes
  - fairness indicators where available
- For open events:
  - still mark event completed normally
  - no controlled roster workflow required

**Do not:**
- Do not require a result file to complete the event.
- Do not allow normal post-completion changes without explicit admin reopen.
- Do not conflate completion and reconciliation.

**Files (Python repo):**
- `mge/mge_completion_service.py`
- `mge/mge_report_service.py`
- `ui/views/mge_admin_completion_view.py`

**Tests:**
- Unit test event completes after 6 days.
- Unit test controlled event freezes edits.
- Unit test open event completes without roster dependency.
- Unit test admin reopen works.
- Unit test summary report generation.

**Acceptance:**
- Event completion is independent of result-file upload.
- Freeze and reopen rules work correctly.
- Internal summary exists for both controlled and open events.

---

## Task M — Phase 2 scaffold only: results import pipeline for open and controlled events

**Task:** Add the initial scaffold for MGE results import, but keep reconciliation out of the critical path.

**Do:**
- Create a parser/service for xlsx imports with columns:
  - Rank
  - Player ID
  - Player
  - Score
- Support filenames like: `mge_rankings_kd1198_20260311.xlsx`
- Parse:
  - rank as int
  - player_id as bigint
  - player name as Unicode text
  - score as numeric after stripping commas
- Preserve Unicode names safely.
- Match import to an MGE event by admin selection or safe event lookup.
- For open events: store final rank/player/score only
- For controlled events: scaffold storage for later reconciliation
- Keep this as phase-2-ready and non-blocking.
- Import files can be uploaded and temporarily stored in `data/imports/` (also `.gitignore`'d).

**Do not:**
- Do not make event completion depend on this.
- Do not implement full reconciliation logic in this task.
- Do not assume commander can be derived from open-event results.

**Files (Python repo):**
- `mge/mge_results_import.py`
- `mge/mge_xlsx_parser.py`

**Files (SQL Server repo — optional scaffold):**
- `sql_schema/dbo.MGE_ResultImports.Table.sql`
- `sql_schema/dbo.MGE_FinalResults.Table.sql`

**Tests:**
- Unit test parse of sample file format.
- Unit test comma-stripped numeric score conversion.
- Unit test Unicode player name handling.
- Unit test open-event result storage path.
- Unit test controlled-event scaffold path.

**Acceptance:**
- The system is ready for later result imports.
- Open-event results can be recorded without reconciliation logic.
- No critical-path dependency is introduced.

---

## Task N — Wiring, permissions, logging, startup registration, and regression coverage

**Task:** Integrate the MGE system into the bot cleanly and safely.

**Do:**
- Register scheduler/startup hooks (follow `ark/ark_scheduler.py` registration pattern).
- Register views and persistent UI components (follow `rehydrate_views.py` patterns).
- Apply admin/leadership permission checks using role IDs from `decoraters.py`.
- Add standard command decorators: `@versioned()`, `@safe_command`, `@track_usage()` from `decoraters.py`.
- Use `safe_defer(ctx)` for deferred responses.
- Add structured logging using module-level loggers (`logger = logging.getLogger(__name__)`):
  - event creation
  - signup create/edit/withdraw
  - switch to open
  - publish/republish
  - completion/reopen
  - cache refresh
  - rule edits
- Add defensive error handling and user-friendly failure responses.
- Ensure restart-safe behaviour where message IDs / event IDs are reloaded from DB.
- Use `graceful_shutdown.py` patterns for shutdown cancellation.
- Add regression tests where existing event systems could be affected.
- Create `mge/__init__.py` for package initialisation.

**Do not:**
- Do not leave MGE state only in memory if it must survive restarts.
- Do not bypass existing permission decorators/patterns.
- Do not break Ark or other event modules.
- Do not use `logging.basicConfig()` (blocked by pre-commit hook).
- Do not use bare `print()` in production code.
- Do not use `datetime.utcnow()` — use `datetime.now(UTC)`.

**Files (Python repo):**
- `commands/mge_cmds.py` — all slash commands with standard decorators
- `mge/__init__.py`
- Bot startup/registration files (modify)
- `tests/test_mge_*.py`

**Prohibited patterns (enforced by pre-commit):**
- `logging.basicConfig()` — use `logger = logging.getLogger(__name__)`
- `except: pass` — always log and handle
- `datetime.utcnow()` — use `datetime.now(UTC)`

**Tests:**
- Integration test startup loads MGE scheduler and views.
- Integration test permissions are enforced.
- Integration test state rehydrates from DB after restart.
- Regression test existing event systems (Ark, calendar) are unaffected.

**Acceptance:**
- MGE system is fully wired into the bot.
- State survives restart.
- Logs and permissions are production-safe.
- All quality gates pass: `black`, `ruff`, `pyright`, `pytest`.

---

## Recommended implementation order

Use this order to keep dependencies sensible:

1. Task A — SQL schema
2. Task B — seed/reference model
3. Task C — commander cache
4. Task D — scheduler + event creation
5. Task E — main embed + open mode
6. Task F — signup/edit/withdraw
7. Task G — DM attachments
8. Task H — review dataset
9. Task I — leadership roster builder
10. Task J — targeting + publish
11. Task K — rule editing
12. Task L — completion/freeze/report
13. Task M — phase 2 import scaffold
14. Task N — integration/regression hardening

---

## Cross-task rules to respect everywhere

### Global rules

- Requested commander is chosen by the player and must not be overwritten by leadership.
- One active signup per GovernorID per MGE event.
- Public pre-allocation view shows governor names only.
- Requested commander / rank request / enrichment data are leadership-only until publish.
- Open mode is destructive to existing signups and requires confirmation.
- Event completion must not depend on results upload.
- Good JSON cache in `data/` must never be overwritten with blank/invalid data.
- Attachment handling is DM-first and optional.
- All meaningful state must persist in SQL and survive bot restart.
- All leadership/admin actions affecting event state must be audited.
- `data/` directory is runtime-only (`.gitignore`'d) — never assume its contents exist on fresh clone.

### Architecture rules (from Engineering Standards + Execution Guidelines)

- MGE package lives at `mge/` (top-level, like `ark/`).
- Discord UI views live in `ui/views/mge_*.py` (like `ui/views/ark_views.py`).
- Slash commands live in `commands/mge_cmds.py`.
- SQL files live flat in `sql_schema/` (no subdirectories).
- Cache files live in `data/` (not committed).
- All commands use `@versioned()`, `@safe_command`, `@track_usage()`.
- All commands call `safe_defer(ctx)`.
- All modules use `logger = logging.getLogger(__name__)`.
- All timestamps use `datetime.now(UTC)`, display with `fmt_short()`.
- Reuse existing helpers before creating new ones (see Execution Guidelines §3).
- Known filename quirks (`decoraters.py`, etc.) must be preserved exactly.

---

## Definition of Done for the full feature

- MGE events auto-create from calendar 7 days before start.
- Controlled and Open event modes both work.
- Players can sign up linked governors with the agreed request model.
- Leadership can review enriched applicants and build a ranked roster.
- Targets auto-generate and can be overridden.
- Public roster publish and republish with change-log work.
- Rules are editable per event.
- Event completes after 6 days without requiring an import file.
- Open MGE deletes signups and disables controlled workflow safely.
- Cache (in `data/`), state, and message IDs survive restart.
- Logging, permissions, and audit trails are in place.
- All quality gates pass (`black`, `ruff`, `pyright`, `pytest`).
- No regressions in Ark or other subsystems.
