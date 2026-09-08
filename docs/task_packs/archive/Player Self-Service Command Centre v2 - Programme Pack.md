# Player Self-Service Command Centre v2 - Programme Pack

## 1. Programme Header

- Programme name: `Player Self-Service Command Centre v2`
- Date: `2026-06-27`
- Owner/context: Follow-on player self-service modernisation after the original Player Self-Service Command Centre programme completed in production PR #486
- Programme type: Audit and design first; Discord command architecture; player stats/profile/inventory workflow alignment
- One-pass approved: No
- Headline: **Finish the remaining player self-service paths without breaking the valuable specialist journeys.**

## 2. Current Status

The first Player Self-Service Command Centre programme is complete and archived. It delivered:

- `/me dashboard`
- `/me accounts`
- `/me reminders`
- `/me preferences`
- `/me inventory`
- `/me exports`
- generated visual card surfaces and fallback embeds
- SQL-backed Discord-user profile preferences
- approved lightweight redirects for legacy account, reminder, preference, and export entry points

Phase 13 smoke testing on 2026-06-27 confirmed all approved redirects are correct.

v2 exists because several larger personal or leadership-adjacent paths were intentionally preserved
instead of squeezed into the first programme:

- `/my_stats`
- `/stats player`
- `/player_profile`
- `/myinventory`
- `/mykvkcrystaltech`

## 3. v2 Objective

Audit and design the remaining player self-service-aligned command paths, then decide which should
stay flat, gain `/me` or grouped entry points, be visually modernised, or remain specialist flows.

The first v2 slice must not implement redirects, removals, or redesigns. It should produce a
classification, risk review, and proposed implementation sequence.

## 4. Candidate Paths

Primary v2 candidates:

```text
/my_stats
/stats player
/player_profile
/myinventory
```

Related path to review for product fit, not automatic inclusion:

```text
/mykvkcrystaltech
```

Modern surfaces to preserve and use as context:

```text
/me dashboard
/me inventory
/me exports
/kvk stats
/kvk targets
/kvk history
/kvk rankings
```

## 5. Initial Design Questions

- Should `/my_stats` remain a channel-gated personal stats command, or should `/me` gain a stats
  entry point that respects the same channel/privacy rules?
- Should `/stats player` and `/player_profile` stay leadership/admin tools, merge conceptually,
  or gain a clearer grouped command model?
- Should `/myinventory` remain the detailed report command behind `/me inventory` Open Report, or
  should the detailed report journey gain a grouped `/me` path while preserving existing behavior?
- Does `/mykvkcrystaltech` belong in any self-service command group, or should it remain a
  channel-gated specialist workflow?
- Which visual cards, selectors, and exports are already good enough to preserve?
- Which code paths contain business logic in commands/views that should be extracted before UX
  changes?

## 6. Out Of Scope Until Approved

- Redirecting or removing `/my_stats`, `/stats player`, `/player_profile`, `/myinventory`, or
  `/mykvkcrystaltech`
- Redesigning stats or inventory export schemas
- Changing public/channel-gated KVK command behavior
- Moving leadership-only behavior into player-only `/me` flows without explicit approval
- Folding CrystalTech into `/me` without a product decision
- SQL schema changes
- Website or external dashboard work

## 7. Validation Strategy

Every v2 implementation slice should consider:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
```

For implementation work, add focused tests for touched command/service/view paths and run the full
suite when command registration, shared stats/profile services, or report rendering behavior
changes.

## 8. Phase 1

Next active task:

```text
Player Self-Service Command Centre v2 Phase 1 Stats, Profile, and Inventory Audit and Design
```

Phase 1 should audit behavior, ownership, permissions, response visibility, command usage signals,
tests, service/DAL boundaries, visual output contracts, and player/operator communication risks.
It should stop at recommendations unless the operator explicitly approves an implementation slice.
