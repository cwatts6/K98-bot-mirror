# Coordination lifecycle correction

The correction treats short, fully rolled-back contention as retryable, active
observation as waiting, and uncertain business completion as retained evidence.
It covers admission through settlement and historical incident closure. It does
not infer success from elapsed time, a healthy monitor, or incident counts.

## Evidence and cause

Reports 51–53 distinguish four defects. Slow connection setup consumed the short
retry allowance before later authorization and error-recording stages could retry.
A writer could retain a durable claim after guard construction failed before its
body entered. Passive discovery competed with active producers using decision
locks. Finally, configuration attempt evidence omitted the card's required summary
and had no verified linked-recovery disposition. Configuration also inherited
player report/cache wording.

The earlier bounded SQL trace established one later same-process collision lasting
about 22 ms between separate sessions. It did not identify the original 18:55
blocker. Report 52's row-lock timeout also lacks an attributed holder. Two
connections are not inherently a defect: guard, business and authority sessions
have distinct ownership roles. Business locks intentionally span atomic report
execution and its checkpoint; removing them would weaken fencing.

Report 53 records a completed pipeline, a confirmed export, and a new successful
configuration attempt. Those results must not be replayed to clear the historical
card. Its Alliance Activity partial result has missing expected governors and is
not classified as a transient lock failure. Stats-alert and provider uncertainty
remain retained until their own exact receipts resolve them. Ark's expired
interaction response is a separate confirmed acknowledgement defect.

## Policy at each boundary

| Boundary | Waiting/retry policy | Evidence that still blocks |
| --- | --- | --- |
| Shared-output root producers | Fair process-local queue before SQL; nested synchronous calls reuse the turn; 900-second maximum wait before non-entry refusal | Stale or cross-thread inherited turn, durable owner, SQL guard, fence/version mismatch |
| Short DAL transaction | At most eight attempts, 25–250 ms backoff, existing one/five-second contention allowance; connection time credited only within a 15-second cooperative total horizon | Anything except exact application-lock timeout -1 with acknowledged rollback and close; parent deadline always wins |
| External or caller-owned cursor | No inner replay | Outer transaction owns rollback and outcome |
| Guard construction before producer entry | Close guard connection, then exact compare-and-set to unavailable and release | Failed/unknown close or compare-and-set preserves claim; original error is retained |
| Producer transaction, atomic checkpoint, capture | Never replay producer because later coordination fails | Unknown commit, partial work, changed generation and missing receipt |
| Discovery/review snapshot | Released row-lock timeout 1222 or exact application timeout becomes waiting; next cycle/recheck observes again | Failed rollback/close, cancellation, deadlock, permissions, transport loss and uncertain commit remain errors |
| Recovery actions | Cards sharing account/storage scope and source identity share local exclusion; SQL remains authoritative | Parent and child identities retain their own SQL exclusion; local guard grants no durable authority |
| Provider dispatch | No mutation replay added; job/attempt/spacing settlement retries only rolled-back SQL transactions | Unknown request outcome or stream closure remains unresolved |
| Health probe | Pre-dispatch, fully released admission timeout means deferred | Any failure after client/request entry stays unresolved |
| Historical ProcConfig attempt | Original immutable failure plus exact operation/account/storage link to verified recovery | Missing, conflicting or corrupt linkage and unrelated later success cannot close the original incident |

These are cooperative scheduling bounds, not promises that an individual driver
call can be interrupted at the deadline. Existing driver timeouts and runtime drain
remain in force. Already accepted runtime calls drain; shutdown refuses new roots.
No age-based ownership expiry, lock deletion or blanket timeout extension is added.

Stats recovery intent crosses the asynchronous offload boundary as data only. Its
worker acquires the scheduling turn inside `admitted_writer`, retaining it through
capture and settlement. The event loop never waits on the synchronous producer
queue. Regression coverage uses the real offload for normal stats execution and
lost-capture acknowledgement, plus a queued-worker test proving loop progress.

## Family and wait-edge coverage

The scope inventory examined 774 tracked application Python files, routing explicit
and indirect SQL/offload/wait candidates into 13 families. The private scope packet
retains the callsite and file inventories. This table is the semantic disposition;
an inventory match alone is not a claim of a defect or complete dynamic SQL audit.

