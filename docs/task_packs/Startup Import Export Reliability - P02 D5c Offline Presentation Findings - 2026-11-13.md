# P02 D5c offline presentation findings

## Outcome

The single authorized offline pass stopped during runner startup, before **any
of the 35 qualification cases** executed. This is a test-runner defect, not
evidence that the bot's status card, Refresh or reports failed. C12 remains open.
No runtime correction or native work occurred, and the pass was not repeated.

The original packet, runner, tests, execution intent and failure are preserved:

- Receipt: `.codex_artifacts/p025/d5c-presentation-offline/result.json`
- SHA256: `45cb9f6fd94a8fd787879d5669cbd8606e0d4b90a9e7015637a1654f38d851e6`
- Intent SHA256: `6bc53c93751d51875946cb5baafa6cf8399c05cbc515f02c5fedeef4397c31aa`
- Adjudication: `.codex_artifacts/p025/d5c-presentation-offline-adjudication.json`
- Recorded elapsed time: 0.266 seconds; combined intent/result: 3,156 bytes.
- Failure: `BoundaryViolation: unlisted_import:` (empty import name).
- Zero case results and zero expected guard controls executed; do not count them
  as passed merely because the guard stopped startup.
- No pending async tasks or other test threads; all 428 pinned source/evidence
  hashes independently rechecked unchanged after exit. Ordinary HEAD/index and
  all four reviewed packet files are unchanged.

## Diagnosis without replay

The runner finishes loading its nine selected source-body groups, creates its
no-IO loop, then calls `asyncio.set_event_loop(loop)`. Installed Python 3.11
`Lib/asyncio/events.py:803-805` calls `get_event_loop_policy()`, which initializes
the policy through `from . import DefaultEventLoopPolicy` at lines 754-759.
The packet deliberately rejects every relative import; this one reaches the
guard with an empty import name and level 1, explaining the exact refusal.

This conclusion uses the saved receipt and installed standard-library source,
not a second execution. Independent follow-up review confirmed the trace. The
earlier static readiness reviews missed this lazy policy-initialization edge;
the completed security review is not evidence of a successful qualification run.

## Concrete continuation plan — not implemented or executed

Prepare a separately versioned runner and manifest, leaving all original files
and receipts unchanged. Remove the unnecessary `asyncio.set_event_loop(loop)`
call. Keep the explicit no-IO loop and every import, network, native, subprocess,
write and output limit intact; do not permit relative imports generally or
initialize a Windows transport to work around this refusal.

`loop.run_until_complete` already supplies that loop to its initial task, and
`run_forever` establishes the running-loop context used by the selected Event,
task, gather and shield operations. Review the complete startup path and remaining
lazy imports again before freezing the replacement. Static follow-up found other
lazy imports only in unused `as_completed` and `mock_open` paths; this is not a
claim that a replacement has passed.

Carry forward all 35 cases and 428 original preservation pins. Add the failed
packet/intent/receipt and this adjudication to the new preservation set. Strengthen
the seven negative guard assertions to require their exact expected reasons:
`socket.getaddrinfo`, `unlisted_import:pyodbc`, `unlisted_import:discord`,
`unlisted_import:win32file`, `subprocess.Popen`, `write_outside_receipt`, and
`active_work`. An unrelated startup refusal must not satisfy a negative control.

Complete static checks and a new exact Changes review before handing back the
corrected packet for one additional offline-pass approval. The original one-pass
allowance is consumed even though no qualification case started. No automatic
repeat is included. A corrected pass would retain the 300-second/1 MiB limits
and stop at its first failure. No PowerShell/VM action is needed for this work.

## Scope, review and validation record

Changes review `fb453aed-175a-4897-b623-040fc272cdf7` completed before the attempt,
with zero reportable security findings, all four changed files covered and no
unresolved security-review tasks. Snapshot range:
`e7443e37212ca91e20d531b3684cc369d0fe1505` to
`45bc50fedbd075ecbe30006fc2783310950016a8`. Syntax and manifest checks passed.
Whitespace check passes with Git's `cr-at-eol` setting for the Windows JSON
manifest. Scan-reported usage: 4,910,678 total tokens, including 4,844,032 cached
input tokens; this is tool accounting, not a billing estimate.

Full pytest/conftest, smoke imports, command registration and test-selector
execution were skipped to avoid unrelated startup and transports. Architecture,
deferred and security-routing validation was a focused source review: the change
adds only offline tooling/tests/plan, no application layer, SQL contract, general
deferred item or routing directive. No PR/promotion handoff is being made. This
findings/adjudication-only addition requires no repeat runtime/security scan.

The selected-body/inert-seam limits remain: no proof of real Discord registration,
command-decorator authorization, delivery, complete report ZIP/download flow,
production bootstrap, Windows transport or universal Python isolation. The exact
subprocess negative control uses all-None handles; its audit boundary must not be
generalized to subprocess PIPE configurations.

Native budget remains **1,361 seconds**, including the protected **1,000-second**
later-phase reserve; Windows-test budget remains **50 seconds**. The **21-input
allowance remains consumed**, with no new inputs. All original evidence and
previously consumed mutation/retry allowances remain unchanged.

D5a/D5b stay accepted. D5c remains partly open across C01/C04/C05/C06/C09/C12;
this failed startup closes none of those groups. D5d fault/restart, D5e cost and
D5f final evidence remain ahead. D6 production deployment is separate and has
not been authorized or performed here.
