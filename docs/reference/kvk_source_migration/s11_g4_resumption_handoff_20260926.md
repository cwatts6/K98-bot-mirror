# S11/G4 resumption handoff — 2026-09-26

## Current S11 checkpoint — 2026-09-29

Read the [current validation handoff](s11_g4_validation_handoff_20260929.md) first and use the [new-chat starter](../../task_packs/S11%20G4%20Controlled%20Validation%20-%20Chat%20Starter%20-%2020260929.md) for the next chat. It supersedes earlier dated S11 next-step, OAuth/fresh-identity, fresh-file and restore-incomplete statements below. Their original bodies remain historical evidence; general engineering/runbook requirements still apply.

The approved single-account/manual-Sheets source implementation and focused local review are complete, pending and unpublished. Chris manually creates Sheets as `chrislos35@gmail.com`; existing `sheets-service@statsupdate.iam.gserviceaccount.com` writes to the registered fixed pool. No human OAuth, automated creation or replacement identity is planned. Equivalent reports and safe referenced/uncertain-output protection remain required.

The 119-set development restore, recovery and clean CHECKDB are evidenced; the selected 15-table baseline covers 2,410,159 rows with its retained provenance qualifications. Keep `S11_G4_Recovery_20260928_97337` read-only/restricted/Broker-disabled. All seven current typed G4 proofs remain incomplete.

Next is local preparation of the exact bounded SQL/provider/two-export validation packet, not execution. Production stays on isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`; no main pull, restart, installation, provider call, activation, publication or automatic chat creation. The old window ended 2026-09-29T09:23:23Z; local preparation needs no window. Rollout and G5 remain separate operator decisions.

## Historical 2026-09-26 handoff body

The remaining original body is retained unchanged; use the current handoff for settled choices, proof status and next actions.


Latest overlay, 2026-09-29: the operator approved focused local manual-Sheets registration implementation using the existing service account. See [implementation and remaining proof boundaries](s11_g4_manual_pool_implementation_20260929.md). This supersedes older automatic-creation/fresh-identity assumptions, not the retained evidence or live-operation gates.

## Current decision and scope

Resume S11/G4 planning and capture reconciliation. The operator has deferred further investigation of the memory incident's cause; it is UNRESOLVED, not fixed or explained by the hotfix. No new chat has been created automatically. This handoff and its checklist authorize no live observation, rollout, provisioning, publication or acceptance.

Read this current-status overlay before `s11_g4_release_packet.md`. Preserve the original packet and all dated receipts/seals as history. Its older “not run”, “not published”, separate-account and incident-investigation prerequisites are not all current. The failed `observe-production-followup.ps1` and associated helper remain WITHDRAWN. Do not run them, or treat old observation approval as approval for a replacement. Planning can resume without resolving memory causation; each proposed new live operation still needs its own bounded, exact approval.

## Production and source state

| Item | Evidence / status |
|---|---|
| Production Bot | Operator deployed isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`, direct parent `abfc3845e9f8b78d70f88bada5a76c454ff32cb8`, on MINI_AMD at `C:\discord_file_downloader`. Guarded checkout verified three runtime hashes. Detached checkout is intentional. |
| Published hotfix | Private repository `cwatts6/k98-bot`, branch `hotfix/procconfig-deployed-20260926`; exact remote SHA verified at publication. This was a specific exception to main-only deployment, not a general policy change. |
| Local Bot main and origin/main | Both `2046ecdbd983450ab5098ec2a0caebfda91e41ab`, read locally for this handoff. |
| Local production/main ref | `3de899abee99102005911f5099c12b056f8aa490`, read locally for this handoff. Contains new importer; do not pull it onto production as an incidental update. |
| Local SQL HEAD and origin/main | Both `4cd1554dc3d063e323f22350c88df1444cd0ed4b`, read locally in `C:\K98-bot-SQL-Server`. |
| Remote freshness | No network ref refresh was performed for this handoff. Local remote-tracking refs are not a new remote observation. |
| S11 runtime | Not deployed/activated by the hotfix. Production SQL installation of S11 remains unproven/previously observed missing. |
| Pending amendment | Approved same-account amendment exists as local, uncommitted/recovered Bot changes. It is not delivered merely because earlier S11 PRs merged. Reconcile current bytes against retained review seals before future review/publication. |

