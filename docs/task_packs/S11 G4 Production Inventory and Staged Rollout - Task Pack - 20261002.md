# S11 G4 — bounded production inventory and staged rollout preparation

## Current mandate

Chris accepted and closed the local implementation review and approved **bounded production inventory and staged rollout preparation** on 2026-10-02. Read the [current handoff](../reference/kvk_source_migration/s11_g4_production_inventory_handoff_20261002.md) first. Carry that approval forward without another general approval cycle.

Complete the authorized read-only inventory and prepare the next concrete merge/install/deployment decisions. No installation, enrollment/export writes, Bot restart/deployment, feature activation or G5 acceptance follows from this approval. This task pack is a local handover document; it does not create another app task automatically.

## Required reading

1. Current handoff above, then current AGENTS and the core documents in the [reference index](../reference/README.md).
2. [Accepted operator-control result](../reference/kvk_source_migration/s11_g4_operator_control_readiness_20261002.md) and [Viewer/recovery implementation](../reference/kvk_source_migration/s11_g4_coordinated_viewer_custody_amendment_20261002.md). Version 5 supersedes version 4's remote custody/exclusion burden.
3. [Decision packet](C:/Users/cwatt/Documents/Codex/s11-operator-readiness-20261002/DECISION-PACKET.md), [pool bindings](C:/Users/cwatt/Documents/Codex/s11-operator-readiness-20261002/pool-bindings.json), [final manifest](C:/Users/cwatt/Documents/Codex/s11-operator-readiness-20261002/final-manifest.json) and [reviewed source pins](C:/Users/cwatt/Documents/Codex/s11-operator-readiness-20261002/security/final-reviewed-source-pins.json).
4. [SQL repair checkpoint](../reference/kvk_source_migration/s11_g4_disposable_sql_retest_20261001.md), [overall report result](../reference/kvk_source_migration/s11_g4_overall_local_publication_20261002.md), [standalone Sheets result](../reference/kvk_source_migration/s11_g4_standalone_sheets_demo_20261002.md).
5. [Historical validation handoff](../reference/kvk_source_migration/s11_g4_validation_handoff_20260929.md), [release packet](../reference/kvk_source_migration/s11_g4_release_packet.md), [full review](../reference/kvk_source_migration/s11_g4_full_readiness_review_20261002.md), [S11 closeout](../reference/kvk_source_migration/s11_closeout_and_g4_handoff.md). Resolve dated instructions using the current handoff.
6. Authoritative SQL in `C:\K98-bot-SQL-Server`, including [delivery log](C:/K98-bot-SQL-Server/docs/SQL_DELIVERY_LOG.md), [migration order](C:/K98-bot-SQL-Server/migrations/README.md) and affected definitions. Use the [promotion guide](../reference/Promotion%20Guide.md) for sequencing only; generic reset/clean examples are prohibited here.

## Settled operation and known targets

Chris controls both machines and all export-command/import triggers. One Windows account (`single_account_application_v1`), one production Bot, no test Bot. Version 5 accepts a named operator confirmation that no conflicting work is outstanding and the other machine's triggers remain held until completion or reconciliation. No remote shutdown, service disabling, process/session inventory or fixed duration cap is required solely for competing-writer exclusion. Active deployment process identity remains a separate technical requirement. Read-only inventory needs no no-write period.

Existing service account `sheets-service@statsupdate.iam.gserviceaccount.com`, project `statsupdate` / `283272667859`, client `103175311864208640064`; sole operator-confirmed active key `0d8b70356ef2fb1ea002daac8e9533463aab5d18`, expiry 31 December 9999, copies on production and local only. Manual Sheets owner `chrislos35@gmail.com`; direct service-account Editor and link-only Viewer. No new account/key, human OAuth, key bytes, automated file creation or personal Drive substitute.

Production comparison target: MINI_AMD; SQL `mini_AMD` / `ROK_TRACKER`; retained original login `MicrosoftAccount\cwattsconsulting@outlook.com`. Bot last observed at isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`, not production/main. Task `StartDLBotAfterSQL`, retained action `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\discord_file_downloader\start-bot-after-sql.ps1"`. Verify identities and action read-only; never invoke the task. Historical successful startup/409-row upload/14 transfers do not prove S11 acceptance.

