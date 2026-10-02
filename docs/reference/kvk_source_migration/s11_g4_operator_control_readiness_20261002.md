# S11 operator-controlled readiness decision — 2026-10-02

## Local review accepted; production inventory approved — 2026-10-02

Chris has **accepted and CLOSED the local implementation review** and **APPROVED bounded production inventory and staged rollout preparation**. Follow the [current approval/handoff](s11_g4_production_inventory_handoff_20261002.md), [handover task](../../task_packs/S11%20G4%20Production%20Inventory%20and%20Staged%20Rollout%20-%20Task%20Pack%20-%2020261002.md) and [new chat starter](../../task_packs/S11%20G4%20Production%20Inventory%20-%20Chat%20Starter%20-%2020261002.md). Carry this approval forward without repeating the question. Prepare exact bounded read commands, preserve their hashes/copies, then execute the permitted production reads. Installation, publication/PR, deployment/restart, enrollment/export writes and G5/activation remain separate decisions. Version 5 operator control and the verified five-file pool remain accepted; do not reopen settled choices. Earlier approval/status statements below are dated history, not current stage authority. No production observation was performed for this documentation update.

**Local amendment, focused validation, source review and five-file provider inspection are complete. The readiness decision is now reviewable; production rollout and G4/G5 acceptance are not complete or authorized.** No further spreadsheet creation or settled account/access decision is needed for the measured one-part validation workload.

This current overlay supersedes the requirement for remote shutdown/process/session inventories in the [earlier two-host amendment](s11_g4_coordinated_viewer_custody_amendment_20261002.md). Chris explicitly controls both machines and all export-command/import triggers and rejected that operational complexity. Historical packets and receipts keep their original interpretation. Do not fabricate old-style shutdown evidence to represent this decision.

Evidence: `C:\Users\cwatt\Documents\Codex\s11-operator-readiness-20261002`. The directory contains the preserved pending candidate, separate sealed/working commands, actual provider result, current pool bindings, SQL source copies, tests, security report, decision packet and final manifest. No SQL connection, production/RDP/Discord observation, provisioning, import/export, deployment, restart, Git publication or activation occurred in this amendment. The only provider activity was the expressly bounded read-only candidate inspection below.

## Completed operating simplification

Boundary/observation **version 5** explicitly represents operator control under `single_account_application_v1`. Versions 1–4 retain their prior requirements and meaning; nothing silently upgrades old evidence.

- Chris's named protected declaration binds the exact deployment, development/production host names, active host, sole existing key, known two copies, and the two controlled triggers: export commands and imports.
- Before an actual run, Chris confirms no conflicting work is outstanding and holds the other machine's triggers until this run finishes or any uncertain operation is reconciled. Standing ownership of both machines is settled; preparation does not invent a timestamped claim about current outstanding work.
- No remote MachineGUID/SID/credential-path inventory, terminated-process/session list, disabled-service proof, fixed time window or export-duration cap is required in this mode. The active deployment still checks its actual local host/SID, protected credential/source/configuration records and process incarnations.
- The old record name `writer_drain` is retained for compatibility. A v5 record is **operator confirmation**, not an assertion that remote processes were observed terminating. It has a different exact schema and rejects fabricated process fields.
- Records are pinned and checked on dispatch. A changed record, different deployment/operator, extra key/copy, missing trigger, outstanding conflicting work or absent hold fails closed. Completion/reconciliation requires explicit release; elapsed time is never permission to restart competing work.
- This trusts Chris's operating control. It does not automatically discover remote writers or isolate a malicious same-account administrator. Durable ownership, fences, unknown acknowledgements, reference protection and reconciliation are unchanged.

Implementation changes are confined to `core/export_execution_host.py` and the existing `core/export_key_custody.py`, plus `tests/test_export_operator_control.py`. Existing UTC/exact-field/protocol helpers are reused. No new SQL, command, scheduler, transport, file-creation path or dependency was introduced. Existing SQL execution session/stream tables persist manifest/source ownership independently of this observation schema. Authoritative SQL source was inspected and retained; no SQL bytes changed. No unrelated refactor or new deferred debt was introduced.

