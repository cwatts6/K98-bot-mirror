# S11 G4 K98DEV preflight result — 2026-10-01

The bounded read-only K98DEV preflight completed successfully after correcting a local assertion. The selected new database name `ROK_TRACKER` is available; no database was created or installed. This supersedes the name-absence uncertainty in the target amendment, at the observation time below. Recheck absence immediately before any later creation.

## Actual observation

At `2026-10-01T20:59:05.2538868Z`, the launcher confirmed child exit 0 without timeout. The SQL runner completed in 0.1629868 seconds, returning seven rows and 3,154 JSONL evidence bytes.

| Check | Observed result |
|---|---|
| Server | `9SX2VF4\K98DEV` |
| Original SQL login | `MicrosoftAccount\cwattsconsulting@outlook.com` |
| Engine | `16.0.1200.5` |
| `ROK_TRACKER` name | Zero existing databases |
| Recovery DB22 | `S11_G4_Recovery_20260928_97337`, ONLINE, RESTRICTED_USER, read-only, Broker-disabled |
| Master certificate `S11LegacyImport` | Absent |
| Master user `S11LegacyImportUser` | Absent |
| Server login `S11LegacyImportLogin` and its grants | Absent |
| `xp_cmdshell` | Configured 0 / in use 0; unchanged |
| Cross-database ownership chaining | Configured 0 / in use 0; unchanged |
| Default data/log directory | `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\` |

Default directories are observations, not approved file paths or proof of free space. No filesystem content was inspected by the SQL batch. DB23 and all other user databases were outside this query's content scope and were not modified. No provider, Discord, RDP, restore, backup, import/export or production action occurred.

## Preserved failed attempt and correction

The initial attempt used `user_access=1` while requiring RESTRICTED_USER. This was an assistant-authored assertion error. Its own result row showed the correct protected state; the batch then raised error 51912. No change to DB22 was needed or made.

The corrected copy compares `state_desc='ONLINE'` and `user_access_desc='RESTRICTED_USER'`. All other SQL bytes are unchanged. The first attempt remains STOP_INCOMPLETE (six rows, 2,997 evidence bytes, 0.2200217 seconds; child exit 2, no timeout). It is not relabelled successful. The second attempt has its own directory, command hash, approval binding and receipts.

## Exact commands and controls

Both attempts reused byte-identical retained launcher and runner copies:

- Launcher SHA256: `e0479077d40e9bbe24fd33627cb98050db80b31cfc47ae2920af673346ae5eeb`.
- Runner SHA256: `5cea659af7b54f443c4b125a4ac32d2547de5b0856857deb1d0078ce9cacf0ee`.
- Initial SQL SHA256: `35d90c32e27637307bb8ac43717ce4cacafa31526fc24072bc12468f8f805729`.
- Corrected SQL SHA256: `3e28003e1e932a66eb8658d009f1b498071bad04f7c84aa08a12a511f2b2d91d`.
- Corrected operation manifest SHA256: `52d5854fd8c3f9b13a7b8710119a0aee79f3a2b455c9deaafbe9db9701ef5cd9`.

Operation ID: `CV4-MAIN-K98DEV-PREFLIGHT`; database allowlist: master only; effects: read. Existing Windows identity, exact server/original login, client file hashes and assembly identity are guarded before dispatch. The accepted development-only TLS setting remains encrypted with TrustServerCertificate true, per connection.

Budgets: one connection per attempt; 5-second connect timeout; pooling and retry disabled; 10-second batch timeout; 1-second lock timeout; 30-second runner wall bound with launcher termination after the additional 30-second allowance; at most 40 result rows and 65,536 JSONL bytes. The runner checks its wall bound between actions and rows; it is not a per-instruction hard deadline. The launcher captures terminal streams without a hard byte cap; no process memory or total-disk quota is claimed. Actual terminal output was bounded and the final evidence seal records every artifact size. No application rows were written and no storage was provisioned on SQL Server.

Commands were launched from each root's complete `sealed` directory with its newly bound `approvals/approved.json` using the pinned PowerShell executable. The approval reference is Chris's current explicit K98DEV selection followed by “proceed and try and resolve issues as you go until complete”; no old maintenance window or prior operation approval was reused. Both local manifests impose a fresh 30-minute validity bound. Preserve the now-used operation IDs and occupied attempt directories; do not replay them.

Roots:

- `.codex_artifacts/s11-k98dev-preflight-20261001/`
- `.codex_artifacts/s11-k98dev-preflight-v2-20261001/`

Each root retains separate working/sealed commands, preparation script, command manifest, preparation seal, approval and terminal/SQL receipts. A new combined result seal binds both attempts and this document. On unexpected state the operation stops and disposes its connection. These were catalog reads; no target rollback was required, attempted or inferred from disconnect.

## Remaining work, without inflated acceptance

The target-name issue and named signing-object collision check are resolved. This does not establish installed schema/signatures, permissions of a restricted application login, filesystem isolation, runtime registration or seven typed G4 proofs.

Source inspection confirms `verify_application_installation_contract` requires the full pinned application's object inventory, UDTs, definitions, dependencies and permission hashes. A minimal installation cannot satisfy that contract. Do not install every source-only object, weaken production checks, or call a limited SQL/report harness full runtime acceptance. The already completed minimal DB23 rehearsal need not be repeated merely because a new database name is available.

The real report comparison requires the actual nonsecret KVK16 DKP/configuration and kingdom/camp mapping (or an explicitly scoped unavailable aggregate result). Chris has been asked for the local configuration path. `config/[KVK].[sp_KVK_Get_Exports].txt` is an old procedure script, not the needed configuration values; authoritative SQL remains in the SQL repository. No weights, timestamps, camp map or production configuration were invented. The other cloud/writer/reference/runtime prerequisite gaps remain recorded in the configuration packet.

Disabled xp_cmdshell is an observed condition, not permission to enable it and not by itself proof that the selected KVK report path needs it. Legacy roots' filesystem effects require separate exact path/identity scope before execution. No new certificate, login, grant or proxy was created.

Skills used: K98 architecture scope, SQL validation and security routing. This turn's operational additions are finite read-only metadata queries and manifests using a retained pinned runner. Source review checked the exact SQL text and effects before execution; a new canonical Changes scan was not run for these artifact-only commands. This is a documented review limitation, not a fresh security-acceptance claim. No application behavior or SQL source changed; application tests and repository-wide validators were not rerun for this observational result. The earlier test/review qualifications remain intact.
