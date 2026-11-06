# S11 coordinated Viewer and two-host amendment — 2026-10-02

Local implementation of readiness findings R1/R2, authorized by “lets proceed”. Production execution, SQL/provider observation, enrollment, publication, restart and activation remain outside scope. No new maintenance window or key material is needed for this local work. Final validation and security results are recorded separately after completion.

## Scope and architecture

The source amendment covers coordinated Google Sheets generation, verification, retirement, rollover, reconciliation and existing-key custody proof. Services retain orchestration, DAL modules retain SQL writes, and core retains host-boundary validation. No Discord command/view, cache, scheduler or live configuration is changed. Existing final/uncertain reports and all databases are preserved.

Reuse: existing transport `_get`, staging/clear/readback methods, immutable attempt manifests, owner/fence transitions, closed provider transcript replay and DeploymentBoundary protected records. Two small modules centralize audience evidence and two-host custody schema validation; neither performs network/SQL/host discovery. No direct SQL was added to commands or views. No unrelated refactor or untriaged security item was deferred.

Before edits, copied all 168 pending/recovered Bot files and 18 pending SQL files into `preserved`. Existing seals remain unchanged. Source members are compared individually, never by treating a documentation-only change as missing implementation.

## Public Viewer behavior

The authority-composed transport selects preservation when its exact registered audience is public Viewer. It still requires the exact owner, sole service-account Editor, link-only Viewer and registered/protected file identities. Existing transport behavior for private audiences and historical explicitly private paths remains.

The coordinated attempt stores `generation.staging_audience` before the first provider mutation. Public staging requires recorded execution evidence and its verified part rows use `AclState=public_viewer`. Public records never assert a private ACL. The legacy SQL phase name `private_started` is retained for wire/schema compatibility; it means the initial unverified attempt stage, and is not evidence of an ACL. `AclState` remains pending until actual readback, with staging exposure explicitly pinned in the immutable manifest. Older manifests without the new field retain their original private interpretation.

Every generation file receives audience readback before verification. Publication still requires complete exact content, pointer and receipt readback. A failure or lost acknowledgment keeps the existing uncertainty/quarantine/owner protections. No path infers absence from a missing pointer or automatically replays a mutation.

Owned retirement/rollover preserves Viewer access and emits `private:false,audience:public_viewer` alongside exact empty/manifest/sheet evidence. Historical private evidence retains its prior bytes and interpretation. The legacy method/phase names `rollover_private` and `private_pending/private_verified` now select the registered staging audience; public completion does not invent privacy. Standalone public transport remains unable to retire files. Reference/final/uncertain checks and independent termination evidence are unchanged.

Rollover journal replay infers the explicit new public mode from recorded clear evidence and rejects permission mutations in that mode. Retirement recovery uses the immutable current attempt staging policy, so completed public clear is recognized after a lost acknowledgment. The historical no-field mode remains private. Reconciliation can read historical evidence; changing a live unresolved operation's policy is not authorized.

## Two-host custody format

Boundary and all seven observation records use version 4 for the new contract. Versions 1–3 retain their existing interpretations and are not silently upgraded. Version 4 is available only under `single_account_application_v1` and retains version 3 existing-identity provenance.

`deployment_boundary.key_custody` contains:

- `version:1`, exact `active_host`, UUID `window_id`, UTC `not_before_utc` and `dispatch_until_utc`.
- Exactly two `copies`, roles `production` and `development`. Each has exact `{machine_guid,hostname}`, Windows `user_sid`, absolute `credential_path`, and `credential_sha256`. Hosts must be distinct; the active copy must match the actual deployment host/SID/path and reviewed credential bytes. No new key or service identity is created.
- `release_rule:"explicit_after_all_writer_drain"`. Expiry closes dispatch permission; it never authorizes the other machine to resume writing. There is no automatic release or fixed export-duration cap.

The `key_inventory` observation retains the exact service account, sole key ID and observation time, replacing the old SID-only holder list with exact `credential_copies`. The observation must be within the selected window and not from the future.

`writer_drain` contains two observations, one for each exact host, bound to the same window, trusted Windows reviewer and release rule. Each contains a canonical nonempty `writer_inventory`, a matching `launch_controls` list, exited `processes`, ended `sql_sessions`, `remaining_writers:[]`, and `observed_utc`. Each launch control has `writer`, `mechanism` (`scheduled_task`, `service`, or `manual_operator`), `state:"disabled_until_explicit_release"` and a reviewed `evidence_sha256`. Process records retain PID/start/image/exit/end identity; SQL session records include server/database/session/login/start/end identity. Lists are bounded and duplicate incarnations refused.

Empty exited-process/session lists are allowed when the reviewed named inventory and no-running-writers observation establish that there was nothing to terminate. Do not manufacture PIDs, timestamps, machine GUIDs, control evidence or session exits. Manual operator control is a trusted operating commitment, not OS isolation or proof against a malicious administrator. The local authority cannot independently discover every remote key copy or writer.

Both authority launchers inject the boundary dispatch guard. It runs after pacing and again after the durable dispatch-intent checkpoint. Boundary verification finishes with a fresh time check so its own file reads cannot hide expiry. Failed guards retain uncertainty and do not dispatch/replay; stream closure/drain remains callable. Already dispatched work still requires terminal evidence before either host is released.

## SQL and persistence review

