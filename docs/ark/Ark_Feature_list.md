read and review the full Task Pack below and then build out the steps included in Task 1A. Develop the code required, I will deploy locally, validate and create the PR. As we build you must also develop unit test scripts and maintain full documentation for the config and code

Task Pack — Ark of Osiris Management (K98 Bot)
Global context for Codex (read first)

Goal: Add a new Ark module that lets leadership create Ark matches (per alliance, per Ark weekend), supports interactive player signups using registered governor accounts, enforces eligibility (CH16, bans, capacity), provides live roster embeds, and runs reminders/confirmations/check-in workflows. Canonical state is stored in SQL. Discord message IDs + reminder “sent” state are persisted to JSON for restart resilience.

Core rules

Ark occurs every 2 weekends (configurable anchor date + frequency=2 weekends).

1 match per alliance per Ark weekend.

Match day can be Sat or Sun; alliance chooses one.

Times are fixed (configurable list) and stored UTC.

Signup closes Friday 23:00 UTC before Ark weekend (configurable).

Users cannot modify signups after close; admins can override add/remove after close.

No alliance membership validation at deadline; warn at signup only.

Team cap: 30 players + 15 subs; subs only once player cap filled.

Auto-promotion: when a player slot opens, promote earliest sub.

Confirmation embed posted after signup closes.

Check-in becomes active 12h before match start.

Emergency “can’t attend” button exists only on confirmation embed.

Reuse expectations

