# MGE finalisation: native SQL and updater qualification packet

Prepared 29 October 2026; updated after the bounded implementation approval.
**Review candidate; not an executable production release.** A1 implementation,
A2 read-only local discovery and A6 review-PR publication/comment management are
now authorized. The subsequent operator instruction also authorizes reviewed source
merges and private promotion (A7). Database creation/writes, updater installation and deployment
remain behind their separate approvals.
The approved MGE implementation direction remains accepted. This packet defines
the additional work and evidence needed to release it; it does not reopen that
direction or repeat accepted A1b operations.

**Verdict: source merge/promotion authorized; deployment blocked.** The bounded updater extension and native
harness have been authored and reviewed. Production bindings and native write qualification
remain outstanding. Only SELECT-based SQL discovery has executed.

The operator's subsequent instruction is to merge the reviewed work and prepare a
deployment, verification and confirmation plan. This supersedes only the source
merge/promotion hold in this dated packet. It does not authorize operational SQL
writes, tool installation or deployment. Initial adoption remains fail-closed until
the separately reviewed MGE profile and descriptor are committed. See the
[deployment and confirmation plan](P1%20MGE%20Finalisation%20-%20Deployment%20and%20Confirmation%20Plan%20-%202026-10-29.md).

## Approved implementation follow-up

The SQL branch now supplies `mge_finalisation_v1` through the existing release
lock/attempt/transaction/receipt protocol. Its fixed five batches create only the
finalisation table/index and three freeze triggers, with absent preimages and
independent structural/trigger postimages. Profiles cannot supply arbitrary SQL,
objects or grants. Historical migrations remain unchanged; the new MGE migration
received required comment metadata during CI review, without changing its executable
body. Its original preparation hash is superseded. Partial/manual installations
are refused.

The Bot updater adds one exact 20-member finalisation transition (14 changed runtime
members and six unchanged dependencies), preserving all 51 historical entries.
The registry permits 52 entries and 110592 bytes. Initial finalisation adoption
requires a changed MGE combined descriptor: the unchanged old KVK descriptor cannot
admit this code as a source-only update. Profile/descriptor authoring helpers require
explicit observed bindings. No production descriptor or profile is invented before A4.

The SQL native harness defaults to SELECT-only discovery. Its explicit write mode
requires a separately approved, already-created empty SIMPLE database, exact login,
creation timestamp/files/backup, collations/compatibility, clean source commits,
approval-byte SHA256 and matching environment opt-in. It never creates/drops a
database. Named child interruption targets only handles created by that run. Actual
DAL/SqlClient/pyodbc cases retain results and refuse blind replay or cleanup.

