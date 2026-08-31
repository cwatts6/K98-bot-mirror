# Codex Task Pack - DL_bot Offload Callable Once-Only Failure Semantics

## 1. Task Header

- Task name: `DL_bot Offload Callable Once-Only Failure Semantics`
- Date: `2026-08-30`
- Owner/context: `Chris Watts / highest-priority implementation-ready deferred optimisation`
- Task type: `bug fix | deferred optimisation`
- One-pass approved: `no`
- Status: `prepared for audit and architecture approval`
- Repository baseline reviewed: `C:\discord_file_downloader` at
  `5ca25bc9cdeb857b079d5157e20f367469d124a4` (`main`, equal to `origin/main` on 2026-08-30)

## 2. Required Reading

Before implementation, read the current versions in this order:

1. This task pack and the operator's launch request.
2. `AGENTS.md`.
3. `README-DEV.md`.
4. `docs/reference/README.md`.
5. `docs/reference/K98 Bot - Project Engineering Standards.md`.
6. `docs/reference/K98 Bot - Coding Execution Guidelines.md`.
7. `docs/reference/K98 Bot - Testing Standards.md`.
8. `docs/reference/K98 Bot - Skills & Refactor Triggers.md`.
9. `docs/reference/K98 Bot - Deferred Optimisation Framework.md`.
10. `docs/reference/deferred_optimisations.md`.
11. `docs/reference/REVIEW_HELPERS.md`.
12. `docs/reference/runbook_diagnostics.md`.
13. `docs/reference/mge_reference_model.md`.
14. Root and any applicable nested `SECURITY.md` files.

The SQL source of truth is `C:\K98-bot-SQL-Server`. This task must not change the SQL repository,
but the implementation audit must confirm that it is preserving the existing import/DAL contract
rather than inventing a SQL-side retry or deduplication assumption.

## 3. Objective

Make `DL_bot.py::_offload_callable` execute each submitted callable at most once per helper call.
If the callable begins and then raises, is cancelled, times out, or has an indeterminate dispatched
outcome, propagate that outcome without invoking the callable through another backend.

Retain fallback only for a backend that is absent or can prove it rejected the work before callable
entry. Preserve successful return values, MGE route error messaging, audit behavior, and the valid
offload preference that the reviewed backend contracts can actually support.

## 4. Background

The active deferred register identifies this as the highest-priority implementation-ready item.
Static review of the current baseline confirmed the production-relevant failure chain:

1. `upload_routes/mge_results_route.py` submits the production importer with four positional
   arguments: file bytes, source filename, uploader ID, and `MgeResultsImportAuditContext`.
2. `DL_bot.py::_offload_callable` tries three imported helpers and finally
   `asyncio.to_thread`, catching broad `Exception` around each of the first three attempts.
3. `file_utils.run_maintenance_with_isolation` has the contract
   `(command, args=None, *, kwargs=None, timeout=..., name=..., meta=..., prefer_process=...)` and
   returns an operational `(ok, output)` tuple. It is not an arbitrary `fn, *args, **kwargs`
   result-preserving adapter.
4. `file_utils.start_callable_offload` is a synchronous module/function subprocess launcher with
   the contract `(module, function, args=None, meta=None, cwd=None) -> dict`; it is not the
   awaitable callable executor assumed by `_offload_callable`.
5. For the four-positional-argument MGE shape, those incompatible attempts fail before callable
   entry. `file_utils.run_blocking_in_thread` is then the first compatible execution backend.
6. If the importer begins there and raises, `_offload_callable` swallows the exception and invokes
   it again through `asyncio.to_thread`. That can repeat parsing, audit writes, and database work
   for one Discord upload before the existing route-level error embed is sent.

This is a correctness and reliability defect. The canonical source says it was reproduced during
a security scan and calibrated as non-reportable because the demonstrated impact was repeated
failed-import work rather than a security-boundary impact. The current repository does not retain
the scan ID or harness beside the active item, so the new implementation must first reproduce the
behavior in a deterministic local regression test and must not invent missing scan metadata.

The same static review found broad catch-and-fallthrough patterns in
`stats_module.py::_offload_callable_py` and `ui/views/kvk_history_view.py::_offload_callable`.
Those are review-only in this task: their production call shapes and side effects have not been
proved equivalent to the MGE reproduction.

## 5. Scope

### In Scope

- Reproduce the four-argument MGE failure path deterministically before changing behavior.
- Define and implement an explicit once-only execution contract for
  `DL_bot.py::_offload_callable`.
