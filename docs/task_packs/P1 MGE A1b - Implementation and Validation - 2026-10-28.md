# P1 MGE A1b: local implementation and validation

Status: approved local implementation and Windows validation complete on 29 October
2026. Linux execution was unavailable on this host, as documented below. Publication, merge, updater installation, deployment, restart and live
SQL/provider operations are separate and have not been performed.

## Custody

- Managed implementation worktree: `p1-mge-a1b/discord_file_downloader`.
- Mirror source base: `8ce3234c54fccebea018ac95f49a2d5076db68c5`.
- Merged handover: mirror PR 455 / `8db65da6`, private PR 703 / `07d5dd17`.
- Preserved design branch: `codex/p1-mge-a1b-design`, `a025adb7`.
- Local slices: B1 `codex/p1-mge-a1b-b1` / `8e7a79b6`; B2 `codex/p1-mge-a1b-b2` / `04351a04`, followed by reliability corrections
  `47c8e316`. The design-only delta was
  carried from the merged handover without resetting the original checkout.
- Deployed runtime evidence remains private `87c1b393`; local changes are not deployed.

## Requirement and evidence map

| Requirement | Implementation / caller evidence | Current validation |
|---|---|---|
| Q1 qualified presentation | Strict MGE DAL metadata checks; event/row/join/lifecycle/identity preparation; all three board delivery guards | Full Windows suite passed; qualification and dataset-validity regression modules cover empty, malformed, unavailable and identity-conflict paths |
| O1 exact action outcome | Roster, targets, rules, modes and signup evidence adapter | Actual DAL primary/audit failure, partial/unknown, wrong-event and private recovery-reference regressions passed |
| R1 reply-independent refresh | Both leadership UIs, signup/edit/withdraw/admin-add, rules/modes | Two actual rules callers plus shared signup caller prove register-before-reply and reply-gated delivery through failure; full caller suites passed |
| C1 coalescing and semantic keys | Owned per-target refresh and dynamic reply-release gates | Dirty follow-up, late gate, cancellation, refusal and shutdown tests passed; five compatible requests coalesce to one pass in every measured sample |
| I1 lifecycle/identity ownership | Publish/unpublish primary transitions, refresh and journal reconciliation | Barrier tests cover both primary/refresh orderings; conditional ID predicate, full revision, historical receipt and saved-publication/render-failure tests passed |
| L1 drain/recovery | Private/background admission, finite startup sweep, periodic recovery | Bounded 52-event/two-page sweep, poisoned target, cursor hold, journal retry, calendar failure and drain regressions passed; measured outstanding work always zero |
| E1 measurement/release evidence | Frozen harness, source manifests, updater pins and security reviews | 660 final sequential samples; full Windows/log-isolation pass; three Changes reviews complete; all 41 source pins and 50 historical entries verified |

Caller tests and shared ownership barriers support the local evidence below; helper
tests alone do not supply production acceptance. Runtime/operator
acceptance and the carried R01-R18, WS1-WS6 and P0 boundaries remain unchanged.

## Validation environment

Windows Python 3.11.9. Final validation uses the managed worktree
`.venv/Scripts/python.exe`, with existing dependency files supplied through a local
site-packages path loaded through `site.addsitedir`, including the existing
Windows extension paths. No dependency download or interpreter-guard bypass was used. Initial restricted test startup could not create worktree-local
test directories. That run was stopped and is not counted. The permitted offline
rerun passed 74 tests in 4.67 seconds. No SQL/provider call is validation evidence.

B1 wider MGE run: 574 passed and two failed in 23.21 seconds. Failures are the
current-source assertions in `test_mge_a1a_update_transition.py` and
`test_mge_update_transition.py`, because the runtime bytes intentionally changed.
At that intermediate checkpoint these were unresolved gates. The final exact
successor and authenticated historical bridge now resolve them without changing
original historical pins. Final B1 qualification tests: 45 passed in 1.97 seconds. Ruff, Black,
architecture (11 Python files), deferred and routing validators and whitespace
checks pass. This is an intermediate local slice, not release readiness.

Security routing: three completed Changes reviews, Deep off, on immutable local
Bot ranges (details below). No SQL repository change or repository-wide audit was
performed. Final full-suite and benchmark evidence are recorded below.

## B2 implementation evidence

