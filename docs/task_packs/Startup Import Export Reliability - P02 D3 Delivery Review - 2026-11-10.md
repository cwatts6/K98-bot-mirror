# P02 D3: ownership and maintenance delivery review

D3a is implemented and qualified for mirror review in PR [513](https://github.com/cwatts6/K98-bot-mirror/pull/513), following the requested fresh bounded coverage review. No outstanding D3a review finding remains. The six maintenance boundaries and D4/D5 remain open. The [D3 handover and scope](Startup%20Import%20Export%20Reliability%20-%20P02%20D3%20Handover%20and%20Scope%20-%202026-11-10.md) and starting-point sections below preserve the earlier handover evidence.

## Authorization and starting point

The operator authorized completing and merging the D2 production PR, holding deployment until after D5, then starting D3. D2 private PR [738](https://github.com/cwatts6/k98-bot/pull/738) merged on 10 November 2026 at `cd04ed5e494adf5bf40f607798b38abb8df1b836`. Its exact reviewed head was `e02c2d37daffc46dcfb5a5b1521f809bfdab3efd`. All five CI checks passed, automated code review completed without findings, and Changes security review `783aa032-d4d3-4b19-898f-ca2bd037ebcf` completed with zero findings. Local tests: 12,951 passed, 1,184 skipped, one warning, eight subtests passed; both operational-log isolation checks passed. Linux CI: 12,772 passed, 1,363 skipped, 19 warnings, eight subtests passed. Windows updater and release-identity checks passed. The two-file test hygiene correction is merged in mirror PR 511.

D3 begins from the resulting scrubbed mirror snapshot `4455bfcacc3c2c5e60216cf80ef84adc42e0d397`, on `codex/p02-d3-file-ownership`. SQL source is clean at `7a3dec1326b2bcc86455626849b373d1123232a2`. No deployment, updater installation, restart, production SQL, provider or retained-recovery action occurred. This record starts the already-approved D3 scope; it does not claim D3 implementation or qualification complete.

Use the existing [remaining-work handover](Startup%20Import%20Export%20Reliability%20-%20P02%20Remaining%20Work%20Handover%20-%202026-11-09.md), [integrated plan](Startup%20Import%20Export%20Reliability%20-%20P02%20Integrated%20Analysis%20and%20Delivery%20Plan%20-%202026-11-07.md), and [D2 delivery review](Startup%20Import%20Export%20Reliability%20-%20P02%20D2%20Delivery%20Review%20-%202026-11-09.md). The operator's later promotion authorization supersedes the handover's historical promotion restriction. The deployment hold remains current.

## D3a scope: shared file ownership

**Scope Summary.** Fix F20 at the shared file-lock boundary before separating SQL maintenance. Acquisition errors, protected-body failures and cleanup outcomes must remain distinct. Release only the exact owned lock; never remove a foreign/replaced sentinel or infer abandonment from age. Retain the original failure when cleanup also fails. Keep admission closed when physical cleanup cannot be established.

**Affected Areas.** `file_utils.acquire_lock` is used by ordinary and guided player-cache publication, startup completion readback, `ark/team_state.py`, `ark/state/ark_state.py`, and `services/tracked_view_store.py`. The tracked-view wrapper currently calls `__exit__(None, None, None)` to compensate for the helper's body-error leak; replace that workaround only together with a verified shared contract. `file_utils.release_lock` has no current repository caller; it must not provide a path-only bypass around new ownership checks. The separately named governor-session DAL lock is SQL-backed and outside this file-lock correction.

**Architecture Direction.** Preserve the public context-manager entry point and existing timeout defaults. Put any substantial platform ownership implementation in a focused `core/` helper rather than expanding the legacy utility module. Separate acquisition retry from the single protected-body execution. Use a monotonic acquisition deadline. Define an exact descriptor/file identity and release contract, including Windows behavior, before coding; a path existence check followed by unlink is insufficient. Prove replacement/close races, not just a normal `finally` path. Keep state writes atomic and drain physical work after cancellation. Do not add automatic stale-lock deletion or widen filesystem permissions.

**SQL / Persistence Review.** D3a changes file ownership only, with no schema, grants, SQL procedures or state-format migration planned. State must remain protected across competing writers and exceptions. A process restart does not authorize deleting an old sentinel. Subsequent D3 maintenance slices require authoritative SQL and durable due/claim/completion evidence. Current SQL object locations for all six stages were confirmed in `C:/K98-bot-SQL-Server/sql_schema`; no business SQL was executed.

**Refactor Triggers.** Fix the duplicated tracked-view cleanup workaround as part of the shared contract. Keep Ark behavior unchanged apart from lock cleanup and regressions. Do not expand into Ark redesign, broader import orchestration, or P01.6 cache decode/rebuild optimisation. Review moving immutable snapshot parsing outside the writer lock as a separate narrowly proved follow-up, preserving generation identity.

**Security Review Decision.** The eventual D3a implementation touches filesystem ownership and restart-sensitive state: require a Changes scan of the exact Bot base/head, Deep off. SQL maintenance changes need their own SQL diff review. This initial document and disposable diagnostic evidence have no runtime change; no new scan is needed solely for this scope record. Root SECURITY.md and shared-helper guidance were consulted.

**Test Strategy.** Regressions must cover normal release, competing acquisition, a body `FileExistsError`, ordinary failures, `BaseException` cancellation, failed descriptor close, cleanup failure preserving the first error, replaced/missing/foreign/symlink sentinels, and replacement at the close/unlink boundary. Exercise player-cache ordinary/guided/startup, Ark team/state and tracked-view callers with isolated paths. Native Windows and a separate process must qualify the actual ownership/release behavior; no production files or locks may be used. Preserve timeout values. Run architecture, deferred, selector and security-routing gates, focused caller regressions, and exact updater transition checks before PR.

**Conditional References.** Shared-helper review guide applies. Startup/shutdown and Windows ownership contracts apply when the final descriptor-lifetime design is selected. No Discord command or public UI redesign is in this slice.

**Open Questions / Approval Needed.** No renewed implementation approval is needed within the agreed D3 scope. The exact race-safe Windows/POSIX release design and handling of cleanup uncertainty require engineering verification before implementation, not a new product decision. A change to lock recovery policy, backup schedules or deferred domain behavior would be outside this scope.

## D3a implementation and qualification

Mirror PR [513](https://github.com/cwatts6/K98-bot-mirror/pull/513) implements the
shared owner, preserves the facade, drains ordinary cache/Ark saves, passes real
tracked-view failures through release, and verifies startup from the same bounded
immutable bytes. Windows releases its exact handle; POSIX keeps the rendezvous
inode. No age/PID recovery or path-only deletion is permitted. Local admission
remains claimed until cleanup is acknowledged, including a physically closed
handle whose acknowledgement is delayed or lost. An uncertain close is never
retried against a potentially reused handle.

The bounded [coverage delta](Startup%20Import%20Export%20Reliability%20-%20P02%20D3a%20Coverage%20Delta%20-%202026-11-10.md)
records caller census, review corrections and the six remaining SQL boundaries.
The baseline failure artifact remains intact. Two additional regressions failed
before the local admission/ancillary logging corrections and pass afterward.

The exact D3a updater family has eleven members (six changed, five retained
dependencies), with 82 total entries. All 81 predecessor definitions and the
registry byte bound remain unchanged. Historical tests now expect the added
entry while retaining their original history digests. This single-slice contract
does not solve the D4 combined deployment jump.

| Gate | Evidence / current result |
| --- | --- |
| Native Windows and Linux | [CI run 42781962660](https://github.com/cwatts6/K98-bot-mirror/actions/runs/42781962660) at `d8490eb476ba08812c077b1ed685de9be082a48c`: Windows 29 passed / 6 POSIX skips; Ubuntu 32 passed / 3 Windows skips. Pure helper suite uses no application fixtures. |
| Focused final corrections | 128 passed, 6 platform skips, covering helper, real callers, exact D3a updater, ordinary cache and foreign-lock timeout. |
| Full repository | 13,051 passed, 1,191 skipped, 1 warning, 8 subtests passed in 1,505.19 seconds. Operational-log isolation passed: production operational logs unchanged. The earlier 18 failures were stale registry-count assertions; their historical digest checks remain intact. |
| Static/repository gates | Architecture (43 Python files), deferred validation (3 Markdown files), security routing, selector, import smoke, command registration and applicable pre-commit checks passed. |
| Security Changes | Final runtime range `402151f8c1a63015c2ad5dd02f8599997cba01d6..d8490eb476ba08812c077b1ed685de9be082a48c`; scan `66f03e2e-5201-4e2b-9a13-4f959800ed76`, complete coverage of all nine source-like files, zero findings, Deep off. Subsequent changes are test-count assertions and delivery documentation only; no repeated security scan for those non-runtime edits. |

Qualification uses disposable local paths and native CI surrogates. Production
filesystem type, parent custody/ACLs, installation and provider behavior are not
requalified here. Trusted local parent directories and cooperating writers remain
prerequisites; same-process uncertain-close custody does not establish
cross-process quarantine after an ambiguous physical release. Ark independent
two-file saves and stale-instance merge behavior remain a recorded domain
follow-up. No SQL changes/execution, private promotion, deployment, restart or
retained recovery occurred. D3a does not close D3, D4, D5 or P05 acceptance.

## Reproduced baseline, before implementation

Fresh continuation review: [D3a coverage delta](Startup%20Import%20Export%20Reliability%20-%20P02%20D3a%20Coverage%20Delta%20-%202026-11-10.md)
records the source/caller reconciliation, additional cancellation/first-failure
cases, platform ownership design and both configuration transaction contracts.
D3a implementation and qualification are recorded above; all six maintenance
boundaries and D4/D5 remain open.

A disposable local fixture exercised the actual helper from the D3 starting snapshot, with inert test configuration and no SQL or network calls:

| Case | Observed current behavior | Required correction |
| --- | --- | --- |
| Body raises `ValueError` | Original error survives, lock remains | Release exact owned lock in cleanup |
| Body raises `FileExistsError` | Original error becomes `TimeoutError`; lock remains | Retry acquisition only; preserve body failure |
| Body raises `asyncio.CancelledError` | Cancellation survives, lock remains | Cleanup runs for cancellation and preserves it |
| Replacement injected after descriptor close, before path unlink | Foreign successor is deleted | Release must bind to original ownership through physical cleanup |
| Foreign sentinel exists before acquisition | Times out and preserves foreign sentinel | Preserve this behavior |

These are reproduced defects, not passing candidate tests. Private fixture evidence is retained with the D2 promotion work. No application source or test suite has been changed at this scope checkpoint.

Scope-record validation: deferred-item validation passed for this document; architecture reported zero changed Python files; test selection and security-routing validation passed. Repeating runtime, SQL or command-registration tests for this document-only checkpoint is skipped because it changes no executable behavior; the completed D2 candidate evidence remains applicable. Implementation tests and review gates above remain mandatory for D3a.

## Remaining D3 maintenance packages

Scope each package against real children, required business effects and existing durable maintenance machinery before changing it. Slice boundaries may combine tightly coupled contracts; this is not a promise to create six unrelated PRs.

| Boundary | Owning procedures / service | Required distinction |
| --- | --- | --- |
| Import Phase A | `UPDATE_ALL2`, `IMPORT_STAGING_PROC_CORE` | Keep claim, typed input, history, allocation, receipt and archive integrity; separately qualify sampled statistics and conditional KS4 maintenance |
| Configuration | `sp_TARGETS_MASTER` -> `CREATE_DELTA_TABLES` | Keep atomic delta publication and identity; separate eligible statistics/rebuild/reorganise and optional timing logs |
| Player report | `SP_Stats_for_Upload` | Keep consistent result and capture; separately qualify FULLSCAN, preserving D2's actual statement budget |
| KVK output | `sp_ExcelOutput_ByKVK` and children | Preserve required schema, unique indexes, views, output and receipt; distinguish nonessential upkeep |
| Final stats reports | `usp_S11CompleteStatsReportsCore` | Keep stage completion/output; distinguish admission headroom from post-success CHECKPOINT, statistics and backup waits |
| Explicit post-import | Python maintenance owner and `usp_update_stats` | Preserve committed outcome and physical worker ownership; durable maintenance due/claim/completion, bounded backlog and headroom |

Maintenance failure after a business commit must not relabel the import as failed or authorize replay. Test real child failures, restart, cancellation, competing owners, cleanup, capacity and both reader/writer arrival orders. Preserve the recorded raw-history SNAPSHOT versus index REBUILD SQL 3961 failure until its D3 reader/maintenance boundary is actually qualified. Keep RCSI off, existing timeouts and resource thresholds unchanged, and backup schedule policy separate.

## Mandatory D4 release-compatibility carry-forward

D2's promotion check found a concrete deployment condition: recorded installed Bot `97abcce1b2a9e71b3959eff74525c57930a703e6` to the combined D2 candidate returns `COORDINATED_RELEASE_REQUIRED`, even with the newly packaged updater. The twelve individually pinned transitions do not authorize a direct jump across all intermediate slice versions. All 69 pre-D2 definitions are preserved; registry occupancy is 81. The offline package's hashes and contents were verified, but it was not installed and does not make the combined target deployable.

D4 already owns final source/SQL/startup/updater compatibility. It must add and qualify an exact final combined transition or supported coordinated release for the actual final target, preserve predecessor definitions and dependency pins, reject mixed/missing/foreign bytes, and regenerate the updater package. Do not weaken matching, infer arbitrary transition chaining or deploy intermediate slices to bypass the refusal. D5 must qualify the resulting combined candidate. Refresh installed identities and changed-path/ancestor custody at the later deployment checkpoint; historical host evidence is insufficient. D2 is merged, but immediate combined deployment readiness is explicitly not claimed.
