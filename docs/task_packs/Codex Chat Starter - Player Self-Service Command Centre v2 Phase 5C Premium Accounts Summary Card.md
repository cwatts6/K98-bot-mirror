# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card

Status: next approval-gated GovernorOS v2 slice. Start with the operator's ideas and visual/product
workshop. Do not implement until the approval checkpoints are confirmed.

## Copy/Paste Starter

```text
Codex, start Player Self-Service Command Centre v2 Phase 5C: Premium Accounts Summary Card.

Context:
GovernorOS v2 Phases 1-5B are complete. Phase 5B operator smoke and final visual acceptance passed
on 2026-07-13; the premium Inventory reports, honest no-data cards, restored icons, Discord avatar,
larger typography, genuine date labels, and upload markers were accepted.

The next slice is `/me accounts`. I have ideas I want to work through before implementation.
Start with review, optioneering, and a visual/product approval checkpoint. Do not assume the current
Accounts background or your first proposed composition is approved.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5C Premium Accounts Summary Card.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5B Premium Inventory Report Backdrops and Visual Alignment.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 4 Premium Governor Dashboard Renderer.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 6 Guided Management Cards and Workflow Simplification.md
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Use these skills:
- k98-architecture-scope
- k98-discord-command-feature
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review
- codex-security:security-scan

Current Accounts contract:
- private/ephemeral Discord-user and all-linked-governor summary
- current 1702x924 output and stable `me_accounts_<discord_user_id>.png` filename
- current runtime background `assets/me/cards/me accounts.png`, pending explicit Phase 5C visual approval
- main-account label/state, linked count/state, account names, and service-owned action guidance
- one guided Manage action for Governor ID lookup, add/register, replace, and remove with confirmation
- mutation revalidation and host-card refresh
- blue primary Accounts/Reminders/Preferences navigation; secondary Dashboard/Inventory/Exports
- current same-payload private embed fallback, attachment replacement, and stream cleanup

Target default format to review:
- successful premium card becomes a standalone private attachment instead of an embed-wrapped image
- retain 1702x924 and the stable filename unless I explicitly approve a different dimension
- use my Discord avatar best-effort with a safe local fallback
- keep real Discord buttons below the card; never paint fake controls into the image
- preserve genuine values and honest zero/unavailable states without dummy governors or slots

Governor rule:
Accounts is not a selected-governor page. Do not add Change Governor, including for more than 25
linked governors. Optional selected governor context may be carried only so Dashboard returns to the
same governor. Direct `/me accounts` entry has no implicit governor filter. Any governor-specific
child action must resolve its governor explicitly and recheck current access.

Before coding, provide:
- architecture/scope review
- current Accounts data/action inventory
- mapping of my ideas to existing payload fields versus any out-of-scope data needs
- 2-3 restrained visual hierarchy options or a representative prototype
- backdrop/runtime/master recommendation
- proposed desktop/mobile typography and empty/unavailable treatment
- exact component rows, standalone/fallback transition, and attachment cleanup plan
- focused test and security plan
- explicit decisions I must approve

Do not do in Phase 5C:
- no SQL, DAL query, payload/model field, account slot, ownership/claim, lookup, registry, persistence,
  command registration, redirect, visibility, permission, or guided Manage redesign unless I
  explicitly approve a separate scope expansion
- no Change Governor on Accounts
- no Reminders, Preferences, Inventory summary, Exports summary, Dashboard, direct Inventory report,
  Export Stats, History, Inspect, Last Login, Olympia, CrystalTech, website/API, or public `/kvk` change
- no broad renderer/view framework

After I approve the visual/product checkpoint, implement only the approved presentation/delivery
scope, validate at original/desktop/mobile size, run focused and repository gates, run security
review, create/update the PR, and stop for operator Discord smoke.
```
