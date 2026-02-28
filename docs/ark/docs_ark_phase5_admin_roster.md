# Phase 5 — Admin Roster Management + Auto‑Promotion

## Overview
Phase 5 adds leadership controls for Ark roster management:
- Admin Add / Remove / Move signups
- Post‑close overrides for leadership
- Auto‑promotion of subs when a player slot opens

All actions write to SQL first, then update embeds, and always log to `ArkAuditLog`.

---

## Phase 5A — Admin Add / Remove / Move

### Deliverables

**UI Controls**
- Admin Add / Remove / Move buttons on the registration embed.
- Visible to all users but gated to **Admin/Leadership** in callbacks.

**Admin Add Flow**
1. Click **Admin Add**
2. Name modal opens → enter governor name
3. Use `lookup_governor_id` (name_cache)
4. If multiple matches → fuzzy select list
5. Slot selector → Player or Sub
6. Validate caps + duplicate weekend rules
7. Write SQL (`add_signup` / `reactivate_signup`)
8. Update embed + audit log

**Admin Remove Flow**
1. Click **Admin Remove**
2. Choose from roster list (GovernorName + GovernorID)
3. SQL `remove_signup` → status `Removed`
4. Auto‑promote if slot was Player
5. Audit log + embed refresh

**Admin Move Flow**
1. Click **Admin Move**
2. Choose from roster list
3. Slot selector → Player or Sub
4. Validate caps / AdminOverrideSubRule
5. SQL `move_signup_slot`
6. Audit log + embed refresh

---

### Rules / Validation

- Admin operations allowed **after signup close**.
- **AdminOverrideSubRule** (default `0`):
  - If `0`, subs are blocked until players are full.
  - If `1`, admin can add/move subs even when players aren’t full.
- Governor cannot be signed up for another match on same Ark weekend.
- CH16 validation still applies.
- All changes must log in `ArkAuditLog`.

---

### Audit Log Actions

| Action | Description |
|--------|-------------|
| `signup_add` | Admin add via UI |
| `signup_remove` | Admin remove |
| `signup_move` | Admin slot change |
| `signup_promote` | Auto‑promotion |

---

## Phase 5B — Auto‑Promotion

### Deliverables
- When a Player slot opens (remove/withdraw), promote the **earliest sub**.
- Promotion logic uses SQL roster order (`CreatedAtUtc ASC`).
- Update slot type to **Player**, refresh embed.
- DM the promoted user (best effort).
- Audit log entry (`signup_promote`).

---

### Acceptance Criteria
✅ Admin add/remove/move works before and after close  
✅ AdminOverrideSubRule enforced  
✅ Auto‑promotion deterministic and logged  
✅ Promotion DM attempted  
✅ Embed refresh reflects roster change  

---

## Status
✅ Implemented (Phase 5)
- Admin buttons live on registration embed (gated by admin/leadership).
- Name modal → name_cache lookup → fuzzy select → slot picker.
- Admin Override flag added to `ArkConfig`.
- Auto‑promotion implemented and audited.
