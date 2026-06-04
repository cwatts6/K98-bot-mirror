# KVK Player Experience Redesign - Phase 2B Player KVK Scaffold Task Pack Draft

## 1. Task Header

- Task name: `KVK Player Experience Redesign - Phase 2B Player /kvk Scaffold`
- Date: `2026-06-03`
- Task type: `feature / command-surface migration scaffold`
- One-pass approved: `no`
- Status: `draft`

## 2. Objective

Create the player-facing `/kvk` command group after Phase 2A resolves the admin collision.

Initial player subcommands:

```text
/kvk stats
/kvk targets
/kvk history
/kvk rankings
```

Legacy commands remain live.

## 3. Approved Behaviour

- `/kvk rankings` should support all three initial modes: `kvk`, `honor`, and `prekvk`.
- `/kvk stats` should keep account selection private, while selected single-account stats post publicly.
- `/kvk targets` should start the in-programme move toward a KVK targets service payload contract and DAL boundary.
- Acclaim/contribution metrics should be included in the programme after SQL source and terminology validation.
- Visual cards remain out of Phase 2B unless explicitly approved.

## 4. Scope

In scope:

- Add player `/kvk` subcommands backed by existing behaviour where safe.
- Add ranking mode routing for KVK, honor, and PreKvK.
- Preserve legacy flat commands unchanged.
- Preserve current permissions and visibility unless this task explicitly changes them.
- Add tests for command registration, permissions, delegation, ranking modes, and old-command preservation.
- Update canonical command reference and command inventory expectations.
- Begin targets service/DAL payload cleanup only where needed to keep `/kvk targets` thin and testable.

Out of scope:

- No generated KVK stats card.
- No old command removal or deprecation.
- No SQL schema/procedure/view/function changes.
- No KVK import/recompute/export or Google Sheets behaviour changes.
- No broad `/my` or `/player` self-service redesign.

## 5. Architecture Direction

- New command module target: `commands/kvk_cmds.py`, unless Phase 2A establishes a better local pattern.
- Commands validate, defer safely, preserve permission checks, and call services/views.
- KVK targets should move toward `kvk/services/` and `kvk/dal/` ownership for payload construction.
- Ranking mode adapters should not duplicate ranking calculations.
- PreKvK image/report rendering remains in `prekvk/` and `ui/views/prekvk_report_views.py`; `/kvk rankings type:prekvk` should delegate.

## 6. `/kvk stats`

Requirements:

- Reuse existing account summary and KVK stats rendering for parity.
- Private account selection.
- Public selected single-account stats posting.
- Preserve no-registration fallback actions.
- Do not introduce the Phase 3 card yet.

## 7. `/kvk targets`

Requirements:

- Preserve current target states: off-season, target unavailable, exempt, below-power, not active, unknown governor, and normal progress.
- Create or prepare a service payload contract and DAL boundary so commands/views do not own target business logic.
- Preserve current target formulas and SQL/cache source-of-truth.

## 8. `/kvk history`

Requirements:

- Preserve existing chart/table output and account selection.
- Keep table-first accessibility.
- Do not add new charting or visual card output.

## 9. `/kvk rankings`

Initial modes:

```text
type: kvk
type: honor
type: prekvk
```

Requirements:

- Preserve current KVK ranking calculations and pagination.
- Preserve current honor ranking calculations and pagination.
- Preserve current PreKvK report payload, sort, limit, and generated PNG behaviour by delegation.
- Decide whether `type` is a required slash option, defaulted slash option, or interactive select before implementation.

## 10. Testing And Validation

Run or justify:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_inventory.py tests\test_command_registration_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_mykvkstats.py tests\test_kvk_personal_views.py tests\test_mykvktargets.py tests\test_kvk_ui_rebuild_options.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_build_kvkrankings_embed.py tests\test_kvkrankingview.py tests\test_honor_rankings_view.py tests\test_prekvk_report_command.py tests\test_prekvk_report_views.py
```

Run Codex Security before PR handoff because user-facing commands, permissions, Discord interactions, SQL-backed outputs, and user-controlled options are touched.

## 11. Acceptance Criteria

- [ ] Phase 2A is complete or explicitly accounted for.
- [ ] `/kvk stats`, `/kvk targets`, `/kvk history`, and `/kvk rankings` are registered.
- [ ] `/kvk rankings` supports `kvk`, `honor`, and `prekvk` modes.
- [ ] `/kvk stats` preserves private selection and public selected stat output.
- [ ] Legacy commands remain live.
- [ ] No generated card work is mixed into this scaffold.
- [ ] No SQL/import/export/recompute semantics change.
- [ ] Targets service/DAL payload cleanup is started or explicitly scoped into the next targets phase.