- Separate backend discovery/rejection-before-entry from callable execution outcomes.
- Audit the actual signatures, return shapes, cancellation behavior, timeout behavior, process
  dispatch semantics, and telemetry of the candidate helpers in `file_utils.py`.
- Preserve callable positional and keyword arguments without mixing them with offload control
  arguments such as `name`, `meta`, and `prefer_process`.
- Preserve successful results, including any deliberately supported result-envelope normalization.
- Preserve the current MGE route success behavior and its existing failure embed/audit behavior.
- Inventory every current `DL_bot.py` direct call and every injected `upload_routes/` call shape;
  add focused coverage for materially different zero-argument, positional, keyword, and mixed
  forms where the implementation could affect them.
- Add useful, non-sensitive logging for backend selection and safe pre-entry fallback decisions.
- Update the active and resolved deferred records only after the fix and its required validation
  are complete.

### Out of Scope

- Retrying a callable after it begins, even when the callable appears idempotent.
- Introducing an `explicitly_retryable` option without a separately approved contract and use case.
- Broad redesign of `file_utils.py`, subprocess registries, maintenance jobs, worker admission,
  upload concurrency, cooldowns, or queueing.
- Fixing `stats_module.py::_offload_callable_py` or
  `ui/views/kvk_history_view.py::_offload_callable` unless separately approved after evidence.
- Rewriting upload routes, importers, parsers, audit services, DAL code, or route embeds.
- Changing SQL schema, procedures, views, indexes, transactions, permissions, or deployment order.
- Changing configuration, environment variables, dependencies, commands, permissions, assets,
  caches, schedulers, backup cadence, or any live schedule.
- Live Discord upload, production SQL, process cancellation, restart, deployment, or load testing
  without the later implementation and promotion approvals.
- Folding the separately deferred shared upload-admission/backpressure item into this fix.

## 6. Source Deferred Items

The canonical active record uses `Type: reliability`. That source classification is retained here
verbatim for traceability; this execution pack treats the work as a bug fix and does not silently
rewrite the source during planning.

### Deferred Optimisation
- Area: `DL_bot.py::_offload_callable`, `file_utils.py` callable offload backends, `upload_routes/mge_results_route.py`, importer failure tests
- Type: reliability
- Description: The same security scan reproduced a bounded correctness defect: for the production four-argument MGE importer shape, the first compatible thread backend can execute a side-effecting callable and propagate its exception, after which `_offload_callable` treats that callable exception as a backend-start failure and invokes the callable once more through `asyncio.to_thread`. The demonstrated consequence is repeated failed-import audit/parsing/database work, not a reportable security impact after policy calibration.
- Suggested Fix: Separate backend-start/transport failures from exceptions raised after callable entry, and never retry a non-idempotent callable merely because it failed. Add a focused regression test asserting one invocation when the callable raises after entry, retain coverage for genuine backend-unavailable fallback, and audit other helper call shapes before claiming they share the same behavior.
- Impact: medium
- Risk: medium
- Dependencies: Preserve current offload preference and route-level error messaging; define once-only versus explicitly retryable callable contracts; run MGE upload, offload, failure/audit, pre-commit, and full regression tests.
- Status: implementation-ready — highest priority
- Last verified: 2026-08-29

## 7. Codex Skills To Use

### Skill Decisions

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required first: resolve helper ownership, candidate backend capabilities, affected call shapes, and the approval boundary before editing runtime code. |
| `k98-discord-command-feature` | not applicable | No slash command, view, modal, interaction callback, permission, registration, or user-facing command contract changes. The existing message-upload error embed must be preserved. |
| `k98-sql-validation` | use, bounded | Confirm that no SQL object or DAL contract change is needed and that repeated SQL-side work is prevented at the caller. Do not modify or deploy the SQL repository. |
| `k98-test-selection` | use | Combine `scripts/select_tests.py` with focused MGE/offload regression coverage and a full suite because a shared runtime helper is changing. |
| `k98-deferred-optimisation-capture` | use if evidence warrants | Capture proved equivalent debt or adjacent helper problems without expanding this task. Do not classify security findings as optimisation debt. |
| `k98-pr-review` | use | Review the completed implementation diff, tests, architecture, security evidence, and deferred closure before PR handoff. |
| `k98-promotion-check` | use later | Required only after review, before mirror-to-production promotion or bot-machine deployment. No deployment is authorised by this pack. |
| `k98-security-review-routing` | use | Route the final bot diff to a Changes review because it affects uploaded-file/import, SQL-side-effect, subprocess/thread, logging, and duplicate-action boundaries. |

