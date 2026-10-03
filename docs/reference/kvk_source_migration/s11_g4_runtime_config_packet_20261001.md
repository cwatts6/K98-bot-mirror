# S11 runtime configuration and metadata preparation — 2026-10-01

**The local preparation packet is complete. The runtime is not configured or activated.** This distinction is deliberate: source review found a target-contract mismatch and remaining evidence requirements that cannot be filled honestly with guessed values. No credential-content read, SQL connection, provider call, application import, new installation or production action occurred.

The deliverable is `C:\discord_file_downloader\.codex_artifacts\s11-runtime-config-packet-20261001\configuration-worksheet-final.json`. It contains supervisor v3, Bot v2 and deployment-boundary v3 drafts inside an explicitly non-runtime wrapper. Required unknown fields remain null. Do not extract these drafts into active configuration or set an activation flag.

## Confirmed and retained bindings

| Binding | Value / evidence |
|---|---|
| Local host/account | `9SX2VF4`; Chris SID `S-1-5-21-3167111192-3307161013-4064290451-1001`; `single_account_application_v1` |
| Protected interpreter | `C:\K98-S11-Validation\python-env\Scripts\python.exe`; dependency evidence remains separately qualified |
| Protected provider child | `C:\K98-S11-Validation\app\scripts\run_export_provider_child.py` |
| Credential path | `C:\K98-S11-Validation\credentials\statsupdate-0d8b70356ef2.json`; successful RDY-K01 move receipt |
| Evidence root candidate | `C:\K98-S11-Validation\evidence`; source provisioning retained, no new current observation |
| Service account/project | `sheets-service@statsupdate.iam.gserviceaccount.com` / `statsupdate` |
| Expected client ID | `103175311864208640064` |
| Expected key ID | `0d8b70356ef2fb1ea002daac8e9533463aab5d18` |
| Expected credential SHA256 | `d23b77b3acb2aa1999c73fd4fce44e04613570d83ceb1955507125672c48a609` |
| Custody observation | `2026-10-01T14:40:52.4081211Z`, file identity `0499764a:008300000005476d`, 2,355 bytes, protected Chris/SYSTEM/Administrators access |
| Provider metadata provenance | Sealed CV3 `identity.json`, SHA256 `54565c94bf186f15b6974bd894c04e21e7894ebd63109a14d060fc0024d5d5d2`; historical 2026-09-29 observation |
| Source inventory | All 549 workspace source members match the retained protected-source plan; no fresh protected-tree observation claimed |
| SQL source inventory | All 540 declared members match authoritative SQL files using the established CRLF-to-LF hash domain; digest `f082cd0cbf28261cddf966a954a4564d34a81a552d796707eb90dc75a6baf3cf` |

The client ID, key ID and expected hash were already available in retained evidence. They were verified against that record's seal, not inferred from the key filename or obtained by reopening the key. The actual key hash has **not** been remeasured after relocation. RDY-K01 proves the move's file identity/size and protection, not a fresh cloud key inventory. Keep the CV3 child-exit qualification; retained successful responses are not a clean launcher-exit claim.

All five supplied spreadsheet IDs, grid 0, owner `chrislos35@gmail.com`, existing service-account Editor and public anyone-with-link Viewer policy are carried into the worksheet. Nine known protected exclusions remain listed, with complete reference/exclusion closure explicitly false. Historical blank `Sheet1` dimensions remain historical, not asserted current. No file needs manually added columns, headers or tabs for this preparation.

The accepted statements “only production and this machine hold the key” and “none” for local consumers remain settled. No repeat holder/consumer question is needed, and no workspace credential copy should be recreated.

## Concrete SQL target blocker

`services/export_runtime_composition.py` requires `approved['database'] == 'ROK_TRACKER'` in both `validate_application_installation_contract` (line 1032) and `validate_legacy_installation_contract` (line 1172). Bot setup also requires all SQL contracts to identify the same server/database/principal. The general execution contract accepts a named database, but that does not override these two stricter contracts.

The completed disposable rehearsal target is `K98_S11_Disposable_20260929_CV01`, database 23. It cannot be substituted into these full application contracts unchanged. Its successful minimal SQL cases also do not prove the full application schema, signature, permission and dynamic-output inventory.

Do not relabel DB23 as ROK_TRACKER, adopt an existing database, rename or repurpose DB22, or remove the guards in a local manifest. The next source/target decision must resolve this incompatibility before an installation or runnable manifest can be finalized. Two distinct approaches require review: a narrowly scoped development-target contract amendment, preserving the production contract, or a genuinely disjoint environment compatible with the existing database-name contract. Neither is implemented or provisioned by this packet. A source inventory is not an instruction to install all 540 objects.

Authoritative SQL source was read for manual enrollment and KVK export contracts; the full declared inventory was hash-checked. The manual enrollment procedure requires its own short transaction, exact session/owner/fence state and authority role. It writes registration evidence. It must not be invoked as a read-only metadata test. No SQL source changed.

## Remaining bindings — no fabricated acceptance

