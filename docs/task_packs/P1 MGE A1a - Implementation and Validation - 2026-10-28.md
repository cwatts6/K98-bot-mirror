# P1 MGE A1a: implementation and validation

Date: 28 October 2026. Scope: operator-approved local implementation and validation
of amended A1a, including the dataset-validity prerequisite and framework additions.
Branch: `codex/p1-mge-a1a-dataset-validity` from mirror
`8b55400700c392823906f7ae4951383e1c7c7c10`.

## Result and boundaries

Leadership rendering and displayed readiness now share one qualified preparation.
Strict reads distinguish a successful empty/populated dataset from unavailable
data; automatic placement failures/readback uncertainty produce incomplete data.
Neither error is rendered as an empty roster or admitted for publication. Existing
board/message references are retained. Placement policy, manual ranks, rejections,
waitlist ordering and successful-empty policy are unchanged. Publication checks
fresh data instead of trusting the displayed snapshot.

Automatic placement was a hidden writer in the read path. Preparation now shares
the reentrant process event owner with roster workers. It stops at unconfirmed
placement/readback without retrying or claiming rollback. Signup transactions and
other processes remain separate competing writers; there is no new global SQL
transaction or whole-publication consistency guarantee.

Correlated stage timing is observational and covers actual signup/rank callbacks,
owned workers, preparation and board delivery. Inclusive stages must not be added
together. See the [shared lifecycle contract](../reference/p1-operation-lifecycle.md)
for meanings, redaction and the reusable adoption/closure record.

A1b remains separate: early saved-response and refresh coordination, including
public-signup strict-data adoption before changing its refresh policy. A1a does
not implement coalescing, dirty-follow-up changes, new retry rules or Ark fixes.
The subsequent operator request authorizes PRs, review corrections and mirror/private
merges. Deployment, restart, live SQL apply and provider operations remain outside
this development task.

## Caller and owner inventory

| Caller | Entry / data owner | Mutation / delivery / uncertainty |
|---|---|---|
| Leadership rank selection and prepared forms | `MGESimplifiedLeadershipView._load_board_payload`, owned thread then event thread owner | One qualified snapshot; private error on failed data; form submission still revalidates |
| Rank/target/admin-add/reject/reset in simplified UI | `run_roster_mutation`, async event owner then reentrant thread owner | Existing service/DAL writes and outcome contracts; refresh/reply independent of persistence |
| Legacy roster builder | Same `run_roster_mutation` owner across complete service call | Second mutation caller; existing audit/transaction limitations retained |
| Leadership board (scheduler, command, manual, signup and mutation triggers) | Bot/event board lock, owned preparation thread, event thread owner | Snapshot reused for readiness; read failure returns false before Discord/ID writes |
| `mge_scheduler.py` interval sync | Calls board sync under existing target-specific owner | Current state reread; does not borrow user admission or change notification keys |
| `commands/mge_cmds.py` refresh and `mge_signup_view.py` saved signup refresh | Existing acknowledgement/private response and board sync | Signup SQL transaction remains its own authority; board failure cannot undo saved signup |
| Publication (`publish_event_awards`) | Fresh readiness and fresh publish-set preparation through roster owner | No display cache authority; failed strict preparation blocks before publication; broader publish races remain R12 |
| Simplified leadership service direct preparations | `get_ordered_leadership_rows` owns synchronous preparation | Call off-loop; reentrant inside roster worker; no thread owner across Discord/await |
| Public signup and award boards | Existing board serialization, delivery journal/identity contracts | Timing only; public signup reads retain legacy empty-on-error behavior pending A1b adoption |

Lock order: optional async roster owner -> thread owner -> existing DAL transaction.
Board owner -> thread owner for board preparation. Roster owner is released before
board delivery. Different events can proceed independently; cancellation drains
the entered worker before releasing ownership. No cross-process assertion follows.
Existing board journal remains authority for known/unknown sends and same-message
identity; the timing reference is not a durable mutation receipt or replay key.

## SQL contract and source evidence

