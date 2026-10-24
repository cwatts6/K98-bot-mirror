# P1 tracked-view restoration — architecture and implementation plan

Date: 24 October 2026. Owner: Chris Watts.
Status: architecture, runtime implementation and validation approved. First-phase
documentation and the first tracked-view runtime slice are implemented and locally
reviewed on `codex/tracked-view-restoration`, then merged as #439/#688 and deployed.
Source/startup and restoration inventory are verified; existing-message callback
acceptance and inaccessible overview disposition remain open. The
[current status record](../reference/P0%20delivery%20and%20P1%20recovery%20status.md)
contains the 21:30 UTC evidence and retains all P0/P1 boundaries. Earlier local
checkpoints below remain historical validation evidence.

## Scope summary

Restore every eligible generic tracked Discord view after startup without cancelling
the entire inventory at the ten-second observation deadline. Keep a bounded,
identity-aware restoration pass, honest partial outcomes and supervised shutdown.
This is the first WS3 slice. All P1 families, WS1–WS6 residuals and outstanding P0
acceptance remain in the [current status record](../reference/P0%20delivery%20and%20P1%20recovery%20status.md).

Evidence: the earlier supplied restart begins a 21-entry pass, cancels during an
Ark fetch at ten seconds and aborts the remainder. The later #438/#687 deployment
log repeats cancellation. A TaskMonitor completion log and zero open recovery
incidents do not prove all views were attached. The inspected baseline schedules
`rehydrate_tracked_views` with the default cancelling deadline. Its sequential
loop rethrows cancellation, has no resumption owner and removes tracker entries
by key without checking whether a newer entry replaced the snapshot.

The initial design used mirror snapshot `cc9aa2ba9014104aa993aa5778219eaa2a2d35e0`.
After GitHub access was restored, the branch was rebased onto current mirror main
`c718150de19c6de0d291a81ca1f60333ecd57c9e`, which names private source
`3a33062cc102e17e5d18d530fb700534d3a661bd`. The tracked-view changes were retained.
This is source alignment, not fresh deployed-runtime acceptance; repeat exact
running-revision and restart checks during promotion. Do not transplant the old
recovery stack into current main.

## Architecture direction

| Layer/file | Responsibility and proposed change |
|---|---|
| New `services/tracked_view_rehydration_service.py` | Dependency-light orchestration and typed per-entry/run outcomes, with injected tracker/Discord adapters and configurable pacing. Own finite inventory accounting and cancellation finalization; the Discord read adapter owns its capped retry budget. No SQL or Discord command routing. |
| New `services/tracked_view_store.py` | Bounded strict tracker reads, exact-entry fingerprints, lock ownership, atomic writes and preservation of unresolved edit receipts. Reuse the existing draining thread helper; no global file utility rewrite. |
| New `ark/dal/rehydration_dal.py` | Restoration-only parameterized Ark config/match reads with one connection attempt, five-second driver login/query timeouts and cursor/connection cleanup. Drain the entered worker on cancellation; never invoke another executor as fallback. |
| `rehydrate_views.py` | Keep compatibility entrypoint, existing serializers, factories, custom IDs, Ark controller callbacks, payload behavior and persistence location. Supply strict snapshot reading, exact-entry comparison, local attachment and existing edit fallback adapters. Extract only the restoration loop. |
| `core/event_rehydration_lifecycle.py` | Schedule one tracked restoration with `cancel_on_deadline=False` and a completion-summary check. Update the scheduling callable typing to support observation keywords. Do not change the vote/survey/calendar contracts in this slice. |
| Existing `bot_instance.schedule_bg` / `core/startup_diagnostics.py` | Reuse keyword forwarding, original-task observation, task ownership and cancellation/drain. Keep other P0 deadline behavior unchanged. Modify shared diagnostic code only if focused tests prove a necessary compatibility gap. |
| Existing TaskMonitor and file utilities | Reuse one named task, locking, atomic replacement and telemetry. No generic TaskMonitor rewrite, cross-domain queue or new external service. |

### Identity and persistence

The tracker remains the durable desired-state authority. A restoration identity is
the tracker key plus a stable fingerprint of the complete view-defining entry,
including channel, message and payload. Exclude only the restoration-owned edit
receipt metadata described below. Do not use key alone or timestamp age.
At the start of each process reconstruct the complete eligible set. Never persist
an "attached" flag that could skip a view after a new process starts.

