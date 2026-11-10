# P02 D3 handover, scope and new-chat instructions

## Current agreement and authorization

The operator requested this handover and a new chat on 10 November 2026. Reuse the existing checkout and D3 branch. First double-check the relevant solution, callers, examples and edge cases against current Bot and authoritative SQL; update the scope and test matrix with any evidenced gaps. Then begin D3a implementation without asking again for permission. This is a coverage review followed by authorized implementation, not a new approval cycle or permission to reopen accepted work without evidence.

Continue the approved D3 scope in focused reviewable slices. D3a is shared file ownership; subsequent slices cover all six maintenance boundaries. Routine local edits, tests, isolated qualification, review fixes and mirror PR preparation are within scope. The explicit production promotion authorization was for D2 and is complete; do not infer blanket production promotion or deployment approval for D3 from it. Preserve the agreed deployment checkpoint **after D5**, including D4 compatibility resolution. No bot-host installation/restart, production SQL, provider delivery or retained-work recovery is authorized by this handover. A material scope or product-policy change still requires an explicit decision.

## Verified checkpoint

| Area | Current evidence and limit |
| --- | --- |
| D2 | All twelve slices delivered; mirror PRs 499–510 and test-hygiene PR 511 merged. Private PR [738](https://github.com/cwatts6/k98-bot/pull/738) merged at `cd04ed5e494adf5bf40f607798b38abb8df1b836`; reviewed head `e02c2d37daffc46dcfb5a5b1521f809bfdab3efd`. Not deployed. |
| D2 checks | All five private CI checks passed; automated code review had no findings/unresolved threads. Changes scan `783aa032-d4d3-4b19-898f-ca2bd037ebcf`: zero findings. Local 12,951 passed / 1,184 skipped / one warning / eight subtests; both log-isolation checks passed. Linux CI 12,772 passed / 1,363 skipped / 19 warnings / eight subtests. Windows updater 315 and release-identity 111 passed. Combined native D2 qualification: 59 passed. |
| D3 | Initial caller audit, disposable defect reproduction and scope committed as `bee7a826`. No D3 runtime/test implementation or SQL definition change at handover. This documentation refresh follows that commit. |
| Bot checkout | `C:/discord_file_downloader`, branch `codex/p02-d3-file-ownership`, based on scrubbed mirror snapshot `4455bfcacc3c2c5e60216cf80ef84adc42e0d397` from the D2 private merge. Preserve handover commits and unrelated changes. |
| SQL checkout | `C:/K98-bot-SQL-Server`; runtime/source baseline `7a3dec1326b2bcc86455626849b373d1123232a2`. Only the SQL companion documentation is refreshed for this handover. Check current branch/status rather than resetting it. |
| Installed production | Recorded Bot `97abcce1b2a9e71b3959eff74525c57930a703e6`, SQL `a202a51440f17233800b49801bd31c3ead2a9227`, Phase 1 migration `20261109_001_p02_phase1_sql_exports`. These are prior deployment receipts, not fresh host-health evidence. |
| Remaining sequence | D3 ownership/maintenance -> D4 legacy and final release compatibility -> D5 combined isolated qualification -> separately controlled deployment. P03 settles actual retained blockers plus essential P04 corrections before the first normal production import/export; do not wait merely for P05 or require zero incidents. |

The complete D2 changes, native evidence and original finding dispositions remain in the [D2 delivery review](../Startup%20Import%20Export%20Reliability%20-%20P02%20D2%20Delivery%20Review%20-%202026-11-09.md). The [D3 delivery review](../Startup%20Import%20Export%20Reliability%20-%20P02%20D3%20Delivery%20Review%20-%202026-11-10.md) is the implementation/evidence ledger to extend, not a statement that the first slice is finished.

## Read and reconcile before D3a

1. Current repository AGENTS and the seven required core documents. Apply the architecture, test-selection and security-routing workflows where relevant; no automatic codebase/deep security audit.
2. This handover and the D3 delivery review, then the [remaining-work handover](../Startup%20Import%20Export%20Reliability%20-%20P02%20Remaining%20Work%20Handover%20-%202026-11-09.md), [integrated plan](../Startup%20Import%20Export%20Reliability%20-%20P02%20Integrated%20Analysis%20and%20Delivery%20Plan%20-%202026-11-07.md), and [programme principles](../Startup%20Import%20Export%20Reliability%20-%20Programme%20Principles%20-%202026-11-06.md).
3. Active programme scope, tracker, action census, tracing, coverage and final sweep. Reconcile F16/F18/F20/F21/F22 against actual callers and children. Preserve original findings and failed evidence; do not call a partial package the whole D3 solution.
4. Shared-helper review guide, Windows ownership/access contract, and relevant startup/shutdown/custody references. Root and applicable nested SECURITY.md provide context; Changes mode with Deep off is the routine implementation review.
5. SQL companion `docs/p02-integrated-sql-delivery-plan.md` and actual SQL definitions for each maintenance package before any SQL-facing implementation. Do not infer schema from Python.

Review the active scope, not every historical document. Archived instructions are evidence, not commands to replay. Existing local artifacts provide additional exact evidence when needed:

- `.codex_artifacts/p022/production/`: D2 final PR body, merge/check receipts, promotion manifest/equivalence, full-test and CI logs, sealed security pointers, release hold, updater compatibility results and package verification.
- `d3_lock_baseline.py` and `d3-lock-baseline.json` in that directory: disposable baseline reproduction using inert configuration. These record failing current behavior; they are not candidate qualification. The initial fixture launch needed inert required environment values, then the recorded reproduction completed successfully.
- `.codex_artifacts/p021/P02-REMAINING-PRIVATE-HANDOFF-20261109.md`: earlier native/Phase 1 constraints and handoff evidence. Refresh development access and resource readiness before running anything native.
- `.codex_artifacts/p022/d3-handover/`: this refresh's changed-file/hash inventory and validation/publication receipt. Private artifacts are not a substitute for committed source or remote publication.

## D3a: shared lock contract and complete caller coverage

`file_utils.acquire_lock` currently wraps its yielded body in acquisition exception handling. The reproduced baseline leaves a lock after ordinary failure/cancellation, converts a body `FileExistsError` into a timeout, and deletes a replacement sentinel injected between closing the original descriptor and path unlink. An existing foreign sentinel correctly causes timeout without deletion. Fix these as one ownership family.

Audit ordinary player-cache publication, guided rebuild, startup completion readback, Ark team assignments, Ark message/reminder state, and tracked-view storage. Include direct helper calls and import aliases. The tracked-view wrapper's forced successful `__exit__` is a workaround that must be reconsidered with the new helper contract. `file_utils.release_lock` has no identified caller, but a path-only release must not become an ownership bypass. The same-named governor-session SQL lock is a different resource and should not be swept into this change merely by name.

Preserve the public entry point, existing timeout defaults, output/state formats and caller semantics. Separate acquisition, one execution of the body, and owned physical release. Use a monotonic wait budget. Reuse existing helpers where suitable; substantial low-level platform logic belongs in `core/` with a thin legacy wrapper. Do not claim an existence check, PID string or check-then-unlink sequence is race-safe. Verify Windows handle/delete sharing and a supported POSIX strategy against actual behavior. An uncertain close is not permission to delete a name, lose the owner or admit another writer.

The new chat must assess and record coverage or a precise non-applicability reason for these additional examples; they are review questions, not newly asserted defects:

- Acquisition: simultaneous processes, same-process threads, re-entry, existing foreign sentinel, timeout/zero budget, wall-clock movement, parent creation failure, permission refusal, failed metadata write, partial acquisition and descriptor initialization.
- Identity: missing/replaced path, rename while held, symlink/reparse/hard-link aliases, case/relative path aliases, reused identifiers, stale PID, parent/path replacement and a restart with an existing sentinel. Do not change stale-lock recovery policy or widen ACLs to make tests pass.
- Release: body `FileExistsError`, ordinary exception, `BaseException` cancellation, cleanup failure on success and failure, close failure/uncertainty, descriptor reuse, successor created at the close/delete boundary, and preservation of the original error when cleanup adds another failure.
- Physical work: cancellation while waiting, immediately after acquisition, during write and during release; repeated cancellation and worker shutdown/drain; prove capacity remains owned until the actual worker/handle completes. A cancelled awaiter is not physical termination.
- Caller semantics: atomic replacement, preservation of last-known-good cache/state, multi-file Ark save outcomes, tracked-view read/modify/write and restoration receipts, guided cache rollback/readback, startup verification and concurrent successor generations. A cleanup error after a committed write must not invite unsafe replay.
- Immutable readback: if parsing moves outside a writer lock, prove the captured generation/bytes still refer to the intended completion; cover concurrent replacement, size limits, truncation and malformed payloads. Do not turn this into the deferred broad cache optimisation.

Turn the relevant cases into behavioral tests. Use disposable paths and native Windows/separate-process fixtures for actual ownership/replacement behavior, plus portable regressions for the supported non-Windows environment. Run all affected caller suites, not only the helper's happy path. Keep production operational logs untouched. Update exact updater contracts for changed protected source; final combined compatibility still belongs to D4.

## Remaining D3: all six maintenance boundaries

| Stage | Authoritative owner/children | Preserve | Separately qualify |
| --- | --- | --- | --- |
| Import Phase A | `UPDATE_ALL2`, `IMPORT_STAGING_PROC_CORE` | Input/digest custody, scan allocation, typed/history writes, atomic import receipt, archive integrity | Sampled statistics and conditional KS4 maintenance |
| Configuration | `sp_TARGETS_MASTER` -> `CREATE_DELTA_TABLES` | Mutex order, atomic configuration/delta publication, shape/identity, completion | Statistics, rebuild/reorganise, optional DeltaProcessingLog |
| Player report | `SP_Stats_for_Upload` | Consistent report, provenance and captured output | FULLSCAN; preserve D2's real statement cap |
| KVK output | `sp_ExcelOutput_ByKVK` and index/view children | Required schema/unique indexes, published view/output, exact receipt | Nonessential upkeep and FULLSCAN |
| Final stats | `usp_S11CompleteStatsReportsCore` | Stage-specific completion/output and required admission headroom | Post-success CHECKPOINT, stats and backup signal/waits |
| Explicit post-import | Python log/maintenance owner and `usp_update_stats` | Truthful committed outcome, saved capture, physical worker ownership | Durable due/claim/completion, bounded backlog, backup processing and intentional sp_updatestats |

Review real child procedures and existing maintenance owners together. A maintenance failure after commit must be pending/failed maintenance, not a failed import or permission to replay it. Qualify crash/restart between commit, enqueue/claim and completion; concurrent claims; lost acknowledgements; cancellation and physical drain; stale ownership; deduplication; failed cleanup; capacity/backlog; and both reader/writer arrival orders. Do not introduce a general scheduler or unowned background work.

Preserve the raw-history SNAPSHOT/index REBUILD failure SQL 3961. Metadata snapshot qualification does not make arbitrary history/DDL overlap safe. Keep RCSI off. Existing floors/limits remain: 8 GiB free memory and disk reserve, sampled log use below 70%, version store below 512 MiB; the one-rehearsal 21-input allowance is consumed. Existing balanced comparisons remain overall median ON <= OFF x1.20 + 1,000 ms and per-stage <= OFF x1.20 + 250 ms when applicable. No timeout, input-cap or backup-schedule increase is implied. Reuse valid evidence and rerun affected qualification for a concrete reason.

## D4/D5 and deployment conditions that must survive this handoff

The recorded installed Bot -> combined D2 target returns `COORDINATED_RELEASE_REQUIRED` with both the recorded old updater and the verified candidate updater. Individual exact D2 transitions do not authorize the combined jump. Registry occupancy is 81 with all 69 predecessor definitions unchanged. D4 must provide a reviewed exact final combined transition or supported coordinated release, reject mixed/missing/foreign dependencies, align final Bot/SQL/startup pins, regenerate tooling, and demonstrate no compatibility blockers. Do not bypass matching or deploy twelve intermediate versions. D2 is merged; immediate deployability is not claimed.

D4 also owns current legacy/manual UPDATE_ALL/Rally/TEST binding evidence and qualification or explicit retirement approval. Do not execute business work merely to discover use. D5 qualifies final combined correctness, actual concurrency, failure/cancellation, restart, cleanup and resource cost. After D5, refresh installed source/tool/SQL and changed-path plus ancestor custody before any separately controlled deployment. Retain committed Phase 1 SQL, receipts, files and provider effects; rollback/recovery may continue only genuinely unfinished stages.

Deferred scope remains deferred: broad datatype conversion, P01.6 decode/rebuild optimisation, wider orchestration extraction, Stats UI/SDK acknowledgement and unrelated MGE/Ark performance. Standalone pre-KVK/weekly physical-close debt retains its separate recorded transaction/outcome contract. Tied zero-score ranking remains an explicit report-policy decision; date-window comparisons use actual report execution time. The fresh coverage review may add tightly related ownership/durability cases, but unrelated findings belong in existing tracking with the required structure.

## New-chat first deliverable and continuation

Produce a concise coverage-delta record: source/callers examined, confirmed coverage, newly added edge cases/tests, missing evidence and any real scope decision. Do not claim that no edge cases can exist; state the bounded review performed. Then implement D3a, run meaningful regressions/native checks, review the exact diff and prepare its focused mirror PR. Record actual outcomes in the D3 delivery review and keep this handover's status current. Only pause for a concrete missing decision/access boundary; the operator has already authorized the review and D3a start.

Documentation-only handover validation uses architecture/deferred/test-selection/security-routing, whitespace and local-link checks. Runtime and native suites are not repeated for prose alone; executable D3 changes require their own tests and Changes review. The handover does not itself promote or deploy anything.
