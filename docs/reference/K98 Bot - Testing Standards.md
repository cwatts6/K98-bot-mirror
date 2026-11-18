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

### SQL query inventory regression (P02, 2026-11-17)

Run `python scripts/validate_sql_aliases.py` for SQL-bearing changes. The pre-commit
hook and ordinary pytest regression discover tracked and untracked Python,
PowerShell and SQL source; they do not maintain a list of yesterday's affected
files. This lexical guard catches the known reserved-identifier family, including
bare `RowCount` columns. It is not a general SQL Server grammar test.

Grouped P02 packet preparation also requires `scripts/p02_sql_inventory.py` and
the local Microsoft ScriptDom parser through `scripts/Test-P02SqlGrammar.ps1`.
Static queries at execution interfaces are discovered automatically. New dynamic
lab expressions require a reviewed materializer; SQL-like literals through other
wrappers and new SQL in host/guest orchestration must not bypass the inventory.
Test new files, concatenation, f-strings, leading comments, CTEs, and failure/final
accounting branches. Check generated SQL with an independent parser rather than
only asserting text also written by the implementation. A missing parser blocks
packet preparation; it must not become a successful skip.

Keep complete-batch grammar results separate from forwarding sites, retained
dynamic SQL evidence, header/assembly fragments, schema validation and native
execution. Preserve the actual inventory, tooling and hashes with the packet.
See the [SQL inventory correction review](../task_packs/P02%20-%20SQL%20Inventory%20Correction%20Review%20-%202026-11-17.md).

### Catalogue collation regression (P02, 2026-11-17)

A valid SQL parse and a mocked cursor result do not prove that SQL Server can bind
the query against the actual server and database collations. Restored preparation
v1 failed with error 451 because it combined server and database principal names
with UNION ALL. For existence checks, prefer EXISTS with a numeric result over
combining text that the caller never uses. Do not change database collation to
make a diagnostic query pass.

The packet SQL inventory now invokes `scripts/p02_sql_collation.py` automatically.
Set operations involving distinct sys catalogue sources require an exact-query
review in `scripts/p02_sql_collation_reviews.json`; additions and text changes
cannot inherit a previous review. This is a conservative offline review trigger,
including sys.databases and explicit master references, not a general SQL type
checker. Whole-batch false positives need a concrete explanation of why no text
crosses catalogue boundaries. It is not a new runtime or production guard.

Retain tests using the actual failed query, newly discovered helper files,
UNION/UNION ALL/INTERSECT/EXCEPT, quoted identifiers, comments, parser-only callers
and invalidated review hashes. Separately record native binding, schema and
permission evidence; never label syntax success as native compatibility proof.

### Installed updater dependency regression (P02 D6)

Test sealed verifier imports against an application root that lacks newly added
dependencies, as well as one containing older versions. Using the developer's
current checkout as the only application root can hide a broken updater package.
`tests/test_installed_verifier_archive.py` imports the complete sealed inventory
in an isolated Python process and exercises the lazy SQL custody dependency with
a fake connection. It also checks that configuration and credential readers keep
the real installed application root and that unbundled services cannot fall back.

Before host handoff, additionally rehearse the actual combined-release preparation
against the exact authenticated predecessor and proposed target, using saved
observations and acquired source files offline. An early deliberately invalid
commit test or successful import alone is not proof that preparation completes.
Retain the failing receipt separately, record the generated package hashes and
unchanged SQL/startup contracts, and never use a live restart or import/export as
a packaging test.

Count the **complete generated release**, including support files and each
non-deleted source payload, rather than only source changes or runtime pins.
The v4 fixed-adapter limit is 526 members; generic packets remain at 128 and the
independent manifest limit remains 64 KiB. `tests/test_prepare_k98_release.py`
checks the Python validator and extracted native PowerShell count guard at and
beyond their limits. Registry entries (90) and transition-family members (80)
are separate limits and do not establish that the release package fits.

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

## 13. Windows custody and deployment validation

For protected filesystem/updater changes, cover production-like inheritance/default ownership, metadata, partial-stage resume, interrupted replacement, prior handles and negative ACL/link/stream/inventory cases. Verify preservation of originals. Distinguish parser checks, surrogate-account fixtures, elevated rehearsal and production receipts. Documentation-only work needs link/content and documentation gates without replaying deployment or provider activity.

The [Windows ownership and access contract](Windows%20ownership%20and%20access%20contract.md)
is required reading for this work and defines the operation matrix and validation details.