The compatibility remote-edit fallback needs a small durable exception to the
in-process outcome map: optional restoration-owned metadata on the exact tracker
entry records the attempt identity, entry fingerprint and `prepared`/`acknowledged`
state. Persist `prepared` atomically before dispatch; persist acknowledgement only
after the exact edit returns successfully. If either acknowledgement is lost, leave
the attempt uncertain. On restart, safe local registration may still run, but an
unacknowledged attempt cannot automatically issue another remote edit. A legacy
entry without this metadata remains readable. Keep the metadata through saves of
the same physical channel/message, including payload updates; a replacement message
must not inherit its receipt. This is not a
general delivery journal or an attached-state marker. If preserving this contract
would require a broader tracker migration, stop and narrow the fallback to an
explicit unresolved result before expanding implementation scope.

Read a bounded snapshot with explicit `loaded`, `empty` or `unavailable` outcomes.
Absent first-use storage may be empty under the existing contract; permission,
decode, corruption or malformed-root failures must be unavailable, not successful
zero-entry completion. Preserve original bytes on failure. Do not globally alter
all callers of the permissive `load_view_tracker` helper; add/use a strict adapter
for this restoration path.

Before attaching, recheck that the snapshot identity still matches. There must be
no await between the final identity check and synchronous `bot.add_view`; coordinate
with the existing tracker mutation lock or a narrowly scoped generation guard so a
concurrent save cannot cross that boundary. Prune only through a locked
compare-and-remove of the exact observed entry. A changed/deleted entry is
`superseded`, not pruned or attached. Keep existing invalid-entry/NotFound and
configured Forbidden policies; do not introduce age-based removal.

Choose an offload backend before entering each tracker operation. Never catch a
post-entry exception and invoke the operation through another backend. Cancellation
must drain any entered persistence worker before ownership ends; use the existing
draining helper where its contract matches. This local correction is required by
WS3, while wider executor consolidation stays WS2.

### Execution and retry policy

1. One named supervised run owns a snapshot and an in-process outcome map. Repeated
   ready events while running reuse that owner. After terminal partial completion,
   reconnect does not silently replay uncertain work; a fresh process rebuilds
   desired state and attempts safe local attachment again.
2. Keep sequential processing initially and the existing minimum pacing. Give each
   asynchronous read/fetch a bounded wait, retaining the existing three-attempt
   maximum and capped backoff for transient read failures. A slow entry must reach
   a recorded outcome so later entries are attempted. Centralize the attempt budget
   to avoid multiplying inner and outer retries. Inject limits in tests; use named
   internal constants rather than adding operator configuration in this slice.
3. Preserve Ark DAL reads and factories. Confirm cancellation semantics of their
   actual executors: a proxy timeout cannot justify starting a duplicate worker.
   If an underlying worker cannot be bounded/drained safely, record the blocker and
   narrow that adapter before claiming bounded restoration. Missing Ark config or
   match data is an explicit unavailable/unsupported result, never accidental
   fall-through into a generic view with unrelated callbacks.
4. Prefer local `bot.add_view(view, message_id=...)`. Preserve current edit fallback
   only for the existing supported compatibility conditions. An entered remote edit
   with a lost reply is `outcome_unconfirmed`: do not retry that mutation in this
   process or a later process, send a replacement message, or prune its tracker.
   An existing unacknowledged edit remains blocked for remote fallback; surface the
   exact reason for later guided reconciliation. A retryable read and an uncertain
   mutation are different states.
5. The ten-second startup threshold records `pending` and observes the same task
   until it ends. It does not cancel, spawn another pass, unlock work or report
   restoration complete. The finite pass reports exhausted read failures as
   unresolved; do not introduce an endless background retry loop or repeated DMs.
6. On shutdown, stop accepting work, cancel/drain active async operations and any
   entered persistence workers, then record attempted/unattempted identities.
   Preserve tracker entries for every unresolved or uncertain result. No business
   import, export, send or claim is replayed by restoration.

### Outcome contract

Retain existing summary keys for callers, with documented meanings, and add explicit
counts/status for `attached`, `pruned`, `superseded`, `failed`,
`outcome_unconfirmed`, `unattempted` and tracker-read state. Each snapshot entry has
exactly one final bucket; totals must reconcile. Attempt-level errors must not
double-count an eventual success. A valid empty tracker is a complete no-op; an
unavailable tracker has unknown inventory and cannot claim zero restored/zero needed.

The completion check returns a summary with `restoration_status` of complete,
partial or unavailable. Generic `completed` means the coroutine ended; the feature
summary is the restoration verdict. Keep per-entry reasons in existing private
logs/diagnostics, with bounded summary counts and representative failures. Do not
add public identifiers or a new command. If existing diagnostic consumers discard
the feature verdict, update only the affected rendering path with focused coverage.