### Security Review Decision

| Repository | Decision | Target | Expected setup / execution | Evidence |
|---|---|---|---|---|
| Bot (`C:\discord_file_downloader`) | Changes review | Final implementation branch diff from its verified `origin/main` merge base to `HEAD` | Use `$codex-security:security-diff-scan`; confirm `Scan type: Changes`, intended base/head, and `Deep: Off`; do not broaden to Codebase | Retain scan manifest/findings/coverage output, final disposition, focused once-only tests, and `validate_codex_security_routing.py` result |

The SQL repository is not an affected Git target because this task permits no SQL file or runtime
SQL contract change. If implementation discovers that SQL changes are required, stop and obtain a
separate SQL scope, task pack decision, Git target, validation plan, and security decision.

## 8. Mandatory Workflow

One-pass implementation is not approved. Use these checkpoints:

1. Audit the baseline, reproduce the defect in a deterministic test, inventory all call shapes,
   and present the scope report below. Stop for operator approval.
2. Present an architecture decision that identifies exactly which backend contracts are valid for
   arbitrary callable execution and result propagation. Stop for operator approval.
3. Present a minimal implementation/test plan and intended file manifest. Stop for operator
   approval.
4. Implement only after approval.
5. Run focused tests and deterministic validators, then the full regression/pre-commit gates.
6. Use `k98-pr-review` on the completed diff and address in-scope findings.
7. Run the routed Changes security review against the final base/head with `Deep: Off`.
8. Only after the behavior and validation are complete, remove the item from the active deferred
   register and append a factual resolved-history entry with exact evidence.
9. Stop before production promotion. Promotion and live smoke require a separate approval and
   `k98-promotion-check`.

### Required First Response

```markdown
**Scope Summary**
[State the exact defect, affected layers, and locked exclusions.]

**Reproduction Evidence**
[Report the deterministic four-argument invocation count and exception outcome before any fix.]

**Backend Contract Audit**
[List actual signatures, awaitability, result shapes, pre-entry rejection signals, and post-dispatch ambiguity.]

**Call-Shape / Side-Effect Map**
[Map all direct and injected DL_bot consumers by zero/positional/keyword/mixed arguments and side effects.]

**Architecture Decision Needed**
[Propose the minimum safe ownership and backend-selection design; do not implement yet.]

**Test Selection**
[Give selector output plus focused, full-suite, smoke, logging, and security-focused additions.]

**Security Review Decision**
[Record the Bot Changes review, exact intended target, Changes plus Deep Off, and SQL repo exclusion.]

**Open Questions / Approval Needed**
[List only decisions that cannot be established from repository evidence.]
```

## 9. Audit Requirements

Review these current boundaries before implementation:

- `DL_bot.py::_offload_callable`, its local imports, exception handling, and result normalization.
- `file_utils.py::run_maintenance_with_isolation` and its subprocess/thread branches.
- `file_utils.py::run_maintenance_subprocess` for dispatch, result, timeout, and failure semantics.
- `file_utils.py::start_callable_offload` and `scripts/callable_worker.py` for its actual synchronous
  launcher contract; do not assume it is awaitable.
- `file_utils.py::run_blocking_in_thread` for callable entry, timeout, cancellation, exception, and
  telemetry behavior.
- `upload_routes/mge_results_route.py` and
  `tests/test_mge_results_upload_route.py` for the four-argument importer and existing error embed.
- All `DL_bot.py` dependency injection sites and all `upload_routes/*_route.py` calls listed below.
- Nearby helpers in `stats_module.py` and `ui/views/kvk_history_view.py` only to decide whether a
  new structured deferred item is evidenced.
- Existing tests for offloads, maintenance helpers, MGE auto import, MGE import service, every
  affected upload route, shutdown markers, and SQL preflight behavior.

### Current Call-Shape Map To Revalidate

