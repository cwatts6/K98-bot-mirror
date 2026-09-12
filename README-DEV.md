# Developer Quickstart

## Current KVK delivery status - S4B closeout, 2026-09-11

**S4B is complete, operator accepted, successfully synthetic-smoke tested and merged.**
Mirror [#269](https://github.com/cwatts6/K98-bot-mirror/pull/269) merged at 21:06:11 UTC as
`39c93df39485d796fd66881e47562da112886da1`; private bot [#576](https://github.com/cwatts6/k98-bot/pull/576)
merged at 21:06:38 UTC as `63fcb392385fd2ccad78801cbd4f8bd70f426cc3` on 2026-09-11.
Local mirror main/origin main is `64f6b058c224e749ece334d66cdf0efc81bd983d` (synchronized from the private merge);
local production/main matches that private merge. SQL main remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
Both repositories were clean at closeout entry; local pulls are complete. The operator confirms **no bot-machine pull**.

The archived S4B pack retains actual real-SDK/disposable-SQL synthetic smoke: private recovery,
public Viewer publication, fresh-client reconciliation/deduplication and retired-slot reuse succeeded.
These are historical bounded smoke results, not a post-merge live rerun. Final review-fix validation:
150 focused tests passed; full suites passed in both checkouts with 3,940 passed / 34 skipped
(production 166.93s, mirror 168.50s), operational logs unchanged. Imports and registration 36/100 passed.
Separate exact Changes reviews, Deep off, completed with zero findings; both review comments were resolved.
Production quality and secret CI passed. Earlier incomplete smoke attempts remain historical evidence.

**Next: S5A Private Intake and Admin Controls in a new chat, after explicit S5A G3 approval.**
S1/S3B/S4A/S4B prerequisites are accepted. Start with fresh repo/contract checks and preserve this pending
closeout documentation. The S5A pack requires its exact documentation carry-forward manifest, both sides
of both S4B archive moves, repaired links and this evidence in its eventual separately authorized PR.
No S5A implementation or new chat was started by this closeout.

S4B-MP01 is complete. S5B-REC01 and S6-OPS01/PERF01/CAP01 remain open under their named gates;
they do not block mocked S5A development and are not closed by S4B smoke. Source routing remains disabled.
No bot-machine update/restart, deployment, production SQL, real import/export or Discord action is authorized.
Use mocks/fake destinations; any disposable SQL target and exact operations require explicit authorization.
Preserve all retained predecessor and S4B disposable databases. Historical prerequisite wording below is
retained as history; accepted slices stay closed and S5A/S5B/S6 retain separate approval gates.


## Core Reference Contract

Before repo work, read `AGENTS.md` and the indexed core docs in
`docs/reference/README.md`. That index separates must-read standards from background,
domain, promotion, and operations references so routine work does not require reading the
entire `docs/reference` folder.

## Programme boundary and next priority

Discord Embed Payload Safety's approved implementation scope is closed through Phase 2K.
Original payload families are delivered, assessed safe within their enforced contracts, or
explicitly deferred. Natural Pre-KVK/off-season and Phase 2F public-save observations remain open;
they do not extend the implementation programme or invalidate accepted Phase 2K smoke.

Final Phase 2K closeout, 2026-09-09: mirror #262 merged at 12:06:38 UTC and production
#569 at 12:07:06 UTC. Verified mirror main: `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`;
production main: `1e72949dc69f1a1e5a529dbf1951039fe0ba74a6`. Operator supplied the same
production bot HEAD and empty `git status --short`. Associated restart invoked 12:08:56.672,
ready 12:09:10.755, full startup complete 12:09:15.539, new child PID 4800. This closes the
final deployment evidence gap; candidate smoke/test revisions below remain historical evidence.


The new [Bot Operational Reliability programme](docs/task_packs/Bot%20Operational%20Reliability%20-%20Programme%20Pack.md) owns ProcConfig WS1
(formerly Phase 2L), executor replay prevention, lifecycle/rehydration, DM/JSON persistence,
durable dispatch policy and evidence-gated cross-invocation admission. WS1 audit/design is complete;
runtime/test/SQL implementation remains unapproved. Retain the exact design/manifests and recheck
source drift if work resumes later. Programme numbering does not determine next priority.

The [2026-09-09 backlog assessment](docs/task_packs/Backlog%20Priority%20Assessment%20-%202026-09-09.md)
records the operator's selected order: **KVK Source Migration first, Private Inventory Import and
Support Sharing second, Reliability WS1 third**. All players see empty KVK stats three times daily;
inventory is optional and used by a handful of players. The operator plans a risk warning and
advice to defer inventory uploads. This is communication-based risk reduction, not technical
containment or a resolved security finding. Start with KVK's read-only Phase 1; implementation and
live actions retain their own approval gates. Bring any proved WS1 prerequisite back for approval.

## Discord Embed Payload Safety delivery history

The following dated delivery history retains original evidence limits. The programme decision
and final Phase 2K deployment record above supersede historical pending/next-phase instructions.
Phase 2J removal, H/I sessions/defaults and Phase 2K receipt/claim semantics remain preserved.

Discord Embed Payload Safety Phase 1 is merged through mirror PR #251 and production PR #558. It
establishes dependency-light canonical ownership in
`core/discord_embed_limits.py`, fixes the exact Pre-KVK launch-week overflow through complete-event
packing, repairs the shared sender, and makes the Pre-KVK module the sole post-success
`prekvk_daily` claim owner. Focused validation passed `40` tests; the full and log-noise suites each
passed `3059 passed, 2 skipped`; both Changes-only security reviews ran with Deep off and found no
reportable issues.

Operator smoke on 2026-09-02 validated a 13-field, 1,847-character payload whose largest field was
530 characters, then edited existing message `1544617668999381044` in place with matching persisted
state and no duplicate or Discord `50035` rejection. Historical `/ops test_embed` bypassed daily guards, so the
valid same-day message ID selected the edit path; a scheduled fresh-send ping and post-success claim
remain a natural operational observation rather than evidence from that test command.

The completed Phase 1 and Phase 2A task packs and starters are archived. Phase 2A event/calendar
payload convergence is merged through mirror PR #252 and production PR #559. Changed renderers
validate against the canonical contract, retain
complete event blocks, and use exact count-bearing omission markers under field or aggregate
exhaustion. Commands, selection/order/caps, mentions, visibility, SQL, cache/state schemas, tracker
formats, timing, and rehydration semantics remain unchanged. Final automated validation passed
`3078 passed, 2 skipped`; the applicable Changes-only reviews ran with Deep off and found no
reportable issues.

Operator production smoke on 2026-09-02 accepted the restart and persistent pinned-calendar edit
path: rehydration completed, the reminder and daily-refresh tasks armed normally, and message
`1488086669876920341` was edited in place for 27 events. The final payload contained 15 fields and
4,789 aggregate characters, with a 533-character largest field and zero compacted or omitted
events. No duplicate or Discord `50035` rejection occurred. This representative smoke did not
naturally exercise public/DM reminder delivery or an omission marker; those unchanged paths and
exact-boundary behavior retain deterministic automated coverage.

Phase 2B Ark payload hardening is delivered and operator candidate-smoke accepted on
`codex/discord-embed-payload-safety-phase-2b` from base `4290b0fc`. Ark registration,
confirmation/result, reminder, cancellation-DM, team-publication, first-publication mention,
fuzzy-selection, team-builder, and player-report outputs now reuse the unchanged canonical contract
with complete-unit packing, visible compaction, character-budgeted pages/chunks, exact omission
markers, and final send/edit validation. The full suite passes with `3090 passed, 2 skipped`.
Changes-only security scan `79603f53-69f8-4586-9296-760385dd9420` reviewed the exact
`4290b0fc..fccde886` bot range with Deep off, complete coverage of all 11 runtime files, and zero
reportable findings; SQL is a documented no-diff skip. Mirror PR #253's delivered tree is present
on mirror `main`, and production PR #560 is merged in production commit `6da1c083`.

Operator candidate smoke on 2026-09-02 exercised match `52` through the existing registration
message reference. The builder produced `fields=4`, `chars=346`, `compacted_units=0`, and
`omitted_units=0`; `should_announce=False` preserved the first-publication-only ping boundary, and
the message was edited in place with no state or identity change and no Discord `50035`. The
production-main merge was verified on 2026-09-03.

Phase 2C player-facing rankings/history convergence completed its evidence-led implementation on
2026-09-03. Authoritative SQL/model/cardinality measurements proved every live embed, text fallback,
and existing attachment/export boundary safe, so the approved change adds regression coverage and
delivery records only; runtime code is unchanged. Tests cover every current Top limit at source
maxima, the 4,030-character maximum Hall of Fame description, an out-of-contract 4,097-character
single-unit rejection, grouped-message aggregate rejection, and complete maximum-contract history
fallback. The focused suite passed `79`; the full suite passed `3104 passed, 2 skipped`.
The independent log-noise run passed the same suite with production operational logs unchanged.
Changes-only security scan `25a90732-3ad2-4ee0-9138-d1f4f11bbf36` reviewed the exact
`e525fb35..fa67d842` bot range with Deep off, complete coverage of all nine changed files, and zero
findings. SQL remains a documented no-diff skip. Review is complete, and the operator confirmed on
2026-09-03 that candidate deployment and smoke testing passed for mirror PR #254 and production PR
#561. Both PRs are merged and their final production-main source state was verified on 2026-09-03.

Phase 2C's task pack and chat starter are archived. Phase 2D operator diagnostics convergence is
delivered and operator-smoke accepted on `codex/discord-embed-payload-safety-phase-2d` from mirror
base `25525c55`. It adds a
diagnostic-only policy layer for 2,000-character content, complete-unit packing, credential-shaped
text redaction, conservative attachment filenames, and destination upload bytes while keeping
`core/discord_embed_limits.py` canonical for embeds. Live admin, log-view, history/failure,
PreKvK/KVK, inventory, subscriptions, shared-sender, and queue outputs now use final validation,
visible exact-count compaction, and complete redacted private attachments where supported. PR
review follow-up fixed quoted credential redaction, mention-neutral diagnostic errors, subscriber
marker field reservation, and singular omission labels. The full and log-hygiene suites now pass
`3172 passed, 2 skipped`; pre-commit and the focused `64`-test review suite pass. Final Changes-only
scan `984d93ff-29b1-4dd3-b681-a9830d01a1c4` reviewed production
`f03b2c8a..08d4c408` with Deep off, covered all 11 runtime files, and found zero issues. SQL is
unchanged. Operator smoke on 2026-09-03 confirmed clean graceful restart/startup, queue-state
persistence and rehydration, `/ops logs` plus component interactions, `/ops show_logs`,
`/ops view_restart_log`, `/ops last_errors`, and the representative command set without
`File.to_dict`, Discord `50035`, traceback, command error, or error/critical entry. Mirror PR #255
and production PR #562 are merged, and final production-main source verification passed on
2026-09-03. The Phase 2D pack and starter are archived.

Phase 2E completed its audit-first gate, review remediation, automated validation, final security
review, candidate delivery, and operator smoke on 2026-09-07 through mirror PR #256 and production
PR #563. Phase 2F prerequisite checks confirmed both PRs merged and production `main` at
`2888512cbb2b329c4c7f472449f005ae2dd07a4e`; its Python source/tests match mirror base
`88de37a2c77f96fe91be98b2e3ed40c4b639e199`. This verifies repository source, not a new
bot-machine deployment. Confirmation history remains keep-all: the measured
local state copy was proved to contain repeated test fixtures and is not production evidence, so no
JSON shape, retention, cleanup, or SQL change is justified. Confirmation-flow tests now use
temporary state paths. Registration delivery reports explicit `created`, `edited`, `moved`,
`reposted`, `recreated`, or `failed` outcomes behind a legacy tuple adapter, and team-builder
assign/remove/reset/auto-balance persistence-plus-audit coordination now belongs to
`ark/team_builder_service.py`. Commands, permissions, visibility, mentions, interaction ordering,
Ark meaning, message identity, timeouts, restart/scheduler behavior, and SQL remain unchanged.
Focused validation passes `48`, Ark-plus-UI regression passes `204`, and the complete suite passes
`3186 passed, 2 skipped`; deterministic validators, pre-commit, and log-noise checks also pass.
Review remediation is in mirror commit `cd973007`. Final Changes-only scan
`e7f618aa-0ab4-4934-a2d0-2bfb398ebf80` reviewed exact range
`06e34776eacf3c49db4a0b93077d5067069ae88e..cd973007f4b88de33ae50f3c455a42e724ced118`
with Deep off, complete coverage of all four changed runtime files, and zero findings. SQL remains
a documented clean no-diff skip. The operator reported that smoke testing completed successfully:
messages posted and refreshed successfully. The Phase 2E pack and starter are archived.
Phase 2F now owns active-reminder tracker atomicity; Phase 2G owns evidence/design-gated atomic
Pre-KVK reservation; separate Stats/KVK History executor audits remain out of scope.

Phase 2F is archived; mirror #257 and production #564 are merged and deployment/restart is
operator-attested. Its next natural public save remains an observation.

Phase 2G PRs #258/#565 are merged; deployment of `c0a3bc6b` was operator-attested.

Phase 2H isolated diagnostic smoke passed on deployed pre-merge commit `7794d2ae`. Phase 2G’s real reservation protocol was exercised successfully through isolated diagnostics. Production-state comparison passed for the observed status/edit operations. Natural production calendar dispatch remains separately pending.

Operator acceptance: 2026-09-08, Chris Watts. The Phase 2H pack/starter are archived.
Phase 2H #259/#566 and Phase 2I #260/#567 are merged. Phase 2I candidate smoke is accepted;
final merged-head process/restart association remains pending. Archived packs retain exact
receipts and historical evidence limits. Phase 2J retires ops publication on operator approval.
Phase 2F's natural public-save observation stays pending.

## KVK Target Publication And Quality Delivery

KVK Target Publication State Separation Phase 1 was deployed and operator accepted on
2026-08-26 through mirror PR #235, production PR #542, and SQL PR #73. The follow-up import-path
transaction fix was delivered through mirror PR #236 and production PR #543. Production SQL
checks confirmed the publication objects, exact source scan/type, configured scans, publication
version/signature, output object, and row-count consistency; the rebuilt bot cache and
`/kvk targets` output were then tested successfully.

Phase 1 keeps target publication state separate from the shared Pass 4 fighting lifecycle and is
documented in `docs/kvk/target_publication_contract.md`. Phase 2 completed the deferred quality
programme through six independently approved slices covering typed target rows, legacy-path
consolidation, target-domain cache ownership/single-flight behavior, explicit fighting-lifecycle
terminology, lifecycle DAL extraction, and final reliability/interaction cleanup. Both programmes'
completed task packs and chat starters are archived under `docs/task_packs/archive/`.

On 2026-08-27 the operator approved Phase 2A implementation together with a companion SQL PR that
standardises only `dbo.EXEMPT_FROM_STATS.GovernorID` from `float NOT NULL` to `bigint NOT NULL`.
The approved SQL slice preserves every row, duplicate, exemption value, KVK value, procedure
contract, and player rule. The operator also confirmed that production automatically transitioned
the target cache from Draft to Official after Phase 1 deployment. That operator-attested live
transition satisfied the Phase 2C evidence prerequisite.

Phase 2A shipped through mirror PR #237, production PR #544, and SQL PR #74. Phase 2B shipped
through mirror PR #238 and production PR #545 and was operator accepted on 2026-08-27 after Discord
smoke covered numeric and fuzzy-name lookup, account selection, public output, exemptions, and
last-KVK comparison. Phase 2C was then merged through mirror PR #239 and production PR #546,
deployed, smoke tested, and operator accepted with clear logs. It retains cache schema version 2
and adds only a target-specific durable single-flight coordination sidecar. Phase 2D was merged
through mirror PR #240 and production PR #547, deployed, smoke tested, and operator accepted on
2026-08-27. It makes the fighting-lifecycle terminology explicit while retaining the original
public adapters and exact operational log template. Phase 2E was then deployed and operator
accepted through mirror PR #241 and production PR #548 on 2026-08-28. Lifecycle SQL execution and
row mapping now live in `kvk/dal/kvk_lifecycle_dal.py`, while `kvk_state.py` retains every public
façade, fighting resolver, reason code, warning, broad-window rule, and fallback decision.
Phase 2F shipped through mirror PR #242 and production PR #549 and was deployed and operator
accepted on 2026-08-28. It makes `/kvk history` summary-rank retrieval tolerate SQL statement-count
result sets, moves the KVK targets selector into `ui/views/`, and removes its proved-unused generic
picker `_last_kvk_map` plumbing while preserving the live `/kvk stats` comparison state. Production
smoke passed history, targets, stats, CrystalTech, and shared account-picker flows with clear logs
and without the prior history rank result-set error. No SQL deployment, command resync, target rule,
publication/cache contract, or fighting-lifecycle behavior changed. The final follow-up review found
no new Phase 2 requirement or active target-subsystem deferred optimisation.

The King of All Britain KVK Card Background delivery is complete and operator smoke accepted on
2026-08-28 through mirror PR #244 and production PR #551, pending the operator's manual merges.
The exact `1180 × 640` RGB production PNG is pinned by SHA-256 and is selected by both the Stats and
Targets renderers through the existing normalised fixed mapping and unchanged fallback chain.
Focused Stats/Targets coverage passes 32 tests, both final code/asset Changes reviews ran with Deep
Off and returned zero findings, and the operator confirmed that Stats and Targets display the new
backdrop correctly and look perfect. Local Stats, More Stats, active Targets, and exempt Targets
smoke artifacts are retained under `smoke_artifacts/king_of_all_britain/`. There is no SQL,
command, payload, publication, permission, persistence, or registration change. Deployment only
requires the normal bot code/asset rollout and process restart. The completed task pack and chat
starter are archived under `docs/task_packs/archive/`.

## KVK Post-Pass-4 Stats Correctness And Refresh Provenance Delivery

The post-Pass-4 healed-troop and provenance-safe stats-refresh fix is complete and archived. Bot
mirror PR #245 and SQL PR #75 merged on 2026-08-28; the initial SQL deployment then exposed a
compile-time `CONVERT` syntax error in a named stored-procedure argument. SQL hotfix PR #76 replaced
that expression with a typed local-variable binding, added deploy-syntax regression coverage, and
was merged before the corrected migration was deployed.

The delivered SQL uses the strict `PRE_PASS_4_SCAN` boundary for current healed deltas, preserves
the starting-healed baseline and existing KP Loss/Tanking Score formulas, and makes
`STATS_FOR_UPLOAD` publication atomic, serialized, and dependent on the successful output
provenance already held in `KVKFinalReportHeader`. `LAST_REFRESH` now comes from the proven output
scan rather than the global newest scan. The bot-side cache contract validates fallback snapshots,
preserves healthy JSON when SQL output is invalid, returns structured refresh outcomes, and reports
last-known-good reuse as degraded rather than unqualified success.

Automated evidence includes `2,999 passed, 2 skipped` in the full bot suite, a passing full
pre-commit run, passing focused SQL rehearsal and repository validation, and zero findings from the
final bot, SQL, and SQL-hotfix Changes security reviews. Operator smoke for KVK 16 Governor
`Chrislos` (`2441482`) confirmed Healed changed from `19.4K` to `0`, KP Loss from `387.1K` to `0`,
and Tanking Score from `0%` to `N/A`, while Rank, Power, Kills, Deads, and Acclaim remained
unchanged. The evidence supplied in this task covers one player; the archived pack records the
additional three-player/provenance checks without claiming they were completed here.

The completed historical record is retained at
`docs/task_packs/archive/Codex Task Pack - KVK Post-Pass-4 Healed Troops and Provenance-Safe Stats Refresh.md`.

## CrystalTech Path Refresh Delivery

The 2026-08-25 CrystalTech path refresh is complete and operator accepted in mirror PR #234 and
production PR #541, pending the operator's manual merges. The final config contains eight paths
and 404 path steps, includes the corrected image mappings and in-game `Archer's Focus` spelling,
and is protected by focused production-config regression tests. `/crystaltech validate` and
`/crystaltech reload` passed; two users progressed through multiple steps, and account reset
behaviour correctly returned the affected path to its start. The clean-rollover deployment
precondition was satisfied with no extant CrystalTech progress.

This delivery made no SQL, command, service, UI, asset, command-registration, automatic progress
migration/reset, or archive/copy config change. The completed task pack, chat starter, review,
approved candidate, proposed diff, and corrected workbook are archived under
`docs/task_packs/archive/`.

## Current GovernorOS Programme

GovernorOS v2 Phase 5B Premium Inventory Report Backdrops and Visual Alignment is complete.
Operator smoke and final visual acceptance passed on 2026-07-13 across the premium Resources,
Speedups, Materials, and honest no-data reports. The shared 1400x980 renderer uses the approved
report-specific production backdrops, restored item icons, the invoking player's best-effort
Discord avatar, fitted typography, up to six genuine upload-date labels, and density-aware markers
for every plotted upload. The 2800x1960 masters remain source-only. Private direct `/me` reports
and the then-live legacy `/myinventory` route shared that visual refresh. Phase 5F subsequently
retires the legacy route while preserving the accepted renderer, data, calculations, controls,
exports, filenames, fallback, and attachment lifecycle. The completed Phase 5B task pack and
starter are archived.

Phase 5C Premium Accounts Summary Card is complete and operator accepted in mirror PR #221 and
production PR #528. `/me accounts` resolves every linked registry entry through set-based Kingdom
1198 and canonical Inventory reads, renders the approved 1702x924 avatar-enabled portfolio card as
a standalone private attachment, preserves the guided Manage workflow, and adds a private,
avatar-enabled paginated Overview/Combat/Economy Account Summary with VIP, compact power, KP
Loss/Tanking Score, percentage-labelled Tanking, Conduct in Economy, UTC date-times, and a complete
formula-safe CSV. The main roster uses a larger two-column governor-tile grid with prominent Power
values and no duplicate Main-governor header line. Same-payload fallbacks, author gates, graceful
timeouts, attachment replacement, and stream cleanup are retained; no SQL schema, registry,
ownership, direct Inventory, or existing export contract changed. The completed Phase 5C task pack
and starter are archived.

Phase 5D Premium Reminders Summary Card is complete and operator accepted in mirror PR #222 and
production PR #529 after final smoke on 2026-07-15. `/me reminders` now provides the private,
avatar-enabled 1702x924 ACTIVE/REVIEW/OFF card, truthful coverage hero, friendly KVK/Calendar
summaries, deterministic insight, duplicate-safe identity, page-relevant navigation without the
deprecated Inventory button, aligned state support, a full UTC footer, same-payload fallback, and
graceful timeout. Manage refresh and all existing reminder behavior remain intact. The completed
Phase 5D task pack and starter are archived.

Phase 5D.1 Authoritative Next Scheduled Alert Projection is complete and operator accepted in
mirror PR #223 and production PR #530 after final Discord smoke on 2026-07-15. The Reminders hero
now selects the deterministic earliest future KVK or Calendar candidate through narrow pure
eligibility shared with live dispatch, distinguishes healthy `NO UPCOMING ALERT` from request-level
`SCHEDULE UNAVAILABLE`, and performs no jobs, DMs, acknowledgements, refreshes, network calls, or
writes. The default KVK snapshot uses the same injected UTC clock as the projection, and the final
card makes the authoritative event start date-time prominent in bold gold. Existing reminder,
tracker, rehydration, retry, command, Calendar, persistence, and DM contracts remain unchanged apart
from the separately authorised KVK at-start eligibility correction. The completed task pack and
starter are archived.

Phase 5E Premium Preferences Summary Card is complete, operator accepted, merged in mirror PR #224
and production PR #531, and deployed on 2026-07-16. `/me preferences` is now the private Discord-
user-level Personal Settings centre with the invoking user's top-left avatar on an approved
1702x924 standalone card, DST-aware local-time context, regional-profile coverage, truthful
Inventory privacy copy, deterministic insight, one in-place `Manage settings` journey, and a same-
payload fallback. `Update VIP` now belongs to the existing
Manage Accounts task selector and explicitly resolves a currently linked governor before the
unchanged VIP service rechecks access and writes. Profile saves use a narrow atomic field-specific
DAL upsert so concurrent edits to different fields do not overwrite one another. No SQL repository
object, schema, migration, procedure, view, index, data, default, or preference meaning changed.
The completed Phase 5E task pack and starter are archived.

GovernorOS v2 Phase 5F supersedes Phase 5E's Inventory-privacy ownership and the proposed Premium
Inventory Summary Card. The implementation retires `/me inventory`, `/myinventory`, and
`/inventory_preferences` together; removes public Inventory reporting, combined `All` viewing, the
visibility model/service/DAL, the orphaned legacy controller, and the old summary backdrop; and
simplifies Personal Settings to regional profile plus derived `LOCAL`/`UTC` context. It preserves
the selected-governor dashboard, `/me resources`, `/me speedups`, `/me materials`, and their private
report-page Excel/CSV/Google Sheets exports. At the accepted Phase 5F checkpoint, `/me exports`
contained only the Stats export journey;
the legacy combined/all-governor Inventory export and `/export_inventory` are retired. `/inventory
import` and `/inventory audit` remain. `dbo.InventoryReportPreference` and existing rows remain
untouched for rollback; there is no SQL deployment in Phase 5F.

Phase 5F is complete and operator accepted after final Discord smoke on 2026-07-16. Mirror PR #225
contains the accepted implementation, and production-branch commit `89f7da16` carries the promoted
patch. The completed task pack and chat starter are archived under `docs/task_packs/archive/`.

GovernorOS v2 Phase 5G Account Data Export Consolidation is complete and operator accepted after
final Discord smoke on 2026-07-17. Mirror PR #227 and production PR #534 carry the accepted
implementation. It removes `/me exports` and `/my_stats_export`, removes every Exports navigation
surface, and makes
`/me accounts -> Account Summary -> Download data` the canonical all-linked personal-data journey.

`Download data` offers a default Account-Summary-first formatted workbook (`.xlsx`), the exact
current Account Summary snapshot (`.csv`), or raw Stats history (`.csv`) for 30/60/90/180/360 days.
The phase also corrects every identified Stats export issue: exact inclusive N-day windows, filtered
`ALL_DAILY`, actual written row counts/date bounds, selected-window Forts semantics, shared formula
safety, separate Stats/Inventory freshness, truthful generated time, and one honest Excel/Google
Sheets-compatible workbook option. The top-level command surface is 38, `/me` has seven grouped
subcommands, and `/inventory` remains at two. Command resync and smoke confirmed both retired routes
are absent, `/my_stats` remains live, the private option window can switch and reselect every
output/window choice, times out safely, and all three output kinds work. The selected-governor
Inventory report-page exports remain unchanged. The completed Phase 5G task pack and chat starter
are archived under `docs/task_packs/archive/`.

GovernorOS v2 Phase 6 Interactive Period Performance is complete and operator accepted after final
production Discord smoke on 2026-07-18. Mirror PR #228 and production PR #535 carry the accepted
bot implementation. It adds private-anywhere `/me stats`, with Overview, Activity, and Combat on
the approved 1702x924 card; selected-governor or explicit All Linked scope; seven exact Stats-anchor
periods; signed, coverage-aware Growth/Activity/Fort/Combat metrics; integrated RSS/Fort and Combat
trends; opaque paged governor selection; current-registry revalidation; and a 180-second preserve-
and-disable timeout. Final smoke accepted every period, governor switching, All Linked, Dashboard
row-0 navigation, source-correct data, timeout behavior, and the final visual presentation.
The accepted refinement uses the Reminders-style right-aligned state pill/header stack,
brighter/bolder typography, compact totals and averages, full selected Governor ID, explicit
Stats/Activity/Fort coverage, a Forts Total-only Activity KPI, and integrated RSS/Fort plus
T4+T5/Deads/Healed charts with consistent date axes and no duplicated chart summary copy.
The selected Dashboard exposes Stats on row 0 after Preferences. The same atomic bot patch removes
`/my_stats` without a redirect while preserving `/stats player` and its proven legacy stack. The
validated command target is 37 top-level, 100 grouped, eight `/me`, and two `/inventory` commands.

The separately reviewed and deployed SQL migrations create `dbo.usp_GetPersonalStatsDaily`, a
bounded set-based read contract for at most 26 deduplicated Governor IDs and 180 source-anchored
days. SQL PRs #43 and #44 deployed before the accepted bot smoke. The follow-up result contract
exposes the latest UTC
`KingdomScanData4.ScanDate` on the global Stats anchor date so the card's `Data last refreshed`
label reports source freshness rather than bot query time. An additional covering index remains
evidence-gated on production plans/logical reads rather than speculative. Account Summary remains
the only central personal-data download home and Phase 5G output contracts remain unchanged.

GovernorOS v2 Phase 7 `/me` Visual Consistency, Content Audit and Programme Closeout is complete
and operator accepted after final Discord smoke on 2026-07-19. Mirror PR #229 and production PR
#536 carry the accepted result. The phase aligned the retained `/me` family to the Stats visual
contract, added only bounded shared primitives in `core/visual_contract.py`, vertically centred the
top-right state-pill text, completed Accounts/Reminders/Preferences/Stats row-0 navigation, moved
Stats page-mode controls below that row, left-aligned the Accounts hero headings, and rebuilt
Preferences into balanced regional-profile, local-time, insight, and Manage panels. Dashboard
remains `1180x760`; core summaries remain `1702x924`; Inventory remains `1400x980` with its
category accents, charts, icons, ranges, exports, and report-specific backdrops.

No command, SQL, payload, metric, formula, rank, permission, privacy, export, or data-source
contract changed. No resync or SQL deployment was required, and command counts remain 37 top-level,
100 grouped, eight `/me`, and two `/inventory`. The completed Phase 6 and Phase 7 task packs and
starters are archived under `docs/task_packs/archive/`.

Phase 8 Leadership `/stats player` Modernisation is complete and operator accepted after production
smoke on 2026-07-21. Mirror PR #230 and production PR #537 carry the accepted bot result; the SQL
migration series and merged follow-up SQL PR #53 were deployed first. `/stats player` is the one
private leadership player-review journey, `/player_profile` is absent with no redirect, canonical
Tanking Score is aligned globally, and the accepted command surface is 36 top-level, 100 grouped,
eight `/me`, one `/stats`, and two `/inventory`.

Phase 8.1 completed and was operator accepted on 2026-07-23. It retained `/stats player`, the
dedicated role-ID/channel permission boundary, private output and the existing command surface,
while delivering the final visual hierarchy, distinct Presence and bounded Last Active signals,
combined location/shield context, clearer KVK and Player Record presentation, latest-scan Power
rank, positive-Acclaim rank, and bounded exact-Governor-ID existence handling. No command resync,
permission, privacy, table, index, refresh or pre-aggregation contract was added.

The Phase 8.1 task pack and chat starter are archived. Representative SQL plan/read/time evidence
for the delivered path remains separately deferred and does not make the implementation pack
active. Phase 9 `/stats kingdom` remains proposed and approval-gated across product, SQL, visual,
performance, security and scheduling decisions.

## Quality Automation

Run before committing:

```powershell
python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/select_tests.py

pre-commit run -a
pytest -q tests
python scripts/analyse_pytest_log_noise.py
```

Before PR handoff, make and record the security-review decision with
`k98-security-review-routing` when the change touches permissions, Discord interactions,
SQL/data access, file handling, secrets/config, dependencies, deployment, network calls,
user-controlled input, subprocesses, or restart-sensitive persistence.

- Routine Git-backed changes: run `$codex-security:security-diff-scan` or record a precise skip.
- Standard or deep codebase scans: only after an explicit operator request for that audit.
- Confirm `Scan type: Changes`, the correct base/head, and Deep off for routine reviews.
- Run or justify skipping `python scripts/validate_codex_security_routing.py`.

`pytest` runs are isolated from production operational log files. Expected negative-path logs
remain visible through pytest output and `caplog`; when a saved audit artifact is needed, capture
the run explicitly, for example:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests 2>&1 | Tee-Object -FilePath .codex_pytest_audit.log
```

Use `python scripts/analyse_pytest_log_noise.py` to verify that pytest did not write to
`logs/log.txt`, `logs/error_log.txt`, `logs/crash.log`, or `logs/telemetry_log.jsonl`.

When a full-suite run feels slow, capture durations with the audit artifact so the next
optimisation task has actionable timing evidence:

```powershell
.\.venv\Scripts\python.exe -m pytest -vv tests --durations=30 --durations-min=1.0 2>&1 | Tee-Object -FilePath .codex_pytest_audit.log
```

Optional: for fast local searches, place `rg.exe` at `C:\discord_file_downloader\tools\rg.exe`.
`dev.ps1` adds `tools\` to `PATH` when that binary exists.

## Windows Setup (per new PowerShell session)
```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
.\dev.ps1
pre-commit autoupdate
pre-commit install --install-hooks
pre-commit run --all-files
pre-commit run --all-files
git switch main
git switch -c feat/

git add -A
git status
pre-commit run -a
git add -A

pre-commit run -a
git commit -m "feat: short summary of the change"

git push -u origin feat/my-topic # = what it is

cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
.\dev.ps1
git switch main
git pull
Git-CleanupMerged
.\venv\Scripts\python.exe -m pip install -r requirements.txt
pre-commit run -a


1. **Load local dev environment**
# === Session bootstrap (paste this as-is) ===
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Create venv if missing, then activate
if (-not (Test-Path .\venv\Scripts\Activate.ps1)) {
  py -m venv venv
}
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Dot-source local dev env (pre-commit cache, UTF-8, etc.)
. .\dev.ps1

# Ensure hooks are installed
pre-commit autoupdate
pre-commit install --install-hooks

# Quick sanity: run all hooks across repo
pre-commit run --all-files
# === end bootstrap ===


cd C:\discord_file_downloader
.\venv\Scripts\Activate
pytest -q tests/test_kvk_personal_views.py -vv
pytest -q tests/test_kvk_personal_service.py -vv
pytest -q tests/test_mykvkstats.py -vv
pytest -q tests/test_mykvktargets.py -vv


pytest -q tests/test_usage_tracker.py -vv
pytest -q tests/test_command_usage_dal.py -vv
pytest -q tests/test_mge_dm_followup.py -vv
pytest -q tests/test_mge_priority_rank_map.py -vv
pytest -q tests/test_mge_public_signup_embed.py -vv
pytest -q tests/test_mge_review_service.py -vv
pytest -q tests/test_mge_signup_config.py -vv
pytest -q tests/test_mge_signup_service.py -vv
pytest -q tests/test_mge_simplified_flow_service.py -vv
pytest -q tests/test_mge_simplified_signup_form_view.py -vv
pytest -q tests/test_mge_content_renderer.py -vv
pytest -q tests/test_mge_publish_service.py -vv
pytest -q tests/test_mge_embed_field_limits.py -vv
pytest -q tests/test_mge_embed_manager.py -vv
pytest -q tests/test_mge_simplified_leadership_service.py -vv

pytest -q tests/test_mge_rules_service.py tests/test_mge_rules_edit_view.py -vv
pytest -q tests/test_mge_signup_service.py tests/test_ark_registration_flow.py -vv

pytest -q tests/test_registry_io.py -vv
pytest -q tests/test_registry_io_xlsx.py -vv
pytest -q tests/test_registry_io_error_roundtrip.py -vv
pytest -q tests/test_registry_service.py -vv
pytest -q tests/test_registry_governor_registry.py -vv
pytest -q tests/test_registry_dal.py -vv
pytest -q tests/test_registry_views_smoke.py -vv


pytest tests/test_mge_simplified_leadership_admin_add.py -vv
pytest tests/test_mge_embed_manager.py -vv 
pytest tests/test_mge_simplified_flow_service.py -vv
pytest tests/test_mge_leadership_dal.py -vv 
pytest tests/test_mge_publish_service.py -vv
pytest tests/test_mge_simplified_leadership_view.py -vv 
pytest tests/test_mge_simplified_leadership_service.py -vv 
pytest tests/test_mge_simplified_signup_view.py -vv
pytest tests/test_mge_public_signup_embed.py -vv
pytest tests/test_mge_xlsx_parser.py -vv
pytest tests/test_mge_results_import.py -vv
pytest tests/test_dl_bot_mge_auto_import.py -vv
pytest tests/test_mge_results_import_service.py -vv
pytest tests/test_mge_results_overwrite_confirm_view.py -vv
pytest tests/test_mge_startup_wiring.py -vv 
pytest tests/test_mge_permissions.py -vv 
pytest tests/test_mge_rehydrate_and_regression.py -vv 
pytest tests/test_mge_startup_hook_invoked.py -vv
pytest tests/test_mge_simplified_flow_service.py -vv
pytest tests/test_mge_completion_service.py -vv 
pytest tests/test_mge_report_service.py -vv 
pytest tests/test_mge_admin_completion_view.py -vv 
pytest tests/test_mge_scheduler_completion.py -vv 
pytest tests/test_mge_rules_edit_view.py -vv
pytest tests/test_mge_rules_service.py -vv
pytest tests/test_mge_event_service_rules_regression.py -vv
pytest tests/test_mge_roster_rank_waitlist_notes.py -vv
pytest tests/test_mge_roster_permissions.py -vv
pytest tests/test_mge_roster_service.py -vv
pytest tests/test_mge_roster_delete_undo_audit.py -vv
pytest tests/test_mge_cache.py -vv
pytest tests/test_mge_event_service.py -vv
pytest tests/test_mge_scheduler.py -vv
pytest tests/test_mge_open_mode_switch.py -vv 
pytest tests/test_mge_signup_views.py -vv
pytest tests/test_mge_signup_service.py -vv
pytest tests/test_mge_dm_followup.py -vv
pytest tests/test_mge_summary_service.py -vv 
pytest tests/test_mge_review_service.py -vv
pytest tests/test_mge_leadership_board_view.py -vv
pytest tests/test_mge_cmds_register.py -vv

pytest tests/test_calendar_reminder_metrics.py -vv
pytest tests/test_calendar_reminder_prefs.py -vv 
pytest tests/test_calendar_datetime_utils_usage.py -vv
pytest tests/test_calendar_view_pagination.py -vv 
pytest tests/test_calendar_engine.py -vv 
pytest tests/test_calendar_reminders_dispatch.py -vv 
pytest tests/test_calendar_reminders.py -vv 
pytest tests/test_calendar_views.py -vv 
pytest tests/test_calendar_pinned_embed.py -vv
pytest tests/test_calendar_pipeline.py -vv 
pytest tests/test_calendar_commands.py -vv 
pytest tests/test_event_generator_sourcekind_mapping.py -vv 
pytest tests/test_constants.py -vv 
pytest tests/test_event_calendar_datetime_utils.py -vv
pytest tests/test_calendar_cache_contract.py -vv 
pytest tests/test_calendar_schema_contract.py -vv 
pytest tests/test_calendar_service.py -vv
pytest tests/test_sheets_sync_flow.py -vv 
pytest tests/test_sheets_sync_parsers.py -vv
pytest tests/test_admin_calendar_commands_task3.py -vv 
pytest tests/test_calendar_service_telemetry_task3.py -vv 
pytest tests/test_calendar_publish_cache.py -vv 
pytest tests/test_event_generator.py -vv 
pytest tests/test_calendar_scheduler.py -vv 
pytest tests/test_calendar_runtime_cache.py -vv
pytest tests/test_calendar_status_embed_task4.py -vv

cd C:\discord_file_downloader
.\venv\Scripts\Activate
pytest tests/test_ark_reminder_phase_gh.py -vv
pytest tests/test_ark_cancel_match.py -vv
pytest tests/test_ark_cancel_match_view.py -vv
pytest tests/test_ark_cancel_dm.py -vv
pytest tests/test_ark_team_publish_mention.py -vv
pytest tests/test_ark_reminder_phase_c.py -vv
pytest tests/test_ark_reminder_phase_bd.py -vv
pytest tests/test_ark_reminder_reschedule.py -vv
pytest tests/test_ark_dal_team_workflow.py -vv
pytest tests/test_ark_confirm_publish_service.py -vv
pytest tests/test_ark_draft_service.py -vv 
pytest tests/test_ark_preference_commands.py -vv
pytest tests/test_ark_preference_service.py -vv 
pytest tests/test_ark_auto_create_service.py -vv 
pytest tests/test_ark_team_balancer.py -vv 
pytest tests/test_ark_team_state.py -vv 
pytest tests/test_ark_registration_messages.py -vv 
pytest tests/test_ark_confirmation_modal.py -vv 
pytest tests/test_ark_scheduler_post_start.py -vv
pytest tests/test_ark_dal_results.py -vv
pytest tests/test_ark_confirmation_view.py -vv
pytest tests/test_ark_fuzzy_select_view.py -vv 
pytest tests/test_ark_bans_enforcement.py -vv
pytest tests/test_ark_ban_utils.py -vv
pytest tests/test_ark_ban_commands.py -vv
pytest tests/test_ark_scheduler_status_gating.py -vv 
pytest tests/test_ark_scheduler_final_day_routing.py -vv 
pytest tests/test_ark_scheduler_grace_window.py -vv 
pytest tests/test_ark_scheduler_dm_failures.py -vv 
pytest tests/test_ark_reminder_prefs_command.py -vv 
pytest tests/test_ark_reminder_prefs.py -vv 
pytest tests/test_ark_reminder_prefs_view.py -vv
pytest tests/test_ark_reminder_state.py -vv 
pytest tests/test_ark_scheduler_reminders.py -vv
pytest tests/test_ark_confirmation_view.py -vv
pytest tests/test_ark_confirmation_embed.py -vv
pytest tests/test_ark_scheduler.py -vv
pytest tests/test_ark_confirmation_flow.py -vv
pytest tests/test_local_time_embed_title.py -vv
pytest tests/test_ark_admin_roster.py -vv
pytest tests/test_ark_registration_flow.py -vv
pytest tests/test_ark_embeds.py -vv
set RUN_CITYHALLLEVEL_TEST=1
pytest tests/test_cityhalllevel_cache.py -vv
pytest tests/test_ark_phase3a_create_match.py -vv
pytest tests/test_ark_phase3b_amend_match.py -vv
pytest tests/test_ark_registration_message_move.py -vv
pytest tests/test_ark_cancel_match.py -vv
pytest tests/test_ark_cancel_match_view.py -vv
pytest tests/test_rehydrate_views_and_localtime.py -vv
pytest tests/test_rehydrate_views.py -vv
pytest tests/test_rehydrate_sanitize_and_fileio.py -vv
pytest tests/test_kvk_helpers.py -vv
pytest tests/test_gsheet_module.py -vv
pytest tests/test_gsheet_sorting.py -vv
pytest tests/test_kvk_helpers.py -vv
pytest tests/test_gsheet_helpers.py -vv
pytest tests/test_ark_state_json_migration.py -vv

pytest tests/test_command_registration_smoke.py -vv
pytest tests/test_domain_registrars_no_legacy_register_commands.py -vv
pytest tests/test_commands_ui_helpers_present.py -vv 
pytest tests/test_admin_views_smoke.py -vv
pytest tests/test_subscription_views.py -vv
pytest tests/test_ui_imports.py -vv
pytest tests/test_events_views.py -vv
pytest tests/test_stats_views_smoke.py -vv
pytest tests/test_kvkrankingview.py -vv
pytest tests/test_registry_views_smoke.py -vv
pytest tests/test_location_views_smoke.py -vv
pytest tests/test_embed_utils_target_lookup_injection.py -vv


python -m py_compile Commands.py ui/views/admin_views.py ui/views/location_views.py ui/views/registry_views.py ui/views/stats_views.py tests/test_ui_imports.py

pytest tests/test_embed_utils_target_lookup_injection.py -vv
python -m py_compile embed_utils.py

python -m py_compile Commands.py ui/__init__.py ui/views/__init__.py ui/views/events_views.py command_regenerate.py tests/test_events_views.py
pytest tests/test_events_views.py -vv
python scripts/validate_command_registration.py
pytest tests/test_interaction_safety.py -vv

pytest tests/test_build_kvkrankings_embed.py -vv
pytest tests/test_kvkrankingview.py -vv

pytest -q tests/test_stats_service.py -vv
pytest -q tests/test_embed_my_stats.py -vv
pytest -q tests/test_stats_export.py -vv
pytest -q tests/test_stats_exporter_csv.py -vv

pytest -q tests/test_kvk_history_offload_and_utils.py

pytest -q tests/test_honor_importer.py
pytest -q tests/test_honor_rankings_view.py

pytest -q tests/test_crystaltech_service.py
pytest -q tests/test_account_picker.py
pytest -q tests/test_kvk_targets_views.py

pytest -q tests/test_registry_io.py
pytest -q tests/test_registry_io_xlsx.py
pytest -q tests/test_registry_io_error_roundtrip.py

pytest -q tests/test_prekvk_stats.py
pytest -q tests/test_prekvk_embed.py
pytest -q tests/test_prekvk_importer.py

pytest -q tests/test_gsheet_module.py
pytest -q tests/test_event_data_loader.py
pytest -q tests/test_player_stats_cache.py
pytest -q tests/test_prekvk_importer.py
pytest -q tests/test_proc_config_import.py
pytest -q tests/test_proc_config_import_phase2.py
pytest -q tests/test_sheet_importer.py
pytest -q tests/test_proc_config_import_offload.py
pytest -q tests/test_gsheet_helpers.py

pytest -q tests/test_event_cache.py

pytest -q tests/test_maintenance_suite.py

pytest -q tests/test_player_stats_cache.py
pytest -q tests/test_prekvk_importer.py
pytest -q tests/test_proc_config_import.py
pytest -q tests/test_proc_config_import_phase2.py
pytest -q tests/test_sheet_importer.py
pytest -q tests/test_proc_config_import_offload.py
pytest -q tests/test_gsheet_helpers.py

pytest -q tests/test_process_utils.py
pytest -q tests/test_file_utils_lockinfo.py
pytest -q tests/test_file_utils_2.py
pytest -q tests/test_file_utils.py

pytest -q tests/test_file_utils_2.py
pytest -q tests/test_file_utils_build_cmd.py

pytest -q tests/test_no_prints_in_cache_modules.py


pytest -q tests/test_live_queue_persistence.py

pytest -q tests/test_processing_pipeline.py

tests/test_processing_pipeline.py
tests/test_live_queue_persistence.py


pytest -q tests/test_offload_callable_integration.py
pytest -q tests/test_worker_module.py

pytest -q tests/test_offload_monitor_once.py
pytest -q tests/test_offload_registry_rotation.py

pytest -q tests/test_offload_serialization.py


pytest -q tests/test_file_utils_build_cmd.py
pytest -q tests/test_maintenance_worker_truncation.py
pytest -q tests/test_no_prints_in_cache_modules.py


## Phase 2G delivery and next task — 2026-09-08

**Phase 2G is complete as an implementation and bounded-validation delivery, by explicit operator
acceptance. Full live Pre-KVK validation is carried forward to Phase 2H; it is not claimed complete.**
This status supersedes preparation and intermediate status statements in this historical record.

Mirror PR #258 and production PR #565 were both OPEN when this closure was prepared. Reviewed
runtime heads are mirror `bd99ea1421286ddb152f7729e11de664116d7e47` and production
`fea2767f52f345450225bcdf0c1f03f3d5e3dc4c`; their Python trees match. Documentation closeout commits
follow these heads. Operator merges, final production-main source verification and bot-machine
deployed-head verification remain pending. Supplied restart logs contain no immutable Git head;
they cannot prove deployment of the final merged source. Codex has not merged or deployed either PR.

Delivered: durable reserve/start/accept/commit/release, conservative uncertain-send retention,
receipt recovery, off-season coordination, generation/CAS fencing, bounded Windows CSV replacement
retries and off-loop fighting/stale-reference invalidation. Phase 1–2F payload, permission,
visibility, mention, eligibility, edit/test and executor contracts remain preserved.

Final validation: full **3314 passed, 2 skipped**, production log-noise pass; **91** focused tests
with pinned filelock 3.20.0; **67** production focused tests; strengthened lifecycle assertions
passed separately (**3**). Pre-commit, architecture/deferred/security-routing validators, selector,
smoke imports and registration (36 primary / 100 grouped) passed. Full suite evidence transfers
through verified Python-tree identity; it was not independently rerun in production.

Changes-only / Deep-off security: mirror full scan `43cd6ae2-7ea7-40b1-89e2-c916b16b79f1`
through `fd93202f`, mirror delta `90ad6945-fded-4367-b915-ee5964414523` through `bd99ea14`, and
separate production scan `eba7b5b2-73ad-4b39-8e64-263362802657` for `d9321328..fea2767f`
completed with zero reportable findings and no deferred candidates. The final documentation-only
delta changes no executable, configuration, dependency, SQL, permission or persistence control;
an additional security scan and pytest run are skipped for that delta, with documentation/hooks
and routing validators required. SQL manifest remains empty; authoritative repo was clean at
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`.

Operator log evidence, 2026-09-08 09:16:40–09:22:06 (timestamps as supplied):

- Graceful shutdown drained queues, persisted state and cancelled registered tasks. Full startup
  completed at 09:17:05; reminder/live-event views reattached and command registration was unchanged.
- At 09:21:50 the normal fighting KVK route skipped Kingdom Summary (already sent) and KVK
  publication (daily cap). The generic subsequent “sent successfully” line is not a send receipt.
- No `[DISPATCH] Reserved` / `Committed` evidence appears. Fresh Pre-KVK/off-season ownership,
  matching CSV/journal/message references and restart-after-commit remain unobserved live.
- ProcConfig failed at 09:20:17 while restoring `conn.autocommit` with pending SQL results;
  later success reporting masked that failure. This unchanged pipeline is separate work.
- Tracked-view rehydration timed out after 10 seconds; remaining generic tracked views are
  unverified. Google Sheets 503 recovered on retry. Neither is silently counted as a clean pass.

Phase 2H owns an admin-only, mention-neutral, explicitly targeted diagnostic using the real
reservation flow and isolated durable journal/CSV/message state. Existing `is_test=True` bypasses
cannot establish reservation admission and still touch shared message state. The diagnostic must
support receipt inspection, repeat/guard/edit and restart verification without changing production
calendar data or weakening eligibility. Natural production calendar routing stays a distinct gate;
an isolated diagnostic cannot prove every live scheduling, contention or uncertain-send scenario.

Rollout/rollback requirements remain binding: stop all writers; back up CSV, message state and
journal together; no mixed versions; reconcile accepted/uncertain receipts before downgrade and
keep dispatch stopped if outcomes remain unknown. No exactly-once, cross-host or TTL-stealing claim.
The separate Phase 2F next-natural-public-save observation remains pending unless new evidence proves it.
## Phase 2H accepted delivery

Phase 2H isolated diagnostic smoke passed on deployed pre-merge commit `7794d2ae`. Phase 2G’s real reservation protocol was exercised successfully through isolated diagnostics. Production-state comparison passed for the observed status/edit operations. Natural production calendar dispatch remains separately pending.

Operator acceptance: 2026-09-08, Chris Watts. The Phase 2H pack/starter are archived.
Phase 2H #259/#566 and Phase 2I #260/#567 are merged. Phase 2I candidate smoke is accepted;
final merged-head process/restart association remains pending. Archived packs retain exact
receipts and historical evidence limits. Phase 2J retires ops publication on operator approval.
Phase 2F's natural public-save observation stays pending.

Current command: `/prekvk dispatch_test` v1.02. Final runtime suite: 3,381 passed, 2 skipped.

## Phase 2I fighting-KVK preview — delivered and operator-smoke accepted

The operator approved replacing `/kvk_admin test_embed` v1.04, including removal of `post_here`
and its seasonal production route. v1.05 requires an explicit ordinary non-production text
destination; `action` is run/status (default run), with an optional issued session token required
for status. This is the real fighting renderer with isolated durable preview publication records,
not production admission validation. Same-session runs edit the same message across restart/dates.
All new output disables mentions; uncertain sends/edits never trigger replacement.

Phase 2H PRs #259/#566 are merged. Verified remote mains: mirror `851ec046`, production
`3caf18e8a4955755ec5cbfe4830a4c57de15a41a`. Operator supplied corresponding restart evidence:
2026-09-08 14:06:02 graceful teardown/queue persistence, 14:06:12 registration 36/101,
14:06:26 successful startup. The log contains no immutable Git SHA; deployment association is
operator-provided. Tracked-view rehydration still timed out at 14:06:34 and remains separate.
Phase 2I pre-merge deployment and operator smoke are accepted; final main/deployed-head verification remains pending. Phase 2H sessions and production defaults
remain unchanged; natural calendar dispatch and Phase 2F natural public save remain pending.


### Approved historical fighting preview selection (Phase 2I v1.06)

`/kvk_admin test_embed destination:<test-channel> action:run kvk_no:15` starts an isolated,
explicit KVK 15 preview using that season's SQL metadata and real reporting blocks. The optional
integer selector accepts 1..2147483647; omitting it on a new session retains the current-KVK flow.
An explicit selection never falls back to current metadata or Sheets. Missing metadata or fighting
rows returns unavailable without publication. Honor is omitted for all explicitly selected-KVK
previews, and the private response explains why: the existing latest-honor reader is not bound to
that selection. Default/current production renderer behavior and honor handling are unchanged.

Explicit selections create version-2 session manifests with a durable `kvk_no`. Reopen run/status
with the same destination/token and omit `kvk_no` to reuse the saved selection, or supply the same
number. A conflicting number is rejected before dispatch or state changes. Version-1 current-KVK
sessions remain readable and retain their current-selection behavior; they cannot be retargeted.
Use a new session for historical selection. No migration of existing Phase 2I or Phase 2H files occurs.
Status remains read-only and does not query metadata/reporting. Malformed version-2 selections fail
closed. Downgrading to v1.05 or earlier leaves version-2 sessions unreadable; preserve them until the
supporting version is restored rather than rewriting/resetting their manifests.

The selector adds one option to the existing command, not a child or top-level command. Resync the
v1.06 command schema. Runtime delta: command adapter, preview runner/store/renderer, exact-season
metadata helper and lifecycle DAL reader. Tests cover real Pycord integer serialization/invocation,
SQL parameter binding, unavailable metadata, no latest/honor fallback, owner/season binding,
read-only status, reopening and same-message edits. No SQL schema, procedure, config, dependency,
calendar, reservation or production-state changes are required. SQL manifest: no SQL-repository
changes; bot-side read-only parameterized dbo.KVK_Details lookup validated against the SQL source.
Security routing remains Changes-only, Deep off, with final mirror and production target reviews.

Historical smoke: retain the existing unavailable KVK 16 session and production/Phase 2H baselines;
start a new KVK 15 session, verify title/data belong to 15 and honor is omitted, then status, repeat
run and restart/reopen with that token. All edits must retain the message ID and season. A conflicting
KVK selector must reject without sending/editing. Historical publication is not proof of natural
current-KVK dispatch, production admission or exactly-once; the separately pending observations remain.


## Accepted Phase 2I delivery — 2026-09-08

This status supersedes earlier candidate/pending-smoke statements. Chris Watts explicitly accepted
smoke testing as complete. Delivered and tested on the pre-merge production candidate; operator
merges and final main/deployed-head verification remain pending and open the next phase.

Reviewed runtime heads: mirror #260 `06f31a942a1b9b99b17769632beb58a760cb609a`; production #567
`d89e606cf83759bdda4a7b7fdeb96e17aef0d121`. Documentation-only closeout commits follow these heads.
No merge or deployment was performed by this documentation update.

Evidence supplied by the operator: current KVK 16 truthfully returned unavailable with no rows;
historical KVK 15 assembled 5 player, 5 kingdom and 4 camp entries and displayed successfully.
Status at 19:50:52 UTC retained selected KVK 15 and its committed operation; an edit at
19:51:52 UTC committed a new operation. The rejection in the instructed conflicting-selector
sequence was followed by status at 19:54:43 UTC retaining KVK 15 and the same committed operation.
Session tokens, destination identifiers and operation identifiers remain in private operator evidence. The generic rejection
text does not independently identify its cause. Operator reports restart returned the same results
and the capture helper matched the baseline with new diagnostic files created. These are operator
reports; raw message IDs, post-restart receipts and capture files were not independently inspected.

Validation: full mirror 3471 passed, 2 skipped; pinned-dependency matrix 129 passed; production
focused matrix 129 passed; applicable hooks and CI passed. Separate Changes-only, Deep-off reviews
of the two runtime heads covered all 19 changed files with zero findings. Sealed terminal reports
are retained; they are not desktop workbench scan IDs. This Markdown-only closeout has no runtime,
config, SQL, dependency, permission or persistence changes: additional pytest/security scans skipped;
documentation hooks, selector, architecture/deferred/security-routing validation remain required.

Natural production calendar dispatch is expected on 2026-09-09 morning, Europe/London; retain its
actual routing/admission/receipt evidence separately. Phase 2F natural public save remains pending.
Neither observation is closed by diagnostic success. Diagnostics do not prove exactly-once delivery
or all live failure modes. Generic tracked-view timeout and ProcConfig repair remain separate.

Next proposed scope: Phase 2J Ops Diagnostic Convergence, audit first. Preserve all Phase 1–2I
production defaults and existing Phase 2H/2I sessions. No Phase 2J runtime work is approved yet.


## Current S4B validation follow-up - 2026-09-11

S4B is accepted and merged; the current closeout record and archived pack supersede historical review-pending text. The remaining synthetic multi-period component test is complete. Track the [named follow-up register](docs/reference/kvk_source_migration/phase_2_implementation_plan.md#s4b-follow-ups) for S5B integration and S6 operational interruption, shared-quota throughput and capacity gates. These remain explicit acceptance work, not permission to execute future packs or activate routing.
