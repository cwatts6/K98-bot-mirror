# Guided recovery delivery

## Atomic configuration producer and guided outcomes — 2026-10-16

Coordinated configuration imports now reserve a typed producer and hold the actual
business transaction's ownership locks across configuration writes, target
publication and the completion checkpoint. No intermediate commit occurs, even
when the legacy non-transactional setting is selected. The target procedure allows
the ambient transaction only for the exact typed writing reservation; ordinary
standalone calls preserve their existing transaction policy. Latest-season lookup
uses the same business connection to avoid waiting on its own configuration locks.

Independent discovery creates a private configuration-publication incident.
**Close rolled-back config & release** presents a separate checklist/confirmation,
then excludes live execution, verifies the absent atomic receipt, fences the old
attempt and verifies the exact release. A committed result instead offers
**Finish capture & queue export** or the explicit verified export-skip action.
The existing admin permission, audit and durable action framework is reused.
Lost replies reconcile the saved receipt; stale confirmation cannot cancel a
later commit. Neither closure nor export queueing claims a cache refresh.

Validation: 280 affected tests passed, including disposable SQL and actual admin
button callbacks. The final migration/source-pin and operational-log checks passed
60 tests. Seven literal target-procedure/migration cases cover transaction gates,
nested commit behavior, rollback and exact source images (delta work is a synthetic
callee; this does not claim full production-data publication). Architecture (196
files), deferred-item, security routing, test selection, synthetic import smoke,
command registration (36/102), Ruff, Black and whitespace checks passed.
Final pin correction: 28 activation/configuration tests passed, including seven
disposable SQL target-contract cases. The reviewed activation scope digest now
matches the canonical document; unchanged fail-closed validation remains enforced.
Bot Changes review `5c606dd0-f193-48fe-ac3f-cf7f7e912713` covers
`d933b94e..c0f8a248` (14 source files), and correction review
`f4e554ed-b12c-4cec-afd0-c7530c5485a4` covers `c0f8a248..5842ec5d`
(one source file). SQL review `c018f01b-44ec-4983-bfa2-8a6b135dd03e`
covers the two SQL source files. All completed, sealed and read back with no
findings or coverage gaps. Tool-reported token usage: 3,502,958, 1,098,856 and
2,734,772 respectively. SQL companion: PR #119. Focused tests cover this slice;
the inherited full-suite result remains qualified as recorded below.
SQL changes install before the
paired Bot and protected contract reissue. Only the target procedure source pin and
its new coordination dependencies changed; unrelated historical pins are preserved.

This is an active P0 slice, not programme completion. Existing partial configuration
commits, guided fresh continuation, UPDATE_ALL2 partial reporting, durable remaining
pipeline stages, all-copy custody/history loss and integrated rollover completion
remain required implementation/acceptance work. None is deferred optimisation.

## Replacement-read admission guidance — 2026-10-16

Replacement verification now identifies an exact account-scoped blocking owner
before offering a read check. The private incident provides **Review blocking
operation**, using the existing authorised guided recovery for queued/held exports,
rollovers, configuration reads, report producers, SQL stages and replacement reads.
After verified settlement, **Recheck** restores **Check replacement files** and its
separate confirmation. SQL still enforces admission at execution time; this read-only
explanation cannot release resources or override healthy work's priority. Changed
ownership invalidates the old confirmation. Other-account identities and private
request/configuration data never enter the incident. Unattributed resources remain
open for the separate required evidence/custody recovery; this is not P0 completion.

The queued/held ownership and stale-click cases use disposable SQL. The restart
case invokes the actual confirmation button and verifies a complete new read before
activation, while the original job remains uncertain. This slice also rechecks the
existing output/source/rollover paths. Twelve disposable SQL tests pass, including
the actual reserved continuation linking to its validated original recovery and
foreign-account rejection. Architecture (191 files), deferred items, security
routing and test selection pass; synthetic imports, command registration, Ruff,
Black and whitespace checks also passed. The parent suite result below remains
qualified; this slice uses focused coverage rather than claiming a full green suite.
Changes review `90aec1d2-f77d-46d8-8d68-59c6e1825426` sealed `a2f4ad5a..eb6e464a`
(two source files); correction review `4b63629d-a406-42ff-8119-3e2bc7bf860d`
sealed `eb6e464a..3cf8fb3a` (one source file). Both have complete coverage and no
findings; sealed results were read back. Tool-reported usage respectively:
1,525,221 and 1,738,105 tokens. The correction validates parent account, storage,
both request hashes, producer type, non-nested lineage and matching retained inputs.
No provider writes, persistent SQL installation or
production deployment are authorised by this slice.

## Rollover evidence-loss routing — 2026-10-16

Lost unactivated rollover proposals and read-check evidence now retain their
explicit rollover owner throughout inventory, authenticated workflow composition
and admin links. The private incident opens the correct rollover recovery with
**Run fresh read check**, or guided read discard and paginated replacement re-entry.
A fresh verified check supersedes the unavailable read/proposal dependency; the
original lost receipt is never reconstructed or accepted as successful evidence.
Activation and the original rollover incident remain separate verified outcomes.

Nine disposable SQL tests passed, including real alert/confirmation callbacks,
lost receipt/closure/payload/event, wrong-account rejection, restart, unfinished
proposal-read discard, new approval, fresh verification, activation and durable
rollover continuation. The original operation stays uncertain. Neither ambiguous
owner identity nor a job-only fallback can authorize recovery. Shared export-job
regression passed 44 tests; the log-isolation check confirmed operational logs
unchanged. Changes scan `ac36e188-2384-4401-beab-25b23c53e31b` now completes and seals
`1261fafd..1cc629da`, all three changed source files, no findings or coverage gaps.
The sealed result was read back. The previous finalization error was malformed
coverage entries, corrected through the semantic draft tool before completion;
no review was skipped. Tool-reported usage: 1,750,191 tokens. This slice does not close
all-copy containment/active-history recovery or the remaining P0 programme.

## Interrupted rollover replacement — implementation checkpoint, 2026-10-16

P0 is still active. The saved `codex/guided-rollover-replacement` Bot and SQL
changes now implement complete old-pool isolation, the existing paginated admin
replacement form, fresh file verification, registration activation, one durable
replacement rollover and independent completion verification. The original
operation stays uncertain and its files remain permanently isolated. Replacement
workers stop after setup for the guided final verification; neither a timeout nor
activation alone resolves the incident. Repeated failures link to the next
replacement's recovery and preserve the original season choices.

The existing private confirmation views are exercised through actual button
callbacks for file checking, activation and queueing. Saved form pages survive
restart. Final verification requires the original sealed phase journals and the
final probe's private receipt, even if that probe is absent from a catalogue
listing. Evidence changes between an admin confirmation and the replacement
snapshot reject the action rather than adopting newer evidence.

Validation: the final affected regression run passed 664 tests, including the
literal migration compilation, both enrollment admission paths, stale-click and
explicit-probe checks. The earlier focused run proved operational logs unchanged.
The actual-button temporary-SQL integration passed.
Ruff, Black and whitespace checks pass. Earlier architecture, deferred-item,
security-routing, test selection, synthetic import and command-registration
checks also passed for this slice. These are synthetic provider/Discord and
disposable temporary-SQL results, not production acceptance.

