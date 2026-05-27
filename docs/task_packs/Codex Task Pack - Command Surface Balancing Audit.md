# Codex Task Pack — Command Surface Balancing Audit

## 1. Task Header

- Task name: Command Surface Balancing Audit
- Date: 2026-05-18
- Owner/context: Deferred optimisation — Discord command registration limit
- Task type: deferred optimisation batch
- One-pass approved: no

## 2. Required Reading

Before implementation, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`.

Also review:

- `docs/reference/deferred_optimisations.md`
- Existing command registration docs or promotion docs that mention slash command sync
- `scripts/validate_command_registration.py`

## 3. Objective

Audit and rebalance the K98 bot Discord application-command surface before the next command-heavy feature work.

The goal is to prevent Discord startup sync failures caused by the 100 top-level command ceiling, especially error `30032`, while preserving user experience, admin permission checks, and existing command discoverability.

## 4. Background

The primary Discord application-command set is currently at or near the 100 top-level command limit.

Phase 2C avoided the immediate failure by grouping PreKvK commands under `/prekvk`, but future standalone slash commands could still break startup sync unless the command surface is actively managed.

This task should produce a clear consolidation plan and implement safe command grouping only where the user experience allows.

## 5. Scope

### In Scope

- Audit all current top-level slash commands.
- Count current registered top-level commands and grouped subcommands.
- Review `commands/` for standalone commands that could be grouped by domain.
- Review `scripts/validate_command_registration.py`.
- Identify stale, duplicate, low-use, or admin-only commands suitable for consolidation or retirement.
- Propose domain groupings such as:
  - `/kvk`
  - `/prekvk`
  - `/mge`
  - `/ark`
  - `/inventory`
  - `/admin`
  - `/events`
  - `/sql` or `/ops`
- Preserve all admin-only checks when commands move.
- Update docs for renamed command paths.
- Keep PR validation enforcing the 100-command ceiling.
- Add tests or validation coverage for command registration where practical.

### Out of Scope

- Building new user-facing features.
- Changing command behaviour beyond path/group relocation.
- Removing public commands without explicit operator approval.
- SQL schema changes unless a discovered command depends on SQL-backed command metadata.
- Large UX redesigns unrelated to command grouping.

## 6. Source Deferred Items

### Deferred Optimisation
- Area: `commands/`, `scripts/validate_command_registration.py`
- Type: architecture
- Description: The primary Discord application-command set is currently at the 100 top-level command limit. Phase 2C avoided the limit by grouping PreKvK commands under `/prekvk`, but future standalone slash commands can still break startup sync with Discord error `30032` unless command surface consolidation is planned before new command work.
- Suggested Fix: Run a command-surface balancing audit before the next command-heavy feature. Group related commands by domain where user experience allows, identify stale/low-use admin commands for consolidation or retirement, update docs for renamed paths, and keep `scripts/validate_command_registration.py` enforcing the 100-command ceiling in PR validation.
- Impact: high
- Risk: medium
- Dependencies: Coordinate with bot operators before renaming public command paths; preserve admin-only permission checks when commands move into groups.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation to map command ownership and grouping boundaries. |
| `k98-discord-command-feature` | use | This directly changes Discord slash command registration and command paths. |
| `k98-sql-validation` | not applicable unless discovered | Use only if command metadata, permissions, or command docs depend on SQL-backed data. |
| `k98-test-selection` | use | Required before validation to choose focused command and registration tests. |
| `k98-deferred-optimisation-capture` | use | Capture any out-of-scope command debt found during audit. |
| `k98-pr-review` | use | Required before PR handoff due to high startup-risk impact. |
| `k98-promotion-check` | use | Required before production promotion because command sync failures can block bot startup. |

## 8. Mandatory Workflow

1. Audit command surface and stop for approval.
2. Present proposed grouping/retirement plan and stop for approval.
3. Implement approved changes only.
4. Update tests, validation, and docs.
5. Run quality gates.
6. Complete PR review and promotion readiness check.

Do not perform public command renames in one pass unless explicitly approved.

## 9. Audit Requirements

Review:

- Number of current top-level application commands.
- Number of grouped commands and subcommands.
- Commands close to natural domain groupings.
- Admin-only commands that can safely move under `/admin`, `/ops`, or domain admin groups.
- Public commands where renaming would require operator communication.
- Duplicate or legacy command paths.
- Commands with weak permission boundaries.
- Command registration validation gaps.
- Startup sync risk.
- Documentation gaps after command path changes.

Map:

- command module
- command name
- public/admin-only status
- current top-level path
- proposed grouped path
- migration risk
- permission decorator/check used
- docs requiring update
- tests requiring update

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | `commands/<domain>_cmds.py` |
| Command groups | Domain-level app command groups where UX allows |
| Views / modals | `ui/views/` |
| Services / business logic | Existing subsystem service modules |
| Repository / DAL | Existing subsystem repository modules |
| Operational tooling | `scripts/validate_command_registration.py` |
| Documentation | `docs/` and relevant command reference docs |
| Tests | `tests/` command registration and import tests |

## 11. Likely Files

### Review

- `commands/`
- `scripts/validate_command_registration.py`
- `tests/`
- `docs/reference/deferred_optimisations.md`
- `docs/`
- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

### Modify

- `commands/<affected_domain>_cmds.py`
- `scripts/validate_command_registration.py`
- Relevant command registration tests
- Relevant documentation

### Create

- Optional: `docs/reference/command_surface_audit.md`
- Optional: focused tests for grouped command validation

## 12. Implementation Requirements

- Keep commands and views thin.
- Do not move business logic into command grouping code.
- Preserve existing permission checks exactly.
- Preserve autocomplete behaviour where commands move.
- Preserve interaction response behaviour.
- Avoid breaking public command paths without approval.
- Prefer grouping admin-heavy or low-use commands first.
- Ensure `scripts/validate_command_registration.py` still fails if top-level command count exceeds 100.
- Add warning output if count is near the limit, ideally at 90+.
- Document grouped command paths clearly.
- Capture any deferred command UX cleanups separately.

## 13. Refactor Decisions

Classify each finding:

| Issue | Decision | Reason |
|---|---|---|
| Top-level command close to domain grouping | fix now / defer | Based on UX risk and approval. |
| Public command rename | defer unless approved | Requires operator coordination. |
| Admin-only command consolidation | likely fix now | Lower user-facing risk. |
| Duplicate command path | fix now / defer | Depends on usage and migration risk. |
| Low-use stale command | defer unless approved | Retirement needs operator confirmation. |

Deferred items must use the structured format from `docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 14. Testing Requirements

Run baseline gates:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```
