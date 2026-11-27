# P02 observer correction — remaining implementation handover

20 November 2026. Start here in the new chat. Local implementation remains
authorised; production is unchanged. This is a continuation, not a new design or
a reset of accepted work. The user explicitly requested that the new chat refresh
programme scope, P02 scope and this task's scope before implementation.

## 1. First actions: refresh the three levels of scope

1. Attach/reuse the existing worktrees below and verify branch, HEAD and local
   changes against the handoff inventory. Do not create a replacement checkout,
   reset, clean, discard, archive or move these worktrees or their ignored evidence.
   Use explicit working directories. The saved project may initially open at
   `C:/discord_file_downloader`; that is not this task's implementation checkout.
2. Read current `AGENTS.md`, `README-DEV.md`, `docs/reference/README.md` and the
   five required K98 standards listed by AGENTS: Project Engineering Standards,
   Coding Execution Guidelines, Testing Standards, Skills & Refactor Triggers,
   and Deferred Optimisation Framework. Read relevant SQL repo instructions too.
3. Refresh **programme scope and aim** from the programme Scope, Principles,
   Tracker and Tracing documents listed below. The aim is reliable startup,
   import/export and recovery with useful progress, correct ownership and truthful
   outcomes, without the correction adding avoidable contention or duplicate work.
4. Refresh **P02 scope** from the integrated analysis/delivery plan, D5 obligation
   reconciliation and D7 reconciliation. Preserve all 68 original requirement
   records and 73 action/policy pairs and their existing owners. Accepted P01 and
   D1–D6 evidence retains its actual scope. P02 is still open; D7 remains 1/4.
5. Refresh **this task's scope** from the observer Design, Traceability and Local
   Implementation documents. Read the current summary at the top of the latter
   before its chronological packet log. Reconcile that summary with the latest
   native receipt. Publish a concise programme/P02/task scope recap, then a finite
   delivery checklist with evidence and completion conditions. Step 1 is review
   and scope only; existing implementation authorisation then permits continuation
   without asking the user to reapprove routine local work.

Older document banners saying design-only, pending execution or testing allowance
are dated history. The later user instructions authorise local implementation and
VM proof and retire cumulative testing quotas. They do not authorise production
operations or make earlier acceptance broader than its evidence.

## 2. Existing worktrees and file inventory

Bot implementation root (B):
`C:/Users/cwatt/.codex/worktrees/p02-observer-proof/discord_file_downloader`

- Branch: `codex/p02-observer-proof`.
- Verified HEAD: `8ef8514821783c0422c4747e61c0222f7ba3c459`.
- Candidate implementation and documentation are uncommitted. Preserve all of it.

SQL implementation root (S):
`C:/Users/cwatt/.codex/worktrees/p02-observer-sql-proof/K98-bot-SQL-Server`

- Branch: `codex/p02-observer-sql-proof`.
- Freshly verified HEAD: `73b004d4a834f87fe3e559480d99dd597995fd91`.
- Earlier notes record base `b924cedd53e29dd88c0e9e7b66208b4fdc1e53ba`.
  Current HEAD is the merge of PR158, including commit
  `8a7aace75c55a6d17c9051edef9026dc25355af8`, which keeps VM memory prerequisites
  out of production deployment. Its change is deployment/docs/tests, not the
  observer's uncommitted SQL objects. Do not reset HEAD to the older note.
- Authoritative SQL reference checkout: `C:/K98-bot-SQL-Server`. Validate SQL
  assumptions there; candidate changes live in S, with their separate Git history.

Evidence root (A):
`B/.codex_artifacts/p02-observer-proof-20261119`

Handoff inventory: `A/handoff-20261120-remaining/manifest.json`. It records exact
heads, every modified/untracked source file and its absolute path/hash, retained
packet/source evidence files, and hashes for both patches and the changed-file
snapshot ZIP. `changed-files.zip` includes the current bytes of changed/untracked
Bot and SQL files; the two binary patches retain tracked diffs. These are local
recovery/review snapshots, not commits or deployment packages. Do not restore them
over later changes. Native evidence remains in its original directories.

Required programme/task documents under `B/docs/task_packs/`:

- `Startup Import Export Reliability - Scope - 2026-11-02.md`
- `Startup Import Export Reliability - Programme Principles - 2026-11-06.md`
- `Startup Import Export Reliability - Tracker - 2026-11-02.md`
- `Startup Import Export Reliability - Tracing - 2026-11-02.md`
- `Startup Import Export Reliability - P02 Integrated Analysis and Delivery Plan - 2026-11-07.md`
- `Startup Import Export Reliability - P02 D5 Obligation Reconciliation - 2026-11-11.md`
- `P02 - D7 Reconciliation and Remaining Scope - 2026-11-19.md`
- `P02 - Observer Admission Design and Qualification - 2026-11-19.md`
- `P02 - Observer Admission Traceability - 2026-11-19.md`
- `P02 - Observer Local Implementation - 2026-11-19.md`

## 3. Latest completed native stage — do not replay

Packet `20261120132838937` passed at 13:31 UTC on 20 November.

- Receipt: `A/packet-20261120132838937/receipt.json`, SHA256
  `062c8cc7ddf90d8862fa690e168c479e7920d30aab77b755a81c5bcaba9f6a14`.
- Sealed archive SHA256:
  `5b78f16b344e272f3c6518ad368b6611bdf7283b827702fa585f4d72f1f3dba7`.
- Complete 487-name application schema/permission/lifecycle comparison passed:
  10.691660 s, 134 dispatches. All independently approved expectations unchanged.
- Same-admission reuse on a different SQL-authenticated connection passed:
  2.239593 s, 29 dispatches, exactly two boundary reads, no full metadata rescan,
  borrowed transaction `(1,1)` preserved until explicit rollback.
- Whole owner: 167 dispatches, maximum execute/fetch batch 218 ms, no first
  failure, three acknowledged connection closures; dedicated login disabled.
- Cold observation SHA256:
  `0df923ed891e667a55b0c9eb61033304ecfae9fc0b33824374325784065e4ccf`.
- Reused observation SHA256:
  `5160c6b02352725c0384d96afdcc58b0aa638a65111c838ba97e9f37d67f5b03`.
- The lab grant correction committed 126 pre-existing profile grants on 62
  source-verified objects, advancing generation 1 to 127. The initial lab harness
  omitted these direct grants. Preserve failures `20261120131206690` and
  `20261120132151081`; do not weaken expected permissions or replay installation.

This proves the complete collector/comparator and reuse mechanism. The claim
binding in this proof is a read-only qualification fixture, not actual durable
producer authorisation. It does not close complete startup/producer/capture,
simultaneous engine overlap, workload OFF/ON cost, release transition or D7.

## 4. VM state, retained business work and operator access

- VM `K98-MGE-Qualification-20261029`, GUID
  `2ac1b401-7076-4965-af71-de36ee0f9f9c`; network-isolated qualification VM.
  Guest SQL server reports `MINI_AMD`; that name alone must never select a target.
  Production is not targeted. Verify VM GUID, guest and exact database identities.
- User's elevated Windows PowerShell 5.1 console owns the PowerShell Direct access;
  prior session ID `fb80997e-0146-404e-8757-aeef45f8f1a7`. Tool process lacks the
  elevated Windows token. Prepare and verify a concrete sealed packet first, then
  request only the necessary console execution, explaining that access boundary.
- Scripts: `B/scripts/Invoke-P02ObserverLab.ps1`,
  `Inspect-P02ObserverBoundary.ps1`, `Observe-P02ObserverLab.ps1`.
  `-CollectOnly` collects an exited run without SQL replay. Never issue an old
  invocation simply because its printed exit status was nonzero.
- **ROK_TRACKER lab DB12:** candidate sequence object 1221344607, create/modify
  `2026-11-20T13:14:27.063000`, bootstrap generation 1, current proven generation
  **127**. Snapshot `K98_P02Observer_RokBefore_20261120131206690` retained.
  Installation committed in packet `20261120131206690`; grants in latest packet.
- Dedicated lab login `S11_ExportApplication_P02ObserverQual`, SID
  `2ea32fb12aab4c2da242ae037c314ad9`, is disabled. Existing credentials untouched.
  Its secret is guest-only, CurrentUser DPAPI-encrypted at
  `Q:\P02Observer\20261120131206690\lab-credential.dpapi`. Do not copy/decrypt it
  into chat, source, arguments or host evidence. Current continuation demonstrates
  guest-only in-memory reuse followed by disabling the exact login.