The hotfix changes only `file_utils.py`, `maintenance_worker.py`, `proc_config_import.py` and three regression test files. It drains result sets and validates worker outcomes, retaining uncertainty/no retry. Final Changes scan (Deep off) `2fdbeb02-3842-4cb5-a063-944eb433e66b` reported zero findings. The exact candidate passed 3,720 tests / two skipped in a local Python 3.11.9 environment matching all 108 operator-reported production package versions. This is package-version parity, not installed-binary or live-provider proof.

### Runtime verification completed

- Restart at 21:16:33 (as logged): queues drained, new child PID7020 acquired singleton lock, executable `C:\discord_file_downloader\venv\Scripts\python.exe`. Old process IDs are historical; PID7020 is also only a point-in-time observation, not a native FILETIME/token binding.
- Startup ProcConfig import completed in 13.0 seconds; background `success=True`. Follow-up supplied through 21:22:12 completed the five-minute observation with Sheets access OK and scheduler errors=0.
- Genuine file `1198_26th_September_26d_26Sep-21h27m.xlsx`, message `1553518526592192642`, processed 409 rows. Immutable CSV identity `stats_bcbbac1e497d6d2aa42afb40f8e87fa8.ready.csv`.
- UPDATE_ALL2 reported SUCCESS, KS5/KS4 each 409 rows, counter reached1028. Post-upload ProcConfig succeeded in13.9s. All14 Sheets transfers reported success. Pipeline summary all true; DONE21:32:48.750.
- No memory/busy-results/error-level failure appears in these supplied excerpts. These are operator-supplied logs, not independent content readback.
- Separate retained issues: tracked-view rehydration exceeded10s and deferred remaining views; later recovery unproven. KVK fighting notification was acknowledged but reported players/kingdoms/camps=0 and `data=empty_or_unavailable`. Do not replay the successful upload or assume a hotfix regression. Neither issue should silently expand S11 scope.

## Settled operator choices — do not ask again

- One existing Windows account on the production Bot host for Bot and authority. No extra account absent a significant demonstrated need. The approved amendment uses `single_account_application_v1`: it trusts those processes/account together and does not claim Bot-inaccessible credentials.
- Only one production Bot, no test Bot. Development SQL is `localhost\K98DEV`; production server is MINI_AMD, database ROK_TRACKER. Disjoint disposable targets may be proposed; none is authorized for creation merely by this statement.
- Admin uploads external exports manually to Discord; imports are upload-triggered. Exports are triggered through Bot uploads/commands. Legacy and new-source choice is for a whole KVK. Reported absence of other manual writers/instances is context, not exhaustive observation.
- Admin Chris is rollout operator and reviewer. No second person is required; retain distinct approval checkpoints without claiming independent-person review.
- `KVK_DATA_CHANNEL=1549003662024642632` is intended for production `.env`; actual installation is UNRESOLVED. Do not add it now.
- Supplied spreadsheet `1EHirQ14aFvnOxM3RwgnlmZ_AogVmvJ0fuPtQuGHhfx0`, grid1683673174, was a proposed destination and reportedly service-account Editor shared. Later decision accepts a fresh generated link and equivalent reports within it. Do not adopt/clear that existing file or assume its permissions were verified.
- Enrollment design uses admin-owner OAuth (`drive.file`) to create private files and grant the service account Editor. Service account creation rights are not assumed. No manual file creation is needed now; creation-origin evidence must come from later approved enrollment.
- Outputs remain unedited after upload; players have anyone-with-link Viewer access. The exact publication/private-pool transition still needs evidence.
- Historical service-account key exists on both machines. Never ask for key bytes. Fresh issuance/custody and old-key inventory remain open under the approved shared-account trust model.
- Operator reports backups complete and online for the hotfix; this is not G4 actual-restore evidence.
- Operator owns manual Bot start using the usual scheduled task. Do not repeat the request for its exact name/action as a prerequisite for the completed hotfix. G4 still needs effects/writer exclusion and a concrete authority/process-binding lifecycle: obtain necessary metadata only through a newly approved narrow observation, explaining that different purpose.

