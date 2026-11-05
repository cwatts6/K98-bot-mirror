> **Archived 5 November 2026.** Completed or superseded delivery record; dated holds and pending statements below are historical. Current outcome: [P01.4 closeout](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Closeout%20-%202026-11-05.md); remaining checks: [natural acceptance](../Startup%20Import%20Export%20Reliability%20-%20P01.4%20Natural%20Acceptance%20-%202026-11-05.md); next work: [P01.5 handover](../Startup%20Import%20Export%20Reliability%20-%20P01.5%20Handover%20and%20Scope%20-%202026-11-05.md).

# P01.4 adoption decision

> **Current E91, 5 November 2026:** The [complete local qualification receipt](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Complete%20Local%20Qualification%20-%202026-11-05.md) records the full original P01.4 design implemented and qualified locally, with both optional workers enabled in the unpublished candidate. Cost, physical-drain, diagnostic-priority, updater, regression and Changes-review gates passed. No CSV scope was deferred. Publication/deployment and natural-activity acceptance remain outstanding; earlier E88-E90 disabled/pending statements below are historical. Existing changes and archive moves are preserved.

> **E90, 5 November 2026:** The [whole-solution design](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Whole%20Solution%20Design%20-%202026-11-05.md) supersedes the recommendation to adopt SQL now and defer file logging. Preserve the full P01.4 scope: settle shared lifecycle and diagnostic isolation, then qualify both workers together. New controls identify a confound in the earlier file lag benchmark, not a qualification pass. Both workers remain disabled. Default recommendation is one complete deployment after validation; an earlier outcome/custody-only candidate remains an optional delivery choice. This review changes documentation only; implementation of the revised design and all publication/deployment remain pending.

**E89, 5 November 2026: ready for an adoption/scope decision, not publication or deployment.** This follows the operator's approval to finish qualification and make the next decision concrete. The [E88 implementation receipt](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Local%20Implementation%20and%20Qualification%20-%202026-11-05.md) and [approved design](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Source%20Review%20and%20Design%20-%202026-11-05.md) remain the historical evidence and acceptance contract. Both optional worker gates remain `QUALIFIED=False`.

## Recommended decision

**Approve the SQL audit worker for the next local release candidate; keep the failed file worker disabled and explicitly defer non-blocking CSV logging.** Carry A's outcome corrections, B's admission/custody corrections, and C's locally qualified SQL audit into release preparation. Omit the failed file-worker prototype from the eventual release patch while retaining its code/evidence privately. Preserve the single existing awaited CSV append outside the processing lock.

This is a scope decision: **the original P01.4 scope is not complete while CSV logging can still delay the downloader.** Do not close P01.4 as fully delivered. Either retain that F30 remainder as an explicit open item, or amend acceptance explicitly. A and C do not prove non-blocking CSV logging.

| Choice | Result | Cost / limitation |
| --- | --- | --- |
| Recommended: adopt SQL, defer file worker | Removes awaited audit SQL from the six selected entry paths while retaining tested outcome/custody corrections. | CSV logging can still delay download completion; original scope remains partial unless acceptance is amended. Optional SQL audit is bounded and can lose observations. |
| Keep the original full scope | Keep P01.4 open and design a different bounded file-log transport before release. | Additional design and qualification; the existing 5 ms loop-lag limit stays unchanged. No replacement has yet passed. |
| Release only outcome/admission corrections | Leave both optional workers disabled and retain their evidence. | Lowest transport change, but both awaited diagnostic paths remain; F30 is substantially outstanding. |

The existing general logging queue is `queue.SimpleQueue` in `logging_setup.py`; moving CSV writes there is not a qualified bounded alternative. The CSV path is an optional download record used by the downloader, not a required Ready/manifest/hash receipt. No diagnostic record has been silently removed in this task. The prior failed file benchmark was not retuned or repeated to manufacture a pass.

## What the follow-up changed

- Optional SQL-worker construction/thread-start failure is caught and logged by error type only. Startup continues, the process makes no automatic replacement attempt, and adopted-but-unavailable audit cannot fall back to awaited SQL.
- A failed connection close retains the connection in its owning writer, refuses further admission, discards queued optional work, and causes shutdown to refuse a physical-drain certificate. It does not retry SQL or close, replace the writer, or reinterpret a business commit.
- Failed physical thread startup can be closed safely without joining an unstarted thread.
- Added regression coverage for construction failure, thread-start failure, gate-off startup, retained close failure and no retry/fallback.

Changes are limited to `services/optional_import_audit_worker.py`, `services/optional_upload_transport.py`, `stats/dal/import_audit_dal.py`, their tests and this decision/status documentation. All earlier implementation remains preserved. There are no SQL repository changes or migrations.

## Qualification completed

All six entry paths ran 30 alternating baseline/candidate pairs after warmup, with their actual routes/services and SQL audit adapters. SQL used only new disposable databases on `localhost\K98DEV`; business import and Discord boundaries were offline fixtures. Location used its real CSV parser. These measurements qualify the audit boundary, not production workbook throughput or live provider behaviour.