| Consumer | Current shape | Side-effect concern |
|---|---|---|
| `ensure_sql_headroom_or_notify` | four positional SQL connection values | SQL read/preflight; secrets must never enter logs |
| `trigger_log_backup_background` | zero callable arguments | operational backup trigger |
| `_write_shutdown_markers` | zero arguments, local closure, process preference off | two filesystem marker writes |
| MGE results route | four positional arguments | parsing, durable import audit, SQL writes |
| Honor route | one positional parse; one positional plus keywords ingest | parsing, audit, SQL writes |
| Player Location route | one positional argument | staging replacement and audit/SQL writes |
| Rally Forts route | one positional path argument | workbook import, audit, SQL writes |
| PreKvK route | two positional plus keyword arguments | workbook import, audit, SQL writes |
| KVK_ALL route | keyword-only importer arguments | workbook import, audit, SQL writes and credentials |
| Weekly Activity route | keyword-only importer arguments | workbook import, audit, SQL writes and credentials |

Also audit for direct SQL in interaction modules, mixed business/interaction logic, duplicate or
near-duplicate helpers, dead fallback branches, swallowed exceptions, sensitive telemetry,
restart implications, and gaps between test fakes and the real injected helper. Do not broaden the
fix merely because adjacent debt exists.

## 10. Architecture Targets

The core state machine is:

| Backend/callable state | Required behavior |
|---|---|
| Backend missing or not selected | Select the next compatible backend before invocation |
| Backend explicitly rejects before callable entry | A typed/structured pre-entry fallback may select the next backend |
| Callable entered and returned | Return the original result exactly once |
| Callable entered and raised | Propagate the original exception; never invoke another backend |
| Work dispatched but entry/outcome is uncertain | Treat as possibly executed; propagate/fail without retry |
| Cancellation or timeout after dispatch/entry | Propagate; never start duplicate work |

Architecture requirements:

- Select a compatible backend before calling the submitted function. A broad caught exception is
  not proof that callable entry did not occur.
- Do not use `TypeError`, `RuntimeError`, or another ordinary callable exception as an implicit
  backend-unavailable signal.
- If a backend needs a distinct pre-entry rejection signal, make it narrow, explicit, and tested.
- Do not await a synchronous launcher or pass arbitrary callable objects to a module/function API.
- Do not use an operational `(ok, output)` runner where callers require the submitted function's
  original arbitrary result unless an explicit adapter proves the complete contract.
- Prefer the smallest compliant ownership. Do not add another generic helper if a corrected
  existing boundary can own the contract. If logic is extracted from legacy `DL_bot.py`, use a
  narrow existing shared-helper location (`core/` or `file_utils.py`) and leave a stable adapter for
  route dependency injection.
- Keep callable arguments separate from offload-control metadata and do not log file contents,
  passwords, connection strings, tokens, or full sensitive argument representations.
- No persisted state or restart contract is added. The correction must reduce duplicate side
  effects without changing queue, scheduler, or rehydration behavior.

## 11. Likely Files

### Review

- `DL_bot.py`
- `file_utils.py`
- `scripts/callable_worker.py`
- `upload_routes/mge_results_route.py`
- `upload_routes/honor_route.py`
- `upload_routes/player_location_route.py`
- `upload_routes/rally_forts_route.py`
- `upload_routes/prekvk_route.py`
- `upload_routes/kvk_all_route.py`
- `upload_routes/weekly_activity_route.py`
- `stats_module.py`
- `ui/views/kvk_history_view.py`
- `tests/test_offload_callable_integration.py`
- `tests/test_maintenance_suite.py`
- `tests/test_dl_bot_mge_auto_import.py`
- `tests/test_mge_results_upload_route.py`
- `tests/test_mge_results_import_service.py`
- affected upload-route tests
- `docs/reference/deferred_optimisations.md`
- `docs/reference/archive/deferred_optimisations_resolved.md`

### Modify

- `DL_bot.py`
- `file_utils.py` only if the approved design requires a narrow backend contract correction
- focused tests selected after the audit
- `docs/reference/deferred_optimisations.md` after validated completion
- `docs/reference/archive/deferred_optimisations_resolved.md` after validated completion
- operational/reference docs only if the public helper contract or diagnostics actually changes

### Create

- Prefer `tests/test_dl_bot_offload_callable.py` for isolated behavior if it avoids mixing the
  contract into route-only tests; otherwise extend the closest existing test module and explain why.
- No SQL, migration, config, dependency, asset, cache, scheduler, or command file.

## 12. Implementation Requirements

- Preserve the submitted callable's exact successful result and exception semantics.
- Preserve `name`, `meta`, and the valid meaning of `prefer_process` without forwarding control
  fields as callable keyword arguments.
- Treat non-idempotent once-only execution as the default and only contract for this task.
- Prove a backend is capable of the submitted call shape and arbitrary result contract before
  choosing it. Capability selection must occur before callable execution.
