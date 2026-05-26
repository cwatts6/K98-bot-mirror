# K98 Bot - Testing Standards

> Canonical repo copy: `docs/reference/K98 Bot - Testing Standards.md`.

## 1. Principles

Testing in this project is not only about proving the happy path. A good test strategy should:

- confirm the intended behaviour
- prevent regressions in the exact area changed
- cover operationally important failure modes
- protect permission boundaries
- protect restart/persistence behaviour where state is involved

Tests should be proportionate to change size, but every meaningful production change requires a
deliberate test decision.

## 2. Minimum Expectations By Change Type

### Bug Fix

Expected:

- one regression test that reproduces the previous failure or bad behaviour
- one happy path test showing the corrected behaviour
- one negative-path test if validation or failure handling is involved

### New Service Logic

Expected:

- happy path coverage
- validation failure coverage
- edge case coverage
- repository interaction behaviour where relevant

### New Or Changed Command

Expected:

- permission boundary test where relevant
- argument validation behaviour
- service handoff or command output behaviour
- at least one negative path

### New Or Changed View/Modal Flow

Expected:

- interaction safety behaviour where practical
- service invocation path
- negative-path or rejection behaviour
- rehydration or persistence coverage if the view is persistent

### Scheduler, Reminders, Or Restart-Sensitive State

Expected:

- restart/persistence coverage
- deduplication behaviour where applicable
- cancellation or recovery behaviour where applicable
- negative path for missing or stale persisted state

### SQL-Backed Cache Or JSON Cache Refresh Logic

Expected:

- valid payload path
- empty/invalid payload protection
- atomic write / replace behaviour where applicable
- stale cache fallback or protection path where applicable

## 3. Required Test Categories

For most non-trivial changes, consider these categories explicitly:

- happy path
- negative path
- regression
- permission boundary
- restart/persistence
- cache safety
- format/output shape
- logging-critical behaviour when a bug depended on observability

Not every category applies every time, but each should be considered and either covered or
explicitly ruled out.

## 4. Test Placement

- Place tests in `tests/`.
- Use `test_<module_or_feature>.py`.
- Keep tests close to subsystem naming where practical.
- Extend existing subsystem test files when that improves discoverability.
- Create a new test file when the feature is distinct enough to justify it.

Examples:

- `tests/test_registry_service.py`
- `tests/test_mge_awards_service.py`
- `tests/test_command_usage_cmds.py`

## 5. What Must Be Updated When Refactoring

If a refactor changes any of these, existing tests must be reviewed and updated:

- file boundaries
- service ownership
- command/service responsibilities
- validation behaviour
- persistence contracts
- output formatting that tests assert against

Refactor work is incomplete if tests still describe the previous architecture.

## 6. Testing Rules For AI-Generated Changes

When an AI coding agent produces code, it must also produce or update tests unless one of these is
true:

- the change is documentation-only
- the change is purely comment-only
- the environment makes the specific automated test impossible and that limitation is stated
  explicitly

"Too small to test" should be rare.

## 7. Suggested Test Matrix

| Change type | Happy path | Negative path | Regression | Permission | Restart/Persistence |
|------------|------------|---------------|------------|------------|---------------------|
| Bug fix | Yes | Usually | Yes | If relevant | If relevant |
| Service change | Yes | Yes | Usually | If relevant | If relevant |
| Command change | Yes | Yes | Usually | Yes if relevant | Sometimes |
| View change | Yes | Yes | Usually | Sometimes | Yes if persistent |
| Scheduler/reminder | Yes | Yes | Yes | Sometimes | Yes |
| Cache refresh | Yes | Yes | Usually | No | Often |
| Documentation-only | No runtime test required | No runtime test required | No runtime test required | No | No |

## 8. Quality Gates

Run or recommend these from repo root:

```powershell
python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/select_tests.py
python -m pytest -q tests
python scripts/analyse_pytest_log_noise.py
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
```

Normal pytest runs are isolated from production operational logs. Expected negative-path logging
must remain assertable with `caplog` or pytest's captured output, but tests must not write to
`logs/log.txt`, `logs/error_log.txt`, `logs/crash.log`, or `logs/telemetry_log.jsonl`. When a
reviewable pytest log artifact is needed, explicitly tee the pytest command to a non-production
audit file such as `.codex_pytest_audit.log`.

Run `python scripts/analyse_pytest_log_noise.py` for broad validation or deployment review when
log hygiene matters. The script runs pytest with the test-mode logging boundary enabled and fails
if production operational log files change.

For targeted work, also run the most relevant focused test commands where practical, for example:

```powershell
python -m pytest tests/test_registry_service.py -q
python -m pytest tests/test_command_usage_cmds.py -q
```

For documentation-only changes, the architecture/deferred/test-selector scripts are usually the
minimum useful gate. Runtime pytest may be skipped when no code or test files changed, but the skip
must be stated.

The AI-assisted security review gate is separate from tests, but should be considered before PR
handoff:

- Run or justify skipping Codex Security review when the change touches permissions, Discord
  interactions, SQL/data access, file handling, secrets/config, deployment, network calls,
  user-controlled input, or restart-sensitive persistence.

## 9. Assertions To Prefer

Prefer tests that assert:

- behaviour
- returned values
- persisted state transitions
- service calls
- message/view identifiers
- user-visible outcomes
- protection against invalid or empty data

Avoid over-coupling tests to incidental implementation details unless the architecture contract
itself is what matters.

## 10. Common Gaps To Avoid

Do not ship changes with only:

- smoke import coverage for behavioural changes
- manual testing claims
- happy path tests only
- no regression test for a known bug
- no test update after moving logic between layers
- no restart-safe test for persistent workflows

## 11. Delivery Expectations

When presenting a task pack or implementation, include a short test plan listing:

- new tests to add
- existing tests to update
- focused pytest commands to run
- any manual verification still required
- any area not automatically testable and why

## 12. Definition Of Test-Ready

A change is test-ready when:

- [ ] the changed behaviour is covered
- [ ] the main failure path is covered
- [ ] regression risk is addressed
- [ ] permission or restart concerns are covered when relevant
- [ ] existing related tests were reviewed
- [ ] focused and general validation commands are identified
- [ ] documentation-only skips are explicitly justified
- [ ] Codex Security review decision is documented before PR handoff
