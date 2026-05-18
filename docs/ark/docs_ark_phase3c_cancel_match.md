# Phase 3C — /ark_cancel_match Command Spec

## Overview
Allows leadership to cancel an Ark match. Cancelling disables signups, edits the embed, and stops reminders.

## Status
✅ Implemented (Phase 3)
- Match cancellation supported.
- Registration embed disabled with cancelled state.
- Reminders cancelled.
- Audit log entry written.

## Preconditions / Guardrails

1) **Permissions**
   - Must use existing admin/leadership decorator.

2) **Match status**
   - Can cancel if `Scheduled` or `Locked`.
   - If `Completed`, deny.

---

## UX / UI Flow

### Command: `/ark_cancel_match`

**Step 1 — Match selector**
- Dropdown: upcoming matches (by Alliance + ArkWeekendDate + Time).

**Step 2 — Confirmation**
- Confirm/Cancel buttons.

**Optional**
- “Notify signed-up players” toggle (future config).

---

## Data Flow (Confirm)

1. **Validate**
   - Match exists, status valid.

2. **Update SQL**
   - Set `Status = Cancelled`

3. **Edit registration embed**
   - Add “Cancelled” banner
   - Disable signup buttons.

4. **Cancel reminders**
   - Stop scheduled tasks for match reminders.
   - Mark reminder state in JSON to prevent resends.

5. **Audit log**
   - `action_type = "match_cancel"`

---

## Error Messages

- “❌ Match already completed and cannot be cancelled.”

---

## Notes
- SQL update first, then embed edits + reminder cancels.
- If configured, DM signed-up players that match was cancelled.