- **D5e DB11:** `K98_P025_D5e_Cost_20261115`, sequence object 1125344265,
  create/modify `2026-11-19T20:57:41.937000`, last proven generation 270.
  Snapshot `K98_P02Observer_D5eBefore_20261119205611983` retained.
- **Two real publisher child operations have committed. Never replay them.**
  Packet `20261120095412651`: header 539, object 1285344835, generation 254,
  maintenance due 14. Packet `20261120100655925`: header 540, object 1333345006,
  generation 270, due 15. Final read passed in `20261120101623191`.
  Controlled arrival order was exercised with the observer paused between reads;
  this is not proof of simultaneous SQL-engine overlap or the full parent flow.
  The existing tied-rank nondeterminism is documented separately; business
  calculations were not changed to make two tied outputs byte-identical.
- **Small DB13:** `K98_P02Observer_20261119175737420`; mechanism, permission,
  bulk restriction, drop/recreate commit/rollback, stale refusal and reuse receipts
  are retained in A. Use original receipts for their declared scopes.
- ROK_TRACKER's 102-row history intentionally lacks production November migration
  rows. Its authenticated retained lab lineage is not a production release.
  Do not manufacture history or relax production validators to make it eligible.
- Databases are used only for this work. User permits extra DB/storage if needed,
  or retiring unneeded lab DBs after checking preservation/recovery value. Keep it
  simple; no storage operation is currently required by this handoff.

## 5. Implementation map and source/evidence dependencies

The inventory enumerates all files. Principal Bot surfaces are:

- `services/catalogue_observation_{contract,dal,batches,batch_dal,query_dal,columns_dal}.py`:
  generation envelope, complete bounded reads, combined result/token dispatches.
- `services/application_observation_{admission,fingerprint}.py` and
  `services/export_observer_contract.py`: source-selected successor, one-admission
  ownership, exact claim/config/registration binding, one-shot collect/consume,
  fresh actual-session permissions/lifecycle, historical typed proof records.
- `services/export_runtime_composition.py`, `export_execution_dal.py`,
  `export_sql_direct_permissions.py`, `export_contract_resources.py`,
  `application_maintenance_{contract,dal}.py`, `maintenance_dal.py`,
  `legacy_export_snapshot_{dal,service}.py`: affected runtime integration.
- `scripts/verify_k98_update_pair.py`, `recovery_release_seed.py`: sealed closure,
  successor contract selection and typed retained observation handling.
- Four `deploy/p02_observer_*.json` resources; new `tests/test_*observation*.py`,
  `test_catalogue_observation*.py`, `test_observer_*.py`, and changed existing
  schema/maintenance/archive tests. `tests/updater_source_assertions.py` has an
  exact candidate-to-predecessor **test-only** bridge, not deployment approval.
- SQL: sequence, three marker/read helpers, database DDL trigger, three lifecycle
  triggers, and amended `sp_ExcelOutput_ByKVK`, `usp_RunMaintenance`,
  `usp_S11ValidateStatsReportStage`; qualification files in `S/qualification/p02_observer`.
- `scripts/prepare_p02_observer_*.py`, `prove_p02_observer_*.py`,
  `continue_p02_observer_application.py` and `inspect/diagnose` scripts prepare
  one-off sealed proof stages. Old builders pin old generations/receipts and are
  not automatic resume commands. In particular, grant repair expects generation
  1 and missing grants; it is completed and cannot be rerun at generation 127.

Retained source projections in A:

- `source-plan-03`: reviewed protocol and application/legacy source closures.
  Protocol SHA256 `73be803fe432907cccee0ed86fe593e733b6d682959f4e526f6d7ec47d7a53cc`.
- `source-fingerprint-02`: complete 487-name expected metadata and permissions.
  Metadata hash `f575d6a9dfdfa74bc628d2e22e79924c4ce9cec63428321814a6f6b9d8c9994c`;
  permissions `0be05a7afb3dd97d135e3bbca1bea01dc13785caac416583a0f747656bf111b4`.
- `source-legacy-01`: independently projected successor legacy expectation;
  unissued contract template. Not live-derived acceptance authority.