The previous security finalization error is resolved: scan
`91eb0a8b-2355-45a8-9087-9b36b37d8fba` is completed and sealed, and its existing
result was read back successfully. It covers its original proposal-loss range;
it does not cover the new rollover replacement implementation. This new Bot/SQL
Bot Changes review `d6352ffc-680f-4185-ba50-6fae6b1d5318` completed and sealed for
`133d1007..cadc0299`: all 19 source files, no findings or incomplete coverage,
Deep off. Its sealed result was read back; tool-reported usage was 1,362,807 tokens.
The full standard suite finished: 8,159 passed, 572 skipped, eight subtests passed,
four failures. Two stale recovery test assumptions were corrected (560 pinned
objects and an accepted integer timeout); the affected tests plus the transient
Windows diagnostic-file failure passed on a focused rerun: 82 passed. The fourth
failure is the pre-existing absent `.github/workflows/command-governance.yml`,
also absent at the base commit. No unrelated workflow was introduced. These
test-only changes do not alter the reviewed runtime. The 664 affected tests and
five historical/current migration tests passed. Architecture (187 files), deferred
items, security routing, test selection, synthetic imports and command registration
passed. SQL Changes review
`38c1fffa-fc9f-4c92-8104-f5dbbfa89ac3` completed and sealed for
`95b4e91b..24cbca0c`: seven source files, no findings or incomplete coverage,
Deep off. The sealed result was read back. Tool-reported usage: 3,800,664 tokens.

The operator explicitly approved both previously rejected changes for implementation
and disposable testing. Private admin comparison pages are implemented in the
separate admission-decisions branch. Enrollment now excludes only receipt-verified
isolated rollovers; the original uncertain operation stays retained. Migration
`20261016_001_rollover_replacement` guards five exact predecessors and installs six
reviewed definitions atomically, with authority-only execution for containment.
The Bot installation contract includes this migration and procedure.

Source pins were updated only for the six affected procedures and two existing
required history tables absent from the prior manifest. The activation scope
retains unrelated source hashes and dependency edges, updates the eight affected
objects, and binds SQL revision `24cbca0c`. A broad regeneration exposed pre-existing
unrelated source-hash mismatches and was rejected by automatic approval review;
no broad rebaseline was applied. This is an installation qualification requiring
separate evidence before deployment, not proof that unrelated definitions match.
No live provider/Discord action, persistent SQL installation or deployment ran.

Remaining P0 acceptance is not deferred: finish both focused reviews and PRs;
verify the full replacement completion and
failure-during-repair paths together; complete historical/changed-registration
admissions, all producer atomic checkpoints and durable remaining-pipeline
continuation; implement guided recovery for all-copy containment/active-history
evidence loss; and pass integrated proactive-alert-to-guided-repair acceptance.
Every remaining recovery must expose its checks and executable admin actions,
retain interrupted decisions, and resolve only after verified settlement.

## Waiting rollover admission — 2026-10-16

The `codex/guided-rollover-admission` slice adds **Continue waiting rollover**
to the recovery centre for the original unowned `closing`/`ready` operation.
Its confirmation states the old/new seasons and that registered old files will
be made private and cleared. Pending old-season exports link directly to their
recovery workflows. The existing authority drain proof, queue admission,
ownership CAS and phase journal remain mandatory.

Lost intent replies and queue waits retain one recovery action and the original
operation. Reconciliation may enter only an unowned operation; it never repeats
an already-owned provider phase. Admission handoff may verify while the incident
remains open; only completed rollover resolves it. This does not yet cover
interrupted private/clear phases or missing historical receipts, which remain
active P0 acceptance requirements.

Validation: 194 focused tests passed, including confirmation, stale preview,
restart, queue waiting, lost provider replies and existing rollover ownership
regressions. Log-noise validation kept operational logs unchanged. Architecture
(174 files), deferred-item and security-routing validators, test selection,
synthetic smoke imports, command registration, Ruff and Black passed. The broader
standard-suite baseline remains the previous 8,115-pass run; it was not repeated
for this two-source-file adapter/composition change. SQL object/state contracts
were checked against the authoritative SQL repository; no SQL schema changed.

Changes security review `497afa0a-5d6c-4de8-a2fa-ec749dfc4a5e` completed and sealed
for `ec87ffedd70d9cc63696fa4465d7e5c15d1aeb54` through
`df6032d046840dd6920845ca9bf189553f0feec6`: both runtime source files reviewed,
zero findings, no deferred security coverage. No measured token usage was
returned. This subsequent documentation-only checkpoint has no runtime effect
and does not require another Changes scan. No deployment or live provider or
Discord execution occurred. P0 remains active with no recovery gaps deferred.

## Guided admission decisions — 2026-10-16

The operator approved private admin comparisons of retained scan inputs and old/current
destinations. `codex/guided-admission-decisions` implements complete bounded review pages
before the separate **Confirm & apply repair** action. Every page reauthorizes the
configured admin/guild/channel and rechecks exact evidence. All destinations are linked;
retained inputs and output settings are paginated without truncation. These details
are ephemeral and are not copied into the proactive incident alert. Reopening after
restart reconstructs the current checks from persisted state.

A changed registration requires the explicit **Continue with current destinations**
decision, bound to both registration fingerprints. Continuation keeps original scan
inputs and history, reserves one durable action, verifies admission/receipt after a
lost reply, and never replays a committed import. Healthy older queued work is shown
as a blocker before it owns a resource. Player-report and receipt-free scan blockers
link to their correct recovery flow. Attempt history is streamed and hashed without
a fixed 100-attempt cutoff; exact original action identities remain reconcilable.

Validation: 57 focused tests passed; a subsequent five-test SQL rerun exercised actual
private review/confirmation callbacks through the saved-input dispatch and lost-reply
receipt. Coverage includes wrong actor/guild/channel, stale evidence, 37 destinations,
long metadata, restart, changed registration after preview, 105 prior refusals and
queue blockers. Only session-local SQL objects and mocked Discord/provider calls ran.
Changes review `5c2fed15-a694-40cb-a512-adae66accea1` completed and sealed for
`ec87ffed..323f227f`, seven source files, no findings or incomplete coverage, Deep
off. Its sealed results were read back; tool-reported usage was 1,615,383 tokens.
Architecture, deferred-item/security-routing checks, test selection, Black, Ruff,
synthetic smoke imports and command registration passed. The earlier full-suite
checkpoint is unchanged; this bounded admission slice uses its 57 affected tests.
No schema installation or deployment ran.

P0 remains active: full pipeline continuation and producer checkpoints, historical
missing-input/pre-request cases, all-copy containment/active-history evidence loss,
replacement admission blocker guidance, and integrated verified completion remain
required acceptance work. None is classified as deferred optimisation.

## Atomic player-report recovery checkpoint — 2026-10-16

The `codex/guided-producer-checkpoints` slice commits player-stat report output
and its completion checkpoint together. The actual producer transaction holds
the exact ownership locks, so a lost independent guard cannot permit recovery
to release a running write. Proactive discovery provides guided **Finish capture
& queue export**, **Keep SQL; skip this export**, or **Close failed report &
release** decisions. Every repair verifies its checkpoint or durable closure;
lost replies reconcile the original action and late old claims are fenced.
Admission-blocker buttons now select the report workflow instead of incorrectly
opening import recovery. Imported scan data is never replayed by these actions.

294 focused tests passed, including isolated temporary SQL commit/rollback,
lost-guard exclusion, lost acknowledgements, interrupted admissions, stale
confirmations, capture failure, real Discord button routing and eligible saved
stage availability after release. The 161-test log-isolation run left operational
logs unchanged. Architecture (173 files), deferred-item/security-routing checks,
test selection, synthetic smoke imports and command registration passed. Ruff
passed; two final formatting-only corrections apply Black's required layout.
Authoritative SQL confirms SP_Stats_for_Upload preserves its caller transaction;
no new schema, persistent SQL installation or production/provider operation ran.

Changes reviews `417190bc-0807-4935-a30f-49099be9e692` (`340490bf..1f5d773e`,
11 source files) and `e993daee-d4cb-4ec8-b04e-ee2fd7fb8af0`
(`1f5d773e..3bede450`, two source files) both sealed successfully with no reported
security findings. Final semantic drafts were accepted before completion and
sealed artifacts were read back. The ordinary blocker-link issue identified in
the first review is corrected and covered by the second. Subsequent changes are
formatting and this evidence record only, with no behavioral security impact.

