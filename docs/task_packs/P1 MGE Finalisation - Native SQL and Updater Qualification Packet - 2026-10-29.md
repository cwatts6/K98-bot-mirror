# MGE finalisation: native SQL and updater qualification packet

Prepared 29 October 2026. **Preparation only; not an executable release or approval
to connect to SQL, create a database, install an updater, publish, merge or deploy.**
The approved MGE implementation direction remains accepted. This packet defines
the additional work and evidence needed to release it; it does not reopen that
direction or repeat accepted A1b operations.

**Verdict: do not promote or deploy yet.** The remaining work includes an updater
capability extension, not just running tests. Native SQL execution has not occurred.

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
remain fakes. The native harness is **to be authored and reviewed**, not supplied
or executed by this packet. Existing KVK table/module rehearsal scripts are
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
patch launcher. This is a proposed implementation scope requiring approval.

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
| A1 | Implement the bounded release capability, MGE profile/descriptor/source transition and native harness described in sections 4–6, with per-repo Changes reviews | Required; not implied by packet preparation. Existing MGE feature approval remains valid. |
| A2 | Bounded read-only local SQL target discovery: server identity, proposed DB absence, defaults/storage, login, version/collations/isolation; no fixture creation or production access | Required for this qualification target |
| A3 | Create/write the exact disposable database and exact observed file/backup paths; synthetic fixtures, two-session races, named fixture-child termination and retained artifacts | Required after A2 binds the missing values and the harness is reviewable |
| A4 | Bounded MINI_AMD read-only inventory: installed Bot SHA/tool manifest/policy/receipts/custody; SQL identity/schema/permissions/ledger/backup observations, no health/provider probe | Required for this release's live bindings; reuse any applicable retained authorization only if it covers these exact operations |
| A5 | Native protected updater rehearsal in a separately named isolated fixture root, with actual elevation and approved synthetic SQL target | Required after exact root/files/tool versions and effects are bound |
| A6 | Publish mirror Bot and SQL branches/PRs, including the explicit mirror publication route | Required. Draft PRs may be published earlier if explicitly approved and clearly blocked; passing native tests is not a prerequisite to honestly labelled draft review. |
| A7 | Merge the reviewed mirror/SQL work and promote an exact patch on a clean private-main-based branch; then merge the private PR | Required after review/CI and relevant qualification. Re-pin SQL if merge strategy changes the reviewed commit's ancestry; rerun affected qualification on changed bytes. |
| A8 | Install the authenticated updater upgrade on MINI_AMD, if required by verified installed capability | Separate approval; tool installation is not Bot deployment. No active release may be bypassed. |
| A9 | Production preparation and final deployment of the exact private-main target, selected SQL profile and manifest/hash, in the agreed drained window | Required. `-PrepareOnly` creates/stages files and is not a no-write diagnostic. Approval must bind the actual package, targets, backup evidence and recovery plan. |
| A10 | Bounded post-deployment acceptance and later cleanup | Acceptance observes the new runtime without replaying accepted business actions. Live mutation tests, historical disposition and artifact/database deletion require their own explicit scope. |

A1/A2 can be agreed independently; A3 waits for concrete bindings. Before merge-ready
publication, resolve B1–B5, preserve CI/security evidence and complete the agreed native
checks. Publication, merge, installed-tool upgrade and deployment approvals are
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

This change adds documentation and a source-fingerprint manifest only. No runtime,
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
