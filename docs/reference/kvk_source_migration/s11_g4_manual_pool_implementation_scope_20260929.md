# Manual Sheets setup and fixed-file reuse — implementation scope

## Current S11 checkpoint — 2026-09-29

Read the [current validation handoff](s11_g4_validation_handoff_20260929.md) first and use the [new-chat starter](../../task_packs/S11%20G4%20Controlled%20Validation%20-%20Chat%20Starter%20-%2020260929.md) for the next chat. It supersedes earlier dated S11 next-step, OAuth/fresh-identity, fresh-file and restore-incomplete statements below. Their original bodies remain historical evidence; general engineering/runbook requirements still apply.

The approved single-account/manual-Sheets source implementation and focused local review are complete, pending and unpublished. Chris manually creates Sheets as `chrislos35@gmail.com`; existing `sheets-service@statsupdate.iam.gserviceaccount.com` writes to the registered fixed pool. No human OAuth, automated creation or replacement identity is planned. Equivalent reports and safe referenced/uncertain-output protection remain required.

The 119-set development restore, recovery and clean CHECKDB are evidenced; the selected 15-table baseline covers 2,410,159 rows with its retained provenance qualifications. Keep `S11_G4_Recovery_20260928_97337` read-only/restricted/Broker-disabled. All seven current typed G4 proofs remain incomplete.

