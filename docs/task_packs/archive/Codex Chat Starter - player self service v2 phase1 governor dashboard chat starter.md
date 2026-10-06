# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 1 Governor Dashboard Product Blueprint and Audit

Status: active starter for the first Player Self-Service Command Centre v2 slice.

Use this starter to begin v2 in the most logical place: the governor-first `/me` dashboard blueprint and audit. This is audit/design only. Do not implement command, SQL, renderer, redirect, or permission changes until the operator approves the Phase 1 findings and recommended rollout plan.

## Copy/Paste Starter

```text
Codex, start Player Self-Service Command Centre v2 Phase 1: Governor Dashboard Product Blueprint and Audit.

Context:
The first Player Self-Service Command Centre programme is complete. Production PR #486 delivered the Phase 13 legacy redirects, and smoke testing on 2026-06-27 confirmed all approved redirects are correct. The foundation is strong, but v2 needs to go much further.

The goal of v2 is not to mechanically move old commands. The goal is to transform /me into the primary daily player interface: a premium, governor-first command centre where every personal workflow either lives, launches, or has a deliberate reason to remain separate.

Phase 1 objective:
Create the definitive product and technical blueprint before implementation. Audit current behaviour, data sources, command ownership, visual card constraints, permissions, usage evidence, and migration risk. Recommend the safest phased implementation plan. Stop before runtime changes.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md

Then follow the required reading order and conditional references defined by docs/reference/README.md.

Also read:
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- docs/task_packs/Codex Task Pack - player self service v2 phase1 governor dashboard task pack.md
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Use these skills:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation where SQL/data contracts need validation
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff if docs are changed
- codex-security:security-scan if permission, privacy, lookup, or data-access guidance is materially changed; otherwise document the skip reason

Primary design direction:
/me should become governor-first.

Target journey:
/me
-> user selects one of their registered governors
-> the selected governor dashboard opens
-> every governor-specific button preserves governor context until the user backs out or changes governor

New dashboard card target:
- Governor Name, with VIP Level if available
- account type and governor ID as secondary/subscript detail
- Alliance Name
- Power
- Kill Points
- Highest Acclaim
- Deads
- Helps
- Healed
- Olympia Fights plus win ratio
- Ark of Osiris plus win ratio
- Autarch count / times named Autarch
- Conduct Score
- Civilisation

Important UX direction:
- Current /me cards are too small and compressed.
- Compare them with /kvk stats, /kvk targets, /kvk history, and /kvk rankings cards.
- Identify what needs to change so /me cards use the same premium, larger, more readable visual standard.
- Treat card size/readability as a first-class workstream, not a minor styling tweak.

Dashboard action direction:
- Export Stats becomes a row 3 green action button on the dashboard card.
- The separate dashboard-level Exports button is no longer required in the primary journey, but do not remove /me exports or any existing export functionality in Phase 1.
- Accounts remains available and is Discord-user-level, not governor-specific.
- Reminders remains available and is Discord-user-level, not governor-specific.
- Preferences remains available.
- Replace the single Inventory dashboard button with direct buttons for Resources, Materials, and Speedups.
- Keep /me inventory because it remains useful when a player wants all three inventory cards in one post.

Inventory target to audit and design:
/me resources
/me materials
/me speedups
/me inventory

The individual resources/materials/speedups cards already contain the core information needed. The later work should mainly refresh the visual format so they match the latest premium card style. Do not redesign their content in Phase 1.

Primary paths to audit:
- current /me command group and subcommands
- /my_stats
- /stats player
- /player_profile
- /myinventory

Also review for product fit, but do not assume inclusion:
- /mykvkcrystaltech
- /kvk history

Specific /kvk history question:
All other /kvk commands are mostly about the live/current KVK experience. /kvk history is a look-back at the player’s personal history, so it may belong under /me. Audit current behaviour and recommend whether it should remain under /kvk only, gain a /me entry point, or eventually migrate while preserving compatibility.

Leadership/admin journey to design:
/me also needs a gated leadership ability to inspect another governor by governor ID or fuzzy governor name lookup. Do not mix this into the normal player journey.

Evaluate naming, with /me inspect as the preferred starting point unless the audit finds a better option:
/me inspect
-> governor ID or fuzzy governor name lookup
-> same governor dashboard renderer, but with leadership permissions and no leakage of Discord-user private account data

Audit requirements:
1. Audit command registration, owner module, decorators, permissions, response visibility, options, usage tracking, views/buttons/selects/modals, services, DAL/repositories, SQL-backed contracts, tests, and user-facing copy.
2. Create a dashboard field-to-source matrix for every proposed dashboard metric.
3. Validate ambiguous data contracts against the SQL repo where needed, especially Conduct Score, VIP, Olympia, Ark, Autarch, Civilisation, stats/profile/latest values, and KVK history.
4. Review available command usage signals before recommending redirects, removals, or compatibility changes.
5. Search for any missed player self-service commands that should be considered for /me v2.
6. Classify each candidate path as preserve as-is, preserve with copy/navigation improvements, add /me entry point while keeping existing command, redesign candidate, leadership/admin workflow, specialist workflow outside v2, or future redirect/removal candidate only after separate approval.
7. Produce a phased implementation plan and stop.

Explicit non-goals for Phase 1:
- Do not implement the new dashboard journey.
- Do not add /me resources, /me materials, /me speedups, or /me inspect yet.
- Do not redirect, remove, rename, or hide /my_stats, /stats player, /player_profile, /myinventory, /mykvkcrystaltech, or /kvk history.
- Do not change SQL schema, stored procedures, views, export schemas, or renderer code.
- Do not fold CrystalTech into /me without a product decision.
- Do not redesign the larger stats export programme. That is a separate future workstream.

Suggested validation for audit/design scope:
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py

Required delivery output:
1. Summary
2. File Manifest
3. Current /me Command Map
4. Legacy and Adjacent Command Audit
5. Candidate Command Classification Table
6. Governor-First Journey Blueprint
7. Dashboard Field-to-Source Matrix
8. Dashboard Action Model
9. Inventory Split Blueprint
10. Card Size and Visual Standard Recommendation
11. /kvk history Product Placement Recommendation
12. Leadership/Admin Inspect Journey Recommendation
13. Missed Player Self-Service Command Discovery
14. SQL/Data Contract Findings
15. Privacy, Permission, and Channel-Gating Findings
16. Usage Evidence and Compatibility Risks
17. Implementation Phase Plan
18. Refactor Findings
19. Test Plan
20. AI Review Gates
21. Deployment / Rollout Notes for Later Phases
22. Deferred Optimisations

Acceptance criteria:
- Every candidate path is audited and classified.
- The governor-first /me journey is fully specified.
- The dashboard field-to-source matrix is complete.
- The card sizing/visual standard recommendation explains how to achieve the larger, clearer KVK-style card format.
- Inventory direct actions are designed without losing /me inventory compatibility.
- /kvk history placement is explicitly recommended.
- Leadership inspect is designed as a gated workflow and does not leak Discord-user-level private data.
- No runtime behaviour changes are made in this Phase 1 audit/design slice.
```