- Ordinary roster, target, rules and mode results carry explicit primary, secondary
  and audit evidence. Existing required audits are checked; this does not add a new
  audit policy to notes or waitlist-order writers. Unknown transaction settlement
  remains unknown. Confirmed earlier writes survive a later audit or target failure.
- Simplified leadership, legacy roster, signup/edit/withdraw, admin-add, rules and
  mode callbacks use the result adapter. Legacy roster snapshots remain available
  through Show Roster, and the existing legacy versus simplified DM policy remains.
- Refresh registration precedes the private reply. A reply-release gate prevents
  refresh IO before that attempt; failure releases owned work. Delivery observers
  report delivered, pending, refused, failed or not-requested per target. Ordinary
  results never promise delivery; explicit refresh observes for ten seconds without
  cancelling the operation. Newer requests during a pass cause a fresh pass.
- Publish/unpublish primary transitions share the event presentation owner with
  refresh, including state change, Discord send/delete and identity settlement.
  Recursive refresh and notifications run after releasing that owner. Conditional
  ID writes compare status, rule mode, publish version, exact SQL revision and IDs.
  SQL datetime2(7) precision is retained as an ISO revision token; Python's
  microsecond datetime is not used as the exact comparison value.
- The recovery inventory uses EventId high-water/keyset pages of fifty and at most
  two event tasks. Startup covers persisted identities including completed events
  outside the calendar window; periodic sweeps cover noncompleted events. Known
  identities are edited only, without placement, creation or mentions. Failed pages
  retain their cursor; failed targets do not starve later events. Progress includes
  scanned, eligible, refreshed, held, failed, outstanding and cursor/high-water state.
- A journal acknowledgement can restore a missing SQL ID only with matching key,
  event, kind, destination, lifecycle/revision and previously absent identity.
  Legacy, uncertain, superseded or cleared bindings remain held, never replayed.
- Shutdown closes new private/background admission together. Already admitted
  private work may register refresh continuation; private work drains before board
  work, while delivery remains available. Ten-second drain observations report
  pending work without cancelling threads, primary transitions or receipts.

### Concrete regression coverage

| Contract | Tests |
|---|---|
| Qualified shape/empty/identity/payload | `test_mge_board_qualification.py`, `test_mge_dataset_validity.py` |
| Actual settled DAL and partial audit results | `test_mge_action_evidence.py` |
| Two actual rules callers: reply order and failed transport | `test_mge_action_evidence.py::test_real_rules_callers_register_before_reply_and_release_on_transport_failure` |
| Shared pass, dirty follow-up, timeout/cancellation, target separation, refused target, drain | `test_mge_refresh_ownership.py` |
| Publish/unpublish versus refresh in both orderings; exact conditional ID predicate | `test_mge_publication_ownership.py` |
| Restart keyset/high-water, poison target, failed page, receipt binding, calendar failure | `test_mge_recovery.py`, `test_mge_board_delivery.py` |
| Existing permission/caller/lifecycle behavior | MGE view, command, lifecycle and service suites |
| Exact fixed release bundle and historical source bridges | `test_mge_a1b_update_transition.py`, `test_a1b_source_bridge.py` and predecessor suites |

### Release qualification boundaries

The local successor is `p1_mge_a1b_v1`: forty-one exact source/dependency members.
All fifty historical transition entries remain byte-equivalent as canonical JSON.
The count cap increases only to fifty-one and registry byte cap from 96 KiB to
100 KiB; the candidate registry is 100,849 bytes. This is one fixed bundle, not a
new wildcard admission rule. Every member/predecessor/required absence is pinned. A local source comparison
against deployed private revision `87c1b39325daaa0ca1a8c0cbca656df82d7fa46b`
matched all 41 predecessor entries, including required absences; this is source
compatibility evidence, not proof of what a running process loaded.
Candidate policy changes do not authorize their own installation: a separately
reviewed installed updater upgrade is still required before ordinary deployment.
No installed updater, production checkout, SQL schema or live data was changed.

