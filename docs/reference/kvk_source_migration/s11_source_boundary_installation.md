# S11 source boundary installation

`scripts/install_s11_source_boundary.ps1` prepares and applies only the filesystem
boundary for the manual paired-process rollout. Preview is the default. It never
connects to SQL, starts the Bot or scheduled task, creates credentials, installs
dependencies, enrolls files or activates S11. Source-only ordinary startup does
not establish coordinated readiness.

The administrator supplies an independently reviewed JSON plan and its SHA256.
The script parses the same bytes it hashes. The plan is not generated from an
unreviewed runtime snapshot. Production observations identify drift checks;
reviewed Git source pins identify the application source to install.

The first plan uses status `REVIEWED_SOURCE_BOUNDARY_INSTALLATION_V1`, exact host,
machine GUID, application SID, private-main head and these factual fields:

- `immutable_source_files`: exact paths, reviewed SHA256 and prior ACLs.
- `immutable_source_directories`: exact source directory paths and prior ACLs,
  including the application root.
- `immutable_config_and_existing_key`: reviewed configuration or the sole existing
  key's digest and prior ACL; contents are never returned.
- `existing_environment`: existing private `.env` path, digest and prior ACL.
- `preserve_moves`: operator-confirmed unused root directories and named source
  bytecode caches, with exact destinations and cache membership.
- `venv_python_sha256`, `venv_config_sha256`: preserved executable/config pins.
- `base_interpreter_observations`: independently reviewed finite supporting
  path/ACL/hash observations; these are drift guards, not a complete dependency
  contract or permission to modify base Python.
- `git_sha256`, `computer_name`, `installation_id`, `source_root`,
  `proposed_control_root`, `application_sid`, `machine_guid`, `source_head`.

The target roots are fixed to the application and `C:\ProgramData\K98\S11`.
The latter and its K98 parent must be fresh; existing state requires explicit
reconciliation. New installation paths use a fresh UUID. Plan ACL suggestions
cannot choose the granted rights: the installer fixes administrator ownership,
SYSTEM/Administrators full control and application read/execute at immutable
paths. Private state leaves retain application write access. `.env` stays private
and content unchanged; edits under the protected source parent become deliberate
administrative operations. The sole key loses ordinary Users access.

The six explicitly allowed legacy root directories are preserved outside source,
as are individually named caches. All move targets are checked before native
same-volume directory renames. Existing destinations, reparse points, changed
cache membership and source/hash/ACL drift stop the packet. There is no recursive
delete, overwrite or copy fallback.

Before effects, each explicitly reviewed import directory admits at most 1,000
immediate metadata entries. Every Python file must belong to the sealed plan;
unreviewed import directories, native modules and loose bytecode are rejected.
Runtime-excluded state/tooling directories are not traversed by this check.
The imported `telemetry` package is application source: its files/directories
must be independently pinned in the plan and later runtime manifests.

The existing application venv is the only additional metadata closure. Each
directory admits at most 1,000 immediate entries and the closure at most 50,000
paths; no package contents or other trees are collected. All venv prior ACLs are
recorded before permission changes. Existing dependency files remain in place;
administrator ownership and read/execute protection cover their full closure.
Base Python is verified against reviewed observations and remains unchanged.
This does not substitute for subsequent ordinary-operator runtime verification.

Both ordinary and coordinated startup publish PID files under the existing
writable `logs` directory using the shared `BOT_PID_PATH`. Atomic temporary-file
creation and replacement need a writable parent; granting access only to the old
root PID leaf would not preserve ordinary startup. Existing root PID leaves are
retained as historical state, without automated deletion or adoption. Source
protection requires deploying this aligned Bot/watchdog change first.

Embed audit appends use `logs/embed_audit.log` through the shared
`EMBED_AUDIT_LOG_PATH`. Any historical root `embed_audit.log` is retained
untouched; new appends require only the private writable logs parent.

`-Apply` additionally requires an elevated named operator,
`-OperatorHoldConfirmed` and `-BotStopped`. These represent actual operator
confirmation of no conflicting work held until completion or reconciliation and
a manually stopped Bot held off; they are not inferred from elapsed time or a
process inventory. Do not use `/ops graceful_restart` to establish a stopped hold.

Receipts retain action intentions, prior ACLs, completed moves and observed final
ACLs. Paths and SDDL strings have explicit dictionary records; subsequent records
refer to those IDs, retaining the exact restoration inputs without repeatedly
printing long descriptors. Capacity for remaining per-member action records is
checked before any effects. Receipt files are created without overwrite. Output
is bounded to 20 MiB and file hashes to 16 MiB.

The public entry point supervises its own PowerShell child with a 60-second
deadline reset before each finite operation. A stalled operation stops that
owned worker, retains the flushed journal and reports incomplete state. Git has
its own shorter 55-second owned-process limit. There is no fixed duration cap on
the full installation. Stopping a worker cannot undo an operating-system action
already issued; intentions without completion records require reconciliation.
The internal `-Worker` mode is not an operator invocation. Use the public sealed
command. A failure never retries or rolls back automatically. Native guard and
PID tests do not prove elevated production owner changes or future process
identities; ordinary-operator verification follows the separately approved Apply.

After filesystem installation, independently reviewed SQL/runtime registration
and static manifests, ordinary held-pair startup, actual process rebinding,
coordinated workflow/failure validation, enrollment/provider writes and G5
activation remain separate steps and decisions. The installer alone does not
authorize any of them. Preserve existing recovery databases, publications,
Sheets exclusions and historical seals.

Rollback is a reviewed reconciliation of the recorded actions, not a blanket
ACL restore or recursive move. Keep S11 admission closed, retain both original
and new receipts, identify exactly which actions completed, then prepare exact
inverse paths/ACLs only if the operator chooses rollback. Administrative source
updates must retain these boundaries rather than silently returning write access
to ordinary application code.