| Family | Disposition and regression coverage |
| --- | --- |
| F01 connection/account/resource/row order | Retry wrapper and job DAL include later authorization and settlement. `test_export_contention`, `test_preparation_request_contention_sql`, `test_coordination_lifecycle` cover connection budget, non-retryable cleanup and inherited deadline. |
| F02 legacy writer/configuration/publication | Root scheduling spans function body and settlement; guard-construction non-entry closes only with exact proof. `test_legacy_export_snapshot`, configuration/read/producer SQL suites and combined overlap test. |
| F03 import/pipeline/report continuation | Known live import and busy/changed pipeline snapshot are typed waiting; business checkpoint and partial-import semantics unchanged. `test_processing_pipeline_receipts`, import capture and report continuation SQL suites. |
| F04 discovery/review/repair | Cheap unowned-hold discovery removes the broad update-lock scan; action confirmation retains it. Canonical source exclusion, released observer waits and durable original-attempt closure. Monitor/race/view and unowned-hold SQL suites. |
| F05 authority/pacing/settlement | Existing authority session lock reentry and request reservations remain unchanged. Typed busy response is restricted to inspect. Job DAL retries SQL only; provider methods are outside retry wrappers. Export execution, request budget, reconciliation and lost-outcome suites. |
| F06 pools/replacement/rollover | Account → sorted resource → pool/row order retained; immediate exclusion refusals are not changed into long waits. Existing replacement/lifetime/containment tests exercise unchanged boundaries. No new pool, URL, claim expiry or rollover eligibility policy. |
| F07 startup/offload/drain | Synchronous report/configuration roots queue before SQL; copied stale or parallel contexts refuse. Existing runtime-composition and cancellation/offload tests cover retained children, self-drain exclusion and reconfiguration. No generic offload rewrite. |
| F08 cache/health | Shared producer queue prevents simultaneous local report rebuild roots. Existing health task remains shielded and reused; pre-dispatch probe contention defers. Cache and health suites preserve last-known-good versus fresh-report distinction. |
| F09 event/reminder/views | Independent delivery/session/file locks are unchanged; no evidence joins them to export account contention. Full regression includes event cache, reminder, tracked-view and notification contracts. Natural live delivery remains operator acceptance. |
| F10 other domains | No shared export-lock causal edge established for MGE, registry, inventory, leadership, voting, location, honor or rally/fort work. Their exclusion policies remain intact. Ark join/select acknowledges before SQL and lost success-response does not replay signup. Missing Alliance Activity rows remain a data-completeness issue. |
| F11 evidence/UI | Attempt adapters feed the actual renderer for failure/success/unknown/repaired states; missing legacy summary has a safe display fallback. Exact linked disposition survives a new adapter instance and leaves journal bytes unchanged. |
| F12 host/deployment | Singleton, updater and protected drain locks are unchanged. One fixed complete source transition is required, including new helpers. Partial bundle, changed predecessor/successor and target-supplied authority are rejected. |
| F13 helper/telemetry | Queue lock is released while waiting and before business work. Observation context resets on failure. Existing atomic file, logging and diagnostic contracts remain unchanged; no evidence justifies unrelated helper refactoring. |

The two opposing recovery/settlement session-guard orders keep immediate exclusion
refusal. No waiting is introduced while holding a competing partial SQL snapshot.
Monitor classification occurs only after rollback and close. Queue waiting happens
before opening the producer's SQL connection. Authority account-session reentry
remains on the same session. These boundaries avoid moving waiting inside a cycle.

## Combined test and acceptance boundaries

New isolated SQL tests run the failed configuration attempt through guided retry,
atomic publication, capture, configuration-only disposition, a reconstructed adapter
and the real incident renderer. They repeat with a lost commit acknowledgement and
prove one producer call, immutable journal bytes and stable resolved state. A
separate overlap test holds a real row lock during report work, queues configuration
before SQL, defers a monitor read, then verifies commit and the later read.

Existing suites cover application/session locks, stale fences, interrupted capture,
partial import, duplicate callbacks, runtime drain, unknown provider replies and
retained output snapshots. Native tests use namespaced temporary SQL objects on
local K98DEV; provider clients are deterministic substitutes. They are not a live
MINI_AMD deployment, Discord callback, query-plan or provider-delivery certificate.

Historical hash-bridge fixtures authenticate exact successor bytes before walking
unchanged predecessor assertions. They do not authorize installation. The installed
updater alone selects the fixed 23-file runtime transition. Its larger member bound
applies only to this exact family; older transitions keep their 16-member bound.

## Deployment and verification

No SQL schema/procedure, dependency, environment or activation-flag change is
required. Deploy from reviewed private main using the protected updater after its
exact-version tool upgrade. The release handoff supplies target and package hashes.
Use Windows PowerShell 5.1 as administrator on MINI_AMD. Run the stable updater,
request `/ops graceful_restart` once only when prompted for drain, and retain its
transcript, verified receipt and readiness result. Do not manually pull the live
checkout or start another process.

After deployment:

1. Verify exact source and successful protected source/seed/start checks, then
   Discord online. Degraded import/export readiness is not a reason to restart again.
2. Reopen the original ProcConfig attempt in Review & fix. It must render the
   original failure, show the exact verified recovery link and resolve only when
   that recovery is complete. Do not rerun the successful repair/import.
3. Export a fresh recovery report after a completed monitoring cycle. Verify no
   pending repair for this operation, preserved original history and resolved
   linked disposition. Counts alone are insufficient.
4. During the next ordinary report/import, look for progressing/waiting states,
   then committed stage/capture/disposition receipts. A transient wait should not
   become a new failed business operation. Retained unknown outcomes stay open.
5. Verify normal export by the exact provider receipt and visually checking the
   affected existing sheets. The supplied Report 53 receipt remains dated evidence.
6. For the next normal Ark signup, verify acknowledgement, one roster entry and
   correct visible state. If response delivery is lost, inspect the roster before
   trying again. No forced production signup is required for this release.

If contention persists, retain the stage, operation identity and existing bounded
SQL capture. Correlate waiter and blocker; never infer the holder from the requesting
session alone. The earlier reviewed capture has a separate stop script; do not
enable an unbounded replacement trace. Unknown commits/provider outcomes, missing
governors, Daily KVK Overview, WS1–WS6 and natural P0 rollover/F01–F05 acceptance
retain their own evidence requirements.

Interrupted deployment resumes from its retained release receipts. A downgrade
requires a reviewed reverse transition or forward correction; do not reset/clean
the live tree, erase attempt history, release uncertain ownership or replay work.

### Deferred Optimisation
- Area: services/recovery_runtime.py / history discovery adapters
- Type: performance
- Description: Historical discovery can take over 100 seconds. Current evidence does not identify a specific slow query plan; the correction separates waiting from failure but does not optimize all history scans.
- Suggested Fix: Profile per-query plans and stage timing, preserve rotating history coverage, then scope measured index or cadence changes.
- Impact: medium
- Risk: medium
- Dependencies: Correct released-observation and durable receipt contracts; this does not defer any demonstrated self-conflict in the corrected paths.
