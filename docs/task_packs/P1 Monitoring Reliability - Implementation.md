# P1 monitoring reliability

The operator approved local implementation on 26 October 2026 following the
monitoring/startup scope review. Publication, merge, deployment, restart and live
SQL/provider operations remain separate. The event-delivery release is the base;
this document does not reopen completed report/cache recovery.

## Increment A: monitoring evidence

The monitor retains separate current, last-completed and last-failed cycle
snapshots. Beginning a cycle no longer discards the prior original failure.
Recovery marks the failure historical. Snapshots are copied under a process-local
lock; original failures are also logged with the existing safe diagnostic shape.
SQL incident/action records remain authoritative. Restart begins unestablished;
logs preserve historical discovery failures but do not certify a new process.

Result freshness remains 90 seconds. Observer progress is a separate state:
starting, idle, progressing, waiting or stalled. No-progress beyond 300 seconds
(the existing health-probe investigation horizon) or total cycle age beyond 900
seconds reports stalled. These are conservative diagnostic limits, not measured
production percentiles, cancellation deadlines or retry authority. Real stage/item
checkpoints advance progress; timers cannot manufacture progress. Controlled tests
cover the retained 100.7-second cycle and the 30-second post-cycle interval.

Checks degrade immediately. One transient timeout/attributed lock-refusal cycle
does not publish a new outage message; a second consecutive failure does. Hard or
unclassified failures notify immediately. Normal due incident notifications remain
independent. The first successful required-check cycle ends the outage episode.
Notification work is timed separately from inspection. Stalled work remains owned;
its state is visible in reports, not proof of process-wide external supervision.

Private status retains defer error type, HTTP status/code, elapsed time and the
creation-time source. An unavailable timestamp is explicit. A local interaction-ID
decode supports context shapes without created_at; no token or identifier is
logged. Failed acknowledgement starts no health checks; no public/DM fallback or
webhook replay is added. The Boolean safe_defer API remains compatible.

Existing admission contexts now identify recovery and health callers separately,
including a process-local invocation correlation. Retry budgets, SQL mutex order,
fences, owner checks and producer entry are unchanged. The historical generic
monitor failures and competing SQL holder remain unknown.

## Increment B: bounded work and shared health

Accepted repairs and failed/open incident pages now precede discovery, with
incident/source deduplication within a turn. Private-evidence history runs last,
using the existing 100-reference page and a cooperative 10-second slice. At least
one reference gets a turn; an individual slow operation can exceed the budget and
is allowed to finish. Existing active page limits remain unchanged. This is not a
wall-clock cycle guarantee when SQL, a repair or a provider call is slow.

The cursor advances attempted references, including failures, to prevent one bad
reference starving later history. Original sanitized failures remain in coverage
diagnostics, and historical failure stays unconfirmed until a complete subsequent
clean wrap-to-wrap sweep. An unrelated successful page cannot clear it. The
same applies to a sweep containing waiting or deduplicated checks whose actual
verification is not established; a successfully observed empty catalog can clear
an initial inventory failure. Regression tests cover both review corrections. The
catalog can change during a sweep: coverage is explicitly rotating and never a
transactional completeness certificate. Inserts before the cursor are seen on a
later wrap. Coverage exposes slice attempts, elapsed time, budget exhaustion,
sweep start/age, wraps and unresolved failure; restart resets process-local
coverage. The typed read-only `pending_page` authority operation returns the wrap
signal; the existing `pending` contract is unchanged. Bot and authority must be
released together, using the existing protected paired-release process.

The deterministic 17,631-reference workload models one second per inspection.
The old discovery-first order delays an existing active check by 100 seconds;
the new order reaches it before history, then inspects ten references in ten
seconds. The new history target is therefore ten items per turn in that fixture,
versus 100 before. At a 30-second post-cycle interval and no other costs, a sweep
takes approximately 19.6 hours rather than 6.4 hours. These are controlled workload
figures, not production measurements or an SLA. Actual throughput depends on RPC,
SQL and protected-copy costs; slower historical damage detection is the explicit
tradeoff for timely active checks. Resolved evidence remains eligible. A single
21-second item finishes once and the next turn resumes at its successor.

Routine alert counts use scoped open incidents and dispatched/unknown actions
without historical JSON aggregation. Full report queries and completeness rules
are unchanged. No new SQL objects/indexes are required. The dashboard SQL check
now shares the operator status service's retained worker, timeout/pending result
and shutdown drain; missing dependencies cannot fabricate a healthy connection.
Startup lock retries, provider work and ownership policies remain unchanged.

### Deferred Optimisation
- Area: `services/recovery_dal.py`, `services/recovery_backlog_dal.py` and SQL recovery indexes
- Type: performance
- Description: Active notification counts no longer aggregate historical JSON, but the pending-action join and open-page queries still have unmeasured SQL costs. The current incident index orders LastSeenUTC while page cursors order FirstSeenUTC. The controlled history budget does not establish a production detection-latency target.
- Suggested Fix: Use the new stage/coverage evidence to measure routine SQL and protected-copy costs, then scope any index or history cadence change separately with a disposable SQL fixture. Preserve complete reports and exact action ownership.
- Impact: medium
- Risk: medium
- Dependencies: Representative timing evidence; separate SQL repository review for index changes; explicit authorization for any live measurement.

## Validation and boundaries

Completed local checks, resolved review findings and remaining limits are recorded
in [Validation and Review](P1%20Monitoring%20Reliability%20-%20Validation%20and%20Review.md).

Use focused monitor, startup-diagnostic, notification, private-response, interaction
safety and retained-health suites. Add next-cycle retention, sanitized discovery
failures, current-failure degradation, long progress, real stalls, total-age limits,
actual Pycord timestamp shape and notification-episode tests. Final integrated work
requires architecture/deferred/security-routing validators, selector, full offline
regression, log isolation, smoke imports and command registration. Security review
is Changes-only with Deep off against the final immutable range.

The SQL source-of-truth review used 1e95e41d; no SQL schema, ProcConfig, permission,
output format, activation or provider retry change is required. Installed SQL has
not been queried by this implementation task.

Preserve the complete R01–R18 ledger in the Startup Cache Foundations closeout and
the event-delivery implementation acceptance overlay. All six exercised foundations
packages and completed report/cache recovery stay accepted. Natural reminders/DMs,
overview lifecycle, loaded-empty to populated transition, exact historical overview
disposition and wider WS1–WS6 residuals remain open. The original Ark callback and
Location checks stay passed. P0 genuine F04 rollover, every-row F01–F05 reconciliation
and fresh-runtime import/export remain separate; earlier accepted scans, eleven-sheet
confirmation, URLs, receipts and abandoned dispositions are unchanged.