- Allow fallback for missing imports or explicit pre-entry rejection only.
- Re-raise `asyncio.CancelledError`; never convert it to fallback.
- Treat timeouts and transport loss after work may have been dispatched as indeterminate execution,
  not safe retry.
- Remove silent broad catch-and-fallthrough behavior from the execution path. Log only useful
  backend-selection/pre-entry fallback context at an appropriate level.
- Preserve the MGE importer's four positional arguments, audit context, route success result, and
  existing failure embed. One upload must cause at most one importer invocation.
- Preserve all other current direct/injected call shapes or stop and report a verified incompatible
  consumer rather than guessing.
- Do not use SQL deduplication, audit uniqueness, or importer idempotence as a substitute for the
  caller-side once-only guarantee.
- Do not introduce direct SQL, Discord command/view business logic, or new process-management
  responsibilities.
- Capture proved adjacent non-security debt structurally. Route suspected security findings through
  the security workflow, not the deferred optimisation register.

This task has no command-surface impact: top-level and grouped command counts, registration,
decorators, permissions, visibility, autocomplete, usage identity, command cache, and resync
behavior all remain unchanged.

## 13. Refactor Decisions

| Issue | Decision | Reason |
|---|---|---|
| Broad catches treat callable failures as backend-start failures in `DL_bot.py::_offload_callable` | fix now | This is the reproduced root defect and approved scope. |
| Incompatible assumptions about `run_maintenance_with_isolation` and `start_callable_offload` | fix now, narrowly | Backend selection cannot be safe until the real signatures, awaitability, and result semantics are respected. Do not redesign unrelated maintenance/process APIs. |
| Ownership of any new state/exception contract | decide at architecture checkpoint | Prefer an existing shared boundary and avoid expanding legacy `DL_bot.py` or adding a near-duplicate helper. |
| Similar catch/fallthrough in `stats_module.py` and `ui/views/kvk_history_view.py` | review, then defer unless separately approved | Static similarity is not proof of the same production side-effect path. Capture evidence precisely if found. |
| Shared upload admission/backpressure | defer | It is a separate evidence/design-gated item with different concurrency and operational risks. |
| Route/importer, audit, DAL, or SQL redesign | not applicable | Once-only orchestration must preserve those contracts. |

## 14. Testing Requirements

### Required Behavioral Coverage

- Regression: use the production four-positional-argument shape; increment an invocation counter,
  raise a sentinel exception after callable entry, assert invocation count is exactly one, assert
  the original exception propagates, and assert no later backend executes it.
- Genuine unavailable backend: prove a missing or explicit pre-entry-rejected preferred backend
  selects one compatible fallback and the callable runs exactly once.
- Happy path: assert a compatible backend returns the callable's original scalar, mapping, tuple,
  or representative importer result without duplicate execution.
- Argument integrity: cover zero-argument, positional, keyword-only, and mixed argument shapes when
  the approved design has different adapter paths.
- Cancellation: assert cancellation propagates and no fallback invocation occurs.
- Timeout/indeterminate dispatch: if the selected adapter can time out after dispatch, assert no
  second invocation is started.
- Backend contract: assert the sync `start_callable_offload` launcher is not awaited as an arbitrary
  callable executor and `run_maintenance_with_isolation` is not used with an invalid signature or
  result contract.
- Route negative path: retain the existing MGE failure embed and no-success/no-backup behavior while
  adding an assertion tied to the real once-only helper boundary where practical.
- Logging: assert useful fallback classification without sensitive callable arguments or SQL
  credentials when new logging is added.
- Existing consumers: run focused upload-route and direct-helper tests selected from the call map.

Permission, cache, and persisted-state tests are not applicable because those contracts must not
change. Restart behavior needs no new state test, but smoke/import validation must confirm startup
imports remain healthy. Command-registration validation remains a deterministic no-drift gate.

### Test Selection

`scripts/select_tests.py` does not currently have a dedicated `DL_bot.py`/`file_utils.py` path
mapping. Because a new or modified test file triggers the selector's full-suite recommendation and
the shared helper feeds multiple upload routes, risk-based selection must add focused tests first
and then the full suite.

