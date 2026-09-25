# S11 source delivery closeout and G4/G5 handoff

## PR #282 review corrections — 2026-09-25

The operator authorized action, replies and resolution for the current PR comments. Two Bot
findings initially required runtime corrections beyond the original byte-exact restoration: incomplete
authority drain now returns status 1 while retaining the SQL session; provider 429/503 feedback
now crosses the authenticated child pipe as an exact request-bound, bounded envelope and
extends the existing shared cooldown. Numeric waits are capped at 3,600 seconds; HTTP dates
remain absolute until SQL server UTC applies the bound. Invalid/missing headers use the existing
fallback. There is no provider retry or terminal outcome inferred from this feedback. A lost
cooldown acknowledgement retains uncertainty, dispatch evidence and claims.

The concrete authority/enrollment connection factory also now opens fresh transactional
connections for shared budget and pool work. Evidence DAL methods explicitly enable autocommit
on their own fresh connections before calling procedures that own their transactions. This
closes the pre-existing caller-wiring mismatch found during review; fixed targets, integrated
identity, encryption/certificate validation, timeout and SQL permissions remain unchanged.
Actual-factory regressions exercise reservation, cooldown and evidence-procedure modes with
inert ODBC connections and the real DAL/transaction helpers.

A subsequent comment identified post-open initialization outside the cleanup scope. Both the
authority and enrollment launchers now protect all initialization after the acknowledged session
open, including late imports and construction. A construction failure before any authority exists
closes the empty session using the acknowledged version; once an authority exists, a successful
drain is required. Failed or raising drains retain the session. An uncertain open is never closed
or retried, and an uncertain close is not retried. Enrollment also returns failure for incomplete
drain. The authoritative SQL close still enforces version CAS and rejects unfinished streams or
enrollment preparations; no SQL contract or live operation changes.

The runtime delta is exactly `scripts/run_export_authority.py`, `scripts/enroll_export_output_pool.py`,
`scripts/run_export_provider_child.py`, `core/export_execution_host.py`,
`services/export_execution_authority.py` and `services/export_execution_protocol.py`, with
regressions in `tests/test_export_authority_launcher.py`,
`tests/test_export_execution_authority.py`, `tests/test_export_execution_host.py` and
`tests/test_export_execution_protocol.py`. SQL #90 has no actionable review comments and no
runtime delta; the existing `ExportCoordinationDAL.extend_cooldown` and authoritative
`dbo.ExportRequestBudget` definition already provide the required SQL contract.

Final offline validation: **899 passed, 13 skipped** across authority, protocol, host, runtime,
enrollment, adapter/budget and publication suites. Skips remain explicitly gated live checks
and unavailable local Windows/rsync capabilities. Network and SQL connections were blocked;
operational logs remained byte/mtime-identical. These are source checks, not G4 runtime proof.
The original restoration and earlier published-head receipts below remain historical evidence.
The merged-delivery manifest is unchanged and does not assert equality for these new corrections.
Current correction security/check/publication evidence is recorded in the release evidence log.
The 21 added startup cases first produced 15 failures and six passing controls at the previous
head; all pass after the correction. They cover both launchers, late-import failure, failed/raising
drain, uncertain open/close acknowledgements and incomplete-enrollment-drain exit status.

Before production promotion, compare every current PR path against the exact production base.
Carry the runtime corrections and their tests as modifications to existing production files;
omit only paths whose current blobs still match. Do not omit all five original restorations:
four now contain review corrections. The unchanged authority-boundary test remains identical.
Use a separate production patch/PR and refresh protected source hashes in the later G4 plan.
Review/merge/promotion does not authorize deployment, live SQL/provider work or G5 acceptance.

## Published PR handoff — 2026-09-25

