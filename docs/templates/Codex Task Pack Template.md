# Codex Task Pack Template

> Canonical template for K98 bot Codex work.
> Replace all angle-bracket placeholders before use.
> Generated task packs must record an explicit Codex Security routing decision; never use
> unqualified `Codex Security review` wording as an execution instruction.

Use this file for new feature work, bug fixes, refactor batches, and deferred optimisation packs.
Do not use archived templates as active guidance.

## 1. Task Header

- Task name: `<short descriptive name>`
- Date: `<YYYY-MM-DD>`
- Owner/context: `<requester, issue, PR, incident, or source>`
- Task type: `<feature | bug fix | refactor | deferred optimisation batch | docs | tooling>`
- One-pass approved: `<yes | no>`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

For a security-review decision, also read the active repository `AGENTS.md`, the root and any
applicable nested `SECURITY.md` files when present, and the `k98-security-review-routing` skill.
`SECURITY.md` supplies policy and threat-model context; it does not select or launch a scan.

Then follow the required reading order and conditional references defined by
`docs/reference/README.md`. Do not add every reference document to a task pack by default.

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

`C:\K98-bot-SQL-Server`

## 3. Objective

<Describe the outcome in 2-4 lines. State the user-visible or engineering result first, then the
implementation direction only where it helps clarify scope.>

## 4. Background

<Summarise relevant context, links, prior PRs, incidents, current behaviour, or deferred items.>

## 5. Scope

### In Scope

- `<specific file, module, behaviour, workflow, or documentation change>`
- `<specific validation or migration work to include>`

### Out of Scope

- `<explicitly excluded work>`
- `<related optimisation that should be deferred unless separately approved>`

## 6. Source Deferred Items

Use this section only when the task comes from deferred optimisation capture. Delete it when it
does not apply.

```md
### Deferred Optimisation
- Area:
- Type: performance | architecture | cleanup | refactor | consistency
- Description:
- Suggested Fix:
- Impact: low | medium | high
- Risk: low | medium | high
- Dependencies:
```

## 7. Codex Skills To Use

Use these local Codex skills when they apply to the task. List `not applicable` with a short reason
instead of deleting a skill silently. The security-routing skill is required for every task pack,
even when its outcome is a documented skip.

| Skill | Use when |
|---|---|
| `k98-architecture-scope` | Always before implementation, unless one-pass execution has already been explicitly approved. Use it to identify affected layers, SQL/persistence implications, refactor triggers, conditional docs, tests, and approval checkpoints. |
| `k98-discord-command-feature` | The task changes slash commands, Discord views/modals, embeds, buttons, selects, interaction callbacks, command registration, permissions, or user-facing bot flows. |
| `k98-sql-validation` | The task touches or depends on SQL schema, stored procedures, views, indexes, UDTs, `ProcConfig`, staging/output tables, DAL queries, imports, exports, reports, or SQL-backed caches. |
| `k98-test-selection` | Always before validation. Use it to combine `scripts/select_tests.py` with risk-based test coverage decisions and skip justifications. |
| `k98-deferred-optimisation-capture` | Audit or implementation finds out-of-scope debt, refactor triggers, duplicate helpers, direct SQL in commands/views, restart-safety gaps, or cleanup candidates. Do not use it to accept, suppress, or reprioritise security findings. |
| `k98-pr-review` | Before merge or PR handoff, to check architecture, SQL alignment, tests, deferred items, Discord safety, and promotion readiness. |
| `k98-promotion-check` | Before production promotion, production PR creation, production merge, SQL deployment sequencing, or bot-machine deployment. |
| `k98-security-review-routing` | Always for every task pack. Choose and record exactly one outcome for each affected repository: documented skip, diff-focused Changes review, explicitly requested standard codebase audit, explicitly requested deep codebase audit, existing-findings triage, or accepted-finding remediation. Selecting the routing skill must not itself start a scan. |

