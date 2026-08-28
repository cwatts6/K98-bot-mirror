# Codex Task Pack - Player Self-Service Command Centre v2 Phase 2 Governor Context and Dashboard Data Foundation

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 2 Governor Context and Dashboard Data Foundation`
- Date: `2026-07-09`
- Completed: `2026-07-10`
- Owner/context: Follow-on from Phase 1 Governor Dashboard Product Blueprint and Audit. Operator direction: go big and bold for the player dashboard, but ignore Olympia data because it is not currently in the source system.
- Task type: `feature foundation | service/DAL implementation | Discord command architecture preparation | SQL-backed data contract`
- One-pass approved: `No`
- Status: `complete - delivered, reviewed, smoke tested, and regression validated`

## Completion Record

Phase 2 delivered the renderer-independent governor dashboard foundation without changing the
visible `/me` journey or any legacy command behavior.

Delivered:

- Typed governor dashboard context, resolution, payload, and field-group models.
- Linked-governor option resolution for no, one, and multiple account states.
- Default-deny self-view access for unlinked governors.
- Explicit opt-in gating for any future unlinked inspect context.
- Dashboard DAL/service assembly for the approved Phase 2 fields.
- Separate self-view-only and future inspect-safe payload data.
- Null-safe handling for missing values, missing VIP, and zero Ark joined.
- Accurate `Conduct` to Conduct Score and `Civilization` to Civilisation mapping.
- Complete exclusion of Olympia fields.
- Focused access, payload, data-mapping, failure-degradation, and command-compatibility tests.

Review hardening added DAL failure degradation, large integer/decimal preservation, safe inspect
defaults, and removal of unrelated hard-coded command-count assertions from the Phase 2 tests.

Validation evidence:

- Operator smoke testing confirmed all existing `/me` and named legacy commands remain working.
- Full regression pytest completed successfully (`2414 passed, 2 skipped`).
- Architecture, deferred-item, test-selection, smoke-import, command-registration, and pre-commit
  validation passed.
- Security review completed for the access/data/privacy surface.

PR records:

- Mirror PR: `K98-bot-mirror#216`
- Production PR: `K98-bot#523`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`.

Required programme/task context:

- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/task_packs/Player Self-Service Command Centre v2 Phase 1 Governor Dashboard Product Blueprint and Audit Report.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
Example UX for reference only:
- `docs/task_packs/me_dashboard_screenshot.jpg`

For SQL-facing work, validate schema, procedure, view, index, and contract details against:

```text
C:\K98-bot-SQL-Server
```

Likely SQL-backed objects to validate before coding against them:

- `dbo.v_PlayerLatestStats`
- `dbo.v_PlayerProfile`
- `dbo.ALL_STATS_FOR_DASHBOARD`
- `dbo.v_EXCEL_FOR_KVK_All`
- `dbo.v_EXCEL_FOR_KVK_Started`
- `dbo.GovernorInventoryProfile`

## 3. Objective

Build the safe governor-context and dashboard-data foundation needed for the new premium `/me dashboard` experience.

This phase should make the future bold dashboard possible without yet replacing the visible `/me` card, changing player navigation, redirecting legacy commands, or adding the final PNG renderer.

The output should be a tested service/DAL foundation that can answer: who is the selected governor, is the invoking user allowed to view it, what dashboard data is available, what is missing, and how should self-view differ from future leadership inspect mode.

## 4. Background

Phase 1 confirmed that `/me` should become a governor-first daily command centre. The current `/me` implementation is useful but Discord-user setup-oriented rather than governor dashboard-oriented.

Phase 1 also confirmed that the safest rollout is staged:

1. Build governor dashboard data service and access checks.
2. Add selector and dashboard shell.
3. Add premium renderer.
4. Add direct inventory actions, export stats, history, and inspect flows later.

Operator direction after Phase 1:

- Keep the design ambition high.
- Make this a point of difference for KD98.
- Ignore Olympia data for now because it does not exist in the current source system.

## 5. Scope

### In Scope

- Add or extend service/DAL code to support a future governor-first dashboard payload.
- Create a clear governor dashboard context model for self-service mode and future inspect mode.
- Resolve linked governors for an invoking Discord user using existing account/registry mechanisms.
- Validate that a requested governor belongs to the invoking Discord user for normal self-service mode.
- Provide one/no/multiple governor decision helpers for the future selector journey.
- Build a dashboard payload for a selected governor using validated existing sources.
- Include null-safe formatting or raw values needed by the future renderer.
- Separate self-view-only fields from inspection-safe fields.
- Exclude Olympia fields entirely from the initial payload and tests.
- Add tests for access, payload assembly, missing data, source field names, and no command-surface changes.
- Update docs/deferred items only where Phase 2 confirms implementation details or new debt.

### Out of Scope

- Do not change the visible `/me dashboard` user journey.
- Do not add the governor selector UI yet.
- Do not build the final premium PNG dashboard renderer.
- Do not add `/me resources`, `/me materials`, `/me speedups`, `/me history`, or `/me inspect` commands yet.
- Do not redirect, remove, or alter `/my_stats`, `/myinventory`, `/stats player`, `/player_profile`, `/mykvkcrystaltech`, or `/kvk history`.
- Do not change inventory report output, export schemas, or stats export semantics.
- Do not include Olympia fights or Olympia win ratio.
- Do not make SQL schema changes unless a blocking issue is discovered and explicitly approved.
- Do not expose leadership inspect behavior to users in this phase.

## 6. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | `use` | Required before implementation because this creates a shared service/DAL foundation. |
| `k98-discord-command-feature` | `use` | Even without visible command changes, the foundation supports Discord command/view behavior and must preserve command governance. |
| `k98-sql-validation` | `use` | Dashboard payload depends on SQL-backed views/aggregate contracts. Validate against SQL repo. |
| `k98-test-selection` | `use` | Required to select focused service/DAL/access tests and command registration checks. |
| `k98-deferred-optimisation-capture` | `use` | Capture discovered dashboard/source/legacy overlap debt structurally. |
| `k98-pr-review` | `use` | Required before PR handoff. |
| `k98-promotion-check` | `not applicable for initial dev` | Use only before production promotion. |
| `codex-security:security-scan` | `use` | This touches access checks, SQL/data access, and privacy-sensitive governor context. |

## 7. Mandatory Workflow

1. Run architecture/scope review first.
2. Confirm likely modules, SQL contracts, and tests before implementation.
3. Implement the service/DAL foundation only after the scope is clear.
4. Keep command behavior and visible Discord UI unchanged unless an unexpected minimal wiring change is explicitly justified.
5. Run focused tests and command registration validation.
6. Run Codex Security review because access checks and SQL/data access are in scope.
7. Produce delivery output using the required shape.

## 8. Audit Requirements

Review the touched area for:

- direct SQL in commands or views
- duplicated governor/account resolution logic
- duplicated stats/profile data mapping
- mixed Discord-user versus governor-specific data
- business logic in views
- missing null guards
- missing access checks
- privacy risks in future inspect mode
- command registration side effects
- test coverage gaps

Map the likely:

- commands that depend on this foundation later
- services and repositories/DAL modules
- SQL objects or contracts
- player self-service views that will consume the foundation later
- renderer inputs for the premium dashboard
- caches or persisted state, if any
- restart implications

## 9. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | No visible slash command changes in Phase 2. Existing `commands/me_cmds.py` should remain behavior-compatible. |
| Views / modals | No selector/renderer view implementation yet, unless tiny non-visible compatibility adjustments are unavoidable. |
| Services / business logic | `player_self_service/` service module(s), preferably a dedicated governor dashboard/context service. |
| Repository / DAL | Existing DAL/repository patterns; new dashboard DAL only if existing services cannot provide clean contracts. |
| Shared helpers | Reuse existing formatters/helpers where practical; avoid premature visual primitive extraction. |
| Documentation | `docs/task_packs/`, `docs/reference/deferred_optimisations.md` only where needed. |
| SQL schema | No schema changes expected. Validate source fields against SQL repo. |
| Tests | Focused unit tests for service/DAL/access/payload behavior plus command registration validation. |

## 10. Likely Files

### Review

- `commands/me_cmds.py`
- `ui/views/player_self_service_views.py`
- `player_self_service/service.py`
- `player_self_service/page_cards.py`
- `player_self_service/dashboard_card.py`
- `inventory/profile_service.py`
- `inventory/reporting_service.py`
- `inventory/dal/inventory_reporting_dal.py`
- `stats_service.py`
- `commands/stats_cmds.py`
- `services/profile_lookup_service.py`
- `embed_player_profile.py`
- `services/kvk_history_service.py`
- `kvk/dal/kvk_history_dal.py`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/task_packs/Player Self-Service Command Centre v2 Phase 1 Governor Dashboard Product Blueprint and Audit Report.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

### Modify

Likely, subject to architecture review:

- `player_self_service/service.py`
- new or existing `player_self_service/*dashboard*service*.py`
- new or existing `player_self_service/*dashboard*dal*.py`
- focused tests under `tests/`
- relevant docs/deferred files if new findings are confirmed

### Create

Likely, subject to architecture review:

- `player_self_service/governor_dashboard_service.py`
- `player_self_service/governor_dashboard_models.py`
- `player_self_service/governor_dashboard_dal.py`
- `tests/test_governor_dashboard_service.py`
- `tests/test_governor_dashboard_access.py`

Use existing naming conventions if the repository has a clearer pattern.

## 11. Implementation Requirements

### 11.1 Governor context model

Create a typed model or dataclass-style contract for selected governor context.

Suggested fields:

```text
viewer_discord_id
viewer_mode: self | inspect
selected_governor_id
selected_governor_name
is_linked_to_viewer
account_type_for_self_view
access_allowed
access_reason
privacy_profile
```

Normal self-service mode must only allow governors linked to the invoking Discord user.

Future inspect mode can be represented as a model/mode, but must not become user-facing in this phase.

### 11.2 Linked governor resolution

Provide service helpers to support future selector behavior:

```text
get_dashboard_governor_options(discord_user_id)
resolve_default_dashboard_governor(discord_user_id)
resolve_dashboard_context(discord_user_id, governor_id=None, viewer_mode='self')
assert_dashboard_governor_access(discord_user_id, governor_id)
```

Expected future journey decisions:

| State | Service result |
|---|---|
| No governors | `requires_setup` / empty options with Accounts as next action |
| One governor | direct selected context |
| Multiple governors | options list and no automatic final selection unless existing main/default account rules require it |
| Requested governor not linked | denied result or clear exception handled by caller |

### 11.3 Dashboard payload service

Provide a service method to assemble the future dashboard payload:

```text
build_governor_dashboard_payload(context)
```

The payload should separate:

```text
identity
latest_metrics
historical_highlights
activity_honours
profile_status
freshness
available_actions
missing_fields
```

The service should be renderer-ready but renderer-independent.

### 11.4 Required dashboard fields

Initial payload should support these fields where available:

| Dashboard field | Requirement |
|---|---|
| Governor name | Use linked account display, latest stats, or profile fallback. |
| Governor ID | Required selected governor identifier. |
| Account type | Self-view only. Do not expose in future inspect-safe payload. |
| VIP level | Optional, from inventory profile. Self-view only unless a later inspect decision approves it. |
| Alliance | Latest/profile fallback. |
| Power | Latest value. |
| Kill Points | Latest/aggregate value. |
| Highest Acclaim | Aggregate/history value, null-safe. |
| Dead | Latest value. |
| Helps | Latest value. |
| Healed | Latest value. |
| Ark joined | Aggregate value where available. |
| Ark won | Aggregate value where available. |
| Ark win ratio | Derived with zero/null guard. |
| Times Named Autarch | Aggregate/history value where available. |
| Conduct Score | Source field is `Conduct`; UI label can be `Conduct Score`. |
| Civilisation | Source field is `Civilization`; UI label can be `Civilisation`. |
| Updated timestamp | Use the latest reliable scan/data timestamp where available. |

Explicitly do not implement:

```text
Olympia fights
Olympia win ratio
```

### 11.5 SQL/DAL requirements

- Validate field availability against `C:\K98-bot-SQL-Server` before implementation.
- Prefer existing service/DAL functions where they already expose the required data cleanly.
- Add a dashboard-specific DAL/repository only when it reduces duplication or avoids command/view SQL leakage.
- Do not add direct SQL to command modules or Discord views.
- Do not change SQL schema in this phase.
- Ensure SQL field naming is accurate: `Conduct`, not `ConductScore`; `Civilization`, not `Civilisation`.

### 11.6 Privacy and inspect-safe boundaries

Normal self-view payload may include:

- linked account type
- own VIP inventory profile
- governor-specific metrics
- available self-service actions

Future inspect-safe payload must not include:

- linked Discord user private account data
- account type if it reveals the Discord-user relationship
- reminders, timezone, language, inventory/export visibility preferences
- private preference metadata
- VIP unless separately approved for leadership inspection

Phase 2 may create the privacy filtering contract, but must not expose `/me inspect` yet.

### 11.7 Formatting/null behavior

The payload should support clear fallback behavior for:

- missing VIP
- missing alliance
- missing highest acclaim
- missing Ark data
- zero Ark joined
- missing Conduct
- missing Civilisation
- missing freshness timestamp

Do not guess missing values.

## 12. Command Surface Governance

- [ ] State whether the task changes top-level command count, grouped subcommand count, or neither.
- [ ] Expected result for Phase 2: neither top-level nor grouped subcommand count changes.
- [ ] Preserve existing `/me` command decorators and behavior.
- [ ] Preserve `@versioned()`, `@safe_command`, `@track_usage()`, permission decorators, response visibility, autocomplete/options, usage-log identity, and command-cache behavior.
- [ ] Run or justify skipping `scripts/validate_command_registration.py`, `tests/test_validate_command_registration.py`, `tests/test_command_inventory.py`, and `tests/test_command_registration_smoke.py`.

## 13. Refactor Decisions

Classify each issue found during implementation:

| Issue | Decision | Reason |
|---|---|---|
| Existing stats/profile/inventory helper can be reused cleanly | `reuse` | Avoid duplicate SQL/data mapping. |
| Existing helper mixes command/view concerns with data assembly | `defer or extract` | Keep Phase 2 focused; extract only when needed for the dashboard foundation. |
| Missing SQL contract for requested field | `exclude or defer` | Do not guess data. Olympia is already excluded. |
| Visual primitive duplication | `defer` | Renderer work starts later after dashboard payload proves out. |
| Legacy command overlap | `defer` | Preserve compatibility until usage-led migration phase. |

Deferred items must use the structured format from `docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 14. Testing Requirements

Add or update tests to cover:

- no registered governors
- one registered governor
- multiple registered governors
- requested governor belongs to invoking user
- requested governor does not belong to invoking user
- payload builds with latest metrics present
- payload handles missing aggregate/history data
- payload handles missing VIP
- payload handles zero/null Ark joined and produces `N/A` or equivalent safe ratio state
- payload uses/labels `Conduct` correctly
- payload uses/labels `Civilization`/`Civilisation` correctly
- payload excludes Olympia fields entirely
- future inspect-safe privacy profile excludes Discord-user private settings
- command registration unchanged

Suggested baseline commands:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

Suggested focused test candidates:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_player_self_service_service.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_governor_dashboard_service.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_governor_dashboard_access.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_validate_command_registration.py tests/test_command_registration_smoke.py
```

Adjust exact test paths after repository inspection.

Before PR handoff:

- Run Codex Security review, or document why a security scan could not be run.
- Include the command-surface statement confirming no slash command count change.

## 15. Acceptance Criteria

- [ ] A governor dashboard context model exists and is typed/structured clearly.
- [ ] The service can list linked governor options for a Discord user.
- [ ] The service can resolve no/one/multiple governor future journey states.
- [ ] The service denies a normal self-service request for a governor not linked to the invoking Discord user.
- [ ] The service can build a dashboard payload for a valid selected governor.
- [ ] The payload includes the approved initial fields and excludes Olympia data.
- [ ] The payload separates self-view-only data from future inspect-safe data.
- [ ] Missing/null values are handled safely and predictably.
- [ ] SQL field names are validated and accurately mapped.
- [ ] No visible `/me` user journey change is introduced in this phase.
- [ ] No legacy command is redirected, removed, or changed.
- [ ] No new direct SQL exists in command/view layers.
- [ ] Tests cover access, payload assembly, missing data, and command registration compatibility.
- [ ] Codex Security review is run because access/data/privacy surfaces are touched.
- [ ] Deferred optimisations are captured structurally.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Data Contracts Validated
7. Helpers Reused
8. Refactor Findings
9. Test Plan
10. AI Review Gates
11. Command Surface Impact
12. Deployment Steps
13. Deferred Optimisations

## 17. PR Summary Template

```md
## Summary

- Added the Phase 2 governor dashboard context and payload foundation for the future `/me dashboard` redesign.
- Added access checks and null-safe dashboard data assembly for selected governors.
- Preserved current command behavior and excluded Olympia fields until a source exists.

## Changes

- <change item>

## Tests

- <test command or verification>

## AI Review Gates

- Codex Security: <run | skipped, with reason>

## Command Surface Impact

- No top-level or grouped slash command count changes.

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Runtime user-facing risk should be low because no visible `/me` flow changes are included. Rollback is bot-code only unless implementation discovers and separately approves SQL changes.
```
