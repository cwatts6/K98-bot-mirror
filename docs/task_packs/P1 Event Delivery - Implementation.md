# P1 event delivery implementation

Operator approved the expanded delivery phase on 26 October 2026 after scope review.
This checkout starts at the unpublished startup closeout commit `0de73d23`.

Selected scope: private status responses, enabled caller/authority map, public and
DM reminder ownership and durable outcomes, Daily KVK Overview disposition,
restart/shutdown qualification, and truthful passive diagnostics.

Existing SQL authority remains unchanged. Startup SP_Stats_for_Upload-path SQL
51400 and recovery-discovery refusal remain separate unresolved incidents. No
blocker identity or common root cause is established. A successful status retry
does not explain the 09:02:46 UTC Unknown Webhook incident.

The deployed baseline is private `a68089b6bccf766e9aabb182c582d486130145dc`.
This development checkout is not MINI_AMD. Source, deployment, readiness, provider
delivery and live acceptance are separate evidence stages.

## Architecture and observable changes

The approved phase combines N1–N5 with the selected DM and Daily KVK Overview
lifecycle work. It preserves reminder windows, event eligibility, public mentions,
private permissions and existing SQL coordination. Public reminder replacement now
requires confirmed deletion of the original. Expiry checks the original message
identity. Failed/cancelled remote operations retain uncertainty across restart.
DM sends check current subscriptions immediately before dispatch; unsubscribe
removes eligibility before cancellation and preserves accepted/uncertain evidence.
The overview reports created, updated, removed, confirmed absent, skipped, closed,
or unconfirmed dispositions rather than claiming every invocation posted a message.

The status command owns one private defer and final edit. SQL connectivity is in a
DAL and retained draining worker with a bounded observation window. Existing Sheets
probe ownership is reused. A failed acknowledgement starts no probes. Webhook
10015 logs phase, acknowledgement, age and duration without token/exception text;
there is no channel or DM fallback. This bounds the failure and improves diagnosis;
it does not establish the historical webhook root cause or promise its elimination.

## Enabled caller and authority map

This is a source-backed map of registered/configured paths, not a new live census.
Runtime feature flags and natural eligibility still determine execution. Report 45
confirms a healthy completed monitoring cycle, not coverage of every writer.

| Caller / entrypoint | Existing owner or authority | Phase change / remaining limit |
|---|---|---|
| `bot_instance.on_ready`, `core/startup_lifecycle.py` | Once-only startup and `TaskMonitor` | Existing ordering retained; no universal scheduler |
| Startup player stats and main/last-KVK refresh | Original cache owner, `LegacySnapshotRuntime`, account then snapshot SQL authority | Preserve draining worker, producer-entry evidence and refusal; no new retry/admission protocol |
| Profile/name startup and Location reads | Delivered profile/name cache ownership | No reimplementation; historical reporting discrepancy has positive post-fix evidence |
| Recovery discovery `UnownedSqlHoldDAL._snapshot` | Account mutex then SQL snapshot mutex, SQL durable records | Separate refusal from startup; requester is not blocker |
| `/ops dl_bot_status` | Existing admin/notify-channel guard; new private response owner; retained SQL and Sheets probes | Bounded observation, no synchronous SQL in command, no public fallback |
| Public reminder loop and expiry | Existing `TaskMonitor` parent plus selected child set and per-event lock | Strong child references, observed errors, close/drain, exact-message expiry, durable send/delete/edit evidence |
| DM scheduler and restoration | Existing per-user reminder task registry, current subscription, sent/scheduled projections | Snapshot writes drain; cancelled sleepers remain scheduled; entered sends are held; acknowledged sends repair markers without resend |
| `/me` unsubscribe | Existing preference persistence and per-user cancellation | Commit eligibility removal first; retain accepted/uncertain delivery evidence |
| Daily overview scheduler/manual command/removal | Per-channel scope lock, existing generic tracker lock, two legacy projections | One orchestration path, separate send/edit/pin/delete receipts, safe projection repair |
| Generic tracked-view restoration | Existing exact-entry fingerprint and restoration-edit receipt | Shares overview scope lock; reports fetch disposition and observed component count; registration is not callback acceptance |
| Recovery report and status evidence | Existing report composition; passive observation of new journal | Timestamp and changed-since-observation flag; no refresh/replay during report rendering |
| ProcConfig, legacy reports, Stats/KVK History, PreKVK/fighting dispatch, Ark/MGE/voting, provider/export recovery | Their existing SQL/domain authorities | Interfaces remain part of WS1–WS6 census; broad implementation is outside this phase |