Validated against `C:\K98-bot-SQL-Server` at
`7e91989f619deb46836194c7e705b0a9eb2ebe11`: `dbo.v_MGE_SignupReview`,
`MGE_Events`, `MGE_Signups`, `MGE_Awards`, signup/award audits, and current placement
insert contracts. No SQL text, schema, index, migration or permissions changed.
Strict flags change Python error propagation only. The legacy insert's missing ID
does not prove rollback; automatic placement therefore returns incomplete.

Historical updater pins remain unchanged. `tests/fixtures/p1_a1a_source_pairs.json`
and the test-only successor bridge authenticate exact local source bytes before
walking the historical assertions. They grant no installation authority.

Release qualification found that the installed updater correctly refuses six
protected source changes. The release adds `p1_mge_a1a_v1`: an indivisible exact
12-file predecessor/successor bundle, including the new timing/error modules. All
49 historical entries remain byte-for-byte semantically unchanged; only the entry
count bound increases to 50, with the existing 96 KiB bound retained. Unknown,
partial, mismatched and target-self-authorized source remains refused. The matching
updater package must be installed through the existing exact-version upgrade before
bot deployment. Tests authenticate every member and both predecessor/successor
states. This release addition is covered by a fresh Changes review.

## Repeatable offline comparison

Harness: `scripts/benchmark_mge_refresh.py`; 30 samples per case; simulated 1 ms IO;
real payload/rank callbacks with fake DAL/Discord and native SQL connection denied.
Baseline checkout `41fbd0ac93f7e823e194162853425a327f61e0e4` has identical runtime
source to the approved base (subsequent base changes were documentation only).
Both JSON records retain harness/source hashes, raw observations, medians, p95,
read/connection/edit/reply/mutation counts and loop-lag samples. Candidate also
retains inclusive stage timings. These are local scheduling observations, not
native SQL costs, Discord latency attribution or production speedup estimates.

| Case | Dataset reads before -> after | Simulated read connections before -> after | Discord edits before -> after |
|---|---|---|---|
| Empty payload | 4 -> 2 | 4 -> 2 | 0 -> 0 |
| 4 / 15 / 30 signup payload | 6 -> 3 | 6 -> 3 | 0 -> 0 |
| Rank selection, 4 signups | 6 -> 3 | 6 -> 3 | 0 -> 0 |
| Rank submission, 4 signups | 8 -> 5 | 11 -> 8 | 2 -> 2 |
| Rank submission + overlapping scheduler board | 14 -> 8 | 19 -> 13 | 3 -> 3 |

The remaining populated readback is intentional: preparation can write. Final
rank response still waits for both boards. Reduced reads alone do not establish
better initial acknowledgement or eliminate presentation latency.

Artifacts: [baseline](../benchmarks/p1_a1a_baseline_20261028.json) and
[candidate](../benchmarks/p1_a1a_candidate_20261028.json).
Repeat with the same harness, `--source-root <checkout> --output <file> --samples 30`.
Run baseline/candidate sequentially on the same machine; avoid comparing busy and
idle host runs as evidence of a code speedup. Failure/ownership gates use deterministic
tests, not benchmark timing thresholds.

## Validation and review

Changed surfaces: shared timing/owned work/private responses; strict MGE data,
leadership preparation/readiness, board refresh and publication admission.
The selector recommends full pytest plus smoke imports and static registration.
Risk additions cover empty/error distinction, wrong-event snapshots, partial
placement, readback failure, snapshot freshness, retained board identity, callback
private errors, both real timing consumers, concurrent preparation, other-event
progress and repeated cancellation. Existing MGE/event-delivery tests retain
permission, stale admission, unknown-send and dirty-follow-up behavior coverage.

Local gate results and Changes review are recorded below after final validation.
Security decision: Changes review of this Bot working-tree patch, Deep off, because
DAL, interactions and logging changed. SQL repository review is not applicable to
an unchanged SQL tree. Tests do not substitute for the security review.

### Final local results

- Final broad sweep: **9,841 passed, 1,100 skipped, eight subtests passed, one
  failed historical source assertion**, 492.10 seconds. The failing
  `test_updater_reader_capabilities` assertion was adapted to the same exact local
  successor bridge already used by the other historical-release tests. At that local-validation checkpoint, production updater source and registry were
  unchanged; the subsequent release-qualification addition is documented above.
