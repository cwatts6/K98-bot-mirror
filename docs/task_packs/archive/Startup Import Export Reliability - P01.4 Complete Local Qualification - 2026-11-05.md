> **Archived 5 November 2026.** Completed or superseded delivery record; dated holds and pending statements below are historical. Current outcome: [P01.4 closeout](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Closeout%20-%202026-11-05.md); remaining checks: [natural acceptance](../Startup%20Import%20Export%20Reliability%20-%20P01.4%20Natural%20Acceptance%20-%202026-11-05.md); next work: [P01.5 handover](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Handover%20and%20Scope%20-%202026-11-05.md).

# P01.4 complete local implementation and qualification

**E91, 5 November 2026: complete original design implemented and qualified locally; ready for a publication decision. Publication and deployment remain held.**

The operator explicitly approved the full [whole-solution design](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Whole%20Solution%20Design%20-%202026-11-05.md), disposable local databases, preservation of existing changes, and a stop before publication/deployment. This receipt supersedes E88/E89 adoption holds and E90 implementation-pending status; their adverse evidence and historical decisions remain intact.

## Scope and implementation

| Original requirement | Local implementation and evidence |
| --- | --- |
| A: truthful outcomes | Five upload routes plus manual Location preserve acknowledged commit independently of optional audit/refresh/send failure. Unknown counts remain unknown. Exact KVK preparation identity still gates export; diagnostics cannot authorize it. Existing cancellation/parser/commit-uncertainty fixes are retained. |
| B: selected fallback admission and file logging | One selected-message admission, staged-input ownership and one queue acknowledgement remain. Duplicate CSV append under the processing lock is removed. A bounded dedicated file writer removes optional CSV I/O from downloader completion. Actual downloader/staging composition and independent file-cost checks passed. |
| C: optional SQL audit | Six entry paths use bounded primitive envelopes and generated local correlation, then bind only exact SQL acknowledgement. Separate trusted connection, no retry/rebinding/replay, and retained uncertain-close custody remain. Native disposable-SQL and all six route compositions passed. |
| Shared lifecycle | Both admissions close before either join; physical waits run independently and remain owned through repeated cancellation. File startup failure is isolated once, with no replacement or synchronous fallback. Normal graceful teardown and the terminal bot.run exit both drain workers. A blocked/uncertain close cannot be labelled drained or release process ownership early. |
| Diagnostic isolation | Separate 64-slot coalescing observation mailbox, including one reserved file slot, and two fixed worker summaries. First failure, latest state, loss lower bounds and partial coverage survive bounded projection. Optional traffic cannot use the main queue or displace business history; preview, restore, file trimming and ZIP selection preserve priority. |
| Exact updater | New p014_upload_outcomes_optional_io_v1 pins 40 required source/dependency files, including DL_bot.py finalizer. All 63 historical transitions retain their exact digest. Old installed readers reject the new family; modified/missing predecessors, postimages or dependencies are rejected. |

Both source QUALIFIED gates are now True in the unpublished candidate. They were enabled after valid cost, resource and physical-drain qualification. There is no production configuration change. The original scope was retained; CSV was not deferred and acceptance budgets were not relaxed.

## Qualification method and results

Private evidence root: C:/discord_file_downloader/.codex_artifacts/p014-complete-20261105/. Application checkout: C:/discord_file_downloader/.codex_artifacts/p1-mge-mirror-review, based on 2f2883a98dfc30dff0373dd38800bb4795f1b652. SQL source remains C:/K98-bot-SQL-Server at 7e91989f619deb46836194c7e705b0a9eb2ebe11; the six authoritative ImportAudit definitions were applied only to uniquely named disposable databases on localhost\K98DEV. No SQL source/schema/migration change is needed.

The final native receipt is complete-20261105T135338Z.json. All four configurations were measured (neither, file, SQL, both), with 32 rotating repetitions per configuration/path and the first two excluded as warmup. Every reported arm has 30 measured runs. Required offline business/Discord results and audit SQL-call counts match; the harness exercises actual downloader/staging and upload service composition with offline HTTP/business boundaries. SQL audit statements and file writes are real. These are local controlled workloads, not production throughput measurements or provider acceptance.

