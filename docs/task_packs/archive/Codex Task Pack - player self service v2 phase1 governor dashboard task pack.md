# Codex Task Pack - Player Self-Service Command Centre v2 Phase 1 Governor Dashboard Product Blueprint and Audit

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 1 Governor Dashboard Product Blueprint and Audit`
- Date: `2026-06-27`
- Owner/context: Chris / KD98 bot / follow-on from the completed Player Self-Service Command Centre programme and production PR #486
- Task type: `audit | product UX design | Discord command architecture | visual output specification | player workflow modernisation planning`
- One-pass approved: `no`
- Status: `prepared - not started`

## 2. Required Reading

Before implementation or design recommendations, read the current repository instructions and indexed standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`. Do not load every reference document by default unless the index or this task requires it.

Also read:

- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Conditionally read when the audit confirms these areas are involved:

- SQL repo: `C:\K98-bot-SQL-Server`
- SQL promotion/deployment guidance only if SQL changes are later proposed
- existing `/me`, stats, profile, inventory, KVK history, and export tests
- visual card/assets folders used by `/me`, `/kvk stats`, `/kvk targets`, `/kvk history`, `/kvk rankings`, and inventory cards

## 3. Objective

Create the definitive v2 blueprint for the `/me` player command centre before any implementation begins.

This phase must audit the current player self-service surface, confirm all data sources and dependencies, design the target governor-first journey, define the new dashboard card content and visual standard, and recommend the safest implementation sequence.

This phase is audit and design only. Do not implement redirects, removals, command changes, SQL changes, renderer changes, or UI behaviour changes until the operator reviews and approves the blueprint.

## 4. Background

