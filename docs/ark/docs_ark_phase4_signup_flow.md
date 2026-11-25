# Phase 4 — Registration Embed + Self Signup Flow (Spec)

## Overview
Phase 4 introduces interactive signups on the registration embed:
- Join as Player
- Join as Sub
- Leave
- Switch Governor
- Local time button

All signup actions must write to SQL first, then update embeds and caches.

## Status
✅ Implemented (Phase 4)
- Registration embed with roster lists + local time toggle.
- Join/Leave/Switch buttons live.
- CH16 enforced.
- Duplicate weekend signup blocked by GovernorID.
- Post‑close self‑signup blocked.

## Phase 4A — Registration Embed Format + Local Time Toggle

### Deliverables
- Registration embed shows:
  - Match time, signup close time
  - Player/Sub counts
  - Player/Sub roster lists (numbered)
  - Notes (optional)
- Embed is edited in place on roster change.
- Local time toggle button renders user‑specific times (ephemeral).

### Data Flow
1. Fetch match + roster from SQL.
2. Build embed using:
   - Counts (players/subs)
   - Roster lists (numbered; split into multiple fields if large)
3. Attach combined view:
   - Signup buttons + local time button.

---

## Phase 4B — Self Signup Buttons (Join/Leave/Switch)

### Deliverables
Buttons and behavior:
- **Join as Player**  
  - only if before close  
  - only if player cap not full  
- **Join as Sub**  
  - only if before close  
  - only if players full AND subs cap not full  
- **Leave**  
  - only if before close  
- **Switch Governor**  
  - only if before close  
  - allows user to switch governor in same Discord account  

All actions must:
- validate eligibility
- write SQL
- update embed
- audit log

### Enforcement rules
- CH16 per governor (from name_cache)
- Ban checks for Discord user and/or governor (deferred to Phase 8)
- Governor cannot sign up in another alliance for the same Ark weekend
- “After close, contact leadership” message

### Governor picker
- Use registry‑backed account selector (`account_picker.build_unique_gov_options`)

---

## Phase 4C — Prevent Duplicate Signups Across Alliances

### Deliverables
- Validation that a governor is not already signed up for any match on the same Ark weekend.
- User‑friendly error message.

### Query
- Match by ArkWeekendDate + active signup by GovernorId (excludes current match).

---

## Deferred
- Ban enforcement (Phase 8)
- DM confirmation (Phase 7)