[Bot-mirror #282](https://github.com/cwatts6/K98-bot-mirror/pull/282) and
[SQL closeout #90](https://github.com/cwatts6/K98-bot-SQL-Server/pull/90) are open for review.
Bot includes all 38 pending files, including every untracked document; SQL contains only its
two closeout documents. Initial published heads: Bot `b6543935e929d14d8a061694ca0cea6fcffc70e3`,
SQL `41301d7544248f30b9db2e0e98ec3fa15fe0243e`. The later Bot receipt commit changes Markdown only;
recheck current PR heads/checks before merge. Exact remote filenames and blobs are read back.

The [Linux publication-policy job](https://github.com/cwatts6/K98-bot-mirror/actions/runs/36125063464/job/108039157281)
passed both tests with rsync 3.2.7, including the real filter regression, on the initial Bot head.
This closes the local rsync availability gap; the earlier skipped local result remains history.
Bot Command Governance also passed on that head. At this receipt, SQL validation and automated
reviews are still running. A passing initial head does not replace final-head checks.

No PR has been merged, production policy promoted, bot machine changed or G4 operation executed
by this follow-up. Next stage remains **G4 plan development only**; controlled rollout and G5
acceptance require their distinct operator approvals. Production's publishing policy still
needs the reviewed repair through a separate production promotion after Bot review.

## Current status — 2026-09-25

S11 implementation and review corrections are merged into Bot mirror #281, SQL #89 and
production Bot #588. Local main refs match the repository delivery anchors below. The operator
reports **nothing updated on the production bot machine**. No live SQL/provider/Discord,
deployment, activation or G5 acceptance evidence is inferred from these merges or local pulls.

The next task is **G4 plan development only**, using the
[new task pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S11%20G4%20Release%20Planning%20Controlled%20Rollout%20and%20G5%20Acceptance.md)
and [chat starter](../../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S11%20G4%20Release%20Planning%20Controlled%20Rollout%20and%20G5%20Acceptance.md).
No task is created automatically. Controlled rollout requires exact operation approval;
G5 remains a subsequent operator acceptance decision.

The mirror repair and this documentation handoff are a **separate follow-up** to the three
merged PRs. On 2026-09-25 the operator explicitly authorized a Bot-mirror repair/handoff PR
including every pending/untracked Bot document, and a separate SQL documentation closeout PR.
That instruction supersedes the earlier requirement to defer these two SQL documents until
an implementation PR. It authorizes branch/commit/push/PR publication, not merge or live rollout.
The repaired policy must still reach production before its publisher can retain the five files.

## Exact repository delivery

| Repository / PR | Final reviewed PR head | Merge commit |
|---|---|---|
| [Bot mirror #281](https://github.com/cwatts6/K98-bot-mirror/pull/281) | `a65b8d676507eb5ac67856ecf5ac114492c99cc5` | `f2ad8741dff537c0953f8cb22c28098fbfb6195b` |
| [SQL #89](https://github.com/cwatts6/K98-bot-SQL-Server/pull/89) | `0aab5d74e116291bde9b027e44ca819fa35db03c` | `aa7b01381e2e451368c9b7118891a9b960bed9d9` |
| [Production Bot #588](https://github.com/cwatts6/k98-bot/pull/588) | `971ef6ba922d3b0c77b5450eff524dcf917c1c9e` | `ab8c8f43d28a6d27f615f672749ca37f334e6e55` |

Verified merge times were 09:51:32Z, 09:51:49Z and 09:52:37Z on 2026-09-25, respectively.
At readback, final-head checks passed: mirror Copilot/Command Governance; SQL Copilot/SQL
validation; production Copilot/Command Governance/quality/scan. Review-thread resolution and
earlier corrections are retained in the local review closeout. CI is source delivery evidence.

Current local comparison anchors at entry to the repair:

- Bot main/origin main: `511c129602e144a198dc29e9c396196d90d30df9`, publisher snapshot
  `Mirror: 2026-09-25T09:53:00Z from ab8c8f43`.
- Production/main: `ab8c8f43d28a6d27f615f672749ca37f334e6e55`.
- SQL main/origin main: `aa7b01381e2e451368c9b7118891a9b960bed9d9`.

Both worktrees were clean at entry. These are immutable comparison anchors, never reset
instructions. Recheck current refs and pending changes when starting G4 planning.

## What was delivered

The approved single-host/fresh-authority-identity design now has actual callers/helpers and
closed composition, authenticated bounded Bot/authority communication, supervised provider
execution, trusted termination/reconciliation/retirement recovery producers, durable evidence
and nested ownership, restricted SQL evidence APIs and complete metadata readiness checks.
All participating shared writers and owned shutdown delivery were reconciled in source.

Review corrections include bounded pre-send pipe acquisition without connected-request replay;
bounded child accept/hello with cancellation and retained handles; fresh SQL role collision
rejection and exact reapply/membership checks; refusal to close unfinished enrollment sessions
or streams with prepared/dispatch-intent evidence; legal terminal appends to frozen streams;
and portable exact SQL manifest paths/LF hash pins. Unknown outcomes still cannot establish proof.

The evidence distinguishes source gaps closed by those implementations from runtime proof still
needed: actual SQL installation and permissions, transactions/concurrency, Windows tokens/ACLs
and containment, exclusive fresh-key custody, provider readback/finality, all-writer exclusion,
deployment, observation and acceptance. No new runtime design is authorized by this handoff.

## Mirror publication repair

Production's `--exclude-from=.publishignore` matched `authority` through `**/*auth*`, omitting
these reviewed files from the mirror snapshot while leaving them in production:

| Exact path | Reviewed and production Git blob |
|---|---|
| `scripts/run_export_authority.py` | `e2041dd47ab42d0f6349413914b2bf43f6c55aa9` |
| `services/export_execution_authority.py` | `9b95e69ef2b0f86cdfca5e0e987a6fc75d54a2a0` |
| `tests/test_export_authority_boundaries.py` | `6de87f9b75b59744eb6a9fef76ef51f45b9c86e5` |
| `tests/test_export_authority_launcher.py` | `ed43c4155b3334d37d491576f8e83aee6c22e15b` |
| `tests/test_export_execution_authority.py` | `5230e8bc2ab7031ae1a4708eae396bef3cec2837` |

The initial approved repair restored exactly these production bytes and added five root-anchored include
rules before the broad auth exclusion. Other credential/runtime exclusions remain in place;
the production publisher's existing secret scan remains unchanged. No folder-wide or general
Python exception is introduced. The
[rsync manual](https://download.samba.org/pub/rsync/rsync.1) documents `+ ` include rules in an
exclude-from file and ordered filter matching.

`tests/test_mirror_publish_policy.py` checks exact exceptions and restored source presence,
then exercises the real publisher rsync flags against inert allowed files and credential-like
negative fixtures. `.github/workflows/mirror-publish-policy.yml` requires rsync and runs that
test with read-only repository permissions. No real credentials, runtime data or production
publication directory are used by the test.

Production already has these original five blobs. The review correction above changes four of
those paths and other existing files. Future patch-based promotion must compare current blobs,
carry those modifications plus `.publishignore`, policy test/workflow and documentation, and omit
only still-identical additions. Do not push mirror history into production. Bot-machine
deployment remains only from reviewed `K98-bot/main`, under later exact approval.

## Filename, content and archive proof

The [machine-readable merged delivery manifest](s11_merged_delivery_manifest.json) records
every original Bot and SQL delivery identity, immutable refs, expected/merged blobs, mirror
presence and exact `previous_filename` or base/content/absence proof. It is not a count-only
check and describes the merged trees before this new documentation delta.

The two S10E archive destinations retain their exact reviewed blobs; their original source
paths are absent in the merged tree, with original-base proof retained. S10D/S10E closeouts,
the original S11 pack/starter and every pending Bot document were included in the genuine S11
implementation delivery. SQL's two delivery documents were separately included in SQL #89.

The only Bot merged-content difference from the final round-two publication manifest is
`s10e_closeout_and_s11_handoff.md`: blob `326e11a5e5cafbd26df9ac7c4f09e90b9558c552` became
`8efcf3f32d0e68661e7e5a17de23ac21adcfdcfb`. Exact byte comparison establishes that only one
trailing blank line was removed. The mirror snapshot's five omitted files are listed explicitly
above, not concealed by an overall inclusion total. All original SQL delivery blobs match.

Original evidence remains under the ignored `.codex_artifacts/s11-authority-composition/`:
`final-delivery-manifest.json`, initial publication proofs, round-one/round-two publication
proofs and `pr-review2-closeout.md`. No evidence or retained dataset was deleted or relabelled.
The new closeout and status updates are additive; older dated instructions remain history.

## Validation chronology and security qualification

The earlier full offline Bot suite passed **5,812 tests / 81 skipped**. The subsequent client
delta passed **704 / 1 skipped**. Final PR review corrections passed **681 / 12 skipped**;
these are separate runs, not a new full suite. SQL final review used **193 evidence assertions,
454 permission assertions and five error-free ScriptDom parses**, including CRLF checkout
validation of the exact manifest. Native/provider/SQL execution was not established.

Final correction-only security reviews used **Changes, Deep off**, separately:

- Bot `514c9dbf-b524-421a-ae11-45358e927306`, base `771be9b45f3e6eb67b224a941e31b55cf5579a7d`
  to `4b0de2f29bf731123ce5d893dd430afac66ef9fb`: complete corrected-source coverage, zero findings.
- SQL `6637beed-5f86-408a-b777-0aa1c7e9c561`, base `70d1916c39359c4bf5cf990552c3b1e57850b2c4`
  to `0aab5d74e116291bde9b027e44ca819fa35db03c`: complete corrected-source coverage, zero findings.

These correction scans do not replace earlier whole-change coverage. The earlier Bot scan
`8cf1584b-9dd4-45bd-918d-7ad55c562173` retains an obsolete pending-review machine row; its
supporting completed reviews/hash clarification remain retained. Do not silently relabel that
machine flag or count the final whitespace-only document correction as a new runtime scan.

Mirror-repair validation: 196 focused tests passed, one real-rsync case skipped locally; all six
repository gates passed and operational logs were preserved. Separate configuration Changes scan
`61ed6784-ae3d-4d5e-aba1-ecc24685151c` completed with zero findings and complete scoped source
coverage. The [current receipt](release_evidence_log.md#mirror-repair-and-g4g5-handoff-validation--2026-09-25)
records the frozen target, post-scan AST-equivalent formatting, usage and retained report. The
Linux rsync check was unavailable at local preparation; its subsequent passing CI result is
recorded in the published handoff receipt above. Require final-head CI before merge. No SQL source is changed by the repair; new SQL
closeout text is documentation-only and does not warrant another SQL runtime scan or execution.

## Remaining work and ownership

1. Review/deliver the narrow mirror repair and Bot handoff together, then verify production's
   corrected publishing policy and regenerated mirror file identities. No standalone docs PR.
2. Develop the exact G4 packet from the new pack: targets, operations, prerequisites, evidence,
   rollback and independent approval checkpoints. Unknown runtime facts remain unresolved.
3. Execute only the specifically approved operation IDs on the approved packet/targets. Retain
   every receipt and stop/reconcile on uncertainty. Approval for one group does not cover others.
4. Present the completed evidence matrix for operator G5 accept/reject/defer decisions and a
   separate explicit activation decision. No source merge closes those gates.

S6-OPS01/PERF01/CAP01, both uncertain publications and all retained data remain open/preserved.
S8A six scripts, S8B 50 cases/actual restore versus offline history and S8C seven local checks
remain distinct. Preserve every pack invariant, P/Q/R, 9,000,000-cell parts, 8/16 bounds,
registration-aware intents and exact owner/fence/version/receipt contracts.

Rollback closes admission, drains/reconciles owned delivery and retains uncertain claims,
origins, journals, receipts and SQL history. Old-writer termination and private clear/readback
precede audited reuse; interrupted retirement needs journal recovery and no-delayed-effects
proof. Never use age/job state or a flag flip to infer release, and never blind-retry uncertainty.

The operator explicitly authorized a separate SQL closeout PR containing only
`docs/SQL_DELIVERY_LOG.md` and `migrations/README.md`, alongside the Bot-mirror repair/handoff PR.
No SQL implementation is manufactured. Every pending/untracked Bot document accompanies the
genuine mirror policy repair, including the new pack/starter and exact identity manifest.
The two PRs can be reviewed together; neither authorizes merge, production promotion or G4
execution. Future preparation-only grouping remains unchanged unless separately authorized.