Read-only discovery verified `9SX2VF4\K98DEV` via `lpc:localhost\K98DEV`, version
16.0.1210.3; server/tempdb collation is `SQL_Latin1_General_CP1_CI_AS`.
`K98_MGE_Finalisation_Qualification_20261029_A` does not exist. Data/log directory:
`C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\`; approximately
1.60 TB free was observed. Proposed files are the database name plus `.mdf`/`.ldf`.
Backup directory: `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\Backup`;
its access/capacity remains unverified. The harness proposes
`K98_MGE_Finalisation_Qualification_20261029_A_qualification.bak` there. Private
evidence retains the exact integrated login; it is not published to the mirror.
Creation timestamp and actual database collation/compatibility cannot be observed
until separately approved creation. No other database was modified.

Offline SQL evidence: 14 guard/import tests and native PowerShell 5.1 parser/profile
construction/dispatch/hash checks passed. A reserved discovery-query alias was
corrected after a read-only syntax failure; the harness's SELECT-only discovery
then passed. All N00–N16 write exercises and protected Windows U05–U13 remain NOT RUN.
The existing combined-updater tools supply the protected stage rehearsal after A5;
the new SQL harness does not claim Windows custody or end-to-end deployment evidence.

The original fingerprint JSON below remains a dated preparation snapshot, not the
new updater's current fingerprints or a deployment manifest.

### Review and validation closeout

- Draft [Bot mirror PR #459](https://github.com/cwatts6/K98-bot-mirror/pull/459):
  executable review target `00d3b7fb8e7d6ed40fafbca51b5293bf00855310`. Automated code
  review found no major issues. Command-governance CI passed. Subsequent changes
  correct only historical registry-bound test assertions and this evidence record.
- Draft [SQL PR #134](https://github.com/cwatts6/K98-bot-SQL-Server/pull/134):
  final review branch `626a1811060f40ad02a74b9030336b29097863db`. CI passed. Review
  identified an awarded-signup FK masking the intended trigger test; `3c5b7d0`
  isolates an unreferenced frozen signup, verifies preservation, and the comment
  was answered/resolved. Re-review found no major issues. Later delta is docs only.
- Bot Changes scan `44efed4c-c97c-4a32-91b0-9421835b06e3`, base `139038e` to
  `00d3b7f`: 18 source/configuration files and 12 test/support files covered,
  no reportable findings. SQL Changes scan `2abbbb8c-8453-4505-9178-a9d9bcba84fd`,
  base `7e91989` to `8a9be2d`: all 15 changed source files covered, no reportable
  findings. Deep was off. Exact subsequent deltas are comment metadata/docs,
  a narrower synthetic delete fixture, and count/byte-bound test expectations;
  runtime/deployment/authorization policy is unchanged, so repeat scans are skipped
  for those reviewed deltas. No native acceptance is inferred.
- Full offline Bot suite: **10640 passed, 1100 skipped, 8 subtests passed; seven
  failures** were stale 51-entry/102400-byte expectations in three historical test
  files. They were corrected to the reviewed 52-entry/110592-byte bounds while
  preserving all historical source hashes. **All 516 affected updater/transition
  tests then passed**, with production operational logs unchanged. No fresh full
  all-green run is claimed; only test assertions/docs changed after the full run.
- Fourteen SQL offline guard/import tests pass; PowerShell 5.1 parser/profile
  checks pass. Existing combined-updater simulation passes **15 interruption/resume
  cases**, with no production access. This is not protected Windows/native SQL
  qualification. Architecture/deferred/security routing, smoke imports, command
  registration and changed-file pre-commit passed.
- A candidate updater installer was built locally, **not installed**, from the
  exact reviewed source. SHA256:
  `d67b522de984a8bc7de3f42c6f3184be5e6475bc8743bcfd983544bf0f72b9b2`.
  Candidate tool-manifest SHA256:
  `8ae43293649ae6100d0a89eb3a2c31ceb2319bb83c4d5a8d3db9487c85c9c5f7`.
  All 12 embedded tool members were verified against that commit. An authenticated
  upgrade is intentionally unbound until A4 observes the actual installed manifest.

Remaining decisions are A3 (exact disposable creation/writes/backup and named child
faults), A4 (bounded production read-only inventory), A5 (isolated protected updater
rehearsal), A8 (installed-tool upgrade), A9 (production
preparation/deployment), and A10 (bounded acceptance/cleanup). Backup-directory
access/capacity is still unresolved; database creation and writes have not occurred.
Review publication is complete and does not satisfy any of these remaining gates.

Read with the [implementation and validation record](P1%20MGE%20Finalisation%20and%20Shared%20Board%20Lifecycle%20-%202026-10-29.md),
[Promotion Guide](../reference/Promotion%20Guide.md),
[Combined Updater](../reference/Combined%20Updater.md) and
[S11 release contract](../reference/S11%20Deployment%20and%20Restart%20Contract.md).
The [qualification manifest](evidence/mge_finalisation_qualification_20261029.json)
pins committed source bytes and records unresolved bindings as null. It is evidence
metadata, not `deploy/k98-release.json`, an installed policy, or a deployment manifest.

## 1. Exact source targets and evidence already available

| Target | Exact revision / scope |
|---|---|
| Bot implementation | `a333656c1168c7da449cee30653140269ad8fdc4`, branch `codex/mge-board-finalisation` |
| Bot mirror base | `139038e416c657cb589f24ca8a4ff61a913b7a3b` |
| Private production main observed this turn | `2c31de42eb91cf6b7f9f61f3aaf3efc3597c4ea6` |
| SQL implementation | `d649d6d659a586939e6566dd48c1ece6d3310e9a`, separate SQL branch `codex/mge-board-finalisation` |
| SQL base / remote main observed this turn | `7e91989f619deb46836194c7e705b0a9eb2ebe11` |
| SQL migration | `migrations/20261029_001_mge_board_finalisation.sql`; ID `20261029_001_mge_board_finalisation` |
| Exact migration Git blob | 3,511 bytes; SHA256 `fd64e9e6cd9b42d1fcd69ed81e012cac66a14baabbf7641fd78825fd0c52d633` |
| Native test implementation target | The bot/SQL implementation pair above; pin any later fix as a new pair and rerun affected cases |
| Final production release target | **Unbound**: future reviewed private `K98-bot/main` merge commit, never the mirror commit |
| Final SQL release target | **Unbound**: future reviewed SQL commit containing the compatible release profile/runner and required migration; must be reachable from SQL main |

Remote refs were read with `git ls-remote` for all three repositories and match
the local baselines. This is repository evidence, not evidence of the running bot
or installed database. Re-resolve refs before publication; do not reset existing work.

The bot worktree is
`C:\Users\cwatt\.codex\worktrees\mge-board-finalisation\discord_file_downloader`.
The SQL worktree is
`C:\discord_file_downloader\.codex_artifacts\mge-board-finalisation-sql`, attached
to the authoritative `C:\K98-bot-SQL-Server` repository. Both implementation
checkouts were clean at preparation start. Original checkouts are preserved.

Existing local evidence: full offline run 10,593 passed / 1,100 skipped / one stale
fingerprint assertion failed; that assertion was corrected and the 239 affected
tests passed with operational logs unchanged. The full run was not repeated after
the correction. Before production promotion, run the full suite on the final
release-authoring code, with the log-noise wrapper and retained output.

Separate Changes reviews, Deep off, found zero security findings:

- Bot `eaf3b342-16dc-4dd2-9b2c-3b76ad82bbd9`: mirror base through `c299d64e9f1f1e69e0e013d88616ce027bf9abb2`.
- SQL `1bb61a7b-905a-43e1-9cbb-3d57be134c0c`: SQL base through `d649d6d659a586939e6566dd48c1ece6d3310e9a`.

The bot closeout's message/test/documentation delta has its precise recorded skip.
These scans do not cover a future updater extension, native harness or release
descriptor. Those require new per-repository Changes decisions against exact diffs.

## 2. Release blockers established by current source

| ID | Evidence and consequence | Required resolution |
|---|---|---|
| B1 | `scripts/prepare_k98_update.py::validate_combined_description` accepts only `module_grants_v1` and `additive_tables_v1`. SQL `SqlDeploy.ModuleRelease.ps1` admits existing P/V modules, not new triggers. | Design, implement and review a narrowly bounded table-plus-trigger release capability, reusing the existing runner/ledgers. Do not route arbitrary SQL through an unrelated profile. |
| B2 | `additive_tables_v1` has no `rowversion`, defaults, ordinary nonunique index or trigger declaration. The finalisation table uses all of these; its checks also exceed the existing bounded expression vocabulary. | Explicitly support and independently verify every required metadata feature, or propose an equivalent reviewed release design. Do not weaken the finalisation schema to fit today's profile. |
| B3 | No `20261029_001_mge_board_finalisation.release.json` exists. Bot `deploy/k98-release.json` still names `20261013_001_kvk_export_history`, SQL `544b401a657246522d295bbc2644bed64a448fbd`, predecessor `ce754d15c4d71c234835ca5ac23635ce353f21bd`. An unchanged descriptor selects a source-only update. | Commit the actual MGE release profile and changed descriptor only after the supported capability, real predecessor and reviewed environment are bound. Do not reapply the historical KVK migration or remove the old descriptor as a shortcut. |
| B4 | The installed-policy source code has 51 bounded transition entries and no finalisation bundle. Existing protected MGE files require an exact complete installed transition. | Author the exact before/after inventory, including new runtime files and peer requirements; explicitly update and test the bounded registry policy. The test-only source bridge grants no release authority. |
| B5 | The migration creates the table and work index inside one `IF table absent` block. A pre-existing table with a missing index is skipped on rerun. Its `GO` batches are not a self-contained atomic deployment protocol. | Native tests must expose partial installation. The release verifier must refuse incomplete state and the release implementation must provide an atomic install or an explicitly reviewed recovery. A second successful script exit is insufficient. |
| B6 | Current checkout `origin` push URL is `no-push://private-checkout-mirror-disabled`; `production` is pushable. | Use an explicitly selected mirror publication checkout/connection or approved bounded remote repair. Never fall through to production because mirror push is disabled. |
| B7 | Current live predecessor, installed `update-tool.json`, native target metadata, backup proof, principal and source custody are unobserved for this release. | Obtain the exact bounded observations under the corresponding approvals below. Do not copy older values into new expected bindings. |

