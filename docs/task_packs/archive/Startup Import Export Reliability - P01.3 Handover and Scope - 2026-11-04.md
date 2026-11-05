# P01.3 handover: passive health presentation

> **Archived 5 November 2026.** This completed record is archived; its original design/release instructions and pending gates are historical. Current outcome: [P01.3 closeout](Startup%20Import%20Export%20Reliability%20-%20P01.3%20Closeout%20-%202026-11-05.md). Next task: [P01.4 review/scope](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Handover%20and%20Scope%20-%202026-11-05.md).

> E81 implementation update: P01.3 runtime and persistent Refresh are implemented locally. Local validation and both independent PR packages are complete; see the [implementation receipt](Startup%20Import%20Export%20Reliability%20-%20P01.3%20Implementation%20and%20PR%20Readiness%20-%202026-11-04.md). Earlier design-only status is historical. No publication or deployment has occurred.

Current E80: full P01.3 implementation, local validation and PR preparation are authorized, including persistent Refresh. Recheck equivalent callers, full H01-H09 coverage and value/non-interference throughout. Earlier design-only holds below are superseded for this implementation; operational actions remain separate.

Current E79, 4 November 2026: the operator agrees 60-minute provider observation freshness, separate existing 90-second recovery-monitor semantics, lock-free reads of immutable published summaries, and re-reading on the existing five-minute dashboard refresh without new retry tasks. Alerts must identify an actionable impact beyond rechecking; card/command use common interpretation and existing notification routes with appropriate navigation. Report integration, telemetry/cost gates and narrow lifecycle corrections are retained. The operator accepts user reports for rare whole-bot outages; no new outage detector is required. The reported Health card timeout adds a proposed persistent Refresh button, prompt acknowledgement and bounded restart registration/migration using the existing message ID. The design packet supersedes E78's try-lock and preserved-timeout choices. Implementation is not started or authorized by this design agreement.

Current E77/E78, 4 November 2026: the operator approved this scope for design and agreed removal of automatic health-card log scans and the last-20-errors button, retaining explicit log inspection. The count-derived spike notification is removed with those counts. The [design and qualification packet](Startup%20Import%20Export%20Reliability%20-%20P01.3%20Design%20and%20Qualification%20-%202026-11-04.md) records the caller/evidence inventory, concrete proposed contract, coverage trade-offs and H01-H09 gates. Design is delivered for review; implementation and operational actions remain unapproved. Do not ask again whether the passive scope or log-feature removal is wanted.

Status: E76, 4 November 2026. P01.2b closeout is complete by operator decision, without deployment. P01.3 is the current review/scope task; implementation is not authorized by this handover. Keep the solution issue-driven and proportionate.

## Operator requirements carried into every review and implementation

User reinforcement, 4 November 2026: no point fixes. Keep the whole solution in mind and choose the best proportionate solution for the bot, not merely a patch for the reported symptom. These requirements must remain in subsequent plans, reviews, tests and handovers:

- Trace the root cause, affected layers, shared helpers, callers and equivalent situations. Search related commands, dashboards, background refresh, report/detail readers and restart/shutdown paths so the same issue is not left elsewhere. Record the searched surfaces and dispositions; do not equate a single passing caller with a complete fix.
- Make tightly related corrections together when necessary for a coherent solution. Keep unrelated work explicitly owned and scoped; whole-solution thinking is not permission for an unbounded rewrite or a repository-wide security scan.
- Every added component and operation must prove its worth against an actual problem. Compare reuse, simplification/removal and doing nothing before adding infrastructure. State the expected operator benefit, complexity and resource costs; set proportionate acceptance limits before qualification and retain adverse results.
- The solution must not introduce blocking dependencies, locks, contention, avoidable latency, incident amplification or failure propagation into bot/business/startup work. Trace scheduling, I/O, physical worker ownership, cancellation, cleanup and failure paths. Optional evidence must not become a prerequisite for business progress or cause retries/duplicate work.
- Prove the behavior with baseline comparisons, deterministic negative tests and representative cost measurements appropriate to the eventual change. Include absent/stale/malformed evidence, concurrent/repeated use, slow or failed dependencies, restart and shutdown. Separate measured facts, design arguments and remaining uncertainty; a timeout is not proof a worker has exited, and finite tests do not prove zero risk.
- If value is insufficient or non-interference/cost limits fail, stop, simplify or decline the proposal. Never weaken acceptance to justify the chosen implementation. Preserve mandatory operational checks at actual write boundaries.

