# P02 D5a.1 drain correction and bounded validation

11 November 2026. Status: approved local correction implemented and bounded
validation passed. No commit, PR, promotion, deployment or native SQL/VM run.
This completes the focused correction requested after the
[investigation findings](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a1%20Drain%20Investigation%20Findings%20-%202026-11-11.md);
it does not close the broader D5 qualification programme or establish the exact
cause of the historical Linux CI occurrence.

## Behavior and implementation

The controlled failing schedule previously returned false from both concurrent
drains after both render workers finished, while the final settlement callback
was still queued. The corrected schedule returns true only after both callbacks
have settled and the executor shutdown has returned.

`player_self_service/stats_runtime.py` now allocates a render-only
`settlement_future` before admitting the job. Submission rejection and the normal
render callback acknowledge their settlement disposition in finally. Drain joins
the native Future and then that acknowledgement, including after native errors
or cancellation, before deciding whether executor shutdown is permitted and
whether jobs remain.

Acknowledgement does not mean successful cleanup: `_settle` still retains the
exact job/key and connection/outcome when cleanup is uncertain, closes admission
and discards the result. Such a drain still returns false. Publication stays
idempotent through the existing settlement path. Dataset/registry ownership and
the shared `core/owned_work.py` helper are unchanged.

No sleeps, timeout increases, retries, registry clearing, new persistence, SQL
changes or executor redesign were added to runtime code. Limits remain two
renders, eight non-render jobs and 32 observers. Service authorization, cache
qualification, teardown failure and final process-release checks are unchanged.

## One bounded validation pass

Private receipt:
`.codex_artifacts/p025/drain-fix-validation-20261111T122443Z/receipt.json`.
Windows CPython 3.11.9 in the repository `.venv`; pytest 9.0.3,
pytest-asyncio 1.3.0, py-cord 2.7.2. HEAD remained
`e7443e37212ca91e20d531b3684cc369d0fe1505` throughout.

| Invocation | Result | Pytest time |
| --- | --- | ---: |
| Twelve controlled drain schedules | 12 passed | 24.03 seconds |
| New settlement contract tests | 3 passed | 1.97 seconds |
| Existing render-submission, shutdown and owned-read modules | 27 passed | 25.99 seconds |

**42 passed**, with no failed/skipped cases and no retry. Aggregate runner time
was 54.422 seconds, below the 300-second cap. Combined captured test output was
41,291 bytes, below 1 MiB. Existing release/deadline assertions were preserved;
new schedule children kept their twelve-second watchdog and five-second render
release guards. No watchdog expired.

All twelve previously proposed schedules were exercised: both ordinary completion
orders, completion before queued settlement, reverse artificial callback hold,
both callbacks held after Future completion, both concurrent-drain entry orders,
one native error with another active worker, repeated cancellation, task-allocation
failure, submission rejection and executor shutdown failure.

The three additional regression tests cover immediate completed-Future publication
exactly once, render cleanup uncertainty retaining its inert ownership sentinel,
and native error plus repeated cancellation while callback settlement is held.
The original focused modules include dataset/registry reads, capacity boundaries,
cache invalidation, retained uncertainty, and actual installed Pycord cancellation
in isolated child processes without constructing a Discord client.

The investigative harness's synthetic-hold cases 04/05 were adapted to release
their own held callbacks after asserting drain remains pending. Otherwise a fixed
drain would correctly wait forever for those test-owned holds. This is explicit
test orchestration, not weakened runtime behavior. Case 03's worker-release
ordering and success assertion are unchanged; its passing trace records final
settlement at sequences 18-19, executor joins at 20-23, and true drain results at
24-25. The original executed harness is retained alongside its failed receipt.

## Evidence custody

Both original CI logs retain their previously recorded SHA256 values. The initial
local failure log still has SHA256
`e7a307f7774c8bbffce3b59d603cf8d5abe15cd16fa857be0514c4506689b371`.
Its exact executed harness is retained as
`drain-investigation-20261111T121557Z/test_personal_stats_drain_schedules.executed.py`,
SHA256 `4911ff70c43eb72ff437e89793a3f360a291401e4267f480a4630e85342e5945`.
Nothing overwrites the initial two-pass/one-failure/nine-not-run result.