The new selected child set owns only public send/expiry and overview invocations.
It is not a scheduler or cross-process singleton. DM tasks retain their existing
registry. Shutdown closes admission before draining; timeout never authorizes
closing Discord while a selected persistence finalizer still runs.

## Persistence and restart contract

`data/event_delivery_receipts.json` is a versioned, atomic, file-locked evidence
journal. Keys identify the delivery family, target, event/window or exact message
operation. States are entered, acknowledged, refused and confirmed not-found.
Entered means an operation may have happened and is never automatic replay
permission. Send acknowledgements retain exact Discord message/channel identity.
Known target identity is written before edit/delete/pin dispatch. No tokens, message
bodies, embed content or credentials are retained in the journal.

Existing `active_reminders.json`, DM sent/scheduled files and Daily KVK Overview
trackers remain compatible projections. The journal protects acknowledged-send /
projection-failure and interrupted-send windows. Legacy sent markers still suppress
duplicates. Corrupt/oversized evidence fails closed; uncertainty is not deleted by
age. Unresolved public tracker entries survive unrelated saves. Two overview
trackers disagreeing blocks publication instead of creating another message.
An exact message-fetch 10008 is distinct from Forbidden or a missing channel.
New creation after confirmed absence is a later ordinary invocation, not a fallback
from an edit exception. Unknown historical overview disposition is not retroactively
resolved by these new receipts.

The journal has an 8 MiB safety limit and no automatic receipt deletion. Bounded
archive/reconciliation tooling remains separate; full evidence requires operator
inspection, not truncation. Source rollback to a reader that ignores the journal
is unsafe while entered/partial operations exist. Preserve all journal/projection
bytes and use a reviewed forward correction; never reset files to make rollback
or redeployment appear clean.

## SQL evidence and causal limits

Static review used clean SQL source `C:\K98-bot-SQL-Server` at `1e95e41d`.
Validated `ExportPreparation`, `ExportPreparationResource`, `ExportResource`,
`StatsImportExecution`, `ExportExecutionStream`, `ExportUnownedHoldDisposition`,
`ProcConfig`, `SP_Stats_for_Upload`, output shape and transaction-lock order.
The procedure's internal import/publish lock errors differ from admission SQL
51400 before producer entry. No new SQL objects, columns, indexes, migrations,
permissions or provider operations are required. The new SQL status DAL only
performs the existing connectivity query. Static source does not attest installed
production SQL definitions.

Startup 08:30:06.446 refusal and recovery discovery 08:41:07.154501 remain separate.
No holder identity/common cause is established. Requester session and process
singleton are not substitutes for blocker evidence. Existing admission diagnostics
are retained; coordination behavior is unchanged until causal evidence supports it.

## Validation, review boundaries and acceptance

Review in four cohesive parts: status/caller ownership; public reminder receipt and
child ownership; DM persistence/unsubscribe/restoration; overview and shared passive
reporting. These parts share the journal contract and ship as one consistent source
release. The prepared documentation closeout is included without reapplying merged
runtime code. Mirror review precedes patch-based private promotion, exact-head
validation and protected MINI_AMD installation.

