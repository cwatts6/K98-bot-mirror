# P02 D5c offline presentation acceptance

## Accepted result

The separately versioned V3 bootstrap correction passed the single additionally
authorized offline pass: **35 passed, zero failed, zero unexecuted**. The correction
preloads the existing trusted IDNA codec before guards; it changes no application
source or guard logic. Both earlier failed attempts remain immutable evidence.

| Group | Cases | Observed result |
|---|---:|---|
| Safety controls | 7 | Each real attempted boundary was refused for its exact expected reason; a swallowed active-source attempt remained observable. |
| Status card | 9 | Missing/uninitialized sources did not start work; stale, busy, shutdown and uncertain-cleanup states retained their correct meaning. Available capacity was not labelled a successful SQL health check. |
| Refresh | 9 | Acknowledgement preceded render; wrong guild/channel/message, unbound, failed acknowledgement, closed and concurrent requests did not render/edit. Failed edit did not repost, and shutdown waited for the outstanding edit. |
| Command/scheduled adapters | 3 | Actual command body and scheduled update used the same actual card projection; failed command acknowledgement stopped completion; selected adapters contained no active health-check edges. |
| Report health components | 7 | Ordinary and complete-component paths accepted available passive observations, reported missing/failed sources explicitly, and rejected an oversized complete health component. |

The expected control reasons were exactly `socket.getaddrinfo`,
`unlisted_import:pyodbc`, `unlisted_import:discord`, `unlisted_import:win32file`,
`subprocess.Popen`, `write_outside_receipt`, and `active_work`. There were no
unexpected boundary attempts, pending async tasks, other test threads or captured
output. No application runtime fix is indicated by these covered checks.

## Evidence and adjudication

- Result: `.codex_artifacts/p025/d5c-presentation-offline-v3/result.json`
- Result SHA256: `d140d67bbb20fd00108f301ae86f2476b8b441635c7dd5ca97e05eb1dd662c69`
- Intent SHA256: `c55a0f1c8c760238fc5b029743d1007a0d287ea5b1bc0a3645f3e19630ce00f9`
- Acceptance: `.codex_artifacts/p025/d5c-presentation-offline-v3-acceptance.json`
- Recorded elapsed time: 0.359 seconds; intent/result total: 7,424 bytes.
- All 462 pinned hashes independently rechecked unchanged, including 18 Python
  runtime identities, all prior preservation pins and both original failure receipts.
- All three frozen packet files, ordinary branch HEAD and ordinary index unchanged.
- Source failures remain original
  `45cb9f6fd94a8fd787879d5669cbd8606e0d4b90a9e7015637a1654f38d851e6`
  and V2 `1c0d24c83f7d2584b7cf9f5d4d824cc721e1336511b6307f8122b038d941f6bd`.

Every case ID, outcome and exact guard event was compared to the frozen manifest.
The new accepted result is separate from historical failure state; originals were
not overwritten or relabelled as successful attempts.

## Review and scope

Changes review `68cb2ceb-1c3e-4acd-bc7b-95535732bb01` completed before execution,
with zero reportable findings and all three changed files plus unchanged tests and
direct supporting paths covered. Frozen range:
`9555f61e0d04e36b36b6c63c48b027c92c20cc33` to
`c37d6d70b36b789d17102f2f725a91b9ed1e22e2`.
Syntax, exact two-hunk delta, identical function/class ASTs, manifest lineage,
case selection, hashes and whitespace checks passed before review/execution.
Scan-reported usage: 1,767,461 total tokens, including 1,761,408 cached input tokens;
these are tool accounting figures, not a billing estimate.

The proof is selected real source-body behaviour with explicitly inert transports
and dependencies. It does not establish live Discord persistent registration,
command-decorator authorization or delivery; the complete ZIP/download pipeline;
real Windows event-loop transport; application bootstrap; or effectful C06 recovery
Refresh. Seven guard controls prove the selected paths, not universal Python isolation.
The subprocess control uses all-None handles, not PIPE configurations.

No runtime code, SQL, account/rights/isolation settings, provider operation, VM
work, input or production state changed. Broad pytest/conftest, smoke/registration
and selector execution remained excluded to prevent unrelated startup. Architecture,
deferred and security routing were focused source checks for this test-tooling delta;
there is no SQL contract change, new general deferred item, PR or deployment here.
This acceptance-only documentation addition needs no repeat runtime test or scan.

## Limits and next boundary

Native budget remains **1,361 seconds**, including the protected **1,000-second**
later-phase reserve. Windows-test budget remains **50 seconds**. The **21-input
allowance stays consumed**; no new inputs or old mutation/retry rights were used.
The approved V3 pass is consumed and will not be repeated to refresh evidence.

This accepts the bounded offline C12 presentation packet, not all D5c. The next
source-only step is to reconcile its covered cases against the D5c matrix and
prepare the remaining C01/C04/C05/C06/C09 and any uncovered C12 obligations with
their exact evidence and approval boundaries. Keep already accepted work accepted;
do not replay it. No further runtime correction or native work follows without
the promised findings/plan handback. D5d fault/restart, D5e cost and D5f final
evidence remain ahead. Separate D6 release authorization/deployment is not performed.
