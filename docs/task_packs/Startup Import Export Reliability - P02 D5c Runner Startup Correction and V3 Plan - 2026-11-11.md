# P02 D5c runner startup correction and V3 plan - 2026-11-11

Status: **broader startup review and test-runner correction prepared. V3 has
not been imported, collected or executed. Another pass requires approval.**

This follows the [V2 findings](Startup%20Import%20Export%20Reliability%20-%20P02%20D5c%20Corrected%20Offline%20Pass%20Findings%20-%202026-11-11.md).
Both failed attempts, the original test bytes, current tests and runtime source
remain unchanged. D5c is still unqualified: 418 cases are planned, zero have run.
The 21-input allowance remains consumed and 1,480 native seconds remain.

## Broader source review

The review covered interpreter startup, pytest configuration and plugin loading,
collection imports, selected fixtures, output writers, error handling and exit.
It used installed source and AST inspection, with no pytest startup probe,
collection-only invocation, application import, SQL connection or VM operation.

| Startup surface | Source finding and correction |
| --- | --- |
| Python site initialization | The environment's `pywin32.pth` imports `pywin32_bootstrap`; the resolved module under `win32/lib` can add a DLL search directory. `distutils-precedence.pth` also executes code. V3 requires `-I -S -B`, adds the package directory directly, and does not process `.pth`, user-site or customization hooks. |
| pytest capture and logging | Capture's Windows Colorama path explains the first refusal; the logging file-handler open is proven by V2's traceback. Both plugins are disabled, with no relaxation of the DLL or write guards. |
| Fault handler and terminal | The fault-handler plugin duplicates a real stderr handle and enables native fault handling. It is disabled. Terminal output stays on the capped non-TTY stream, with color/highlighting disabled, fixed dimensions and no terminal-progress plugin. |
| Environment/configuration injection | V3 clears pytest option/plugin/debug environment inputs, disables plugin auto-loading and conftest loading, and uses a private minimal `pytest.ini`. Python optimization is refused so assertions remain active. |
| Other unused plugins | Cache, temporary-directory, legacy-path, debugger, pastebin, doctest, unittest integration, recwarn fixture, setup-only/plan, stepwise, subtests and JUnit paths are disabled. The selected functions need none of their fixtures. |
| Required controls | Fourteen plugins retain collection, parameterization, fixtures/monkeypatch, assertions, execution, terminal/reporting, skipping and warning/thread/unraisable-exception handling. Thread and unraisable warnings become errors. The full 31-entry disposition is in `startup-plan.json`: fourteen enabled, seventeen disabled, including conditional terminal-progress. |
| Application imports | Static traversal identifies 35 repository files reachable from module-level imports and selected test bodies. The reviewed set and installed pytest/pluggy sources are hash-bound. This is a source closure, not observed imports. Lazy or dynamic behavior remains guarded. |
| Optional NumPy | The profile repository optionally imports NumPy before its factory-failure tests. V3 deliberately makes NumPy unavailable before import, using the module's existing optional-dependency path. No profile conversion behavior is qualified; these selected tests inject a failing factory and never reach conversions. |
| Existing stubs | The exception-typing-only pyodbc stub and always-refusing workbook parser remain. Calls to either refusal now latch failure so an application catch cannot turn a refused external entry into a clean result. |
| Diagnostics and cleanup | Direct JUnit output is replaced by bounded JSON phase reports. Every runner output uses create-new writes and a shared byte budget. The deadline exits with 124 without waiting on a receipt lock or disk write. Missing final evidence means incomplete/cleanup unconfirmed. |

The `.pth` finding does not rewrite either original receipt. Earlier zero-native
claims concern SQL/VM/pipe/file-lock qualification work; they are not evidence
that the Python interpreter executed no Windows support hook. V3 narrows that
startup surface. Standard CPython runtime services and the existing bounded
Python thread tests remain in scope; this is not an operating-system sandbox or
proof of zero underlying native library activity.

## Frozen correction and execution packet

Prepared files are under
`C:\discord_file_downloader\.codex_artifacts\p025\d5c-offline-preparation-v3`:

| File | SHA-256 |
| --- | --- |
| `run_offline.py` | `2cd925c75304d70bf93df9eea3723d171fabfc9d5fcbcb18bc2717604a0b983f` |
| `startup-plan.json` | `1c8f0fd22295aab35e617a7b21f36ddb1b42886860a728ab75353f33b4d27308` |
| `pytest.ini` | `713f986ee48be06ad4bff2a700d39514a9f69e34b3547af52366c0a274e30e5b` |

`d5c-v3-corrected-execution-plan.json` records the exact interpreter command,
hash gates, limits and acceptance conditions. It is a plan, not authorization.
The runner selection is AST-identical to V2, and all test files/assertions are
unchanged. The audit predicates and allowed-write policy are retained; refusals
add a latch checked before execution and at report boundaries. This correction
touches no bot runtime, SQL source, VM setting, permission or installed package.

Proposed sequence after approval:

1. Recheck the three packet hashes, all 131 startup/source bindings and original
   evidence; require an unused V3 output directory with no prior execution intent.
2. Start the existing pinned interpreter once with isolated, no-site and
   no-bytecode flags. Freeze exact node IDs and imported repository hashes before
   executing any test. Refuse unless collection yields exactly 418 unique cases.
3. Stop on the first assertion, setup, guard, count, output-budget or cleanup
   failure. Keep the five-minute ceiling, 1 MiB total directory ceiling including
   prepared files, 128 KiB captured text and 256 KiB serialized phase-record cap.
   There is no automatic retry, fixture repair or runtime correction.
4. Accept only a zero pytest result, 418 passed call phases with no skipped/failed
   phases, unchanged evidence, no recorded boundary refusal and no remaining test
   worker. Verify setup/teardown evidence and file sizes before reporting results.
   Exit 124, missing receipts or uncertain cleanup cannot count as success.
5. Return findings for review. Even a complete offline pass does not authorize
   the held native readiness packet or close the outstanding native D5c cases.

The original five-minute/1 MiB limits are unchanged. The new caps subdivide that
budget; they do not add allowance. No retained input is read, imported or replayed.

## Static validation and remaining gates

Validation is syntax/AST/hash inspection, architecture lint, read-only Ruff,
documentation checks, deferred-item and security-routing checks, and the path
selector. No test-runner import, fixture setup, test collection or application
test is used as a preparation check. The initial Ruff import-order finding was
corrected only in the unexecuted V3 draft; V1/V2 and test files were not changed.
The earlier `d5c-startup-correction-static-review.json` records an intermediate
draft hash; the final validation and execution packet identify the final bytes.

The selector's broader suite, smoke imports and registration runs are held
because they exceed this source-only correction authorization. No production
or SQL validation is needed for a runtime change: there is no such change.

Security routing remains **Changes review for executable handoff**, with Deep
off and this exact private runner/test delta as the intended scope. No independent
scan/pass is claimed in this source-only preparation; the previously recorded
review gate before native handoff remains pending. The Python audit mechanism is
a guard for this trusted, bounded selection, not a general security boundary
against hostile code. No new repository-wide scan or permission change occurs.

**Next decision:** authorize one V3 offline pass of this exact packet under the
same limits. No further pass is included in this preparation approval. All prior
D5b acceptance, failures, completed claims and the consumed targeted retry remain
preserved; D5c/d/e/f and production acceptance remain open.
