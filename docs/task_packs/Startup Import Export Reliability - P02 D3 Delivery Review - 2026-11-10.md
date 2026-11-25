> **Final merge receipt, 10 November 2026:** [PR739](https://github.com/cwatts6/k98-bot/pull/739) merged at `5ec55e3bbfaaca020b6046e94d80bb7645736742` after exact-head review and six passing CI checks; zero unresolved threads. Final local regression: 13,376 passed / 1,262 skipped; Linux CI: 13,197 passed / 1,441 skipped; updater 315 and release identity 111 passed. Runtime and operational evidence limits below remain. [Final receipt](https://github.com/cwatts6/k98-bot/pull/739#issuecomment-6773271380). Proceed to [D4 scope review](archive/Startup%20Import%20Export%20Reliability%20-%20P02%20D4%20Scope%20and%20Handover%20-%202026-11-10.md); no deployment occurred and D4/D5 remain required. Earlier PR-open and pre-cleanup test records below are historical.

# P02 D3: source delivery closeout

D3a–D3g are implemented, individually reviewed and merged in the Bot mirror;
the six SQL companion slices are merged in the authoritative SQL repository.
This closes D3 source delivery and its bounded qualification. It does not close
D4/D5, establish installed compatibility, or authorize deployment/restart.
The operator authorized the combined private production PR and its review cycle.

## Delivered scope and expected impact

| Slice | Coverage and change | Practical effect |
| --- | --- | --- |
| D3a — shared file ownership | Exact physical lock ownership across ordinary/guided player cache, startup readback, Ark team/state and tracked views; body errors, cancellation, foreign successors and uncertain cleanup | Original errors survive; cleanup cannot delete another operation's lock or silently permit unsafe reuse. |
| D3b — maintenance ownership | Six fixed kinds; coalesced durable generations, exact claims, first/current failure, unknown outcome; fresh dedicated SQL connection and verified physical release | Optional work has its own durable outcome; process cancellation or a pooled connection close cannot manufacture completion. |
| D3c — import | Phase A sampled statistics and conditional KS4 upkeep moved behind committed import intent; required scan/history/metadata work retained; managed snapshot reader/schema exclusion | Shorter required import work; maintenance cannot overlap the managed recovery reader's schema-sensitive snapshot. |
| D3d — configuration | Actual CREATE_DELTA_TABLES upkeep, original large-batch/168-hour eligibility, typed outer transaction and optional log handling | Configuration publication and maintenance remain distinct; a failed timing log cannot erase successful upkeep or the first failure. |
| D3e — player report | FULLSCAN moved after transactional report publication; provenance, capture, name publication and D2 statement cap retained; all worker kinds take player-publication guard | Consistent report publication without coupling its commit to FULLSCAN. |
| D3f — KVK output | Required schema/unique indexes/calculations/views/exact receipt retained; post-output nonunique index upkeep and FULLSCAN deferred; typed per-KVK generation plus object/header identity, one target per pass | Bounded optional work cannot accidentally act on a replaced output or report incomplete multi-target work as complete. |
| D3g — final reports and backup | Dashboard/summary intent at each actual stage commit; optional statistics/completion CHECKPOINT moved; exact final success receipt preserved; one durable backup request with no fallback after uncertain dispatch | Final report success no longer waits for optional backup work. Backup relief remains eligible from committed summary demand even when statistics are deferred by high log usage. |

All six maintenance boundaries are represented: import, configuration, player report,
KVK output, final stats and explicit post-import. Required business calculations,
output identities, receipts and pre-admission checks remain. Backup acknowledgement
means a request was accepted; it does not prove a backup completed. Historical
unowned backup queue rows are held for reconciliation, never adopted or expired by age.

Expected benefits are fewer false business failures, shorter required commit paths,
truthful recovery evidence and controlled maintenance ownership. No latency percentage,
throughput gain or production resource saving is claimed: D5 measures the combined cost.

## Merged source receipts

| Slice | Bot mirror PR / merge | SQL PR / merge |
| --- | --- | --- |
| D3a | [513](https://github.com/cwatts6/K98-bot-mirror/pull/513) / `1e001aad` | No SQL change |
| D3b | [514](https://github.com/cwatts6/K98-bot-mirror/pull/514) / `f910fa83` | [142](https://github.com/cwatts6/K98-bot-SQL-Server/pull/142) / `8ba5850a` |
| D3c | [515](https://github.com/cwatts6/K98-bot-mirror/pull/515) / `2d1103df` | [143](https://github.com/cwatts6/K98-bot-SQL-Server/pull/143) / `faddbd12` |
| D3d | [516](https://github.com/cwatts6/K98-bot-mirror/pull/516) / `b80c5813` | [144](https://github.com/cwatts6/K98-bot-SQL-Server/pull/144) / `adb5f8a7` |
| D3e | [517](https://github.com/cwatts6/K98-bot-mirror/pull/517) / `04223144` | [145](https://github.com/cwatts6/K98-bot-SQL-Server/pull/145) / `2af0a70e` |
| D3f | [518](https://github.com/cwatts6/K98-bot-mirror/pull/518) / `aee7d882` | [146](https://github.com/cwatts6/K98-bot-SQL-Server/pull/146) / `6504865e` |
| D3g | [519](https://github.com/cwatts6/K98-bot-mirror/pull/519) / `4bdf3151` | [147](https://github.com/cwatts6/K98-bot-SQL-Server/pull/147) / `0d93e228` |

D3g final reviewed heads: Bot `738a702dd7958ce1be108e226b922a64b2871710`,
SQL `9cb0895cb2dc1d9bf59cf7c898b36ddbe7e17d89`. Both code reviews completed
without findings or unresolved threads; SQL CI passed twice (3m08s and 4m25s).
The earlier D3 scope/documentation PR512 is included in combined promotion.
SQL plans are reconciled in documentation PR148, merged at `6d88e09a`.

The full regression exposed one stale updater-history test dispatcher after the
runtime slices merged. [Mirror PR520](https://github.com/cwatts6/K98-bot-mirror/pull/520)
adds the missing D3c/D3d/D3e/D3g mappings to existing authenticated predecessor
bridges. Runtime, transition entries, bridge implementations and historical hashes
are unchanged. All 243 focused updater/history checks passed after the correction.
The preceding full run retained 13,319 passes, 1,262 skips and that one failure;
the clean full result below is the repeat on the corrected stable tree.

## Qualification and evidence limits

Pre-cleanup-correction full Bot regression: **13320 passed, 1262 skipped, 1 warning, 8 subtests passed in 1579.22s (0:26:19)**.
The operational-log isolation check confirmed production logs unchanged.

Focused D3g qualification: 122 combined native/Python cases passed before the
review correction; all 14 final native D3g cases passed after it, including injected
75-percent log observation with actual dispatch/claim SQL and simulated backup.
133 updater/history checks and final pre-commit/repository gates passed.
The final-report continuation fixture executes real guards and receipts with simulated
large calculations; separate exact-source checks preserve the actual business body.
Disposable native coverage includes both ownership orders, outer commit/rollback,
real statistics/index children, partial KVK progress, stale output identity, first
failure, failed ACK and unknown physical absence. D3a additionally has native
Windows/POSIX and separate-process evidence in its archived delivery review.

One unrelated opt-in native continuation assertion remains recorded: the changed
exception-chain test expects only exception_types/observed_utc to differ, although
fingerprint also differs. Its assertion was not relaxed and unrelated runtime code
was not changed. The remaining continuation selection passed. The earlier D3g full
run was stopped before source edits after review found the backup eligibility coupling;
that partial log is retained, not counted as acceptance. The stable result above
supersedes it. Actual provider/SQL Agent delivery was never invoked by these tests.

Review found and corrected the backup-relief/statistics-headroom coupling before
merge. Historical failed fixtures and initial evidence remain separate from final
results. There is no claim that every possible edge case or production topology
has been exercised.

Security Changes reviews covered every slice; Deep was off. D3g Bot scan
`d7883c6d-b020-4b4e-b797-dfc482cbc2a1` covered all 51 paths at runtime head
`0ce80f19`; SQL scan `3276c65e-3ec5-43d3-ab80-acc48bb8c59a` covered all 17 paths
at `f2712a8`; SQL correction scan `4b1addf0-1e6d-4dfc-a427-cbbcd9563cc9` covered
all four changed paths through `9cb0895`. All had zero security findings. Bot's
final follow-up is tests/evidence only, with a precise security skip.
The first two recorded identical overlapping usage windows: 2,638,109 total tokens
(2,630,650 input, 2,603,776 cached, 7,459 output). Correction: 341,058 total
(340,328 input, 339,840 cached, 730 output). Do not sum overlapping windows as billing.
Earlier slice scans and receipts remain in their archived packs.

Combined private candidate Changes scan `c3802c0c-ffee-44c4-a3e0-afea83f57f7e`
reviewed exact private `cd04ed5e..5b2eb398`: all 112 changed paths, zero findings.
Its measured window was 2,690,463 total tokens (2,681,144 input, 2,630,400 cached,
9,319 output; 1,484 reasoning output). This is scan-reported usage, not a sum or
billing claim. The final closeout/archive follow-up is Markdown only, with a
documented security skip and exact runtime/test equivalence retained.

The private production PR is [739](https://github.com/cwatts6/k98-bot/pull/739).
Its first candidate passed all six CI checks, including 13,141 Linux tests;
the code review was clear. The separate Copilot review raised three comments.
The password-placeholder claim was disproved against the exact source f-string
without reading credentials or attempting a connection. Mirror
[PR522](https://github.com/cwatts6/K98-bot-mirror/pull/522) corrects the two valid
text issues: the D3g archive heading's encoding and its final-report refusal label.
All 56 D3g transition tests pass; AST comparison proves only the diagnostic literal
changes. No predicate, exception type, registry, hash or admission policy changes.
This follow-up has a precise security skip for diagnostic text and documentation;
the private PR retains the final-head CI and comment-cycle receipts.

A final sweep also reconciled late comments on the already-merged slice PRs.
The native fixture already uses IF EXISTS for both tables and has no intervening
foreign key; Python text reads already normalize CRLF; current SQL source is
authenticated against all 23 fixed pins before historical P0/Phase 1 comparisons.
The pending worker result and durable pipeline observation already expose the
non-complete outcome. Extra telemetry, a duplicate procedure field and hoisting
a four-entry test mapping were optional consistency suggestions, not demonstrated
correctness gaps, and were not added. Remaining archive-title/spacing and SQL
native-test opt-in documentation were clarified. Exact replies and dispositions
remain on the original review threads; no runtime or test behavior changed.

The original D3g updater had 87 fixed entries; prior 86 digest is
`49752cc86f05563aeb7b04111c050e2730548e0a32654e757b5b24e7d7991d90`.
D3g has twelve members, six changed. The 232448-byte registry cap is unchanged.
Exact per-slice transitions are not authority for the installed combined jump.

## Late cleanup review correction

The private review subsequently identified an actual ownership gap: snapshot
isolation restoration or cursor-close failure could still reach connection.close,
and maintenance cursor-close failure had the same path. Closing a handle can return
a session to ODBC pooling; a retained reference afterwards is insufficient custody.

The correction stops cleanup at its first unacknowledged boundary and preserves
the first failure, connection and cursor. Coverage includes snapshot and maintenance
owners, plus equivalent player-report, import-capture, source transaction and legacy
writer callers. An exact-identity custody query prevents outer owners from closing
a connection already retained by an inner cursor, rollback or diagnostic helper.
Healthy cleanup and unrelated connections retain their existing semantics. No
business replay, automatic cleanup retry, new SQL object or permission is added.

Focused regression: 315 passed plus eight disposable-local native SQL cases,
including transition authentication and injected cursor/reset/rollback/guard/close
failures, cancellation and nested ownership. Nested cursor/guard resources remain
strongly referenced without replacing the first custody evidence or incrementing
its owner count; an original UncertainCommit remains the primary error if outer
cleanup also fails. The first follow-up Changes review found no security candidates
but exposed these reliability gaps; they were corrected before merge acceptance.
The correction adds one eight-member updater transition, taking the registry to 88
entries. All prior 87 entries remain immutable (digest
`3f164e60c4398e9f4b1f2404b15cc0863b97ee658572824dd02b3e67f9597879`);
the 232448-byte cap remains unchanged. Full CI, native qualification and the exact
Changes review receipts for this follow-up are retained on its mirror PR and the
combined production PR739. Earlier full-suite and security receipts above remain
historical evidence for their recorded heads, not substitutes for this follow-up.

The full cleanup regression exposed one historical D2j fixture still comparing
current custody bytes directly with its original postimage, plus two older tests
expecting connection close after failed rollback. The fixture now authenticates
the current successor before exposing the unchanged historical hash; the two
assertions require retained ownership and no pool-return attempt. Runtime and
registry bytes are unchanged by this test correction. The preceding run retained
13332 passes, 1262 skips, two stale assertions and 42 setup errors from that one
fixture. Corrected focused results and the final full repeat are recorded on PR524.

## Remaining programme obligations

D4 owns current installed/manual/legacy bindings (including UPDATE_ALL/Rally/TEST),
permissions/signing and final Bot/SQL/startup pins, plus the demonstrated
`COORDINATED_RELEASE_REQUIRED` combined transition. It must reconcile the missing
authoritative `KS4_UNO_SEQ` definition and installed msdb backup wrapper, direct
child guard expectations and historical backup queue outcomes. No guessed objects,
new grants, TRUSTWORTHY switch or automatic replay substitutes for this evidence.

D5 owns final scale, cost and whole-programme fault/restart/concurrency qualification.
Keep RCSI off; preserve 8 GiB free memory/disk reserves, log below 70 percent for
optional statistics, version store below 512 MiB and the existing balanced cost
limits. The single 21-input rehearsal allowance remains consumed. No timeout,
input-cap or backup-schedule increase is implied.

After D5, separately controlled deployment must refresh actual installed identity
and changed-file/ancestor custody. SQL ledger/child/producer and Bot changes form a
coordinated release; reverting Bot alone is not a sufficient rollback policy.
Preserve committed imports, output captures and provider effects. P03 actual
blockers plus essential P04 corrections precede the first standard import/export;
zero incidents and waiting merely for P05 are not prerequisites.

The active D3 handover carries these remaining obligations. Completed slice packs
and original scope evidence are archived with links retained through mirror/private
promotion. This closeout performs no production SQL, deployment, restart or recovery.

## Archived slice evidence

- [Startup Import Export Reliability - P02 D3a Coverage Delta - 2026-11-10](archive/Startup%20Import%20Export%20Reliability%20-%20P02%20D3a%20Coverage%20Delta%20-%202026-11-10.md)
- [Startup Import Export Reliability - P02 D3b Maintenance Ownership - 2026-11-10](archive/Startup%20Import%20Export%20Reliability%20-%20P02%20D3b%20Maintenance%20Ownership%20-%202026-11-10.md)
- [Startup Import Export Reliability - P02 D3c Import Maintenance - 2026-11-10](archive/Startup%20Import%20Export%20Reliability%20-%20P02%20D3c%20Import%20Maintenance%20-%202026-11-10.md)
- [Startup Import Export Reliability - P02 D3d Configuration Maintenance - 2026-11-10](archive/Startup%20Import%20Export%20Reliability%20-%20P02%20D3d%20Configuration%20Maintenance%20-%202026-11-10.md)
- [Startup Import Export Reliability - P02 D3e Player Report Maintenance - 2026-11-10](archive/Startup%20Import%20Export%20Reliability%20-%20P02%20D3e%20Player%20Report%20Maintenance%20-%202026-11-10.md)
- [Startup Import Export Reliability - P02 D3f KVK Output Maintenance - 2026-11-10](archive/Startup%20Import%20Export%20Reliability%20-%20P02%20D3f%20KVK%20Output%20Maintenance%20-%202026-11-10.md)
- [Startup Import Export Reliability - P02 D3g Final Report Maintenance - 2026-11-10](archive/Startup%20Import%20Export%20Reliability%20-%20P02%20D3g%20Final%20Report%20Maintenance%20-%202026-11-10.md)
- [Startup Import Export Reliability - P02 D3a Delivery Review - 2026-11-10](archive/Startup%20Import%20Export%20Reliability%20-%20P02%20D3a%20Delivery%20Review%20-%202026-11-10.md)
- [Startup Import Export Reliability - P02 D3 Original Handover and Scope - 2026-11-10](archive/Startup%20Import%20Export%20Reliability%20-%20P02%20D3%20Original%20Handover%20and%20Scope%20-%202026-11-10.md)