| Entry path | Baseline p95, ms | Optional SQL p95, ms | Audit SQL calls, baseline/candidate |
| --- | ---: | ---: | ---: |
| Honor | 10.610 | 0.535 | 5 / 5 |
| PreKVK | 18.958 | 0.694 | 5 / 5 |
| Weekly Activity | 20.655 | 0.673 | 5 / 5 |
| KVK All | 29.829 | 0.900 | 9 / 9 |
| Automatic Location | 22.919 | 1.536 | 5 / 5 |
| Manual Location | 17.653 | 1.461 | 5 / 5 |

Every path passed the unchanged median/p95 elapsed and p95 loop-lag gates, retained the same checked business summary, and produced a completed audit row with a known written count. Candidate loop-lag samples stayed below the 5 ms added allowance. The small fixture durations are not a promise that actual imports take these times.

**Real contention:** with the audit table locked and its 128-entry queue full, all six business fixtures completed in 18.165 ms while the entered audit SQL request remained blocked. An independent SQL connection also progressed. There were 34 visible rejected offers; closing discarded the queued 128 and joined the entered native timeout in 1.982 seconds. No active request remained afterward.

**Disconnect and close:** killing only the fixture-owned session in its disposable database produced a native driver error and confirmed close in 0.00098 seconds. A separate injected close refusal around a real open SQL connection retained that session, refused new work and refused drainage. This injection is not claimed as a naturally occurring SQLDisconnect failure. Earlier real two-second login/statement and table-contention results remain applicable; no universal upper bound on all OS/driver stalls is claimed. Unconfirmed close intentionally blocks normal release/shutdown certification.

**Memory:** four pressure cycles reached exactly 128 queued envelopes, 916,776 encoded bytes and 256 contexts, staying within the approved caps. Peak traced allocation was 2,923,088 bytes; the largest process RSS increase was 4,022,272 bytes in the first cycle. All contexts and queued payloads were released on close. Post-close RSS increased by 176,128 bytes across the later cycles, so allocator retention is reported rather than claimed to be zero. These measurements include the active diagnostic sink; absolute process RSS includes imported libraries.

**Loss tradeoff:** the deliberate pressure workload reported 8,450 diagnostic drops, including 8,192 critical drops, with zero invalid events and zero sink failures. The shared existing diagnostic queue reached 1,024. Audit pressure can reduce retained diagnostic coverage, including coverage shared with other operations; it does not guarantee every failure observation survives. Loss is visible, queues remain bounded, and business progress is preserved. This is an adoption tradeoff, not a lossless-audit claim.

Every disposable database created in the follow-up was removed, including the first failed fixture run. That run tried to inspect a deliberately retained connection while it still had pending results and received HY000; inspection was corrected to use the independent master connection. The failed receipt is retained.

## Validation and remaining release work

- Final focused matrix: **467 passed, 1 skipped**; log-hygiene check confirms operational logs unchanged.
- Configured Pyright: zero errors/warnings. Scoped Ruff, architecture, deferred-item and security-routing validation passed. Smoke imports and command registration passed. Existing SQL object hashes match the earlier authoritative-source receipt. Preservation checks confirmed unchanged root/private/SQL heads and statuses, unchanged prior root document/private source hashes, and no unexpected runtime delta beyond the three named files. All 556 relative document links resolve.
- The prior full suite's 27 failures and 156 setup errors remain exact updater source-pin assertions. They were not hidden, weakened or relabelled as unrelated. This follow-up changes gated optional transport and its failure handling; focused tests cover all selected and compatibility callers. Full pytest will be required again after the adoption decision and final updater candidate, rather than repeating the known pin failures now.
- Final security routing is **Changes, Deep off**, against the complete uncommitted Bot patch based on `2f2883a98dfc30dff0373dd38800bb4795f1b652`. Scan `05260474-b6da-401c-b184-de89443a866a` completed with no reportable findings across all 31 runtime inventory files: 28 retain hash-verified prior review, and the three follow-up files received a dedicated source review with supporting lifecycle callers. Earlier completed scans are preserved. SQL source is unchanged, so no separate SQL diff scan is warranted. This final receipt-only edit has a documented security skip because it changes no executable behaviour. The tool reported 1,668,428 rollout-accounted tokens, including 1,659,776 cached input tokens; this is not a price estimate.

After the decision, prepare the selected candidate, separate reviewable slices, add the reviewed updater successor without rewriting historical pins, run the final full checks, and request publication authorization only when the exact result is reviewable. Actual predecessor/deployment evidence and natural-activity acceptance remain release-stage work. No publication, private promotion, restart, provider request or production mutation is authorized by this packet.

Private evidence: `C:/discord_file_downloader/.codex_artifacts/p014-decision-20261105/`, including `qualification-20261105T115716Z.json` (failed fixture), `qualification-20261105T115753Z.json` (six workloads, memory and disconnect/close), the separate pressure receipt, test output and the pre-edit source copies. The E88 adverse file result remains in the prior evidence directory.