The first Player Self-Service Command Centre programme delivered a strong foundation:

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me inventory
/me exports
```

It also delivered generated visual card surfaces, fallback embeds, SQL-backed Discord-user preferences, and approved lightweight redirects for legacy account, reminder, preference, and export paths. Phase 13 smoke testing on `2026-06-27` confirmed the approved redirects.

v2 exists because the remaining personal player paths are still fragmented and visually inconsistent with the newer premium KVK experience:

```text
/my_stats
/stats player
/player_profile
/myinventory
/mykvkcrystaltech
/kvk history
```

The goal is not to mechanically move commands. The goal is to transform `/me` into the primary daily player interface: a premium, governor-first dashboard where every personal workflow either lives, launches, or has a deliberate reason to remain separate.

The operator has supplied a new target journey:

```text
User enters /me
-> selects one of their registered governors
-> opens the governor dashboard card
-> uses focused actions for stats export, KVK/history, inventory resources, materials, speedups, accounts, reminders, and preferences
```

The operator also wants the `/me` card format fixed. Current `/me` cards are too small and compressed compared with the newer `/kvk stats`, `/kvk targets`, `/kvk history`, and `/kvk rankings` card outputs. Phase 1 must identify exactly what needs to change to make `/me` cards larger, clearer, and consistent with the latest visual design language.

A larger stats export redesign is explicitly separate and must not be folded into this programme.

## 5. Scope

### In Scope

#### A. Full `/me` current-state audit

Audit the current `/me` command group and all existing subcommands:

```text
/me dashboard
/me accounts
/me reminders
/me preferences
/me inventory
/me exports
```

For each current path, document:

- command registration shape
- owner module
- service/DAL/view dependencies
- response visibility
- permission and channel gating
- user-facing copy
- UI components, buttons, selects, modals, and callbacks
- restart/rehydration considerations
- fallback embed behaviour
- current tests and missing coverage
- usage tracking identity
- any deferred optimisation items already linked to the path

#### B. Legacy and adjacent command audit

Audit these primary legacy or adjacent player self-service paths:

```text
/my_stats
/stats player
/player_profile
/myinventory
```

Also review for product fit, but do not assume inclusion:

```text
/mykvkcrystaltech
/kvk history
```

For each path, classify whether it should be:

- preserved as-is
- preserved but improved with copy/navigation
- exposed through `/me` while preserving existing command compatibility
- redesigned into a `/me` subcommand or dashboard action
- treated as a leadership/admin workflow
- treated as a specialist workflow outside v2
- marked as a future redirect/removal candidate only after separate approval

#### C. Governor-first journey design

Design the target journey:

```text
/me
-> registered governor select
-> governor dashboard
-> governor-context-preserving actions
```

The audit/design must answer:

- What happens when the Discord user has one registered governor?
- What happens when the Discord user has multiple registered governors?
- What happens when the Discord user has no registered governors?
- How is governor context preserved across buttons and subcards?
- How does the user return to the governor selector?
- How does the user return to the dashboard from a subcard?
- What should be ephemeral/private by default?
- Are there any paths that must remain public/channel-visible?
- How should stale interactions, timeouts, missing data, or permission failures behave?

#### D. New governor dashboard content blueprint

Design the new `/me dashboard` card around a premium governor summary, using the supplied screenshot direction as the UX benchmark.
`docs/task_packs/me_dashboard_screenshot.jpg`


Target dashboard fields:

- Governor name
- VIP level, if available, displayed with the governor name
- Account type and governor ID as secondary/subscript identity detail
- Alliance name
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

For each field, document:

- whether it is currently available
- source command/view/service/table/procedure
- latest-value or historical-value semantics
- null/missing-data behaviour
- whether field naming differs between import, SQL, DAL, and output layers
- formatting convention
- whether it is safe for normal player visibility
- whether it requires SQL validation

Important naming note:

- Conduct Score may originate from file/import naming changes. Validate the latest data contract before assuming the column/table/view name.

#### E. Dashboard action model

Define the target dashboard action model.

Known operator direction:

- `Export Stats` becomes a row 3 green action button from the dashboard card.
- The separate dashboard-level `Exports` button is no longer required in the primary landing journey.
- Do not remove `/me exports` or any existing export functionality in Phase 1. Classify and recommend the compatibility strategy only.
- The `Accounts` card remains available and is Discord-user-level, not governor-specific.
- The `Reminders` card remains available and is Discord-user-level, not governor-specific.
- The `Preferences` card remains available.
- Replace the single dashboard `Inventory` button with focused buttons for `Resources`, `Materials`, and `Speedups`.
- Keep `/me inventory` because it remains useful when a player wants all three inventory cards in one post.

The blueprint must specify:

- exact proposed dashboard buttons/actions
- which actions are governor-specific
- which actions are Discord-user-specific
- button order and grouping
- button styles and priority
- back/return behaviour
- whether each action should be a subcommand, button-only action, or both
- compatibility with current `/me inventory` and `/me exports`

#### F. Inventory split and visual refresh blueprint

Audit the current inventory journey and card outputs.

Target direction:

```text
/me resources
/me materials
/me speedups
/me inventory
```

The individual `resources`, `materials`, and `speedups` outputs already have the core content needed, but they need to be reformatted to match the latest premium card style. This is a visual consistency change, not a content redesign.

Phase 1 must document:

- current `/myinventory` behaviour
- current `/me inventory` behaviour
- whether there are already separate resources/materials/speedups renderers
- whether each card can be launched directly without forcing an intermediate inventory menu
- expected privacy and channel behaviour
- any cooldown/import/data availability checks
- required tests if later implemented
- whether the split changes command count or only grouped subcommands under existing `/me`

#### G. Card size and visual standard audit

Treat card sizing and readability as a first-class workstream.

Compare current `/me` card outputs with newer KVK cards:

```text
/kvk stats
/kvk targets
/kvk history
/kvk rankings
```

Document:

- current `/me` image dimensions
- current KVK card dimensions
- renderer technology and layout constraints
- Discord preview/scaling behaviour
- font sizes, whitespace, icon scale, and readability differences
- whether `/me` cards can adopt the same dimensions or need a different standard
- what code or asset changes would be required
- risk to mobile readability
- fallback embed implications

The recommendation must produce a clear v2 visual standard for `/me` cards.

#### H. `/kvk history` product-placement decision

Review whether `/kvk history` should migrate, duplicate, or remain separate.

Operator hypothesis:

- `/kvk stats`, `/kvk targets`, and `/kvk rankings` are about the live/current KVK experience.
- `/kvk history` is a personal retrospective view and may be better served under `/me`.

Phase 1 must evaluate:

- current `/kvk history` behaviour
- whether it is purely player personal history or also public KVK workflow
- current permission/channel/privacy model
- whether a `/me history` or `/me kvk-history` entry point would improve UX
- whether existing `/kvk history` should remain for compatibility
- whether the same renderer can be reused
- whether any naming conflicts exist with generic player history/profile concepts

Do not move it in Phase 1.

#### I. Leadership/admin inspect journey

Design a separate leadership workflow to inspect another governor without overloading the normal player journey.

Possible target shape:

```text
/me inspect
```

Alternative naming to evaluate:

```text
/me leaders
/me governor
/me lookup
```

Preferred direction unless audit finds a better naming model:

```text
/me inspect
-> governor ID or fuzzy governor name lookup
-> same dashboard renderer with inspected governor context
```

Phase 1 must document:

- required permission gates
- channel restrictions
- role checks
- audit/logging requirements
- usage tracking identity
- privacy implications
- whether leader inspection can reuse the same dashboard renderer
- whether normal players can ever access lookup by governor name
- how to avoid leaking linked Discord-user/private account data
- whether the inspected view should show all fields or omit Discord-user-level settings

#### J. Missed player self-service command discovery

Search the command surface for other player self-service paths that may have been missed.

Examples to consider, but do not assume inclusion:

- player stats or profile commands
- personal KVK commands
- personal inventory/export commands
- personal reminder/preference/account commands
- personal achievement/history commands
- commands that use governor registration or Discord-user linkage
- leadership commands that look like player self-service but are actually admin workflows

Create a candidate inventory and classify each path.

#### K. Usage, compatibility, and deprecation planning

Review available command usage signals before recommending any change.

Phase 1 must produce a migration approach that preserves compatibility until a later rollout is approved.

For every command that may later be redirected, hidden, renamed, or visually redesigned, document:

- current usage level if available
- compatibility risk
- communication requirement
- whether a soft redirect is appropriate
- whether command copy should say `use /me ...` later
- whether the command should remain indefinitely as a specialist shortcut

### Out of Scope

- Runtime implementation of the new dashboard journey
- Redirecting, removing, renaming, or hiding any command
- Implementing `/me resources`, `/me materials`, `/me speedups`, or `/me inspect`
- Redesigning stats export schemas or export workbooks
- Redesigning the larger stats export programme
- SQL schema changes
- SQL deployment or promotion
- Changing public/channel-gated KVK behaviour
- Moving leadership-only behaviour into normal player flows
- Folding `/mykvkcrystaltech` into `/me` without explicit product approval
- Website or external dashboard work
- Creating new achievement/records functionality in this phase

## 6. Source Deferred Items

This task is partly motivated by deferred optimisation and product-modernisation findings around the older personal stats/profile/inventory paths.

Codex must inspect `docs/reference/deferred_optimisations.md` and identify any deferred items that relate to:

- `/my_stats`
- `/stats player`
- `/player_profile`
- `/myinventory`
- `/me dashboard`
- `/me inventory`
- `/me exports`
- KVK history/profile/history cards
- duplicated card rendering helpers
- direct SQL or business logic in command/view layers
- card sizing, output consistency, or visual renderer debt

For each relevant item found, classify it as:

```md
### Deferred Optimisation Review
- Area:
- Existing item/reference:
- Related v2 decision:
- Decision: include in v2 | defer | superseded | needs operator decision
- Reason:
```

## 7. Codex Skills To Use

| Skill | Use when |
|---|---|
| `k98-architecture-scope` | Required. Use before recommendations to map commands, views, services, DAL, SQL contracts, docs, tests, and approval checkpoints. |
| `k98-discord-command-feature` | Required. This work changes or proposes changes to slash commands, Discord views, buttons, selects, response visibility, permissions, and user-facing flows. |
| `k98-sql-validation` | Use for audit validation where dashboard fields, stats/profile data, inventory data, Conduct Score, VIP, KVK history, or export status depend on SQL contracts. Do not change SQL in Phase 1. |
| `k98-test-selection` | Required before final validation recommendations. Use it to identify focused tests for later implementation slices. |
| `k98-deferred-optimisation-capture` | Required. Capture out-of-scope debt and update structured deferred items only if documentation updates are approved in this audit slice. |
| `k98-pr-review` | Required before handoff if any docs are modified. Use for architecture, scope, command governance, SQL alignment, and validation review. |
| `k98-promotion-check` | Not expected for audit-only docs. Required later before production promotion or SQL deployment. |
| `codex-security:security-scan` | Required or explicitly documented as skipped. Use if the branch changes permission-sensitive docs, command behaviour, lookup flows, SQL/data access, or privacy guidance. |

### Skill Decisions

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | `use` | Required to avoid accidental command, SQL, or architecture drift. |
| `k98-discord-command-feature` | `use` | Required because the target model affects slash commands, buttons, selects, permissions, and response visibility. |
| `k98-sql-validation` | `use conditionally` | Use to validate field availability and SQL/data contracts; no SQL changes in Phase 1. |
| `k98-test-selection` | `use` | Required to recommend the correct Phase 2+ test strategy. |
| `k98-deferred-optimisation-capture` | `use` | Required to classify old stats/profile/inventory debt. |
| `k98-pr-review` | `use` | Required before PR handoff if docs are changed. |
| `k98-promotion-check` | `not applicable` | No production promotion in audit-only Phase 1. |
| `codex-security:security-scan` | `use or document skip` | Required if any security/privacy/permission-sensitive behaviour is specified or docs are materially changed. |

## 8. Mandatory Workflow

Default workflow for this task:

1. Read required docs and run architecture scope review.
2. Audit the current command surface and dependencies.
3. Audit data sources and SQL-backed contracts where needed.
4. Produce current-state maps and classification tables.
5. Produce the target product blueprint.
6. Produce the recommended implementation sequence.
7. Stop for operator approval.

Do not proceed into implementation without explicit approval.

If Codex believes a small documentation update is needed to capture the Phase 1 audit output, make that explicit in the plan and preserve the audit-only constraint. Runtime bot behaviour must not change in this task.

## 9. Audit Requirements

Review the touched area for:

- direct SQL in commands or views
- business logic in interaction layers
- duplicate renderers or near-duplicate card helpers
- weak validation or logging
- cache and persistence safety
- restart safety
- privacy and response visibility risks
- role/channel permission boundary risks
- missing usage tracking
- output/card readability issues
- fallback embed consistency
- test coverage gaps
- stale command references or docs
- deferred optimisation alignment

Map the likely:

- commands
- grouped subcommands
- decorators
- usage-tracking keys
- services
- repositories / DAL modules
- SQL objects or contracts
- views, modals, buttons, selects, and callbacks
- generated card renderers and assets
- caches or persisted state
- tests
- documentation

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | `commands/<domain>_cmds.py` or existing `/me` command module |
| Views / modals | `ui/views/` or existing player self-service view modules |
| Services / business logic | subsystem package or `<domain>_service.py` |
| Repository / DAL | subsystem package or repository/DAL module |
| Shared card rendering helpers | existing card renderer modules or a clearly named shared visual helper module |
| Shared helpers | `core/` or existing helper modules |
| Documentation | `docs/`, `docs/reference/`, `docs/task_packs/` |
| SQL schema | SQL repo `sql_schema/<schema>.<Object>.<Type>.sql` when validation is needed |
| Tests | `tests/` |

Implementation direction for later phases:

- Keep commands and views thin.
- Put governor dashboard orchestration in a service.
- Put SQL/data lookup behind existing repositories/DAL, not command callbacks.
- Reuse the same dashboard renderer for normal player and leadership inspect where safe.
- Keep Discord-user-level cards separate from governor-specific cards.
- Preserve backward-compatible command paths unless a later rollout explicitly approves redirects or removals.

## 11. Likely Files

Codex must locate the actual files before making conclusions. Start with search rather than assuming exact names.

### Review

- `commands/*me*.py`
- `commands/*stats*.py`
- `commands/*profile*.py`
- `commands/*inventory*.py`
- `commands/*kvk*.py`
- `ui/views/*me*.py`
- `ui/views/*profile*.py`
- `ui/views/*inventory*.py`
- `ui/views/*stats*.py`
- `ui/views/*kvk*.py`
- `services/**/*stats*`
- `services/**/*profile*`
- `services/**/*inventory*`
- `services/**/*player*`
- `services/**/*kvk*history*`
- `core/**/*card*`
- `core/**/*render*`
- `assets/**/*me*`
- `assets/**/*inventory*`
- `assets/**/*kvk*`
- `tests/**/*me*`
- `tests/**/*stats*`
- `tests/**/*profile*`
- `tests/**/*inventory*`
- `tests/**/*kvk*history*`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- `docs/player_self_service_command_centre_briefing.md`

### SQL repo review if field/data contracts require validation

- latest player stats/profile views and procedures
- KVK history views/procedures
- inventory tables/views/procedures
- governor registry/profile tables
- Conduct Score / Conduct / Credit import/output contracts
- VIP data contracts
- Olympia, Ark, and Autarch data contracts

### Modify

For Phase 1, only modify documentation if approved by the audit plan. Likely docs:

- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- a new or updated Phase 1 audit/design report
- `docs/reference/deferred_optimisations.md` only if new structured items are confirmed
- `docs/reference/canonical_command_reference.md` only if documentation needs to reflect approved design intent; do not document unimplemented commands as live commands

### Create

Likely output document:

- `docs/task_packs/Player Self-Service Command Centre v2 Phase 1 Governor Dashboard Product Blueprint and Audit Report.md`

Do not create runtime modules in Phase 1.

## 12. Implementation Requirements

Phase 1 is audit/design only.

- Do not change runtime command behaviour.
- Do not alter command registration.
- Do not alter SQL.
- Do not alter renderer code.
- Do not alter permissions.
- Do not remove any existing command.
- Do not redirect any existing command.
- Do not add new subcommands yet.

The Phase 1 output must include enough detail to support later implementation without re-discovering the same information.

### Command Surface Governance

This task does not implement command changes, but it must plan them carefully.

- [ ] State whether the recommended later implementation changes top-level command count, grouped subcommand count, or neither.
- [ ] Prefer grouped subcommands under existing `/me` rather than creating new top-level commands.
- [ ] Identify proposed grouped subcommands, likely including `/me resources`, `/me materials`, `/me speedups`, and a leadership lookup path such as `/me inspect`, subject to operator approval.
- [ ] Do not mark proposed commands as live in the canonical command reference until implemented.
- [ ] Preserve or explicitly plan updates to `@versioned()`, `@safe_command`, `@track_usage()`, permission decorators, response visibility, autocomplete/options, usage-log identity, and command-cache behaviour.
- [ ] Plan validation for `scripts/validate_command_registration.py`, `tests/test_validate_command_registration.py`, `tests/test_command_inventory.py`, and `tests/test_command_registration_smoke.py` for later implementation phases.

## 13. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| Business logic in command/view layers | `fix later | defer | not applicable` | Decide based on implementation risk and v2 sequencing. |
| Direct SQL in command/view layers | `fix later | defer | not applicable` | Do not fix in Phase 1 unless docs-only; capture if found. |
| Duplicate renderers/card helpers | `fix later | defer | not applicable` | Important for card sizing and visual consistency. |
| Missing tests | `fix later | defer | not applicable` | Include in implementation phase plan. |
| Privacy/permission ambiguity | `operator decision | fix later | not applicable` | Do not implement until the desired boundary is approved. |

Deferred items must use the structured format from `docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 14. Testing Requirements