- `source-migration-01`: `20261120_001_p02_catalogue_observer.sql` and profile.
  SQL SHA256 `871d8f8b4bf1ffe274ba9e66b2fe0544dbf1b049237145f012d1d8fccb3c3b9b`.
  Production candidate requires exact D4 history and an externally owned drained
  release transaction. The labelled lab installer substitutes authenticated lab
  lineage for that prerequisite only. Issuer/coordinator integration is unfinished.
- Exact supplied updater: `C:/Users/cwatt/Downloads/deployed updater.zip`, SHA256
  `693bb3bd9454e648d4ac50be8afca29e243522b89148bbc98bd9bc76e909c91e`.
  Extracted read-only evidence: `A/installed-updater/`; 14 payload members plus
  manifest authenticated. Manifest SHA256
  `aa3f06a13ed342c404e48a42b36b0e3a0f859a4607abf6f773419d3aa030a337`.
  Its code has not been executed. Exact predecessor rehearsal remains open.
- Accepted historical observations:
  `C:/Users/cwatt/.codex/worktrees/p02-private-promotion/discord_file_downloader/.codex_artifacts/p02-native-qualification/Admission-Observation-v2/received-run-01.zip`,
  SHA256 `64a8e25120771ec6ee4ce000cdc29ab9ae57ae9866f772ec2af435766c90fba0`.
  Lab-lineage verifier is `scripts/p02_restored_baseline.py` in that older
  worktree; it reauthenticates files under `C:/discord_file_downloader/.codex_artifacts/p025`.
  Inspect its exact dependencies if needed; never execute old installation code.

## 6. Remaining delivery plan and completion conditions

Maintain one finite checklist mapped to Q01–Q10 and L1–L9 in the design. Retain
the source/consumer census and all 68/73 original records. Group compatible proofs,
reuse passing evidence and only repeat for a relevant change, failure or real gap.

### A. Finish application ownership and scheduling

Review the complete startup, preparation/producer, immutable capture, next-writer
and recovery consumers. Finish bounded rescheduling/coalescing under the existing
logical request budget and physical connection/custody owner. Avoid a second full
scan when valid same-admission proof exists; expiry, changed generation/identity,
claim/config/registration drift or unknown cleanup must refuse safely. Preserve
fresh actual-entry permission/headroom checks and existing business locks.

Done when actual caller chains, not just the shared collector helper, are covered
with supported native transaction/types, truthful deferred/mismatch/unknown
outcomes, bounded useful continuation and no duplicate work. Resolve dependencies
on committed release bindings with C; do not fake production history for A.

### B. Finish real concurrency and cost qualification

Complete remaining source/sink coverage and five-role/two-order questions using
real publisher, report, maintenance, recovery and observer actors. Establish actual
simultaneous engine overlap where required; observer-paused barriers are not enough.
Finish the real post-state → full comparator → immutable capture → next writer →
fresh consumer chain and relevant deferred-index cases. Use the existing fixtures
and preserve both committed publications; any new business test must have its own
fresh identity and an explicit unresolved acceptance question.

Done when useful actors complete within existing policies with no observer-induced
refusal/deadlock/duplicate/stranded claim/false incident, and the planned balanced
OFF/ON cost evidence meets the agreed limits. The design calls for warmup plus
five balanced pairs; reuse genuinely matching evidence and do not create a new
cumulative quota. Preserve 45 s / 256-dispatch verifier ownership, 3 s safety caps,
250 ms batch target, zero-wait locks and existing producer limits. No RCSI switch,
blanket indexing, global DB tuning or raised timeout as a shortcut.

### C. Complete coordinated release, rollback and exact updater transition

Finish committed installation issuance, the three matching protected contracts,
source/manifest/registry closure and actual runner stage order. Stage pre-drain
checks → physical drain → SQL stage → matching source/policy stage → one successor
→ bounded readiness/late checks. Receipt SQL commit, source install, successor start
and readiness separately; unknown effects retain custody and stop successors.

Rehearse the exact supplied installed preparer and its reviewed tool upgrade with
external effects replaced, then the necessary Windows/VM transition cases. Cover
LF/CRLF/raw identity, transitive imports, target-supplied registry refusal, partial
replacement, interrupted stages and compatible rollback/downgrade/re-upgrade.
Never execute the host updater or production SQL for rehearsal. Rollback is a
compatible Bot/SQL/contract/tool set, not a Git reset or automatic DB restore;
after new business work or unknown effects, review forward correction.

