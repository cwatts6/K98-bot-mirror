> **Archived at E100, 5 November 2026.** Delivered or superseded P01.5 record. Preserve the dated evidence below; earlier next-action/approval statements are historical. Current authority: [P01.5 closeout](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Closeout%20-%202026-11-05.md) and [P01.6 handover](Startup%20Import%20Export%20Reliability%20-%20P01.6%20Handover%20and%20Scope%20-%202026-11-05.md).

# P01.5 local implementation and qualification

**E97, 5 November 2026. Local candidate only.** The operator accepted the additional design thinking and authorized local implementation and qualification. The [design](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Whole%20Solution%20Design%20-%202026-11-05.md) was amended before implementation. This record supersedes E96's pending-approval status without changing its historical evidence.

Bot baseline: `8806f7e96bfb32624e10029668c992a5c04651e1`. SQL source baseline: `b1eeb8e894fec380c7a6d6c5cc5bbfd9dbc3470c`, unchanged. No commit, push, PR, merge, promotion, bot deployment or restart was performed. The guarded disposable SQL fixture was created and removed locally; no retained or production database was changed. No provider writes or Discord delivery were performed.

## Scope, outcome and reuse

| Finding / objective | Implemented behavior | Local evidence |
| --- | --- | --- |
| F23: optional EventSyncLog blocks work or erases a committed result | One independently admitted audit task, separate configured SQL-login sessions, acknowledged start ID only, fixed terminal projection, no retry/rebind/backlog. Business never awaits audit. Unknown audit cleanup retains only the optional slot. | Blocked/failed start, lost acknowledgement, failed finish, denied writes, native lock/query timeout, bounded offer storm and independent business completion. |
| F24: caller timeout/cancellation releases ownership before physical work | Shared per-event-loop owner across service instances and all public mutators. Direct requests get truthful refusal; at most one scheduled waiter revalidates admission. Deadlines observe the original work. Repeated cancellation joins entered work and suppresses later stages. | All 16 ordered mutator pairs, blocked sync/generate/publish, pre-executor cancellation, repeated cancellation and shutdown/deferred-intent cases. |
| F25: auxiliary index failure hides successful primary publication | Primary replacement freezes its success/count before index construction/replacement. Index failure becomes a warning. Unknown primary replacement is not reported as zero successful writes. | Real temporary-file/replacement failures, preserved old bytes, exact Unicode serialization, empty-cache protection and temporary-file cleanup. |
| Truthful effects, cleanup and delivery | Explicit commit/rollback/close facts; lost commit reply stays unknown; acknowledged commit survives later close failure. Unconfirmed cleanup retains its exact connection and refuses later work. Delivery has its own observation. Busy replies carry a separate blocking-run reference and cannot overwrite another run's delivery. | Native commit/rollback/close cases, unknown-count command rendering and negative delivery attribution checks. |
| Reuse delivered P01 foundations | Existing owned-work helpers, timing/evidence fields, bounded diagnostics, recovery ZIP/report machinery, atomic JSON helper and protected updater are reused. No new permanent worker or runtime retry framework. | Actual report ZIP/digests; combined calendar + both P01.4 upload transports + blocked-read cost qualification; historical updater regression. |

Calendar rules, identities, command permissions/options, schedules, cache formats and empty-cache policy remain compatible. The auxiliary index remains available; the operator reports no known consumers outside the bot. It is not an atomic pair with the primary cache. Ownership is in-process and loop-local, not a distributed lock or cross-restart continuation journal.

## Local qualification

Private receipts remain under `.codex_artifacts/p015-qualification-20261105/`; do not publish raw local fixtures or production evidence.

