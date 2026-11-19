# P02 D5d G1 closeout and native preparation

**G1 is complete within its bounded offline scope: 47/47 behavioral cases passed,
11/11 runner controls passed, zero failed or unexecuted cases. Three D5d work
groups remain: G2, G3 and G4.** D5c stays closed with zero remaining checks.

This records qualification under the existing approval. It is not production
deployment, native fault/restart acceptance, or a request for renewed permission.

## Frozen denominator and result

The [scope and exact selection rationale](Startup%20Import%20Export%20Reliability%20-%20P02%20D5d%20G1%20Grouped%20Offline%20Qualification%20-%202026-11-15.md)
remains unchanged as part of the frozen packet. Its 47 behavioral cases comprise
four threaded setup, fourteen dispatch/handle-custody, thirteen checkpoint and
sixteen nested-cleanup cases. Eleven runner controls are separate; they are not
eleven additional product scenarios. The 141 adapter setup/call/teardown entries
are phase accounting, not independent pytest tests.

The one qualification attempt passed in 0.703 seconds with 19,469 bytes across
intent and result. The independent receipt reconciliation checked exact ordered
case identifiers, all outcomes/phases, no unexecuted cases, no live other threads,
eight expected refusal events and no unexpected event. All 2,403 pinned bounded
source/evidence/index files remained unchanged. Both repository HEADs and the
handover's source/evidence pins matched again. The retained VHDX was not modified
or content-hashed as part of the qualification manifest.

- [Acceptance record](../../.codex_artifacts/p025/d5d-g1-acceptance-20261115.json)
- [Original result](../../.codex_artifacts/p025/d5d-g1-qualification/result.json), SHA256 `2d71aab6f660b84b5f8dbc5ba280bd8b3f9612bb284d4072288f332897a05a69`
- [Frozen packet](../../.codex_artifacts/p025/d5d-g1-qualification/packet.json), SHA256 `726862ade69f2f98626a5232da9f03ec7e6e79e02b0ce5ee4f39d44cfcde59bc`
- [Original intent](../../.codex_artifacts/p025/d5d-g1-qualification/intent.json), SHA256 `9579faca5d4d5809dd966209631c0ed5aa38263dc0436d6f84a04a1cb0979145`

The accepted 42 local drain checks and 38 earlier custody checks remain carried
evidence. None was replayed. No production defect or production-source change was
needed. The original helper/test files were preserved; additions are the G1
runner, selection adapter and documentary/evidence files.

## Preparation and review evidence

Preparation retained its failures separately. Initial manifest generation
mistakenly included the 97,513,373,696-byte qualification VHDX in a read-only hash
selection; the owned generation command was interrupted and exited without a
packet. A premature preparation launch refused the absent packet before intent
or tests. The next bounded-text manifest loaded the source graph and exposed a
missing `ImportExecutionActive` exception-class binding in the isolated loader.
That failed receipt is preserved in `d5d-g1-prep-02/result.json`. The corrected
binding reused the original class and changed no application source.

`d5d-g1-prep-03/result.json` then passed all eleven controls, including original
writer-fixture construction, exact source selections, clock isolation, forbidden
effects, thread refusal and receipt serialization. Preparation ran zero of the
47 behavioral cases. The reviewed final qualification repeated only its runner
controls, then ran each selected behavioral case once.

Changes review `16c1fe18-9436-4cca-b1b8-ae14fc06f63b`, Deep off, completed with no
reportable findings and complete coverage of both new Python files. Exact review
range: `e7443e37212ca91e20d531b3684cc369d0fe1505` to
`2bd0bdb0914d47a451392042ce9585a2063ac875`. The latter is an unreferenced review
snapshot built with a separate index, not a branch change, PR, or deployment.
Both source blobs were compared with that snapshot before qualification. The
accepted bootstrap loader was externally hash-checked before invocation.
Independent architecture review checked fixture dependencies and thread paths.
SQL had no changed source and retained the documented no-diff skip.

Architecture, deferred-item and security-routing validators passed. Test selection
was run for the two files; broad suites/import smoke/command registration were
explicitly skipped for the isolated harness boundary. Both files compile and the
runner passes targeted fatal/undefined-name lint checks. No claim is made that the
AST-injected test adapter is an ordinary pytest module or that full pytest ran.

Tool-reported scan usage: 5,580,568 aggregate rollout tokens, including 5,450,624
cached input tokens. This is not incremental billing or qualification-time usage.

## Proof limits and remaining groups

Original source bodies and assertions were exercised with fake SQL/transport,
inert diagnostic records and an inert writer store constructor. Selected real
Python threads physically finished. This does not establish SQL connection
termination, native rollback/durable commitment, Windows file/job ownership or
provider effects. Synthetic uncertain handles remained strongly referenced until
the test process exited; no native custody registry was reset.

| Group | State and next proof |
| --- | --- |
| G1 | Complete: original failure preservation, nested synthetic custody/capacity and no offline replay after lost replies. |
| G2 | Open: native pre/post-entry cancellation, failed owner, lost grant reply, rollback/reset/cursor/guard/close uncertainty and independent exact physical closure; include equivalent factories and shared Ark/file custody. |
| G3 | Open: map all six real-child maintenance boundaries to remaining faults and committed-effect preservation; truthful backup demand/attempt/completion without real backup for permission checks. |
| G4 | Open: old process birth/owner plus durable outcome must control re-entry; process death/restart and lost commit/dispatch reply. Group the unexecuted synthetic birth/ACK guard cases with this physical packet. |

No exact native case denominator has been invented. Existing D5c native-final
transport, source-bundle and PowerShell custody patterns were inspected for reuse.
Their consumed intents and historical operation budgets must not be reused. The
next packet needs new exact case IDs, source/statement/row/process bounds,
independently provable per-case cleanup and stop-on-uncertainty before review.

## Allowances and operator handoff boundary

Native balance stays **1,248 seconds**, of which **1,000 seconds remain protected
for later D5**. G2-G4 currently have only the unreserved 248 seconds collectively;
allocate D5e/f's reserve jointly with native packet preparation and record any
necessary approved extension before execution. Windows-native test balance stays
50 seconds. Inputs remain 21 consumed; synthetic SQL rows remain 67 consumed.
No allowances were reset and no inputs/rows/native operations were added.

The next native packet must verify `$global:D5bReportSession`, recorded name
`D5cResume`, instance `b09386eb-cc29-40b3-8f31-75636e9fe3da`, in the operator's
console. The agent cannot access that console's session. Check availability before
asking for reconnection, and verify the exact VM and database identities from the
[handover](Startup%20Import%20Export%20Reliability%20-%20P02%20D5d%20Scope%20Reconfirmation%20and%20Chat%20Handover%20-%202026-11-15.md).
Preserve both disposable databases, original database, rows, source, VHDX, receipts
and all consumed/uncertain intents. No operator PowerShell is issued at this
offline boundary because no complete reviewed native packet is ready.

D5e cost and D5f integration/readiness remain after D5d. D6 production deployment
is separate; actual P03 blockers and essential P04 corrections still precede first
normal import/export. SQL 3961, historical Linux CI causation and natural/provider
acceptance limitations retain their existing owners. No unrelated refactor or
deferred optimisation was introduced.
