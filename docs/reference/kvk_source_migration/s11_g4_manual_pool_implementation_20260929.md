# S11 manual Sheets registration — local implementation

## Public Viewer correction — current 2026-09-29 overlay

Read the [public Viewer implementation update](s11_g4_public_viewer_implementation_20260929.md) before older policy/source statements below. The operator explicitly retains anyone-with-link Viewer access. Local manual plan v3 and coordinated SQL correction are implemented, offline-tested and separately reviewed; no installation, registration, export, deployment or activation follows. Private-only initial wording and older source pins below are historical. Existing receipt interpretations, seals and reference/uncertainty protections remain preserved.


## Current S11 checkpoint — 2026-09-29

Read the [current validation handoff](s11_g4_validation_handoff_20260929.md) first and use the [new-chat starter](../../task_packs/S11%20G4%20Controlled%20Validation%20-%20Chat%20Starter%20-%2020260929.md) for the next chat. It supersedes earlier dated S11 next-step, OAuth/fresh-identity, fresh-file and restore-incomplete statements below. Their original bodies remain historical evidence; general engineering/runbook requirements still apply.

The approved single-account/manual-Sheets source implementation and focused local review are complete, pending and unpublished. Chris manually creates Sheets as `chrislos35@gmail.com`; existing `sheets-service@statsupdate.iam.gserviceaccount.com` writes to the registered fixed pool. No human OAuth, automated creation or replacement identity is planned. Equivalent reports and safe referenced/uncertain-output protection remain required.

The 119-set development restore, recovery and clean CHECKDB are evidenced; the selected 15-table baseline covers 2,410,159 rows with its retained provenance qualifications. Keep `S11_G4_Recovery_20260928_97337` read-only/restricted/Broker-disabled. All seven current typed G4 proofs remain incomplete.

