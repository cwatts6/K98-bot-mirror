# Codex Task Pack - Player Self-Service Command Centre v2 Phase 3 Governor Selector and Dashboard Shell

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 3 Governor Selector and Dashboard Shell`
- Date: `2026-07-10`
- Owner/context: Follow-on from the completed Phase 2 governor context and dashboard data foundation.
- Task type: `Discord interaction feature | private governor selection | dashboard shell integration`
- One-pass approved: `No`
- Implementation approved: `Yes - registry authority checkpoint confirmed 2026-07-10`
- Status: `implementation complete - local validation passed; operator smoke pending`

## Completion Record

Phase 3 delivered the dashboard-specific private governor journey without adding or removing slash
commands. The operator approved existing active registry linkage as the self-view authorization
source, supported by Discord onboarding audit, monthly admin reconciliation against in-game
records, and owner-approved account transfer controls.

Delivered:

- Private no/one/multiple/unavailable/denied journey handling.
- Direct single-governor opening and pre-fetch multi-governor selection.
- Access re-resolution before every selected-governor payload fetch.
- Author gating, timeout disabling, stale/replaced-view rejection, forged selection denial, and
  private failure behavior.
- In-place Change Governor for multiple linked accounts.
- A renderer-independent fallback embed containing only the approved Phase 2 fields.
- Safe missing metrics, absent VIP, zero Ark joined, and complete Olympia exclusion.
- Existing Accounts, Reminders, Preferences, Inventory, Exports, `/me`, and legacy command
  compatibility.
- `/me dashboard` version increment from `v1.00` to `v1.01`; command counts unchanged.
- Selector pagination for more than 25 linked governors without using `AccountPickerView`.

Automated validation completed with 108 focused service/view/command tests and the full repository
suite (`2435 passed, 2 skipped`). Architecture, deferred-item, test-selection, smoke-import,
command-registration, full pre-commit, and diff checks passed. The Codex Security plugin was not
exposed to this task and the local CLI could not be launched, so an independent security-focused
diff review was used as the documented fallback. It found and drove closure of one interaction
integrity issue around concurrent/stale/timeout transitions, then completed with no reportable
findings. Operator Discord smoke remains before rollout.

Product direction confirmed during the approval checkpoint: admin/leadership inspect is required
for kingdom management and player support. It remains outside Phase 3 and must be delivered as a
separate permission-gated slice using the existing inspect-safe payload boundary.

## 2. Objective

Make `/me dashboard` governor-first by wiring the completed Phase 2 context and payload foundation
into a safe private Discord journey.

This phase delivers the no-governor, one-governor, and multiple-governor states, a selected-governor
fallback dashboard shell, and an in-place Change Governor journey. It does not build the premium
PNG renderer or add any new slash subcommands.

## 3. Required Reading

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- `docs/task_packs/archive/Player Self-Service Command Centre v2 Phase 1 Governor Dashboard Product Blueprint and Audit Report.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 2 Governor Context and Dashboard Data Foundation.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Inspect the current implementation before coding:

- `commands/me_cmds.py`
- `ui/views/player_self_service_views.py`
- `account_picker.py`
- `player_self_service/governor_dashboard_models.py`
- `player_self_service/governor_dashboard_service.py`
- `player_self_service/governor_dashboard_dal.py`
- `player_self_service/service.py`
- `tests/test_governor_dashboard_service.py`
- relevant player-self-service view/command tests

No SQL schema change is expected. If Phase 2 DAL fields are changed, validate the contract against
`C:\K98-bot-SQL-Server` before implementation.

## 4. Phase 2 Baseline

Phase 2 delivered:

- Typed governor option, context, resolution, payload, and payload-section models.
- Linked-governor resolution for `requires_setup`, `selected`, `requires_selection`, `denied`, and
  `unavailable` states.
- Default-deny access for unlinked self-service requests.
- Explicit opt-in before future unlinked inspect context can be allowed.
- Renderer-independent payload assembly for approved fields only.
- Separate self-view-only data and future inspect-safe data.
- Null-safe handling and focused regression tests.

Phase 2 deliberately did not create or wire a Discord governor selector.

## 5. Selector Architecture Decision

Create a dashboard-specific selector/view for Phase 3. Do not wire the shared
`account_picker.AccountPickerView` directly into `/me dashboard`.

Rationale:

- `AccountPickerView` is a one-shot picker that marks itself complete after a selection.
- It bundles governor lookup, optional registration, and refresh controls intended for command
  launch flows.
- The governor dashboard needs author-gated, in-place context switching and dashboard navigation.
- Every selection must re-resolve access through the Phase 2 service before data is loaded.
- The selected dashboard must support Change Governor without creating a chain of private followups.

Reuse instead of duplicate:

- Phase 2 `GovernorDashboardOption` values and resolution/access helpers.
- Existing `core.interaction_safety` defer/response patterns.
- Existing player-self-service author gating, timeout disabling, message-reference, and fallback
  response patterns.
- Existing Accounts, Reminders, Preferences, Inventory, and Exports page handoffs.

Recommended placement:

- `ui/views/player_self_service_governor_dashboard_views.py` for the dashboard-specific view/select.
- Keep command wiring thin in `commands/me_cmds.py` and/or the existing page-send boundary.
- Keep payload assembly and access decisions in `player_self_service/governor_dashboard_service.py`.

## 6. In Scope

- Change `/me dashboard` to resolve the invoking user's dashboard journey privately.
- No linked governors: show a safe setup shell with Accounts as the primary action.
- One linked governor: select it automatically and open the dashboard shell.
- Multiple linked governors: show a private governor selector before loading dashboard data.
- Selected governor: build the Phase 2 payload and render a concise fallback embed/dashboard shell.
- Add Change Governor only when multiple linked governors exist.
- Preserve access to Accounts, Reminders, Preferences, Inventory, and Exports.
- Keep all output private/ephemeral.
- Author-gate all selector and dashboard interactions.
- Re-resolve governor linkage/access on selection and every governor-specific refresh/action.
- Disable controls on timeout and reject stale or foreign-user interactions safely.
- Distinguish account-source unavailable from genuinely having no linked governors.
- Handle dashboard data failure with the Phase 2 null-safe payload/fallback behavior.
- Increment `/me dashboard` command version because its visible behavior changes.
- Add focused command/view/service tests and manual Discord smoke instructions.
- Update programme, command, briefing, and deferred documentation where the delivered behavior
  requires it.

## 7. Out of Scope

- No final premium PNG governor dashboard renderer; that remains Phase 4.
- No changes to existing Accounts, Reminders, Preferences, Inventory, or Exports semantics.
- No `/me resources`, `/me materials`, `/me speedups`, `/me history`, or `/me inspect` commands.
- No leadership/admin inspect journey or unlinked inspect opt-in call path.
- No redirect, removal, or behavior change for `/my_stats`, `/myinventory`, `/stats player`,
  `/player_profile`, `/mykvkcrystaltech`, or `/kvk history`.
- No inventory output, export schema, or stats export semantic changes.
- No Olympia fields, placeholders, copy, or blockers.
- No SQL schema changes.
- No premium card primitive extraction.
- No governor registration ownership-policy redesign inside this phase without explicit approval.

## 8. Required Journey States

| Resolution state | Required Discord behavior |
| --- | --- |
| `requires_setup` | Private setup shell; Accounts is primary; no empty metric grid. |
| `selected` | Build payload and show selected-governor dashboard shell. |
| `requires_selection` | Private selector using the returned options; do not fetch a governor payload yet. |
| `denied` | Private access-denied message; do not fetch payload data. |
| `unavailable` | Private temporary-unavailable message; do not imply the player has no accounts. |

Selection callback flow:

```text
interaction author check
-> defer privately
-> resolve_dashboard_context(user_id, selected_governor_id, viewer_mode="self")
-> require selected + access_allowed
-> build_governor_dashboard_payload(context)
-> edit the existing private message in place
```

## 9. Dashboard Shell Contract

The Phase 3 shell is intentionally renderer-light but must prove the payload and interaction flow.

Show, when present:

- Governor name and Governor ID.
- Self-view account type and optional VIP.
- Alliance, Civilisation, and Conduct Score.
- Power, Kill Points, Highest Acclaim, Dead, Helps, and Healed.
- Ark joined, won, and guarded win ratio.
- Times Named Autarch.
- Freshness/update timestamp or a clear unavailable state.

Shell rules:

- Use concise embed sections or fields; do not extend the current setup-card renderer into a
  temporary pseudo-premium renderer.
- Do not guess missing data.
- Do not include Olympia.
- Keep field labels aligned with Phase 2 payload names.
- Keep the shell replaceable by the Phase 4 renderer without changing the service contract.
- Preserve existing user-level navigation separately from governor metrics.

## 10. Access, Privacy, and Trust Boundary

- Normal self-service only accepts governors currently linked to the invoking Discord user.
- Never call `allow_unlinked_inspect=True` from this phase.
- Do not trust a select value by itself; resolve context again through the service.
- Do not accept another user's interaction even if the governor ID is linked to both records.
- Do not expose Discord-user preferences in the governor metric shell except the approved
  self-view account type and optional VIP payload.
- Log failures and denied outcomes without logging private preference values.

Phase 3 approval checkpoint:

