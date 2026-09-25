# Environment Reference

## Current delivery and next phase — 2026-09-25

S11 Bot mirror #281, SQL #89 and production Bot #588 are merged. See the
[source closeout and exact manifest](kvk_source_migration/s11_closeout_and_g4_handoff.md) for delivered behavior, review
corrections, source pins and the mirror publication repair follow-up. Production deployment,
SQL installation, provider behavior and G5 acceptance are not established by these merges.

Next: **G4 plan development only**, using the [new task pack](../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S11%20G4%20Release%20Planning%20Controlled%20Rollout%20and%20G5%20Acceptance.md) and
[chat starter](../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S11%20G4%20Release%20Planning%20Controlled%20Rollout%20and%20G5%20Acceptance.md). Controlled rollout executes only specifically approved
operations; G5 remains operator-owned. Earlier dated checkpoints below retain their original
scope/status as historical evidence, including headings used by existing links. They do not
reopen implementation or authorize live operations. Preserve S6/S8 gates, uncertainties and data.

## S11 client pipe access correction — 2026-09-25

Both the Bot client and supervised provider child use the same message-pipe opener. Its
explicit access mask, also used by the server's client DACL entry, is 0x120103: read/write data,
read control, synchronization and FILE_WRITE_ATTRIBUTES for selecting message-read mode.
It excludes FILE_CREATE_PIPE_INSTANCE (0x4). Mode-setup failure closes the just-opened handle,
including interruption. These are source and fake-native test results; actual access checks,
message mode, server identity, cancellation and recovery still require the exact G4 host.

## S11 authority launcher preconditions — 2026-09-25

The three explicit G4 entry files (run_export_authority.py, run_export_provider_child.py and
enroll_export_output_pool.py under scripts) and the isolated Python/pywin32 installation are
administrator-verified deployment trust roots. Launch with -I. Child and enrollment load the
shared authority launcher by exact .py filename before making application packages importable.
This is not a mechanism for validating a launcher that was already replaced before execution.

Provision a reviewed source-only application tree: no native application modules, adjacent
sourceless bytecode or populated application __pycache__ directories. Bootstrap checks the
protected manifest and full source hash inventory, and checks each executable source directory
as a protected leaf so untrusted create-file/create-directory rights are rejected before imports.
Bytecode writing is disabled after that check. No cleanup or deployment is performed here.
Existing administrator/authority ownership, private credential/evidence paths and reparse-point
refusal remain required. General drive ancestors retain replacement checks; their unrelated
child-creation rights are not confused with rights inside the executable source tree.

Bot-facing authority pipe accept, whole-frame read and reply write each have a 30-second I/O
deadline. Broker/provider processing is outside that transport deadline. Timeout or disconnect
does not release claims or authorize a retry; the caller retains reconciliation uncertainty.
Actual Windows overlapped cancellation and the next-client recovery cases require G4 evidence.

## S11 protected runtime manifest — 2026-09-24

K98_EXPORT_RUNTIME_MANIFEST is a local absolute path to the independently reviewed, administrator-
owned Bot-readable runtime manifest. It is consumed only when EXPORT_COORDINATION_ENABLED is true;
missing or mismatched readiness keeps the actual factories closed. Do not set it or enable flags
as part of source authoring. The version-1 Bot manifest has exact fields version, authority,
registration, sql_contract, legacy_sql_contract, application_sql_contract, spool_root, source_hashes,
export_config_file and export_config_sha256. authority pins host, authority_sid, bot_sid, pipe_id
and deployment_hash. Source/config/manifest must not be writable by the Bot identity; spool is an
existing private Bot-owned directory outside Git. No credentials are loaded by this factory.

Normal authority manifests are version 2 and require deployment_boundary plus runtime_registration.
Enrollment retains its separate version-1 manifest/enrollment_profile. Never substitute one for
the other. Both are explicit operator tools; no launcher or provisioning runs at Bot import/startup.
The fresh provider key/client identity and seven protected G4 records are exact hashes in the
boundary. See the current integration contract and release readiness packet for custody and G4.


## S11 legacy SQL permission contract — authored 2026-09-24

