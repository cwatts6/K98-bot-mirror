# P01: truthful outcomes, owned work and boundary evidence

> **Current E76 checkpoint - 4 November 2026:** [P01.2b closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Closeout%20-%202026-11-04.md) is complete by operator decision, without deployment. The design records are archived. Proceed with [P01.3 passive-health review/scope](Startup%20Import%20Export%20Reliability%20-%20P01.3%20Handover%20and%20Scope%20-%202026-11-04.md) (F11); no implementation or production action is authorized. Earlier next-task wording is historical.

> **Current programme checkpoint - 4 November 2026 (E68/E69):** P01.2a is deployed and accepted for its declared reporting/evidence scope at private `67c4e12a8ecf0c25280770860480ac65a6826602`.
> Read the [P01.2a closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Closeout%20-%202026-11-04.md) for delivered corrections, evidence limits, learnings and remaining owners; [P01.2b handover](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Handover%20and%20Scope%20-%202026-11-04.md) is the next review/design task.
> Earlier dated statuses, holds and next-action instructions in this document are retained history and are superseded for current scheduling. P01.3-P01.6/P02-P05 and exact incident recovery remain open; no replay of accepted work.

Date: 3 November 2026. Status: P01.1 deployed; exercised startup and diagnostic
behavior accepted under E55, following E54 review/merge (mirror #480/#481, private
#721). Private target: `0247371d90ec88d4c0639e9200164f4256086037`.
E56 amends the remaining scope using that production learning: deliver P01.2a
evidence collection/clarity first, then P01.2b early issuer evidence. This is a scope
amendment, not implementation approval for the remaining slices. F09/P02,
continuation/P03 and wider acceptance retain their separate gates.

E57: the user accepted this scope and requested a focused P01.2a chat. Read the
[P01.1 closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.1%20Closeout%20-%202026-11-03.md)
and [P01.2a scope/handoff](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Scope%20and%20Handoff%20-%202026-11-03.md)
for current task status and the implementation-ready design deliverable.

E58: the focused [P01.2a design and qualification packet](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Design%20and%20Qualification%20-%202026-11-03.md)
now supplies the concrete collection/outcome/milestone contract and resource bounds.
Its proposed slice-specific limits refine the earlier P01 budgets below. This is
design delivery, not approval or qualification of the runtime implementation.

## Scope summary and decision

Implement P01 as a family of focused changes, beginning with **P01.1: startup result
preservation and fault-isolated timing/evidence** (F08/F32). A startup observation
deadline must not cancel a configuration import merely to measure it. A diagnostic
failure must not prevent the worker from entering, replace its result or original
exception, or release physical ownership early. This is more than changing one
timeout flag: the first slice includes both startup paths, shared-helper callers,
completion verification, correlation, bounded diagnostic handling and cancellation tests.

The [agreed scope](Startup%20Import%20Export%20Reliability%20-%20Scope%20-%202026-11-02.md)
remains authoritative. The [tracker](Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md)
owns status. This packet supplies design detail under E51, not a replacement programme.
P01 -> P02 -> remaining P03 -> P04 -> P05 remains the delivery order. F09/51421 is P02;
F28 is remaining P03/P04. No global timeout increase or isolated 51421 retry is proposed.

P03a.1 remains accepted. P03a.2 and corrected startup are deployed/accepted as described
in E49; whole-flow functional acceptance and F02 closure remain open. Report 68 stopped
at configuration writer entry before export, after stats/player commits and captures.
Its actual production holder, negative application-lock result and hold duration are
unknown. The local native experiment proves an observer-first refusal mechanism, not
that the production monitor held that lock or that P03a.2 caused a regression.

## Evidence basis and affected areas

The existing C01-C16/B01-B15 caller census, 73 action pairs, 371 historical path
dispositions and separate 322-candidate final sweep were reused. This was a scoped
current-source design pass, not another repository audit. Counts are inventory
denominators, not production-qualified coverage.

Local source state checked for this design:

| Checkout | Revision / use |
|---|---|
| Project root | `a025adb7a69aac321fd62794b871ed5903338f44`, `codex/p1-mge-a1b-design`; older design source. Existing README/index edits and seven untracked programme documents preserved. |
| Existing private checkout `.codex_artifacts/a1b-updater-correction` | `b6ec4a0eeabd3d32d8fd98726ab8a6af5e6b829b`, `codex/p03a-failed-startup-recovery-production`; clean at entry; runtime source used below. This is a local source pin, not a fresh running-process observation. |
| Existing mirror checkout `.codex_artifacts/p1-mge-mirror-review` | `ed9e7f157f6c1ce40d7777a71a0697874a90ff60`, `codex/p03a-startup-recovery-reviewed`; clean at entry. |
| SQL source of truth `C:/K98-bot-SQL-Server` | `7e91989f619deb46836194c7e705b0a9eb2ebe11`, `main`; clean at entry. |

No fetch, branch switch, new worktree or remote-state claim is part of this design.
Before implementation, recheck mirror/private bases and changes; use a `codex/` branch
in the suitable existing mirror checkout. Promote the reviewed patch onto a verified
private base through the established process, never old mirror history wholesale.

Private evidence is retained under `.codex_artifacts/startup-import-export-review-20261102`:
`P01-Chat-Handoff-20261103.md`, `P03a2-Report68-Failure-Analysis.md`,
`p03a2-report68-failure-analysis.json`, `report68-native-guard-result.json` and the
new `P01-Design-Recovery-Dependency-20261103.md`. Exact operational IDs belong there,
not in mirror documentation. The earlier preservation ZIP is historical local backup,
not a current live-state receipt or authority to execute archived scripts.

## Architecture direction: four independent dimensions

Extend the existing [P1 operation lifecycle contract](../reference/p1-operation-lifecycle.md).
Do not introduce another coordinator, receipt authority, retry engine or incident store.

| Dimension | Values / transition rule |
|---|---|
| Observer | `pending`, `deadline_elapsed`, `observed`, `observer_cancelled`, `unavailable`. These describe a caller's knowledge, never a SQL rollback or remote absence. |
| Physical execution | `not_entered`, `entered`, `draining`, `settled`. Only worker completion/exception or the existing positive native termination proof establishes settlement. Cancellation of an asyncio proxy does not. |
| Business effects | A per-stage map: `not_entered`, `running`, `committed`, `rolled_back`, `unknown`; capture `absent/confirmed/unknown`; provider `not_dispatched/dispatched/confirmed/unknown`; publication and notification independently described. These are model values, not new SQL enum strings. |
| Evidence / ancillary output | Mandatory receipt `confirmed/pending/unknown`; diagnostic/audit/index/notification `available/degraded/unavailable/not_applicable`. Optional failure cannot undo a confirmed business effect. Mandatory receipt failure still prevents a claim of completed settlement. |

The operation result is a product of these dimensions, not a single success Boolean.
Existing Boolean/tuple APIs remain compatibility adapters at the edges. They must say
which dimension they represent. For example, configuration `ok=False` after a required
terminal receipt failure must retain `import_reported_success=True` if that is what the
worker reported; it must not be flattened into either verified completion or rollback.

State rules:

1. Establish an operation/attempt context at the real entrypoint, before offload. Reuse
   the existing durable operation identity where one exists; a diagnostic UUID never
   replaces it. Retries/continuations get distinct attempt IDs and a parent link.
2. Record admission and actual worker entry separately. Retain the execution owner
   until the worker settles, even if every UI observer has gone away.
3. At an observation deadline, publish `deadline_elapsed/pending`; keep the original
   owner task alive. Do not resubmit work or infer failure. A worker's own TimeoutError
   remains a worker error, distinct from an observer deadline.
4. Record commit, capture, publication and delivery at their actual authority boundaries.
   A returned function or successful timer is not a commit receipt.
5. A real shutdown cancellation closes admission according to existing policy and
   drains entered work. Preserve the physical result in the owner's settlement hook
   before propagating cancellation to the observer. Do not start a later business stage
   merely to finish an observation after shutdown admission closes.
6. Release local ownership after settlement; release durable SQL/provider ownership
   only through the existing exact authority/receipt path. A diagnostic `released`
   event reports that acknowledgement and cannot cause it.
7. On restart, reconstruct known effects from domain receipts, not the diagnostic
   timeline. Missing acknowledgements stay unknown. Attach a recovery observation to
   the original attempt and preserve its first failure separately from recovery success.

### Layer and helper placement

| Component | Design decision |
|---|---|
| `core/owned_work.py` | Canonical physical drain primitive. Keep its once-only execution and repeated-cancellation behavior. Add a narrow optional settlement-observation hook only if needed to retain a drained result; hook failures cannot change result/drain. Never make this helper retry, authorize SQL or infer commit. |
| `core/operation_timing.py` | Preserve `timing_scope`, `record_timing`, `timed_stage` compatibility. Clock, formatting, collection and emission are best effort. Keep inclusive timing semantics; never sum nested inclusive intervals as total execution. |
| Proposed `core/operation_evidence.py` | Small dependency-light context/value model for D01-D06 and safe fixed-shape event collection. Necessary because existing timing context is only a random local reference, while cache diagnostics support only a few origins. No Discord, SQL or filesystem dependency. |
| Proposed `services/operation_diagnostics.py` | Bounded projection/retention adapter for those records, using existing logging/redaction/file primitives. Diagnostics only, with no replay/recovery/admission methods. The concrete limits and drain rules below are part of its contract. |
| `core/startup_diagnostics.py` | Own observer state and completion-check observation. Config opts into non-cancelling deadlines explicitly; do not silently change every default startup task. |
| `services/configuration_attempt_recovery.py` | Keep mandatory attempt/phase journaling and strict v1 receipt validation. Optional evidence is a separate versioned diagnostic projection keyed to this receipt, not extra unvalidated keys injected into it. |
| `services/cache_admission_diagnostics.py` | Bridge existing identity/report API to the common context. Preserve `requesting_session_not_blocker`. Do not add SQL holder queries here. |
| Domain services/DAL | Own authoritative stage outcomes and transaction/receipt interpretation. Commands/upload routes supply actor and input identifiers, call services and render results. |
| Existing report adapters | Include the P01 diagnostic projection as optional, timestamped evidence using an allowlist. If absent/corrupt, report that gap without failing the domain report. P04 later combines history/policy across all packages. |

Reuse `services/export_publication_metrics.py` fault isolation, `core/coalesced_work.py`
single-flight ownership, existing event-cache pending/drain behavior, `file_utils.py`
atomic writes and telemetry, and `core/operator_diagnostic_payloads.py` redaction.
The generic telemetry helper already catches emission errors, but the shared logging
queue is a `SimpleQueue`; that alone does not meet the new saturation bound. Do not
solve this by making all existing application logging synchronous or globally changing
all callers. P01 evidence uses a bounded ingress and a dedicated managed sink.

The normal helper inventory was considered: `utils.py`, `process_utils.py`,
`logging_setup.py`, `bot_helpers.py`, `file_utils.py`, `embed_utils.py`,
`admin_helpers.py`, `target_utils.py`, `account_picker.py`, and interaction safety.
The governor registry is under `registry/`, not a new root helper. None supplies the
full boundary contract. Legacy `services/legacy_export_snapshot_service.py:drain_thread`
remains a thin compatibility delegate; no duplicate drain implementation is added.

## Common D01-D06 schema and propagation

Version the diagnostic envelope `operation-boundary/1`. Required fields cannot simply
be omitted: each applicability-dependent field is `{quality, value, reason, observed_utc}`,
where quality is `observed`, `not_applicable` or `unavailable`. Reasons are bounded,
code-owned classifications; last-known values carry their own observation time/age.
Null is not evidence that a resource or effect was absent.

| Record | Fields and interpretation |
|---|---|
| D01 | Envelope version, operation ID, attempt ID, parent operation/attempt, origin, step, transition, UTC, per-attempt sequence, evidence reference. Include existing pipeline/preparation/job/stream/request and release/incarnation IDs when applicable. Monotonic timestamps are process-local durations only. |
| D02 | Initiating actor kind and authorized private identifier; executing host, process incarnation (PID plus creation identity), task/worker identity, SQL connection instance and session ID with lifetime. A scheduled/startup actor is explicitly a service, not the last human who ran a command. |
| D03 | Resource kind/key or stable redacted digest, requested mode/scope; logical owner/fence/version; separately observed physical holder identity, owning operation/phase, acquired/released timestamps and source. Multiple holders use bounded entries plus exact omitted count; no arbitrary first-holder attribution. |
| D04 | Connect, admission, queue, lock-wait, hold, worker, commit, capture, settlement and cleanup durations and configured budgets, with `inclusive` annotation where necessary. Preserve original SQLSTATE/native code/applock return before wrappers translate it; retry/reschedule decision and cleanup acknowledgement are separate. |
| D05 | Per-stage effects, mandatory receipt references/verification level, worker settlement and remaining work. A normal return, cache replacement, SQL commit, provider response and released reservation are different facts. |
| D06 | Observation source, time, field quality, bounded reason for unavailable attribution, attempted method, loss/overflow counters and last successful observation. Old records are visibly old. No historical holder is inferred from a later local reproduction. |

Use ContextVar propagation for task creation and `asyncio.to_thread`; explicitly copy
context for executor APIs that do not propagate it. Existing process payloads are
strictly decoded: add a reviewed allowlisted metadata envelope to both sender and
receiver in the slice that needs that process hop. Never serialize runtime objects,
credentials, SQL handles or authority tokens. Missing context from an old payload is
`unavailable:legacy_payload`, not a new independent business operation. No protocol
change is needed for the first active-runtime configuration thread path; its legacy
process/fallback path still needs a compatibility test and an explicit limitation.

Application-owned local resources record acquisition/release at the owner, correlated
with the requester. Do not replace locks with diagnostic maps. Instrument existing
lock scopes rather than changing lock ordering. On uncontended entry, conflicting
holder is not applicable, while the newly acquired holder is observable. A controlled
contention test must identify the holder/phase; `unavailable` is a test failure there.
P02 supplies SQL acquisition/release and actual conflicting-holder attribution,
including connection recycling, transaction versus session ownership and implicit
row-lock waits. No additional privileged production collector is proposed by P01.

### Boundary coverage and package responsibility

Each row requires all six records. The combined D01/D02 column identifies correlation
and actor/requester; the remaining columns identify applicability rather than waiving
fields. T numbers refer to the executable qualification cases below. C/B labels refer
to the existing census, not a fresh coverage inventory.

| Boundary / census | D01/D02 context | D03 ownership/holder | D04 measurements | D05 effect / D06 quality | Implement / qualify |
|---|---|---|---|---|---|
| Launch before incarnation; B07 | Release/start intent, launch attempt, administrative issuer PID/create time; successor only when created | Launch mutex/native process owner; SQL holder N/A until connection | Preflight, spawn, exit, journal appearance separately | Exit is not pair termination or readiness; pre-journal evidence explicitly labelled | P01.2; T04 |
| Startup schedule and observation; C01-C03 | Startup incarnation -> config/player/profile/name attempt; system actor | Tracked task and original child | Observation budget vs actual elapsed | Late result retained; receipt verification may remain pending | P01.1; T01/T03 |
| Async -> thread/process; C01-C04/C10/C14-C15 | Same operation, distinct worker identity; initiating actor preserved | Physical worker and caller scope, not cancelled proxy | Queue vs physical execution vs drain | Exactly one invocation; outcome hook cannot claim SQL commit | P01.1 shared primitive; each adopting slice; T02/T03 |
| SQL connection and authorization; C02-C06/C09-C16 | Connection instance/session lifetime mapped to operation | Requesting session separate from logical owner and blocker | Connect vs query vs admission budgets | Failure before body entry is non-entry only when proved | P01 correlation; P02 SQL instrumentation/budgets; T09 |
| Account/global snapshot/row locks; C03-C07/C16 | Preparation/operation and stream/request if present | Account owner/fence/version vs actual SQL holder and lock scope | Preserve 51400/51421 and original return separately | Cleanup acknowledged or unknown; known-holder attribution mandatory | P02; T09/T13; P01 leaves explicit dependency |
| Config/stats/player SQL and capture; C02-C05 | Existing operation/preparation/attempt/pipeline links | Existing writer ownership and capture fence | Execution, commit, capture, cleanup separately | Atomic receipt + captured hash; never success from wrapper timer | P01.1 context; P02 contention; P03 convergence; T01/T10 |
| Pipeline stage/queue handoff; C04-C05 | Parent pipeline, stage operation, distinct notification run | Existing preparation/job authority | Handoff vs observation vs settlement | Completed stages preserved; absent export job means not dispatched only with exact evidence | P03; P01 adapters preserve meaning; T10 |
| Provider dispatch/result/pacing/terminal; C06 | Session/stream/request/sequence and parent producer | Provider stream owner distinct from SQL admission holder | Request execution vs result recording vs pacing vs close | Saved response is not durable terminal/closure; no resend | P03 (accepted P03a retained), P02 holder; T10/T13 |
| Passive status and pinned health; C08 | Viewer request is separate from last health operation | No new business resource/owner; cite last observation | Render cost and evidence age only | Unknown/stale/degraded explicit; cached health cannot authorize writes | P01.3; T05 |
| Active probes/background observation; C07-C08/C16 | Explicit monitor/probe actor and its own operation | Its resources and physical worker recorded; not the UI viewer | Cadence, admission, cleanup, deferral | Probe result does not establish producer outcome | P01.3 separates entrypoints; P02 non-interference; T05/T09 |
| Upload parse/ingest/audit/refresh/notify; C10-C13/B04 | Human/source event -> import batch and stage attempts | Staging/ingest owner vs audit connection vs refresh owner | Each stage separately; audit queue wait separate | Ingest, audit, refresh and notification outcomes independent | P01.4; T06/T11; P03 Rally retry identity remains separate |
| Fallback staging/CSV/ack; C10/B04 | Queue item -> staged callback -> durable importer ID | Processing lock, active-job identity, actual callback | Download, lock wait/hold, callback, cleanup | CSV is optional; immutable import custody/queue acknowledgement remain required | P01.4; T07 |
| Calendar sync and EventSyncLog; C14 | Calendar run/stage/actor -> SQL sync attempt; audit ID optional | Service operation owner and SQL session | Fetch, parse, upsert/commit vs audit I/O | Commit counts survive failed audit; commit acknowledgement lost stays unknown | P01.5; P02 SQL-holder/budgets; T08/T11 |
| Calendar generate/cache publish; C14-C15 | Same parent run, separate stage IDs/generation | Shared calendar mutation owner through physical settlement | Generate commit, primary replace, auxiliary write | Primary/new and index/old represented separately; no rerun SQL for index | P01.5; T08 |
| Personal read / semaphore / cache; B06 | Private caller and dataset request, authorization context | Semaphore slot belongs to physical SQL worker; cache generation separate | Admission, observer deadline, read, physical completion | UI unavailable does not free physical capacity or publish stale unauthorized result | P01.6; T12; P02 factory budgets |
| Cancellation, cleanup, shutdown; B07/all | Cancelling requester distinct from executing worker; original attempt retained | Local scopes until settled; durable release only acknowledged by authority | Cancel requested, drain started, settled, cleanup acknowledged | Pending physical work blocks a false drain claim; diagnostics cannot release it | Each P01 slice; P02/P03 authority parts; T03/T13 |
| Restart/recovery/disposition/report; C07-C08/C16 | Original ID + new recovery attempt/actor and observation time | Fresh exact authority; stale last-known owner labelled | Recovery time separate from original failure | First failure + material transitions retained; report is passive | Each slice emits/retains its source evidence; P03 reconciliation, P04 combined history, P05 reconstruction; T10/T11/T13 |

The remaining action census dispositions retain their owners: presentation is P01.3;
passive SQL discovery/isolation is P02; receipt binding, saved-result settlement and
original-intent continuation are P03; policy/incident aggregation/retention is P04.
Fresh work, discard, replacement and unknown-outcome decisions retain existing gates.
Opening a page does not execute any of the 73 action pairs. P05 verifies the union;
it cannot supply a missing P01/P02/P03/P04 event source after those packages claim acceptance.

## Bounded diagnostics and durable evidence

Required correctness data remains required: configuration attempt/phase receipts,
immutable import custody, producer completion/capture, authority request/result/closure,
queue durable handoff and deployment termination/drain receipts. Do not put their
writes behind a best-effort wrapper or drop them on telemetry overflow.

Optional observations use a bounded ingress, not direct arbitrary logger callbacks
inside the business region. Producers construct only allowlisted primitives, snapshot
them, and offer without waiting. The sink runs outside SQL/operation/file critical
sections. No SQL writes or provider calls are introduced for generic diagnostics.
Use a dedicated bounded handler/worker owned by the existing logging lifecycle; avoid
feeding these records into the unbounded general logging queue as a second copy.

Proposed initial limits (reviewable engineering budgets, **not measured results**):

| Item | Limit / overflow policy and rationale |
|---|---|
| Envelope | 8 KiB encoded; depth <=4, fixed keys and <=16 evidence/holder references. Bound before formatting arbitrary values; exact omission counts. Enough for six record groups without raw payloads. |
| Ingress | 1,024 envelopes / <=8 MiB, nonblocking offer; reserve 128 entries for first failure/terminal/loss summaries. Coalesce ordinary repeated waits by operation/resource/step. Never one record per poll. |
| In-memory context | <=256 active diagnostic contexts; eviction/loss affects diagnostics only. Ownership remains in existing execution structures. No arbitrary caller-provided cardinality labels. |
| Persistent diagnostic projection | Per operation <=32 KiB: first meaningful failure, <=32 material transitions, latest state and loss counts. <=512 retained projections / 16 MiB total, plus <=64 MiB rotated diagnostic stream. Completed history expires at 30 days or capacity, whichever comes first, with explicit coverage cutoff. These are optional diagnostic copies, not domain receipts. |
| Saturation | Keep first-failure slot for already retained operations; evict oldest completed optional projections first. If all capacity is occupied, refuse new diagnostic records and increment loss/coverage bounds. Never delete required receipts or block business admission to make space. |
| Enqueue cost | Target p95 <=1 ms, p99 <=5 ms; no network/SQL/filesystem call in producer path. No awaited diagnostic operation under a business owner. Measure context-copy and redaction cost as well as logger cost. |
| Matched workload | >=30 repetitions per important path; <=2% median and <=5% p95 added elapsed time, plus <=5 ms p95 event-loop lag increase. Report absolute distributions and variability; thresholds are provisional until representative measurements justify them. |
| Optional SQL audit | Bounded dedicated queue <=128 requests, one physical writer per family; zero business-owner wait for optional audit. Proposed login 2 s / statement 2 s, no diagnostic retry loop. Native timeout/close behavior and endpoint cost must be qualified before adoption. |

Persistence reuses atomic file replacement for detached snapshots, under a diagnostic
directory with application data custody. It is explicitly supplementary history;
existing SQL/attempt receipts retain authority and their existing retention. Read
bounded individual projections by validated UUID, never scan an unbounded directory
on status rendering. Preserve the first failure when later state is successful. A
late terminal update adds a transition rather than replacing the original cause.

Drain order matters: close business admission; settle owned physical work and required
receipts; stop diagnostic ingress; discard unstarted optional emissions if necessary;
join already entered diagnostic I/O through the existing managed shutdown lifecycle.
An observation timeout does not detach a logging/audit thread. If native I/O cannot
finish within its qualified bound, expose that limitation and retain an incomplete
drain; do not falsely certify physical exit. This is a release-blocking qualification
failure, not permission to make a stuck optional worker invisible. No new background
worker without a tested shutdown owner is allowed in P01.1.

Redact before persistence: code-owned labels, private actor IDs only where authorized,
resource digests, error type/SQLSTATE/native integer/return code, bounded source frames
without locals. No connection strings, tokens, cookies, raw SQL parameters, sheet/input
contents, command lines or arbitrary exception/stderr text. Reuse the operator
diagnostic redactor as a second defense; allowlisting is primary. Sink failures update
bounded in-memory loss health without recursively logging through the failed sink.
If both durable diagnostics and loss reporting are unavailable, show the coverage gap
when possible; do not promise recovery of observations that were never persisted.

P01.1 must deliver its own restart/report preservation test and optional report field;
P04 owns the later cross-source report/history policy. This avoids postponing all
durability to P04/P05 while keeping a diagnostic projection distinct from business state.
No claim of infinite retention or lossless telemetry during disk failure is made.

## Caller-specific decisions and exact files

Paths below are repository-relative to the private source pin above. Files are an
implementation/review manifest, not files changed by this design. Existing tests are
named explicitly; new tests are identified as proposed.

### P01.1 — startup result preservation and common diagnostic safety (first PR)

- `bot_instance.py`: `_proc_import_wrapper`, `schedule_bg` call for `proc_config_import`,
  `run_blocking`, and startup scheduling integration. Set configuration's observation
  policy explicitly to non-cancelling, as player startup already does. Preserve the
  returned report/attempt identity through the startup service adapter instead of
  discarding the report to a Boolean before the completion observation can correlate it.
- `core/startup_diagnostics.py`: distinguish completion-check failure from worker failure;
  retain a completed worker result when verification is pending/unavailable. Preserve
  shutdown cancellation and its drain path. Diagnostic recording itself is fault-isolated.
- `core/owned_work.py`, `core/operation_timing.py`, proposed evidence/diagnostics modules
  above: safe common contract, original exception identity, once-only worker entry,
  bounded persistence and physical drain. Existing timer API remains usable by MGE.
- `services/configuration_attempt_recovery.py`: extend startup verification adapter to
  consume the explicit result/report contract compatibly; do not relax `AttemptJournal`
  or classify its required writes as optional. `services/cache_admission_diagnostics.py`
  bridges the existing process-local context; `services/recovery_report.py` adds only
  the bounded optional P01 evidence projection. `logging_setup.py` owns bounded sink
  setup/shutdown; `bot_instance.py` wires it without starting business work.
- Review unchanged `proc_config_import.py:run_proc_config_import_offload` and payload
  adapter, `services/player_stats_startup.py`, `services/profile_cache_startup.py`,
  `core/startup_lifecycle.py`, `core/interaction_safety.py`, `core/coalesced_work.py`,
  `services/event_delivery_service.py` and the legacy drain delegate. Change a supporting
  file only if needed by this contract; no MGE domain redesign.
- Existing tests: `test_monitor_startup_diagnostics.py`, `test_operation_timing.py`,
  `test_p1_owned_operations.py`, `test_proc_config_import_offload.py`,
  `test_configuration_attempt_recovery.py`, `test_player_stats_startup.py`,
  `test_startup_lifecycle.py`, `test_recovery_report.py`.
  Proposed `test_operation_boundary_evidence.py` covers schema, transport, retention,
  redaction and sink failure. Add actual thread/barrier tests, not only AST/fake timeout tests.

No SQL migration, source admission-policy change, issuer/launcher change or provider
mutation is expected in P01.1. Protected source inventory/update-transition admission
must still be checked during release preparation; a normal Python change is not an
exemption from the installed updater contract. First-slice success closes only qualified
F08/F32 behavior and its evidence boundaries, not the entire P01 family or A13 globally.

### P01.2 — usable evidence first, then early issuer exit evidence

E56 expands this package into two separately reviewable and deployable parts.
P01.2a is first and must not wait for protected-launcher qualification in P01.2b.
They share an evidence contract, not one mandatory combined release. Keep P01.1's
accepted behavior and original evidence; this amendment addresses observed diagnostic
clarity/collection gaps without repeating completed startup or business work.

#### P01.2a — evidence collection and diagnostic clarity, first delivery

Extend the existing authorized complete-report download rather than introducing a
second recovery workflow. Normal-size evidence should be obtainable with one action:

- Keep the existing incident summary/details and add bounded operation history,
  startup outcomes, diagnostic-worker health and loss/omission counters.
- Include a versioned manifest with available source/process identity, per-component
  observation/publication/export times, sizes/hashes and explicit coverage status.
  Collection is not a transactionally consistent snapshot across all sources.
- Distinguish child-worker return values from verified parent/feature outcomes.
  A boolean predicate returning false must not become an aggregate business failure.
  Preserve parent/child/stage identity; explicitly map known startup stage names.
- Retain first entry, deadline/cancellation, first meaningful failure and terminal
  result milestones independently of bounded rolling worker detail. Preserve the
  original first failure through later success. Count trimming separately from
  producer drops, context loss and publication failure; do not just enlarge buffers.
- Distinguish no new events from failed publication: show latest event time and
  available successful-publication evidence, without introducing a new active probe.
- Use existing authorized saved-incident reads and passive diagnostic snapshots.
  Do not start provider probes, reconciliation, business work, retries or restarts.
  Bound read/build cost off the interaction/event-loop critical path; retain caller
  authorization, redaction and safe archive names. Never expose protected raw files
  or weaken their ACLs to populate an attachment.
- Missing, corrupt or unavailable optional evidence must be labelled precisely and
  must not suppress otherwise available incident evidence. Preserve the existing
  all-incidents guarantee: normal-size bundles use one download; an exceeded bound
  needs explicit coverage/continuation, never a falsely complete ZIP or silent loss.
- Read existing persisted diagnostic versions compatibly; do not rewrite ambiguous
  historical child booleans into verified business outcomes. Keep mandatory receipts
  unchanged and distinct from the optional exported projection.

Affected areas: `core/operation_evidence.py`, `services/operation_diagnostics.py`,
`services/recovery_report.py`, `services/recovery_complete_report.py`, the existing
recovery service and download view, plus startup adapters for explicit outcome labels.
No SQL schema change is proposed. Final design must fix component/archive byte bounds,
concurrency/build budgets and source-identity provenance before implementation.

Qualification adds child false/parent success; repeated worker detail around a
deadline; first failure followed by recovery/restart/export; mixed old/new schemas;
missing/malformed/unwritable evidence; oversized archives; concurrent downloads;
redaction/authorization; and fail-on-call assertions against probes/repairs/replay.
Verify the actual produced archive contains the evidence needed to reconstruct a
known attempt, with honest omissions and no business-result or drain changes.
Reuse P01.1's real-thread cancellation/fault/cost cases where shared helpers change.
Production acceptance uses a normal download and already-occurring work, not a
manufactured failure or extra restart. This is early delivery of the shared contract;
P04 still owns broader incident history, deduplication, retention and escalation.

#### P01.2b — early issuer exit evidence, separately qualified

The gap occurs before a successor journal exists. `start-bot-after-sql.ps1` launches
the issuer with `Start-Process -PassThru` and returns after recording PID. An archived
reviewed gate delegates to that wrapper. That archived gate is not fresh installed
evidence. `scripts/prepare_k98_update.py:release_seed` only rebinds authenticated gate
identities; it must not become an arbitrary text patcher for new behavior.

Prepare a narrow supervisor/launcher change in `start-bot-after-sql.ps1`,
`scripts/run_export_startup_issuer.py`, the reviewed launch-gate source/package,
and the exact updater transition/package tests if required. Inspect the actual
installed gate and wrapper bindings before finalizing that manifest. Record launch
attempt, policy/source digest, issuer PID/create-time, spawn/exit time and exit code;
use an allowlisted early error stage/type. Capture bounded stderr only through a
redacting reader that drains/discards overflow so a full pipe cannot block startup.
Handle failures before Python can initialize its own logger. Never treat PID or exit
code alone as proof of pair termination, failed business work or permission to restart.

Keep original start intent; no fallback launcher, automatic repeated start or synthetic
incarnation. Diagnostic failure cannot weaken custody checks. Tests must cover missing
Python, invalid policy, custody rejection before journal, immediate/nonzero exit,
Unicode/oversize stderr, saturation, journal/exit race, PID reuse, exactly one launch,
surrogate-account versus elevated evidence, and actual PowerShell 5.1 execution.
Reuse `test_export_startup_issuer.py`, `test_export_startup_custody.py`,
`test_startup_correction.py`, `test_prepare_k98_update.py`, `test_combined_k98_update.py`
and `test_export_issuer_deployment_exit.py`. No repeat of accepted E49 recovery.

Add the safe early-start projection to P01.2a's evidence contract where available.
When the bot is offline, the installed protected updater/status path must provide
a bounded operator-accessible export; Discord cannot be its only collection path.
Do not give the unelevated bot direct access to privileged raw launch evidence.
Final installed binding/transition qualification determines whether an updater
upgrade is necessary; P01.1's successful upgrade is not proof for this new change.

### P01.3 — passive health presentation (F11)

Change `services/gsheets_health_service.py`, `services/operator_status_service.py`,
`commands/admin_cmds.py` status callback, and all three `bot_instance.py` health
consumers (button/detail refresh, `_update_health_embed`, helper wrappers). Separate
`snapshot()` from explicit `request_probe()/observe_probe()`; snapshot cannot call
SQL, Sheets, recovery refresh, mutation or probe task creation, even on cache miss.
Keep `HealthProbe` once-only sharing and owned shutdown for any explicitly scheduled
probe. Show source, observed time, age, `unknown/stale/in_progress/degraded`; do not
turn a deferred observation into provider failure or cached health into authorization.

Use existing successful business activity as narrowly scoped health evidence (e.g.
SQL connection/operation, configuration read), never as proof all provider permissions
or destinations work. Default P01 policy: no fresh provider probe caused by presentation
and no new autonomous provider-probe cadence. Absent business evidence displays unknown.
If periodic active probes remain necessary, P02 must justify usefulness, cadence,
budget and non-interference before enabling them; P04 owns escalation for prolonged
monitoring loss. Existing write-boundary checks remain mandatory. Existing tests:
`test_gsheets_health_service.py`, `test_private_status_response.py`,
`test_health_probe_cleanup.py`, `test_health_probe_proof_admission.py`,
`test_health_activity_update_transition.py`, `test_server_status_channels.py`.

### P01.4 — upload outcomes and optional queue audit (F17/F30)

Adopt one pure stage-outcome mapping through existing per-domain audit services;
do not create a generic workflow executor. `upload_routes/honor_route.py`,
`upload_routes/prekvk_route.py`, `upload_routes/player_location_route.py` and
`upload_routes/weekly_activity_route.py` are the primary equivalent callers.
`upload_routes/kvk_all_route.py` and `kvk/dal/kvk_all_import_dal.py` also need the
post-commit negative-count diagnostic distinction. Keep rows/counts/receipt identity
when that later query fails; unknown negative count must not be displayed as zero.

The audit aggregate represents ingestion status; phase rows/details represent refresh,
backup and notification separately. After a confirmed ingest, a refresh exception gives
`ingestion completed; refresh failed`, not a failed/rolled-back import. A notification
exception never schedules import retry or a false red import-failure message. Preserve
typed unknown delivery outcomes as unknown. Weekly Activity is a comparison, not proof
every optional write has bounded latency. SQL audit writers remain in
`stats/dal/import_audit_dal.py`; `services/import_audit_service.py` and domain audit
services own bounded optional scheduling and summary mapping. Do not alter an importer's
transaction, once-only offload selection or input validation to repair presentation.

For queued audit writes, allocate the diagnostic correlation before enqueue and keep
per-batch FIFO order. A pending local audit handle is not a SQL ImportAuditBatchId.
Only the audit worker binds the returned ID before dependent phase writes. If start
or its acknowledgement fails, retain the local diagnostic projection and mark dependent
SQL audit unavailable; do not invent an ID, block ingestion or blindly replay the
start write. Any later lookup uses the exact existing CorrelationId through the DAL.

`bot_helpers.py:queue_worker` invokes `append_csv_line` before active-job registration
and business processing. Make this optional download-log emission independent of
callback entry and outside the processing critical section. Review
`services/fallback_upload_staging_service.py` and `file_utils.py:append_csv_line`;
preserve one callback, active-job removal, staging custody/cleanup and exactly one
queue acknowledgement. A missing immutable import receipt is not a CSV failure and
must still refuse unsafe processing. Do not change all CSV writers globally without
classifying their correctness role. Scope can split into upload and queue PRs if the
combined diff stops being reviewable; both use the same outcome/diagnostic contract.

Tests: all four `test_*_upload_route.py` suites above, `test_import_audit_service.py`,
`test_import_audit_dal.py`, corresponding domain audit tests,
`test_kvk_all_import_dal.py`, `test_kvk_all_upload_route.py`,
`test_fallback_upload_staging_service.py`, `test_utils_live_queue.py`,
`test_live_queue_persistence.py`. Rally deduplication/attempt semantics (F29) stay P03;
notification-journal admission/retention (F19) stays P04.

### P01.5 — calendar ownership and outcomes (F23/F24/F25)

`event_calendar/service.py` owns one calendar mutation lifecycle across full refresh,
direct generation and direct publication. Current external lock names differ:
`calendar_refresh`, `calendar_generate`, `calendar_publish_cache`. Preserve those
interaction debounce contracts if useful, but place the shared business owner inside
the service so direct/admin/scheduled/startup callers cannot bypass it. Full pipeline
calls private already-owned stage methods to avoid reentrant asyncio-lock deadlocks.
No lock is acquired twice by the same pipeline. Use `core/owned_work` at the actual
sync/generate/publish thread boundary; outer timeouts cannot release the service owner
until physical work settles. Keep `allow_timeout_retry=False`; there is no late SQL retry.

`event_calendar/sheets_sync.py`: separate `_insert_sync_log_start` and `_finish_sync_log`
from fetch/parse/upsert/commit outcome handling. EventSyncLog is optional telemetry,
not an atomic commit receipt. A known commit returns its real row counts with audit
degraded and continues existing generation/publication intent unless shutdown has
closed it. A lost commit acknowledgement stays unknown and does not automatically
rerun sync. Move touched audit execution into a small calendar DAL module if needed;
do not add SQL to command/view code. Do not claim exactly-once restart continuation
for calendar: no per-run atomic business receipt currently exists.

`event_calendar/event_generator.py` retains its transactional EventInstances replacement.
`event_calendar/cache_publisher.py` treats primary JSON and type index separately.
Current source reads the primary runtime cache; no Python consumer of the index was
found in the prior census. Keep writing the index compatibly as an auxiliary artifact
for now, report its generation/write failure separately, and never roll back the
reported primary success. **Do not remove the index** until installed/manual consumers
are checked. Any discovered consumer requiring atomic pairing blocks F25 closure and
requires a reviewed versioned-generation/pointer design, not an assumed two-file atomicity.
Preserve empty-cache protection and existing runtime cache schema.

Callers: `commands/admin_cmds.py` refresh/generate/publish commands,
`bot_instance.py:_run_pinned_calendar_refresh_once`, `event_calendar/scheduler.py`,
and `CalendarService.refresh`. Review `event_calendar/runtime_cache.py` and
`cache_contract.py`. Tests: `test_calendar_pipeline.py`, `test_calendar_service.py`,
`test_sheets_sync_flow.py`, `test_calendar_publish_cache.py`,
`test_admin_calendar_commands_task3.py`, `test_calendar_scheduler.py`,
`test_calendar_runtime_cache.py`, `test_event_generator.py`,
`test_calendar_service_telemetry_task3.py`. Keep event rules/reminder/board redesign in P1.

### P01.6 — read-worker ownership follow-through (F24/B06)

`player_self_service/stats_service.py:_fetch_dataset` currently holds an eight-slot
semaphore around `wait_for(to_thread(...), 9s)`. Move physical ownership to an owned
dataset task; UI observation can return unavailable/pending at 9s without cancelling
the loader or freeing its slot. Retain `_INFLIGHT` identity until the physical task
settles, avoid replacement work for the same key, and drain registered tasks at shutdown.
Keep authorization revalidation, cache key/TTL and dataset publication separate; a late
result cannot be delivered under stale account authorization. Review existing download
worker cleanup and `stats_alerts/db.py` as cross-caller tests; its connection fallback
policy belongs to P02/F26. Tests: `test_player_self_service_stats_service.py`,
`test_personal_stats_dal.py`, plus a proposed real-thread capacity/cancellation test.

## SQL and persistence review

**Verdict: source contracts support the proposed Bot-only first slice; deployment is
not assessed.** No SQL schema, permission, isolation-level or index change is proposed
for P01.1. Later slices can use existing shapes for diagnostic enrichment; they must
not invent status enum values or claim a receipt that the schema does not provide.

| Bot boundary | Authoritative SQL source / verified design constraint |
|---|---|
| Import audit | `sql_schema/dbo.ImportAuditBatch.Table.sql`, `dbo.ImportAuditPhase.Table.sql`, `dbo.usp_ImportAudit_StartBatch.StoredProcedure.sql`, `dbo.usp_ImportAudit_RecordPhase.StoredProcedure.sql`, `dbo.usp_ImportAudit_CompleteBatch.StoredProcedure.sql`, `dbo.usp_ImportAudit_FailBatch.StoredProcedure.sql`. Batch has unique `CorrelationId`, actor/source/external-batch fields and `DetailsJson`; phases have `PhaseName`, `PhaseStatus`, counts/times/errors/DetailsJson. Use existing `completed/failed/...` statuses, put separate dimensions in bounded versioned JSON/phase rows. No unsupported `completed_with_warning` SQL value. |
| Calendar inputs and audit | `dbo.EventSyncLog.Table.sql`: identity `SyncID`, UTC start/finish, `Status nvarchar(32)`, source/counts/error. It has no operation/actor/commit receipt column. `dbo.EventRecurringRules.Table.sql` / RuleID, `dbo.EventOneOffEvents.Table.sql` / EventID, `dbo.EventOverrides.Table.sql` / OverrideID remain business input tables. Diagnostic correlation is supplementary; EventSyncLog absence never proves rollback. |
| Calendar generation/cache | `dbo.EventInstances.Table.sql` defines the selected instance/source/time/type/cancellation fields; generator replacement commits separately from input sync. JSON primary and index are two later file effects, not part of the SQL transaction. |
| Configuration | `dbo.ProcConfig.Table.sql`, `dbo.ProcConfig_Staging.Table.sql`, `dbo.sp_Upsert_ProcConfig_From_Staging.StoredProcedure.sql` and existing `dbo.sp_TARGETS_MASTER.StoredProcedure.sql` remain unchanged. The Python configuration attempt is a strict local journal, not a guessed `ConfigurationImportAttempt` SQL table. |
| Durable preparations / resources | `dbo.ExportPreparation.Table.sql`: PreparationID, State, OwnerID/Fence/Version, RequestJson/RequestHash, GenerationJson and spool fields with constraints. `dbo.ExportResource.Table.sql`: separate ActiveJobID/ActivePreparationID/ActiveOutputOperationID, OwnerID/Fence/Version/BlockedReason. Current diagnostic fields must not be added to signed/hashed RequestJson without a separately reviewed protocol change. |
| Restart/session/stream | `dbo.ExportExecutionSession.Table.sql`, `dbo.ExportExecutionStream.Table.sql`, their Transition procedures: session State/Version/ManifestHash and stream State/ActiveAccountKey/ClosedUTC/ClosureHash/ClosureReference/EventDigest. `closed`, `target_contained`, `read_contained` have distinct constraints; a closed session alone does not prove no stream or preparation hold. |
| Pipeline / producer evidence | `dbo.ProcessingPipelineRun.Table.sql`, `dbo.ProcessingPipelineStage.Table.sql`, `dbo.StatsImportExecution.Table.sql`, existing capture and writer-completion contracts remain authoritative. P03 owns automatic binding/continuation. P01 preserves references and their meanings. |

Do not run a new SQL experiment merely to reproduce retained E50 evidence. Native
qualification for P02 and any later audit connection/budget change must use explicit
disposable local targets, real deployed methods, both overlap orders and actual
cleanup. Existing restored databases and captures are not test scratch space.
If a later slice needs a new atomic calendar receipt or SQL-holder facility, bring
back an exact SQL design/migration and separate review; it is not hidden in this packet.

## Refactor decisions and residual limits

- Fix within P01: duplicated outcome classification, logging that can replace results,
  loss of physical ownership, thin startup report adapter, and a service-owned calendar
  mutation boundary. Reuse canonical helpers rather than another coordinator.
- Preserve mandatory attempt journal writes, writer/capture receipts, authorization,
  commit/rollback, source identity and protected updater restrictions. Required receipt
  errors are not optional telemetry errors.
- SQL remains in existing DAL/data-access modules; move only touched calendar audit SQL
  into calendar DAL if needed. Do not rewrite all legacy configuration/command modules.
- Existing tests encoding Honor's false terminal failure must change. Preserve their
  notification-error assertions as independent outcome tests. Do not delete negative tests
  to obtain green results. No dead-code removal is justified by this design alone.
- P02 owns SQL-holder coverage, observer isolation, maintenance lifetimes, F20 file-lock
  cleanup and F26 fallback. P03 owns automatic durable convergence and Rally retry
  identity. P04 owns broader incidents/history/notification capacity. These are already
  recorded programme work, not newly discovered debt requiring duplicate backlog entries.
- An unavailable diagnostic sink can lose optional detail; report that coverage limit.
  It never permits replay or false success. Process termination/SQL receipt authority
  remains outside the diagnostic projection.
- Fresh installed launcher bindings, index consumers, sink cost, native audit timeouts
  and current production ownership are not proved by source review. They are named
  gates for the relevant slice, not assumed complete and not blockers to P01.1 design.

## Risk-based qualification

Every implementation slice supplies normal/negative/concurrency/restart and redaction
evidence for its adopted boundaries before acceptance. T09/T13 distinguish P01-local
evidence from later SQL/authority coverage. Do not count a missing known holder as a pass.

| Test | Executable scenario and required assertions |
|---|---|
| T01 Startup deadline | Real thread held by barriers beyond a short observer deadline; one invocation, no task cancellation from deadline, completion check once, returned tuple/report/attempt retained. False result and completion-check failure stay distinct. Repeat for preferred and selected fallback backend; never fallback after entered execution fails. |
| T02 Diagnostic failures | Raise from clock, record construction, redactor, enqueue and sink at entry/exit; success return and original worker exception identity preserved. Include actual MGE callback and event caller sharing the helper. Check no recursive failure logging. |
| T03 Cancellation/drain | Cancel before entry, during thread execution, during completion verification and repeatedly during shutdown. Next caller cannot acquire owner until physical completion; zero replay. Preserve late known outcome and cancellation as separate facts; required receipt failure remains unconfirmed. |
| T04 Issuer | Execute real PS5.1 supervisor fixture, pre-journal failures, immediate exit, large stderr, blocked/broken capture sink, PID reuse and journal race. Exactly one launch, bounded memory/files, no blocked pipe and no new start on unknown outcome. Native custody/termination evidence separately qualified. |
| T05 Passive UI | Replace SQL/provider/probe/recovery entrypoints with fail-on-call spies; all status/health/button rendering succeeds or shows unknown/stale without calling them, including empty cache and concurrent viewers. Explicit probes retain original task on UI timeout and drain on shutdown. |
| T06 Committed upload | Parameterize Honor/Pre-KVK/Location/Weekly/KVK-all: commit then audit error, refresh exception, typed unknown delivery, notification error. Exactly one ingest, original rows/external batch preserved; distinct phase failure. Include ingestion failure and unknown commit so neither becomes success. |
| T07 Queue | CSV permission/error/saturation before callback; callback runs once under original staging owner, active job cleaned, queue ack once. Real processing failure still fails truthfully. Required immutable-input receipt failure still prevents entry; cancellation does not delete an in-use input. |
| T08 Calendar | Sync/generate/publish each with real blocked thread; timeout then direct/admin/scheduled competitor excluded until settlement. Audit-start and audit-finish failures, commit-ack loss, successful primary replacement then index failure, empty preserve case, direct-stage versus full-pipeline overlap and no reentrant deadlock. |
| T09 Known holders | Two controlled actors in both acquisition orders, local operation lock/semaphore first; P02 adds real SQL session and transaction guards/row locks. Assert correct holder operation/phase/lifetime, resource/mode, original return and elapsed categories. Recycle session/PID and ensure no stale attribution. Missing expected holder fails. |
| T10 Reconstruction | Same attempt through task/thread/process where enabled, receipt, capture, settlement, restart and report; parent/child identities not overwritten. Lost reply resolves only from exact receipt; corrupt/missing evidence stays unknown. No producer/provider replay to repair diagnostics. |
| T11 Retention/failure | First failure -> successful reconciliation -> restart -> private report still shows original cause/time and material transitions. Overflow, disk full, malformed old schema, permission failure and loss counter tested. Output redacted and bounded; domain receipt files unchanged. |
| T12 Read capacity | Eight blocked physical readers, UI deadlines, ninth caller and duplicate key. No ninth physical entry until a slot settles; no replacement for same in-flight key. Authorization changes prevent late result disclosure; shutdown drains actual readers. |
| T13 Matched cost/drain | Diagnostics off/on with same fixture, source pins and workload; measure counts, p50/p95/p99, event-loop lag, queue/high-water, drops, file bytes, lock hold and drain. Inject slow/failing sink and full queue. Business counts/outcomes/required receipts identical. Later P02/P05 repeat with real observer/producer overlap. |

Run focused suites per slice first, then full `python -m pytest -q tests` for shared
helper/startup/lifecycle changes. Run `python scripts/analyse_pytest_log_noise.py` when
qualifying full-suite log isolation; test evidence must not modify operational logs.
Before PR: architecture, deferred, security-routing validators, explicit-path
`scripts/select_tests.py`, smoke imports, command registration and scoped lint/hooks.
The selector is a recommendation, not proof it found concurrency/custody gaps.
P01.2 additionally needs actual Windows/PowerShell qualification; source/parser fixtures
are not an elevated production rehearsal. Native SQL cases remain separate from mocks.

No new test suite was authored or runtime pytest run for this design-only delta.
Documentation validators/link/manifest checks are recorded in E52. Numerical budgets
above are proposed gates; no diagnostics-off/on performance improvement is claimed.
Performance/lock budgets require measurements before implementation acceptance and
release; design approval must not be recorded as measured non-interference approval.

## Pre-deployment incident and recovery dependency plan

Assess this **before any bot stop**, independently of the P01 code PR and P02 fix.
The private companion maps the exact Report 68 IDs to these steps. Report 68 is a
snapshot, not current authority. Six operational open records are five linked records
for one pipeline plus old F28; the overview is another presentation row. Neither six
nor zero incidents determines deployment readiness.

| Gate | Fresh evidence / decision | Action boundary |
|---|---|---|
| R1 Installed context | MINI_AMD, actual SID/elevation, PowerShell 5.1, exact installed updater manifest, source/policy/gate hashes, current private-main predecessor and release stage | Read/inspect only through approved bounded tooling. Do not launch health probes to inspect streams. E49's updater hash is a historical comparison, not present verification. |
| R2 Exact ownership | Current incarnation/process pair plus authority SessionID/ManifestHash/Version; every relevant ExportResource hold; preparation/stream state, owner/fence/version, receipt/hash/closure fields | Supported protected authority/SQL observations. A diagnostic requester is not a holder. Prepare evidence before stop; refresh at action time because preflight reserves no quiet interval. |
| R3 Original pipeline | Stats/player completion and captured hashes; configuration attempt + read/preparation links; writes-not-entered/atomic noncommit evidence; pipeline stage state/version; absent/present export job/stream | Preserve input, committed data and captures. Do not repeat accepted startup/P03a.1 work or re-upload the file. |
| R4 Supported config disposition | Current `cancel_configuration` eligibility: exclude live execution, verify absent atomic receipt, exact owner/fence, original inputs and saved closure | Only after specific operator authorization: close exactly this uncommitted attempt, verify receipt/release and reread ownership. It does not run configuration or export, and does not prove the pipeline can continue. |
| R5 Drain decision | `StartupReconciler._readiness` and protected deployment receipt semantics, including permitted already-quarantined preparations and positively terminated predecessor | Safe if existing contract permits retained work and session/stream/native proofs pass. Active jobs/output operations/unexplained holds or unclosed streams block. Do not force state into a permitted category. |
| R6 Unsupported continuation | Existing pipeline continuation excludes configuration when a child/read already exists; closing the attempt need not remove that association | If current evidence confirms this gap, review an exact successor/remaining-stage repair under P03/recovery, with immutable original history, fresh intent, CAS and lost-reply reconciliation. No new blanket retry or F09 patch in P01. |
| R7 Deployment | Reviewed mirror/private patch, any installed updater transition first, supported prepare/status checks, exact target and source/seed pairing | Separately authorized deployment through installed updater. One graceful restart only when prompted; require protected drain before source replacement, one successor and readiness receipt. No manual live Git pull/start. |
| R8 Acceptance | P01 late-outcome/passive-view/diagnostic behavior and retained incident history on deployed target | P01 acceptance can be recorded while F09/P03a.2 whole-flow acceptance remains open. Later remaining-stage/provider acceptance preserves original captures and needs its own authorization/evidence. |

The readiness source allows only specific quarantined preparations to survive a
positively terminated predecessor; it does not permit all held work. It checks resource
ownership and stream closure/contained-terminal fields, then exact old-session closure
and rechecks. `core/export_deployment_handoff.py` writes `deployment_drained` only with
native termination proof after SQL session closure. Incident UI resolution is not this
receipt. Do not weaken this contract to make the next deployment convenient.

If R4 is insufficient but R5 already permits safe retained state, deploy without inventing
a zero-incident cleanup requirement. If R5 fails, keep the Bot running where possible
and prepare the precise repair packet before stop. A pipeline successor repair would
need to bind both existing committed captures, preserve the old configuration failure,
prove its read/writer closure, record separately identified remaining configuration
intent, and prevent dispatch twice after a lost acknowledgement. That is a bounded
repair design request, not an instruction to execute it here. Root contention remains P02.

Rollback uses the protected source/seed process with physical drain. Do not downgrade
over unknown new receipt schemas or erase diagnostic/incident history. P01.1 keeps
authoritative schemas unchanged; later envelope/projection readers must tolerate
missing optional evidence and reject malformed versions without executing recovery.

## Security review and approval checkpoint

Applied `k98-security-review-routing`: **documented skip for this documentation-only
design delta**. No executable, configuration, permission, SQL or runtime persistence
behavior changed. No codebase/deep scan was requested or launched.

Each implementation slice touches lifecycle, data access, file handling, interactions
or protected launch surfaces and requires an exact Bot Changes review, Deep off, after
the intended base/head or uncommitted patch is fixed. A SQL delta, if later approved,
requires a separate SQL history/review. Unit tests do not replace those reviews.

E55 records P01.1 deployment and its exercised live acceptance without reopening it.
E56 authorizes this scope/priority amendment; the next implementation packet is
P01.2a, followed by separately qualified P01.2b. P01.3-P01.6 adopt the clarified
outcome/milestone/export contract as each caller is changed. Each part retains an
exact final diff, qualification and deployment record. This amendment does not
authorize runtime implementation or close wider programme/whole-flow acceptance.

Conditional references used: startup/shutdown/singleton and diagnostics runbooks,
`REVIEW_HELPERS.md`, P1 operation lifecycle, Windows ownership/access, Combined Updater,
Promotion Guide and S11 restart contract for the dependency plan. Earlier dated status
blocks are historical where superseded by E49-E51.