## SQL and interaction review

No migration, schema, reservation, permission or ProcConfig contract changes.
The restoration-only DAL reads existing `dbo.ArkConfig` (ordered by `ConfigId`)
and `dbo.ArkMatches` (parameterized `MatchId`), verified against the authoritative
SQL repository's table definitions. Original controllers and mutation paths remain
unchanged. The dedicated read path avoids the legacy wrappers' executor fallback.
SQL mutations require a separate reviewed SQL diff.

Preserve original message/channel IDs, sanitized custom-ID prefixes, view class,
buttons, callback authorization, pagination, event content and initial limits.
Registration does not grant permissions or certify message delivery. No new public
messages, mentions, business actions or diagnostic commands are introduced.

Refactor decisions: extract the restoration orchestration and fix its strict read,
exact-entry prune and once-only adapter boundaries now. Defer event-cache readiness,
singleton ownership, public child-task supervision, vote/survey/calendar lifecycle,
general JSON ordering and executor rewrites to their existing P1 owners.

## Implementation phases and acceptance

| Phase | Deliverable | Exit evidence |
|---|---|---|
| 1 — documentation reconciliation (this patch) | Current P0 acceptance record, full P1/WS1–WS6 map, updated active/resolved deferred records, architecture/plan and PR inventory. | No false whole-programme closure; latest report/deployment distinguished from earlier provider acceptance; documentation gates pass. |
| 2 — one focused runtime PR | Typed service and adapters, exact-entry persistence checks, single-owner lifecycle wiring and feature outcome summaries. | Local restoration completes beyond ten seconds; one slow/failing entry does not silently drop the tail; all mutation ambiguity remains explicit; no duplicate worker/mutation after entry. |
| 3 — validation and review | Focused regression suite, required validators, scoped interaction/security reviews and final diff review. | Every acceptance case below has evidence, with precise unrelated failures/skips. No acceptance based solely on a passing synthetic startup. |
| 4 — reviewed promotion and natural observation | Existing protected promotion flow after separate release authorization; bounded existing-view reconciliation on deployed revision. | Exact source/startup receipt plus inventory accounting, preserved IDs/custom IDs and working original callbacks. Partial restoration remains open with reasons. No forced business publication or repeated P0 checks. |

Runtime manifest: add the orchestration service, tracker store and Ark restoration
DAL listed above; edit `rehydrate_views.py` and
`core/event_rehydration_lifecycle.py`; change diagnostic consumers only if the above
contract requires it (no shared diagnostic edit was needed). Test manifest: add
`tests/test_tracked_view_restoration.py`;
update focused tests below. Documentation updates accompany the final contract.
No SQL migration/config/dependency/deployment manifest change is required; optional tracker
edit-receipt metadata and participating save adapters are part of the persistence
manifest. Refresh the manifest if current source reveals a necessary change before
expanding the PR.

Required deterministic cases:

- Twenty-one entries with restoration exceeding the observation deadline: retain
  the original task, attempt the tail and reconcile every entry outcome.
- Transient read then success; exhausted read; NotFound; both Forbidden policies;
  missing Ark data; malformed entry; unavailable/corrupt versus valid empty tracker.
- Concurrent tracker replacement before attach/prune preserves the newer identity;
  one failed persistence operation enters one backend only.
- Local registration preserves exact IDs/custom IDs, classes and callbacks;
  compatibility edit succeeds, or lost reply stays uncertain with zero fresh sends.
  Crash after durable edit preparation, after remote acknowledgement and before
  receipt persistence never permits a duplicate edit after restart. Legacy tracker
  entries and same-identity producer saves preserve the optional receipt contract.
- Repeated ready events, reconnect after partial completion, repeated cancellation,
  shutdown during fetch/persistence and a fresh process all preserve ownership.
- Formerly successful entries are reattached in a new process; unresolved entries
  remain in storage; summaries distinguish task completion from feature completion.
- Regression: existing P0 observation deadlines, vote/survey/calendar scheduling,
  payloads, Ark controller authorization and persistence contracts remain intact.

Primary suites: `test_event_rehydration_lifecycle.py`, `test_rehydrate_views.py`,
`test_rehydrate_views_and_localtime.py`, `test_rehydrate_sanitize_and_fileio.py`,
`test_monitor_startup_diagnostics.py`, plus the new service tests. Select actual Ark
permission/callback and scheduler tests from the final changed paths. Run architecture,
deferred, security-routing, test selector, import-smoke, command-registration,
format/lint/type and required full/log-isolation gates under current repository rules.
Use fakes/disposable tracker files; no live Discord/Google/production SQL tests.

