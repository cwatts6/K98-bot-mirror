# P02 D5b maintenance failure and diagnostic plan — 2026-11-11

Status: native maintenance failed; no retry, permission change or D5b completion.
The report/oracle workload remains unexecuted. Original evidence is preserved.

## Findings

The exact reviewed packet ran once. Receipt
`d5b-maintenance-result-e87efec446d64472841a455b33b9a636.json`, SHA-256
`e92dc35bcfcdc82748e7aa603164953b32fa22d717b9de3e521d5086b8803462`,
records committed labelled test demand followed by successful command returns for
import, configuration, player_report, kvk_output and final_stats. The sixth call,
post_import, raised “User does not have permission to perform this action.”

This is not six-child qualification. The end-of-run ledger, physical statistics,
entry counters and source poststate checks were not reached. The five successful
command returns do not substitute for those final observations. Do not rerun them,
reset claims, change due generations or create another copy. The original failed
receipt lacks the nested SQL error number; retain that diagnostic limitation.

Physical cleanup passed: the unpooled work connection was disposed and a separate
authorized observer found the exact session ID/login-time pair absent. Observer
disposal and VM isolation were recorded. The run used 35 client commands, 63 rows
and 12.5806003 seconds. Subtracting from the prior conservative 1541-second native
allowance leaves **1528 seconds**, without rounding up. No input was consumed;
the original 21-input allowance remains consumed. Resource samples remained
within disk/log/version-store limits. No report producer or backup dispatch ran.

The authoritative SQL source puts `usp_MaintenancePostImport` under
`EXECUTE AS OWNER` and calls `sys.sp_updatestats` after its guard checks.
The connected caller was sysadmin, but that does not by itself prove the nested
impersonated execution context. Microsoft documents database ownership or sysadmin
as the SQL Server requirement for
[sp_updatestats](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-updatestats-transact-sql?view=sql-server-ver17).
The failing permission predicate and whether the issue is restored-copy ownership
or candidate behavior are **not yet established**. Do not infer that a grant,
TRUSTWORTHY, ownership change or CALLER substitution is the remedy.

## Concrete next operation

One read-only observation on the same disposable copy, using the existing console
session and observer permissions. The packet pins the failed receipt and copy
identity. A host-only CreateNew intent prevents another execution of this packet.

Read the six durable ledger rows, configuration/KVK receipts and latent backup
demand; database and dbo SID/owner metadata; effective caller metadata; the two
candidate procedure definitions/execution contexts; the installed system
`sp_updatestats` definition; six procedure entry counters; eight physical-statistic
targets; and bounded copy-session/application-lock observations. All eleven
observation queries are SELECT-only. The packet neither impersonates nor invokes
the system procedure or a maintenance child. Definition text is evidence, never
executed. Cached entry counters are supporting observations, not durable proof.

Retain original source protection observations before/after, SQL closure proof,
fixed VM identity/4 CPU/8 GiB/zero adapters, Q volume identity and 8 GiB disk reserves.
Retain 300-second outer/210-second guest limits, three-second metadata commands,
zero lock wait, 48 commands/2048 rows/1 MiB receipt and the remaining 1528 seconds.
This path needs 24 client commands including closure and at most 32 rows
per observation. Stop on every error/incomplete result; no automatic follow-on.

Packet:

- `scripts/collect_p02_d5b_failure_observation.ps1`, SHA-256
  `4e761b0af2565e28d6cc5c4ea450d322e85101d1a19c739a04f080d88a07fe33`.
- `.codex_artifacts/p025/d5b-failure-observation-manifest.json`, SHA-256
  `22c28ca7856391b34627f12aa8bb3465dbecbdaff20c02252af1c861bc0ca922`.
- `tests/validate_p02_d5b_failure_observation.ps1`, SHA-256
  `c3183822d138ef4a37a8aec394150a938e633d26659cadfc2787cd4f0416237f`.

Actual Windows PowerShell 5.1 inert tests pass parser, identity/visibility refusal,
row/command/deadline boundaries, disposal/cancellation ownership, exact eleven
SELECT-only observations, absence of a workload executor, one-shot intent and
unchanged original failure bytes. No native check was run by those tests.

Security routing: Changes-only review of the Bot working tree at
`e7443e37212ca91e20d531b3684cc369d0fe1505`, Deep off. This is a new SQL/file-handling
collector and requires a review before operator execution. SQL repository source
is read-only and unchanged; its table/column definitions were cross-checked.
Broad Python/runtime suites are not applicable to this standalone observation.

Adjudicate the new receipt before proposing any correction. If a permission or
ownership change proves necessary, return its exact consequences for approval;
none is included in existing D5b authorization. Any eventual recovery must retain
the first failure and avoid rerunning the five completed calls. Reports and the
remaining D5 obligations remain open.

Changes review `f9662dd3-6efe-40a3-b97b-e6f1ebc4452b` completed with zero reportable
findings and no correctness blocker in the observation packet. Independent review
confirmed 24 commands and at most 102 rows. All eleven source inventory files are
accounted for; the ten earlier files remain byte-identical to prior reviewed pins.
Snapshot digest `fd4cdd00e493433eae000dbab9027b8ab2f199b28b7ccd95c13b0bc7d6c76426`.
Findings SHA-256 `8626db674dd5d7544ce1c4295813fc8aa37f2bc030cb3119db79456f40a0786e`;
coverage SHA-256 `6288b8b185a62e1c36542524c005c8ce9222577795d1336c90a2984a6a6e325f`.
Routing validator and whitespace checks passed. Native diagnostic execution is
pending; this review does not resolve the maintenance failure.
