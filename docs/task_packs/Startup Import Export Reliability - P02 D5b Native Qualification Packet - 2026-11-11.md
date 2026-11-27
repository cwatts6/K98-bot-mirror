# P02 D5b native qualification packet — 2026-11-11

Status: **native scope approved; capacity observation awaiting operator result**.
This updates authorization, not qualification status. D5b is not complete.

## Explicit operator authorization

The operator approved this specific scope in chat after asking to complete D5b:
one disposable database copy in the existing isolated VM, test-only candidate
installation, report recomputation and the real six maintenance children needed
for D5b. This supersedes the earlier no-copy/no-installation/no-rehearsal
restriction for this bounded qualification only.

The original retained database and evidence remain untouched. The 21-input
allowance remains consumed: no new input or import replay. All original resource
and time limits remain mandatory. Lab adapters must preserve production guards
and use clearly labelled test receipts. No permission grants, production changes
or VM resource increases are authorized. Stop and report if these bounds cannot
support completion. Actions within this approved scope do not require repeated
approval; a new exception outside it does.

## Stage 0: exact copy-capacity observation

Prepared executable: `scripts/collect_p02_d5b_capacity.ps1`, SHA-256
`0e977181f64dfa44180e483c8805850715a0f6b3ee96cba70753ff5ee0a3191e`.
Inert validator: `tests/validate_p02_d5b_capacity.ps1`, SHA-256
`5af79c40fc097954ce06c3a1a0da2d69bf9fef26712dd00e66e57fb518daf5e5`.
Uses the unchanged D5a.2 manifest only for its pinned source/file identity;
manifest SHA-256
`f8fe5c5291baa5baf86502c3924d10eb48200c2dcb0d0e84f5e8e1ff82a743f1`.

The source is `MINI_AMD` / `K98_P021_PreImport_20261107`, ID 7, with its pinned
read-only/restricted settings and MDF/LDF paths. The proposed sole disposable
target is `K98_P025_D5b_20261111`; an existing target stops the packet, never
authorizes overwrite or another database. VM ID remains
`2ac1b401-7076-4965-af71-de36ee0f9f9c`, four CPUs, fixed 8 GiB, zero adapters.
The borrowed PowerShell session remains
`8818b422-6855-457c-a81e-ff95fc155c84` in the operator's elevated Windows
PowerShell 5.1 console on `9SX2VF4`.

This observation adds allocated database-file sizes, fixed proposed-target
catalog presence and existing create/backup/sysadmin permission facts. It removes
all retained-input hashing, module, migration and ledger queries from the prior
collector. It performs no backup, copy, restore, installation, workload, grant or
guest-file write. The existing identity, process, resource, owned-session closure
and deadline controls remain. The host writes a new uniquely named receipt.

Bounds remain one attempt, 300 seconds overall, 48 SQL commands, 512 rows per
command, 2,048 overall rows and 1 MiB host receipt; three-second metadata commands,
zero lock wait and five-second connection timeouts. The fixed query inventory is
well below those ceilings. Original 8 GiB host memory is a pre-start gate; this
packet does not invent a post-start host or guest free-memory floor.

Adjudication must verify all of the following before planning a copy:

1. Exact source/VM/session identity, no errors, original source settings,
   unchanged isolation, budgets and observed work-session closure.
2. Source allocated bytes and both free-space samples. The emitted
   `singleCopyAloneFits` is only a lower bound: backup staging, database files,
   temporary/growth/workload allocations and the unchanged 8 GiB reserve still
   need a complete capacity budget. `qualificationReady` is always false.
3. Sufficient metadata visibility before interpreting zero proposed-target rows
   as absence. Require recorded `IsSysadmin=1` or separately verified equivalent
   visibility; zero rows alone could mean hidden metadata. No grant fallback.
4. Existing permissions sufficient for the later exact operation packet. Raw
   permission observations do not themselves authorize execution or establish
   application least-privilege behavior.

If a capacity/resource/identity gate fails, preserve the receipt and stop; do not
consume inputs, delete old databases/evidence, shrink files, expand the VM or
silently lower a reserve. No automated retry follows an incomplete result.

## Following stages within the approved scope

After Stage 0 passes adjudication, prepare the remaining exact artifact/operation
bindings before execution:

- **Copy and source custody:** prove source/data-file identities, exclusive new
  destination names and absence, and a bounded backup/copy/restore strategy with
  peak disk cost. Original database settings/data and evidence remain unchanged;
  any backup staging must be separately owned and must not reset a backup chain.
- **Lab installation:** bind the corrected candidate manifest and fixed D4 SQL
  payload; verify full structural pre/postimages and dependencies. Lab-target
  adaptations must be exact, explicit and confined to the disposable copy.
  Do not run production Apply against a renamed target, weaken its resource
  gate, create false formal migration receipts or grant missing rights.
- **Report/oracle qualification:** bind all 42 states and 14 exports to their
  retained captures, original independent oracle, numeric/name semantics and
  immutable queued bytes. Explicitly control execution-clock differences;
  preserve accepted tied-zero-rank adjudication. Recompute only authorized report
  work on the copy; do not replay a consumed import.
- **Actual six-child qualification:** each child needs legitimate, labelled lab
  demand/claim provenance, actual physical-work evidence, result/generation
  observations and owned cleanup. Determine those exact stimuli from the SQL
  contracts and observed copied state before invoking anything. No skipped-child
  or empty-ledger pass; no invented production business-completion receipts.
  No original/production backup job is dispatched as a test substitute.
- **Closeout:** compare all required evidence, preserve failures and unknown
  effects, account for every owned resource, and report remaining gaps honestly.
  Do not declare D5b complete from the offline validator or capacity probe alone.

The 1,800-second rehearsal ceiling, disk/version-store/log gates and all original
ownership/resource limits remain. D5c–f/D5e balanced cost acceptance and separate
D6/production authorization are not absorbed into this D5b packet.

## Preparation validation

Actual Windows PowerShell 5.1 executed the inert test successfully: parser,
budget/refusal/disposal, bounded worker cancellation, raw permission/identity
evidence, nested errors and capacity arithmetic. It did not execute the collector
or contact SQL/Hyper-V. Routing and whitespace checks passed.

Changes review `9b97bf26-ae00-4c5a-9e58-cf7136a6d9b8` completed with zero reportable
findings. Independent review confirmed the narrowed read-only scope and added
the catalog-visibility adjudication condition above. Snapshot digest:
`5a237beeab9bff7dd36c28bc1cb88d3da794a39e594b13367eebc48962cce1f3`.
The prior D5a collectors, original receipts and 146-pass correction evidence
remain separate and unchanged. This document is added afterward as documentation.

References:
[corrected candidate](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Receipt%20Correction%20and%20Validation%20-%202026-11-11.md),
[source preparation](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Preparation%20Review%20and%20Execution%20Plan%20-%202026-11-11.md),
[D5a closeout](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a%20Closeout%20and%20Feasibility%20-%202026-11-11.md).
