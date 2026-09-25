# KVK Source Migration S6 release evidence log

## Separate Bot and SQL PR handoff authorized — 2026-09-25

The operator authorized publishing the mirror repair with all pending/untracked Bot documents,
and a separate SQL closeout documentation PR for parallel review. This explicitly supersedes
the prior SQL-document deferral for `docs/SQL_DELIVERY_LOG.md` and `migrations/README.md`.
No runtime/configuration byte changed after the completed repair review; this continuation
updates only Markdown publication status and approval scope. The existing Changes review is
reused for exact reviewed source; additional Markdown status edits have a documented skip.
SQL remains Markdown-only, so SQL execution and a new SQL Changes scan are skipped.

Merged S11 implementation remains mirror #281, production #588 and SQL #89. The new PRs are
follow-up repair/closeout delivery, not production deployment or acceptance. Next: **G4 plan
development only**, then only specifically approved controlled operations, then operator G5.
The validation receipt below is historical local evidence; its earlier pending-publication and
SQL grouping statements describe the decision before this explicit authorization.

## Mirror repair and G4/G5 handoff validation — 2026-09-25

The approved local follow-up on `codex/s11-mirror-g4-handoff` restores five exact production
source/test blobs and narrows publication exceptions to their exact root-relative paths.
The current [closeout](s11_closeout_and_g4_handoff.md) and new task pack/starter replace the
old initial-S11 entrypoint. No commit, PR, production policy update or publisher run is claimed.

Guarded focused validation: **196 passed / 1 skipped**, with external network/SQL blocked,
live fixture flags disabled and operational log bytes/sizes/mtimes unchanged. The skipped case
requires real rsync, unavailable locally; the new Linux workflow requires it and remains unrun.
Architecture, deferred items, security routing, test selection, command registration and import
smoke all passed. Restored source/tests pass Black and Ruff unchanged. The test selector suggests
full pytest because tests were restored/added; a fresh full run is skipped because those runtime
bytes exactly equal reviewed production, with focused restoration/import tests covering this
repair. Earlier full-suite evidence remains historical. No native/SQL/provider execution occurred.

All 96 added local links resolve; every existing amended Bot document body is preserved. Exact
merged identities, both S10E previous_filename/source/destination proofs and the single trailing-
blank-line exception are in `s11_merged_delivery_manifest.json`. SQL's two additive closeouts stay
pending separately for the next real authorized SQL implementation PR, with a documentation-only
security skip. No retained data or recovered evidence changed.

Bot Changes scan **61ed6784-ae3d-4d5e-aba1-ecc24685151c**, Deep off, completed and was read back:
**complete scoped source coverage, zero candidates/findings**. Base/head:
`511c129602e144a198dc29e9c396196d90d30df9`; frozen snapshot
`codex-security-snapshot/v1:sha256:bc9a2b4b0f62ebc324c438aec61c5d92d72aefda954eeda557e169e662068b89`.
The inventory's three source-like paths were supplemented by all 38 changed/new files, including
filter, tests, documents and identity manifest. Independent review read all eight source/config/
test files and directly supporting publication/authority paths. Preflight ready; no config edits.

Retained report:
`C:/Users/cwatt/.codex/state/plugins/codex-security/scans/discord_file_downloader/511c129602e144a198dc29e9c396196d90d30df9_20260925T101657Z_h7pg52cq/report.md`.
Tool-reported aggregate rollout usage: **3,342,048 tokens**, including **3,115,136 cached input**,
across three threads. This is aggregate rollout attribution, not isolated scan analysis cost.

This receipt/readiness update follows sealing and is documentation-only. The new policy test also
received only whitespace/expression wrapping after sealing, with AST equality proved; its SHA-256
changed from `fe2d2cecda90aa50367a5e26d3f682eb309a9c09f368254ab679e2e2f452ced3` to
`59328d73e7818c024c4313a4a159dc364f9b6785c7168cae519fc9ab461ed5cf`.
That nonfunctional delta has a precise security skip; the sealed snapshot is not relabelled as
including later bytes. `.publishignore`, workflow and all restored runtime/test bytes are unchanged.
Final delivery hashes and format evidence remain under `.codex_artifacts/s11-authority-composition/`.
Final Black in-process and Ruff checks passed; the formatted policy test again passed its portable
check with only rsync skipped. A stalled Black CLI process was stopped by verified process identity;
no Bot process was touched. Final security routing and whitespace checks passed in both repos.
Live G4 proof and G5 acceptance remain open.

## Current delivery and next phase — 2026-09-25

S11 Bot mirror #281, SQL #89 and production Bot #588 are merged. See the
[source closeout and exact manifest](s11_closeout_and_g4_handoff.md) for delivered behavior, review
corrections, source pins and the mirror publication repair follow-up. Production deployment,
SQL installation, provider behavior and G5 acceptance are not established by these merges.

Next: **G4 plan development only**, using the [new task pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S11%20G4%20Release%20Planning%20Controlled%20Rollout%20and%20G5%20Acceptance.md) and
[chat starter](../../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S11%20G4%20Release%20Planning%20Controlled%20Rollout%20and%20G5%20Acceptance.md). Controlled rollout executes only specifically approved
operations; G5 remains operator-owned. Earlier dated checkpoints below retain their original
scope/status as historical evidence, including headings used by existing links. They do not
reopen implementation or authorize live operations. Preserve S6/S8 gates, uncertainties and data.

## S11 final local review receipt — 2026-09-25

Sealed-readback qualification: canonical coverage.completeness is **partial** because an
earlier in-progress deferred row (deferred-4e2d4e3316790341) remains. It says the three final
client files are awaiting review, while the same sealed bundle includes their completed
independent review, matching hashes and three no_issue_found surfaces. The final submission
sent an empty deferred list; the readback retained that placeholder. No source review is
missing under it. Preserve the sealed report and read the standalone clarification at
C:\Users\cwatt\.codex\state\plugins\codex-security\scans\discord_file_downloader\artifacts-1e260e5bff8d24478e9c6aea0fdbbbfc9009bc7673a8016ceaec600f93fe8652\artifacts\s11-final-coverage-clarification.md.
Do not claim its machine coverage flag is complete or silently reseal it. The adjacent
fix_report.md records local remediation and **blocked live verification** under the explicit
G4 boundary. This is an artifact qualification plus an actual live-evidence limitation, not
another local implementation request. Reviewers must read these alongside the sealed result.

All approved local source/offline completion work is finished. Final Bot Changes scan
**8cf1584b-9dd4-45bd-918d-7ad55c562173**, Deep off, completed once and its sealed canonical
result was read back: **zero candidates and zero reportable findings**. Base/head:
721ad7e0cd6b160ddddad328c2338a98bdfb6e0a. Reviewed working-tree digest:
codex-security-snapshot/v1:sha256:61328fa8bbe1e4cc2641090f2f78a8658a44fa442698dc756aa6170fed2f0d4c.

All 33 changed runtime sources are covered. Thirty reuse completed scan f0d13c1f coverage only
after exact SHA-256 equality verification; the three final changed sources received independent
complete-current-file review. No intra-file unchanged-body proof is claimed for those three.
The final review found no additional concrete regression. Its seven extra in-memory fake-native
cases passed. Prior canonical threat-model content was retained unchanged, with historical line
anchors explicitly distinguished from refreshed source coverage. Preflight was ready, all three
capabilities passed, and no configuration changed. Validation/attack-path stages had no candidates.

Retained managed directory:
C:\Users\cwatt\.codex\state\plugins\codex-security\scans\discord_file_downloader\721ad7e0cd6b160ddddad328c2338a98bdfb6e0a_20260924T233734Z_23ezx1nc.
It contains report.md, findings.json, coverage.json, scan-manifest.json, exports/results.sarif,
the exact 128-path source proof, prior coverage provenance and the independent client review.
The completion tool reports aggregate rollout usage across one task of **1,636,540 tokens**,
including **1,539,456 cached input tokens**. This measured aggregation is not an isolated
analysis-cost estimate and is not an account usage estimate.

Final source validation is **5,812 passed / 81 skipped** for the full tree before the narrow
client correction, followed by **704 passed / 1 skipped** on all affected final suites. The
44-case boundary file is included in the latter result. All 50 changed Python files pass Black
API formatting/AST-equivalence checks and Ruff. The six settled-tree checks pass: architecture,
deferred items, security routing, test selection, command registration and smoke imports.
Security routing reports zero errors/warnings; registration has no unexpected command drift.
Both repositories pass whitespace checks. Operational log bytes, sizes and mtimes remain exact.
No broad pre-commit rewrite or second full/log-noise run was necessary after the narrow delta;
the equivalent explicit format/lint/gates and guarded log-preservation results are retained.

SQL is still the exact separately completed 31bb2941 target below: no SQL file changed in this
continuation. All 59 mandatory document identities retain their original lines or exact bytes;
both S10E filename/previous_filename pairs retain base-content and absent-at-base proof. HEAD,
origin/main and production/main comparison anchors remain unchanged and both indexes are empty.

This completion receipt and its linked readiness receipt were added after scan finalization.
They are additive Markdown evidence/approval notes only; their narrow security routing outcome
is documented skip. All runtime, test, configuration and SQL hashes remain the exact reviewed
ones. The final-delivery-manifest.json in .codex_artifacts/s11-authority-composition identifies
each post-review document hash separately, every required file/action/base blob and both exact
archive identities. final-delivery-plan.md renders that complete file list. The sealed scan
snapshot is not relabelled as including subsequent receipt text.