The historical arbitrary-SQL path in `Deploy-SqlMigration.ps1` is not the normal
combined-release receipt protocol. Its `-ValidationOnly` is not a no-connection
dry run. Do not invoke it, skip backup checks, or use a standalone manual SQL
apply to avoid B1–B5. The old running bot must be drained before the freeze
triggers are installed because it can edit historical Discord messages before
its later SQL write is refused.

## 3. Native SQL target and controlled fixture

Proposed local target, requiring approval and identity verification:

| Binding | Proposed value / required observation |
|---|---|
| Transport | `lpc:localhost\K98DEV`, on the development machine only |
| Expected `SERVERPROPERTY('ServerName')` | `9SX2VF4\K98DEV`, from the existing local-development contract; confirm before use |
| New database name | `K98_MGE_Finalisation_Qualification_20261029_A`; existence has not been queried |
| Data/log/backup paths | Unbound until local default directories and free space are observed; bind exact filenames before creation approval |
| Login and effective permissions | Unbound; record `ORIGINAL_LOGIN()`, `SUSER_SNAME()`, `USER_NAME()` and the native process SID/elevation. Do not infer SQL login from Windows display name. |
| SQL version, database/tempdb collation, compatibility, recovery/isolation | Unbound; capture and compare with the intended production contract, including RCSI/snapshot settings and trigger settings |
| Drivers | Actual Windows PowerShell 5.1 / SqlClient for release stages; the supported Python/pyodbc/ODBC driver used by the bot DAL, with versions recorded |