Budgets remain offer p95 <=1 ms / p99 <=5 ms, <=2% added median / <=5% added p95 business elapsed, <=5 ms added p95 responsiveness, and <=5 seconds measured native failure settlement. Identical minimum 80 ms observation windows cover physical settlement beyond business return. Responsiveness includes source wake lateness and event-loop delivery separately; both combined lateness and delivery are retained. Deliberate 50 ms loop/CPU stalls are detected by the calibrated observer.

| Upload path | Neither median / p95 (ms) | Both median / p95 (ms) | File / SQL / both gates |
| --- | --- | --- | --- |
| honor | 17.72 / 24.99 | 4.50 / 5.98 | Pass / pass / pass |
| prekvk | 19.75 / 22.14 | 5.04 / 6.14 | Pass / pass / pass |
| weekly_activity | 19.74 / 24.27 | 4.94 / 6.57 | Pass / pass / pass |
| kvk_all | 28.49 / 48.35 | 4.65 / 6.75 | Pass / pass / pass |
| player_location | 21.20 / 23.50 | 6.05 / 6.73 | Pass / pass / pass |
| manual_location | 19.36 / 22.25 | 5.20 / 6.34 | Pass / pass / pass |

All file-only, SQL-only and combined gates passed for every path. Independent downloader/file qualification (file-resources-20261105T134704.json) also passed: median 3.826 -> 2.802 ms, p95 5.983 -> 3.854 ms. This separate check prevents SQL savings from concealing a file regression.

Native sharing refusal settled in 0.000114 seconds; killing only the fixture-owned SQL session settled in 0.001270 seconds. Under simultaneous blocked SQL/file pressure, all six staged business paths completed in 20.62 ms while entered optional I/O remained blocked, independent SQL progressed, and final physical settlement took 1.965 seconds after close requests/release. Active fixture SQL requests at completion: zero. An injected close-refusal wrapper around a real connection proves retained custody/refused drain/no automatic retry; it is not claimed as a natural SQLDisconnect failure. Every database created by the three completed native runs was dropped.

Resource pressure reached SQL 128 x 8 KiB, file 64 x 2 KiB and 256 SQL contexts. Four sustained cycles released contexts, queues and discard custody. Non-instrumented offer p95 was at most 0.0238 ms and p99 at most 0.0501 ms across both writers. Mailbox slots remained 64; encoded bound remains 256 KiB. A near-capacity projection preserved all 448 business records under optional storms, with zero general drops, zero critical drops and zero sink failures. Optional coalescing/refusal/retention omissions correctly marked diagnostic coverage partial. RSS/trace samples are retained, including a transient 18.30 MiB traced peak during bounded document publication; this is not a zero-allocation claim. Cold two-worker start/close p95 was 0.781 ms over 30 runs.

## Retained adverse evidence and corrections

E88 file lag/cost failure remains recorded. The first new run (complete-20261105T133943Z.json) passed the combined candidate but file-only Honor p95 missed the 5% gate. The next run (complete-20261105T134914Z.json) exposed source-timer variance and failed some responsiveness comparisons. Neither is relabelled passed.

Independent no-work controls (timer-source-controls.json, 100 samples each) showed the 5 ms Event.wait timer overshot by 12.81 ms p95, versus 0.751 ms for time.sleep. The final observer uses the Python3.11 Windows high-resolution sleep source, identically for every arm, with unchanged frequency/windows/budgets and positive stall calibration. No system timer resolution was changed. Previous harness source is retained as qualify_complete_event_timer.py. Python's [time.sleep documentation](https://docs.python.org/3.11/library/time.html#time.sleep) describes the Windows timer; actual host measurements support the correction. Scheduler delays remain possible; one local pass is not a universal latency guarantee.

The first resource run (file-resources-20261105T134600.json) also retained a harness setup failure: controlled diagnostic preloading attempted publication before its private directory existed. The corrected fixture creates its directory first; file-resources-20261105T134704.json has zero sink failures. The original script/log remain. Initial sandbox SSPI failure occurred before database creation; native runs used authorized local Windows authentication.