P0 remains active: this closes the report transaction/capture/release gap, while
guided remaining-stage continuation, configuration/other producer checkpoints,
historical and changed-registration admissions, queue contention, earlier
rollover phases and all-copy containment/active-history repair still require
implementation and integrated acceptance. None is deferred optimisation.

## Interrupted original admission checkpoint — 2026-10-16

Draft PR #352 provides confirmed-refusal continuation. The next focused
`codex/guided-unstarted-stage` change also discovers typed original admissions
interrupted in pending, preflight, SQL-pending, writing or uncertain state before
SQL execution registration. **Cancel unstarted reservation** checks both SQL
guards, exact ownership, immutable inputs, and absence of receipts/streams/output;
it atomically fences and releases the reservation. Only then is a separate
**Resume saved SQL stage** confirmation offered. A registration race instead
links the exact original import receipt without release or replay.

62 focused tests pass, including temporary SQL for all five interruption phases,
lost closure/intent replies, live original writer exclusion, changed ownership,
late callbacks, child-adoption rejection, discovery and existing guided flows.
An initial fixture query qualification and test timestamp transaction were fixed;
the final run passes. Architecture (168 files), deferred-item/security-routing
checks, test selection, Ruff, Black and synthetic imports pass. The prior command
registration check is retained because this change adds no command/view surface.
No schema, persistent SQL installation or provider/production operation is added.

Changes review `fd9f6167-de78-43e6-8a52-141ebfaf5c25` sealed successfully for
`fb394d51..1d54e2ba`: both source files reviewed, zero findings, sealed result
read back. The final semantic draft was accepted before completion.

Historical inputs and changed-registration decisions, durable remaining pipeline
stages, partial producer results, earlier rollover phases, all-copy containment/
active-history evidence recovery and integrated full P0 acceptance remain active.
This checkpoint does not mark P0 complete or defer a recovery requirement.

## Refused SQL stage checkpoint — 2026-10-16

`codex/guided-refused-stage` adds durable exact stats inputs before writer admission,
proactive discovery of confirmed pre-execution refusals, scoped blocker buttons,
an explicit **Resume saved SQL stage** confirmation and links to the resulting
SQL receipt/capture recovery. Excel conversion and archive are not repeated.
Action reservations and terminal markers prevent replay after lost replies;
dispatcher, producer and per-import SQL guards exclude live work. An interrupted
continuation without any execution receipt, provider stream or generation is
fenced and released by exact ownership checks before another action is offered.
A registered execution is handed to the existing guided import recovery and is
never replayed by this adapter. Recovery does not overwrite another pipeline's
global metadata manifest.

172 focused tests pass, including temporary SQL, real Discord view callbacks,
authorization, changed registration, lost intent reply, late dispatch, interrupted
admission phases, external session locks, discovery pagination and receipt handoff.
Architecture (167 files), deferred-item and security-routing validation, synthetic
imports and command registration pass. Test selection was run. Existing isolated
UI-import fixture limitations and the preceding full-suite evidence remain as
recorded below. SQL statements were checked against the authoritative existing
preparation/resource/execution tables; this slice adds no schema or installed SQL.

Changes review `9ccceb0c-611d-4c94-8a1c-cdbb0d34a5c2` for
`03822d47..2c95c466` reviewed all seven source files and sealed successfully with
no findings; sealed results were read back. The 55-test log-isolation run also
passes with operational logs unchanged. Publication is a stacked draft mirror PR;
no production merge, installation, provider call or live Discord action is implied.

This is a focused recovery workflow, **not P0 completion**. Remaining-stage pipeline
checkpoints, original admission/withdrawal acknowledgement failures, historical
refusals without retained inputs, partial producer results, earlier rollover
failures, and all-copy containment/active-history evidence loss remain active P0
implementation requirements. None is moved to deferred optimisation.

## Lost proposal recovery checkpoint — 2026-10-16

Read-evidence supersession is published as draft Bot PR #350, stacked on the
private-evidence restoration PR #349. The next `codex/guided-proposal-loss` slice
provides the full guided path for a lost or corrupt unactivated proposal receipt:
proactive evidence incident, **Recover replacement**, **Discard unfinished read**
when needed, **Re-enter replacement links**, fresh verification, activation and
retained-input publication. Original approval and read results remain unverified.
Activated evidence cannot use this shortcut; active-history recovery remains P0.

All 15 proposal-loss temporary-SQL tests pass, covering both lost copies, combined
proposal/read loss, restart, stale/foreign confirmation, lost discard replies,
lost discard receipts, earlier damaged receipts, invalid ledger/ownership/mapping,
the actual ephemeral admin button and complete publication. The earlier affected
run had 43 passes and three incorrect exception expectations; those expectations
are corrected in the passing 15-test run. Another 71 admin/recovery/notification
tests pass with operational logs unchanged. Architecture, deferred-item,
security-routing, Ruff, Black, synthetic smoke imports and command registration
pass. The previous 8,115-pass standard suite is retained; this bounded follow-up
uses focused regression validation.

Changes review `91eb0a8b-2355-45a8-9087-9b36b37d8fba` for
`99b4b369..02ba51c4` reviewed all six changed source files. Its draft initially used
an unsupported coverage disposition; the final semantic draft was corrected and
accepted before successful completion on the same scan. The ordinary pending-
discard correctness issue found during review is fixed in `bd9234f6`; correction
review `c23b9241-ed76-4da4-a68b-b27128e8c8c6` covers its one source file. Both scans
sealed successfully with no reported security findings and their results were
read back. No new SQL schema, persistent installation or production/provider
execution was performed. P0 remains active; no recovery workstream is deferred.

Approved 2026-10-15. This is active delivery scope, not deferred optimisation.
The programme remains incomplete until every workstream and acceptance gate below is satisfied.

## Current P0 completion checklist — 2026-10-15

Active implementation checkpoint (**not P0 completion**): the complete output
replacement slice is published as Bot PR #347 / SQL PR #116. The next focused
`codex/guided-config-replacement` slice adds shared configuration/output recovery.

- The admin form identifies configuration workbooks and lists the seven required
  copied input tabs. The read-only check validates owner/sharing, complete bounded
  grid contents, formulas, schema, dates and keys, plus the blank output area.
  Review output links shows tab row counts. Activation requires the admin to
  verify the intended settings and switches configuration reads and report output
  together. Copied input tabs are protected from subsequent report publication.
- Configuration aliases compose through repeated replacement and restart;
  ProcConfig imports, validation, health checks and display metadata resolve the
  active input. Report delivery continues from retained input without repeating
  committed imports. Incomplete reads offer guided discard and fresh verification.
- Temporary SQL tests exercise the full admin path through verified publication
  and a subsequent configuration read, plus lost reads and malformed roles.
  The affected regression run passed 205 tests; another 498-test run covers the
  final configuration cases, runtime contracts, source pins, permissions and Sheets
  regressions. Migration 010 literal bodies and predecessor/postimage hashes match
  the authoritative SQL snapshots. SQL Changes review
  `3235fc22-5123-4607-ae8c-3c29c415c81f` sealed with no findings across all three files;
  measured usage: 1,827,020 total tokens (1,822,389 input, 4,631 output).
  Bot Changes review sealed successfully. Review corrections validate actual
  formatted import tokens, numeric bounds/precision, SQL UTF-16 text lengths,
  camp IDs and ordered scan windows before activation. The current SQL preflight
  checks retained/overlaid ProcConfig values, effective season, exact scan rows,
  official target publication and enabled source period/weight prerequisites.
  Failed prerequisites offer a guided configuration-copy correction and fresh
  check; activation rechecks SQL. Empty optional tabs and blank ProcConfig cells
  explicitly retain existing SQL values, matching the current importer.
  The complete seven-tab populated fixture, guided correction/recheck, changed
  SQL at activation, source checks and affected regressions pass 625 tests.
  The standard baseline run recorded 8,065 passes, 446 skips, one deselection and
  eight subtest passes; its one stale-proposal failure is fixed and covered by the
  passing affected run. The correction Changes review sealed with no findings;
  the final compatibility review also sealed with no findings across its one
  source file (247,530 measured total tokens). The final 85-test run passes,
  including global exemptions and real SQL integer-staging round trips.
  Configuration replacement is published as Bot draft PR #348 / SQL draft PR #117.
  The remaining P0 workstreams below stay active.

