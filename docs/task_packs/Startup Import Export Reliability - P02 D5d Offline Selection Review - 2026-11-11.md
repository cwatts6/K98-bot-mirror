# P02 D5d offline selection review - 2026-11-11

Status: **Source preparation only; no D5d pass or native execution claimed.**
The operator directed completion of D5c and then all D5 slices. This review
advances independent preparation while the one-shot D5c readiness receipt is
pending. Preserve all original evidence, the consumed 21-input allowance and
the carried native budget; do not reset it for this slice.

## Reuse existing assertions with explicit fixture boundaries

| Test source | Proposed selection | Evidence and boundary |
| --- | --- | --- |
| `tests/test_sql_setup_custody.py` | All seven test functions, 18 expanded cases | Synthetic driver setup failure, cancellation, pending close, concurrent setup and late success. Its `connections` fixture substitutes settings and driver connection. No real driver or credentials are required. |
| `tests/test_profile_sql_custody.py` | First four test functions, six expanded cases | Explicit rollback, cursor/connection close, primary failure preservation and no candidate on cleanup failure. Exclude `facade` and async tests from this initial selection; those add real file/cache and event-loop prerequisites. |
| `tests/test_authority_observation_dispatch.py` | Interrupted start, lost reply, dispatch failure, unconfirmed transport/SQL cleanup, deadline and waiting-request ownership | Real local threads with injected dispatcher/transport, bounded waits and explicit joins. Preserve the actual failed owner through each test. Exclude Windows launcher/pipe tests from this offline packet. |
| `tests/test_checkpoint_observation_lifecycle.py` | Lifecycle ACK failure, no retry for other transactions, exact completed receipt, and external cursor ownership | Fake connections exercise commit/rollback/close uncertainty and receipt binding. The imported clock helper needs the correction described below before selecting these cases. No producer replay. |
| `tests/test_d3_cleanup_custody.py` | Nested player/capture cleanup and retained resources, after import review | Requires a controlled `file_utils` boundary and imports `producer_runtime` even for non-writer nodes. Do not assume selecting a node avoids the module's imports. Writer fixtures use files/locks and need a separate owned-path plan. |
| `tests/test_export_child_restart.py` | Exact birth, lost freeze/close ACK and no replay, after fixture closure review | Imports other test fixtures and Windows host code. The real suspended-child test is native and excluded from offline execution. Synthetic restarted records do not prove process death or job containment. |
| `tests/test_personal_stats_shutdown.py` | Preserve accepted D5a drain evidence; select only additional uncovered cases | Module includes subprocess and installed Pycord cancellation checks. Do not repeat the accepted drain investigation or execute this module wholesale. |

These are reviewed function selections, not a final collected-node manifest.
The eventual runner must bind exact expanded node IDs and source/import hashes,
then verify all setup/call/teardown phases and absence of additional live workers.

## Startup and cleanup corrections needed before a pass

The project `tests/conftest.py` imports the snapshot fixture and installs broad
autouse application fixtures. The D5c runner deliberately used `--noconftest`.
D5d must retain that bounded startup and explicitly provide the required
`isolated_sql_cleanup_custody` equivalent for **fake test handles only**. Without
it, a test that intentionally retains a failed fake connection closes admission
for later tests. Never apply that reset to runtime or native connections.

`tests/test_export_contention.py::clock` currently patches
`module.time.monotonic` and `module.time.sleep` on the shared Python `time`
module. Reusing it unchanged could affect the runner's elapsed-time accounting
while the fake clock is active. Before execution, isolate the target module's
clock behind a test-owned facade, or separately prove that every runner,
watchdog and reporting clock is captured independently. Prefer the test-owned
facade because it confines the fake clock to the target under test. Preserve the
original helper bytes and review equivalent callers before making that change.

The D5c startup plan is reusable design evidence, not permission to rerun V3 or
copy its hardcoded 418-node/1,254-phase ledger. D5d needs its own create-new
directory, selected plugin/fixture/import bindings, case counts, output bounds,
one-shot intent and first-failure receipt. Keep no-site isolated startup,
provider/driver/native refusal guards and no writes outside its owned output.
The optional NumPy and parser paths remain excluded unless explicitly selected
and independently prepared.

## Native and final gates remain separate

Lost grants, durable commit outcomes, process birth/death, Windows handles and
physical SQL release need exact native schedules and cleanup evidence. Doubles
cannot close those gates. Admit no native D5d packet until D5c readiness and
remaining budget are adjudicated; do not grant permissions, change isolation,
replay input or kill an unowned process to manufacture coverage.

D5e still requires equal warmup and at least five balanced OFF/ON pairs including
actual maintenance and physical cleanup. D5f must reconcile every obligation;
neither this review nor a green offline packet closes those slices.

## Validation disposition

This document changes no executable code. Security discovery and application
tests are skipped for this source-review record; exact executable Changes review
and focused tests remain required before the new runner is used. Validate
documentation whitespace, deferred-item structure and security routing. No
native rehearsal time or retained inputs were consumed by this review.
