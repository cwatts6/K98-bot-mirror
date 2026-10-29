# MGE finalisation and shared board lifecycle — 29 October 2026

Current authority: approved bounded local MGE implementation, shared design and
second-domain validation, plus documentation reconciliation. Do not ask for the
same direction again. PR publication, merge, SQL execution, updater qualification,
production deployment and live acceptance remain separate. Local implementation
and offline validation are complete, with the full-suite/focused-rerun distinction
below. Native SQL and exact updater qualification still gate release readiness.

Read the [A1b deployed closeout](P1%20MGE%20A1b%20-%20Deployed%20Closeout%20-%202026-10-29.md)
for accepted delivery and residual evidence. This pack is the focused source of
truth; the [A2 scope](P1%20Batch%20A%20Remaining%20Discord%20Domain%20-%20Scope%20-%202026-10-28.md)
owns subsequent domain adoption.

## Scope and architecture

MGE signups begin roughly seven days before an event. Ranks and targets remain
changeable during the six-day event; preserve the existing automatic completion
boundary `StartUtc + 6 days`, rather than silently substituting calendar `EndUtc`.
An explicit admin completion freezes sooner by existing operator intent. Final
results and summaries remain available independently of the historical boards.

Separate domain state, final-delivery state and retirement. Domain completion
freezes mutable event/signup/award data and atomically captures all existing public,
leadership and awards identities. Pending boards have one generation UUID,
publication version and rowversion-qualified settlement. An immutable JSON payload
is saved before the first final edit. A confirmed edit is terminal. Cancellation
and restart retain the original identity and intent. A lost acknowledgement
permits readback reconciliation only; mismatched unknown edits become held.
Missing messages and inaccessible messages have distinct held reasons. Neither
permits replacement. Retirement retains messages, results, receipts and audits.

Existing completed events without final-delivery records are **legacy frozen**.
They receive zero routine Discord fetch/edit work and are not described as newly
confirmed final deliveries. Historical cleanup requires a separately reviewed
inventory/disposition. No age cutoff grants deletion or retry authority.

| Layer | Responsibility |
|---|---|
| `core/board_lifecycle.py` | Small pure eligibility contract, including ended/awaiting result versus domain final; no scheduler, IO or domain rules |
| `mge/mge_completion_service.py` | Existing MGE completion rules; reject stale reopening |
| MGE completion/finalisation DAL | Atomic status/identity inventory; qualified target reads; generation/version/identity/rowversion settlement |
| `mge/mge_finalisation.py` | Discord final-edit adapter, immutable payload capture, unknown readback, exact retirement preview and owned delivery |
| Existing presentation owner / refresh coordinator / `drain_thread` | Serialize refresh, publication identity and completion; preserve cancellation/drain custody |
| Scheduler/recovery | Active ordinary inventory plus distinct unfinished finalisation inventory; never sweep all completed history |
| Existing admin completion view | Complete, check final delivery, preview and confirm exact retirement; admin/actor checks remain at confirmation |
| SQL freeze triggers | Authoritative rejection of stale event/signup/award writes after completion, including legacy and hidden placement writers |

Source verification corrected the handover: `/mge admin_completion` and an existing
Complete/Reopen view already exist. The follow-up updates that surface; it does not
add a second completion command. Reopen/unpublish cannot thaw completed history.
Final boards remove mutation controls; read-only reports remain independently
available. Completed SQL state rejects stale controls retained on legacy messages.

The process presentation owner is not cross-process Discord ownership. SQL freeze
guards serialize domain completion with writers, but do not make legacy multi-call
roster actions atomic. R12 and broader receipt adoption remain separate. The
existing single-bot deployment invariant is required for IO serialization.

## SQL and release contract

Bot implementation review target: mirror base
`139038e416c657cb589f24ca8a4ff61a913b7a3b` through
`c299d64e9f1f1e69e0e013d88616ce027bf9abb2`. SQL implementation review target:
`7e91989f619deb46836194c7e705b0a9eb2ebe11` through
`d649d6d659a586939e6566dd48c1ece6d3310e9a`. Both are separate local commits on
`codex/mge-board-finalisation`; neither has been published. Original design and
production checkouts remain unchanged. The subsequent closeout retains those
reviewed targets and records its narrowly bounded message/test/documentation delta
below; it must not be described as the original sealed scan target.