Development: `localhost\K98DEV`, canonical `9SX2VF4\K98DEV`; user `9SX2VF4\cwatt`; retained SID `S-1-5-21-3167111192-3307161013-4064290451-1001`. Protected runtime root `C:\K98-S11-Validation`; credential under `credentials\statsupdate-0d8b70356ef2.json`, SHA256 `d23b77b3acb2aa1999c73fd4fce44e04613570d83ceb1955507125672c48a609`. Never display its bytes. Preserve the agreed connection-local development TrustServerCertificate exception; do not start another certificate-trust project or silently change production TLS settings.

The five files in pool-bindings are verified blank candidates, not enrolled origins: Slot 02 is proposed index and Slots 03–06 are generation slots; all grid 0 / Sheet1 / 1000×26 as observed on 2026-10-02. No rename or additional creation is needed for measured P=1,Q=0,R=0. No repeated provider inspection merely to restamp a handoff. Enrollment later performs its own fresh exact reads. Preserve the completed demo index/report and all 11 exclusions in the binding file.

## A. Reconcile and preserve locally

Inspect both Git histories and every pending path before work. Preserve drift; compare source members individually. Do not reset, clean, stash or pull main. Bot base `2046ecdbd983450ab5098ec2a0caebfda91e41ab`; SQL base `4cd1554dc3d063e323f22350c88df1444cd0ed4b`. Local refs do not prove remote freshness.

Accepted package final-manifest SHA256 `c739b758ab37d90ff36df6110c0d85291ab4a1722e528e3a7975f5342c768c67`. Later approval/docs evidence is separate at `C:\Users\cwatt\Documents\Codex\s11-production-inventory-handoff-20261002`. Preserve old seals and their saved files. The historical accepted SQL 540-object source list used canonical digest `73c23c1391471e829c6a835be0f7371239e11d9880071c079fbfdb3c157c1555` and raw SHA256 `343e1fa220b639bd620ccb8bb789d9c3e8f183bd49bdb6020d788d606f95d3bd`; retain those seals. Keep normalized source and installed-definition hash domains distinct.