The existing registry linkage is the current authorization source used by established self-service
commands. The broader GovernorOS ownership-assurance policy is tracked separately in deferred
optimisation. Before implementation starts, confirm that existing registry linkage remains the
approved authority for this Phase 3 rollout. If not, stop and prepare a separate account-linkage
verification hardening slice before exposing the new dashboard journey.

## 11. Command Surface Impact

Expected result:

- Top-level command count: unchanged.
- `/me` grouped subcommand count: unchanged.
- `/me dashboard`: visible behavior and version change only.
- All other `/me` and legacy command registrations: unchanged.

Preserve decorators and command governance:

- `@versioned(...)`
- `@safe_command`
- `@track_usage()`
- private defer/response behavior
- command-cache and registration compatibility

## 12. Likely Files

Likely modify:

- `commands/me_cmds.py`
- `ui/views/player_self_service_views.py`
- `player_self_service/__init__.py` only if a clean export is required
- focused tests under `tests/`
- programme/briefing/canonical docs after implementation

Likely create:

- `ui/views/player_self_service_governor_dashboard_views.py`
- `tests/test_player_self_service_governor_dashboard_views.py`

Avoid modifying Phase 2 service/DAL contracts unless implementation reveals a real missing
interaction-facing contract. Any service change requires matching service tests.

## 13. Test Requirements

Automated coverage must include:

- no-governor setup state and Accounts action
- one-governor automatic dashboard open
- multiple-governor selector state
- selected option maps to the expected governor context
- selection callback rechecks linkage/access
- unlinked or forged governor value denied without data fetch
- foreign user rejected by selector and dashboard view
- stale/expired view behavior
- account source unavailable is not rendered as no accounts
- payload/data failure renders safe missing-data shell
- missing VIP and missing metrics remain safe
- zero Ark joined shows `N/A`
- Change Governor present only for multiple linked governors
- user-level navigation remains available
- no Olympia text/fields in the shell
- `/me dashboard` remains private
- command decorators/version and registration compatibility
- all existing `/me` subcommands and named legacy commands remain registered

Suggested focused commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_governor_dashboard_service.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_player_self_service_governor_dashboard_views.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_player_self_service_views.py tests/test_me_cmds.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_validate_command_registration.py tests/test_command_registration_smoke.py
```

Required validation:

```powershell
.\.venv\Scripts\python.exe scripts/validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts/validate_deferred_items.py
.\.venv\Scripts\python.exe scripts/select_tests.py
.\.venv\Scripts\python.exe scripts/smoke_imports.py
.\.venv\Scripts\python.exe scripts/validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
```

Run Codex Security review because this phase changes Discord interactions, access enforcement,
private data presentation, and user-controlled selector input.

## 14. Manual Discord Smoke Test

Use test users or controlled registry fixtures representing each state:

1. No linked governors: `/me dashboard` shows private setup guidance and Accounts opens.
2. One linked governor: dashboard shell opens directly with the correct Governor ID.
3. Multiple linked governors: selector opens privately; each account loads its own shell.
4. Change Governor: returns to the selector and switches the same private message in place.
5. Foreign interaction: another user cannot operate the view.
6. Missing data/VIP: shell remains readable and uses safe fallback values.
7. Existing `/me accounts`, `/me reminders`, `/me preferences`, `/me inventory`, and `/me exports`
   continue to work.
8. Legacy `/my_stats`, `/myinventory`, `/stats player`, `/player_profile`, `/mykvkcrystaltech`, and
   `/kvk history` continue to work unchanged.

## 15. Acceptance Criteria

- [x] `/me dashboard` uses the Phase 2 governor resolution service.
- [x] No/one/multiple/unavailable/denied states are represented safely.
- [x] Multiple-account users receive a private dashboard-specific selector.
- [x] One-account users open the selected dashboard shell directly.
- [x] Every selected governor is access-checked again before payload fetch.
- [x] Foreign and stale interactions are rejected safely.
- [x] Change Governor works in place for multiple linked governors.
- [x] The fallback shell renders approved Phase 2 fields and excludes Olympia.
- [x] Accounts, Reminders, Preferences, Inventory, and Exports remain reachable.
- [x] No top-level or grouped subcommand count changes occur.
- [x] Legacy commands remain behavior-compatible.
- [x] No SQL schema change is introduced.
- [ ] Focused, regression, and validator evidence is recorded; operator Discord smoke remains.
- [x] Security-focused diff review completed with no reportable findings after hardening.
- [x] Deferred findings are captured structurally.

## 16. Delivery Output

Provide:

1. Summary and visible journey change.
2. File manifest.
3. Selector reuse/new-view decision confirmation.
4. Access/privacy behavior.
5. Command surface/version impact.
6. SQL changes or explicit no-change statement.
7. Automated validation results.
8. Manual smoke instructions/results.
9. Codex Security status.
10. Deferred optimisations and Phase 4 handoff notes.