- After that test-only correction: **220 passed**, 10.27 seconds, covering the full
  updater-reader/MGE transition suites, both source bridges, dataset validity,
  timing, owned operations and event delivery. Protected operational logs were
  unchanged in this final run. No known task-related test failure remains.
  A warning-visible repeat also passed all 220 tests; its only warning is the
  installed Google library's Python 3.11 future-support notice, not a test failure.
- Four unchanged, slow archival-export proof modules were deliberately excluded
  from the final broad sweep: `test_export_reconciliation_service.py`,
  `test_export_retirement_evidence.py`, `test_export_retirement_recovery_evidence.py`
  and `test_export_rollover_evidence.py`. Their direct service/test paths do not
  adopt the changed helpers. Earlier full attempts were stopped, not counted as
  passing. This is **not** a claim that the entire repository suite passed.
- One earlier attempt incorrectly placed temporary private-spool fixtures inside
  Git; the existing outside-Git guard correctly rejected them. Reproducing the
  isolated test with normal external temporary storage passed. No guard was relaxed.
- Ruff and Black (cache disabled) passed for all changed Python files;
  architecture, deferred-item, security-routing, test-selection, import smoke,
  static command registration, local links and whitespace checks passed. Registration:
  36 top-level commands, 102 grouped subcommands; no drift.
- Final **Changes / Deep off** scan
  `6b853fa2-68b1-45b5-a8d9-17b3cb79e6b8`: complete, **zero findings**, all 13
  source inventory files plus supporting tests/fixtures reviewed. Frozen patch digest:
  `cc906dcc2fb38ca6f92e8a3c249e367dfa21b9cd30ba39f5354306b0a3d70209`.
  Earlier completed scan `e0f5605c-1f9a-4b86-a205-9d73cbf2c274` remains historical.
  Final source correction returns safe failure results for target generation,
  promotion and reset; real modal/confirmation tests prove private replies.
- Post-scan delta is limited to the second test assertion using the already reviewed
  source bridge, regenerated benchmark data and this evidence text. Documented
  security skip for that exact non-runtime delta: no new input, SQL, permission,
  configuration, file/network behavior or installation authority. Runtime hashes
  remain those of the final reviewed patch and the final benchmark manifest.

Local raw test output is retained in ignored `.codex_artifacts/a1a-final-regression.txt`
and `.codex_artifacts/a1a-final-focused.txt`. Report custody is the Changes-only
`security-diff-scan` record above, under the user's local security state directory. Reported final
scan usage: 1,684,316 aggregate tokens, including 1,677,184 cached input tokens
(host rollout accounting, not a billing estimate). Final review goal usage:
17,239 tokens / 92 seconds; earlier review goal: 192,318 tokens / 306 seconds.

### Final timing observations

The two final benchmark runs were sequential after regression work stopped, using
identical harness SHA-256
`5a0da1ce83cdffcc3f46dde1c4aa60215e9fb8f01bd5abd005910bf9098002e0`.
Source/harness hashes were checked after generation. Values below are milliseconds;
each cell shows median / p95 across 30 observations.

| Case | Before total | After total | Before acknowledgement | After acknowledgement | Before loop lag | After loop lag |
|---|---|---|---|---|---|---|
| Empty payload | 6.48 / 9.32 | 3.10 / 9.62 | n/a | n/a | 5.11 / 8.34 | 2.09 / 7.12 |
| 4-signup payload | 9.72 / 10.30 | 4.88 / 5.35 | n/a | n/a | 8.08 / 8.91 | 3.67 / 4.27 |
| 15-signup payload | 10.07 / 10.64 | 5.26 / 5.96 | n/a | n/a | 8.38 / 9.42 | 4.03 / 5.01 |
| 30-signup payload | 10.34 / 10.87 | 5.53 / 5.97 | n/a | n/a | 7.38 / 9.89 | 4.33 / 5.00 |
| Rank selection | 28.74 / 35.89 | 23.20 / 32.89 | 11.42 / 16.47 | 10.16 / 15.64 | 13.15 / 15.45 | 9.90 / 14.53 |
| Rank submission | 78.49 / 94.36 | 76.37 / 94.23 | 11.18 / 15.56 | 12.30 / 15.70 | 14.55 / 17.61 | 14.52 / 15.18 |
| Submission + scheduler overlap | 100.25 / 119.84 | 93.12 / 105.58 | 0.17 / 0.27 | 0.23 / 0.34 | 14.94 / 19.00 | 14.55 / 17.12 |