**Current source pin, 2026-10-04:** after the reviewed declaration-name correction in [mirror PR #288](https://github.com/cwatts6/K98-bot-mirror/pull/288) / [production PR #595](https://github.com/cwatts6/k98-bot/pull/595), new packets must bind canonical digest `73562d08660ee44465e6d407c065329f56af7a14369f8c8b80aac6ac87c79b02` and raw manifest SHA256 `28e8b2cac59e4415c43f853bc4f72a449ee0d6be190a91d8c0596be7e97bf398`. The two logical table names are `dbo.ID#` and `dbo.LATEST_T4&T5_KILLS`; source paths and all 540 SQL file hashes are unchanged. These pins describe the correction under review, not a claim that production has deployed it. Verify the actual deployed head before execution; preserve historical packets. See the [current checkpoint amendment](../reference/kvk_source_migration/s11_g4_pr_review_checkpoint_20261002.md#source-name-correction-amendment--2026-10-04).

## B. Prepare and run the approved read packet

Establish one exact production access route and target identity. Prefer purpose-built tooling; read computer-use instructions if UI/RDP is needed. An unavailable route is a factual blocker, not permission to improvise credentials or widen targets. Continue independent local preparation while resolving it.

Before each operation, retain separate sealed and working command copies with SHA256, exact allowlisted paths/objects and identities, expected effects, budgets, evidence format, stop conditions and recovery boundaries. Announce grouped reads and execute under existing approval. Ask only for missing access facts or a materially broader target/effect, not routine reapproval.

Permitted finite read groups:

- Deployed Bot commit/local changes and exact relevant source/config/dependency hashes; secret values excluded.
- Named startup action/settings and relevant path ACL/reparse metadata; no recursive machine crawl or task/service invocation. This is deployment inventory, not the rejected writer-exclusion audit.
- Exact SQL target/login/visibility, named affected objects/columns/constraints, migration receipts, public certificate/signature metadata and relevant grants/roles. Identify full-application prerequisites beyond the minimal export set. No data census, DBCC, plans or memory/performance collector.

Default ceilings per operation: 60 seconds total, SQL connect 5 seconds / statement 15 seconds / lock wait 1 second, at most 1,000 metadata rows per query and 20 MiB output. Lower where practical; implement and verify actual guards. Stop on foreign identity, unavailable/opaque metadata, timeout, bounds or uncertainty; retain partial evidence and reconcile before any revised attempt. No grant/configuration change, provisioning, backup/restore, import/export or provider mutation. Never run the withdrawn collector/helper or a replacement broad collector.

An administrator observer's rights are not proof of the restricted application principal's rights. Reviewed source defines expected metadata; sampled runtime metadata must not approve itself.

## C. Prepare staged rollout and rollback

Produce a source-versus-installed comparison and minimum missing-only prerequisites. Do not install every source object. October 1 corrected 001–006 replace their named September entrypoints; 007–010 apply only where predecessor guards match. `20260924_002_export_legacy_module_permissions.sql` separately requires exact deployment/signature rows and matching public certificate prerequisites in ROK_TRACKER/Import/master. Do not invent signing material.

Prepare distinct later operations for SQL installation/permissions, source publication/promotion, protected deployment, actual process/pipe/typed records, manual enrollment, coordinated exports/reuse/recovery, S6/S8/G5 acceptance and activation. Each needs exact commands/hashes once inputs are known, transaction boundaries, request/row/byte/cell/lock/log/storage/time budgets, stop conditions and readbacks. Unknown inputs stay visibly unresolved and nonexecutable. The old standalone demo budget is not a substitute for a new authority-run budget.

Keep admission closed. Before installation rollback means no change. Afterwards settle exact owned work and preserve uncertainty before considering a compatible fallback. Do not restore over retained databases, clear outputs or reenable an old writer whose compatibility is unproved. A reviewed forward correction may be required.

## D. Preserve the existing publication checkpoint

[Bot PR #284](https://github.com/cwatts6/K98-bot-mirror/pull/284) and [SQL PR #91](https://github.com/cwatts6/K98-bot-SQL-Server/pull/91) were explicitly authorized as ready for review and must remain unmerged. Follow the [PR review checkpoint](../reference/kvk_source_migration/s11_g4_pr_review_checkpoint_20261002.md) and final publication evidence. Reconcile their exact heads, reviews and path/content manifests; do not create duplicates or reinterpret publication as rollout approval. Inventory proceeds independently. The new SQL fail-closed selection guard requires exact migration selection and rejects superseded IDs; it does not establish production prerequisites.

Carry all implementation/recovered documents and archive identities forward. Exclude credentials/private artifacts deliberately. Do not mix histories or push mirror history into production. Later promotion uses the documented patch-based flow and a separate merge/deployment decision.

## Evidence, protections and exit criteria

Every actual read records operation/command/input hashes, targets, UTC start/end, elapsed time, counts/bytes, exit where applicable, redacted observations and result/stop classification. Return installation/configuration differences, source-backed prerequisites, staged commands where possible and genuinely missing facts or decisions. Do not claim future process identities, seven complete typed proofs, installation/provider/G5 acceptance from fixtures or historical receipts.

Preserve DB22 `S11_G4_Recovery_20260928_97337` ONLINE/RESTRICTED_USER/read-only/Broker-disabled and 119 media; DB23 `K98_S11_Disposable_20260929_CV01`; DB24 `ROK_TRACKER`; all files/receipts. Actual historical restore and 15-table/2,410,159-row baseline remain evidenced, with 352 tables outside scope. Retain B02 timeout and B04R1/B05 command-provenance qualifications; no rerun or writable flip.

Preserve uncertain publications `e19c89ac-7977-5f28-ae4c-031807cd1728` and `54a2480a-26fb-5bad-a3f5-9321525a731c`. September 12 measured S6 results were already accepted; remaining capacity/retention/uncertainty handling and S8/G5 operational gates stay open. Memory investigation/withdrawn helper remain deferred; empty KVK report and view-rehydration warning remain separate.

Accepted focused tests: 644 passed, one skipped; subsequent full offline suite: 6,124 passed, 65 skipped, 8 subtests passed (see PR checkpoint for later formatting/review qualification). Bot Changes scan `25f11c9d-3ca6-40f2-9280-e3f4b61e7d09`: 21/21, no findings, Deep off. Preserve historical broad-suite and SQL complete/partial review qualifications. Later runtime changes need scoped test/security routing; documentation-only changes justify a skip. No routine Codebase/Deep audit or predecessor rerun.