Phase 1 is audit/design only. If only documentation changes are made, run or justify:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

For later implementation phases, the Phase 1 report must recommend focused tests for:

- happy path
- no registered governor
- one registered governor
- multiple registered governors
- governor selector behaviour
- dashboard rendering
- missing/null data fields
- permission boundary
- channel boundary
- leadership inspect access
- fuzzy lookup ambiguity
- privacy/data leakage prevention
- response visibility
- button/select callbacks
- stale interaction/timeouts
- fallback embeds
- card image dimensions
- `/me resources`, `/me materials`, `/me speedups`, `/me inventory`
- `/my_stats`, `/stats player`, `/player_profile`, `/myinventory` compatibility
- `/kvk history` compatibility if a `/me` entry point is later added

Before PR handoff, include the AI-assisted review gate decision:

- Codex Security review when security-sensitive surfaces are touched, or a documented skip reason.

## 15. Acceptance Criteria

- [ ] Current `/me` command group behaviour is fully documented.
- [ ] `/my_stats`, `/stats player`, `/player_profile`, `/myinventory`, `/mykvkcrystaltech`, and `/kvk history` are audited and classified.
- [ ] The report includes a complete governor-first target journey.
- [ ] The report includes a dashboard field-to-source matrix for all proposed dashboard fields.
- [ ] The report identifies which fields are currently unavailable, ambiguous, or require SQL validation.
- [ ] The report defines the target dashboard actions and distinguishes governor-specific from Discord-user-specific actions.
- [ ] The report defines the inventory split plan and compatibility approach for `/me inventory` and `/myinventory`.
- [ ] The report includes a card sizing and visual standard recommendation based on comparison with the newer KVK cards.
- [ ] The report makes a clear recommendation on `/kvk history` product placement.
- [ ] The report designs the leadership/admin inspect journey and its permission/privacy boundaries.
- [ ] The report identifies any missed player self-service commands or confirms none were found.
- [ ] Recommendations are backed by current behaviour review and available usage evidence.
- [ ] No command is removed, redirected, renamed, hidden, redesigned, or newly implemented in Phase 1.
- [ ] No SQL schema, procedure, view, or export contract is changed in Phase 1.
- [ ] Deferred optimisation items are captured structurally where confirmed.
- [ ] Validation commands are run or clearly justified if skipped.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. Current `/me` Command Map
4. Legacy and Adjacent Command Audit
5. Candidate Command Classification Table
6. Governor-First Journey Blueprint
7. Dashboard Field-to-Source Matrix
8. Dashboard Action Model
9. Inventory Split Blueprint
10. Card Size and Visual Standard Recommendation
11. `/kvk history` Product Placement Recommendation
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

