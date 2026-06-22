# Codex Chat Starter - Player Self-Service Command Centre Phase 3 Modern Account Centre

Status: active starter for the next Player Self-Service Command Centre phase.

Phase 1 audit/design is complete and archived.

Phase 2 `/me` Command Shell and Navigation Foundation is delivered in mirror PR #164 and
production PR #472, smoke tested successfully, and awaiting manual merge/promotion by the
operator.

Delivered Phase 2 context:

- `/me dashboard`, `/me accounts`, `/me reminders`, `/me preferences`, and `/me exports` are
  registered.
- The `/me` shell is private, read-only, and uses the player self-service service/view boundary.
- `/me dashboard` shows account, reminder, and preference status plus dashboard Quick Launch.
- Quick Launch provides guidance for KVK stats, KVK targets, KVK history, KVK rankings,
  inventory, and exports.
- `/me exports` opens the exports page with page navigation only; dashboard Quick Launch is
  dashboard-only by design.
- Legacy commands still work and must remain live in Phase 3.

Source documents:

- `docs/task_packs/Player Self-Service Command Centre - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 3 Modern Account Centre.md`
- `docs/task_packs/archive/Player Self-Service Command Centre - Phase 1 Audit and Design Report.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 2 Command Shell and Navigation Foundation.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

## Copy/Paste Starter

```text
Codex, start Phase 3 of the Player Self-Service Command Centre: Modern Account Centre.

Phase 1 audit/design is complete and archived.

Phase 2 is delivered and smoke tested successfully in mirror PR #164 and production PR #472. The
operator will manually merge and push the PRs. The delivered `/me` shell includes `/me dashboard`,
`/me accounts`, `/me reminders`, `/me preferences`, and `/me exports`. It is private and read-only.
Dashboard Quick Launch works and shows guidance. `/me exports` opens only the exports page and
intentionally does not include the dashboard Quick Launch menu. Existing legacy commands still work.

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
- docs/task_packs/Player Self-Service Command Centre - Programme Pack.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 3 Modern Account Centre.md
- docs/task_packs/archive/Player Self-Service Command Centre - Phase 1 Audit and Design Report.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 2 Command Shell and Navigation Foundation.md
- docs/player_self_service_command_centre_briefing.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-sql-validation
- k98-test-selection
- k98-deferred-optimisation-capture if new out-of-scope debt is found
- k98-pr-review before handoff
- codex-security security review or documented skip before PR handoff

Phase 3 objective:
Turn the delivered read-only `/me accounts` page into a modern private account centre for account
review, Governor ID lookup, registration, modification/replacement, removal with confirmation, and
return-to-dashboard navigation.

Scope:
1. Start with audit/scope only unless I explicitly approve one-pass implementation.
2. Validate registry SQL contracts against `C:\K98-bot-SQL-Server`.
3. Reuse existing registry service/DAL write paths; do not invent new SQL or write SQL in commands/views.
4. Keep `commands/me_cmds.py` thin.
5. Keep service logic Discord-type-free.
6. Extend `ui/views/player_self_service_views.py` or create a focused account-centre view module
   only if the existing view becomes too broad.
7. Use buttons for account actions, selects for slots, modals for Governor name/ID input, and
   confirmations for removal/replacement.
8. Preserve duplicate/claim protection and slot rules.
9. Keep `/register_governor`, `/modify_registration`, `/my_registrations`, and `/mygovernorid`
   registered and usable. Do not redirect or remove them in Phase 3.
10. Capture out-of-scope cleanup structurally.

Likely files:
- commands/me_cmds.py
- player_self_service/service.py
- player_self_service/account_service.py if needed
- ui/views/player_self_service_views.py
- services/governor_account_service.py
- registry/registry_service.py
- registry/dal/registry_dal.py
- target_utils.py
- tests/test_me_cmds.py
- tests/test_player_self_service_service.py
- tests/test_player_self_service_views.py
- tests/test_player_self_service_account_service.py if a dedicated service is added
- docs/player_self_service_command_centre_briefing.md

Suggested validation:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_service.py tests\test_player_self_service_views.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_registry_service.py tests\test_registry_dal.py tests\test_registry_views_smoke.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py

Acceptance criteria:
- `/me accounts` remains private and opens the modern account centre.
- Players can review linked accounts.
- Players can look up Governor IDs.
- Players can register, modify/replace, and remove accounts through service-backed flows.
- Removal and replacement require confirmation.
- Duplicate/claim protection is preserved.
- Legacy account commands remain live.
- No direct SQL is added to commands or views.
- Focused tests and standard validators pass.
- SQL contract validation is documented.
- Codex Security is run or explicitly justified.
```
