# Operator provider decision — 2026-09-29

## Current S11 checkpoint — 2026-09-29

Read the [current validation handoff](s11_g4_validation_handoff_20260929.md) first and use the [new-chat starter](../../task_packs/S11%20G4%20Controlled%20Validation%20-%20Chat%20Starter%20-%2020260929.md) for the next chat. It supersedes earlier dated S11 next-step, OAuth/fresh-identity, fresh-file and restore-incomplete statements below. Their original bodies remain historical evidence; general engineering/runbook requirements still apply.

The approved single-account/manual-Sheets source implementation and focused local review are complete, pending and unpublished. Chris manually creates Sheets as `chrislos35@gmail.com`; existing `sheets-service@statsupdate.iam.gserviceaccount.com` writes to the registered fixed pool. No human OAuth, automated creation or replacement identity is planned. Equivalent reports and safe referenced/uncertain-output protection remain required.

The 119-set development restore, recovery and clean CHECKDB are evidenced; the selected 15-table baseline covers 2,410,159 rows with its retained provenance qualifications. Keep `S11_G4_Recovery_20260928_97337` read-only/restricted/Broker-disabled. All seven current typed G4 proofs remain incomplete.

Next is local preparation of the exact bounded SQL/provider/two-export validation packet, not execution. Production stays on isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`; no main pull, restart, installation, provider call, activation, publication or automatic chat creation. The old window ended 2026-09-29T09:23:23Z; local preparation needs no window. Rollout and G5 remain separate operator decisions.

The earlier scope/decision text below describes the pre-implementation checkpoint. The operator subsequently approved local implementation; its completed outcome is recorded in the [manual-registration implementation](s11_g4_manual_pool_implementation_20260929.md). This does not authorize live use.


Latest explicit operator direction supersedes older G4 assumptions about human OAuth and fresh service-account creation:

- Sheets owner: chrislos35@gmail.com, operator-reported; sheets are created manually by Chris.
- No admin OAuth client/enrollment planned. Do not request an OAuth client/project or consent setup as if still required by the operator's chosen model.
- Keep existing service account sheets-service@statsupdate.iam.gserviceaccount.com, project statsupdate; no new account/identity planned.
- Do not infer new key issuance/rotation, credential contents or verified provider permissions from this decision. Existing-account reuse does not itself prove which keys/holders/writers exist. Never request key bytes.

This is a settled planning direction, not live provider verification, approval to provision/share/clear files or permission to bypass existing release gates. Manual creation and existing identity should be supported in the revised design; no repeated preference question is needed. Fresh output link/equivalent reports remain the existing requirement, now requiring reconciliation with manual creation. Existing previously named file remains a protected exclusion, not automatically selected or adopted.

## Source impact found locally

services/export_runtime_composition.py:592 enrollment_profile currently requires a human owner, OAuth client ID and exact drive.file scope. services/export_enrollment_service.py:413 creation requires an original successful sheets.create request/transcript. Its later origin verification rejects unproven files/fabricated origins. The current SQL migration20260924_001_export_execution_evidence.sql defines creation-stream/request/closure fields and created/eligible stages for ExportManagedFileOrigin. Thus manual owner-created files cannot truthfully be relabelled as the existing automatic-creation proof. This is a design/source compatibility gap, not a missing OAuth installation fact and not permission to remove guards.

Next local preparation should define a distinct manual enrollment evidence route: explicit approved file/grid IDs, owner/editor/private-access verification, blank/structure checks, protected exclusions, registration/eligibility, durable audit and restart/uncertainty handling. Separate operator creation attestation from observed provider metadata; never fabricate provider creation journals. Assess Bot service/evidence/runtime configuration and authoritative SQL contracts together before implementation. Preserve owner/fence/version checks, existing origins/receipts and no-write-before-eligibility boundary. No code/SQL change authorized merely by these facts.

Identity issuance and key inventory wording must be revised to existing-identity provenance and nonsecret key/holder/status/location/custody evidence under the already approved single-Windows-account trust model. Existing service account must not silently stand in for fresh issuance proof in the old versioned records. Select the exact changed proof schema/validation and retained risk statements in the forthcoming reviewable plan; all seven G4 records remain incomplete meanwhile.

No new live capture is proposed until the manual enrollment design determines the necessary facts and exact named targets/client. Stop asking for unused OAuth/fresh-account details. Do not read credentials or automatically use a connected Drive identity. No provider/SQL/Discord call, provisioning, file adoption, write, Bot deployment/restart, rollout or G5 action occurred.

Historical packets/seals remain intact; this additive decision controls newer preparation. Completed restore/integrity and15-table baseline remain retained with their recorded provenance qualifications. Memory-cause investigation remains deferred; withdrawn collector remains prohibited. Planning/source review only; implementation validation and separate Changes security review targets must be defined before any future authorized runtime/SQL edits.
