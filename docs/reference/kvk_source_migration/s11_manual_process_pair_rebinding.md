# S11 manual process-pair rebinding

Chris selected manual administrative rebinding for the first coordinated rollout.
This is a startup mechanism, not enrollment or activation authorization. Ordinary
startup with all S11 flags off retains the existing Bot/watchdog path.
Intake-only and recovery-only startup also retain that ordinary path when export
coordination is off; those independently supported modes do not require a pair.

For an approved startup-binding validation before activation, set the process-local
`K98_EXPORT_LAUNCH_VALIDATION=1` and `K98_EXPORT_LAUNCH_PLAN` to the fresh reviewed
plan, then invoke the existing `start-bot-after-sql.ps1` wrapper from that ordinary
PowerShell session. Its usual SQL/network checks precede `run_bot.py`; the new
settings are inherited by that real watchdog. A process-local `WATCHDOG_CHILD_LOG`
may retain the held Bot descriptor under the existing writable logs directory.
All three S11 flags must remain off in this mode. The watchdog supplies the normal
child startup environment, singleton ownership and supervision, starts the held
Bot gate, and pauses automatic replacement after its exit. Start only the authority
gate directly in its separate ordinary terminal. Do not launch the Bot gate directly
or manually supply `WATCHDOG_RUN`. Remove the process-local validation setting before
later coordinated activation; it is not a new `.env` credential/configuration path.

An enabled coordinated launch requires `K98_EXPORT_LAUNCH_PLAN`, an absolute path
to a reviewed, administrator-owned static plan. The watchdog starts an isolated
held Bot process. The operator starts the authority gate separately under the
same ordinary Windows account. Neither gate starts SQL/provider/application work
while waiting for the final protected publication. The two printed descriptors
are actual observations, not permission to adopt new expected capabilities.

The plan supplies version 1, reviewed `source_hashes`, `application_sid`, two
independently approved `token_profiles`, `python`, `python_sha256`, two exact
template references (`path`, `sha256`), two fresh manifest destinations and one
fresh `commit_file`. Every destination has an already provisioned private,
administrator-controlled parent. Templates and destinations must be distinct.
Do not place expectations in an application-writable evidence/spool directory.

Templates contain complete reviewed Bot/authority configuration, registration,
SQL expectations and the authority's version 5 deployment review. Only the three
`process_bindings` fields and the Bot authority `deployment_hash` are null before
binding. All seven deployment review records remain separately pinned; the
`bot_identity` record must already approve the actual ordinary token profile.
Future PIDs, token profiles, installed metadata hashes and permission findings
must not be fabricated. Missing static bindings block creation of a usable plan.

## Per-launch sequence

1. Confirm the actual no-conflicting-work hold until completion or reconciliation.
   Preserve old deployment/ownership receipts and reconcile uncertain work.
2. Use a fresh reviewed plan and output paths. With coordinated flags configured
   for the approved stage, launch the standard scheduled startup task for the
   held Bot. In a separate ordinary terminal, run the reviewed interpreter with
   `-I -B scripts/run_export_process_gate.py --role authority --plan <exact-plan>`.
   Record both held-process receipts. Do not elevate either application process.
3. From the administrative terminal, use the reviewed interpreter with
   `-I -B scripts/provision_export_process_pair.py --plan <exact-plan>
   --authority-pid <observed-authority-pid> --bot-pid <observed-bot-pid>` for the
   read-only identity comparison. This observes only those two exact processes.
4. The separate approved startup decision covers adding `--apply
   --operator-hold-confirmed`. Publication reopens and retains the exact handles,
   checks executable/token/incarnation, validates the authority manifest and all
   deployment review records, writes fresh administrator-owned manifests and
   writes and protects a private pending commit, rechecks both still-live pins,
   then atomically moves it to the final release path without overwriting.
   Release allows authority SQL-session creation; it is an effectful startup
   decision even though the publisher itself opens no SQL/provider connection.
5. Each gate verifies the protected commit and both manifests against its static
   plan/templates, then verifies its own actual incarnation and pinned peer.
   Authority starts its existing entry point. Bot waits for the exact pipe,
   then runs `DL_bot.py` in the same PID; normal runtime contract/readiness
   checks still govern admission. Gate bytecode suppression precedes imports.

Use full sealed commands with factual paths, hashes and current receipts for an
actual installation. The placeholders above are documentation, not executable
production instructions or a prepared production plan.

## Exit, restart and failure

An S11-enabled watchdog does not automatically launch a replacement child.
`/ops graceful_restart` stops the current child and pauses for manual rebinding.
Reconcile old authority/session receipts, prepare a fresh pair and publish fresh
manifests before the next admitted startup. Existing planned-restart markers are
retained for operator reconciliation. Flags-off restart behavior is unchanged.

The authority retains a handle to the exact Bot incarnation and uses it during
pipe waits. Bot exit returns to the existing drain routine. A clean drain may
close that SQL execution session; unresolved work retains the session/claims.
Exit, a lost reply or a new process never proves completion or authorizes replay.

A failed publication retains partial files. Without a protected final commit,
gates stay held. Do not retry into existing destinations, overwrite old manifests
or clean evidence. Stop/reconcile the held pair and prepare fresh reviewed paths.
Every individual pipe wait is bounded; no fixed total operator provisioning or
workload duration is introduced. No process/session inventory or remote shutdown
is required.

Both coordinated and ordinary flags-off PID publication use `logs/bot_pid.txt`
so source-root replacement rights are unnecessary. Any retained root
`bot_pid.txt` is historical state and must not be used as the live process PID.
Source/config/import ancestors still require the separately reviewed immutable
installation; logs/data/downloads, private environment access and evidence/spool
leaves need explicit writable-state dispositions. This mechanism does not install
ACLs, remove caches, learn SQL expectations, enroll output files or activate G5.
