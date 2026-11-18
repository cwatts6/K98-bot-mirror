# P02 D5a closeout and retained-state feasibility — 2026-11-11

**D5a's bounded readiness and feasibility review is complete. The read-only
inventory passed; combined D5 qualification is not ready to execute.** This is
an assessed no-go with explicit prerequisites, not D5b–f acceptance, installation
approval or a finding that the retained database is a deployable D4 predecessor.

The operator agreed to complete D5a. The corrected access-only attempt was
reviewed first, then one remaining full read-only inventory was requested in the
same authenticated elevated console. Both returned successful bounded receipts.
No installation, permission change, import, replay, rehearsal, reset/restore,
new input, scheduling change or production/provider action followed.

## Completed D5a evidence

- Full scope and reconciliation remain F01–F32, C01–C16, all 73 action pairs,
  52 actions, 22 kinds and four empty kinds, with separately counted Recheck,
  group, batch and outcome paths. No row is waived by this closeout.
- D5a.1 drain investigation/correction retains its original CI/local failures
  and 42 passing focused checks. The approved runtime patch remains unchanged;
  no additional runtime fix was made during this native inventory.
- Local retained-evidence review preserves 66 final-continuation artifacts and
  130 comparison artifacts, the 42-state/14-export baselines and original queued
  export bytes. Historical timing gaps and failure/adjudication distinctions
  remain unchanged.
- D5a.2 now establishes current input custody, selected SQL metadata/resources,
  effective observer access, and the two new work sessions' observed closure.
  The case/state and operation/stop/cleanup matrices below record what remains
  infeasible before later qualification.

## Native results and evidence limits

| Attempt | Result | Bounds / SHA-256 |
| --- | --- | --- |
| Original failed inventory, `6ac0bdc278b94ce6a812c6d2a6a0a726` | Preserved incomplete result. Its invalid permission-check arguments and missing raw-value/session diagnostics were corrected separately. Old work-session closure remains unverified. | 7 statements, 3 rows, 1.5584887 seconds, 11,067 bytes. `de124a7df3233d3ef56f73b98cb74b00070aad9a122a7003cc3a978e55a55e34` |
| Access-only, `497f4751d3844dd9ae7bc77b2c37ab00`, 14:09:27 UTC | Required visibility equals one on work and observer; same existing effective/original login `MINI_AMD\K98LabAdmin`, server `MINI_AMD`, version `16.0.1210.3`. Zero retained-input or target-database reads. | 7 statements, 2 rows, 0.8153696 seconds, 5,027 bytes. `36c8e6dd006ace0312b56ccc93c2724e86c347de62553f10a8a8699af89c52f1` |
| Full read-only inventory, `4833c46c87d94bd0b203753ee843458d`, 14:10:32 UTC | Collection completed; independent local adjudication passed the pinned custody/metadata checks. No permission change was needed. | 19 statements, 236 rows, 1.3123009 seconds, 140,253 bytes. `75f86c3597cf01cd8421938170767c58d4c07a461a866c1e968fcdaca315686a` |

Raw receipts remain separate in `.codex_artifacts/p025/`, named
`d5a2-inventory-result-<attempt>.json`. Local adjudications are
`d5a2-access-adjudicated.json` and
`d5a2-completed-inventory-adjudication.json`. The executed original source, test,
manifest and failed receipt were preserved byte-for-byte before correction in
`d5a2-diagnostic-correction/preservation.json` and its referenced copies.

Both new attempts preserved the borrowed session and verified the exact running
VM identity and zero-adapter isolation after collection. Each disposed the work
connection before creating its observer. SQL reused session ID 64, but the
recorded login times differ and the parameterized closure check matched both
fields. Thus reuse was not confused with survival of the work session. Observer
disposal is local evidence, not a third independently observed server closure.
Neither new receipt retroactively closes the old failed attempt's missing tuple.

## Verified retained target and outstanding release prerequisites

