# Phase 3B — /ark_amend_match Command Spec

## Overview
Allows leadership to amend an existing Ark match (day/time/notes). Alliance can only change if **no signups** exist.

## Status
✅ Implemented (Phase 3)
- Amend day/time/notes supported.
- Alliance change blocked if signups exist.
- Registration embed edits in place.
- Reminders rescheduled.
- Audit log entry written.

## Preconditions / Guardrails

1) **Permissions**
   - Must use existing admin/leadership decorator.

2) **Match status**
   - Can amend when status is `Scheduled` or `Locked`.
   - If `Cancelled` or `Completed`, deny.

3) **Alliance change**
   - Only allowed when there are **zero signups** for the match.

4) **Time slot validation**
   - Must be in `ArkConfig.AllowedTimeSlotsJson`.

---

## UX / UI Flow

### Command: `/ark_amend_match`

**Step 1 — Match selector**
- Dropdown: upcoming matches (by Alliance + ArkWeekendDate + Time).
- Only `Scheduled` or `Locked`.

**Step 2 — Amend fields**
- Day dropdown (Sat/Sun)
- Time dropdown (allowed slots for selected day)
- Notes field (optional)
- Alliance dropdown (optional, enabled only if no signups)

**Step 3 — Confirmation**
- Show before/after summary.
- Confirm/Cancel buttons.

---

## Data Flow (Confirm)

1. **Validate**
   - Match exists, status valid.
   - New time slot is allowed.
   - If alliance change requested: ensure no signups.

2. **Compute updated values**
   - New `match_time_utc`
   - New `signup_close_utc` from config
   - Updated `Notes`

3. **Update SQL**
   - DAL: `amend_match(...)`

4. **Edit registration embed**
   - Update time + close time + notes.
   - Keep roster list intact.

5. **Reschedule reminders**
   - Clear old reminder schedule.
   - Recompute reminders from new time.

6. **Audit log**
   - `action_type = "match_amend"`

---

## Error Messages

- “❌ Match is cancelled or completed and cannot be amended.”
- “❌ `{time}` is not an allowed time slot for `{day}`.”
- “❌ Alliance cannot be changed because signups already exist.”

---

## Notes
- All edits should be written to SQL first, then embed edits.