Authoritative source checked in `C:\K98-bot-SQL-Server`: `dbo.ExportAttempt`, `dbo.ExportAttemptPart`, `KVK.SourceOutputOperation`, related pool/slot/disposition contracts and the coordination/evidence procedures. Existing JSON manifests and evidence hashes carry the new policy; `ExportAttemptPart.AclState` already allows `public_viewer`. Existing phase constraints are unchanged. No SQL schema/migration/source modification is needed for this amendment and no SQL connection was made. The 540-object source-list digest remains the October 1 value; it does not prove installation.

The current SQL Changes review and prior complete identical-source review remain separate evidence. This amendment changes Bot DAL behavior, so the current Bot Changes review includes those paths. No new SQL review is claimed for unchanged SQL source.

## Validation plan and execution boundaries

Tests exercise actual typed transport request/replay paths with offline provider fakes, real DAL audience-transition methods with mocked transactions, malformed/missing/foreign custody records, expiry during pacing and intent persistence, positive public clear and lost-ack recovery, historical private behavior, uncertainty and reference protections. Existing architecture/deferred/security routing, test selection, smoke import and command-registration validators are included. The broad offline suite excludes both explicitly gated live SQL suites and clears the native Windows fixture authorization variable. Source tests are not installation/provider/native/G5 acceptance.

Independent local review found and corrected the post-intent expiry gap and the default-private retirement-recovery observer. A canonical Bot Changes scan follows the frozen source candidate; no Codebase/Deep scan is requested. No new source runtime acceptance is implied by zero security findings.

## Remaining factual/operator work

The two-host contract is now expressible, but no actual version 4 operating packet has been issued. Exact production/local GUID/SID/path/control evidence, process/session inventories and a future bounded operating window must be bound and reviewed. No expired window or earlier demo no-write assurance is reused.

The five-file minimum for the measured one-part pool is unchanged. The completed index/report remain protected; only three blank spares remain, so final new file/grid roles and sufficient manual capacity still need binding. No files were created, cleared, shared or selected by this amendment.

Seven typed G4 proofs, production SQL installation/effective permissions/signatures, native operational cases, S6/S8 operator acceptance and G5 remain open. Production remains the last observed isolated hotfix, not production/main. Preserve DB22 read-only/restricted/Broker-disabled and all 119 media, DB23/DB24, both uncertain publications, every receipt and pending shared-account amendment. Memory investigation/withdrawn helpers stay deferred; empty-report and view-rehydration issues remain separate.

## Completed local result

**Local R1/R2 source amendment implemented and reviewed. No production activation or G4/G5 acceptance.** Existing source-level blockers now have explicit coordinated Viewer and two-host proof contracts. Actual target-bound proofs remain outstanding.

- Broad offline run: **6,101 passed, 65 skipped, 8 subtests passed**; log-noise check passed. Its process started before the final historical recovery-factory correction, so it is not represented as a single all-green final-source run.
- Final amendment regression run after that correction: **51 passed, 608 deselected**, log-noise check passed.
- Complete affected runtime module plus audience/custody suites on the final source: **364 passed in 11.71s**; log-noise check passed. Counts overlap and must not be added.
- Architecture, deferred-item validator, security-routing validator, test selection, smoke imports, command registration, scoped Ruff and both Git diff checks passed. The two gated SQL suites were explicitly excluded; native Windows fixture authorization was removed. No target-bound fixture ran.
- Initial intermediate failures were a retained standalone retirement error-message expectation, a missing test import and test DAL construction missing prerequisite flags; corrected and retested. All intermediate logs remain retained.

Bot canonical Changes review `30c61dcd-8bb9-4cae-a141-64fafc684493` completed with 21/21 source members, zero findings and complete coverage; Deep off. **Retain its changed-working-tree qualification**: canonical start snapshot `b2251241a0d27fa76802a727e4b546d90ac4e27b5df5cd347c11172f666d85d9` predates the reviewed historical recovery-factory fix. The final reviewed 21 members are individually pinned in `security/final-reviewed-source-pins.json`, SHA256 `b7649d74b39cc994dac22b26ac91c4ada9a5b9a0ab3d375142b388770ee3c42b`. The start digest is not claimed to seal the corrected bytes. The canonical report and separate member pins are both retained locally; measured canonical scan token usage was unavailable.

All authoritative SQL pending source/document bytes remain unchanged from the pre-amendment copy. The 540-object canonical source-list digest remains `f082cd0cbf28261cddf966a954a4564d34a81a552d796707eb90dc75a6baf3cf`. Previous SQL complete/partial coverage qualifications remain as recorded in the full readiness review.

Evidence directory: `C:\Users\cwatt\Documents\Codex\s11-coordinated-amendment-20261002`. It contains the exact local command sources, logs/result JSON, full prior pending-file copies, isolated amendment diff, final candidate copies and hashes, security report/member pins, and a final manifest. Complete sealed copies of commands are separate from their working copies. Nothing in that directory is a production execution approval.

## Next boundary

Prepare the exact current operational proof packet using this final source candidate. Bind the two host custody/exclusion records and exact blank file/grid roles, preserve the final demonstration index/report, and supply sufficient manually created pool capacity. The historical standalone demonstration is not rerun or upgraded into full authority acceptance. No further settled preference question is needed. Actual observations/execution require the previously documented exact target and operator decisions; no window is requested merely for preparation.