For P01.3, the deliverable of the initial review is a related-caller map, a reusable-evidence inventory, the smallest coherent design, explicit coverage trade-offs and a cost/non-interference validation plan. No implementation, deployment, restart or live probe is authorized by starting the new chat.

## Source-confirmed starting point

F11 records that viewing status/health can start SQL and Google Sheets probes. Initial read-only inspection confirms this in retained mirror HEAD `6f58f87829de1f663eda8a091c9169dc5afd6ca6`, clean at review time: `commands/admin_cmds.py:1142` calls `check_sql`, and line 1154 calls `check_health`; `bot_instance.py` refresh and pinned-card update call both health helpers. `HealthProbe.observe()` in `services/gsheets_health_service.py` creates a task when none is retained; `operator_status_service.check_sql()` supplies the SQL connection operation. Task sharing limits duplicate work but does not make a display request passive. These are local source facts, not fresh production measurements.

Expected value: stop presentation from creating unnecessary SQL/provider work and avoid implying old evidence is a fresh health check. No new diagnostic infrastructure is required by this objective.

## First review and proposed boundary

1. Recheck the suitable current mirror source before implementation; the root checkout is the older documentation workspace. Trace every status, refresh, pinned-card, helper and scheduled health caller, including alerts and cleanup.
2. Inventory existing observations and successful business activity that can be reused safely. Map provenance, timestamp, freshness, bounded retention and reset/restart behavior. Identify any actual missing evidence before proposing a producer.
3. Propose a pure snapshot/read path. Rendering may send/update its intended Discord message, but must not start SQL/Sheets probes, recovery reconciliation, repair, replay or other business work, even on a cache miss. Prefer existing helpers and narrow services; no new supervisor, startup observer, logging pipeline or autonomous probe cadence.
4. Show observation source/time and unknown, stale, in-progress or degraded states accurately. After restart or missing evidence, show unknown; never use cached status to authorize a write. Successful activity proves only that specific activity, not all provider permissions or destinations.
5. Review any retained explicit probe entrypoint separately. Preserve once-only sharing, physical worker ownership and shutdown semantics. P02 must justify active probe cost/cadence/non-interference; P04 owns prolonged-loss escalation. Do not remove mandatory checks at actual write boundaries.

## Affected areas and tests to select

Primary paths: `services/gsheets_health_service.py`, `services/operator_status_service.py`, `commands/admin_cmds.py`, and `bot_instance.py` health consumers. Review relevant `operator_status_dal.py`, underlying Sheets activity, callers and shutdown dependencies; no schema change is currently proposed. Validate any SQL-facing implementation assumptions against `C:/K98-bot-SQL-Server` before coding.

Six existing suites were verified present, not executed: `tests/test_gsheets_health_service.py`, `tests/test_private_status_response.py`, `tests/test_health_probe_cleanup.py`, `tests/test_health_probe_proof_admission.py`, `tests/test_health_activity_update_transition.py`, `tests/test_server_status_channels.py`.

Design deterministic tests proving zero probe/SQL/provider/recovery calls during status rendering, including empty/stale/error snapshots, repeated refresh and restart. Preserve permissions/redaction, response handling, truthful freshness, shared explicit-probe ownership and shutdown. Measure render cost only after the actual change is scoped; do not add probes to measure the absence of probes.

This handover is documentation-only: architecture/deferred/security-routing/test selection and link/archive checks apply; runtime tests and security scan are skipped. A future command/health/SQL-facing implementation requires the relevant skills and an exact Changes security review, Deep off. No full/deep audit is implied. Step 1 remains review/scope; present the smallest reviewable design and validation plan before coding.

[P01.2b closeout](Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Closeout%20-%202026-11-04.md); [P01 shared design](../Startup%20Import%20Export%20Reliability%20-%20P01%20Design%20-%202026-11-03.md); [tracker](../Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md); [documentation carry-forward](Startup%20Import%20Export%20Reliability%20-%20Documentation%20Carry-forward%20-%202026-11-04.md).