The approved local permission addition introduces no automatic runtime enable flag or credential
default. LegacySnapshotDAL(execution_evidence=True) requires a protected legacy_sql_contract:
version 1, exact server/database/principal, the source-pinned SQL permission manifest, certificate
thumbprint/public-key hashes, per-module signature hashes, migration hash and metadata fingerprint.
The supported source resolution is SQL Server 2022 / ROK_TRACKER / dbo default schema. Expected
values come from independently approved source and a G4 packet, never from live observation or
Bot IPC. No private signing key belongs in this contract. The existing coordination contract's
version remains 2; the legacy gate does not activate the still-closed production factory.

The separately disabled legacy SQL test fixture uses K98_S11_LEGACY_SQL_AUTHORIZED with exact value
S11_EXACT_LEGACY_PERMISSION_TESTS_APPROVED, K98_S11_LEGACY_SQL_APPROVAL_FILE (absolute local path),
and K98_S11_LEGACY_SQL_APPROVAL_SHA256. These are G4 test inputs, not instructions to set them now.
The private packet includes the exact isolated instance, restricted connection, original manifest,
backup/actual restore evidence and four named operations. Do not reuse production/S6/S8 data or
the ordinary S11 evidence fixture's database for these legacy-body tests. Local offline runs keep
this authorization disabled. See release_readiness_and_rollback for the unchanged operator gates.

## S11 SQL permission contract version 2 — 2026-09-24

Both normal authority and fresh-file enrollment manifests now require version 2 inside their
approved SQL installation contract. The outer manifest and enrollment_profile still use version 1;
these are distinct version fields. Version 2 binds the exact target, restricted principal,
migration hashes, independently approved metadata fingerprint and fixed effective export permissions.
No environment flag grants readiness and no live observation may supply its own approved fingerprint.

