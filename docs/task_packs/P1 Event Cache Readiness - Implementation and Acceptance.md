# P1 event-cache readiness — implementation and acceptance

Date: 2026-10-25. Scope: the approved WS3 empty-but-ready slice, including shared
refresh ownership, truthful outcomes, and per-member startup recovery. The
operator's subsequent implementation approval supersedes the review-only stage
in the [25 October handoff](P1%20Next%20Phase%20-%20Handoff%20-%202026-10-25.md).
This approval covers local implementation and validation, not merge, deployment,
restart, SQL/provider operations, or activation changes.
The subsequent PR-stage approval also covers opening mirror/production PRs and
addressing review feedback. Both PRs must remain unmerged for operator review.

## Baseline and custody

Development starts from mirror main `92c97949ea987fe7b71ac619042e09dd2f529955`
in managed worktree `event-cache-readiness`, branch `codex/event-cache-readiness`.
Documentation PRs #440/#689 are already present; their content is not reapplied.
The 24 October deployment of private source
`d127cb6e08aaecf0a397b9f5a3d41279280b245c` remains the last verified runtime.
Local source/test evidence does not establish what production loaded.

Work follows the [Windows ownership/access contract](../reference/Windows%20ownership%20and%20access%20contract.md).
This is a development checkout on 9SX2VF4, not MINI_AMD or protected live source.
Worktree creation and local test writes use the app's managed checkout and scoped
sandbox approval. No ACL/owner changes, credential copies, updater preparation,
provider probes or production repair form part of this slice.

## Problem and resulting behavior

Previously, collection truthiness treated a successfully loaded empty calendar
as unavailable. Startup could fetch twice, deferred scheduler admission expired
after one background window, and failures could leave part of the bundle started
without per-member accounting. Refresh callers could infer success from an integer
count, and a swallowed persistence error could look like a saved cache.

The new implementation separates these facts:

| Fact | Meaning |
|---|---|
| Availability | Unavailable, loaded empty, or loaded populated; zero upcoming events is valid. |
| Freshness | Age of the actual last successful snapshot; stale data remains usable as before. |
| Fetch outcome | Succeeded, failed, pending, or interrupted; failure does not advance the snapshot timestamp. |
| Persistence | Saved or failed for the published generation; memory-only success is explicit. |
| Startup | Each registration/one-shot has its own state and attempt count. |
| Delivery | Independently evidenced elsewhere; cache success, registration and attachment do not prove delivery. |

## Ownership and layer boundaries

`services/event_cache_service.py` owns one refresh task per process. It depends on
injected adapters, without Discord, provider, filesystem, SQL or configuration
imports. `event_cache.py` retains the existing facade and supplies those adapters.
`event_data_loader.py` selects one worker per range and drains the original worker
on cancellation. The established thread-draining helper is reused through the
adapters; the export coordinator and its authority are not modified.

Startup, periodic and manual refreshes join the active owner. A caller's observation
deadline detaches only that caller. The loader deadline cancels and drains the
original loader group; it does not release ownership while a thread is still alive.
There is no fallback execution after entry and no automatic fetch retry. A later
scheduled/manual invocation may start a new attempt only after termination.
Transport timeouts remain applied to the selected provider path. Thread drainage
may exceed the observation deadline; this is not a hard process-kill guarantee.

The disk envelope remains `{events, last_refreshed}`. Whole-candidate validation
precedes publication; malformed rows or timestamps retain the prior live snapshot
and disk bytes. Blank/valid past-only sources may produce a healthy empty calendar;
malformed source data cannot silently become healthy empty. Existing recent-cache
protection on an empty fetch is preserved and reported as retention by policy.
An exact candidate is atomically saved before live publication. A save failure
still permits valid live data but labels it memory-only. No fabricated timestamp,
partial-source publication, schema migration or durable exactly-once claim is added.

`core/event_rehydration_lifecycle.py` performs one startup refresh observation when
needed. The service owns late completion, avoiding a second background fetch race.
`core/scheduler_lifecycle.py` owns the startup ledger. `bot_instance.py` declares
the existing members and closes admission before teardown awaits, then drains
owned refresh/one-shot work before stopping its supervisors.

## Startup manifest

| Member | Admission | Completion and retry |
|---|---|---|
| periodic_live_embed_update | Available cache, including empty | Register once through TaskMonitor. |
| daily_kvk_overview | Available cache, including empty | Register once; existing daily publication policy unchanged. |
| schedule_event_reminders | Available cache, including empty | One registration; DM initialization/restore gate below. |
| event_embed_expiry | Available cache, including empty | Register once; expiry policy unchanged. |
| refresh_reminder_format | Populated usable cache | One owned task; observe past eight seconds; never replay uncertain edits. |
| rehydrate_live_event_views | Populated usable cache | One owned task; observe past ten seconds; partial/unavailable is explicit. |

