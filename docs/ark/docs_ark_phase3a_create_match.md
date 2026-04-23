# Phase 3A — /ark_create_match Command Spec + UI

## Overview
Create one Ark match per alliance per Ark weekend. The command guides leadership through selecting:
- **Alliance** (from `ArkAlliances`)
- **Ark Weekend** (computed from `ArkConfig`)
- **Day** (Sat/Sun)
- **Time** (UTC allowed slots from config)

The command posts a registration embed and persists the match to SQL, **plus** saves message/channel IDs to `ark_message_state.json`.

## Status
✅ Implemented (Phase 3)
- Alliance + weekend + day + time selection flow complete.
- Signup close computed from ArkConfig close rule.
- Registration embed posted to alliance channel.
- Message/channel IDs stored in `ark_message_state.json`.
- Audit log entry written on create.

## Preconditions / Guardrails

1) **Permissions**  
   - Must use existing admin/leadership decorator (reuse existing admin decorators).

2) **Alliance configuration**  
   - The selected alliance **must** have `RegistrationChannelId` and `ConfirmationChannelId` configured.
   - If either is `NULL`, **block creation** with a clear error:
     - “Registration/Confirmation channel not configured for {Alliance}. Set channel IDs in ArkAlliances before creating a match.”

3) **Uniqueness**  
   - Must enforce `(Alliance, ArkWeekendDate)` uniqueness.
   - If duplicate exists, respond with:
     - “A match already exists for {Alliance} on {ArkWeekendDate}. Use /ark_amend_match instead.”

4) **Time slot validation**  
   - Must be in `ArkConfig.AllowedTimeSlotsJson`.
   - If not, reject with allowed times list.

5) **Signup close calculation**  
   - Use ArkConfig close rule (Friday 23:00 UTC default).
   - `signup_close_utc` = Friday before the Ark weekend date.

---

## UX / UI Flow (Slash Command)

### Command: `/ark_create_match`

**Step 1 — Alliance selector**
- Dropdown list from `ArkAlliances` where `IsActive=1`.

**Step 2 — Ark weekend selector**
- Dropdown computed from `ArkConfig.AnchorWeekendDate` + `FrequencyWeekends` (default 2).
- Present next N weekends (e.g., 6–8 options).
- Weekend date is Saturday date of that Ark cycle.

**Step 3 — Day selector**
- Dropdown: Saturday / Sunday (only from `AllowedDaysJson`).

**Step 4 — Time selector (UTC)**
- Dropdown: time slots for the chosen day from `AllowedTimeSlotsJson`.
- Format: `HH:MM UTC`.

**Step 5 — Confirmation**
- Show summary:
  - Alliance, weekend date, day, time, signup close
- Confirm/Cancel buttons.

---

## Data Flow

**On Confirm:**

1. **Validate**  
   - Alliance exists + channels set
   - Time slot allowed
   - `(Alliance, ArkWeekendDate)` does not exist

2. **Compute values**
   - `match_time_utc` = chosen slot
   - `signup_close_utc` computed from config
   - `status` = `Scheduled`

3. **Insert Match (SQL)**
   - Use `create_match(...)` DAL.
   - Persist `ArkMatches` row.

4. **Post Registration Embed**
   - Channel = `ArkAlliances.RegistrationChannelId`
   - Include:
     - Alliance
     - Match time (UTC + local time button)
     - Signup close time
     - Player/Sub counts (0/30, 0/15)
     - Rules: “Signups close Friday 23:00 UTC; after close contact leadership”

5. **Persist message/channel IDs**
   - Update JSON: `ark_message_state.json`
   - Also persist in SQL:
     - Add fields to `ArkMatches` (future schema add):  
       `RegistrationChannelId`, `RegistrationMessageId`  
       `ConfirmationChannelId`, `ConfirmationMessageId` (optional for now, used later)

6. **Audit Log**
   - Insert row in `ArkAuditLog`:
     - action_type = `match_create`
     - actor_discord_id
     - match_id
     - details_json: alliance, weekend, day, time, signup_close

---

## Embed Content (Registration)

**Title:** `Ark of Osiris — {Alliance}`  
**Fields:**
- Match Day/Time (UTC)
- Signup Close (UTC)
- Players: `0/30`
- Subs: `0/15`
- Notes (if provided)

**Footer:**  
- “Signups close Friday 23:00 UTC. After close, contact leadership.”

**Buttons:**
- Join as Player
- Join as Sub
- Leave
- Switch Governor
- Show in my local time

---

## Error Messages (User-facing)

- **Missing channels**  
  “❌ `{Alliance}` has no registration or confirmation channel configured. Update ArkAlliances first.”

- **Duplicate match**  
  “❌ A match already exists for `{Alliance}` on `{ArkWeekendDate}`.”

- **Invalid slot**  
  “❌ `{time}` is not an allowed time. Allowed times for `{day}`: …”

- **Config missing**  
  “❌ ArkConfig is missing or invalid. Contact an admin.”

---

## Notes for Implementation

- Use existing **View patterns** (`ui/views/*`) and **timezone/local-time toggle** utilities.
- **No blocking I/O** in async handlers; use `run_blocking_in_thread` where needed.
- Always write SQL **before** editing embeds.
- Always create **audit log** entry.
