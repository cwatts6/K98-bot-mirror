# S11 deployment and restart contract

This contract covers the reusable handoff, release runner and packet preparation.
Routine source-only updates use one versioned, reviewed updater which generates
release metadata and matching seed automatically. The operator runs the same
command and requests one restart when prompted; no per-release script authoring,
manifest editing or Codex session is required. The first source/startup release
succeeded on 2026-10-09, including the orphan-queue fix. Routine-update usability
still requires acceptance of the ownership/index corrections below; that first
release needed manual intervention. Do not repeat its restart or recovery.
An installation still using the older
issuer needs the initial cutover described below. MINI_AMD completed that cutover
on 2026-10-08; consult the latest handover before selecting a deployment path.
Merging this code does not deploy a release. For copy-and-paste operator steps,
use the [Promotion Guide](Promotion%20Guide.md).

## Operator workflow

An ordinary `/ops graceful_restart` drains the existing incarnation and starts a
fresh incarnation of the installed release. No source pull or SQL migration is
part of an ordinary restart.

For deployment, an administrator runs `scripts/Deploy-K98Release.ps1` with a
reviewed release manifest and its independently supplied SHA256. The script
stages protected release files, checks the release, excludes scheduled starts,
then asks the operator to run `/ops graceful_restart`. After that command drains
the existing pair, the release script installs the selected SQL migration(s),
production-main source and matching seed, starts once, and verifies readiness.

For routine source-only updates, the installed `Update-K98.ps1` fetches private
production main and prepares the manifest automatically from authenticated source
and the protected installation. `-PrepareOnly` prepares without deploying; the
unchanged normal command refreshes unused preparation before recording deployment
intent, then retains that exact package for all resumes. The reviewed updater uses
fixed apply/verify adapters and preserves SQL/dependency observations and flags.
Operators do not manually edit hashes, process IDs, scheduled-task arguments or
source inventories. The generic packaging interface remains available for releases
with separately reviewed migration, dependency or configuration changes.
The release author uses `python -m scripts.prepare_k98_release --specification
<reviewed-spec.json> --output <fresh-directory>` to package the runner, selected
files and canonical `release.json`. The command returns the manifest and runner
checksums. Supplied member checksums are checked, never silently replaced. No
script, SQL operation or production launch runs during packaging.
Source acquisition must target the exact reviewed commit on private production
`main`. SQL acquisition must target the exact reviewed SQL-repository commit and
explicit migration IDs; discovering and executing all pending filenames is not
permitted. Existing successful migration receipts are retained and verified.

`-AlreadyStopped` uses the installed issuer's `--drain-only` path. It requires a
retained stop receipt or the existing native reboot proof; it does not infer a
successful shutdown from an absent process ID. The first installation of this
protocol requires a separately reviewed bootstrap for the older issuer.

## Restart while work is quarantined

The operator approved returning ordinary bot functions while affected work stays
paused. The initial supported case is an uncertain preparation with a blocked
resource and matching account, owner and fence. Its resource ownership and all
input/output evidence remain unchanged. Neither restart nor release installation
replays it, releases it or relabels it as completed.

The previous process pair must have positively terminated, all provider streams
must be closed, and any old authority session must match the exact previous
publication. Active jobs/output operations, unexplained ownership, unknown
sessions and malformed observations remain startup blockers. Recovery of those
cases is a separate change, not an implicit extension of this rule.

Readiness must distinguish process/Discord availability from import/export health.
A quarantined resource can block several dependent operations, not just the
operation which originally failed. Report that degraded state explicitly.

## Protected handoff

The administrator writes `deployment-request.json` into the installed policy's
protected history directory. It names one release ID and the exact current
policy hash, sequence and publication. It contains no command or executable path.

Only a graceful restart outcome consumes that request. After both retained native
handles signal termination and SQL session reconciliation succeeds, the issuer
writes an immutable `deployment-drained-<release-id>.json` and exits. The runner
also waits for the old issuer to exit before installation. No old source is
modified while its application processes are running.

The issuer records `terminated-<sequence>.json` after each confirmed stop. That
administrator-protected observation supports a later same-boot start without
inventing a new termination proof. The exact previous journal is embedded;
another incarnation, altered receipt or application-writable receipt is refused.

A reviewed successor policy can name its predecessor's history directory and
policy hash. The first successor start reads the old identity under its original
policy hash. It does not rewrite old observations as evidence for the new release.
Subsequent incarnations use the successor's own history and policy.

## Release manifest and resumption

The runner's version-one manifest includes `release_id`, `host`, `application_sid`,
`repository`, pinned `policy` and `issuer_launcher` references, a flat checksummed
`members` inventory, `preflight`, and ordered `steps`. A script invocation contains
`file` and an `arguments` object of explicit string parameters. Only listed,
hash-verified PowerShell files can run from the protected staging directory.

Each step has `id`, `kind`, `apply` and `verify`. Allowed kinds are `sql`, `source`,
`seed`, `start`, `readiness`, in that order. Exactly one seed, start and final
readiness step is required; SQL/source steps depend on the release's contents.

Verifier exit codes are a reviewed protocol:

- `0`: the exact postcondition is independently confirmed; skip apply.
- `10`: the postcondition is not present and this initial apply may begin.
- Any other code: outcome unresolved; stop without starting later steps.

An immutable intent precedes each apply. If an interrupted step is not confirmed
by its verifier, the runner does not repeat it. `-Resume` first verifies the same
manifest and the actual state, so a committed migration or completed source
update is not replayed merely because the runner lost its acknowledgement.
The source verifier has one narrow resumable bookkeeping operation: when HEAD,
branch, all target hashes and deletions independently match, the staged diff is
empty, and only authenticated release members appear modified, it may normalize
those exact index paths. This requires the same protected source intent, verified
drain and disabled predecessor task. It rechecks hashes, empty staged diff and
tracked cleanliness afterward. It never reapplies source or starts a process.
Readiness probes must be bounded and distinguish healthy, online/degraded and
not-ready outcomes. A failed start is not an automatic rollback of SQL.