Proven pre-registration failures alone retry, with at most three attempts and
one/five-second delays. A registered member is not restarted by this ledger;
TaskMonitor retains its existing runtime supervision. Reports distinguish recorded
registration from `currently_running`. Entered one-shots remain observed after a
deadline; errors, cancellation and uncertain results are not automatic retry signals.
The cache readiness observer stays available across repeated 300-second windows.
It reads state and never probes providers.

The reminder scheduler alone loads DM trackers once. The later `on_ready` duplicate
reload is removed. Unavailable/empty event data defers restoration without pruning
markers. Once populated data is available, persisted scheduled work is restored
before normal scheduler admission. Invalid tracker reads or partial restoration
remain unconfirmed and block automatic re-entry. Existing marker eligibility,
send policy and user-task supervision are retained; this does not settle broader
send-versus-disk uncertainty or the historical eligibility backlog.

## Interfaces for subsequent work

- `get_upcoming_event_cache_snapshot()` is a read-only copy with availability,
  timestamp, freshness, generation, source and persistence. Consumers must not
  equate `bool(events)` with readiness. Generation is process-local provenance,
  not a durable source version or business receipt.
- `refresh_event_cache_result(observation_seconds=...)` returns the structured
  outcome and whether the caller joined. The legacy integer facade remains for
  existing callers; new control/diagnostic code should use the structured result.
- `refresh_service.report()`, `event_startup_report()` and `dm_startup_report()`
  are included in the existing recovery report. They perform no provider work,
  registration, replay, or settlement. General monitoring health remains separate.
- Existing private admin refresh commands report retained/memory-only/pending
  outcomes and actual cache timestamps. Publication is described as attempted;
  the existing publication APIs do not provide independent delivery receipts.
  Command names, permission decorators and channel restrictions are retained.

These interfaces give WS2 an observable no-reentry example, WS4 explicit startup
ordering and snapshot boundaries, and WS5 separate preparation/publication facts.
WS1 and WS6 can reuse the outcome vocabulary and read-only reporting pattern,
but must continue using their existing SQL authority and durable receipts. This
in-process cache owner must never be substituted for ProcConfig admission.
Independent monitoring can consume the report without causing a recovery action.

## Validation and security routing

Deterministic coverage includes loaded-empty/unavailable/stale/past-only data,
malformed source/disk data, preservation policy, failed atomic persistence,
overlapping observers, actual worker drainage after timeout/cancellation, shutdown
admission closure, deferred recovery after multiple readiness windows, partial
registration, non-replayed uncertain one-shots, DM initialization order, corrupt
tracker retention, command permissions, and truthful command responses.

Run the focused tests, full pytest through `analyse_pytest_log_noise.py`, changed-file
Black/Ruff, architecture/deferred/security-routing validators, test selector,
import smoke with synthetic test configuration, and command-registration audit.
Local evidence and any limitations are recorded in the implementation handback.
No live credential, Discord, SQL or provider verification is part of these tests.

Security routing: **Changes**, Deep off, final working-tree patch against the
baseline above, including new files. Review parsing, fixed filesystem destinations,
permission preservation, diagnostics, worker ownership, cancellation and restart
state against `SECURITY.md`. Tests do not replace this diff review. No SQL diff
exists and no SQL execution/schema validation is needed for this implementation.

### Local validation result

The full suite completed with 9,252 passed, 1,080 skipped, seven failures, one
dependency warning and eight subtests passed (1,603.70 seconds). All seven failures
were caused by test boundaries changed in this slice: five historical runtime-hash
assertions encountered the new source images, and two isolated teardown fixtures
lacked the event-bundle dependency. No runtime fix was required after this run.

The teardown fixture now supplies isolated cache/bundle owners and asserts their
admission closure and drainage. A test-only bridge checks the exact new hashes of
`bot_instance.py` and `services/recovery_health.py` before comparing the unchanged
historical release hashes. Negative tests reject foreign bytes. This changes no
production transition registry, deployment guard or installed updater capability.
Promotion must separately reconcile protected-source compatibility; these test
fixtures are not installation authority.

