# K98 Bot — Testing Standards

> **Purpose:** Define the minimum testing expectations for AI-generated and human-authored changes in the K98 bot project.

---

## 1. Principles

Testing in this project is not only about proving the happy path.

A good test strategy should:

- confirm the intended behaviour
- prevent regressions in the exact area changed
- cover failure modes that matter operationally
- protect permission boundaries
- protect restart/persistence behaviour where state is involved

Tests should be proportionate to change size, but every meaningful production change requires a deliberate test decision.

---

## 2. Minimum Test Expectations by Change Type

### 2.1 Bug fix

Expected:

- one regression test that reproduces the previous failure or bad behaviour
- one happy path test showing the corrected behaviour
- one negative-path test if validation or failure handling is involved

### 2.2 New service logic

Expected:

- happy path coverage
- validation failure coverage
- edge case coverage
- repository interaction behaviour where relevant

### 2.3 New or changed command

Expected:

- permission boundary test where relevant
- argument validation behaviour
- service handoff or command output behaviour
- at least one negative path

### 2.4 New or changed view/modal flow

Expected:

- interaction safety behaviour where practical
- service invocation path
- negative-path or rejection behaviour
- rehydration or persistence coverage if the view is persistent

### 2.5 Scheduler, reminders, or restart-sensitive state

Expected:

- restart/persistence coverage
- deduplication behaviour where applicable
- cancellation or recovery behaviour where applicable
- negative path for missing or stale persisted state

### 2.6 SQL-backed cache or JSON cache refresh logic

Expected:

- valid payload path
- empty/invalid payload protection
- atomic write / replace behaviour where applicable
- stale cache fallback or protection path where applicable

---

## 3. Required Test Categories

For most non-trivial changes, consider these categories explicitly:

- **happy path**
- **negative path**
- **regression**
- **permission boundary**
- **restart/persistence**
- **cache safety**
- **format/output shape**
- **logging-critical behaviour** when a bug depended on observability

Not every category applies every time, but each should be considered and either covered or explicitly ruled out.

---

## 4. Test Placement

- place tests in `tests/`
- use `test_<module_or_feature>.py`
- keep tests close to the subsystem naming where practical
- extend existing subsystem test files when it improves discoverability
- create a new test file when the feature is distinct enough to justify it

Examples:

- `tests/test_registry_service.py`
- `tests/test_mge_awards_service.py`
- `tests/test_command_usage_cmds.py`

---

## 5. What Must Be Updated When Refactoring

If a refactor changes:

- file boundaries
- service ownership
- command/service responsibilities
- validation behaviour
- persistence contracts
- output formatting that tests assert against

then existing tests must be reviewed and updated, not simply left to fail or bypassed.

Refactor work is incomplete if the tests still describe the previous architecture.

---

## 6. Testing Rules for AI-Generated Changes

When an AI coding agent produces code, it must also produce or update tests unless one of these is true:

- the change is documentation-only
- the change is purely comment-only
- the environment makes the specific automated test impossible and that limitation is stated explicitly

“Too small to test” should be rare.

---

## 7. Suggested Test Matrix

Use this as a default checklist.

| Change type | Happy path | Negative path | Regression | Permission | Restart/Persistence |
|------------|------------|---------------|-----------|------------|---------------------|
| Bug fix | Yes | Usually | Yes | If relevant | If relevant |
| Service change | Yes | Yes | Usually | If relevant | If relevant |
| Command change | Yes | Yes | Usually | Yes if relevant | Sometimes |
| View change | Yes | Yes | Usually | Sometimes | Yes if persistent |
| Scheduler/reminder | Yes | Yes | Yes | Sometimes | Yes |
| Cache refresh | Yes | Yes | Usually | No | Often |

---

## 8. Quality Gates

Run or recommend these from repo root:

```bash
python -m black --check .
python -m ruff check .
python -m pyright
python -m pytest -q
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
```

For targeted work, also run the most relevant focused test commands where practical, for example:

```bash
python -m pytest tests/test_registry_service.py -q
python -m pytest tests/test_command_usage_cmds.py -q
```

---

## 9. Assertions to Prefer

Prefer tests that assert:

- behaviour
- returned values
- persisted state transitions
- service calls
- message/view identifiers
- user-visible outcomes
- protection against invalid or empty data

Avoid over-coupling tests to incidental implementation details unless the architecture contract itself is what matters.

---

## 10. Common Gaps to Avoid

Do not ship changes with only:

- smoke import coverage
- manual testing claims
- happy path tests only
- no regression test for a known bug
- no test update after moving logic between layers
- no restart-safe test for persistent workflows

---

## 11. Delivery Expectations

When presenting a task pack or implementation, include a short test plan listing:

- new tests to add
- existing tests to update
- focused pytest commands to run
- any manual verification still required
- any area not automatically testable and why

---

## 12. Definition of Test-Ready

A change is test-ready when:

- [ ] the changed behaviour is covered
- [ ] the main failure path is covered
- [ ] regression risk is addressed
- [ ] permission or restart concerns are covered when relevant
- [ ] existing related tests were reviewed
- [ ] focused and general validation commands are identified