Run from the repository root, in this order (adjust only the focused filename if the audit chooses
a different test location):

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_dl_bot_offload_callable.py tests\test_mge_results_upload_route.py tests\test_dl_bot_mge_auto_import.py tests\test_offload_callable_integration.py tests\test_maintenance_suite.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_honor_upload_route.py tests\test_player_location_upload_route.py tests\test_rally_forts_upload_route.py tests\test_prekvk_upload_route.py tests\test_kvk_all_upload_route.py tests\test_weekly_activity_upload_route.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
.\.venv\Scripts\python.exe -m pre_commit run -a
git diff --check
```

If the focused test is added to an existing module, substitute that exact path. Do not omit the
full suite solely because focused tests pass: this is a shared helper with multiple SQL-writing and
filesystem-writing consumers. Fix task-related failures only; document unrelated failures without
expanding scope.

Manual/live validation is deferred to promotion. No production attachment upload, SQL write,
backup trigger, shutdown-marker write, restart, resync, process cancellation, or concurrent load
test is authorised during local implementation.

## 15. Acceptance Criteria

- [ ] The pre-fix four-argument MGE reproduction proves the duplicate invocation deterministically.
- [ ] The final once-only contract distinguishes pre-entry rejection from post-entry or
      indeterminate outcomes.
- [ ] A callable that begins and raises is invoked exactly once and its original exception reaches
      the route/caller.
- [ ] Cancellation, timeout, and indeterminate post-dispatch failure cannot start duplicate work.
- [ ] Genuine missing/pre-entry-unavailable backend fallback still works and invokes the callable
      exactly once.
- [ ] The current helper signatures, awaitability, and result contracts are used accurately.
- [ ] Successful callable result shapes and every affected current call shape are preserved.
- [ ] MGE success behavior, failure embed, audit context, and backup scheduling behavior are
      preserved except that failed importer work cannot repeat.
- [ ] No secrets, file contents, or SQL credentials are added to logs or telemetry.
- [ ] No command, permission, SQL, config, dependency, asset, cache, scheduler, or live schedule
      change is mixed in.
- [ ] Focused tests, full pytest, log-noise analysis, smoke imports, command registration, required
      validators, full pre-commit, and `git diff --check` pass or have precise unrelated failures.
- [ ] `k98-pr-review` finds no unresolved merge blocker.
- [ ] The final bot diff receives a Changes security review with the intended base/head and
      `Deep: Off`; no routine standard or deep codebase audit is started.
- [ ] Equivalent adjacent helper debt is fixed only with approval or captured structurally with
      evidence.
- [ ] After validated completion, the active deferred item is removed and an exact resolved-history
      entry records the implementation and validation.

## 16. Required Delivery Output

Return:

1. Summary of the once-only contract and corrected behavior.
2. Exact changed-file manifest, separated into new and modified files.
3. Pre-fix reproduction and post-fix invocation-count evidence.
4. Backend contract/selection decision and helpers reused.
5. Call-shape audit results for all direct and injected `DL_bot` consumers.
6. SQL changes: explicitly `none`, unless the task stopped for a separate scope.
7. Refactor findings: fixed, deferred, or not applicable.
8. Exact validation output, including focused/full pytest counts and any skips/failures.
9. Security Review Decision and retained Changes-review evidence.
10. Deferred-register removal and resolved-history addition, or why closure is not yet justified.
11. Deployment steps and rollback notes, while making clear deployment was not performed.
12. Any source statement that could not be verified without guessing.

## 17. PR Summary Template

```md
## Summary

- Enforce once-only execution for `DL_bot.py::_offload_callable` after callable entry or dispatch.
- Preserve safe pre-entry backend fallback and existing upload-route results/error behavior.

## Changes

- Select only a contract-compatible backend before invocation.
- Propagate callable, cancellation, timeout, and indeterminate dispatch outcomes without retry.
- Add deterministic regression and compatibility coverage.
- Close the active deferred item only after validation.

## Tests

- `[focused commands and results]`
- `python -m pytest -q tests`: `[result]`
- `python -m pre_commit run -a`: `[result]`
- `[validators, smoke imports, command registration, log-noise analysis, and diff-check results]`

## Security Review

- Decision: `Changes review`
- Repository / target: `C:\discord_file_downloader; [verified base]..[head]`
- Expected setup / execution: `Changes + Deep Off`
- Evidence: `[scan result path/ID and finding disposition]`

## Deferred Optimisations

- `[resolved item movement and any separately captured adjacent evidence, or none]`

## Risk / Rollback

- Primary risk is accidental loss of a genuinely safe pre-entry fallback or result-shape drift
  across another upload consumer.
- Roll back the bot commit through the normal reviewed production process; no SQL/config/data
  rollback is required because this PR changes none of those surfaces.
```