| Observation | Result and implication |
| --- | --- |
| Inputs | Exactly **21 files / 1,638,735 bytes**; one ready, zero claimed, 20 archived. Every expected name, size and SHA-256 matches. The allowance remains consumed; a ready filename does not authorize replay. |
| Database | `K98_P021_PreImport_20261107`, ID 7, expected MDF/LDF paths, owner SID `01`, `Latin1_General_CI_AS`, compatibility 160. READ_ONLY / RESTRICTED_USER, SNAPSHOT on, RCSI off, Broker off, trustworthy off. Creation time is a new catalog observation, not proof of unchanged business rows. |
| File-command configuration | `show advanced options` and `xp_cmdshell` configured/current values remain zero. |
| Retained modules | All **174** raw UTF-8 definition fingerprints match the retained final baseline. The allowlist contains 193 objects: 176 present and 17 absent. This is not a full D4 structural-preimage/permission/signature qualification. |
| D4 additions | All 17 new D4 objects are absent, including `MaintenanceWork`, `MaintenanceConfigurationWork`, `MaintenanceKvkWork` and `MaintenanceBackupWork`. Empty `ledgers` in the receipt means those tables were absent, not that pending work was zero. No table or seed was created. |
| Migration prerequisites | Four of the six required predecessor migration rows are present, Applied, and checksum-matched to the fixed profile. **`20261106_001_personal_stats_daily_read_plan` and `20261109_001_p02_phase1_sql_exports` are absent.** The combined D4 migration is absent as expected. Module fingerprints do not replace those receipt requirements. |
| Deployment linkage | Three referenced deployment rows were found with Succeeded status. Migration `20261003_001_export_legacy_direct_permissions` references missing deployment ID `66cebeda-882c-43d1-9c64-25b9d5455724`. Retain this lineage gap; do not synthesize a deployment receipt. Existing deployment rows name historical `ROK_TRACKER`; they do not change the actual current database identity. |
| Resources | Both target samples: disk 11,389,124,608 bytes (about 10.607 GiB), log usage 2.402443%, version store 0 KiB. Guest free memory approximately 5.80 then 5.75 GiB is observational. Relevant process census showed PowerShell and SQL Server, no Python producer. This is bounded observation, not a complete activity audit. |

The fixed SQL release remains commit
`ba5c6acbefba0eb89cb18842a7f6c6811096759b`, migration
`20261111_001_p02_d4_combined`, profile `p02_d4_v1`. Current authoritative SQL
HEAD is clean `b924cedd53e29dd88c0e9e7b66208b4fdc1e53ba`; fixed script/profile
hashes remain `8c0c99d92c14cac6da6e22076a5620927bac4c8af3deaa50950d66062381a8dc`
and `57944777e50b7dc9200220cfcc2ce767edb22a2e0972e02bc2cd6f04e23e8171`.

Source review of `C:\K98-bot-SQL-Server\deploy\SqlDeploy.P02D4Release.ps1`
establishes additional future execution boundaries. Its installed-target gate
requires `MINI_AMD` / `ROK_TRACKER`, writable MULTI_USER state, specific sequence
and backup-wrapper/job/permission bindings; those dependencies were not queried
by this bounded inventory. Its resource function separately requires 8 GiB free
on the SQL host. That installer gate must be reconciled with the fixed 8 GiB VM
and original pre-start-host memory rule before any proposed use. The D5a inventory
passed its approved rules; do not silently repurpose the installer, change the
database name/state, weaken either rule or add a new D5a post-start RAM floor.

Bot source remains `e7443e37212ca91e20d531b3684cc369d0fe1505` plus the reviewed
uncommitted D5a.1 patch. The exact combined candidate still needs an execution
manifest/package binding before later native work. Last accepted installed Bot
and Phase 1 SQL identities remain historical; this collector did not freshly
inventory an installed Bot tree or production host.

## Case/input/state feasibility matrix

| Later obligation | Existing usable evidence/state | Missing prerequisite / disposition |
| --- | --- | --- |
| D5b 42 detailed states, 14 exports, numerics/latest names and original queued bytes | Retained full-size captures, independent oracle and immutable queued payload are available. Current selected module/input baseline matches. | Exact combined candidate installation and an authorized comparable execution state are absent. Captures are reference evidence, not a new candidate pass. No business rows or producer were run here. |
| Actual `import` maintenance child | Retained completed-input history and consumed 21-file custody. | No authorized fresh import or due generation. Do not replay the surviving ready file. |
| Actual `configuration` child | Historical reference results; current read-only target. | Ledger absent; actual eligible generation/work and authorized mutation unavailable. |
| Actual `player_report` child | Historical report references. | Ledger absent; actual admitted report/maintenance work and output ownership unestablished. |
| Actual `kvk_output` child | Historical KVK outputs and reference captures. | KVK ledger absent; valid due generation and actual child work unavailable. An initially empty KVK ledger would not prove this child. |
| Actual `final_stats` child | Historical final-state evidence. | Ledger absent; due generation and permitted actual maintenance not established. |
| Actual `post_import` child | Historical completed import/continuation receipt. | Ledger absent; no authorized fresh producer completion or actual child work. |
| D5c both-order concurrency, rights and real holders | Existing observer identity now verified for this bounded session-visibility purpose. | It does not establish application least-privilege behavior, known competing owners, alternate factories or either overlap order on the combined candidate. No locks/workers were started. |
| D5d faults, cancellation, late completion and restart | D5a.1 offline drain correction evidence remains usable for its stated schedules. | Native combined-candidate owners, mutable state, controlled fault/restart packet and physical-cleanup proof are not available from read-only inventory. |
| D5e balanced measured costs | Historical Phase 1 measurements and preserved captures inform design. | No comparable mutable pre-states or authorized actual six-child workload. Historical reset/restore harness cannot be reused under current limits; no new copy/input is authorized. |
| D5f integration and D6 handoff | Full reconciliation and this explicit readiness matrix. | Final candidate evidence for every required row, installed dependencies, release binding and separate D6 decision remain open. |