- The next active slice adds proactive inventory of private evidence, a second
  encrypted copy, guided exact-byte restoration, and recovery-only startup when
  an activation receipt cannot be read. The admin sees the affected receipt and
  copy verification, confirms restoration, and the bot verifies both saved hashes
  before retrying normal admission. New healthy receipts do not create alerts.
  Damaged ciphertext is retained. Authority and Bot recovery access is independent
  of effective-registration verification; normal writes still require it.
  Temporary SQL tests exercise a real completed activation, delete/corrupt its
  private receipt, restore through the admin service and typed broker, and verify
  the unchanged authenticated chain and unresolved original write history.
  The affected authority, startup, recovery, notification and temporary-SQL suite
  passes 551 tests with one existing skip. Changes review
  `1702f46e-dc04-4d97-97fc-94ef936dcd57` sealed with no findings across nine source
  files. The correction adds reconciliation-proof audit receipts to the inventory
  and registers worker supervision while startup admission is closed. Verified
  repair wakes queued exports without restart. Its 138-test run passes, including
  real temporary SQL proof-audit repair and the repair-to-resume regression.
  Changes review `a9c1e208-56b9-4510-b380-ba3ce057e77f` sealed with no findings
  across all three changed source files. Another 352 runtime/recovery tests pass.
  The selector's unrelated UI-import fixture fails because its constants stub
  omits `PLAYER_STATS_LAST_CACHE`; this slice does not change that import path.
  Synthetic-config import smoke, command registration, architecture, deferred-item,
  security-routing and log-noise checks pass. The broader suite at `6f2189f6`
  passes 8,115 tests with 465 skips, one deselection and eight subtest passes.
  It excludes the scrubbed command-governance workflow fixture and unchanged
  Windows atomic-writer concurrency test already documented above. The final
  correction is covered by the focused runs; code trees match the reviewed
  `f27b7496` correction after cherry-pick.
  Loss of every valid copy, registration-checkpoint recovery, earlier rollover
  phases and refused-stage continuation are still required implementation, not
  deferred optimisations. This slice does not close those acceptance gates.

- Guided saved multi-page admin forms, strict file-link parsing, fresh read-only
  verification, original-journal finish/discard buttons, sealed activation and
  retained-input publication queueing are wired through the Bot and authority.
  Output-link pages and linked replacement/blocker incident buttons are included.
- Registration activation now drains existing export callers without waiting on
  its own recovery call. Concurrent admin activations serialize; shutdown waits
  for admitted recovery work. A changed registration offers guided refreshed
  choices instead of overwriting another completed recovery.
- A second failure during replacement follows the immutable delivery chain:
  the original incident stays open until final publication, exact receipt,
  released ownership and original closed journals verify. Previously queued,
  unstarted exports sharing one complete replacement mapping can follow their
  blocking incident and publish their own retained input.
- SQL migration 009, startup object/permission contracts and application source
  pins are authored. Both 008 and 009 literal procedure postimages and state
  constraints compile and match independent source definitions in temporary SQL.
  No permanent installation or provider operation has run.
- Legacy delivery and complete source-pool replacement now exercise real temporary
  SQL transactions, typed provider requests, private journals and final settlement.
  Provider children are simulated. Lost writes remain linked to a separate repair;
  lost final commit acknowledgements settle from original evidence without replay.
- The saved admin form also passes through the Bot adapter, typed IPC client,
  authority broker, authenticated registration refresh and final private verifier.
  The pipe transport is simulated; this is not Windows peer-authentication or live
  Discord acceptance. Mixed queued legacy destinations compose several authenticated
  mappings while preserving unaffected targets and their existing grid identities.
- Large replacement checks retain the 1,024-file ceiling with explicit bounded
  documents (2 MiB verification plan, 512 KiB enrollment scope, 1 MiB export incident).
  Ordinary probes/imports keep their previous bounds. Read progress is visible;
  progress alone never establishes verification. The migration checks exact trusted
  predecessor and successor constraints as well as procedure bodies.
- A real temporary-SQL source-pool test now drives the guided actions after the
  first replacement also loses a provider-write response. A second verified pool
  publishes the retained intent; both uncertain jobs remain in history, the
  original incident verifies through the chain, and waiting work queues its own
  committed input against the composed mapping. All six source-delivery tests pass.
- Ordinary enrollment excludes only replacement-check preparations matched to
  protected verification records and their plan hashes. Repeated verified or
  discarded checks therefore do not consume new-pool capacity. The related
  capacity, skip and target-admission regression run passed 26 tests. Managed
  enrollment also accepts the intended hyphen in a canonical storage-owner ID.
- SQL Changes reviews sealed successfully for `48676668..2dd649bf` (20 files)
  and its `2dd649bf..9dc3e42b` correction (3 files), with no reported vulnerabilities.
  The Bot base Changes review also sealed successfully. Publication verification
  now binds the original private input commitment to complete closed-journal
  content, including chained replacements, waiting jobs and both source renderers.
  Waiting work carries a private input decision through restart. Reader publication
  records the same final grid-identity checks used by cold recovery. The resulting
  correction's Changes review sealed successfully for `30a57dfb..daae1110`
  (eight source files, no reported vulnerabilities). The focused replacement,
  containment, source publication and guided-admin run passed 470 tests; the
  final private-content run passed 27 tests. A subsequent test-only review
  addition verifies every replacement hop and the root content commitment;
  all five chain tests pass. That inert test/documentation delta requires no
  additional security scan. Architecture, deferred-item and security-routing
  validators, Ruff, command registration and synthetic-config smoke imports pass.
  The standard suite before this correction passed 8,028 tests with 436 skips
  and one explicit deselection. An earlier interrupted run is not counted.
  Its missing containment fixture was corrected; related skip/admission failures
  pass in the sequential focused run. An unchanged
  atomic-writer concurrency test separately produced Windows access-denied and
  remains a documented validation limitation, outside this replacement change.

Required work still inside unknown-write recovery: loss of every valid private
evidence copy, separately verified superseding recovery for those losses,
registration-checkpoint recovery and integrated negative-path acceptance. These are
active acceptance requirements, **not deferred optimisation**. The wider P0
workstreams in the table remain required after this slice.

The chronological sections below retain earlier checkpoints; their historical "still required"
lists are not a count of current work. The current remaining P0 workstreams are:

| Workstream | Remaining acceptance |
| --- | --- |
| Unknown-write replacement | Fresh-file proposal through verified publication is implemented for legacy outputs, configuration workbooks and complete source pools. Finish missing-evidence/superseding paths and integrated negative-path acceptance; isolation alone cannot resolve the incident |
| Earlier rollover failures | Guided decisions and verified continuation for every interrupted phase before the already-covered completed-rollover/retirement paths |
| Remaining producer checkpoints | Atomic completion evidence and safe remaining-stage continuation for all enabled producers, including player stats, configuration imports and stats procedures; explicit partial/unverifiable-output decisions |
| Admission-refused stages | Durable refused-stage identity and exact blocker linkage, proactive discovery, healthy-contention distinction and guided safe continuation without replaying earlier committed work |
| Missing/corrupt evidence | Guided receipt restoration or a separately verified containment/repair outcome; no permanent recheck-only incident, fabricated success or timeout unlock |
| Integrated P0 acceptance | Alert-only entry through admin checks/buttons to verified repair and resumed eligible work, with restart, lost replies, concurrent actions and failure during recovery |