Use a fresh synthetic database, not a production clone or an existing recovery
database. If the proposed name already exists, stop and review its ownership; do
not drop, reuse or generate a silent alternative. Preserve
`S11_G4_Recovery_20260928_97337`, its files/media and all other existing databases.
The production endpoint `MINI_AMD` / `ROK_TRACKER` is a repository default and a
future approval target, not a verified live binding for this packet.

Fixture installation order is the exact SQL definitions at the pinned SQL head:
`MGE_Variants`, `MGE_Commanders`, `MGE_Events`, `MGE_Signups`, `MGE_Awards`, then
`MGE_SignupAudit`, `MGE_AwardAudit`, `MGE_DefaultRules`, `MGE_RuleAudit`,
`MGE_ResultImports`, `MGE_FinalResults`. Resolve their declared FKs and retain
normal enabled constraints; do not simplify the shape or scan/apply every file
in `sql_schema`. The qualification manifest pins these files. Add the existing
deployment ledgers only when testing the reviewed release protocol, using their
exact reviewed definitions. Any further dependency requires explicit inventory.

Use synthetic active/completed events, signup and award rows with original
channel/message IDs represented by inert test values. Keep a fixture ID ledger.
Bind every connection explicitly to this database and validate server, database
and approved login on that same connection before any mutation. Never load a
production `.env`, launch the bot, invoke calendar sync, or contact Discord/Sheets.
Exercise real DAL callbacks with an injected native connection; Discord adapters
remain fakes. The native harness is now authored in the SQL review branch; its write mode has
not executed. The implementation follow-up above supersedes the original proposal. Existing KVK table/module rehearsal scripts are
reference patterns; their target guards and fixture domains do not qualify MGE.

## 4. Native SQL check matrix

All cases start `NOT RUN`. Each result must record source pair, case ID, fixture
IDs, connection/driver/isolation, UTC times, actual rows/errors, commit/rollback
outcome and retained evidence path. Expected rejection is a passing negative case
only when state preservation is independently checked.

