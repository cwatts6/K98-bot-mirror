# RDY-K01 — existing local key transition packet

Prepared and rehearsed locally, **not executed against the real key**. Chris answered **“none”** to the local-consumer question. This settles that fact; do not ask again. Existing two-machine holder statement and shared-account design remain accepted. No local consumer config edit, production key change or new key is proposed.

This packet replaces the unresolved command/staging portion of the [earlier preparation](s11_g4_credential_transition_preparation_20261001.md). Earlier documents and seals remain historical evidence. The previous maintenance window is not reused.

## Exact operation and effects

One approval, **RDY-K01**, covers the two dependent stages below on host `9SX2VF4`, as Chris SID `S-1-5-21-3167111192-3307161013-4064290451-1001`.

| Stage | Exact targets and effects |
|---|---|
| Protected command staging | Exclusively create `C:\K98-S11-Validation\key-transition-rdy-k01`, its `working` and `observations` directories. Atomically grant only Chris, SYSTEM and Administrators FullControl. Write six verified nonsecret command/preimage files and the exact approved receipt. Existing target or partial prior attempt means stop; never merge or overwrite. |
| Existing-file transition | Protect and rename `C:\discord_file_downloader\statsupdate-0d8b70356ef2.json` to `C:\K98-S11-Validation\credentials\statsupdate-0d8b70356ef2.json`. Preserve file ID, volume, byte length and single-link identity. Change only that file's DACL to protected Chris/SYSTEM/Administrators FullControl, retaining owner/group. No credential-content read, copy, hashing, deletion or key replacement. |

The destination filename is proposed, not reserved. Ancestors `C:\`, `C:\discord_file_downloader`, `C:\K98-S11-Validation` and its `credentials` directory are held open without delete sharing during the actual transition. Their permissions are checked but not changed. The key is held exclusively through protection and rename. Destination overwrite is disabled in the native rename call. No old-path alias, symlink or junction is created.

Zero SQL/provider/Discord requests or target rows; no Bot startup, deployment, restart, environment/configuration edit, token refresh or process enumeration. Production remains isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`. The application candidate remains inactive. The operation does not revoke cached credentials, tokens or other copies; the existing account/process-family trust model remains explicit.

## Preconditions and approval binding

- Exact reviewed command bytes below; trusted pinned PowerShell installation and trusted inline invocation.
- Fresh explicit RDY-K01 execution approval with Chris, review complete, local consumers `none`, a retained approval reference and a new interval of at most one hour. The interval is created only when execution is approved; no window is needed for this preparation.
- Retained H02 owner/group/allow-entry preimages for drive, workspace and key. Only ordering of identical ordinary allow entries is ignored. Owners, groups, control flags, ACL revision, entry multiplicity, SID, access mask and ACE flags must match. Deny, callback, opaque or unfamiliar entries refuse. Current private destination directories must satisfy the three-principal protected policy.
- Canonical paths, no reparse point, same volume, one file link, nonempty file at most 65,536 bytes, absent destination and no sharing conflict. The file's pre-move ID is captured under its exclusive handle, then checked after mutation. Historical ACL matching is not content authentication or a key-ID inventory.
- Existing protected runtime/dependency evidence remains retained; this operation does not claim its complete trust closure or any typed G4 proof.

The approval template is deliberately false. Do not interpret a JSON boolean as human authorization. A real receipt must be created under a new filename only after the operator decision, and its digest bound into the trusted invocation. Execution may not substitute another source/destination or broaden the read set.

## Commands and exact hashes

Packet root: `C:\discord_file_downloader\.codex_artifacts\s11-key-transition-packet-20261001`.

Complete command copies are under `working/` and `sealed/`; bootstrap/staging copies also appear under `sealed-bootstrap/`. `invocation.txt` supplies the full trusted inline command. Its only unresolved value is the digest of the not-yet-approved receipt. The inline command reads bootstrap once, hashes that buffer and evaluates the same buffer. Bootstrap likewise verifies/evaluates stage/helper buffers, avoiding a hash-check/path-load race. The protected stage copies only verified in-memory payloads before launching from the protected directory.

| File | SHA256 |
|---|---|
| `bootstrap.ps1` | `0a2b4b10d9680fe3b10fc97b0c0084fde3a52bf877286a78191b6afd60737d28` |
| `stage-protected-command.ps1` | `2cdd088806b50d50d149e96f94db8099949387cad3b505330f3bf8c523a00bba` |
| `launch-key-transition.ps1` | `65941e61fcd0826f6316a737bc76354c5ba01d38d663054c116ac777f6aab62a` |
| `move-local-key.ps1` | `049937a4c96f8e1ab35d7fc381afce6384deccde87a90651382543b3b8ec06df` |
| `native-key-file.cs` | `27d5bbb935e975bf6ab3e4f3fe3fe5cae98a9fe8693b96136211d18d49282f5b` |
| `transition-core.ps1` | `0b9a200b8003b159b3cb74f8932cd4746780119b625537adb921f5c7ca3f7265` |
| `preimages.json` | `6116914bb59339a066a5e20a8a1ceaa4d0fce3a648d35678e6966124da60d142` |
| `bounded-process.ps1` | `188c1baf10fcb9668c21239eba57344842a628ba19512517f6089c4adfb1c479` |