Reuse existing admin decorators, UI View patterns in ui/views/*, reminder scheduler logic, timezone/local-time button patterns, registry/governor lookup caches, logging utilities, and JSON persistence patterns.

Phase 1 — SQL Schema + Config + Audit + Retention
Task 1A — Create Ark SQL schema objects

Deliverables

SQL scripts to create tables (or new schema) for:

ArkMatches

ArkSignups

ArkBans

ArkConfig

ArkReminderPrefs

ArkAuditLog

Requirements

ArkMatches uniqueness constraint: (alliance_id, ark_weekend_date) unique.

ArkSignups unique: (match_id, governor_id) unique.

Store ark_weekend_date (date), match_day (Sat/Sun), match_time_utc (time), signup_close_utc (datetime).

ArkSignups includes: governor_id (bigint), governor_name_snapshot, discord_user_id nullable, slot_type (Player/Sub), status (Active/Withdrawn/Removed), checked_in bit + timestamp, source (Self/Admin), created/updated.

ArkBans: supports ban by discord_user_id and/or governor_id; includes banned_ark_weekends (N) + start_ark_weekend_date + computed expiration fields.

ArkAuditLog: action_type, actor_discord_id, match_id nullable, governor_id nullable, details_json nvarchar(max).

Acceptance criteria

Tables created successfully with sensible datatypes.

Unique constraints + indexes exist for expected queries (open matches, roster, ban checks).

Foreign keys where appropriate (match_id → ArkMatches).

Task 1B — Seed default ArkConfig values

Deliverables

SQL seed script inserts default config values:

anchor weekend date = 2026-03-07

frequency_weekends = 2

allowed days = Saturday/Sunday

allowed time slots (UTC): Sat 11:00/13:00/14:00/15:00/20:00; Sun 04:00/12:00/14:00/20:00

signup close rule = Friday 23:00 UTC

capacities: players=30, subs=15

check-in activation offset = 12 hours before start

reminder intervals = 24h/4h/1h/start plus daily channel nudges until close

Acceptance criteria

Bot can read config and compute next Ark weekends deterministically.

Task 1C — Retention policy (2 years)

Deliverables

SQL stored procedure or job script definition that:

deletes/archives ArkMatches older than 2 years (and dependent rows)

keeps audit logs for 2 years as well (or longer if you prefer; default 2 years)

Acceptance criteria

Cleanup logic is safe, tested against FK constraints.

Phase 2 — Data Access Layer + Cache Plan (No commands yet)
Task 2A — Define required queries and DAL functions

Deliverables

A list (doc + stub signatures) for all DAL operations needed:

create match

amend match

cancel match

list open matches (by alliance / global)

get match by id

get roster for match

add signup (self/admin)

remove signup (self/admin)

switch signup governor (self)

move signup player/sub (admin)

ban add/remove/list + compute active bans for a given user/governor

reminder prefs read/write

mark checked-in

mark emergency withdraw

record win/loss

Acceptance criteria

Every future command/view can be implemented without new DB access patterns.

Task 2B — In-memory caches + JSON state design

Deliverables

Spec for:

ark_message_state.json (match_id → registration msg/channel; confirmation msg/channel)

ark_reminder_state.json ((match_id, user_id, reminder_type) → sent_at)

In-memory caches: governor profile cache, roster cache, open match cache

Acceptance criteria

Restart resilience plan is explicit: on startup, load open matches from SQL, rehydrate reminder schedules, and re-link to existing messages when possible.

Phase 3 — Match Lifecycle Commands (Admin/Leadership)
Task 3A — /ark_create_match command UX and validations

Deliverables

Command spec + UI design:

Setup channel restriction

Dropdowns: Alliance, ArkWeekend (computed list), Day, Time

Validation rules:

(alliance_id, ark_weekend_date) must not already exist

time must be in allowed list

compute signup_close_utc from close rule

Post registration embed in alliance registration channel

Persist message/channel IDs in SQL + ark_message_state.json

Write audit log row

Acceptance criteria

Creating a match results in a valid SQL row and a posted embed ready for signups.

Task 3B — /ark_amend_match command

Deliverables

Allow admin to change: day/time/notes (alliance change only if no signups)

Update SQL + edit registration embed

Reschedule reminders

Audit log entry

Acceptance criteria

Existing signups remain, roster preserved, reminders shift to new time.

Task 3C — /ark_cancel_match command

Deliverables

Set status Cancelled

Disable signup buttons, edit embed to show cancelled

Cancel reminders

Audit log entry

Optional: DM signed up players (configurable)

Acceptance criteria

No further signups allowed; all scheduled reminders stop.

Phase 4 — Registration Embed + Self Signup Flow
Task 4A — Registration embed format + local time toggle

Deliverables

Embed template spec:

counts, roster lists, close time, match time

“Show in my local time” button

Behavior:

embed is edited in place on any roster change

local time toggle renders per-user view (ephemeral or interaction response)

Acceptance criteria

Time conversion works using your existing timezone/location system.

✅ Implemented (Phase 4)
- Registration embed now includes numbered Player/Sub rosters and splits fields when needed.
- Local time toggle is available and renders per-user (ephemeral).

Task 4B — Self signup buttons: Join/Leave/Switch

Deliverables

Button behavior:

Join as Player (only if player slots available + before close)

Join as Sub (only if player slots full + subs slots available + before close)

Leave (before close only; after close should instruct “contact leadership”)

Switch governor (before close only; allow pick from linked governors)

Must select from registered governors for that discord user

Enforce:

CH16 per governor

ban checks (discord or governor)

governor not already signed up for another match in same Ark weekend

DM confirmation on successful signup (respect opt-out for confirmation DM? default send)

Acceptance criteria

Roster updates instantly; constraints enforced; audit log written.

✅ Implemented (Phase 4)
- Join/Leave/Switch buttons are live.
- CH16 enforced via name_cache.
- Duplicate weekend signup blocked by GovernorID.
- Signups blocked after close with “contact leadership” message.

⚠ Deferred
- Ban checks (Phase 8)
- DM confirmations (Phase 7)

Task 4C — Prevent duplicates and enforce 1 match per Ark weekend per governor

Deliverables

Validation logic and SQL constraints/checks so a governor cannot sign up twice in same weekend (even across alliances).

Acceptance criteria

Attempted duplicate returns a clear user-facing message and logs.

✅ Implemented (Phase 4)
- Duplicate GovernorID signups across alliances for same Ark weekend are blocked.

Phase 5 — Admin Roster Management + Manual Signups
Task 5A — Admin add/remove/move signup (with post-close override)

Deliverables

Admin command(s) or UI controls:

Add (GovID + GovName + Player/Sub selection)

Remove (GovID)

Move Player/Sub (GovID)

Rules:

Admin can add/remove even after close

Users cannot modify after close

Subs only allowed when players full (unless admin override explicitly enabled; default follow rule)

Removing a player triggers auto-promotion of earliest sub if available

Audit log all actions

Acceptance criteria

Post-close changes work and roster remains consistent.

✅ Implemented (Phase 5)
- Admin Add/Remove/Move buttons on registration embed (gated by admin/leadership).
- Admin Add flow: name modal → name_cache lookup → fuzzy select → slot selector.
- Admin Remove/Move uses roster-based selection (GovernorName + GovernorID).
- AdminOverrideSubRule config flag added and enforced.
- All admin actions write audit logs.

Task 5B — Auto-promotion engine

Deliverables

Deterministic promotion logic:

when player count < 30 and subs exist → promote oldest sub

update slot_type + slot_order if needed

DM promoted user

edit embeds accordingly

audit log promotion event

Acceptance criteria

Promotions occur on player removal and emergency withdraw.

✅ Implemented (Phase 5)
- Auto-promotion promotes earliest sub (SQL ordering by CreatedAtUtc).
- Promotion triggers audit log + best-effort DM.
- Registration embed refresh after promotion.

Phase 6 — Deadline Close + Confirmation Embed + Check-in + Emergency

Phase 6 delivery summary
- Scheduler locks matches at signup close and posts confirmation embeds.
- Confirmation embeds track roster + checked-in list and store message IDs in SQL + JSON.
- Check-in activates at T-12h (button hidden until then) and writes audit logs.
- Emergency withdraw on confirmation embed triggers auto-promotion and “Updates” field entry.

Task 6A — Signup close job + confirmation embed posting

Deliverables

Scheduled job at signup_close_utc:

mark match status Locked

edit registration embed to reflect “Signups Closed”

post confirmation embed to alliance planning channel

store confirmation msg/channel IDs

audit log lock event

Acceptance criteria

Happens automatically, reliably, survives restart.

✅ Implemented (Phase 6)
- Ark scheduler posts confirmation embed at signup close.
- Match status set to Locked, registration embed updated to “Signups Closed.”
- Confirmation message/channel IDs stored in JSON + SQL fields.
- Audit log entry for match_lock.

Task 6B — Check-in system (activates 12h before start)

Deliverables

Check-in button appears on confirmation embed but is disabled until T-12h

At T-12h:

button becomes active (edit embed or toggle internal logic)

optional DM “Check-in now” reminder to signed-up users

Clicking check-in:

marks checked_in in SQL

updates confirmation embed showing who has checked in

audit log

Acceptance criteria

Check-in cannot be performed early; works for all signed-up users.

✅ Implemented (Phase 6)
- Check-in button hidden until T-12h, then added to confirmation view.
- Check-in writes CheckedIn + CheckedInAtUtc and updates confirmation embed.
- Checked-in roster displayed in confirmation embed.
- Audit log entry for check_in.

Task 6C — Emergency “can’t attend” (confirmation embed only)

Deliverables

Button only on confirmation embed (not on registration embed)

On click:

confirm prompt (Are you sure?)

mark signup status = Withdrawn/Emergency

remove from player list

trigger auto-promotion

notify leadership channel (or add to embed log section)

audit log

Acceptance criteria

One click cannot silently remove someone; promotion + notifications occur.

✅ Implemented (Phase 6)
- Emergency withdraw only on confirmation embed.
- Withdraw triggers auto-promotion of earliest sub.
- Confirmation embed updates with “Updates” field.
- Audit log entry for emergency_withdraw.

Phase 7 — Reminders + Preferences + Dedupe + Failure Handling
Task 7A — Channel reminders

Deliverables

On match created: post an announcement (or rely on embed post)

Daily reminder until close (either repost or edit a single reminder message—prefer edit to reduce spam)

Strong reminder on final day (configurable)

Stop reminders after match locked/cancelled

Acceptance criteria

Reminders don’t duplicate after restart and respect match state.

Task 7B — DM reminders + opt-out preferences

Deliverables

DM schedule for signed-up users:

24h / 4h / 1h / start

plus optional check-in DM at T-12h

ArkReminderPrefs allows:

opt out all

opt out by interval

Use ark_reminder_state.json to prevent duplicates across restarts

Log DM failures (reuse your failed DM logging conventions)

Acceptance criteria

Opt-out fully respected; no duplicate DMs; failures recorded.

Phase 8 — Bans with “Next N Ark Weekends” Expiry
Task 8A — Ban rules + auto expiry

Deliverables

Ban add requires:

target: discord user and/or governor id

banned_ark_weekends N

reason

Active ban applies to the next N Ark weekends starting from configured “current/next weekend”

Auto-expire once those weekends pass (computed via ark_weekend_date stepping)

Enforcement: banned users/governors cannot self signup; admin add should also block by default

Acceptance criteria

Ban naturally expires after N weekends and no longer blocks signups.

Phase 9 — Results Tracking + Reporting Hooks
Task 9A — Record win/loss and lock completed state

Deliverables

/ark_set_result admin command:

sets Win/Loss and optional notes

status becomes Completed

edits confirmation embed to show result

audit log

Acceptance criteria

Completed matches are excluded from “open” lists and reminders stop.

Task 9B — Reporting-ready query set (no UI required yet)

Deliverables

SQL views or stored procedures for:

last 2 years matches by alliance + result

attendance metrics (signups, emergency withdrawals, check-ins)

ban history (who/why/how long)

Acceptance criteria

Outputs are stable and can be used later for dashboards/bot commands.

Phase 10 — Hardening & Operational Resilience
Task 10A — Startup rehydration and reconciliation

Deliverables

On bot startup:

load open/locked upcoming matches from SQL

rehydrate scheduled jobs (close, check-in activation, reminders)

reconcile message IDs:

if message missing, post a new embed and update state

ensure no duplicate scheduled tasks per match

Acceptance criteria

Restart mid-cycle does not cause duplicate reminders or broken buttons.

Task 10B — Comprehensive test checklist

Deliverables

A test plan covering:

match create duplicates (same alliance/weekend)

signup restrictions (CH16, bans, caps, subs only after full)

post-close admin override add/remove

emergency withdraw triggers promotion

check-in activates at T-12h only

reminders dedupe across restart

cancellation/reschedule flows

retention procedure safety

Acceptance criteria

Tests are runnable in a staging Discord server and validated with SQL checks.

Notes for implementation consistency (Codex should follow)

Use your existing View pattern and keep UI logic out of command files (match your recent refactor).

All state changes write to SQL first, then edit Discord messages.

Always create an audit log entry for: create/amend/cancel/lock/result, signup add/remove/switch, admin ops, bans, promotions, check-ins, emergency withdraw.

Keep user-facing messages clear about:

“You must be in the alliance in-game at deadline”

“Signups close Friday 23:00 UTC”

“After close, contact leadership for changes”