| Gate | Result / receipt |
| --- | --- |
| Focused related suites | 214 passed in 16.36 s before final review correction; later focused command/outcome/owner and report suites passed. |
| Final busy-delivery correction | 112 passed in 9.25 s: physical owner, command delivery and exact updater successor. `attribution-final-tests.txt`. |
| Full repository regression | Completed: 11,755 passed, 1,114 skipped, 3 failed, 8 subtests passed in 1,176.15 s. All three failures were stale test fixtures/expectations corrected below; their complete affected suites then passed 205 tests. No second full-suite pass is claimed. Earlier interrupted runs are not acceptance. |
| Native disposable SQL | Eight native cases passed; repeated audit start/finish measured over 30 pairs. Zero remaining sessions, fixture dropped. `K98_P015_Disposable_20261105_01a1acb4-878d62ed/native-receipt.json`. |
| Native boundaries covered | Identity-preserving generation, acknowledged commit, simulated lost reply after actual commit, simulated close failure after actual commit, rollback, exact audit ID, denied audit, actual lock and statement timeout. |
| Combined-load cost | Every declared gate passed in `cost-4777826a/cost-receipt.json`, with both real P01.4 transport implementations, inert SQL boundary fixtures, actual JSON replacement and a blocked read. |
| Architecture / deferred / routing / selection | Validators and test selection passed. Full suite, smoke imports and command registration were selected and executed. |
| Import smoke / registration | Imports passed using isolated test-mode configuration with dotenv loading disabled and synthetic OUR_KINGDOM. Registration passed with no unexpected command drift or duplicate risks. This does not validate installed configuration. |
| Formatting / lint / types | Black and Ruff passed for 41 changed Python files; qualification/updater scripts passed Pyright with the explicit repository interpreter. Final correction and fixture updates also passed focused Black/Ruff checks. |
| Updater | Fixed 26-member P01.5 successor; all actual baseline/postimage hashes checked. All 64 historical records retained. Missing, altered and old-reader cases refuse admission. No protected installer was run against an unpublished candidate commit. |

Native qualification used Windows authentication solely to the exact newly created local fixture. This proves SQL statement/transaction/cleanup behavior, not the deployed configured-login permissions. Source and unit checks establish that runtime audit selects the existing SQL-login factory without principal fallback. Login/statement/lock budgets do not bound arbitrary native commit or close hangs.

Measured combined-load results: added business p95 at 0 events was 5.529 / 5.846 / 2.688 ms for audit off/on/blocked; at 1,000 events 2.241 / 2.295 / 2.141 ms; at 10,000 all three were below the matched control. Offer p95 was 0.0037 ms, maximum 2.645 ms. Across five paired ten-second windows, added heartbeat p99 was 1.0386 ms (limit 5 ms); candidate maximum was lower than control (allowed increase 20 ms). A deliberate 50 ms stall was detected at 41.1176 ms. Owner bookkeeping p95 was 0.0285 ms; post-release drain p95 0.2932 ms. These are local observations, not a universal production latency guarantee.

## Adverse evidence and bounded correction

All adverse runs remain retained. An initial asyncio-clock heartbeat did not achieve the specified sampling cadence and is invalid for acceptance. A corrected high-resolution heartbeat exposed repeated diagnostic-sink GIL reacquisition on Windows. The two existing sink-only batch yields now pause for 1 ms; producers, worker bounds and admission rules are unchanged. The calibrated isolated run then passed. No generic executor or business timing change was introduced.

One stress run stopped on a Windows atomic-replacement PermissionError. Another heartbeat run was contaminated by concurrent formatter CPU work; neither is a pass. F20 file-sharing behavior remains a P02 concern; no retry or wider file-sharing change was hidden in this packet. Initial formatter trouble was traced to tool temporary-directory access and resolved with process-local TEMP/TMP/cache paths under the private artifact directory, not persistent configuration changes.

An early focused run still mocked old public service boundaries and attempted Sheets GETs before interruption; the unit SQL guard prevented live SQL. Tests were corrected to isolate the physical boundaries. This record does not claim zero attempted provider reads across the entire development session. All accepted qualification uses inert provider fixtures; no provider writes occurred.

Security source review found a non-security outcome-attribution bug: refused requests borrowed the active run's identity, allowing a busy reply to alter its delivery observation. Refusals now have no admitted pipeline ID and expose `blocking_run_id` separately. The 16-pair negative check verifies refused delivery leaves the active operation unchanged.

## Security and release boundary

