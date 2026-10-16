# Guided recovery: P0a first release and P0b full release

Operator decision, 16 October 2026: release complete supported workflows early for
admin feedback, then finish the full P0 scope. Notify the operator as soon as P0a
is deployment-ready; the operator will arrange the maintenance window and deploy.
This authorizes preparation and validation, not a live deployment or SQL install.

## P0a — first release

Status: **preparing; not deployment-ready**. Candidate implementation heads are
Bot `3a1851e2` (the P0a action boundary and legacy-command correction, stacked
on draft PR #364, including the guided handoff/rehearsal) and SQL
`9a59efbf3a7c31a6d83d1913307cdeee71c3346b` (draft PR #120, migration-chain
corrections and retained rehearsal, stacked on draft PR #119 and predecessors).
These are development candidates, not private-production deployment commits.

Remote `main` heads were read back on 16 October and still match the audit
baselines: Bot mirror `02b57ac682e988c5fefece5669f40de31936a756`, private Bot
`ded19ccda7c3c7ebeeb9379b15a72ae39cb935a4`, and SQL
`b3480656e3454fbe713905460177f8d038c2bd5f`. These Git observations do not establish
which versions or updater are installed on the bot machine.

The initial pilot must provide complete alert-to-verification workflows for:

1. Verified abandoned configuration reads, including the approved automatic
   read-only release and guided investigation when proof is insufficient.
2. Account/SQL writer refusal before execution: explain and link the blocking
   operation, preserve the saved inputs, show registration changes, then confirm
   one fresh admitted continuation without replaying an uncertain write.
3. Atomic configuration publication: distinguish rollback from committed output,
   guide exact release or capture/export settlement, and offer separately confirmed
   fresh configuration publication or an explicit decision to retain prior config.

Other already implemented families may join P0a only after their complete
acceptance evidence and required dependencies are recorded in the release matrix.
Do not expose an unfinished repair merely because its backend is present in the
candidate stack. Discovery must still report unsupported incidents accurately;
absence of a repair must never be described as a healthy or resolved outcome.

P0a release acceptance:

- Freeze exact Bot and SQL commits, dependency/PR order, migrations and hashes.
- Resolve the known source-pin mismatches by identifying each original reviewed
  image and intended change. Do not broadly rebaseline unrelated SQL objects.
- Prepare the supported updater/release metadata, matching protected runtime
  contracts, SQL-before-Bot sequence and a tested rollback/forward-recovery plan.
- Pass an integrated full-suite run, or explicitly qualify unrelated baseline
  failures with evidence; pass architecture, routing, registration, import, lint,
  whitespace and operational-log-isolation checks on the release candidate.
- Complete exact-diff security reviews for any new runtime/deployment changes in
  each repository, and retain the sealed reviews for the included feature stack.
- Prove proactive discovery, private admin-only review pages/buttons, confirmation,
  execution and independently verified settlement for every enabled repair.
- Prove restart, lost reply, duplicate/stale click, changed registration, live
  ownership and failure during repair without duplicate writes or timeout release.
- Document which incidents P0a can fix and which remain P0b; verify the runtime
  exposure matches that matrix. An admin must not need to invent a query/command.
- Prepare a concise operator deployment packet and feedback checklist. Notify the
  operator when all pre-window gates pass; record live acceptance after deployment.

Feedback should capture whether the alert identifies the issue before dependent
work fails, whether checks/actions are understandable, and whether the final
message accurately describes the verified result and any remaining work.

## P0b — full release

These remain required acceptance work, not deferred optimisation:

1. Historical partially applied configuration writes and guided superseding repair.
2. UPDATE_ALL2 partial reporting continuation without repeating committed imports.
3. Durable whole-pipeline continuation: caches, maintenance, remaining publication,
   pre-request failures and historical cases with missing inputs.
4. All-copy containment/active-registration-history evidence loss, with guided
   verification and superseding repair rather than fabricated success evidence.
5. Held access without verifiable ownership and its executable guided disposition.
6. Integrated rollover and recovery acceptance across worker execution, final
   independent verification, restart, concurrency and interruption during repair.

P0b incorporates P0a feedback and passes the full original recovery coverage matrix.
P0 is complete only after P0b acceptance; P0a deployment is an interim milestone.
The broader bot recovery programme outside P0 remains in scope as previously agreed.
The P0a action boundary does not remove existing export replacement, private-evidence,
all-KVK or player-report recovery work. Every withheld family needs explicit full-release
qualification and guided completion; none may disappear from the acceptance matrix
because its backend already exists or its first-release buttons are disabled.

Each remaining workflow must meet these specific acceptance outcomes as well as
the shared alert, private review, confirmation, audit and verification requirements:

| Required P0b workflow | Completion criterion |
| --- | --- |
| Historical partial configuration | Admin reviews the affected configuration and confirms a fresh superseding publication; the bot fences the old attempt, performs the approved repair and verifies the new result. The original unknown outcome stays recorded. |
| Partial UPDATE_ALL2 reporting | Resume reporting from the committed import receipt without claiming or importing the file again. Retain completed phase receipts; prove interruption and repeated confirmation cannot duplicate non-idempotent report effects. |
| Whole-pipeline continuation | Persist and resume outstanding cache, maintenance, configuration and export stages. Pre-request failures also create incidents. Missing historical inputs have guided collection/validation and an explicit disposition; admins do not construct commands or queries. |
| Lost containment or registration history | Identify unavailable proof before dependent work fails. Guide verification and a safe superseding repair; never manufacture original proof or discard uncertainty to release ownership. |
| Unattributed held access | Proactively surface the hold, guide the required ownership checks, then execute and independently verify the permitted disposition. Unproven live ownership remains protected and visibly unresolved. |
| Rollover completion | A single integrated test chain drives actual admin callbacks, authority journal, disposable SQL and worker through final independent verification. Cover restart, concurrent/stale confirmation and interruption at each effect boundary. |

## Immediate release blockers

- `deploy/k98-release.json` still describes the earlier October 13 release, not
  this recovery stack. Twelve additional SQL migration files are in the candidate
  SQL delta from its locally known main; compatibility/install qualification remains.
- The four historical application-source pin mismatches have been traced and
  corrected in the candidate (details below). Exact-diff review and installation
  contract/updater qualification remain release gates; source pins alone do not
  approve the installed database.
- The pilot exposure boundary is enforced in the candidate; complete acceptance
  of every enabled path, the final release-candidate suite and updater/rollback
  rehearsal remain required. No maintenance window is requested yet.

## Complete SQL migration-chain rehearsal

The twelve recovery migrations now pass in sequence on a fresh disposable SQL
database built from 58 baseline tables and seven predecessor procedures. Running
the complete files exposed three real migration 009 deployment failures: repeated
temporary-table names within a batch, references to newly added columns being
compiled too early, and constraint comparisons across different collations.
SQL candidate `21de1988` corrects those failures while retaining the transaction,
exact preimage checks, procedure payloads and permissions. Candidate `662f58c6`
also retains the reproducible local-only opt-in rehearsal helper.

A failure injected immediately before migration 009's commit restored the captured
object, column, index and permission metadata; the original migration then applied
successfully. The retained run is `K98_P0a_Migrations_8e954346a854`. Companion Bot
regressions compile all six temporary declarations together and check the reviewed
constraint definitions; these and rollover migration checks passed (4 tests).
Architecture, deferred-item validation, security routing, test selection, Black,
Ruff and whitespace pass for the Bot companion change. The full suite is not
repeated for this test-only delta; the preceding integrated-suite qualification
below remains explicit. Smoke imports and command registration are unchanged by
the test and documentation files and are covered by PR #363's retained checks.

SQL Changes scan `c5434566-e65e-427b-8198-c3b1e9c10a26`, Deep off, covered
`71c6cedc..662f58c6` and completed with zero findings and complete coverage. Its
sealed result was read back at `2026-10-16T08:55:08.279104Z`; reported usage was
953,337 tokens. The Bot companion changes only the migration regression and this
document; no Bot runtime, permission, configuration or deployment execution changes,
so a separate Bot scan is skipped for that narrow delta. The actual migration
and SQL rehearsal helper are covered by the separate SQL scan.

These checks establish migration-chain execution and precommit rollback. They do
not establish lost-commit receipt recovery, representative configuration business
output, host activation or final coordinated-package readiness. Those remain P0a
release gates; none are transferred to P0b.

## SQL source-pin qualification

The read-only audit compared all 560 pinned source blobs with candidate SQL
`71c6cedcdc317b49df5a312a938759c5a6183a93` and SQL baseline
`b3480656e3454fbe713905460177f8d038c2bd5f`. Exactly four differed from the Bot
manifest; all four have identical bytes at the SQL baseline and candidate.
Each stale pin is exactly the blob immediately before the change identified below;
each replacement is exactly that change's postimage, unchanged through candidate SQL.

| Object | Historical change | Stale SHA256 | Candidate SHA256 |
| --- | --- | --- | --- |
| `dbo.ARCHIVE_IMPORT_STAGING_FILE` | `1159e82456761080eefe18a7a914190b70ecafce` | `aa3b5e4f14e6f84d0de7c48179a0c7a573ca93eb46bf35350bfefe30fbe1fced` | `80ded675c44eb406569f62ef68666646d530582365a3dde7742ad242633b086d` |
| `dbo.CLAIM_KS4_IMPORT_FILE` | `1159e82456761080eefe18a7a914190b70ecafce` | `ee46075e0ce2ba4bc5de5201d108acee1bd817090cb852fe902400ce3561f2df` | `56fa3718d947206b71dfc556d47c2af6a1ab5aa91094e67ea635c584375404ea` |
| `dbo.IMPORT_STAGING_PROC_CORE` | `1159e82456761080eefe18a7a914190b70ecafce` | `df01cd3699b3e9f056ab60bd28e276d081ecd6c62ba57ba17d133e1460411898` | `70143750800457202f79c00174bc0a367e026837ef84041e7053635b72d37d24` |
| `dbo.ExportAttemptPart` | `0cc5f529fa462ec95b68a3d9af1ee1606d70215a` | `8174bd0df3f4914cfb98e4164ab4d0c20494175069d00a09a0edc201dbb6f699` | `888068ce8c2e5796dd0767aaf8985f98e102816b2f1d3f1e6ed78d85b2ece5d8` |

The three procedures replace eleven `xp_fileexist` calls with scalar
`sys.dm_os_file_exists` checks, preserving file identity, ownership, hash checks,
locking and transactions. The table constraint permits `public_editor` only for
legacy `output` parts; it does not make index/generation parts public editors.
The SQL migrations and historical signing/permission profile pins are unchanged.
This Bot patch does not run those migrations or accept live SQL metadata.

Complete offline regeneration of the activation scope succeeds against the exact
candidate SQL commit after these four corrections. Roots and admitted objects are
unchanged. The existing conservative matcher also restores three reference edges:
`StatsImportExecution -> STATS`, `usp_S11RunStatsImport -> STATS`, and
`usp_ExportJobContainTargets -> TARGETS`. These arise from unqualified text
matches (including a filename literal, lock resource, and table variable), not
new SQL dependencies. Keeping them matches the generator's documented conservative
contract. The saved scope equals its complete regenerated output.

## Release packaging and pilot exposure findings

The combined updater consumes explicit `migrations/<id>.release.json` profiles,
not arbitrary `.sql` migration files. The SQL candidate currently contains only
the October 13 reader-history profile. Its module and additive-table profiles
do not automatically support this recovery stack's table alterations, new modules,
and ordered dependencies. Updating the descriptor with SQL-file hashes would be
incorrect. P0a needs an explicitly reviewed, tested deployment path for the exact
twelve recovery migrations, including interrupted apply/verification and receipt
handling. This is a P0a blocker, not a P0b deferral.

The historical arbitrary-SQL runner is not an automatic fallback: it applies a
migration and writes the migration-history receipt in separate calls. A lost reply
between them needs independent postimage verification, and its `ValidationOnly`
path writes a deployment audit row. The P0a preparer must supply a genuinely
read-only preflight and an exact reviewed reconciliation path; it must not treat
missing history as permission to replay a migration or call that legacy validation
mode a read-only observation.

The existing updater classifier was applied offline to the exact mirror source
delta `02b57ac6..b55cb730` (209 changed files). It reports
`COORDINATED_RELEASE_REQUIRED`: 48 protected source changes are outside its current
routine policy, and the transition registry is an updater-package member change.
This is source-capability evidence only. Historical October 14 installed-tool
and host evidence has since been located locally; it does not attest current
host custody or the new recovery deployment contracts.
P0a must use a reviewed coordinated release package or an explicitly reviewed
bounded updater extension. Do not bypass guards, add a generic force exemption,
or describe the current ordinary updater as capable of deploying this stack.

The runtime retains all ten recovery adapter kinds for discovery and diagnosis.
Candidate `3a1851e2` enforces the explicit P0a action matrix below in both runtime
composition paths. The service filters fresh dispatch, automatic actions and input
forms as well as the displayed buttons. It preserves original durable evidence,
its token, blocker links and reconciliation of previously accepted repair intents.
Unsupported incidents stay open and show a release-coverage explanation, rather
than suggesting that repeated Recheck will unlock an unavailable repair.

| Incident family | Fresh actions enabled in P0a | Boundary |
| --- | --- | --- |
| Configuration read | Release abandoned read; cancel unstarted read; isolate verified read and release | Requires the authority's exact read-only/ownership proof. Timeout alone never authorizes release. |
| Producer admission refusal | Cancel unstarted reservation; resume saved SQL stage; continue with reviewed current registration | Only verified non-execution admits a fresh attempt. A blocker outside P0a remains visible and requires its P0b workflow. |
| Atomic configuration producer | Close verified rollback; finish capture; queue verified capture; explicitly skip export | No claim that skipped spreadsheets or caches are current. Historical partial writes remain P0b. |
| Configuration continuation | Read and atomically publish current registered config; keep prior config | Separate current-source/destination review and confirmation; no scan import replay. |
| Stats-import dependency of admission continuation | Release verified failed import; finish capture; queue verified capture; explicitly skip export | Completed SQL output only. Accepting unfinished reports and partial-report continuation are not enabled in P0a. |
| Export job, rollover, private evidence, all-KVK, player report | Diagnosis, blocker links and monitoring; no new repair dispatch | Required P0b qualification/work remains. Already accepted repair intents continue reconciling. |

New action names default to withheld. The legacy `/ops import_resolution`
status/preview/resolve entry point now opens the same current guided page; old
confirmation tokens do not apply repairs. Its unused direct-settlement helper is
removed. This closes the alternate dispatch path found during boundary review.

The matrix is an enforced candidate boundary, not completed acceptance evidence
for every enabled action. Admission-to-capture/worker delivery, representative
configuration business output and final installed-package qualification remain
required P0a work. Detection of a P0b blocker is not described as its recovery.

## P0a boundary verification

The initial policy patch passed 58 focused service, UI, notification and form
tests. All three disposable SQL alert-to-confirmation configuration rehearsals
pass with the actual policy enabled. The legacy-path correction passed 57 selected
command, policy and command-registration tests, including all fifteen combinations
of status/preview/resolve and admin, channel, guild and expired-interaction checks.
The log-isolation wrapper verified production operational logs were unchanged in
each passing run. These counts overlap and must not be added as unique tests.

Architecture, deferred-item validation, routing, selected smoke imports, command
registration (36 primary / 102 grouped), Black, Ruff and whitespace checks pass.
The isolated `test_ui_imports.py` fails because its constants stub omits
`PLAYER_STATS_LAST_CACHE`. This reproduces on unchanged prior worktree `34cdb5c5`;
the failing test and its registry/target/cache import chain are unchanged. It is an
unrelated baseline test-fixture failure, not a passing gate or a recovery deferral.

The integrated full suite on the frozen policy candidate completed with **8,189
passed, 635 skipped, eight subtests passed and one unrelated failure** in 797.71
seconds. The failure is the previously documented missing
`.github/workflows/command-governance.yml`; it is absent from the unchanged prior
candidate and mirror main. The narrow legacy-command correction was validated
separately by the 57 selected tests above after collection of that full run.
Therefore this is integrated policy evidence plus targeted command evidence, not
a claim of a clean full suite on the eventual deployment package. SQL opt-in cases
skipped by this run retain their separate actual-engine rehearsal evidence.

Changes scan `10b13b25-a35c-45d7-b0b2-fae45ac20f91` reviewed the four policy/runtime/UI
files committed in `695b0336`: complete coverage, zero security findings, sealed
at `2026-10-16T09:05:59.788220Z`, usage 1,566,969 tokens. It identified the ordinary
legacy-entry-point consistency blocker described above. Follow-up Changes scan
`d21684f5-2326-47b4-b4a7-82eba605fd17` reviewed both the command modification and
deleted service baseline committed in `3a1851e2`, confirmed that blocker closed,
and completed with zero findings and complete coverage. Its sealed result was
read back at `2026-10-16T09:10:06.894054Z`; usage 783,307 tokens. Deep was off for
both scans. This evidence document adds no executable or permission changes.

## Initial pilot acceptance evidence map

Existing tests are evidence for individual slices, not a claim that release
packaging or the complete final candidate has already passed.

| Pilot behavior | Existing focused evidence | Remaining release check |
| --- | --- | --- |
| Verified abandoned read automatically releases; unknown writes never do | `test_config_recovery_guided.py`, `test_config_preparation_recovery_sql.py` | Rehearse notification-to-settlement on the packaged candidate and verify exact ownership after restart. |
| Explicitly confirmed unstarted/read-only containment | `test_config_read_containment_sql.py`, `test_config_unstarted_read_sql.py` | Confirm explanation distinguishes fenced/discarded reads from positively terminated children. |
| Writer refusal before execution links its blocker and retains inputs | `test_producer_admission_recovery_sql.py`, `test_admission_decisions_sql.py`, `test_replacement_admission_sql.py` | Prove every enabled blocker link reaches a qualified action or clearly identifies the P0b boundary. |
| Atomic configuration rollback or committed capture | `test_configuration_producer_recovery_sql.py`, `test_configuration_targets_contract_sql.py` | Qualify exact migration/install contracts and representative publication data; synthetic nested-callee tests alone do not prove business output. |
| Fresh configuration publication or keep-prior decision | `test_configuration_continuation_sql.py`, `test_recovery_review_view.py` | Verify the full displayed path through capture/export settlement, including changed registration and lost reply, on the packaged candidate. |
| Proactive alerts and persistent private admin controls | `test_recovery_notifications.py`, `test_recovery_review_view.py`, `test_recovery_input_view.py` | Exercise the deployed admin channel after maintenance; record alert usefulness and clarity without exposing private targets publicly. |

The deployment handoff must identify exact approved commits/package checksums,
explicit migration order, expected success/degraded messages, safe interruption
instructions and the feedback cases to run. It must give the operator executable
steps; it must not require the operator to design release manifests or repair SQL.

## Source-pin correction validation

The 350 existing activation-scope, runtime-composition and log-isolation tests
passed. Architecture (203 Python files), deferred-item validation, security routing,
test selection, Ruff, Black, whitespace, synthetic imports and command registration
(36 primary commands / 102 grouped subcommands) passed. The read-only SQL
file-visibility validator verified all three exact migration/source postimages and
the inverse proof of precisely eleven existence-check replacements.

Changes scan `bfec7228-67dc-4f4e-a146-191ff26a7eb7` reviewed the frozen working-tree
patch against `34cdb5c5`, subsequently committed unchanged as the three source files
in `c66b0d81`. All three source files have complete coverage and no findings; the
scan completed, sealed and was read back at `2026-10-16T07:59:57.442351Z`.
Tool-reported scan usage: 1,692,981 tokens. Release documentation added after that
scan changes no runtime, permission, input, deployment execution or persistence
behavior and needs no additional Changes scan. It does not certify deployment.

Broader candidate validation completed with **8,178 passed, 624 skipped,
8 subtests passed and one failure** in 908.85 seconds. The sole failure is
`test_command_governance_config.py::test_command_governance_workflow_runs_validator_and_focused_tests`:
the repository lacks `.github/workflows/command-governance.yml`. Git tree checks
confirm it is also absent at the immediate base `34cdb5c5` and mirror main
`02b57ac6`; this patch does not change it. Per repository rules, the unrelated
baseline failure is documented rather than expanded into this PR. No fully green
suite is claimed. Opt-in SQL tests were skipped in this run; the earlier feature
PRs retain their separately approved disposable-SQL evidence.

The full-suite log wrapper exits on pytest failure before comparing operational
logs. A separate focused wrapper run completed with 12 tests passed and explicitly
verified that production operational logs were unchanged. This is focused log
evidence, not an assertion that the failed full wrapper completed its comparison.

## Guided workflow rehearsal — 16 October

The alert-to-disposition rehearsal found and fixed a real handoff gap: a verified
rollback closed the original incident, and the view then hid its **Choose
configuration continuation** link. The view now retains that particular link;
other obsolete recovery links remain hidden. Opening it checks admin, guild,
channel, scoped original preparation and current evidence again. Fresh publication
or keep-prior still requires its own confirmation.

`test_p0a_guided_rehearsal_sql.py` drives proactive monitor discovery, persisted
SQL incident/alert identity, a newly constructed persistent entry button, private
review, rollback closure, continuation and final disposition. Each callback
reconstructs the service/DAL/adapters. Three cases finish with verified settlement:
keep prior; fresh publication followed by explicitly skipping its export; and
the same path after losing the publication commit reply. Old confirmations cannot
dispatch another publication. Additional tests reject wrong admin, guild and
channel before following the retained link.

These tests use actual disposable SQL storage and actual callbacks. Discord
transport and the configuration producer body are simulated; the producer helper
commits the actual durable atomic receipt. They do not prove live Discord delivery,
representative configuration/target business results, export worker delivery or
installation of the coordinated package.

Combined validation passed **169 tests, zero skipped**, including the three new
SQL rehearsal cases, all selected read containment, admission, configuration,
notification, review and durable incident tests. The log wrapper verified that
production operational logs were unchanged. Older tests were corrected to compare
an immutable migration with its own reviewed postimages, include the contained-target
table in temporary fixtures, and distinguish historical read prefixes from fresh
probe or write evidence. Unique temporary constraint names prevent collisions
across pooled fixture connections. No runtime SQL contract was weakened.

Architecture (204 files), deferred items, security routing, test selection,
synthetic smoke imports, command registration (36 primary / 102 grouped), Ruff,
Black and whitespace checks passed. The inherited full-suite baseline remains
qualified by the unrelated missing governance workflow described above; it was
not repeated for this narrow UI change and disposable test-harness correction.

Changes scan `209d540b-d721-4c09-921a-d779aef68a0f` reviewed the frozen patch
against `7bee1fc6`, whose runtime change is committed as `5a5256d6`. Its complete
one-file runtime inventory (`ui/views/recovery_view.py`) has no findings; supporting
test changes were inspected. Finalization succeeded and the sealed result was read
back, sealed at `2026-10-16T08:30:03.698675Z`. Tool-reported usage: 1,462,007 tokens.
The later temporary-constraint namespace fix changes only an opt-in local SQL test
fixture, with no production runtime, permissions, deployment or persistence effect;
it does not require another security scan. This documentation also adds no executable
behavior. There are no deferred findings in this review.

**P0a remains not deployment-ready.** The coordinated migration/apply/verify package,
protected successor contracts, interruption/forward-recovery rehearsal, complete
enabled-action acceptance and final operator packet are still P0a release gates. All
six P0b workstreams above remain required. No maintenance window is requested yet.

## Coordinated deployment qualification — 16 October

SQL PR 121 adds the coordinated twelve-migration adapter and independently derived
schema images. Its disposable Windows PowerShell / SQL Server rehearsal passed
thirteen adapter calls covering unstarted, competing ownership, process death,
rollback, lost commit acknowledgement, repeat apply, receipt corruption and module
drift. All migrations and thirteen receipts share one transaction. This proves the
adapter protocol; its fixture profile is not a production deployment profile.
Production application grants and successor startup contracts still need binding.

The bot's fixed-adapter v4 packet now permits up to 512 authenticated members,
enough for the observed 243-member candidate. Generic packets retain their 128-member
limit, action layouts remain fixed, and preparation rejects a manifest larger than
64 KiB before writing outputs. Native orchestration and 133 focused preparation
tests passed. A stale legacy source pin would have rejected the migrated atomic
`sp_TARGETS_MASTER` at startup; it now accepts the immutable reviewed SQL postimage
and rejects the prior body. Its linked unchanged grant plan was repinned. All 100
selected source, contract and grant tests passed, with operational logs unchanged.

Architecture (211 files), deferred-item, test-selection and security-routing gates
passed. Changes scan `51a40104-8ca9-415b-a56c-a2539bfa5d74` covered all seven changed
source files and inspected both test files at snapshot
`de63b5dba6a958844fea461ef5542443e362a3dbc3ebad40a63f3b9043bb8e2d` against
`cb5d439c`. It completed with no findings and its sealed documents were read back;
sealed at `2026-10-16T09:48:59.456163Z`, tool-reported usage 1,667,747 tokens.
This subsequent evidence-only documentation adds no executable behavior and does
not require another scan. No full-suite rerun is claimed for this narrow change.

P0a remains **not deployment-ready**. Remaining release gates include production
grant-aware images, protected successor contracts, the actual coordinated source
packet, representative business output and complete enabled-action acceptance,
and installed-package interruption/restart/forward-recovery rehearsal. These are
required P0a work, not deferred optimisations. All P0b work remains in scope.

## Startup permission qualification — 16 October

The application startup contract now expects the immutable rollover procedure's
explicit `DENY ALTER`. The previous direct-profile expectation incorrectly required
ALTER and would reject the correctly installed procedure. No SQL right is granted
or widened. Neighboring legacy and evidence expectations remain unchanged.

The source-pinned disposable qualification checked 313 actual object and column
permissions across all sixteen new recovery objects, under the application user.
All matched. The retained database is `K98_P0a_Migrations_0241337766c2`; this is local
fixture evidence, not a production observation or whole-startup acceptance.
The focused suite passed 346 tests with one opt-in SQL migration case skipped;
production operational logs remained unchanged. Architecture (213 files), deferred
items, security routing, test selection, Ruff, Black and whitespace checks passed.

Changes scan `5c214e1b-3891-4b01-9eab-ba0a7e3e5254` covered the frozen runtime patch
and supporting tests against `c2d9a961`, snapshot
`5dc3f8f6f2666e90e628af3fc0549caca387a18b8b6cc27541864555f117c9bd`.
Finalization succeeded with complete coverage and no findings; sealed documents
were read back at `2026-10-16T10:24:36.740937Z`. Tool-reported usage: 2,019,577 tokens.
This subsequent evidence-only entry changes no executable behavior. The package
and final rehearsal gates above remain open; no maintenance window is requested.

## Coordinated seed evidence integration — work in progress

Bot mirror PR 367 contains the reviewed startup-permission correction. SQL PR 124
adds the existing evidence-role grants to the disposable fixture, with another
successful 22-call real SQL fault rehearsal and a completed Changes review.
The startup permission qualification was then repeated against SQL fixture commit
`5e5fdb8151c539d8bd12b8df17753526218b5987`: all 313 checks passed in retained local
database `K98_P0a_Migrations_f5e053c4d98e`. No production state changed.

The coordinated package cannot relabel a predecessor SQL observation as proof of
the successor installation. The saved implementation now collects complete actual
installation, legacy and application SQL snapshots, requires all three existing
startup comparators to pass, retains those rows and their collection time, and
derives the existing SQL observation record from the actual installed identity,
metadata and migration checksums. No expected fingerprint is adopted from live SQL.
The existing deployment admission record format and checks remain unchanged.

The saved helper has 29 passing focused tests, including collected-row provenance,
verification failure, incomplete evidence, schema/permission drift, interrupted
publication, restart, foreign release, altered seed and corrupted evidence. The
preceding broader run passed 496 tests with operational logs unchanged; the four
subsequent collector cases passed separately. Architecture (216 files), deferred,
security-routing and test-selection gates passed. This is not a native installed
package rehearsal or security approval of the unfinished integration.

Automatic approval review rejected two earlier proposals: accepting a reviewed
migration expectation instead of an actual installation observation, and creating
the observation summary from expected values after a verification call. Neither
proposal was applied. The saved implementation instead retains and rechecks the
complete actual SQL rows before constructing the observation.

The remaining native integration was also rejected pending exact operator approval.
Its proposed sequence is: after the immutable SQL chain and target source verify,
collect and retain the actual SQL evidence; derive and protect the successor seed;
verify its enclosing hashes; install it; perform the existing single-start and
readiness checks. Only seed member hashes, the policy's enclosing plan checksum and
its checksum may be rebound. Source pins, activation flags, deployment identities,
paths, expected SQL contracts and admission checks remain immutable. Partial
observation/seed writes must resume deterministically, with drift rejected.

The operator explicitly approved that isolated implementation and disposable
testing. The approved native integration is now applied; production deployment
remains separate. It selects derived seed bindings only after complete live SQL
verification and retains the immutable base bindings for every resume. Native
checks reject changes to source, flags, paths and release identity. Missing or
partial evidence cannot reach startup; the helper resumes deterministic publication
without replacing the original collected evidence.

The installed updater now carries the finite P0a policy: 49 exact protected source
pairs from private predecessor `ded19ccda7c3c7ebeeb9379b15a72ae39cb935a4`, three
reviewed before/after SQL contracts and 15 SQL source members at
`5e5fdb8151c539d8bd12b8df17753526218b5987`. The 12-migration atomic profile retains
26 independently derived object images and eleven predecessor receipts. Fresh
read-only environment discovery supplies server/database, collations and SQL
compatibility; it never supplies expected object images or permissions.

The offline private-history overlay assembled 256 changed source files into 286
authenticated members, with a 32,566-byte manifest. All member hashes, SQL revision,
contract expectations, stage ordering and preserved flags passed. Evidence is in
the retained development fixture `K98_P0a_Package_m4gyfh8r`; this is explicitly
non-deployable (synthetic target label and ambient fixture values). The host updater
must acquire reviewed private main and fresh installed observations independently.
The rehearsal preserves private-only files and refuses differing private/mirror
preimages instead of copying the scrubbed mirror tree into production history.

Required P0a gates still include final changes review, complete startup-contract
qualification, representative business/worker and enabled-action acceptance, and
the installed-package interruption/restart/forward-recovery rehearsal. No
maintenance window is requested yet. All six P0b recovery workstreams remain
required; none has been deferred or marked complete.

## Coordinated package and populated rehearsal — 16 October

Mirror PR 368 publishes the coordinated package at `84b19f54`. Changes scan
`3744b7f9-d812-4715-9430-e8053e74c930` covers `1f6e0c47..84b19f54`: all thirteen
source-like files reviewed, no candidates/findings, complete coverage. Finalization
succeeded and sealed documents were read back at `2026-10-16T11:40:20.158819Z`.
Tool-reported usage was 3,581,109 tokens. The 591 focused tests and native suites
of 76, 15, 30 and 30 checks passed. The exact predecessor updater upgrade and
installer were built locally; their presence does not authorize installation.

The complete export installation comparator now passes against actual restricted
login observations in a fresh local database: 48 objects, 503 columns and 1,311
effective permission checks, preserving reviewed metadata hash
`2dece9329be54dfb031c07f3c61903fd52835d83e3bf29d0ad70af18ac7e881f`.
The fixture reconstructs historical column ordering, executes the twelve literal
migrations, and uses explicitly synthetic baseline receipts. It changes only
the local server/database identity in the reviewed contract. Temporary login
creation is paired with cleanup even when the rehearsal fails, and connection
pooling is disabled before the first connection. Existing databases are untouched.

The populated business rehearsal invokes all nine real nested target procedures,
using three synthetic governors across two power bands and one exemption. It
checks exact target and DKP values, two exported target rows, three final report
rows, outer-transaction rollback, draft publication, promotion to official and
preservation of the existing official publication identity. All four cases passed
in `K98_P0a_Migrations_4fbfc5a88afe`. No nested business procedure is stubbed.
The SQL repository references but does not export the `KS4_UNO_SEQ` definition;
this fixture supplies an unused sequence dependency and provides every SCAN_UNO
explicitly. This is not sequence installation evidence or provider delivery proof.

The current native adapter also passed seven elevated Windows custody checks in
a unique protected disposable directory: CreateNew/readback, atomic directory
publication, preserved ACLs and bytes, overwrite refusal, changed-hash refusal and
exclusive operator locking. Production state was not changed.

The full-suite investigation found the SQL repository's current outcome manifest
still described the predecessor `sp_TARGETS_MASTER`, while the bot already pinned
the atomic successor. The focused SQL follow-up aligns that exact module entry
and verifies both its immutable forward migration and the inverse historical
source. Historical signing/direct-permission manifests and migration files remain
unchanged; old bodies are not admitted to the runtime allowlist. Python source
compatibility checks passed 23 cases against the paired SQL checkout. SQL checks
passed for atomic configuration, stats outcomes, 863 historical source assertions,
80 direct-permission assertions and target publication.

P0a is still **not deployment-ready**. Whole-application/legacy startup qualification,
complete capture/worker acceptance, installed-package interruption/restart
qualification and final promotion/handoff checks remain open release gates. This
does not defer any of the six P0b workstreams or authorize the maintenance window.

## Final qualification reviews and queue/worker acceptance — 16 October

Bot PR #369 (`99ae0243`, stacked on #368) and SQL PR #125 (`72b1af55`, stacked
on #124) retain the populated qualification and exact source alignment. Their
Changes reviews both finalized successfully and sealed documents were read back:
`b53aebc1-5e54-408a-87a5-0b522df1bba3` (three source items plus supporting test
and documentation; 1,324,653 reported tokens) and
`bec56188-9843-4dc8-97d0-b28d2a2d453c` (all six files; 981,734 reported tokens).
Both have complete bounded coverage and zero findings. No finalization error or
approval request remains for those reviews.

The frozen export/business rehearsal passed again in
`K98_P0a_Migrations_5361cbbc4e3e`: 48 objects, 503 columns, 1,311 permissions and
all four populated target-publication cases. Current smoke imports and command
registration passed: 36 primary commands and 102 grouped subcommands.

Guided capture acceptance now uses the actual queue DAL and worker coordinator
with preparation, output-operation and execution-evidence gates enabled. Admin
buttons drive capture and one durable job; a lost queue acknowledgement is
reconciled through a newly constructed service. Actual spool bytes reach worker
admission after reconstruction. A controlled pre-dispatch failure releases only
the job's exact claims; a corrupt spool prevents dispatch and reopens recovery;
an unknown request checkpoint retains claims and never automatically retries.
The related disposable SQL set passed 62 tests with production logs unchanged.
Discord transport, the producer receipt helper and provider failure injection
remain explicit fixture boundaries; this is not successful provider-delivery proof.

The narrow follow-up changes only two test files and this evidence record. Security
routing: documented skip for this diff, because it adds isolated, opt-in synthetic
test coverage without changing deployed runtime, permissions, configuration,
dependencies or deployment tools. The SQL table names and shapes are read from the
paired authoritative source. Architecture, deferred-item, security-routing,
test-selection, formatting, lint and whitespace checks pass.

The grant provenance audit resolved all ten apparent historical pin differences.
Of 115 distinct annotated sources, 20 match Git bytes and 85 match the current
CRLF checkout form. Ten match exact earlier reviewed revisions: three table shapes
at `93acb69f`, UPDATE_ALL2 at `6072697b`, sp_TARGETS_MASTER at `64bc2975`, two
enrollment transitions at `9dc3e42b`, replacement activate/plan at `2dd649bf`, and
replacement verification at `95b4e91b`. These annotations record grant provenance;
runtime validates the complete grant-plan digest and actual effective permissions,
while current SQL definitions have their separate source/metadata pins. No runtime
allowlist or unrelated source hash was relaxed. The exact audit is retained in
`p0a-grant-provenance-20261016.json` in the local task artifacts.

Remaining P0a gates stay open: complete application/legacy startup qualification,
successful capture-to-provider acceptance, composed installed-package interruption
and forward recovery, and final private promotion/operator handoff. P0b retains all
six required workstreams. The maintenance window is not yet authorized by readiness.
