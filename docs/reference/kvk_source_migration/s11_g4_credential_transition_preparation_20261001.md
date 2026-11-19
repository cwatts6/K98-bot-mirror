# S11 local credential transition preparation — 2026-10-01

Status: source/configuration mapping completed; **credential transition not executed**. Chris requested continued local completion. Routine local preparation remains approved. A question about current local consumers is pending; no new permission question is needed for source review. No credential contents, `.env`, target state, SQL, provider, Discord or production runtime were read in this step.

## Verified locally

- Fifteen explicitly named source files were hashed and their credential-reference line numbers recorded in `.codex_artifacts/s11-credential-transition-20261001/source-and-path-verification.json`.
- `constants.py` obtains `GOOGLE_CREDENTIALS_FILE` and combines it with `BASE_DIR`. AST checks confirmed the actual assignments, and two Windows path-resolution checks confirmed an absolute value resolves identically from the workspace and protected application roots. These are source/path checks, not application imports or actual environment observations.
- All 48 members of the prior dependency result seal still match their recorded sizes and hashes. No historical seal was changed.
- No application code change is needed to support the proposed absolute credential path.

## Local consumer mapping

| Source | Configuration/use | Transition consequence |
|---|---|---|
| `constants.py` | `load_dotenv()`, then `GOOGLE_CREDENTIALS_FILE`, default `credentials.json` | Set an absolute path in the specifically approved consumer's configuration. Do not assume its existing value or change a machine-wide variable. |
| `gsheet_module.py` | Default arguments and direct credential factories | Existing imported defaults remain bound; an on-disk environment edit does not rebind a running process. |
| `event_data_loader.py` | Cached service-account credentials | Moving a file does not invalidate already cached credentials or tokens. |
| `proc_config_import.py` | Reads `CREDENTIALS_FILE`; logs configured path during validation | Do not run it to discover configuration: it can call Sheets and SQL. |
| `kvk_all_importer.py`, `processing_pipeline.py`, `bot_instance.py`, admin/stats commands | Pass the constants-derived credential path into report consumers | These are possible consumers, not evidence that any is currently running locally. Importing or invoking them is not a custody probe. |
| `scripts/config_self_test.py` | Checks the configured credential path | Do not execute a broader config diagnostic merely to answer one path question. |
| `scripts/run_export_authority.py`, provider child, `core/export_execution_host.py` | Exact `credentials_file` plus deployment-bound identity/hash | Protected manifest must use the new path and be resealed. Environment variables alone do not configure this path. |
| `scripts/enroll_export_output_pool.py` | Normal shared-account manifest; manual registration operation | SQL registration writes and live provider reads follow readiness validation. Do not use it as a harmless key test. |
| `start-bot-after-sql.ps1` | Existing startup wrapper names workspace Python/Bot paths | No wrapper/task change or execution is part of key preparation. Preserve production action. |

## Exact proposed transition boundary

- Host: `9SX2VF4`, Chris SID `S-1-5-21-3167111192-3307161013-4064290451-1001`.
- Existing file: `C:\discord_file_downloader\statsupdate-0d8b70356ef2.json`.
- Proposed destination: `C:\K98-S11-Validation\credentials\statsupdate-0d8b70356ef2.json`. This filename is proposed, not reserved or observed absent by this step.
- Same existing service account/project: `sheets-service@statsupdate.iam.gserviceaccount.com` / `statsupdate`.
- Keep existing file contents and identity; no additional key, credential copy, placeholder, old-path symlink or junction. No production copy change.
- Desired file access: protected inheritance; Chris, SYSTEM and Administrators only, with recovery access. Preserve workspace and drive-root ACLs. Protect the destination parent against replacement.
- Future authority `credentials_file` and any explicitly retained local legacy consumer's `GOOGLE_CREDENTIALS_FILE` must name the same absolute destination. No `.env` or manifest has been changed or fabricated.

