# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 1 Stats Profile Inventory Audit and Design

Status: active starter for the next Player Self-Service Command Centre v2 slice.

The first Player Self-Service Command Centre programme is complete. Production PR #486 delivered
Phase 13 legacy redirects, and smoke testing on 2026-06-27 confirmed all approved redirects are
correct.

Use this starter to begin v2 with audit/scope only.

## Copy/Paste Starter

```text
Codex, start Player Self-Service Command Centre v2 Phase 1: Stats, Profile, and Inventory Audit
and Design.

The first Player Self-Service Command Centre programme is complete. Production PR #486 delivered
the Phase 13 legacy redirects, and smoke testing on 2026-06-27 confirmed all approved redirects
are correct. The remaining larger paths were intentionally preserved rather than redirected or
redesigned in Phase 13.

Phase 1 objective:
Audit the remaining player self-service-aligned paths and recommend the safest v2 scope.

Start with audit/scope only. Do not redirect, deprecate, remove, or redesign commands until I
explicitly approve the rollout after reviewing your classifications and recommendations.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/reference/K98 Bot - Project Engineering Standards.md
- docs/reference/K98 Bot - Coding Execution Guidelines.md
- docs/reference/K98 Bot - Testing Standards.md
- docs/reference/K98 Bot - Skills & Refactor Triggers.md
- docs/reference/K98 Bot - Deferred Optimisation Framework.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 1 Stats Profile Inventory Audit and Design.md
- docs/player_self_service_command_centre_briefing.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- codex-security security review or documented skip before PR handoff if Discord command behavior changes

Audit these primary paths:
- /my_stats
- /stats player
- /player_profile
- /myinventory

Also review for product fit, but do not assume inclusion:
- /mykvkcrystaltech

Scope:
1. Audit current behavior, owner module, service/DAL/view dependencies, permission model,
   visibility, command registration, options, usage tracking identity, and user-facing copy.
2. Review available command usage signals before recommending any grouping, redesign, redirect, or
   removal.
3. Classify each path as preserve as-is, preserve but improve copy/navigation, add /me or grouped
   entry point while keeping existing command, redesign candidate, leadership/admin workflow, or
   specialist workflow outside v2.
4. Preserve compatibility unless I explicitly approve a rollout change.
5. Do not redesign stats cards, inventory report cards, profile embeds, export schemas, SQL
   contracts, public KVK behavior, or CrystalTech in this audit slice.
6. Update docs, canonical command reference, deferred backlog, and tests only for the approved
   audit/design or implementation slice.

Suggested validation for audit-only scope:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py

Acceptance criteria:
- Every candidate path has documented classification and rationale.
- Recommendations are backed by behavior review and available usage evidence.
- No command is removed, redirected, or redesigned without explicit approval.
- Leadership/admin and specialist workflows are not accidentally folded into player-only /me flows.
- Docs and deferred backlog are updated to match the approved plan.
```
