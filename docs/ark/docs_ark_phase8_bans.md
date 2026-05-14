# Phase 8 — Bans with “Next N Ark Weekends” Expiry

## Overview
Phase 8 adds enforceable Ark bans with deterministic weekend-window coverage and revoke support.

## Status
✅ Implemented and locally validated

## Scope Delivered

### 1) Ban model
- Ban target can be:
  - Discord user (`DiscordUserId`)
  - Governor (`GovernorId`)
  - or both
- Ban includes:
  - `BannedArkWeekends` (N)
  - `StartArkWeekendDate`
  - `Reason`
  - created/revoked metadata

### 2) Start policy (anchor resolution)
- Ban begins at the **next Ark weekend on/after now UTC** using configured Ark cadence.

### 3) Expiry + revoke
- Natural expiry after covered weekends.
- Explicit revoke supported.
- Effective enforcement rule: block if **any active, non-revoked row applies**.

### 4) Enforcement points
- Self signup flow checks active ban before add/reactivate.
- Admin add flow checks active ban before add/reactivate.
- `AdminOverrideBanRule` config flag allows emergency bypass (default `0` / OFF).

### 5) Commands
- `/ark_ban_add`
- `/ark_ban_revoke`
- `/ark_ban_list`

### 6) Messages
- Self block:
  - “❌ You cannot sign up for this Ark weekend because this account is currently banned. If you believe this is incorrect, contact leadership.”
- Admin block:
  - “❌ Cannot add this governor: an active Ark ban applies for this weekend.”
- Admin override warning:
  - “⚠️ Ban override is enabled. Proceeding with admin add despite active ban.”

### 7) Audit + structured logging
- Audit event:
  - `ban_block_signup` for enforcement blocks
  - `ban_add`, `ban_revoke` for admin actions
- Structured logger fields include:
  - `match_id`, `alliance`, `ark_weekend_date`
  - `discord_user_id` / `actor_discord_id`
  - `governor_id`, `ban_id`, `source`

---

## SQL / Config Notes
- `ArkBans` used as canonical ban source.
- `ArkConfig` includes `AdminOverrideBanRule` (bit, default 0).

---

## Tests
- Added pytest coverage for:
  - ban window helpers
  - admin add enforcement with override OFF/ON
  - command-level wiring smoke checks
- Existing Ark tests still pass after integration.
