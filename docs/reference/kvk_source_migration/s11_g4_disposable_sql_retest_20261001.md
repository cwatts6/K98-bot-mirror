# S11 G4 disposable SQL repair and retest — 2026-10-01

The isolated development installation failures are corrected and the planned SQL synthetic cases have completed across preserved, reconciled attempts. This is development SQL installation/rehearsal evidence, not provider acceptance, a real export, production readiness, or G5 acceptance.

This checkpoint supersedes earlier statements that no installation has run. It does not replace their historical receipts or source seals. The operator approved diagnosis, correction and retesting through resolution without further routine approval requests. Production remains the isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`; no Git publication, production SQL change, Bot restart/deployment, provider mutation or activation was performed in this repair.

## Target, client and recovery boundary

- Exact SQL target: `9SX2VF4\K98DEV`, disposable database `K98_S11_Disposable_20260929_CV01`, observed ID 23. Windows identity `9SX2VF4\cwatt`; integrated original SQL login `MicrosoftAccount\cwattsconsulting@outlook.com`.
- Explicitly approved development TLS exception: `Encrypt=true;TrustServerCertificate=true`. This is per-connection certificate-validation bypass, not evidence of a trusted certificate chain and not a global configuration change. The exception is not production transport evidence.
- Data: `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\K98_S11_Disposable_20260929_CV01.mdf`, fixed 128 MiB. Log: same directory, `K98_S11_Disposable_20260929_CV01_log.ldf`, fixed 64 MiB. Growth disabled; SIMPLE recovery; Broker, TRUSTWORTHY and DB_CHAINING disabled at creation. No real source import.
- Original MAIN creation, prerequisites and failed installation receipts remain under `.codex_artifacts/s11-main-execution-20261001/`. All repairs, sealed commands, per-operation approvals, failures and result receipts remain under `.codex_artifacts/s11-main-repair-20261001/`.
- Final observation at 2026-10-01T08:17:43Z retained database 22 `S11_G4_Recovery_20260928_97337` ONLINE / RESTRICTED_USER / read-only / Broker-disabled. Its 119 media files and restore/baseline receipts remain preserved. No restore/baseline rerun or writable flip occurred.
- Corrections use exact predecessor/postimage guards and short owned transactions. Unexpected state stops; no blind retry, cleanup, drop, historical-row rewrite or inferred rollback. Failed fixtures and open/uncertain sessions remain evidence. Further correction is forward-only; later database disposal needs its own decision.

## Source corrections and explicit installation order

Do not run migration filenames in date order or run both a corrected entrypoint and its replaced predecessor. On the source-derived minimal prerequisite chain, use this exact substitution order:

| Corrected entrypoint | Replaces | Correction |
|---|---|---|
| `20261001_001_legacy_export_preparation_installation.sql` | `20260914_002` | Compile dependent constraints after adding the column |
| `20261001_002_kvk_output_pool_installation.sql` | `20260915_001` | Expected metadata follows the actual appended column order |
| `20261001_003_kvk_output_operation_installation.sql` | `20260915_002` | Appended column order and dependent compilation boundaries |
| `20261001_004_export_execution_evidence_installation.sql` | `20260924_001` | Expected resource column order across the preceding installs |
| `20261001_005_manual_export_registration_installation.sql` | `20260929_001` | Explicit metadata collation and SQL Server's stored procedure header representation |
| `20261001_006_manual_public_viewer_installation.sql` | `20260929_002` | Exact stored header comparison while preserving executable CREATE OR ALTER |
| `20261001_007_manual_file_id_characters.sql` | Forward correction after 006 | Literal hyphen/underscore in Unicode JSON file IDs |
| `20261001_008_manual_file_id_constraint.sql` | Forward correction after 007 | Align trusted manual-origin CHECK with the same character rule |
| `20261001_009_manual_resource_membership_order.sql` | Forward correction after 008 | Create unclaimed resource, insert membership, then claim, inside the existing locks/transaction |
| `20261001_010_reconciliation_file_id_characters.sql` | Forward correction after 009 | Same valid file-ID class in reconciliation JSON targets |

Authoritative files are in `C:\K98-bot-SQL-Server\migrations`. All original migrations and older seals are preserved. The tested minimal prerequisites are recorded in the original MAIN operation manifest: KVK scan base, the 20260909/20260910 source prerequisites, S8 preview/apply operations and 20260914_001 shared coordination, then the substituted chain above. The 540 source objects are an application source inventory, not a mandate to install all of them into this fixture.

The three affected snapshots are manual enrollment, reconciliation proof and manual file origin. The Bot source list remains 540 entries; only those three member hashes changed from the immediate pre-repair candidate. New canonical source-list digest: `f082cd0cbf28261cddf966a954a4564d34a81a552d796707eb90dc75a6baf3cf`. Member bytes are LF-normalized UTF-8; installed procedure hashes below are UTF-16LE stored definitions. Do not mix the hash domains. Previous runtime/config packets bearing older pins require explicit regeneration/review before later use.

## Verification and qualifications

- The minimal catalog read returned all 58 expected objects, zero missing.
- V3 positive enrollment completed with three eligible origins. Expected reader/authority permissions, invalid plans, owner/version conflicts, mutation rejection and uncertainty protections were exercised. The v3 run stopped at an overly restrictive reconciliation file-ID predicate; exact retained state was read and its remaining negative/proof cases completed after correction. This is a composed result from sealed attempts, not a claim that the original batch passed uninterrupted.
- Untouched v2 synthetic identities completed the full compatibility rehearsal: 71 returned rows, 131,157 evidence bytes, 0.503 seconds. V3 remaining assertions: 19 rows, 31,391 bytes, 0.462 seconds. Both terminal result messages explicitly limit the result to SQL synthetic assertions.
- Two owned connections acknowledged lock acquisition and expected concurrent refusal; lock hold plus release was 0.01035 seconds. No DML is part of this contention check.
- Final 008/009/010 exact-postimage reapplication passed. Earlier corrected installation reapplications passed before later forward corrections. Do not replay 006/007 after 009: their exact postimage guards intentionally bind older bodies.
- Final manual procedure hash: `3ae857b51e938806feeb09b4639dd99fc61d3222dd061b6f0bdba14185dee60f`; reconciliation proof: `2686b368b10a09b430b43bda938beb373af319f66a3ac18c0b14b39e65425385`; provider append: `753b3ed4331760000218e43d6a543b4695422e41aa48264db9a4b00fdb309f12`. Manual identity CHECK is enabled and trusted. Positive v2/v3 preparations remain completed; unknown/nonterminal preparations remain preflight, as required.
- Focused offline tests: **193 passed** in 5.33 seconds using `.venv\Scripts\python.exe` across manual enrollment, public Viewer, single account and enrollment service suites. Architecture, deferred-item, security-routing and test-selection validators passed. The system Python lacked pytest; the repository environment was used, with no dependency installation.
- Test selection sees the entire inherited pending patch and recommends full pytest/smoke/command registration. Those predecessor-wide reruns are skipped for this bounded SQL correction plus mechanical source-pin update; focused tests, actual SQL cases and separate final Changes reviews provide the relevant validation. No Discord command/registration or startup code was changed by this repair.
- Retained operational qualifications: a metadata diagnostic had a duplicate alias; a retest instrumentation alias needed brackets; a local continuation generator failed before SQL dispatch. One earlier viewer-install operation was dispatched after a failed manual reapply in the same shell orchestration; its exact guard refused and its failure is retained. Subsequent operations were reconciled individually. No failed receipt is relabelled as success.

## Packet and evidence indexing

`operation-results-index.json` links every executed repair operation to its immutable command hashes, effect class, manifest hash, summary and JSONL receipt. Each stage retains separate `working` and `sealed` command copies. Commands launch only through its pinned `launch.ps1` with the corresponding `approvals/approved.json` (the older continuation uses named operation receipts). These are historical executed packets, not reusable approval.

The repair runner pins the PowerShell/client binaries and assembly identity, guards target/original login and binds the exact command hashes before dispatch. Standard repair limits: 5-second connection timeout, pooling/retry disabled, 1-second lock timeout, 30-second command timeout, 90-second operation wall bound, at most 2,000 output rows and 1 MiB evidence. Schema locks are immediate refusal. The synthetic rehearsal retains the original at-most-2,000 row-effect budget per full case packet; no provider requests or real file bytes occur. The dedicated contention packet has stricter 1-second command, 45-second wall and 64 KiB output bounds with explicit barrier/hold/release checks. Any bound, error or uncertainty yields STOP_INCOMPLETE; preserve and reconcile before continuation.

`source-pin-update.json` records immediate old/new source members. `historical-v3-member-comparison.json` compares all 19 original implementation-seal members individually; later public-Viewer/repair/document differences are not missing original implementation. `final-source-seal.json` and `final-evidence-seal.json` bind this completion separately. Earlier seals, source copies, databases, files and failure receipts remain intact.

## Remaining boundaries

No new provider verification or export was performed in this repair. Retained CV3 provider observations remain historical evidence; do not upgrade them to real two-export equivalence/reuse proof. The separately approved real two-export demonstration, complete seven typed G4 proofs, controlled production rollout and G5 operator decision remain outstanding. S6/S8 open gates, both uncertain publications, the pending shared-account amendment, memory-investigation deferral and withdrawn-collector prohibition remain unchanged. Empty-report and view-rehydration issues remain separate.

Security-review completion is recorded in the final review addendum below; no source publication is implied.

## Final Changes review addendum

Both reviews completed with Deep off and no security findings:

| Repository | Scan | Coverage | Immutable review snapshot digest |
|---|---|---|---|
| SQL | `7fc6e83f-5ef1-4b60-a772-3697b2287386` | 16/16 source files | `c9c0fba5820e5d7acd9fea2525961e72aa7d4e24d6d571089fad69726977d586` |
| Bot | `f8bb206f-156e-4587-9c69-7c1dbfbf915b` | 10/10 source files | `a05880aeb0cecd2ad74ec162234a583d296377389b0b6c68356429b61ab91183` |

Reports: [SQL](C:/Users/cwatt/.codex/state/plugins/codex-security/scans/K98-bot-SQL-Server/4cd1554dc3d063e323f22350c88df1444cd0ed4b_20261001T081713Z_pu4_a5fm/report.md), [Bot](C:/Users/cwatt/.codex/state/plugins/codex-security/scans/discord_file_downloader/2046ecdbd983450ab5098ec2a0caebfda91e41ab_20261001T081724Z_gwa8td99/report.md).

The Bot finalizer reported whole-working-tree drift while this agent wrote the documentation checkpoint. All ten current source hashes were independently compared and match the reviewer's pre-finalization stdout capture. That capture is supplemental evidence, not a sealed initial source manifest; the whole-working-tree warning is retained. The completed review binds its original snapshot. Exact immediate before/after comparison independently verifies that this repair's Bot delta is only the DAL acceptance pin and three SQL member hashes. See `bot-review-source-reconciliation.json`; the separately created final source seal binds the final 26 source members and does not retroactively replace review provenance. Review token usage was unavailable. Ruff also passed for the changed DAL source.