B1 Changes scan `a8ccabd7-1036-4c8b-b61d-a663e0d0ad6f` completed on immutable
`8ce3234c..8e7a79b6`: all nine changed source files reviewed, no candidates/findings.
B2 Changes scan `5acb8539-3e6c-4c92-8511-f90d9220f452` completed on
`8e7a79b6..04351a04`: all 36 changed source/configuration files reviewed, no
candidates/findings. Correction scan `3b892385-be30-42e5-9c54-6845f84489cb`
completed on `04351a04..47c8e316`: all seven source/configuration files reviewed,
no candidates/findings. Each scan included directly supporting control paths;
no incomplete coverage or deferred security candidates remain.

The review also identified reliability edges, corrected within A1b:

- Uncertain rules edit/reset preserves the known signup destination for its
  read-only refresh; an unconfirmed write still never receives a green success.
- Unknown signup outcomes retain the private administrator reconciliation reference.
- Payload or adapter exceptions after publication settlement return the saved
  publication version and an unconfirmed-board result, without a blind retry.
- Gates registered while a shared pass waits join before it enters its read/delivery
  factory; an already executing pass retains its dirty follow-up semantics.
- An unavailable startup journal read remains pending for the next scheduler tick.
  Successful inspection retires that read, even when individual receipts are held.

The focused correction suite passed 55 tests in 2.30 seconds. Regression cases
cover the actual rules DAL outcome, private recovery reference, post-commit
render failure, late gate registration and a three-tick journal retry sequence.

The final benchmark-only amendment records existing request, coalescing and failed
pass counters. The test amendments also update the existing cross-caller reply-order assertion
to exercise a real gated refresh and route the generic historical A1a registry
assertion through the authenticated A1b source bridge. Original historical hashes
remain unchanged; the new successor is checked against its exact current bytes.
Other test amendments are formatting-only. A new security
scan is skipped for that exact nonbehavioral delta: no runtime, authority, IO,
privacy or deployment-control behavior changes.

### Recovery and acceptance limits

Startup's historical-target inventory is deliberately one finite pass. A failed
completed-event target does not block later pages and is not automatically retried
by the noncompleted periodic sweep. Its saved identity/evidence remains retained;
a future authorized existing-only reconciliation may revisit it. Completion of the
inventory means its cursor reached the bound, not that every target delivered.
Read `failed`, `held` and `outstanding` alongside `complete`. Receipt-read failure
is different: it remains pending and retries at the scheduler cadence.

The owner is process-local. It does not establish a cross-process roster snapshot
transaction or make legacy multi-step writers atomic. R12 remains separate. The
finite recovery pass never creates missing messages or reruns business mutations.
Linux pytest was not run: the host exposes only the Docker Desktop WSL distribution,
and its Docker daemon is not running. No runtime was installed or started for this
check. Native Linux qualification remains a separate unclaimed result.

The first broad Windows run was stopped after the bot correctly rejected an
interpreter from the original checkout. It is not counted as a product failure or
as final validation. Eighteen affected import/offload checks then passed using the
worktree-local interpreter in 10.26 seconds. The final full-suite run uses that same
local interpreter and protects operational logs. The first complete local run
reported 10,536 passed, 1,101 skipped, four failed and 25 setup errors in 1,049.31 s.
The native Windows failures/setup errors were missing `win32api`/`ntsecuritycon`
from incomplete dependency-path loading, not runtime implementation defects.
The other two failures were the old reply-registration ordering assertion and
an unbridged historical updater-source assertion. All 89 tests in their affected
modules passed after those environment/test corrections, in 20.94 seconds.
The definitive full run is rerun after these corrections; the diagnostic run is
retained and is not represented as passing or as log-isolation proof.

Authoritative SQL fields were rechecked in the SQL repository at `7e91989f`:
`dbo.MGE_Events` has the EventId primary key, persisted board IDs and `UpdatedUtc`
`datetime2(7)`. Recovery and conditional writes require no schema migration.
No SQL object, provider data, installed updater or deployed process was changed.

Keep the complete carried-item table in the approved design packet: R01-R18,
WS1-WS6, natural P0 F04 and F01-F05 reconciliation, CFG-51421 operator choice,
Report 62 queue closure, gateway-lag evidence, A2 Ark admin-add and remaining
natural acceptance. Earlier accepted predecessor work is not reopened by A1b.


### Security measurement provenance

The completion tools reported the following measured Codex rollout usage. These
scan windows can overlap; they must not be added into a task-total estimate.
All returned usage coverage values were `complete`.

