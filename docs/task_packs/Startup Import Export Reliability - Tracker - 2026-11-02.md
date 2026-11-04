# Startup, import and export reliability: progress and evidence

> **Current E80 - 4 November 2026:** Full P01.3 implementation, validation and PR preparation are approved, including persistent Refresh. Implementation is in progress on mirror branch `codex/p013-passive-health`; earlier implementation holds below are historical. No publication, merge or production action is implied.

> **Current programme checkpoint - 4 November 2026 (E68-E79):** P01.2a is deployed and accepted for its declared reporting/evidence scope at private `67c4e12a8ecf0c25280770860480ac65a6826602`. P01.3 design decisions are agreed and the reported Health card timeout is included in the revised design; implementation remains unapproved.
> Read the [P01.2a closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Closeout%20-%202026-11-04.md) for delivered corrections, evidence limits, learnings and remaining owners. The [P01.2b design and qualification packet](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Design%20and%20Qualification%20-%202026-11-04.md) records E72-E74 and the E75 operator decision to close proactive startup instrumentation without deployment. Use existing evidence and issue-driven best-effort collection; no replacement instrumentation is queued.
> Earlier dated statuses, holds and next-action instructions in this document are retained history and are superseded for current scheduling. P01.3-P01.6/P02-P05 and exact incident recovery remain open; no replay of accepted work.

