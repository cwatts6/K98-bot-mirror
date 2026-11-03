# P1 MGE lifecycle: implementation and evidence

> **Current MGE checkpoint — 29 October 2026:** A1b and its updater correction are
> delivered; Report63 verifies the exercised actions and response-before-refresh
> ordering. Exact running SHA remains operator-reported. See the [deployed closeout](P1%20MGE%20A1b%20-%20Deployed%20Closeout%20-%202026-10-29.md).
> The approved [MGE finalisation follow-up](P1%20MGE%20Finalisation%20and%20Shared%20Board%20Lifecycle%20-%202026-10-29.md) owns immutable historical boards,
> durable unfinished final delivery and the shared Ark/voting/calendar caller design.
> Its local source work is separate from publication, SQL qualification and deployment.
> Earlier A1a-current, A1b-local-only and approval-pending passages below are retained
> historical evidence, not current instructions. A1b's completed-event startup sweep
> was implemented and is now superseded by the clarified finalisation policy.
> Queue closure reconciliation, CFG-51421, exact audit/cleanup, atomic/cross-process
> writers, natural acceptance, P0 and wider B/C remain separate. Do not replay live actions.

> **Historical status - 28 October 2026, A1a deployed:** Mirror PR 454 and private
> PR 702 are merged; private `87c1b39325daaa0ca1a8c0cbca656df82d7fa46b` is deployed
> and Discord online. Signup/edit/withdraw are verified on this runtime. A1a qualified
> datasets and timing are delivered; the A1b design packet is prepared for approval.
> Rank confirmation still waits for board refresh. Report 62 queue closure, the older
> configuration decision and separate Discord lag remain follow-ups. Exact audit/cleanup,
> unexercised cases, fresh import/export, natural acceptance and P0 remain explicit.
> See [deployed closeout](P1%20MGE%20A1a%20-%20Deployed%20Closeout%20-%202026-10-28.md) and [A1b design packet](P1%20MGE%20A1b%20-%20Design%20and%20Delivery%20Packet%20-%202026-10-28.md).
> Earlier dated status and next-action text is historical where superseded.
> This documentation update requires no deployment, restart, SQL apply or repeat import.

Original implementation checkpoint: 28 October 2026, locally qualified before deployment.
Current delivery and operator acceptance are recorded in the closeout above. Subsequent
release/deployment statements below retain their original checkpoint context.

The operator approved the expanded MGE scope, reusable P1 foundations, a second
caller compatibility check and measured optimisation. The accepted monitoring/
import/export phase and R18 remain closed. The operator separately approved the
exact isolated native SQL target; its seven-table fixture is installed and retained.
No production operation, restart or acceptance replay is part of this work.

## Reviewed release preparation