For a test runner that changes Windows identity, test the complete dependency
access path: working/source directories, dependency environment, required native
modules and actual imports. Development-account imports and substituted identity
APIs prove packaging only. An actual restricted child must establish access before
fixture/data installation; an administrator's successful probe is not equivalent.
Offline regressions should cover a dependency tree readable by an older account
but not the new actor, preservation of existing ACLs/ownership, read-only grants,
and failure diagnostics containing the exact safe path, operation and OS code
without credentials. Keep real-account proof explicitly pending until observed.
Use reusable lab fixtures and recorded attempts; do not infer that every setup
failure requires production-style recovery machinery or new infrastructure.

### Installation evidence must match the environment

Production deployment-history rows and separate lab qualification receipts are
different evidence types. Before introducing an acceptance guard, trace its
expected facts to the actual environment's installation path and retained
evidence. A lab that ran reviewed SQL directly must not be required to possess
deployment-history rows its installer never writes. Do not fabricate those rows
or weaken the independent schema, permission or ownership checks to compensate.

Regression coverage must include a hash-pinned retained-history case, not only a
success fixture that repeats the new guard's assumptions. Test missing production
history with valid lab lineage, invalid lineage, and incorrect current object
definitions independently. Production history requirements remain unchanged.
Receipt tests must distinguish completed actions from later verification failure
and connection disposition, so a failed check cannot imply that a committed
restore or other completed action should be repeated.

Exercise that distinction through every downstream verifier, including the fresh
process and sealed archive used by the final check. A baseline-only test cannot
prove that a later production-history guard accepts an approved lab installation.
`tests/test_p02_lab_evidence_verifier.py` replays all three contract comparisons
against pinned retained evidence and tests each legacy observation category
independently. Actual observations must remain unmodified; any lab-only projection
belongs in the independently validated expectation. Confirm the production
verifier still rejects missing production receipts. Save observations before
comparison and include safe mismatch categories in failure receipts.

### Shared SQL helpers must cover transaction state

For transaction-sensitive SQL functions, test both zero and nonzero server
transaction counts independently of the driver's autocommit setting. Manual
commit mode does not prove that a transaction is active. Review every caller,
including startup/updater verification and business cursors borrowed by import,
reporting and recovery paths. Do not start a transaction in a wrapper merely to
hide an invalid shared-helper precondition.

For `schema_observation`, preserve caller transaction count, isolation and
existing locks. Model SQL3918 for an unconditional transaction-owned
`APPLOCK_MODE` call without a transaction; verify the original query fails that
model. Cover refusal of session/transaction-owned locks and unknown acquisition
or release. The caller inventory test must flag new direct helper/contract/
producer entry points for review. Query discovery and grammar checks are useful
but do not establish engine semantics. A prepared native probe must execute the
real shared helper in both states on its own connection and record before,
inside and after state; keep native acceptance pending until receipts pass.
Tests: `test_application_schema_transaction_states.py` and
`test_p02_transaction_probe.py`.

### Retained evidence and maintenance controls

Replay real retained observations through the same scalar encoding used by the
receipt writer before comparing SQL values to saved JSON. Include dates,
datetimes, decimals and bytes; prove that real value changes still fail. Keep raw
SQL observations for comparisons within a single run. An all-string fixture
cannot detect a native SQL date versus JSON string mismatch.

Before holding an artificial blocker for a maintenance test, inspect the actual
worker's access order and lock timeout. A worker that touches the blocked table
before acquiring its schema guard may fail before the intended assertion. Use
the exact guard as a deterministic refusal control and run the real worker after
acknowledged release when that is the reviewed claim; do not describe those
separate checks as proof of simultaneous worker/observer overlap. Check process
receipt labels against the actual connection mode as well as child exit status.
Coverage: `test_p02_restored_qualification.py`, including retained preflight/final
replay, exact packet imports and native PowerShell flow with effects replaced.

### Complete evidence transport, not only individual cases

Exercise the actual orchestration return through the actual completion emitter
with production-sized retained observations. Passing each case receipt does not
prove that an aggregate completion message fits the transport limit. Keep full
evidence once and return a compact manifest of event/occurrence references;
the host inventory hashes bind the saved bytes. Do not hash a Python value and
assume it matches a PowerShell-reserialized receipt (float precision and escaping
can differ). Failed emissions must not create successful references.

Test one byte below, at and above the unchanged receipt byte limit, plus the real
retained oversized aggregate. Parent protocol tests with tiny synthetic values
are useful for sequencing but do not cover payload size. Completion-only packets
must prove that invalid retained pins or child identity stop before retirement,
and that failed retirement or verification cannot reach later checks. Preserve
completed case receipts and do not replay business writes to recover a summary.
Coverage: `test_p02_completion_receipts.py` and `test_p02_completion_packet.py`.