The worksheet includes an explicit eight-item ledger:

1. **SQL target compatibility** described above.
2. **Installed application contract:** effective principal/capabilities, metadata, signatures, dynamic objects, migration evidence and review identity.
3. **Cloud identity evidence:** current user-managed key status/list and issuer/admin/impersonator closure. An existing authorized read identity and exact service-account/project/inherited role/group targets must be established before a bounded IAM operation can be finalized. No personal connected Drive identity, new OAuth consent, new account/key or permission grant is assumed.
4. **Holder/writer closure:** retain both known host copies. The source expects a sole reviewed authority SID in the typed key record; the two-machine statement must not be silently converted into that record without resolving host/SID/custody interpretation. “No local consumers” is not production drain evidence or an exited-process ledger.
5. **Runtime process identity:** actual Bot/authority incarnations, native handles, token profiles, pipe and deployment/review IDs. No historical PID adoption or second Bot.
6. **Registration and references:** account/storage-owner keys, pool identity, complete legacy destination configuration, protected/reference/uncertain outputs and eligible capacity. Do not invent a pool UUID or hash as if registered.
7. **Final host/configuration closure:** exact protected config, spool/evidence paths and full source/dependency/ACL bindings. Prior selected checks remain supporting evidence, not a complete typed proof.
8. **Report expectations:** accepted B0 and Pass 4 player input evidence is retained. Actual DKP/config identity, intended report scope and authoritative Kingdom/Camp aggregate inputs or explicit unavailable coverage remain necessary for the real demonstration.

All seven typed G4 records are left incomplete. Review administrator labels identify Chris, not an observed Google Cloud login or grant of authority. No timestamps or source-record hashes were manufactured for missing observations. Runtime registration, deployment identity, process bindings, SQL metadata/signatures and configuration hashes remain null where unresolved.

## Exact local operations performed

Only these offline commands were executed, from `C:\discord_file_downloader`:

```powershell
& 'C:\Program Files\Python311\python.exe' -I -S -B .codex_artifacts/s11-runtime-config-packet-20261001/prepare_packet.py
& 'C:\Program Files\Python311\python.exe' -I -S -B .codex_artifacts/s11-runtime-config-packet-20261001/finalize_worksheet.py
```

| Command | SHA256 |
|---|---|
| `prepare_packet.py` | `2a53036e06b42a7f69ccf06ab5d096dcc46760207bd06b3afb6bae51f7b87001` |
| `finalize_worksheet.py` | `234e1bd25fe97d1f9491786d4c3c71badd22385933a7155a5f7f1271851e61e9` |

The first command uses a finite source/evidence list: 549 `.py` source members, 540 declared `.sql` source members, the selected sealed identity record, 11 key-move execution-seal members and local supporting manifests. It verifies sizes/hashes and statically inspects the two database-name checks. Inputs are bounded at 4 MiB per read. Credential and `.env` seal members are expressly refused. It performs no application import or network operation and writes only new local report/worksheet files using exclusive creation.

The second command reads the verified worksheet and derives the inert supervisor/Bot/boundary drafts and missing-binding ledger. It checks expected field sets, versions, all 549 source pins and deliberate absence of typed acceptance. It does not call runtime validators that could inspect a host or connect to SQL.

Observed command elapsed times were approximately 1.56 seconds and 0.18 seconds. There was no runtime lock or live request; these are measured local durations, not watchdog guarantees. Zero SQL rows, provider/authentication requests, credential bytes, or target storage changes. Generated worksheets/reports total less than 256 KiB before command-copy/document/seal storage. No global memory/disk quota is claimed.

Both scripts refuse existing output files; preserve this completed run rather than replaying it into occupied paths. Any mismatch stops local preparation. Reads require no target rollback, and partially generated drafts must remain inactive. Separate sealed and working command copies and a new result seal retain the completed local packet. No executable IAM, migration, registration or export operation is supplied while its prerequisite bindings remain unresolved.

## Validation and scope

`offline-verification.json`: 12 retained evidence members matched, 549 workspace source members matched, 540 authoritative SQL source members matched, two explicit database-name constraints confirmed. `worksheet-validation.json`: expected draft versions/field sets passed; `runtime_manifest_valid=false` is intentional. These results are not installed-state or provider acceptance.

Skills applied: K98 architecture scope and SQL validation. Security-routing decision: documented skip for this new inert documentation/worksheet and finite offline source/hash bookkeeping. No application behavior, live configuration, permissions, secrets, dependencies or SQL source changed. No new runtime test, architecture/deferred/security-routing validator or security scan was needed for this preparation-only result; previous failures and bounded-review limitations remain open. No new implementation helper, refactor or deferred optimisation item was introduced.

Production remains the isolated hotfix. Preserve DB22 ONLINE/RESTRICTED_USER/read-only/Broker-disabled and its 119 media files, DB23 evidence, all original inputs and seals, S6/S8, uncertain publications, the shared-account amendment and the withdrawn collector. Real registration, two-export execution, controlled rollout and G5 are separate decisions, not acceptance implied by these drafts.
