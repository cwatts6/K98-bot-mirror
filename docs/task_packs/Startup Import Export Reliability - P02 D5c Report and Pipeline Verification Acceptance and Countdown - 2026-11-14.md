# D5c report and pipeline verification acceptance

The corrected grouped offline pass completed all **87 checks**: 34 report-continuation scenarios, 46 pipeline-verification scenarios and seven runner controls. Both routes are accepted within the original-code, simulated-database scope. No PowerShell handoff is needed for this group.

## Countdown

| Track | Accepted | Remaining |
| --- | ---: | ---: |
| Final recovery-action routes | 45 of 73 | 28 |
| Inspector checks | 25 of 25 | 0 |
| D5c acceptance families | 9 of 12 | 3 |

The 28 action routes comprise 14 export-job routes, 10 rollover routes and four private-evidence routes. The three open families remain C04 native season/routing/weight consistency, C05 native queue/pool/hold exclusion, and C06 remaining final actions and native effects. These are different levels of counting; 87 scenario checks do not mean 87 additional action routes. Later D5d/D5e/D5f and separate D6 deployment are not closed by this result.

## What this group proves

The existing Stats-report recovery code checks exact identity, evidence, guards and saved intent before requesting the unfinished reports. The cases cover changed evidence, busy owners, duplicate completion, known failures, lost acknowledgements, reconciliation and cleanup. Already-modeled reporting timestamps are preserved.

Pipeline verification uses the original child-result observers for import and configuration, original association snapshots, final guarded decision and reconciliation. It records a completed child result against the same pipeline operation without starting the pipeline worker. Changes to scope, registration, child receipts or stage versions are refused, including changes immediately before the final decision. Original history and other stages remain intact.

SQL validator/report procedure effects are explicit inert models. Actual report calculations, archive validation, checkpoint skipping, physical locking, constraints, commit durability and provider effects remain outside this result. Simulated lost replies test control flow, not real database uncertainty. Some negative cases invalidate the full token before deeper gates; unique scenario identifiers are not a claim of independent branch coverage.

## Failure and correction preserved

V1 stopped before any scenario because its loader denied a source file omitted from the manifest: `services/stats_import_outcome_service.py`. Its intent, failed result, review, packet and code remain unchanged. V2 adds that exact source pin and a recursive audit of all 41 literal loader files. Test behavior is byte-identical and runner changes only separate its evidence identity. The safety boundary was not loosened. Existing operator approval covered the additional offline pass; no frozen attempt was repeated.

## Evidence and limits

- V2 packet SHA256: `8ce8d172b35d816cea20b89239897dd06f4d1d614f21544f3deb454c77bbb4c9`.
- Result SHA256: `6f4b4a38b1e71579b2cb9605327bc92ddc6d3fc8eab34599059938fc9434c653`.
- Elapsed: 0.812 seconds; combined intent/result: 25,387 bytes, within 300 seconds and 1 MiB.
- All 967 preservation pins and 27 authoritative SQL source pins verified unchanged. All seven runner guards behaved as expected. No pending tasks, extra threads or unexpected output remained.
- No native operations, new inputs, synthetic rows, runtime/SQL-source changes, permission changes or VM changes occurred.
- Inputs remain 21 consumed; native allowance 1,260 seconds including the protected 1,000-second later-phase reserve; Windows-test allowance 50 seconds; synthetic rows 11 of 64.
- Ordinary Git HEAD/index remained unchanged; review commits are isolated snapshots.

[Acceptance record](../../.codex_artifacts/p025/d5c-report-pipeline-verification-acceptance.json), [cumulative closeout](../../.codex_artifacts/p025/d5c-report-pipeline-verification-closeout.json), [V2 result](../../.codex_artifacts/p025/d5c-report-pipeline-verification-v2/result.json), [original failure](../../.codex_artifacts/p025/d5c-report-pipeline-verification/result.json).

## Review and validation

Changes review, Deep off, exact five-file V2 range `e37fa0602480b83fe4f6ea119e7352751dcdd09e..aaea5e14745f1ceff40e38e59d60d00f23cf5510`; scan `1907b2bf-1422-43a3-80e4-846ca46c4613`, sealed before execution at `2026-11-14T21:39:24.036986Z`. Parent and independent reviews found no blocker or reportable security finding. The original scan `e859e48d-3e6d-4686-a48e-633c73499c49` remains complete; it did not catch the missing allowlist pin, which was subsequently refused by the runtime boundary. An early review-draft request omitted its required reason field; the rejected request was corrected before review completion, with no scenario execution involved.

Measured review usage: V1 3,345,360 total tokens (3,275,264 cached input); V2 1,826,370 total tokens (1,820,160 cached input). These are tool-reported review counts, not additional native seconds or inputs.

The bounded runner is the selected targeted validation. Full application pytest and smoke imports were not run because this packet deliberately excludes runtime startup and unrelated dependencies. Architecture, deferred-item, test-selection and security-routing PR gates remain required at actual PR handoff. No PR, promotion or deployment took place.

## Next grouped work

Prepare the remaining export-job, rollover and private-evidence action checks in coherent batches, preserving their separate permission/provider-effect boundaries. Then reconcile the outstanding native C04/C05/C06 evidence and later D5 stages. Existing accepted checks need not be repeated to refresh evidence.