Updated: 4 November 2026. [Agreed scope and acceptance](Startup%20Import%20Export%20Reliability%20-%20Scope%20-%202026-11-02.md).
Owner for policy/acceptance: Chris Watts. Delivery owner: Codex in this chat.
Historical sequence is retained below; E68-E79 supersede earlier next-step wording.
P03a.1 remains operationally complete under the user's accepted E43 evidence; do not replay it.
P03a.2 installed source/seed but failed before an incarnation on 3 November (E47).
The startup custody correction (#478/#719) and separately receipted recovery (#479/#720)
are now merged, reviewed and qualified (E48). The exact private target is `b6ec4a0eeabd3d32d8fd98726ab8a6af5e6b829b`.
The user has applied recovery and restarted the bot. E49 verifies corrected source,
one successor, Discord readiness and the installed updater from supplied evidence.
The next ordinary pipeline failed at configuration writer admission (E50, SQL 51421),
before export dispatch. Functional acceptance remains open. The user explicitly chose
P01 design next (E51), then P02, remaining P03, P04 and P05. F09 stays in P02; the
earlier F09-first recommendation is superseded, with the E50 evidence preserved.
Scope D01-D06/A13/A14 makes boundary visibility and diagnostic safety mandatory.
The old P03a.2 deployment packet must not be rerun.

## Current position and next action

**Documentation carry-forward obligation:** the next appropriate authorized reliability mirror PR and private promotion must include the complete [documentation and archive-move manifest](Startup%20Import%20Export%20Reliability%20-%20Documentation%20Carry-forward%20-%202026-11-04.md). Verify actual PR files and final trees; missing documentation blocks release readiness.

**Current E79:** P01.3 design records agreed 60-minute provider freshness, existing recovery-monitor semantics, lock-free presentation reads and five-minute rereads, actionable alerts/common interpretation, existing-report integration and telemetry/cost gates. The [revised design and qualification packet](Startup%20Import%20Export%20Reliability%20-%20P01.3%20Design%20and%20Qualification%20-%202026-11-04.md) includes a proposed persistent Refresh/early-acknowledgement correction for the reported card timeout. No new whole-bot outage detector is required; user reports are accepted for rare outages. Automatic log features remain removed in scope and explicit inspection retained. No implementation or operational action is approved. E76's P01.2b closeout and archive preservation remain intact.

**Historical E75:** the operator declines proactive P01.2b instrumentation: theoretical coverage does not justify measured cost and risk. Keep the bot/startup unchanged and use existing evidence; any further collection must address an actual incident gap with proportionate cost and safety. No replacement observer/helper or mandatory new exporter is queued. This closes the proposal by scope decision, not by delivering the feature. P01.3-P01.6/P02-P05 retain their outstanding work; no production or recovery action is authorized.

**Historical E74:** the user approved the smaller validation-only external observer, holding back the E73 native issuer helper. Fourteen functional cases and 120 matched pairs completed; all fixture process jobs settled. Cold attachment added 3443.3 ms versus a 500 ms maximum, so integration is stopped. See the [replacement review and E74 results](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Revised%20Transport%20Review%20-%202026-11-04.md) for measured costs, useful native-exit evidence and unresolved security/lifetime/coverage gaps. No runtime or production change; no user-visible P01.2b delivery.

**Retained E73:** the requested [replacement transport review](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Revised%20Transport%20Review%20-%202026-11-04.md) recommends fixed pagefile-backed structured-event mailboxes and native process observation, preserving ordinary stderr. It explicitly requires approval to replace arbitrary stderr capture with structured early-failure evidence: pre-emitter failures may retain launch/exit without traceback, and unpublished memory can be lost. Initialization/native-helper feasibility and all existing non-regression gates remain. No replacement implementation or experiment; E72's stop remains active pending the revised design decision.

**Retained E72:** the user approved local implementation/isolated qualification and required a stop if the design changes. Native Desktop PowerShell 5.1 observer loss caused the inert child to exit 120 instead of its planned 37; both control cases preserved 37. The sole-reader stderr pipe fails B03/A14. Implementation stopped before application integration. No deployment or production change.

**E71 supplied evidence:** task XML, gate, policy and updater manifest are reconciled in the P01.2b packet; all 817 policy source hashes match retained private source. Targeted SQL evidence confirms six open historical incidents, seven pipeline stages and retained captures at its observation time. No further operator collection is needed for this design pass. Live custody/action-time evidence remains a later gate.

**Retained E68-E70:** P01.2a is deployed and accepted at private `67c4e12a8ecf0c25280770860480ac65a6826602`. Report 73 confirms bounded collection with retained progress, diagnostic preservation and correct startup attribution. The closeout records all evidence limits. P01.2b review/design specifies early/offline evidence, a proposed manifest and B01-B09; E71 supplies bindings and E72 supersedes the proposed stderr transport. P01.3-P01.6/P02-P05 and exact incident recovery remain open.

**Historical E65:** the operator deployed private `07bc9d6ebd5964f9bf660822f03a932a2472d966`; source/startup release verification passed. P01.2a functional acceptance remains open: Report 70 delivered zero incidents and unavailable diagnostics after 31.147 seconds. An isolated local probe confirms shared-deadline suppression of healthy diagnostic sources. Ordinary-report monitor availability, current V2 evidence visibility and overlapping gateway lag also need focused investigation. See the [review/acceptance receipt](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Review%20and%20Merge%20-%202026-11-03.md). No additional restart, replay or production action was performed during verification.

**Historical local checkpoint E62: ready for PR review.** E61 authorized completion through PR readiness. The [final receipt](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20PR%20Readiness%20-%202026-11-03.md) supersedes E60 cost/updater holds for this local candidate. PR creation and later promotion/deployment remain separate; production acceptance is still open.

Historical deployed checkpoint (E55): the user deployed private
`0247371d90ec88d4c0639e9200164f4256086037` after the updater prerequisite and preflight.
Supplied deployment and live evidence validate P01.1's exercised startup/diagnostic
behavior. The original configuration result survived its observation deadline;
all eight startup references correlate with persisted evidence. The diagnostic
worker was alive with zero reported drop/failure/eviction/context-loss counters.
The [live validation receipt](../../.codex_artifacts/startup-import-export-review-20261102/p011-live-diagnostics-validation-20261103.json)
and `p011-report69-review.json` retain input hashes, checks and limits alongside E54
qualification. Production cancellation/fault injection was not performed; restoration
of this file at a later production restart remains a natural observation, not a new
restart request. Fresh end-to-end import/export is not certified.

Current scope instruction (E56): incorporate P01.1 learning into remaining P01 and
P02-P05 scope now, and deliver improved evidence collection as soon as practical.
Next is P01.2a collection/clarity/milestone retention, then separately qualified
P01.2b early issuer evidence. P01.2a can be reviewed/deployed without waiting for
P01.2b. See the amended [P01 design](Startup%20Import%20Export%20Reliability%20-%20P01%20Design%20-%202026-11-03.md)
and scope ownership matrix. Runtime implementation is not authorized by this scope
amendment. F09 stays P02; retained-pipeline continuation stays P03; wider P01/P05
acceptance is open. P03a.1/E43 and P03a.2 installed/startup acceptance/E49 remain
preserved. Do not rerun the P01.1 deployment package or completed business work.

E57: the user accepted the amended scope and requested a focused new P01.2a chat.
The [P01.1 closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.1%20Closeout%20-%202026-11-03.md)
records requirement/task dispositions. The [P01.2a scope and handoff](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Scope%20and%20Handoff%20-%202026-11-03.md)
is the next chat's starting point: begin exact design/qualification planning now,
without asking again whether the already accepted scope is wanted.

E58: the focused [P01.2a design and qualification packet](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Design%20and%20Qualification%20-%202026-11-03.md)
is prepared against the clean deployed-source checkout. It fixes the typed
child/parent outcome, milestone/compatibility, incident-first archive, explicit
continuation, publication-health and collection-budget decisions, with Q01-Q12
qualification. The next boundary is approval of this Bot implementation and local
qualification. No runtime code, SQL, publication or production action was performed.

E59/E60 supersede that implementation-approval boundary: the user approved the
design and local qualification. The [implementation receipt](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Implementation%20and%20Qualification%20-%202026-11-03.md)
records the candidate on `codex/p012a-evidence-bundle`, final Changes review and
controlled tests. The broad Windows run has 11,066 passes and 31 authenticated
updater-inventory failures; the source transition is still a release gate. The
200-pair report latency/memory gates passed, but producer median/p99 overhead failed
Q12. Keep P01.2a open for a focused cost correction; do not raise the limits or
claim release readiness. No PR, merge, deployment, restart or
provider/recovery mutation has occurred under E59.

The user has accepted the broad/focused analysis and delivery direction. The
[delivery handover](Startup%20Import%20Export%20Reliability%20-%20Delivery%20Handover%20-%202026-11-02.md)
is prepared for a fresh delivery chat, with all 32 findings assigned to packages and
the uncommitted-document/private-evidence transfer requirements. The user has now
approved the adjusted sequence and requested creation and immediate start of that chat:
S2 dependency review, P03a for the blocked export (any exact prerequisites first), then
P01, P02, remaining P03, P04 and P05. The user subsequently approved the concrete
P03a.1 package. Do not ask to reconfirm that approval or the accepted sequence.

The [S2 decision packet](Startup%20Import%20Export%20Reliability%20-%20Tracing%20-%202026-11-02.md#s2-decision-packet-and-p03a-implementation-boundary)
now supplies the outcome/check/retention policy, dependency decision, exact P03a state
machine, file/SQL/test manifest and bounded first implementation target. There is no
broad P01/P02 prerequisite to P03a.1; exact receipt reconciliation, durable intent and
owned scheduling are mandatory within P03a. A normal restart cannot be assumed to
install recovery while the old stream is unclosed: P03a.1 uses a protected runner before
normal deployment, with P03a.2 runtime recurrence prevention required before F02 closure.
Original P03a.2 implementation checkout: `C:/discord_file_downloader/.codex_artifacts/p1-mge-mirror-review`,
branch `codex/p03a-runtime-settlement`, mirror base
`a5fa112a29b2f8b9f82f032b6d35d7eccf77f797` (synchronized from merged private `83a4b656`).
The original checkout/docs/private evidence remain preserved. P03a.1 production recovery
was completed by the user. Codex has not executed a production operation. Six real local SQL/DPAPI cases qualify the implemented P03a.1 service with
synthetic private evidence, including 177 requests and three-second contention. Actual
installed custody/process/package and production private proof passed for the exact
P03a.1 operation in E43; P03a.2 retains its own qualification and deployment gates.
Both Git histories have completed final Changes reviews with zero security findings (E42).
Private promotion preserves the production history and exactly matches all nine reviewed
mirror files. The deployment path is the standalone packet: the normal updater classifier
returns `COORDINATED_RELEASE_REQUIRED` for the two new protected recovery service paths.
Do not perform a routine Bot upgrade for this commit. Carry normal source installation
into P03a.2 coordinated-release qualification after P03a.1 operational acceptance.

Current recovery delivery (E48): startup fix [#478](https://github.com/cwatts6/K98-bot-mirror/pull/478)
and [#719](https://github.com/cwatts6/k98-bot/pull/719), then recovery [#479](https://github.com/cwatts6/K98-bot-mirror/pull/479)
and [#720](https://github.com/cwatts6/k98-bot/pull/720), are merged. All actionable review
comments are addressed and resolved. Final Codex reviews, separate Changes security
reviews and private Linux/Windows/secrets CI pass. The recovery preserves original
failure receipts, start request and real predecessor lineage; it requires fresh native,
SQL, ownership and startup exclusion checks before one successor start.
Use `K98-P03a2-Startup-Recovery-20261103T104525Z.zip` and `K98-P03a2-Startup-Recovery-20261103T104525Z-Deployment-and-Validation.md` under the private evidence directory, with verified copies
provided for the operator. The guide gives Inspect, one Apply, normal-updater upgrade
and read-only validation in order. A refusal requires evidence review, not a bypass.
The original E46 packet and E47 failure remain historical evidence. The expected
application-write evidence ACL is retained. No SQL migration, activation-flag change,
provider replay or forced claim/session closure is included.
P03a.1 remains complete. E49 accepts the recovered startup and updater upgrade from
operator-supplied receipts. M07/F02 remains open for the next genuinely new ordinary
export's durable request/result/pacing/closure and destination evidence. Do not repeat
deployment or restart. Report 67 has three operational records plus their overview:
the old cancelled stats projection is existing F28 (remaining P03/P04), the startup
player-cache queue needs fresh domain verification, and ProcConfig has a successful
inner import/capture log but an unconfirmed outer attempt (consistent with P01/F08).
The user confirms F28 stays in its later package. Zero open incidents is not the
acceptance gate; exact disposition and absence of conflicting ownership are.
Early issuer stderr/exit diagnostics remain a separately recorded P01 resilience item.

E50 / Report 68 supersedes the pending startup reconciliation above: the original
startup queue and ProcConfig attempt are resolved, with exact success/no-export
receipts. A new pipeline completed stats import and player cache, then failed before
configuration writes when the zero-wait legacy snapshot guard returned 51421. Its
five linked open records plus historical F28 account for the six operational records;
the overview is separate. Eight direct-path source files are unchanged by P03a.2.
A namespaced local SQL experiment reproduces observer-first producer refusal and
successful producer entry after observer release, with no application-table/provider
access and no retained experiment locks. The production lock holder and original
negative applock return were not captured. F09 is a known P02 dependency; this is
failed whole-flow acceptance, not proof of a post-provider settlement regression.
Keep F28 in later P03/P04. E51 retains F09 correction/qualification in P02 and starts
P01 design first. Prepare an exact remaining-stage recovery/deployment dependency
plan without whole-import replay or blanket clearing. E50 alone authorized no
runtime implementation or production action.

Historical review and the main tracing/cross-check pass are recorded in the
[Stage 1 tracing handback](Startup%20Import%20Export%20Reliability%20-%20Tracing%20-%202026-11-02.md).
It includes the producer/observer map, reproduced startup completion gap, static
observer/producer conflict and F13-F30 from wider callers. F20 reproduces an observer
leaving its own file lock behind and links it to the earlier #688 wrapper correction.
F21 traces conditional maintenance/performance logging inside atomic configuration
publication; its SQL contract fixture substitutes a stub for that callee. F22 expands
the maintenance map to import, player-report and KVK-output publication. F23/F24 reproduce
calendar audit-failure misclassification and deadline/worker-ownership loss. F25/F26 add
partial cache-publication reporting and broad connection-fallback behaviour. F27 adds a
report-validator branch that classifies contention as a failed check; driver diagnostics
survive, and earlier producer-guard waiting already works. Fresh Report 66 and the later
screenshots confirm an old export restriction plus a cancelled stats admission whose
parent incident remains open (F28). F29/F30 reproduce Rally failure-history deduplication
and queue CSV logging preventing processing. The
[action census](Startup%20Import%20Export%20Reliability%20-%20Action%20Census%20-%202026-11-02.md)
classifies all 73 allowed pairs (52 action names) and preserves existing automatic recovery
outside the central allowlist. The [coverage ledger](Startup%20Import%20Export%20Reliability%20-%20Coverage%20-%202026-11-02.md)
attaches 242 scoped-edge reviews and 129 source-backed boundary dispositions to all
371 historical paths. B01-B15 explain the actual shared edges and independent-domain
limits; these are coverage counts, not whole-module approvals or a percentage complete.
The **main first pass and separate source outlier sweep are complete for the recorded
scope**. The [final sweep](Startup%20Import%20Export%20Reliability%20-%20Final%20Sweep%20-%202026-11-02.md)
reconciles 322 additional signal-path candidates from 2,486 tracked files and records
F31's legacy Rally custody/error gap and F32's timing-logger interference. These are
dispositions, not whole-module approvals.
The user's 10:58:15 UTC SQL read now confirms the old export's exact closure blocker:
request 177 has no terminal event; its frozen mutation stream retains the account and
the job retains blocked ownership of 11 destinations. F02 includes the missing settlement
and stale cached-closure problem. The user's 12:01:42 UTC protected-folder read found
matching primary/replica copies of the saved response and original termination/closure
document (E37). The closure reports the exact child stopped with its job empty, version
532 and last sequence 177. This is positive historical termination evidence; the UI's
generic wording does not mean a writer is known to be running. Full request/response and
current journal/ownership validation remain part of a reviewed repair preflight. The
focused recovery design is recorded in tracing; S2 must also retain G04's per-state
automation and retention decisions, rather than starting isolated timeout edits.

Original investigation checkout baseline: `a025adb7a69aac321fd62794b871ed5903338f44`.
Implementation mirror base: `76f9578940c97acb017c810d099a07a63abba9f4`.
Authoritative SQL checkout: `7e91989f619deb46836194c7e705b0a9eb2ebe11`.
Retained deployed Bot evidence: `ad4cd9955d8fcaf7d214612d7803ab3c4c2c4bd0`;
SQL pin: `9344a37656b034dd43867435e7c039ed20ae1c5e`.
These are inspected source/retained evidence baselines, not a new live-host health claim.
Recheck drift before implementation or operational conclusions.

## Milestones

| ID | State | Exit evidence / next action |
|---|---|---|
| M01 Historical review | Complete for inspected evidence | Prior PRs and source comparisons recorded in scope and E01-E05; live PR comments were not refreshed. |
| M02 Scope and observer principle | Agreed | User accepts six workstreams, necessity review, non-interference, P0 mapping and Ark-next sequence. Documentation created 2 November. |
| M03 S1 caller/check inventory | Main first pass complete | All 371 historical paths have dispositions: 242 scoped edges and 129 independent-domain/dependency boundaries; B01-B15 and extra inspected paths explain coverage. No exclusion based only on filename/zero hits. M04a now records the independent current-inventory challenge; concrete G04 policies remain M05 decisions. |
| M04 S1 findings and proposed packages | Source handback recorded | F01-F32 and safeguards/dispositions recorded. F02's exact live closure blocker is confirmed; private evidence qualification and physical origin of the original one-second refusal remain open. Another 300 focused baseline tests and closure/timing fault experiments pass; batch totals are not deduplicated. |
| M04a Final outlier/one-off sweep | Complete for recorded source scope | Independent inventory and 322 additional dispositions recorded separately; legacy/manual entrypoints, dynamic imports/SQL, exceptional closure, cancellation and boundary exclusions challenged. Live Agent/trigger/enablement inventory and native performance remain qualification, not implied source coverage. A12. |
| M05 S2 design decision | E75 closes proactive P01.2b instrumentation by operator scope decision | P01.1/P01.2a acceptance retained. No observer or native issuer helper will be integrated under the current scope. Existing evidence and small issue-driven collection improvements are the chosen direction. Remaining P01.3-P01.6/P02-P05 ownership is unchanged; this is not proof of their completion. |
| M06 S3 implementation/qualification | P01.1 and P01.2a deployed and accepted for declared scope | E53/E54 retain shared-caller/cancellation/restart/cost qualification and updater prerequisite; E55 adds supplied deployment and live diagnostic evidence. P03a.1/E43 and P03a.2/E49 remain preserved; whole-flow acceptance is open. |
| M07 S4 operational acceptance/P0 reconciliation | P03a.1 and P01.1 exercised paths accepted; ordinary pipeline acceptance open | E49 preserves earlier startup/updater acceptance; E55 adds P01.1 deployment/live diagnostics. E50's configuration-entry 51421 and committed captures remain separate P02/P03 obligations. Fresh export evidence and F02/P0 closure remain outstanding. Any future incident disposition is assessed before its dependent deployment; zero incidents is not the gate. |
| M08 Return to P1 Ark | Pending this phase | Preserve earlier accepted cases; review remaining Ark lifecycle/admin/publication work, then continue remaining P1 programme. |

States are not percentages. Source review, reproduced defect, fixed locally, qualified,
deployed and accepted are distinct milestones; do not collapse them into a single Done flag.

### Current P01 slice status

| Slice | Status | Next action / owner |
|---|---|---|
| P01.1 | Complete for declared scope; deployed and exercised paths accepted | Preserve closeout/E53-E55. Later natural restart restoration is an observation watchpoint; no new restart required. |
| P01.2a | E68 closed: deployed and accepted | Final private `67c4e12a`; Report 73 validates retained 850-row prefix, exact continuation, independent diagnostics and eight startup references/known actors. Full and focused qualification covers unobserved faults. See closeout for limits; no business-incident or whole-programme closure. |
| P01.2b | E75 proactive instrumentation declined; proposal closed without deployment | E72-E74 establish cost/risk and limited value. Keep existing evidence collection; accept missing early detail. Further collection is issue-driven and best-effort, with no observer/helper or mandatory exporter queued. Feature-specific delivery gates are historical, not blockers; existing safety requirements and other package owners remain. |
| P01.3 | E79 design refinements agreed; reported button-timeout correction designed; implementation not started | F11 passive presentation across command/button/card, lock-free retained evidence, five-minute rereads, 60-minute provider freshness and removal of automatic log features. Persistent Refresh/early acknowledgement and H01-H09 qualification are in the revised implementation contract; preserve write-boundary controls and telemetry. |
| P01.4 | Designed; implementation not started | Upload outcome separation and optional queue audit; adopt P01.2a contract. |
| P01.5 | Designed; implementation not started | Calendar physical ownership and independent stage outcomes; adopt P01.2a contract. |
| P01.6 | Designed; implementation not started | Read-worker physical capacity and authorization-safe late outcomes; adopt P01.2a contract. |

## Evidence register

| ID | Evidence and conclusion | Limit |
|---|---|---|
| E01 | Local merged private history for #677/#679/#685/#686/#692/#694/#695/#696/#698; [coordination verification](../reference/Coordination%20lifecycle%20verification.md). | Historical scope/delivery, not current live functional proof; GitHub comments unavailable during review. |
| E02 | Private `.codex_artifacts/coordination-system-map-20261026` system map and candidate inventories: 774 Python files, explicit/indirect callsites, SQL lock sites. | Historical lexical census is a seed, not a current semantic audit or count of defects. |
| E03 | [28 October closeout](P1%20Monitoring%20and%20Import%20Export%20Reliability%20-%20Closeout%20-%202026-10-28.md) explicitly retains broader census and acceptance gaps. | Successful normal run did not exercise a live checkpoint retry. |
| E04 | Private November handoff and `production-acceptance-report65` logs, report and authority diagnostics under `.codex_artifacts/mge-isolated-vm-plan-20261029/qualification-preparation`. | Result-recording admission failed after provider response validation; blocker/hold duration unknown; closure not proved. Historical cases need separate causes. |
| E05 | Source comparison against retained deployed revision: authority lock/execution unchanged since #686; inspected retry/snapshot/pipeline/recovery paths unchanged since #698. Relevant SQL definition diff after deployed pin contains only MGE finalisation changes. | No demonstrated rollback; this does not exclude indirect timing effects or every possible regression. |
| E06 | Current source seed review: `core/sql_observation.py`, `services/authority_observation.py`, `services/recovery_runtime.py`, `services/recovery_service.py`. | Typed waiting and automatic rechecks exist; loop also invokes explicit allowlisted recovery actions. Must classify actual effects rather than assume everything called by monitoring is passive. |
| E07 | Offline current-helper experiment: worker completed once in both cases; cancelling startup observation skipped completion check and lost result, non-cancelling observation retained success. Private `startup-import-export-review-20261102/startup-observation-result.json`. | Scaled deadline and controlled worker; no actual ProcConfig body, SQL or production-cause attribution. |
| E08 | 76 focused baseline tests passed: startup diagnostics, checkpoint observation lifecycle, pipeline receipts, recovery monitoring, Sheets health. | Existing tests partly encode current behaviour; not proof of new acceptance contract. Native SQL/concurrency and production acceptance not run. |
| E09 | Current AST references/source hashes and 42-file comparison in private `startup-import-export-review-20261102`; 40 normalized files identical to retained deployed revision. Private blame attributes observer global guard to #698. | Selected sources only; mirror/deployed metadata-query differences must be considered in cost qualification. No live deployment-state claim. |
| E10 | Refreshed offline inventory: 789 Python files, 572 canonical SQL files, 600 signals/151 files, zero Python parse errors, all 371 historical candidate paths present. All 73 policy action pairs mapped; source paths verified. | Lexical/AST extraction is not a full semantic audit; dynamic/bracketed SQL, inheritance and enablement require source review. Private CSV inventories remain local; action census is durable Markdown. |
| E11 | Current-method offline guard model: observer-first producer refusal 51421; producer enters after observer release; writer-first observation defers; no remaining model locks. | Account/contract checks stubbed, no native SQL/driver timing or live attribution. Existing native observer-first checkpoint test is a different entrypoint. |
| E12 | Additional 212 baseline tests passed: 155 recovery/policy/report/receipt/configuration tests and 57 log-management/import-outcome/player-continuation tests. Total with E08: 288. | Existing behaviour, not new qualification. No production replay, native SQL contention or provider operations. |
| E13 | Wider caller review identifies F13 age/attention classification, F14 KVK read/write season lock, F15 second cache confirmation, F16 post-SQL maintenance under writer guard. Also verifies separate failure-settlement worker and live exact-completion recovery. | Static mechanisms do not establish incident frequency, actual blocking duration or the latest blocker. Existing safeguards must be preserved. |
| E14 | F17: Honor/Pre-KVK/Location audit and presentation distinctions compared with Weekly Activity. History: #491/#493/#494/#495; Honor failure-expectation test traces to cfa1d400, typed delivery-result test to fb096e3d. Six selected route/service/adapter files identical to retained deployed pin. Another 79 tests passed; total 367. | Tests expose a longstanding inconsistent outcome contract, not a rolled-back import or proof of current production incident frequency. Live PR comments not refreshed. |
| E15 | F18 source trace: final report transaction contains CHECKPOINT and backup-signal insertion before exact completion/commit. Native continuation fixture compiles real SQL but substitutes business/maintenance spans in fault cases. | Source-proven dependency, not measured live contention or native fault injection. Earlier import stages remain committed. |
| E16 | F19 notification store capacity/readability is an import-admission dependency; automatic terminal closure and closed-history pruning verified in source/tests. Evidence-origin/retention table added for 11 layers. | Do not claim there is no auto-closure or expire uncertain records. Concrete capacity/retention and degradation policies still require design. |
| E17 | F20 private `cache-observer-lock-result.json`: isolated current helper bodies show normal readback cleanup, mismatch leaving sentinel, next writer timeout, and correct cleanup through existing tracked-view wrapper. #688/9662bb80 explicitly recognised the same shared-helper exception behaviour. | Temporary files, injected dependencies and scaled deadline; no live cache/SQL/provider actions. Registry's same-named SQL lock is unrelated. |
| E18 | Another 165 baseline tests passed (notification policy/DAL, restart reconciliation, profile ownership, player startup, failure diagnostics, audit DAL); total 532. Six more Bot sources and report procedure match retained deployed pins. | Baseline behaviour/source equality, not operational acceptance. Native SQL fixture inspected only. |
| E19 | F21: configuration publisher -> sp_TARGETS_MASTER -> CREATE_DELTA_TABLES traced across caller transaction, parent/child mutex acquisitions, conditional maintenance and logging. SQL history c07058f/758f456/f5ecc3e; both procedures unchanged from retained SQL pin. Private 12-root dependency graph and seven lexical-name dispositions recorded. | Static dependency/history, not measured cost or latest blocker. Atomic-entry fixture substitutes the maintenance-bearing child. Dynamic/system execution edges still require semantic coverage. |
| E20 | 385 existing tests passed in runtime composition, configuration offload, pipeline step/normalization and Sheets module. Preserved ownership, typed-result and queued-acknowledgment paths inspected. | Separate batch; do not add to earlier 532 as distinct cases without overlap reconciliation. No real SQL/provider execution or qualification of proposed fixes. |
| E21 | F22 statement-level maintenance map extends to import Phase A, player-report and KVK-output publication; three procedures unchanged from retained SQL pin. Separately traced claim/import/archive integrity and transaction lifetimes. | Source/history review, not measured contention. Digest and receipt checks protect real custody and duplicate prevention; do not remove them as optional observations. |
| E22 | Offline current-body calendar experiments: audit completion fails after one committed upsert transaction but returns failed-fetch/validate with zero counts; stage deadline permits another lock owner before the blocked worker finishes. Four sources match retained Bot pin; blame dates audit/deadline logic to March. | Injected dependencies and 30 ms deadline; no SQL/provider/cache mutation, second business operation or live incident attribution. Generation/publication workers need their own qualification. |
| E23 | 28 existing calendar sync/pipeline/service and sheet-importer tests pass. Timeout test checks no retry using an immediately raised exception; happy sync stubs audit completion. Optional batch-commit suppression reproduced, but inspected importer callsites retain explicit commits. | Tests do not cover physical-worker overlap or post-commit audit failure. Do not attribute the unused batch-commit branch to protected imports. |
| E24 | Durable coverage ledger adds explicit per-path state for all 371 historical candidates and separately lists inspected paths outside the seed. | 52 scoped-edge reviews and 17 action-policy mappings do not approve entire modules; 302 pending records can include prior analysis not yet attached. Fresh final inventory still required. |
| E25 | F25 temporary-file current-body experiment: main calendar JSON replaced, auxiliary index write fails, returned result is failed/zero. No production Python index reader found. F26 current-body experiment: retry factory raises and direct legacy factory is then invoked. | No live cache/SQL/provider operations. External index consumers remain unverified; alternate-principal use depends on runtime context and is not asserted for normal startup. |
| E26 | Twelve cache/adapter sources match retained Bot pin. F25 sequence dates to March; F26 fallback existed before October profile extraction. 72 existing calendar-publish/event-cache/profile/registry tests pass; preserved ownership and passive-reader patterns inspected. Coverage now 68 scoped/17 policy/286 pending. | Separate test batch, not new unique aggregate or fix qualification. Local metadata, process locks and SQL ownership remain distinct. |
| E27 | Recovery DAL matrix extends F03/F09/F10 across capture, configuration, queue, unowned-hold, historical and failed/stranded-export snapshots. F27 isolated current-body experiment converts writer refusal and row timeout to SourceConflict; actual diagnostic function retains underlying driver-shaped codes. | No native SQL, monitor/store dispatch or live incident reproduction. Producer-guard SourceBusy, exact action-time checks, cheap discovery and bounded safe retry remain valuable counterexamples. |
| E28 | 26 recovery Bot/SQL sources equal retained deployed pins. F27 dates to Bot #675 / SQL #129, not a demonstrated rollback. 147 existing tests pass across six contention/recovery suites; ledger advances to 91 scoped/17 policy/263 pending. | Native contention test inspected uses QueueAdmissionDAL, not the report validator. Test batch has possible overlap with earlier runs; no unique aggregate or production acceptance claim. |
| E29 | Report 66, actual Report 65 comparison and attached 2 November scheduled-run log; private hashes and structured admission/cycle extraction retained. | Two open operational incidents plus overview; old account restriction predates today's refused admission. No fresh business SQL/provider execution proved. Report is nontransactional, not a live SQL snapshot. |
| E30 | Current-body isolated experiments reproduce misleading cancellation context, Rally error-row duplicate skip for both importers, and queue CSV failure with zero processing calls. Selected history traced; 35 follow-through sources match retained Bot/SQL pins. | F28/F29/F30 mechanisms, not production fault injection or complete native transaction qualification. F28 experiment does not substitute for strong cancellation-receipt validation. |
| E31 | B01-B15 main-pass dispositions cover all 371 historical candidates: 242 scoped edges and 129 boundary dispositions. Another 79 tests pass across seven targeted suites. | No whole-module/domain approval or unique cumulative test total. Final fresh inventory/outlier sweep not performed. |
| E32 | User screenshots at 10:25-10:26 UTC match Report 66's exact export/import/refusal incident identities; import remains open while linked cancellation is resolved. | Confirms persistence of the UI contradiction after later rechecks; no new ownership/stream snapshot or permission to clear the old restriction. |
| E33 | User-executed fixed read-only diagnostic on physical MINI_AMD at 10:58:15 UTC: one uncertain job v3, frozen mutation stream v532, request 177 prepared/dispatch_intent only, active account, 12 blocked resources (account plus 11 destinations), no closure/closeout receipt. | Bounded read-committed observations, not an atomic snapshot or current physical-child proof. Identifies current closure blocker, not the connection responsible for the original one-second admission refusal. |
| E34 | Separate final inventory: 2,486 tracked files, 868 fixtures, 680 signal files, 322 new path dispositions, zero Python parse errors. F31 legacy UPDATE_ALL/Rally edge added. Eight relevant Python methods and five SQL definitions match retained deployed pins. | Wider denominator than earlier censuses; no claim of every branch or installed Agent/trigger/externally invoked path. Source equivalence is not fresh deployment verification. |
| E35 | Actual authority/verifier methods with inert substitutes reproduce saved response before failed append, child termination before refused closure, stale cached seal after result settlement, unknown-mutation rejection and successful closure control. Timing helper bodies reproduce pre-work and post-completion interference with a raising diagnostic sink. 300 focused authority/reconciliation/legacy-closeout tests pass. | SQL refusal/close guard modeled, not native SQL. Fakes cannot prove live private evidence survives; injected logger failure is not evidence the installed handler raises. No runtime fix or production operation performed. |
| E36 | User's first saved-evidence diagnostic stopped at its 100,000-directory-entry cap before candidate blob reads. The v2 replacement streams metadata, filters before retaining candidates, keeps time/count/byte limits and returns explicit partial-search status. Windows PowerShell 5.1 tests find two matches after 100,005 old entries, cover caps/errors/disposal and decode synthetic response/closure copies without emitting payload values; six custody helpers are unchanged. | Establishes a lower bound of 100,001 enumerated files, not a complete folder count, retention fault or missing response. Local fixtures do not establish live folder speed or custody; E37 records the subsequent supplied production result. |
| E37 | User's 12:01:42 UTC v2 result: metadata search complete, 123,288 direct files enumerated in 365 ms, all 18 time-window candidates decoded, 35,736 ciphertext bytes read. Two matching copy pairs found: saved response for request 177 and saved closure v532/sequence 177 with exact child, job_empty and process_signaled true. Summary consistency checked against E33. | Protected-file discovery and historical termination evidence, not full saved-response protocol validation, a current SQL digest/ownership snapshot or fresh OS liveness proof. Replicas are redundant copies, not independent witnesses. No release occurred. |
| E38 | Delivery-design preflight reverified Bot/SQL HEADs, current branch/remotes and the unchanged original handover archive SHA-256. Current authority/DAL/private storage, broker/client, legacy closeout, stranded recovery, startup and SQL contracts traced. Existing terminal-on-frozen/close/legacy-release procedures support the proposed sequence without a schema change. | Source design, not installed-state proof. Normal drain/startup cannot be presumed to install this repair first. All 32 primary assignments retained; protected runner and runtime recurrence are separate required slices. |
| E39 | User authorized qualification on new/existing local development DB; `localhost\\K98DEV` verified as `9SX2VF4\\K98DEV`, SQL 16.0.1210.3. Private `s2-native-result.json` records 177 requests/530 events: digest n=20, median 5.07 ms/p95 6.50 ms/max 16.33 ms; 3-second account hold settled once at 3,065.37 ms after discarded commit reply, closure 11.75 ms, 12-resource SQL closeout 75.11 ms. Four existing native account-lock tests passed in 15.50 s. | Fresh synthetic DB/restricted login and unchanged relevant procedure bodies; unrelated table FKs omitted by existing fixture. No private response/protocol/closure proof, runtime service, production repair or provider call. Experiment retry is orchestration under test, not shipped functionality. Only generated DB/login cleaned up; retained databases untouched. Other-family concurrency/cost and real Windows custody remain open. |
| E40 | Approved P03a.1 implemented on mirror base `76f95789`. Six real restricted-login SQL/DPAPI cases pass in 69.35 s: ordinary recovery 0.466 s; discarded event/stream/closeout replies each converge once; 3-second contention completes in 3.457 s; 177 complete private request histories in 14.246 s, maximum step 5.713 s. Initial focused regression 336 pass/one skip; final diagnostic-isolation regression 84 pass; 79 earlier log-hygiene passes and nine PowerShell checks. `p03a-qualification.json` retains details. | Overlapping test batches, not a unique total. Native history uses one destination and synthetic stream v4, with journal ACL/process checks substituted; E39 separately covers 12-resource SQL closeout. Real DPAPI is under the development identity. Lost replies are deliberately discarded after actual commits. No production repair, full production-shaped acceptance or common P02 budget approval. |
| E41 | Final Codex Security Changes scan `ff63e856-19f6-4953-9814-c01bb94828fe` completed, Deep off, zero findings, all six changed executable files plus both tests/runbook accounted for. Target base/head `76f95789`, working-tree digest `0b341171b50f6b2928df1d1743517afd8e5e5213de1714fa9196bd17dac51c64`. Earlier scan `cdd79ab4-a347-4ea5-8b2e-1a91cf2c7529` is retained; the final scan reconciles unchanged hashes and reviews the diagnostic correction. | Scoped code security evidence, not production readiness or proof of no possible defects. Application SQL profile, protected installed custody/process/package and full production private proof remain operational gates. Re-review changed bytes; neither scan approves a production action. |
| E42 | Authorized PR/review/merge delivery: mirror #475/#476 and private #717 merged; private `83a4b656` equals reviewed head `29ff6eb1`. Accepted adapter pre-execution issue fixed/responded/resolved. Final mirror Changes `72f84b15-d349-40fb-a8b6-ae7a955526ec` and private `839dd02d-7b3b-440a-8957-cea75d6f17ae`: zero findings. Final Linux CI 10,734 passes / 1,248 skips / 8 subtests; both Windows checkouts 86 affected passes/log hygiene and isolated `-I -B` qualification. Corrected packet and command-ready plan verified; source/hash/merge/CI receipts retained privately. | E41 remains the pre-PR checkpoint. Native SQL/service paths unchanged. Standalone packet only: routine source classification is `COORDINATED_RELEASE_REQUIRED`. Actual installed checks and production operation unexecuted; no F02 closure follows from merge. Automatic mirror sync `a5fa112a` preserves all nine reviewed files. |
| E43 | User-executed P03a.1 recovery accepted at 2026-11-02 19:56:47 UTC on MINI_AMD/ROK_TRACKER. Inspect returned RECOVERY_REVIEW_READY for 11 destinations; Apply and verified journal agree on PARTIAL_EXPORT_CLOSED and one action ID. Diagnostic confirms expected response reference/hash and prepared/dispatch_intent/succeeded sequence, closed stream v534/sequence177, failed job v4, one closeout and 12 unblocked resources. Zero provider requests. Private raw output and p03a1-production-acceptance.json retained. User then approved P03a.2 implementation and tracker closeout. | Operator-supplied evidence, not an independent live query by Codex; SQL diagnostic is bounded/read-committed. Original failure and partial-abandonment meaning retained. P03a.1 complete does not close F02 recurrence, certify original export delivery, deploy merged Bot source or authorize new production operations. |
| E44 | P03a.2 local implementation adds pre-dispatch fixed locators, immutable encrypted saved results, receipt-first terminal/pacing settlement, owned execute/close start and passive status, physical worker drain, original predecessor/child closure, and two exact updater transitions. Seven local SQL/DPAPI cases passed in 52.15 s: normal 0.308 s; terminal reply loss 0.507 s; pacing reply loss 0.869 s; 3-second account contention 3.344 s; pacing contention 3.613 s; lost restart freeze/close replies 1.626/0.662 s. Maximum status poll 0.182 ms, zero provider requests, unchanged job/resource ownership. Additional targeted regressions and mandatory gates recorded privately. | Synthetic local restricted-login fixture and real DPAPI; restart native job/pair observations substituted in these SQL cases. Test databases use existing guarded fixture creation/cleanup. Full regression and final Changes review pending; this is not production deployment, fresh export acceptance, or F02 closure. Code remains under missed-case review. |
| E45 | P03a.2 committed locally as `131711b94e911c6735c4cf2009be869c5924bab9` (38 files), clean mirror branch. Eight related durability gaps corrected across saved evidence, pacing, transient classification, startup reads and complete child drain. Final 366 affected tests passed with log hygiene; seven real local SQL/DPAPI cases passed in 55.73 s with one terminal event, zero provider requests and unchanged job/resource ownership. Final Changes scan `71bc71d9-ea6d-47d9-a2fe-b2e84f68abd9` completed, 17 executable/registry paths covered, zero findings, Deep off. Exact updater projection qualifies 46 combined P03a.1/P03a.2 paths and 811 source pins; retained tooling requires upgrade, candidate tooling is routine-compatible. Local patch, source manifest, review and deployment/validation plan retained privately. | Local implementation/qualification, not deployment or F02 acceptance. Broad regression: 10,916 passes / 1,113 skips / eight subtests, log hygiene passed; final corrections were separately revalidated. Exact final-head CI remains a promotion gate; details in `p03a2-local-review.md`. Startup native pair/job observations were substituted in SQL tests. Fresh installed tool/source/custody, private promotion/review/CI and ordinary new export acceptance remain release gates. No production or provider action performed. |
| E46 | User authorized P03a.2 PR creation, review management, fixes/responses/resolution and merges. Mirror #477 `8f49b8219bbced608a9de315490f1753c2b5f8f0`; private #718 `3d702510229460f740d66708fe64e00959f54838`; reviewed heads `8cb63e4`/`a9049c3`, 40 exact matching files, merge-tree equality. Review fixed retained-request error typing, worker-start attention, missing/corrupt locator diagnostics, rollover birth/resource verification and mixed-case hostname matching; adjacent consumers reviewed. Final Codex reviews clear; all actionable threads resolved. Separate Changes scans `00bab562-8bb5-416f-b3e3-08f6b9d03b03` and `28082b6c-d45a-46d3-ab6f-a29b67dd8fed` complete with zero findings over 18 source/registry paths, Deep off. Final CI: 10812 passed, 1255 skipped, 19 warnings, 8 subtests passed in 843.27s (0:14:03); Windows updater 263 passed, 1 warning in 31.97s plus PowerShell 5.1 orchestration; secrets/publication gates pass. Final focused 204 passes per repository; seven native SQL/DPAPI cases pass in 38.91 s, one terminal event, zero provider requests, unchanged business ownership, maximum passive status 0.518 ms. Verified merged-source packet matches 48 deployment paths, 811 source pins and 34 archive members; bound to current user-supplied updater manifest. Packet SHA-256 `0cc958931febe5327abf8d29dae44b9ccc50d259e9f87dcb619cc9a653736a64`. | Code delivery/packaging complete, production deployment and F02 functional acceptance pending. Synthetic native process/job observations remain substituted; live custody comes from protected updater gates. Copilot review had model policy/plan restrictions, not a full approval. Earlier Windows CI subprocess timeout passed locally and on its one rerun; final-head Windows CI passed. SQL unchanged at `7e91989f`; no migration/grant/config/dependency/flag change. Broader programme items unchanged. Private local evidence/archive is not a remote backup. |
| E47 | MINI_AMD release `ed2e439d-6514-4f05-a2d9-dda494ad68d6` installed private `3d702510` source and seed, then issued one unconfirmed start at 2026-11-03T08:40:53Z. Wrapper launched issuer PID 19140, which exited; no new startup log or incarnation was written. Operator reports expected application-write evidence ACL, empty failed history, no remaining bot processes, and five original source/seed/start receipts. Exact binding SHA-256 `a252e23a901bf54f41886321e3830ee67f4d7bad07fce2082db23ea6b32b6035`. Local regression reproduces administrative evidence-guard rejection before role creation. Correction uses the verified application SID for evidence only; exact updater transition and negative/native-descriptor tests added. Mirror #478 and private #719 opened; code reviews clear at initial heads, separate Changes reviews complete with zero findings. Related predecessor fixture corrected after Windows CI; 263 packet/protocol tests now pass locally. | Production source/seed installation is not startup acceptance. Original session row is the retained pre-deployment observation, not a fresh live SQL read. Current SQL closure/ownership and exclusive startup lock must be verified by recovery. Preserve original receipts/start intent and expected evidence ACL. No second manual start, P03a.1 replay, blind updater rerun or claim clearance. Corrective continuation and final CI/merges remain pending. |
| E48 | Startup fix mirror #478 `e1648d27d09d9d7785a8806a8b95c8ff04c371aa` and private #719 `2549a648cdbeb4734e7c4f572751d7b744d17ba6`; recovery mirror #479 `89968dec90c1de6c9f67cbfb1f1dd1b0c87a0584` and private #720 `b6ec4a0eeabd3d32d8fd98726ab8a6af5e6b829b`. Final reviewed recovery heads `ed9e7f1`/`36fe1f6a`; all six recovery source/test/doc files match, with private-only Windows CI test coverage. Final Codex reviews clear, all actionable threads resolved. Review adds explicit adapter/bindings inventory, duplicate-member refusal, missing/duplicate issuer diagnostics and real adapter-execution regressions. Initial 408 focused tests plus final 52 recovery tests in each repository; operational logs unchanged. Final CI: 10856 passed, 1279 skipped, 19 warnings, 8 subtests passed in 906.31s (0:15:06); Windows 315 passed, 1 warning in 57.02s, plus existing PowerShell 5.1 orchestration. Root-fix full CI: 10827 passed, 1256 skipped, 8 subtests passed. Separate Changes scans including final mirror `627375aa-6a01-4b00-b437-3ae726c50362` and private `0b3a93c6-9262-40fa-9800-4176fb1c07f5` are complete with zero reportable findings, Deep off; prior full scan IDs are retained in the PRs. Exact merged-source package qualifies 22 changed files, 813 source pins and 34 verifier members. Recovery `182f11cc-8a48-48c1-a9a8-aba7412b4779`; ZIP SHA-256 `21d167d270f8f1f5390f81abfa86322d0c9ecfa4d018337f0b93ee1c440487ed`. | Code and recovery packet delivery complete; MINI_AMD execution/readiness and P03a.2 functional acceptance still pending. Native mutex tests use a surrogate account/local namespace; orchestrator fixtures substitute live SQL/task/custody. No elevated production rehearsal or fresh provider-delivery proof is claimed. Copilot selected-tier review was incomplete; its concrete comments were handled. Original E47 failure evidence remains immutable; use separate correction closeout. Early pre-journal diagnostics captured for P01. Local evidence/archive is not a remote backup. |
| E49 | User supplied completed recovery/upgrade transcript, Report 67 and runtime logs. Correction reports STARTUP_CORRECTION_VERIFIED at private b6ec4a0eeabd3d32d8fd98726ab8a6af5e6b829b, original start intent preserved, one successor sequence 84, empty failed history and Discord online. Installed updater manifest matches the expected hash. Report 67 includes 17,724 records: 17,720 resolved, three operational open records and one overview. Exact startup player report logs committed capture/cache completion; ProcConfig logs successful inner import/capture followed by cancelled startup observation and an unconfirmed attempt. Old stats admission is already cancelled before SQL; its sibling projection is existing F28. | Operator-supplied snapshot, not an independent live production query. Startup/updater accepted; no fresh export/provider delivery or F02 closure established. Recheck exact queue and original configuration attempt/receipt before new work. User confirms F28 belongs to later P03/P04; P01 owns F08 cancellation observation. No blanket incident clearing, replay, new runtime fix, SQL mutation or restart. Private analysis and attachment hashes retained in p03a2-post-start-report67.json. |
| E50 | Report 68 and new runtime logs establish a pipeline failure at configuration writer admission (SQLSTATE 42000 / native 51421) after verified stats import and player capture/cache completion. No dependent export job was created in this run. Six operational open records comprise historical F28 plus five linked records for the new pipeline; original startup queue/configuration are resolved. Eight direct-path sources are byte-identical between 83a4b656 and deployed b6ec4a0e. A real local K98DEV experiment reproduces observer-first 51421 refusal, success after observer release and producer-first observer deferral, with isolated resources, no application tables/provider calls and zero retained experiment locks. Private report68 analysis, inputs/hashes, source comparison and native result retained. | Failed ordinary-flow acceptance; no post-provider settlement failure demonstrated. Actual production holder, negative applock return and hold duration are unknown. Native guard experiment stubs account/contract checks and is not full importer/fix qualification. Recommend focused F09/P02 dependency before another acceptance import and exact remaining-stage recovery preserving committed captures. F28 stays in later P03/P04. No production repair, new runtime change or provider replay. |
| E51 | User explicitly chose a properly designed P01 next instead of a one-off F09 fix; requests recorded F09 evidence, stronger scope and a new P01 chat. Canonical scope now requires D01-D06 step/actor/requester/logical-owner/physical-holder/timing/outcome records at every relevant boundary, with A13 known-holder/reconstruction tests and A14 diagnostic non-interference. Scope, tracker, tracing, handover and navigation aligned. Exact Report 68 identities/status and clean mirror/private checkout pins are retained in the private P01 handoff. | Scope/design handoff only; F09 stays P02, F28 stays later P03/P04. Incident recovery may gate next deployment, subject to fresh protected preflight and separately authorized bounded actions. No zero-incident gate, production operation, runtime fix, blanket implementation approval or repeat accepted work. P03a.1 complete; P03a.2 installed/startup accepted, whole-flow acceptance open. |
| E52 | P01 design delivered on 3 November: [design packet](Startup%20Import%20Export%20Reliability%20-%20P01%20Design%20-%202026-11-03.md) covers F08/F11/F17/F23/F24/F25/F30/F32, four outcome dimensions, D01-D06 boundary/owner/test mapping, helper reuse, SQL constraints, six focused slices and an exact private Report 68 recovery/deployment dependency companion. Clean private/mirror/SQL source pins rechecked locally; source manifest validates 38 explicit source paths, 22 SQL definitions and 38 existing named tests plus one proposed test file. P01.1 startup result preservation/diagnostic safety is recommended first; early issuer work is a separate protected-launcher slice. | Design/prose only; implementation approval pending. No finding closed, native qualification rerun, production ownership query or mutation. Diagnostic budgets are proposed and unmeasured. Documentation gates and final path/link checks are retained in `p01-design-validation.json`; runtime pytest/import/registration and Changes scan skipped for this prose-only delta. F09 remains P02 and P03a.2 whole-flow acceptance remains open. |
| E53 | Approved P01.1 implemented on mirror `codex/p01-startup-outcomes`, base `031af6e1`, final runtime `80b05df`. Frozen `f364440` suite: 11,047 passed, 1,113 skipped, 8 subtests. Final sink counter/batching follow-ups: 217 focused passes. Both log-isolation checks pass. Architecture/deferred/security-routing/registration/smoke/lint/format/secrets pass; configured type check zero errors/28 dependency warnings. Three complete Changes reviews (15/15, 5/5, 2/2 source items), zero findings. Final 200-pair sink-cost check: median +0.19%, p95 -1.23%, heartbeat p95 +0.21 ms. Exact updater classification has no blockers and requires an updater upgrade; reviewed package built and PowerShell 5.1 parsed. | Full suite predates narrow final sink follow-ups; final focused tests cover them. Synthetic cost is not production qualification. Optional projection can lag one second plus I/O; close interrupts batching and joins the writer. No push/PR/merge/deployment/restart/provider/SQL/recovery mutation performed. Recovery/deployment assessment is pre-work within P01.1, before bot stop; fresh installed/retained-work evidence remains required. F09 remains P02, continuation P03. |
| E54 | User-authorized P01.1 PR delivery complete: mirror #480 and #481, private #721 merged; private target `0247371d90ec88d4c0639e9200164f4256086037`. Final source `e03f5208`: 11,057 passed, 1,112 skipped, 8 subtests; operational logs unchanged. Final private quality, Windows updater and secret checks pass. Review comments answered/resolved; late required-event-fields and callback-interruption fixes included. Original private and both follow-up Changes scans cover 15/15, 3/3 and 3/3 source items with zero findings. Exact updater packet and [operator plan](../../.codex_artifacts/startup-import-export-review-20261102/K98-P011-Deployment-20261103/README.md) supplied. | Merge/local qualification is not deployment or production acceptance. Fresh installed identity and protected retained-work/process/session/stream preflight remain required before stop. No production execution. F09 P02, continuation P03; P01.2-P01.6 and whole-flow/P05 acceptance remain open. Earlier evidence retained. |
| E55 | User completed P01.1 deployment of private `0247371d90ec88d4c0639e9200164f4256086037`; supplied updater output, Report 69, startup log, ordinary report and persisted observations validate exercised live startup/diagnostic behavior. Eight startup references correlate; configuration completed after its deadline with its original recorded result. The later file retains 23 settled operations; worker alive and all four reported sink counters zero. Private `p011-report69-review.json` and `p011-live-diagnostics-validation-20261103.json` retain hashes/checks. | Scope is recorded deployment and observed behavior. Bounded report omissions/transition trimming are accounted for. Cancellation/failure/restart restoration rely on retained controlled qualification, not newly induced production cases. No fresh whole-pipeline/provider certification; later natural cross-restart file observation remains separate. |
| E56 | User requested P01.1 learning be incorporated into remaining P01/P02-P05 scope and improved evidence collection delivered early. P01.2a now owns combined collection, precise child/parent outcomes, key milestones and availability/freshness metadata; P01.2b retains early issuer evidence plus offline collection. Scope/design/handover/navigation updated; each later package extends and qualifies the common contract. | Documentation/scope amendment only. No runtime implementation, PR, deployment, restart, SQL/provider action or recovery mutation. P01.1 acceptance is preserved; no unowned optimisation backlog or delay of basic collection until P04. Exact P01.2a implementation bounds/manifest still need final design. |
| E57 | User accepted E56's amended scope, requested completion of P01.1 documentation/task statuses and creation/start of a focused P01.2a chat. Dedicated closeout and scope/handoff added; F08/F32 and current slice/acceptance rows updated. | Focused design may start immediately. No blanket runtime implementation, PR/merge, deployment, SQL/provider action or replay authorization. New-chat identity and creation/start confirmation are retained in the private handoff receipt. |
| E58 | P01.2a focused source review and [implementation-ready packet](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Design%20and%20Qualification%20-%202026-11-03.md): exact proposed files/shared callers, typed outcomes, fixed milestones, V1/V2 compatibility, publication provenance, incident-first components/continuations, resource bounds and Q01-Q12. Clean local private `0247371d`, mirror `607f6a81` and SQL `7e91989f` rechecked; authoritative RecoveryIncident/Action definitions reviewed. Private `p012a-design-20261103` retains source/caller manifest and documentation qualification. | Design only; budgets are acceptance targets, not measured results. No runtime tests, native SQL, live observation, provider/recovery action, restart, commit or PR. Implementation approval is the next decision. P01.1 accepted evidence and all later package obligations remain intact. |
| E59 | User approved the P01.2a design and local qualification: "Approved please proceed". Mirror main refreshed to `ecaaf2dcfa10b48cea1a088aa7465ab20bd0eb4b`; source tree matches reviewed `607f6a81`. Implementation is on `codex/p012a-evidence-bundle` in the existing mirror checkout. | Implementation/local qualification only. No PR, merge, production deployment, restart, provider request or recovery mutation. SQL qualification uses the existing localhost K98DEV session-local fixture; no installed schema change. Release gates remain open until recorded. |
| E60 | P01.2a local candidate implements typed child/parent outcomes, retained milestones, independent V1/V2 publication, passive evidence ZIP/continuations and nonwaiting report ownership. [Qualification receipt](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Implementation%20and%20Qualification%20-%202026-11-03.md) retains exact hashes, three completed Changes reviews, controlled bounds/fault/cancellation tests and native local SQL evidence. Final scan `6b457f0f-35ca-41cd-80b1-7b980efd2538` covers all 14 runtime and six test files with zero findings. | Local implementation; release readiness held. 760 focused/205 shared-caller tests pass with log hygiene; final report/privacy 140 and native report 7 pass. Broad Windows: 11,066 passed, 1,114 skipped, 8 passing subtests, 31 updater-inventory failures. Report 200-pair p95/p99=4.38244/4.51823 s and extra RSS 4,698,112 bytes pass. Producer 200-pair median +2.42549% and p99 +95.33771% fail Q12; retain original limits and correct cost before release. Native 18,000-row/1,800-action 10-row-page query cost 11.44923 s; installed factories remain unqualified. No PR, merge, deployment, restart or provider/recovery action. |
| E61 | Operator: **“Agreed please continue until we are ready for PRs.”** | Authorizes local P01.2a cost correction, authenticated updater source-transition preparation, tests and final reviews through PR readiness. Preserve original cost limits, failed evidence and unrelated work. Opening PRs, commit/push/merge, promotion/deployment/restart and provider/recovery actions are not included. |
| E62 | [Final P01.2a PR-readiness receipt](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20PR%20Readiness%20-%202026-11-03.md): exact 31-file patch, source hashes, five completed Changes reviews retained; latest `b247da18-0f56-4939-a41b-c10362f9a1de` covers final source with zero findings. | 11,163 passed, 1,114 skipped, eight passing subtests; operational logs unchanged. 1,859 focused pass. Corrected disk-backed 1,000-pair producer overhead: median +0.47368%, p95 -4.48409%, p99 -9.55373%; no drops/failures, all 2,000 calls preserved. Full-bound extra RSS 105,594,880 bytes. Source transition has 14 exact members matching private P01.1 predecessor. Ready for PR review; no PR, commit/push/merge, deployment/restart or provider/recovery action. |
| E63 | Operator requests required PRs, review management, corrective work, merges and a clear deployment/validation plan. Mirror #482 opened from qualified candidate; two code-review findings reproduced and fixed in `19d713d`. Private patch-promotion validation and final review are in progress. | Authorizes Git/PR/review/merge actions and local release preparation. No deployment, restart, provider request or recovery mutation. Final acceptance remains pending. |
| E64 | Required implementation PRs [mirror #482](https://github.com/cwatts6/K98-bot-mirror/pull/482) and [private #722](https://github.com/cwatts6/k98-bot/pull/722) merged after six corrections, final-head reviews, complete Changes security review and final CI. Private target `07bc9d6ebd5964f9bf660822f03a932a2472d966`; [review/merge receipt](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Review%20and%20Merge%20-%202026-11-03.md) links the sealed updater package and operator plan. | Source implementation complete for P01.2a; actual installed predecessor/custody, protected deployment and passive production acceptance remain operator gates. No SQL migration, deployment, restart, provider request or recovery mutation. P01.2b/P02-P05 remain open. |
| E65 | Operator confirms deployment, bot online and command versions correct. Supplied updater transcript verifies target `07bc9d6e` and release `a1b257ad-4249-4f89-836d-58033a4bd590`. Report 70 and ordinary part 1, startup logs and a controlled expired-lease probe are retained in the [acceptance receipt](../../.codex_artifacts/startup-import-export-review-20261102/p012a-production-acceptance-20261103/acceptance-review.json). | Deployment is verified; feature acceptance is not. Incident scan consumes the shared deadline and suppresses all diagnostic sources; existing deadline regression asserted incomplete/count/ownership only. Ordinary monitor unavailable and current V2 evidence omitted from the supplied preview remain gaps. Gateway delay41.6s overlaps but causation is unproven. No fresh full import/export acceptance or independent installed-manifest verification. No new production action. |
| E66 | Diagnostic preservation/long-worker correction merged as mirror #483/private #723, private `b31f022c`. Report 71 confirms improved collection; known startup actor attribution remained a gap. | Intermediate acceptance only; no historical holder or whole-flow closure. |
| E67 | Evidence-contract correction merged as mirror #484/private #724, private `1f54cbb3`: startup attribution, malformed/lost events, stages, counter provenance and real reader compatibility addressed together. Report 72 exposed recoverable collection gaps. | Retain original failed evidence; P01.2a acceptance still open at this intermediate release. |
| E68 | Recoverable reporting merged as mirror #485/private #725, private `67c4e12a8ecf0c25280770860480ac65a6826602`; updater hash `b7dd6757ea4405ff7e89b5f5290d4d046bf410688b4e06536d994ed9c55b81a7`. User deployed; Report 73 validates 850 retained incidents plus 100 non-overlapping continuation rows, five component hashes, eight startup rows/known actors and later ProcConfig settlement. User accepts declared P01.2a closeout. | Partial census, controlled-only fault/retry evidence, monitor follow-through and all remaining packet/incident owners are explicit in the closeout. No production replay or whole-programme acceptance. |
| E69 | User requested recording closeout, updating programme documentation and creating/starting P01.2b. Dedicated closeout/handover, current status and navigation reconciled; learnings, remaining gaps, incident owners and B01-B09 carried forward. | Documentation and next review/design only; no new runtime change, production operation or blanket incident clearance. Private documentation manifest and chat receipt retain exact carry-forward state. |
| E70 | [P01.2b design and qualification](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Design%20and%20Qualification%20-%202026-11-04.md) records locally retained current mirror/private sources, all 61 transitions, rehashed Report 73 inputs, SQL-definition checks, exact proposed file/shared-caller manifest and B01-B09 mapped to D01-D06/A13-A14. Preserves the concurrent archive moves and complete portable documentation manifest. | Review/design only. Long-lived scheduled task conflicts with updater admission; detached pipe observation has a mandatory observer-loss feasibility gate. No historical six incident IDs appear in the supplied 950 rows, so their current status is unproven. Fresh installed bindings and exact saved recovery/ownership inputs are specified. No runtime implementation, native qualification, SQL/provider operation, restart, PR or deployment; local implementation approval remains open. |
| E71 | Operator supplied current gate, task XML, active policy and updater manifest; policy/gate pin agrees, 817 source hashes exactly match retained private source, updater manifest matches accepted P01.2a. Targeted SQL export verifies all 17 chunks/hash, six open historical incident rows, seven original stages, four preparations and three unique resource keys. Packet records actual task termination settings for native qualification. | Supplied configuration and saved-state evidence only. Captures retained; configuration unconfirmed and target-cache/export not started. Included resources are unowned at observation, not a global or physical-worker proof. Repair-action Records omitted, so absence is unverified. No further design collection requested; native feasibility and live custody remain later gates. User ran the SELECT extract; no assistant SQL/repair/restart/deployment or runtime implementation. |
| E72 | User approved local implementation and isolated qualification starting with observer feasibility, requiring a stop if the design changes. Actual Desktop PowerShell 5.1 and Python 3.11 inert experiment: NUL and healthy-observer controls each completed 1 MiB stderr and exited 37; confirmed observer loss before writing caused OSError/errno 22, zero completed bytes and exit 120. Exact process creation/exit times and source hashes retained privately. | B03/A14 outcome preservation failed; implementation stopped as requested. One inert child per case, all fixture processes settled; only the intended observer fault was terminated. No application source, runtime branch, installed files, SQL/provider, scheduled task, deployment or production state changed. Revised transport/coverage requires review; full qualification not claimed. |
| E73 | User requested replacement-transport review before further implementation. Current issuer bootstrap/source boundaries and official Win32 mapping, ordering, process and pipe/ETW contracts reviewed. Packet recommends separate fixed-size producer mappings, observer read-only handles, retained native process identity, unchanged stderr, structured events after trusted bootstrap and independent bounded publication. | Design recommendation only. Explicitly proposes replacing arbitrary stderr capture; earliest Python/interpreter failures may provide launch/exit but no cause/traceback, and unpublished memory is not durable. Native ABI/initialization and observer-loss tests remain unperformed gates. E72 stop is active; no new runtime, experiment, production action or silent weakening of acceptance. |
| E74 | User approved a smaller external-observer value/cost screen with unchanged issuer and streams. Fourteen functional scenarios, a 125-second idle observation and 120 matched pairs completed in private inert fixtures. All jobs settled; native exit and missing-interpreter evidence demonstrated. | Cold attachment added 3443.3 ms, failing the pre-set 500 ms maximum. Stop before integration. Reduced handle rights are not a process sandbox; installed lifetime/custody, concurrent startup and full bot/report qualification remain open. E73 mailbox/helper is held back. No production changes or delivered P01.2b feature. |
| E75 | Operator agrees the theoretical startup-observer requirement does not justify cost and risk; simplicity and bot/startup safety take priority. Proactive instrumentation is declined, with existing evidence and simple issue-driven best-effort collection sufficient. | Close the proposal without deployment or claiming feature delivery. No replacement observer/helper, tuning backlog or mandatory exporter. Missing early detail is accepted coverage; operational safety, existing receipts and other incident/package obligations remain. Documentation only; no runtime, production, recovery or publication action. |
| E76 | User requested P01.2b closeout, documentation update/archive and progression to P01.3. Preserved E72-E75, archived three design records, added an archived closeout, renamed the active carry-forward checklist and repaired links. P01.3 handover identifies F11 and source-confirmed display-triggered probes. | P01.2b closed by operator decision, not feature delivery. P01.3 review/scope only; no runtime, production, SQL/provider action, experiment rerun, PR or deployment. Full documentation/archive carry-forward remains required. |
| E77 | User approved the P01.3 scope for design and removal of automatic log scans/last-20-errors, retaining explicit log inspection. The decision followed the stated count-derived spike-alert trade-off. | Design authority only. No runtime implementation, new monitoring mechanism, live probe, SQL/provider request or production action. |
| E78 | Concrete P01.3 design delivered against clean retained mirror `6f58f878`: common passive projection/card, non-consuming probe observations, nonblocking optional getters, journal-read removal, truthful provenance, alert/lifecycle rules and optional existing-report component. H01-H09 define behavior, compatibility and cost qualification. | Source/design evidence, not runtime qualification or production health. Existing command telemetry is explicitly outside pure health assembly and must be measured without amplification. Documentation gate results recorded in the design packet; implementation remains unapproved. |
| E79 | Operator agrees 60-minute provider freshness, separate 90-second recovery-monitor rule, zero reader locks, existing five-minute rereads, actionable alerts/common views, report/telemetry gates and accepted user-reported rare whole-bot outages. Screenshot reports Health card interaction timeout; retained source shows 30-second view expiry and pre-acknowledgement probe/log work. Design now proposes persistent Refresh, early acknowledgement and bounded startup registration/migration with the existing message identity. | Supersedes E78 try-lock/15-minute/preserved-timeout proposals. Screenshot is symptom evidence, not proof of the exact failed path. No new outage detector or recheck scheduler. Documentation-only refinement; runtime implementation and operational actions remain unapproved. |

Operational IDs, raw exception material and private logs stay in protected evidence. Public
documentation uses safe summaries and source references; unknown causes remain unknown.

## Stage 1 inventory

The tracing report expands these routes and records main-pass dispositions. The route
notes below retain the investigation's progression; B01-B15 and M03 record the completed
main-pass mapping. Final-sweep questions and G02-G05 remain. Only explicitly linked
package evidence establishes qualification for its declared subset; the full caller
inventory is not production-qualified merely because P01.1 is accepted.
Required fields: enabled entrypoint,
operation identity, passive/active/producer role, source/SQL objects, transaction/locks,
timeouts, effect on other work, evidence lifetime, useful decision, disposition, test and
exclusion reason if applicable.

| ID | Route / source starting points | State and next question |
|---|---|---|
| C01 | Startup scheduling: `bot_instance.py`, `core/startup_lifecycle.py`, `core/startup_diagnostics.py` | F08 corrected/qualified in P01.1; E55 verifies late configuration result preservation and eight startup references. E75 accepts pre-journal evidence gaps and declines proactive P01.2b instrumentation; collection/clarity improvements are P01.2a. |
| C02 | Player report/cache: `player_stats_cache.py`, `file_utils.py`, `core/export_sql_connection.py` | Partially reviewed: logged 300-second setting changes lock wait, not inherited 15-second query timeout. Verify all callers and actual connection policy. |
| C03 | Configuration: `proc_config_import.py`, `services/configuration_producer.py`, snapshot service/DAL | Provider inputs gathered before writes; ownership spans atomic publication, including child maintenance/logging (F21). Typed offload decoding and no-retry-on-unknown behaviour preserved. Real-child failure/cost qualification remains. |
| C04 | Import/report/pipeline: `processing_pipeline.py`, stats import outcome services/DAL, pipeline receipt/recovery services | Partially reviewed: committed producer and unconfirmed observation are separate. Trace automatic convergence and every remaining-stage caller. |
| C05 | Claim/guard/capture/queue: legacy snapshot service/DAL, export coordination service/DAL | Partially reviewed: classify setup, transaction and settlement locks, cleanup certainty and distinct connection budgets. |
| C06 | Authority request/result/pacing/closure: export execution authority/DAL/lock, request budget, authoritative request-event SQL | Partially reviewed: one-second result-admission boundary remains; trace exact saved result/event identity and settlement without provider replay. |
| C07 | Discovery/rechecks: recovery runtime/service/DAL, authority observation, SQL observation, unowned-hold discovery | Core loop and nested replacement/rollover/inherited actions traced; 73 allowed pairs classified. Separate outcome-worker automation preserved. Per-state eligibility remains. F04/F09/F10/F12/F13. |
| C08 | Status/health/UI/report: `bot_instance.py`, admin commands, recovery views/report/health, health probes | Traced: status starts active probes, detail review can reconcile accepted work; retained centre/report reads provide an existing passive pattern. F04/F11. |
| C09 | Failure history/closeout: export diagnostics/provenance, recovery DAL/report, player-report and legacy-closeout adapters; upload audit/notification routes | Field projection gaps recorded; existing audit adoption compares committed import, refresh and notification separately. F17 shows inconsistent terminal classification despite retained rows/identity. |
| C10 | Remaining admin/scheduled/compatibility callers and shutdown/restart | Added explicit admin export/offload and manual recovery/cache-diagnostic dispositions. Preserve queued acknowledgement, physical-work ownership and SQL-success/post-stage separation. Remaining conditional dispatch and candidate-row reconciliation stay G01. |
| C11 | SQL reporting/maintenance and file custody: UPDATE_ALL2, S11 import/report wrappers, target/delta publication, player/KVK output, claim/archive/hash procedures | F18/F21/F22 plus Python F16 map maintenance across six stages. Claim/import/archive lifetimes and integrity purpose recorded. Added 12-root graph and classified lexical artifacts/system names. Remaining dynamic edges and row dispositions remain G01; real cost/fault testing remains qualification. |
| C12 | Processing notification registration/store/observer and passive report export | Automatic closure/pruning, exact send evidence, import-admission coupling and retained-field/report boundaries traced. F19 and G04 disposition table. |
| C13 | Shared file-lock helper, startup player verification, guided/ordinary cache publication, Ark state/team persistence, tracked-view wrapper | All discovered direct helper callers classified; mismatch/next-writer reproduction and known prior scoped fix recorded. F20. Indirect/dynamic aliases remain a final-sweep target. |
| C14 | Calendar startup/daily/admin sync -> generation -> cache publication; event_calendar service/sheets_sync/scheduler | F23/F24 reproduced. Preserve no-timeout-retry and distinguish actual audit, worker and business outcomes. Domain calendar/reminder redesign remains separate P1 work. |
| C15 | Event/profile/name/registry cache readers, startup verifiers, admission diagnostics, calendar runtime/index output and profile SQL adapter | F25/F26 reproduced. Keep single refresh ownership, short immutable-snapshot reader locks and separate memory/disk outcomes. Assess index necessity first; qualify readback/copy cost and fallback policy. |
| C16 | Recovery snapshot DALs, report-stage validator, incident writes, replacement/evidence retained reads, contention wrapper and pacing | Matrix separates display/discovery from exact mutation validation. F27 reproduces a distinct waiting-classification gap; unchanged polling writes are a cost question, not a new incident/revision each time. Preserve session-guard busy handling and atomic action checks. |

## Findings and check dispositions

| ID | Current evidence/classification | Required disposition / next action | Acceptance |
|---|---|---|---|
| F01 | Confirmed static startup report query-timeout mismatch; latest failure appears before body entry, so not its proved cause. | Investigate all shared-factory consumers and propose explicit justified execution policy. | A01/A04 |
| F02 | One-second authority admission precedes result persistence. E33 confirms missing request-177 terminal evidence keeps its mutation stream frozen and account blocked; the cached closure also becomes stale if the journal is settled. | Design exact evidence settlement and renewed closure proof; preserve known/unknown outcomes and never resend a provider mutation to fix bookkeeping. | A03/A06 |
| F03 | Confirmed business transaction owns account/resource locks; long ownership already recognised historically. | Keep required fencing; investigate narrower coordination and observer isolation with SQL evidence. No blanket removal. | A02/A04 |
| F04 | Waiting classification/rechecks already exist; automatic recovery allowlist shares monitoring orchestration. | Classify and separate passive versus active effects; evaluate every manual recheck/clear/verify action. No proved bug merely from sharing an orchestrator. | A02/A07/A08 |
| F05 | Mutable incident evidence and adapters/report omission do not uniformly preserve historical failure context. | Design proportional history retention, safe redaction and complete export without one record per poll. | A09 |
| F06 | Producer completion can precede pipeline observation; pipeline adapter supplies stage detail omitted from report allowlist. | Review automatic reconciliation and reporting; no rerun to repair observation. | A05/A08 |
| F07 | Exact latest blocker and duration absent from retained evidence. | Specify minimal non-interfering evidence needed; do not invent attribution or install intrusive monitoring without review. | A02/A10 |
| F08 | Corrected, qualified and deployed in P01.1 (E53-E55): a startup observation deadline no longer discards the original successful configuration return/completion check. Production naturally exercised completion after deadline with the same recorded attempt. | Closed for P01.1's declared startup-result boundary. Preserve ownership/drain and exact receipt semantics; early issuer and later evidence usability have separate P01.2 owners. | A04/A05; P01.1 evidence complete, programme acceptance separate |
| F09 | Observer-first/global snapshot guard conflict documented; E50 records production 51421 at that producer-entry boundary, and namespaced native SQL reproduces the mechanism. Actual production holder/negative return remain unknown. | P02 owns a shared observer/admission design and D01-D06 holder/resource/timing evidence with both-order SQL qualification. E51 retains P01 first; no isolated blanket retry or claim of a known historical blocker. | A02/A03/A07/A13/A14 |
| F10 | Pipeline inspection repeats account-locked snapshots; exact completed-stage binding remains a manual action outside the automatic allowlist. | Simplify passive snapshots and define idempotent automatic binding; retain mutation-time identity/version checks. | A05/A08 |
| F11 | `/status` and health embed launch active SQL/Sheets probes; Sheets probe owns durable preparation/resources and an authority stream. | Use retained health for presentation; justify explicit probe cadence and cost, retain real write-boundary controls. | A02/A07/A10 |
| F12 | Authority inspection shares serial pipe dispatch and performs SQL/private-evidence I/O. | Include request scheduling and I/O in non-interference design and measurements; no proved starvation or latest incident attribution. | A02/A10 |
| F13 | Recovery discovery uses 120-second job/rollover age; overview labels all open/pending counts attention-required. Request progress need not refresh job age. | Separate candidate age, ongoing progress and useful operator action; measure false incidents instead of only changing thresholds. | A08/A10 |
| F14 | Ordinary KVK routing reads acquire exclusive season application lock and update locks also used by source writers/configuration snapshots. | Design consistent passive selection reads; retain mutation-time validation. Metadata lock ends before payload read. | A01/A02/A07 |
| F15 | Completed fresh player report can lead to another confirmation to refresh its local cache. | Assess automatic continuation of original intent with exact generation binding and atomic cache replacement. | A05/A08 |
| F16 | Post-SQL log-backup processing and waits occur before global writer guard/capture sequence finishes. | Separate useful maintenance from critical guard lifetime; preserve headroom and existing exact-completion recovery. No claim that Python waits keep the procedure transaction open. | A02/A04/A05 |
| F17 | Honor notification exception can label a committed import failed; refresh exceptions mark Honor/Pre-KVK/Location audit batches failed despite recorded ingestion. Existing tests encode this, while Weekly Activity isolates notification failure. | Standardise separate mutation/audit/refresh/delivery outcomes and require the same acceptance matrix for equivalent callers. Preserve once-only offload and original row/receipt evidence. | A01/A05/A09 |
| F18 | Final SQL reporting transaction includes CHECKPOINT and log-backup signal insertion before receipt/commit; their failure can roll back this reporting stage. | Separate operational maintenance where justified; keep exact completion atomically tied to data. Qualify the real maintenance boundary omitted from simulated calculation tests. | A02/A04/A05 |
| F19 | Full/unavailable notification journal prevents new import registration, despite separate business receipts. Auto-closure and closed-history pruning already exist. | Justify and narrow this admission dependency; preserve uncertain send evidence and define bounded archival/degraded notification policy. | A01/A05/A08/A09 |
| F20 | Reproduced: cache readback exception leaves shared helper's sentinel; next writer times out. #688 contains a scoped workaround, but direct cache/Ark callers remain. | Correct the shared exception-cleanup/ownership contract across direct callers; keep tracked-view protection, shorten observer lock duration and distinguish superseded observation from failed production. | A01/A02/A04/A07 |
| F21 | Configuration publication calls conditional statistics/index maintenance and performance logging before the caller commits/releases its delta mutex. Existing atomic-entry SQL test stubs the child. Both procedures unchanged from retained deployed SQL pin. | Assess together with F16/F18; separate ancillary maintenance/logging from required calculation and exact completion. Qualify real child failure/overlap; do not remove atomic publication or infer a live blocker. | A01/A02/A04/A05/A09 |
| F22 | Player-report/KVK-output FULLSCAN and import Phase A statistics/index maintenance run before their respective commits. Source/history shows retained dependencies beyond configuration and final reporting. | Use one maintenance acceptance matrix across all six stages. Distinguish required data/index contracts and headroom protection from optimizer/diagnostic maintenance; qualify failure, lock duration and truthful stage outcomes. | A01/A02/A04/A05 |
| F23 | Calendar audit start blocks sync; audit-completion failure after business commit returns failed-fetch/validate with zero counts and prevents continuation. Reproduced. | Separate committed data, audit availability and remaining generation/publication; justify whether audit admission is essential. Preserve meaningful original evidence and avoid repeating sync to repair logging. | A01/A05/A08/A09 |
| F24 | Calendar stage timeout cancels to-thread awaiter; caller operation lock becomes available before physical worker completion. Reproduced. No immediate timeout retry already exists. | Extend owned-work/drain and truthful timeout policy to sync/generation/publication and next-caller admission. Keep no blind retry; test actual thread overlap, not only a raised TimeoutError. | A01/A02/A04/A05 |
| F25 | Main calendar cache replacement succeeds, auxiliary index write fails, and result says failed/zero. Reproduced; runtime reads primary cache. No production Python index reader found. | Establish index value/consumers before adding coordination. Optional output must not redefine primary success; required paired output needs a coherent publication/outcome contract. | A01/A05/A08/A09 |
| F26 | Profile adapter catches connection execution failure as helper unavailability and invokes a direct fallback factory. Reproduced; predates recent extraction. | Make connection/budget selection explicit and preserve first failure. Distinguish unavailable import from failed connection; verify context-dependent runtime versus legacy policy. No mutation replay or permission-bypass attribution. | A01/A04/A09 |
| F27 | Report-validator refusal/row-timeout becomes SourceConflict and takes the failed-check route. Same SQL 51961 also denotes genuine invalid prerequisites; retained diagnostics still contain underlying codes. Present since #675 / SQL #129. | Distinguish verified contention from real mismatch after clean release; do not blanket-retry 51961 or suppress real conflicts. Cover the actual report-inspection path and preserve receipts/no import replay. | A02/A03/A05/A08 |
| F28 | Report/screenshot and source confirm verified pre-SQL cancellation resolves refusal but leaves sibling import open; generic nonempty-generation context falsely says SQL retained. | Reuse exact cancellation proof across projections and report cancelled-before-SQL consistently. No blanket closure from absent receipts and no release of the old export. | A05/A08/A09 |
| F29 | Both Rally importers persist an error IngestionLog row then skip the same filename as duplicate; authoritative SQL uniqueness also occupies that key. Reproduced offline, longstanding source. | Separate failure-attempt history from successful ingestion identity, with content/uncertain-commit semantics and SQL migration review. Do not just change the SELECT or blindly replay. | A01/A05/A08/A09 |
| F30 | Queue CSV logging runs before business processing under the staging lock; log I/O error propagates and prevents the callback. Reproduced offline. | Justify optional logging versus required custody. Preserve serialization/input/acknowledgement while preventing optional audit failure from blocking or mislabelling import. | A01/A02/A05/A09 |
| F31 | Legacy UPDATE_ALL invokes UPDATE_RALLY_DATA inside its transaction; Rally deletes its input CSV before the outer commit and catches errors with PRINT. Current scheduled use is unverified. | Include legacy/manual enablement in the scope. Retire the path if unused or align error, custody and post-commit archive semantics; do not assume the newer stats claim protocol covers Rally. | A01/A05/A09/A12 |
| F32 | Corrected/qualified in P01.1 across selected shared callers: optional clock/diagnostic/sink failures preserve worker entry, original result/exception and physical drain. Deployed sink health is observed in E55; live diagnostic faults were not injected. | Closed for the qualified P01.1 shared primitive/callers. Later slices must qualify their own adoption; child/parent labels, milestone retention and combined collection are required P01.2a scope. | A02/A05/A09/A12; controlled qualification and live healthy-sink evidence |

No keep/remove decision is final until its concrete protection, effect on producers and
replacement (if any) are justified. A retained check must pass non-interference acceptance;
the fact that it existed before this phase is not justification.

## Current scope decision - 4 November 2026

P05 owns the mandatory repository-wide reliability/correctness confirmation after
the relevant P01-P04 deliveries. Its refreshed Bot/SQL entrypoint-to-sink review,
caller/action census reconciliation, separately recorded final sweep and A01-A14 /
D01-D06 implementation-test-production evidence matrix are specified in the
[scope](Startup%20Import%20Export%20Reliability%20-%20Scope%20-%202026-11-02.md#p05-repository-wide-reliability-confirmation---4-november-2026).
The earlier A12 sweep remains valid only for its pinned historical sources; it
does not close this new P05 confirmation. Status: **required, not started**.
Owner: P05 delivery/review; inputs include P02/F31 installed-path qualification.
This is not authorization for a repository-wide security scan or production replay.

**Historical pre-E67 correction checkpoint:** P01.2a was not fully accepted. The operator approved addressing the evidence
contract as one correction group before another PR: known startup attribution,
malformed checker output, silent event-construction loss, unknown-stage counts,
historical/current counter and eviction provenance, and actual deployed-reader
rollback compatibility. The local
[cross-work receipt](../../.codex_artifacts/startup-import-export-review-20261102/p012a-cross-work-review-20261104.json)
records five confirmed gaps, one prospective compatibility risk and 627 passing
baseline regressions. Those passes alone did not close the gaps. E67 implements the correction and E68 records final acceptance after the additional recoverable-progress correction. P05 was not their owner.
No new production action is required to implement or locally qualify this group.

## Qualification plan and progress

| Acceptance IDs | Planned evidence | State |
|---|---|---|
| A01 | Relevant caller/check census with every disposition/exclusion and source/test mapping | Main pass and independent final source sweep recorded; live installed bindings/native qualification remain explicit |
| A02/A07 | Equivalent observer-off/on workloads; SQL session lock/transaction evidence, bounded resource cost, passive presentation side-effect assertions | Not run |
| A03/A04 | Deterministic brief/long contention, slow connection setup, pre-entry failure and cleanup; zero manual actions for ordinary waiting | Startup helper experiment reproduced F08; native contention qualification not run |
| A05/A06 | Committed producer, delayed readback, post-provider persistence, pacing and closure failures, restart and lost reply without duplicate work | Not run |
| A08/A09 | Automatic convergence versus genuine escalation; failure -> recovery -> restart -> report retains meaningful history; deduplication | Not run |
| A10 | Before/after manual-action, false-incident, completion, convergence and observer-cost results with denominators/workload | Not run |
| A11 | Original P0 matrix reconciled row by row and linked to evidence | Not started |
| A12 | Separate final sweep after main analysis; compare new candidates against reviewed coverage and investigate exceptions | Completed for pinned sources in M04a/E34/E35; 322 additional dispositions, F31 and F02 closure extension recorded |
| A13 | D01-D06 boundary-to-owner/test mapping; correct known actor/requester/holder, return/resource/phase and correlation through handoff/restart/report; explicit genuine attribution gaps | P01.1 startup/result correlation qualified and observed (E53-E55). E56/E57 assign clearer outcomes/milestones/collection to P01.2a; SQL-holder attribution and wider enabled-boundary coverage remain with P02 and adopting packages.  E67/E68 qualify and observe known startup actors, parent/child outcomes and report reconstruction; E75 accepts theoretical early-issuer gaps; actual SQL-holder attribution remains P02 and future evidence additions must be issue-driven. |
| A14 | Bounded redacted diagnostics, sink-failure/saturation/cancellation tests and measured non-interference; required correctness receipts stay enforced | P01.1 controlled fault/cancellation/restart/cost qualification complete and deployed healthy sink observed. P01.2a adds collection/compatibility/concurrency budgets; each later package qualifies adoption and P05 verifies combined evidence.  E67/E68 deliver bounded recoverable collection, real 125-second combined failure and unchanged cost gates; later adoption remains required. |

Potential existing suites: `test_recovery_monitor_observation`, `test_recovery_work_budget`,
`test_export_execution_lock`, `test_export_execution_lock_sql`, `test_export_contention`,
`test_coordination_lifecycle`, player stats cache/startup, pipeline receipts/recovery and
recovery report/failure diagnostics. Confirm exact names and gaps when designing packages;
existing green tests are not proof of all required combined scenarios.

### How outstanding obligations close

Close obligations through their owning packages, with evidence linked here. Package
progress, a merge, elapsed time or fewer open incidents does not itself close them.
The delivery agent maintains this record and prepares the evidence; routine evidence
collection is not another operator acknowledgement or production incident workflow.

| Obligation | Owner and completion point | Evidence needed to close |
|---|---|---|
| Value of retained checks, outcome states and budgets | S2, before the affected implementation | Recorded keep/simplify/consolidate/automate/remove decision, useful failure response and tests for the affected callers. Resolve package-specific details as that package is designed. |
| Old-export result, closure and ownership | P03a, before repair and at operational verification | Full exact saved-evidence/current-state validation; restart/lost-reply tests; after an approved repair, durable closeout receipt and matching released ownership/projection, with no provider replay. Finding the saved files alone does not close this obligation. |
| Real contention, maintenance cost and observer interference | Affected P01/P02/P03 slices, before their acceptance | Isolated native SQL/host qualification, both observer-first and producer-first overlap, actual relevant maintenance children, failure/cleanup cases and comparable workload results. Inert fixtures alone are insufficient. |
| Installed scheduled, manual and legacy paths | P02/F31 and any dependent slice, before claiming coverage or retirement | Bounded installed-binding/enablement inventory. Include active paths in qualification; record verified unused paths and any approved retirement. Source absence alone does not establish runtime absence. |
| Automatic convergence, meaningful incidents and retention | P04, with P03 dependencies | Ordinary waiting and known completed/cancelled states converge without operator clearing; genuinely uncertain effects remain protected; history survives recovery/restart and capacity handling is bounded. |
| Combined acceptance and earlier programme credit | P05, after relevant deployment and natural evidence | Reconcile A01-A14 and the original P0 rows against linked results. Retain P0 F04/unexercised natural cases separately; do not replay accepted work. Return to P1 Ark with any remaining obligations explicitly carried forward. |

Only a dependent package is gated by an unresolved prerequisite. Track design, tested
implementation, deployment and operational verification separately; none substitutes
for the next. Historical F07 blocker attribution may remain explicitly unknown when
evidence is unavailable, without blocking independently demonstrated correction and
safe recovery. Do not manufacture certainty or add intrusive monitoring to close it.
Any deferral must retain its reason, impact and next owner; it is not a completed fix.

## P0/P1 reconciliation and return path

| Obligation | This phase contributes | Current disposition |
|---|---|---|
| P0 F01 | Publication result persistence/settlement and truthful outcome | Open reconciliation; prior accepted exports remain accepted. |
| P0 F02 | Evidence/ownership recovery, stale reservations and eliminating indefinite recheck-only workflows | Open reconciliation; unknown historical outcomes remain qualified. |
| P0 F03 | Startup/report/configuration and pipeline continuation | Open reconciliation; completed stages must not be replayed. |
| P0 F04 | Only evidence relevant to original rollover obligations | Separate natural acceptance; no claim of closure from this phase's ordinary exports. |
| P0 F05 | Observation correctness, actionable incidents and acceptance coverage | Open reconciliation; reduced alert count is not sufficient. |
| P1 R01/R08/R09/R12/R15; WS1/WS2/WS4/WS6 | Credit specific reviewed/fixed callers and recovery improvements | Partial overlap, not blanket closure of any entire workstream. |
| P1 Batch A Ark | Next domain phase after this bounded reliability phase | Retain accepted callback; recheck recorded admin-add and remaining lifecycle/publication gaps. |
| P1 voting/calendar, remaining B/C and natural acceptance | Preserve existing programme obligations | Separate follow-on; MGE remains closed for now with unexercised natural cases retained. |

## Decision and change log

- 2 November: user agrees full six-workstream scope, read-only first stage, P0 reconciliation
  and return to Ark. User explicitly requires valuable retained checks not to cause contention
  or failure: observing should not interfere.
- 2 November: user requests durable documentation and progress tracking. Scope/tracker and
  developer/reference navigation created; seed source inventory started. No runtime/SQL or
  production state changed. Detailed current census and qualification remain incomplete.
- 2 November: first tracing handback adds F08-F12, check dispositions, offline reproduction,
  76-test baseline and proposed P01-P05 sequence. Current/deployed source and private history
  distinguish retained gaps from a possible adverse interaction introduced by #698. G01/G04
  remain Stage 1 work; no implementation or P0 closure is claimed.
- 2 November: user requests double/triple checking. Wider census, shared-path review and
  counter-checks add F13-F16, all 73 action pairs, offline guard-order evidence and 212 more
  passing tests. Corrected any implication that four central actions are all automatic
  recovery: the outcome worker and live committed-result recovery already handle more.
  G01/G04 are narrowed, not silently closed. No runtime or operational changes.
- 2 November: continuing through non-monitor upload callers finds F17 and the older audit
  PR/test history. Another 79 tests pass while demonstrating inconsistent success contracts;
  total 367. This is evidence that green tests must be challenged against the intended
  business outcome. No claim that all import factories share the S11 one-second timeout.
- 2 November: user requests a separate final outlier/one-off sweep after analysis. Added
  M04a/A12; it has not been run. Continued main analysis adds F18-F20, evidence-lifetime
  dispositions and 165 passing tests. The cache-lock reproduction demonstrates a missed
  shared-helper obligation already worked around in #688. No runtime changes or live repairs.
- 2 November: continued indirect tracing adds F21, a 12-root SQL dependency candidate graph,
  and explicit preserved admin/offload/queued-result safeguards. Seven unresolved lexical
  names are classified as syntax/name artifacts or system execution edges, not missing
  application procedures. Dynamic/custody behaviour still requires disposition. Another
  385 existing tests pass, recorded separately to avoid double-counting suite overlap.
  Historical candidate-row placeholders are explicitly retained as unfinished G01 work;
  M04a has not started. Statement-level cross-check then adds F22 across import/player/KVK
  publication and a source-backed file-custody disposition. No runtime, SQL or operational changes.
- 2 November: continuing conditional/dynamic analysis adds calendar F23/F24 with isolated
  current-body reproductions, March history and four-source equality. Dynamic publication
  checks retained; suspected stale-dashboard reuse rejected for the inspected caller.
  Shared optional batch-commit suppression reproduced but not attributed to protected
  import callers, which explicitly commit. Added coverage ledger and 28 passing tests.
  Main analysis and final sweep remain separate; no runtime/SQL changes.
- 2 November: cache follow-through adds F25/F26, preserves existing event/profile/name
  ownership and passive diagnostics, and checks registry/caller metadata distinctions.
  Source/history confirms retained gaps rather than a demonstrated reversion. Another
  72 baseline tests pass. Coverage advances to 68 scoped/17 policy/286 pending; remaining
  reconciliation can include already-inspected paths awaiting evidence attachment.
  No runtime or production changes; final sweep not started.

- 2 November: recovery DAL follow-through adds F27 and the shared snapshot/check-value
  matrix. Code/history and isolated diagnostic counter-checks distinguish a retained
  classification gap from existing successful busy handling. 147 baseline tests pass;
  26 source comparisons match retained deployment pins. Coverage advances to 91 scoped/
  17 policy/263 pending. Main semantic census continues; final sweep remains unstarted.

### Main-pass closeout and operational evidence update

Report 66 and the 10:25-10:26 screenshots are E29/E32, not retrospective proof that the
cancelled scheduled SQL import succeeded. The old account restriction remains unresolved;
no-action closeout messaging does not identify its failed predicate. F28 documents the
separate stale parent projection. F29/F30 add source-body fault reproductions and historical
attribution. The B01-B15 mapping replaces the earlier pending-row counts with explicit
scoped/boundary dispositions, while keeping the independent final sweep open. No business
operation, provider request, live repair or runtime source edit was performed.

That main-pass handback made M04a the next step. The subsequent separate sweep is now
E33-E35/M04a: both source pins were rechecked, 322 additional candidates received
dispositions, F31/F32 were added and F02's exact closure chain was verified. Eight relevant
Python methods and five SQL definitions match the retained deployed pins. The 300-test
batch passed with one dependency Python-support warning; no runtime correction is claimed.
The original private-evidence diagnostic reached its directory-count guard (E36); the
user's completed v2 result found both saved evidence pairs (E37). The P03a recovery
slice is now drafted in tracing. Continue S2 design,
including F02 settlement/seal renewal, F28 terminal convergence, F31 legacy invocation
policy and G04 automation/retention. A generic incident-clear operation would not settle
the old account restriction.

## Validation of this documentation change

Security routing: documented skip for this exact prose/navigation-only working-tree delta.
No executable/security boundary changes; no SQL diff. Smoke imports and command-registration
checks skipped because runtime behaviour is unchanged. Baseline investigation tests and the
offline experiments are recorded separately in E07/E08/E11/E12/E14/E17/E18/E20; they do not qualify a runtime fix.
After the cross-check update on 2 November, architecture validation passed (0 Python files
changed); explicit-path deferred-item validation passed (all six documentation files);
security-routing validation passed (0 errors/warnings). Explicit-path test selection ran
for all six files and recommended only the generic smoke/registration commands, skipped
for the reason above. All 22 local links in the four new documents/navigation passed;
all 73 unique policy action pairs match the Markdown census and referenced source files
exist. New-document whitespace and `git diff --check` passed. These are documentation checks, not
production or native SQL qualification. Private experiment files are local evidence only.
After the F21/F22 continuation, the documentation gates passed again: architecture,
deferred items, security routing, explicit-path test selection, local links, duplicate
headings and whitespace. Generic smoke/registration recommendations retain the same
no-runtime-change skip. The 385-test investigation batch is E20, not fix acceptance.
After F23/F24, architecture, deferred-item validation (seven files), security routing,
explicit-path test selection and `git diff --check` passed. All 23 local links across
the five task documents, headings/whitespace and all 371 unique coverage rows checked
successfully. Smoke/registration checks retain the no-runtime-change skip. Private
source-body experiments and 28 baseline tests are E22/E23, not fix acceptance.
After F25/F26, the same seven-file documentation gates passed again, including all 23
task-document links and 371 unique coverage rows. The 72-test batch and twelve-source
comparison are E26; no runtime change, native SQL qualification or security-sensitive
patch was introduced. Generic smoke/registration checks retain the documented skip.
After F27, architecture, deferred-item validation (seven files), security routing and
explicit-path test selection passed. All 24 local links in the five task documents,
371 unique coverage rows, F01-F27/E01-E28 IDs and document whitespace/headings checked
successfully; `git diff --check` passed. Source pins are unchanged and SQL remains clean.
Generic smoke/registration and security-scan skips retain the exact documentation-only
rationale above. E27/E28 record the isolated experiment and 147 baseline tests separately.

After the main-pass closeout/F28-F30 update, architecture (0 changed Python files),
deferred-item validation (seven Markdown files), security routing (0 errors/warnings)
and explicit-path test selection passed. The selector again recommended generic
smoke/registration checks, skipped because this patch changes documentation only.
Security review remains a precise documentation-only skip; there is no SQL/runtime
patch. The 79 baseline tests and isolated current-body experiments are E30/E31,
separate from fix qualification. Document verification checks 25 local links, 371
unique coverage rows, F01-F30/E01-E32 identifiers, table structure, headings and
whitespace. Source pins remain unchanged; no production operation was repeated.

The final-sweep update adds the sixth task document and E33-E35/F31-F32. Architecture,
deferred-item validation (eight Markdown files), security routing, explicit-path test
selection and document checks pass: 31 local links, 371 historical rows, 322 distinct
final-sweep rows and F01-F32/E01-E35 identifiers. SQL is unchanged. The same generic
smoke/registration and documentation-only security-scan skips apply to the repository
patch. The two private diagnostic scripts were parsed and inspected separately for
fixed identities, bounded reads, suppressed payload values and absence of repair/provider
operations; these local evidence helpers are not application deployment changes.

The pre-commit wrapper could not update its read-only user cache. Its five cached
hygiene hooks were run directly instead. Existing README trailing whitespace was
preserved after the formatter touched it; the newly added README lines pass
`git diff --check`, and the other seven Markdown files pass the direct hooks. No
repository-wide Python type check or staged-secret scan is claimed for this prose-only,
unstaged change. The 300 focused tests and both isolated closure/timing experiments are
investigation evidence, not runtime-fix acceptance or a unique cumulative test count.

The E36 follow-up replaces only the private read diagnostic after its enumeration cap
was reached. It preserves the original script/evidence and changes no application or
SQL source. The new selector retains bounded candidates instead of materialising the
directory, reports time/candidate/metadata limits without claiming absence, and bounds
actual ciphertext bytes read. The tests ran under Windows PowerShell 5.1 using local
synthetic metadata and encrypted fixtures; no production folder or application client
was used. The tracker/tracing update remains a documentation-only security-review skip.

## S2 delivery-design validation

The current S2 addition passes architecture validation (zero Python source changes),
deferred-item validation for nine Markdown files, explicit-path test selection and
security-routing validation (zero errors/warnings). Document reconciliation passes:
seven task documents, 43 local links, 371 historical rows, 322 final-sweep rows, all
32 findings assigned once, and E01-E39. Whitespace checks pass. Runtime smoke/import
and command-registration checks remain skipped for the prose delta; E39's four native
tests and synthetic SQL experiment are separate design evidence, not new-fix acceptance.

The ignored local experiment uses the existing guarded fresh-database fixtures and
restricted SQL principal, pins unchanged procedure sources, and has no provider client
or production connection input. Its deliberate discarded commit reply tests readback
orchestration after a real commit; it is not a network-fault injection. A separate
Codex Security scan has a documented skip for this non-deliverable measurement harness
and prose-only proposed repository delta. Use `k98-security-review-routing` for the
executable P03a implementation/runner, then `security-diff-scan` on its exact Changes
target before handoff, including custody and SQL access; Deep off.
No evidence here approves that executable package.

The original preservation archive remains unchanged. A new timestamped private local
snapshot is prepared after S2 validation; its manifest/receipt includes the updated
documents, native experiment and result. Neither archive is a publication or permission
to execute included scripts. This was the S2 checkpoint: the subsequent P03a.1 approval
and implementation supersede its pending M05/M06 state; M07 remains unstarted. No new
deferred item was invented: identified work remains within the F01-F32 package mapping.

## P03a.1 implementation and durability qualification

The exact nine-file mirror package contains a resumable saved-result service, short
account-locked snapshot/CAS adapter, protected fixed packet/launcher, compatibility
bootstrap, focused and native tests, and `docs/reference/Saved result export recovery.md`.
It records the retained final result, creates a new closure linked to the original
stopped-child evidence, then verifies the existing legacy closeout receipt. The old
failure and original seal remain preserved. It issues zero provider requests and reports
partial-export abandonment, never completed delivery.

Repeated missed-case review checked shared default stranded callers, complete private
proofs, native SQL representation, restart after each write, lost acknowledgements,
connection cleanup, permanent errors and optional output failures. It corrected SQL
GUID casing in the digest, canonicalised private-store references, removed redundant
full-history verification, and isolated final Python/PowerShell presentation after a
durably verified result. Corrupt/partial journals and incompatible ownership still stop;
they are not converted into successful retries. No unrelated refactor was added.

Architecture, deferred-item, security-routing, explicit nine-path test selection,
ruff/black, staged whitespace, staged secret scan, import smoke and command registration
passed. The configured pyright run returned zero errors and 28 dependency-resolution
warnings in its cached environment. Smoke passed with synthetic test configuration and
dotenv disabled; its initial missing-OUR_KINGDOM/console-encoding setup was corrected.
The earlier local-handoff full-suite skip is superseded by PR qualification. Mirror full
pytest had 10,856 passes, 1,106 skips and 8 passing subtests; its only 18 failures were
the unchanged interpreter guard rejecting the shared environment. All 18 passed with
the mirror-local interpreter, with the log guard confirming unchanged operational logs.
The failed full run exited before its log comparison, so it supplies no full-run log
hygiene claim. Private full pytest with its local environment passed all 10,875 tests,
with 1,105 skips and 8 passing subtests. No source workaround was made for environment
setup. These results do not substitute for installed custody or production acceptance.

The later PR comment exposed adapter execution before its collision guard. The final
loader rejects the saved-result collision before module execution; original stranded
defaults are preserved. Both checkouts passed 86 final recovery tests/log hygiene, and
real Windows `-I -B` qualification proved no module side effect on rejection. The earlier
full Windows/Linux suites predate this narrow correction; final private CI repeats the
full Linux suite (10,734 passes, 1,248 skips and 8 subtests). The affected Windows tests cover the correction; no service/DAL/SQL
source changed, so native SQL tests were not repeated. The null-spec diagnostic suggestion
was assessed and answered: fixed authenticated `.py` callers and existing fail-closed
handling remain unchanged. No unsupported fallback or extra workflow was introduced.

The final [operator plan](C:/Users/cwatt/Downloads/K98-P03a1-20261102-r2-Deployment-and-Validation.md)
and private ZIP `C:/Users/cwatt/Downloads/K98-P03a1-20261102-r2.zip` are prepared.
Use only this corrected packet; the earlier local candidate is marked superseded.
Private `p03a-merged-delivery-review.md`, `p03a-operator-handoff.json` and final PR
source/patch/CI receipts retain exact hashes and qualification. The user subsequently executed this handoff successfully (E43). P03a.1 is complete; do not repeat its recovery steps.

The source review found a terminal console failure that could label committed recovery
as stopped; the final 84-test batch includes write, flush and PowerShell notice failure
regressions, with default stranded and unverified output errors unchanged. Native SQL
tests were not rerun after this presentation-only correction because the service/DAL
and SQL paths were unchanged. No F01-F32 finding is closed by local source readiness.
P03a.2 automatic runtime settlement and truthful projection remain required for F02.

## Handoff rule

Handover validation passed: nine Markdown files through architecture/deferred-item/test
selection, security routing with zero errors/warnings, and five cached hygiene hooks
run directly for this update. Document checks cover seven task documents, 39 local links,
371 historical rows, 322 final-sweep rows, all 32 findings assigned exactly once to a
primary package, and E01-E37. Generic runtime smoke/registration checks retain the
documentation-only skip; no application test rerun is needed for this handover edit.
The preservation script verifies every archived file against its SHA-256 manifest and
records a separate receipt. Raw external attachments are indexed by path/hash and are
not included in that private local snapshot.

The delivery handover is the next-chat entry point. Preserve its local snapshot and
the existing uncommitted documents/private evidence before transferring to another
checkout. The user has requested the new delivery chat; its creation receipt will identify
the continuation. The original investigation created no branch/worktree/PR/deployment;
delivery now uses the existing mirror and private promotion checkouts, with explicitly
authorized PR/review/merge work. See current M06/M07 rather than the historical no-PR
checkpoint. Preserve the patch, source hashes, review/CI receipts and operator handoff.
The user completed P03a.1 production recovery (E43) and the P03a.2 startup correction/updater upgrade (E49). Fresh export acceptance remains pending. Local preservation is not a remote backup.
The agreed priority adjustment does not renumber packages or drop P01-P05 work.

Resume at the first unfinished milestone and next question above. Keep accepted evidence,
stable IDs and user decisions. Add findings to this register, link actual PR/test/acceptance
evidence as work progresses, and update source pins when they change. Do not restart the
historical review or declare the census complete because the seed map exists.

| E80 | Operator approved full P01.3 implementation and validation including persistent Refresh, and preparation for PRs. Required related-caller and cost/value checks continue throughout. | Implementation and local validation authority; no live probes, production changes, merge or deployment. |