K98 routing selected **Changes**, Deep off, for the Bot working-tree patch against the pinned baseline. SQL has no diff. Scan `aa6ca5c0-c649-43b8-a8d7-cbdb298c28d7` completed with all 18 changed source items reviewed and zero reportable security findings; its immutable snapshot preceded the final delivery-attribution correction. Final scan `e47efc7a-2df7-464a-8ab0-31ab86b14737` completed against the corrected snapshot with all 18 source items accounted for and zero reportable findings. It reused unchanged-source coverage and independently verified the attribution correction, all 26 postimages and unchanged 64 historical records. No repository-wide or Deep scan was performed.

The service-generated audit terminal projection has fixed fields and sanitized errors; the design's 8 KiB envelope is not an arbitrary-input serialization validator. There is no public caller accepting arbitrary terminal payloads. Cross-process ownership, automatic restart continuation, installed grants, natural live acceptance and immutable candidate release acceptance remain explicit limits.

Next release work, when authorized: final whole-PR review against an immutable candidate, protected updater/source admission, mirror/private promotion checks and installed/natural acceptance. Local green tests do not close these gates.

## Programme carry-forward

P01.4 remains delivered/deployed; its remaining natural acceptance stays in its own register. P01.2b stays closed without feature delivery. P01.6 and P02–P05 retain their existing ownership and sequencing. In particular, P02 keeps F20 file-sharing and F26 connection-fallback review, F09 contention remains separately qualified, and recovery must reconcile unfinished stages without replaying committed work. Use this packet's shared physical/effect evidence contracts and qualification fixtures where they fit later work; do not copy calendar-only policies blindly into other workflows.

Preserve all inherited documentation and all nine archive moves through the [carry-forward manifest](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Delivered%20Documentation%20Carry-forward%20-%202026-11-05.md).

## E97 final local checkpoint

The complete regression run exposed two AST teardown fixtures missing the newly required calendar service and one updater test expecting constants to be refused before any blob read. The teardown fixtures now isolate calendar/upload drains while retaining every diagnostic failure-isolation assertion. The updater test now proves an arbitrary constants change is refused through the exact-family content check; the other startup-contract early-refusal cases remain. These are test-only corrections, not runtime workarounds. All 205 tests in the affected teardown/updater suites passed in 10.75 s (`full-suite-fixture-corrections.txt`). The final busy-attribution runtime change separately passed 112 targeted tests; its physical-work/cost mechanisms are unchanged, so native/cost rehearsals were not repeated. The full suite ran once to completion; the three failed cases and their surrounding suites were then rerun. A second all-suite green run is not represented by these receipts.

Native audit start/finish p95: 5.202 / 5.363 ms across 30 pairs, below the 250 ms gates. Final security snapshot digest is `codex-security-snapshot/v1:sha256:248df9beed999e11fd8b02afc17c9b7680da56e0a2646a66be8eeffef07b2dfe`. Subsequent changes are this completion documentation and the two test-only fixture corrections; runtime/updater bytes are unchanged. Those supplemental changes were read/reviewed locally and do not alter deployed permission, input, data-access, configuration or persistence behavior; no additional discovery scan is required for them.

Security artifacts are retained in the app-managed scan bundles for the two scan IDs above. Final scan reports 1,341,115 aggregate rollout tokens, including 1,329,664 cached input tokens; the initial scan reports 7,132,710 aggregate rollout tokens including 6,808,960 cached input tokens. These are the plugin's cumulative rollout counters, not a claim about incremental billable usage. No findings or coverage gaps remain within the reviewed changed-source scope; production and release limits above remain.

Documentation check: 40 required Markdown destinations, 809 relative links, zero broken targets. Of 42 inherited Git paths, 36 remain byte-identical or preserve their prior removal and six have intentional navigation/status additions. All inherited archive destinations and all nine archive moves are preserved. Private preservation/link receipt: `documentation-validation.json`. Final ordinary validators and whitespace checks passed.

**Local implementation and qualification are complete with the explicitly recorded test-run history and limits.** The next step is immutable candidate/PR review and release preparation when authorized; this document does not authorize publication or deployment.
