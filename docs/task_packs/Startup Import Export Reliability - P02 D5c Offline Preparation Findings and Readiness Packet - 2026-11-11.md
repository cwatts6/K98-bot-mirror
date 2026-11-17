# P02 D5c offline preparation findings and readiness packet â€” 2026-11-11

Status: **offline preparation attempted; test-tool bootstrap refused before
collection. No application test ran. D5c remains unqualified.**

This follows the approved bounded offline slice in the
[D5c execution plan](Startup%20Import%20Export%20Reliability%20-%20P02%20D5c%20Source%20Review%20and%20Execution%20Plan%20-%202026-11-11.md).
The first attempt and source bytes are preserved. There was no SQL connection,
VM operation, native pipe/file-lock test, provider call, runtime correction,
permission change or input consumption. The 21-input allowance remains consumed;
the native budget remains **1,480 seconds**.

## Observed outcome and diagnosis

The runner exited with code 2 in approximately **0.61 seconds**. Its audit boundary
refused `ctypes.dlopen` during pytest startup. No collection manifest or JUnit
result was produced, and its recorded repository-module set contains only the
runner. Therefore this is a harness/bootstrap failure, not a failing application
assertion and not a pass for any D5c case. The refusal prevented the attempted
native-library load. All **145 source/evidence hash bindings** in its preservation
record were unchanged at exit.

Source inspection identifies a matching startup path in the installed tooling:
pytest's default `capture` plugin calls `_colorama_workaround()` on Windows;
Colorama imports `ctypes`, whose Windows initialization loads `kernel32`, and
Colorama binds console functions. The capture hook catches ImportError, while
the audit hook deliberately raises RuntimeError. This explains a compatible
mechanism for the observed refusal. The first receipt did not retain a traceback,
so the exact interrupted frame/library is not claimed as dynamically proven.

The agreed one-pass/stop boundary was applied. The original runner was not
rerun and the native-load guard was not relaxed. Independent source preparation
continued; no dependent application test or native operation followed.

## Prepared test coverage and its limits

`tests/test_p02_d5c_offline.py` plus selected existing nodes defines an estimated
**418 expanded cases**, derived statically; authoritative pytest collection is
still pending. These are authored cases, not executed results:

- 292 common recovery-service refusal controls: each of the 73 allowed pairs
  against stale revision, stale token, removed action and unauthorized actor.
  Each must refuse before a claim or adapter effect.
- 73 detached policy-projection controls preserving original evidence.
- 32 additional controls for schema-busy versus other errors, disabled snapshot
  admission, selected-factory failure, damaged season tuple, known/fabricated/
  unavailable holder, wrong resource, effectful selectors, passive status and
  the source call-site census.
- 21 selected existing admission, snapshot and authority-saturation cases.
  Their original assertions are retained; native fixtures and cleanup-fault
  modules requiring broader fixture setup are excluded.

The private coverage map binds all **35 direct managed snapshot sites** to
C01/C04/C05/C06 and retains all twelve family dispositions. The 73 action-pair
tests exercise the common RecoveryService boundary with inert adapters, not every
adapter's current-state implementation. The status test exercises the service
projection with a loaded-source dependency spy, not Discord/view integration.
C03/C05/C11 need further fixture or native evidence; no actual maintenance,
committed tuple interleaving, file handle or pipe contention is claimed. The
out-of-count Recheck, accepted-action, group/batch, inherited and outcome-worker
paths remain in the register and require effect-level tests.

The runner substitutes only a pyodbc exception-typing module whose connect
always refuses, and workbook-parser functions that always refuse. It does not
claim driver or parser qualification. Real provider/driver/native imports,
network, subprocess and writes outside its owned artifact directory are denied.
No project conftest or automatically loaded pytest plugin is admitted. The
planned real-thread authority cases retain their existing short event/join
bounds; no arbitrary sleep or stress loop was added.

## Proposed test-only bootstrap correction

A separate V2 runner is prepared, **syntax-checked only and not executed**:

`C:\discord_file_downloader\.codex_artifacts\p025\d5c-offline-preparation-v2\run_offline.py`

SHA-256: `bc178bc30ae0de1414130bc9e587a8f52d354c870b284da55a94b0fc44151e0e`.

It disables pytest's capture plugin and console colour, retaining the runner's
capped in-memory output and unchanged `ctypes.dlopen`/native-entry prohibition.
It also records a bounded traceback on bootstrap failure. It does not preload
the native library before the guard or substitute another principal/runtime.
The V2 artifact directory is separate; it cannot overwrite the first intent or
receipt. Test collection must freeze exact node IDs and imported source hashes
before any application test starts. The proposed single pass remains bounded
to five minutes and 1 MiB diagnostics, stops on the first failure, and admits no
native or runtime-correction work.

The lint configuration unexpectedly applied its enabled safe import-grouping
fix when checking the new test file. Exact pre-lint bytes were reconstructed and
verified against the first intent's SHA-256, then saved as
`d5c-offline-preparation/original-test-46c68eb75936.py`. The current test differs
only by import grouping/order; no original existing test/runtime file changed.
The first attempt never imported this test. Future lint commands must explicitly
use `--no-fix` when evidence bytes are frozen.