Next is local preparation of the exact bounded SQL/provider/two-export validation packet, not execution. Production stays on isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`; no main pull, restart, installation, provider call, activation, publication or automatic chat creation. The old window ended 2026-09-29T09:23:23Z; local preparation needs no window. Rollout and G5 remain separate operator decisions.

Retained validation: initial 844 passed / 1 skipped; corrected affected suites 467 passed / 1 skipped (overlapping counts), Ruff and relevant validators passed, five SQL files parsed without errors. Final Changes reviews, Deep off: Bot `22f0b2af-37b0-4f3d-89ae-4ba3375682ae`, SQL `a87cb75f-c10b-4a4c-99bd-55c22921102b`, zero security findings. These are source/offline results; native/SQL/provider integration and two actual exports remain unproved. Exact report links and evidence paths are in the current handoff.


The operator approved the focused local implementation after the scope proposal. Chris creates the dedicated Sheets once as `chrislos35@gmail.com`, shares them with existing `sheets-service@statsupdate.iam.gserviceaccount.com`, and reuses the registered file IDs. No human OAuth, automated creation, replacement service account or generated file per export is required. This decision supersedes the older creation/issuance assumptions; equivalent reports and safe publication still apply.

## Implemented behavior

`scripts/enroll_export_output_pool.py` now accepts only the explicit `S11_REGISTER_MANUAL_OUTPUT_POOL` operation. It validates the normal protected service-account manifest, complete deployment boundary and SQL installation contract before opening its registration session. This is an operator CLI, not a startup action or Discord command. Do not execute it as part of preparation.

A version 2 plan declares the exact account, storage owner, human owner, Editor/project, manifest and credential-profile hashes, plan UUID, ordered files and protected exclusions. The file order must match exactly one runtime pool: index first, then its slots. Other pools and protected historical IDs must be excluded. Each file declares its spreadsheet ID, sheet ID, title, rows and columns. Initial verification supports one blank grid per file, 3–17 files per pool, at most 50,000 initial cells per file; existing slot/part and eight-pool limits remain. This bounds initial observation, not later report capacity.

For each file the verifier permits exactly four reads: Drive metadata, complete permissions, workbook/grid metadata and the declared initial value range. It requires the exact owner plus Editor, private direct sharing, no extra/inherited/expiring permissions, no existing values or unexpected sheet structures. It never creates, clears, shares or adopts a historical file. Uncertain reads, missing closure or lost SQL acknowledgement leave incomplete evidence and prevent replay.

The additive SQL draft `20260929_001_manual_export_registration.sql` introduces `dbo.ExportManualFileOrigin` and `dbo.usp_ExportManualOutputEnrollmentTransition`. Registered and eligible stages are append-only and distinguish manual provenance from API creation. Eligibility binds the exact protected plan, session, resources, owner/fence/version and closed successful verification transcript. Existing managed origins remain readable. Reconciliation includes both supported origin kinds and all their preparation history. The manual provider event path rejects mutations. Existing SQL migrations and historical creation evidence remain unchanged.

Normal export admission can recheck retained registration without repeating creation or initial blank-file setup. Existing publication, reference protection, retirement, uncertainty and capacity checks still determine which registered files can be safely reused; a fixed pool does not mean overwriting a currently referenced workbook. No provider mutation is authorized by an origin record alone.

## Existing identity and source bindings

Deployment-boundary version 3 explicitly describes existing service-account provenance. It has no `previous_service_account_email` field and no fabricated creation/issuance dates. The `identity_issuance` record name is retained for compatibility, but its version 3 observation contains `provenance: existing`, `observed_utc` and `reviewing_administrator` alongside exact nonsecret identity and custody fields. Older boundary versions keep their historical issuance contract. All seven versioned records remain required; copied-key/writer exclusions and custody checks have not been waived. Never supply key bytes in chat.

The application source inventory now contains 540 objects: the previous 538-object SQL Git inventory plus the two manual objects and updated provider-event/reconciliation snapshots. New/changed snapshot hashes use LF-normalized UTF-8 source; installed definition hashes are a separate domain. The canonical source-list SHA256 is `fda765142962492ffa7fb5ed919ac1a4026c51114365f2d1cdc7ad2c03462944`. This is a candidate source pin, not installed SQL proof.

Old deployment manifests, source hashes, application schema contracts and seven-record version 2 packets are stale for this candidate. Preserve them as historical evidence. Produce a separately reviewed exact candidate packet; do not relabel earlier observations or regenerate live bindings from guesses.

## Validation and retained evidence

The local pre-edit preservation bundle is `.codex_artifacts/s11-manual-pool-implementation-20260929/before.zip` with its path/hash index `before.json` (199 files). All prior pending/recovered S11 files are retained. Test, source and final review results are recorded in the implementation directory and the final verification note below; no test result substitutes for installation/provider proof.

The focused suite initially passed 844 tests with one skip; registration-specific tests cover read-only success, wrong owner/access/shape/content, protected/duplicate targets, manifest mismatches, retained-origin restart checks, uncertainty/no replay, existing-identity provenance and extra-key rejection. The repeated-origin test demonstrates reuse of retained eligibility, not two real provider exports. A real two-export equivalence/reuse demonstration remains a later controlled validation.

All five authored SQL files passed offline ScriptDom parsing. Parsing and source equivalence do not prove SQL transaction/concurrency behavior. A disjoint disposable SQL integration fixture is still required under a separate exact approval; the recovered database 22 stays read-only and retained.

## Remaining operator packet

Use retained evidence first. Missing target inputs are the exact dedicated spreadsheet/grid IDs, chosen initial grid shapes and complete current owner/access/writer/key-metadata observations for the existing identity; no further preference decision or new account is needed. Prepare exact bounded operations and hashes for approval before any new provider or installation observation. No observation, grant, clearing, migration, restart or activation is implied here.

Production remains isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`. The completed historical restore and content baseline remain retained; all seven typed G4 proofs, controlled rollout and G5 acceptance remain incomplete/unapproved. Memory-cause work stays deferred and the withdrawn collector must never run. Empty KVK output and view rehydration remain separate issues. No Git publication, PR or production/main pull occurred.