## Delivery evidence to retain and reconcile

S11 mirror281, SQL89 and production588 are historical merged anchors. Later mirror repair/handoff282, production589 and SQL documentation90 were verified delivered in the retained packet. The two SQL delivery paths are exactly `docs/SQL_DELIVERY_LOG.md` and `migrations/README.md`.

Retain `.codex_artifacts/s11-g4-plan-20260925/delivery-proof.json`, `remote-file-proof.json`, `mirror282-files.json`, `production589-files.json`, `sql90-files.json`, review receipts and `source-pins.json`. These bind individual filenames/status/previous_filename or base/content/absence proof, including both S10E archive sides. The initial five-file restoration proof is historical; four of those files were later corrected. Final production589 patch SHA256: `5cba76f916e6e81a9c3e8897a0e60566064b153cb940f3f8321dc37ada209df1`.

Retain incomplete-drain failure status and shared provider429/503 cooldown corrections and their runtime cases. Mirror283/production590 delivered the later ProcConfig fixes to main; the isolated deployed backport is separate. No additional PR or Git publication is authorized now. Bot preparation belongs with genuine authorized Bot implementation, including mirror handoff; no separate invented Bot docs PR. SQL90 was a narrow delivered exception, not continuing publication authority.

## Evidence locations and preservation

All paths below are relative to `C:\discord_file_downloader` unless stated otherwise.

| Location | Purpose |
|---|---|
| `docs/reference/kvk_source_migration/s11_g4_release_packet.md` | Historical evolving G4 packet, operation ledger, cases and invariants; reconcile stale clauses using this handoff. |
| `.codex_artifacts/s11-g4-plan-20260925/` | Source/delivery proofs, packet seals, same-account amendment validation/security seals and schema candidate. |
| `.codex_artifacts/s11-g4-observations-20260925/` | Raw host/SQL observations, reports, failed collector originals, incident records and seals. |
| `.codex_artifacts/procconfig-hotfix-20260926/deployed-v2/` | Hotfix manifest, source/rollback archive, security/validation links, HF01/HF02/HF06 evidence, upload log and extracted evidence. Read `OPERATOR-PACKET.md`, `hf06-startup-evidence.json`, `post-hotfix-data-upload-evidence.json`. |
| `.codex_artifacts/recovery-20260926/` | `verified-pending-files.zip`, `git-recovery.json`, `restoration-verification.json`, verified originals and before-restore copies. |
| `.codex_artifacts/s11-authority-composition/` | Detailed corrected delivery/review/rename/patch proofs. |

Root checkout contains25 pending entries from the recovered S11 work (21 modified tracked paths and four untracked entries, including `deploy/`). Preserve every file under untracked directories too. Earlier recovery retained30 pre-PR files;25 pending entries were restored while five merged hotfix files stayed at their newer versions. Do not reset, clean, discard, stash automatically, overwrite recovery archives, or commit all changes indiscriminately. The normal Promotion Guide cleanup commands are unsafe here while work is pending.

Existing isolated hotfix worktree: `C:\Users\cwatt\.codex\worktrees\procconfig-result-drain\discord_file_downloader`, branch `codex/procconfig-deployed-hotfix`. Discover attached artifacts before reuse; do not remove it or its local test environments as part of handoff.

