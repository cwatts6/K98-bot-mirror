# P02 D5a.1 bounded drain investigation findings

11 November 2026. Status: a real completion-versus-settlement ordering defect
was reproduced; investigation stopped on its first failed invariant. No runtime
fix is applied. D5 qualification and the original CI incident remain open.

The operator confirmed the [D5 scope and bounded test-only slice](Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Scope%20Review%20-%202026-11-11.md).
The [full obligation reconciliation](Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Obligation%20Reconciliation%20-%202026-11-11.md)
remains in force. This receipt advances Q01 evidence only; it does not close the
remaining D5 scope, Q04, Q05, SQL 3961, P03/P04 or deployment prerequisites.

## Finding and practical effect

`StatsRuntime.drain()` joins a render's asyncio Future, but completion of that
Future and execution of its `render_completed -> _settle` callback are distinct
events. An already-done Future can be awaited without yielding. When a drain
resumes after the first render, the second Future can already be done while its
settlement callback is still queued. The drain then sees a retained render job,
skips executor shutdown and returns false. Two concurrent drains can both take
this path before the callback removes the final job.

This was demonstrated with two actual bounded rendering threads, normal asyncio
Future propagation and the unchanged runtime. The harness coordinated the second
worker's release with scheduling of the first drain's wakeup. It did not withhold,
replace or manually invoke the render settlement callback in the failing case.
The `_settle` wrapper only recorded entry/return and called the original method.
This is a controlled ordinary-callback-path reproduction, not an uncontrolled
recurrence of the historical CI run.

The result is a conservative false failure, not demonstrated early capacity
release. Both jobs remained owned while blocked; a third submission was refused.
At false drain return, both physical futures and their asyncio futures were done,
but one job remained unsettled. Its normal callback subsequently removed it.
Test cleanup then joined the real executor and confirmed no remaining jobs.

Production impact inferred from source: `bot_instance.py:1108` treats false Stats
drain as unconfirmed physical cleanup and raises during graceful teardown. Thus
the ordering can report shutdown failure despite completed renders. The
`DL_bot.py:872` remaining-jobs guard is a separate final ownership check; this
experiment does not establish an incorrect process release, lost render work,
production occurrence or provider effect.

## Exact failing trace

Run: `drain-investigation-20261111T121557Z`, case
`03_ready_before_settlement`. Jobs use zero-based indices in the private trace.

| Sequence | Observed event | Job/future state |
| --- | --- | --- |
| 7 | Third render refused | Two physical jobs still active and owned. |
| 8-9 | Drains A and B entered | Both joined the existing jobs. |
| 10-13 | First worker completed and its normal callback settled job 0 | One job remained; job 1 was still physically active. |
| 14-16 | Before drain A's wakeup was queued, the second worker was released and its normal Future-state propagation was acknowledged queued | Both native futures done; second asyncio Future not yet marked done. |
| 17 | Second asyncio Future completed and queued its settlement callback | Both asyncio futures done; job 1 remained unsettled. |
| 18-19 | Drains A and B returned false | One retained job; both native/asyncio futures done; no executor shutdown by those drains. |
| 20-21 | The normal settlement callback ran | Zero retained jobs, both settled. |
| 22 | Harness collected the two results | Both results stayed false; later callback completion did not change them. |
| 23 | Finally cleanup confirmed | Actual workers/executor joined; no retained jobs or forced registry clearing. |

Local stdlib inspection supports the trace: `asyncio.shield` directly returns
an already-complete inner Future, and `BaseEventLoop._run_once` processes the
ready-queue length sampled at the start of the turn. Newly scheduled callbacks
run on a subsequent turn. No stdlib or event-loop implementation was modified.

Relevant application sources: `player_self_service/stats_runtime.py:207`
(render callback), `:252` (settlement), `:294` (drain), and
`core/owned_work.py:14` (shielded await helper).

## Execution and stop disposition

One pytest invocation, no retry: **two passed, one failed; nine not run**.
Pytest reported 7.51 seconds; the bounded runner recorded 8.375 seconds including
startup/collection. Output was 12,925 bytes, below the 1 MiB cap. Neither the
five-minute aggregate watchdog nor a twelve-second child watchdog expired.
Each new render retained its five-second release guard and two-worker limit.

| Schedule | Disposition |
| --- | --- |
| 01: ordinary first/second completion | Passed once. |
| 02: ordinary second/first completion | Passed once. |
| 03: completion ready before settlement, two concurrent drains | Failed once with both drain results false; physical cleanup confirmed. |
| 04: reverse completion with artificial callback hold | Not run after stop. |
| 05: both Futures done with artificial callback holds | Not run after stop. |
| 06: concurrent drain A first | Not run after stop. |
| 07: concurrent drain B first | Not run after stop. |
| 08: one native exception while another remains active | Not run after stop. |
| 09: repeated cancellation of entered drain | Not run after stop. |
| 10: owner-task allocation failure after submission | Not run after stop. |
| 11: executor submission rejection | Not run after stop. |
| 12: executor shutdown failure | Not run after stop. |