| ID | Exercise | Required result |
|---|---|---|
| N00 | Identity guard: wrong instance, database, login or source hashes | Refuse before DDL/DML; zero mutation. Confirm fresh target and dependency inventory. |
| N01 | First install through real SqlClient batches, then exact repeat | Table, rowversion, defaults, PK/FK/checks, index and all three enabled triggers match expected metadata. Repeat changes no data, identities or existing payloads. Record actual batch splitting and driver behavior. |
| N02 | Interrupted install after table creation, before index, and between trigger batches | No false success. Expose B5; require explicit refusal/verified atomic rollback or reviewed recovery, with originals retained. Check disabled/altered trigger, missing index and altered columns separately. |
| N03 | Active signup, award and rules writers using their actual `OUTPUT INTO` code | Correct ID/result rows with enabled triggers; rowcounts and additional result sets work in the real driver. Audit and primary mutation commit together where the caller promises atomicity. |
| N04 | Complete an eligible event with three saved identities | One transaction commits completed state plus exactly three targets, one generation, retained publication version and original IDs. Complete again produces no new target/generation. |
| N05 | Complete with zero/one/two targets; partial or nonpositive saved identity pair; invalid status | Complete valid absent pairs without invented targets. Invalid pair/status does not partially complete or insert inventory. Existing completed history is never backfilled. |
| N06 | Force inventory insertion failure after the event UPDATE, then kill only the fixture client before commit | Event remains active and no target inventory commits; transaction rollback proven from a new connection. No business replay based only on connection loss. |
| N07 | Client loss after commit but before acknowledgement | Completed event plus exact inventory survive. Reconciliation reads the durable result without reopening, recreating targets or replaying completion writes. |
| N08 | Stale direct INSERT/UPDATE/DELETE to completed events/signups/awards, including moving children into/out of completed events and mixed multi-row statements | Error 51830 where the freeze guard is reached; entire statement/transaction follows its verified rollback contract. No mixed active-row partial commit. Separate FK rejection from actual trigger coverage. |
| N09 | Two-connection writer/completion races, both acquisition orders | Barrier-controlled schedule: writer first must settle before freeze; completion first blocks/rejects later writer. Retain locks, SQL errors and both outcomes. Deadlock victims roll back; no automatic retry of an unknown business outcome. |
| N10 | Final-target transition with stale rowversion, generation, event/board, publication version or destination | Zero rows changed; original immutable payload/identity remains. Valid CAS changes one row and yields a fresh byte-valued revision through pyodbc. |
| N11 | Confirmed/retired terminal transitions, attempted payload replacement, retirement actor validation | Bot DAL refuses terminal changes and retains first payload. Unauthorized/invalid actor is rejected before write; DB constraints independently hold. Do not claim SQL alone enforces every DAL transition rule. |
| N12 | Two connections race settlement/retirement using the same preview revision | At most one winning transition; stale confirmation cannot retire a changed target. Unknown edit cannot be retired via the application preview path. |
| N13 | Saved payload, process restart and lost Discord edit acknowledgement, with fake Discord and native SQL | Unknown state survives; matching readback confirms without editing again; mismatch holds; 404/403 remain distinct. No replacement send. Confirmed/held/retired targets perform zero routine network work. |
| N14 | Result import and summary reads after completion | Synthetic result import persists through the actual result DAL into `MGE_ResultImports`/`MGE_FinalResults`; audits/results remain readable. Freeze blocks mutable roster/event state without blocking the independent result workflow. |
| N15 | Multi-call legacy roster operations interrupted around completion | Document each committed/rolled-back call separately; no assertion of whole-operation atomicity. Detect any frozen inconsistent result needing a separately reviewed fix. |
| N16 | Representative active/pending/terminal inventory, >50 pending events | Keyset traversal covers each eligible event without offset loss; measure SQL calls, durations, row/target counts and index use. Historical terminal targets add no Discord IO; full count-query cost is still measured. |

Run each race using explicit barriers and bounded lock timeouts, not timing sleeps
as proof. Process-loss cases terminate only a named child fixture process and
require explicit approval for that fault injection. Never terminate SQL Server,
the bot, an updater or a process identified only by a stale PID. Retain fixture
databases/backups/transcripts after qualification; cleanup is a separate decision.