## Capture refresh checklist

Raw observations must not be relabelled as completed typed proofs. All seven version2 records remain incomplete. Old sealed evidence remains valid as history, but restart/source changes invalidate adoption of old process bindings. Metadata-only observations and effectful proof operations are separate stages.

| Record / area | Retained facts usable as history | Missing or stale; next planning action |
|---|---|---|
| `host_acl` | Host receipt04:46:41Z; sampled paths/hashes/SDDL. Authenticated Users Modify on Bot root and `.env` was observed. Hotfix source hashes and108 package versions captured later. | Reconcile exact final source/config/interpreter/base-Python/dependency hashes, parents/reparse boundaries and protected paths. Plan narrow ACL reads and exact future ACL changes; do not change ACLs during capture. Full new-release source manifest differs from deployed hotfix. |
| `bot_identity` | Observer MINI_AMD\cwatt SID `S-1-5-21-2970367362-111206357-3835881402-1001`; runtime log confirms venv executable/PID7020 at restart. | Current exact PID/creation FILETIME/native token groups/privileges/elevation and executable binding; future authority identity and retained handles. Observer SID and SQL client PID are not authenticated Bot proof. Same SID/different PIDs required by amendment. No adoption across restart. |
| `identity_issuance` | Historical shared key acknowledged; admin-owner enrollment design chosen. | Nonsecret project/client/service identity, issuer/admin/impersonator capabilities and fresh issuance plan. Issuance is a separately approved mutation, not a capture task. Bind new shared-account custody semantics; reject old exclusive-custody assertions. |
| `key_inventory` | Historical key on development and production machines. | IDs/status/locations and access/holders/revocation metadata, protected credential references and old-writer isolation. Never read key/token bytes. Fresh identity/key does not itself exclude old writers. |
| `file_access` | Proposed existing file/grid and reported Editor/Viewer arrangement. | Fresh provider access check approval, owner/editor/viewer/inheritance metadata, all protected exclusions/aliases, exact index/slot/grid IDs and P/Q/R. New IDs arise only from later approved enrollment receipts. Prior provider attempt was blocked by approval-token failure; do not assume access now works. |
| `writer_drain` | Partial processes/tasks/Agent jobs; Bot-only user-trigger report; successful hotfix shutdown queue drain. | Effects of startup/daily restart/log rotation/schema export and SQL jobs, all writer families/manual tools; closed admission, sessions/children, owned deliveries, uncertain claims, termination/no delayed effects. Hotfix queue drain is not G4 authority drain. Capture inventory first; live drain/reconciliation is later separately approved. |
| `sql_installation` | MINI_AMD/ROK_TRACKER SQL16.0.1200.5, FULL/compat160;538-source inventory comparison gave480 name/type matches,58 absent. Export roles absent; SHEETS_USER had db_owner. | Exact current approved SQL delta, table/parameter/type/module/signature/grant shape and restricted effective capabilities; installation receipts later. Git-byte hashes differ from SQL UTF16 definition hashes. No install-every-missing-object shortcut or production grant changes during observation. |
| Isolated targets/storage | Development instance had17 retained application DBs plus system DBs; prior file output truncated. | Complete durable DB/logical/physical file exclusions, storage/space and exact approved disposable names. `K98_S11_G4_20260926_validation` / `_restore` were candidates only, not reserved or authorized. Preserve all existing DBs/files. |
| Backup/actual restore | SQL history records FULL/DIFF/LOG in `C:\SQL_BACKUP`; prune and two LOG schedules observed. Operator's hotfix backup assurance. | Exact chain/media/readability/retention and prune effects; disjoint restore destination/file mapping, storage budget, literal commands and verification assertions. Actual restore needs separate approval/execution; VERIFYONLY/local code-archive extraction/hotfix backup assurance cannot satisfy it. |
| Operational packet | G4-00H/S/P families and later G4 stage/case ledger exist. | Fresh source/config/script hashes, operator/reviewer/abort owner, precise UTC window/expiry, effects, time/resource budgets, stop/reconciliation/rollback operations. No inherited authorization across changed targets/hashes. |