## Concrete readiness packet, held from execution

Private `d5c-readiness-execution-packet.json` contains the exact ordered SQL text,
parameters, row bounds, expected D5b preimages and identity/cleanup requirements.
SHA-256: `cda42134aafddc6b383f4191bfe8d7c377ca9134ac360dd806157316061a1fe2`.
It is **declarative and not executable**. A runnable collector and manual-console
handoff remain blocked by offline validation and review; no old D5b runner is an
approved substitute.

| Item | Frozen draft requirement |
| --- | --- |
| Target | Existing VM `2ac1b401-7076-4965-af71-de36ee0f9f9c`, MINI_AMD, SQL `lpc:localhost`, copy `K98_P025_D5b_20261111`, recorded database ID 8/create time `2026-11-11 17:00:42.830`. Original database ID 7 remains read-only/restricted. |
| Connection | Existing integrated identity, pooling off, five-second login maximum. Validate the existing console PSSession object; do not start the VM or recreate a session automatically. |
| Command ledger | **27 planned client commands; at most 137 returned metadata rows** on the complete successful path. Existing ceilings stay 48 commands, 512 per-command rows, 2,048 total and 1 MiB receipt. A 33rd principal row refuses the 32-row observation cap. |
| Reads | Session/database/source/file identity; owner, six maintenance rows, backup demand and permissions; thirty pinned candidate images; required-object availability; bounded existing principals; log and version-store resources. Repeat relevant pre/post preservation checks. |
| Host/guest | Fixed four CPUs/eight GiB, zero NICs, exact existing Q: volume, disk reserves, no active Python producer. Bounded existing Python/ODBC registry metadata only; no search/install/import or interpreter invocation. |
| Deadline | 60-second overall proposal including cleanup/receipt; work admission stops at 35 seconds, guest work at 40, host stop request at 45, at most ten seconds to join, five reserved to record uncertainty. Worst-case async ownership/cancellation accounting must be verified before collector approval. |
| Closure | Work disposal plus observer check of captured session birth, not SPID alone; observer disposal and worker join. Unknown cleanup stops all dependent work and remains in the receipt. Borrowed PSSession is retained. |
| Effects | No fixture rows, maintenance demand, report recomputation, install, setting/grant/owner change, input read or provider/backup dispatch. Only create-new host intent/evidence files. |

The first inventory only discovers existing runtime locations. A later exact
Python/pyodbc read-only factory probe requires its own reviewed executable/path
binding; .NET metadata success cannot qualify Python connection behavior. Missing
objects/principals/runtime are reported explicitly, without automatic repair.
The new synthetic rows, actual-worker demand, restricted identity and native
SNAPSHOT-off cases remain separate gates in the full plan. No fixture mutation
packet can be finalized from guessed installed prerequisites.

## Custody and validation

Private artifacts under `C:\discord_file_downloader\.codex_artifacts\p025`:

| Artifact | Role / SHA-256 where needed |
| --- | --- |
| `d5c-offline-preparation/execution-intent.json` | One-shot intent, initial runner/test identities and 145 preservation bindings. |
| `d5c-offline-preparation/runner-failure.json` | First refusal; `aa6c84b9beedf075f45424b9c97a906ff4c47c58f63894c49616945dcf225ea5`. |
| `d5c-offline-preparation/result.json` | Exit/preservation record; `550a97e37ca31753dc6f8f6c1db0a3db1b1dc7deca2f53b7d47f03aeea6d4ffc`. |
| `d5c-offline-preparation/run.log` | Empty because refusal preceded normal pytest reporting; not evidence of success. |
| `d5c-offline-coverage.json` | 35-site mapping, 73 pairs, twelve family dispositions and explicit unexecuted coverage limits. |
| `d5c-readiness-execution-packet.json` | Non-executable exact command/identity/budget draft. |
| `d5c-offline-preparation-v2/run_offline.py` | Separate proposed bootstrap correction, unexecuted. |

Static syntax/source custody, architecture, deferred-item, security-routing,
selector, link and whitespace checks apply. Ruff completed after the recorded
safe import regrouping. The selector's full pytest/smoke/registration and broader
release/schema/permission recommendations are not run: they exceed this bounded
offline selection and its stop boundary. No production or SQL source correction
is present. Security Changes review of the new executable harness is **pending**;
no native handoff or reviewed-executable claim is made. A future review must use
this exact test/runner delta and supporting source, with Deep off; any SQL delta
requires a separate SQL-repository target. This packet's prose/data additions
do not themselves grant native authority.

**Next decision:** permit one corrected offline V2 pass under the same limits,
preserving this refused attempt. Return its results and reviewed readiness
collector before any native work or runtime correction. The original D5b
closeout, failures, completed claims, consumed targeted retry and 21 inputs
remain unchanged; D5c/d/e/f and production acceptance remain open.
