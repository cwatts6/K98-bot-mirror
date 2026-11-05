> **Archived 5 November 2026.** Completed or superseded delivery record; dated holds and pending statements below are historical. Current outcome: [P01.4 closeout](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Closeout%20-%202026-11-05.md); remaining checks: [natural acceptance](../Startup%20Import%20Export%20Reliability%20-%20P01.4%20Natural%20Acceptance%20-%202026-11-05.md); next work: [P01.5 handover](../Startup%20Import%20Export%20Reliability%20-%20P01.5%20Handover%20and%20Scope%20-%202026-11-05.md).

# P01.4 local implementation and qualification

> **Current E91, 5 November 2026:** The [complete local qualification receipt](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Complete%20Local%20Qualification%20-%202026-11-05.md) records the full original P01.4 design implemented and qualified locally, with both optional workers enabled in the unpublished candidate. Cost, physical-drain, diagnostic-priority, updater, regression and Changes-review gates passed. No CSV scope was deferred. Publication/deployment and natural-activity acceptance remain outstanding; earlier E88-E90 disabled/pending statements below are historical. Existing changes and archive moves are preserved.

> **E90, 5 November 2026:** The [whole-solution design](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Whole%20Solution%20Design%20-%202026-11-05.md) supersedes the recommendation to adopt SQL now and defer file logging. Preserve the full P01.4 scope: settle shared lifecycle and diagnostic isolation, then qualify both workers together. New controls identify a confound in the earlier file lag benchmark, not a qualification pass. Both workers remain disabled. Default recommendation is one complete deployment after validation; an earlier outcome/custody-only candidate remains an optional delivery choice. This review changes documentation only; implementation of the revised design and all publication/deployment remain pending.

> **E89, 5 November 2026:** The [adoption decision packet](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Adoption%20Decision%20-%202026-11-05.md) records completed SQL-worker qualification, startup/close-failure corrections and the concrete file-logging choices. Both worker gates remain off pending the decision. The failed file gate and updater release blocker remain visible; P01.4 is not complete under its original scope. No publication or deployment occurred.

**E88, 5 November 2026: local implementation prepared; optional-worker adoption and release remain held.** The operator approved the three slices in the [source review and design](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Source%20Review%20and%20Design%20-%202026-11-05.md), with cost/physical-drain gates, preservation of existing changes, and a stop before publication or deployment. Disposable SQL qualification on `localhost\K98DEV` was separately authorized. Earlier implementation-approval holds are historical. This is not P01.4 acceptance or release readiness.

## Source and preservation

Implementation is uncommitted in the existing mirror checkout `.codex_artifacts/p1-mge-mirror-review`, based on `2f2883a98dfc30dff0373dd38800bb4795f1b652`. The older root checkout's intentional documentation changes remain intact. The private checkout at `65ad4fa6d765a88b45cfbb6bba8b6b32af802f6e` and SQL repository at `7e91989f619deb46836194c7e705b0a9eb2ebe11` were not changed. No commit, push, PR, merge, production request, deployment, restart or recovery action was performed.

The prior [documentation carry-forward](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Delivered%20Documentation%20Carry-forward%20-%202026-11-05.md) was reconciled into the mirror: 25 destination documents and five exact archive moves, with pre-copy files retained privately. Carry this report and the latest status overlays forward too. Do not replace the root checkout's documents from the mirror without reconciling subsequent user work.

## Slice disposition

| Slice | Implemented locally | Disposition |
| --- | --- | --- |
| A: truthful upload outcomes | Honor, PreKVK, Location including manual service, Weekly and KVK distinguish committed ingestion, unconfirmed execution, optional audit/refresh/scheduling and delivery. Missing diagnostic counts remain unavailable. KVK negative-count/capture-finalization failure preserves acknowledged ingestion but removes export preparation authority. Location reads named result columns and preserves commit acknowledgement across cleanup failure. | Focused regression coverage passed; release not prepared. |
| B: fallback admission and file logging | One message admission retains its selected attachments; duplicate CSV append under the processing lock removed; private staged readers remain owned through cancellation; queue acknowledgement retained. Bounded file-writer prototype is present. | **File worker adoption stopped on cost failure. `QUALIFIED=False`.** Existing single awaited download log remains outside the processing critical section. F30 is not fully resolved. |
| C: optional SQL audit | Five domain adapters, local correlation distinct from SQL identity, bounded primitive queue, exact acknowledgement binding, no retry/rebinding, local loss projection, report/archive coverage and lifecycle ownership. Dedicated optional connection uses two-second login/statement settings. | Native SQL and one matched route workload passed. **`QUALIFIED=False`** pending remaining qualification and readiness. Legacy audit path remains active. |

Both optional writers are source gated, not configuration enabled. The prototypes admit at most one file and one SQL writer; queue limits are 64 x 2 KiB and 128 x 8 KiB, with 256 SQL contexts. Closing discards unentered work and joins entered work; a timeout is never reported as physical drain. Required Ready, fsync, hash, manifest and export ownership contracts remain required.

Late review corrections keep the Weekly source-count parser owned through cancellation and apply PreKVK commit evidence before both generic and `IntegrityError` classification. The ContextVar annotation was corrected. Four commit/close error regressions and a physical parser-cancellation regression cover those changes.

## Disposable local SQL evidence

Only newly created, uniquely named `K98_P014_Qualification_*` databases were used on `localhost\K98DEV`. The six audit table/procedure definitions were taken from the SQL source repository, with hashes retained. Every created database was removed in cleanup. Existing development databases and production were not modified.

Private receipts are under `C:/discord_file_downloader/.codex_artifacts/p014-scope-20261105/`:

- `native-qualification.json`: failed qualification fixture used an old fixed timestamp and overflowed a duration conversion. This adverse run is retained; it is not classified as a runtime defect.
- `native-qualification-20261105T110131.json`: corrected 30-sample matched comparison, including the **file worker cost failure**.
- `native-qualification-20261105T110718.json`: SQL-only native and matched Honor-route comparison with the real diagnostic sink.

| Measurement | Observed result | Interpretation |
| --- | --- | --- |
| File added event-loop lag p95 | 15.2062 ms; baseline 0 ms | Fails the unchanged 5 ms allowance; adoption stopped. |
| File offer p95 / p99 | 0.0027 / 0.0035 ms | Offer alone passes; does not override loop-lag failure. |
| File real writes | 32 settled | Physical write evidence, not general filesystem-stall qualification. |
| SQL statement timeout | 2.0053 s, HYT00 | Driver statement budget observed. |
| SQL login refusal | 2.1038 s, 08001 | Local refused endpoint; not every network-failure mode. |
| SQL close under real table contention | 2.0040 s; entered 1, settled 1, discarded 128 | Entered operation physically settled before close returned. |
| Lost start acknowledgement | Dependent completion suppressed; existing SQL row stays started | No invented ID, re-query or retry. |
| SQL offer p95 / p99 | 0.0173 / 0.0572 ms | Passes producer budget under measured load. |
| Matched real Honor route, 30 alternating samples | Baseline median/p95 7.7739/9.8713 ms; candidate 0.4299/0.5949 ms | Real disposable SQL audit; importer and Discord were offline fixtures. Not full uploaded-workbook performance. |
| SQL cold setup plus close p95 | 0.3309 ms | Local setup sample only. |
| After SQL close | 0 active requests; 3 idle session rows | Driver pooling/fixtures retain sessions; do not claim zero physical SQL sessions. |

Diagnostic pressure was bounded and lossy: 269 drops, including 139 critical drops, were visible; no invalid events or sink failures were reported. Actual report ZIP membership, sizes and hashes were tested separately. No claim of lossless audit is made.

Remaining SQL adoption gates include representative workloads beyond Honor, peak-memory evidence, native close-failure qualification, and startup-failure behavior. In particular, optional worker startup must be isolated before adoption; an unavailable adopted worker must not silently restore synchronous SQL. No source gate may be turned on merely because the measured subset passed.

## Validation and review

- Focused matrix: **457 passed, 1 skipped**. A repeat with the mirror interpreter also passed log-hygiene validation: production operational logs unchanged. An intervening root-interpreter run failed the existing interpreter guard; that receipt is retained.
- Review corrections: **54 passed**, including the new commit/close and parser cancellation cases.
- Broad suite: **11,293 passed, 1,114 skipped, 27 failed, 156 setup errors**, plus eight passing subtests. All reported failures/errors are updater source-hash assertions for changed runtime members. This is a release blocker, not a green full-suite claim. The suite began before the last implementation edits; focused checks cover the final corrections.
- Architecture, deferred-item and security-routing validators, test selection, scoped Ruff, configured Pyright, smoke imports and command registration passed. A separate expanded Pyright invocation encountered a pre-existing Weekly `create_task` annotation mismatch; the unchanged baseline declaration was verified. The repository-configured type gate passes.
- Historical updater pins and source-bridge assertions were preserved. A future release requires an additive reviewed successor and actual predecessor evidence; do not rewrite past pins or weaken tests to make this candidate appear releasable.
- Codex Security Changes review, Deep off, completed for the frozen initial patch: `3eb9b5c7-3b90-4474-af75-2c1e038b5827`, 31 runtime files, no reportable findings. Final patch scan `f9466afc-6f7f-4248-97b0-675ce5a4528a` retained that review and threat model, explicitly reviewed the three final runtime corrections, and completed with no reportable findings. The only later change is this documentation receipt, with a documented security skip because it changes no executable behavior. This is scoped static review, not proof of deployment ACLs or runtime security.

The full suite's failed exit prevents its wrapper from reaching the log-hygiene assertion; only the successful focused wrapper supplies that hygiene result. Raw outputs, failed runs, source preservation and final file hashes are retained privately. The security tool reported 11,558,839 accumulated tokens, including 11,249,024 cached input tokens, for the initial scan; final review reported 556,722 tokens, including 551,808 cached input tokens. These are rollout accounting, not price estimates. Final document validation checked 545 relative links with none missing; root/private/SQL heads and statuses, root design-document hashes and selected private-source hashes remained unchanged.

## Remaining ownership

P01.4 stays open. A and the fallback admission correction can be separated for review; optional file adoption is stopped on its recorded failed gate, and SQL adoption is still held. Publication/deployment remain outside this authorization. P01.3 stays closed; P02/P03/P04/P05 and incident-specific recovery boundaries are unchanged. Do not replay committed uploads to validate these changes.

### Deferred Optimisation
- Area: services/download_log_service.py
- Type: performance
- Description: The optional file worker exceeded the approved event-loop lag allowance despite cheap queue offers.
- Suggested Fix: If this slice is reopened, investigate the retained matched workload and propose a bounded alternative before repeating qualification; preserve the failed receipt and unchanged gate.
- Impact: medium
- Risk: medium
- Dependencies: Explicit decision to resume the failed optional file-worker slice.

### Deferred Optimisation
- Area: bot_helpers.py fallback queue presentation
- Type: consistency
- Description: When processing a selected multi-attachment message stops early, remaining attachments are logged as unattempted but existing UI rows may still display queued; the business queue remains the pre-existing unbounded queue.
- Suggested Fix: Design exact attachment-level UI terminal identity and admission policy separately, without durable redelivery or business replay.
- Impact: medium
- Risk: medium
- Dependencies: Separate scope for queue presentation/admission; preserve this slice's one-message admission and staged custody.