### Skill Decisions

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | `<use | not applicable>` | `<why>` |
| `k98-discord-command-feature` | `<use | not applicable>` | `<why>` |
| `k98-sql-validation` | `<use | not applicable>` | `<why>` |
| `k98-test-selection` | `<use | not applicable>` | `<why>` |
| `k98-deferred-optimisation-capture` | `<use | not applicable>` | `<why>` |
| `k98-pr-review` | `<use | not applicable>` | `<why>` |
| `k98-promotion-check` | `<use | not applicable>` | `<why>` |
| `k98-security-review-routing` | `use` | `<decision, repository/target, and precise reason; do not write only "Codex Security review">` |

### Security Review Decision

Complete this subsection for every task pack. Choose exactly one outcome for each affected
repository. Bot and SQL changes require separate Git targets and normally separate decisions.

| Repository | Decision | Target | Expected setup / execution | Evidence |
|---|---|---|---|---|
| `<bot | SQL | other>` | `<documented skip | Changes review | standard codebase audit | deep codebase audit | findings triage | finding remediation>` | `<files inspected; base..head; scoped folder; captured findings path; or finding ID>` | `<Not applicable | Changes + Deep Off | Codebase + Deep Off | Codebase + Deep On | triage-finding | fix-finding>` | `<precise skip reason, scan result path, stable finding IDs, tests, or pending>` |

Routing rules:

- Routine pull requests, commits, branch ranges, and working-tree changes use
  `$codex-security:security-diff-scan` when a security review is required.
- Standard or deep codebase audits require an explicit operator request for that exact audit. A task
  pack, PR gate, promotion gate, or deployment gate does not authorise one implicitly.
- Existing captured findings use findings triage without launching another discovery scan.
- Accepted findings are fixed individually, or as one tightly related root-cause family, and the
  resulting change is then reviewed with the normal diff-focused workflow.
- A documented skip must name the files inspected and explain why no runtime, configuration,
  dependency, permission, input, data-access, deployment, or persistence behaviour changed.

## 8. Mandatory Workflow

Default workflow:

1. Audit / scope review, then stop for approval.
2. Use `k98-security-review-routing` to record the provisional security decision and exact target;
   do not start a standard or deep scan merely because the routing skill was selected.
3. Architecture validation, then stop for approval.
4. Implementation plan, then stop for approval.
5. Implementation after approval.
6. Validation and final review.
7. Execute or confirm the selected security outcome against the final change. For a Changes review,
   verify the intended base/head and `Deep: Off`; for a skip, record the precise evidence-based reason.

Proceed in one pass only when the user explicitly approves it.

## 9. Audit Requirements

Review the touched area for:

- direct SQL in commands or views
- business logic in interaction layers
- duplicate helpers or near-duplicates
- dead code from prior iterations
- weak validation or logging
- cache and persistence safety
- restart safety
- test coverage gaps

Map the likely:

- commands
- services
- repositories / DAL modules
- SQL objects or contracts
- views or modals
- caches or persisted state
- restart implications
- conditional reference docs

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | `commands/<domain>_cmds.py` |
| Views / modals | `ui/views/` |
| Services / business logic | subsystem package or `<domain>_service.py` |
| Repository / DAL | subsystem package or repository module |
| Shared helpers | `core/` or existing helper modules |
| Operational tooling | `scripts/` |
| Documentation | `docs/` |
| SQL schema | SQL repo `sql_schema/<schema>.<Object>.<Type>.sql` |
| Tests | `tests/` |

## 11. Likely Files

### Review

- `<path>`

### Modify

- `<path>`

### Create

- `<path or none>`

## 12. Implementation Requirements

- Keep commands and views thin.
- Move business logic into services.
- Move data access into repository/DAL code.
- Avoid new direct SQL in commands or views.
- Reuse existing helpers where practical.
- Preserve restart safety.
- Add or improve meaningful logging where operational paths are touched.
- Add or update tests unless the change is documentation-only or tooling-only.
- Capture non-security out-of-scope debt as deferred optimisations. Route suspected vulnerabilities
  through `k98-security-review-routing`; do not downgrade them into normal optimisation debt.

### Command Surface Governance