For documentation-only work, state that no runtime code, SQL, helper reuse, or restart behaviour changed.

## 17. Suggested Implementation Phase Plan To Validate

Phase 1 should recommend and refine this sequence:

```text
Phase 1 - Governor Dashboard Product Blueprint and Audit
Phase 2 - Governor Selector and Dashboard Data Service Foundation
Phase 3 - New Premium Dashboard Card Renderer and Visual Standard
Phase 4 - Inventory Direct Actions: Resources, Materials, Speedups, Combined Inventory
Phase 5 - Legacy Stats/Profile Consolidation into Dashboard and /me Entry Points
Phase 6 - Leadership Inspect Journey
Phase 7 - KVK History Placement and Compatibility Entry Point
Phase 8 - Compatibility Redirects, Copy Updates, Docs, and Player Comms
```

Do not implement these phases in Phase 1.

## 18. PR Summary Template

```md
## Summary

- Completed Player Self-Service Command Centre v2 Phase 1 audit/design for the governor-first `/me` dashboard vision.
- Documented current command behaviour, data dependencies, visual constraints, candidate classifications, and recommended implementation sequence.

## Changes

- Added/updated the Phase 1 audit/design report.
- Captured deferred optimisation findings where confirmed.
- No runtime command, SQL, renderer, permission, or export behaviour changed.

## Tests

- <validation command or documented skip>

## AI Review Gates

- Codex Security: <run | skipped, with reason>

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Documentation-only. Rollback by reverting the docs commit.
```
