# RDY-K01 local key transition result — 2026-10-01

**Completed once: MOVED_PROTECTED**, at `2026-10-01T14:40:52.4081211Z`, following Chris's explicit approval of the [exact RDY-K01 packet](s11_g4_key_transition_packet_20261001.md). No retry or recovery action was needed. Preserve the occupied staging/evidence directories; never rerun the one-shot command.

## Confirmed result

- Existing file moved from `C:\discord_file_downloader\statsupdate-0d8b70356ef2.json` to `C:\K98-S11-Validation\credentials\statsupdate-0d8b70356ef2.json`.
- The held file's identity, volume, single-link status and 2,355-byte length were preserved. The operation checked the old path was absent and the held final path was the exact destination.
- File inheritance is protected. Only Chris SID `S-1-5-21-3167111192-3307161013-4064290451-1001`, SYSTEM and Administrators have FullControl. Owner/group were retained. Workspace, drive-root and existing application directory ACLs were not changed.
- Three protected command directories and seven nonsecret command/approval files were staged under `C:\K98-S11-Validation\key-transition-rdy-k01` before execution. Exact verified buffers were used, closing the reviewed workspace command-load race within the existing trusted-account model.
- No credential-content read, content hash, copy, replacement key, old-path alias or provider request occurred. Native operations used metadata, descriptor and rename access only. File-ID/size preservation is not a separately measured content hash.
- Chris's statement that no local consumers depend on the old path remains accepted. No `.env`, legacy startup task or runtime manifest was changed. Any future local consumer must explicitly use the protected path; do not recreate a workspace copy.

The file remains the existing service-account key. This workflow did not read its client/key identifiers or check its cloud status, and did not revoke cached tokens or other copies. Production's copy and serving hotfix `bd980c0f497faf2048eaf1fb6b79600662911763` were untouched.

## Receipts and measured bounds

| Stage | Exit/capture | Elapsed | Peak sampled working set | stdout / stderr |
|---|---|---:|---:|---:|
| Protected command staging | Exit 0; termination and capture complete | 1,116 ms | 171,749,376 bytes | 255 / 0 bytes |
| Protect and rename | Exit 0; termination and capture complete | 795 ms | 166,461,440 bytes | 1,419 / 0 bytes |

No timeout or output overflow was reported. Working-set values are sampled observations, not kernel quota proof. These timings cover the two child operations, not all approval preparation and receipt preservation.

Move stdout retains all three phases: `LOCKED_PREIMAGE`, `PROTECTED_AT_SOURCE`, `MOVED_PROTECTED`, with the same file identity. Launcher status is `MOVED_PROTECTED`; approval and six command hashes are retained. Receipt copies were compared by SHA256 with their protected originals; the key itself was not hashed.

Evidence root: `C:\discord_file_downloader\.codex_artifacts\s11-key-transition-packet-20261001`.

- Original preparation seal: `result-seal.json`, SHA256 `387ced996f7cd63bf8c9a48f59e2286c09c34df454d5e295ab216d43fc6ce03f`. All 58 members matched before execution; original seal retained.
- Approval: `approval-RDY-K01-attempt01.json`, SHA256 `f255d73a0b7bce0d39ddcbc5dde92936a77fc23c52f81de9ff4c3a0a816f8496`. Fresh 30-minute interval; no historical maintenance window reused.
- Complete approved command body: `invocation-approved-attempt01.txt`, SHA256 `52a6a4b49ae733a5c615d61f8d122fb0266d7f65a4e6a74f898d0f56593ac40b`.
- Staging receipt files: `staging-observations/RDY-K01-stage-attempt01/`.
- Preserved nonsecret move receipt copies: `execution-evidence/`.
- Protected originals: `C:\K98-S11-Validation\key-transition-rdy-k01\observations\RDY-K01-attempt01\`.
- A separate execution seal binds the new approval/invocation/receipts and this result. Prior fixtures, rejected drafts, reviews and seals remain unchanged.

## Remaining boundary

The local key-location/permission transition is complete. The protected application is still inactive. No SQL session, migration, provider registration, real import/export, Bot start/restart/deployment or G5 acceptance occurred. All seven complete typed G4 proofs remain pending; this result is supporting custody evidence only.

Next preparation can bind this confirmed path into the future exact manifest. Actual credential identity/hash and cloud inventory, complete application SQL contract, process/writer state, protected-file/reference closure and report-equivalence execution still need their own bounded evidence. Do not fabricate those values from this receipt or bypass readiness checks.

Preserve DB22 ONLINE/RESTRICTED_USER/read-only/Broker-disabled and all 119 media files, DB23 and its synthetic evidence, accepted input files, S6/S8, uncertain publications, pending/recovered source and the shared-account amendment. The withdrawn collector remains withdrawn.

No source/test/SQL change was made in this execution turn. The exact reviewed packet was executed unchanged; no further runtime tests or security scan were needed to document its receipts. The packet's bounded independent-review/canonical-scan qualification remains explicit.