The existing render-submission, shutdown and owned-read modules were **not run**
because the approved stop-on-first-failure gate had fired. They were not skipped
to obtain a green report. Their files and assertions are unchanged. Cleanup's
final drain is part of releasing this case's resources, not a rerun or acceptance
replacement for the failed result. The reproducer retains the failing assertion;
it is not xfailed. The new investigation module is explicitly opt-in through
`K98_D5_DRAIN_SCHEDULES=1`; that flag was enabled for this run.

## Source and original evidence custody

- Bot HEAD remained `e7443e37212ca91e20d531b3684cc369d0fe1505` throughout.
- Python: Windows CPython 3.11.9, repository `.venv`; pytest 9.0.3,
  pytest-asyncio 1.3.0 and py-cord 2.7.2. No Discord client was created.
- Historical failed CI log points to Linux CPython 3.11.18. Its scheduling trace
  is absent. The local mechanism fits the failed assertion and its cancelled
  owners/concurrent drains, but does not establish that exact historical cause.
- Original failure remains CI `42998021332`, attempt 1, head `8b6879bf`,
  `test_cancelled_unstarted_owners_keep_two_native_slots_and_drain` line 63.
  Its 1 failure/13,248 passes and later separate passes remain intact.
- Before/after SHA256 matches cover the runtime, owned-work helper, all three
  original focused modules and both original private CI logs. No tracked runtime
  file changed. SQL repository remained clean.
- Original failure log SHA256 remains
  `528deff3b5bd983c148572a971c924336ca8ed58fc4a4cbd8c2e6f28a13b8ec3`;
  original success log remains
  `65bbc5ce6b48b088fb0b7643a0325e06d066888ca30aa5bbdd516efb11d4bfa1`.
- All four operational logs had unchanged existence, size and modification time.
  The existing log-noise helper's snapshot comparison was used without launching
  another pytest run. The harmless test-config warning is retained in the failure
  output; `.env` loading was disabled and no configuration file was changed.

Private evidence is in
`.codex_artifacts/p025/drain-investigation-20261111T121557Z/receipt.json`
and `controlled-schedules.log`. Log SHA256:
`e7a307f7774c8bbffce3b59d603cf8d5abe15cd16fa857be0514c4506689b371`.
The exact test source hash at execution is
`4911ff70c43eb72ff437e89793a3f360a291401e4267f480a4630e85342e5945`.
Keep original and derived private traces local; do not attach raw logs to public PRs.

## Focused correction proposal, awaiting confirmation

Address the distinction between physical Future completion and completed
settlement explicitly in `StatsRuntime`:

1. Give accepted render work an awaitable acknowledgement of its settlement
   callback, established before work can complete. Resolve that acknowledgement
   after the callback has recorded the original result/error and its cleanup
   disposition. Unknown cleanup must remain retained and make drain fail.
2. Drain both physical completion and settlement acknowledgement before deciding
   whether executor shutdown is permitted or returning the final jobs result.
   Native errors and cancellation must not bypass settlement or joining other
   owners. Preserve the current physical-owner and first-error contracts.
3. Keep one settlement path and idempotent publication across simultaneous drains,
   immediate completion, submission rejection and task-allocation failure. Do not
   add sleeps, timeouts, retries, registry clearing or larger capacity limits.
   Do not redesign executor ownership unless a separately evidenced defect
   requires it.

Proposed acceptance after a focused correction: the unchanged controlled schedule
must return true only after both callbacks and executor join; finish the nine
unexecuted schedules and run the three existing modules once under a fresh bounded
packet. Include already-done and exceptional futures, task-allocation/submission
failure, repeated cancellation, concurrent drains, retained unknown cleanup,
dataset/registry reads and installed Pycord shutdown behavior. A future Linux
matching-environment check can strengthen CI attribution; it is not authorized or
performed by this receipt. Do not claim the entire Q01/D5 lifecycle scope closed
from this single local mechanism reproduction.

## Review gates and boundaries

Changed surface: one new opt-in test module plus this findings document. The
approved scope/reconciliation documents are retained unchanged. No runtime,
existing test, SQL, dependency, config, permission or release artifact was edited.

Security routing decision: documented skip for this uncommitted test-only
investigation and documents. The subprocess uses a fixed interpreter and fixed
argument list with an allowlisted case identifier, no shell, user input, network,
SQL or production state. It exercises existing lifecycle behavior using inert
workers; it does not alter an application trust boundary or persisted ownership.
Any runtime correction needs its own Changes review decision, Deep off, against
the exact subsequent diff. No standard/deep repository scan was launched.

Static checks apply to the actual test/document delta. The selector's generic
full-suite, smoke-import and command-registration recommendations do not override
the approved bounded stop: no additional application-executing checks or blanket rerun are
performed after this failed invariant. No PR, commit, production action, VM/SQL
execution, provider dispatch, input replay or new allowance occurred.

Static results: architecture passed for the new Python file; deferred validation
passed for this document; security-routing validation passed with zero
errors/warnings; Ruff passed. Test selection completed and its broader executable
recommendations were deferred for the reason above. Black's pre-run check passed
on the exact subsequently executed source. Formatter processes also stalled during
preparation and a redundant post-run check; those identified formatter processes
were stopped, without changing the tested source or terminating any test worker.
The redundant check is recorded as interrupted, not another pass. No formatter
or investigation failure was hidden by a runtime change or test retry.