Implemented slices remain draft PRs and have not been deployed. The common incident/action
framework, verified read-only automatic release, several guided read/capture/export recoveries
and permanent target fencing are implemented. Containment is in
[Bot PR 346](https://github.com/cwatts6/K98-bot-mirror/pull/346) and
[SQL PR 115](https://github.com/cwatts6/K98-bot-SQL-Server/pull/115); their Changes reviews sealed
successfully. P0 is not at final polish, and no workstream above is deferred optimisation.

## Required packages

| Package | Priority | Status | Acceptance |
| --- | --- | --- | --- |
| Durable incidents and guided actions; SQL import settlement vertical | P0 | Draft Bot PR 331 / SQL PR 108 | Proactive discovery, persistent alert entry, fresh authorised preview/confirm, durable action identity, postcondition verification; restart/concurrency tests |
| Contested access and abandoned read ownership | P0 | Draft Bot PR 332 / SQL PR 109; incomplete-journal/closure paths still required | Proven-safe automatic release, exact-owner fencing, incident buttons, eligible work resumes |
| Unknown spreadsheet writes, exports and rollover | P0 | Guided verified-outcome slice implementing; unknown-mutation containment still required | Mutation-specific reconciliation, verified completion/continuation or guided containment, no blind replay or unsafe unlock |
| Committed import checkpoint/capture and partial processing | P0 | Draft Bot PR 333; all-KVK/missing-output paths still required | Resume remaining stages without replaying committed import; explicit partial-result choice |
| Discord deliveries and domain publication | P1 | Required | Existing-post reconciliation, guided missing-post repair, expired-reminder policy; Ark/MGE/voting/calendar coverage |
| Files, archives, caches and queues | P1 | Required | Identity-checked continuation, conflicting-file preservation, no duplicate timeout fallback |
| Monitor health, outage recovery and complete write inventory | P1 | Required | Independent outage detection, guided host recovery, every enabled write path classified and covered |
| Integrated acceptance and deployment verification | Release gate | Required | Admin begins with alert only; no IDs, commands or SQL needed; verified outcomes and resumed eligible work |

## Common contract

Persist the incident, evidence revision, action intent, execution outcome and audit history.
Permissions and current evidence must be checked on every action. A confirmation authorises
a decision; it cannot prove an old remote writer has stopped. Never release by timeout alone.
An uncertain repair must be reconciled through its original action identity, never replayed.
Acknowledgement, snooze and ownership release are not proof that business work completed.
Alerts must survive restarts, support deleted-message repair and retain unresolved incidents.

Target detection: within 60 seconds of observing uncertainty or an operation-specific stall
threshold while dependencies are healthy; no subsequent job is needed to discover failure.

## Required validation

Inject failure before dispatch, after remote success, after SQL commit and during recovery.
Exercise restart, simultaneous clicks/admins, stale evidence, revoked permissions, deleted
alerts, missing/corrupt receipts, partial output, external edits and live old writers.
Run focused tests, architecture/deferred/security-routing validators, test selection,
command registration and import smoke. Separate Bot and SQL Changes reviews, Deep off.
Validate actual SQL transactions on a disposable target before deployment acceptance.

## Delivery boundary

Implementation and focused mirror/SQL PRs are authorised. Production merge, SQL installation,
deployment and provider operations are not performed by this implementation task.
Preserve existing reader/updater work in the original checkout. New work uses isolated branches.
Any newly discovered recovery gap in these categories remains required programme work.

## Current evidence and remaining P0 work

The first slice is published as [Bot PR 331](https://github.com/cwatts6/K98-bot-mirror/pull/331)
and [SQL PR 108](https://github.com/cwatts6/K98-bot-SQL-Server/pull/108). Its clean full suite
passed 7,717 tests, with 113 skipped and one existing scrubbed-mirror failure for the absent
command-governance workflow. Production installation and integrated acceptance remain open.

The next slice provides authority-derived investigation and guided release for closed abandoned
configuration reads, including after authority restart. On 2026-10-15 the operator explicitly
approved automatic release when the authority verifies the complete private journal, read-only
requests, closed child and exact ownership. The monitor uses the same durable action intent and
verified settlement as the admin button. This approval does not cover unknown writes or
unverifiable history. Normal contention remains amber/deferred in health displays, and repeated
health checks share their retained operation rather than abandoning it at the UI timeout.

Still required in P0: incomplete journal/closure recovery, unknown provider-write reconciliation
or verified containment, export/rollover guidance, committed SQL checkpoint/capture continuation,
and proof that eligible queued work resumes. A held incident with only a recheck button does
not satisfy programme completion. These are required implementation packages, not optimisation.

The committed stats-import continuation adds a guided **Finish capture & queue export**
action. It requires the original completion receipt, original registered configuration,
exact retained reservation and both SQL session guards. Adoption increments preparation
and resource versions while preserving the import receipt. A durable action marker lets
the same repair continue after checkpoint, spool, capture-receipt or queue-acknowledgement
loss. Complete output hashes cannot be replaced. Resolution requires verified retained
bytes and idempotent queue admission; provider delivery remains a distinct incident.
Temporary-table engine tests cover those interruption points, active original sessions,
stale claims and changed output. All-KVK generation recovery and unverifiable or missing
output still require their guided workflows before the programme can be complete.

## Focused publication and export recovery checkpoint

The read slice is [Bot PR 332](https://github.com/cwatts6/K98-bot-mirror/pull/332)
and [SQL PR 109](https://github.com/cwatts6/K98-bot-SQL-Server/pull/109).
The committed scan-data capture slice is
[Bot PR 333](https://github.com/cwatts6/K98-bot-mirror/pull/333). Its full suite passed
7,799 tests, with 113 skipped and the same existing absent command-governance workflow
failure. Both final Changes reviews are sealed and read back; the draft-schema finalization
error was corrected on the original scan without replacing it.

The next focused export slice connects account/storage/registered-pool scoped discovery to
the existing recovery centre. It provides pre-attempt retry, authority-verified publication
settlement, verified interrupted-retirement continuation, completed-rollover settlement and
proven-damage rebuild. Each uses durable action identity, fresh registration and evidence,
existing exact-version SQL transitions and independent receipt verification. A queued repair
resolves repair admission only; its delivery remains separately monitored. Existing unknown
mutation proofs cannot be overridden by a button or admin assertion. No new persistent SQL
objects are introduced in this slice; authoritative schemas are used in temporary-table tests.

That export slice is now [Bot PR 334](https://github.com/cwatts6/K98-bot-mirror/pull/334).
Its exact Changes review covered all five changed source files with no findings and was
sealed/read back successfully. Its focused suite passed 197 tests; its full suite passed
7,816 tests with 113 skipped and the same baseline missing-workflow failure.

The closure slice, [Bot PR 335](https://github.com/cwatts6/K98-bot-mirror/pull/335), retains positive exact-child termination evidence and its immutable
closure receipt across local acknowledgement/storage failures. It re-reads the exact session,
child, account, frozen version and sealed journal before finishing closure. Configuration
discovery can finish an already interrupted owned read; registered proof requests can finish
only the matching job/rollover's interrupted locally owned children. Healthy streams are not
interrupted, old-session children are not adopted, and no provider request is replayed. Closed
streams still need the independent complete-journal and operation-specific settlement proofs.
Recovery after losing the entire authority process before durable closure, and incomplete
read-terminal journals, remain required P0 work in the subsequent focused slice.

The read-journal slice accepts only complete sealed historical probe prefixes consisting of
`prepared`, or `prepared` then `dispatch_intent`, as abandoned reads. All immutable request
identities, private payload/event bytes, sequence membership, closure and registration still
verify. The same prefixes remain forbidden as fresh provider observations or mutation proof.
An additive SQL migration makes the historical catalogue gate agree with the private verifier,
so a recovered failed read cannot poison the next independent reconciliation. Bot and SQL must
be deployed together with refreshed protected source/installation pins. Temporary SQL tests
execute the migration's actual predicate and procedure postimage; no persistent objects are
installed. Missing/corrupt private bytes and unproven old-session closure remain separately
required recovery paths, along with the unknown-write and P1 packages above.

Still required before P0 completion: legacy unknown writes, absent attempted-publication retry,
damaged-index/unknown-write containment and registration replacement, earlier rollover phases,
incomplete private journal/child closure recovery, all-KVK generation and missing/unverifiable
output. P1 and integrated alert-to-resolution acceptance also remain required. These entries
are implementation obligations, not deferred optimisation or claims of completed coverage.

## All-KVK capture and retained queue admission

The next focused slice resumes all-KVK capture only from the atomic completion checkpoint
written by KVK ingest/recompute or KVK recompute. It rechecks original configuration and season,
exclusive SQL producer exclusion, exact retained reservation, immutable completed output hashes
and the original recovery action. The shared capture implementation preserves checkpoints and
reconciles lost acknowledgements without rerunning SQL producers.

Both all-KVK and stats captures stranded before queue admission are independently discovered.
The recovery centre offers **Queue verified capture** with a confirmation checklist. Inspection
is read-only; only a durable confirmed action can admit that snapshot to the queue. Its
idempotent job link and retained bytes are verified before resolution. Stale confirmation,
foreign storage/account, changed output, active original producer and lost queue acknowledgement
are covered by focused tests and actual temporary SQL transactions.

Security routing: Changes review of this focused branch against `e4eacf39`, Deep off,
covering SQL fencing, storage/account scope, retained file verification, admin confirmation
and restart persistence. The authoritative ExportPreparation and ExportResource definitions
were checked in the SQL source repository; this slice introduces no persistent SQL objects.
Missing checkpoints, unverifiable output and all other remaining programme workflows above
remain required implementation work. This slice does not claim full recovery completion.

The capture/queue slice is [Bot PR 337](https://github.com/cwatts6/K98-bot-mirror/pull/337).
336 affected tests and 74 log-isolation tests passed, including temporary SQL fault cases;
the exact eight-source Changes review is sealed with no findings. Full-suite validation
continues separately and is recorded in the PR.

## Verified absent-publication retry

An attempted new-source export settled as absent keeps its original failed attempt and
quarantined parts. The recovery centre now offers **Retry verified absent export**:
admin confirmation requests a fresh authority probe, complete closed journal verification
with no dispatched mutation, current absence, original retained input and safe capacity.
Only then can one separate RepairID export be admitted. The original attempt is never reset.
Lost admission acknowledgements resolve from that exact repair receipt. Unknown writes
remain in the distinct containment/reconciliation scope; they cannot use this action.

The coordinated SQL change allows failed jobs to enter a read-only probe. Mutation admission
stays running-only. The migration pins the exact installed predecessor/postimage and retains
session, resource, ownership, membership and role checks. Bot source pins and updater
transitions change with it. The action preserves existing quarantine rather than inventing
a replacement history.

During this review, the stream-close SQL gate was found to reject unfinished read prefixes
before the private verifier can evaluate them. Completing that close gate with exact positive
child closure and read-only membership is the next required focused P0 correction. It is
distinct from missing/corrupt private evidence and lost-authority-process recovery, which
remain required. No recheck-only path is considered completed programme coverage.

## Read-prefix closure correction

The SQL close gate now permits a preserved nonterminal request only when the persisted
stream purpose is `probe`, its request kind is `read`, and its history contains `prepared`
with no events outside `prepared`/`dispatch_intent`. Missing events, mutation requests and
other purposes remain blocked. The unchanged exact session/account/child/version/sequence
CAS and authority-derived positive child termination still govern closure. The independent
private verifier then checks complete bytes and ordering before any configuration release.
No terminal event is fabricated, and an unfinished read cannot count as a fresh observation.

Migration `20261015_005_read_prefix_closure.sql` follows the failed-publication probe migration,
pins the whole predecessor/postimage, refuses unexpected signatures and preserves roles.
Coordinated Bot source pins must be deployed with it. Actual temporary SQL tests exercise the
close predicate, unchanged history, all closure CAS dimensions and installed module hash.
Separate Bot/SQL Changes reviews use the focused `guided-read-close` branches, Deep off.
No persistent SQL installation or provider operation is part of these tests.

This closes the read-prefix SQL/verifier mismatch only. Whole-authority process loss,
unverifiable evidence, unknown-write containment and the other required P0/P1 workflows
remain active programme obligations, with guided actions and verification required throughout.

## Failed-publication probe request admission

The follow-through review found that request prepare/dispatch still used the older job-state
allowlist after stream-open admitted a failed-job probe. Migration
`20261015_006_failed_probe_request_events.sql` aligns that read-only probe gate with stream-open.
Mutation admission remains running-only; probe preparation still rejects mutation requests.
Both gates retain exact owner, account, fence, version, epoch, nested action and membership
checks. The migration pins the actual manual-public-viewer predecessor, not an earlier
installation body, and refreshes the paired Bot source pins.

Temporary SQL tests now exercise both admission gates across the same state matrix and all
job-ownership dimensions, plus probe mutation rejection and exact compiled postimages.
Separate Changes reviews cover the focused Bot and SQL `guided-probe-events` branches.
This is required completion of the verified-absence button's probe path, not a new recovery
policy or permission to replay unknown writes. All remaining P0/P1 obligations stay active.

## Committed capture with unavailable output

Stats and all-KVK incidents now offer **Keep SQL; skip this export** alongside capture/queue
continuation. The confirmation states that committed SQL data is preserved and the spreadsheet
may remain out of date. The repair excludes active producers, checks the original completed
checkpoint and exact account/storage/owner/fence/version, refuses any queued job or associated
provider stream, and atomically marks only the unqueued preparation unavailable and releases
its exact SQL snapshot reservation. Original requests, execution receipts, generation hashes
and spool references remain intact. Resolution explicitly reports `export_skipped`.

A deterministic local output/format failure during a capture repair records a durable failure
checkpoint under the same producer guards. That fences the old action and exposes the next
guided decision rather than leaving it perpetually pending. SQL timeouts and unknown queue
commits are not classified as safe failure. A queued export cannot use this action.

Tests cover the full failed-capture to confirmed-skip flow, lost acknowledgement, later
unowned reservation, stale/foreign scope, active SQL work, provider evidence and retained
spool preservation for both consumers. The existing confirmation view displays KVK season.
This branch requires a Bot Changes review, Deep off; no SQL schema delta is needed because
the authoritative preparation, resource and execution contracts already represent this
state. Missing atomic checkpoints, queued corrupt exports and unknown provider writes retain
their separate required workflows; no programme completion or deferral is claimed.

The committed-capture decision is [Bot PR 341](https://github.com/cwatts6/K98-bot-mirror/pull/341).
Its nine-source Changes review is sealed with no findings. The broad run passed 7,843 tests
with 250 optional/platform skips and eight subtests; the only failure is the existing absent
mirror workflow. The final queue fences passed a separate 205-test affected run.

## Queued legacy export without provider execution

Stats and all-KVK export incidents offer **Keep SQL; skip queued export** when no attempt or
execution stream exists. This includes missing/corrupt retained input and a worker interrupted
before provider execution. The guided confirmation explicitly accepts no spreadsheet update.
The account/resource transaction rechecks custody, immutable destination membership, exact
job version and complete absence of provider evidence. It fences the old worker, releases
only reservations still owned by that exact job and preserves the job, input and audit history.
It never changes another owner's reservation. Confirmed skip receipts cannot request or admit
a later retry of the same job. The monitor verifies the original decision after lost replies.

Actual temporary SQL tests cover both consumers, lost acknowledgement, stale/foreign inputs,
attempt/stream rejection, mismatched ownership, a later owner's preserved reservation, old
worker rejection and successful admission of later eligible work. Discord tests verify that
the button opens an ephemeral checklist and confirmation before any action executes.
The existing coordinator, scoped discovery and recovery confirmation are reused; no new
command, cache or persistent SQL object is needed. Changes security review, Deep off, covers
this focused branch against `249e9665`. Existing authoritative ExportJob, ExportAttempt,
ExportResource, ExportJobResource, ExportExecutionStream and SourceDelivery contracts apply.

This closes the no-provider-execution queued-input case only. Attempted legacy writes,
unknown-write containment, missing authority evidence, earlier rollover stages and every P1
workflow remain required active scope; the programme cannot be marked complete yet.

The no-attempt queue decision is [Bot PR 342](https://github.com/cwatts6/K98-bot-mirror/pull/342).
297 affected/log-isolation tests passed, including actual temporary SQL. Its three-source
Changes review is sealed with no findings. The isolated UI-import fixture also fails on the
unchanged parent because of its incomplete constants stub; import smoke passes.

## Configuration read closure after authority-process loss

Published as [Bot PR 343](https://github.com/cwatts6/K98-bot-mirror/pull/343), stacked
on PR 342. Runtime and updater Changes reviews are sealed with no security findings.
974 affected/log-isolation tests passed, one optional skip; 174 updater tests passed.
The broad run passed 7,869 tests, 263 skips and eight subtests. Its outdated Windows
test double was corrected and a 52-test rerun passed; the known absent mirror workflow
is unrelated. This is source validation, not deployed recovery.

New Windows provider children use a unique, private global job name with a non-inheritable
authority-only handle, kill-on-close and no breakaway. For configuration-read streams the
authority encrypts and verifies the exact child/job/host/session birth record before SQL
admission and child resume; SQL retains only its private reference and hash in ScopeJson.
Caller-supplied birth fields are rejected. Existing enrollment and mutation scope contracts
remain unchanged.

After an authority restart, discovery can finish closure of an old-session read only from
that exact private birth and a same-host job observation. A live job, changed containment,
access-denied or other lookup error cannot establish retirement. Windows job destruction
requires all associated processes to have terminated; an existing job must have zero active
processes. Closure records this distinct observation method without fabricating a process-
handle wait. Exact old session/child/version/sequence SQL CAS remains mandatory. No provider
request is replayed, no live process is adopted or killed by recovery, and closure alone
does not release ownership. Complete private-journal verification and the durable recovery
action still precede the approved automatic read release and independent postcondition read.

References: [Windows job lifecycle](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[named-job open](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-openjobobjectw),
[global namespace](https://learn.microsoft.com/en-us/windows/win32/termserv/kernel-object-namespaces).
Tests cover lost freeze/close replies, foreign/corrupt birth, live job refusal, private closure
binding and restart-to-incident-to-verified automatic release. A disposable suspended local
test child exercises actual Windows live/empty/destroyed observations; no provider child,
credentials or existing process is used. Existing SQL stream/session/scope contracts were
validated; the previously required read-prefix close migration remains necessary.

Older streams without a bound birth and missing/corrupt private evidence still require the
programme's guided containment workflow. Unknown writes, earlier rollover stages and P1
work remain required, with no deferral or claim that this slice completes the programme.

## Guided containment of older configuration reads

The next paired Bot/SQL slice adds **Isolate read & release** when historical private
closure cannot verify but the complete typed SQL request ledger proves a configuration
read. The existing alert opens an ephemeral checklist and a separate confirmation.
It explicitly explains that a previously dispatched read may still finish and that its
result will be discarded. This action never runs under the automatic-release policy.

The authority reconstructs account, registration, storage, preparation, owner, fence,
versions and complete resource/stream membership. It seals the current typed read ledger
and original snapshot in private storage. One SQL transaction compares the entire snapshot,
changes the exact streams to `read_contained`, marks the preparation unavailable and
releases only its exact reservations. Any failure rolls back every fence and release.
The private receipt and SQL audit preserve original closure hashes, request events and
ownership. Late prepare, dispatch and terminal-result events are rejected after containment.
No request replay, child-termination assertion or provider-health assertion is introduced.

Historical catalogue verification accepts this distinct sealed no-write coverage; fresh
observational proofs still require a genuinely closed successful probe. SQL proof issuance
and consumption agree with that distinction. Verification after a lost reply reads the
committed preparation, exact receipt and every contained stream before resolving the incident.
An unrelated owner, enrollment, mutation, incomplete typed ledger or changed evidence cannot
use this action. Existing normal closed-read release and automatic policy remain separate.

Migration `20261015_007_read_dispatch_containment` follows the reviewed recovery module
chain through 006. It compares trusted predecessor/postimage definitions and rolls back
constraint/module updates together. The Bot source manifest and protected updater transition
must move with it. Installation and production permission proofs remain deployment gates;
tests use only temporary SQL objects and do not install the migration or change roles.

Acceptance covers guided confirmation, no automatic isolation, missing historical private
bytes, complete read prefixes, same-transaction rollback, stale/foreign scope, lost replies,
immutable history, historical catalogue inclusion, rejection as a fresh observation and
late child-event refusal. Unknown-write target containment, missing typed SQL evidence,
remaining producer checkpoints, earlier rollover phases and every P1 recovery obligation
are still required delivery scope. This paired slice does not close the programme.

Published as [Bot PR 344](https://github.com/cwatts6/K98-bot-mirror/pull/344) and
[SQL PR 114](https://github.com/cwatts6/K98-bot-SQL-Server/pull/114). All three Changes
reviews (Bot, SQL and the private-I/O correction) finalized successfully and were read back;
no security findings remain in those reviewed ranges. The affected suite passed 1,216 tests
with one skip and unchanged operational logs; 18 temporary SQL tests passed. The broad run
passed 7,888 tests, 281 skips and eight subtests; only the known absent mirror workflow failed.
The final private-I/O correction passed 201 targeted tests. Hash and Windows decryption
failures now deny private verification without preventing an independent guided typed-read
containment decision. SQL errors remain outside that normalization boundary.

## Configuration claim interrupted before execution

The next focused Bot slice offers **Cancel unstarted read** when a canonical configuration
read claimed reservations but has no stream, request or event. It requires the complete exact
account/storage/resource/owner/fence/version snapshot and excludes enrollment or ambiguous
request identities. Cancellation is an explicit durable admin action, never automatic.
The existing recovery transaction fences the original preparation and releases reservations
together. It rechecks absence of execution under the same admission locks; a concurrent
stream causes the whole action to fail. The cancelled old claim cannot later open a stream.

The authority verifies the whole committed private receipt even when there are no stream
rows, and resolves lost acknowledgements from that exact receipt. The confirmation explains
that no provider execution occurred. Existing read containment and closed-read automatic
release retain their separate semantics. No SQL schema or permission change is introduced;
the authoritative preparation, resource and stream admission contracts were validated against
the paired SQL source. Temporary SQL tests exercise cancellation, late-open rejection,
concurrent stream appearance and complete rollback; Discord tests exercise the actual button.
Changes review is required against Bot `d18716e9`, Deep off.

Unknown-write containment, corrupted/missing typed history, receipt restoration, remaining
producer checkpoints, earlier rollover phases and P1 workflows remain required work. These
are active programme obligations; this slice is not programme completion or a deferral.

The unstarted-read slice is [Bot PR 345](https://github.com/cwatts6/K98-bot-mirror/pull/345).
468 affected/log-isolation tests passed, including actual temporary SQL; its five-source
Changes review finalized with no findings and was read back successfully.

## Account-admission refusal is required recovery scope

The reported `SQL execution failed: Writer unavailable: account admission refused before
execution` comes from `LegacyExportRuntime.begin_writer` after up to 60 seconds of
acknowledged admission refusals and successful withdrawal of that unstarted ticket. It
does not establish that this writer executed SQL, or that the blocking owner is abandoned.
The outer SQL-failure wording must distinguish admission refusal from execution uncertainty.

Acceptance requires retaining and showing the refused stage's identity, linking its exact
blocking reservation or older ticket to the relevant recovery incident, distinguishing healthy
active contention from stranded/uncertain ownership, and detecting the blocker independently
of the next failed process. Guided repair must verify the blocker and safe continuation of the
affected stage. No automatic replay of an earlier committed import is permitted. Configuration
read recovery in PRs 332–345 addresses some blockers; this complete refused-work workflow is
not yet implemented and remains required P0 work, including refusal/withdrawal acknowledgement
loss and producer paths without atomic checkpoints.

## Unknown-write containment implementation boundary

Unknown writes cannot be made safe by a timeout, a current readback or an admin assertion.
The next paired implementation must permanently fence the entire verified possible target set,
preserve original request/ownership history, logically retire its streams without claiming
process termination, and release only exact held ownership in the same transaction. All future
mutation admission must consult that permanent target fence, including a changed account or
new job. A retired target must not become reusable through rollover, retry or registration.

The guided action must name the affected outputs, explain that a delayed old write can still
change them, obtain confirmation, verify the permanent fence and retained receipt, and show
replacement/continuation progress. Target retirement alone must not mark the business export
delivered or the overall recovery resolved. Replacement registration, queued-work migration,
fresh publication verification and admission-refusal linkage remain part of this implementation,
including legacy fixed targets, new-source indexes/slots and rollover. Temporary SQL and fault
tests must prove the dispatch fence, stale clicks, lost commits, other-owner preservation and
successful work on verified replacement targets before programme completion.

### Current unpublished target-containment work

The paired `codex/guided-write-containment` worktrees contain an unfinished implementation,
not a deployable recovery workflow. The SQL prototype preserves the unknown provider ledger,
permanently fences the complete physical target set across accounts, logically isolates its
streams, and releases only the exact job owner in one transaction. New-source pool isolation
requires exact season, epoch, registration, pool version and complete slot membership. Original
slot history remains unchanged. The authority service reconstructs the installed scope, seals
the decision privately, compares the locked snapshot, and verifies the original receipt after
commit or a lost reply. It explicitly keeps `business_resolved=false`.

Thirty session-local SQL cases and sixteen authority/DAL integration cases passed during
development. They cover strict JSON shapes, stale/foreign confirmation, preserved unknown
events, late child refusal, global target fencing, rollback, later unrelated stream admission,
lost acknowledgements and changed/missing postconditions. These are temporary-object tests,
not production installation or provider acceptance. The final affected rerun, including the
pool postcondition check and slot-count guard, passed all 46 tests with unchanged operational
logs; lint passed for the four new Python files.

Migration 008, permission/source pins and bounded authority RPC are now implemented locally.
Actual temporary SQL validates the literal migration procedure definitions and stream-state
constraint against the checked-in snapshots; installation and role permissions remain separate
deployment checks. The migration has not been installed into a persistent database.

Queue admission excludes jobs with permanently isolated targets, including safe-retry jobs and
another account using the same physical file. A second check after sorted resource locks rejects
a stale candidate list. Legacy writer and rollover queue fairness ignore those ineligible jobs;
healthy older work retains its priority. Inputs, tickets and old jobs remain unchanged. Recovery
discovery immediately includes affected queued jobs, without waiting for age or a failed execution.
An ordinary retry cannot close their incidents or bypass the replacement requirement. Existing
explicit skip of an unstarted legacy export still requires its original evidence-bound checks.

Whole-pool authority tests now verify original slot history, exact pool state and lost replies.
The publication catalogue already selects exact physical destination history: a retired file's
history does not enter an unrelated file's catalogue. A temporary SQL regression exercises this
boundary without relaxing historical evidence or declaring an isolated writer terminated.

The 768-test affected run passed. The full suite recorded 7,922 passes, 342 skips and eight
subtest passes; two stale test assertions were then corrected (source inventory count and
private-evidence error wording). The final 117-test focused rerun passed, including a new
SQL-compiled comparison of the immutable migration 007 predecessor and migration 008
postcondition. It caught and fixed a generated predecessor check that wrongly used the new
constraint for both images. The remaining full-suite failure is the pre-existing missing
`.github/workflows/command-governance.yml` in the scrubbed mirror. No production logs changed.

Separate Changes reviews finalized and their sealed artifacts were read back: Bot
`a8d5c130-2a45-4185-b560-b11b2fbb4d21` (16 source files, `bef9b5a3..f5bebc17`), SQL
`b943ba88-45ea-410b-b314-224bf4e8fd9b` (10 source files, `79987f7b..5078b513`) and the
one-line migration correction `fc11619b-7fbb-4cd3-90fa-e8137b5f83a0`
(`5078b513..48676668`). No security findings were reported. The Bot follow-up changes only
regression tests and this evidence record; a further security discovery scan is skipped because
they do not alter executable application, authority, permissions, SQL or deployment behavior.

The complete guided workflow remains active implementation scope: replacement enrollment and
registration, retained-input continuation, fresh publication verification, guided UI wiring,
refused-stage linkage and continuation, and earlier rollover owners. The remaining P0/P1
workflows also remain required. No containment button is exposed before its replacement workflow
is implemented; target isolation alone cannot resolve an unknown-write business outcome.

### Replacement workflow in progress

The unpublished `codex/guided-target-replacement` branches now contain deterministic
destination-only registration proposals, authority-private proposal receipts and immutable
SQL proposal/mapping records. Lost SQL replies are resolved by reading the original receipt;
proposals explicitly remain unverified, inactive and business-unresolved. Projection tests
preserve queries, audience, reader bindings, unrelated pools and original registration bytes.

The manual enrollment SQL path now recognizes an exact stored replacement proposal for one
isolated pool. It verifies complete index/slot order, owner and audience before allowing fresh
read-only enrollment despite the original isolated job remaining uncertain. Healthy queued
work retains priority, ordinary enrollment retains its guards, and old files stay fenced.
Engine testing also found and corrected the manual enrollment storage-owner pattern so its
Unicode JSON validation accepts hyphens consistently with Python.

This is an implementation checkpoint, not a PR-ready workflow. Provider verification orchestration,
failed-verification recovery, activation/registration history, retained-input publication and
guided admin input/buttons remain unfinished in this branch. The new SQL objects and procedure
changes still need a literal migration, source/permission pins and separate final Changes reviews.
No provider calls, persistent SQL installation, production deployment or admin action exposure
has occurred. The six current P0 workstreams remain open.
# Lost replacement-read evidence delivery — 2026-10-15

The `codex/guided-evidence-loss` slice adds proactive evidence incidents with a
**Recover replacement check** button. For an unactivated replacement whose complete
typed read ledger is settled and owns no reservations, the guided workflow offers
**Run fresh read check**, then the existing verified activation and retained-input
publication actions. Lost receipts remain unverified; a new complete private
readback is required. Evidence already used by an activation cannot use this path.

Validation: 44 affected temporary-SQL tests, three additional ownership/activation/
confirmation cases and 71 admin/recovery/notification tests passed. Architecture,
deferred-item, security-routing, lint, formatting, test selection, synthetic smoke
imports and command registration passed. Operational log files were unchanged.
The previous standard-suite checkpoint remains 8,115 passes; it was not repeated
for this bounded follow-up. The separately recorded isolated UI-import fixture
failure is unrelated and unchanged.

Changes review `ba065c03-d438-4cb7-b04a-06b5210fd2ca` finalized successfully for
`7fd1b17f..dfc3b52d`: all six source files reviewed, no reported findings, Deep off.
The sealed artifacts were read back. This also confirms the review finalization
path works. No persistent SQL installation or production/provider operation ran.

P0 remains open. Lost proposal, containment and active registration-history
evidence, earlier rollover phases, producer checkpoints and admission-refused
continuation remain required implementation work, not deferred optimisations.