Done when a reviewable release candidate can install, verify and recover without
replaying committed stages or selecting incompatible versions. No production
configuration currently selects this candidate; do not issue one casually.

### D. Final regression, review and scope reconciliation

Run relevant final regression and repository gates after implementation settles.
Resolve task-related failures, document unrelated ones, complete required Bot and
SQL **separate Changes reviews, Deep off**, and address findings. Use K98 security
routing before scans; never launch a whole-codebase/deep audit as routine completion.
Produce a clear delivery/evidence/rollback plan and reconcile every original owner
and new in-scope finding. Production promotion/deployment remains separately gated.

Done when local implementation and proof are complete and reviewable with explicit
limits. Do not mark P02/D7/P03/P04/provider acceptance complete from these lab gates.

## 7. Validation already done, gaps and practical tooling

- Extensive focused protocol, fingerprint, ownership, caller-selection,
  predecessor-format, maintenance, recovery-seed and archive checks passed; exact
  groups/results are in Local Implementation. Do not sum overlapping runs as a
  coverage score. Final full regression is not reported green.
- Recent gates: architecture, deferred-item and security-routing validators passed;
  static command-registration and smoke imports passed. Latest packet: 69 sealed
  files, 25 SQL grammar batches, three offline success/failure/rollback cases.
- Known test reference-format gap: SQL names manifest Git-LF versus checkout-CRLF
  and Phase 1 source-pin representation mismatch. Earlier run 19 failures; Git-blob
  export corrected one prerequisite leaving nine Phase 1 failures. Preserve the
  evidence and investigate source/representation; never silently update expected
  production pins to pass. No accepted final regression or security scan exists.
- Four temporary-path variants passed when journal fixtures used a short temp path
  outside Git. Paths inside Git are deliberately refused; long Windows paths also
  caused fixture failures. Do not change production journal policy for these.
- Python: `C:/discord_file_downloader/.venv/Scripts/python.exe` (3.11.9).
  Black multi-file CLI multiprocessing hung in this environment; in-process
  `black.format_file_contents` at line length 100/PY311 works. Ruff defaults to
  fixes: pass `--no-fix` for read-only validation. Use isolated sealed imports.
- ScriptDom:
  `C:/Program Files/Microsoft SQL Server Management Studio 22/Release/Common7/IDE/Extensions/Application/Microsoft.SqlServer.TransactSql.ScriptDom.dll`.
  Grammar helper: older private-promotion worktree `scripts/Test-P02SqlGrammar.ps1`.
  Syntax validation is not native execution proof.
- At handoff, sandboxed exec and Node launcher returned
  `CreateProcessWithLogonW failed: 32` before execution. A reviewed escalated
  read-only exec succeeded. This is a launcher failure, not a repository or SQL
  test failure, and does not provide an elevated Hyper-V token. Use the normal
  sandbox first in the new chat; handle actual tool errors proportionately.

## 8. Non-negotiable boundaries and programme status

- No cumulative testing allowance, balance, reservation, shortfall or extension
  request. Finite meaningful tests, realistic timeouts, bounded cleanup, diagnose
  hangs, and reuse valid evidence. No tests for their own sake.
- Preserve original failure receipts and later successes; never replay committed
  business work, queued work, accepted E1, or original failed E2 to obtain a clean run.
- Production unchanged. No restart, deployment, recovery action, provider probe,
  Sheets/Discord send, import/export replay or maintenance on production.
- Local lab secrets and connection policies are not production authority.
- P02 open; D7 1/4. E1 closed; E2 failed/not_applied retained; E3/E4 paused; E5 is
  the later fresh genuine normal whole flow. Retained workflow, required provider
  receipt and fresh acceptance remain with P03/P04/D7/P05 as recorded.
- Last recorded running Bot source was `3a2694f7fc61606a3758eb8bf64065209f90c7d4`;
  this is historical evidence, not a fresh production inspection. Merged source,
  installed source, standalone verifier and business acceptance are distinct.
- Preserve original historical cause uncertainty. Local reproduced contention or
  timeout mechanisms do not prove the exact old production blocker.
- No commit, push, PR, merge, production promotion or deployment was performed in
  this continuation. Keep implementation PR-sized; final review remains required.
- The old chat stops implementation when the new chat takes ownership. The new
  chat should work from this handover and current sources, not depend on automatic
  conversation memory or start competing work in the same files.
