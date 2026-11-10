# P02 remaining work: approved scope and delivery handover

## Current authorization and starting point

On 9 November the operator agreed this remaining scope, requested updated scope,
archives and a new chat to complete P02, and explicitly kept production deployment
separate. Begin the whole-solution review/design and progress within this scope;
do not ask again whether to start. Make PR-sized implementation slices after
revalidating the existing design against current Bot and SQL. Escalate only a
material scope change or a concrete separately controlled production action.

Use the existing `C:/discord_file_downloader` checkout; no new worktree is required.
The authoritative SQL repository is `C:/K98-bot-SQL-Server`. Verify current Git
state, relevant AGENTS/core guidance and unrelated edits before changing either.
The private promotion checkout at
`C:/Users/cwatt/.codex/worktrees/p016-production/discord_file_downloader` is reusable
after checking its state. Independent repository histories must remain separate.

Read the [integrated plan](Startup%20Import%20Export%20Reliability%20-%20P02%20Integrated%20Analysis%20and%20Delivery%20Plan%20-%202026-11-07.md),
[programme principles](Startup%20Import%20Export%20Reliability%20-%20Programme%20Principles%20-%202026-11-06.md)
and [documentation manifest](Startup%20Import%20Export%20Reliability%20-%20Documentation%20Carry-forward%20-%202026-11-09.md).
The existing programme scope, tracker, action census, tracing, coverage and final
sweep remain active. This handover is the current dated overlay, not a replacement
programme or authority to replay archived commands.

## Delivered Phase 1 and evidence boundaries

- Summary calculations avoid rebuilding the 32 full-history intermediate caches.
  All reports use the latest nonempty name while historical statistics stay historical.
- 139 columns across 31 summary/output tables use qualified exact integer types;
  large values use bigint. Exact values survive Bot capture, export and reload.
  Existing queued payloads keep their original bytes and identity.
- Selected recovery inspections use short explicit snapshot reads. Snapshot
  allowance is ON; read-committed snapshot mode remains OFF. This is not proof
  that every remaining observer or arbitrary history reader is qualified.
- Final isolated 415-row rehearsal verified 14 local outputs, 49,468 rows and
  827,683 cells. Five balanced OFF/ON pairs, observer-first, active-writer,
  a 30-second metadata reader and exact connection cleanup passed. No provider
  delivery was exercised by those local captures. Preserve earlier failed runs.
- SQL commit `a202a51440f17233800b49801bd31c3ead2a9227` was installed through
  migration `20261109_001_p02_phase1_sql_exports`. Corrective Bot deployment
  `97abcce1b2a9e71b3959eff74525c57930a703e6`, release
  `fa1e52e1-afe5-4e26-9932-fde16ebb6e50`, verified source/seed/start/readiness and
  Discord online in operator output. This is recorded deployment evidence,
  not a new live health check.
- Successor logs show startup, player caches and the ordinary ProcConfig import
  completed. Fresh standard stats import and complete provider/export acceptance
  remain separate. The supplied recovery report was only part 1, not a current
  complete inventory or proof that old failures recurred.
- Permanent regression changes are merged in mirror PR 497 and private PR 736
  (private merge `ecd0dde82783bfd87e6f83659198bfc659b6c848`). These test/tooling
  changes were not separately deployed; no extra restart is required for them.
  Full CI: 12,073 passed, 1,304 skipped, 19 warnings, eight subtests passed.
  Windows regression gate: 111 passed, zero skips; native SQL runner: 33 checks.
  Changes security review `4435ae8b-2c07-44b5-9257-12c7e9a5fab2`: zero findings.

Do not confuse private main with the installed Bot. Do not rerun the successful
deployment, migration, rehearsal or recovery tooling to refresh evidence.

## Remaining P02 delivery slices

The [D2 delivery review](Startup%20Import%20Export%20Reliability%20-%20P02%20D2%20Delivery%20Review%20-%202026-11-09.md)
records all twelve D2a–l slices, the final caller/resource matrix and the original
finding disposition. D2a–l implementation, combined regression/correction checks,
native qualification and Changes review are complete. The final D2l mirror PR
supplies the review/merge gate. All 59 combined native fixture cases passed;
the full regression checkpoint and eight corrected fixture failures are recorded
in the delivery review. Next is D3, then D4 and D5. This does not authorize
production promotion or retained-work recovery.