[Mirror PR 452](https://github.com/cwatts6/K98-bot-mirror/pull/452) and
[private PR 700](https://github.com/cwatts6/k98-bot/pull/700) carry the same file
delta through separate Git histories. The operator explicitly approved the exact
27-file MGE updater transition and bounded registry increase to 49 entries and
96 KiB. All 48 historical transitions remain unchanged. The registry is 85,602
bytes; missing, altered, extra or renamed family members and mismatched installed
policy/registry versions remain refused. No updater has been installed.

Fresh complete runs supersede the earlier full-run-plus-recheck qualification
below: **10,085 passed / 1,100 skipped** in the mirror implementation worktree and
**10,086 passed / 1,099 skipped** in the private promotion worktree, each with eight
subtests and one dependency warning. After the release amendment and review fix,
**1,258 focused updater/lifecycle tests passed, 20 skipped**, with production
operational logs unchanged. Final PR-head CI and review receipts are retained on
the linked PRs; merging still does not establish deployment or live acceptance.

PR review found a queued-refresh loss when an in-flight pass raised. The corrected
worker records each failure and runs a newer independently requested revision;
it never retries a failed revision automatically. Deterministic tests cover a
successful or failing newer pass, exactly-once execution of each pass, cleared
pending ownership, and propagation when there is no newer request. The release
registry pins the corrected source image.

Additional completed Changes security reviews, all with zero reportable findings:

- Private runtime patch: `d121b9a3-f110-4627-8989-6a8de6d2e8df` (28 source entries).
- Mirror updater amendment: `75e0c44a-5ef3-44a9-a5a0-c1d9115db4a6` (two entries).
- Private updater amendment: `63d82d1f-5fef-4bd8-b1c4-421fb9c9aa24` (two entries).
- Mirror refresh correction: `cd7fd325-8608-4ded-91dd-0726e365ba66` (two entries).
- Private refresh correction: `693208c9-20cd-43b3-9192-66c3704399c6` (two entries).

The final registry-bound assertion and this evidence update are test/documentation
changes only; they do not alter the reviewed runtime or updater policy. The exact
upgrade package is checked against the retained accepted runtime and updater
manifest. Its generated helper must still verify actual installed bytes and
custody on MINI_AMD. Use the final release handoff for package hashes and the
merged private target; preserve the prompted graceful restart and natural MGE
verification boundary.

## Baseline and implementation slices

Mirror baseline: `50c5e1a4a60a0438dca788298047f7d6dfb66e39` (includes the accepted
28 October closeout). Branch: `codex/p1-mge-lifecycle`. SQL definitions reviewed in
the separate authoritative SQL checkout; no SQL repository changes or migration.

| Slice | Changes | Reusable contribution |
|---|---|---|
| Persistence | Atomic signup/audit/withdraw cleanup, exact identities, current event checks, edit snapshot, operation receipt, explicit commit/rollback/unknown | Outcome vocabulary and writer/conflict template |
| Interaction | Early private acknowledgement, owned off-loop execution, current roles and form owner, repeat guard, commit separate from reply/DM/refresh, safe prepared-modal handoff | Compatible interaction helper and shared cancellation primitive |
| Presentation | Event-scoped board serialization, coalesced refresh requests, off-loop scheduler/board reads, durable board-send evidence, exact-ID recovery | Reusable refresh coordinator and failure scenarios |

Mutation persistence is deliberately MGE-specific. The global legacy SQL wrapper
is unchanged. No new domain policy, schema, global lock, retry framework or
automatic recovery command is introduced.

## Conflict and ownership map

| Writer / consumer | Authority and ordering | Remaining boundary |
|---|---|---|
| Signup create/edit/withdraw | Event lock -> exact signup -> awards where needed; required writes/audits in one transaction | Registry linkage is validated through the existing service; no registry policy rewrite |
| Open-mode switch | Existing event-first transaction, then award/signup deletion and audits | Historical receipts remain history |
| Publish/unpublish | Existing event-first DAL locks order with signup admission | Provider publication protocol remains its own service contract |
| Complete/reopen | Event-row update conflicts with held event lock | Existing completion semantics retained |
| Roster insertion | Event -> active exact signup -> award insert | Other roster operations retain existing outcome contracts |
| Legacy roster UI writers | Both UIs share whole-service event ownership before off-loop entry; SQL insert rechecks rank and capacity | Process-local ownership; cross-process/audit contract adoption remains separate |
| Board scheduler/manual sync | Event-scoped serialized read/render/edit | Process lock is not cross-process ownership |
| Background refresh callback | Coalesced owned request; dirty-during-run guarantees another pass | Authoritative state reread after restart; no persisted refresh queue |
| Board creation | Existing durable delivery journal before send, receipt before SQL ID save | Unknown send held; missing known message requires disposition |

## Second caller evidence

`services/event_delivery_service.py` now imports the extracted worker directly.
The old `services/legacy_export_snapshot_service.py:drain_thread` remains a
compatible wrapper for existing consumers. MGE SQL writes and event-journal writes
both prove that cancellation does not release the caller while the worker lives.
Context propagation and exception behaviour are tested through the compatibility
entry point. The event caller retains its own journal, admission and locks;
MGE retains its own SQL transaction and business policy.

MGE additionally consumes the existing durable delivery journal for board creation.
Restart fixtures verify exact-ID recovery after acknowledgement and refusal to
resend after a lost send acknowledgement or failed receipt write.

## Measurement method and results

`scripts/benchmark_mge_lifecycle.py` executes the real callback and board sync
with deterministic simulated SQL/service/Discord delays. No live database or
Discord call occurs. Raw measurements and source hashes are retained locally in
the [retained benchmark data](../benchmarks/p1_mge_lifecycle_20261028.json).
These are development evidence, not runtime receipts. Baseline source was verified
byte-for-byte after newline normalization against the pinned mirror revision.

Final 20-sample callback fixture, 50 ms blocking service:

| Metric | Before | After |
|---|---:|---:|
| Median acknowledgement | 50.31 ms | 0.019 ms |
| p95 acknowledgement | 50.63 ms | 0.026 ms |
| Median total callback | 50.32 ms | 51.08 ms |
| p95 total callback | 50.65 ms | 51.46 ms |
| Median maximum event-loop lag | 49.39 ms | 15.89 ms |
| Mutation / reply / refresh requests per submission | 1 / 1 / 1 | 1 / 1 / 1 |

The improvement is responsiveness and ownership, not faster business SQL. Windows
timer scheduling remains visible in the lag measurement. Instrumented application
logs record callback acknowledgement/total duration and mutation outcome/duration.

Same-turn burst of 20 board-refresh requests, 50 ms simulated IO per pass:

| Metric | Before | After |
|---|---:|---:|
| Event reads / roster reads / Discord edits / ID writes | 20 / 20 / 20 / 20 | 1 / 1 / 1 / 1 |
| Fixture elapsed time | 556.31 ms | 81.62 ms |

The baseline excludes its old fixed 0.5-second dispatch delay. This is a burst
fixture, not a claim that all refresh traffic reduces by 95%. A separate test
injects another burst during execution and requires two passes with the latest
revision displayed. Source hashes distinguish uncommitted after-code from baseline.

Native SQL qualification subsequently passed all 15 named cases in the explicitly
approved target. Real competing sessions showed `LCK_M_U` behind the exact event
owner; an unrelated event committed in 4.79 ms while that owner remained held.
Required-write failures rolled back; lost commit acknowledgement remained unknown
and an exact persisted receipt reconciled it without another mutation.

Twenty measured native persistence cycles per mode, after two warm-ups:

| Metric | Before create / edit / withdraw | After create / edit / withdraw |
|---|---:|---:|
| Median duration, ms | 1.760 / 1.579 / 1.891 | 1.739 / 1.737 / 1.479 |
| p95 duration, ms | 2.268 / 1.921 / 2.473 | 2.431 / 1.993 / 2.092 |
| Connections and commits | 2 / 2 / 3 | 1 / 1 / 1 |
| Statements | 3 / 2 / 3 | 5 / 5 / 6 |
| Median logical reads, separate instrumented pass | 46 / 30 / 37 | 87 / 84 / 80.5 |

This reconstructs the original separate DAL workflow using preserved statements,
not the full UI/service/provider path. Withdrawal timing uses an empty award lookup;
award deletion/audit is separately proven by native failure cases. The separate
read-cost pass started with 1,142 audit rows and used 20 cycles per mode. Median
session CPU was below the millisecond reporting resolution, not zero CPU work.
Local timings show fewer connection/commit boundaries, not universal SQL speedup;
the stronger ownership/receipt checks add statements and reads.

Actual receipt plans chose a clustered index scan, despite the available EventId
index: 15 / 17 / 31 logical reads at 0 / 100 / 1,000 event-audit rows (142 / 242 /
1,142 total rows). The JSON predicate remains a measured scaling follow-up; no
schema/index change was made. All observed connections closed. The fixture retains
1,262 audit rows, below its 2,000-row bound. See the
[native qualification packet](P1%20MGE%20-%20Native%20SQL%20Qualification%20Packet.md)
and [retained native measurements](../benchmarks/p1_mge_native_sql_20261028.json).

## Validation

- Initial focused lifecycle/transaction/second-caller suite: 79 passed.
- Expanded MGE, interaction and legacy-worker suite: 457 passed, one dependency warning.
- Subsequent focused suite before review amendments: 464 passed; operational logs unchanged.
- Review amendments: competing rank additions, stale notes/rank interleaving,
  cancellation ownership, unrelated-event progress, cancel-after-entry, actual
  reminders-modal submission, locked rank/cap checks and five actual roster modal
  submissions pass (13 tests).
- Architecture, import smoke (isolated test configuration), command registration
  and security-routing gates passed during implementation.
- Final focused MGE/shared lifecycle suite: 480 passed, one dependency warning;
  production operational logs unchanged.
- Full suite and resolution evidence are recorded below; final Changes review
  completed with zero reportable security findings.

Fault injection covers required write/audit failure, confirmed rollback, rollback
failure, lost commit acknowledgement, exact receipt reconciliation, identity
mismatch, inactive/stale signup, locked event, unknown acknowledgement, current
form owner, repeated clicks, worker cancellation, reply failure, refresh ordering
and restart after uncertain board delivery. Offline and native SQL evidence are
identified separately; live callbacks and operator visual acceptance remain open.

Security target: Changes review of this branch against the pinned mirror baseline,
Deep off. No repository-wide audit is selected. SQL source remains unchanged.

Completed source-review chain (all with zero reportable security findings):

- Initial 27-source-file patch: `fda91c12-6fdf-42aa-a557-9713821ac1e5`, retained in
  commit `9d3ef829cd61ea50877b1e251a444d8d5947124f`.
- Six-source-file correctness amendment: `a863930d-791d-4de7-8bd4-a5f4da60bba0`,
  retained in commit `3ef186b50abcef660aa1d6401bc31247ed62ca3a`.
- Final five-line parent-event correction: `bbde3b53-1c00-411f-b395-b1502b9c99cd`.

Ordinary review found and corrected double acknowledgement in legacy publish,
misleading cancellation after entry, new roster concurrency exposure and nested
modal event wiring. Security results do not stand in for correctness checks.
Subsequent documentation/evidence-only edits do not change a security boundary.

The first full run had 10,026 passes, 1,100 skips and 36 failures. Eighteen failures
were the interpreter guard correctly refusing a different checkout's interpreter;
the worktree now has its own `.venv` interpreter, with the existing development
packages exposed through a local `.pth` file. Eighteen were historical exact-source
assertions requiring an authenticated successor bridge. The new test-only bridge
pins exact before/after bytes and rejects changed/missing mappings; it does not
alter production updater capability. This development environment is not a
production environment build.

The subsequent full run recorded 10,049 passes, 1,101 skips, five failures and 25
setup errors. Two temporary-fixture mapping omissions and one direct historical
hash assertion were corrected. The remaining failures/setup errors came from
pywin32 package paths not being initialized by the local dependency bridge;
`site.addsitedir` now processes its package path files. Every affected test file
was rerun: **117 passed**, with production operational logs unchanged. The final
480-test focused run also passed after the source corrections. This is a full run
plus successful targeted resolution, not a claim of one uninterrupted green full
run. A third full run was not repeated after the bounded fixture/environment fixes.

Final architecture, deferred-item, test-selection, security-routing, Ruff, Black,
import smoke, command-registration and diff-whitespace checks passed. Test-only
historical-source mapping corrections and documentation/measurement additions
after the sealed source reviews do not change runtime or security boundaries.

At the original local implementation checkpoint no protected-updater transition
had been authorized. The reviewed release-preparation section above records the
subsequent explicit approval, exact transition and validation. Installation and
live acceptance remain separate; the old installed updater correctly refuses the
new source until the reviewed exact-version upgrade is installed.

## Operator evidence and acceptance

For a new normal MGE signup/edit/withdraw, retain the operation reference, exact
event/governor/signup, response outcome and refreshed original board. Verify the
signup and mandatory audit/cleanup together. The service exposes the exact
read-only `read_operation_receipt(event_id, actor_discord_id, operation_id)` lookup.
Its absence or read failure is not retry authorization. Do not rerun the reported
historical attempt merely to obtain acceptance.

For board delivery uncertainty, retain the existing journal entry and destination.
An acknowledged channel/message ID supports exact recovery; `entered` does not.
Do not delete the journal, repost automatically, or classify elapsed time as failure.

Source review, local tests, native qualification, mirror PR, promotion, deployment
and operator acceptance remain separate. R03/R04/R13 natural/historical obligations,
R05/R08-R12 residual audits/policy, R14-R16 operations/performance and separate P0
R17 remain on the [stable ledger](P1%20Monitoring%20and%20Import%20Export%20Reliability%20-%20Closeout%20-%202026-10-28.md).

See the [shared adoption contract](../reference/p1-operation-lifecycle.md).
