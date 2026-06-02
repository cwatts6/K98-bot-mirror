# Codex Task Pack - Command Platform Phase 7 Governance And CI Guardrails

## 1. Task Header

- Task name: Command Platform Phase 7 - Governance And CI Guardrails
- Date: 2026-06-02
- Owner/context: Command Platform Audit & Optimisation Programme
- Task type: governance / validation tooling / CI preparation
- One-pass approved: no
- Status: final planned command-platform phase

## 2. Required Reading

Before implementation or documentation changes, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/task_packs/Codex Task Pack - Command Platform Audit & Optimisation Programme.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/command_platform_audit.md`
- `docs/reference/command_surface_audit.md`
- `docs/reference/deferred_optimisations.md`

Also review:

- `commands/command_inventory.py`
- `scripts/validate_command_registration.py`
- command registration, inventory, lifecycle, validator, and CI/pre-commit tests
- existing CI, pre-commit, and local validation configuration

## 3. Objective

Complete the Command Platform Audit & Optimisation Programme by adding governance and guardrails
that prevent future command-limit drift and keep the canonical command reference maintainable.

Phase 7 should make it difficult to accidentally:

- exceed Discord's 100 top-level application-command limit
- add ungrouped admin/leadership/operator commands without review
- bypass standard command decorators
- forget command registration validation
- forget to update `canonical_command_reference.md` after command-surface changes

## 4. Background

Phase 6 was completed in PR 137 (`codex/command-platform-phase-6-canonical-docs`), merged, marked
complete, and pushed to production. It created `docs/reference/canonical_command_reference.md`,
updated stale active command docs and smoke references, and left the command baseline at:

```text
primary=39 grouped_subcommands_detected=76 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=39
```

The command surface now has a 61-command buffer below Discord's top-level command limit. Phase 7
should preserve that headroom through governance rather than more command movement.

## 5. Scope

### In Scope

- Review current command validator output and failure modes.
- Decide whether `scripts/validate_command_registration.py` should emit a richer machine-readable
  or Markdown inventory artifact.
- Add or update local validation, pre-commit, or CI wiring so command registration validation is
  consistently run before command-surface PRs.
- Add governance documentation for new commands:
  - group-first command design
  - when a flat path is allowed
  - required permission decorators
  - version/usage tracking expectations
  - canonical reference update requirement
  - command-count impact review
- Add tests for any validator, artifact, CI, or checklist changes.
- Update `docs/reference/canonical_command_reference.md` only for governance metadata; do not
  change command paths.
- Close or update command-platform deferred optimisation items that are resolved by governance.

### Out Of Scope

- Moving, renaming, retiring, or adding slash commands.
- Player self-service workflow redesign.
- Public calendar/KVK calendar UX redesign.
- SQL schema changes.
- Permission behavior changes.
- Runtime command handler implementation changes.
- Production promotion or deployment.

## 6. Mandatory Workflow

1. Review/scope Phase 7 and stop for approval.
2. Inventory existing validator, CI, pre-commit, and command-governance docs.
3. Present the proposed guardrail design and stop for approval.
4. Implement approved governance/tooling/docs updates.
5. Run focused validation.
6. Open a ready-for-review PR against `K98-bot-mirror`.

## 7. Design Questions

- Should command registration validation be enforced only in CI, or also through pre-commit?
- Should the validator produce a reusable command inventory artifact for PR review?
- Should the validator fail on ungrouped admin/leadership/operator commands, or only warn?
- What exact checklist should future task packs include when adding or changing commands?
- Should Phase 7 close the programme after guardrails land?

Recommended answer for the final question: yes. Phase 7 is the final planned command-platform
programme phase. Player self-service workflow redesign and public calendar/KVK calendar redesign
should remain separate deferred optimisation programmes.

## 8. Suggested Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_validate_command_registration.py tests\test_command_inventory.py tests\test_command_registration_smoke.py
```

Before PR handoff, run or justify skipping:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
```

Codex Security review is usually optional for governance/docs/tooling-only Phase 7 work. Run it if
the phase expands into permission behavior, command runtime behavior, SQL/data access, file
handling, secrets/config, deployment, network calls, user-controlled input parsing, or
restart-sensitive persistence.

## 9. Required Delivery Output

1. Summary
2. File Manifest
3. SQL Changes
4. Helpers Reused
5. Refactor Findings
6. Test Plan And Results
7. AI Review Gates
8. Deployment / Rollback Notes
9. Deferred Optimisations
10. Programme Closure Recommendation