## Five-file pool verified and assigned

Actual read completed **2026-10-02T11:43:04.322503Z** using existing service account `sheets-service@statsupdate.iam.gserviceaccount.com`, project `statsupdate`, client `103175311864208640064`, sole operator-confirmed key ID `0d8b70356ef2fb1ea002daac8e9533463aab5d18`. One service-account token exchange used read-only Drive/Sheets scopes. No connected personal Drive identity was used and no key/token bytes were saved or displayed.

All five files passed the current manual public-Viewer predicates: owner `chrislos35@gmail.com`, direct service-account Editor, link-only Viewer, no extra principals, one blank `Sheet1`, grid **0**, **1,000 rows × 26 columns**, no unexpected workbook structures, existing app properties or description. Names are observed facts, not inferred from the link order.

| Proposed pool role | Observed file name | Spreadsheet ID |
|---|---|---|
| Index | S11 Validation Slot 02 | `1oNTj1W2OzdzZP4dpWNwvU3I81qRvnnlcn_uhoI8QVLQ` |
| Generation slot 1 | S11 Validation Slot 03 | `1m6R1p4hInf-CtL9bAK-fzc4emB38XoP8ViJEpuI9jA4` |
| Generation slot 2 | S11 Validation Slot 04 | `1JsMrUOCav1mQu2570M8tQ7RPauJD6fft_ztLhkx61mE` |
| Generation slot 3 | S11 Validation Slot 05 | `1CaOblsUbAbhl3iLEubadilIHympxbsUp9u2JXlc8rpQ` |
| Generation slot 4 | S11 Validation Slot 06 | `1zKq3eSCkVd2BTvGkRCTfXa9GenLc8_gCICcNQuKdHsg` |

No rename is necessary. Roles are prepared, **not SQL enrollment**; enrollment will freshly verify these exact files/grids before recording origins. The measured 23,388-row / 2,162,035-cell report needs one part. These five files satisfy `1 + P + P + max(P,Q) + P + R` at P=1,Q=0,R=0. This does not promise unlimited retention or extra quarantine capacity. If occupancy or report size exceeds that budget, admission stops; no referenced/uncertain file is cleared to make space.

The completed demo index `1ydIKNmq74VWfD52u_Ft_l7hd7qOQgLWdpX8erQw7j7o` and report `1Sfa6NJw4urC2ldTu16q5EGFSRR4VFPX0Pgt4paLiM1g` remain intact and excluded. `pool-bindings.json` carries these plus the nine retained historical exclusions (11 total). No request went to an excluded file.

Measured inspection: **25 GETs, one token exchange, 344,375 response bytes, zero mutations**. Metadata plus blank-grid/value checks were grouped into one bounded attempt. The first sandboxed launch could not access the protected interpreter; it did not start Python or call Google. Exact-path inspection and execution then succeeded through approved escalation. No provider failure or write retry occurred. The script uses normal local TLS/proxy configuration; it is not independent proof of direct network egress.

## Validation and source review

- **644 passed, 1 skipped**, including new operator-mode rejection cases and the existing two-host, single-account, host-boundary, authority, launcher and runtime-composition suites. Log-noise check passed: operational logs unchanged.
- Architecture, deferred-item, security-routing, test selection, smoke imports and command registration passed. Scoped Ruff and final diff/document/preservation checks are recorded in the final evidence.
- The broad 6,101-test run remains historical with its documented final-correction qualification. It was not relabelled as a full run on this amendment. The selected 644 tests exercise the changed boundary and its direct consumers; SQL/native gates were not enabled or counted as passed.
- Bot Changes scan **`25f11c9d-3ca6-40f2-9280-e3f4b61e7d09`**, Deep off: **21/21 source members**, zero findings/deferred/open questions, no target warnings. Snapshot `de0c242dcd9322242a10919db4970f61beffab4ba627382a9b25849cc4aa1384`, sealed 2026-10-02T11:41:37.045348Z. Canonical scan token usage was unavailable, not zero.
- Report SHA256 `6fdd6a0a7fce5148f7ab0404a765ab98d68acbd02b283506a457c22bf993901d`; final source-pin manifest SHA256 `b36537fffeeb30fd851d26fc57d61d01533a0539b0aa2d1e9646bd2f13609f8f`. All final source members are checked separately during sealing.
- Supplemental ordinary review of the exact provider inspection script found no blocker. This does not expand the canonical scan's source inventory. SQL is unchanged; its prior complete/partial review qualifications remain as previously recorded.