Meaningful deterministic gates cover concurrent callers, cancellation before and
during dispatch, restart with entered or acknowledged receipts, failed atomic writes,
lost projection writes, exact-message expiry, failed deletion, duplicate suppression,
unsubscribe ordering, missing/forbidden messages, private acknowledgement failure,
10015 response failure and retained SQL probes. Broad offline regression, architecture,
deferred-item, command-registration, smoke-import, test-selection, log-hygiene and
security-routing checks remain required before promotion. Review security with
Changes against the final base/head; Deep is off. SQL is unchanged and does not
need a fabricated SQL diff review. No live probes are part of offline validation.

Deployment/readiness acceptance must name the protected source, restart and
readiness receipts. Natural runtime acceptance then observes a legitimately due
public reminder, a subscribed DM, unsubscribe while pending, and an eligible
overview lifecycle without synthetic events, refreshes or reposts. Verify exact
message identities, visible controls, callback eligibility and both tracker
projections. A healthy monitor or acknowledged Discord API response alone does
not satisfy those acceptance rows. Do not repeat the passed Location checks or
eligible original Ark callback merely to populate new-runtime evidence.

## Separate programme residuals

The complete R01–R18 register in the 26 October closeout and scope remains binding.
This phase advances selected R02/R03/R04/R06/R12 interfaces; it does not close their
unexercised natural paths or any whole workstream. Preserve all three P1 families:
tracked views/restoration, startup/cache readiness, and operational coordination /
background delivery. Carry forward:

- R01 SQL refusals; R02 historical webhook cause; R03 natural loaded-empty to
  populated transition, deferred tasks and natural DM restoration; R04 exact old
  Daily KVK Overview disposition; R05 singleton ownership; R06 broader children;
  R07 historical tracker eligibility and original callback evidence.
- R08/WS1 legacy ProcConfig reports, manifests, artifact identity and truthful
  partial/unknown reporting; R09/WS2 fallback/history/stats alerts and no re-entry;
  R10 durable profile invalidation; R11/WS5 caps, KS preclaim, PreKVK ambiguous edit,
  in-memory tracker and audit policy; R12/WS6 complete enabled-writer census.
- R13 natural PreKVK/off-season/Phase 2F public-save acceptance; R14 external
  monitoring; R15 updater/custody/stream/stranded-export productization; R16
  history/quota/performance, SQL 1222 and lost-acquisition-ack qualification.
- R17/P0 genuine F04 rollover and final every-row F01–F05 reconciliation; R18 fresh
  runtime end-to-end import/export acceptance. Preserve scan 1233 eleven-sheet
  confirmation, all accepted imports/exports/scans, original receipts, URLs and
  abandoned disposition. Scan 1193 from 29 September 14:44 is expected off-season
  data. No new acceptance is inferred from this implementation or its tests.

### Deferred Optimisation
- Area: services/event_delivery_store.py receipt retention and operational reconciliation
- Type: performance
- Description: The selected delivery journal retains all original receipts and fails closed at 8 MiB. Rewriting the full bounded document becomes more expensive as receipts accumulate; there is deliberately no age-based eviction or automated uncertain-work recovery.
- Suggested Fix: Design an exact-identity reconciliation and archive workflow with immutable retained receipt segments, a bounded active index, verified readback and interruption/resume behavior. Archive only dispositions established from evidence; preserve entered/unknown work and references from both legacy trackers. Measure real growth before choosing limits.
- Impact: medium
- Risk: medium
- Dependencies: Separate reviewed persistence design, complete receipt preservation, deterministic lost-ack and partial-archive tests, and Changes security review. This is not authority to truncate, replay or release retained work.

## Release mechanism

The installed updater registry remains the authority. The new `p1_event_delivery_v1`
entry pins exactly 16 application members and their predecessors; the registry
bound increases from 42 to 43 while the 16-member/64-KiB bounds remain unchanged.
Historical transition hashes are unchanged. The new policy and registry must be
installed through the authenticated updater-upgrade package before preparing this
source release. Target source cannot authorize its own new transition. Exact
bundle tests reject omitted/extra/foreign members, renamed transitions and altered
predecessor/successor bytes. Test-only historical hash bridges do not authorize
production installation.