The corrected affected suites passed 113 tests with operational logs unchanged.
Every caller of the historical-source test helper was then checked: 134 passed.
At that checkpoint the full suite had not been rerun after the test-only
corrections; the original failed run remains historical evidence. Black/Ruff, diff whitespace, architecture,
deferred-item/security-routing validators, test selection, synthetic-config import
smoke and command registration passed. The active command surface remains 36
primary commands and 102 grouped subcommands. Existing platform/integration skips
were retained, without adding skips to obtain passing results.

Changes security review `7fb922a8-b6a5-48ca-aba9-fc628f3b95cd` completed against the
runtime patch with all ten source items reviewed and zero reportable findings.
It included a fresh-context architecture review. Subsequent edits were confined
to test fixtures/negative tests and these documentation results: no runtime,
permission, provider, persistence, configuration or deployment behavior changed.
Those follow-up edits receive a documented security-review skip; the runtime
source reviewed by the completed scan is unchanged. No live acceptance is claimed.

### PR-stage validation and review correction

The corrected mirror implementation at `97f9b5a` subsequently passed the full
suite: **9,261 passed, 1,080 skipped, one dependency warning and eight subtests
passed** in 1,109.47 seconds. The log-noise harness confirmed operational logs
unchanged. Pre-commit, including secrets scanning and Pyright, passed.

Mirror PR #441 identified one startup regression: a marker removed under the
existing fetch-failure cleanup policy was counted as uncertain even after a
successful save, blocking other subscribers. Commit `56e08e67` corrects that
classification in both delayed and immediate restoration. Failed saves and
per-item uncertainty still block re-entry. Six new regression cases exercise
both paths, another subscriber, persistence failure, item failure and repeated
startup observation; the focused suite passed **18 tests**, with operational
logs unchanged. Marker eligibility/deletion and retry policies are unchanged.

The initial full run above predates this bounded correction. Production full-suite
results and exact final-head review/check evidence are retained with the PRs;
do not describe a pre-correction run as final-head execution. Incremental Changes
scan `00476fb3-4fac-4f97-a957-3a7e09bb795d` covered the correction without findings.
Production Changes scan `3c6ce67f-d06c-4166-8369-bd63255c11d7` reconciled all
ten source files to the reviewed source and correction, also without findings.

A further production review found that the compatibility bulk loader returned
`None` for `retained_by_policy`, despite a successful fetch and deliberately
preserved cache. It now returns cached events for the three successful outcomes;
failed, pending, closed and cancelled outcomes remain `None`. Eight added cases
cover retained/memory-only/empty availability and failure boundaries. The combined
cache, loader, startup and command suites passed **68 tests**, with operational
logs unchanged. Incremental security and final-head CI/re-review receipts for this
bounded correction are recorded in the PRs; the earlier full-run counts must not
be attributed to this later source revision.

An unconfirmed DM restoration still requires separately reviewed operator recovery;
it is not automatically replayed. Existing marker deletion after failed user fetch
remains a separate durability obligation. Startup completion records historical
registration; consumers must also inspect current liveness. Thread drainage relies
on the configured transport returning. None of these local results settles runtime
acceptance or protected-updater compatibility with the actual installed version.

## Acceptance and explicit residuals

Local acceptance requires the deterministic cases and validation above, truthful
partial/unknown reporting, and no new provider entry after observation timeout.
Runtime acceptance requires separately authorized promotion/deployment followed
by naturally occurring observations. Do not generate events, force rollover,
restart, repost or reopen historical workflows to manufacture acceptance.

Remaining WS3 work stays separate: exclusive process/singleton ownership after
protected-launcher review; public-reminder child send/delete/expiry supervision;
historical tracker eligibility/reporting; and outstanding runtime acceptance.
The live-button check still requires a naturally eligible original message with
visible controls after a natural restart, a direct message link and the safe
private local-time callback. Closed/cancelled historical Ark posts are unsuitable.
The exact Daily KVK Overview deletion/access disposition remains unresolved.
Updater custody and stream diagnostics remain independently scoped.

The [programme status](../reference/P0%20delivery%20and%20P1%20recovery%20status.md)
continues to own all three P1 families and every WS1–WS6 residual: legacy ProcConfig
outcomes/artifacts; legacy executor caller inventory; remaining process/child
ownership; broader DM/JSON ordering and durability; fighting/KS/Pre-KVK dispatch
and ambiguous publication; and independent writer admission audit. This slice
provides foundations, not completion credit for those obligations.

P0 natural eligible rollover and final F01–F05 reconciliation remain open. Preserve
accepted import/export and visual confirmation evidence. Do not replay accepted
operations, clear claims, alter activations or infer production acceptance from
local tests, loaded caches, registration counts, or monitoring health.
