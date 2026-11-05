> **Current E95 - 5 November 2026:** P01.4 delivered and deployed; locally qualified across the full scope; production acceptance confirmed for exercised paths, with remaining natural-activity checks tracked explicitly. See [closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.4%20Closeout%20-%202026-11-05.md), [acceptance register](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Natural%20Acceptance%20-%202026-11-05.md) and [P01.5 handover/scope](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Handover%20and%20Scope%20-%202026-11-05.md). P01.5 calendar ownership and outcomes (F23/F24/F25) is next, review/scope first. Earlier dated checkpoints below are historical. Carry this documentation delta through [the current manifest](Startup%20Import%20Export%20Reliability%20-%20Documentation%20Carry-forward%20-%202026-11-05.md).

# Startup, import and export reliability: Stage 1 tracing

> **Historical E91, 5 November 2026:** The [complete local qualification receipt](archive/Startup%20Import%20Export%20Reliability%20-%20P01.4%20Complete%20Local%20Qualification%20-%202026-11-05.md) records the full original P01.4 design implemented and qualified locally, with both optional workers enabled in the unpublished candidate. Cost, physical-drain, diagnostic-priority, updater, regression and Changes-review gates passed. No CSV scope was deferred. Publication/deployment and natural-activity acceptance remain outstanding; earlier E88-E90 disabled/pending statements below are historical. Existing changes and archive moves are preserved.

> **Historical E85/E86 - 5 November 2026: P01.3 CLOSED.** Passive health, persistent Refresh and the complete-ZIP correction are merged, deployed and live-validated at private `6ec393f71626d15fcb8c50c840854fb681d5f09e`. See [P01.3 closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.3%20Closeout%20-%202026-11-05.md) and [P01.4 handover/scope](archive/Startup%20Import%20Export%20Reliability%20-%20P01.4%20Handover%20and%20Scope%20-%202026-11-05.md). P01.4 (F17/F30) is next, review/scope only. P01.1/P01.2a remain accepted; P01.2b is closed by decision without feature delivery. P01.4-P01.6/P02-P05 and exact incident recovery remain open. Dated checkpoints below retain historical evidence, not current approval or scheduling authority. The [new documentation carry-forward manifest](archive/Startup%20Import%20Export%20Reliability%20-%20P01.4%20Delivered%20Documentation%20Carry-forward%20-%202026-11-05.md) covers this local closeout update.

> **Historical programme checkpoint - 4 November 2026 (E68/E69):** P01.2a is deployed and accepted for its declared reporting/evidence scope at private `67c4e12a8ecf0c25280770860480ac65a6826602`.
> Read the [P01.2a closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Closeout%20-%202026-11-04.md) for delivered corrections, evidence limits, learnings and remaining owners; [P01.2b handover](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Handover%20and%20Scope%20-%202026-11-04.md) is the next review/design task.
> The earlier checkpoint is retained history. Current remaining implementation is P01.5/P01.6/P02-P05 and exact incident recovery; P01.4 natural acceptance is tracked separately at E95. Do not replay accepted work.

Date: 2 November 2026. Review only; no runtime or SQL changes.
This handback completes the **main first-pass dispositions**, including Report 66 and the
later screenshots. The separate final outlier sweep and production qualification are
still open. [Scope](Startup%20Import%20Export%20Reliability%20-%20Scope%20-%202026-11-02.md)
owns requirements; [tracker](Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md)
owns milestone status and remaining work. Findings below extend its stable F identifiers.

## Result and historical explanation

Related work was delivered previously. The inspected changes have not simply disappeared.
The remaining problems cross boundaries that those packages did not fully qualify:
observer admission versus arriving producers, business completion versus its observation,
provider success versus durable settlement, and status presentation versus active probing.
There is also a possible adverse interaction introduced by the previous observer correction.
It must be tested rather than dismissed as either definitely a regression or definitely unrelated.

| Earlier delivery | Protection retained | Gap exposed by this review |
|---|---|---|
| Private #677/#679 | Correct report session/execution policy for the repaired route | The player-cache producer still inherits a 15-second query timeout while its 300-second setting changes SQL lock waiting. A shared factory does not give every consumer the intended execution budget. |
| Private #675 / SQL #129, then selected waiting corrections in #698 | Durable reporting receipts, remaining-stage continuation and prevention of committed import replay | Report validation still converts writer contention and invalid prerequisites into the same conflict. Existing contention tests exercise other branches. F27 is retained code, not a demonstrated reversion. |
| #685/#686 | Authority diagnostics and bounded account-lock waiting; no blind provider replay | The outer authority account-lock admission is still one second before result recording. Provider response validation does not guarantee result persistence or closure. |
| #692/#694/#695/#696 | Startup ownership, attempt recording, worker drain, connection/retry budgets, queue and observation handling | Startup configuration retains cancelling deadline semantics; display health checks remain active operations; some verified completion still requires a separate workflow action. |
| #698 and SQL #133 | Correct checkpoint/observer lock order, typed busy after cleanup, selected metadata retry and diagnostic support | Nonblocking acquisition does not mean an observer cannot block an arriving producer. Retry coverage applies to selected checkpoint transitions, not every producer guard or authority boundary. |
| Earlier import audit adoption: private #491/#493/#494/#495 | Location/Honor/Pre-KVK/Weekly Activity phase and batch records; Weekly Activity separates notification failure from import success | Honor still reports import failure after a success-notification exception; Honor/Pre-KVK/Location can mark a batch failed after post-import refresh failure. Tests encode these inconsistent outcome contracts. F17. |
| Tracked-view restoration: private #688, commit 9662bb80 | `tracker_lock` explicitly works around exception cleanup in the shared file-lock helper | Direct cache/Ark callers still use the unchanged helper. Startup verification can leave a lock file behind when readback fails. F20 reproduces the mechanism and confirms that the tracked-view wrapper cleans up correctly. |
| Atomic configuration publication: SQL f5ecc3e (16 October), with earlier delta serialization 758f456 | Configuration data/publication and its exact receipt share a transaction; competing delta preprocessing is serialized | The delta callee also performs statistics/index maintenance and writes a performance log. The configuration contract fixture substitutes a transactional stub for that callee, leaving this combined failure/cost boundary unqualified. F21. |

