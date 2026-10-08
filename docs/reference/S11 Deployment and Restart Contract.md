# S11 deployment and restart contract

This contract covers the reusable handoff, release runner and packet preparation.
It is not an executable production release packet. Each release must supply its
reviewed installation/verification scripts; the current older issuer also needs
the initial cutover described below. Merging this code does not deploy a release.

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

The manifest is prepared as part of release review. Operators do not manually
edit hashes, process IDs, scheduled-task arguments or source inventories.
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
Readiness probes must be bounded and distinguish healthy, online/degraded and
not-ready outcomes. A failed start is not an automatic rollback of SQL.

## Validation and release requirements

- Local failure-injection tests cover missing/altered receipts, unknown ownership,
  open provider streams, exact predecessor lineage and retained SQL claims.
- Orchestration tests cover successful apply, already-applied operations, unknown
  results, interrupted steps and loss of acknowledgement without replay.
- A native Windows rehearsal must exercise atomic ACL creation, scheduled-task
  exclusion, real retained process handles and the offline start path.
- Release adapters must prove exact production-main source, explicit SQL ledger
  checks, seed integrity and one-start/readiness behaviour before the packet is
  approved for operational use. They are release-specific reviewed files, not
  commands selected by the bot or discovered from pending migration filenames.
- The initial bootstrap must preserve the currently uncertain preparation and
  obtain actual old-process termination evidence. It cannot fabricate a stop
  receipt merely to make the new path accept the old release.
- Changes security review and normal repository validation precede promotion.

## Initial cutover and release-specific checks

The previously installed issuer does not understand deployment requests. Do not
run the new runner against that issuer and expect a graceful handoff. The first
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