Use this section when the task creates, moves, renames, retires, or changes any slash command,
command group, grouped subcommand, command decorator, command registration helper, or command
lifecycle/cache behavior. Delete it only when the task has no command-surface impact.

- [ ] State whether the task changes top-level command count, grouped subcommand count, or neither.
- [ ] Prefer grouped commands for admin, leadership, operator, diagnostic, and domain-maintenance
  work.
- [ ] If the task creates a new top-level command, document why an existing command group is not
  suitable, record operator approval for the flat path, update
  `scripts/validate_command_registration.py::APPROVED_TOP_LEVEL_COMMANDS`, update
  `docs/reference/canonical_command_reference.md`, update relevant user/operator docs and smoke
  references, and run command registration validation.
- [ ] If the task creates a grouped subcommand under an existing group, update the canonical
  command table and grouped summary, but do not change the approved top-level baseline.
- [ ] If the task creates a new command group, treat it as a new top-level command and complete
  the flat-path approval/baseline steps above.
- [ ] Preserve or explicitly update `@versioned()`, `@safe_command`, `@track_usage()`, permission
  decorators, response visibility, autocomplete/options, usage-log identity, and command-cache
  behavior.
- [ ] Run or justify skipping `scripts/validate_command_registration.py`,
  `tests/test_validate_command_registration.py`, `tests/test_command_inventory.py`, and
  `tests/test_command_registration_smoke.py`.

## 13. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| `<issue>` | `fix now | defer | not applicable` | `<short reason>` |

Deferred items must use the structured format from
`docs/reference/K98 Bot - Deferred Optimisation Framework.md`. Suspected or confirmed security
findings remain in the security findings workflow and must not be classified as deferred
optimisations.

Validated, accepted, or risk-accepted security findings are not deferred optimisations. Track them
in the private security findings register with their stable ID, owner, disposition, and review date.

## 14. Testing Requirements

Consider each category and either cover it or explain why it does not apply:

- happy path
- negative path
- regression
- permission boundary
- restart/persistence
- cache safety
- format/output shape

Suggested baseline commands:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
```

Add focused pytest commands for the subsystem under change. For broader or runtime changes, also
consider:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

Before PR handoff, complete the Security Review Decision table and retain the resulting evidence.
For a routine change requiring review, use the diff-focused Changes workflow against the final
base/head with `Deep: Off`. For a skip, record the files inspected and the precise reason.

## 15. Acceptance Criteria

- [ ] Scope is complete and no out-of-scope work was mixed in.
- [ ] Correct architecture/layer ownership is preserved.
- [ ] No new direct SQL exists in commands or views.
- [ ] Helper reuse was checked and documented.
- [ ] Logging is adequate for changed operational paths.
- [ ] Restart safety is preserved or explicitly not applicable.
- [ ] Tests were added/updated or a clear testing exception is documented.
- [ ] Quality gates were run or documented.
- [ ] A precise security decision and target are recorded for every affected repository.
- [ ] Any routine security scan used the Changes workflow with the intended base/head and `Deep: Off`.
- [ ] No standard or deep codebase audit was started without an explicit operator request.
- [ ] Deferred optimisations are captured structurally; security findings are tracked separately.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Helpers Reused
7. Refactor Findings
8. Test Plan
9. Security Review Decision and Evidence
10. Deployment Steps
11. Deferred Optimisations

For documentation-only work, state that no runtime code, SQL, helper reuse, or restart behaviour
changed.

## 17. PR Summary Template

```md
## Summary

- <summary item>

## Changes

- <change item>

## Tests

- <test command or verification>

## Security Review

- Decision: `<documented skip | Changes review | explicit standard codebase audit | explicit deep codebase audit | findings triage | finding remediation>`
- Repository / target: `<repository and files, base..head, scope, captured findings path, or finding ID>`
- Expected setup / execution: `<Not applicable | Changes + Deep Off | Codebase + Deep Off | Codebase + Deep On | triage-finding | fix-finding>`
- Evidence: `<precise skip reason, completed scan result, stable finding IDs, or remediation/test evidence>`

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- <risk and rollback note>
```