The corrected candidate was byte-pinned before and after all three invocations:

| Path | SHA256 |
| --- | --- |
| `player_self_service/stats_runtime.py` | `9e6e9f3be2c9dfe261e0d8c4ef512776ebeeb6e5137cb535f1572ed24bc8c010` |
| `tests/test_personal_stats_drain_schedules.py` | `8e5f395a2b0c35cba8dd7b924acef169be455c6e2f4f26abb95f79bbb1dc74cd` |
| `tests/test_personal_stats_render_settlement.py` | `94d0c681ea3f1111a5ce26efa71e0d91b22c69ad2d3acbb803f99e5c8c22617e` |

The shared owned-work helper and all three original focused test modules are
unchanged. All four operational logs retained existence/size/mtime throughout
the run, using the existing log-noise helper's snapshot comparison. No additional
pytest invocation was hidden inside a log check. Prior scope, reconciliation and
investigation documents remain historical, unchanged records. SQL remains clean.

## Review and validation gates

- Architecture boundary validator passed for all three changed/new Python files.
- Ruff and Black checks passed on those exact sources; Black used `--no-cache`
  with a bounded invocation and completed without the prior formatter stalls.
- Security-routing validator passed with zero errors/warnings.
- Test selection completed. Its generic full-suite and release regression
  recommendations were deliberately not run: this is the approved bounded
  correction, with no release/schema/permission changes. Smoke-import and command
  registration checks were not separately run; focused tests imported the affected
  modules, and no command wiring changed. Full pre-commit was not run.
- Source/caller review covered admission, rejection, task allocation, native
  exceptions, cancellation, concurrent drains, publication, cleanup uncertainty,
  snapshot serialization and shutdown/process-release callers. No blocking
  correctness finding remains for this focused local patch. Broader D5 and
  promotion/merge qualification are separate.

Codex Security Changes review `80dce54c-8161-484d-ba10-650c6b67d3f8` completed with
**zero findings** and complete coverage of its declared scope. Deep was off.
The tracked runtime diff was reviewed against `e7443e37212ca91e20d531b3684cc369d0fe1505`;
snapshot digest is
`codex-security-snapshot/v1:sha256:5c13d9971870b793f301eb6ee53a284091063c2bebcadfd63aa569ec7e3fa0ea`.
The tool inventory contained one tracked source file; both untracked test modules
were additionally reviewed and byte-pinned in its supplemental custody artifact.
Independent architecture review informed the model; the parent reviewed the diff.
No repository-wide security claim or newly discovered vulnerability is made.

The sealed report is under the security workbench scan directory ending
`e7443e37212ca91e20d531b3684cc369d0fe1505_20261111T122618Z_pp_13p04/report.md`.
This closeout document was added after sealing and is a documentation-only delta;
the runtime/test hashes above remain the reviewed versions. No additional scan is
needed for this factual receipt alone. Workbench-reported usage was 4,174,532 total
tokens across three agent threads, including 3,896,704 cached input tokens; that is the
tool's cumulative rollout accounting, not an isolated estimate for this patch.

## Remaining boundaries

This corrects the reproduced local mechanism and supplies focused regression
evidence. It does not erase the original CI failure or prove its exact scheduling
cause: that run used Linux CPython 3.11.18 and lacks the necessary trace. The
remaining integrated lifecycle obligations still belong to D5d.

The full F01-F32/C01-C16/action obligations, Q04 fingerprint assertion, Q05
maintenance receipt checks, SQL 3961 history, current host readiness and retained
data feasibility remain in their existing registers. The consumed 21-input
allowance and frozen resource/cost gates are unchanged. No native SQL/VM operation,
provider dispatch, input replay, deployment, restart or production modification
was performed. D6 and first normal import/export retain their separate gates.