## 5. Required release-authoring slice

Recommended approach: extend the existing bounded combined updater and SQL
ledger protocol for this exact table/index/trigger family. Reuse exclusive release
ownership, immutable intents, authoritative verification and safe resume. Do not
invent a second MGE scheduler, a generic arbitrary-SQL executor, or a one-off live
patch launcher. This bounded implementation scope is now approved; production bindings and native
execution remain separately gated.

Its reviewed contract must cover:

1. Exact absent/existing preimages and independent postimages for the table,
   named constraints/defaults/work index, rowversion and three trigger definitions,
   parent bindings, events, enabled state, ANSI_NULLS and QUOTED_IDENTIFIER.
2. Atomic schema changes plus Applied/Succeeded receipts where supported; retained
   attempt and proven rollback otherwise. Existing partial objects without matching
   history are refused rather than adopted. Immutable migration IDs cannot be
   repurposed after an attempt; use a reviewed corrective identity if needed.
3. Explicit collation/compatibility/principal and backup requirements, protected
   object exclusions, metadata visibility, DDL/ledger-trigger handling, no backfill,
   and no unexpected grants or side effects.
4. Committed LF profile/module bytes, exact SQL Git commit and hashes, real driver
   encoding/batch behavior, preserved old migration bytes and profile history.
   The source `.sql` hash and a future `.release.json` hash are different contracts.
5. The complete MGE predecessor/successor source transition in installed tooling,
   the new runtime members and full startup source inventory. Preserve all older
   registered transitions and test the revised count/size bounds. Merely raising
   the count bound or copying the test bridge is insufficient.
6. A changed Bot release descriptor selecting only the reviewed MGE migration
   profile, exact SQL commit and **observed installed private Bot predecessor**.
   The descriptor must be committed before the final Bot target is selected.
7. An authenticated updater upgrade from the actual installed `update-tool.json`
   to the reviewed candidate tool, using the existing upgrade mechanism and retained
   predecessor. No hand-editing installed policy or live source fingerprints.

The existing generic `prepare_k98_release --specification ... --output ...` packs
reviewed inputs without executing them; it does not fill these missing capability,
receipt or verification contracts. Do not manufacture a runnable specification now.

## 6. Updater qualification checks

| ID | Check | Pass evidence |
|---|---|---|
| U00 | Exact private candidate/predecessor, SQL ancestor and installed tool | Full commits, tree/patch comparison, actual old manifest bytes/hash, candidate tool hash and explicit profile IDs/order. Mirror-only comparison is not installed compatibility. |
| U01 | Existing updater refusal | Current unsupported MGE profile/source bundle is rejected before drain; no suppression, target-supplied exemption or modified expected hash. |
| U02 | Descriptor/profile validation | Wrong predecessor, SQL commit/hash, missing member, duplicate ID, wrong order, unsupported feature and altered file each refuse. Profile and descriptor removal cannot turn a SQL change into source-only success. |
| U03 | Exact transition and inventory | Full final source bundle passes; every missing/extra/changed peer fails. New modules included in seed/source inventories. Historical 51 entries remain exact; new bounded policy is tested explicitly. |
| U04 | Actual SqlClient preflight | Exact reviewed environment, permissions, visible metadata, backup history, dependency ledger and preimages pass. Native SQL target differs from the isolated test target only by reviewed bound values. |
| U05 | Protected native Windows rehearsal | Real PowerShell 5.1, observed owner/SID/elevation, production-like inheritance/metadata, configured Git/Python, fresh-object custody, ACL/reparse/hard-link/alternate-stream/prior-handle checks and retained originals. Surrogate fixtures are labelled separately. |
| U06 | Startup SQL/source contract compatibility | Run existing comparators against the exact MGE postimage and successor seed in the isolated rehearsal. Determine whether changed MGE metadata intersects sealed contracts; any required amendment is separately reviewed. Never accept observed metadata as its own expected hash. |
| U07 | Drain before every effect | Before valid drain receipt and old issuer exit, SQL/source/seed mutation cannot enter. Existing admission and owned-work drain include pending finalisation work. No manual task start or second restart. |
| U08 | SQL commit / lost acknowledgement | Independent ledger/postimage verification proves committed; resume records completion without applying SQL again. Live owner, mismatched history or unknown outcome stops. |
| U09 | SQL rollback / process loss | Proven exact preimage and retained attempt permits only the supported same-release continuation. Incomplete or contradictory state never returns safe-to-apply. |
| U10 | Source/index/seed interruption after SQL | Resume uses the same release/intent and preserves SQL success. No migration replay, receipt deletion, or old-bot launch against freeze triggers. |
| U11 | Start/readiness/closeout interruption | Exactly one successor; missing acknowledgement is not permission to start twice. Recheck source/seed/native/SQL identities and publish missing closeout only from authoritative receipts. |
| U12 | Active release / changed package / drift / concurrent operator | Refuse conflicting release, hash substitution, altered postimage or competing ownership. Preserve the evidence and exact stopped stage. |
| U13 | End-to-end native combined rehearsal | Actual reviewed SQL runner, installed-predecessor representation and exact source/seed stage adapters complete in the isolated environment; mocked orchestration alone is insufficient. |
| U14 | Final evidence bundle | Manifest/runner/tool/profile/member hashes; ordered stage intents/completions; drain/exit proof; SQL ledgers/postimages; unchanged flags/held-work; successor identities/readiness; `verified.json`; failure/resume transcripts. |