Qualification receipt hashes predate only the source gate/comment activation and terminal-exit correction. Core normal-path worker/diagnostic algorithms are unchanged; final updater hashes authenticate the complete candidate. The exit correction has separate tests executing the actual main finalizer for normal return, exception, SystemExit, blocked writer and close refusal. No retrospective claim is made that the earlier native run executed that finalizer.

## Final validation and security

Final full suite: **11632 passed, 1114 skipped, 1 warning, 8 subtests passed in 1203.50s (0:20:03)**; operational-log hygiene passed with no writes to operational log files. The final run (full-tests-confirmed.txt) uses the mirror checkout's own .venv interpreter and the fixed candidate. Earlier root-interpreter/mixed-state run was stopped and retained as full-tests.txt; its interpreter-guard and legacy-audit fixture failures are not hidden. The first completed full run (full-tests-final.txt) had 11,620 passed, 1,114 skipped and 12 updater-fixture failures. Those 12 failures were corrected without runtime changes: generic packet fixtures now use an ordinary application module because DL_bot.py is protected, registry count expects 64, and the historical bridge removes only the family it is testing. The affected 377 updater tests plus log hygiene passed before the clean full rerun. Legacy audit-helper tests explicitly opt into a compatibility fixture; enabled-worker and six-path native tests retain their own coverage. No blanket worker disable or test skip was introduced.

Additional evidence: 228 updater/lifecycle tests passed before the terminal-exit correction, 177 final focused tests plus log hygiene passed after it, and 53 compatibility/interpreter cases passed. All changed Python files pass Ruff lint/format. Configured Pyright reports 0 errors / 29 existing import/environment warnings. Architecture, deferred-item format, security routing, test selection, smoke imports and command registration passed. Smoke uses disabled dotenv and inert test settings; initial default smoke failures are retained.

Security used k98-security-review-routing and Codex Security Changes review, Deep off. Parent and dedicated reviewers reviewed all 38 changed source inventory files, with **zero security findings and no deferred review surfaces**. The terminal-exit correctness concern was fixed and independently re-reviewed. Initial scan 3a5292aa-30a6-4f02-bc99-082f5abddc57 retains its snapshot-change warning because the correction occurred during review; its supplementary manifest pins the final42 runtime/updater/dependency files. The final unchanged-snapshot review carries forward only hash-verified source evidence. Its sealed identity, report path, snapshot digest, warnings and tool-reported token accounting are retained in the private security-completion.json closeout receipt. Cached context is included in that accounting; it is not a separate billing estimate. The canonical supplied threat model is unchanged; its historical disabled-worker assumption is explicitly superseded by enabled-path review. No SQL diff exists. This review does not establish live ACLs/grants or production acceptance.

Final preservation, source hashes, SQL-definition hashes, links and validation commands are recorded in final-validation.json and document-preservation.json. Root/private/SQL HEAD/status and root document/private source hashes remain unchanged. Existing pending runtime changes outside the reviewed lifecycle/reporting/updater work remain byte-identical. All prior archive moves and receipts are retained.

## Delivery decision and boundaries

Recommended delivery remains one complete P01.4 candidate. Shared lifecycle and reporting are implemented once for both workers; no second competing solution is required. Splitting publication into reviewable PRs remains possible, but deploying a partial family would require a separately qualified exact candidate and updater transition.

Publication, PR/merge, private promotion, deployment/restart and natural-activity acceptance remain outstanding and are not authorized by this local task. The next decision can be whether to publish this complete candidate after final validation. P01.4 programme closure requires its later release/acceptance evidence; local qualification alone does not claim it is delivered.

Optional SQL/CSV evidence is deliberately best effort: overload/crash/disk failure may omit it, and reports expose partial/unknown coverage. There is no durable retry spool, guaranteed audit delivery or forced termination guarantee for an arbitrary OS/driver hang. Such a hang retains ownership and refuses successful drain. Required Ready/fsync/hash/manifest/export/business custody is unchanged. P01.5/P01.6, P02-P05, F09 contention and exact incident recovery are outside this implementation.

All existing changes and archive moves must travel with the [documentation carry-forward manifest](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Delivered%20Documentation%20Carry-forward%20-%202026-11-05.md). Private harnesses, logs, fixture data and before-copies must not be published. No commit, push, PR, merge, deployment, production mutation or provider request occurred.