Security decision: the initial documentation-only phase had a precise skip. The
current runtime patch touches Discord interaction restoration,
network/file handling and restart persistence: use `k98-security-review-routing`,
then **Scan type: Changes**, exact base/head or working patch, **Deep off**. A
Codebase/Deep scan is not an appropriate completion gate. Review bot and any later
SQL changes separately.

Conditional references: existing event/lifecycle tests, root security policy,
Reliability programme and WS1 design, P0 qualification/acceptance packs and the
deferred register. Promotion Guide applies at phase 4, not as approval to deploy.

Rollback: revert the reviewed runtime change through the protected release process;
no destructive tracker migration is planned. Preserve tracker and unresolved edit
receipts. Qualify older readers against optional metadata before release. If an old
reader would replay an unacknowledged remote fallback, block that rollback path or
retain the narrow fallback guard; do not erase the receipt. Rollback can restore the
old restoration limitation and must be reported as such.

## Initial documentation-phase evidence (historical)

Phase 1 local validation on 24 October: architecture validator passed (zero Python
files changed), deferred validator passed across all twelve changed/new Markdown
files, security-routing validator passed with zero warnings, and test selection ran.
Whitespace checking and all 44 local links in new documents/checkpoint overlays
passed. The initial deferred validation caught a disallowed vague phrase; it was
replaced with the exact subsequent-export action and the validator rerun passed.

Runtime pytest, full/log-isolation suites, smoke imports, command registration,
Python lint/type checks and live/provider tests are skipped for this documentation-only
diff: no executable code, dependencies, command definitions, SQL or runtime state
changed. The selector's generic smoke/registration suggestions apply to the later
runtime PR. No new production observation or GitHub mutation was performed.

The operator subsequently approved phases 2–3, now implemented locally.
Production promotion remains separately controlled. Outstanding F04 and final
F01–F05 receipt reconciliation remain P0 throughout.

## Runtime validation — 24 October 2026

The first slice retains the original startup task past its observation deadline,
uses one restoration owner per bot instance, and reports feature completion separately
from coroutine completion. Reads are bounded; tracker writes and SQL workers drain
after cancellation. Driver timeouts are the SQL bound, not a claim that Python can
kill a stalled native driver. Strict tracker failures retain bytes and report
unavailable. Identity checks preserve newer entries, and durable prepared edit
receipts prohibit automatic replay of an uncertain remote edit.

Focused tests cover 21-entry completion beyond the observation deadline, slow reads
and the remaining entries, both Forbidden policies, invalid and inaccessible
storage, Ark callbacks/custom IDs, concurrent replacement, new uncertain receipts,
edit preparation/acknowledgement failures, reconnect, fresh process and repeated
cancellation. Synthetic test configuration disables dotenv loading; no live provider
or production database operations are part of validation.

The initial full-suite attempt stopped with 35 collection errors for missing
recovery modules in the mirror baseline. The operator then explicitly authorized
investigation and resolution before publication; the baseline-repair section below
records that follow-up. Focused suites also run through the production-log isolation
guard. Initial tracked-view gates: **89 focused tests passed**, production operational logs unchanged;
architecture validation passed (seven Python files), deferred validation passed
(twelve Markdown files), security-routing passed with zero warnings, test selection
ran, import smoke and command registration passed (36 primary / 102 grouped), and
Black, Ruff, targeted Pyright (zero errors/warnings) and whitespace checks passed.
The complete staged pre-commit gate also passed, including secret scanning and its
configured Pyright scope, after normalizing line endings in three touched files.
Changes scan `ec86fa9a-2cc7-4418-9ef3-6ef9e5ce229a` completed with five runtime
surfaces reviewed, zero findings and no deferred security candidates. It reviewed
the frozen working patch against `cc9aa2ba9014104aa993aa5778219eaa2a2d35e0`, digest
`e7a5e70314d9b363461f7ec1dc4e45219324df419f8c22982aaefd8b3771b5ee`, with Deep off.
After sealing, final code review restored the original Ark match-label em dash and
added a display assertion to the existing factory test. The immediate post-scan changes
were that literal, its assertion, line-ending normalization and review-status
documentation. The later baseline restoration has its own Changes reviews below. Security routing
for this follow-up is a documented skip: no permission, input handling, SQL, path,
network, persistence, callback or control-flow changes. The frozen scan is preserved;
it is not represented as covering different bytes. No measured scan token count was
returned by the completed-scan tool.

Deployment acceptance still requires existing-view inventory reconciliation on the
deployed revision and working original callbacks. Local deterministic results do
not close all of WS3, any other P1 family, or outstanding P0 acceptance.