| Review | Total tokens | Input tokens | Cached input tokens |
|---|---:|---:|---:|
| B1 | 5,488,219 | 5,475,494 | 5,339,520 |
| B2 | 5,629,150 | 5,614,525 | 5,442,304 |
| B2 corrections | 849,013 | 846,781 | 834,304 |

Sealed reports are retained in the local Codex Security workbench under the scan
IDs above. The advisory access check returned no Daybreak grant; no elevated
access was assumed. The completed source reviews and their coverage are local
evidence, separate from live system acceptance.

### Local handoff and later release sequence

The local K98 review covers the composed mirror change, SQL source alignment,
private/public response behavior, restart ownership, exact source protection and
security evidence. The review corrections above are addressed; no additional
blocking implementation issue was identified. Completed full-suite and benchmark evidence is recorded below. This is not a production promotion
review or authorization to publish/merge.

The two intended review slices remain B1 (`8ce3234c..8e7a79b6`) and B2
(`8e7a79b6..codex/p1-mge-a1b-b2`), with one combined production release later.
The runtime correction checkpoint is `47c8e316`; `dcb1c3c6` freezes benchmark
counters/measurement notes and formats three already changed tests. Runtime bytes
are unchanged by that latter checkpoint. `efd2e5d5` records the corrected shared
caller and historical registry assertions; it also changes no runtime bytes. Final evidence/navigation commits add no
runtime behavior and do not require refreshing the exact source pins.

Later stages, when separately requested: publish/review the mirror
slices from a suitable mirror checkout while preserving the current push guard;
promote equivalent reviewed patches to the private repository; qualify and install
the exact supported updater pair; then deploy private main and perform the bounded
natural acceptance checks. No intermediate B1-only deployment is implied. Keep
receipts and committed business data across release or rollback; never repeat
uncertain operations to manufacture acceptance.

## Final Windows validation and frozen measurement evidence

**Full Windows suite:** 10566 passed, 1100 skipped, 1 warning, 8 subtests passed in 1025.83s (0:17:05)

The protected-log wrapper passed: `logs/log.txt`, `logs/error_log.txt`, `logs/crash.log` and `logs/telemetry_log.jsonl` were unchanged. Full output is retained locally as `a1b-full-final-tests.log` (SHA256 `1f0b5bd6ab8187df29e607ce806d99ecb8c95b6315c8eb849b0ecbc943334c20`). Earlier diagnostic runs remain separate.

Architecture, deferred-item and security-routing validators, explicit-path test selection, Ruff, Black, import smoke and command registration pass. Registration remains 36 primary commands and 102 grouped subcommands, with no duplicate or top-level drift. Runtime files remain the reviewed `47c8e316` image; later commits contain tests, measurement and evidence only.

The frozen harness is `scripts/benchmark_mge_refresh.py`, SHA256 `08d9bdd48709efcb5468e9be055177bddac8cb005bc92b2def0a45a924b43efe`. Baseline source revision is `a025adb7a69aac321fd62794b871ed5903338f44`; candidate is `efd2e5d562b2a1453fe88b74116f76d6997a82b5`. The baseline is the preserved design checkout with the unchanged A1a runtime; its predecessor-source equivalence is verified above. Each raw artifact includes source-file hashes, raw observations, aggregate stage timings and measurement semantics.

Final runs used the same Windows host/interpreter, sequentially without concurrent validation, 30 observations per case per source, and a 10 ms simulated base IO setting (300 ms configured board delay in the slow case). Native SQL and Discord IO are replaced by fixtures; live SQL connection entry is denied. One-millisecond exploratory samples and runs overlapping a stalled formatter were excluded and retained only as local diagnostic files. Windows asynchronous timers remain coarse at small intervals: configured delays are not measured minimum delays, and acknowledgement/loop-lag figures are host-specific. The slow-board comparison and deterministic barrier tests establish the response-ordering benefit. These data establish no production SLA or native SQL latency.

[Baseline raw observations](evidence/p1_mge_a1b_baseline_2026-10-28.json) and [candidate raw observations](evidence/p1_mge_a1b_candidate_2026-10-28.json). All times below are milliseconds; each cell is p50 / p95. Result time measures completion of the private reply attempt, not proof of delivery. Zero means the case has no private reply. End-to-end time includes refresh drain.