The native host timer/scheduling granularity is visible even with 1 ms simulated IO.
Acknowledgement did not consistently improve. The durable conclusion is the exact
read-count reduction; A1b remains necessary to address response/refresh coupling.
Candidate JSON includes per-stage sample counts, median and p95 (null below 20
samples); baseline lacks the new stage instrumentation. Example rank-submit stages:
worker queue 0.062 / 0.148; dataset preparation 4.511 / 4.742; Discord edit
13.448 / 15.962; private response 7.865 / 14.697. These inclusive timings overlap.

## Follow-on sequence and acceptance custody

1. A1b: saved-result response and refresh coordination. First adopt public-data
   validity, preserve destination/notification keys, prove dirty-during-run and
   failed refresh after confirmed commit. Use the caller matrix and measured counts.
2. A2: Ark. The supplied admin-add screenshot shows private timeout; operator says
   roster add succeeded. Logs show registration edit success followed by final
   interaction response 404/10062. Mutation/audit and entry/ack timing remain
   unverified. Capture ARK-A2-ADMIN-ADD in the deferred register; do not replay it.
3. A3 voting; A4 calendar: domain-sized caller/adoption matrices before implementation.
4. A5 / R11: fighting caps, KS preclaim and legacy replacement policy require their
   own decisions. Broader R12 atomic writers and R16 receipt scaling remain separate.

The [accepted closeout ledger](P1%20MGE%20Lifecycle%20-%20Accepted%20Closeout%20-%202026-10-28.md)
is carried forward in full: MGE-01 exercised acceptance remains accepted while exact
audit/cleanup and unexercised cases remain open; MGE-PERF is locally improved, A1b
and production measurement open. R01/CFG-51421 and CFG-OVERVIEW remain independent;
no keep-prior/fresh-publication choice is made. R02/R06/R07/R11/R12/R16 retain their
bounded A/B follow-ups. R03/R04/R13 natural/historical evidence remains pending;
R05/R08/R09/R10 remain B; R14/R15 remain C; R17 P0 F04/F01-F05 remains open.
R18 predecessor acceptance remains accepted, with no new-runtime end-to-end proof.

Missing MGE audit/cleanup evidence: only an independently authorized read-only
comparison of exact event/signup/operation receipts and required audit/deletion
rows can close it. Preserve original source/runtime and receipt identities; absence
is not replay authority. No such production query was performed in A1a.

## Release qualification

The deployment prerequisite adds no SQL migration, dependency, environment or
activation change. The retained predecessor is private runtime
`4c8ca0d5fada35c7a32d31846bad6cc492aa92a9` and the matching MGE updater manifest.
The exact upgrade helper authenticates actual installed bytes before changing
anything. A different host installation requires reconciliation; retained release
evidence is not a fresh host inventory. Final PR, compatibility, package checksums
and operator instructions are retained in the development release handoff.

Initial release-policy regression: 256 passed, including exact source pins,
historical preservation, registry limits, every member tamper/absence, complete
bundle admission and target-policy refusal. The full repository suite is run again
for the final release delta; results are recorded in the PR handoff.

### PR review correction

Copilot identified that wrong-event placement readback was correctly refused but
its `placement_identity` label was caught and rewritten to `placement_readback`.
The catch now covers only the DAL read. Paired tests preserve the distinct labels,
incomplete state, redacted message and one attempted placement. The unreleased
A1a successor pin and exact test bridge are updated; all 49 historical release
entries remain unchanged. Stored before/after benchmark observations predate this
diagnostic-only correction; no new production-latency claim follows from it.