Authoritative SQL base: `7e91989f619deb46836194c7e705b0a9eb2ebe11`.
Validated event fields, status constraint, original identity columns and publication
version against `dbo.MGE_Events`; signup/award tables and final-result imports are
separate. No ProcConfig, UDT or result-import schema change is required.

Add `dbo.MGE_BoardFinalisation`, supporting state/EventId index and three completed
history triggers. Completion plus target capture must share one non-autocommit
transaction. No historical backfill, age deletion or provider operation is part of
the migration. Partial saved identity pairs must be held explicitly, never treated
as authority to send. SQL source and bot source have separate Changes targets.

The SQL review identified a compatibility requirement: enabled INSERT triggers
reject bare `OUTPUT INSERTED` in the existing signup and award writers. Those
writers, plus the affected event rules UPDATE, now use `OUTPUT INTO` and a final
SELECT. Their fake-transport regressions pass; native driver/trigger qualification
is still required. The companion SQL review predates this bot correction and its
original open question must be read with the later bot source evidence.

This requires a coordinated drained rollout: qualify the migration and concurrency
on a separately authorized disposable database; review both diffs; drain the old
bot; apply SQL; install the exact qualified new bot; restart using the protected
updater. The old bot still edits historical boards before persisting IDs, so an
unattended SQL-first rollout while it runs is unsafe. Do not drop receipts/guards
or restore the old historical sweep as routine rollback. Preserve frozen state and
use a reviewed forward correction. Exact protected updater source pins are a
release gate, not satisfied by local pytest.

## Second-domain contract and A2 callers

Ark is materially different: match end can precede the result. Ended/awaiting-result
must stop roster refresh while still allowing the authorized result workflow.
Only an accepted result or explicit no-result disposition should trigger a final
results payload. The shared policy expresses this independently of MGE's dates.
The local contract test exercises the real Ark `set_match_result` DAL caller with
a fake SQL transport, then applies the shared policy. This is compatibility evidence,
not Ark runtime adoption or native SQL evidence.

Ark's current Scheduled/Locked inventory can include old matches; expected active
workload of two or three boards is not a cap. Its completion fallback is called
from an already-Completed query; seven-day/timestamp finalisation eligibility can
strand older work and conflate revisions. Registration, confirmation, team boards
and tracked restoration need separate target receipts. `bot.add_view` registers a
handler locally; it does not edit a Discord board or prove visible controls.

Voting/surveys close domain state before final board edits and announcements;
open-only selectors cannot recover those deliveries. Manual close/reopen/delete
must participate in the same explicit generation/identity contract. Unknown
announcements cannot be blindly resent. Calendar's rolling 30-day overview remains
live; event-specific messages, reminders and private responses are different
targets. Broad fetch failures must preserve tracker identity and never imply
deletion/replacement. These are A2 findings, not implemented by this MGE slice.

Ark policy to settle before its implementation: prefer ended/awaiting-result with
no roster refresh, then explicit result finalisation; alternatively permit an
explicit no-result finalisation disposition. Do not add an automatic timeout that
discards late results. Corrections after immutable finalisation require a separately
identified revision/result record, not silent historical board rewriting.

## Validation and acceptance mapping

| Requirement | Local evidence / remaining gate |
|---|---|
| Final delivery versus domain state | Completion transaction construction and retained per-target state tests; native atomicity still requires disposable SQL |
| Repeated restart with zero historical network work | Confirmed/held/retired and ordinary completed-board regression tests count fetch/edit calls |
| Crash before/after edit | Saved payload/unknown readback and mismatch-held tests; no send path |
| Partial success and stale work | Per-target CAS, presentation-owner barriers and versioned retirement; native competing writers remains separate |
| Deleted versus inaccessible | Distinct 404/403 held tests; transient fetch retains identity |
| Stale interactions / retirement | Existing admin permission checks, preview actor and rowversion checks; SQL guards are authoritative |
| Ark late results | Actual Ark DAL caller with fake SQL, domain-neutral policy test; live adoption remains A2 |
| Voting close and calendar continuity | Source caller audit and contract mapping; no claim of fixing their runtime gaps |
| Runtime costs | Count SQL reads, original-message fetch/edit, active/pending/confirmed/held/retired targets; timing alone is insufficient |