Required transition sequence: identify consumers and their exact config targets; bind current source metadata/identity and destination absence; exclusively hold the same file without reading credential content; refuse reparse points, multiple links, unexpected owner/ACL, existing destination or sharing conflicts; apply/read back the protected descriptor and perform a non-overwriting same-volume rename through a reviewed identity-preserving mechanism; confirm file identity, protected access and old-path absence; record the exact phase reached. Path-only prechecks followed by an unguarded `Move-Item` are insufficient to establish same-file identity under replacement races. No runnable transition body is supplied until these bindings and recovery behavior are resolved.

Proposed operation budget: one credential file, one descriptor change, one rename, zero credential-content bytes captured, zero provider/SQL requests and zero target rows. At most six named path metadata records plus required ancestor checks; no recursive collector. Proposed 30-second owned operation deadline, 64 KiB stdout, 8 KiB stderr, 128 KiB nonsecret evidence. Enforceable launcher/phase bounds and complete reviewed command hashes remain **UNRESOLVED**; these proposed budgets are not execution authorization or measured outcomes.

Evidence must contain operation/revision, approved source/command hashes, host/SID, UTC phase transitions, file ID/volume/link count, old/new path, before/after owner/DACL, child exit and capture/termination status. Never emit private key, JSON credential body, token or unfiltered exception contents. A local hash/allowlisted identity read needed by the eventual deployment manifest is a separate explicitly bounded credential-content operation; do not pretend metadata observations supply that hash.

Stop without retry on changed preimages, unexpected consumers, source/destination mismatch, locked file, failed protection/rename/readback, timeout or uncertain phase. Preserve all evidence and the actual file location. If protection succeeds but rename fails, keep the file protected at its old location. If rename succeeds but configuration is incomplete, leave consumers stopped and retain the protected file at the destination. Do not automatically restore broad permissions, move back, duplicate the key or start the Bot. Recovery requires reconciling actual file identity/phase, then a narrowly reviewed corrective operation.

## Missing fact and later gates

The single immediate question is whether any local Bot, scheduled task, importer or other tool currently uses or must retain the workspace credential path. The prior statement that only production and this machine hold the key remains accepted; this question concerns consumers on this machine, not additional holders. A source search cannot answer it. If none need the old path, no existing consumer configuration needs to be edited merely to stage the inactive candidate. That answer does not by itself prove all writers drained.

Actual registration and the two-export demonstration remain beyond this transition:

1. Complete application SQL installation/permission bindings; DB23's minimal synthetic rehearsal is not the complete application contract. Preserve DB22 and its 119 media files.
2. Current nonsecret identity/key inventory, exact process incarnations and writer-drain evidence. Cached tokens are unaffected by a filesystem move.
3. Complete protected/reference/uncertainty set and fresh bound manual enrollment. The five supplied files and public Viewer policy are settled; historical blank/access evidence is retained, not rerun here.
4. Final selected input/report/config identity and independent expected results. Preserve all accepted input evidence; do not infer expected reports from newly generated Sheets.
5. Separately approved actual exports and later production/G5 decisions. No second Bot, readiness bypass, automated file creation or production/main pull.

## Validation and security decision

Executed only `C:\Program Files\Python311\python.exe -I -S -B .codex_artifacts/s11-credential-transition-20261001/prepare_local.py`. It reads the finite 15-file source list and 48 sealed local evidence members, performs AST/Windows path checks and exclusively creates a local report. No application imports or target-bound fixture execution. Separate working/sealed copies of this **offline preparation command** and a new result seal retain its exact bytes. They are not credential-transition commands.

Security routing: documented skip for this preparation-only delta (this document and the bounded offline source/hash/path report helper). No application, SQL, dependency, permission, credential or runtime configuration behavior changed. Any future transition executable needs a Changes review, Deep off, before real-key execution. Prior independent review limitations and the broader test run's 20 failures/one setup error remain open. No full-suite, installation, provider or G4/G5 acceptance follows.

Architecture/test-selector/deferred/security-routing repository validators and runtime pytest were not rerun: no production code, tests or SQL changed, no PR is being handed off, and this step's meaningful checks are the exact static path/source and preserved-seal checks above. No new refactor or deferred implementation item was introduced.
