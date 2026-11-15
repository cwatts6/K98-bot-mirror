# P02 D5c reader acceptance and schema orders - 2026-11-12

Status: managed-reader baseline accepted; holder-first packet reviewed and ready for one attempt.

Receipt `d5c-reader-baseline-result-c4fad9570f6447b2966d51b877efd61c.json`
matches SHA256 `B6AA0244B4659E30FF246087BFECDAD02F15E243CC1D67F02850A9D01DAE906A`.
Independent adjudication checked all 28 observations, source hashes, pinned
preimages, original protection, resources and exact cleanup sequence. PID 5648
matched the owned process and exited normally without forced termination.
The real reader used pyodbc 5.2.0 / Driver 18.07.0001, one factory call and four
SQL executions returning three rows. It entered SNAPSHOT in one transaction,
acknowledged rollback, isolation restoration, cursor close and connection close.
The independent observer found both the work session birth and reader application
absent. Its reused work SPID had a different birth and connection identity.

All six completed maintenance rows, 30 candidate images, permissions, ownership,
backup demand and protected-original state match pinned expectations. Disk
reserves passed, log was approximately 2.57%, version store zero. The 61,259-byte
receipt uses 48 reserved command units and 84 reserved row units: 28 actual
wrapper statements/76 rows plus the full 20-command/eight-row child reservation.
These totals are not mislabeled as 48 actual SQL executions. Host elapsed
1.4035759 seconds consumes two seconds, leaving **1,473 native seconds** and
473 of the proposed D5c allocation. **21 inputs remain consumed**.

Acceptance is recorded in `.codex_artifacts/p025/d5c-reader-baseline-acceptance.json`.
All earlier failed readiness receipts were rehashed and preserved. This proves
the lab-factory baseline only; production factory/restricted rights and broader
D5c/d/e/f are still open.

## Next bounded native scope

Prepare two independently adjudicated packets, in this order:

1. An owned session acquires `K98:maintenance-schema:v1` Exclusive/Session with
   zero wait. Capture its birth and actual owned mode. Invoke the unchanged
   managed reader once; require its exact typed busy outcome and native 51966,
   acknowledged cleanup and no entry into the read body. Release the holder,
   verify NoLock, close it and observe both session identities absent.
2. A distinct later managed reader enters its Shared/Transaction guard and records
   actual owned mode. A second owned session requests Exclusive/Session with
   zero wait and must return -1. After acknowledged reader rollback/close, that
   scheduled contender may acquire the same guard, record Exclusive, release it
   and prove NoLock. Close all owned connections and observe physical absence.

The SQL source of truth confirms `dbo.usp_RunMaintenance` uses this exact
Exclusive/Session resource and its children enforce it. These tests exercise
that guard protocol; they do not execute maintenance children or prove actual
child overlap. Fresh D5c demand remains a separate reviewed authorization gate.

No synthetic business rows, permissions, settings, retained inputs or completed
claims change. The exact source modules, executable and extension remain pinned.
Each packet must fit 48 total command units, 2,048 rows, one-MiB receipt and the
existing timing/resource limits, including all actor cleanup. Use fixed queries,
known holder identities and zero-wait requests, never arbitrary sleeps or a
historical-holder inference. Preserve the expected native refusal as evidence.
Any unexpected result or uncertain cleanup stops dependent work; no workload
retry follows automatically. Prepare exact command ledgers and offline failure
tests, then complete Changes review before either handoff.

## Holder-first packet prepared

The first packet uses the verified base interpreter, exact native extension and
unchanged six-module helper bundle. One lab holder and one real managed reader
share a unique application identity but must have distinct SQL births. The
holder records Exclusive ownership, the reader must raise ObservationBusy with
native 51966 after acknowledged cleanup, and the holder must acknowledge release
with NoLock before normal close. Any different busy code, admitted read body,
unknown close or release error fails the packet; no retry is permitted.

Maximum reservation is 24 wrapper statements plus 24 child command units = 48.
The child uses at most three holder statements and two reader executions on the
expected refusal path; all connect/control/cleanup paths fit its reserved units.
Wrapper maximum rows64 plus child reservation12 =76, below the existing caps.
The four omitted baseline statements are prior table/principal discovery, file
census and candidate-image collection. This guard-only packet invokes no
application or maintenance procedure, so their inventory is retained from the
accepted baseline. Identity, protected-original, ownership, permissions, ledger,
backup, session context and resource checks remain, including paired poststate
and independent physical work/actor session absence. Accepted baseline receipt
bytes are pinned before admission.

Six fake-driver tests passed, including wrong holder identity, accidental reader
admission, unknown reader close, failed holder release, and a different busy code.
Ninety-four PS5.1 offline checks passed. Ruff, architecture, deferred-item and
security-routing checks passed. No native schema packet has run. Full application
tests/startup remain outside this bounded packet; selection follows the prior
isolated reader test rationale. Source-only Changes review is required before
handoff, with Deep off and no SQL-repository change.

## Holder-first handoff ready

Changes scan `ff98c177-e915-485e-9cbb-971b8dfbfd4c` completed with zero findings
and complete scoped coverage. Independent source review found no execution
blocker. Immutable review head is `73a2d5a86a8aeaebb1ef5c1d67109b82d3e73131`.
Measured review usage was 1,489,271 tokens, including 1,477,120 cached input tokens;
this consumes no native rehearsal budget. Test selection was run for all four
source/test paths; broader startup/full-suite recommendations remain excluded
under the documented isolated-packet scope.

Wrapper SHA256:
`AE54F7E14CEDF0E6CBE67A7725A9599CCADB7341581F0B9A312C38B785A28BFA`.
Manifest SHA256:
`62736d3cf32eb04c9ce1740c31227c8c6fe3b3be9afa51f61d35c5876c2ca3ff`.
Native balance remains 1,473 seconds. Only one holder-first attempt is ready;
adjudicate its immutable receipt before preparing the reader-first handoff.
This final status addition changes no executable/manifest bytes.
