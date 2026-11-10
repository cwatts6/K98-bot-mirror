# P01.2a design and qualification: one useful evidence download

> **Current programme checkpoint - 4 November 2026 (E68/E69):** P01.2a is deployed and accepted for its declared reporting/evidence scope at private `67c4e12a8ecf0c25280770860480ac65a6826602`.
> Read the [P01.2a closeout](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Closeout%20-%202026-11-04.md) for delivered corrections, evidence limits, learnings and remaining owners; [P01.2b handover](Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Handover%20and%20Scope%20-%202026-11-04.md) is the next review/design task.
> Earlier dated statuses, holds and next-action instructions in this document are retained history and are superseded for current scheduling. P01.3-P01.6/P02-P05 and exact incident recovery remain open; no replay of accepted work.

**Current E64:** mirror [#482](https://github.com/cwatts6/K98-bot-mirror/pull/482) and private [#722](https://github.com/cwatts6/k98-bot/pull/722) are merged. Private target `07bc9d6ebd5964f9bf660822f03a932a2472d966` is prepared for operator deployment, with final review, CI and the packet recorded in the [review/merge receipt](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Review%20and%20Merge%20-%202026-11-03.md). No production deployment, restart or recovery action was performed. Earlier scope, authorization and failed-run receipts below are historical.

Date: 3 November 2026. Status: implementation and local qualification approved
by the user in E59 ("Approved please proceed"). E57 authorized review/design;
E58 records the proposal below. Publication, merge and deployment remain separate.
The original design decisions and release gates below are preserved.

Current implementation and measured evidence are recorded in the
[implementation and qualification receipt](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Implementation%20and%20Qualification%20-%202026-11-03.md).
Its current status supersedes historical approval-pending wording below; the
design's budgets and release gates remain in force.

## Scope summary

Extend the existing complete-report action with bounded, redacted operation
history, startup outcomes, diagnostic health and a versioned manifest. Preserve
the complete incident export and its authorization. Separate worker values,
feature verification, observer deadlines and physical settlement. Retain important
milestones outside rolling detail. Collection reads saved facts; it does not
verify business completion, probe a provider, repair, replay or restart anything.

The [agreed scope](../Startup%20Import%20Export%20Reliability%20-%20Scope%20-%202026-11-02.md)
and [tracker](../Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md)
remain authoritative. This implements the accepted
[P01.2a handoff](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Scope%20and%20Handoff%20-%202026-11-03.md),
under the shared [P01 design](../Startup%20Import%20Export%20Reliability%20-%20P01%20Design%20-%202026-11-03.md).
[P01.1 acceptance](Startup%20Import%20Export%20Reliability%20-%20P01.1%20Closeout%20-%202026-11-03.md)
is preserved. P01.2b launcher/offline evidence, P02 contention, P03 continuation,
P04 incident history/escalation and P05 combined acceptance remain separate.

## Source and evidence basis

Read-only local verification found both supplied source checkouts clean:

| Source | Revision and use |
|---|---|
| Private `.codex_artifacts/a1b-updater-correction` | `0247371d90ec88d4c0639e9200164f4256086037`; primary runtime-source review, matching the supplied deployed target. |
| Mirror `.codex_artifacts/p1-mge-mirror-review` | `607f6a8136d15c8c60e0fdfed1a059b75e774384`; reviewed follow-up candidate, not a fresh claim about remote main. |
| `C:/K98-bot-SQL-Server` | `7e91989f619deb46836194c7e705b0a9eb2ebe11`; clean authoritative schema checkout. |
| Project root | Older design checkout; intentional README/index edits and programme documents preserved. Not the runtime baseline. |

No remote refresh, live observation or runtime test was performed for this design.
The retained merge qualification, final scope review, Report 69 assessment, live
diagnostic validation and chat-handoff documentation validation were inspected.
Their dates and limitations remain attached to their claims. In particular,
23 settled operations and eight correlated startup references are historical
observations from one incarnation, not proof of a later restart or provider flow.
Private source/caller hashes and validation receipts live under
`.codex_artifacts/startup-import-export-review-20261102/p012a-design-20261103/`.

### Findings that determine the design

| Current source | Consequence / decision |
|---|---|
| `services/recovery_complete_report.py:build_complete_report` writes only `incidents.jsonl` and `summary.json`; monitor health is nested in the summary. `services/recovery_report.py` separately adds the small operation projection. | Add common optional component projection to the existing complete action. Do not require the operator to assemble three unrelated downloads. |
| `core/operation_evidence.py:scope` reuses one Observation through nested calls; `worker_result` replaces one shared result field. `result_facts(False)` calls a generic Boolean `reported_success`. | Add child identity and typed value semantics. Keep the old helper for the mandatory configuration verifier; do not globally reinterpret its API. |
| `core/startup_diagnostics.py` retains verified completion in `_steps`, but emits a generic event without that completion. Four rehydration labels are absent from `STAGES`. | Persist an allowlisted projection of already obtained completion, and add the known stage labels. Do not run completion checks during collection. |
| `DiagnosticSink._accept` coalesces/trims detail with one `omitted` counter; first failure and result are separate, but entry/deadline/cancellation are not. | Add fixed milestone slots and separate detail-coalescing, detail-trimming and ingress-loss counters. |
| `_publish` replaces the in-memory snapshot before attempting disk output; `observed_utc` is projection time, not last event or successful disk publication. | Publish memory and disk facts separately. A live worker and an old file do not establish current persistence health. |
| A record with a first failure never becomes `complete`; only complete records are eligible for eviction. | Preserve that existing failure-retention policy in this slice. Expose saturation and refused-new-operation counts; do not silently expire original failures to improve diagnostics health. P04 owns policy changes. |
| `RecoveryDAL.report_page` fetches up to 101 rows and recounts each page. SQL bounds one export incident's evidence at 1 MiB UTF-16 and action result at 32 KiB. | Keep the existing all-state, scope-bound, SQL GUID ordering/cutoff contract. Add a smaller page option for bundle collection so driver/Python allocations are bounded. No new index or isolation design here. |
| Complete-report callbacks share `show_complete_report`; ordinary report has continuation and an unavailable fallback. The common call uses owned offload. | Keep both persistent entry buttons. Add report-specific admission, fallback and final authorization without changing every recovery action's executor. |
| `RuntimeLifetime.owned` can wait for reconfiguration before report collection starts. | Add report-only nonblocking runtime admission; the 30 s collection deadline alone cannot bound this earlier wait. Keep default producer/repair ownership unchanged. |

These are bounded correctness/design observations, not a new whole-programme audit
or a claim that each is a security vulnerability.

## Affected areas and exact implementation manifest

Paths are relative to the verified private source above; implement on a refreshed,
suitable mirror base after approval. Existing files are changed only for the
responsibility named here. New files are explicitly marked.

| File | Intended change |
|---|---|
| `core/operation_evidence.py` | Typed diagnostic events, parent/child identity, code-owned result roles, sequence/availability and known stages; preserve compatibility helpers and nonblocking failure isolation. |
| `core/owned_work.py` | Establish a child observation around each physical thread invocation and its observer cancellation; preserve signature, once-only execution, original returns/exceptions and repeated-cancellation drain. |
| `core/startup_diagnostics.py` | Emit parent return, verification and terminal milestones independently; publish an immutable bounded startup snapshot; never re-run the verifier. |
| `services/startup_outcome_projection.py` (new) | Pure, label-specific projection of existing startup returns/completion values; no SQL, disk, Discord or business calls. |
| `services/operation_diagnostics.py` | V2 fixed-slot retention, version readers, passive full snapshot, independently observed publication health, exact loss counters and V1 compatibility publication. |
| `services/recovery_evidence_bundle.py` (new) | Optional component collection, manifests, budgets, frozen diagnostic continuation sessions and report-build admission/ownership. No repair methods or Discord objects. |
| `services/recovery_complete_report.py` | Incident-first archive assembly, bounded whole-component packing, truthful partial/fallback result and common evidence components. |
| `services/recovery_report.py` | Reuse safe projection/encoding; preserve V1 ordinary incident parts and make optional failures unable to suppress fitting incidents. |
| `services/recovery_service.py` | Authorized bundle/continuation service facade; validate actor, configured scope, budget and continuation before reads. |
| `services/recovery_runtime.py` | Select a passive, nonwaiting runtime scope for report methods only; expose the bounded already-loaded provenance descriptor. No installation/retry fallback. |
| `services/export_runtime_composition.py` | Narrow `RuntimeLifetime` nonblocking report admission and report-caller context, with identical owner/reference/drain accounting after admission. Existing default `owned` behavior unchanged. |
| `services/recovery_dal.py` | Optional bounded page-size parameter, default 100 retained; bundle uses 10, plus one lookahead. Parameterized `TOP`, same projections/cutoff/order. No write/schema changes. |
| `ui/views/recovery_backlog_view.py` | Existing action renders full/partial/unavailable states, routes diagnostic or incident continuation, rechecks authorization and disposes attachments on every exit. |
| `ui/views/recovery_view.py` | Ordinary-part continuation remains available; narrow integration for shared attachment lifecycle and final actor recheck where needed. Preserve persistent IDs. |

Supporting review, expected unchanged: `core/operation_timing.py`,
`core/interaction_safety.py`, `core/coalesced_work.py`, `core/startup_lifecycle.py`,
`core/event_rehydration_lifecycle.py`, `bot_instance.py`, `logging_setup.py`,
`services/recovery_health.py`,
`services/recovery_release_policy.py`, `services/recovery_execution_guard.py`,
`services/legacy_export_snapshot_service.py`, `services/cache_admission_diagnostics.py`,
`services/configuration_attempt_recovery.py`, `services/player_stats_startup.py`,
`services/player_stats_cache_service.py`, `services/profile_cache_startup.py`,
`services/tracked_view_rehydration_service.py`, `target_utils.py`, `profile_cache.py`,
`proc_config_import.py`, `core/operator_diagnostic_payloads.py` and the existing
runtime connection/ownership composition. A change to these supporting contracts
must be justified in the final manifest; it is not permission to redesign them.

### Shared-caller challenge

The retained AST inventory covers direct imports of owned work, timing and evidence,
including local imports. Review the legacy drain delegate's consumers as well:
an import census alone does not prove all indirect callers were qualified.
The retained current inventory has 43 imports across 33 source files for these
three modules; its denominator differs from P01.1's narrower helper-import count.

| Caller family | Required regression / boundary |
|---|---|
| Startup/config/player/profile/name | Parent result cannot be overwritten by later verification children; configuration strict attempt/terminal receipt still required. |
| Tracked views, vote/survey and pinned calendar rehydration | The four known labels survive export. Tracked-view false child predicate can coexist with 21 attached/zero failed; the other three get unknown feature outcome when no verifier exists. |
| MGE board/roster ownership, embed manager, review/roster DAL, simplified flow | Existing local holder references survive child contexts; ownership reference remains the root operation. Timings stay inclusive and must not be summed. |
| MGE finalisation/publish/recovery/scheduler and admin/signup/roster/rules/leadership views | Generic worker return does not certify mutation or delivery. One actual callback and actual roster/board caller must run through the changed helper in negative tests. |
| Event delivery, coalesced work, private interaction, legacy export drain | No early release, detached worker, extra invocation or duplicate delivery after cancellation. |
| Both recovery entry buttons, ordinary report, unavailable report, direct service calls | Same access rules, no adapter inspection/reconciliation, no bypass of collection admission through a direct caller. |

Helper reuse: keep `drain_thread`/`drain_awaitable`, `optional`, existing redactor,
attachment-budget resolver, safe defer, incident allowlist, JSON encoding and
`BoundedArchive`. Keep diagnostic atomic replacement and link rejection in the
sink. Do not call the raw-log collector or add another generic executor, atomic-file
framework, health probe or coordinator. New services are necessary to keep pure
outcome mapping and bounded report-session policy out of views and legacy modules.

## Result and correlation contract

Use `operation-observations/2` for the retained projection and
`operation-boundary/2` for new typed events. V1 is a distinct accepted input format.
The product remains diagnostic-only. Domain receipt formats and business APIs do
not change.

Each new event carries root `reference`, `process_incarnation`, `event_id`, a
per-context sequence, `stage`, UTC time and `role`. A physical invocation receives
its own `child_reference` and `parent_reference`; child context flows through
`asyncio.to_thread`. Existing durable `operation_id`/`attempt_id` remain separate
references. Allocate before invocation where possible; UUID/sequence/context
failure records context loss and still executes the business call once. A
nonblocking sequence assignment failure must not wait on a business thread.
Diagnostic incarnation is not native process creation or authority identity.
Keep root holder identity separate from the child reference. Bind durable attempt
IDs to the event/attempt that actually supplied them; concurrent children must not
overwrite or inherit another child's configuration attempt. Include code-owned
origin/caller and actor kind: startup is a system actor, while an uninstrumented
interactive producer is explicitly unavailable. The admin downloading evidence is
the collection requester, never a guessed producer or lock holder. SQL holder
availability remains `unavailable_P02` with source/time, not an invented attribution.

| Field / role | Meaning |
|---|---|
| `worker_value` | `kind=boolean|configuration_tuple|none|unclassified`, bounded primitive value, `meaning=unclassified_return` unless an explicit adapter assigns it. False is not an aggregate failure. Never serialize arbitrary result objects or use their `repr`. |
| `parent_return` | Original top-level return facts. It is independent of the last child result and survives a later verifier failure/cancellation. |
| `feature_outcome` | `succeeded|partial|failed|unknown|not_checked`, with code-owned verifier/source, verified time and allowlisted supporting fields. Only explicit feature adapters assign it. |
| `observer` | Pending, deadline elapsed, observed or cancelled; does not determine business failure. |
| `physical` | Not entered, entered, draining or settled; only actual worker settlement supplies the last value. Scope exit is separately labelled. |
| `failure` | Error type, bounded function/line, SQLSTATE/native code when available, and `role=worker|verification|observer`. Cancellation is a separate milestone, not automatically a meaningful business failure. |

Keep `result_facts()` and its `reported_success` output unchanged for
`verify_startup_import` and legacy consumers. Add a separate typed projection at
diagnostic callsites; changing the mandatory verifier to consume an optional
diagnostic record would violate the receipt boundary.

Pure startup mappings consume the completion already returned by the existing
checker. Configuration success means its existing accepted returned/recorded
contract, not independent fresh SQL certification. Player cache reports main
readback and last-KVK state separately; a successful main cache with failed last-KVK
is partial. Profile/name report execution, available data and persistence separately;
available memory with failed persistence is partial. Tracked views use
`restoration_status` plus failed/unconfirmed/unattempted counts, preserving attached,
pruned and superseded counts. A checker returning a dict is not by itself success.
Missing/malformed checker output is unknown with a reason. Vote/survey/pinned calls
without a checker are `not_checked`, even when their coroutine returns normally.

Add these exact known stage labels: `rehydrate_tracked_views`,
`rehydrate_vote_post_views`, `rehydrate_survey_post_views`,
`rehydrate_pinned_calendar_view`. Unexpected labels remain unavailable with an
unknown-stage count. Do not admit arbitrary user-supplied labels.

## Milestones, bounded history and compatibility

For each retained root operation keep eight fixed milestone slots: scope entry,
first physical entry, first observation deadline, first cancellation request,
first meaningful failure, parent return, feature verification, scope terminal.
First slots are write-once. Parent return/verification/terminal retain their own
facts; a later explicit recovery observation is a distinct linked attempt, never
a rewrite of the original failure. Record first and latest time plus repeat count
for repeated deadline/cancellation signals. Physical child outcomes remain distinct.

Retain at most 16 child summaries per root (first entry, latest terminal/value,
stage and identity). Preserve the first failing child when prioritizing retained
summaries; count unrepresented children and event loss explicitly. A first failure
in an unrepresented child still fills the root first-failure slot. Do not claim
complete child reconstruction when the child bound was exceeded.

| Resource | Concrete decision |
|---|---|
| Producer contexts / ingress | Keep 256 contexts, 1,024 envelopes and 128 critical-reserve entries. Nonblocking offers only. New typed envelope <=2 KiB; V1 reader still accepts <=8 KiB. |
| Critical classification | Milestone-bearing events use reserve, including first entry, deadline, cancellation, parent return and verification. Reserve exhaustion is possible and counted; it is not lossless storage. |
| Root projection | <=32 KiB total: 16 KiB milestone area (8 x <=2 KiB), 8 KiB child summaries (16 x <=512 B), 6 KiB rolling detail (<=32 events), 2 KiB identity/counters. Serialize/check each partition; trim detail first, never milestone slots to fit detail. |
| Whole projection | <=512 roots; encoded document <=16 MiB including envelope overhead. Enforce both row and whole-file bounds. At the latter bound evict eligible completed records or refuse new optional evidence with explicit loss. |
| Retention | Keep current 30-day/capacity policy for successful settled rows and existing first-failure protection. All-failure saturation is visible degraded coverage, not a reason to block business or remove receipts. |
| Counters | Separate `detail_coalesced`, `detail_trimmed`, `producer_dropped`, `critical_dropped`, `context_lost`, `children_omitted`, `records_evicted`, `invalid_events`, `restore_failures`, `publication_failures`. Saturate at signed 64-bit maximum with saturation flag; critical drops are a subset of producer drops, not additive. |

Record current-incarnation and restored totals separately; do not double-count
first-failure/result duplicates while restoring. Unknown legacy trimming stays
`legacy_omitted_combined`, not guessed split counts. Epoch/cutoff/reason accompanies
evictions; counts whose history was never available are unknown, not zero.

Use separate fixed `observations-v2.json` and `observations-v2.tmp` paths in the
existing operation-observations directory. Continue producing the existing
`observations.json` V1 compatibility projection on the same single sink thread.
Each is <=16 MiB, so final files <=32 MiB and worst simultaneous old/temp files
<=64 MiB. No new diagnostic stream or raw-log export. The compatibility projection
contains only V1-legal stages/fields and retains legacy ambiguous values as such;
it is explicitly a reduced view in V2 coverage. No V2 keys are injected into strict
V1 event dictionaries. Qualify the unchanged V1 loader against actual new output.

On startup prefer valid V2, import valid V1 only when V2 is absent, and label that
origin. Corrupt/unknown-version V2 is not silently replaced by an apparently fresh
V1 history: expose the restore failure and separately labelled older V1 fallback.
Validate a document/row before installing it; salvage only independently valid rows
with explicit rejected counts. Never synthesize missing entry/deadline/parent facts
from a legacy final Boolean. Preserve original files on failed restore; publish new
history only through the reviewed compatible replacement policy, with the failure
visible. A bounded `.invalid` preservation slot per version may be used on first
corrupt replacement (<=16 MiB each); if occupied, refuse replacement of that corrupt
source and keep live diagnostics available rather than deleting earlier evidence.
Including preservation slots, absolute diagnostic disk budget is 96 MiB.

V1 downgrade keeps reading its own file; V2 remains untouched. On later upgrade,
never merge two histories as independent events: compare provenance/generation,
deduplicate stable identities, label the intervening V1-only interval and retain its
legacy ambiguity. New evidence cannot retroactively certify old outcomes.
Legacy rows retain their validated V1 representation and <=32 KiB row bound inside
V2; do not force an old 8 KiB event into a new 2 KiB milestone slot or silently
truncate it. The new partition sizes apply to newly typed rows. Whole-document
limits still include legacy wrappers and provenance overhead. Pre-existing
oversized files are preserved and reported, never copied into an unbounded backup;
the 96 MiB limit bounds files this implementation creates, not arbitrary pre-existing
disk content it is forbidden to delete.

### Publication and freshness

Publish immutable memory snapshots by pointer replacement. A collector pins one
generation and copies/serializes off-loop without holding the producer queue lock.
Do not mutate a published snapshot. Retention and collection can overlap safely.

Track latest accepted event UTC separately from projection time, last write
attempt, last successful replacement, represented generation/hash, failure count,
error classification and worker liveness. Track V1/V2 disk targets separately.
Successful replacement means flush/close/replace acknowledged; it is not an fsync
or power-loss durability guarantee. Update success only after replacement returns.
Persist the prior acknowledged publication watermark in the next document, labelled
as prior; a file must not claim to prove its own successful replacement. On restore,
report `file_observed_on_restore` separately from the prior writer's watermark.

An idle sink with last-event <= last-success generation is caught up even if both
timestamps are old. New events after last success mean publication pending or
failed; a live worker alone is insufficient. No periodic write/probe is added to
make an idle timestamp look fresh. Failure of both persistence and health projection
remains an explicit observability limitation.

## Archive contract and exact limits

Use the existing filename `K98-recovery-complete-report.zip` for the normal complete
incident bundle. Keep `summary.json` format `k98-recovery-complete-report-v1` and
`incidents.jsonl` field meanings. Add `manifest.json` with
`schema=k98-evidence-bundle/1`; existing readers can ignore the new members.
`summary.complete` continues to mean incident enumeration, not complete diagnostics.

| Member | Content and uncompressed bound |
|---|---|
| `summary.json` | Existing incident aggregate/monitor fields, <=256 KiB; excess aggregate detail gets explicit count/continuation, never unbounded Counter cardinality. |
| `incidents.jsonl` | Same redacted incident projection, all states, configured scope and first-seen cutoff; <=128 MiB per complete attempt and <=1,000,000 rows. Stream; do not materialize all incidents. |
| `operations.jsonl` | V2 retained root records including milestone/child/detail coverage, <=16 MiB / 512 rows. |
| `startup.json` | Up to 64 named startup summaries, <=128 KiB; includes reference, known stage and separate outcome dimensions. |
| `diagnostic-health.json` | Diagnostic ingress/retention/publication/worker facts and passive monitor snapshot, <=128 KiB. Each provider is independently guarded. |
| `manifest.json` | <=32 KiB, at most 16 component descriptors; source/process provenance, capture windows, coverage, limits, continuation and member hashes. |

One archive has at most 16 fixed/code-generated relative member names, no directory
walk, supplied paths, absolute paths, drive names, `..`, duplicate members or symlinks.
No environment dump, raw logs, exception text/locals, cache payloads, SQL inputs,
authority transcripts, credentials or privileged launch files. Redact/allowlist
before compression and hash the final exported UTF-8 member bytes. The manifest
does not hash itself; the returned artifact descriptor contains ZIP byte size/hash.
Hashes identify bytes, not authenticity or recovery authority.

Each component descriptor carries schema, availability (`available`, `partial`,
`unavailable`, `not_applicable`), exact reason, source kind, capture start/end,
source observation time/range, publication watermark if available, export UTC,
included/available/omitted counts, retention cutoff, byte length and SHA-256.
Use unknown counts/times explicitly where measurement failed. Source freshness
and export freshness are different. Bundle capture is not cross-source atomic.

Process identity is the existing diagnostic UUID, PID and available event thread
IDs, with `native_creation=unavailable_not_collected`. Source identity defaults to
`unavailable_not_exposed_by_runtime` for commit/release/host authority rather than
running Git or reading protected launch evidence. Include code-owned schema/build
descriptor and any already supplied, allowlisted runtime identity with provenance;
do not add source-tree hashing or a new launcher dependency to P01.2a. The operator's
separate deployed-SHA receipt supplies release association during acceptance.
This explicit absence is intentional; P01.2b supplies safely projected issuer facts.
One existing available identity must be included when the runtime scope is
admitted: `AuthorityClient.deployment_hash`, validated as a 64-hex primitive and
labelled `authority_deployment_hash_from_loaded_runtime`. It is not the Bot Git SHA
or evidence of current provider health. Its capture time is known; the earlier
validation time is unavailable unless already recorded. Do not serialize the
client, registration, process-bindings object or configuration wholesale.

### Attachment pressure and continuation

Hard ZIP budget is `min(destination_limit, 8 MiB)`; reject values below 64 KiB or
above the supported range at the service boundary. Check again at delivery.
Incident evidence has priority over optional components. Work in this order:

1. Collect frozen optional snapshots independently, then stream the complete
   incident archive using the existing incident projection and cutoff. Reserve
   32 KiB for minimal manifest/ZIP completion; bound summary aggregate entries to
   256 per category. Count contributions to unrepresented groups in an explicit
   `other_contributions` bucket; their distinct group count is unknown unless
   actually tracked. Do not call that counter a count of unique omitted groups.
   Incident details remain complete.
2. If incidents fit, pack whole optional components in priority order: startup,
   diagnostic health, operation records. If a component does not fit, record its
   exact omitted rows/bytes and offer **Download remaining diagnostics** from the
   same frozen generation. The incident archive can be complete while bundle
   coverage is partial. Do not trim incident text to make room for diagnostics.
3. If full incident collection exceeds compressed/uncompressed/count/time bounds,
   discard the unfinished ZIP, return a small partial evidence ZIP with a truthful
   manifest and offer the existing **Download incident report parts** beginning
   at `after=None`, with the same cutoff when one was obtained. No abandoned prefix
   was delivered, so it must not advance the cursor. No automatic second full scan.
4. Ordinary parts preserve existing cursor semantics: advance only after inclusion;
   final part completes enumeration through the cutoff. A single incident that
   cannot fit that destination remains an explicit blocked record, with cursor
   unchanged and required byte budget stated. No truncation, silent skip, broader
   destination or claim of completeness. At the normal 8 MiB budget, qualification
   must prove a maximum SQL-contract incident fits after safe projection.
5. Missing/corrupt/denied optional evidence never turns available incidents into
   an error. Incident-store failure yields diagnostic-only partial evidence and
   `incidents_available=false`; never an empty complete census. Authorization
   failure is not caught as an optional-source failure and returns no attachment.

Diagnostic continuation partitions whole operation rows and whole startup records,
uses fixed part filenames, repeats the manifest/coverage descriptor and retains
the same bundle ID/generation/hash chain. One row <=32 KiB fits the 64 KiB minimum
with bounded metadata. No automatic multi-send or background upload. At most two
idle frozen diagnostic sessions, each <=17 MiB encoded and 600 seconds lifetime;
evict the oldest idle session if necessary, never an active delivery. Tokens are
opaque, random, bound to actor/guild/channel/recovery scope and process incarnation.
The session stores no privileged raw material. Expiry/restart means unavailable
continuation, explicitly requiring a new collection; it does not mean lost domain
evidence. View memory is not authorization. No SQL continuation ledger is required
for this disposable read-only convenience.

## Build ownership, concurrency and cost

One report build/delivery owns a process-wide nonblocking admission slot; zero
queued builds. A second click receives busy without reading SQL or cloning
snapshots. Apply the same slot to direct service callers and diagnostic continuations.
The slot remains owned until worker settlement and attachment disposal, including
repeated cancellation; an observer timeout must not make a second build eligible.
Do not coalesce actor-bound downloads or let unrelated repair calls use this slot.

Make this explicit in the API: a report-request context owns the admission lease;
the UI acquires it before offload and closes it in `finally` after send/disposal.
The worker accepts only that internally issued lease, and direct service callers
use the same context around build and byte consumption. Keep the old synchronous
`download_complete_report` facade as a build-only compatibility adapter: it acquires
the same slot for its entire synchronous build and releases on return, since it
does not own any delivery. Its caller owns returned bytes. New UI routes use the
request context, not that compatibility adapter. Existing ordinary report parts
join this request context in the UI; no new generic recovery-action queue is added.

The existing owned offload remains the physical worker primitive. Snapshot capture,
JSON encoding, redaction, hashing, compression and all DAL reads occur there.
Use a report-specific cancellation flag to stop between pages/components; while
an entered DB/file operation is blocked, retain ownership and drain it. Runtime
caller ownership must cover the worker's service scope as it does today. Shutdown
closes report admission, stops unstarted collection, drains entered work, releases
ephemeral buffers, then permits diagnostic-sink shutdown. No detached executor.

Report-only runtime admission tries the installation lock and runtime condition
without waiting, refuses reconfiguration/closed/stale inherited context, and
registers the caller under the same condition before releasing it. There must be
no check-then-register race. Use the existing installed bundle or already-published
recovery-only bundle; never install, reconfigure, activate or bypass drain. Busy
admission makes incident evidence unavailable for this attempt while independently
authorized in-memory diagnostic components remain exportable. Existing repair and
producer calls retain the default waiting policy. Do not hold installation/runtime
locks during serialization, SQL reads or Discord delivery.

| Budget | Decision / qualification |
|---|---|
| Build elapsed | 30 s cooperative collection deadline, checked before/after each page and component. Not a promise to kill a native call at 30 s. Return explicit time-bound continuation after current call settles. |
| DAL working set | Bundle page size 10 plus lookahead, default ordinary-page API unchanged. Maximum raw evidence per fetched page follows verified SQL constraints; do not fetch all rows. |
| SQL timing | Preserve installed factory/transaction cleanup. Inspected application path has 5 s login, 15 s statement and 1 s lock timeout; the reader path uses the existing operational retry factory and must be reported with its actual settings. No collector retries. No global timeout/isolation/lock changes. The 30 s budget is cooperative and can overrun by an entered page/cleanup; a native call remains owned. Measure both supported profiles; an unbounded/unqualified profile cannot be advertised as meeting the latency gate. |
| Logical build memory | One <=8 MiB ZIP, <=17 MiB encoded diagnostic snapshot, <=10+1 bounded incident rows, <=256 summary groups per category, no all-incident list; at most two retained diagnostic sessions (34 MiB). |
| Measured process overhead | Additional peak RSS <=256 MiB at all hard limits, including Python/driver objects and temporary ZIP copies; normal 18,000-incident/64-operation fixture <=128 MiB. These are release gates, not measured results. |
| Archive I/O | No report spool files or log reads. Optional sink persistence has the independent 96 MiB absolute disk budget above. |
| Normal latency | Matched synthetic 18,000-incident/64-operation fixture: p95 build <=5 s, p99 <=10 s; 200 paired runs. Use identical machine/source/data and report native/synthetic IO separately. |
| Producer cost / loop impact | Keep enqueue p95 <=1 ms/p99 <=5 ms; matched business median overhead <=2%, p95 <=5%, p99 <=10%; p95 heartbeat delta <=5 ms/p99 <=20 ms. Normal load has zero new drops; overflow tests have exact declared losses. |

Use DEFLATE level 1, streaming incident writes and incremental hashes. Avoid
quadratic full-archive serialization on every row. At most one incident scan per
action and no automatic retry on build failure. If measured budgets fail, narrow
the implementation or return a revised decision; do not silently raise limits.
Native driver/disk hangs cannot be forcibly bounded by Python. This residual limit
is retained explicitly and cannot be hidden behind a completed-drain claim.

## Access, redaction and failure isolation

Authorize before every privileged read using the existing configured admin,
guild and notification channel triple. Reauthorize at service continuation lookup
and immediately before send against current configuration and interaction identity.
Bind the store scope to the session; reject configuration/scope changes. Preserve
ephemeral output and `AllowedMentions.none()`. Close `discord.File` and its backing
buffer in `finally` on success, timeout, cancellation and send error. A failed send
does not change incident/business state or start a replacement download automatically.

Use the incident allowlist and existing text redactor as independent protections.
Diagnostic projection accepts fixed primitive schemas before storage; the bundle
validates restored input again. Do not invoke arbitrary properties, `repr`, error
formatters, or recursive unbounded dictionaries. Bound depth at four, collection
counts, integer ranges and UTF-8 bytes; reject non-finite numbers. Failure reports
contain classification, timestamps and counts without raw sensitive text.

Collection must not call `refresh`, adapter `inspect/reconcile/execute`,
`observe_recovery`, retry admission, provider/Sheets health, startup completion
checkers, import/export entrypoints or source installation. Composition constructs
existing adapters; negative tests must cover its actual call path, including
missing runtime/recovery-only mode, rather than stubbing the entire service facade.
The current `recovery_caller_scope` uses existing installed/recovery bundle ownership;
collection must not add an activation or probing fallback when that scope is absent.

Missing one monitor/cache/startup provider must not suppress other optional
components. Use per-source guards; do not rely solely on `recovery_health.report()`,
whose aggregation can fail as a whole. Optional projection errors never weaken
configuration attempt receipts, publication receipts, ownership or original results.

## SQL / persistence verdict

Source-compatible Bot-only proposal; not a deployment-readiness verdict.
`dbo.RecoveryIncident` has `IncidentID`, `ScopeKey`, `SourceKind`, `SourceID`,
`State`, `Revision`, `EvidenceJson`, `FirstSeenUTC` and `LastSeenUTC` used by the
current report. State is open/resolved; do not invent a partial SQL incident state.
Its JSON constraint is 1,048,576 UTF-16 bytes for export jobs, 32,768 otherwise.
`dbo.RecoveryAction` supplies state/kind/created/updated/result fields; ResultJson
is nullable and <=32,768 UTF-16 bytes. Both definitions were read from the SQL repo.
`IX_RecoveryIncident_Pending` and `IX_RecoveryAction_Pending` exist; neither is a
new report-through-cutoff performance guarantee. Measure the actual paged query,
repeated count and OUTER APPLY cost before acceptance; no speculative index here.

No SQL schema, grants, ProcConfig, import staging, writer transaction, required
receipt, source registration or provider protocol changes. A smaller optional
page parameter is Bot DAL code and belongs in the Bot Changes review. Qualify real
GUID ordering and count/cutoff races; Python lexical UUID sorting is not a SQL-order
proof. Reads at different times remain nontransactional across pages. If totals
change, return incomplete/recollect guidance rather than certify a frozen census.
No native SQL experiment or production access is authorized by this design.

## Qualification packet

Implement tests beside the existing suites. New test files:
`tests/test_recovery_evidence_bundle.py`, `tests/test_startup_outcome_projection.py`.
Extend `tests/test_operation_boundary_evidence.py`, `tests/test_recovery_backlog.py`,
`tests/test_recovery_report.py`, `tests/test_monitor_startup_diagnostics.py` and
`tests/test_recovery_report_sql.py`, plus `tests/test_export_runtime_composition.py`
for nonwaiting report admission and unchanged default ownership. Preserve the actual
V1 reader in compatibility tests; do not merely test two functions changed together.

| ID | Scenario and required assertions |
|---|---|
| Q01 Artifact reconstruction | Open the real ZIP, validate every member/hash/byte count/schema, reconstruct startup entry -> deadline -> child return -> parent verification -> terminal. All incident IDs match the cutoff enumeration, including resolved rows. No self-hash or cross-source atomicity claim. |
| Q02 Typed outcomes | False child/parent success; true child/parent failure; multiple concurrent children and verifier child; unknown/no checker; profile memory/disk split; main/last-KVK split; tracked partial restoration. Original business return object and exception identity unchanged. |
| Q03 Retained milestones | Thousands of repeated detail events around entry/deadline/cancel/failure/terminal; slots survive detail trimming, first failure survives later success; exact coalesced/trimmed counts. Saturate children, contexts, queue, critical reserve, rows and whole-file bytes separately. |
| Q04 Restart compatibility | Real V1 files, V2 files, mixed legacy/new operations, downgrade/upgraded V1-only interval, duplicate milestone events, malformed/unknown schemas, truncated JSON, timestamp/UUID/type/NaN failures and corrupt-preservation cap. No counter inflation or poison blocking later valid records. |
| Q05 Publication truth | Pause before replace, fail write/flush/replace, permission denied, disk full, V1 succeeds/V2 fails and reverse, idle sink and late event. Memory can be current while disk is failed; last-success time/hash never advances on failure. Failed sink never recursively logs or changes business results. |
| Q06 Missing sources | Each optional source missing/corrupt/oversize/failing independently, sink not configured/worker dead, missing installed runtime, incident store unavailable, one malformed incident. Useful components remain available; authorization failure emits none; no false zero/complete/healthy state. |
| Q07 Bounds/continuation | Normal 17,431 and 18,000 incident fixtures; maximum single SQL-contract incident; incompressible evidence; exact byte boundaries including ZIP central directory; small 64 KiB limit; incident overflow, diagnostic overflow, summary cardinality, 30 s deadline. Cursor advances only after delivered inclusion; diagnostic parts share frozen generation. |
| Q08 Access/privacy | Wrong user/guild/channel, changed config before send, wrong session scope, expired/restarted token, replayed token, 2-session capacity, lowered delivery budget, send exception/cancellation. No read before auth, no cross-scope bytes, redacted credential-shaped text, no raw object/stringification or unsafe member names; buffers close. |
| Q09 Real ownership | Barrier-held physical thread, second download, direct service caller, cancel before/after entry, repeated cancellation during DB read/compression/send, shutdown, runtime reconfiguration and stale inherited context. Report admission refuses immediately while ordinary callers retain their existing semantics. At most one UI build/delivery, zero queued builds, no early slot or runtime-owner release; no detach/re-entry. |
| Q10 Passive collection | Fail-on-call spies on provider/probe/repair/import/export/verification/activation paths through real composition. Compare business call counts/returns/receipts with collection off/on. Read-only SQL report and in-memory snapshots are the only data sources. |
| Q11 Native report reads | Existing disposable SQL fixture with real RecoveryIncident/Action definitions: all states/scopes, GUID ordering, zero rows, concurrent insert/update, action joins, 10+1 page, query failure and cleanup. No business ownership acquired and no active transaction leaked. Explicitly separate source/schema checks from native execution evidence. |
| Q12 Cost and shared callers | 200 matched off/on pairs, normal/full-bound/slow-sink/saturated cases; counts, p50/p95/p99, RSS, loop lag, queue/high-water/loss, disk bytes and drain. Actual MGE callback/owner, event delivery and legacy delegate cases retain P01.1 behavior. Synthetic cost is not production performance. |

Additional existing suites to run for shared/lifecycle adoption:
`test_operation_timing.py`, `test_p1_owned_operations.py`,
`test_configuration_attempt_recovery.py`, `test_proc_config_import_offload.py`,
`test_player_stats_startup.py`, `test_profile_cache_ownership.py`,
`test_event_rehydration_lifecycle.py`, `test_tracked_view_restoration.py`,
`test_graceful_shutdown.py`, `test_recovery_backlog_sql.py`,
`test_guided_recovery.py`, `test_operator_diagnostic_payloads.py` and
`test_interaction_safety.py`, `test_startup_lifecycle.py`,
`test_mge_publication_ownership.py`, `test_mge_refresh_ownership.py`,
`test_mge_finalisation.py`, `test_event_delivery.py` and
`test_recovery_monitor_observation.py`. Run a full suite before promotion because the
shared helper, startup and persistence change. Skips remain unexecuted coverage.

Run focused tests first, then architecture/deferred/security-routing validators,
explicit-path test selection, scoped lint/type/hooks, smoke imports and command
registration. Full Windows pytest must use log isolation with source/fixture hashes
and retain the audit output outside operational logs. Do not rerun a broad suite
after documentation-only closeout unless a new runtime change justifies it.

## Refactor and security decisions

Fix within this package: ambiguous shared result storage, missing stage mapping,
retention/publication ambiguity, optional report failure coupling, unbounded
aggregate cardinality and absent report admission/attachment cleanup. Keep business
orchestration in services and SQL in DAL. No direct SQL was found in the touched
view/report entry surfaces. Do not rewrite the legacy lifecycle or the raw-log CLI.

Broader incident retention and repeated full-count query optimization remain with
the already recorded P04/P02 work respectively; no new independent debt is asserted.
If implementation proves a new unrelated defect, capture it in the required
Deferred Optimisation structure, or the security workflow when applicable.

Applied `k98-security-review-routing`: documented skip for this exact documentation
packet/navigation/status delta, because no runtime, SQL, configuration, permission,
filesystem behavior or deployment policy changed. No security scan launched.

Implementation requires `$codex-security:security-diff-scan`: **Scan type: Changes,
Deep off**, exact refreshed mirror base to final candidate, including shared callers,
archive/restore/session/input boundaries and DAL paging. Record hashes, coverage and
finding disposition. Private patch promotion requires its own exact history target
and equivalence/review gates. SQL repository has no proposed diff; if that changes,
stop for a separate SQL design and Changes target. Tests are not security approval.

## Operator validation and next implementation boundary

After separately approved implementation/review/promotion, assess installed updater
classification and current retained work before the next necessary deployment. A
normal Bot-only patch can still need authenticated source inventory updates; this
packet does not claim routine updater eligibility. No command IDs, SQL migration,
provider probe or protected-launcher change is proposed.

After that authorized deployment, use one normal complete-report download on the
recorded deployed target. Check incident totals/cutoff, member hashes, known stage
labels, child/parent outcome distinction, publication watermark and honest legacy
gaps using naturally occurring evidence. Preserve the artifact privately. Observe
V2 restoration at the next independently necessary restart; do not request another
restart, import/export or deliberate fault just to populate acceptance evidence.
Carry unexercised production cases explicitly alongside controlled qualification.

The concrete next decision is approval to implement this P01.2a Bot slice and its
local qualification, starting with typed observations and compatibility, then the
bundle/service/UI path. The whole slice must pass Q01-Q12 before release. Do not
ship only a larger buffer or a ZIP wrapper and declare the outcome/milestone work
complete. P01.2b is independently scheduled; subsequent P01/P02/P03/P04 packages
must extend and test these schemas as they deliver their own boundaries.

Conditional references: diagnostics, startup/shutdown/singleton runbooks,
`REVIEW_HELPERS.md`, P1 operation lifecycle and Windows ownership/access contract.
Architecture-scope, test-selection, SQL-validation and security-routing skills were
used for this design. Runtime implementation remains unapproved by the handoff,
not blocked by a missing reconfirmation of the accepted scope.

## Validation of this design-only delivery

Architecture validation passed with zero Python files changed; deferred-item
validation passed for the four task documents; security-routing validation passed
with zero errors/warnings; explicit-path documentation test selection completed.
Its generic smoke/registration recommendations are skipped because this delta
changes no runtime or command registration. Runtime pytest, native SQL, cost
measurement and production acceptance are deliberately unexecuted design gates.
The future implementation has a separate selector/qualification manifest.

Source/test path checks, introduced-link/whitespace checks, preserved README/index
hashes and source-checkout cleanliness are retained in the private validation
receipt. Existing programme files remain local/unpublished. The pre-commit wrapper
was not retried after the handoff's cache/environment limitation; direct document
checks and repository validators were used without reinstalling environments.