The source bridge in `tests/fixtures/p1_mge_finalisation_source_pairs.json` and
`tests/updater_source_assertions.py` authenticates the exact local successor before
walking older test assertions. Tampered code, missing mapping and altered mapping
are rejected. It does not modify the production updater registry or authorize an
installation. Prepare and qualify the exact release inventory separately.

Required repository checks pass: architecture boundaries (24 changed Python
files), deferred-item structure (30 Markdown files), security-routing validation
(zero errors/warnings), import smoke and command registration (36 primary / 102
grouped commands; six MGE commands). Changed-file pre-commit passes, including
lint, formatting, secret scanning and type checking. Initial mixed line endings
were corrected; repository-wide formatting outside the change was not requested.
All 58 introduced local Markdown link targets resolve after the final documentation
edit. The test selector recommends the full suite because test infrastructure changed.

Full offline run: **10,593 passed, 1,100 skipped, eight subtests passed, one failed**
in 1,192.43 seconds. The only failure was the old delivered-source fingerprint in
`test_updater_reader_capabilities`; it still compared current MGE files directly
with A1b's immutable registry. The assertion now uses the authenticated local
successor bridge before comparing the historical fingerprint. No registry entry,
release permission or production source pin changed. The same closeout corrects
only the completed-event reminder refusal text, removing its stale suggestion to
select an explicit event ID.

After those corrections, **239 tests passed** across updater reader capabilities,
finalisation source-bridge tamper checks, A1b transitions, MGE publication and MGE
finalisation. The log-noise wrapper confirmed operational logs unchanged for this
rerun. The full suite was not rerun after this narrow correction; the earlier
failed full run is not relabelled as a fresh all-green run. Its one warning is the
installed Google library's Python 3.11 future-support notice. No unrelated test
failure remains identified. Native SQL, live Discord and Linux execution were not
performed by these Windows offline checks.

Security routing is **Changes, Deep off**, separate bot/SQL targets. SQL scan
`1bb61a7b-905a-43e1-9cbb-3d57be134c0c` completed with zero findings and all five
changed SQL source files plus the companion document accounted for. Native SQL
execution remains explicitly outside its static coverage. Bot scan
`eaf3b342-16dc-4dd2-9b2c-3b76ad82bbd9` completed with zero findings: all 14 runtime
files, 10 tests/fixtures and 27 documentation files are accounted for, with no
deferred security candidates. Its sealed target is the exact bot range above.
The post-scan delta was inspected separately: documentation/runbook clarification,
one rejection-message literal in `mge_publish_service.py`, the exact test-only
successor hash and its helper digest, and the historical updater assertion above.
Additional security discovery is skipped for that delta: no condition, permission,
input handling, SQL, network call, deployment admission, persistence rule or
dependency changes. The test still rejects unauthenticated source/mapping bytes.
Both sealed scans remain evidence for their exact ranges, not a claim to have
scanned a later commit.

Reported usage snapshots: bot 2,729,801 total tokens, including 2,657,792 cached
input tokens; SQL 7,325,538 total tokens including cached input. These are
workbench-associated rollout accounting, not isolated marginal review consumption;
do not sum them or interpret them as uncached billed usage.

No SQL installation, Discord operations, business replay or bot restart is a test
performed in this chat. Natural acceptance and Report63 residuals remain open.

Local review disposition: no unresolved code/security finding is identified.
Do not promote or deploy yet. Qualify native migration repetition and interrupted
installation recovery (including index presence), trigger/driver result sets,
atomic completion and rollback, concurrent writers/CAS/retirement, and result
imports on an explicitly authorized disposable SQL target. Then qualify exact
protected updater admission and the coordinated drained rollout. These are
release requirements, not completed local-test claims.

## Operator use after a separately approved deployment

Use `/mge admin_completion` for an exact event. Complete freezes domain mutations;
its response separately reports each board's final delivery. Check Final Delivery
processes pending work or reads back unknown edits without reopening the event.
Held/missing/inaccessible targets remain held. Review Retirement lists exact saved
identities and states, then an actor-bound confirmation records retirement only if
the preview still matches. It does not delete messages or claim delivery success.
Unknown targets must reconcile before retirement. Do not re-run business actions
to repair board delivery. Legacy history requires a separate inventory review.
