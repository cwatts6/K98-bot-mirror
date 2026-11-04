# P01.2a local PR readiness

> **Current programme checkpoint - 4 November 2026 (E68/E69):** P01.2a is deployed and accepted for its declared reporting/evidence scope at private `67c4e12a8ecf0c25280770860480ac65a6826602`.
> Read the [P01.2a closeout](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Closeout%20-%202026-11-04.md) for delivered corrections, evidence limits, learnings and remaining owners; [P01.2b handover](Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Handover%20and%20Scope%20-%202026-11-04.md) is the next review/design task.
> Earlier dated statuses, holds and next-action instructions in this document are retained history and are superseded for current scheduling. P01.3-P01.6/P02-P05 and exact incident recovery remain open; no replay of accepted work.

**Current E64:** mirror [#482](https://github.com/cwatts6/K98-bot-mirror/pull/482) and private [#722](https://github.com/cwatts6/k98-bot/pull/722) are merged. Private target `07bc9d6ebd5964f9bf660822f03a932a2472d966` is prepared for operator deployment, with final review, CI and the packet recorded in the [review/merge receipt](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Review%20and%20Merge%20-%202026-11-03.md). No production deployment, restart or recovery action was performed. Earlier scope, authorization and failed-run receipts below are historical.

Date: 3 November 2026. Authorization: tracker E61, “Agreed please continue until we
are ready for PRs.” This continues the approved P01.2a implementation; it does not
authorize opening PRs, committing/pushing, promotion, deployment or production actions.

**Status: ready for PR review.** Local implementation, qualification and final review
are complete. No PR has been opened and no commit, push or production action occurred.

## Candidate

- Mirror worktree: `C:/discord_file_downloader/.codex_artifacts/p1-mge-mirror-review`.
- Branch: `codex/p012a-evidence-bundle`.
- Base: `ecaaf2dcfa10b48cea1a088aa7465ab20bd0eb4b`; all changes remain uncommitted.
- Evidence: PR-readiness receipts (private evidence: `.codex_artifacts/startup-import-export-review-20261102/p012a-pr-readiness-20261103/final-chunked`).
- Earlier [implementation qualification](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Implementation%20and%20Qualification%20-%202026-11-03.md)
  retains the original failed producer timings and 31 updater-inventory failures.
  Those are historical results, not silently replaced samples.
- SQL source and private deployed-source checkout remain clean and unchanged.

## Corrections and evidence

Profiling identified recursive publication copying as the largest active sink cost:
the instrumented six publications took approximately 15–92 ms, with `deepcopy`
accounting for 308 of 341 ms of publication work. Direct copies of validated primitive
containers reduced the measured publication range to 2–10 ms. That first correction
alone still failed tail timing, so it was not accepted.

The final sink caches frozen rows and their exact encoded sizes. Only changed rows
are recopied; eviction removes their cache entries. File-bound calculation includes
document metadata and separators, with headroom for the final timestamp. The consumer
yields outside the producer lock after each sixteen events. It still drains every
accepted observation on close. Public readers receive defensive copies; tests verify
generation isolation, child/failure retention, exact cached sizes and cache eviction.

The original 200-pair producer harness, using current sink on both sides, passes on
the corrected source: median 12.96615→12.77870 ms; p95 14.37080→14.20830 ms; p99
27.32850→14.98260 ms. Enqueue p95/p99 0.0294/0.0521 ms; zero drops; all 400 business
calls and original returns preserved. This isolates helper/emission changes under a
shared current sink, rather than measuring the complete original sink implementation.

A supplemental 200-pair run used the exact original sink and candidate sink writing
to separate temporary directories, both active. Median overhead was approximately
1.25%, p95 6.07%, and p99 decreased. Its p95 exceeds the 5% budget and remains recorded.
A fixed 1,000-pair follow-up confirmed p95 overhead of 7.50%, so that candidate
remained failed. Profiling isolated whole-file serialization in the disk publication
path. The final correction encodes one bounded operation row at a time and yields
every sixteen chunks. It checks aggregate size and computes the exact SHA-256 before
opening the temporary file; flush/close/replace and independent V1/V2 acknowledgement
semantics are unchanged. Exact-byte equivalence and pre-write refusal are tested.

The corrected source passes a separate fixed **1,000-pair** disk-backed run: median
13.21565→13.27825 ms (**+0.47368%**), p95 18.11070→17.29860 ms (**−4.48409%**),
p99 28.72700→25.98250 ms (**−9.55373%**). Enqueue p95/p99 are 0.0358/0.0592 ms;
heartbeat deltas are −0.0688/−0.7293 ms. Both original/candidate sinks write to
separate temporary directories. No other qualification jobs ran concurrently.
There are zero drops and sink failures; all 2,000 calls and returns are preserved.
All raw call/heartbeat samples and prior failed results are retained. No filtering
or raised limits. Synthetic timing is not production performance.

The installed updater has one new fixed 14-member transition,
`p012a_evidence_bundle_v1`, including explicit absence of the two new helper modules.
All predecessor pins match both mirror HEAD and clean private deployed-source
`0247371d90ec88d4c0639e9200164f4256086037`; all successor pins match candidate source.
The prior 57 registry entries remain unchanged. The registry bound increases to 58.
Historical tests authenticate the exact new source before walking earlier contracts.
Each member is tested for altered/missing successor, wrong predecessor and omitted
inventory, plus absent installed authorization and an incomplete registry.

This prepares source capability and review evidence. An actual installed updater
upgrade package still requires the real installed manifest during separately
authorized release preparation. Candidate metadata cannot authorize itself.

## Validation

| Check | Result |
|---|---|
| Corrective focused tests | Initial 110 passed; final **1,859 passed** across 67 updater, publication, bundle, projection and redaction test files; operational logs unchanged. |
| Full Windows suite | Pre-final run: 11,151 passed, 10 updater-test expectation failures, 1,114 skipped, eight passing subtests in 1,013.14 s. All ten causes corrected; final 1,859-test batch passes. Final frozen candidate: **11,163 passed, 1,114 skipped**, eight passing subtests, one dependency warning, 987.32 seconds; operational logs unchanged. No failures remain. |
| Maximum bounds | 512 roots, all eight milestones and 16 children; all 512 exported through 64 KiB continuation and restored; two 17 MiB sessions. Additional peak RSS 105,594,880 bytes <256 MiB. V2 11,956,657 bytes; V1 2,415,288 bytes. This fixture is not every possible 32 KiB row shape. |
| Write/flush faults | Four actual-file fault cases passed; previous bytes and acknowledgements preserved, other version published independently, current memory retained, temporary files cleaned. |
| Report cost | Earlier 200-pair result retained: p95 4.38244 s, p99 4.51823 s, extra RSS 4,698,112 bytes. All three report-builder/redactor source hashes remain identical. The changed sink produces equal 64-root projections; 200-pair snapshot-reader comparison p95 1.1497→2.0568 ms, p99 1.6318→2.2223 ms, concurrent with pytest. This is narrow integration evidence, not a new 200-pair ZIP benchmark. |
| Native SQL | Earlier seven tests and 18,000-row query qualification retained; DAL and SQL source bytes unchanged. Installed connection factories and production plans remain unqualified. |
| Architecture/routing | 30 Python paths pass architecture validation; security routing has zero errors/warnings. Test selector requires full suite, UI-import disposition, smoke and registration. |
| Lint/format/types | Ruff and sequential Black pass 30 Python files. Configured Pyright: zero errors, 28 pre-existing dependency-resolution warnings. |
| Imports/commands/secrets | Synthetic-config smoke passes; registration has no unexpected drift or duplicate risks. Gitleaks scans the exact 31-file snapshot with no leaks. |

## Test isolation and failure-boundary evidence

One focused invocation omitted the shell dotenv-disable flag and was blocked from
reading the ambient root `.env`; all 1,859 setup errors had that same cause. Its log
is preserved. The test fixture now defaults `PYTHON_DOTENV_DISABLED=1`, and final
commands also set it explicitly. The corrected batch passes with synthetic settings.
No ambient dotenv content was read.

Final blocked-sink qualification accepts 1,024 events and counts exactly 1,176
critical drops. Exhausting both 256-context pools produces 400 visible losses and
zero queued/dropped events. Both cases preserve all 400 calls and returns and drain
physically. They ran concurrently with pytest; their timing is not used as normal
latency acceptance. Maximum-bound and four write/flush fault checks were rerun on
the final chunked writer.

## Security and review

Final Changes scan `b247da18-0f56-4939-a41b-c10362f9a1de` completed with Deep off,
complete coverage and zero findings. Frozen digest:
`e6499e0fa1813d71f5c42f04a32d276849783e05aae56ee06c05c3eb2b108eb8`.
Coverage includes all 16 runtime/tooling files and 15 changed tests/fixtures.
Independent reviewers inspected the final sink writer, updater authority and test
contracts. Parent coverage includes reports, runtime/UI and tests, with exact byte
verification before carrying forward unchanged complete reviews. This final scan
includes every test correction; it supersedes the preceding scan/test-only skip
for final-target coverage. No source change followed the final freeze.

Managed report: `C:/Users/cwatt/.codex/state/plugins/codex-security/scans/p1-mge-mirror-review/ecaaf2dcfa10b48cea1a088aa7465ab20bd0eb4b_20261103T204007Z_fqzze0fw/report.md`.
Completion reported 1,850,682 tokens, including 1,838,208 cached input tokens,
attributed to one chat by the tool. This is the tool's rollout usage scope, not a
claim of isolated per-file cost or complete child-agent accounting.

## Remaining boundary

**Review verdict: ready for PR review; no outstanding local blockers.** Production acceptance
remains separate: normal authorized download/startup behavior, installed updater
custody, and selected runtime connection performance require later release evidence.
No SQL migration or provider/recovery operation is introduced by this package.

The existing standalone UI-import fixture issue remains deferred with its baseline
reproduction and structured record in the earlier implementation receipt. No unrelated
production import contract was weakened to satisfy that fixture.