### Ownership preflight

Before requesting a drain, the source adapter establishes administrative custody
for existing changed non-runtime files. The repository root, existing ancestors
and previously pinned runtime paths must already be protected. Only an already
trusted file owner or the exact configured application owner is allowed.
Files must match authenticated predecessor hashes (the installed exact runtime pin,
or Git blob/checkout newline forms for non-runtime text). Binary preimages stay exact.
Reparse points, hardlinks, unexpected owners, null/writable non-administrative ACLs
and conflicting new paths are refused. Replacement candidates additionally reject
alternate streams and unsupported attributes.
A retained native handle excludes data writes while a fresh, atomically secured
file receives the authenticated bytes, existing DACL/group and ordinary metadata.
The fresh Administrators-owned object atomically replaces the old file under its
protected parent. Prior owner security handles therefore cannot change the accepted
object. Bytes and permissions are checked again. Failed preparation retains unique
scratch files; completed preparation is idempotent. The application SID never
becomes trusted, and altered content is not repaired. Application-owned directories
remain refused: recursive custody migration is outside the routine source update.

## Validation and release requirements

- Local failure-injection tests cover missing/altered receipts, unknown ownership,
  open provider streams, exact predecessor lineage and retained SQL claims.
- Orchestration tests cover successful apply, already-applied operations, unknown
  results, interrupted steps and loss of acknowledgement without replay.
- A native Windows rehearsal must exercise atomic ACL creation, scheduled-task
  exclusion, real retained process handles and the offline start path.
- Release adapters must prove exact production-main source, explicit SQL ledger
  checks, seed integrity and one-start/readiness behaviour before the packet is
  approved for operational use. Routine source-only releases reuse reviewed tool
  code with generated exact bindings. SQL steps require explicit reviewed migration
  identities. Neither path accepts commands selected by the bot or discovers
  executable migrations from pending filenames.
- The initial bootstrap must preserve the currently uncertain preparation and
  obtain actual old-process termination evidence. It cannot fabricate a stop
  receipt merely to make the new path accept the old release.
- Changes security review and normal repository validation precede promotion.

## Initial cutover and release-specific checks

This section applies only to an installation that has not completed initial cutover.
The legacy issuer does not understand deployment requests. Do not run the new
runner against that issuer and expect a graceful handoff. The first
production packet must retain the current native process handles before shutdown,
observe both exits, preserve the uncertain preparation, exclude old scheduled
starts and stop the old issuer before changing its source. Missing PIDs are not
proof. The bootstrap must be reviewed against the then-current live state; the
October 8 diagnostic PIDs are historical observations, not execution parameters.

Release verification scripts must independently establish their postconditions:

| Step | Required evidence |
| --- | --- |
| SQL, when present | Exact reviewed SQL commit/migration IDs and successful ledger hashes; unresolved outcomes never return `10`. |
| Source | Exact private production-main commit, tracked cleanliness, full source hashes and protected runtime paths; environment/dependencies unchanged unless explicitly included. |
| Seed | Fresh matching policy/templates/launch gate, retained predecessor lineage and unchanged activation flags; disabled task action/security readback. |
| Start | One newly published incarnation from the new policy and matching live native identities; no retry based only on a missing acknowledgement. |
| Readiness | Fresh Discord availability plus explicit healthy/degraded import/export status. Cached data or a successful task exit alone is insufficient. |

The runner does not infer these postconditions from an apply exit code. It
requires the verifier to confirm them. A packet with placeholder verification
scripts is not deployable, even when packaging and generic runner tests pass.

## Reviewed amendment after the first SQL step fails

A version-two manifest can explicitly amend a drained version-one release before
any original step completed. It retains the same release ID, host, account,
repository, predecessor policy and issuer. Its `amendment` names a new canonical
ID, the exact original manifest SHA256 and the original first SQL step ID.
The amended steps must begin with SQL under a different step ID and a different
pinned apply-script hash. No later step may reuse the failed ID or apply-script
bytes either. Omitting SQL or renaming the failed script is refused.
The changed corrective script still requires review; distinct bytes alone do not
establish a safe migration.

The original stage must contain only that step's starting intent and no start
request. The runner preserves all original files and receipts, stages the new
packet in `release-<release-id>/amendment-<amendment-id>`, and records one immutable
amendment selection. A competing amendment is refused. The existing original
request and drain receipt remain authoritative; no replacement drain is invented.

The new packet must provide a reviewed preflight that reconciles the specific
failed SQL outcome, verifies unchanged source/native/task/SQL predecessor state,
and checks backup readiness before any new migration. An absent process or a
failed ledger status is insufficient proof of rollback. The replacement migration
has its own reviewed ID and checksum; the failed predecessor receipt is preserved.
No original apply is replayed. New apply intents and completion receipts live in
the amendment directory and retain the ordinary no-replay rules.

This is an explicit coordinated recovery operation, not an automatic retry or a
routine updater option. Original or amended unknown outcomes require evidence
reconciliation. Once an amendment is selected, use its exact launcher for every
resume. Installed runtime contracts must explicitly approve the replacement
migration lineage and its expected predecessor status; observed receipts never
select or update their own expected hashes.

The current runner refuses version-one execution when an amendment selection is
present, both before and after preflight. Historical pinned runners cannot be
retroactively changed. A packet amending such a runner must prove its original
verifier remains fail-closed for the retained outcome. The October 10 correction
requires the exact original Failed receipt throughout; it does not support
amending an original Applied outcome. Use only the amended launcher after selection.