## Baseline repair before publication

The operator requested resolution of the full-suite blocker before publishing the
tracked-view PR. The mirror's broad `**/*auth*` credential exclusion also matched
legitimate authority Python modules and tests. Its five exact exceptions predated
nine later delivered files. The snapshot `cc9aa2ba` named private source `27e805e7`;
the only Python differences between those trees were these nine omissions.

Current mirror main `c718150de19c6de0d291a81ca1f60333ecd57c9e` names delivered private
revision `3a33062cc102e17e5d18d530fb700534d3a661bd` and has the same nine omissions.
The tracked-view branch was aligned to that current mirror snapshot in an isolated
managed checkout after the shared checkout changed during validation. Interrupted
runs against the shared checkout are not final validation evidence. The nine restored
files are byte-identical at both named private revisions:

- `services/config_recovery_authority.py`
- `services/export_authority_diagnostics.py`
- `services/export_replacement_authority.py`
- `services/export_target_recovery_authority.py`
- `services/failed_export_recovery_authority.py`
- `services/rollover_replacement_authority.py`
- `tests/test_authority_diagnostic_update_transition.py`
- `tests/test_export_authority_diagnostics.py`
- `tests/test_publication_authority_timing.py`

The repair restores existing delivered logic, adds only those exact publication
exceptions, and extends the filter tests to require explicit review of every
authority source plus reject nested copies and credential/backup suffixes. Broad
credential exclusions remain. The sole command-governance workflow exception is
explained below; all other production workflows remain excluded. No recovery
algorithm, SQL contract, migration or production state is changed. The restored
adapters' existing DAL references resolve to 30 authoritative SQL definitions at
SQL revision `1e95e41`; no missing object was inferred or invented.

The wider run found the existing command-governance test also depended on
`.github/workflows/command-governance.yml`, which a blanket workflow-directory
exclusion removed despite the adjacent comment saying it was mirrored. The exact
49-line workflow was restored from private source `3a33062c`. Its parent directory
and exact filename are now included ahead of the child/directory exclusions;
no other workflow is published. Filter fixtures reject unreviewed workflows,
nested copies and backup/key suffixes. The workflow's governance tests and policy
checks pass: **43 tests and eight subtests**, with two expected local skips.

The isolated worktree uses its own `.venv` interpreter, with existing dependencies
loaded using `site.addsitedir` so their Windows `.pth` initialization is honored.
This preserves the bot's own-checkout interpreter guard and restores `win32event`
for the disposable native-process test, which passes. The primary environment was
not modified. These environment failures are not hidden by changing runtime guards
or weakening tests.

Security routing: Changes scan `f7585c46-7fd7-4db8-92fd-eff05cbddc64` reviewed the
restored modules and filter delta against `ad0104eaa49f86063632d1b0a0741e6b14c5525c`.
Follow-up scan `d577e10e-b728-42d0-a8bd-2e5d744317e2` reviewed the exact workflow,
filter and test delta against `5c8e38449e74b99757c32f3ea4b44591237fc753`, frozen
patch digest `2fc271caebd90f3f7cc6244755f281a966e154d685634487476c094c5f88c4e7`.
Both completed with zero findings, complete changed-surface coverage, no unresolved
candidates and Deep off. No measured token count was returned. Subsequent changes
to this plan, the cleanup report, P0/P1 status and deferred register are evidence/status
prose only, with a documented
security-review skip: no runtime, permission, persistence, configuration or deployment
behavior changes.

`rsync` is unavailable on this Windows host, so actual filter execution is explicitly
skipped locally; the production-only publisher invocation check is also skipped in
the scrubbed mirror. Static exception/source checks, negative fixture definitions,
secret scanning and the existing Linux publication-policy gate remain intact.
Final full-suite validation against committed source `d5ff7f22` completed in
882.27 seconds: **9,218 passed, 1,080 skipped, one dependency warning and eight
subtests passed**, with zero failures/errors. The operational-log isolation guard
passed. The private local evidence is `p1-full-suite-verified.log`; the earlier
diagnostic run is retained separately and is not represented as a passing run.
Skips retain existing environment/platform/disposable-integration opt-ins, including
the two publication checks described above; no test was weakened or newly skipped
to obtain this result. The complete PR checks also passed: architecture (17 Python
files), deferred items (12 Markdown files), security routing (zero errors/warnings),
test selection, import smoke, command registration (36 primary / 102 grouped),
pre-commit lint/format/type/secret checks and diff whitespace validation. Live SQL/provider
acceptance and the full P1/P0 carry-forward boundaries above remain separate.