Next is local preparation of the exact bounded SQL/provider/two-export validation packet, not execution. Production stays on isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`; no main pull, restart, installation, provider call, activation, publication or automatic chat creation. The old window ended 2026-09-29T09:23:23Z; local preparation needs no window. Rollout and G5 remain separate operator decisions.

The earlier scope/decision text below describes the pre-implementation checkpoint. The operator subsequently approved local implementation; its completed outcome is recorded in the [manual-registration implementation](s11_g4_manual_pool_implementation_20260929.md). This does not authorize live use.


## Decision and user-visible behavior

Chris (chrislos35@gmail.com) manually creates the dedicated output Sheets once and grants existing sheets-service@statsupdate.iam.gserviceaccount.com Editor. No human OAuth enrollment, automated file creation or new service account. Register explicit spreadsheet/grid IDs once; retain and reuse that fixed set across subsequent runs/restarts. Returned links point to those registered files; no newly generated file per run. This newer fixed-file decision supersedes automatic creation/fresh-file assumptions. Equivalent reports remain required.

This is a source-grounded implementation proposal, not code-change or live-operation approval. Current review changes only local planning/evidence files.

## Proposed minimal workflow

1. Admin supplies a reviewed manifest of exact dedicated file/grid IDs, roles, owner and existing service identity. Files must be deliberately selected and excluded from protected historical S6/S8/uncertain resources; no title search or automatic adoption of a previously suggested file.
2. A separately approved one-time verification reads owner, editor/viewer/inherited permissions, grid/structure/capacity and initial content against the exact manifest. Initial eligible content must be blank or explicitly covered by a later migration plan; do not clear existing data merely to register it. Arbitrary user layouts are not implicitly supported. Define the canonical expected report layout without requiring system-generated creation titles or a fabricated one-cell creation response.
3. Persist a versioned manual-registration record with operator attestation, exact manifest hash and observed verification receipts. It means 'admin-supplied and verified for use', never 'created by our API'. Interrupted/uncertain verification remains incomplete; restart reads the durable record and does not invent success or duplicate registration.
4. Normal exports use the registered file/grid identities and existing service-account credentials. Capacity shortage stops and explains the missing capacity; no automatic creation or file substitution. One-time setup must cover the actual required pool, not an assumed universal file count.
5. Subsequent reuse follows existing ownership/fence/version, reader-visible publication and retirement constraints. Do not demand that a previously published file be blank merely because a new export starts. Establish safe eligibility for replacement before any clear/write: protect current/referenced and uncertain outputs, exclude conflicting writers, and retain required receipts/history. Never promise unconditional overwriting of live referenced cells to keep a URL constant.

A fixed set can be reused while publication selects eligible members. Existing capacity/P-Q-R, parts and registration/slot bounds remain until a separately reviewed change; manual creation does not remove capacity needs. A demand for one exact physical workbook to be overwritten while it is still referenced would require a different publication design and is not inferred here.

## Concrete affected surfaces

- services/export_enrollment_service.py: replace the operational create/grant sequence with explicit manual registration and verification. Preserve exact target scopes, claims and append-only evidence. Refactor creation-specific private readback into reusable owner/access/structure checks; remove generated-title and original sheets.create dependencies for the new mode.
- services/export_runtime_composition.py and scripts/enroll_export_output_pool.py: manual manifest input and existing-service credential profile; remove the human OAuth profile requirement from this workflow. Change the command's user-facing purpose to register/verify existing dedicated Sheets. No credential contents in manifests or logs.
- services/export_execution_protocol.py and services/export_execution_authority.py: narrow manual-registration request allowlist; observation phase is read-only. Do not permit sheets.create or sharing mutation simply because enrollment is active. Preserve request IDs, durable dispatch/finality and no retry after uncertainty. Keep historical transcript decoding separate if needed for retained evidence.
- services/export_execution_dal.py and SQL persistence: versioned manual-origin eligibility lookup and same-transaction revalidation. Do not fake creation request/stream/event IDs. Registration must be bound to account, exact resources and manifest, actor/reason, verification evidence and owner/fence/version; exact schema/parameter design must be validated in the SQL repository before authoring.
- services/export_rollover_evidence.py and all PoolOriginVerifier consumers: accept only an explicitly supported verified manual origin or a genuine retained historical origin; no generic origin bypass. Existing clear/readback and no-delayed-effects rules remain.
- core/export_execution_host.py and corresponding manifest producers: explicitly version existing-identity provenance instead of relabelling it fresh issuance. Current identity_issuance row checks and sole-key/holder assertions must be assessed against the approved shared-account model. Enumerate observed key IDs/holders/custody; unexcluded copied-key writers remain a blocker. No new key/account or silent revocation is inferred.

## SQL source findings and migration ordering

Authoritative20260924_001_export_execution_evidence.sql defines ExportManagedFileOrigin creation stream/request/event/closure fields, created/eligible stages, and usp_ExportOutputEnrollmentTransition requiring the first successful sheets.create mutation. It also verifies those exact module bytes. A Python-only bypass would therefore be invalid. Add a new reviewed versioned SQL delta for manual provenance and eligibility; retain already delivered migrations and historical creation receipts unchanged. Prefer the smallest additive contract that represents manual provenance honestly; do not make all origin validation optional or synthesize provider events. Final choice of table/stage/field names must be explicit in the implementation diff, not treated as existing schema here.

SQL definition and migration precede Bot consumption. Target installations must support the exact new contract before runtime activation. Do not install all absent historical objects as a shortcut. The recovered database22 stays read-only and retained; it is not an implementation scratch target. Any later SQL integration fixture requires separate exact disjoint target, budget, preservation and approval. No SQL changes are made in this preparation.

## Focused validation and review plan

Tests should cover complete manual registration, wrong owner/editor, unexpected inheritance/public access, duplicate file/grid/alias, protected historical file, nonblank initial content, wrong manifest and schema version, insufficient capacity and no creation request. Verify restart/idempotency, lost read/SQL acknowledgement, stale owner/fence/version, incomplete evidence, extra key/holder and conflicting writer rejection. Demonstrate a second export reuses registered file IDs with zero creation calls and preserves referenced/uncertain outputs. Retain genuine historical-origin verification and current export behavior regressions.

Likely focused suites: test_export_enrollment_service, test_export_runtime_composition, test_export_execution_protocol, test_export_execution_authority, test_export_execution_host, test_export_rollover_evidence and SQL source-contract tests. SQL integration/live provider cases remain separately approved; passing mocks is not provider proof. Select exact nodes after implementation scope is approved.

Security routing: this document is preparation-only; no runtime scan claimed. Implementation touches authority, credentials, SQL persistence and file permissions, so review exact Bot Changes and separate SQL Changes targets with Deep off, preserving existing pending work. No full/deep repository scan. Run relevant architecture/deferred/security-routing validators and targeted test selection before a future PR handoff; no PR or publication authorized now.

## Preserved boundaries and next approval

Single Windows account and Chris as operator/reviewer remain. Existing service account does not establish current access or all-writer exclusion. Manual creation does not authorize clearing historical files, grant changes or activation. Memory investigation remains deferred; withdrawn collector never runs. Production stays isolated hotfix; no main pull, deployment/restart, provider call, provisioning, backup/restore repeat, cleanup or new task.

Approval requested only for focused local implementation of this manual-registration/existing-identity contract, related tests and documentation in the two local repositories, preserving pending/recovered files. Deployment, actual migration execution, provider registration/calls, file sharing/clearing, Git publication, controlled rollout and G5 each remain outside that scope. Required SQL workspace write permission, if unavailable, must be obtained through the normal tool boundary rather than broad filesystem changes.
