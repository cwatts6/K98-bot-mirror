# D01 — grouped development database/file exclusions

PREPARED, NOT APPROVED OR EXECUTED. Command `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/D01.sql.txt`; exact SHA256 is recorded in the proposal seal and approval request.

## Operator-supplied binding

Operator reports an existing locally available SSMS connection to localhost\K98DEV using Windows Authentication, username 9SX2VF4\cwatt. This resolves the pending client-selection question. Historical successful development @@SERVERNAME is 9SX2VF4\K98DEV. Use that existing development connection, current database master. Chris Watts remains operator/reviewer/abort owner. Do not use the MINI_AMD production query tab or copy its accepted SQL ORIGINAL_LOGIN into this proposal.

Reported Windows authentication/username is not an observed SQL ORIGINAL_LOGIN. Emit safe SQL identity before comparing it to the reported binding; if it differs, stop with that evidence, do not broaden login allowlists, reconnect, impersonate or grant rights. Historical production SSMS executable/PID pins do not attest this local client; local client binary/native continuity remains unverified. This packet explicitly uses the operator-designated client with that limitation, not a fabricated executable hash.

## Exact capture

After isolated scalar transaction-state/count/implicit checks, set NOCOUNT ON, LOCK_TIMEOUT1000 and DEADLOCK_PRIORITY LOW. Emit UTC/server/database/ORIGINAL_LOGIN/machine/instance/product version and observer sysadmin flag. Guard @@SERVERNAME=9SX2VF4\K98DEV, MachineName=9SX2VF4, InstanceName=K98DEV, database master and ORIGINAL_LOGIN=9SX2VF4\cwatt (case-insensitive identity comparisons). Require already-existing sysadmin observer visibility, otherwise stop without granting anything.

Read sys.databases (ID/name/state), sys.master_files (database ID/name, file ID/logical name/type/physical path/size/max size/growth/percent-growth flag), and SERVERPROPERTY default data/log paths. No application tables, login/SID/credential catalogs, module bodies or filesystem/media access. Instance-level metadata includes system/offline databases; all returned names and files become protected exclusions. Unknown paths/state remain protected, not available for reuse.

This revises retained S00 after earlier development output was truncated. It is the missing durable exclusion inventory, not a rerun of completed production predecessors. Default paths are informational, not chosen restore destinations. Physical paths may include UNC/mount locations: no traversal or access follows. Database file size/max_size values are 8-KiB pages with special max-size encodings retained; growth is meaningful with is_percent_growth. These fields are not free-space capacity or file existence proof. Do not infer actual volume layout from drive letters alone.

## Budgets and effects

Five result sets: one identity row; zero to 65 databases; zero to 257 files; one default-path row; one completion row. Independent sentinels 65 databases and 257 files require stop without paging. Maximum 512 KiB output; one attempt, one batch, ten-second query timeout, fifteen-second cancellation cutoff, one-second lock timeout, MAXDOP1 on catalog lists. TOP limits output, not all scan/resource costs; statements are not an atomic snapshot. Null default paths require reconciliation, not fallback guessing.

Effects: catalog reads/audit/resource/locking, scalar assignments, observer session SET effects, editor/history/autorecovery. Preparing the existing development query tab to use master and setting that tab's timeout to ten seconds are included in this proposed scope; no global settings, new connection or authentication change. No USE in the query or automatic context repair. Stop if obtaining the query context would require another connection or unrelated unsaved work to be replaced.

No DB/file creation, overwrite, detach/drop, restore/reservation, backup/media read, VERIFYONLY/FILELISTONLY/CHECKDB, filesystem enumeration, SQL application execution, provider/Discord, job/task control, deployment/restart or Git publication. No production observation.

## Execution after exact scope approval

Existing maintenance window ends 2026-09-29T09:23:23Z; no scheduling reconfirmation needed. Approve the D01 query and limited existing-tab settings scope separately. In the existing development query tab, select master and set/confirm query timeout ten seconds. Replace only old capture text, verify marker `D01 development exclusion metadata completed`, execute whole batch once. Start timing before Execute, cancel at fifteen seconds and report if still running. Cancellation does not prove server quiescence.

Stop on unavailable/disconnected/changed target, reconnect/auth/certificate prompts, transaction/identity/visibility guard failures, sentinel, secret-bearing path metadata, missing/oversized/truncated/unexpected output, null defaults or missing completion/time cap. Keep secret-bearing path local and report redacted stop. No retry, pagination, new query connection, TLS weakening, grant, reconnect, COMMIT/ROLLBACK/state repair or cap expansion. Return all safe results and errors; partial identity followed by a guard error is not success.

## Validation and unresolved proof

Local static comparison to retained S00's catalog fields and isolated transaction-guard pattern; literal development binding and caps reviewed, no live validation. Documentation/inert metadata preparation retains security-routing skip; no runtime implementation or PR, predecessor tests/security discovery inapplicable.

After successful capture, plan exact volume/path metadata using actual exclusions and separately bind the disposable target. No target name, path or restore is selected here. Source F01 existence/lengths, catalog chain candidate and partial prune attestation remain separate. All seven typed G4 proofs and actual restore incomplete, rollout/G5 unapproved. Preserve pending/recovered evidence, isolated hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues.
