# Phase 9 — Ark Results + Reporting (Feature Summary + Smoke Test Plan)

**Goal:** Document Phase 9 functionality and validate all Phase 9 features end‑to‑end in Discord with SQL verification.

---

## ✅ Phase 9 Feature Summary (What Was Added)

### 1) Match Results Flow
- **Record Result** button appears after match start (T+30m refresh).
- Result is selected from a **Win/Loss dropdown** (no free‑text).
- Optional **Result Notes** supported.
- Persists to SQL:
  - `ArkMatches.Result`
  - `ArkMatches.ResultNotes`
  - `ArkMatches.CompletedAtUtc`
  - `ArkMatches.Status = Completed`

### 2) No Show Tracking
- **No Show** button appears after match start (T+30m refresh).
- Admin selects a roster member marked as Active.
- Persists to SQL:
  - `ArkSignups.NoShow = 1`
  - `ArkSignups.NoShowAtUtc`

### 3) Reporting
- `/ark_report_players` produces a paged player report.
- Report includes:
  - Matches played
  - Emergency withdrawals
  - No shows
  - Win %
- View is navigated with Next/Prev buttons.

### 4) Admin Add Fuzzy Lookup (improved UX)
- Admin Add now uses a **fuzzy governor search**:
  - Name/ID is entered in modal
  - **Fuzzy results dropdown** shown
  - Admin selects governor → chooses Player/Sub
- Prevents typos and improves consistency with `/player_profile`.

### 5) Guard Rails
- Cancelled match blocks:
  - Record Result
  - No Show

---

# ✅ Smoke Test Plan

## 0) Pre‑flight
- Ensure bot is running on **main** with Phase 9 changes.
- Confirm SQL migrations applied:
  - `dbo.ArkMatches.Alter.Results.sql`
  - `dbo.ArkSignups.Alter.NoShow.sql`
  - `dbo.vw_ArkPlayerReport.View.sql`

---

## 1) Create Match
1. Use `/ark_create_match` in setup channel.
2. Select alliance / weekend / day / time.
3. Verify **registration embed** posts.
4. Confirm SQL row created in `ArkMatches`.

---

## 2) Signups
1. Add 2–3 players and 1 sub via self signup.
2. Verify roster counts update in embed.
3. Ensure roster order is stable.

---

## 3) Admin add/remove/move (Phase 5 + Phase 9 UX update)
1. Use **Admin Add** → enter name or ID.
2. **Fuzzy lookup dropdown** appears with matching governors.
3. Select a governor → choose **Add as Player** or **Add as Sub**.
4. Use **Admin Move** to swap a slot.
5. Use **Admin Remove** and confirm promotion of earliest sub.
6. Confirm audit log entries exist.

---

## 4) Close signup → Confirmation embed
1. Set `SignupCloseUtc` to now (or wait).
2. Confirm scheduler locks match + posts confirmation embed.
3. Confirm registration embed shows **Signups Closed**.
4. Confirm `ArkMatches.Status = Locked`.

---

## 5) Check‑in (T‑12h)
1. Adjust match start time so now is within T‑12h.
2. Confirm Check‑in button appears.
3. Check‑in as a player.
4. Confirm checked‑in list updates.
5. Verify `ArkSignups.CheckedIn = 1`.

---

## 6) Emergency Withdraw (pre‑start only)
1. Use **Emergency — can’t attend** button.
2. Confirm player removed + auto‑promotion of earliest sub.
3. Confirm confirmation embed updates **Updates** field.
4. Verify `ArkSignups.Status = Withdrawn`.

---

## 7) **T+30m Post‑Start Refresh**
1. Set match start time = now ‑ 31 minutes.
2. Wait for scheduler cycle or force refresh.
3. Confirm:
   - Check‑in button removed
   - Emergency button removed
   - **Record Result** + **No Show** buttons appear

---

## 8) Record Result (Win/Loss)
1. Click **Record Result**.
2. **Select Win/Loss from dropdown**.
3. (Optional) add notes.
4. Confirm:
   - `ArkMatches.Status = Completed`
   - `Result`, `ResultNotes`, `CompletedAtUtc` updated
   - Confirmation embed shows **Result** section

---

## 9) No Show
1. Click **No Show** button.
2. Select a roster member who is still Active.
3. Confirm:
   - `ArkSignups.NoShow = 1`
   - `NoShowAtUtc` set
   - Confirmation embed updates **Updates** field

---

## 10) Reporting
1. Run `/ark_report_players` (public).
2. Confirm report posts in channel.
3. Use Next/Prev buttons to navigate pages.
4. Verify values:
   - Matches Played = Active & not Withdrawn & not NoShow
   - Emergency Withdraw count
   - No Show count
   - Win %

---

## 11) Cancelled Guard Checks
1. Cancel a match.
2. Attempt Record Result → **should be blocked**
3. Attempt No Show → **should be blocked**

---

## 12) Final SQL Verification
- `ArkAuditLog` contains:
  - `match_result`
  - `signup_no_show`
- `vw_ArkPlayerReport` shows expected counts.

---

✅ **If all steps pass, Phase 9 is complete and ready for final Phase 10 wrap‑up.**