The authority profile includes durable budget writes and coordination/origin reads plus restricted
evidence-procedure execution. The reader profile includes the Bot's existing coordination writes
as well as evidence reads. Object and every-column SELECT/UPDATE observations must match the fixed
source-derived map; direct evidence mutation and extra ownership/DDL permissions are rejected.
This bounded contract does not certify broader import/configuration SQL or complete writer coverage.
No manifest, credential, SQL grant or deployed configuration was created or changed here. See the
[source and remaining readiness record](kvk_source_migration/release_evidence_log.md#s11-fixed-coordination-permission-contract--2026-09-24).

## S11 enrollment profile contract — 2026-09-24

Source authoring only; no environment or credential has been provisioned. The separate enrollment
manifest uses all protected authority identity/source/storage/SQL fields, replacing
`runtime_registration` with `enrollment_profile`. That exact profile contains version 1,
owner_email, client_id and the sole scope https://www.googleapis.com/auth/drive.file. The ordinary
service-account manifest/profile remains distinct. Neither profile permits credential fallback.

An external authority-private authorized_user credential file must contain exactly type, client_id,
client_secret, refresh_token, token_uri and scopes; token_uri is https://oauth2.googleapis.com/token,
client_id and scopes must match the protected profile. Cached access tokens, broader scopes,
service-account substitutes and delegated credentials are rejected. Refresh happens before the
sole provider send; an absent or broader granted_scopes result blocks send and needs G4 investigation,
never inferred permission. Actual credential access, consent and provisioning need exact G4 approval.

The separately protected plan binds the raw manifest SHA-256 and canonical profile SHA-256, version,
purpose output_enrollment, account, storage_owner, owner_email, editor_email, project_id, file_count
3–17 and plan_id. SQL hashes canonical plan JSON as UTF-16LE. Source/profile hashes alone do not prove
old-writer exclusion, live containment or historical provider finality. No actual path/token/value
has been selected by this source contract; do not place private inputs in Git.


## S11 protected authority inventory — 2026-09-24

The independent authority launcher now requires runtime_registration in its protected manifest:
version, account, spool storage_owner, service_account_email, complete legacy_configuration
(all_kvk/scan_data/config), all one-through-eight pools and sorted protected_file_ids. Each pool
binds pool_id, registration_sha256, index_file_id, two-through-sixteen slot_file_ids, owner_email
and explicit audience. All pool files must be unique and disjoint from protected/shared files.
This is an immutable scope binding, not old-writer exclusion or installation/finality proof.
No actual environment, credential, manifest or bot-machine configuration was changed.

Normal runtime factories remain closed pending complete trusted issuance/composition/readiness.
The [proposed initial enrollment extension](kvk_source_migration/integration_contract_and_consumer_matrix.md#s11-initial-file-enrollment-additional-implementation-proposal)
would add an independently protected human-authorized creation profile; that credential capability
and origin persistence are not approved or implemented here. Do not provision credentials or enable
exports from this source checkpoint. Exact G4 operations and G5 acceptance remain separate.


## S11 implementation status — 2026-09-24

S11 independent-authority configuration is not deployable yet: the validated authority launcher and complete composition are unimplemented. Do not infer readiness from source files or enable exports. No actual environment or credential configuration was changed. See [checkpoint](kvk_source_migration/release_evidence_log.md#s11-approved-implementation-checkpoint--2026-09-24).


## Current status — S10E merged; S11 review/scope next, 2026-09-15

S10E Bot [mirror #280](https://github.com/cwatts6/K98-bot-mirror/pull/280),
[production #587](https://github.com/cwatts6/k98-bot/pull/587) and
[SQL #88](https://github.com/cwatts6/K98-bot-SQL-Server/pull/88) are merged and locally pulled.
Bot main/origin main `721ad7e0cd6b160ddddad328c2338a98bdfb6e0a`; production/main `3dbe63e7a47175df85ed17814ea06f9dd3d130b7`; SQL main/origin main `2352a898881d4b74d6eec153bb3cb381d6162041`.
**No changes have been pulled to the bot machine.** Repository delivery is complete;
SQL installation, real provider/Discord execution, runtime acceptance and activation remain unproven.

Next: **S11 Controlled Release and Acceptance, initial review/scope only**:
[task pack](../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md) and [starter](../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md).
Read the [S10E closeout and exact next-PR manifest](kvk_source_migration/s10e_closeout_and_s11_handoff.md).
S11 starts from S7's eight-document release proposal plus mandatory carry-forward docs;
reconcile real composition/installation/operational gaps before proposing any runtime scope.
Its eventual authorized Bot PR MUST include every listed pending document, both S10E archive
move identities, this closeout and S11 pack/starter. Verify filename AND previous_filename,
exact content and absent-at-base proof; counts are insufficient. No standalone docs PR,
mixed repositories or manufactured implementation. Pending SQL closeout edits belong only
in the next genuine authorized SQL implementation PR; otherwise carry them forward.

Preserve all recovered documentation evidence, S6-OPS01/PERF01/CAP01, both uncertain publications
and retained data. S8A six scripts, S8B 50 cases/actual restore versus offline history, and S8C
seven local checks remain distinct. S10C/D/E static authoring is not installation/provider proof.
No predecessor rerun, SQL/provider/Discord operation, bot-machine pull/restart/deployment,
activation, new task creation or Git publication is authorized by this documentation closeout.
Earlier dated pending/next-slice instructions are historical and do not reopen accepted work.

## S10E local authoring — 2026-09-15

S10E adds no production environment setting, ProcConfig activation row or automatic provider
client. `configured_operator_service()` remains closed. Future explicitly authorized composition
must inject the exact registered pools, complete accepted-generation loader, shared coordinator
with preparation/output-operation ownership enabled, all compatible writers, durable request
budget, and independent termination/readback verifier. An environment flag or SQL job state
cannot attest installation or old-writer termination. Existing protected configuration files,
S10C snapshot/header/provenance capture and durable spool ownership remain unchanged.

`tests/test_kvk_export_sql_integration.py` authors a separate, disabled S10E execution gate.
`K98_S10E_SQL_AUTHORIZED` must equal `S10E_EXACT_DISPOSABLE_OPERATIONS_APPROVED`, with the exact
`K98_S10E_SQL_SERVER`/`K98_S10E_SQL_DATABASE`, backup and actual restore evidence. Its reviewed
disposable database pattern is `K98_S10E_Disposable_YYYYMMDD_validation`. Distinct seeded case
identities are required by `K98_S10E_READY_OPERATION_ID`, `K98_S10E_CAS_OPERATION_ID`,
`K98_S10E_CONTENTION_OPERATION_ID`, `K98_S10E_CONFIRM_POOL_ID` and `K98_S10E_CONFIRM_NEW_KVK`.
Those strings document an authored gate; setting them is not authorization. S10B/S10C gates
are independent and remain disabled. No live SQL/provider/Discord test was authorized here.

The current implementation and evidence boundaries are in the
[S10E pack](../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md).
Earlier scope/closeout entries below remain historical.

## Historical S10D closeout — 2026-09-15

SQL #87 is merged and locally pulled at `80353a6280e523f30c27e724f71e7b47dadadd16`.
Bot main/origin main remains `bf3eccf964601e2975dd86eefe96f7b0153be3bb`; production/main remains
`aa1821adbde9ccda47797caa83b5d5a9958bfce9`. **No changes have been pulled to the bot machine.**
S10D authoring, offline checks and Changes security review are complete; SQL installation and
provider/Discord execution are not established. S10C remains source/static SQL evidence too.
See [S10D closeout and exact carry-forward manifests](kvk_source_migration/s10d_closeout_and_s10e_handoff.md).

Next: **S10E Export Operator UX and Rollover, initial review/scope only**:
[task pack](../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md) and [starter](../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md).
The eventual authorized S10E Bot implementation PR MUST include every pending Bot document in
that closeout, this pack/starter and all required archive identities. Verify filename AND
previous_filename, or exact merged/content and absent-at-base proof. No standalone docs PR,
repository mixing, manufactured implementation or renewed predecessor/grouping approval.
Both SQL documents were delivered in #87; their new closeout edits stay in SQL for the next
actual authorized SQL implementation PR. S10E scope must assess any genuine SQL delta separately.

Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and every retained database/file.
S8A six scripts, S8B 50 cases/actual restore versus offline history, and S8C seven local checks
remain distinct; none is new live Discord or deployment evidence. Shutdown stops admission and
drains owned delivery; uncertainty retains claims. No lease-age/job-state release.
This documentation closeout authorizes no implementation, Git publication, SQL/provider/Discord
execution, real import/export, bot-machine action, deployment, activation, predecessor rerun or
new task. Earlier dated checkpoints are historical; the current closeout controls the next step.

Purpose: document the environment variables and runtime configuration points used by the bot.

Primary code sources:

- `bot_config.py` for typed Discord/config environment variables
- `constants.py` for path, SQL, and file constants
- `logging_setup.py` for logging-related environment handling
- `scripts/config_self_test.py` and `scripts/validate_env.py` for validation examples

## Required

### DISCORD_BOT_TOKEN

- Type: string secret
- Used by: `bot_config.py`, `DL_bot.py`, Discord client startup
- Notes: Required for normal bot operation. Never commit real tokens.

## Required For Normal Bot Startup

### WATCHDOG_RUN

- Type: `1` for supervised bot startup
- Used by: `DL_bot.py`, `scripts/smoke_imports.py`
- Notes: Normal bot startup exits when this is missing. Smoke/import validation sets it safely.

## Common Production / Local Variables

### GUILD_ID

- Type: Discord snowflake integer
- Used by: command registration/sync paths
- Notes: Recommended for local and production command sync behaviour.

### ADMIN_USER_ID

- Type: Discord snowflake integer
- Used by: startup/shutdown/admin notification flows

### GOOGLE_CREDENTIALS_FILE

- Type: filesystem path
- Default in `constants.py`: `credentials.json`
- Used by: Google Sheets access
- Notes: Keep credential files outside source control.

### ODBC_DRIVER

- Type: ODBC driver name
- Default in `constants.py`: `ODBC Driver 17 for SQL Server`
- Used by: SQL connection strings in `constants.py`

### CONFIG_STRICT

- Type: boolean-like (`1`, `true`, `yes`)
- Used by: `bot_config.py`
- Notes: Makes bad list/integer environment values fail loudly where strict parsing applies.

## Logging / Validation Variables

### LOG_TO_CONSOLE

- Type: `1` to mirror logs to console
- Used by: `logging_setup.py`
- Notes: Useful in local debugging; avoid noisy console logging for unattended production runs.

### DISABLE_FILE_LOGGING

- Type: `1` to avoid creating file handlers
- Used by: validation/smoke import paths

### SMOKE_IMPORTS

- Type: `1` during import-only validation
- Used by: `scripts/smoke_imports.py` and startup guards

### NO_DISCORD_LOGIN

- Type: `1` to prevent Discord login during validation/import tests

### DISABLE_STARTUP_TASKS

- Type: `1` to prevent background startup tasks during validation/import tests

## Channel / Feature IDs

Defined through `bot_config.py` and validated by `scripts/config_self_test.py` where relevant:

- `PLAYER_LOCATION_CHANNEL_ID`
- `PREKVK_CHANNEL_ID`
- `HONOR_CHANNEL_ID`
- `ACTIVITY_UPLOAD_CHANNEL_ID`
- `FORT_RALLY_CHANNEL_ID`
- `PROKINGDOM_CHANNEL_ID`
- `KVK_EVENT_CHANNEL_ID`
- `KVK_NOTIFICATION_CHANNEL_ID`
- `LEADERSHIP_CHANNEL_ID`
- `NOTIFY_CHANNEL_ID`
- `OFFSEASON_STATS_CHANNEL_ID`

Use `bot_config.py` as the exact source for exported names and types.

## Voting Configuration

### VOTE_OPTION_LABEL_MAX_LENGTH

- Type: integer from `1` to `80`
- Default: `20`
- Used by: `voting.service`, `/vote_admin create`
- Notes: Caps vote option labels for Discord slash-command validation, SQL validation, button
  labels, and result-card readability. Values above `80` are rejected because Discord button
  labels cannot exceed 80 characters.

## Runtime Path Constants

These are primarily configured in `constants.py`, not usually as environment variables:

- `LOG_DIR`
- `DATA_DIR`
- `QUEUE_CACHE_FILE`
- `COMMAND_CACHE_FILE`
- `LAST_SHUTDOWN_INFO`
- `BOT_LOCK_PATH`
- `BOT_PID_PATH`
- `RESTART_EXIT_CODE`
- `EVENT_CALENDAR_CACHE_FILE_PATH`

## Validation Commands

```powershell
python scripts/config_self_test.py
python scripts/validate_env.py
python scripts/smoke_imports.py
```

## Adding A New Variable

1. Add typed parsing in `bot_config.py` or `constants.py`.
2. Add validation to `scripts/config_self_test.py` or `scripts/validate_env.py` when practical.
3. Update this file with type, default, usage, and security notes.
4. Add tests if behaviour changes.

## Security Notes

- Do not commit secrets.
- Redact tokens and credentials in logs, diagnostics, and PR output.
- Use least-privilege SQL and Google credentials.
- Keep credential files readable only by the bot service user where possible.


## KVK source private intake (S5A)

| Variable | Default | Meaning |
|---|---|---|
| KVK_SOURCE_INTAKE_ENABLED | false | Enables private admission and manual receipt controls only. Does not activate serving. |
| KVK_SOURCE_RECOVERY_ENABLED | false | Enables the S5B recovery worker; independent of serving activation. See recovery configuration below. |
| KVK_SOURCE_CHANNEL_ID | 0 | Dedicated private intake channel; must differ from every legacy upload and monitored fallback channel. |
| KVK_SOURCE_UPLOADER_ROLE_IDS | empty | Explicit guild uploader role IDs; fresh membership is checked in handlers and callbacks. |
| KVK_SOURCE_ARTIFACT_ROOT | unset | Absolute private service-owned directory outside Git for content-addressed originals. |

No real channel, role, root or enabling flag is supplied by this change. Disabled intake creates
no directory or connection and preserves legacy routing. Verify channel membership/ACLs and
private-root filesystem permissions before enabling. Existing GUILD_ID and ADMIN_USER_ID define
the guild/admin boundary; ordinary uploaders cannot finalize/correct/configure. The existing
NOTIFY_CHANNEL_ID is also allowed for that admin's private command responses. SourceRouting.Enabled
is independent and remains off. Keep originals and receipts when disabling intake; no cleanup
or retained-database deletion is part of rollback.

## KVK source recovery (S5B)

| Variable | Default | Contract |
|---|---|---|
| KVK_SOURCE_RECOVERY_INTERVAL_SECONDS | 30 | Integer seconds, 1-300 inclusive. |
| KVK_SOURCE_RECOVERY_BATCH_SIZE | 8 | Integer periods per worker batch, 1-32 inclusive. |
| KVK_SOURCE_EXPORT_REGISTRATIONS | [] | JSON array of zero to eight explicit registrations, validated before SQL or credential access. Empty means no automatic export destination. |

KVK_SOURCE_RECOVERY_ENABLED defaults false. Enabling it registers one off-event-loop worker;
it does not enable SourceRouting or authorize Discord publication. Invalid interval/batch bounds
fail registration. Invalid export configuration fails closed before opening SQL/credentials;
the worker records the exception type and retries on its interval. Validate the configuration
before separately authorized activation; do not infer permission to enable it from this example.

Synthetic JSON example (all identifiers are placeholders):

```json
[{"kvk_no":1,"index_file_id":"synthetic_index","slot_file_ids":["synthetic_slot_a","synthetic_slot_b"],"owner_email":"owner@example.invalid","service_account_email":"bot@synthetic.iam.gserviceaccount.com","audience":"private"}]
```

Required keys are kvk_no, index_file_id, slot_file_ids, owner_email and service_account_email.
Only audience is optional; unknown keys are rejected. kvk_no is an integer 1-2147483647
(booleans are rejected). IDs are strings matching `[A-Za-z0-9_-]{3,128}`. Each registration
requires 2-16 slot IDs; the index and every slot must be distinct across the entire configuration
and cannot equal KVK_SHEET_ID or ALL_KVK_SHEET_ID. The durable receipt size may require fewer
slots; S4B returns setup-required if the registration plus quarantine exceeds receipt capacity.

owner_email must be a nonempty string containing @. service_account_email must end in
`.iam.gserviceaccount.com` and differ from the owner. Runtime provider checks verify actual
ownership and editor permissions; syntax validation does not establish ownership.
audience defaults to `private`; the only other value is `public_viewer`, which requires explicit
operator approval for that audience. Use dedicated pre-provisioned My Drive workbooks. Existing
S4B permission, protected-file, manifest, receipt and quarantine checks still apply.
Credentials come from the existing CREDENTIALS_FILE reference; never put keys or tokens in
this JSON or Git. An empty registration list loads no export credentials. No workbook discovery,
creation, automatic Discord send or uncertain/private-slot reclamation is authorized here.

When MAINT_SPEC_ALLOWLIST is explicitly configured, permit the exact callable
`proc_config_import:run_proc_config_import_payload` for process-mode ProcConfig imports.
The worker still enforces its configured allowlist; this change does not broaden it automatically.
Thread mode preserves the same actor/provenance without using the process callable allowlist.

## S10B shared export worker configuration

| Variable | Default | Meaning |
|---|---|---|
| EXPORT_COORDINATION_ENABLED | false | Registers no production worker until S10C shared adapters and deployment attestations exist. The flag alone cannot authorize admission. |
| EXPORT_SNAPSHOT_ROOT | unset | Explicit pre-provisioned absolute private spool directory outside Git; no automatic directory creation or cleanup. |
| EXPORT_STORAGE_OWNER | unset | Stable registered storage owner, bounded ASCII identity; another owner cannot read or claim its spool. |

S10B provides dependency-injected DAL/worker composition and a pinned new-source Sheets delivery path. Production registration deliberately remains closed even when the flag is true. No existing legacy/manual provider entry point is rerouted in this slice; shared producer integration is S10C. SourceRouting.Enabled is not an activation gate.

ExportSnapshotStore validates the root, opaque keys, byte limits, length and SHA256 before use. Provision the root with private operating-system permissions; storage ownership is an affinity identity, not an ACL substitute. Spool receipt registration follows exclusive write, fsync and readback. No retained spool is deleted by the worker.

Durable pacing also checkpoints a full policy interval after each actual provider completion. A lost checkpoint retains claims for reconciliation; reservation timing alone cannot permit a delayed request burst.