| Slice / findings | Required result | Verification before release |
| --- | --- | --- |
| D2: readers, factories and budgets; F01/F03/F09/F12/F14/F26 | Complete the caller/resource census. Choose connection factories once; no fallback after execution failure. Extend passive reads only to proved read-only paths. Keep mutation fencing and current-state checks. Prevent slow observations monopolizing authenticated authority dispatch; identify actual holder separately from requester. | Both arrival orders, known competing owners, stale views, alternate factories, permission refusal, lost replies/acknowledgements, observation saturation, cancellation and physical drain. Keep original errors and explicit unavailable diagnostics. |
| D3: file ownership and six maintenance boundaries; F16/F18/F20/F21/F22 | Fix shared lock cleanup across all equivalent callers. Release only owned locks in finally; body exceptions are not acquisition failures. Separate eligible optional upkeep from required business commit/capture, using durable owned maintenance. | Real child procedures and all six stages: import, configuration, player report, KVK output, final reports, post-import upkeep. Test failed/replaced locks, cancellation, foreign sentinels, restart and maintenance failure after commit. Include raw-history reader/index-rebuild interaction. |
| D4: legacy/manual paths and final release compatibility; F31 | Reconcile installed bindings and manual use of UPDATE_ALL/Rally/TEST. Qualify used paths or seek explicit retirement approval. Preserve input custody, error propagation and post-commit archive semantics. Keep exact source/SQL/startup contracts aligned. | No business execution merely to discover use. Test rollback preserves input and child errors propagate. Verify current updater/source pins and actual changed-path custody before any later deployment. |
| D5: combined isolated qualification | Qualify the final remaining P02 package together against the delivered Phase 1 baseline. | Correctness, real concurrency, failures, cancellation, restart, cleanup and resource cost. Reuse valid baseline evidence; repeat affected checks for a reason, not merely to increase test counts. |

D2j delivers one bounded observation worker and at most one waiting observation,
while mutations remain serial. Only the exact proved read-only selectors use that
worker. Configuration reconciliation retains serial dispatch. Lifecycle evidence
includes authentication, saturation, lost replies, cancellation and physical drain.
Check every selector for reconcile/seal/provider side effects. Do not add a general
scheduler, outbox, SQL notification system or broad diagnostics without demonstrated need.

## P03/P04 dependencies and first standard import/export

P02 prevents recurrence; P03 continues/settles retained unfinished work; P04 makes
incident state, cancellations, history and notifications converge correctly; P05
confirms the complete solution. P01 remains accepted with its recorded limitations.

The target for the **first standard production import/export test is after P03 has
safely settled the actual blockers, plus any essential P04 correction**. Do not
defer that first test merely until the end of P05. Nor promise that finishing P03
automatically resolves every incident or proves delivery.

Before that test, the P03/P04 owners must provide a bounded current assessment of:
exact incident and pipeline identities; committed stages and retained captures;
owner/fence/version; outstanding physical sessions, claims and provider streams;
supported recovery predicates; and the remaining authorized work. Historical six
rows were five linked to one pipeline plus an older cancellation projection; later
inventories had nine rows. Neither number establishes the current blockers.

Continue only unfinished authorized stages. Never replay committed imports/player
reports/provider effects, clear unknown work, delete evidence, or expire ownership
by age. A zero incident count is not the entry criterion. Normal test execution,
provider actions and any recovery operation retain their concrete approval and
current-precondition gates. Production deployment remains separately approved.

## Limits and remaining decisions

- Keep disk reserve >=8 GiB, version store <512 MiB and sampled log use <70%.
  Approved host free-memory prerequisite remains 8 GiB. Preserve existing
  command/connection/execution limits and operation-specific overrides.
- Recovery snapshot statements retain three seconds and zero row-lock wait.
  The rehearsal's 1,800-second cap is not a production timeout increase.
- The one-rehearsal 21-input allowance has been consumed. Preserve all inputs;
  no new input copy or higher cap is implied by this handoff. Reassess test-host
  readiness after the development PC crash; do not assume retained elevated
  PowerShell sessions or guest state survived.
- Retain existing balanced cost limits where comparable measured work is required:
  overall median ON <= OFF x1.20 +1,000 ms; per-stage <= OFF x1.20 +250 ms.
  No new speed benchmark is required merely to justify the shared-name design.
- Raw-history snapshot across index REBUILD failed with SQL 3961. The qualified
  metadata reader does not erase that failure or authorize arbitrary reader/DDL
  overlap. D3 owns its maintenance/reader contract.