## Cost design retained for later D5e

Use the same exact combined candidate and comparable admitted workload in both
arms; only the reviewed observation/diagnostic condition may differ. Fix equal
warmup and at least five balanced OFF/ON pairs, alternating which arm goes first.
Bind each arm to its authorized input/state and due-generation identity before
execution. A mutable state that cannot be restored or otherwise made comparable
within authorization is a feasibility blocker, not grounds to count unequal arms.

Include actual maintenance and physical cleanup in eventual total cost, while
also reporting each child separately. Record actual child entry, due/completed
generations, observer count, successes/refusals, manual actions, false incidents,
convergence, per-stage time, total time and resource samples. Skipped children,
missing timings and displaced work are not zero-cost passes.

Frozen acceptance remains overall median ON <= OFF × 1.20 + 1,000 ms; each report
stage ON <= OFF × 1.20 + 250 ms. Warmup and five pairs are prerequisites. The
1,800-second rehearsal cap does not extend a Bot timeout. RCSI stays off; relevant
disk reserves stay at least 8 GiB, version store below 512 MiB, optional statistics
sampled log below 70%. The original host memory floor is 8 GiB **before VM start**.
Observation statements stay at three seconds/zero lock wait; later held metadata
tests stay within 30 seconds. No cost or qualification execution is authorized here.

## Operation, stop and cleanup matrix / next plan

| Operation | Current disposition | Stop and ownership rule |
| --- | --- | --- |
| Read-only D5a inventory | Finished; no further attempt needed for this packet. | Preserve all three receipts. No automatic retry or cleanup by guessed SQL session ID. Existing PSSession and VM are left as provided. |
| Receipt/dependency reconciliation | Next proposed work is source/retained-evidence review of the two missing prerequisite migrations, missing deployment link, and qualification-vs-installed-target contract. | Do not invent receipt rows from matching module hashes, alter release pins, change database settings or run the deployment scripts. Return a concrete corrective/qualification design before implementation or native action. |
| D5b installation/qualification preparation | Not executable under the current target and unchanged constraints. | Must identify an explicitly authorized suitable state, exact candidate/SQL package and case-to-state bindings first. No implicit copy, reset, restore, input replenishment or schedule change. |
| D5c–e native execution | No-go until prior gates and exact operation packets pass. | Stop on identity/isolation/resource/cost/ownership failure; preserve unknown outcomes and original errors. Release only proven owned operations; no arbitrary KILL, retry-to-green or fallback privilege. |
| Production/provider/D6 | Outside D5a. | Separate authorization; preserve private-only files and deployment/updater/seed/rights/ancestor requirements, including archives. After SQL commit, use the same verified receipt and forward continuation only. |

The next concrete deliverable is a **source-only qualification-state and receipt
reconciliation proposal**, not a grant or another native retry. It must state
which cases remain possible without new input and explicitly identify any state
requirement that cannot be met under the existing limits. No solution that changes
those limits is assumed or approved by this closeout. P03 actual blockers and
essential P04 fixes still precede normal import/export; D7/P05 whole-flow/provider/
natural acceptance remains separate. Original SQL 3961 evidence is unchanged;
managed metadata protection does not prove general reader/DDL safety.

## Validation, custody and review

Both successful receipts were hash-checked against the operator output, parsed
locally, and independently compared to the unchanged manifest and authoritative
release requirements. Checks include identity/mode, errors, budgets, input map,
all 174 module digests, 193-object allowlist, absent-object mapping, migration
checksum/status, missing deployment links, resources and exact-session closure.

No executable source changed after the reviewed collector
`599e8d1bf171a68e270a999243b7265d5a486041b9b07773a1d27a9ae2cd4aaf` and inert test
`f87ea06401705b9fda1a537f806e619495c0f1e93ab78048caccfa7a85a3716b`. Its completed
Changes review is `35c02989-2aee-4274-9d5a-8b6a861853a9`, with zero security
findings; this is not a whole-repository or native workload approval.

This closeout adds Markdown and ignored evidence/adjudication metadata only.
Security routing is a documented skip for that delta: no runtime/configuration,
SQL implementation, grants or permissions changed. Broad Python tests, smoke
imports, command registration and another security scan would not test these new
read-only observations and are skipped. Document validation and original-evidence
hash checks are recorded in `.codex_artifacts/p025/d5a-closeout-validation.json`.

References:
[scope](Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Scope%20Review%20-%202026-11-11.md),
[complete reconciliation](Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Obligation%20Reconciliation%20-%202026-11-11.md),
[readiness packet](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a%20Readiness%20and%20Retained%20Data%20Plan%20-%202026-11-11.md),
[diagnostic correction](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a2%20Diagnostic%20Correction%20and%20Observer%20Access%20Plan%20-%202026-11-11.md).