Seven-record contract: `single_account_application_v1`; supervisor manifestv3, Botv2, enrollment outerv2, boundary/recordsv2, SQL readinessv3/application. Verify these against current implementation before building executable records. Application principal needs the approved capabilities without sysadmin/db_owner or reader-role DENYs; no new Windows account is implied. Source schema manifest candidate digest `e9a6a1042de97e4fd4d7902756375f642a5a960354edb4018207ebc806a68b32` is Git-byte evidence, not installation proof.

## Next chat sequence

1. Read current AGENTS/core references, this handoff, packet/task pack and S11 closeout. Read S7 contracts/manifests, architecture/EndScanID amendment, authoritative S10A/C/D/E/S11 SQL, retained S6/S8 and relevant startup/shutdown/environment/diagnostics/promotion/rollback references before proposing affected operations.
2. Reconcile retained local evidence and pending amendment bytes first. Preserve a before-edit inventory. Recheck source/PR outcomes only read-only if needed; no publication. Do not restart completed S11 implementation or predecessor suites.
3. Produce a concise revised capture subpacket identifying reused evidence, invalidated bindings and only missing reads. Split fixed-field bounded observations; no broad recursive object serialization or replacement collector executed on preparation consent. Pin commands/scripts, exact paths/targets, output limits, connect/query/overall budgets and stop behavior. Keep secrets out of output. Metadata observations create connection/audit/resource activity and evidence files; describe those effects honestly.
4. Present that exact subpacket for operator approval before any SQL/provider/Discord/RDP runtime observation. Obtain nonsecret missing facts from source/retained evidence first; do not ask again for settled preferences or key bytes.
5. Reconcile approved results, then finish the exact G4 release packet: source/dependency/config pins, all writers, seven records, disjoint targets, actual restore, provider pools, literal operations, budgets/stops/rollback and approval checkpoints. Unknowns stay UNRESOLVED.
6. Controlled rollout executes only approved packet/operation IDs/targets. G5 remains an explicit operator accept/reject/defer decision after evidence; no merge/test/hotfix success implies it.

Preserve running-A immutability/eligible pending coalescing, daily fairness/order, registration-aware intents, source/endpoint/UpdateID, complete S10C provenance/spool/nested ownership, exact owner/fence/version CAS, append-only dispositions and byte-exact receipts. Preserve P/Q/R,9,000,000-cell parts and8/16 bounds. Rollover closes admission and drains/reconciles; old-writer termination plus private clear/readback precede audited reuse. Interrupted retirement needs explicit journal recovery/no delayed effects. Uncertain means reconciliation, never blind retry; shutdown retains uncertain claims and drains owned delivery.

S6-OPS01/PERF01/CAP01 stay OPEN. Preserve uncertain publications `e19c89ac-7977-5f28-ae4c-031807cd1728` and `54a2480a-26fb-5bad-a3f5-9321525a731c` and every retained database/file. S8A six scripts, S8B50 cases/actual restore versus offline history, S8C seven local checks remain distinct. Include N/C/T/S/L/Q/P/R/D cases from the packet, especially incomplete-drain failure and durable429/503 cooldown/no retry. Later security is Changes/Deep off against exact runtime target and separately assessed actual SQL deltas.

## Handoff validation

Documentation/evidence handoff only: no runtime code changed, no live call, no deployment or Git publication, no new task. Runtime tests/security scans/predecessor runs are not warranted for this status artifact; no PR handoff is being performed. Local Git refs and existence of the named principal evidence files were checked; no claim is made that every historical seal has been revalidated today. A new local evidence snapshot accompanies this handoff under `.codex_artifacts/s11-g4-resumption-20260926/`; old seals remain unchanged.