- Equal-score ranks have no defined secondary key. Stable tie ordering remains an
  explicit report-policy decision, not a silent correction. Date-window outputs
  must be checked against actual report-log execution time, not collection time.

## Connected/deferred scope

The Task C summary audit/rewrite and this chain's exact types/names/export work are
delivered Phase 1, not an unstarted optimisation proposal. Broader datatype
conversion is excluded. CFG-51421 holder evidence and session-lock grant
acknowledgement uncertainty belong to D2/D5. Evaluate the ActivePreparationID
index only if current plans and write cost demonstrate benefit; no blanket indexes.

P01.6 snapshot decode/rebuild optimisation, broader import-orchestration extraction,
Stats UI/SDK acknowledgement work and unrelated MGE/Ark performance retain their
post-P01-P05 deferral. Shared Ark callers of F20 still require regression coverage.
Bring a deferred item forward only for a concrete agreed dependency. Backup-schedule
policy is not permission to change schedules as part of maintenance refactoring.

## Permanent lessons and operating rules

1. No point fixes: review Bot and authoritative SQL, equivalent callers, direct
   invocation, startup, failure, cleanup and restart as one affected solution.
2. Separate business commit, capture, cache, provider delivery, notification and
   observation. Deadlines/cancelled awaiters do not prove physical termination;
   retain ownership and capacity until actual cleanup is established.
3. Server identity: accept case variants of the same qualified Windows host,
   while rejecting other hosts/instances, whitespace, databases and changed modes.
   Do not apply blanket case folding to SQL object/column/permission identities.
4. Permission rows: SQL uses different comparison rules for object grouping and
   inner fields. Python tuple sorting changed 1,099 existing entries without
   changing rights. Use the tested offline projector, preserve native inner
   order, authenticate the predecessor and qualify native candidate evidence.
   Never adopt a live hash merely to silence a startup mismatch.
5. Metadata row enumeration and genuine visible column order are different.
   Reuse portable schema fingerprints and permanent positive/negative tests;
   harmless enumeration changes must not hide real schema or privilege drift.
6. SQL may have committed when later startup verification fails. Read exact
   receipts and resume only supported remaining stages; never reapply SQL or
   start a second Bot to repair an uncertain start.
7. Windows PowerShell 5.1 is the production shell. Test actual collection return
   shapes (scalar/array/.Count), cross-process JSON, SQL alias quoting and complete
   error capture. A root wrapper message is not the original failure. Bound and
   compress evidence rather than silently raising limits. Existing run folders
   are evidence to inspect, not a reason to delete or replay one-shot work.
8. Track exact connection identities, not reusable SPIDs alone. Test monitors
   can fail after SQL succeeds; preserve completion evidence before another run.
9. Verify fresh production source/SQL/updater and changed paths plus ancestors,
   including archived docs. Development privileges and historical ACL checks do
   not prove current production custody. Do not weaken guards or widen permissions.
10. Mirror main is periodically replaced by a scrubbed private snapshot. Refresh
    bases before PR creation; use patch-based private promotion and verify bytes.
    Private CI workflows may be omitted by mirroring. The permanent Windows
    regression workflow is authoritative in private main; verify gate presence
    and results, not merely file presence in the scrubbed mirror. GitHub reported
    branch-protection API unavailable for the private subscription, so do not
    claim remote required-check enforcement; explicitly check all CI before merge.
11. Keep diagnostics bounded and passive. Known-holder tests need actual holder
    evidence; unavailable historical attribution stays unavailable. Avoid broad
    instrumentation or repeated workloads without an unanswered question.

## Review, publication and next-chat deliverable

Use focused regression/native tests plus applicable full CI, architecture,
deferred, security-routing and test-selection gates. Future executable Bot and SQL
changes each need an exact Changes security review; no inferred repository audit.
Test the real boundaries, including negative controls, and preserve first failures.

First new-chat deliverable: refreshed caller/resource/SQL matrix, explicit
disposition for every original finding above, concrete first D2 slice and its
tests/cost limits. Continue the approved implementation and local qualification
through focused reviewable PRs; do not restart planning from scratch or ask to
reapprove unchanged scope. Production deployment, retained-work recovery and the
standard provider test remain separate concrete actions.

Private evidence is under `C:/discord_file_downloader/.codex_artifacts/p021`.
Use `release-identity-regressions-completion.json`, completed rehearsal receipts,
the final report-clock evidence and sealed deployment/recovery evidence. Keep raw
inventories, installed policies, player data and private incident identities out
of public source. The private handoff supplies exact evidence paths separately.
