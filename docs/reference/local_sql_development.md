# Local SQL development environment

## Current delivery and next slice — 2026-09-12 post-S6 closeout

**S6 evidence/rehearsal delivered, accepted and merged; feature activation remains blocked.**
Mirror [#272](https://github.com/cwatts6/K98-bot-mirror/pull/272) merged at
19:20:50 UTC as `016df1e61c8017556a7e8ba8374d31375aebfb74`; production-repository
[#579](https://github.com/cwatts6/k98-bot/pull/579) merged at 19:21:34 UTC as
`a8c9c515066ca6ef079120b76dd160e3389badab` (reviewed/final head
`b9c84751d3cc1deaba0a5772ab45d89263fcb398`). Mirror review fix `fa1f4733` records
the missing public routing consumer. Bot local main/origin main is
`a2f148fa9bd4fb367fd46d0500a768c14fee915b`; SQL main/origin main remains
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Both were clean at this update's entry.

Operator reports merged and deployed locally, with nothing pushed to production.
GitHub confirms the production-repository merge above; **no production runtime or
bot-machine deployment, source activation, or fresh post-merge smoke is claimed**.
Local deployment is operator-attested; exact running process/config was not checked.

All preceding slices remain accepted. S6-OPS01/PERF01/CAP01 retain their open
operational components; accepted measured evidence is not pending reapproval.
The newly agreed requirements are fixed source per KVK for all affected outputs,
matched-pair public publication, confirmed reuse of an unchanged correction
counterpart, import-triggered serialized/latest-pending exports, export-only
recovery, retained input/publication history and safe output reuse after each KVK.
These are requirements, not claims of implemented behavior.

**Next: S7 Integration Contract and Implementation Planning**, documentation/read-only
scope after explicit S7 approval. Do not rerun predecessors or start later packs.
Carry every path in the post-S6 handoff manifest into the next separately authorized
slice PR, including both S6 archive move sides. No Git publication, SQL/provider
execution, restart, production promotion or activation is authorized by this update.
Earlier dated blocks below are historical and do not select the next task.

[Settled requirements](kvk_source_migration/post_s6_integration_requirements.md); [handoff and exact manifest](kvk_source_migration/post_s6_handoff_log.md); [S7 pack](../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md).

> **2026-09-12 S6 authenticated rehearsal update:** The operator restored the ignored
> local credential and approved the 5,806-player × ten-period synthetic benchmark,
> confirming both other importers would remain idle. Actual Google write/readback
> and local K98DEV rehearsal evidence now supersedes the earlier credential blocker.
> S6-OPS01, S6-PERF01 and S6-CAP01 remain OPEN for operator acceptance and the exact
> unresolved operational gates recorded in the latest appendix of both release
> documents and the S6 pack. No production activation or G5 acceptance is claimed.


> **2026-09-12 S6 output-provisioning update:** Separate S6 output creation was
> approved and completed: one private index and eight private slots, owner and
> service-account Editor metadata verified. Operator expectation is 2–3 exports/day,
> with no fixed maximum duration. Code review found no common lock across S6,
> all-KVK export and scan-data import. Runtime Google rehearsal is currently blocked
> by the missing configured local service-account key; no provider interruption or
> representative-load pass is claimed. All three S6 gates remain OPEN. See the latest
> provisioning appendix in the two release documents and S6 pack.


> **2026-09-12 S6 rehearsal update:** Chris Watts subsequently approved a local
> K98DEV database and beginning rehearsal. Synthetic local SQL/process checks passed
> in `K98_S6_Disposable_20260912`; no production activation occurred.
> S6-OPS01, S6-PERF01 and S6-CAP01 remain OPEN pending provider evidence and operator
> acceptance. Earlier G3-only/no-rehearsal statements below describe the retained
> preparation checkpoint, not the subsequent local rehearsal. See the dated
> rehearsal appendix in both S6 release documents for exact outcomes and gaps.


## Current S6 evidence preparation - 2026-09-12

**S6 G3 approved for documentation/evidence preparation only; stopped at G4.**
All preceding slices remain accepted; S5B-REC01 is closed. S6-OPS01, S6-PERF01 and
S6-CAP01 remain OPEN until separately authorized measurements and Chris Watts's acceptance.
G4 exact-operation approval and G5 acceptance remain operator-owned. No rehearsal, bot-machine
update, SQL operation, real import/export, Discord action, restart, deployment or activation.
The exact 18-path S6 documentation delivery includes all 16 pending closeout paths and both
S5B archive move sides. Eventual PR Files changed verification and promotion remain separately
authorized gates. Historical status blocks below retain their original dated evidence;
their pending/next-slice wording does not reopen accepted slices or authorize execution.

[Readiness and rollback](kvk_source_migration/release_readiness_and_rollback.md); [Canonical S6 evidence and delivery](kvk_source_migration/release_evidence_log.md).


## Current KVK delivery status - S5B closeout, 2026-09-12

**S5B is complete, operator accepted, successfully smoke tested and merged.**
Mirror [#271](https://github.com/cwatts6/K98-bot-mirror/pull/271) merged at 13:49:41 UTC as
`65c535dce831d0840f1a047b9c58f29c562df3df`; production
[#578](https://github.com/cwatts6/k98-bot/pull/578) merged at 13:50:14 UTC as
`c7e063f02ebe8287a584d0054ea14f91a0c0ecc6` on 2026-09-12, including final fix `e5bbd8f7`.
Local mirror main/origin main is `85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`, synchronized from
that production merge; the final recovery fix and tests match production/main. This closes the
prior mirror synchronization handover item. SQL main remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
Both repositories were clean at closeout entry. Local pulls are complete. The operator confirms
**no changes have been pulled to the bot machine**; repository merge is not runtime deployment.

Smoke acceptance is operator-reported and supported by recorded local import smoke and synthetic
recovery/transaction checks, not a fresh post-merge or bot-machine smoke. Final review-fix evidence:
186 focused tests passed, including five disposable SQL cases on local K98DEV database
`K98_S5B_Disposable_20260912`; split full suite 4,084 passed / 39 skipped, operational logs unchanged.
Imports, registration (36 top-level / 101 grouped), architecture, deferred-items, routing, lint/type
and staged secret checks passed. Production CI passed. Exact Changes review, Deep off,
`cf5a25c1-f9c6-431b-a2c6-fa9dba1716a7` completed with zero findings; earlier exact-slice evidence is
retained in the archived S5B pack. Historical results are not fresh tests of this closeout patch.

**Next: S6 Release Readiness and Controlled Activation in a new chat, after explicit S6 G3.**
All preceding slices remain accepted; S5B-REC01 is closed by accepted caller/lifecycle and disposable
SQL recovery evidence. S6 prepares documentation only and stops for separate G4 operational approval.
S6-OPS01, S6-PERF01 and S6-CAP01 remain open pre-activation evidence gates. G5 acceptance remains
operator-owned. The prepared S6 pack/starter require every pending closeout documentation change,
both S5B archive move sides and repaired links in the eventual separately authorized S6 PR.
No S6 execution or new chat is started by this closeout. Preserve all retained synthetic databases
and review evidence. Source routing and intake/recovery defaults remain disabled; no bot-machine
update, restart, production SQL, real import/export, Discord action, deployment or activation here.

## Historical KVK delivery status - S5A closeout, 2026-09-12

**S5A is complete, operator accepted, successfully smoke tested (operator reported) and merged.**
Mirror [#270](https://github.com/cwatts6/K98-bot-mirror/pull/270) merged at 08:53:35 UTC as
`c78823d5ae6852b251b2ea6dbc35fa2b4af7e42c`; private bot [#577](https://github.com/cwatts6/k98-bot/pull/577)
merged at 08:54:15 UTC as `dd69666a04daa47d6d596e694aff024a02417144` on 2026-09-12.
Local mirror main/origin main is `90aea74c93c6aad2c890d1783ff53f109cc7bf8a` (synchronized from that private merge);
local production/main matches the private merge. SQL main remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
Both repositories were clean at closeout entry; local pulls are complete. **No changes have been pulled
to the bot machine**, as explicitly confirmed by the operator. Repository promotion is not deployment.

Successful S5A smoke is operator-attested; its detailed environment, commands and transcript were not
supplied in this closeout. Do not infer live SQL, real provider/Discord execution or a bot-machine smoke.
Recorded deterministic evidence remains 162 focused tests and 4,033 full tests passed / 34 skipped,
operational logs unchanged, import smoke passed, and registration 36 top-level / 101 grouped.
Every command group is <=25 children (kvk_admin 8; largest ops 24). Exact Changes review, Deep off,
scan `541665eb-2d37-4e14-8ce9-038329bf9653` has complete coverage and zero findings. Earlier gaps
remain historical in the archived S5A delivery; these tests/reviews are not fresh closeout reruns.

**Next: S5B Endpoint Config and Recovery Integration in a new chat, after explicit S5B G3 approval.**
S3B/S4B/S5A prerequisites are accepted. The S5B pack/starter are prepared; no S5B implementation or new
chat is started by this closeout. Recheck both repos and preserve the exact pending documentation
carry-forward manifest in S5B, including both S5A archive move sides and repaired links.
Use mocks/fake destinations until an exact disposable SQL target and operations are explicitly
authorized. S5B's required transaction/recovery SQL evidence remains a separate execution prerequisite;
full S5B acceptance cannot substitute mocks for that requirement. Preserve all retained databases.

S5B-REC01 and S6-OPS01/PERF01/CAP01 remain open. S5A smoke does not close them. Source routing remains
disabled; intake/recovery defaults remain false. No bot-machine action, deployment or activation is
performed here. Historical statuses below are dated evidence, not instructions to rerun accepted slices.

## Historical S4B closeout - 2026-09-11

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


## S4A completed closeout — 2026-09-10

**S4A is complete, operator smoke accepted and merged.** Mirror [#268](https://github.com/cwatts6/K98-bot-mirror/pull/268) merged on 2026-09-10 at 16:12:39 UTC as `eba04639eced51e368d6fc7036284f25640ce871`; private bot [#575](https://github.com/cwatts6/k98-bot/pull/575) merged at 16:13:04 UTC as `021fc7adc9952ab07d21517e8e47f3966c285f7a`.
Operator candidate smoke on `055b9590e1114661ff0369c7815fbbea82661454` passed imports, registration **36/100** without drift/duplicates, **134 focused tests in 11.97s**, and **3,810 full-suite tests with 34 skipped in 134.19s**. Both pytest runs left operational logs unchanged. This closes the S4A full-suite gap; earlier stalls and passes remain historical evidence, not a post-merge rerun.
Local mirror `main` is `7baf92c7badc3f40006841046825a788bc823373`; local `production/main` is `021fc7adc9952ab07d21517e8e47f3966c285f7a`; SQL `main` remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Bot and SQL checkouts were clean at closeout entry. Local pulls are complete, per operator and local refs; **nothing has been pulled to the bot machine**.
S4A pack/starter are archived. **Next: S4B Versioned Exports and Delivery in a new chat, with separate S4B G3 approval.** S4B's pack requires all pending closeout documents and both archive rename sides in its eventual separately authorized PR. Prior S3B closeout documents were included in the merged S4A PRs.
Source routing remains disabled. No bot-machine update/restart, SQL deployment, live imports/exports, Discord action or activation is needed for S4B local development. Use mocks/fake destinations unless a disposable SQL target and exact operations are explicitly authorized first; preserve retained S2A/S2B/S3B databases. Historical prerequisite wording below does not reopen completed slices.

## Purpose and boundary

Use this permanent local SQL Server instance for explicitly approved development and disposable
integration tests. It is independent of the production SQL server. It is not a replicated mirror
and does not contain a production data copy. Authoritative SQL definitions remain in
`C:/K98-bot-SQL-Server`; database contents are test evidence, not the schema source of truth.

## Verified setup — 2026-09-09

| Setting | Value |
|---|---|
| Local server | `9SX2VF4\K98DEV` |
| Local connection alias | `localhost\K98DEV` |
| Engine | SQL Server 2022 Developer, 64-bit |
| Version | `16.0.1200.5` (KB5122771), matched to operator-supplied production version |
| Authentication | Windows Authentication; installing Windows user added as SQL administrator |
| Server collation | `SQL_Latin1_General_CP1_CI_AS` |
| Development database collation | `Latin1_General_CI_AS` |
| Database compatibility | `160` |
| SQL max server memory | `8192 MB`, configured and active; host has 32 GB RAM |
| Service | `SQL Server (K98DEV)` / `MSSQL$K98DEV`, Manual startup |
| Client | SSMS installed separately; local connection uses Trust server certificate |

The instance was patched and the PC restarted before the final version verification. Microsoft
signature and published update SHA-256 were checked. These are dated setup facts; verify the
current instance/database before each execution. Read-only service check on 2026-09-10 found
`MSSQL$K98DEV` stopped, with Manual startup unchanged.

## Starting a local session

1. Open SQL Server Configuration Manager, select SQL Server Services and start only
   SQL Server (K98DEV) if stopped. No production service or bot restart is involved.
2. In SSMS, connect to `localhost\K98DEV` using Windows Authentication. Trust server certificate
   is a setting for this local development connection; it is not a production connection policy.
3. Verify `SERVERPROPERTY('ServerName')`, `SERVERPROPERTY('ProductVersion')`, `DB_NAME()`, database
   collation and compatibility against the explicitly authorized target before executing SQL.

SQLCMD is available at
`C:/Program Files/Microsoft SQL Server/Client SDK/ODBC/170/Tools/Binn/SQLCMD.EXE`.
Prior local runs used explicit `-S lpc:localhost\K98DEV`, Windows authentication `-E`, `-C`, a
named database `-d` and fail-on-error `-b`. No password or production connection string is needed.
The agent sandbox could not authenticate; approved elevated local tool calls worked. This is
execution-environment behavior, not permission to search for credentials or alter security config.

## Retained S2A evidence database

`K98_S2A_Disposable_20260909` on the server above was explicitly authorized for S2A only. It has
the revised twelve S2A tables, 18 enabled/trusted foreign keys and 89 enabled/trusted CHECK
constraints. Last independent readback after the review fixes found zero rows in every table.
The fixture passed 96 expected rejection cases and positive correction/status checks, with full
rollback; the static validator passed 401 assertions. No production data was imported.

Retain this database as S2A evidence unless its rebuild/removal is separately within an approved
test operation. It is not an automatically authorized target for S2B or later slices.

## Retained S2B evidence — 2026-09-10

The operator authorized `9SX2VF4\K98DEV` and `K98_S2B_Disposable_20260910` for S2B.
Creation with compatibility 160 and `Latin1_General_CI_AS`, accepted S2A prerequisite
installation and migration `20260910_001_kvk_source_publication_state.sql` passed.
The service was already running at execution; no start or restart occurred.
Initial validation passed 131 rejection cases; the S2B PR review revision passed 144, with
265 static assertions and full 25-table rollback. The reviewed migration was retested by
transactionally replacing only verified-empty S2B tables in this same authorized database.
The accepted S2A migration and separate S2A evidence database were preserved. Independent
readback found 25 empty tables, 47 trusted/enabled FKs and 165 trusted/enabled CHECKs.
The separate S2A evidence database remained unchanged. Both databases are retained.

## Future slices

The instance can be reused; each slice must explicitly name and authorize its disposable database.
S2B authorization and completed execution are recorded above; neither retained evidence database
is automatically authorized for a later slice or destructive rebuild.
Use synthetic fixtures and the accepted S2A migration as prerequisites; installing prerequisites
in a fresh test database does not reopen S2A implementation or automatically execute another pack.

Keep migrations/fixtures in their owning slice's exact SQL manifest. Recheck migration date and
sequence at authoring time; the proposal in a prepared task pack is not an allocated slot.
Production deployment, real imports/exports, Discord actions and source activation remain separate.

## S2B repository closeout — 2026-09-10

S2B SQL #79, mirror #265 and private bot #572 are merged. Both local repositories were pulled
by the operator; the bot machine was not updated. Repository merge is not production SQL
execution. Preserve both evidence databases. S3A uses pure offline tests and requires no SQL
connection, database rebuild, bot restart or source activation.


## S3A merged closeout and S3B handoff — 2026-09-10

GitHub readback confirms mirror #266 merged at 11:28:48 UTC as
`3154997fa2dfc124da75ee35dca79463c3196a43`, and private bot #573 at 11:29:18 UTC as
`140fc89765b1d6ec8418ac6f6d039e575419c29e`. The synchronized local mirror main is
`9d08b3bf9e7cac6c95db1c4a120c8bf0aad7475f`; SQL main is
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Both local repos were clean at documentation
entry. Operator confirms local pulls complete, with no bot-machine pull or restart.

Operator smoke on mirror `d5cf27613e54047efb856f4bc3777ee6923fa14e` passed 77 tests in
3.10s, operational logs unchanged, and command registration 36/100 without drift or duplicates.
The prior implementation/regression results (260 tests) and separate completed production/mirror
Changes reviews remain in the archived S3A pack; those are historical runs, not newly rerun here.
S3A runtime/test contents matched the production candidate. Repository merge is not deployment.

S3A pack and starter are archived with repaired links. All predecessor evidence is retained.
Start S3B in a new chat using its refreshed pack/starter only with explicit S3B G3 approval and
an explicitly named disposable SQL integration target. Existing S2A/S2B evidence databases are
retained and not authorized for reuse/rebuild by this handoff. The bot machine need not be updated
for S3B local development. No SQL connection, service start, production action or successor
implementation occurred in this documentation closeout.

These documentation edits, including untracked archive destinations, remain pending for the
separately authorized S3B PR. Its pack contains the full carried-forward manifest and requires
both sides of renames, repaired links and preservation checks. No commit/push/PR is performed
by this closeout. Security routing: exact Markdown-only skip (status, evidence, links and archive
moves; no runtime/config/permission/data-access effect), plus separate SQL no-change skip.

## S3B merged closeout and S4A handoff — 2026-09-10

**S3B is complete, operator smoke accepted and merged.** Mirror
[PR #267](https://github.com/cwatts6/K98-bot-mirror/pull/267) merged at 13:59:47 UTC as
`e915f9727f9492fe4ecc02b5c0d9f3c6e443be13`; private bot
[PR #574](https://github.com/cwatts6/k98-bot/pull/574) merged at 14:01:14 UTC as
`a8ad9f1d81cfb7884a9cdcc0b067c4346a204488` on 2026-09-10.
Operator post-merge smoke on mirror main `e915f972`: import smoke passed, registration
36/100 without drift or duplicates, **36 tests passed in 9.11s** (4 publication + 32 SQL).
Current synchronized local mirror main is `02385a0edc0ec83f77241e02648eabb3b7640ea6`;
local production/main is `a8ad9f1d81cfb7884a9cdcc0b067c4346a204488`; SQL main remains
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Both repos were clean at closeout entry.
S3B pack/starter are archived. **Next: S4A Shared Reports and Cards in a new chat, with
separate S4A G3 approval.** Preserve pending S3B closeout docs and both archive moves
for the eventual separately authorized S4A PR; its pack contains the complete manifest.
S3B's latest full-suite rerun stalled around 19% and remains incomplete; the accepted smoke
does not replace it. The earlier 3,764-pass full result is pre-review-fix evidence.

The operator confirms local pulls completed and no changes were pulled to the bot machine.
No bot-machine restart, production SQL deployment or source activation is evidenced or performed.
S4A local development does not require a bot-machine deployment. New routing remains disabled.

The accepted S3B boundary includes immutable acceptance, atomic publication and four review fixes:
rollback delivery reconciliation with increasing fences; aggregate rejection for equal-endpoint
no-fight windows; complete immutable action replay scope; accepted revision period-scope checks.
All five inline threads were replied to and resolved before merge. The two separate final
five-file Changes reviews, Deep off, completed with zero findings/deferred/open questions:
mirror `308e7130-8e09-45fc-9765-c4c9673fc21f`, private
`97196427-2c4a-40e5-acbd-3f3c3f71c6e9`. Earlier implementation/security evidence is retained.

Preserve the operator-approved endpoint amendment: either StartScanID or EndScanID may change;
a supplied end must be >= start. Distinct imported scans advance both ScanID and UTC scan start,
oldest first; semantic re-exports allocate no new scan. Blank/future end uses the latest eligible
interim; an available end pins the final, and an authorized endpoint update permits replacement
without a separate correction command. Equal endpoints produce zero supported fight scores for
every frozen B0-eligible member, including absent scan members, with aggregates not applicable.
Ordinary missing-data states remain explicit. Aggregate reports and daily SCANORDER stay separate.

The authorized S3B test target was `9SX2VF4\K98DEV` /
`K98_S3B_Disposable_20260910`, including prerequisite schema and synthetic two-connection tests.
Retain this database and the separate S2A/S2B evidence databases; no reuse/rebuild for S4A is
implicitly authorized. S4A uses mocks by default; any SQL integration must first have an explicitly
authorized disposable target and operations. No connection or setup was performed in this closeout.

The supplied transcript shows 36 passed in 9.11s on merged mirror main `e915f972`, import smoke
success and registration 36/100 without drift/duplicates. Its raw attachment stays outside Git.
The current synchronized main contains identical KVK source and these test files to private merge
`a8ad9f1d`. Historical 257 affected regressions passed with logs unchanged. The operator smoke
did not run the log-noise wrapper, so it is not new log-hygiene or full-suite evidence.
The interrupted post-review full suite remains an explicit S4A validation follow-up; investigate
its cause and run the required full suite/log-noise gate without silently expanding runtime scope.

S3B pack and historical starter are archived, with links repaired and delivery history retained.
The S4A pack/starter require all pending closeout documentation, including untracked archive
destinations and both source deletions, in the eventual separately authorized S4A PR.
These edits stay uncommitted for that handoff. No new chat or S4A implementation is started here.
Documentation-only security skip: exact closeout/status/links/archive manifest, no runtime,
configuration, permission, data-access or deployment effect. SQL repository: separate no-change skip.
Runtime pytest/smoke/registration reruns are skipped for this Markdown-only closeout.