Existing offline checks to retain and extend include
`tests/test_combined_k98_update.py`, `tests/test_updater_reader_capabilities.py`,
`tests/test_updater_transition_inventory.py`, `tests/test_mge_a1b_update_transition.py`,
and `scripts/Test-K98CombinedUpdate.ps1`. Select native custody/recovery tests from
the actual changed updater surfaces. Those tests' prior results are not results
for a new capability. Record every command, interpreter, exact target and exit code.

## 7. Remaining approvals and ordering

| Gate | Concrete approval / prerequisite | Current status |
|---|---|---|
| A0 | Prepare this packet, source checks and local documentation | Authorized; completed locally |
| A1 | Implement the bounded release capability, MGE profile/descriptor/source transition and native harness described in sections 4–6, with per-repo Changes reviews | Authorized in the current instruction; implemented for review. Existing MGE feature approval remains valid. |
| A2 | Bounded read-only local SQL target discovery: server identity, proposed DB absence, defaults/storage, login, version/collations/isolation; no fixture creation or production access | Authorized and completed; SELECT only, target absent, backup storage verification outstanding |
| A3 | Create/write the exact disposable database and exact observed file/backup paths; synthetic fixtures, two-session races, named fixture-child termination and retained artifacts | Required after A2 binds the missing values and the harness is reviewable |
| A4 | Bounded MINI_AMD read-only inventory: installed Bot SHA/tool manifest/policy/receipts/custody; SQL identity/schema/permissions/ledger/backup observations, no health/provider probe | Required for this release's live bindings; reuse any applicable retained authorization only if it covers these exact operations |
| A5 | Native protected updater rehearsal in a separately named isolated fixture root, with actual elevation and approved synthetic SQL target | Required after exact root/files/tool versions and effects are bound |
| A6 | Publish mirror Bot and SQL branches/PRs, including the explicit mirror publication route | Authorized by explicit create-PR instruction; draft review must retain native/binding blockers. This does not approve merge or deployment. |
| A7 | Merge the reviewed mirror/SQL work and promote an exact patch on a clean private-main-based branch; then merge the private PR | Authorized by the subsequent explicit merge instruction, subject to final source review/CI. Native qualification remains a deployment gate. Re-pin SQL if merge strategy changes the reviewed commit's ancestry; rerun affected qualification on changed bytes. |
| A8 | Install the authenticated updater upgrade on MINI_AMD, if required by verified installed capability | Separate approval; tool installation is not Bot deployment. No active release may be bypassed. |
| A9 | Production preparation and final deployment of the exact private-main target, selected SQL profile and manifest/hash, in the agreed drained window | Required. `-PrepareOnly` creates/stages files and is not a no-write diagnostic. Approval must bind the actual package, targets, backup evidence and recovery plan. |
| A10 | Bounded post-deployment acceptance and later cleanup | Acceptance observes the new runtime without replaying accepted business actions. Live mutation tests, historical disposition and artifact/database deletion require their own explicit scope. |