Review outcome: no source-level blocker identified for the prepared draft-PR delivery. No Git
publication or merge is authorized by this result. The [exact next approval](release_readiness_and_rollback.md#s11-local-closure-and-exact-next-approval--2026-09-25)
is separate Bot-mirror and SQL draft PR delivery. Actual Windows containment, key custody and
writer exclusion, installed SQL/transaction outcomes, provider finality/readback/recovery and
operator G5 acceptance remain unproven. All S6/S8 retained gates/data/uncertainties are unchanged.


## S11 settled local validation checkpoint — 2026-09-25

The approved one-host/fresh-authority-identity implementation is locally authored. The trusted
issuer, real factories/callers, producer-connection SQL checks, full application metadata
contract and owned shutdown drain are now implemented. Historical pending-design and missing-
implementation notes below are superseded by this checkpoint, not deleted. No live gate closes.

The guarded full suite completed with **5,812 passed, 81 skipped in 626.25 seconds**. A later,
narrow pipe compatibility correction unified both client openers and added only the specific
FILE_WRITE_ATTRIBUTES right required for message-read mode, preserving the ban on pipe-instance
creation. The final affected authority/host/protocol/runtime/enrollment suites then completed
with **704 passed, 1 skipped in 8.08 seconds**, including the now-44-case boundary regression
file. The full run predates that final delta; the focused run covers it. No second full run is
needed without a new change, failure or unresolved concern. Native and SQL gates stayed off.

Both runs blocked external sockets and pyodbc connections and retained exact byte hashes,
sizes and mtimes of log.txt, error_log.txt, crash.log and telemetry_log.jsonl. That preservation
check covers log noise without another live or full-suite rerun. Raw commands/results are in
the ignored local .codex_artifacts/s11-authority-composition directory: authority-corrected-
full.txt/json and authority-message-mode-final.txt/json. An earlier interrupted run is retained
as history and is not passing evidence. Black's in-process API with AST-equivalence verification
and Ruff passed for the corrected files; final all-file gates and exact review are recorded in
the subsequent completion receipt.

Initial Bot Changes scan b79d01b8-af9d-45fb-b8db-613a5cdc3c67 found three source issues: import-
directory creation permissions, peer exceptions escaping the authority loop, and unbounded
Bot pipe I/O. The corrected scan f0d13c1f-b9f2-42fc-8e95-60d7db6cc0b9 completed with zero reportable
findings, before the final message-mode compatibility correction. Its snapshot digest was
codex-security-snapshot/v1:sha256:3904a1c078fa7e5dc7070ee8ee0118214824dc88aa022cf581396286aef7f98d.
Source-only bootstrap/import-directory checks, rejected links/listing failures, per-peer error
isolation and bounded overlapped I/O close those source issues. Native Windows behavior remains
unproven. The corrected scan's measured aggregate rollout usage was 3,647,550 tokens, including
3,567,488 cached input tokens, across one task; this is not an isolated scan-cost estimate.

The final Bot review is Changes, Deep off, at base/head
721ad7e0cd6b160ddddad328c2338a98bdfb6e0a. It must account for all 33 changed runtime sources,
reusing prior coverage only for exact unchanged hashes and reviewing the final three source
deltas. SQL scan 31bb2941-e0de-41d5-80df-5a7b5454d269 remains the separate unchanged 19-source
target recorded below. All pending documents and exact archive identities remain preserved.
Static/fake evidence is not installation, SQL transaction, provider, deployment or G5 evidence.


## S11 corrected SQL Changes review complete — 2026-09-24

Scan **31bb2941-e0de-41d5-80df-5a7b5454d269** completed and its sealed result was read back.
Mode: Changes, Deep off; SQL base/head **2352a898881d4b74d6eec153bb3cb381d6162041**.
Exact working-tree digest:
codex-security-snapshot/v1:sha256:8102c027eaa48ff7d6c39447cb058c2d0a251299bf1f12bb35b805e78ef39bc2.

All 19 changed source files received a fresh complete-file review: eleven schema/API snapshots,
six delivery/permission files and two parent-owned checker/fixture files. The two SQL Markdown
paths were read as context. No plausible candidates or reportable security findings remained;
validation/attack-path analysis was inapplicable with zero candidates. The earlier canonical
threat model was retained unchanged with its original version provenance explicitly separated
from current coverage. The six earlier NULL guard candidate instances were closed on their
actual corrected source. The frozen-target evidence verifies all 21 SQL paths against
their SHA-256s, unchanged HEAD and empty index. No SQL or provider operation was performed.

The managed scan directory is:
C:\Users\cwatt\.codex\state\plugins\codex-security\scans\K98-bot-SQL-Server\2352a898881d4b74d6eec153bb3cb381d6162041_20260924T212151Z_g6bm2xw0.
Retained outputs: report.md, findings.json, coverage.json, scan-manifest.json and
exports/results.sarif; preflight, per-file evidence and exact frozen-target verification remain
under artifacts. Preflight was ready with three passing capabilities and no config edits.
The completion tool reports aggregate rollout usage across four tasks: **6,536,348 tokens**,
including **6,090,752 cached input tokens**. This is its measured aggregation, not an inferred
isolated SQL-analysis cost; no account-wide usage estimate was substituted.

The NULL-correction checkpoint retained **403 passed, 9 skipped**, 181/454 static assertions,
zero ScriptDom errors for three changed SQL drafts, Black and Ruff success, and all four
operational logs byte/size/mtime exact. Current validators pass: architecture 39 files,
deferred 55 documents, security routing zero errors/warnings. Selection recommends full tests,
imports and command registration for the entire unfinished runtime tree; those remain final
settled-runtime gates. They were not unnecessarily rerun for this test-only/Markdown continuation.
Both repository whitespace checks pass; exact archive move pairs and all original documents
were reverified. These results do not prove installation, transaction/provider behavior or G4/G5.

The remaining issuer/runtime work exposed an unresolved deployment design boundary: the same
key on two machines cannot authenticate exclusion of unregistered credential holders, and local
DPAPI journals cannot establish another authority's private history. The concrete
[one-host/fresh-identity proposal](integration_contract_and_consumer_matrix.md#s11-remaining-host-and-credential-decision--2026-09-24)
and exact source/test manifest are ready; the operator's answer is pending. No additional
runtime/SQL change was made for that proposal. The separate corrected SQL result is complete;
the final Bot Changes review remains pending its completed implementation target.


## S11 completed SQL Changes review and correction scope — 2026-09-24

Codex Security scan dc5898eb-2967-4c3e-89a3-8a9cc7f47346 completed successfully as Changes,
Deep off, on the SQL working tree against 2352a898881d4b74d6eec153bb3cb381d6162041. Exact
target digest: codex-security-snapshot/v1:sha256:0f0ac8d40180540f88aa67fa68df68b3db01a5a9108a14611523e80cda4d2e46.
All 19 changed source files were reviewed; the two changed SQL Markdown files were accounted
for as context. Before sealing, all 21 pending SQL paths matched their pre-scan SHA-256s,
HEAD remained exact and the index was empty. No SQL or provider operation ran.

The scan has zero reportable security findings. Six candidate instances were retained and
statically validated: one NULL event-version comparison and five NULL procedure-definition
checks. Security suppression is supported by the authority-owned version, exact SQL role/
session checks, protected schema/deployment boundary and runtime refusal of opaque metadata.
It does not mean those guards satisfy the required correctness contracts. A related NULL
permission-observation issue in the narrow fixture is included in the correction proposal.
No exploit, SQL transaction, installed privilege or provider result was claimed.

The sealed report, findings.json, coverage.json and scan-manifest.json are under the local
Codex Security scan directory ending in
K98-bot-SQL-Server/2352a898881d4b74d6eec153bb3cb381d6162041_20260924T202951Z_w3bqkpnb.
The report retains the generated canonical threat model, all concrete candidate dispositions,
coverage and operational limitations. The completion tool reports aggregate usage of
14,099,739 tokens across five task rollouts, including 13,461,888 cached input tokens. This
is the plugin's aggregate, not a measured isolated cost for this review phase; usage was not
available when the semantic draft was authored.

Only four existing Bot documents receive additive review/scope notes. No Python or SQL source
changed, so the 5657-pass/81-skip guarded full-suite checkpoint remains tied to the same code.
No full test rerun is needed for this documentation-only continuation. Exact preservation and
archive proofs are retained in sql-review-scope-preservation.json and
sql-review-scope-archive-identities.json under the existing local s11-implementation directory.

The [correction design](integration_contract_and_consumer_matrix.md#s11-sql-null-guard-correction-proposal--2026-09-24),
[exact file scope](integration_implementation_manifests.md#s11-sql-null-guard-correction-manifest--2026-09-24)
and [approval plan](release_readiness_and_rollback.md#s11-sql-review-correction-approval--2026-09-24)
are pending. The trusted issuer, complete caller/runtime composition and whole-application
readiness remain real implementation work. S6 open gates, both uncertain publications,
all S8 evidence distinctions and operator-owned G4/G5 remain unchanged.


## S11 legacy permission final offline checkpoint — 2026-09-24

The current unchanged Python tree passed the full guarded suite: **5657 passed, 81 skipped
in 667.66 seconds**. All four operational logs retained their bytes, length and mtime. The
81 skipped cases remain unexecuted evidence; live SQL/network and Windows authorizations
were disabled. This run is distinct from the older 5515-pass checkpoint and the focused
561-pass/9-skip run below. Guarded smoke imports passed. Static command registration found
36 unique primary commands and 101 grouped subcommands, with no duplicate or surface drift.

The SQL repository validator passed on an isolated source copy. Its 15 warnings concern
historical migrations; none names the new 20260924_002 delivery. Original SQL validation
logs were not rewritten. The module-permission checker passed 454 assertions; ScriptDom
parsed all three SQL drafts and all 13 readiness batches without errors. Parsing, static
checks and synthetic permission rows establish no installed signatures or transaction result.

Artifacts: legacy-module-full-regression.txt/json, legacy-module-smoke.txt,
legacy-module-sql-repo-validation.txt, legacy-module-final-sql-parse.json and
legacy-module-readiness-parse.json under the retained local s11-implementation directory.
The exact 20-path delta and original-document/archive proof are recorded separately in
legacy-module-delta.json, legacy-module-preservation.json and
legacy-module-archive-identities.json. No index, branch, comparison anchor or remote changed.

The remaining transaction matrix must explicitly observe the existing UPDATE_ALL2 call to
sys.dm_db_index_physical_stats for dbo.KingdomScanData4 and CREATE_DELTA_TABLES' wildcard call
under their certificate tokens. The draft already grants database/server performance-state
access. Microsoft's documentation describes both object CONTROL and wider state visibility;
source review does not establish the exact installed token behavior. No extra CONTROL grant
was added on that assumption. See [Microsoft's permission contract](https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-objects/sys-dm-db-index-physical-stats-transact-sql).
Also verify counter-signature validity reporting through sys.fn_check_object_signatures and
the exact root/child capability transitions. The KVK schema's creation/owner definition was
not found in the authoritative source; dbo ownership is a required supported deployment
policy checked by the draft, not an observed fact or an authorization to change its owner.

The approved permission slice is complete as local source/offline work. The broader S11
issuer, complete caller composition and whole-application readiness remain real implementation
work; installed SQL, provider, containment, G4 and G5 remain separate operational evidence.


## S11 SQL NULL guard correction results — 2026-09-24

The approved source correction is applied. The SQL evidence checker passed 181 assertions;
the unchanged legacy permission checker passed 454 assertions. ScriptDom parsed the three
changed SQL drafts (event procedure, 001 migration, narrow fixture) with zero errors. The
changed Bot test passed synchronous Black equivalence/stability and Ruff.

Guarded offline authority/composition/event tests: **403 passed, 9 skipped in 6.11 seconds**.
All SQL gates were disabled; pyodbc connections and external sockets were blocked. The four
operational logs retained exact bytes, sizes and modification times. The nine skips are
unexecuted SQL tests, not transaction evidence. The earlier 5657-pass full suite applies to
the preceding runtime tree, whose Python runtime bytes are unchanged by this correction.

Local artifacts: sql-null-guards-copy-plan.json, sql-null-guards-staged-parse.json,
sql-null-guards-focused.txt/json and sql-null-guards-{files,preservation,anchors,delta}.json
under the task's s11-implementation artifact directory. The original document identities and
both exact archive pairs were verified again; neither Git index nor comparison anchor changed.

The completed SQL scan dc5898eb-2967-4c3e-89a3-8a9cc7f47346 covers the pre-correction digest
only. A new corrected immutable SQL Changes review, Deep off, remains required and authorized.
Final Bot review follows settled issuer/caller/runtime work; the repositories remain separate.

## S11 legacy permission authoring and offline evidence — 2026-09-24

The operator approved the additional local SQL permission-isolation scope. The source inventory
now covers 38 exact module definitions (37 procedures plus fn_NormalizeGovernorNameKey), 26
signature entries (three roots and 23 countersignatures) and 26 explicit certificate/entry-role
grant entries. Existing source-body hashes match; no business body was edited. The SQL static
checker passed 454 checks, and the forward, reverse and metadata-validation SQL drafts parsed
with ScriptDom. These are source results, not installed permission or signature evidence.

The Bot's 13 metadata-only readiness batches parsed with ScriptDom. The captured query inventory
was generated under blocked SQL/network/subprocess access; it independently compared the Bot
source-manifest pin and every canonical source definition against the authoritative SQL files.
The collector reads the producer's own cursor and opens no connection, commits no transaction,
issues no grant and invokes no business/file/provider procedure. Master public-certificate
encoding is read in master context through a fixed metadata SELECT.

Focused guarded validation: 561 passed, 9 skipped in 8.54 seconds. It included execution authority,
protocol, runtime composition, authority launcher, legacy preparation and the S11 SQL integration
module. All nine SQL cases remained disabled (including three new legacy permission/transaction
cases). External SQL/network and live Windows gates were blocked. All four operational log files
retained their original bytes, size and mtime. Synchronous Black AST-equivalence/stability and
Ruff checks cover the six changed Python paths. The earlier 5515-pass full regression remains
evidence for its older checkpoint; it is not relabeled as a full run of this tree.

Local artifacts under the existing s11-implementation evidence directory include the corrected
legacy-permission-ast.json, legacy-module-readiness-queries.json,
legacy-module-readiness-parse.json, legacy-module-staged-parse.json,
legacy-module-focused.txt/json and guarded SQL copy plan. The exact preservation/checkpoint
report follows this source update. Original S6/S8 evidence and both uncertain publications are
unchanged; no predecessor operational scenario was rerun.

The disabled legacy fixture uses its own approval token/file/hash and a separately named
disposable SQL instance with database ROK_TRACKER. The existing evidence fixture's differently
named disposable database stays separate. Its authored fallback case requires a single exact
synthetic ProcConfig_Staging sentinel, observes the original helper with denied ALTER, checks
committable caller ownership and confirms explicit rollback. No root import, upsert, real export,
file operation or provider action is hidden inside that fixture. Actual backup/restore and nested
root/proxy tests remain operator-owned G4 evidence.

## S11 legacy SQL permission scope discovery — 2026-09-24

After the 434-pass fixed coordination checkpoint, continued read-only tracing matched all fourteen
checked-in scan queries to thirteen exact authoritative SQL table/view definitions. Two queries name
ROK_TRACKER explicitly and others depend on default-schema resolution. The all-KVK export procedure
retains its ten ordered result sets. Seven existing procedure roots produced a retained inventory
of 37 lexical procedure candidates with exact source paths, SHA-256s and call-site lines. This is
bounded source evidence, not proof of complete dynamic closure or installed rights.

Manual verification confirmed caller-context output DDL in UPDATE_ALL2/sp_Rebuild_ExcelForDashboard,
existing master.dbo.xp_cmdshell/file operations in claim/archive/hash helpers and BULK INSERT in
IMPORT_STAGING_PROC_CORE. No repository certificate/signature delivery contract was found by the
SQL/PowerShell/Markdown source search. No live permissions, module signatures, proxy, credentials,
SQL connection or filesystem-import operation was inspected or changed. The configuration helper's
existing TRUNCATE-to-DELETE fallback is retained; its real transaction behavior is still unproven.

The proposed additional layer keeps privileged capabilities on exact reviewed modules, with separate
signature/countersignature and installation evidence. It does not broaden the Bot's trusted-evidence
rights or rewrite legacy business procedures. Microsoft documentation was consulted for SELECT INTO,
schema ownership-chain and nested-signature semantics; sources and interpretation are linked in the
[design proposal](integration_contract_and_consumer_matrix.md#s11-legacy-sql-privilege-isolation-proposal--2026-09-24).
This is a new SQL scope decision, not a validated production vulnerability or a completed security scan.

Only four existing Bot documents were added to in this follow-on review. All Python remains exact
to the tested 434-pass checkpoint and all pending SQL files/deletions remain exact. The
[additional proposed file manifest](integration_implementation_manifests.md#s11-legacy-sql-permission-scope-amendment--2026-09-24)
and [approval/rollback boundary](release_readiness_and_rollback.md#s11-additional-sql-permission-scope-decision--2026-09-24)
are concrete for operator review. Nothing in this proposal changes the approved local work's prior
authorization, document grouping, S6/S8 distinctions, unknown outcomes or operator-owned G4/G5 gates.

## S11 fixed coordination permission contract — 2026-09-24

Ruff, synchronous Black format/AST/stability, guarded imports, architecture (39 pending Python
paths), deferred validation (55 Markdown paths), security routing (zero errors/warnings), command
registration (36 top-level/101 grouped; no drift) and both repository whitespace checks passed.
The test selector recommends full regression for DAL/composition changes. The focused suite covers
this isolated readiness contract; another full run is deferred until the remaining composition is
settled. The previous full-run result below remains tied to its exact preceding source checkpoint.

Continued under the existing local implementation approval. The installation observation and
its approved SQL contract now require version 2. The existing nine read-only metadata batches
cover effective permissions for all 30 fixed export objects, both application-lock procedures,
and SELECT/UPDATE on every installed table column. Exact keyed equality rejects omitted,
duplicate, unknown, non-integer and mismatched permission rows. The column inventory is bound
to the independently approved installed-metadata fingerprint; observation cannot approve itself.
Version 1's evidence-only permission observation is rejected. This does not change SQL grants.

The authority profile requires the existing budget SELECT/INSERT/UPDATE, coordination/origin
reads and evidence-procedure execution, while denying direct evidence/preparation mutation.
The reader profile means the Bot's evidence-reader role plus its existing coordination writes;
it is not a read-only application principal. The fixed map covers 18 existing Bot write targets,
including preparation, source selection, intents, publication, delivery and pool operations.
Append-only membership/disposition updates, pool/file registration inserts, source-routing UPDATE,
DELETE and ownership/DDL capabilities remain outside this contract. Both profiles require the
existing application-lock APIs. Column checks also reject an unexpected column grant beneath
an otherwise denied table permission. These are fixed object-grant profiles, not support for
alternative column-only grants or a certificate for every application dependency.

Guarded authority/protocol/composition/launcher tests passed **434 tests in 11.31 seconds**.
They include budget/origin-read failures, evidence-column writes, malformed/partial inventories,
obsolete version rejection and both authority/enrollment startup paths stopping before session
transition, evidence-store creation or provider-child construction. External network/SQL remained
blocked, real Windows containment remained disabled and all four operational log bytes/sizes/mtimes
stayed exact. The previous 5,515-pass/78-skip full regression belongs to the preceding proof
acknowledgment checkpoint; it is not a full-suite result for this changed tree. The new fixed
permission boundary is covered by the focused suite; final settled composition still needs regression.

Static source verification matched each of the 30 objects to its exact authoritative SQL definition
and content hash, and matched the 18 Bot write targets/actions to current DAL callers. A SQL Server
ScriptDom parser accepted all nine captured parameterized metadata SELECT batches with zero errors.
The capture used fake rows only. No SQL connection, installed permission observation, grant change,
transaction/provider test or SQL source edit occurred. Source-derived permissions for broader
imports and configured capture queries, including KVK.sp_KVK_Get_Exports and checked-in scan-query
configuration, remain separate readiness work. The trusted issuer and complete caller/runtime
composition remain incomplete; this prerequisite supplies neither a ProofID nor writer exclusion.

See the [exact nine-path continuation](integration_implementation_manifests.md#s11-fixed-coordination-permission-continuation--2026-09-24)
and [remaining gates and rollback](release_readiness_and_rollback.md#s11-fixed-coordination-permission-continuation--2026-09-24).
Every earlier evidence entry below remains historical. All retained S6/S8 data, both uncertain
publications, pending documents and archive identities remain preserved. Separate exact Bot/SQL
Changes reviews with Deep off, authorized delivery, operator-owned G4 and G5 remain required.

## S11 exact proof persistence acknowledgment — 2026-09-24

Final guarded full regression passed **5,515 tests, 78 skipped, in 1,131.68 seconds** on the
unchanged final Python source for this checkpoint. All four operational log bytes/sizes/mtimes
remained exact. Ruff, synchronous Black format/AST/stability, guarded imports, architecture
(39 pending Python paths), deferred validation (55 Markdown paths), security routing (zero
errors/warnings), command registration (36 top-level/101 grouped; no drift) and both repository
whitespace checks passed. Four new local documentation links/fragments resolve. The guarded
runner supplies the log-noise check with additional byte hashes; the standalone log-noise
script was not run because it would repeat the same full suite without these SQL/network guards.
This is the current offline checkpoint, not final release validation of the unfinished runtime
composition or an installed transaction/provider/security-review result.

Continued under the existing local implementation approval. ExportExecutionDAL now validates
the complete proof request before opening SQL, then accepts only the exact returned proof after
consuming the procedure's entire result batch. This closes a persistence boundary; it does not
implement trusted proof production or establish complete writer coverage/provider finality.

The authoritative dbo.ExportReconciliationProof table and dbo.usp_ExportReconciliationProofIssue
procedure were reread in the separate SQL repository. The procedure returns SELECT before COMMIT.
The DAL therefore requires completed batch consumption, exact SessionID/ProofID/account, both
32-byte identity hashes, supported kind/outcome, exact original MembershipJson/EvidenceJson,
the SQL-compatible SHA-256 of UTF-16LE membership text, a datetime CreatedUTC and the exact
eleven-column shape. Driver UUID/binary representations are normalized without rewriting JSON.
Mutable input hashes are frozen before connection creation. Missing, duplicated, changed or
unacknowledged results remain EvidenceCommitUnknown; no repeat issue/provider request follows.
Preflight checks validate bounded typed input only, never infer a trusted finality flag.

The focused authority/protocol/composition suite passed **338 tests in 5.24 seconds** with external
network/SQL blocked and real Windows containment disabled. All four operational log bytes, sizes
and mtimes remained exact. The initial run passed 336 tests but two oversized parametrized test
names caused four Windows environment-variable setup/teardown errors; short explicit case IDs
fixed that test-harness issue. Both run outputs are retained separately. No runtime fix was needed
for those errors. A broader guarded offline regression is recorded separately at this checkpoint.

Only services/export_execution_dal.py and tests/test_export_execution_authority.py change source
in this continuation, accompanied by the three existing checkpoint documents listed in the
[implementation manifest](integration_implementation_manifests.md#s11-exact-proof-acknowledgment-continuation--2026-09-24).
No SQL source change is needed for this exact acknowledgment contract. Static SQL agreement and
mocked commit-loss tests do not establish installed transaction behavior or real provider outcomes.

Readiness tracing also confirms that the normal authority's RequestBudget uses SELECT/INSERT/
UPDATE on dbo.ExportRequestBudget, beyond the evidence-role permission checks currently authored.
The enrollment preparation path and Bot domain DALs have additional application permissions.
Enrollment mutation stays behind its dedicated authority procedure; origin verification also
reads dbo.ExportPreparation. This is not a proposal to grant direct enrollment-table mutation.
Complete fixed application permission profiles and their caller composition remain implementation
work; deployed effective grants and exclusion of both credential-holding hosts remain G4 evidence.
Do not treat an evidence-reader/authority role, protected registration, successful probe or this
new persistence check as complete readiness or permission to issue a trusted ProofID.

Both uncertain publications, S6 open gates, distinct retained S8 evidence and every pending
document/archive side remain retained. Bot and SQL delivery grouping is unchanged. Separate
settled Bot/SQL Changes reviews with Deep off remain required. No live SQL/provider/Discord,
credential operation, real import/export, predecessor operational rerun, Git publication,
bot-machine action, deployment or activation occurred. Exact G4 and G5 remain operator-owned.

## S11 origin-bound reconciliation probes — 2026-09-24

Final targeted validation passed **62 tests, 349 deselected, in 98.57 seconds**, covering all five
changed probe sequences, actual enrollment-to-pool verification, missing origins and late snapshot
changes after the last ordering guards. All four operational log bytes/sizes/mtimes stayed exact.
Ruff and synchronous Black format/AST/stability passed all nine Python paths; guarded imports,
architecture (39 pending Python files), deferred validation (55 Markdown files), security routing
(zero errors/warnings), and command registration (36 top-level/101 grouped; no drift) passed.
These are offline source checks, not installed/provider acceptance or a completed security scan.

Continued under the existing local implementation approval. Publication, ordinary retirement,
interrupted-retirement recovery, rollover drain and rollover completion probes now authenticate
the complete pool's existing managed origins before opening a provider stream. The shared
PoolOriginVerifier binds exact account, owner, Editor, index/slot membership and registration
digest, then reuses ManagedOriginVerifier's original creation/session/private-journal checks.
There is no new origin, file adoption, provider method, SQL object or credential behavior.

Each sealed observation now includes the authenticated origin digest. Before returning it, the
probe rechecks origin evidence and subsequently rereads the exact current job/pool/operation
snapshot. Missing/foreign origins, changed private evidence, or a version change during the final
origin read fail closed. The existing complete catalogue, closure, receipt-byte and retirement/
rollover-journal checks remain required. Successful origin verification does not establish
deployment coverage, external-writer exclusion, no-delayed-effects or permission to issue ProofID.
These probes still cannot settle, clear, retry, release claims or activate a factory.

Exact continuation source paths: services/export_reconciliation_service.py;
services/export_retirement_evidence.py; services/export_retirement_recovery_evidence.py;
services/export_rollover_evidence.py. Tests change in their four corresponding test files and
tests/test_export_enrollment_service.py. The latter exercises real offline enrollment transcripts
through the pool binding for private and public_viewer registrations; probe sequencing cases
separately stub the origin reader and inject missing/drifting origins and late snapshot changes.
The no-origin publication case uses the real verifier and refuses provider/catalogue admission.

The initial affected suite passed **406 tests in 429.66 seconds**, with all four operational log
bytes/sizes/mtimes unchanged. It began before the final snapshot-read ordering guards; its result
is distinct from the final targeted guard cases retained in origin-probe-final-pytest.txt and the
matching log-preservation JSON artifact. Network and SQL remain blocked, and real containment
tests disabled. No retained S6/S8 operational fixture is rerun. A settled full regression and
separate exact Bot/SQL Changes reviews (Deep off) remain final delivery gates.

The continuation has nine Python and three additive Bot documentation paths; every SQL byte
and other pending file/deletion remains unchanged. Both indexes, comparison anchors, all inherited
documentation and exact archive identities are preserved. Trusted issuance, complete runtime/
caller factories and deployment readiness remain unfinished; no runtime acceptance is claimed.
Existing local approval persists. Mandatory Bot/SQL document grouping, both uncertain publications,
all retained data and separately operator-owned exact G4/G5 boundaries remain unchanged.

## S11 player audience confirmed — 2026-09-24

The operator confirms that existing output sharing is **anyone with the link — Viewer**, and
reports that none of the outputs contains secret information. This resolves the audience question
in the preceding inventory entries. Preserve that audience for published outputs; do not request
the same decision again. This is operator-reported intended sharing, not an observed live ACL.

The existing SheetsRegistration public_viewer contract and typed permission operation match:
type=anyone, role=reader, allowFileDiscovery=false. No new audience mode, account identity,
permission behavior, SQL delta or runtime change is required for this clarification. Recorded
fresh-file enrollment, private clear/readback before reuse, exact owner/Editor checks and all
termination/reconciliation gates remain the agreed lifecycle. Public readability does not change
write ownership, ordered publication, byte-exact receipts or handling of unknown remote outcomes.

The requested operator inventory clarification is now complete. Remaining work is the already
approved trusted issuer/shared caller composition and its validation, followed by separately
authorized exact G4 operations and operator G5 acceptance. No additional sample file, credential
material or implementation approval is requested. Both credential-holding hosts remain in the
G4 coverage packet. This documentation-only continuation preserves all earlier source/evidence,
both uncertain publications, mandatory Bot document/archive grouping and separate SQL delivery.

## S11 account and host inventory response — 2026-09-24

The operator supplied the normal Google service-account email and reports that both the Bot
machine and development PC hold its key. They report no edits to generated outputs after upload,
and that all players have read-only access. The exact supplied identifier is retained in the
local operator inventory artifact, outside source defaults and the scrubbed mirror documentation.
No credential file was opened. Key IDs, whether the two copies are identical, effective file
permissions, running processes and current deployed configuration have not been observed.

This completes the requested identity/host/output-edit inventory at the operator-report level.
The preceding report of no other Bot instances, import jobs or manual mutation workflows remains
applicable. It does not remove internal scheduled/configuration writers from the source inventory.
The upstream export generator supplies Discord input files; it is not thereby an outgoing Sheets
writer. The human owner remains a trusted administrator. The no-edit report concerns generated
outputs and does not redefine configuration/input-sheet contracts.

Shared coordination remains the chosen design for the participating Bot paths. A credential copy
on the development PC remains relevant even with one reported Bot instance: code using that copy
can bypass the Bot's coordinator. The proposed production topology is one normal export authority
on the Bot machine, with development offline or isolated from production write capability. Exact
exclusion controls are a G4 deployment decision, not implemented or established by this report.
If development must participate in production exports, it instead requires its own registered
local authority using the same durable coordinator and complete storage/identity bindings.
Neither option authorizes a key change, process operation or additional Bot instance now.

Player read-only access establishes a role, not the audience. The question whether existing
sharing is anyone-with-link Viewer or named people/groups remains pending. The current typed
public Viewer operation uses anyone/reader with allowFileDiscovery=false; do not silently widen
named/group access to that audience. Registration and any later exact sharing operation must
match the operator's answer. No provider sharing operation has been performed.

See the [two-host G4 coverage packet](release_readiness_and_rollback.md#s11-reported-writer-inventory-and-g4-coverage--2026-09-24).
The real remaining source work is trusted ProofID issuance and complete shared runtime/caller
composition; the inventory is not a finality certificate or a reason to manufacture another SQL
delta. Installation, transaction behavior, provider effects and deployed writer exclusion remain
separate unproven gates. No sample workbook, secret or further implementation approval is required
for independent local work. Final Changes reviews (Deep off), G4 and G5 remain separate gates.

This continuation changes only this evidence document and the release-readiness document,
additively. Runtime/tests/SQL and every other pending byte/deletion remain unchanged. Validation
and exact preservation results are retained in the local writer-inventory checkpoint artifacts;
no runtime test result is newly claimed for a documentation-only change. Existing local source
approval, mandatory Bot document/archive grouping, separate SQL delivery, all S6/S8 evidence,
both uncertain publications and all retained data remain intact. No Git publication, deployment,
activation, credential access/change, real import/export or SQL/provider/Discord execution occurred.

## S11 operator inventory clarification — 2026-09-24

The operator reports that a separate system generates files, which an admin manually uploads to
Discord. These are incoming data files, distinct from the Bot's outgoing Google Sheets exports.
The operator creates Google Sheets and grants a service account access. They report no other
import jobs (all imports originate in Discord uploads), no other manual tools/workflows that
trigger changes beyond Bot commands/uploads, and no other Bot instances. Shared coordination is
their preferred treatment. These are operator-reported scope facts, not observed deployment proof.
Do not infer that the Bot has no internal scheduled/cache/configuration writers from this report.

Source trace: DL_bot.py supplies handle_kvk_all_upload with _auto_export_kvk;
upload_routes/kvk_all_route.py invokes ingest_kvk_all_excel and passes a captured preparation ID
to the automatic export where available. kvk_all_importer.py validates the Full Data workbook;
kvk/dal/kvk_all_import_dal.py calls KVK.sp_KVK_AllPlayers_Ingest and
KVK.sp_KVK_Recompute_Windows before commit. The normal legacy Sheets renderer reads
KVK.sp_KVK_Get_Exports, loads configured service-account credentials and opens the primary
workbook by name. Additional legacy renderers contain create-if-missing branches. Their presence
does not establish actual use or permission, and does not authenticate a new managed pool's origin.
The coordinated path instead submits the exact durable capture and registered destination plan.
All three stored procedure definitions were checked in the separate authoritative SQL source repo.

Shared means one coordinated admission, ownership and provider-budget boundary across relevant
Bot paths, with per-consumer/source data and output registrations preserved. It does not merge
source contracts or permit different pools to overlap files. One Bot can still have overlapping
uploads, admin actions and background work. Queueing and retained uncertainty are deliberate costs
of preventing concurrent updates, partial captures and unsafe reuse. Existing manually provisioned
legacy sheets remain distinct from the approved recorded enrollment for new reusable S11 outputs.

Remaining inventory details requested: the service-account email (an identifier, no key/token),
the machines holding its credential, and whether the admin edits generated output tabs or their
sharing after setup; edits to separate configuration/input sheets must be identified separately.
Sample workbooks are not needed to resolve this writer inventory. Existing S6/S8 evidence and both
uncertain publications remain retained. This clarification changes no runtime or SQL source and
authorizes no live checks, credential changes, Git publication, deployment or activation. Existing
local implementation approval and separate exact G4/G5 gates remain unchanged.

## S11 shared-writer ownership continuation — 2026-09-24

Validation completion: the broader intermediate-tree run passed **5,408 tests with 78 skips**
in 586.33 seconds. It started before the final nested-failure guards and their two new cases;
the separate **242-test focused pass** covers those final changes. Do not call this an immutable
final-target full run. Both runs preserved operational log bytes, sizes and modification times;
all live SQL/Windows authorizations were disabled and network/SQL access blocked. Architecture
checked 39 pending Python files, deferred validation checked 55 Markdown files, security routing
reported zero errors/warnings, and guarded imports and command registration passed (36 top-level,
101 grouped; no drift). Both repository whitespace checks passed. Exact preservation records
retain all 59 inherited documentation identities and both filename/previous_filename archive
pairs; both indexes are empty, anchors unchanged, and every SQL byte/deletion unchanged.

Continued under the existing local implementation approval. A WriterOwner now belongs to its
exact LegacyExportRuntime instance. Nested contexts cannot replace or disable that runtime,
substitute a different owner, or turn a closed inherited/explicit token into fresh SQL admission.
An exception from a nested producer marks the shared owner failed even when the parent catches
it: further writer work and completion checkpoints are refused; the root retains uncertainty
instead of capturing a partial generation or returning a misleading success. The root remains
responsible for closing its own connection; a foreign runtime cannot checkpoint, release or close it.

Exact executable/test delta: services/legacy_export_snapshot_service.py and
tests/test_legacy_export_snapshot.py. These reuse the existing context variables, writer decorators,
SQL ownership/session methods, durable captures and drain_thread; no global registration shortcut,
new credential/API, SQL delta, command, production factory or activation is introduced. Runtime
identity is an in-process binding, not replacement evidence for SQL owner/fence/version CAS.
Restart still requires fresh composition and durable reconciliation; old tokens are never adopted.

Focused validation passed 242 tests across the legacy snapshot, processing pipeline and runtime
composition files, with all four operational logs unchanged. New cases cover foreign/closed owners,
nested runtime substitution, caught ordinary/BaseException failures and concurrent tasks carrying
their exact runtime/owner through thread offloads. The initial test-fixture omission (uncreated
private test directories) is corrected and its failed run retained. Ruff and synchronous Black
format/AST/stability checks pass both changed paths. A broader run was started before the final
caught-failure guards; its result is recorded separately and cannot replace the final focused cases.

The actual startup/caller composition remains incomplete: use_runtime is scoped to an explicit
context, and startup context alone cannot populate unrelated future Discord tasks or standalone
writers. Complete shared factory resolution, trusted ProofID issuance and deployment readiness
remain required. No caller-supplied Boolean, manifest allowlist alone or current blank readback
can establish complete writer exclusion. The requested operator inventory must identify other
hosts, scheduled jobs, manual tools and human-owner/provider credential users, plus external
shared-output SQL writers (or explicitly identify categories with none). No secrets are requested.

Local implementation approval persists. Separate settled Bot/SQL Changes reviews, Deep off, and
final regression remain required before a merge-readiness handoff. Exact G4 operations and G5
acceptance remain operator-owned. No SQL/provider/Discord operation, real import/export, credential
access, Git publication, predecessor operation or bot-machine action occurred. Mandatory document
grouping, all S6/S8 evidence, both uncertain publications and every retained artifact remain intact.

## S11 origin identity and local probe transport — 2026-09-24

Under the existing local implementation approval, origin verification now loads the original SQL
authority session and requires the enrolled plan's exact protected manifest digest and protocol.
Enrollment's fixed workbook read uses includeGridData=true, with no field projection that could
hide notes, formatting, charts or hidden grid metadata; its separate formula read still covers the
entire one-cell initial grid. Incorrect metadata retains preparation ownership and created origins.

The parent now has LocalAuthorityClient: fixed proof producers can use the same registered broker
and SQL admission without calling the parent's own synchronous pipe server. This path accepts only
probe streams and reads, refuses enrollment/mutation authority, and retains uncertain failures.
It is an internal transport dependency; it does not issue ProofIDs or enable any production factory.

Exact continuation Python paths: services/export_runtime_composition.py;
services/export_execution_dal.py; services/export_enrollment_service.py;
tests/test_export_runtime_composition.py; tests/test_export_enrollment_service.py. No SQL source
changed after the enrollment checkpoint. The final three-file focused run passed 270 tests and
preserved operational log bytes/size/mtime. Ruff and synchronous Black AST/stability checks passed
these paths. The full settled suite and separate Bot/SQL Changes reviews remain future gates.

An operator inventory of external hosts, scheduled/manual Google-account users and shared SQL
writers has been requested to define exact deployment coverage checks. No source search proves
that inventory empty. Keep complete coverage/issuer/factory readiness unresolved until the actual
boundary is specified and its later G4 evidence independently verified. This request grants no
live access or operation. Existing local implementation authorization and all S6/S8/G4/G5 limits
remain unchanged; do not substitute an editable assertion for a trusted proof producer.

## S11 fresh-file enrollment source checkpoint — 2026-09-24

Completion validation for this checkpoint: the expanded ten-file suite passed **650 tests** with
**six live SQL skips**. After the final strict response/receipt-type checks and profile/launcher
tests, all **148 enrollment/protocol/launcher tests** passed. Tests/test_export_authority_launcher.py
is also an exact implementation-delta path (separate normal/enrollment manifest coverage). No
uninterrupted full-suite pass is claimed for this checkpoint; the settled full run remains pending.
Both test runs preserved all four operational logs exactly. SQL source checker passed 162 assertions;
ScriptDom parsed all 13 SQL source files; eight synchronized weakened source variants were rejected.
These source checks do not execute SQL or establish transaction/provider behavior.

Ruff passed all 13 changed Python paths. Black's Windows process-pool invocations did not exit;
their exact task-owned process trees were verified and stopped, then the synchronous Black API
passed formatting, AST equivalence and stability for all 13 paths. No unrelated process was stopped.
Architecture checked 38 pending Python files; deferred validation checked 55 Markdown files;
security routing passed with zero errors/warnings; guarded import and command registration passed
(36 top-level, 101 grouped, no drift). All 59 inherited documentation identities and both exact
archive filename/previous_filename pairs remain intact. Both indexes are empty and comparison
anchors unchanged. The continuation changes exactly 21 Bot paths (13 Python, eight docs) and
11 SQL paths; every other pending byte/deletion remains unchanged from the admission checkpoint.

The operator explicitly approved the additional enrollment scope. All work here is local source,
static validation or guarded offline tests; no credential/OAuth, provider, SQL, Discord, publication,
bot-machine or deployment action was performed. No predecessor operational fixture was rerun.

### Exact source delta

New Bot paths: services/export_enrollment_service.py; scripts/enroll_export_output_pool.py;
tests/test_export_enrollment_service.py. Existing approved paths extended:
services/export_execution_protocol.py; services/export_execution_authority.py;
services/export_execution_dal.py; services/export_reconciliation_service.py;
services/export_runtime_composition.py; scripts/run_export_authority.py;
scripts/run_export_provider_child.py; tests/test_export_reconciliation_service.py;
tests/test_export_execution_sql_integration.py. The contract/manifests/evidence/readiness,
ENV_REFERENCE and startup/shutdown/diagnostics documents receive additive evidence only.

New SQL paths, in the separate SQL repository: sql_schema/dbo.ExportManagedFileOrigin.Table.sql;
sql_schema/dbo.usp_ExportOutputEnrollmentTransition.StoredProcedure.sql. Existing unmerged,
uninstalled paths amended: migrations/20260924_001_export_execution_evidence.sql;
sql_schema/dbo.ExportExecutionStream.Table.sql;
sql_schema/dbo.usp_ExportExecutionStreamTransition.StoredProcedure.sql;
sql_schema/dbo.usp_ExportProviderRequestEventAppend.StoredProcedure.sql;
sql_schema/dbo.usp_ExportReconciliationProofIssue.StoredProcedure.sql;
validation/kvk_source/s11_export_execution_evidence.sql;
deploy/Test-ExportExecutionEvidenceContracts.ps1; docs/SQL_DELIVERY_LOG.md; migrations/README.md.
No predecessor migration or schema snapshot is rewritten.

### Contracts and evidence limits

One exact protected plan binds the account/storage identities, human owner, service-account
Editor/project, narrow OAuth profile, source manifest, PlanID and one index plus 2–16 slots.
Enrollment uses a separate authority-side entry/profile; normal Bot IPC accepts neither creation
nor Editor grants. Each create is a fixed private one-cell workbook, recorded before send; its
response and exact child closure precede returned-file resource acquisition. SQL preserves existing
account/sorted-resource/owner ordering, queue precedence, owner/fence/version CAS and an eight-pool
bound including still-unregistered enrollment plans. One phase has one stream, without retries.

Origins append `created` then `eligible` records. Immutable file/ordinal/request uniqueness,
preparation/session/stream/event foreign keys and private response/closure/receipt digests bind
the lineage. Eligibility requires the entire fixed owner/ACL/grid/blank-cell transcript and all
bootstrap children closed. Canonical receipt comparisons distinguish JSON numeric types. SQL
origin writes remain narrow-authority-only; ordinary reader rights cannot create or alter them.
The migration now checks six evidence tables/five procedures and refuses incompatible partial
installations. It never maps principals or activates registration.

Catalogue selection now includes every origin preparation stream, including account-only creation
before a FileID existed. SQL proof issue and consuming settlement both require eligible origins;
the protected origin verifier also reconstructs creation/readback from private bytes. Current
emptiness, a completed mutable preparation, or zero old ledger rows cannot establish prior history.
Origins are necessary input to the still-pending complete finality issuer, not ProofIDs themselves.

| Layer | Local result | Still separate |
|---|---|---|
| Bot/static/offline | Typed enrollment, no Bot enrollment IPC, fixed endpoint/profile, closed-stream origin verification and negative paths | Complete issuer/factories, settled full regression and Changes review |
| SQL/static | Source-synchronized migration, structural/permission/lineage checks and parser validation | Installation, effective principals, transaction races/locking, actual backup/restore |
| Transaction fixtures | New disabled synthetic enrollment admission/replay/stale-owner/unproven-bind tests; reader origin/API denial | Exact disposable target/operations approval and execution |
| Provider/Windows | Fakes for response/commit/closure loss, wrong identity/ACL/grid, altered receipts and broad/unknown token scopes | Actual owner consent, OAuth refresh scope behavior, private creation/readback and OS containment |
| Deployment | Explicit separate protected creation profile, no import/startup activity or automatic pool registration | Full writer/credential/host inventory and exclusions, exact G4 operations and G5 acceptance |

Initial focused enrollment validation: 35 passed. The related authority/protocol/reconciliation/
composition/launcher run then passed 403 tests, with five live SQL skips and unchanged operational
logs. The first related run exposed old test-cursor assumptions about the new origin lookup; those
fixtures were corrected, without weakening the lookup. The wider current regression and final
source checks are recorded separately after completion. These interim results do not stand in for
the final settled full-suite/security gates or any live evidence.

Rollback remains non-installation now. After separate deployment authorization, close admission,
drain/observe owned children and retain every preparation, origin, stream, request, unknown file
and receipt. Never delete uncertain creations, replay a grant/create, reset ownership, substitute
old direct writers or use retained S6/S8 evidence as fixtures. SQL rollback is forward-fix only.
Both uncertain publications and every open S6 gate remain retained and unresolved.


## S11 drain, legacy streams and protected registration — 2026-09-24

This approved local continuation adds fixed rollover-drain observation, exact legacy/configuration
stream binding and a protected immutable authority registration. It does not enable the production
factories or issue a finality ProofID. The previous completion-observation checkpoint remains intact.

### Exact implementation delta

- services/export_rollover_evidence.py and tests/test_export_rollover_evidence.py: common exact
  operation context, unowned closing/draining observation and sealed replay; all registered file
  identities/ACLs, current snapshot and full recorded catalogue must agree. Public current files
  can be observed without being labelled private, empty or reusable. No ready/claim/clear occurs.
- services/export_runtime_composition.py and tests/test_export_runtime_composition.py: exact
  S10C captured-job/configuration scope factories, immutable UTF-8 configuration digest, account/
  owner/fence/version/storage/resources; protected RuntimeRegistration, full pool/legacy inventories,
  human owner/service-account identity/audience and protected-file disjointness. SQL repeats current
  epoch/CAS/resource checks. Registration is scope authorization, not historical coverage.
- services/export_provider_adapter.py and kvk/services/new_source_export_service.py: share static
  Sheets/Drive request-descriptor clients with no credential loading or local HTTP capability.
- gsheet_module.py, proc_config_import.py and their respective tests/test_gsheet_module.py and
  tests/test_proc_config_import.py: recorded configuration reads use the authority exactly once;
  no SDK discovery, credential access, alternate read fallback or silent empty configuration on
  unknown response. Disabled-mode behavior remains; the service client is created inside the
  configuration claim, including dry runs. Pandas blank-cell conversion remains its existing shape.
- scripts/run_export_authority.py and tests/test_export_authority_launcher.py: require the protected
  runtime_registration manifest field; validate it before SQL startup, and reject an unregistered
  account/hash/file set or incompatible legacy scope before child/stream creation.
- These five existing Bot documents receive additive evidence, manifest, contract/readiness and
  environment notes. No SQL byte/object, actual environment, credential or installed service changes.

### Validation and retained limits

Focused legacy/configuration/adapter validation passed 210 tests. The initial registration/rollover
run passed 312 tests with one integration-fixture failure: a test constructing AuthorityBroker lacked
the new mandatory registration argument. Correcting that fixture and its exact file membership
passed all 202 composition/launcher tests; all 111 rollover cases had passed in the preceding run.
The final expanded regression outcome is recorded in the appended validation result below.

Earlier intermediate test failures remain in the local logs: a misplaced rollover test tail and
an assertion expecting None where Pandas represents a blank as NaN. Corrected affected tests pass;
neither justified a change to the production contracts. Ruff and Black format/AST/stability passed
all twelve Python paths. Architecture checked 35 pending Python files; deferred validation checked
55 Markdown files; security routing reported zero errors/warnings. Guarded import smoke and command
registration passed (36 top-level, 101 grouped, no drift), and both repository whitespace checks
passed. Complete test/log and exact preservation artifacts accompany this checkpoint.

| Evidence layer | Established locally | Still required |
|---|---|---|
| Bot/static | Drain observations, bound legacy/config streams, immutable authority inventory and refusal of invalid scopes | Complete origin/coverage and trusted issuance; final shared-caller factories/readiness |
| SQL/static | Current authoritative S10C/D/E and S11 shapes inspected; no SQL delta in this continuation | Installed definitions, effective application/evidence permissions and concurrent CAS/transaction evidence |
| Provider/Windows | Fixed fake request/response, closure/replay and corruption cases | Actual containment, credential isolation, complete external-writer exclusion and provider outcomes |
| Deployment/G4/G5 | Production factories remain closed; no live target selected | Exact operation packet, permitted identities/paths/builds and operator acceptance |

### Expanded offline regression result

The broad guarded run completed with **5,326 passed, 77 skipped and one harness-induced failure**.
The failure was test_two_processes_perform_one_metadata_and_rowset_fetch: the local wrapper lacked
an `if __name__ == "__main__"` guard, so Windows spawn re-entered pytest instead of the cache worker.
The wrapper was corrected, the exact spawned helper belonging to this run was verified and stopped,
and the complete affected test_kvk_target_cache_repository.py file then passed **16 tests**. No
application source or unrelated test was changed. Both runs independently verified all four
operational logs unchanged, including exact bytes, sizes and modification times. Live SQL/network
were blocked and every S8/S10/S11 SQL and S11 containment authorization was disabled. These are
offline regressions, not predecessor operational reruns. The initial full-run failure is retained;
do not relabel it a single uninterrupted all-green full run. A clean full run and separate exact
Changes reviews remain final gates on the completed implementation after the scope decision.

All twelve changed Python files passed Ruff and Black format/AST/stability checks. Local link QA
resolved 133 links/anchors across the five changed documents, including an existing explicit HTML
anchor (the first checker omitted HTML anchors and was corrected without changing repository links).
The checkpoint records all 59 original documentation identities, both exact archive pairs, empty
indexes and unchanged comparison anchors. Every SQL byte/deletion is unchanged. No owned test
helper remains running, and no unrelated process was stopped.

### Additional implementation decision

The current request ledger cannot establish an existing file's pre-recording history. Neither a
blank readback, a protected allowlist nor zero matching S11 streams is that proof. The five existing
evidence entities have no implemented authenticated creation-to-returned-file origin association,
and the fixed child currently refuses create/discovery. Complete automatic proof issuance therefore
still has a real implementation gap; deployment observations are a separate prerequisite.

The [initial-enrollment proposal](integration_contract_and_consumer_matrix.md#s11-initial-file-enrollment-additional-implementation-proposal)
defines the concrete additional choice: recorded creation of new dedicated human-owned files via
a separate authority-held owner-authorized profile, existing preparation ownership with a typed
enrollment purpose, one additional SQL origin entity/transition procedure, exact proposed paths,
negative cases, independent live gates and rollback. This scope is proposed only. Its additional
credential capability and persistence contract require the operator's explicit scope amendment.
No OAuth consent, credential access, SQL/provider operation, real file creation or deployment is
requested now. Existing files with unprovable history and both retained uncertainties stay blocked.

The normal shared-writer hooks were retraced: processing_pipeline.collect_producer_captures and
admitted_writer/writer_scope, legacy manual export helpers, kvk_all_importer, stats_module,
player_stats_cache, proc_config_import and grouped admin services. They still fail closed in admitted
mode until one complete runtime bundle is installed. This continuation does not claim those
factories were wired, application readiness passed, or the complete S11 implementation finished.
The origin decision changes their trusted composition prerequisites; do not install a placeholder
coverage callback or caller-supplied true flags merely to open them.

Separate exact Bot/SQL Changes reviews with Deep off remain required on the settled implementation;
no final merge/readiness handoff is claimed. This checkpoint is not a full/deep security scan or
transaction/provider test. Existing local implementation approval otherwise persists.

All inherited documentation and prior pending source/SQL evidence are preserved. Both archive
identities require exact filename/previous_filename plus base-content/absent-at-base proof; counts
are not proof. Every pending Bot document, S11 pack/starter, S10D/E closeout and both archive sides
remain in the next genuine Bot implementation PR; SQL work and its closeouts remain separate.
No Git mutation/publication, predecessor operational rerun, SQL/provider/Discord execution, real
import/export, bot-machine change, deployment or activation occurred. S6 gates, S8 evidence layers,
both uncertain publications and retained data remain intact. G4/G5 stay operator-owned. Current
rollback is non-installation; later stop admission, drain/reconcile owned work and retain uncertain
claims, exact journal history and receipt bytes. Never blindly retry interrupted retirement.


## S11 sealed rollover completion observation checkpoint — 2026-09-24

The approved local implementation now evaluates the original rollover phase history and a fresh
read-only completion probe. The final index contains the new-season marker, so its earlier empty
state must come from the original clear transcript. Current slot emptiness and final index setup
remain separate observations. This source checkpoint neither issues a ProofID nor enables a factory.

### Exact continuation scope

- services/export_rollover_evidence.py: fixed completion context, protected original drain-proof
  association, complete original private/clear/setup phase verification, fresh read-only evaluator
  and closed-catalogue/sealed-transcript orchestration.
- tests/test_export_rollover_evidence.py: 73 offline cases using actual typed provider descriptors
  and recorded fake responses, including public-to-private transitions, sixteen slots/eight pool
  registrations, lost journal acknowledgments, exact ownership and altered historical/current evidence.
- services/export_runtime_composition.py: require a fresh unchanged operation snapshot before a
  closing probe; add an owned running/uncertain completion probe that preserves all owner/fence/
  version/resource identities and cannot adopt a closing operation.
- tests/test_export_runtime_composition.py: update the existing closing-probe fixture to supply
  its exact current operation snapshot for the new admission recheck.
- These three Bot evidence/manifest/readiness documents receive additive checkpoint notes.

Only these seven Bot paths differ from rollover-setup-files.json. All other pending Bot files
and every SQL byte/deletion remain exact. No SQL object, DAL query or installation contract changed.
The authoritative SourceOutputOperation, ExportExecutionStream, ExportProviderRequest and
ExportReconciliationProof definitions and proof-issue procedure were inspected; no SQL was executed.

### Evidence contract and conservative outcomes

The fixed evaluator requires the complete original plan and setup-phase journal. It accepts only
the retained running or uncertain owner, exact original resource versions/fence/epoch/registration,
all original private clear entries, matching recorded setup evidence, no unresolved jobs/legacy
receipts and no staged/quarantined/retired slot. Partial operations need separate reconciliation;
this evaluator never resumes their mutations or invents a recovery owner.

The historical verifier reloads the original protected rollover-drain ProofID and compares its
account, kind, outcome, registration, snapshot, membership hash and canonical evidence body with the
operation journal. Missing pre-S11 proof evidence remains unresolved. It derives every original
phase claim version from the actual private/clear/setup transition sequence and checks exactly one
sealed mutation stream for each phase. Owner/fence/epoch/resource membership, full private request
and event bytes, child closure, successful outcomes and the final read projections must match.
The original clear's replacement sheet ID and complete manifest must equal the durable journal.
Private ACL and setup marker readbacks are evaluated by the existing fixed transport validators.
Historical mutations are never replayed. An unknown outcome is never turned into success.

A fresh probe checks every slot against its original sheet identity and private empty shape, then
checks the complete marker-bearing index against its original sheet identity. The complete relevant
account catalogue is checked before and after the probe; the probe closes before its private
transcript is replayed. Snapshot and original-journal fingerprints are rechecked. Changed ownership,
catalogue membership, original proof/phase bytes, marker, sharing or sheet identity reject the
observation. The returned immutable observation contains original clear evidence, current slot
evidence, current setup evidence and closed membership, not a termination Boolean or settlement.

Original protected drain proof and complete recorded S11 closure are necessary inputs. They do not
establish pre-S11/external-writer exclusion or a new no-delayed-effects claim by themselves. Complete
trusted writer/deployment coverage and protected ProofID issue orchestration remain implementation
work; no caller may substitute an observation or a successful fresh read for those prerequisites.

### Validation and remaining gates

The initial 67 focused cases passed. After adding public-sharing, maximum-bound and journal-match
cases, the final affected 17-file suite passed **968 tests / six gated checks skipped**, with S11
SQL authorization disabled. This run includes the preceding final JSON-type proof fix. Ruff and
Black format/AST/stability checks passed for all four Python paths; architecture checked 31 pending
Python paths. Deferred validation checked 55 Markdown paths; security routing reported no errors
or warnings. Import-only smoke and command registration passed (36 top-level, 101 grouped, no
drift). Both repository whitespace checks passed. select_tests still requires full pytest on the
completed composition. Separate exact Bot and SQL Changes reviews with Deep off remain pending
the settled implementation. The initial Ruff check found one unused import, removed before this
suite; no test failure required a behavior change.

| Evidence layer | Established here | Still unproven / pending |
|---|---|---|
| Source/offline | Complete phase association, fixed current readback, sealed replay and conservative failure | Trusted issuance, full caller composition and final regression/security review |
| SQL/static | Existing authoritative object contracts inspected; no SQL delta | Installation, effective permissions and concurrent transaction/CAS behavior |
| Provider/OS | Recorded fake successful/unknown responses and child-closure validation | Actual provider finality, containment and complete old-writer exclusion |
| Deployment/G4/G5 | Closed factories, exact retained evidence and approval boundaries | Immutable deployment/writer coverage, exact authorized operations and operator acceptance |

Remaining real implementation includes the rollover drain producer, protected ProofID issuance
with complete writer/deployment coverage, actual-caller/shared-writer composition, immutable
account/registration/storage/spool bindings and remaining application readiness checks. Completion
observation is now authored, but its trusted issuance and runtime connection remain unfinished.
Existing local implementation approval persists; no further approval is needed for that local work.

Fresh rollover-completion artifacts verify all 59 inherited documentation identities, both exact
S10E filename/previous_filename archive pairs with original-content and absent-at-base proof,
unchanged comparison anchors, empty indexes and the exact seven-path continuation. Every pending
Bot document stays with the next genuine authorized Bot implementation PR, including the pack/
starter, S10D/S10E closeouts and both archive sides. Pending SQL implementation and closeout docs
remain separate. No Git publication or document regrouping occurred.

Preserve S6 open gates, both uncertain publications and retained data; S8A six scripts, S8B fifty
cases/actual restore versus offline history, and S8C seven local checks remain distinct. No live
SQL/provider/Discord operation, real import/export, actual containment test, predecessor operational
rerun, bot-machine action, deployment or activation occurred. G4/G5 remain operator-owned. Rollback
is non-installation now; later close admission and drain owned delivery, retain uncertain claims and
append-only journals/byte-exact receipts, and require explicit retirement recovery without blind retry.


## S11 complete rollover setup readback checkpoint — 2026-09-24

The approved local implementation now checks the complete final rollover index. Previously
rollover_setup checked the Sheet1 value and sharing, which could accept the expected marker
while extra tabs, metadata or hidden cell content remained. It now delegates to the fixed
read-only rollover_setup_readback evaluator before returning setup evidence. A mismatch remains
unresolved; no clear, repair or retry follows. This source correction is not activation.

### Exact continuation scope

- kvk/services/new_source_export_service.py: validate distinct positive season identities;
  add complete read-only final-index evaluation; make the existing setup writer use it.
- tests/test_kvk_output_rollover.py: 38 new offline cases for typed reads, raw/computed cell
  values, complete workbook/ACL rejection, invalid identities before requests, read response
  loss, no repair following contradiction, and full private-transcript replay without provider I/O.
- services/export_retirement_recovery_evidence.py and
  tests/test_export_retirement_recovery_evidence.py: preserve exact JSON types when comparing
  original protected proof bodies with recorded disposition associations. Canonical JSON
  comparison rejects integer 1 and floating 1.0 substituted for true; Python dictionary equality
  previously treated those values as equal. Two added negative cases pin this boundary.
- These three Bot evidence/manifest/readiness documents receive additive checkpoint notes.

Only these seven paths differ from recovery-observation-files.json. All other pending Bot files
and every SQL byte/deletion remain exact. No SQL schema, DAL shape or installation requirement
changed. The preceding recovery checkpoint and its 855/6 evidence remain retained separately.

### Readback contract

The evaluator reads the full index grid, the whole Sheet1 formula projection and the registered
Drive identity/ACL through the existing recorded adapter. It requires exactly one Sheet1 with
one row and three columns; the literal expected marker in A1; no other cell content, notes,
entered formatting, charts, tabs, names, developer metadata or data sources; no retained k98
properties/description; and exact private owner/editor sharing. An optional original sheet ID
must match. Computed string/formatted values must agree when present. Default computed formatting
does not replace the literal entered value. Invalid index/season/sheet identities fail before reads.

The result carries the observed full-manifest hash and sheet identity alongside the existing
setup fields. It never labels the marker-bearing index empty. The original index clear evidence
must remain a separate earlier observation; full trusted completion must bind that clear to the
same operation and sheet, establish every slot's private clear and exclude all delayed effects.
Successful current readback alone is not no-delayed-effects, writer termination or a ProofID.

The direct setup writer still dispatches its existing single marker update, then evaluates the
complete result. Contradiction stops completion and leaves reconciliation to the existing owning
caller. The read-only evaluator performs no mutation and can consume the same sealed transcript
through ClosedProbeReplay. Neither path introduces a recovery owner or an automatic operation retry.

### Validation and remaining gates

The 38 new focused cases passed; the affected 16-file suite then passed **893 tests / six gated
checks skipped** with S11 SQL authorization disabled. The subsequent JSON-type comparison fix
passed the complete affected recovery file (**63 tests**, including both new type-confusion cases).
The 16-file suite predates that final narrow fix; it was not rerun after the affected recovery file
passed. Ruff and Black format/AST/stability checks passed for all four Python files. Architecture
checked 29 pending Python paths; deferred validation
checked 55 Markdown paths; security routing reported zero errors/warnings. Import-only smoke and
registration checks passed (36 top-level commands, no drift). Both repository whitespace checks
passed. select_tests still recommends full pytest after composition. Separate exact Bot and SQL
Changes reviews with Deep off remain required on the settled patch.

The first two type-confusion fixtures changed the journal flags and hit the existing strict
Boolean journal gate before the intended SQL-body comparison. The tests were corrected to alter
the protected proof row instead, exercising the new comparison directly; production logic did
not change for that correction. The 61 existing recovery cases passed on that initial run, and
the full recovery file was rerun. Both logs are retained.

| Evidence layer | Established here | Still unproven / pending |
|---|---|---|
| Source/offline | Full final-index evaluation, typed requests, sealed replay and failure behavior | Full completed-composition regression and exact security review |
| SQL/static | No SQL delta; prior source/static assertions retained | Actual installation, permissions and concurrent transaction/CAS evidence |
| Provider/OS | Fake readbacks and lost-response handling only | Actual provider semantics/finality and Windows containment |
| Deployment/G4/G5 | Closed factories and preserved pending evidence | Complete writer exclusion, authorized exact operations and operator acceptance |

Remaining real implementation is trusted ProofID issue orchestration and writer/deployment
coverage, complete rollover drain/completion producers, actual-caller/shared-writer composition,
immutable account/registration/storage bindings and remaining readiness gates. The final-index
readback is one required part of completion, not the full completion producer. Runtime factories
remain closed. Existing local approval persists; no further local implementation approval is needed.

Fresh rollover-setup artifacts verify all 59 inherited documentation identities, both exact S10E
filename/previous_filename pairs with base-content and absent-at-base proof, unchanged anchors,
empty indexes and the exact seven-path continuation. Every pending Bot document stays in the next
genuine authorized Bot implementation PR; SQL implementation and its closeout documents remain
separate. No Git publication or regrouping occurred. Preserve S6 open gates, both uncertain
publications and retained data; S8A, S8B and S8C evidence remain distinct. No predecessor operational
rerun, SQL/provider/Discord operation, real import/export, process containment test, bot-machine
action, deployment or activation occurred. G4/G5 remain operator-owned. Rollback remains
non-installation now; later close admission, drain owned delivery or retain uncertainty, and
preserve append-only journals and exact receipt bytes without blind retries.


## S11 interrupted-retirement observation checkpoint — 2026-09-24

Existing local implementation approval continues. The fixed interrupted-retirement evidence path
now validates the exact recovery journal, reloads original retirement ProofIDs, observes the current
publication and every pending slot, and re-evaluates the complete sealed private transcript. It
returns an immutable observation only. No nested owner, ProofID, clear, retry, settlement or claim
release is created. Runtime factories remain closed and no live operation is authorized by this note.

### Exact source scope

- services/export_retirement_recovery_evidence.py: new journal validation, historical retirement
  proof comparison, read-only current-publication/slot evaluation, sealed replay and fixed probe.
- services/export_execution_dal.py: canonical-ID, parameterized read_proof SELECT with cursor and
  connection closure on success/failure, completed before any provider/private-evidence work.
- tests/test_export_retirement_recovery_evidence.py: 61 offline cases covering complete one/two-slot
  journals, original and interrupted nested ownership, current empty/nonempty observations,
  proof/journal tampering, stale owner/fence/version, sealed replay, closure loss and unresolved
  former nested writers. SQL and provider dependencies are fakes.

These three Python paths plus the three Bot release/evidence/manifest documents are the complete
continuation delta. All SQL pending files, including both closeout documents, remain byte-exact
against the ordinary-retirement checkpoint. No executable SQL or schema requirement was added.
Referenced fields and shapes were checked against authoritative ExportReconciliationProof,
ExportExecutionStream, SourceOutputDisposition, SourceOutputSlot and existing Bot DAL projections.

### Journal and historical-proof binding

The journal check reuses the existing hashed pending-retirement reconstruction, then requires the
complete unique pending disposition/slot projection. It checks the retained job/resource owner,
fence and versions, exact pool/source/season/choice, ordered disposition sequence, file/resource
identity, old/new epoch and recorded pool/slot version transitions. Current publication files
cannot be retired. Nested recovery must retain the exact current token and supported version;
a completed recovery cannot have unfinished retired slots. All snapshot bytes remain unchanged.

Each disposition's original retirement proof is reloaded from dbo.ExportReconciliationProof.
ProofID, account, kind/outcome, registration, original snapshot hash, session identity, exact stored
body association and membership hash/targets must match. The fingerprint includes the original
evidence bytes. Caller Boolean flags or a disposition hash cannot replace that protected SQL row.
Missing pre-S11/S10E ProofIDs remain unresolved and retained; no old journal is rewritten or given
a fabricated S11 proof. Original proof membership remains historical and is never substituted for
the fresh recovery catalogue. Protected deployment/SQL permission checks remain prerequisites.

The fixed probe checks historical records before opening, after closure and after sealed evaluation.
The full current snapshot and catalogue must also remain unchanged. A read-only stream preserves
the exact original/nested claim and uses the existing SQL admission predicates. An empty result
records only present private/empty readback. A nonempty or partially cleared slot remains unresolved
in the observation; it is not cleared, retried or labelled absence. The current receipt stays
byte-exact and both durable journals and retained legacy history stay intact.

Every previous relevant S11 stream is checked before probing, including earlier nested writers.
Unknown dispatched requests, unclosed/frozen streams, missing private evidence or uncertain child
termination prevent a result even when the current workbook appears empty. Neither this source
check nor successful readback proves complete pre-S11/external writer exclusion or provider
no-delayed-effects. Those remain necessary for the eventual trusted recovery ProofID producer.

### Validation and limits

The affected 16-file suite passed **855 tests / six gated checks skipped**, including all 61 new
recovery cases and the prior 15-file affected set. The initial four new historical-stream cases
used a non-closable list iterator instead of the real DAL's closable generator; the fixture was
corrected and the affected suite rerun. Both logs are retained. Production behavior did not change
for that fixture correction. S11 SQL authorization remained disabled throughout the run.

Ruff and Black formatting/AST-equivalence/stability checks passed on all three Python paths using
the repository 100-column/Python 3.11 settings. Architecture checked 29 pending Python paths;
deferred-document and security-routing validators passed (zero security-routing errors/warnings).
Guarded imports and command registration passed (36 top-level commands, no drift); both Git
whitespace checks passed. select_tests recommends full pytest; that remains a final gate after
composition, together with separate exact Bot/SQL Changes reviews with Deep off.

| Evidence layer | Established locally | Still requires later approval/evidence |
|---|---|---|
| Python/source and fixed SELECT | Journal/proof/receipt identity checks and fail-closed fake boundaries | Real installed metadata and effective SQL permissions |
| SQL transaction/CAS | Existing authoritative source and unchanged source/static history retained | Real concurrent ownership, catalogue and consuming-CAS cases |
| Provider/child | Deterministic read-only transcripts, closure-loss/unknown-history rejection | Windows containment and actual provider outcome/finality behavior |
| Deployment and acceptance | Factories remain closed; exact pending evidence preserved | Full writer inventory/exclusion, target installation, G4 operations and operator G5 |

Remaining implementation: trusted ProofID issue orchestration with complete writer/deployment
coverage, fixed rollover drain/completion evidence, actual-caller/shared-writer composition,
immutable account/registration/storage bindings and remaining readiness gates. Recovery source
authoring is not a deployed recovery capability or permission to retry a historical clear.

Fresh recovery-observation artifacts verify all 59 inherited documentation identities, unchanged
anchors/empty indexes, exact S10E filename/previous_filename and merged/content/absent-at-base
proof, and only the six expected Bot paths changed. The settled complete Bot document union stays
with the next genuine authorized Bot implementation PR; pending SQL implementation/docs stay
separate. No standalone docs PR or Git publication occurred.

Preserve S6 open gates, both uncertain publications and all retained data; S8A six-script evidence,
S8B 50 cases/actual restore versus offline history, and S8C seven checks remain distinct. No
predecessor operational rerun, SQL/provider/Discord operation, real import/export, service launch,
bot-machine pull/restart/deployment or activation occurred. Local implementation needs no new
approval. Exact G4 operations and G5 remain operator-owned. Current rollback is non-installation;
later close admission, drain owned delivery or retain uncertainty, preserve append-only journals
and receipt bytes, and use reviewed forward SQL repair. No blind retry or evidence removal.


## S11 ordinary-retirement observation checkpoint — 2026-09-24

The existing local implementation approval continues. This continuation implements the fixed
read-only observation needed by ordinary retirement, including its distinct pool-snapshot binding.
It does not issue a ProofID, journal a retirement, clear a workbook, settle a job or release claims.
Configured runtime factories remain closed. No additional decision is needed for local edits/tests.

The new services/export_retirement_evidence.py selects the exact current publishing attempt and
superseded confirmed attempt from the complete registered pool context. It requires an explicit
unretained decision, complete manifest/part identities, disjoint generation files, exact account/
KVK/epoch/owner/fence, positive versions, active unowned old slots and valid assignment identities.
Final/unknown retention, quarantine, closing pools, mismatched receipts and changed ownership fail
closed. The same 9,000,000-cell part and 8-registration/16-slot bounds remain in force.

Readback reuses the fixed current-publication evaluator and additionally checks the old generation's
registered file order, explicit remote retention flag, pinned content, directory and retained URL.
The old receipt must remain byte-exact. A not-yet-settled current receipt may be observed, but this
does not write it to SQL. Retained legacy receipts remain in the hashed snapshot without changes.
No observation is labelled no_live_references or writer_terminated: external references, pre-S11
writers, deployment exclusion and remote finality still require the independent trusted producer.

NewSourceJobStreams.retirement_probe rereads the complete operator snapshot and retains the exact
current claim/resource versions while binding SnapshotHash to the pool context used by
SourceOutputPoolDAL.retire_generation. The normal publication probe's wider snapshot is not
substituted. Nested recovery owners and changed contexts cannot acquire this ordinary-retirement
probe. Existing SQL admission and pre-dispatch checks remain independent of this source check.

RetirementProbe compares the owned context before admission, after stream closure and after sealed
evaluation. It verifies the closed stream catalogue around the fresh read, then replays every
private response through the same evaluator. Missing/extra reads, changed snapshot/history,
unavailable private bytes and lost closure acknowledgments produce no result. There is no retry.
This does not replace the eventual account-locked SQL proof-issue and consuming-CAS checks.

### Exact continuation files and validation

Five Bot Python paths changed:

- services/export_retirement_evidence.py: new fixed evaluator, sealed replay and probe orchestration.
- services/export_runtime_composition.py: pool-context-bound ordinary-retirement probe scope.
- kvk/services/new_source_export_service.py: recorded read-only old-generation content/retention check.
- tests/test_export_retirement_evidence.py: 59 offline positive, negative and ownership/sealing cases.
- tests/test_export_reconciliation_service.py: existing private transcript fixture accepts both exact
  domain snapshot shapes; no production proof assertion is supplied by the fixture.

The three Bot release/evidence/manifest documents receive additive checkpoint notes. No SQL file,
including either pending SQL closeout document, changed in this continuation. ExportAttempt,
SourceOutputSlot and proof-issue/source-consumption fields were checked against authoritative SQL.
The earlier SQL 125-assertion/11-input static evidence remains unchanged historical authoring proof.

The explicit 15-file affected suite passed **794 tests / six gated checks skipped**. It includes
execution authority/host/protocol/launcher, reconciliation/composition/retirement, provider adapter,
coordination, legacy snapshot, new-source delivery/exports and rollover/operator coverage. An
initial run had one new assertion expecting the inner rejection rather than the existing adapter's
ProviderOutcomeUnknown wrapper. The assertion now verifies both wrapper and SourceConflict cause;
the complete affected rerun passed. Both logs are retained. No live SQL gate was enabled.

Ruff passed for all five paths. Black's CLI temporary/cache path stalled; only the owned formatter
processes were interrupted. Black's formatter, AST-equivalence and stability APIs then checked all
five paths successfully using repository Python 3.11/100-column settings, without CLI cache writes.
Guarded import smoke, architecture (27 pending Python paths), deferred-document validation,
security-routing (zero errors/warnings), command registration (36 top-level/no drift) and both Git
whitespace checks passed. select_tests recommends the full suite; it remains a final gate after
composition, alongside separate exact Bot/SQL Changes security reviews with Deep off.

### Remaining implementation and operational boundary

Trusted ProofID issuance still needs complete writer/deployment coverage and outcome authority.
Interrupted-retirement recovery and rollover need their fixed evidence producers; complete actual
caller/shared-writer composition, immutable registration/account/storage bindings and remaining
readiness checks are still outstanding. These are real implementation gaps. SQL installation,
transaction/permission semantics, Windows containment and provider/Discord behavior are separately
unproven operational properties. This source checkpoint is not release acceptance.

All 59 inherited documentation identities, exact S10E filename/previous_filename archive pairs,
base-content and absent-at-base proof, comparison anchors and empty indexes are rechecked in
retirement-observation-*.json. The mandatory Bot document union, this S11 pack/starter and S10D/E
closeouts stay with the next genuine authorized Bot implementation PR; SQL's pending work stays
separate. No standalone docs PR, Git publication, predecessor operational rerun, provider/SQL/
Discord action, containment launch, bot-machine pull/restart/deployment or activation occurred.

Preserve both uncertain publications, all retained data, S6 open gates and distinct S8A/S8B/S8C
evidence. Rollback remains non-installation now. Later rollback closes admission, drains owned
delivery or retains uncertain claims, preserves journals/receipts and uses reviewed forward SQL
repair. Exact G4 execution and G5 acceptance remain operator-owned.


## S11 foundation SQL startup-contract checkpoint — 2026-09-24

The existing local implementation approval continues to cover source authoring and offline tests.
No new operator decision is needed for this work. The authority launcher now requires a protected
sql_contract manifest section and verifies actual installation observations before creating its
session, evidence store or provider host. The Bot's configured runtime factories remain closed.

The DAL's explicit, read-only installation_snapshot collects the canonical server/database/
collation/principal; S10A/C/D/E/S11 migration IDs, Applied status and checksums; and metadata for
28 required coordination/evidence/dependency objects. Metadata includes table/procedure type,
procedure text/options/execution context, columns/types/defaults/computed/identity attributes,
indexes/ordered columns/filters, checks, foreign-key mappings/actions/trust and triggers. It uses
fixed parameterized SELECT batches and closes its cursor/connection on success and failure.
No IDs, SQL text or expected hashes can be supplied over the Bot IPC boundary.

The comparator checks the complete approved migration set and exact metadata fingerprint, and
independently rejects missing/opaque modules, unsupported table/procedure shapes, invisible
metadata, disabled/untrusted constraints and disabled/hypothetical indexes. Target identity and
restricted authority/reader profile must match; sysadmin, db_owner, CONTROL DATABASE, role/user
alteration and impersonation are rejected. Effective HAS_PERMS_BY_NAME observations must show
SELECT-only direct access to the five evidence tables and procedure EXECUTE only for the authority
profile, with ALTER/CONTROL/TAKE OWNERSHIP denied. Missing/unknown/duplicate permission records
cannot be replaced by a role-membership assertion.

Expected fingerprints are protected, independently reviewed deployment inputs. Startup never
learns its expected hashes from the observation it is checking. Preparing an exact target contract
requires approved G4 inspection and authoritative metadata comparison; no current database,
principal, applied checksum, metadata fingerprint or deployment manifest was fabricated here.
The source-file inventory is not the installed-metadata fingerprint. Snapshot metadata reads and
their semantic/type/visibility/concurrency behavior still require G4 execution. DDL exclusion and
deployment sequencing remain operational requirements, not a lock implied by these SELECTs.

### Exact files and validation

Bot changes in this continuation:

- services/export_execution_dal.py: fixed required migration/object/permission sets and explicit
  bounded installation observation; all SQL stays in the DAL.
- services/export_runtime_composition.py: pre-connection contract shape validation and exact
  installation/identity/effective-evidence-permission comparison; returns an observation hash,
  not a runtime factory, ProofID or release approval.
- scripts/run_export_authority.py: require the protected SQL contract and check it before session,
  private-store or provider-host creation; no fallback for a missing contract.
- tests/test_export_runtime_composition.py and tests/test_export_authority_launcher.py: wrong
  target/principal, missing/changed migrations, definition drift, unsafe metadata, role-versus-
  effective-permission differences, closure on failure and startup-before-session ordering.

No SQL repository executable source changed in this continuation. Both pending SQL closeout
documents receive this source-alignment note separately; the existing S11 SQL delta remains pending.
The required 28 object paths and five migration paths were verified against authoritative source.
Nine emitted fixed SQL SELECT batches were captured through a fake connection and parsed by
ScriptDom; none was sent to SQL Server. The prior S11 125-assertion/11-input SQL source evidence
remains historical and unchanged, not a new execution result.

Affected offline suite: **747 passed / six gated checks skipped** across 15 files. Ruff/Black
passed for the five changed Python paths; guarded smoke imports passed. Architecture/deferred/
security-routing and command-registration checks are retained with the final checkpoint inventory.
The full suite and separate Bot/SQL Changes security reviews (Deep off) remain final gates once
composition is complete. This is not a merge-ready or deployment-ready result.

### Remaining work and approval boundary

This closes the foundation SQL contract-comparison/startup-ordering implementation gap, not all
readiness. Remaining real implementation includes trusted ProofID producers for every settlement
kind, complete actual-caller/shared-writer composition, immutable account/file/registration/spool
bindings and the remaining application permissions and deployment/writer-coverage gates. Existing
catalogue/sealed-publication observations do not prove pre-S11 or external-writer finality. All
unsupported or uncertain outcomes retain their claims and data.

Local source/test work remains authorized without another approval request. Exact Git publication,
SQL installation/transaction/permission/provider/Discord/Windows-containment operations and
bot-machine deployment remain separately operator-approved G4 steps; G5 acceptance remains
operator-owned. No such operation occurred. Preserve S6 open gates, both uncertain publications,
all retained data and the distinct S8A six scripts, S8B 50 cases/actual restore versus offline
history, and S8C seven local checks. No predecessor operational fixture was rerun.

The settled Bot document union, S11 pack/starter, S10D/E closeouts and both S10E move sides remain
pending for the next genuine authorized Bot implementation PR. SQL docs remain separate. Fresh
installation-readiness-*.json evidence records every pending path, all 59 inherited identities,
unchanged comparison anchors/empty indexes and exact archive filename/previous_filename plus
base-content/absent-at-base proof. Rollback remains non-installation now; later it closes admission,
drains owned delivery or retains uncertainty, preserves byte-exact receipts/journals and uses
reviewed forward SQL repair. No blind retry, old-writer restart or evidence removal is authorized.


## S11 sealed publication observation checkpoint — 2026-09-24

Continued under the existing local implementation approval. The fixed confirmed-publication
evaluator now reuses the actual content/ACL/directory/pointer readback, binds the immutable SQL
attempt manifest and exact parts/owner/fence/epoch/registration, and reconstructs the coordinated
receipt. An existing receipt must match byte for byte. A mismatch remains unresolved; this path
never classifies a failed read as absence or damage.

PublicationProbe now performs the complete local source sequence: read the exact job snapshot;
verify the recorded historical catalogue; admit a read-only stream; run the fixed evaluator;
close the exact stream once; recheck the snapshot; bind the closed probe to the catalogue; replay
the entire readback from sealed private request/response bytes; and recheck the snapshot again.
Lost closure acknowledgment, unclosed historical writers, changed snapshots/catalogues, corrupt
private evidence and incomplete transcript consumption return no observation. It never retries,
settles, releases a claim or issues ProofID. SQL must still independently enumerate the catalogue
under its account lock at proof issuance and at the eventual consuming settlement.

Tracing interrupted retirement also found an exact version transition: interruption increments
the job version once while retaining the owned nested recovery journal version. Read-only probe
admission and pre-dispatch SQL now accept that exact one-version difference only for an uncertain
job. Mutation admission still requires the current nested version. The Python scope also binds
completed historical journals without reviving their mutation token. No lease, arbitrary older
version, new owner or resource takeover is introduced.

### Exact source files in this continuation

Bot:

- kvk/services/new_source_export_service.py: share the existing publication readback and add a
  recorded, pinned, read-only coordinated-publication entry; legacy receipt behavior is preserved.
- services/export_coordination_dal.py: share immutable attempt/part validation between SQL reads
  and the observation evaluator, accepting SQL binary hashes or the canonical wire hex form.
- services/export_reconciliation_service.py: fixed fresh/sealed publication evaluators and the
  owned probe sequence; returned immutable observations explicitly carry no finality or ProofID.
- services/export_runtime_composition.py: exact retained-owner probe scope and snapshot recheck;
  the interrupted nested-owner exception is observational only.
- tests/test_export_reconciliation_service.py and tests/test_export_runtime_composition.py:
  actual offline SDK readback/sealed replay, receipt bytes, tamper/failure paths, nested version
  transition and rejection of mutation revival or mixed composition.

Separate SQL source:

- migrations/20260924_001_export_execution_evidence.sql
- sql_schema/dbo.usp_ExportExecutionStreamTransition.StoredProcedure.sql
- sql_schema/dbo.usp_ExportProviderRequestEventAppend.StoredProcedure.sql
- deploy/Test-ExportExecutionEvidenceContracts.ps1

The migration and its two object snapshots repeat the exact probe-only version predicate at
admission and dispatch. Merged S10 predecessors are unchanged. This S11 migration is still
uninstalled; incompatible installed S11 definitions require separately reviewed forward repair.
These paths supplement the full pending union; they are not a replacement PR manifest.

### Fresh validation and remaining boundaries

| Category | Evidence from this continuation | Still required |
|---|---|---|
| Bot offline | 689 passed / six opt-in checks skipped across the affected 15-file suite; six-path Ruff/Black pass; guarded imports pass | Completed issuer/readiness/caller composition, then final full regression and separate review |
| SQL static | 125 contract assertions; 11 ScriptDom source inputs; 18 weakened source variants rejected (4 interrupted-owner, 8 catalogue, 6 closing-probe) | Installation, effective roles, SQL/Python hash parity, exact CAS/transaction/concurrency and lock-cost behavior |
| Provider/containment | In-memory provider and private-journal fixtures; no real request or Windows child launch | Exact G4 targets, child containment/termination, no-delayed-effects evidence and fresh real readback |
| Deployment/acceptance | Configured production factories remain closed; no state changed | Immutable readiness and all-writer inclusion/exclusion, approved deployment order and operator G5 |

Architecture validation passed for 25 pending Python paths, deferred validation for 55 Markdown
paths, security routing with zero errors/warnings, and static registration with 36 top-level
commands/no drift. The selector recommends full pytest; that final gate remains pending completed
composition. Bot and SQL each require their own settled Changes security target with Deep off.
No security scan or merge-readiness result is claimed here.

Real implementation still required: trusted ProofID production (including ordinary retirement,
interrupted recovery and rollover outcomes), immutable deployment/readiness checks and complete
actual-caller/shared-writer composition. The sealed publication observation is one completed
prerequisite, not pre-S11/external-writer coverage or no-delayed-effects authority. Unsupported
absence, damage and partial-rollover outcomes stay closed rather than being inferred.

Local implementation approval persists; no additional approval is requested for those remaining
local edits/tests. Git publication and exact G4 SQL/provider/Discord/containment/deployment
operations still require the operator's separate, concrete approval; G5 remains operator-owned.
Rollback now is non-installation and preservation of source/evidence. Later rollback closes
admission, drains owned work or retains uncertain claims, preserves journals and receipt bytes,
and forward-fixes installed SQL. It cannot restart old writers, delete evidence or blindly retry.

All inherited document bodies, S6 open gates, both uncertain publications and retained data stay
preserved. S8A six scripts, S8B 50 cases/actual restore versus offline history and S8C seven local
checks remain distinct. No predecessor operational fixture was rerun. All pending Bot documents,
S11 pack/starter, S10D/E closeouts and both exact S10E archive move sides remain the settled next
genuine Bot implementation-PR union. SQL closeout documents stay separately grouped. Fresh
publication-observation-*.json artifacts record per-path hashes, exact filename/previous_filename
base-content/absent-at-base archive proof and unchanged comparison anchors with empty indexes.


## S11 complete recorded-catalogue checkpoint — 2026-09-24

Continued under the existing local implementation approval. A matching domain snapshot and no
active stream did not detect a writer which opened and closed after a probe. Membership v2 now
binds the complete recorded S11 stream catalogue for every registered pool file, including shared
writers, prior probes, prior registrations and former nested owners. The trusted verifier reads
all matching closed streams and verifies each private request/response/child-closure journal.
Unknown outcomes, missing records or altered private bytes remain unresolved.

A count and chained SHA-256 fingerprint bind every stream UUID, version and sealed event digest;
retained history is not truncated to fit the 65,536-byte membership receipt. Python and authored
SQL use lowercase UUID text in binary lexical order and the same ASCII/binary framing. SQL proof
issuance independently enumerates that catalogue under the account lock. Consumption repeats it
inside the owning settlement transaction after exact domain-snapshot comparison, catching even
a new already-closed stream. A fixed Python hash vector and source inspection establish static
alignment; cross-engine/hash and transaction behavior still require G4 SQL execution.

The absence guard examines every stream of the exact publication job, including nested owners
and streams outside its current file set. Any dispatched mutation blocks absence. Older successful
jobs remain covered by the complete catalogue without being mistaken for this job's dispatches.
The private verifier still rejects unknown historical outcomes. No receipt or disposition changes.

Catalogue and request enumeration use bounded keyset pages and close SQL before private-file I/O.
ClosedProbeReplay lets the actual static SDK request builder and readback helpers evaluate only
the next exact successful response in a sealed probe. It rejects mutations, changed files/methods/
projections/streams, unused observations and swallowed read failures. Response bytes are hash
checked again at consumption. This bridge performs no provider call or SQL mutation, produces no
ProofID, and does not make a historical observation fresh.

### Exact continuation paths

Bot source/tests: services/export_execution_protocol.py; services/export_execution_dal.py;
services/export_reconciliation_service.py; tests/test_export_execution_protocol.py;
tests/test_export_reconciliation_service.py. Bot checkpoint docs: this log,
integration_implementation_manifests.md and release_readiness_and_rollback.md.

Separate SQL source: migrations/20260924_001_export_execution_evidence.sql;
sql_schema/dbo.usp_ExportReconciliationProofIssue.StoredProcedure.sql;
deploy/Test-ExportExecutionEvidenceContracts.ps1. SQL checkpoint docs: docs/SQL_DELIVERY_LOG.md
and migrations/README.md. No predecessor script is edited or executed. These changes revise only
uninstalled S11 authoring; an incompatible installed S11 definition is refused for forward repair.

### Validation and remaining work

| Layer | Fresh result | Outstanding evidence / work |
|---|---|---|
| Bot offline | 653 passed, six opt-in cases skipped; scope/race/private-byte/sequence checks and actual SDK descriptor through sealed replay | Complete fixed outcome evaluators and trusted ProofID orchestration; pre-S11/external-writer coverage cannot be inferred from this catalogue |
| SQL static | 121 contract assertions; 11 ScriptDom inputs; eight weakened catalogue variants plus six closing-probe variants rejected | Installation, effective roles, cross-engine hash vector, post-probe concurrency and real transaction isolation remain unexecuted |
| Repository checks | Ruff/Black on five changed Python paths; architecture/deferred/routing/command registration passed; guarded import smoke passed | Final full suite and separate exact Bot/SQL Changes reviews, Deep off, remain for the settled implementation |
| Deployment | No operational state changed; configured production factories remain closed | Immutable readiness, complete actual-caller/provisioning bindings, all-writer inventory/exclusion, exact G4 operations and operator G5 |

The selector recommends the full suite because tests changed. This continuation runs the affected
15-file suite; final broad validation waits for completed composition. No live opt-in is enabled.
The first parallel Black invocation stalled after formatting and was interrupted; single-worker
Black completed. Two initial fixture failures from omitted slot State fields were corrected and
the focused and affected suites passed. No runtime contract was weakened to satisfy a test.

Full catalogue enumeration under account/row locks has an unmeasured history-size/lock-duration
cost. Measure it on the approved G4 target; do not introduce a retention cutoff or claim a latency
bound from static checks. A complete S11 ledger does not prove pre-S11 closure, excluded external
writers, no delayed effects from unknown requests, or method-specific current provider truth.
Those are explicit remaining producer/readiness requirements, not successful runtime evidence.

Preserve S6 open gates, both uncertain publications and all retained data. S8A six scripts, S8B
50 cases/actual restore versus offline history and S8C seven checks remain distinct. No SQL,
provider, Discord, import/export, bot-machine, activation, publication or predecessor operation
occurred. Rollback remains non-installation and retained claims/evidence, never blind retry.
All pending Bot documents, this pack/starter, S10D/E closeouts and both S10E archive sides remain
one next genuine Bot implementation-PR union; SQL closeout docs remain separate. Fresh per-path
preservation/hashes are in catalogue-*.json alongside the retained archive identity proof.


## S11 adapter and retirement lifecycle checkpoint — 2026-09-24

Continued under the existing local implementation approval. Actual new-source export helpers
now cross the typed boundary for ordered values.batchGet readback (1–16 explicit rectangles,
50,000 cells maximum, exact response membership/shape). The authority's child routes that
operation to the fixed Google endpoint without retries. Rollover's exact named-range and
metadata-ID deletion requests are admitted and their replies checked; broad metadata filters
remain refused. Empty appProperties is accepted for the real description-only clear case.
The separate uninstalled SQL request-kind constraint now includes this read operation.

Delivery now owns its authority context and closes it before retirement verification or final
confirmation. Ordinary retirement and explicit nested recovery use distinct streams per slot;
private clear/readback completes, then child closure returns, then the existing slot CAS records
reusable capacity. Lost closure/provider/SQL acknowledgments stop further work. The pool DAL
checks that no authority stream remains active inside the existing owner transaction before
freeing a slot or completing the nested recovery owner. The existing operator service then
obtains a fresh publication snapshot/probe; no old proof is relabelled. Evidence-mode mismatch
between participating DALs is rejected. Disabled predecessor behavior remains available only
outside the selected S11 evidence mode.

NewSourceJobStreams binds freshly read current owner/fence/version, complete resource membership,
registration/epoch and exact hashed retirement journal. Recovery retains its exact nested token;
it cannot replay delivery. Attempted delivery also cannot be reopened by this factory. These are
explicitly injected components, not a production runtime activation or a complete proof producer.

### Exact continuation paths

Bot executable/test changes: services/export_execution_protocol.py;
scripts/run_export_provider_child.py; services/export_runtime_composition.py;
kvk/services/new_source_delivery_service.py; kvk/services/source_output_pool_service.py;
kvk/dal/source_output_pool_dal.py; tests/test_export_execution_protocol.py;
tests/test_export_execution_host.py; tests/test_export_runtime_composition.py.
Bot checkpoint docs: this log, integration_implementation_manifests.md and
release_readiness_and_rollback.md. No other inherited document is removed or regrouped.

Separate SQL source changes: migrations/20260924_001_export_execution_evidence.sql;
sql_schema/dbo.ExportProviderRequest.Table.sql; deploy/Test-ExportExecutionEvidenceContracts.ps1.
SQL checkpoint docs remain docs/SQL_DELIVERY_LOG.md and migrations/README.md. Merged predecessor
migrations are unchanged. SQL evidence sources are authored and uninstalled.

### Validation and proof boundaries

| Layer | Fresh evidence | Still unproven / not executed |
|---|---|---|
| Bot offline | 611 passed, six opt-in cases skipped; actual SDK request descriptions exercised against the typed boundary and an in-memory provider fake; separate close/reuse/failure ordering cases | Real provider behavior, authority Windows process/pipe containment and restart |
| SQL static | 108 source assertions; 11 ScriptDom inputs parsed; six weakened source variants rejected | Installation, effective permissions, transactions and concurrency on a database |
| Repository checks | Ruff/Black on nine changed Python paths; architecture on 25 pending Python paths; deferred and routing validators; 36 top-level commands, no drift; guarded import smoke | Final full-suite gate and separate exact Bot/SQL Changes reviews, Deep off, for the settled implementation |
| Deployment / acceptance | No live state changed; all admission remains disabled | Exact G4 operations and G5 acceptance remain operator-owned |

The import harness denied SQL, external socket connections and all subprocess starts. Its first
attempt also stopped Python's optional OS-version shell probe; returning the probe's OSError
fallback fixed the harness while keeping that subprocess forbidden. It permits only the standard
library's internal loopback socketpair setup. No provider child or launcher was run.

The prior retirement stream-ordering gap is addressed at the injected service/DAL boundaries.
Remaining real implementation includes complete trusted historical request coverage, fresh
method-specific readback and ProofID issuance, immutable deployment readiness, and full actual
caller/transport composition. Production configured factories remain closed. Mocked lifecycle
and source checks do not establish historical finality, installed SQL or provider truth. Retained
S6 open gates and both uncertain publications remain untouched; S8A six scripts, S8B 50 cases and
actual restore versus offline history, and S8C seven local checks remain distinct.

No SQL/provider/Discord execution, real import/export, bot-machine action, activation, Git
publication or predecessor rerun occurred. Rollback remains non-installation and preservation;
uncertainty retains claims and requires explicit reconciliation, never blind retry. Every pending
Bot document, S11 pack/starter, S10D/E closeouts and both S10E archive-move sides remain in the
future genuine Bot implementation PR; pending SQL closeouts stay with the separate genuine SQL
implementation PR. Filename-level preservation and hashes are in adapter-retirement-*.json in the
local S11 implementation artifact directory. No standalone documentation PR is introduced.


## S11 closing-probe binding checkpoint — 2026-09-24

Continued under the existing local implementation approval. The uninstalled SQL evidence
contract now preserves the closing operation's actual null OwnerID and zero Fence for a
read-only probe. Only operation/probe scopes may use that identity. Both stream admission and
request pre-dispatch repeat account/resource membership and version checks, then the closing
pool reservation, registration hash, epoch and exact closing/draining operation CAS. Resources
must be unowned; no worker owner is fabricated, claim released, fair ticket advanced or mutation
admitted. The pool lock follows sorted resource locks and precedes operation/stream checks.

Bot's OutputOperationStreams binds the current operation snapshot to either the existing
rollover phase factory or a read-only closing probe. It rejects changed claims, membership,
registration, phase or epoch before IPC; SQL remains authoritative at admission and dispatch.
The closing probe hashes the exact drain snapshot consumed by readiness. Legacy export and
configuration callers now use the real AuthorityStream.execute interface and close the stream
before confirmation/release. These helpers remain explicitly composed; production factories
are still closed. The probe is not a trusted historical-coverage or finality certificate.

Validation: **344 passed, six skipped** in the affected offline suite. The six opt-in SQL/Windows
cases were not executed. SQL static checker: **107 assertions**; **11 ScriptDom parse inputs**;
**six weakened source variants rejected**. Ruff/Black and architecture/deferred/security-routing
validators passed. The selector recommends full pytest for changed tests; final full-suite,
smoke/registration and separate exact Bot/SQL Changes security reviews (Deep off) remain for the
settled implementation, rather than treating this incomplete checkpoint as a PR handoff.

Exact Bot executable/test changes in this continuation: services/export_runtime_composition.py,
scripts/run_export_authority.py, services/export_provider_adapter.py,
services/legacy_export_snapshot_service.py, tests/test_export_runtime_composition.py,
tests/test_export_authority_launcher.py, tests/test_export_execution_sql_integration.py and
tests/test_export_provider_adapter.py. Exact separate SQL changes:
migrations/20260924_001_export_execution_evidence.sql,
sql_schema/dbo.ExportExecutionStream.Table.sql,
sql_schema/dbo.usp_ExportExecutionStreamTransition.StoredProcedure.sql,
sql_schema/dbo.usp_ExportProviderRequestEventAppend.StoredProcedure.sql and
deploy/Test-ExportExecutionEvidenceContracts.ps1. These are uninstalled S11 sources, not changes
to merged predecessor migrations. The guarded SQL test accepts an optional exact synthetic
closing_probe_scope in its separately approved disposable-target packet; it never runs by default.

The prior closing-operation scope blocker below is superseded by this source change. Remaining
implementation includes complete trusted historical coverage and method-specific readback/proof
issuance, ordinary retirement/recovery stream composition, immutable deployment readiness and all
actual callers. Installed schema/effective permissions, Windows containment and real provider
behavior remain unproven. No SQL/provider/Discord execution, real import/export, bot-machine
operation, activation, Git publication or predecessor fixture rerun occurred. All pending Bot
documents and archive identities stay grouped with its genuine implementation PR; SQL closeouts
stay with SQL. G4 and G5 remain operator-owned.


## S11 local composition and rollover checkpoint — 2026-09-24

Under the existing local implementation approval, Bot source now has an explicit independent
authority launcher and authenticated typed Bot client. The S11 rollover worker opens a fresh
authority stream for each pending private, clear and setup phase, binds the recorded transport
to that exact stream, and closes the stream before advancing the SQL phase version. A missing
stream factory or mismatched transport fails closed and retains the operation. The disabled
legacy path is unchanged. This is source authoring, not service installation or provider proof.

Focused offline validation after the phase change: 245 passed; Ruff, Black check and architecture
validation passed. No live SQL/provider/Discord operation, real import/export, bot-machine action,
Git publication or predecessor rerun occurred. The standalone launcher/client have not been
provisioned or exercised against the target Windows/SQL/provider environment.
An additional mismatched-transport negative path passed in the 91-case rollover suite after
that broader run; no provider call occurred and the operation remained owned/uncertain.

Release remains blocked on complete trusted historical coverage, fresh method-specific provider
readback and no-delayed-effects proof issuance. The authored SQL stream procedure also lacks a
closing-operation observational probe for rollover drain; its ordinary operation scope requires
an owned running claim while drain is unowned and closing. Retirement recovery and all production
factories/callers still require exact composition and live G4 evidence. No readiness, activation or
G5 acceptance is inferred. Retained S6/S8 records and both uncertain publications remain intact.


## S11 continuation: trusted proof consumption — 2026-09-24

Continued under the existing implementation approval. Six settlement transitions now resolve
ProofID from SQL inside the existing account/resource/snapshot transaction when S11 evidence is
selected: publication reconciliation, damage repair, retirement intent, retirement recovery,
rollover completion and rollover drain readiness. Caller preview fields are replaced with the
stored immutable evidence body; account, snapshot, registration and proof kind must match, and
an active authority stream blocks settlement. Audit records retain the actual ProofID/body.
Retirement/recovery reject mismatched evidence settings between the collaborating DALs.
Resource locks use sorted keys; no new transaction spans provider or filesystem I/O.

The new private-journal verifier checks exact closed-stream identity, closure reference/hash,
child termination evidence, final sequence/digest, each immutable request/payload and every
terminal event/response. Missing/unknown events, changed bytes, wrong child identity and empty
observational probes fail closed. It returns only verified journal facts: it does not issue
ProofIDs, establish complete historical coverage, perform fresh provider probes, or release claims.
No pre-S11/S6 history is reconstructed.

The separate uninstalled SQL source now constrains outcomes by proof kind: publication allows
confirmed/absent/damaged; retirement, recovery and drain allow confirmed; rollover completion
requires completed. Proof issuance also checks body/outcome/snapshot agreement and requires a
successful read in the matching probe stream. These authoring checks do not establish provider truth.

Fresh validation: **379 passed, five skipped**, including 28 new proof-consumption/private-journal
cases and the existing affected regressions. Ruff passed on the five changed Python files;
architecture validation passed on the four implementation files. The SQL offline checker passed
87 assertions and ScriptDom parsed all 11 SQL source files. No live opt-in tests were executed.

Exact Bot code delta for this continuation: modify services/export_execution_dal.py,
services/export_coordination_dal.py and kvk/dal/source_output_pool_dal.py; create
services/export_reconciliation_service.py and tests/test_export_reconciliation_service.py.
Exact SQL executable delta: migrations/20260924_001_export_execution_evidence.sql,
sql_schema/dbo.ExportReconciliationProof.Table.sql and
sql_schema/dbo.usp_ExportReconciliationProofIssue.StoredProcedure.sql. SQL closeouts stay separate.

**Still incomplete and disabled:** the standalone authority launcher, complete trusted proof issuer
with historical coverage and exact fresh method-specific readback, immutable readiness checks,
all caller/context bindings and runtime composition. The newly added verifier is only one part
of that issuer. Separate stable Bot/SQL Changes security reviews with Deep off remain pending.
No SQL/provider/Discord execution, bot-machine action, activation, Git publication or predecessor
rerun occurred. Existing G4/G5 boundaries, retained uncertainties, rollback rules and full pending
57-identity Bot documentation grouping remain unchanged.


## S11 approved implementation checkpoint — 2026-09-24

The operator approved the expanded implementation proposal after the trusted-proof mechanism
review. Local Bot and separate SQL source authoring has begun. This supersedes the earlier
statement that the current executable edit manifest is empty; the earlier dated design records
below remain historical. **Implementation is incomplete and activation remains closed.**

Implemented foundations: typed bounded provider requests; an injected independent authority
with prepare/dispatch/result journaling; full SQL batch acknowledgment before dispatch; encrypted
private evidence storage; suspended Windows child/Job Object and authenticated local pipe helpers;
an explicit child runner; additive SQL evidence objects and disabled transaction fixtures; optional
account stream gates in the three existing DALs; and an optional recorded SDK bridge that refuses
local execution fallback. Shutdown closes new admission while allowing already owned delivery to
drain. Authority uncertainty uses the worker's existing retain-claims exception contract.

The production authority launcher, immutable manifest/identity readiness, complete trusted proof
producer, same-transaction ProofID settlement integration, all caller/context bindings and closed
runtime composition are still missing. These are real implementation gaps, not merely unproven
runtime behavior. Existing factories remain closed; no production caller selects these foundations.
Rollover drain's unowned closing operation, retirement's current-versus-old owner binding,
provisioning/create identity, complete historical request membership and method-specific verified
readback require completion before activation. No caller-built proof flags become trusted here.

### Fresh validation and limits

- Focused offline regression run: **351 passed, five skipped**, covering authority/protocol/host,
  disabled SQL tests, provider adapter, coordination, legacy snapshots, rollover, operator,
  gsheet module and new-source export service. The skips are Windows/SQL opt-in execution.
- Ruff passed on the 14 changed/new Python implementation and test files. Architecture validation
  passed on the nine implementation files. Static command registration passed (36 top-level
  commands, no drift). Import smoke passed with SQL/external connections blocked. The first
  harness also blocked Windows internal socketpair setup; the corrected harness permits only
  that exact standard-library socketpair caller on loopback. Deferred validation passed for
  55 Markdown files; security-routing validation passed with zero errors/warnings. Both
  repositories passed git diff --check.
- Separate SQL source checker: **87 assertions passed**. SQL Server ScriptDom parsed all **11 SQL
  files** (migration, nine object snapshots, guarded fixture). These are source-level checks only.
- No SQL connection/install/transaction fixture, Windows child launch, provider/Discord call,
  import/export, activation, deployment, bot-machine pull/restart, predecessor rerun or Git
  publication occurred. Security review remains pending on stable, separate Bot and SQL Changes
  targets with Deep off; this is not a security-cleared or merge-ready patch.

The entry preservation archive and exact per-path manifest are retained at
`C:/Users/cwatt/.codex/visualizations/2026/09/24/01a0d231-08d0-7610-a83f-9d9d907c2b0d/s11-implementation/`
as `entry-documents.zip` and `entry-manifest.json`. This does not restore missing historical
archives or prove GitHub rename metadata. Preserve every pending Bot path including both S10E
archive move sides for the genuine implementation PR; SQL closeouts remain separately grouped.
All retained S6 gates/data/uncertainties and distinct S8 evidence remain unchanged.

Rollback at this checkpoint is non-activation and preservation of the local patch/evidence.
No installed schema or live process has been changed. Later rollback must close admission,
drain or retain uncertain ownership, preserve append-only journals/receipts and avoid any blind
retry, resource release, old-writer restart or evidence-table removal.


## S11 trusted-proof design evidence — 2026-09-24

Authority: documentation/mechanism design only, following the operator's agreement to that next
step. No Bot/SQL runtime implementation, execution against SQL/provider/Discord, Git publication,
deployment or activation occurred. Only the eight S7 preparation documents are amended.

Source inspection found factory/composition gaps, caller-supplied proof dictionaries, aggregate
request pacing without independently durable per-request outcomes, and no production authority
that establishes provider-child termination. The resulting proposal adds independent supervision
and five SQL evidence entities; it does not claim installation or provider proof. Public Microsoft
Job Object/process-handle/named-pipe documentation and Google Sheets limits/Drive permissions
references were read; the mechanism contract links the supporting sources. No provider account
was accessed. A Sheets timeout/readback is not accepted as no-delayed-effects proof.

### Preservation and historical evidence availability

The earlier temporary directories `k98-s11-preparation-20260924T074541Z`,
`k98-s10e-closeout-20260915`, `k98-s10d-implementation-20260915` and `k98-s10e-authoring`
under `C:/Users/cwatt/AppData/Local/Temp` are currently absent. They were not removed by this pass.
Earlier verification statements below remain historical records, not fresh archive verification.
The operator was asked for any moved/backed-up location; no replacement evidence is invented.

A new pre-edit snapshot is retained at
`C:/Users/cwatt/.codex/visualizations/2026/09/24/01a0d231-08d0-7610-a83f-9d9d907c2b0d/s11-proof-design-080231/`.
It contains `before-documents.zip`, `before-manifest.json` and both entry status records:
57 Bot path identities (55 extant/two absent) and two separately prefixed SQL documents, with
SHA256/current baseline blob identities. This preserves current files, not missing historical
archives. Exact old rename/delivery evidence remains open until recovered or equivalently proven.


### Design-pass validation

Fresh checks passed: unchanged Bot/production/SQL comparison refs; empty indexes; exact entry
status identities; every non-authorized pending-file hash unchanged; and the original complete
body of each of the eight amended documents retained byte-for-byte. Both repositories passed
`git diff --check`. Architecture validation passed with zero Python files; deferred validation
passed for all 55 extant pending Bot Markdown files; security-routing validation passed with zero
errors/warnings. Test selection used all 57 Bot identities. All 962 relative file links resolved.
Logs and final snapshots are retained beside the fresh pre-edit archive above.

No pytest, smoke imports or command registration execution is warranted for these Markdown-only
changes; none can validate the proposed unimplemented authority. SQL static authoring checks,
transaction/concurrency tests, Windows child-lifecycle tests, provider/Discord checks and deployment
acceptance are future evidence categories, not results of this pass. Changes security scans are
skipped for this documentation-only delta; separate exact Bot and SQL implementation diffs require
routing with Deep off. No whole-repository scan is authorized.

## S11 preparation evidence — 2026-09-24

### Authority, source state and preservation

The initial review made no changes. The operator then approved its proposed **preparation/design
only** next step. New work is limited to the eight S7 Markdown files and offline documentation
validation. No executable Bot/SQL/test/config file is edited; no operational execution, Git
publication, deployment, activation or new task is authorized or performed.

Rechecked Bot main/HEAD/origin main `721ad7e0cd6b160ddddad328c2338a98bdfb6e0a`,
production/main `3dbe63e7a47175df85ed17814ea06f9dd3d130b7`, SQL main/HEAD/origin main
`2352a898881d4b74d6eec153bb3cb381d6162041`; indexes empty. No bot-machine pull is reported.
Comparison anchors were not reset instructions. No network/GitHub refresh was performed; delivery
checks used retained GitHub filename/previous_filename metadata and local immutable objects.

Before editing, all 59 entries in the retained S10E final manifest matched local exact paths,
SHA256 bytes/deletions and baseline blobs/absence (57 Bot identities, two SQL docs). The initial
scope also compared retained delivered PR metadata to Bot/production/SQL blobs with no mismatch,
and checked the five recorded S10D recovery artifact hashes. These checks do not substitute for
future PR-head/merge verification of the new pending union.

The complete pre-edit pending-document snapshot, manifest and both repositories' staged/unstaged
patch/status records are retained at
`C:/Users/cwatt/AppData/Local/Temp/k98-s11-preparation-20260924T074541Z/`.
`before-documents.zip` includes both repositories with separate prefixes; it is backup evidence,
not a mixed-repository publication. Original S10D/S10E recovery artifacts remain untouched.
Final validation/identity manifests and recovery ZIP are recorded in this same directory.

### Findings and evidence matrix

| Surface | Source/retained result | Current S11 conclusion |
|---|---|---|
| Startup | bot_instance calls register_exports without factory | Hook exists; registration remains closed; earlier initial-search suggestion of a missing hook was corrected |
| Factories and writers | Both configured factories raise; no production legacy runtime construction/binding found | Real composition gap; no flag-only activation |
| Trusted recovery | DALs check exact snapshot/owner/fence/version and evidence shape; services require injected probes/verifiers | Production proof authority/read-only probe composition missing; interface alone is not proof |
| Bot offline | S10E retained 4,664 passed / 71 skipped; focused 311 | Historical results, not rerun or new composed-runtime evidence |
| SQL S10A | Accepted earlier disposable operations including actual restore | Preserve accepted result; not proof of another target |
| SQL S10C/D/E | Static authoring/checker evidence; D 463 assertions/90 authored cases; E 428 assertions | No installation, fixture/concurrency, backup/restore or provider pass inferred |
| S8A | Six disposable scripts and VERIFYONLY; no actual restore | Preserve separately from later S8B restore |
| S8B | 50 SQL cases and actual restore at recorded hashes; later fixes/runner history offline | Neither repeat nor relabel as fresh final-runtime transaction evidence |
| S8C | Seven operator-reported local work-instruction checks | Not live Discord/deployment acceptance |
| S6 | Accepted 5,806-player × ten-period benchmark, 2,248.609s full export/readback and retained interruption outcomes | Measurements remain accepted; OPS01/PERF01/CAP01 operational components remain open |
| Deployment/provider/Discord | No bot-machine pull; exact new target identities not supplied | G4 packet cannot execute; G5 remains operator-owned |

Preserve uncertain publications `e19c89ac-7977-5f28-ae4c-031807cd1728` and
`54a2480a-26fb-5bad-a3f5-9321525a731c`, all retained files/databases and receipt bytes. No new
provider inspection or disposition of these publications occurred.

### Preparation validation and security routing

Preparation validation passed: architecture (zero Python files affected), deferred-items (55
extant pending Markdown files), security routing (zero errors/warnings), exact-path test selection
(all 57 Bot identities), both repositories' whitespace checks, and all 951 checked relative file
links. Before/after verification found exactly the eight approved Bot edits; all prior document
body bytes and all other pending Bot/SQL bytes/deletions were preserved. New section anchors are
checked separately in the retained validation evidence. Runtime
pytest/full-suite/log-noise, smoke imports, command registration, SQL fixtures, provider and Discord
checks are skipped because this step changes only Markdown. Selector recommendations are not
execution evidence. No predecessor rerun or newly accepted runtime result is claimed.

Security routing: documentation-only skip for the eight preparation edits within the complete
57-path Bot Markdown union at `721ad7e0cd6b160ddddad328c2338a98bdfb6e0a`. No executable
permission/input/data-access/network/config/persistence/deployment effect. SQL's two pending docs
at `2352a898881d4b74d6eec153bb3cb381d6162041` are unchanged by this step and retain their
documentation-only skip. No scan started. Any approved runtime patch needs Changes, Deep off,
exact immutable target and supporting coverage; actual SQL changes are a separate review.

All preparation stays pending for the next genuine authorized Bot implementation PR, together
with every mandatory S10E manifest identity and both archive move sides. The two SQL closeout
documents remain separate and unchanged. See the [manifest](integration_implementation_manifests.md#s11-preparation-and-proposed-implementation-manifests--2026-09-24)
and [approval packet](release_readiness_and_rollback.md#s11-preparation-and-release-approval-packet--2026-09-24).

## Current status — S10E merged; S11 review/scope next, 2026-09-15

S10E Bot [mirror #280](https://github.com/cwatts6/K98-bot-mirror/pull/280),
[production #587](https://github.com/cwatts6/k98-bot/pull/587) and
[SQL #88](https://github.com/cwatts6/K98-bot-SQL-Server/pull/88) are merged and locally pulled.
Bot main/origin main `721ad7e0cd6b160ddddad328c2338a98bdfb6e0a`; production/main `3dbe63e7a47175df85ed17814ea06f9dd3d130b7`; SQL main/origin main `2352a898881d4b74d6eec153bb3cb381d6162041`.
**No changes have been pulled to the bot machine.** Repository delivery is complete;
SQL installation, real provider/Discord execution, runtime acceptance and activation remain unproven.

Next: **S11 Controlled Release and Acceptance, initial review/scope only**:
[task pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md) and [starter](../../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md).
Read the [S10E closeout and exact next-PR manifest](s10e_closeout_and_s11_handoff.md).
S11 starts from S7's eight-document release proposal plus mandatory carry-forward docs;
reconcile real composition/installation/operational gaps before proposing any runtime scope.
Its eventual authorized Bot PR MUST include every listed pending document, both S10E archive
move identities, this closeout and S11 pack/starter. Verify filename AND previous_filename,
exact content and absent-at-base proof; counts are insufficient. No standalone docs PR,
mixed repositories or manufactured implementation. Pending SQL closeout edits belong only
in the next genuine authorized SQL implementation PR; otherwise carry them forward.

Preserve all recovered documentation evidence, S6-OPS01/PERF01/CAP01, both uncertain publications
and retained data. S8A six scripts, S8B 50 cases/actual restore versus offline history, and S8C
seven local checks remain distinct. S10C/D/E static authoring is not installation/provider proof.
No predecessor rerun, SQL/provider/Discord operation, bot-machine pull/restart/deployment,
activation, new task creation or Git publication is authorized by this documentation closeout.
Earlier dated pending/next-slice instructions are historical and do not reopen accepted work.

## Historical S10D closeout — 2026-09-15

SQL #87 is merged and locally pulled at `80353a6280e523f30c27e724f71e7b47dadadd16`.
Bot main/origin main remains `bf3eccf964601e2975dd86eefe96f7b0153be3bb`; production/main remains
`aa1821adbde9ccda47797caa83b5d5a9958bfce9`. **No changes have been pulled to the bot machine.**
S10D authoring, offline checks and Changes security review are complete; SQL installation and
provider/Discord execution are not established. S10C remains source/static SQL evidence too.
See [S10D closeout and exact carry-forward manifests](s10d_closeout_and_s10e_handoff.md).

Next: **S10E Export Operator UX and Rollover, initial review/scope only**:
[task pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md) and [starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md).
The eventual authorized S10E Bot implementation PR MUST include every pending Bot document in
that closeout, this pack/starter and all required archive identities. Verify filename AND
previous_filename, or exact merged/content and absent-at-base proof. No standalone docs PR,
repository mixing, manufactured implementation or renewed predecessor/grouping approval.
Both SQL documents were delivered in #87; their new closeout edits stay in SQL for the next
actual authorized SQL implementation PR. S10E scope must assess any genuine SQL delta separately.

Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and every retained database/file.
S8A six scripts, S8B 50 cases/actual restore versus offline history, and S8C seven local checks
remain distinct; none is new live Discord or deployment evidence. Shutdown stops admission and
drains owned delivery; uncertainty retains claims. No lease-age/job-state release.
This documentation closeout authorizes no implementation, Git publication, SQL/provider/Discord
execution, real import/export, bot-machine action, deployment, activation, predecessor rerun or
new task. Earlier dated checkpoints are historical; the current closeout controls the next step.

## Historical S10A closeout status — 2026-09-14

S10A SQL #85 is merged and locally pulled at `3776dfa6b0892a8800d236fdf111c4d2f93c3813`.
All five disposable fixture modes, 76 unique cases in install and constraints, direct apply/rerun,
backup/actual restore and final preservation checks passed; final CI passed. Results accepted.
No changes have been pulled to the bot machine; no production SQL deployment or activation.
S9B mirror #277, production #584 and SQL #84 remain delivered. Bot comparison anchors are unchanged.

Next: **S10B Shared Export Coordination Worker and Durable Budget, initial review/scope only**.
Use the [S10B task pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10B%20Shared%20Export%20Coordination%20Worker%20and%20Durable%20Budget.md) and [starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10B%20Shared%20Export%20Coordination%20Worker%20and%20Durable%20Budget.md).
The [S10A closeout and exact carry-forward manifest](s10a_implementation_and_s10b_handoff.md) controls delivery.
Completed S10A and S9B packs/starters are archived; retained execution/operator evidence stays available.
Every pending Bot document and archive destination belongs in the eventual S10B implementation PR.
Check exact filename AND previous_filename, with explicit absent-at-base proof for never-committed
S10A source paths. No standalone documentation PR or repository mixing; grouping is settled.
Both mandatory SQL delivery documents were included and merged in SQL #85.

Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and all retained databases/files.
S8B accepted smoke/50-case and actual-restore evidence remains distinct from offline runner history,
S8A six-script evidence and S8C seven local checks; S8C is not live Discord acceptance.
No S10B implementation, Git publication, runtime execution, deployment, activation or automatic new task
is authorized by this closeout. SourceRouting.Enabled alone never enables source activation.
Earlier dated checkpoints below are historical.


## Historical S8B closeout status — 2026-09-13

S8B is complete, operator accepted, successfully smoke tested and delivered through merged
production #581 and SQL #81. Local pulls are complete; **no changes have been pulled to the
bot machine**. Mirror #274 is closed without a merge record; its delivered content is verified
in synchronized mirror main. See the [canonical closeout and exact carry-forward manifest](s8b_closeout_and_s8c_handoff.md)
for merge/content proof, final offline tests and the distinct historical disposable/runner evidence.
No fresh post-merge SQL or bot-machine smoke, deployment or activation is claimed.

**Next: S8C Intake and Admin Pairing UX in a new chat, initial review/scope only.**
Use the [S8C pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8C%20Intake%20and%20Admin%20Pairing%20UX.md) and [starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8C%20Intake%20and%20Admin%20Pairing%20UX.md).
The eventual separately authorized S8C Bot PR must include all closeout documentation and both
sides of both S8B archive moves, checking actual filename and previous_filename; SQL delivery-log
carry-forward is separate. S7 decisions and predecessor acceptance remain settled. S9 public
routing and S10 export coordination remain later work; SourceRouting.Enabled alone is insufficient.
Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and all retained databases/files.
Earlier dated scope/approval/next-slice statements are historical and do not reopen accepted work.

## Historical delivery — 2026-09-12 post-S6 closeout

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

**Historical next-slice selection: S8B followed S7/S8A; current next slice is S8C above.**
Follow the current status above; do not rerun predecessors or start later implementation packs.
Carry every path in the post-S6 handoff manifest into the next separately authorized
slice PR, including both S6 archive move sides. No Git publication, SQL/provider
execution, restart, production promotion or activation is authorized by this update.
Earlier dated blocks below are historical and do not select the next task.

[Settled requirements](post_s6_integration_requirements.md); [handoff and exact manifest](post_s6_handoff_log.md); [S7 pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md).

> **2026-09-12 PR #272 routing review correction:** Public runtime routing is an
> OPEN implementation prerequisite. The current code does not consume
> SourceRouting.Enabled to switch ordinary readers to V2. The routing-row update
> below is only a conditional design and must not run until a separately approved,
> reviewed, deployed and accepted public routing consumer exists. Synthetic
> rehearsal acceptance does not close this gap or establish activation readiness.


> **2026-09-12 mirror PR authorization:** Chris Watts explicitly approved committing,
> pushing and opening the complete documentation-only draft PR in K98-bot-mirror.
> This supersedes the preceding pending-PR-permission statements. No merge,
> production promotion or activation is authorized. Rehearsal evidence is accepted;
> unresolved operational gates and all retained uncertain outputs remain preserved.


> **2026-09-12 operator acceptance update:** Chris Watts replied "approved please
> proceed" to the completed rehearsal report. The measured rehearsal outcomes are
> accepted. Outstanding scheduling, capacity/retention and uncertain-publication
> dispositions remain explicit release gates; this is not evidence of their
> resolution. The next proposed external step is the complete S6 documentation
> mirror PR. Its exact commit/push/PR permission is being clarified against the
> earlier explicit prohibition. Production operations remain unexecuted.


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


2026-09-12. **Documentation preparation under explicit S6 G3; stopped at G4.**
Operational readiness and G5 acceptance are not granted. The
[readiness and rollback packet](release_readiness_and_rollback.md) defines proposed operations;
the [S6 pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S6%20Release%20Readiness%20and%20Controlled%20Activation.md)
section 11 is the exact authorization manifest. No rehearsal was executed.

## 1. Summary

User explicitly approved S6 G3 for evidence preparation only, confirming all predecessors accepted.
Current core references, approved architecture/EndScanID amendment, Phase 2B plan, 70 scenarios,
S4B follow-up register, 2026-09-11 handoff and archived S5B delivery were inspected before edits.
Operational references were read as guidance, never executed. K98 architecture-scope,
test-selection, security-review-routing and SQL-validation apply; final local review uses
k98-pr-review. Promotion-check waits for separately authorized G4 review. No delegation/new task.

Preserve B0 eligibility/attribution, exact endpoints, UTC scan start and semantic re-export identity.
Interim 11−10 then 12−10; final 13−10; authorized EndScanID=14 itself permits replacement 14−10
without a second correction command. Pending 14 cannot label 13 current final. Aggregate authority
and daily SCANORDER remain separate. The latest accepted equal-endpoint and either-endpoint
amendments are retained in the readiness document; historical architecture text is not rewritten.

## 2. File Manifest

All bot paths below are relative to `C:/discord_file_downloader`. Exact S6 delivery: 18 Git paths,
16 extant Markdown documents, including the two archive source deletions. Entry was exactly 16
pending Git paths / 14 extant documents. None is excluded merely because it predates S6.

| Path | Required disposition |
|---|---|
| README-DEV.md | Preserve closeout; add current S6 evidence status/navigation |
| docs/reference/README.md | Preserve closeout; add current S6 evidence status/navigation |
| docs/reference/kvk_source_migration/decision_and_evidence_register.md | Preserve closeout; add current S6 evidence status/navigation |
| docs/reference/kvk_source_migration/phase_2_implementation_plan.md | Preserve closeout/follow-up register; add current S6 evidence status/navigation |
| docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md | Preserve closeout; add current S6 evidence status/navigation |
| docs/reference/local_sql_development.md | Preserve closeout; add current S6 evidence status/navigation |
| docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S6 Release Readiness and Controlled Activation.md | Preserve original approval template/handoff; add dated current status |
| docs/task_packs/archive/Codex Task Pack - KVK Source Migration S6 Release Readiness and Controlled Activation.md | Preserve original pack/handoffs; append S6 canonical delivery |
| docs/task_packs/KVK Source Migration - Programme Pack.md | Preserve closeout; add current S6 evidence status/navigation |
| docs/task_packs/README.md | Preserve closeout; add current S6 evidence status/navigation |
| docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S5B Endpoint Config and Recovery Integration.md | Retain untracked archive destination and its complete entry bytes |
| docs/task_packs/archive/Codex Task Pack - KVK Source Migration S4B Versioned Exports and Delivery.md | Retain complete pending closeout bytes |
| docs/task_packs/archive/Codex Task Pack - KVK Source Migration S5B Endpoint Config and Recovery Integration.md | Retain untracked archive destination and all historical delivery bytes |
| docs/task_packs/archive/README.md | Preserve closeout; add current S6 evidence status/navigation |
| docs/task_packs/Codex Chat Starter - KVK Source Migration S5B Endpoint Config and Recovery Integration.md | Preserve archive source deletion |
| docs/task_packs/Codex Task Pack - KVK Source Migration S5B Endpoint Config and Recovery Integration.md | Preserve archive source deletion |
| docs/reference/kvk_source_migration/release_readiness_and_rollback.md | Create |
| docs/reference/kvk_source_migration/release_evidence_log.md | Create |

The eventual separately authorized PR must contain all 18 paths, allowing Git's rename presentation
to account for both move sides. Any omission requires exact merged-path proof. **PR Files changed
verification is pending because no PR exists.** Local manifest checks are not that remote check.
Later separately approved production promotion must carry this same documentation delta and archive
changes under the current promotion guide; no promotion operation is authorized here.

### Repository observations

| Repository | Branch; entry/end HEAD | Remotes and state |
|---|---|---|
| Bot | main; `85f303f6bd82bdc9a5cfc2d713da5480e1fa694a` | origin `https://github.com/cwatts6/K98-bot-mirror.git`; production `https://github.com/cwatts6/K98-bot.git`; origin/main equals HEAD; pending docs retained |
| SQL | main; `44afa315dd6cbfe9fec101f2a39a62e534f5b583` | origin `https://github.com/cwatts6/K98-bot-SQL-Server.git`; origin/main equals HEAD; clean |

Local production/main is `c7e063f02ebe8287a584d0054ea14f91a0c0ecc6`. Read-only `git status`,
branch/HEAD/remotes/local tracking refs and worktree inventories were inspected in both repositories.
Existing worktrees, including a stale/prunable SQL worktree entry, were left untouched. No new
branch/worktree is needed for this unstaged documentation preparation; proposed `codex/kvk-source-s6`
is not created. No fetch, pull, reset, merge, staging, commit, push or PR.
Focused source continuity comparison of kvk, proc_config_import.py, bot_config.py, bot_instance.py
and the S5B recovery/config tests against local production/main showed no delta. This proves only
the inspected source paths, not deployment or remote freshness.

Entry byte copies and SHA-256 manifest are retained outside Git at
`%TEMP%/k98-s6-evidence-q9qmwbbg/entry.json`. This captures all 14 original documents and the
two absent source paths before S6 edits. Final preservation checks must retain each original
document's complete bytes and all prior closeout changes.

## 3. New Files

- `docs/reference/kvk_source_migration/release_readiness_and_rollback.md`: release bindings,
  verified schema/config contracts, proposed transaction/rehearsals, open gates and rollback limits.
- `docs/reference/kvk_source_migration/release_evidence_log.md`: this canonical eleven-part
  delivery, exact preservation manifest, historical evidence provenance and fresh validation outcomes.

## 4. Modified Files

Nine named closeout/index documents gain an identical dated S6 status block and relative navigation
to the two new documents. The S6 starter gains a current-status notice without changing its
historical approval template. The S6 pack gains current status and canonical delivery evidence.
All original bytes and both archive move sides are retained. The three carried archive documents
are unchanged by S6 itself. No runtime, config, test, SQL or read-only operational reference is edited.

### Accepted historical evidence — not fresh S6 passes

The following are records read from retained delivery documents. Their dates, tested revisions and
limits remain controlling; no predecessor tests, database connections or provider operations reran.

| Evidence | Exact retained identity / actual recorded outcome | Limit |
|---|---|---|
| S5B accepted closeout | Mirror #271 merge `65c535dce831d0840f1a047b9c58f29c562df3df`; production #578 merge `c7e063f02ebe8287a584d0054ea14f91a0c0ecc6`, fix `e5bbd8f7`; synchronized mirror `85f303f6bd82bdc9a5cfc2d713da5480e1fa694a` | Operator accepted smoke; no fresh post-merge/bot-machine smoke. Local refs inspected; GitHub was not queried by S6. |
| S5B final review-fix validation | Patch over production `ff0dba287aa25cced60518d39d2c3b9036111bfa`, finalized in `e5bbd8f7`; seven-file focused suite 186 passed, zero skipped, 12.36s, including five SQL cases | Exact seven paths: tests/test_kvk_source_config_hook.py, tests/test_kvk_source_recovery.py, tests/test_proc_config_import.py, tests/test_proc_config_import_phase2.py, tests/test_kvk_source_upload_route.py, tests/test_kvk_source_delivery.py, tests/test_proc_config_import_offload.py. Historical only. |
| S5B split full suite | 4,048 passed / 39 skipped / 191.33s plus 36 dashboard tests / 1.80s; total 4,084 passed / 39 skipped; operational logs unchanged | Split around previously stalled dashboard timeout area; no claim the stalled single-process run passed. Five S5B SQL cases ran separately. |
| S5B SQL target | `9SX2VF4\K98DEV` / `K98_S5B_Disposable_20260912`; setup used `lpc:localhost\K98DEV`; SQL `44afa315dd6cbfe9fec101f2a39a62e534f5b583`; retained `%TEMP%/k98-s5b-setup.py` | Synthetic integration; retain, do not reuse/rebuild/delete. |
| S5B original Changes review | `6033894b-0125-44ea-8bd4-10651fcd8d38`; ten-Python-path authored patch over `90aea74c93c6aad2c890d1783ff53f109cc7bf8a`; Deep off, zero findings | Exact original manifest/digest and subsequent fix scans retained in archived S5B; not replaced by final fix-only review. |
| S5B final Changes review | `cf5a25c1-f9c6-431b-a2c6-fa9dba1716a7`; production fix patch over `ff0dba287aa25cced60518d39d2c3b9036111bfa`; digest `codex-security-snapshot/v1:sha256:645aab4b987b8eaebf2c2a63a9a4e9cb2ef7150adcb77b1f6efea8f0fb01a27b`; Deep off, zero findings | Two runtime files, two tests and nine status documents; private canonical artifacts under `%TEMP%/codex-security-scans-nRIFjb`. Record read, raw scan directory not revalidated by S6. |
| S4B real SDK/SQL recovery smoke | SQL `44afa315dd6cbfe9fec101f2a39a62e534f5b583`, database `K98_S4B_Disposable_20260910`; recovery/public cycle results 148.69s/fence 4, 141.16s/fence 5, 140.06s/fence 6 | Small synthetic recovery/readback/reuse; no actual process kill during in-flight request or representative shared-quota load. |
| S4B smoke-source review | Authored nine-file patch over `7baf92c7badc3f40006841046825a788bc823373`, `.codex_scan_stage/s4b-recovery-public`; scan `15b30d80-e074-4a01-87ce-1237b1ca30d9`, Deep off, digest `codex-security-snapshot/v1:sha256:0221b7a40a9151e5e80baaac575872522dcbb2ba066ee0d5ee6924b788aa31ac` | Retain later exact review-fix/closeout scans too; this smoke revision is not relabelled as merged HEAD. |
| S4B sizing / MP01 | 10,000 synthetic players / ten periods: four generation files, nine initial files; named parameterized test `test_multi_period_delivery_uses_changed_anchor_and_deduplicates`, two cases passed | Sizing is not capacity acceptance; real generation/DAL logic composed over fake SQL/Google is component evidence. |

Full immutable histories, exact disposable files/IDs, intermediate scan targets and prior failures:
[archived S4B](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S4B%20Versioned%20Exports%20and%20Delivery.md),
[archived S5B](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S5B%20Endpoint%20Config%20and%20Recovery%20Integration.md).
Those archive files are preserved byte-for-byte from S6 entry. Retain predecessor S2A/S2B databases
and `K98_S3B_Disposable_20260910` as directed by the plan; S6 does not inventory database contents.

## 5. SQL Changes

None. The separate SQL working tree is clean at its entry HEAD. Read-only local contract checks
covered `sql_schema/KVK.SourceRouting.Table.sql`, `KVK.SourceSelection.Table.sql`,
`KVK.SourcePublication.Table.sql`, `KVK.SourceConfigRequest.Table.sql`, `KVK.SourceDelivery.Table.sql`,
`KVK.SourceAction.Table.sql`
and both accepted migration hashes recorded in the readiness packet. Routing has Enabled default 0,
positive RoutingVersion and required approval/capability fields when enabled. Selection is scoped
to source/KVK/period; delivery receipt remains nvarchar(1024). No live schema/rows/jobs, permissions,
migration history, backup/restore or deployed module parity was queried. Local alignment is suitable
for this documentation preview; **SQL deployment safety remains unverified at the live target**.

## 6. Helpers Reused

No helper created or changed. The preview references existing `lock_scope`, `locked_period` and
`desired_config` semantics in the accepted DAL: transaction-owned season mutex, routing → selection
→ request lock order, desired request resolution and expected-version checks. `require_schema` is
a local source contract, not comprehensive deployed capability proof. No activation helper exists.
Existing delivery/recovery and validation tools are referenced; no duplicate runtime implementation.

## 7. Refactor Findings

No new in-scope runtime/refactor defect established by this documentation review. Legacy exporter
grouping/summation and generic ProcConfig WS1 debt remain outside S6. The missing activation helper,
unbound operational target and three named evidence gates are explicit release prerequisites;
this task does not implement a helper, alter schema or close them with documentation.

## 8. Test Plan with outcomes

Fresh S6 checks are documentation/static only. See the final validation append below for actual
results. Exact test manifest is: local Markdown path/fragment checks; section-11 vs Git-path equality;
entry-byte preservation/archive-move checks; cited local refs/source continuity and migration hashes;
architecture/deferred/security-routing validators; exact-path selector; applicable Markdown hooks;
`git diff --check`. No test files are created or modified.

Runtime pytest, log-noise suite wrapper, import smoke, registration/inventory tests and SQL integration
are deliberately skipped: no runtime/config/command/test changes, no predecessor reruns, and S6 G3
does not authorize rehearsal execution. Selector's generic smoke/registration recommendations are
recorded and overridden for this Markdown-only boundary. No historical suite result is a fresh pass.
SQL deployment validators are skipped because they can connect/write; no default target is used.

### Exact S6 scenario allocation

All rows below are **proposed G4 evidence, not executed by S6**. Definitions remain the
[70-scenario contract](phase_2_acceptance_scenarios.md); accepted predecessor coverage is retained.

| S6 assigned IDs | Proposed evidence and acceptance condition | Fresh S6 outcome |
|---|---|---|
| T17, T35–T43 | Rejected partial aggregates preserve prior revision; latest live/final/corrected selection and independent overall/stream coverage in private readback | Not executed; exact synthetic target/operations pending |
| T46–T51 | Transaction interruption/concurrency and current desired-config/selection integrity with durable readback | Historical SQL coverage retained; no new S6 operational pass |
| T52–T54 | One request pins a generation; lost cache notification/restart, stale views and current permission recheck | Not executed; deployed capability/permission evidence pending |
| T55–T58 | Honest missingness and exact precision; multi-period export, private partial writes, stale queued generation rejection | OPS01/PERF01/CAP01 pending |
| T59 | Uncertain external outcome remains reconcilable; no blind send or daily-claim reset | OPS01 pending; no Discord operation approved |
| T61–T62 | Legacy recompute isolation and independent targets/history/rankings/daily/profile/calendar behavior | Local source unchanged; operational evidence pending |
| T64 | Revoked/wrong actor, guild/channel/role denied at final action without private-row leakage | Current deployed ACL/identity proof pending |
| T65–T67 | Rollback increases versions, retains immutable history, refuses invented legacy fallback and incompatible comparisons | Proposed rollback only; verified recovery target pending |
| T68–T70 | Interim 11−10 / 12−10, final 13−10, authorized 14−10; missing 14 pending, retries/races idempotent without extra correction command | Accepted deterministic/SQL history retained; no fresh S6 rehearsal |

### Open gate register — acceptance remains operator-owned

| ID | Status | Existing evidence | Required closure / exact gap | Evidence and acceptance |
|---|---|---|---|---|
| S6-OPS01 | OPEN | S4B real SDK recovery/readback and S5B accepted caller/SQL recovery | Exact process/database/file targets, real in-flight interruption at private writes, Viewer grants and pointer publication; durable phases/fences/receipts, external readback, quarantine/uncertainty and no duplicate after restart | Plan in readiness §5; new measurement path not yet created; not executed; Chris Watts acceptance pending |
| S6-PERF01 | OPEN | Small S4B timings and synthetic partition sizing | Agreed duration/cadence/shared request budget; representative multipart bytes/cells/periods, actual API counts/readbacks, elapsed time, quotas/429/503 and other consumers | Plan in readiness §5; thresholds unset; no representative measurement; Chris Watts acceptance pending |
| S6-CAP01 | OPEN | Four files/generation and nine initial files; bounded receipt checks | Provisioned exact owner/Editor/canShare/audience; current/staging/final/reference/quarantine sizing, insufficient slots and nvarchar(1024) exhaustion, safe fresh destination | Plan in readiness §5; S6 IDs/retention horizon unbound; no rehearsal; Chris Watts acceptance pending |

No operational gate can close from documentation, historical test totals or operator acceptance of
S5B. A future acceptance entry must record exact revisions/targets/operations, evidence path/hash,
measured outcomes, residual limits, approver and UTC. Until then all three remain activation blockers.

## 9. Security Review Decision and Evidence

Bot: **documented documentation-only skip**, exact section-2 18-path working-tree delta against
`85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`, including pre-existing closeout and archive moves.
Only inert Markdown evidence/status/navigation and an explicitly non-executable operational preview
are authored. No runtime, permission, input, data-access, configuration, dependency, network,
deployment or persistence behavior changes. Inspect the final patch plus untracked files; do not
claim a staged-only scan covers unstaged documentation. No new security scan launched.

SQL: **separate no-change skip**, `44afa315dd6cbfe9fec101f2a39a62e534f5b583` to the same HEAD,
empty staged/unstaged/untracked delta. Historical S2A/S2B reviews remain in their accepted packs.
Any later authorized implementation or operational delta must be re-routed separately: required
reviews use Changes with exact per-repo base/head or task-only patch, Deep off. No standard/deep
scan, combined repo history or automatically created task is authorized.

## 10. Deployment Steps

**None executed.** Proposed SQL-first/flags-off deployment, private rehearsal, capability checks,
guarded activation transaction and versioned rollback are in the readiness packet. Exact production
targets, current versions, runtime state, jobs/editors/readers, permissions and backup proof remain
unavailable. G4 exact-operation approval is pending; G5 acceptance remains Chris Watts's decision.
No pull/reset/merge/push/PR, live SQL, real imports/exports, Discord actions, restart, deployment or
activation. No predecessor/later pack or automatic new task. No private player data/credentials in Git.

## 11. Deferred Optimisations

None newly evidenced. Existing WS1 and legacy export debt remain separate. S6-OPS01, S6-PERF01,
S6-CAP01 and unbound activation/audit/rollback capabilities are release gates, not deferred debt.
Documentation rollback removes only S6 additions while retaining every carried-forward closeout
edit and archive move. Operational rollback remains separately approved and evidence-dependent.

## Final S6 documentation validation

Fresh checks on 2026-09-12:

- `python scripts/validate_architecture_boundaries.py`: passed; 0 Python paths changed.
- `python scripts/validate_deferred_items.py`: passed; 16 Markdown documents. Initial run flagged
  generic wording in nine new status blocks; replaced only that S6
  wording with "authorized gates", then passed. No pre-existing evidence was rewritten.
- `python scripts/validate_codex_security_routing.py`: passed; 0 errors / 0 warnings.
- `python scripts/select_tests.py` with exactly the 18 section-2 paths: passed; recommended only
  smoke imports and command registration. Documentation-only skips above apply to those commands.
- Local manifest/preservation check: exact 18 Git paths, no extras/omissions; all original bytes
  retained, three carried archive documents unchanged, two source deletions retained. Local links
  and fragments resolve; final counts are recorded in the S6 pack appendix.
- `git diff --check`: passed. Final refs match entry; bot index empty, SQL working tree clean.
- Installed pre-commit-hooks v6.0.0 direct entry points: end-of-file, merge-conflict, mixed-line-ending
  (check only) and large-file checks passed. Trailing whitespace passes on the 15 documents other
  than README-DEV.md; its original historical trailing spaces are deliberately retained. S6-added
  lines have no trailing whitespace. An initial direct fixer changed old README whitespace; those
  changes were restored from the entry snapshot before delivery and preservation was rechecked.
- Pre-commit orchestration limitation: system Python has no pre_commit; the repository virtualenv
  launcher could not write its sandbox-restricted cache database/log. A temporary cache copy stalled
  and was interrupted without a reported hook outcome. Direct cached hook modules supplied the
  checks above, without package installation or network access. No blanket pre-commit pass claimed.
  Python/YAML/type/registration hooks have no changed matching runtime surface; staged-only gitleaks
  is skipped because nothing is staged and it would not cover this patch. Authored evidence was
  reviewed for private data/credentials; only redacted metadata and synthetic examples were added.

Final local k98-pr-review verdict: documentation is ready for operator review; no blocking issue
found within the evidence-preparation scope. This is neither PR authorization nor activation
readiness. Exact live bindings, OPS01/PERF01/CAP01 measurements, durable activation audit/rollback
approval, eventual PR Files changed verification and G5 acceptance remain open as specified.
Preparation completion does not satisfy the unexecuted G4 scenarios or G5 acceptance.

## 2026-09-12 authorized local rehearsal — partial evidence, gates OPEN

Chris Watts approved "local database on K98DEV server" and "approval to begin
rehearsal" after the retained G3 preparation checkpoint. This authorizes the local
synthetic work recorded here; it is not production activation or G5 acceptance.
No predecessor pack was executed. No real player import/export, Discord action,
bot-machine update/restart, Git publication, deployment or activation was performed.

### Exact execution and retained evidence

- Local server identity: `9SX2VF4\K98DEV`, SQL Server `16.0.1200.5`; shared-memory
  connection `lpc:localhost\K98DEV`, Windows authentication.
- New, previously absent database: `K98_S6_Disposable_20260912`, collation
  `Latin1_General_CI_AS`, compatibility 160. Retained predecessor databases were
  not modified. Installed accepted migrations `20260909_001_kvk_source_observation_facts.sql`
  (SHA-256 `4b19c8e54a7555e796c06124640efd27b6838c8360d352bd55265d04bdc1614c`)
  and `20260910_001_kvk_source_publication_state.sql`
  (`2985551c7cac6ba158a38c436389aa13b44fe36235ccf6768b684037cce77fbc`).
  Synthetic KVK_Windows fixture matches authoritative columns, primary key, default
  and checks; legacy secondary indexes were not installed. There are 26 KVK tables;
  setup reported zero disabled/untrusted constraints. This is not a full production schema.
- Bot main/origin-main `85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`;
  SQL main/origin-main `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
  Remotes retain the section-1 entry mapping; no fetch, pull or ref mutation.
- Temporary S6 harness uses existing synthetic helper functions and current DAL/services;
  it does not invoke predecessor test suites. Only owned hidden child processes exit.
  No production bot process is started or killed. All database connections assert the
  exact server and database. Evidence directory (outside Git):
  `C:/Users/cwatt/AppData/Local/Temp/k98-s6-rehearsal-x8tpc14d`.
- `setup.py` completed once. Initial sandbox Windows-authentication connection failed;
  the same target succeeded with approved elevated execution. No authentication or
  TLS-verification bypass was added to resolve that failure.
- `local_rehearsal.py` completed once, exit 0, from
  `2026-09-12T14:42:16.747885Z` to `2026-09-12T14:42:27.478053Z`.
  Exact outcomes, UTC timestamps, publication/period IDs and versions are retained in
  `local-results.json`; child process IDs and committed/checkpoint evidence are in
  `before_commit-exit.json`, `after_commit-exit.json`, `private_started-exit.json`
  and `publication_pending-exit.json`. Preserve this directory and database; no cleanup
  or blind replay is authorized. Entry documentation backups are in `entry.json`.

### Actual results and limits

| Check | Actual result | Limit / scenario allocation |
|---|---|---|
| Synthetic endpoints in seasons 139295168 and 65250356 | Both advanced live 11−10, live 12−10, final 13−10 | Partial T68–T70; two synthetic governors, not representative population |
| Duplicate observation 13 | Existing ScanID 13 returned; recovery allocated no publication | Semantic duplicate path checked; not a full ZIP/format variation matrix |
| Owned process exit before transaction commit | Fresh connection observed zero config requests and zero Windows rows; prior publication retained | Partial T46–T51; no SQL server restart |
| Owned process exit after commit/lost acknowledgement | One durable request and Windows row; fresh process recovered pending live 13−10, then corrected_final 14−10 after scan 14 arrived | EndScanID update itself supplied authority; no separate correction command; second recovery no-op |
| Exit after private_started checkpoint | Normal retry blocked; explicit local recovery changed owner and fence 1→2; two old synthetic slot IDs quarantined | S6-OPS01 partial only: no Google request was in flight |
| Exit after publication_pending checkpoint | Normal retry and private recovery both blocked | S6-OPS01 partial only: no grant or pointer mutation performed |
| Receipt boundary | Exactly 1024 UTF-16 units accepted; 1025 rejected | S6-CAP01 partial only: direct serializer contract, not actual multipart/provider exhaustion |
| Isolation | Routing enabled rows = 0; aggregate state remained not_received | No inferred aggregate report, daily SCANORDER operation or real data import |

### Workbook inventory and outstanding operator inputs

B0, F1S, F1M and F1E source workbooks are present in Downloads and their SHA-256
hashes match the accepted evidence. The A1 aggregate example is also present under
the private evidence directory and matches
`563e7a67948dbcde211764e30645a1188d06d7e39335e5793335a23f6ea9d2e3`.
Presence/hash verification did not import their contents or approve their endpoint
mapping. A1 remains a format/example artifact unless separately bound. No required
recorded source workbook is missing from this inventory; it does not establish a
future production input set. Private workbooks and credentials remain outside Git.

Read-only Google metadata checks found all five registered S4B workbooks accessible:
index `1xwF92PbxgXD0InA-ekuEPkN8MA5pgd1navpMyxEe6_Y`, quarantined slots
`1lD6o6uOKUg1e0H0cAz2guFOkFG0sXDntjt9wz_oDC3I` and
`1_Jb6hkBreXTR256MEYgFAraKDjytcQtCjEPe26qABFg`, retained recovery slots
`1bcqUkN3fySc34BsEDo_nflU3hfHJLqe5pBM6med9VS4` and
`1H9kXpIl0Vg5zv1CoLghp680j0Q90mD3fE_IpIIPG-7M`.
Existing service-account Editor access and owner's canShare were verified. Index
and recovery slots have link Viewer access; quarantined slots remain private.
These are retained evidence, not disposable S6 destinations; none was mutated.
No dedicated S6 workbook set was found in the metadata search. Approval to provision
a separate index/eight blank slots with exact rehearsal sharing, or operator-supplied
dedicated IDs, remains pending. A proposed eight-slot set is not yet a proven retention budget.

| Gate | Status after local rehearsal | Still required before acceptance |
|---|---|---|
| S6-OPS01 | OPEN; local process/SQL recovery evidence added | Dedicated Google targets and authorized sharing; measured interruption during private writes, Viewer grants and index pointer; actual external readback, fences/receipts, quarantine and reconciliation |
| S6-PERF01 | OPEN; no representative load measurement | Operator export cadence, maximum duration and other service-account consumers; agreed shared budget; actual representative multipart bytes/cells/API calls/readbacks/timing/429/503 outcomes |
| S6-CAP01 | OPEN; receipt boundary and existing ACL metadata checked | Dedicated owner/Editor/canShare/audience proof, measured active/staging/final/reference/quarantine retention, insufficient-slot and receipt-exhaustion behavior at actual provider scale |

G4 authorization remains bounded to approved rehearsal operations. G5 acceptance
and production activation remain operator-owned; none of these gates is accepted
by this local pass. Earlier unexecuted scenario rows retain their historical G3
meaning; only the partial evidence explicitly allocated above is new.

### Security, delivery and rollback disposition

Tracked changes remain the exact documentation carry-forward manifest, including
both archive rename sides. Temporary synthetic harnesses and results stay outside
Git; no production implementation, config, schema source or test file changed.
Bot security target remains the exact 18-path Markdown working-tree delta against
`85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`: documented inert-evidence skip.
SQL target remains separately `44afa315dd6cbfe9fec101f2a39a62e534f5b583` to itself,
empty delta: no-change skip. Runtime rehearsal evidence does not constitute a new
security scan. Any required later review must use Changes at exact separate repo
targets, Deep off. No standard/deep scan or automatic new task was launched.

No new deferred item was identified. Promotion verdict remains **Do not promote**:
provider evidence, acceptance, exact production operations and rollback authority
are unresolved. Retain local artifacts and disabled routing; do not delete/reuse
quarantined or retained workbooks. Canonical delivery remains sections 1–11 plus
this dated supplement. Eventual separately authorized PR and production promotion
must include the complete carry-forward manifest or prove individual paths merged.

### Local evidence SHA-256 manifest

| File | SHA-256 |
|---|---|
| `setup.py` | `56004b38572af3e4922ceecee5125f3bb133c3569a3b4da8581fb3c94a29644a` |
| `local_rehearsal.py` | `5982c3bd0c81b2e57edab75f003c12cee08c9b149f267cda9e5641a91d9c5acb` |
| `local-results.json` | `1be09acac6cdf679377a3994c7db4adb3e09a32bed5e601141022fdf355ba7ba` |
| `before_commit-exit.json` | `bbe1bf6084afcaa981b9d7cd458aaaeb84518a0a3da24589dfc7aef7a249978a` |
| `after_commit-exit.json` | `71d0faed122a7d540afe68c96cca510d2b57e3929ca46dc85333a5c1e5e9a783` |
| `private_started-exit.json` | `f1d94f5a4283832604d15d3e44e420aef2c836dca462751e3ad029afeb65fa3c` |
| `publication_pending-exit.json` | `a8faeaad3a71229522a17fd31db2962a386078cef6a26714800687d5e0beff66` |

### Rehearsal documentation validation

Fresh architecture validation passed (0 Python paths); deferred validation passed
(16 Markdown documents); security-routing validation passed (0 errors/warnings);
`git diff --check` passed. Exact-path test selection passed for all 18 manifest
paths; generic smoke-import/command-registration recommendations are skipped for
this documentation delta. No predecessor suite or full runtime suite was rerun.
The separately executed S6 synthetic process/SQL harness outcome is recorded above.

Manifest/preservation and link checks passed: exactly 18 Git paths, 16 extant
documents, all original rehearsal-entry bytes retained, three carried archived
documents unchanged, both archive source deletions preserved, 174 local links and
13 fragments resolved. Bot index remains empty; SQL repo remains clean; branches,
HEADs, origin/main refs and remotes remain at entry. Read-only local refs do not
prove remote freshness. Detailed validation and exact-path selection are retained
as `documentation-validation.json` and `selected-tests.txt` in the local evidence
directory. Earlier pre-commit orchestration limitations remain; no new blanket
pre-commit or security-scan pass is claimed. No private rows or credentials were
added to Git. Required eventual PR Files changed verification remains pending.

## 2026-09-12 S6 output provisioning and shared-consumer review

### Authority and operator performance expectations

Chris Watts approved S6 outputs and asked Codex to create them. The earlier question
specified a separate index/eight blank slots, the existing service-account Editor,
and Viewer sharing only for verified synthetic publication rehearsal. Creation and
Editor grants are now complete. No public Viewer grant, synthetic Google export or
pointer publication has yet been executed in S6. Retained S4B workbooks were untouched.

Operator expectation: **two or three exports per day; no fixed maximum duration**,
with runtime to be measured and made efficient where authorized. This removes the
unanswered cadence/duration question; do not invent a duration pass threshold.
Expected other service-account consumers are the all-KVK importer and scan-data
importer. The operator believed controls may prevent overlap and requested a check.
No account-wide quota isolation or runtime exclusivity is attested by that belief.
Performance acceptance should report actual elapsed time, size, calls, readbacks,
throttling and remaining headroom, then retain the operator's G5 decision.

### Created output manifest and verification

Nine unique native Google spreadsheets were imported from one verified blank local
XLSX into the new private My Drive `ChatGPT` folder
`1DMOF77hmxhY8PVS5R99E7kXFm3OKzU1k`. All title prefixes are
`K98 S6 rehearsal 2026-09-12`. The index and slots have distinct IDs from all retained
S4B/protected workbooks. No production config was changed to register these IDs.

| Role | Exact Google spreadsheet ID |
|---|---|
| index | `19jOzLAnEildMoxEQNqLsnkcB8tPo0w9Kym5_cbLof_g` |
| slot01 | `1oMIBoMqDp5od5hwEoAqlsvs8kK7svCsYcd0VEHb8Oxw` |
| slot02 | `1eWty-3Zr4RGfpA4eqpSTiVSNYZwrzUiXbG0kQ7yybMU` |
| slot03 | `1LeoZ5bySHbGTAyNUGNiKyUiG9zqn56eRvD-CTQvH7RI` |
| slot04 | `1i3o7DxQnsECQnFJ9bzI_mx6BBXb8-zvkVRU7pxQYWQ8` |
| slot05 | `1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg` |
| slot06 | `1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0` |
| slot07 | `1zMc_m7I70jr1s-GDBq035mGh0orXBAl3v2VJ-KZeY9k` |
| slot08 | `10GwOQWI5TgC2StB7axq3zZrMyjlQgj-PX_i6Ku3d2Lw` |

Connected-owner Drive metadata verified owner Chris Watts and exactly one additional
permission: the existing service-account Editor. There are no anyone/domain/group
permissions. Owner canShare is true for all nine. This is not yet evidence that the
runtime service-account credential can authenticate or that its canShare is true.
Native Sheets metadata verified one `Sheet1` per file, 1000 rows by 26 columns.
Bounded formula-mode readback of `Sheet1!A1:Z1000` returned no cells for every file.
They are intentionally blank operational slots, not finished reader-facing reports.
Native metadata retained hidden gridlines; no populated view exists for visual QA.
Default workbook timezone is America/Los_Angeles; no date values/formulas were
written. This timezone does not assign or alter UTC scan-start evidence; any later
timestamp handling must preserve the approved explicit UTC contract.

The local artifact builder exported and rendered the empty XLSX, then its process
returned exit 1 despite reporting completion. This is not recorded as a clean
builder process pass. Independent saved-XLSX inspection found only Sheet1 and no
populated cells; all nine native conversions and blank readbacks succeeded.

### Shared-consumer controls — static findings at exact accepted bot HEAD

| Code evidence | Finding and implication |
|---|---|
| `bot_helpers.py:280–339`; `services/fallback_upload_staging_service.py:79–101` | Monitored scan uploads share a process-local processing_lock across downstream processing. This protects that queue's participants. |
| `dl_bot.py:635–658` | All-KVK upload is a separate route before the fallback queue, returning without enqueueing there. |
| `upload_routes/kvk_all_route.py:535–548`; `kvk_all_importer.py:134–151` | All-KVK auto-export is scheduled as its own task and offloaded to a thread. The scan processing_lock is not acquired here. |
| `file_utils.py:1355–1400` | Thread offload runs the callable via asyncio.to_thread; its telemetry registry is not a global export queue. |
| `kvk/dal/new_source_delivery_dal.py:220–249` | S6 SQL session lock is keyed by destination kind/ID. It serializes participants for that destination, not all Google consumers. |
| `kvk/services/new_source_export_service.py:23–35,665–688` | S6 service-account pacing is 2.1 seconds between calls within a process. Other processes and legacy gsheet callers do not share that process memory. GET 429/503 retry behavior does not serialize mutations across consumers. |

Conclusion: **the current code does not establish a common lock/queue across all
three consumers**. Two or three exports/day does not preclude simultaneous bursts.
This is a concrete S6-PERF01 release gap, not a request to rewrite the importers or
run them concurrently. No live importer, bot-machine or credential consumer was
started to test contention. Runtime deployed versions/settings remain unverified.
Use separately verified scheduling/exclusivity or an explicitly approved shared
control change before claiming account-wide serialization; no implementation change
is included in this evidence-only delivery.

### Runtime preflight blocker and open acceptance gates

`sdk_preflight.py` ran once at `2026-09-12T14:59:38.149140Z` and failed before any
Google API call with FileNotFoundError. Read-only configuration resolution confirmed
the current GOOGLE_CREDENTIALS_FILE target is
`C:/discord_file_downloader/statsupdate-0d8b70356ef2.json`, which is absent; the default
credentials.json path is also absent. The existing trust bundle is present and TLS
verification remains enabled. No key was printed, created, copied or put in Git.
The operator was asked for the existing local key path or restoration at the configured
path; only a filesystem path/confirmation is needed, not key contents in chat.

Connected-owner Google Drive access was used for authorized provisioning and
readback; it must not substitute for the missing runtime service-account identity
in OPS01/PERF01/CAP01 measurements. No automatic retry of the failed preflight,
provider mutation or predecessor execution occurred. Preserve its failed result.

| Gate | Current status | Remaining exact evidence |
|---|---|---|
| S6-OPS01 | OPEN; local process evidence retained, dedicated outputs now bound | Restore local runtime credential; actual private-write/grant/pointer interruption and fresh-process external readback/reconciliation |
| S6-PERF01 | OPEN; 2–3/day, no hard duration cap recorded; shared-lock gap evidenced | Authenticated representative multipart measurement with actual calls/readbacks/bytes/timing/retries; shared-consumer budget or verified exclusivity; operator acceptance |
| S6-CAP01 | OPEN; nine private files provisioned; owner/Editor/blank readback passed | Runtime service-account canShare and synthetic Viewer publication proof; actual capacity/retention/insufficient-slot/receipt exhaustion; operator acceptance |

No G5 acceptance or production activation is granted. Database remains
`K98_S6_Disposable_20260912` with routing disabled from the retained local result;
this provisioning step did not write SQL. No pull/reset/merge/push/PR, production
SQL, real data import/export, Discord action, restart, deployment or activation.
All existing documentation, untracked archives and both rename sides remain in
the exact S6 carry-forward manifest. Canonical delivery is sections 1–11 plus the
dated supplements; previous pending-output/cadence statements are historical.

### Retained evidence manifest

Evidence directory remains `C:/Users/cwatt/AppData/Local/Temp/k98-s6-rehearsal-x8tpc14d`.

| File | SHA-256 |
|---|---|
| `s6-output-ids.json` | `b567d50aac28788ed83dcace812169edf77f4c2edcfbc0b6b8b330d61ac4dd5e` |
| `s6-output-metadata.json` | `dfac47c6338ddab0205972ad4f93c1441c5dec98a96955183529f8842e686a58` |
| `s6-output-blank-readback.json` | `6a3db33da630e95a6657500e3f2ddd13ad5fe1502344aaadbba51b2a3afc0054` |
| `sdk_preflight.py` | `1398e0d0f0c2981c8f05fb460819edbac40a5c4c9c9ced3450528c65234c3d8b` |
| `sdk-preflight-results.json` | `e95b26f5867247350f07ef6c2ff2afa25d70befc45033bdb99d1ca6b1a91b5e3` |

## 2026-09-12 authenticated S6 rehearsal and representative benchmark

### Authority, isolation and immutable revisions

The operator restored the configured local credential and explicitly approved
**5,806 synthetic players across ten periods**, confirming that the all-KVK and
scan-data importers would remain idle. This is operator-attested isolation during
this benchmark, not independent monitoring or a proven common concurrency lock.
Earlier approval covers the local K98DEV rehearsal and dedicated S6 outputs.
No real source-player workbook was imported or exported. Existing S4B files and
accepted predecessor evidence remain untouched; no predecessor was rerun.

Bot main/origin main remains `85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`,
with local production/main anchor `c7e063f02ebe8287a584d0054ea14f91a0c0ecc6`.
Bot origin is `https://github.com/cwatts6/K98-bot-mirror.git`; production is
`https://github.com/cwatts6/K98-bot.git`. SQL main/origin main remains
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`, origin
`https://github.com/cwatts6/K98-bot-SQL-Server.git`, with no SQL Git changes.
There are no runtime-source or tracked-test edits. Temporary rehearsal harnesses
and exact result artifacts are retained outside Git in the evidence directory below.

The only database written is retained disposable `K98_S6_Disposable_20260912`
on verified `9SX2VF4\K98DEV`, reached using `lpc:localhost\K98DEV` and Windows
authentication. Completed checks assert zero enabled SourceRouting rows. No
production SQL, bot-machine update, restart, real import/export, Discord operation,
deployment, activation, pull/reset/merge/push/PR or commit occurred.

The configured service-account key was restored locally and remains Git-ignored;
its contents are absent from Git and evidence. The restored runtime preflight
authenticated successfully and checked all nine original S6 files private/blank,
service-account Editor and canShare. The earlier missing-key failure remains
retained rather than rewritten. TLS verification used the existing trust bundle.

### Actual operations, recovery and limits of interruption evidence

The small operational scenarios deliberately use an **11,223-cell test ceiling**
to force two real Google files from 2,286 logical cells. This is a temporary harness
override; the accepted production 9,000,000-cell limit is unchanged. These scenarios
are operational proofs, not representative performance measurements.

* A child process exited after submitting a private data-write body, before reading
  its response. A fresh process observed the durable private_started claim and
  blocked blind retry. Explicit private recovery used fresh original slots 03–04,
  changed owner/fence 1→2, quarantined slots 01–02, fully verified and published.
  An independent audit found the quarantined grids/values unchanged. Confirmed
  repeat returned the same receipt with zero Google calls.
* Receipt-capacity exhaustion was rejected before SQL claim or provider calls using
  sixteen synthetic, unallocated 128-character IDs. No fake ID was accessed. Actual
  retained-slot exhaustion refused original slots 03–04 with setup_required after
  four GETs and no provider mutation. This proves fail-closed behavior, not an
  accepted long-term retention budget.
* The original pointer send-boundary interruption did **not** advance the index.
  Its planned confirmation assertion failed: fresh external readback correctly
  left the claim unresolved at publication_pending. Original slots 05–06 are
  verified public Viewer files, but the original index still references the prior
  confirmed generation in slots 03–04. Blind retry and private reclaim were blocked.
  This uncertainty is preserved; no forced pointer write or receipt repair occurred.
* A separate small scenario on the benchmark destination exits **after Google
  returns pointer success but before SQL confirmation**. Fresh-process reconciliation
  confirms the exact pointer/key/fence/directory evidence; a repeat makes zero
  Google calls. This proves loss of the application's acknowledgment, not an
  in-flight network cut that happened to succeed remotely.
* A separate Viewer-grant interruption submits the first grant, holds the response
  unread for one second, and exits. Fresh external ACL/pointer readback records the
  actual resulting permissions. Its publication_pending claim remains unresolved;
  blind retry and private reclaim remain blocked. No permission replay or repair
  is attempted. See the retained readback JSON for exact observed ACLs.

Intentional exit markers requested codes 88/89; the shell runner reported exit 1
for those interrupted processes. They are recorded as deliberate interruptions,
not clean process passes or observed runner exit codes 88/89. The original pointer
readback assertion failure is retained distinctly from the safe blocked outcome.

### Representative performance measured with normal settings

The accepted SQL publication path supplied 5,806 synthetic B0-eligible players and
ten fight-period publications, across two synthetic kingdoms/camps. All ten selected
publications contain 5,806 player results. This is a representative row/period load,
not the real B0 workbook's 36-kingdom distribution or a mixed aggregate-report case.
Independent aggregate/overall reports remain honestly not_received. No fight sum
was presented as an authoritative aggregate. Daily SCANORDER remains separate.

The run used the unchanged **9,000,000 cells per part**, **500 rows per data write**,
and **2.1-second service-account pacing**, followed by full provider value readback
before Viewer publication and index confirmation. There were 17,831,186 logical
data cells and 17,831,355 physical cells including repeated headers and directory,
split across two output files. These are measured/planned generation counts, not
an assertion that all cells contain nonempty values.

| Measurement | Actual result |
|---|---|
| Run UTC | `2026-09-12T15:27:06.420046+00:00` to `2026-09-12T16:07:01.192365+00:00` |
| Generation loading | 92.281 seconds |
| Export including full readback and publication | 2248.609 seconds (37.48 minutes) |
| Export API calls (excludes initial preflight) | 991 |
| Encoded request-body bytes | 219796508 |
| Decoded response JSON bytes | 202250907 |
| HTTP error status counts | `{}` |
| Durable outcome | confirmed, export_complete; repeat identical receipt with zero Google calls |

Response JSON bytes are decoded application measurements, not compressed wire
traffic. Elapsed time includes the actual default pacing and provider/network time.
The operator specified two or three exports daily with no fixed maximum duration;
no invented timing threshold or claim of optimal performance is applied.

| Actual export method | Calls |
|---|---|
| `drive.files.get` | 110 |
| `drive.files.update` | 5 |
| `drive.permissions.create` | 3 |
| `sheets.spreadsheets.batchUpdate` | 2 |
| `sheets.spreadsheets.get` | 16 |
| `sheets.spreadsheets.values.batchGet` | 368 |
| `sheets.spreadsheets.values.get` | 9 |
| `sheets.spreadsheets.values.update` | 478 |

### Dedicated benchmark output manifest and retained state

These additional seven synthetic files were created under the existing S6 output
and benchmark approvals. Initial runtime preflight verified private blank files,
Editor access and canShare. Full benchmark files 01–02 are retained unchanged by
the subsequent small operational checks. Slots 03–04 hold the independently
confirmed small acknowledgment-loss generation. Slots 05–06 hold the later
grant-interruption generation with unresolved publication. The benchmark index
therefore points to the confirmed small generation after those checks; use the
large generation's retained receipt directory URL to inspect the benchmark.

| Role | Exact Google spreadsheet ID |
|---|---|
| index | `1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY` |
| slot01 | `1_idQ1VTjlkY7AuTehXde783k7OZfwqm4GjvBOb9nkZU` |
| slot02 | `1CkgvVGNN-UUBfM0rCVxmHoDbWK_5nfDU7R63j2EYP6g` |
| slot03 | `1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU` |
| slot04 | `1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU` |
| slot05 | `1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ` |
| slot06 | `1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk` |

Large-generation receipt (exact): `{"delivery_state": "confirmed", "diagnostic": null, "export_complete": true, "receipt": "{\"export_key\":\"eca93ecc70fe04cb836a483fafb65fa17cd0a990730d4ca77e5d55667557b9ea\",\"publication_id\":\"390dd712-10c4-5cc3-befd-7dbb067e300c\",\"selection_version\":1,\"export_complete\":true,\"remote_id\":\"https://docs.google.com/spreadsheets/d/1_idQ1VTjlkY7AuTehXde783k7OZfwqm4GjvBOb9nkZU/edit#gid=2036238961\",\"phase\":\"published\",\"audience\":\"public_viewer\",\"attempt_slots\":[\"1_idQ1VTjlkY7AuTehXde783k7OZfwqm4GjvBOb9nkZU\",\"1CkgvVGNN-UUBfM0rCVxmHoDbWK_5nfDU7R63j2EYP6g\",\"1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU\",\"1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU\",\"1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ\",\"1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk\"]}", "setup_required": null, "sql_selected": true}`

### Acceptance gates and rollback boundary

| Gate | Status and evidence | Remaining operator-owned decision |
|---|---|---|
| S6-OPS01 | OPEN: real private-write interruption/recovery/quarantine, successful-pointer acknowledgment-loss reconciliation and grant uncertainty readback recorded | Accept precise measured evidence; decide exact handling of retained publication_pending claims. Do not blind-retry, reclaim or erase them. |
| S6-PERF01 | OPEN: approved 5,806 × ten-period normal-budget full-readback measurement completed under operator-attested importer idleness | Accept measured duration/cadence and representative-profile limits; establish verified scheduling/exclusivity or separately approved shared control. Static review found no common lock across all three consumers. |
| S6-CAP01 | OPEN: real multipart publication/ACL checks, retained-slot refusal and receipt-size fail-closed checks recorded | Accept retention horizon, correction/quarantine allowance and provisioned-slot budget; unresolved files remain occupied evidence, not reusable capacity. |

The original final/interim contracts remain: B0 eligibility, exact endpoint IDs,
UTC scan start, semantic re-export deduplication, interim 11−10 then 12−10, final
13−10 and authorized EndScanID 14 permitting replacement 14−10 without another
correction command. Accepted preceding slices and S5B-REC01 remain closed. No
G5 acceptance is inferred from rehearsal execution. Live G4 exact operations and
G5 acceptance remain operator-owned; production activation is not authorized.

Rollback readiness here means preserving disabled routing, original files and
receipts, all uncertain/quarantined outputs, and the isolated disposable database.
No destructive cleanup, live rollback or activation action was executed.

### Canonical validation, carry-forward and exact evidence manifest

This appendix supplements canonical delivery sections 1–11 and earlier dated
evidence; prior blockers and failures are historical records, not current claims.
The exact eighteen Git paths remain the required delivery manifest: sixteen
existing Markdown files plus both deleted rename sources, with an empty index.
All pre-existing closeout work and untracked archives must accompany the eventual
separately authorized S6 PR; no Files changed verification against a PR is possible
because no PR exists. The three carried archived delivery/starter documents remain
byte-for-byte unchanged. Final local path/link/hash verification is recorded in
documentation-validation.json after this update.

Tracked-source tests are not rerun for this Markdown-only update. Architecture,
deferred-item, security-routing, test-selection and whitespace checks are recorded
separately. Earlier pre-commit environment/cache limitations and historical README
trailing spaces remain qualified; no blanket pre-commit or gitleaks pass is claimed.
Security routing remains the documented documentation-only skip: exact Bot
working-tree eighteen-path delta against 85f303f6, separate SQL empty delta against
44afa315. No new Changes review is claimed for temporary harnesses. Any separately
required review must use Changes at separate exact repo targets, Deep off; no
standard/deep scan or automatic task was started.

Evidence directory: `C:/Users/cwatt/AppData/Local/Temp/k98-s6-rehearsal-x8tpc14d`.
Artifacts below are local evidence, not committed data. Retain them for operator
acceptance; temporary storage is not a durable external archive.

| Result artifact | Actual status | Wall seconds | API calls | SHA-256 |
|---|---|---|---|---|
| `sdk-preflight-results.json` | failed | None | 0 | `e95b26f5867247350f07ef6c2ff2afa25d70befc45033bdb99d1ca6b1a91b5e3` |
| `sdk-preflight-restored-results.json` | passed | 62.692 | 27 | `056f413efcf9779f6e7fb814b8d9a246ad6f59fce99a9baadd4166b3f2fc3cc7` |
| `provider-private_interrupt.json` | process_exit_after_request_body_sent | 67.452 | 33 | `d0f79b7bbe3507a919a4c6bf281fb5270f2e8d7d260e6e7cd322aa595581e0db` |
| `provider-private_readback.json` | passed | 40.762 | 20 | `87794272a267676f4d1e384cf05a36ddcb9870659c2a2416bf66d8cd1226a158` |
| `provider-private_recover.json` | passed | 181.493 | 87 | `2fbe2c65f0c547b9ba86db0d90dcd755a57badb8b2ba5bd9301027941fc182e3` |
| `provider-quarantine_audit.json` | passed | 36.483 | 18 | `2bb7c23be548ce38fea1277d8c45a4cf0518c9987c10a0f1b8bbe2afe0f46aa0` |
| `provider-confirmed_repeat.json` | passed | 0.202 | 0 | `414442b4f63d187d9bba88690dfce4a247bc0e5981f368a5b76db2e612680a30` |
| `provider-receipt_capacity.json` | passed | 0.173 | 0 | `7d57b9e391a4f742c26016c0186c067cee3709c2e7ee65069304063060a0ef3b` |
| `provider-insufficient_slots.json` | passed | 7.137 | 4 | `27a05211d2113d071246b48a1ba0bfa2814dbdd95b1a18c7bc36d8cd04bc2179` |
| `provider-pointer_interrupt.json` | process_exit_after_request_body_sent | 189.391 | 84 | `bd2b272bbcce4912786307d608479d1bb8030918e117fe94d959a046c3d41952` |
| `provider-pointer_readback.json` | failed | None | 26 | `be2df5ccfdc28ed4d0d1dbbc8c5dfef7e96041bebd98c55b3d3d03c8b3a69757` |
| `benchmark-plan.json` | prepared | 384.769 | 0 | `80f063bc02c9e81c1f94ada693144899df105458f28461ab8cf8e39127182c37` |
| `benchmark-results.json` | passed | 2394.772 | 1012 | `3587bbafc0bc145744c79ff03cb51e119915ad373ec3dd428385051880615e7b` |
| `benchmark-ops/provider-pointer_interrupt.json` | process_exit_after_google_success_before_sql_confirmation | 175.194 | 84 | `cd4564f160011a516b373048ad6d13ec2756ef1431e1a3ab15bac09367b79833` |
| `benchmark-ops/provider-pointer_readback.json` | passed | 72.031 | 35 | `4584425b6995f81788a2f2ca4947d3033f9683e1ffcd0f5c5b73e3f6a1de6752` |
| `benchmark-ops/provider-pointer_repeat.json` | passed | 0.118 | 0 | `c0519e4c8b4bde982a35e9dd34993a0d9d6919da38cfeeff6e7bee878499e393` |
| `benchmark-ops/provider-grant_interrupt.json` | process_exit_after_request_body_sent | 167.528 | 80 | `be447d3ce3eef8740c402957b948ebb72cced27b2a8d1dbbab863de6834bb82c` |
| `benchmark-ops/provider-grant_readback.json` | passed | 50.941 | 25 | `adabc4e3d5b404e5bc4ef755e66e2c783b581e301c680f75bd507763b4bfe553` |

### Exact interruption readback identities


`provider-pointer_readback.json`:

```json
{
  "index": "19jOzLAnEildMoxEQNqLsnkcB8tPo0w9Kym5_cbLof_g",
  "key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
  "slots": [
    "1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg",
    "1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0"
  ],
  "claim_before": {
    "state": "claimed",
    "fence": 4,
    "owner": "bca05d8c-2fa1-43b2-a036-9905e45150f0",
    "receipt": {
      "export_key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "publication_id": "e19c89ac-7977-5f28-ae4c-031807cd1728",
      "selection_version": 5,
      "quarantined_slots": [
        "1eWty-3Zr4RGfpA4eqpSTiVSNYZwrzUiXbG0kQ7yybMU",
        "1oMIBoMqDp5od5hwEoAqlsvs8kK7svCsYcd0VEHb8Oxw"
      ],
      "phase": "publication_pending",
      "export_complete": true,
      "attempt_slots": [
        "1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg",
        "1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0"
      ],
      "audience": "public_viewer"
    }
  },
  "reconcile": {
    "state": "claimed",
    "fence": 4,
    "owner": "bca05d8c-2fa1-43b2-a036-9905e45150f0",
    "receipt": {
      "export_key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "publication_id": "e19c89ac-7977-5f28-ae4c-031807cd1728",
      "selection_version": 5,
      "quarantined_slots": [
        "1eWty-3Zr4RGfpA4eqpSTiVSNYZwrzUiXbG0kQ7yybMU",
        "1oMIBoMqDp5od5hwEoAqlsvs8kK7svCsYcd0VEHb8Oxw"
      ],
      "phase": "publication_pending",
      "export_complete": true,
      "attempt_slots": [
        "1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg",
        "1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0"
      ],
      "audience": "public_viewer"
    }
  },
  "index_values": [
    [
      "78792a5a9782b69ca430cc3a5deeecf5a8e8ff7090dd547cbe533d229c589d56",
      "2",
      "https://docs.google.com/spreadsheets/d/1LeoZ5bySHbGTAyNUGNiKyUiG9zqn56eRvD-CTQvH7RI/edit#gid=1761925453"
    ]
  ],
  "blind_retry_blocked": true,
  "private_reclaim_blocked": true,
  "observed_permissions": [
    {
      "id": "19jOzLAnEildMoxEQNqLsnkcB8tPo0w9Kym5_cbLof_g",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1AdfEMfuNFciqbe0tJ3f5W9vjRFDs-t5lKFOpp1oTzBg",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1FKTFrya6rho4fBS10VdmZ8SsBW9OCo_OyU8Y0SgIwn0",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    }
  ]
}
```

`benchmark-ops/provider-pointer_readback.json`:

```json
{
  "index": "1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY",
  "key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
  "slots": [
    "1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU",
    "1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU"
  ],
  "claim_before": {
    "state": "claimed",
    "fence": 2,
    "owner": "11e75cb1-3ec1-4371-bcab-73d5898ed90b",
    "receipt": {
      "export_key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "publication_id": "e19c89ac-7977-5f28-ae4c-031807cd1728",
      "selection_version": 5,
      "phase": "publication_pending",
      "export_complete": true,
      "attempt_slots": [
        "1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU",
        "1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU"
      ],
      "audience": "public_viewer"
    }
  },
  "reconcile": {
    "state": "confirmed",
    "fence": 2,
    "owner": "11e75cb1-3ec1-4371-bcab-73d5898ed90b",
    "receipt": {
      "export_key": "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "publication_id": "e19c89ac-7977-5f28-ae4c-031807cd1728",
      "selection_version": 5,
      "export_complete": true,
      "remote_id": "https://docs.google.com/spreadsheets/d/1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU/edit#gid=1773447482",
      "phase": "published",
      "attempt_slots": [
        "1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU",
        "1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU"
      ],
      "audience": "public_viewer"
    }
  },
  "index_values": [
    [
      "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "2",
      "https://docs.google.com/spreadsheets/d/1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU/edit#gid=1773447482"
    ]
  ],
  "blind_retry_blocked": true,
  "private_reclaim_blocked": true,
  "observed_permissions": [
    {
      "id": "1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1slQmOxCKSQNjbMMwYSKEibPrhdicqiqoi9Y10ZVoBWU",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    }
  ]
}
```

`benchmark-ops/provider-grant_readback.json`:

```json
{
  "index": "1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY",
  "key": "c19df611173a42517f45c61fdc76693d1f363187b1ea83bc3677de3966b7d85c",
  "slots": [
    "1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ",
    "1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk"
  ],
  "claim_before": {
    "state": "claimed",
    "fence": 3,
    "owner": "487a17d9-c64d-4116-9274-143ddffbabb1",
    "receipt": {
      "export_key": "c19df611173a42517f45c61fdc76693d1f363187b1ea83bc3677de3966b7d85c",
      "publication_id": "54a2480a-26fb-5bad-a3f5-9321525a731c",
      "selection_version": 1,
      "phase": "publication_pending",
      "export_complete": true,
      "attempt_slots": [
        "1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ",
        "1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk"
      ],
      "audience": "public_viewer"
    }
  },
  "reconcile": {
    "state": "claimed",
    "fence": 3,
    "owner": "487a17d9-c64d-4116-9274-143ddffbabb1",
    "receipt": {
      "export_key": "c19df611173a42517f45c61fdc76693d1f363187b1ea83bc3677de3966b7d85c",
      "publication_id": "54a2480a-26fb-5bad-a3f5-9321525a731c",
      "selection_version": 1,
      "phase": "publication_pending",
      "export_complete": true,
      "attempt_slots": [
        "1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ",
        "1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk"
      ],
      "audience": "public_viewer"
    }
  },
  "index_values": [
    [
      "e1935194df0d82d5d1a879ea63ebdfb3a6ea54b92844be71b691d77ef4266c1a",
      "2",
      "https://docs.google.com/spreadsheets/d/1QCQdofh1Zcc3DaSBtg5rACbHB4bdDvDguRicfX1PRoU/edit#gid=1773447482"
    ]
  ],
  "blind_retry_blocked": true,
  "private_reclaim_blocked": true,
  "observed_permissions": [
    {
      "id": "1NNYBHJ4QOG0xNroZA40F35yz59ygDIxal-cXTTp6bCY",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1QBJp5bi0CG7i6VwiqSJ1KuVGOsjNEQVl1uE9sOE2TMQ",
      "permissions": [
        {
          "type": "anyone",
          "role": "reader"
        },
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    },
    {
      "id": "1psx350bk4fu_JAfXarfSLj2PojfpqO3CoFkazBI8Ddk",
      "permissions": [
        {
          "type": "user",
          "role": "owner"
        },
        {
          "type": "user",
          "role": "writer"
        }
      ]
    }
  ]
}
```

| Additional exact artifact | SHA-256 |
|---|---|
| `local_rehearsal.py` | `5982c3bd0c81b2e57edab75f003c12cee08c9b149f267cda9e5641a91d9c5acb` |
| `local-results.json` | `1be09acac6cdf679377a3994c7db4adb3e09a32bed5e601141022fdf355ba7ba` |
| `provider_ops.py` | `024042a7326dd52a20e029300cdcd67da2e5d3b8e038a1c940c1f02742f78fb4` |
| `provider_followups.py` | `3e0ebe1ff201ee86e0a500d503261cff60c857395d2d30e15336b744d75e65eb` |
| `provider-plan.json` | `0d9beb3c2d8468493aaa440f5dfdbd6602462557f32185e50c61bf011df0e05d` |
| `benchmark_setup.py` | `7e3c752531519e1c00bd753694f029bb2497d71fad29296e0e3397071b50f161` |
| `benchmark_run.py` | `ebe84bad8a1dd3cdf35ad4b1ece6dde27af2b549d151324d8204d286fc1d7502` |
| `benchmark_operational_followups.py` | `2c1c4af4334699b99603a33368556f21a2643f1ef7c0de6b529a6bfd99d8f885` |
| `benchmark-output-ids.json` | `b7d62f7be4937a7478ba0ce57e0e6ec0e5bb09f55d8b3fc7df91732e5aa80483` |
| `benchmark-output-metadata.json` | `f2f49b7b1c90a7eb56487ba88ee071a2796c7f6afbdccf43253c12bdd080efbe` |
| `benchmark-request-estimate.json` | `bee223dd1ca04c7f9d5c90a57d6db5eed07fbe2e7e727348f327bf800ae24c9d` |
| `runtime-summary.json` | `ca3866531e21cf29ee47d377b8fea667cc2657b635c30fcc26205846da161222` |

### Final authenticated-rehearsal documentation validation

After recording the actual runtime outcomes, architecture validation passed
(0 changed Python files), deferred-item validation passed (16 Markdown files),
security-routing validation passed (0 errors/warnings), and git diff --check passed.
Exact-path test selection passed; its generic smoke-import and command-registration
recommendations are skipped because runtime source/registration are unchanged and
no PR is being handed off. No predecessor tests or production smoke were rerun.
The complete 18-path manifest, empty Git index, all original evidence-entry bytes,
three unchanged carried archive documents and both rename deletions were verified.
All 174 local links and 13 fragments resolved. Bot/SQL main and origin/main remain
at the entry anchors; remotes were rechecked, SQL status is clean, and bot changes
are exactly the preserved documentation manifest. Local production/main is still
c7e063f02ebe8287a584d0054ea14f91a0c0ecc6. No remote fetch was performed.

All required source workbooks are present according to the retained read-only
inventory; the restored credential now authenticates. No additional workbook or
credential creation is required for this completed rehearsal. S6-OPS01, S6-PERF01
and S6-CAP01 remain OPEN with the precise acceptance gaps above. No production G4
action, G5 acceptance, PR or activation is claimed.

## 2026-09-12 operator approval of completed rehearsal evidence

Chris Watts approved proceeding after the completed rehearsal report. Record this
as acceptance of the measured synthetic results, including the 37m 29s full export
and verification, successful private recovery and pointer acknowledgment-loss
reconciliation, and safe blocking of the two uncertain publications. Earlier
statements awaiting acceptance of those measured results are historical.

This approval supplies no new scheduling window, shared-consumer control, retention
horizon, correction/quarantine allowance or exact recovery operation for uncertain
publications. Those facts must not be invented or marked implemented. S6-OPS01,
S6-PERF01 and S6-CAP01 therefore retain their open operational components, with
the measured rehearsal evidence now operator accepted. Full release G5 acceptance
and production G4 execution are not inferred.

The concrete next proposed action is a documentation-only mirror branch
`codex/kvk-source-migration-s6-release-evidence`, exact eighteen-path commit and
push to `origin` (`cwatts6/K98-bot-mirror`), and a draft PR into `main` titled
"Document KVK S6 rehearsal evidence and release gates". Include all pending
closeout documentation, both S5B rename sides and untracked archive files. After
creation, verify the PR Files changed against the complete manifest; do not merge
or promote. This is a prepared proposal, not a claim that a branch/commit/PR exists.
The earlier explicit no-push/no-PR restriction makes clarification of this exact
external step necessary; rehearsal acceptance alone does not identify it.

Validation at approval entry reconfirmed both repository HEADs/remotes/status,
all eighteen Git paths, empty index, clean SQL tree, preserved original document
bytes, 174 local links and 13 fragments. This update changes documentation only;
the existing runtime-test and separate-repository security skip decisions remain
applicable. No SQL, Google, Discord, Git publication or production action is part
of this approval record. Preserve all disposable databases and retained outputs.

## PR 272 review correction — missing public routing consumer

Review comment 3996906362 is valid. At reviewed bot commit
`758d6be163026f0299c05c3ad0bf2c4517c55932`, routing-row access in
`kvk/dal/new_source_config_dal.py:13–28` and
`kvk/dal/new_source_admin_dal.py:494–498` provides locking/onboarding, not public
read dispatch. `stats_alerts/embeds/kvk.py:154–185` selects V2 only with explicit
diagnostic source_selection; ordinary requests retain the legacy path.

A successful SourceRouting.Enabled update alone cannot activate public V2 readers.
The readiness sequence and transaction preconditions now explicitly stop until a
separately approved, reviewed, deployed and accepted routing consumer covers all
intended public readers. Require ordinary-request enable/disable behavior, pinned
routing/selection versions, unavailable/stale/capability handling, cache/restart
behavior and rollback tests bound to the deployed consumer revision. This is an
implementation gap, not merely missing deployment evidence or an activation helper.
No runtime implementation is included or authorized by this documentation correction.
S6-OPS01/PERF01/CAP01 and all retained uncertainty remain as previously recorded;
this additional prerequisite cannot be discharged by their synthetic measurements.

Copilot reviewed 16/16 files and generated no inline comments, but requested final
human review of the large evidence record. That requirement remains: operator
rehearsal acceptance is recorded, while independent remote reviewers cannot verify
local disposable databases, runtime JSON artifacts or every historical claim from
the PR alone. Hashes identify retained artifacts; they do not substitute for access
and inspection. No independent review or full release acceptance is invented.

Validation for this correction: Markdown-only; no runtime tests or predecessor
rehearsals rerun. Recheck local links, the complete 18-path PR manifest, staged
whitespace, architecture/deferred/security-routing and staged secrets. Security
routing remains documentation-only skip for the exact Bot review-fix diff; SQL
remains unchanged at 44afa315dd6cbfe9fec101f2a39a62e534f5b583. No activation,
merge, production promotion, SQL execution or Google operation is performed.


## S10E repository closeout and S11 preparation boundary — 2026-09-15

S10E mirror #280 / production #587 / SQL #88 are merged and locally synchronized. The operator
confirms no bot-machine pull. Final offline suite: 4,664 passed / 71 skipped; Changes review and CI
passed. This is source/repository delivery, not installation, runtime deployment, provider proof,
activation or G5 acceptance. [Exact closeout and carry-forward manifest](s10e_closeout_and_s11_handoff.md).

S11 begins review/scope from the approved eight-document release proposal. Reconcile disabled
composition, trusted termination/reconciliation/retirement-recovery producers, compatible shared
writers and S10C/D/E SQL installation evidence before proposing exact G4 operations. No predecessor
rerun or use of retained S6/S8 data as disposable targets. Keep OPS01/PERF01/CAP01 and both uncertain
publications open; do not infer runtime truth from static SQL, merged commits or fake-client tests.

Release rollback stops admission and drains/reconciles owned work. Preserve sealed inputs, receipt
bytes, history, old/nested-owner evidence and uncertain claims; forward-fix installed SQL. Only an
explicit target/operation approval permits any provider/Discord/SQL or bot-machine action.

### S11 PR review corrections — 2026-09-25

Bot mirror PR #281 and SQL PR #89 remain separate source deliveries. The review delta
preserves independent read-only calendar/display Sheets access while inherited export
contexts and recorded authority failures cannot fall back to legacy credentials. Provider
child accept and hello each have a 30-second deadline and observe the retained process
handle. Timeout/exit cancels and drains pending IPC; authority startup failure retains the
SQL claim, terminates the owned child and returns control for reconciliation. Provider
HTTP/authentication timeouts are unchanged after the authenticated handshake.

SQL first installation rejects either pre-existing evidence-role name before installation
DDL; exact-schema reapplication preserves subsequently authorized G4 memberships. Session
closure rejects incomplete enrollment preparations, including the interval between closed
provider phases. Enrollment admission locks the session until its transaction completes.
The authoritative procedure snapshots and both migration body copies agree.

Correction validation: 632 focused offline tests passed, 10 live-only cases skipped;
operational logs remained byte/metadata unchanged. Black/Ruff, architecture, deferred-item,
security-routing, test-selection, command-registration and smoke-import checks passed.
SQL static checks passed 188 assertions and ScriptDom parsed the three changed SQL files
without errors. The selector recommends full pytest for the entire branch; the earlier
5,812-pass full run is retained historical evidence, with the correction's 632-case run
covering the changed boundaries, composition, snapshots and event-data caller. It is not
represented as a new full-suite run. Separate Changes reviews use the published Bot
`c3e9fc37391c690f0c9303b6e6f3056947cc36a4` and SQL
`c106867fe8278b9d1d341a77a0b6f5b71ce94de6` as correction baselines, Deep off.

The authored SQL tests now reject session closure before an enrollment's first stream and
between closed phases. SQL installation/reapplication, effective role membership, concurrent
transaction behavior and native child-failure timing are still unexecuted G4 gates. No
provider/Discord operations, deployment, activation, merge, predecessor rerun or G5
acceptance is implied by resolving these source-review threads. All retained S6/S8 evidence,
uncertain publications, pending-document/archive identities and rollback obligations stand.

### S11 additional PR review corrections — 2026-09-25

PR #281 now waits up to one overall 30-second deadline to acquire the authority pipe.
Busy instances, the race after availability, and the gap between server instances are
handled before authentication or action transmission. Access errors still fail immediately;
connected sends/replies are never retried. The shared provider-child connection helper keeps
the existing exact pipe rights, message mode, server authentication and cleanup obligations.
Timeout or uncertain delivery still retains claims for reconciliation.

SQL PR #89 rejects closing a frozen stream while any registered request lacks a terminal
`succeeded`, `not_sent` or `unknown` event. Legal terminal appends remain possible while
frozen. `unknown` remains insufficient for reconciliation proof. The authoritative snapshot
and both migration copies match. All 14 permission-manifest source paths use forward slashes;
LF checkout is pinned and all three exact manifest-hash references are synchronized.

Validation: 681 focused offline tests passed, 12 live-only cases skipped, with operational
logs unchanged. Tests cover busy/raced acquisition, instance turnover, one overall deadline,
fail-fast errors and no connected-action replay. Black/Ruff and all six repository gates
passed. SQL checks passed 193 evidence and 454 permission assertions; ScriptDom parsed all
five changed SQL files. The whole-branch test selector still recommends full pytest; its
earlier full-suite evidence remains historical. This correction uses focused affected-path
coverage and does not rerun predecessors. Separate Changes reviews, Deep off, target the
Bot delta from `771be9b45f3e6eb67b224a941e31b55cf5579a7d` and the SQL delta from
`70d1916c39359c4bf5cf990552c3b1e57850b2c4`.

The authored, gated SQL case now checks rejection without row/event changes for prepared
and dispatch-intent requests, then legal terminal append and closure for each terminal
state. It has not run against SQL. Native two-caller contention, exact installation/reapply,
concurrent SQL transactions, provider/deployment proof and G4/G5 acceptance remain operator
gates. Rollback closes admission, drains/reconciles and retains evidence and uncertain claims;
installed SQL is forward-fixed. No provider/Discord/SQL execution, merge, bot-machine change
or activation occurred. Prior document grouping and every retained S6/S8 obligation stand.
