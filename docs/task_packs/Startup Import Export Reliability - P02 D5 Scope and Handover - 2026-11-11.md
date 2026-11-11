# P02 D5 integrated qualification: scope and handover

Status: D4 source delivery and production repository promotion are complete.
Private [PR740](https://github.com/cwatts6/k98-bot/pull/740) merged at
`ef8aee342fbe2d91c9e8aaef34c0df6b54570803` on 11 November 2026 at 10:41:16 UTC.
This is not deployment or D5 acceptance. Begin D5 with a fresh scope review,
cross-repository obligation reconciliation and missed/new-issue check.

## Authority and working approach

The operator requested PR740 merge, this scope/handover, updated documentation
and archives, and a new D5 chat. Carry settled P02 decisions forward; do not ask
again whether to begin the review. The first deliverable is review/scope only:
reconfirm the bounded D5 sequence and identify concrete decisions before new
implementation or native qualification runs. Existing approval does not imply a
new input copy, expanded resource allowance or arbitrary test-host mutation.

No production SQL installation, deployment, restart, backup/provider dispatch,
retained-work recovery or normal import/export is authorized by this handover.
D6 release authorization remains separate after D5. Read-only source review and
preparing a concrete qualification packet may proceed now. Preserve unrelated
working changes and use the existing Bot and SQL checkouts; no new worktree is
required. The new chat must start the review, not merely acknowledge the packet.

Maintain the established approach: no point fixes; assess Bot and authoritative
SQL together, include equivalent/direct/legacy callers, compare proportionate
alternatives, keep the Bot and startup safe, and retain failed evidence apart
from later recovery or success. A new issue needs evidence, consequence, owner,
disposition, prerequisite and acceptance proof; do not silently defer a required
obligation or widen D5 into unrelated refactoring.

## Verified starting evidence

| Item | Receipt and boundary |
| --- | --- |
| Private D4 | Reviewed head `8b6879bfde30dec6de2f9f4500e935cf89d22450`, merged as `ef8aee342fbe2d91c9e8aaef34c0df6b54570803`; all four applicable checks passed, code review clear, four documentation threads fixed/resolved. |
| Mirror delivery | PRs 525-534 merged; final D4 mirror `835005b5a16c87c01b9ae175f161fbe22c26e134`. Mirror subsequently refreshed to scrubbed `9b3bf339e97f503f0bdb0700a17c405195d2fc88` from private `ef8aee34`; refresh again before future publication. |
| SQL source | PRs 150-155 merged. Fixed payload stays `ba5c6acbefba0eb89cb18842a7f6c6811096759b`; documentation successor `5520daacb0da6dcd2527219241ac36ee25843a11` does not change it. |
| Fixed release | Migration `20261111_001_p02_d4_combined`, profile `p02_d4_v1`; 30 objects, four ledgers, six maintenance kinds, 13 existing predecessor definitions and 17 new objects; eight initial rows, no adoption of historical work. |
| Installed baseline | Last accepted installed Bot `97abcce1b2a9e71b3959eff74525c57930a703e6`, accepted Phase 1 SQL `a202a51440f17233800b49801bd31c3ead2a9227`. D4 installed receipts were bounded observations, not a new deployment or continuous-use proof. |
| Startup/update qualification | Actual reviewed private head passed 13 offline cases: 841 predecessor source pins, 14 updater members, 852 successor pins, three startup contracts, seven fixed SQL payload files and missing/altered/partial/foreign refusals. Generated candidate is not installed. |
| Registry | 89 entries: one complete 79-member combined successor; all original 88 definitions and 232448-byte cap retained. No redesign or historical hash rewrite. |
| Final CI | Quality attempt 2: 13,249 passed, 1,458 skipped, 19 warnings, eight subtests; imports/registration passed. Windows: 315 Python cases plus seven PowerShell 5.1 scripts; release identity: 111 cases; secrets check passed. Failure below remains evidence. |
| Security | Bot Changes scan `e350717c-3367-4d49-a0a9-f4d113112888`, exact `5ec55e3b..7cefa991`, zero findings across 94 files; subsequent 15-line Markdown delta to `8b6879bf` inspected with documented skip. SQL scan `247247c4-a99d-4334-8b69-1beeb706232b` covers its separate 18-file PR154 target, zero findings. Neither establishes live-host/provider acceptance. |

The [final PR740 receipt](https://github.com/cwatts6/k98-bot/pull/740#issuecomment-6793565436)
records detailed validation and scan accounting. Its original unmerged wording
describes the pre-merge receipt; the verified merge above supersedes that status.
The [D4 delivery register](Startup%20Import%20Export%20Reliability%20-%20P02%20D4%20Delivery%20and%20D5%20Handoff%20-%202026-11-11.md)
retains the complete F01-F32 and C01-C16 mapping. The
[combined transition](Startup%20Import%20Export%20Reliability%20-%20P02%20D4d%20Combined%20Transition%20-%202026-11-11.md)
remains active release-reference material until operational closure.

## Failed drain-test evidence: required D5 follow-through

Quality run `42998021332`, attempt 1, on exact `8b6879bf` failed
`tests/test_personal_stats_render_submission.py::test_cancelled_unstarted_owners_keep_two_native_slots_and_drain`.
The final `assert await runtime.drain()` at line 63 returned false. Result:
one failure, 13,248 passes, 1,458 skips, 19 warnings and eight subtests.
The test and the entire `player_self_service` tree were byte-identical to the
private baseline. The preceding complete run on `7cefa991` passed; only Markdown
banners changed between those heads. All four render-submission tests passed
locally on `8b6879bf`; one same-head CI retry passed the full suite. No Personal
Stats code, timeout or test assertion was changed.

This is unresolved failure evidence, not a proved D4 regression and not a proved
harmless flake. Native-future completion versus settlement-callback ordering is
a hypothesis, not the established cause. Do not erase it, weaken the assertion,
increase timeouts or rerun repeatedly until green. D5 cancellation/drain owner
must inspect owner-task cancellation before its first event-loop turn, both
native renderer slots, concurrent drain callers, settlement callback ordering,
executor shutdown, physical completion and admission/capacity retention.
Design a bounded deterministic investigation and relevant equivalent-caller
checks; classify any reproduced defect before proposing a focused fix.

Acceptance: explain or reproduce the failure with exact scheduling/ownership
evidence; demonstrate that logical cancellation cannot release native capacity
early and that successful drain reflects completed physical work and settlement.
If still unresolved, retain it explicitly as a D5 qualification gap with owner
and next evidence, rather than using the passing retry to close it.

Evidence: [failure disposition](https://github.com/cwatts6/k98-bot/pull/740#issuecomment-6793114051),
[quality run](https://github.com/cwatts6/k98-bot/actions/runs/42998021332), and private
`.codex_artifacts/p024/d4-private-quality-final-failed.log` plus
`d4-private-quality-final-ci.log`. These local logs are retained; do not assume
hosted log retention is permanent. Keep private receipts, principal inventories
and job identifiers out of public documents.

## Proposed D5 slices and acceptance matrix

This is the starting scope to reconfirm, not permission to execute every row.
Each test receipt must identify candidate/baseline, host/database, inputs,
effective identity, actual versus simulated work, limits, original outcome and
cleanup state. Resolve prerequisites before expensive or mutating qualification.

| Slice / owner | Required work and proof |
| --- | --- |
| D5a: reconciliation and bounded packet / Bot+SQL review owner | Reconcile D1-D4 final composition, all F/C obligations and direct/equivalent callers against current source. Inventory retained fixtures, inputs and failed receipts; check host/VM/session readiness after the prior PC crash. Produce exact isolated targets, dependency graph, operation/stop/cleanup matrix and evidence budget before execution. |
| D5b: correctness and real children / SQL+Bot test owner | Compare all 14 output sets and detailed state with accepted Phase 1; exact integer/rounding values, latest-name rules, original queued payload bytes, execution-time date windows and explicit tied-rank policy. Exercise actual import, configuration, player, KVK, final-report and post-import maintenance children, not only simulated expensive calculations. Preserve committed business/capture results when optional upkeep fails. |
| D5c: observers and competing owners / coordination+SQL owner | Both arrival orders for each relevant writer/reader/maintenance overlap; known actual holders separately from requesters; selector purity, alternate factories, stale tuples, denied rights, disabled snapshot, observation saturation and serial mutation admission. Preserve three-second statements, zero row-lock wait and bounded 30-second metadata hold. |
| D5d: failure, cancellation and restart / lifecycle+test owner | Lost lock-grant/commit/dispatch acknowledgement, rollback/reset/cursor/guard/close uncertainty, pre/post-native cancellation, owner task failure, nested physical resources, scheduling and restart. Include the failed Personal Stats drain test above and equivalent custody callers, shared Ark file locks and all six maintenance boundaries. Never infer closure from a cancelled awaiter, closed proxy, reused SPID or elapsed time. |
| D5e: controlled cost and resources / SQL+performance owner | Warmup then at least five balanced OFF/ON pairs on comparable work and inputs; measure overall/report-stage cost, observer saturation and actual maintenance. Retain original failures and confounds. No new speed benchmark solely to justify shared names; no arbitrary index or instrumentation programme. |
| D5f: integration closeout / Bot+SQL+release owner | Reconcile every matrix row to passed evidence or an explicit unresolved gate. Confirm final source/profile/startup/updater compatibility and documentary archive carry-forward, then prepare D6 readiness and recovery sequencing. Do not label source/fixture success as host-ready, installed or whole-flow/provider acceptance. |

Specific retained cases include backup relief from committed summary demand when
high log use defers optional statistics; requested versus completed backup;
hidden/denied wrapper metadata; one attempted dispatch and no fallback/replay
after uncertainty; legacy backup queue guards preserving historical rows;
exact KVK target identity; and changed/foreign file-lock sentinels. No real backup
dispatch is needed to discover route permissions.

Raw-history SNAPSHOT across index REBUILD failed with SQL 3961. Keep that failed
receipt and distinguish qualified managed metadata readers from arbitrary
history readers/ad-hoc DDL. A correct direct-child refusal is not proof of actual
maintenance performance; a test that models work is not real-child acceptance.

## Resource and data boundaries

- RCSI stays off. Preserve at least 8 GiB free memory and disk, sampled log below
  70 percent for optional statistics and version store below 512 MiB.
- Overall median ON <= OFF * 1.20 + 1000 ms; each report-stage median
  ON <= OFF * 1.20 + 250 ms, after warmup and at least five balanced pairs.
- The 1800-second rehearsal cap is not a Bot timeout increase. Preserve current
  connection/command limits and explicit operation-specific overrides.
- The single 21-input allowance is consumed. Reuse only valid retained authorized
  evidence/fixtures after checking their state; no new copy, reset, restore,
  expanded allowance or backup-schedule change is implied. Missing prerequisites
  require a concrete bounded proposal, not an invented replacement dataset.
- Keep immutable original failure evidence separate from current/resolved state.
  Do not delete retained captures, inputs, claims, job rows or previous run folders
  to make qualification easier. Identify exact ownership/outcome before retry.

## Remaining programme obligations and ownership

The full F01-F32/C01-C16 register remains in the active D4 delivery record;
the programme scope, tracker, coverage, tracing, final sweep, principles and
remaining-work handover remain active. Reconcile rather than replace them.

| Owner | Obligations carried forward |
| --- | --- |
| D5 | F01/F03/F07/F08/F09/F12/F14/F16/F18/F20/F21/F22/F24/F26/F32: actual workload, observers/holders, all maintenance boundaries, factory/custody, failure/restart and cost. D4 resolves F31 retirement within bounded caller evidence; recheck compatibility, not arbitrary historical non-use. |
| P03 | F02/F04/F06/F09/F10/F15/F28/F29: actual retained-work blockers, original-intent capture/stream/claim closure, configuration attempt and separate Rally XLSX attempt-versus-success identity. Retiring legacy SQL roots does not close Rally XLSX recovery. |
| P04 | F04/F05/F06/F11/F13/F19/F27/F28: cancellation, incident/history/notification convergence, journal capacity and waiting-versus-conflict classification. Preserve original first failure. |
| Accepted P01 with retained limits | F08/F11/F17/F23/F24/F25/F30: existing startup/passive health, file/calendar outcomes and natural observations remain accepted within their recorded scope. Do not repeat deployment or business effects just to refresh evidence. |
| D6 | Separate release decision after D5; fresh installed source/updater/seed, effective process identity and rights, exact changed paths and all ancestors including archives; safe drain, fixed SQL package, same-release receipts, source/seed/start/readiness. Configuration files alone do not attest the running environment. |
| D7/P05 | Exercised whole-flow/provider and natural acceptance. First normal import/export follows P03 actual blocker settlement plus essential P04 corrections; it is not deferred merely until P05 and does not require cosmetic zero incidents. |

Action census remains 73 pairs, 52 action names, 22 kinds and four empty kinds.
Recheck, group approval, historical/evidence batches and outcome workers remain
outside that count and inside the review. Refresh action-time predicates; empty
action lists and zero incidents are not evidence of passivity or health.

SQL may commit before source/seed/start/readiness completes. Recovery after that
commit is forward-only from the same verified receipt: no SQL replay, reverse
bigint-to-float conversion, old-Bot fallback or second start to repair uncertainty.
Production uses private main and Windows PowerShell 5.1. Existing fixture limits
for substituted administrative ACL/task controls and PowerShell 7 historical
checks remain visible; do not silently claim native PS5.1 production proof.

Broader datatype conversion, snapshot decode/rebuild optimisation, broad importer
extraction, Stats UI/SDK acknowledgement, unrelated MGE/Ark performance and
standalone pre-KVK/weekly physical-close debt keep their existing owners. Bring
work forward only for a demonstrated dependency. The new drain evidence is an
explicit D5 investigation, not an unowned optimisation note.

## Architecture, references and first review deliverable

Review service/DAL ownership, `core/sql_connection_custody.py`,
`core/recovery_sql_snapshot.py`, maintenance service/DAL/worker, player/report/
import-capture/legacy-export custody, `player_self_service/stats_runtime.py`,
`tests/test_personal_stats_render_submission.py`, shared file-lock consumers,
observer dispatch and the existing combined release tooling. Reuse those
boundaries; commands/views stay thin. No new scheduler, outbox, polling framework,
blanket index, broad grant or speculative instrumentation is implied.

Authoritative SQL: `C:/K98-bot-SQL-Server`, especially
`docs/p02-d5-scope-handover.md`, `docs/p02-d4-delivery-handoff.md`,
`docs/p02-d4c-combined-release.md`, the integrated SQL plan and exact schema/
qualification sources. Validate names and contracts there before changes.
Read current AGENTS/core references, local SQL development guidance, relevant
startup/shutdown/diagnostic contracts and promotion/Windows custody guidance
only where applicable.

First new-chat output: current cross-repository baseline and caller/ownership
matrix; obligation disposition including the drain failure and SQL 3961; any
missed/new issue with owner and evidence; revised D5a-f order; exact first bounded
slice, tests, prerequisites, cost/stop conditions and genuine decisions needed.
Reconfirm scope against the overall programme goals before implementation.

This handover/archive change is Markdown only. Run architecture, deferred-item,
security-routing, test-selection, introduced-link, archive-preservation and
whitespace checks plus pre-commit. Runtime/native/provider tests are skipped for
the prose delta. Future executable Bot and SQL changes need separate exact diff
Changes reviews or precise skips; no standard/deep audit is implied.