## Readiness decision and remaining work

The earlier R1/R2 **source blockers are resolved**, including the simpler operator model. R3's **minimum candidate-file shortage is resolved and directly verified**. This supports closing the local implementation review with explicit deployment prerequisites. It does not support marking full G4/G5 accepted or immediately activating production.

| Readiness area | What is available now | What remains before its acceptance |
|---|---|---|
| Host/configuration | Preserved protected-runtime work, current source pins and offline checks | Final deployment path/dependency/config/evidence closure on the target actually selected for rollout |
| Bot/authority identity | Native historical fixtures and tested incarnation checks | Actual future Bot/authority process identities and held-handle evidence; no test Bot and no stale PID adoption |
| Existing service identity/key | Known sole active key, user-confirmed two copies, actual successful service-account read; v5 represents these facts honestly | Review existing issuer/admin/impersonator scope and bind the records for that deployment; no new key/OAuth |
| Pool/access | Five exact blank eligible candidates; roles and 11 exclusions saved | Review complete legacy/reference inventory and enroll the exact pool with real closed authority evidence |
| Competing writes | Chris's trigger ownership accepted as the operating model | One actual run confirmation for no outstanding conflicting work/hold; no remote shutdown or inventory requirement |
| SQL installation | Retained DB23 minimal rehearsal, DB24 real calculation and authoritative source reviewed | Current target's installed prerequisites, effective application permissions and module signatures; observer sysadmin access is not this proof |
| Coordinated operational cases | Source tests and successful historical standalone transport demonstration | Real full-authority registration/export/reuse/recovery cases on the final bound target; do not rerun the standalone demo as a substitute |
| S6/S8/G5 | Retained measured results and accepted earlier evidence | Remaining operational capacity/retention/uncertainty handling and named production Discord acceptance cases |

The September 12 measured S6 rehearsal (including 37m29s) was **already operator accepted**, as recorded in `release_readiness_and_rollback.md`. Do not ask to reaccept that measurement. Its remaining operational limits and the two uncertain publications remain open. V5 supplies a representable operator-controlled scheduling model; it does not retrospectively reconcile those publications or select a production retention budget.

The immediate decision is whether to close this local review **with those explicit prerequisites** and proceed to a separately scoped production inventory/staged rollout preparation. Recommendation: accept the local amendment and verified pool; keep admission closed until installation/configuration, real coordinated evidence and operator acceptance are satisfied. Publication, production SQL changes, Bot deployment/restart and final activation remain separate explicit decisions. A direct main pull onto the isolated hotfix is not a rollout plan.

`DECISION-PACKET.md` contains completed commands/hashes, proposed stages, budgets, evidence formats and stop/rollback boundaries. It is honest about commands that cannot yet be made executable: production's current missing-object/signature inventory and future process identities have not been observed. No guessed install/signing command or invented typed proof is supplied.

## Preservation

All 182 pending/recovered Bot files and 18 SQL files were copied before edits. Old seals are unchanged and source members compared individually. Preserve DB22 `S11_G4_Recovery_20260928_97337` ONLINE/RESTRICTED_USER/read-only/Broker-disabled and all 119 media; DB23/DB24; both uncertain publications `e19c89ac-7977-5f28-ae4c-031807cd1728` and `54a2480a-26fb-5bad-a3f5-9321525a731c`; all files/receipts and the pending shared-account amendment. The historical 119-set restore and 2,410,159-row/15-table baseline are not rerun; B02 timeout and B04R1/B05 command provenance qualifications remain.

Production remains the last observed isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`, not production/main. Its startup/409-row/14-transfer evidence remains historical. Memory investigation and the withdrawn collector stay deferred. Empty KVK reports and view-rehydration warnings remain separate. No reset, clean, stash, new task or Git publication occurred.