Private history attributes `StatsImportOutcomeDAL._observe_idle` and its exclusive global
snapshot guard to `f6a929c0` (#698). The producer guard in `LegacySnapshotDAL.session` rejects
immediately when that guard is held. This identifies a concrete interaction introduced by
the observer fix; it does **not** identify the holder in the latest production failure.

Why it was missed: the evidence supports incomplete cross-caller acceptance and an incomplete
non-interference contract. The earlier native suite even tests observer-first checkpoint
contention successfully, but that success depends on the checkpoint's retry policy. It does
not cover new producer admission at the same guard. Startup cancellation is tested as a valid
unconfirmed outcome in existing helper tests, without checking this configuration caller's
completed-worker result. Normal import/export acceptance exercised success, not every overlap.
The 28 October closeout explicitly retained broader R08/R09/R12 census work. These are
coverage and scope conclusions; PR discussion intent was not independently refreshed.
Two later cross-checks make this concrete: Honor tests preserve an incorrect import-failed
classification after notification failure (F17), and #688 repairs the shared file-lock
exception behaviour only through a tracked-view wrapper while direct callers remain (F20).

## Evidence and limits

- Mirror: `a025adb7a69aac321fd62794b871ed5903338f44`; authoritative SQL:
  `7e91989f619deb46836194c7e705b0a9eb2ebe11`.
- Compared 42 selected Bot files with retained deployed `ad4cd995`. Forty are identical
  after newline normalization. Differences are MGE shutdown admission in `bot_instance.py`
  and installation-contract/index metadata handling in `services/export_execution_dal.py`.
  The latter matters to future cost measurements; use deployed queries rather than an older
  mirror query plan. Relevant SQL diff from retained pin `9344a376` contains MGE finalisation.
- Current AST reference searches found 78 distinct candidate references across 28 files.
  References include function arguments as well as direct calls. This is a selected-root
  census, not 78 independently executed paths or a complete repository audit.
- Private artifacts under `.codex_artifacts/startup-import-export-review-20261102` contain
  `entrypoint-references.csv`, `secondary-references.csv`, `source-manifest.json` and
  `startup-observation-result.json`. Raw incident identifiers remain in private evidence.
- The older inventory examined 774 Python files and identified 424 explicit sites in 111
  files, plus 2,268 indirect sites in 223 additional files; 188 SQL sites in 33 files.
  Those lexical candidates are not all defects, and have not all received a current semantic
  disposition. G01 below prevents this first handback being mistaken for that completion.
- No live SQL, provider request, production repair or new host-health verification was run.

## Process and caller map

| Tracker route | Current callers and path traced | Effects, retained protection and disposition |
|---|---|---|
| C01 startup | `bot_instance.on_ready` schedules player cache and ProcConfig; runtime startup registers recovery/export workers. `core/startup_diagnostics` observes their tasks; `core/owned_work` drains entered work. | Keep single owned execution and drain. Separate observation deadline from execution cancellation. Configuration differs from the player route, which already sets `cancel_on_deadline=False`. F08. |
| C02 player report/cache | Startup builder, `commands/stats_cmds.refresh_stats_cache`, KVK admin cache refresh and report continuation reach the shared producer/cache services. `player_stats_cache._execute_sp_with_retries` verifies the actual producer cursor. | Keep exact producer identity and captured generation. Correct per-connection query policy; do not interpret the logged 300-second lock setting as query timeout. F01/F03. |
| C03 configuration | Startup wrapper, admin import, maintenance worker, pipeline configuration and configuration continuations reach `run_proc_config_import`. Active runtime gathers provider inputs before SQL writes and uses the shared admitted writer/snapshot path. | Keep input identity and atomic SQL outcome; check inherited query budget and guard lifetime. Completion observation must not cancel successful work or require repeat import. F01/F03/F08. |
| C04 stats/pipeline | Pipeline and admin stats paths reach `stats_module`, UPDATE_ALL2, execution receipts, checkpoint/capture and pipeline binding; recovery resumes evidence-bound unfinished stages. | UPDATE_ALL2 has a distinct 595-second query budget within a 600-second execution envelope. Preserve it where justified. Automatically bind exact completed evidence where policy allows; never replay SQL to make observation green. F06/F10. |
| C04 all-KVK | Workbook importer -> admitted ingestion -> DAL write/stage completion; KVK admin recomputation verifies its producer cursor. Active export uses exact capture identity and runtime submission. | Shared admission is reused by nested helpers. Review recomputation's inherited short query budget; preserve multistage commit and capture semantics. Legacy runtime-none export is a separate compatibility path. |
| C05 coordination | Snapshot service/DAL, coordination DAL, queue, claim admission, producer session, commit/capture and release. | Distinguish process-local producer turn, SQL application lock, durable reservation and incident status. Clearing one is not proof that the others are finished. Retain owner/fence/version checks at mutation; remove observer ownership of producer guards after qualified replacement. F03/F09. |
| C06 authority | Runtime client -> authenticated pipe -> serial authority broker -> execution authority, account lock, provider dispatch/result event, pacing and closure. | Retain request identity, peer authentication and exact-result evidence. Settle completed provider work without resending it. Observation shares the serial server and can delay later requests even without SQL conflict. F02/F12. |
| C07 recovery | Recovery monitor discovery and existing incident refresh; outcome worker; configuration/read/producer/pipeline/evidence adapters. | Typed waiting and some automation exist. Monitor orchestration also executes accepted or allowlisted actions and persists observations. Separate those effects and budgets rather than labelling the entire loop passive. F04/F09/F10. |
| C08 status/report | `/status`, recurring health embed, health probes, recovery centre/detail/recheck and report export. | Historical trace: centre/report retained reads, status-triggered probes and detail refresh/reconciliation. E85 closes F11 with passive status/card/Refresh and health reports. F04 still requires explicit classification of actual recovery actions. |
| C09 history | Mutable incident evidence, source adapter evidence, `recovery_report` allowlist, complete paginated report. | Preserve meaningful original/subsequent failures separately from current state; include pipeline detail safely. A missing report field does not prove its source never existed. F05/F06. |
| C10 secondary/lifetime | `maintenance_worker`, `file_utils`, stats offload helpers, display-only `stats_alerts/kvk_meta`, target warmup, queue presentation and shutdown ownership. | Protected runtime uses owned/drained work. Legacy stats offload fallbacks can re-enter after exceptions and need separate disposition; they are not the enabled protected path. Display metadata can fall back to an active configuration read. Shutdown must drain real work without mistaking an observer deadline for worker termination. |

The Crystaltech offload reference and independent Ark/MGE/voting/event SQL/locks remain
candidate edges until shared resource interaction is established. Domain implementation
stays in P1; a domain name alone neither excludes a shared-lock edge nor brings all its
business logic into this phase. Host deployment/singleton mechanisms are distinct from
the account/snapshot contention discussed here. The previous broad inventory remains the
source for reconciling these boundaries, rather than silently dropping unmatched files.

## Findings requiring design

### F09: an observer can refuse a new producer

**3 November evidence update (E50/E51):** Report 68's new pipeline failed at this
producer guard with 51421 before configuration writes, after stats/player capture
completed. A real local SQL experiment using extracted deployed guard methods and
unique resource names confirms observer-first refusal, success after observer release
and producer-first observer deferral, with zero retained experiment locks. Account
authorization and contract checks were stubbed; the actual production holder and
negative applock return were not captured. Eight direct-path sources are unchanged
by P03a.2. This validates the mechanism, not historical holder attribution or a fix.
Private evidence: `P03a2-Report68-Failure-Analysis.md`,
`p03a2-report68-failure-analysis.json`, `report68-native-guard-result.json` under the
existing private investigation root. Earlier qualification wording below is historical.
The user chose P01 design first; F09 remains P02. The extended canonical scope now
requires D01-D06 evidence and A13/A14 qualification across relevant boundaries.

`services/stats_import_outcome_dal.py:164` enters observation and a transaction, then
`_observe_idle:187` takes exclusive global `k98-legacy-output-snapshot` and account locks.
Snapshot reads also use update/held row locks. All-KVK, player-report and configuration
producer recovery inherit the same admission pattern.

`services/legacy_export_snapshot_dal.py:652` authorizes a producer, then obtains that global
guard as an exclusive session lock with zero wait, throwing 51421 if refused. A legal
interleaving is: producer authorization finishes; observer takes the guard; producer tries
the guard and fails. Observer `LOCK_TIMEOUT 0` prevents the observer waiting; it does not
prevent it holding a lock that refuses another session. Account-lock snapshots can likewise
delay other account users, including authority settlement, subject to actual overlap.

This is a static protocol counterexample. Native SQL qualification of this exact producer
entry remains required, and the latest production blocker remains unknown. The existing
`test_checkpoint_observation_sql.py::test_observer_first_serializes_checkpoint_without_opposed_row_wait`
tests a different, retryable checkpoint boundary. It must be retained and supplemented.

### F08: startup observation can discard a successful worker result

`bot_instance.py:1976` schedules configuration with a 180-second observation deadline and
the default `cancel_on_deadline=True`. `core/startup_diagnostics.py` cancels the coroutine;
`proc_config_import.run_proc_config_import_offload` drains the entered thread through
`core/owned_work`, then propagates cancellation. The completion check after the awaited
operation is skipped, even if the worker returned success. `verify_startup_import` itself
only checks the returned result; it does not need another SQL query.

An isolated experiment used these current startup/drain helpers, a scaled deadline and
threading barriers. It did not import the operational configuration or execute ProcConfig:

| Observation policy | Worker executions/completions | Completion checks | Result |
|---|---|---|---|
| Current cancelling default | 1 / 1 | 0 | `deadline_elapsed_outcome_unconfirmed`, result lost |
| Observe without cancellation | 1 / 1 | 1 | `completed_after_deadline`, success retained |

This reproduces the mechanism, not the timing or cause of the retained production incident.
Keep worker ownership/drain; make cancellation an explicit execution policy, not a side
effect of measuring duration. The player startup path already demonstrates the distinction.

### F10: exact completion can still require a manual verification action

`services/processing_pipeline_recovery.py:37` obtains a review snapshot, gathers producer
evidence and checks another snapshot; `inspect` checks again before returning. A normal
inspection can acquire at least three account-locked snapshots. If exact producer evidence
already proves the unfinished import/configuration stage, it offers `verify_stage` to bind
that evidence. This action is absent from `RecoveryService.recover_automatic`'s four-pair
allowlist. Reconciliation of previously accepted actions is a separate mechanism.

Design an idempotent, exact-evidence automatic binding policy, preserving fresh identity,
owner/version and stage checks at mutation time. Simplify passive inspection separately.
Deciding to continue remaining business stages, discard work or repeat an uncertain effect
is not equivalent to acknowledging an already completed stage.

### F11: viewing health starts consequential work

**Disposition at E85: CLOSED for P01.3.** The trace below records the original defect and pinned historical source. Passive presentation, persistent Refresh and complete/ordinary health report delivery are now reviewed, merged, deployed and live-validated. Preserve real write-boundary controls; the trace does not describe current display behavior.

`commands/admin_cmds.py:1132` and the recurring health embed in `bot_instance.py` call SQL
and Sheets health checks. `HealthProbe` shares an in-flight task, but does not retain a
completed result as a time-based cache. A UI wait timeout leaves the probe running.

Sheets health reaches `gsheet_module.check_basic_gsheets_access` and runtime
`read_configuration(..., wait_for_admission=False, health_probe=True)`. This uses a durable
preparation, claims configuration resources, opens an authority probe stream, performs a
real provider read, records evidence/pacing and releases ownership. Existing defer/cleanup
handling is useful, but the probe is not passive. A provider read can still contend or
leave uncertain bookkeeping. SQL health similarly opens a connection and executes a query;
its UI timeout is not an explicit statement budget.

Prefer retained health with timestamp/freshness for display. Evaluate successful business
activity as health evidence and schedule explicit probes only when their result is useful.
Retain actual pre-write authorization; a cached display must never authorize a mutation.

### F04/F12: refresh and scheduling need effect-level separation

`RecoveryService.review` calls `refresh`, which can reconcile already accepted pending
actions before inspecting. `review_source` can inspect and then refresh again. Recovery
monitoring runs discovery, selected automatic recovery and incident persistence; it is
not solely a read loop. An observation can update LastSeen even when nothing meaningful
changed. Private-evidence checks decrypt/hash copies and query the catalog repeatedly.

`scripts/run_export_authority.py:703` handles one pipe connection and broker dispatch at
a time. Inspection therefore occupies the same request-serving path as useful execution.
SQL nonblocking admission cannot remove this scheduling/I/O cost. No measured starvation
or latest-incident attribution is claimed. Preserve authenticated serialization where
needed; design bounded observer scheduling rather than casually parallelising mutations.

The recovery notification system uses a deduplicated overview with a five-minute delivery
cadence, not one message for every stored incident. However, open/pending counts feed its
attention classification even when no operator action is useful. Ordinary waiting and
automatic progress should not require acknowledgement merely to clear that classification.

## Check necessity and proposed dispositions

These are design recommendations, not permission to delete protections without replacement.

| Check / consumer | Value that must be retained | Proposed disposition and acceptance |
|---|---|---|
| Actual writer owner/fence/version and resource claims | Prevent stale/concurrent mutation | **Keep at mutation boundaries**; consolidate duplicate reads only with equivalent protection. A01/A04. |
| Request identity, provider result, closure evidence | Prevent duplicate delivery and false success | **Keep; automate exact settlement** without provider replay. A05/A06. |
| Observer global/account ownership and update-lock snapshots | Currently makes inspection internally consistent | **Replace observer admission/read design**; it violates intended non-interference at producer entry. Mutation must still revalidate. A02/A03/A07. |
| Producer installation/permission and schema checks | Ensure the actual session operates within the pinned installation | **Keep session-sensitive checks; investigate consolidating stable contract checks**. Some verification occurs inside the global guard and repeats on the actual cursor. Any caching needs explicit invalidation. A01/A02/A04. |
| Startup completion result | Truthful readiness/completion | **Keep; separate observation from cancellation**. Delayed success is success. A04/A05. |
| Pipeline repeated review snapshots and manual `verify_stage` | Bind the exact completed producer to its intended stage | **Simplify reads and automate eligible binding**; retain strong write-time validation. A05/A08. |
| Passive status and detail rendering | Inform the operator what is known and whether action is needed | **Use retained evidence; separate active refresh/recovery execution**. A07/A08. |
| SQL/Sheets probes | Detect persistent dependency unavailability when no useful recent evidence exists | **Consolidate, cache for display and schedule proportionately**; remove implicit probe on ordinary view. A02/A07/A10. |
| Private evidence hash checks | Detect unavailable/corrupt evidence before relying on it | **Keep at reliance/repair boundaries; investigate background cadence and duplicate work**. Never treat restoration as delivery proof. A02/A09. |
| Poll persistence, open/pending overview and generic Recheck text | Monitor freshness and genuine actionable failures | **Aggregate routine activity; distinguish waiting, automatic progress, blocked work and decisions**. No manual acknowledgement for routine recovery. A08/A10. |
| Original/subsequent failure context and report allowlist | Explain what failed and why it recovered | **Preserve bounded meaningful history and extend safe reporting**; no incident per poll. A09. |
| Legacy offload exception fallback | Compatibility when protected runtime is absent | **Investigate/remove re-entry after uncertain execution** for supported fallback modes; do not attribute it to the protected runtime. A01/A05. |

## Manual actions: initial necessity review

An action's label is not enough to classify it. In particular, "clear lock" may clear a
durable blocker flag, fence a reservation, discard a read result, or acknowledge a completed
stage. These need different policies. The following source-reviewed cases narrow G04;
nested replacement/rollover and inherited/dynamic action paths have now been cross-checked
in the [complete allowed-action census](Startup%20Import%20Export%20Reliability%20-%20Action%20Census%20-%202026-11-02.md).
The table below retains the first-pass examples; the census covers all 73 allowed pairs.

| Current action / source | What actually happens | Recommended treatment |
|---|---|---|
| Recheck / `recovery_service.refresh` | Inspects again and may reconcile previously accepted actions | Routine retries/progress should happen automatically. Passive viewing should not be the trigger for executing accepted work. Keep an optional explicit refresh, without making it necessary for success. |
| `verify_stage` / pipeline recovery | Binds exact completed producer evidence to an unfinished stage | Candidate for automatic idempotent metadata reconciliation. No repeated producer execution. |
| `complete_cache_only`, `complete_configuration_only` / producer recovery | Verifies captured output and original no-export intent | Already eligible for automation. Check why any instance reaches the operator, rather than adding another confirmation. |
| `release_read` / configuration-read recovery | Verifies read-only authority history and releases exact abandoned-read reservations | Already eligible for automation. Retain exact closure/identity evidence and make ordinary contention automatic. |
| `withdraw_health_probe` / queue recovery | Cancels a disposable probe proven never to have executed | Already automatic. Prefer preventing unnecessary probes from creating durable queue work in the first place. |
| `close_withdrawn_read` / queue recovery | Records closure of an already withdrawn, unexecuted older read; original inputs/intent may be absent | Candidate for automatic administrative closure if it does not discard outstanding business intent. Keep unknown configuration outcome explicit; closing this row is not configuration success. |
| `withdraw_queued` / queue recovery | Cancels business work that has not acquired admission | A genuine cancellation decision unless an existing policy already supersedes it. Normal waiting alone should not create an incident demanding cancellation. |
| `contain_read` / configuration-read recovery | Cancels an unstarted read or fences/discards an entered read's result | Define cancellation policy from original intent and worker lifecycle; do not equate it with passive verification. Disposable health reads and business-input reads may differ. |
| `clear_unowned_hold` / unowned SQL recovery | Excludes current workers, verifies no durable owner/stream, audits and clears only BlockedReason; original SQL outcome can remain unknown | Investigate why the stale flag survives. Automate only if the system can establish the same safe disposition. The current click supplies an obsolescence decision, not missing proof of success. Never terminate a real SQL lock to make this pass. |
| `retry_configuration` / configuration continuation | Reads current source sheets and performs a new atomic configuration publication | Fresh business work, not a recheck. Retain a decision when sources/intent changed; uninterrupted original intent may support a separately designed automatic continuation. |
| `keep_prior`, skip/abandon actions / configuration, pipeline and export recovery | Chooses to retain old configuration or stop remaining delivery | Real business decision; preserve it and explain consequences. It must not be the only way to close bookkeeping for already completed work. |
| `retry_unstarted` / export recovery | Queues retained export after proving no attempt or execution stream exists | Evaluate automatic retry for ordinary transient refusal and unchanged intent. Genuine input/configuration correction may need operator input; avoid generic confirmation after every harmless delay. |
| `verify_publication` / export recovery | On uncertain publication can verify old writers and settle/clean retired slots; on confirmed output performs a fresh provider/content check | Separate settlement needed for original execution from optional later integrity checks. It is not a cheap status read, and should not run just to render a view. |
| `retry_absent`, `rebuild_damaged` / export recovery | Creates a separately identified physical export after fresh proof and capacity checks | Retain explicit recovery policy/decision; these are new provider effects, unlike recording a retained successful response. |
| `protect_evidence`, `restore_evidence` / evidence recovery | Restores exact hash-bound protected bytes and verifies copies | Assess narrow automatic repair eligibility and cadence. Adapter declares an automatic action, but the central allowlist does not include it; do not assume declaration means execution is automatic. Missing original evidence must not be replaced with an assertion. |

## Second and third cross-checks

The second pass widened discovery to tracked Bot source and canonical SQL definitions,
then followed shared helpers, inherited adapters and non-monitor callers. The third pass
challenged the conclusions against existing recovery code, focused tests and an offline
guard-order model. These are different checks, not three identical searches.

The refreshed inventory parsed 789 Python files without parse errors and scanned 572
canonical SQL files. It found 600 coordination/timeout signals across 151 files. All 371
historical candidate rows still have a current file. Counts include unrelated domains,
strings and infrastructure; they are not defect counts or proof of semantic coverage.
The private reconciliation ledger deliberately leaves unreviewed candidates open.
AST string extraction cannot fully resolve bracketed/dynamic SQL or inherited dispatch.

### Correction: automatic recovery is broader than four central actions

The central allowlist is only one execution route. `processing_outcome_worker.recover_failures`
calls `stats_import_outcome_service.settle_known_failure` for eligible prepared/rolled-back
receipts. `release_failure` therefore already has automatic execution outside that list.
During a writer exception, `recover_completed_writer` can verify exact committed SQL,
checkpoint/capture it under the retained guard and release ownership. The outer
`stats_module.run_sql_procedure` then recognises matching completed/captured evidence and
returns success without importing again. Pending capture is distinguished from SQL failure.

Preserve this work. Do not infer that every post-SQL exception loses success or requires
a manual click. The design question is which remaining continuation/settlement states
fail to converge automatically, with exact state and original intent as evidence.

The action census covers 52 distinct actions in 73 allowed source/action pairs. Four source
kinds expose no individual actions; group approval and generic Recheck are reviewed
separately. Fresh replacement destinations, discarding business input, retiring an export
and acknowledging an already completed receipt are not equivalent decisions. Completing
the policy census does not establish native safety of the proposed automation.

### F13: age-based discovery is not an actionable-failure test

`export_recovery_dal.pending_jobs` selects failed/uncertain work and running/waiting/ready
jobs whose UpdatedUTC is over 120 seconds old (or whose targets are isolated).
`pending_rollovers` uses a similar threshold. Provider request progress is recorded on
execution streams/attempts; it does not necessarily refresh the job timestamp. The
coordinator updates job state around claim and terminal/reconciliation transitions.

An old timestamp can therefore nominate work that is still progressing. AuthorityBusy
handling can defer inspection, so this does not prove every two-minute job creates an
incident. However, `recovery_runtime.alert_rows` classifies any open or pending count as
`attention_required`. Discovery age, actual progress, unresolved outcome and a useful
operator decision need separate policies. Measure false incidents with workload and
duration denominators; do not merely increase the threshold or suppress all slow work.

### F14: ordinary KVK reads acquire writer-style season ownership

`kvk/dal/source_routing_dal.resolve_season_read` calls `lock_scope`, which obtains the
exclusive transaction application lock `kvk-source:{SOURCE_KEY}:{kvk_no}` with a
10-second wait, then uses UPDLOCK/HOLDLOCK on season/routing/selection metadata. Public
report and card routing reach this path. Even the legacy-source choice is made after
season locking. This is a small metadata transaction: immutable report payload loading
happens afterwards, so the lock is not held across the entire report read.

Source intake/selection/publication and configuration's enabled source snapshot use the
same scope. The read/writer contention edge is source-proven; its live frequency and
impact are not measured. The authoritative SQL definitions for SeasonSource, SourceRouting
and SourceSelection exist. Design a consistent read of the pinned selection without
granting routine readers writer ownership. Keep fresh validation at actual selection or
publication mutation; do not substitute dirty reads or a global isolation change.

Other shared-read edges remain relevant even when a domain has its own tables. Ark uses
`v_PlayerProfile`, whose SQL definition joins player stats/location/account/fort views;
its separate `vw_ArkPlayerReport` is Ark-local. Leadership review reads KingdomScanData4,
PlayerLocation and activity/history objects. Profile caches use PlayerKVKHistory and
PlayerScanMeta through views. These are implicit SQL read dependencies to qualify, not
evidence that all Ark/MGE/voting locks share the export account guard. Local JSON FileLock,
process singleton and Discord delivery controls remain separate mechanisms.

### F15: player report completion asks for a second cache confirmation

`player_report_continuation.inspect` can recognise the approved fresh report's completed
cache-only child and then offer `refresh_cache` as a separate step. Cache freshness and
atomic replacement are valuable; another approval of unchanged original intent may not
be. An automatic continuation must bind the exact intended generation, preserve the old
cache on failure and avoid silently consuming changed current SQL output. This is a
continuation design issue, not permission to remove generation checks or blindly click
all refresh actions.

### F16: post-SQL log maintenance extends the global writer guard

The admitted stats writer calls `execute_update_all2_with_log_management`, which consumes
the procedure results and checks its final SUCCESS summary, then processes log-backup
triggers and waits for log usage before returning success. The global snapshot guard is
still owned until the wrapper completes its receipt/capture sequence. Trigger processing
can run up to five backups, wait after successful triggers, and then poll log usage.
The SQL procedure's transaction may already be finished: this is evidence of extended
session guard/reservation lifetime, not proof that Python sleeps keep that SQL transaction
open. Query/backup time adds to the explicit waits; no single total-duration bound is proved.

This is active operational maintenance mixed with telemetry. Preserve genuine headroom
protection, but evaluate moving post-success maintenance after required capture/guard
release or into separately owned maintenance. The protected preflight already uses a
dedicated read-only health path; do not confuse it with the legacy preflight that can
start backups. Existing committed-result recovery above also means this path does not
necessarily turn committed SQL into a failed import.

### F17: equivalent upload routes disagree about committed success

`upload_routes/honor_route.py` records completed ingestion, then sends its success embed
before recording the terminal batch outcome. If that send raises, the outer exception
handler records a failed batch and attempts a red "KVK Honor Import" failure message.
Committed rows and external batch identity remain in the evidence; the database was not
rolled back by the failed notification. The user-facing failure classification is therefore
misleading about the import. Its current test explicitly expects this behaviour:
`test_honor_route_success_embed_exception_fails_audit_terminal_status`.

Weekly Activity already records terminal success first and catches notification exceptions
separately. Player Location records its terminal audit before notifying, although Location,
Honor and Pre-KVK still label the overall audit batch failed when a post-import refresh
raises. A successful import and a failed downstream refresh can both be true; keep the
stage outcomes instead of making one ambiguous failure status stand for both. Honor and
Pre-KVK already preserve import completion when the refresh returns a typed DeliveryResult
with an unknown outcome; the thrown-exception path still differs. Do not remove useful
refresh/delivery failure evidence or describe that exception as a rolled-back import.

Local private history traces the Honor test to `cfa1d400` (29 June), included in #493;
the analogous audit packages are Location #491, Pre-KVK #494 and Weekly Activity #495.
Later `fb096e3d` delivery work adds typed delivery-result handling without eliminating the
older exception path. The six inspected route/service/adapter files are identical to the
retained deployed Bot pin. This is a longstanding non-uniform completion contract, not
evidence that the recent one-second lock correction was reverted. It also shows why a
passing suite alone missed the desired requirement: a test can preserve the wrong
outcome distinction.

Require a shared acceptance matrix across upload, startup and recovery entrypoints:
committed business work remains committed when audit, refresh or notification fails;
failed/unknown delivery is reported independently; neither recheck nor retry repeats the
import to repair presentation. Keep the existing once-only `DL_bot._offload_callable`:
it selects its backend before invocation and does not resubmit after execution fails.
Its `prefer_process` argument is compatibility-only; do not infer process execution from
the upload call sites alone.

| Additional source family | Reviewed distinction | Remaining qualification |
|---|---|---|
| Honor/Pre-KVK importer connections | Use `get_conn_with_retries`; it selects the admitted runtime factory only when that context exists, otherwise the legacy factory | Trace enabled caller/context and budget explicitly. These callers do not all automatically inherit the S11 one-second setting. |
| Location/Forts/Weekly Activity | Own legacy SQL transactions/factories; Weekly Activity's explicit five seconds is connection setup, not a declared statement budget | Validate workload statement/cleanup policy and shared table contention. Preserve actual transaction protection. |
| Import audit DAL/services | Separate trusted audit connections and best-effort exception handling; route awaits audit writes | Error suppression is not a latency budget. Measure/bound audit work and define truthful unavailable-audit reporting without holding up completed business results. No native latency measurement yet. |
| `sheet_importer` helpers | Caller-controlled commit/replace/batch behaviour | Keep per-caller atomicity review; a helper capable of per-batch commits is not proof every caller uses that mode. |

The additional 79 baseline tests passed: Honor, Weekly Activity, Player Location, Location
service, Pre-KVK and once-only DL bot offload. They confirm both the preserved safeguards
and the current inconsistent outcome expectations. Review total is now **367 passing
existing tests**, not 367 tests of a new fix.

### Field retention and report completeness

| Evidence layer | Current source result | Disposition |
|---|---|---|
| Current RecoveryIncident observation | `recovery_dal.observe` replaces EvidenceJson; LastSeenUTC updates on every observation, while revision changes only for changed evidence/state | Keep current state distinct from bounded immutable first failure and meaningful transitions. Do not create a historical event for every poll. |
| Accepted action and execution receipts | Separate action outcomes and exact producer/provider receipts already exist | Reuse authoritative identities/history; avoid a second competing outcome ledger. |
| Pipeline diagnostics | Adapter supplies `input`, `stage_results` and `selected_stage`; report diagnosis allowlist omits these | Add a bounded, redacted projection of useful stage/outcome identity. Do not export raw InputsJson wholesale. |
| Failed versus legacy export closeout | Failed closeout emits `failure_context`; legacy closeout does not emit the same context | Trace to retained original evidence and expose a safe explanation. Missing presentation is not proof underlying evidence was erased. |
| Next-step wording | Several report branches tell the operator to Recheck while automation/accepted work is pending | Explain automatic progress and meaningful escalation. A click should not be required merely to update a successful outcome. |

This closes the initial allowed-action classification, but not every field's origin,
retention/redaction contract or state-specific eligibility. Those remaining decisions are
explicit in G04 and must precede design approval.

### Challenges and limits of the additional verification

An offline model executes the current observer and producer guard methods with explicit
exclusive application-lock semantics: observer first refuses the producer with 51421;
after observer release the producer enters; producer first makes observation defer.
No model locks remain. Account/contract checks are stubbed: this supports the ordering
mechanism, not actual SQL isolation, driver timing or latest-incident attribution.

The existing native `test_observer_first_serializes_checkpoint_without_opposed_row_wait`
already covers observer-first checkpoint overlap and selected retries. The missing case
is new producer entry and authority result settlement, not every observer-first test.
Authority recovery inspection also holds the shared authority RLock while reading SQL
and private evidence, in addition to serial pipe dispatch. Its cost still needs measurement.

Another 212 focused tests passed: 155 covering release policy, export/replacement/rollover
recovery, reports, work budgets, receipt identity, configuration guidance and publication
results; 57 covering UPDATE_ALL2 log management, import outcomes and player continuation.
Together with the earlier 76, those batches cover 288 passing existing tests; the additional
79 for F17 bring the review total to 367. They establish
the current baseline and challenge overbroad claims; they do not prove the proposed
non-interference contract. No native SQL or provider operation was run.

## Continued indirect-caller and retention analysis

This is continuation of the main analysis. It is **not** the separately requested final
outlier sweep. That sweep is now M04a/A12 and must run after the main coverage decisions.

### F18: SQL maintenance can roll back the final reporting stage

The authoritative `dbo.usp_S11CompleteStatsReportsCore` starts the final reporting
transaction when CompletedStage=2 (line 266). It rebuilds reporting outputs, executes
CHECKPOINT (line 518), reads log usage, and inserts a LogBackupTriggerQueue signal
(line 557), before writing the exact completion/continuation receipts and committing
(line 613). The CHECKPOINT and signal insertion are not independently contained by a
best-effort error boundary. An error there reaches the outer rollback, so operational
maintenance can prevent that reporting stage from committing. Earlier import/report
stages remain committed; this is not a rollback of the whole imported scan.

This differs from F16: F16 is Python maintenance after SQL success while the global
session guard remains held; F18 is SQL-side maintenance before the reporting transaction
commits. Keep exact completion receipts and their atomic relationship to the data. Review
whether CHECKPOINT and backup scheduling belong in that transaction at all. Moving them
requires a reliable separate maintenance policy, not pretending they succeeded.

There is useful existing error isolation: UPDATE_ALL2 rolls back before its ErrorAudit
write, catches logging errors and rethrows the original failure. Preserve that pattern.
Its reporting continuation also protects against replaying already committed stages.
The native continuation fixture compiles the unchanged procedure but replaces large
business/maintenance spans for its transactional fault cases. It deliberately avoids
checkpointing its host database. Those tests do not qualify real maintenance contention
or signal-queue failure. No native SQL test was executed in this review.

### F19: notification capacity is a business-admission dependency

`processing_pipeline.handle_file_processing` refuses to start an import when managed
notification registration fails. `NotificationStore` uses a single JSON journal and
five-second file lock, rejects journals over 4 MiB, and rejects creation at 256 retained
runs after pruning closed history down to 127. This makes notification bookkeeping
capacity/availability a gate on new business work. The existing test
`test_registration_failure_stops_before_prompt_or_import` explicitly verifies that policy.

Do not overstate the gap: `stats_alerts.processing_notifications.observe_notifications`
already closes eligible runs automatically after exact terminal/delivery evidence;
`create` already prunes closed records. Uncertain exports and unresolved notification
components correctly remain retained. The issue is the coupling of those retained
notification cases to every future import, not the absence of any automatic closure.

Separate essential business identity/receipt persistence from delivery tracking in the
design. Preserve send-once evidence and uncertain outcomes. Do not delete old unresolved
records by age or simply bypass registration when business identity is also unavailable.
Decide whether unavailable presentation tracking should degrade notifications while
durable business processing remains available, and specify bounded archival/capacity
handling. It is not justified to require manual dismissal of irrelevant old notifications
merely to admit unrelated new work.

### F20: a failed cache observation leaves its own file lock behind

`services/player_stats_startup._verify_completion` takes the same sentinel lock used by
the cache writer, reads/parses up to 64 MiB and compares the saved payload with the
original result. A mismatch, invalid JSON or read failure raises inside that lock.
`file_utils.acquire_lock` closes the descriptor in its finally block but unlinks the
sentinel only after normal generator completion. A thrown body exception skips unlink.
The next cache writer then sees the sentinel and can time out (default five seconds).

An isolated experiment executed the current function bodies with injected file paths,
a temporary cache and a scaled 20 ms admission deadline. Matching verification removed
the lock. Mismatched verification raised `startup_cache_readback_differs`, left the lock
file present and caused the next writer to time out. It also executed the existing
tracked-view wrapper with a body exception: that wrapper removed its lock correctly.
No application/config imports, SQL, provider calls or real cache paths were used in the
successful experiment. Initial direct-module loading required application configuration,
so it was replaced with isolated source bodies rather than reading production settings.

This has a precise historical counterpart. Private #688 introduced `tracker_lock` in
`services/tracked_view_store.py`; its comment explicitly identifies the shared helper's
exception-cleanup behaviour. The common helper still traces to `b4a37c73` (2025).
The startup verifier traces to `d0e5732c`; it calls the helper directly. The tracked-view
fix remains present, but its protection was scoped to that wrapper and did not repair
the shared contract for other callers. Existing startup tests check failed readback and
unchanged cache bytes, but do not assert lock cleanup or a subsequent writer's admission.
This is evidence of a missed shared-helper/cross-caller obligation, not merely a theory
that a previous fix was reverted.

| Direct caller | Current distinction | Scope/disposition |
|---|---|---|
| `services/player_stats_startup.py` | Observer can raise while holding writer's sentinel | Fix shared cleanup contract and reduce observation lock duration; preserve original-generation evidence. Treat superseded/unavailable readback separately from failed production. |
| `player_stats_cache.py` | Ordinary builder and guided publisher use the helper; unhandled write/validation errors can escape | Include all direct writer bodies in exception/cancellation/ownership qualification; preserve existing cache on failure. |
| `ark/team_state.py`, `ark/state/ark_state.py` | JSON persistence directly uses the same helper | Include shared-helper regression coverage here; Ark domain/lifecycle redesign remains the next P1 phase. |
| `services/tracked_view_store.py` | Wrapper forces normal generator exit during body exception; existing cleanup test | Preserve proven cleanup and assess consolidation only after the common contract is corrected. |
| `registry/dal/governor_session_lock_dal.py` | Unrelated function with the same name, using SQL ownership | Exclude from this file-lock defect; do not remove its ownership checks based on a name match. |

The observer also holds a writer lock during JSON parsing/comparison; its cost is not yet
measured. Profile cache publication uses a different design: readers retain an immutable
dictionary reference under a short state lock and copy outside it. Keep that existing
pattern. A stale/mismatched observation must not itself strand the cache or imply that a
previously completed SQL producer failed. No live incident attribution is claimed.

### Retention and useful evidence: source-level disposition

| Source of facts | Current lifetime and consumer | Necessary retained evidence / disposition |
|---|---|---|
| ExportJob.ProvenanceJson | `fail` preserves first_failure using setdefault; updates latest_failure; safe-retry history prevents inventing a new original fault | Keep original failure and distinct later failures/decisions. Existing bounded diagnostics exclude arbitrary exception prose. Do not replace this with one incident per poll. |
| Export provider request/event and attempt receipts | Exact request, execution and acknowledgement history supports settlement/no replay | Keep identities, stage/outcome, recorded response evidence and closure/proof links. Presentation may be summarised; these facts must not be discarded because an incident turns green. |
| StatsImportExecution / reporting continuation | State/scan/counter and SQL error number/procedure/line survive independently of the incident summary | Keep committed stage and resolution distinct from error history. These are correctness receipts, not optional logging. Missing historical exception prose remains missing. |
| Capture preparation and refusal records | Original intent, configuration/registration hashes, ownership and current blocker; capture context often says original_fault=not_recorded | Preserve known original facts and state why evidence is absent. A current refusal is not proof of the original import outcome or blocking owner. |
| RecoveryIncident | One mutable observation per scoped source; revision and FirstSeen/LastSeen, but no immutable failure-history column in its SQL definition | Use as current-state projection. Reuse authoritative failure/receipt records, with bounded meaningful transitions where those records are insufficient. LastSeen is not completion time. |
| RecoveryAction | One accepted action per incident revision; actor/reason/input and later result/state | Preserve accepted intent and its outcome. Repeated viewing should not create actions or become a prerequisite for reconciliation. Raw guided inputs are not report payloads. |
| ProcessingPipelineStage | Mutable stage evidence keyed by exact operation; reports currently omit useful stage fields | Export bounded stage name/state, exact operation identity and result/receipt references. Omit raw input documents, credentials, SQL text and provider payloads. |
| ImportAuditBatch/Phase | Separate phase and aggregate records; F17 shows aggregate status can misrepresent completed ingestion | Preserve ingest commit, refresh and delivery separately, with useful failure codes and stage timing. Audit unavailability must not retroactively change a known mutation result. |
| Notification journal | Bounded retained runs, exact send receipts, automatic closure and closed-history pruning | Keep unresolved sends and links to business receipts. Archive/summarise closed history proportionately; separate capacity from business admission (F19). |
| Recovery health/admission diagnostics | In-memory latest/failed cycle and bounded 32-entry admission deque; restart loses these details | Useful low-cost diagnostics, not durable business history or blocker proof. Persist only meaningful outage transitions if required; avoid durable per-poll logging. |
| Recovery report | Reads saved scoped observations, paginates with byte limits; does not perform recovery | Preserve this passive model. Clearly label incomplete/non-transactional coverage and expose safe original/latest failure and exact stage references. Do not expand to arbitrary stored JSON. |

A retained event should explain a changed outcome, a distinct failure, an accepted decision
or an unresolved condition requiring action. Ordinary waiting and repeated identical
checks belong in bounded aggregate metrics. The S2 packet must choose concrete retention
and capacity limits, safe projections and retry eligibility; this table is the source-backed
analysis, not a schema migration or permission to expire uncertain work.

### Continued validation and remaining analysis

Another 165 focused tests passed for notification policy/DAL, startup reconciliation,
profile ownership, player startup, export/recovery failure diagnostics and import-audit
DAL. The review's existing-test total is now **532**. The isolated cache-lock experiment
is separate from that count. The native report-continuation fixture was inspected only.
Six additional Bot files match the retained deployed Bot pin, and the reporting SQL
procedure matches the retained SQL pin; these are source comparisons, not live health.

Startup reconciliation still justifies exact predecessor termination, ownership and
stream-closure checks before adopting a process session. It does not replay jobs or
release held resources. Reporting input/row-shape/identity checks protect actual data
publication and are different from monitoring reads. Their duplication and cost should
be reviewed, but removing them solely because they are called checks is not justified.

G01 still needs the remaining admin/scheduled/conditional dispatch and transitive SQL
dependency dispositions. G04 now has source-level action and evidence-lifetime coverage;
concrete per-state automation eligibility, redacted projections and retention/capacity
choices belong in the S2 design packet. M04a must then perform the final outlier sweep
from a fresh inventory of entrypoints and sinks. Do not count the discoveries above as
completion of that separate gate.

## Further indirect dispatch and SQL dependency review

This is continued main analysis, not the separate M04a final sweep. An offline candidate
graph follows 12 explicit SQL roots through 51 procedure/view/function definitions and
161 table references. Roots include stats import/report, player reporting, configuration,
all-player KVK intake, post-import statistics, location import/replace and rally import.
The graph is retained as `sql-dependency-candidates.csv` and `sql-dependency-review.json`
in the private review evidence folder. It is a navigation aid, not proof that every edge
or every SQL object has been reviewed.

The seven unresolved lexical names were checked against source. `dbo.as` and `dbo.the`
are parser artifacts from `EXECUTE AS` and text; `dbo.master` is a multipart-name artifact;
`sp_executesql`, `sp_updatestats` and `master.dbo.xp_cmdshell` are system execution edges,
not missing application procedures. `dbo.latest_t4` is a truncated bracketed identifier:
`dbo.[LATEST_T4&T5_KILLS]` exists in `dbo.LATEST_T4_T5_KILLS.Table.sql`. The custody/shell
and dynamic execution edges still need their own semantic dispositions; resolving a name
does not qualify its behaviour. Dynamic target/output table creation is visible in
`sp_Prep_TargetTable`, `sp_Prep_ExcelOutputTable` and `sp_Prep_ExcelExportTable`; it cannot
be excluded merely because a literal object-reference extractor omits generated names.

### F21: configuration publication includes conditional maintenance and performance logging

Source chain: `proc_config_import.py:1123` calls the typed publisher, then commits at
line 1124. `dbo.sp_TARGETS_MASTER` requires one active caller transaction for an atomic
configuration publication (line 35). It acquires the session delta-preprocessing mutex
(line 117), calls `CREATE_DELTA_TABLES` (line 130), then releases its acquisition.
The child commits its own nested transaction and releases its own mutex acquisition
before its maintenance block; that does not end the parent's transaction or release the
parent's separate mutex acquisition. Consequently, the maintenance remains inside the
configuration caller's commit/lock lifetime, even though a standalone child invocation
has a different lifetime.

`CREATE_DELTA_TABLES` conditionally runs statistics updates for 13 tables, including
`kingdomscandata4`, examines index fragmentation, and may rebuild an index with
`ONLINE = OFF` or reorganize it. Eligibility includes a missing previous maintenance
record, seven days, or 5,000 rows; the no-new-delta-rows early return skips this block.
This is not a claim that maintenance runs on every configuration import. Individual
index-operation errors are already caught and printed. Statistics updates, the
fragmentation query, and the final `DeltaProcessingLog` insert have no equivalent local
best-effort boundary. Their errors can propagate to the enclosing configuration publisher;
their elapsed time can extend the publication's transaction and mutex ownership.

This is a third distinct placement of maintenance, alongside Python post-import work
under the global writer guard (F16) and maintenance inside final report completion (F18).
The design should assess these together: retain necessary data calculation and atomic
completion receipts, justify headroom/maintenance controls, and separate ancillary work
that should neither prevent business completion nor extend critical ownership.
`DeltaProcessingLog` is performance/maintenance history, not the exact configuration
completion receipt; its necessity and failure policy must be assessed separately.

Historical cross-check: statistics/logging code traces to January 2026 (`c07058f`, with
later additions); serialization was strengthened in August (`758f456`), and the atomic
configuration entry contract in October (`f5ecc3e`). Both inspected procedures are
unchanged between the retained deployed SQL pin and the current checkout. This supports
a retained dependency/coverage gap, not evidence that a recent patch removed a fix.
`tests/test_configuration_targets_contract_sql.py:33` explicitly substitutes a small
nested-transaction delta stub. That fixture is useful for the atomic entry contract but
does not exercise real maintenance, its failure, or its producer/observer overlap.
No native SQL operation was run and no latest-production blocker is attributed to F21.

### F22: publication maintenance also sits inside import and report transactions

The dependency scan was challenged against actual maintenance statements, not only
procedure names. It finds additional instances of the same design question:

| Source | Boundary and disposition |
|---|---|
| `SP_Stats_for_Upload:418` | `UPDATE STATISTICS STATS_FOR_UPLOAD WITH FULLSCAN` precedes commit while the transaction owns both the KS4 import mutex and the stats-publication mutex. Failure enters the procedure's rollback/savepoint handler. Its data provenance/row/identity checks protect publication; optimizer statistics require separate justification. This extends F01 beyond its timeout mismatch. |
| `sp_ExcelOutput_ByKVK:668` | Full statistics scan follows output/index creation but precedes view publication, exact final-report receipt and commit. Necessary output schema/index requirements must be distinguished from optimizer maintenance; do not remove all index creation as if it were incidental. |
| `UPDATE_ALL2:184,293,301,314,318` | Sampled statistics and conditional KS4 index reorganize/rebuild occur before the Phase A import receipt/continuation and commit at line 348. These are inside the import transaction, unlike F16's later Python waits. Errors here can prevent the import commit; errors after that commit cannot undo it. |
| `usp_S11CompleteStatsReportsCore:98,376,518,557` | Pre-report headroom CHECKPOINT plus diagnostic audit, full statistics on dashboard output, final CHECKPOINT and backup-signal insertion extend F18's maintenance inventory. Preserve stage-specific commit/continuation evidence; headroom controls may be useful but need an explicit cost/failure policy. |
| `usp_update_stats:19` | Explicit post-import maintenance calls system `sp_updatestats`. Its purpose is maintenance; whether callers should require it for overall business success is a separate policy question. |

The first three definitions are unchanged from the retained deployed SQL pin. Blame
places the inspected statements in August (`3fa7425`, stats upload) and January
(`c2c53a7`, KVK output; `aa1a1ec`, import index maintenance). These are retained mechanisms,
not evidence that the recent timeout/observer patches regressed them. Actual duration,
failure frequency and necessity of each statement remain qualification/design questions.
The real report-continuation fixture replaces `SP_Stats_for_Upload` with a stage probe in
its simulated continuation body; it does not establish the full-scan failure behaviour.
Private `sql-maintenance-candidates.json` records the search; comments and the string
`atomic_checkpoint` are lexical hits, not additional maintenance operations.

The shared acceptance matrix must therefore include import Phase A, configuration,
player report, KVK output, final reporting and explicit post-maintenance. Removing a
single CHECKPOINT or raising a single timeout would leave this family unresolved.

### Indirect callers: safeguards retained and remaining scope

| Inspected path | Source-backed disposition |
|---|---|
| Admin Sheets export -> `run_all_exports` -> `bound_runtime` -> `caller_scope` | Keep physical-work ownership. The synchronous decorator acquires runtime ownership inside the worker; `RuntimeLifetime.owned` retains references through completion. An outer `to_thread` alone is insufficient evidence of abandoned ownership. |
| Protected exporter return -> admin/pipeline | Keep `ExportSubmission`'s explicit queued acknowledgment. Legacy unpacking yields false plus a queued/pending message; the admin labels it queued, and the pipeline has structured identity. Enqueue is not represented as provider success. |
| Configuration offload and worker result decoding | Keep protected runtime's drained in-process route and typed `(bool, report)` result validation. An unavailable process result returns unknown/failure evidence without rerunning the importer. Worker transport success is not substituted for the business result. |
| Protected runtime unavailable versus coordination disabled | `_writer_runtime` fails closed when enabled coordination lacks a verified context. The legacy exporter/retry path is a separate disabled-coordination branch; it is not a silent fallback from failed protected admission. Its compatibility policy remains a design/coverage question. |
| Explicit post-stats worker | `usp_update_stats` is intentional maintenance, not passive observation. The helper sets its execution policy, consumes result sets and propagates errors. Review where callers make it a business prerequisite rather than treating every statistics operation as an observer defect. |
| `scripts/retry_phase52_stats_import.py` | Explicit operator recovery, not a normal startup job. It validates immutable filename/manifest parameters and distinguishes SQL success from failed post-SQL stages. Preserve that distinction; include its cache deadline and mandatory post-stats policy in the shared continuation design. This script was read, never executed. |
| `verify_cityhalllevel_cache.py` | Manual diagnostic actively refreshes a process-local name snapshot and then checks data coverage; it is not a passive health display. Keep its explicit diagnostic classification. It was not executed. |
| SQL claim/import/archive/hash chain | Keep filename/digest binding, before/after bulk-import integrity, exact committed receipts and refusal to overwrite a conflicting archive. Claim movement/hash occurs between short claim transactions; archive hashing/move/reconciliation owns a separate transaction-scoped import mutex. `UPDATE_ALL2` commits import before invoking archive; archive refuses an enclosing transaction. Archive failure cannot roll back that committed import. Error-ledger writes run after rollback and preserve the original error. Qualify custody cost/overlap; these checks protect real file ownership and duplicate prevention rather than status presentation. |

Four existing suites passed in this continuation: runtime composition, configuration
offload, pipeline step/normalization and Sheets module: **385 tests**. This is a separate
batch, not an asserted increase of 385 distinct cases over the earlier 532 (suite overlap
has not been reconciled). They support preserved behaviour; they do not test the real
configuration maintenance boundary or qualify proposed corrections. The only warning
was the dependency's future Python-version support notice.

G01's remaining work is now explicit: reconcile the historical per-file candidate rows
with reviewed findings/exclusions; finish the remaining dynamic SQL dispositions (the
claim/import/archive custody chain now has an explicit lifetime/integrity disposition);
finish conditional/manual dispatch dispositions; record which unrelated
domain paths are outside this phase while retaining shared-helper obligations. The
[coverage ledger](Startup%20Import%20Export%20Reliability%20-%20Coverage%20-%202026-11-02.md)
now records 68 scoped-edge dispositions, 17 policy-only mappings and 286 pending evidence
reconciliations. These are not whole-module approvals or a percentage of completion.
After the remaining analysis, perform M04a/A12 independently.

## Conditional calendar import and dynamic publication follow-through

### F23: calendar audit completion can relabel committed data as failed

`event_calendar/sheets_sync.py:569` inserts `EventSyncLog` before fetching or writing any
business inputs. Failure of that insert escapes without starting the sync. After all
three input tables are upserted and committed (line 598), `_finish_sync_log` runs at
line 612 inside the same broad exception handler as fetch/parse/upsert. If that separate
log update fails, the handler constructs `ok=False`, `failed_fetch_or_validate`, and
zero default row counts. It then attempts to overwrite the same log row with failure.
`CalendarService.refresh_pipeline` treats this as sync failure and stops before generation
and cache publication. This is a concrete path from ancillary logging failure to an
incorrect business result and stalled continuation. It belongs to the F17/F19 outcome
family rather than requiring a calendar-domain redesign.

An isolated experiment executes the current AST-extracted function with fake connection,
fetch and audit dependencies. Normal success makes one commit and returns success. An
injected audit-completion error still makes that commit, then returns failure and zero
counts; the audit attempts are success followed by failed-fetch/validate. An audit-start
failure performs no fetch or business write. This proves the code path, not a live
incident or SQL fault frequency. The authoritative `EventSyncLog` definition contains
the status/count fields used here; it is distinct from the three input tables.

### F24: calendar deadlines can release ownership before physical work finishes

The startup/daily pinned-calendar path (`bot_instance.py:179`) and admin full refresh
hold the `calendar_refresh` operation lock around `refresh_pipeline`. Each stage is
wrapped in `asyncio.wait_for` (`event_calendar/service.py:487`); sync, generation and
publication use `asyncio.to_thread`. On timeout, cancelling the awaiter does not drain
the worker. The pipeline can return failure and release the caller's lock while the
worker still writes. A later operator/scheduled call can obtain that lock before the
previous work finishes. This differs from F08, where the worker is drained but its
completed result is discarded.

The offline experiment runs the actual `refresh` and `_run_stage_with_policy` bodies
with a blocked fake worker and a scaled 30 ms policy. It observes timeout and successful
second lock admission while the first worker remains unfinished, then releases and waits
for that worker to finish. It does not start a second mutation, use SQL or call Sheets.
The same caller structure exists for generation/publication; their actual filesystem/SQL
operations were not exercised. Qualify those stages separately in implementation.

Preserve `allow_timeout_retry=False`: it prevents an immediate retry within that stage.
It does not retain ownership until the worker finishes. The existing timeout test raises
`TimeoutError` directly from a fake coroutine and checks one attempt; it cannot prove
thread lifetime or exclusion of the next caller. The sync happy-path test replaces audit
completion with a no-op. These are specific acceptance gaps, not reasons to discard the
tests' narrower protections.

Private evidence: `reproduce_calendar_boundaries.py`, `calendar-boundary-results.json`
and `calendar-source-comparison.json`. Four compared sources (calendar sync/service/
scheduler and shared sheet importer) match the retained deployed Bot pin. Private blame
attributes audit completion to `c1215b49` (6 March) and the stage deadline to `5d12c5c5`
(8 March). No recent reversion is demonstrated. Four existing suites for calendar sync,
pipeline, service and sheet import passed **28 tests**; no unique aggregate with prior
batches is claimed.

### Counter-checks and explicit dispositions

| Path / suspicion | Reviewed disposition |
|---|---|
| Generated target/output/export tables | `sp_TARGETS_MASTER` calls preparation children inside its publication transaction, propagates child exceptions, checks generated object/rows/identity and bot-facing publication rows, then commits. Keep atomic data/receipt and shape checks; F21/F22 separately challenge maintenance. Dynamic identifiers alone do not prove an unguarded publication. |
| Dashboard rebuild with no eligible tables might reuse old data | Rejected for the reporting caller: it drops `EXCEL_FOR_DASHBOARD` before calling the builder. The builder's no-output return is not proof of successful final publication; downstream use still needs the output. Keep empty/absent-output qualification without inventing a stale-success incident. |
| Shared `executemany_batched` suppresses commit exceptions | Reproduced with `commit_per_batch=True` for single/multiple batches. Inspected Pre-KVK and configuration callsites use caller-owned commits; even the non-transactional staging/upsert helper passes false and its importer checks the final commit. Record the misleading optional contract for shared-helper design, not as the cause of protected import failures. No production-defect ID assigned. |
| Event-calendar scope | Includes startup/daily/admin import, generation and cache-publication ownership/outcomes. Event rules, board lifecycle and reminder redesign remain separate P1 work. Shared reliability fixes must cover this caller family without reopening accepted domain operations. |

The coverage ledger replaces blanket historical placeholders with explicit evidence links
and lists inspected paths outside the old seed. No automatic exclusion uses directory
name or lack of a lexical lock hit. G01 remains open; this is not the final outlier sweep.

## Cache consumers, auxiliary publication and alternate connections

### F25: secondary cache output can misreport an already-published primary cache

`event_calendar/cache_publisher.py:139-140` replaces the runtime calendar JSON, then
replaces `event_type_index.json`. Each file uses a temporary file and `os.replace`, but
the pair is not one publication. If the second write fails, the broad handler returns
`failed_publish`, `ok=False`, and zero `events_written` even though the first replacement
is already visible. The runtime reader (`event_calendar/runtime_cache.py`) reads the
primary calendar file. A source search found the index writer and tests but no production
Python reader of the index. This does not establish that no external/manual consumer exists.

The isolated current-body experiment uses temporary files and the actual atomic writer:
normal publication makes both generations new; injected second-write failure leaves the
primary new and the index old while returning failed/zero. No production cache is touched.
Existing tests check two-file success and preserving an existing cache on empty input,
but do not exercise partial publication. The two-write sequence traces to private
`d0ac3e4a` (6 March), and current source matches the retained deployed revision.

Design starts with necessity: establish whether the index has a valuable consumer before
adding a two-file transaction protocol or additional verification. If optional, it must
not redefine successful primary publication as failure; if both are required, define
coherent publication and truthful partial outcome. Preserve the meaningful distinction
between SQL generation, main-cache publication and any auxiliary artifact. This extends
the F17/F23 family; it is not permission to rerun SQL after a cache bookkeeping failure.

### F26: profile connection fallback catches execution failure as well as import failure

`stats/profile_cache_repository.py:_connect` wraps both importing and invoking
`get_conn_with_retries` in `except Exception`. Therefore an available helper that exhausts
its connection policy still causes a direct `constants._conn()` attempt, with the debug
message saying the helper is unavailable. The isolated current-body experiment injects
a connection failure and observes the second factory return successfully; no SQL opens.

The actual helper uses `producer_connection(_conn)` unless operational mode is requested.
Without a runtime context, the fallback repeats the legacy connection factory after the
retry policy failed. With an admitted runtime context, it can select the legacy factory
after failure of the runtime's connection factory. This is conditional policy drift,
not proof that ordinary startup uses a different principal or that any permission was
bypassed. Connection setup is not a replay of a business mutation. Review this under
F01/A04's complete connection/timeout policy; preserve the original failure and do not
silently reinterpret operational failure as import unavailability.

History double-check: the adapter extraction is private `2f0cfe61` (25 October), but its
parent `profile_cache.py` already contains the same broad fallback body. This was carried
forward, not shown to have been introduced by that extraction. It is unchanged against
the retained deployed revision. Current profile tests inject connection/build adapters;
their ownership guarantees do not qualify this real connection-selection branch.

### Safeguards and bounded review dispositions

| Inspected family | Value / disposition |
|---|---|
| Event cache service and loader adapters | Keep one refresh owner, shielded observer waits, joined callers and explicit pending. The loader group's actual deadline cancels/drains original workers; adapter cancellation also drains. Persistence failure can produce `refreshed_memory_only`, distinct from failed fetch. This is a reusable existing contrast to F24, not another missing ownership mechanism. |
| Profile and name cache publication | Keep immutable snapshot replacement, generation/revision binding, owned thread drain, preserved last-known-good data and distinct memory/disk outcomes. Profile readers capture the snapshot reference under a short state lock and copy/project outside it. Name verification checks the original generation without another SQL query. |
| Profile startup readback | Does not query SQL or take the cache writer's lock. It bounds the disk read to 64 MiB and checks original generation/time/content. Full snapshot copy/serialization cost and expected supersession classification belong in A10/A07; do not infer contention solely from the existence of verification. |
| Registry TTL cache | Status reads local metadata; invalidated snapshots are not offered as stale fallback. Full dictionary reads/writes deep-copy under the local cache lock, a cost to measure for realistic sizes, not a demonstrated SQL incident or reason to clear a lock. |
| Admission diagnostics | Bounded 32-record in-memory deque; passive report reads add no SQL/provider probe. Identity explicitly says requesting session, not blocker. Keep that evidence boundary and proportional retention; these records do not prove the blocking owner. |
| Calendar generation | Inputs are read and instances replaced in a SQL transaction, followed by explicit commit. Keep that atomic data boundary; F24 still applies to the outer waiting/ownership policy. It has no equivalent post-commit audit-log update to F23. |
| Startup gate and event scheduler bundle | `claim_startup_once` is process-local admission/deduplication, not completion evidence. Scheduler members retain entered task ownership beyond observation deadlines; failures before registration get bounded retries, while uncertain entered work is not replayed. Keep these distinct from SQL lock ownership. |
| Recovery monitor notifications | Inspection and notification outcomes are recorded separately; delivery failure does not invalidate successful SQL inspection. Existing F04 still requires separating active recovery effects from passive observation. |
| Command-sync startup metadata | Local signatures may be saved after a timed-out/skipped remote sync; result flags separately record sync success/timeout. The local cache is not proof of Discord delivery. Its future skip/reconciliation contract is a startup-adjacent design question; no missing-command production incident or automatic repair is asserted here. |

Private `reproduce_cache_publication_boundaries.py` and `cache-publication-boundary-results.json`
record F25/F26. Twelve inspected cache/adapter sources match the retained Bot pin in
`cache-followthrough-comparison.json`. **72 existing tests** passed across calendar
publication, event-cache service, profile ownership and registry cache. This is a separate
batch, with no unique aggregate claim. These tests preserve valuable existing guarantees;
the isolated experiments demonstrate gaps outside their current assertions.

The coverage ledger advances to 68 reviewed scoped edges, 17 action-policy mappings and
286 pending evidence reconciliations. These numbers record traceability, not full-module
qualification. Source review/coverage reconciliation continues; M04a remains unstarted.

## Recovery snapshot, contention and check-value follow-through

This pass extends F03/F04/F09/F10 across the recovery DALs. A method named `inspect` or
`snapshot` does not establish a passive SQL read. Conversely, these locks often protect
an exact action-time comparison; removing them from mutations would discard useful safety.
The matrix records the inspected edges, not approval of each entire module.

| Source / edge | Mechanism and disposition |
|---|---|
| `all_kvk_capture_recovery_dal.inspect`; inherited player-report inspection | Takes the global output guard through `_observe_idle`, then account admission and locked preparation/resource reads; player reports also read execution with update/hold hints. Extends F09's observer-first refusal risk. Keep exact capture/ownership checks at mutation time; redesign ordinary observations. |
| `config_preparation_recovery_dal._snapshot` | Account then sorted resource mutexes, server/database identity and locked preparation/resource/stream/request evidence. Settlement repeats the snapshot and compares the reviewed token. Preserve action-time identity/consistency; F10 challenges repeating that full exclusion path just to display state. |
| `queue_admission_recovery_dal._snapshot` | Account mutex, preparation update/hold read and four locked dependency counts. Withdrawal revalidates the snapshot. The absence checks are valuable before withdrawal; ordinary status should not compete through the same full validation transaction. |
| `unowned_sql_hold_dal` | Discovery already reads the blocked marker cheaply before performing a detailed snapshot. Action review locks account/resource and checks producers, streams and all ownership. Preserve this cheap-discovery pattern and never release solely because a hold is old. |
| `import_capture_recovery_dal.session`; historical import retirement | Producer/session guards explicitly release in reverse order, including pooled connections; refusal is already `SourceBusy`. Historical retirement preserves an unproven SQL outcome and requires exact reviewed evidence. Keep those guarantees and the genuine business decision. |
| `failed_export_closeout_dal`; `stranded_export_recovery_dal` | Inspection takes account admission and locked job, member, resource, attempt and stream snapshots. Stranded settlement rechecks the reviewed snapshot before changing state. Separate passive projection from mutation-time comparison without weakening the latter. |
| `export_replacement_verification_dal`, `export_replacement_dal`, `export_evidence_catalog_dal` | Inspected read methods use scoped SELECTs without explicit application mutexes/update hints; mutations call separate procedures and evidence copies retain hash agreement. Reusable separation, not proof of zero SQL blocking or free queries. |
| `recovery_dal.observe`, `check_failed`; `recovery_backlog_dal` | Observing an existing incident always writes evidence/state/LastSeen, but increments Revision only when meaningful content/state changes. Identical failure diagnostics are skipped. Backlog summaries use aggregate reads; action candidates can request locks separately. Measure repeated write cost and justify freshness requirements without claiming a new incident/revision on every poll. |
| `recovery_execution_guard`, `export_contention`, `core/sql_observation`, shared source transaction | Process-local recovery admission is nonblocking. Selected retries require explicit safe refusal plus acknowledged rollback/close; observations yield rather than repeatedly compete. The ContextVar alone does not change every connection or make a SELECT non-interfering. Keep cleanup certainty and distinguish local scheduling from durable ownership. |
| `export_request_budget`; operator status service/DAL | Pacing reservations commit before waits; refreshed reservations account for later cooldowns. Completion checkpoint failure does not authorize resending. Held authority admission is distinct from an open reservation transaction. The status SQL probe is active work (F11); it is not a passive retained-state read. |

### F27: report-validation contention bypasses the existing waiting classification

`stats_report_continuation_dal._snapshot:53-66` catches every exception from
`usp_S11ValidateStatsReportStage` and raises `SourceConflict`. The SQL validator first
tries the KS4 writer mutex with zero wait and uses error 51961 for refusal. It also uses
51961 for invalid transaction/guard/input/configuration/ownership prerequisites. Thus the
same mapper handles ordinary writer contention and genuine invalidity. A row-lock timeout
raised inside that validation call is also converted to the conflict.

`RecoveryService._inspect` supplies an observation context, but this DAL uses its own
session/explicit transaction path rather than the shared transaction wrapper that turns
cleanly released contention into `ObservationBusy`. The monitor's existing-incident
branch handles `SourceBusy`/`ObservationBusy` as waiting; `SourceConflict` instead records
a failed check, updates its diagnostic and contributes to the failed cycle. This provides
a concrete route by which a later ordinary recheck can succeed without any repair. It
does not prove that every recheck-only incident, or the latest incident, came from here.

The current-body offline experiment returns the incomplete snapshot normally, then injects
writer-refusal, real configuration-conflict and row-timeout responses. All three become
`SourceConflict`, not typed waiting. A second check through the actual diagnostic function
confirms that driver-shaped error codes survive the exception context, even with
`from None`. The loss is control-flow classification, not erasure of every underlying
diagnostic. No SQL, incident store, provider or production worker is invoked.

Counter-checks narrow the finding. The earlier session-guard refusal already raises
`SourceBusy`; it must remain. The native test named
`test_restricted_monitor_contention_retains_sql_code_and_recovers_without_release`
actually exercises `QueueAdmissionDAL.snapshot`, not this validator branch. Another test
preserves changed exception chains without revision churn. Those are useful protections,
but neither tests this report-specific route. Native suites were inspected, not executed.

Private blame locates the broad mapper in `1c68f824` (22 October), merged by Bot #675;
the SQL error contract is `203f90c`, merged by SQL #129. Both are unchanged against the
retained deployed pins. The earlier [coordination family review](../reference/Coordination%20lifecycle%20verification.md)
records typed waiting for live import and busy/changed pipeline snapshots while retaining
partial-report semantics. The missed edge is the report validator's separate exception and
connection path. This supports a retained coverage gap, not a claim that prior fixes vanished.

Design must distinguish verified contention from invalid prerequisites at the SQL/adapter
boundary and preserve acknowledged cleanup before treating it as waiting. Do not make all
51961 errors, all negative lock returns or all `SourceConflict` instances retryable. Keep
exact receipt/configuration checks before continued reporting, skip committed stages and
never repeat the committed import. Extend A02/A03/A05/A08 to the actual report-inspection
branch, with genuine mismatch and cleanup-failure counterexamples.

Private evidence: `reproduce_report_observation_classification.py`,
`report-observation-classification-results.json`, `recovery-followthrough-comparison.json`.
All 26 compared Bot/SQL sources match their retained pins. Six existing unit suites passed
**147 tests** across contention, recovery exclusion, capture, configuration preparation,
backlog and replacement verification. This is a separate batch, not a unique aggregate
or qualification of a fix. The coverage ledger now records 91 reviewed scoped edges,
17 policy mappings and 263 pending evidence reconciliations. G01/M03 remain open;
the separate final outlier sweep has not started.

## Main first-pass completion and fresh scheduled-run evidence

The main first pass now has a recorded disposition for every historical candidate:
**242 reviewed scoped edges and 129 boundary dispositions, 371 unique paths**. The
[coverage ledger](Startup%20Import%20Export%20Reliability%20-%20Coverage%20-%202026-11-02.md)
also lists inspected sources outside that seed. A boundary disposition records the actual
dependencies/store and the shared edge retained in this phase; it is not approval of
every branch in an independent domain. Neither count is a count of defects or tests.
The separate final outlier sweep has **not started**. It must challenge this mapping
against fresh entrypoints/sinks and transitive/dynamic SQL before S1 closes. Native
concurrency, cost, and operational acceptance remain separate qualification work.

### Report 66: one retained export restriction and a new stopped admission

Report 66 was generated at **09:58:56 UTC on 2 November**. It contains 17,722 unique
records: 17,719 resolved and three open, including the overview record. There are two
open operational incidents, not three new failed transactions. Comparison with the
actual Report 65 archive finds four new records for today's pipeline/admission, plus
two older open records now resolved. Reports are nontransactional collections with
different last-checked times; these counts are not a fresh atomic SQL snapshot.

The attached log covers 04:56:23-09:59:09. All **62 structured admission-refused
observations identify the same older export job** and account restriction. They are
not 62 attempted exports and do not identify a SQL blocking session. That restriction
was already present before today's upload arrived. The current source and report
distinguish a durable blocked resource from an application-lock timeout.

| Time / evidence | Supported conclusion | What it does not establish |
|---|---|---|
| 09:21:13-09:21:19 | Fallback staging writes 414 rows, publishes the immutable CSV and completes the Excel/archive steps | Completion of the business SQL import |
| 09:21:23-09:22:25 | SQL-stage preflight waits on the old account restriction, then records confirmed admission refusal after about 61.6 seconds | SQL execution for today's input, a new provider request, or the physical blocking SQL session |
| 09:22:26-09:22:40 | Pipeline stops at SQL failed/unproven; cache, maintenance, configuration and export stages do not run | That the separate old export failed again, or that notification-stage wording proves provider dispatch |
| Report 66, same preparation | Refusal adapter records verified saved-stage cancellation before SQL; queue handoff is resolved; import adapter remains open without a SQL receipt, spool, export job or held resources | Successful import, or permission to release the old export |
| 10:25-10:26 screenshots | Both operational records remain visible after later rechecks; linked admission says resolved/cancelled while parent import still says unproven | New execution, an independently refreshed SQL ownership snapshot, or a second held export lock |

The old export's `closeout_review_required` explanation comes from
`LegacyExportCloseout._proofs`, which uses the same message for several failed
conditions: job/account/owner/fence/registration binding, active account marker, stream
state and purpose, absence of incompatible ownership fields, session principal,
claim version, and equality with a fresh stream read. **The message alone does not
prove that a physical writer is still running.** It also does not prove that the
restriction is safe to lift. Its inspection returns no action when those checks fail.
The retained Report 65 authority diagnostic already records result persistence failing
after response validation (F02); neither today's report nor the screenshots supply the
missing exact current stream/closure facts to determine which predicate now fails.

Practical effect: the old account restriction can continue to refuse exports sharing
that account and the stats admission that depends on it. The open incident list itself
is not the admission gate. Report 66 gives no held resources for the cancelled stats
preparation. Closing that display record would not release the old export. G03 must
identify the precise missing or inconsistent closure fact, with existing exact job,
stream, request and custody evidence, before proposing settlement. Repeated manual
rechecks cannot manufacture a missing receipt. Improving this diagnostic is part of
F05/F13/P04; it must not become another provider mutation or intrusive polling loop.

The report's last completed monitor cycle took **226.781 seconds**, including
187.578 seconds in player-report discovery, 15.125 in stats-import discovery, 10.094 in
private evidence, 8.734 in export-job discovery and 4.313 in configuration-read
continuation. The log records 63 completed cycles ranging from 61.907 to 295.547
seconds. The report says healthy/fresh with 14 waiting and zero failed checks;
11 waits are stats-import 51400 observations and three configuration-attempt 1222
observations. This supports A10 cost/cadence analysis, not attribution of all that
elapsed time to SQL locks or proof of F27 in this run. Websocket lag/disconnects are
concurrent observations without a demonstrated causal link.

Raw identities, attachment hashes and the exact comparison are retained privately in
`report66-evidence.json` and `report66-admission-observations.json`. The two screenshots
are registered in `report66-screenshot-evidence.json`. No live recheck, SQL read,
provider call, lock release, replay or restart was performed for this analysis.

### F28: a verified pre-execution cancellation does not settle every incident projection

`producer_refusal_dal._original_phase` validates the cancellation marker, exact version
and fence increments, no held resources and the previous refused state.
`ProducerRefusalRecovery.inspect` then returns resolved with `saved_stage_cancelled`.
This is useful proof: missing execution evidence alone must never mean cancelled.
However, `ImportRecoveryService.inspect` follows its missing-receipt branch, links to
the refusal adapter and remains unresolved. It does not adopt that verified terminal
disposition. Today's report and later screenshot show both views of the same input.

There is a second defect in the explanation. `capture_context` treats an empty
generation plus no completed execution as unproven, but a nonempty cancellation
marker can fall through to **"The SQL result is retained"** when registration matches.
The isolated experiment executes the current helper body: no receipt/no marker gives
`completion_unproven`; adding a cancellation-shaped document gives the misleading
capture/queue wording. This experiment tests explanatory classification, not the
stronger cancellation validator. The report's resolved refusal supplies the observed
terminal-state evidence.

History is consistent with an integration omission: the generic context branch comes
from `ebfa3df6` (18 October), its wording from `53abc762` (19 October), the verified
cancellation marker from `13194649` (19 October), and the missing-receipt navigation
branch from `ada72368` (17 October). Those selected current files match the retained
deployed pin. This is not evidence of a recent rollback. An adapter-local cancellation
test does not prove every sibling incident converges or tells the same outcome.

Disposition: project the exact validated cancellation into all linked recovery views,
preserving input and refusal history and reporting **cancelled before SQL**, not SQL
success. Do not close arbitrary missing-receipt incidents or release unrelated work.
Acceptance must exercise cancellation -> all linked views -> recheck -> restart ->
report export, with zero further operator actions once the terminal receipt exists.

### F29: a failed Rally attempt can permanently occupy the duplicate-success key

Both daily and all-time functions in `forts_ingest.py` check `IngestionLog` by
`Source` and `FileName`, without checking status or content. On a procedure failure
they roll back, write an `error` log row and commit that diagnostic separately. A later
attempt with the same filename then returns `skipped / duplicate filename` before
running the procedure. The authoritative `dbo.IngestionLog` table has an unconditional
unique key on `(Source, FileName)`, so changing only the SELECT filter would be an
incomplete fix: a later success-log insertion would still collide.

An isolated current-body experiment injects procedure failure before commit. For both
functions the first attempt records one error, and the second skips without another
procedure call. This is not a live SQL reproduction and is not attributed to today's
stats incident. The selected Python source matches the retained deployed pin; the
filename-only guard is present in the oldest retained 2025 history. The existing
`test_forts_ingest` checks the log insert's returned identity, not failed-attempt reuse.

Disposition: separate attempt/failure history from authoritative successful-ingestion
identity, including exact content and uncertain-commit handling. Preserve successful
duplicate protection; do not propose automatic retry based on an exception alone.
Validate the SQL uniqueness/migration implications and daily/all-time symmetry together.
Rally's date replacement application lock is 10 seconds and caller-transaction-owned;
it is not another occurrence of the one-second authority admission setting.

### F30: queue CSV logging can prevent a staged upload from reaching its processor

`bot_helpers.queue_worker` awaits `append_csv_line` at the start of its staged callback,
before registering the active job or calling `handle_file_processing`. The helper does
not catch file-open/write failure. `fallback_upload_staging_service` holds the local
processing lock around that callback and cleans up temporary staging in `finally`;
the outer queue worker logs the exception and acknowledges the queue item. This is
distinct from the durable immutable import-file receipt used later in processing.

An isolated execution of the current nested callback with a CSV permission error
propagates the error and makes zero business-processing calls. No user file was staged
or deleted in the experiment. The CSV-before-work dependency dates to retained 2025
code and survives the August 2026 staging refactor; current selected sources match the
deployed pin. Normal staging/worker tests pass, but do not exercise this fault boundary.

Disposition: establish the CSV's actual value and make any required durable custody
receipt explicit. Optional download logging should not prevent a safely staged import;
logging failure must not be described as SQL or download failure. Preserve processing
serialization, input custody, duplicate protection and acknowledgement semantics.

### Remaining family dispositions and safeguards

These are the B01-B15 reasons attached to individual paths in the coverage ledger.
They deliberately state what was inspected and what still needs qualification.

| Boundary | Source-backed disposition | Remaining qualification / limit |
|---|---|---|
| B01 recovery continuations and groups | Cancellation/withdrawal, exact child lineage and saved intent are distinct from completion. Historical group approval serializes its own scope and retains selected identities. Unreceipted closure rejects provider streams and preserves unknown SQL outcome. | F28 projection consistency; legitimate business decisions stay explicit. Group approval lock failure is not proof of business failure. |
| B02 export/provider/replacement | Provider calls occur between DAL transactions; completed proof workers retain/drain their physical thread. Startup reconciliation uses exact old session/stream custody, not age alone. Containment and closeout inspections repeatedly take account/resource snapshots. | F02/F10/F12 scheduling and settlement design; exact proof checks stay at mutation/closure boundaries. SQL log headroom is a capacity prerequisite, not merely optional telemetry. |
| B03 KVK source and rollover | Immutable publication/vector identities bind reads and exports. Destination serialization explicitly commits before yielding to provider work while retaining a session application lock. History capture freezes the selected intent; pool mutation orders account/resources/pool locks. | F14 ordinary metadata reads still share writer-style locks. Receipt/hash checks protect selection and duplicate delivery; native overlap and original P0 rollover acceptance remain open. |
| B04 upload/audit/custody | Generic import-audit wrappers catch their own failures; Rally route separates backup/notification problems from ingestion. Immutable stats claims require exact filename/hash/receipt. KVK negative-count diagnostics execute after its business/completion commit and can still raise before returning success. | F17 extends to post-commit KVK diagnostics; retain its completion evidence instead of replaying ingestion. F29/F30 require shared outcome and attempt-history tests. |
| B05 delivery/observation | Entered/sending/accepted receipts protect duplicate delivery. CSV success projection follows durable accepted state. Event delivery and processing journals have locks and size bounds; notification DAL reads exact lineage without a provider call. | F19 retention/admission cost, capacity and degraded-presentation policy. Keep unknown-send evidence; report fewer useful incidents rather than erase uncertainty. |
| B06 readers, downloads and cache metadata | Personal download worker cleanup waits for physical completion; profile/player reads close connections. Personal-stats `wait_for(to_thread)` can end its semaphore scope before the physical read finishes. Shared `stats_alerts.db` async wrappers also catch worker failure before fallback offload. Target cache uses generation/token fencing and separate metadata publication. | Extend F24/F26 tests to read-only resource overlap and fallback cause preservation; no claim of committed mutation replay from the read-wrapper trace alone. Include primary-cache/coordination-file outcome in A05; ordinary reads can still consume or contend for SQL resources. |
| B07 launch, teardown and release | Task-registry drain preserves live children after an observation deadline. Singleton/process identity is separate from SQL account ownership. Release/readiness tools use pinned receipts and retain an unfinished release rather than infer success from timeout. | Startup F01/F08 and authority budgets remain in scope. Existing accepted deployment is not repeated for evidence. |
| B08 manual rehearsals | SQL account tool renders grants; rehearsal and smoke entrypoints explicitly use disposable fixtures/identity checks. They are not ordinary scheduled producers. | Exclude fixture execution from this evidence-only review; inspect dynamic/manual aliases again in the final sweep. |
| B09 authority SQL | Request-event append owns its short transaction; legacy closeout, replacement activation and verification require the exact caller transaction. Stream containment has its own explicit outer-transaction contract. Admission gates check role, identity/version and exact resources. | Do not flatten zero-wait gates, one-second Python admission, execution deadlines and observer budgets into one timeout. Different SQL error families need typed cause-specific treatment. |
| B10 business SQL and receipts | Import/report/date-snapshot completion remains tied to business data. Stats execution session ownership, post-import maintenance ownership, file custody and archive transactions have different lifetimes. | F18/F21/F22 actual maintenance cost/failure and F29 SQL uniqueness require native qualification. Keep completion/data atomicity. |
| B11 Ark/MGE boundaries | DALs operate on their domain rows; MGE publication commits before Discord send. Ark rehydration uses a bounded query with connection cleanup and drained offload. Direct Ark file-helper callers remain included in F20. | Full event lifecycle/admin/board correctness stays in P1; accepted MGE work is preserved. This is not a whole-module approval. Ark remains next. |
| B12 inventory/registry/preferences/review | Inventory approval writes domain records and approval state in one transaction. Governor session locks are separate row leases; preference/account/review DALs use their own identities. Leadership audit failure is isolated. | Shared factory/reader cost remains included; do not transfer governor-lease expiry rules to uncertain exports. Independent domain semantics remain outside this phase. |
| B13 reports and interaction entrypoints | Ordinary KVK/pre-KVK/player report/render paths delegate to the mapped DAL/cache/services. Recovery/command routes do not gain arbitrary account settlement authority. | Reader cost and cancellation remain A02/A04/A10; view expiry is not a SQL execution deadline. Domain calculations/layout are not re-reviewed here. |
| B14 other telemetry/local workflows | Usage recording uses a bounded nonblocking queue and separate flushing; voting/survey reminders claim their own rows before Discord work; CrystalTech and diagnostic sessions use separate local stores. Shared file/delivery helpers remain included. | Background buffering, file-lock contention and cost require proportionate budgets; separate-store mapping does not mean zero interference or approve all domain logic. |
| B15 recovery UI | Recheck delegates to the same inspection contracts. No-action display follows failed proof checks; a view cannot invent a receipt or clear durable ownership. | F28 truthful outcome/terminal convergence and F05/F13 exact actionable reasons. Never add a generic force-clear to make the UI green. |

The 79 selected baseline tests passed across Rally import/route, fallback staging/worker,
capture recovery, refusal view and recovery notifications. The new isolated experiments
are retained in `final-main-pass-edge-results.json`; despite the filename, these belong
to the **main pass**, not the reserved final outlier sweep. A 35-file normalized comparison
finds all selected follow-through sources identical to their retained deployed Bot/SQL
pins. This narrows regression claims for these files; it does not prove all runtime
configuration, deployment or timing is unchanged.

The reason these issues were missed is now more specific than "insufficient logging":
earlier packages tested particular adapters and happy-path boundaries, while sibling
projections, reused legacy helpers, post-commit diagnostics and diagnostic-as-admission
dependencies remained inconsistent. Several tests actively preserve the old behaviour;
some native fixtures replace the costly child operation. Previous acceptance documents
also explicitly left broader census/overlap obligations open. Those are evidence-backed
coverage gaps, not proof that every earlier fix failed or was rolled back.

## Separate final sweep and exact old-export closure diagnosis

The [separate final sweep ledger](Startup%20Import%20Export%20Reliability%20-%20Final%20Sweep%20-%202026-11-02.md)
records the refreshed inventory, 322 additional path dispositions, reverse-call checks,
dynamic/manual entrypoints, counterexamples and source boundaries. It does not replace
or inflate the earlier 371-row historical ledger. The source analysis is complete for
the recorded scope; native cost/concurrency and installed external bindings remain
qualification. The original physical blocker behind the one-second wait is still unknown.

### F02 extension: request 177 prevents closure, and the existing repair path cannot settle it

At **2026-11-02 10:58:15 UTC**, the user executed the prepared fixed read-only SQL
diagnostic on physical MINI_AMD. It returned the following for the exact Report 65/66
old-export job. Raw identities/hashes remain in private evidence; the chat contains the
complete supplied result. These are read-committed observations, not an atomic snapshot.

| Boundary | Observed fact | Consequence |
|---|---|---|
| Job | uncertain, version 3 before and after; same owner/fence | No closeout has advanced this job |
| Stream | One mutation stream, frozen, version 532, last sequence 177; session open | Still an unfinished journal; not proof a child is currently running |
| Last request | sheets.batchUpdate, sequence 177; prepared and dispatch_intent only | Missing terminal event is the SQL close guard's exact failing condition |
| Other request prefixes | One nonterminal request returned, the same request 177 | No second returned nonterminal request needs to be invented to explain this block |
| Closure | No closure hash/reference; no closeout receipt | Current closeout cannot verify a stopped, closed execution scope |
| Ownership | Active account remains; account and 11 destinations blocked for this exact job/owner/fence | Future exports using this account remain inadmissible |
| Other gates | No returned binding/scope/claim-version mismatch; no foreign active stream returned | Those checks do not explain this observed refusal; absence is bounded to this read |

The causal chain is now specific:

1. Retained authority diagnostics place the first failure at `request_result`, after
   response validation. `ExportExecutionAuthority._event` evaluates `_evidence` before
   `ExportExecutionDAL.transition` attempts its one-second account mutex. Private
   storage encrypts, fsyncs, reads back and retains a replica before returning a receipt.
   Source predicted saved response bytes preceding the failed SQL admission. E37 now
   finds those bytes in matching primary/replica copies for the exact request. Full
   saved-payload/response validation still belongs to the repair preflight.
2. The result event is absent in the supplied SQL read. The authority marks the stream
   uncertain; it does not have a mutation-result reconciliation path that retries only
   the evidence append after independently establishing its durable state.
3. `close_stream` freezes, obtains child-termination evidence, computes the journal seal
   and saves closure evidence before its final SQL transition. The retained failure
   frames reached that final transition. `usp_ExportExecutionStreamTransition` rejects
   this mutation prefix with 51700, "Nonterminal request evidence prevents stream
   closure." This is a durable-state guard, not another physical-lock timeout.
4. `LegacyExportCloseout._proofs` then rejects the frozen stream/active account with
   "Original writer is not verifiably stopped in its registered scope." The UI collapses
   missing closure proof and physical liveness into that generic message. Recheck has
   no approved repair action to resolve the missing event, so repeated rechecks cannot
   clear this state by themselves.

The SQL event procedure permits terminal evidence on an exact **frozen** stream, with
authority role/session, expected version and request-state checks. However, calling it
is not a complete existing repair. Appending the event changes both version and digest;
the authority caches the old closure document and refuses a changed journal with
`Frozen journal changed after closure evidence`. A reviewed recovery must produce and
verify a new exact seal without reusing the stale one or dispatching the request again.
An `unknown` event is also insufficient: although it satisfies the stream's terminal
guard, both the private verifier and legacy closeout require a supported known mutation
prefix. It cannot be used as a shortcut to release this job.

The stranded-writer repair expects an eligible running/open/unblocked ownership snapshot;
this job is uncertain/frozen/blocked. Read containment applies to qualified read-only
scopes. Neither route is an alternative generic unlock for this mutation.

**Concrete recovery sequence to design:** use the now-located privately retained response
and termination document; validate original payload, complete response, exact child and
authority custody; reconcile the existing event without a Google call; create and
verify a closure seal over the reconciled journal; revalidate job/resource ownership;
then use the exact legacy closeout transition. That transition records the old job as
failed and releases its restrictions while preserving history and URLs. It must not
call the partial old export successful. If valid response evidence cannot be recovered,
keep the outcome unknown and design an explicit mutation-containment/reconciliation
route; do not manufacture a success event. No release has been executed or approved here.

A second fixed private diagnostic has been prepared for the user. It verifies the
installed authority/host/account binding, bounds candidate discovery to the 20-second
failure window and returns references/hashes/closure flags without spreadsheet values.
It makes no SQL/provider call, performs no repair and gives no release authority.
Candidate timestamps are discovery filters, never expiration or correctness evidence.

The user's first collection stopped at the directory enumeration guard: the root has
at least 100,001 enumerated files, so the collector's cap fired before candidate blob
reads. This is a diagnostic limitation, not evidence of missing response bytes or a
new export failure. The revised v2 helper streams direct-entry metadata, applies the
same time/name filter before retaining at most 256 candidates, and bounds metadata
enumeration and ciphertext reads separately. It returns completion/partial status;
an incomplete search cannot establish absence. Host/account/root ownership checks
are unchanged. Windows PowerShell 5.1 fixtures cover matches beyond the original cap,
empty/limited/error results, enumerator disposal, and synthetic DPAPI response/closure
projection. The user subsequently supplied the completed v2 result at 12:01:42 UTC.

That result enumerated 123,288 direct files in 365 ms, selected and decoded all 18
time-window candidates, read 35,736 ciphertext bytes and found four matches: primary
and replica of the response for request 177, and primary and replica of the original
closure. Each pair has identical plaintext hash, ciphertext hash, reference and size.
The closure is 282 bytes, version 532, last sequence 177, and records the exact child
with `job_empty=true` and `process_signaled=true`. The 188-byte response contains a
spreadsheet identity and one reply. References/hashes are retained privately in
`final-sweep/saved-evidence-v2-production-result.json`; they are no longer hypothetical
or missing locators. The two copies provide redundancy, not independent attestations.

The displayed closure version/sequence match E33. The summary is not its full plaintext
(the original termination document also contains PID), so it cannot independently
reproduce the closure hash here. Nor does one reply alone establish exact response
membership/target agreement. These are precise preflight obligations, not reasons for
another broad folder search or another routine incident. This read did not refresh SQL
state or establish present-day OS liveness; the last SQL observation remains 10:58:15.

Carry this into S2: exact-result recovery should have a durable request-bound locator
for saved outcome evidence, so it need not discover an orphan through a large folder.
Assess retention and index costs under G04; this observed lower bound alone does not
justify deleting evidence or prove that the retention policy is wrong.

### P03a draft: settle the retained result and close the old export

This is a focused S2 design slice, not an implemented or approved production repair.
It addresses the observed frozen mutation stream with privately retained response and
termination evidence. It does not create a generic clear-lock action or weaken the
existing outcome/ownership contract. Raw job/stream/request/copy references are in the
private evidence packet; the stored first failure and old seal remain immutable.

| Step | Required behaviour | Why this check remains valuable |
|---|---|---|
| 1. Read-only preflight | In the trusted authority/service boundary, load only the exact saved references. Verify private custody/hashes, original SQL payload binding, protocol response target/reply membership, original child termination and original journal digest/version. Read current job/session/stream/resource membership; detect drift and foreign ownership. | Prevents a wrong or incomplete response, stale seal or changed owner from authorizing release. No directory scan, provider call or business replay. |
| 2. Settle request 177 | Reconcile whether the exact terminal event already exists. If absent and evidence qualifies, append the known result through the authority-role SQL procedure using the exact frozen-stream version. Preserve the prepared/dispatch events and first failure. | Records the already-observed result without sending the Google mutation again. Distinguish pre-execution refusal from lost SQL acknowledgement. |
| 3. Renew closure | Recompute the journal after settlement and create a new closure receipt bound to its new version/digest and verified original termination evidence. Preserve the old closure record. Coordinate with any cached in-memory closure state explicitly; do not simply reset or reuse a stale cached receipt. | The current cached document will differ after event append. This is the second reproduced gap, not optional duplicate validation. |
| 4. Exact legacy closeout | Run the existing complete private-history/registration/membership checks, then its exact closeout transaction under current ownership/version checks. Release only this job's reservations; retain the same URLs and failed/partial historical outcome. | Allows subsequent exports without claiming the old export fully succeeded or releasing unrelated work. |
| 5. Verify receipt and projection | Read the resulting closeout/ownership state and project that durable result to the recovery incident. A failed acknowledgement must converge by reading exact receipts, not by re-sending work or requiring a cosmetic recheck. | Establishes that the restriction was actually released; a successful UI response is not the receipt. |

The existing event SQL admits terminal evidence on a frozen stream and already checks
authority principal, session, exact request prefix and stream version. Its role/transaction
contract remains mandatory. The existing closeout SQL records the old job as failed and
releases its resources only after proof. The missing capability is trusted orchestration
of saved-result settlement and renewed closure, including restart and lost-acknowledgement
handling. Decide the exact authority endpoint/recovery adapter and restart ownership
model before implementation; an ad hoc SQL update from the diagnostic account is not
the implementation. No new SQL schema is assumed necessary or ruled out by this draft.

Preflight file/protocol/history work must run outside SQL write transactions and account
mutex ownership. Mutations recheck exact versions/membership at their short transaction
boundaries. A passive observer must not acquire producer exclusion merely to refresh a
status. Ordinary waiting and diagnostic-log failure must not abort the recovery or create
an incident requiring manual acknowledgement. This is one explicit recovery action with
state-derived progress, not repeated manual steps for each internal checkpoint.

Qualification must cover: refusal before result append; append committed but reply lost;
restart between append and seal; seal saved but SQL close refused/acknowledgement lost;
closeout committed but UI confirmation failed; exact already-completed retries; changed
owner/fence/membership; mismatched response, hash or original digest; and absent/unknown
mutation evidence. Across every boundary, assert zero new provider mutation calls,
preserved first failure, no unrelated release and convergence from durable receipts.
Automatic eligibility and meaningful escalation belong to the full P03/P04/G04 design.
F28's cancelled-import parent projection remains a separate correction, not a second
account lock. Original physical mutex-holder attribution remains a separate G03 question.

Eight relevant Python method bodies and five SQL definitions, including both legacy
Rally procedures, match the retained deployed revisions. This supports a **coverage and
recovery-completeness gap**, not a demonstrated code rollback. The authority baseline
fake increments its version before simulating a lost acknowledgement; that scenario
does not model admission refusing the event before execution. Existing unknown-outcome
tests correctly preserve safety, but do not establish automatic liveness for this
missing-result/frozen-closure combination. The new offline experiment exercises both
gaps and a successful control. It is not native SQL or live orphan-file proof.

### F31: the legacy Rally child can consume a file before its parent commits

`dbo.UPDATE_ALL` claims the stats file, starts a transaction and acquires the stats
import lock, then calls `UPDATE_RALLY_DATA` before the digest-bound stats core. The
Rally child bulk-loads its separate fixed CSV, rebuilds output and invokes `xp_cmdshell`
to delete that CSV. Its catch prints the error without throwing. The parent commits
much later and rolls back on later failures. A rollback can undo SQL writes but cannot
restore the deleted Rally file; a child error can also return without a reliable failed
result. The newer stats file claim/archive protocol does not cover that separate file.

This is a static, conditional legacy/manual path finding. The current scheduled caller
uses the newer chain; no production use of this legacy entrypoint or Rally loss is
claimed. Local history for the Rally procedure predates the recent P0/P1 work. The
earlier twelve-root graph started from current producer contracts and missed this
alternative parent's additional side effect. Include installed-use verification and
either explicit retirement or custody/error/transaction alignment in S2. Do not merely
move the delete while leaving silent child failures and invocation policy unspecified.

### F32: timing emission can interfere with the operation it measures

`core/owned_work.drain_thread` calls `record_timing` before invoking its worker and
wraps the body in `timed_stage`. `core/operation_timing.record_timing` calls the logger
directly; `timed_stage` emits in its finally block without isolating diagnostic errors.
With an active timing reference, a raising logging sink can prevent the worker call
or replace a completed result/original failure with the diagnostic exception.

The isolated experiment extracts the actual helper bodies, injects a raising logger,
and confirms zero worker calls on entry failure, a completed body followed by an exit
failure, and a successful no-reference control. This tests the non-interference
contract; it does not prove the installed logging handlers raise or attribute today's
incident to logging. Standard handlers may already handle their own I/O errors.
`export_publication_metrics` explicitly catches its collection and logging exceptions;
that is a useful existing pattern. Design the shared timing boundary to preserve the
business result/exception and physical drain, rather than adding another incident for
a failed timing line. This shared-helper finding does not reopen accepted MGE domain
behaviour or finalisation evidence.

## Timing policy to design, not flatten

| Boundary | Current source distinction | Design requirement |
|---|---|---|
| SQL connection factory | Login 5 s, query 15 s, row-lock wait 1 s | Separate budgets; actual workload and cleanup determine policy. |
| Short coordination transactions | Selected 1/5 s retry budgets, bounded attempts/backoff and connection setup credit | Verify coverage of each transition; retries require acknowledged cleanup and renewed ownership checks. |
| Authority account admission | Outer one-second wait before transition/result persistence | Handle ordinary contention without replaying external work. |
| Global snapshot guard | Immediate refusal at producer entry; zero-wait observer acquisition | Observation must not own a guard that refuses useful work. |
| Player report | 300 s SQL lock wait but inherited 15 s query timeout | Configure and log the actual statement budget; latest pre-entry failure is a separate cause. |
| UPDATE_ALL2 / post-import maintenance | Distinct explicit 595 s / 300 s statement settings | Preserve justified per-operation policies rather than replacing them with a global increase. |
| Authoritative business SQL | SP_Stats_for_Upload and target/publication work include 60 s application-lock waits | Check compatibility with caller deadlines and transaction lifetime. |
| Startup / UI observation | Configuration 180 s cancelling; player 20 s non-cancelling; health UI waits separately | Elapsed observation is not business failure or proof of cancellation. |

SQL definitions inspected include `ExportResource`, `ProcessingPipelineStage`,
`usp_ExportProviderRequestEventAppend`, `SP_Stats_for_Upload` and `sp_TARGETS_MASTER`.
The request-event procedure requires its own transaction and authority role, then takes
account/row locks; bypassing that contract is not a safe settlement fix. No schema/index
change is proposed from Python usage alone. Native lock lifetime and query cost remain
qualification work; dirty reads and global isolation changes are not default remedies.

## Proposed package order

| Package | Coherent change and ownership | Exit evidence |
|---|---|---|
| P01 observation/completion | Startup services preserve completed results; status UI reads retained health; upload/calendar mutation, audit, refresh and delivery outcomes stay distinct; optional CSV/timing logging cannot prevent or mislabel work (F30/F32) | F08/F11/F17/F23/F25/F30/F32 get caller-level regressions; first decide auxiliary index necessity. Viewing status starts no SQL/provider/recovery work; delayed success remains success. Include F24 physical worker drain and next-caller exclusion. Split independent caller families into focused PRs. |
| P02 observer isolation and producer budgets | Shared file-lock cleanup and observer lifetime (F20); DAL admission/scheduling/budgets and alternate factories (F26); SQL maintenance (F18/F21/F22), Python guard lifetime (F16), legacy custody/error policy (F31) | Every direct helper caller releases only its own lock on exceptions/cancellation. Both observer-first and writer-first SQL cases cover producer, checkpoint and settlement. Real maintenance failure preserves committed stages; costs are bounded. Verify legacy enablement before retirement. Separate Bot/SQL PRs where applicable. |
| P03 exact completion/settlement | Pipeline automatic receipt binding, exact cache continuation, cancellation projection convergence (F28), Rally attempt/success identity (F29), and authority result/pacing/closure settlement (P03a) | Commit or provider success followed by contention/lost reply/restart converges without rerunning SQL or resending provider mutation. Cancellation and failed attempts retain truthful identities. Split these distinct root-cause families into focused PRs. |
| P04 actionable incidents/history | Recovery policy, presentation, report-validator waiting classification (F27), bounded event history/report completeness and notification-capacity dependency (F19) | Routine delays need zero operator actions; meaningful faults still escalate; failure -> recovery -> restart -> export preserves the explanation. Unrelated notification backlog must not block work without a justified correctness dependency. |
| P05 combined acceptance/P0 credit | Cross-package qualification, original P0 rows and production acceptance after separate authorisation | Workload denominators, completion, manual actions, false incidents, convergence and observer cost; preserve prior accepted work; Ark handback. |

P01-P04 are a proposed sequence, not implementation approval. F26 belongs to P02's complete
connection/budget policy, including fallback error classification. P02 must be designed across
all mapped writers/observers before making isolated timeout edits. Services own policy and
scheduling; DAL/SQL own consistency and transaction boundaries; views only present/route.
Existing helpers should be corrected or consolidated rather than adding another ownership
framework. Review/security targets for Bot and SQL remain separate when either changes.

The [delivery handover](Startup%20Import%20Export%20Reliability%20-%20Delivery%20Handover%20-%202026-11-02.md)
now supplies a complete primary-owner mapping for F01-F32. It recommends moving the
focused P03a recovery ahead of P01 because the existing export restriction remains,
subject to checking and completing any actual shared prerequisite first. This is an
explicit priority proposal, not a silent reordering or permission for a production
repair. Remaining P03 work stays after P02; all packages still feed P05 acceptance.

## Validation completed and remaining gates

The first validation batch completed the startup experiment and 76 focused tests across:
`test_monitor_startup_diagnostics`, `test_checkpoint_observation_lifecycle`,
`test_processing_pipeline_receipts`, `test_recovery_monitor_observation`, and
`test_gsheets_health_service`. Existing green tests establish baseline behaviour, not the
new acceptance contract. Tests ran in the existing virtual environment with dotenv loading
disabled for that process; initial attempts found system pytest unavailable and then a
protected `.env` read during collection. No environment file or dependencies were changed.
Subsequent batches and offline experiments are recorded above: the earlier 532-test tally,
then separately recorded 385-test, 28-test, 72-test and 147-test batches. No unique combined total is claimed.
None is evidence that a runtime correction has been implemented.

| Gap | Required work / owner | Closure condition |
|---|---|---|
| G01 full current census | Main 371-path ledger plus separate 322-candidate final dispositions recorded; entrypoints/sinks/dynamic/manual boundaries challenged | Source review complete for the recorded scope. Installed Agent/trigger/manual enablement and native execution remain qualification; no every-branch or whole-domain approval. |
| G02 native concurrency and cost | Design/qualification: observer-first producer entry, authority post-response persistence, ordinary reads, serial IPC and repeated observation | Isolated SQL/host evidence with both directions and measured cost; no production fault injection. |
| G03 latest causal attribution | Current closure blocker confirmed by the user's SQL read; E37 finds matching saved response/termination copies | Missing request-177 terminal event, frozen stream and blocked ownership known. Original physical mutex holder/duration remain unknown. Full response/current-journal qualification remains in P03a preflight; no release or historical-cause generalisation. |
| G04 automation eligibility and retention | All 73 allowed pairs classified; worker/group routes and 11 evidence-lifetime layers traced. Carry per-state eligibility, safe projection and concrete retention/capacity choices into M05 | Source coverage recorded; automatic recommendations still require exact eligibility and design approval. No uncertain outcome may be erased merely to satisfy a limit. |
| G05 P0 acceptance rows | Reconcile original matrices after designs and qualification are concrete | Credit F01/F02/F03/F05 precisely; retain F04 natural rollover and unexercised cases. |

The S2 decision packet below advances that draft with explicit ownership, delivery
dependencies, policy choices and local native measurements. E37 remains the private
evidence reference; it does not become a current production preflight. M04a remains
the separately recorded fresh sweep, not a relabelled earlier search.
No new runtime observer should be installed merely to make
the tracker look complete. This review can help finish earlier P0 obligations, but does
not itself close them. After this bounded phase, return to P1 Batch A: Ark next.

## S2 decision packet and P03a implementation boundary

**Current direction, E51 (3 November):** P03a.1 is complete; P03a.2 and startup
correction are deployed/startup accepted, with ordinary-flow acceptance open after
E50. Start P01 design, then P02, remaining P03, P04 and P05. Do not accelerate a
one-off F09 change. Apply the canonical scope's mandatory boundary evidence and
incident/deployment-dependency contract; a supported recovery prerequisite does not
move the contention fix from P02. The original S2 design below is retained history.

Prepared 2 November 2026 against Bot `a025adb7a69aac321fd62794b871ed5903338f44`
and SQL `7e91989f619deb46836194c7e705b0a9eb2ebe11`. This section is the current
design proposal within the existing programme, superseding the tentative sequence
wording above. The accepted order is S2 -> P03a (necessary prerequisites first) ->
P01 -> P02 -> remaining P03 -> P04 -> P05 -> applicable P0 reconciliation -> P1 Ark.
All F01-F32 retain the handover's primary owners. No finding closes through this design.

### Outcome and check policy

Keep business outcome, current execution, recovery progress and presentation separate.
Use existing durable receipt identities; an observation revision, elapsed timeout,
released reservation or missing response is never a substitute for a business receipt.
These are semantic states to map into existing typed contracts, not new SQL enum values.

| Evidence state | Required behaviour | Automatic eligibility / escalation |
|---|---|---|
| Admitted/running or waiting for a useful lock | Preserve physical ownership; show the stage and last confirmed progress. A caller deadline may stop waiting, not stop the worker. | Bounded rescheduling with acknowledged cleanup and renewed identity checks; ordinary contention resolving in three seconds creates no actionable incident. |
| Exact committed result; later audit/refresh/notification failed | Preserve committed success and report the secondary stage separately. | Reconcile the receipt and retry only the independently safe secondary stage. No repeat import/export to repair presentation. |
| Valid saved provider result; terminal SQL event missing | Validate complete request/result and exact journal, then settle bookkeeping. | No provider resend. Automatic for a previously accepted owned request; historical adoption requires the exact reviewed recovery packet below. |
| Exact cancellation completed | Close its current projection from authoritative cancellation evidence. | Preserve the original refusal/failure; no cosmetic acknowledgement or clearing action. F28 remains P03/P04 work. |
| Missing/ambiguous provider result, foreign ownership or unproved child termination | Preserve uncertainty and exclusion; state the precise missing proof. | Do not append invented success, release ownership, contain a mutation as a read, or treat age as finality. One actionable state transition, with changed evidence updating the same case. |
| Observation unavailable/stale | Show last-known state and observation time separately from business status. | A failed poll does not fail business work. Sustained loss of observation is its own bounded health incident, not another incident per poll. |

Keep scope/registration, payload hashes, owner/fence/version, exact SQL receipts,
provider response validation and physical termination checks at their useful action
boundaries. Consolidate immutable-history validation into one bounded proof per exact
version tuple; invalidate it on drift. Do not cache mutable ownership across actions.
Passive status/report reads consume retained projections only: no account/global guard,
SQL proof generation, provider request or private-directory scan. Active verification
and recovery are explicitly named work, with independent admission and retained progress.

P01 isolates optional audit/CSV/timing emission from business outcomes and keeps physical
drain. For F25, remove the auxiliary index only after installed-consumer verification;
otherwise keep it as an independently reported derivative, never a reason to deny the
main cache commit. P02 owns ordinary SQL-read cost, alternate factories, legacy callers
and all six maintenance stages. Move maintenance outside critical ownership only after
its actual durability/headroom requirement and failure semantics are proved; do not
relabel required capture or claim/archive integrity as optional logging. F31 needs
installed-use evidence before retirement, or a focused custody/error correction.

### G04 retention and capacity decisions proposed for P04

| Evidence class / existing source | Proposed retention and capacity rule |
|---|---|
| Correctness evidence: ExportJob provenance, provider/attempt receipts, StatsImportExecution, capture intent and RecoveryAction | Preserve first failure, exact accepted intent, commit/cancel/closeout receipts and referenced private proof while any ownership, uncertainty, restart or rollback dependency remains. No age-based deletion in P03a and no P04 deletion without an independently verified unreferenced-terminal policy. A green incident is not permission to delete its proof. |
| Current RecoveryIncident and ProcessingPipelineStage projection | One current projection per exact source identity. Rebuild from authoritative receipts; retain compact original/latest failure and meaningful state changes, not every poll. Proposed hot history: 90 days after durable terminal resolution; archive those transitions for 365 days, then delete only unreferenced, resolved presentation history. These durations do not expire correctness records. |
| ImportAuditBatch/Phase and notification history | Preserve ingest, refresh and delivery separately. Apply the same 90-day/365-day policy only to resolved presentation history; retain uncertain send identities until resolved. Optional notification capacity must not refuse an otherwise valid import. At saturation, omit a new optional progress notification and record a coalesced notification-health state; do not claim delivery or evict an unresolved send. Required delivery stays a separately unfinished stage. |
| Health/admission diagnostics | Keep the existing 32-entry volatile admission ring. Aggregate repeated waiting/counts; persist first outage, material change and recovery only. Proposed 30-day retention for resolved health transitions, with one active outage per source. Losing optional telemetry must not mask the original result. |
| Recovery report | Retained projections only; paginate at existing byte bounds, explicitly mark truncation/staleness. Export stage, identity, original/latest failure code, accepted decision and receipt references. Exclude raw InputsJson, credentials, payloads, SQL text and arbitrary exception strings. |

No new arbitrary global row cap is introduced in S2. P04 must measure the existing
notification/store byte limits against representative records before changing their
numbers. Unresolved correctness evidence reaching capacity stops only work that needs
that evidence store for safe execution; it is a real storage fault, not permission to
discard uncertainty. Archive failure keeps the original. P04 supplies schema/adapter
mapping and capacity tests in its own PRs; these decisions do not authorize a migration
or garbage collection now.

### P03a dependency decision and delivery slices

No broad P01/P02 fix is required before the first P03a slice: active exact recovery can
reuse existing event/stream procedures and legacy closeout, keep all private I/O outside
SQL locks, and expose retained passive status. The narrow prerequisites are **inside
P03a**: durable action/event identity, exact receipt reconciliation after any uncertain
acknowledgement, verified connection cleanup, and bounded owned scheduling. Do not wrap
provider execution in generic coordination retry or claim this completes P02.

There is a deployment dependency. `export_startup_reconciliation._readiness` and the
S11 restart contract require streams closed and reject this held job; authority drain
also cannot seal its nonterminal mutation. An ordinary upgrade/restart must not be
assumed to install the repair first. Use two reviewable slices under F02:

1. **P03a.1 retained-result settlement service and protected runner.** Implement the
   state machine below, reusable pure proof checks, exact SQL adapter and a protected,
   independently packaged runner for the installed authority account. This enables
   separately authorized recovery before a normal runtime upgrade. Reuse the custody,
   isolated `-I -B` launch, fixed manifest and immutable journal patterns from
   `scripts/recover_stranded_export.py`; do not loosen that runner's running/open rules
   or repurpose read-only containment. No Discord command or general SQL repair console.
2. **P03a.2 runtime recurrence prevention.** Persist a request-bound locator before
   dispatch, settle saved results through the same service, renew closure, and integrate
   an owned asynchronous worker plus passive status in authority/client/shutdown.
   Complete and qualify this slice before F02 closure and transition to P01. Shipping
   only a one-off runner is not completion of P03a.

P03a.1 is the first implementation approval target. Its packaging must load the fixed
reviewed helper set from a protected location without modifying the installed live
source or launching another provider authority. Bind the installed manifest, SQL
principal, original open session, exact host/deployment identity and original process
pair using retained handles; recheck the boundary before every write. The historical
child's saved termination evidence is checked cryptographically; do not identify that
child by a potentially reused PID or require it to be alive to prove it stopped.
If the original session is closed or process/deployment identity changes, stop this
packet and retain progress. Tool restart may resume the same packet while its binding
still holds; a new process pair requires a newly validated binding, not silent adoption.
The existing failed-export action is `allow_next_export`: preserve its explicit partial
output abandonment decision. Evidence settlement alone is not consent to abandon work.

### Exact P03a.1 state machine

Inputs are one protected manifest with the exact job/account/owner/fence/version,
registration and membership, session/stream/child, request/sequence, original stream
version/digest, payload/result/original-seal references and hashes, plus a single action
ID, actor and reason. Raw production values remain in the private packet, not this doc.
No broad evidence search or current provider probe is part of this action.

| Stage | Required proof and write | Resume / lost-reply rule |
|---|---|---|
| Validate | Read all 177 requests/events and their protected payload/event documents, full saved response through the original protocol validator, registration/scope, original closure and exact owner/resource set. Verify the original digest and v532/sequence 177, child termination and empty job. Historical replicas are redundancy, not two witnesses. | A summary file is insufficient. Every identity/version/hash mismatch refuses the action with original evidence intact. SQL reads are action-time validation, not labelled passive observation. |
| Record intent | Exclusive, fsynced, read-back-verified protected intent fixes event ID, saved result hash/reference and original state before append. Retain immutable stage receipts. | Journal progress never proves SQL commit; reread authoritative rows. Conflicting existing intent is a conflict, not overwritten. |
| Settle terminal event | Existing `usp_ExportProviderRequestEventAppend`, original authorized open session and exact frozen version, append the validated `succeeded` result once. No provider call. | On any error, close/verify cleanup, then read exact request/event ID/hash/reference and version. If committed, advance; if unchanged and safe to retry, reschedule the same event; otherwise stop. Never classify all EvidenceCommitUnknown exceptions as safe pre-entry refusal. |
| Renew closure | For expected single append, v532 -> v533 and a new digest. Save a new closure using the original exact termination proof and current journal; retain old seal unchanged and link both in recovery evidence. Close through existing stream procedure to v534. | Reconstruct original digest by excluding only the exact accepted repair event, checking every remaining row and version. Do not merely accept a changed digest. A matching already-closed receipt is success; mismatched seal/version refuses. Never reuse the cached old seal. |
| Close out partial export | Existing LegacyExportCloseout full proofs/registration/ownership checks, then short exact closeout transaction. Preserve original failure, set old job failed, release only its exact 12 resources, keep URLs. | Persist the one closeout action ID/evidence reference before invoking. Read its exact durable receipt after lost reply, including job version and membership. Do not rerun provider work or report the whole export succeeded. |
| Project completion | Retain closeout receipt and released-membership result; report partial export closed and account available for subsequent normal work. | Failed UI/log acknowledgement must converge from receipts automatically. P04 owns broader incident presentation; F28 cancellation remains independent. |

The expected versions above describe E33/E37, not fresh production facts. The current
state must match or prove an exact already-completed stage before a future operation.
Preflight validates the complete history outside write transactions. Each short write
revalidates its own CAS; ownership drift cannot be waived by an earlier preflight.

### Durable recurrence and worker ownership

In P03a.2, allocate the event ID and result reference and persist a small immutable
request-bound locator **before provider dispatch**. Write the validated result at that
fixed reference with existing encrypted primary/replica custody, exclusive creation,
fsync and readback. Adding a pointer only after saving a randomly named result leaves
the same crash gap. A partial/missing result remains unknown; a conflicting file is
never overwritten. Use fixed references to resume, not a scan of the evidence directory.
This is supporting private evidence, not a second SQL outcome ledger.

One owned worker per account consumes exact accepted work. Deduplicate by immutable
request/action ID, reconstruct pending work from protected intents and SQL after restart,
and schedule through an explicit authority recovery start/status contract. Start is an
active operation; status returns a bounded retained projection without SQL/file/proof
work. Reuse the proof-progress threading pattern where useful, but its 16-entry local
cache cannot be durable authority. The serial pipe and authority-wide RLock must not be
held during retry sleeps or whole-history I/O. Shutdown joins the actual worker; a UI
timeout does not relinquish ownership. Existing drain/startup invariants remain.

For a live owned request, a saved validated result can settle and return to the original
caller without resending the provider request. If that caller has already abandoned the
operation, settle evidence and closure but preserve the partial job outcome; automatic
`allow_next_export` is not granted to arbitrary historical jobs. P03a.1's exact approved
packet includes that abandonment decision once, not a confirmation at every stage.

### SQL contract and file manifest

No SQL schema, permission expansion, isolation change or migration is proposed. Checked
in the SQL source-of-truth repository: `ExportExecutionSession`, `ExportExecutionStream`,
`ExportProviderRequest`, `ExportProviderRequestEvent`, `ExportLegacyCloseout`, `ExportJob`,
`ExportJobResource`, `ExportResource`, and the event/stream/legacy-closeout procedures.
Event ID and request/event-sequence uniqueness plus version CAS support read-before-retry;
the procedures themselves do not make duplicate invocation a successful acknowledgement.
Terminal append accepts the exact frozen stream; dispatch does not. Close checks terminal
history; legacy closeout retains failure and releases only matching ownership. Any newly
discovered SQL requirement must be a separate SQL diff/review, not embedded command SQL.

| Slice | Exact affected or proposed files and ownership |
|---|---|
| P03a.1 proof/state machine | New `services/export_saved_result_recovery.py`; reuse `services/export_reconciliation_service.py` full closed-stream verifier and `services/legacy_export_closeout.py`. Extract common pure proof/digest logic only where needed, preserving normal closure checks. |
| P03a.1 SQL adapter | `services/export_execution_dal.py` for exact event receipt/history read and reusable ordered digest fold; `services/legacy_export_closeout_dal.py` existing action settlement. No SQL in the runner or Discord views. |
| P03a.1 runner/custody | New `scripts/recover_saved_export_result.py` and `scripts/Invoke-SavedExportResultRecovery.ps1`, with a fixed reviewed file/hash manifest. Reuse `core/stranded_export_host.py` and protected-journal primitives where applicable; isolate historical-result eligibility from stranded-writer eligibility. |
| P03a.2 evidence storage | `core/export_execution_host.py`, `services/export_snapshot_store.py`, `services/export_evidence_storage.py`: narrowly scoped fixed-reference encrypted writes and request locators. Preserve existing random-reference compatibility and original damaged evidence. |
| P03a.2 runtime | `services/export_execution_authority.py`, `scripts/run_export_authority.py`, `services/export_runtime_composition.py`, `services/export_proof_progress.py` as needed for owned scheduling/passive progress; `services/export_startup_reconciliation.py` only for explicit compatible recovery binding. No weakened ordinary startup readiness. |
| Tests/docs | New focused saved-result unit/native/custody and launcher tests; extend the existing authority, lock, protocol, host, legacy closeout, startup and runtime suites listed below. Update the existing tracker/handover and actual operational runbook when the implementation is known. |

### Measured boundary and proposed budgets

The user authorized synthetic qualification on local `localhost\K98DEV`, confirmed by
the screenshot and server identity `9SX2VF4\K98DEV`, version `16.0.1210.3`. E39 records
an isolated newly created database and restricted real login (neither sysadmin nor
db_owner). Complete event/stream/closeout procedure bodies ran unchanged; existing
fixture tables retain checks/indexes but omit unrelated foreign keys. This measures
the relevant SQL boundary, not full installation or private-proof cost.

| Local measurement | Result and useful limit |
|---|---|
| 177 requests / 530 events, 20 complete digest reads | Median 5.07 ms, p95 6.50 ms, maximum 16.33 ms; warm local development workload, not a production latency promise. |
| Account held for 3,000.62 ms | Two refused attempts at 1,014.58 / 1,009.85 ms; third append succeeded; exact readback after discarded commit reply converged at 3,065.37 ms. Exactly one appended event, zero provider calls, no operator steps after starting. |
| Another account during the hold | Admission/read 1.14 ms; one sample, not a universal fairness claim. |
| Seal and legacy closeout | Closure 11.75 ms; exact SQL closeout of 12 synthetic resources 75.11 ms; stream v534, failed job and one closeout receipt. Private-history verification was not included. |

Retain the existing one-second account admission per attempt. Proposed recovery policy:
at most one active worker per account, one SQL connection per attempt, fresh exact
readback after uncertainty, and backoff 250/500/1,000/2,000 ms capped at five seconds.
After a 15-second burst, persist progress and reschedule after 30 seconds, capped at
60 seconds while still eligible; release connections/locks before every wait. This is
a scheduling budget checked between operations, not a hard cancellation of ODBC or
filesystem I/O. Keep distinct existing login/query limits; do not increase all callers.
Escalate once after five minutes without confirmed progress or immediately for proof
conflict/storage failure; continue only state-safe recovery. Successful three-second
contention is ordinary waiting and needs zero manual incident acknowledgement.

Use existing 256-request pages, at most three events/request, the protocol/private-store
payload limits and a proposed 64 KiB locator/intent cap. No directory-wide scan on status
or restart. Measure full decrypt/protocol/history cost and worker/IPC responsiveness in
P03a qualification before accepting its production budgets. P02 still must measure its
other writer/read/maintenance families; these local numbers cannot justify their budgets.

### Qualification, rollback and approval

P03a.1 tests must exercise pre-append refusal, real commit with lost acknowledgement,
restart after each durable boundary, old-seal rejection, new seal saved/SQL close refused,
close committed/reply lost, closeout committed/UI failed, and exact completed retries.
Negative cases include wrong principal/session, changed owner/fence/membership, tampered
payload/response/hash, missing intermediate event, extra request, unknown mutation,
invalid child termination and process/deployment binding drift. All assert zero provider
calls, no unrelated resource release and preserved original failure/seal. P03a.2 adds
partial fixed-reference writes, restart before/after replica, concurrent duplicate start,
serial IPC responsiveness, physical shutdown drain and both observer-first/producer-first
overlap. Retained status must not acquire producer locks or perform proof I/O.

Relevant existing suites: `test_export_execution_authority.py`,
`test_export_execution_protocol.py`, `test_export_execution_host.py`,
`test_export_execution_lock.py`, `test_export_execution_lock_sql.py`,
`test_legacy_export_closeout.py`, `test_legacy_export_closeout_sql.py`,
`test_stranded_export_recovery.py`, `test_stranded_export_live_recovery.py`,
`test_stranded_export_host.py`, `test_export_startup_reconciliation.py` and
`test_export_runtime_composition.py`. Native tests must execute real relevant procedure
bodies and restrictive permissions; mocks/stubbed maintenance cannot close those gates.
Windows qualification includes actual protected file custody/DPAPI, PowerShell 5.1,
package hashes, installed-version compatibility and retained process handles.

Rollback disables the new entrypoint/scheduler while retaining every intent, response,
seal and SQL receipt. It never deletes terminal events, resurrects released ownership or
replays the old export. Standard SQL event/closure shapes remain readable by old code;
old code cannot be assumed to resume new private intents. Prove downgrade behaviour with
pending work before deployment. Keep recovery-before-upgrade separate from later normal
runtime deployment, each with an exact reviewed package and operational authorization.

S2 checkpoint delta: documentation plus ignored local synthetic experiment only. No runtime,
test-suite or SQL source implementation, provider call, production change, PR, merge or
restart. Architecture/deferred/security-routing and explicit-path selection apply to the
documentation. For implementation, route security first, then **Scan type: Changes** on
the exact Bot diff, **Deep off**; a SQL change would have its own separate diff review.
That documentation skip does not exempt the proposed recovery code or its
executable package from review.

The user subsequently approved implementation/qualification of **P03a.1**, with P03a.2
retained as mandatory recurrence follow-through. This does not approve production
recovery. See the tracker for implementation and measured native evidence; no broad
P02 budget is approved here.

P03a.1 is now implemented in the existing mirror checkout on
`codex/p03a-saved-result-recovery`, base `76f9578940c97acb017c810d099a07a63abba9f4`.
E40 and the tracker record native full-private-verifier qualification, repeated durability
review, related corrections and exact limitations. The final source package adds no SQL
schema, grants or provider calls. Its separate final Changes review must bind the exact
staged bytes; historical documentation skips and earlier scan targets do not cover edits
made after those checkpoints. Production custody/current-proof and operational approval
remain open; local package readiness does not close F02 or replace P03a.2.