| Case | Baseline result | Candidate result | Baseline end-to-end | Candidate end-to-end |
|---|---:|---:|---:|---:|
| payload_0 | 0.00 / 0.00 | 0.00 / 0.00 | 21.15 / 21.57 | 21.47 / 21.90 |
| payload_4 | 0.00 / 0.00 | 0.00 / 0.00 | 32.01 / 32.45 | 32.17 / 32.79 |
| payload_15 | 0.00 / 0.00 | 0.00 / 0.00 | 32.04 / 32.82 | 32.42 / 33.10 |
| payload_30 | 0.00 / 0.00 | 0.00 / 0.00 | 32.25 / 32.59 | 32.97 / 33.69 |
| rank_select_4 | 61.61 / 63.15 | 61.72 / 63.06 | 61.74 / 63.29 | 61.91 / 63.53 |
| rank_submit_4 | 201.37 / 216.84 | 25.71 / 26.58 | 201.46 / 216.94 | 201.99 / 204.61 |
| overlap_4 | 278.85 / 295.83 | 22.01 / 22.49 | 278.96 / 295.94 | 263.90 / 280.43 |
| slow_board_4 | 1328.48 / 1344.85 | 25.89 / 26.41 | 1328.58 / 1344.96 | 1309.85 / 1327.36 |
| reply_failure_4 | 203.26 / 218.79 | 25.73 / 26.42 | 203.39 / 218.92 | 201.76 / 205.50 |
| partial_4 | 31.22 / 31.75 | 25.81 / 26.27 | 31.31 / 31.86 | 172.52 / 189.00 |
| repeated_refresh_4 | 0.00 / 0.00 | 0.00 / 0.00 | 77.57 / 79.04 | 63.13 / 79.14 |

The four payload sizes retain their read counts. Rank submission adds one final event-membership award read and removes one separate leadership-identity read: eight simulated query connections before and after. Overlap removes two separate identity reads and adds one membership read, reducing thirteen to twelve. Partial outcomes now trigger the intended read-only reconciliation: seven reads and two existing-message edits versus none on the old failed-result path. That extra work is explicit and drains fully; the mutation is not retried.

| Case | Reads before / after | Edits before / after | Candidate requests / passes | Candidate ack p50 / p95 | Candidate max loop lag p50 / p95 |
|---|---:|---:|---:|---:|---:|
| payload_0 | 2 / 2 | 0 / 0 | 0 / 0 | 0.00 / 0.00 | 14.15 / 15.03 |
| payload_4 | 3 / 3 | 0 / 0 | 0 / 0 | 0.00 / 0.00 | 14.63 / 15.78 |
| payload_15 | 3 / 3 | 0 / 0 | 0 / 0 | 0.00 / 0.00 | 14.64 / 15.50 |
| payload_30 | 3 / 3 | 0 / 0 | 0 / 0 | 0.00 / 0.00 | 14.65 / 15.82 |
| rank_select_4 | 3 / 3 | 0 / 0 | 0 / 0 | 15.31 / 15.89 | 14.75 / 15.44 |
| rank_submit_4 | 8 / 8 | 2 / 2 | 2 / 2 | 4.21 / 4.79 | 15.13 / 15.43 |
| overlap_4 | 13 / 12 | 3 / 3 | 2 / 2 | 0.28 / 0.33 | 15.12 / 15.32 |
| slow_board_4 | 8 / 8 | 2 / 2 | 2 / 2 | 4.16 / 4.67 | 15.39 / 15.59 |
| reply_failure_4 | 8 / 8 | 2 / 2 | 2 / 2 | 4.14 / 4.80 | 15.08 / 15.36 |
| partial_4 | 0 / 7 | 0 / 2 | 2 / 2 | 4.29 / 4.73 | 15.11 / 15.26 |
| repeated_refresh_4 | 3 / 3 | 1 / 1 | 5 / 1 | 0.00 / 0.00 | 15.01 / 15.35 |

All 660 samples finish with zero outstanding owned children. Five rapid compatible refresh requests produce one pass and one edit. Ordinary mutation samples execute one fixture mutation and one fixture audit; partial samples execute one mutation and zero confirmed audits. Reply-failure samples record one failed reply attempt with completed owned refresh. These counters are simulated boundary evidence, complemented by actual DAL outcome and deterministic barrier tests; they are not live transaction receipts. Inclusive stage timings overlap and must not be summed.