A1/A2 can be agreed independently; A3 waits for concrete bindings. Before executable
release readiness, resolve B1–B5, preserve CI/security evidence and complete the agreed native
checks. The subsequent A7 instruction permits source merge ahead of those operational gates.
Publication, merge, installed-tool upgrade and deployment approvals are
distinct; do not ask again for the already accepted MGE design direction.

For production promotion, preserve private repository history: use a clean branch
based on the freshly observed `production/main`, apply the reviewed mirror patch,
and verify changed-file and byte equivalence. A reused branch label must not imply
pushing the mirror commit ancestry. Never deploy a mirror or local feature head.

## 8. Ordered production procedure after approvals

1. Resolve final approved Git revisions, SQL ancestry/profile hashes and installed
   predecessor/tool. Confirm no active/uncertain release, relevant ownership and
   open provider-stream state using bounded existing evidence. Do not poll health
   dashboards to manufacture a quiet interval.
2. Validate the approved tool upgrade, install it if authorized, then run normal
   installed-updater preparation for the exact private-main release. Retain its
   generated package, hashes and observations. Stop on any unsupported profile,
   custody, source inventory, SQL preimage/permission or backup mismatch.
3. After final package approval, start that release. Issue one graceful restart
   only when the runner requests it. Require the protected drain receipt and old
   issuer exit before SQL installation. PID absence alone is insufficient.
4. Runner applies/verifies only the selected MGE SQL profile, then installs exact
   source/index and matching seed, starts one successor and verifies readiness.
   Preserve configuration/activation flags and all held or uncertain work.
5. Retain SQL ledgers/postimages, native/source/seed identities and `verified.json`.
   Observe active ordinary inventory and unfinished final-delivery counts; legacy
   completed/confirmed/held/retired boards must add zero routine Discord work.
   Startup success does not establish native callback or natural-event acceptance.

No ready-to-run production command is supplied while final commit, installed
manifest, SQL profile and release hash remain unbound. Once bound, use the existing
runbook's exact installed command and generated arguments, not a new manual launcher.

## 9. Stop and recovery rules

Before SQL commit, a proven rollback can continue only under the reviewed protocol.
After SQL commit, retain frozen domain data, finalisation payloads and receipts;
the old bot's historical sweep is not a safe rollback. Keep the bot drained or
use a reviewed compatible forward correction. Never drop guards/receipts, clear
unknown states, delete historical messages, restore the database or replay business
actions merely to restore a green status. A failed source/readiness/closeout stage
does not undo SQL success. Resume the same release only after independent outcome
and ownership verification; unknown/live/mismatched state remains stopped.

## 10. Packet validation and evidence boundary

The original packet commit added documentation and a source-fingerprint manifest only.
The implementation follow-up above has a separate runtime/test/security review; the
following validation paragraph describes only the original preparation delta. No runtime,
SQL definition, updater registry, descriptor or installed state changes. Apply the
security-routing documentation-only skip to this exact packet delta; do not rerun
the completed source scans or infer any whole-repository/deep audit requirement.
Architecture/deferred/security-routing/selector, link/hash checks and changed-file
pre-commit are the local gates. Runtime/native tests are intentionally not executed
for packet preparation. Record their future results under N/U case IDs instead of
relabeling the existing offline suite as native qualification.

Preparation checks: 42 exact committed-file SHA256/length pairs verified; all
nine introduced local links resolve; architecture, deferred-item and security
routing validators pass with no routing errors/warnings; whitespace check passes.
The explicit documentation-only test selection recommends smoke imports and
registration; both are skipped for this delta because no executable source,
dependency, command or test changes. Existing implementation evidence remains
in the linked handover. Runtime pytest and native execution are likewise skipped.
The release-description validator accepts the **old KVK descriptor's syntax**;
this does not qualify MGE packaging or resolve B1–B4. Changed-file pre-commit
passed; runtime-only hooks correctly reported no applicable files.