The native design uses handle-based [security-descriptor reads](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-getsecurityinfo) and a [non-overwriting rename](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_rename_info). Source file access requests exclude content read/write; directory handles include LIST_DIRECTORY solely to establish the tested sharing reservation, with no directory enumeration.

## Budgets and evidence

- Stage: ten-second cooperative creation/write deadline, 15-second owned-child watchdog. Six input payloads at most 64 KiB each, approval at most 16 KiB; three new directories/seven new nonsecret files. No recursive collection.
- Move: one file, one DACL change, one rename, at most four held ancestors plus the key. 30-second owned-child watchdog; file size capped at 64 KiB but zero content bytes read. Locks are held only for the owned operation lifetime.
- Each child: 64 KiB stdout, 8 KiB stderr, sampled 512 MiB working-set threshold. Up to five seconds termination and five seconds capture wait follow the watchdog. These are not a kernel memory quota or a hard end-to-end deadline; bootstrap input/hash setup occurs outside child watchdogs.
- Allow 1 MiB regular-file storage for bounded payloads/receipts/capture plus filesystem metadata. Per-input/output caps are enforced; there is no volume quota or preallocated disk reservation. Disk/receipt failure leaves an uncertain outcome requiring reconciliation.
- Stage capture: packet `staging-observations/RDY-K01-stage-attempt01`. Move capture: protected operation root `observations/RDY-K01-attempt01`. Fresh paths only.
- Successful move stdout is three JSON lines: `LOCKED_PREIMAGE`, `PROTECTED_AT_SOURCE`, `MOVED_PROTECTED`, with UTC, file identity, path, size and descriptors. The historical `stdout.json` capture filename contains JSON Lines here; the launcher parses linewise. Process and launcher receipts bind exit, termination/capture completeness, approval digest and command hashes. No private key, token or credential JSON is emitted.

## Stops and recovery

Any mismatch, occupied destination/staging/evidence directory, unexpected descriptor, hard link, reparse path, sharing conflict, deadline, output overflow, failed readback or uncertain process result stops without retry. A renamed file is never recreated at the old path. An occupied old path during final readback is a stop, not permission to delete it.

Preserve partial stage directories and every receipt. If protection was attempted but rename did not complete, retain the existing file and reconcile its actual ACL/path. If rename completed but capture/readback failed, keep the protected destination and reconcile its file ID before any further action. No automatic rollback restores broad permissions or moves a key back; no cleanup, duplicate key or Bot start is a recovery step. Timeout can interrupt between phase receipts, so absence of the final line does not prove absence of a mutation.

## Rehearsal and review evidence

- Eight native dummy cases passed in `fixture-attempt03`: file-ID/content preservation, phase records, early/late collisions, stale descriptor, multiple links, open reader and held-parent rename refusal.
- Six additional dummy guard cases passed in `fixture-additional01`: empty/oversized file, wrong volume, missing destination parent, reparse directory and unexpected principal.
- Nine offline descriptor comparison cases passed: identical allow-entry reordering accepted; changed rights/SID/flags/owner/group/control, deny and duplication refused.
- Protected staging passed in `fixture-stage02`: three protected directories, seven verified files. Source/destination literals and three executable payload hashes were replaced with inert synthetic payloads. No operational launcher ran in that rehearsal.
- Both real command entry points refused the unapproved receipt; final PowerShell syntax checks passed. Bootstrap is verified statically, not executed as an integrated real-key workflow.
- Preserve `draft-v1`, `draft-v2`, `fixture-attempt01` and `fixture-stage01`: initial metadata-only directory sharing failed a test, and literal SDDL ordering caused staging refusal before target creation. Corrections and successful fresh attempts do not erase these outcomes.

Security routing is Changes intent, Deep off, bounded independent review of this artifact-only packet. The native scan's unsupported artifact-baseline qualification remains; supporting review is not a canonical completed scan. Review reports and final hashes are retained in this packet. Source application/SQL code was not changed. Broad repository validators and runtime suites were not repeated because this is an isolated operational packet, with native and negative tests specifically covering its new behavior; no PR/publication is being handed off.

## What completion would establish

RDY-K01 success would establish this local file's protected move and retained file identity. It would not establish credential contents/cloud key status, complete host trust, writer drain, full application SQL installation, provider registration, report equivalence, any complete typed G4 proof or G5 acceptance. Those remain the next separately bound operations. Preserve DB22 read-only/restricted/Broker-disabled and its 119 media files, DB23 evidence, historical Sheets/uncertain publications, all source/input/seal history, S6/S8 and the withdrawn collector.
