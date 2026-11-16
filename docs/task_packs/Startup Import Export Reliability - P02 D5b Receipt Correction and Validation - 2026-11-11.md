# P02 D5b receipt correction and validation — 2026-11-11

**The approved narrow offline correction is complete: 146 checks passed.**
Both reproduced Q05 validation gaps are corrected in the shared Bot validator.
The original 69-test packet is byte-for-byte unchanged and now passes in full.
Its earlier 23 failures and original report remain preserved separately.
This is not native D5b acceptance, deployment or permission to mutate the VM.

## Change and SQL contract

`services/maintenance_dal.py:validate_receipts` now requires exactly the existing
six kinds, with duplicate/foreign kinds still rejected. It validates due and
completed generations as exact Python integers in the non-negative signed SQL
bigint range, with completed <= due. A non-null claimed generation must be an
exact integer with 0 < claimed <= due. Booleans, textual/approximate values and
overflow are rejected.

NULL seed claims and retained claim fields after completion or subsequent due
work remain valid. No claim-clear rule or new state transition was introduced.
The SQL source of truth is unchanged: `dbo.MaintenanceWork` defines these types,
nullability and bounds; `dbo.usp_update_stats` returns the six fixed kinds;
`dbo.usp_RunMaintenance` retains historical claim fields. No migration, SQL
definition, permission, backup wrapper or installed-target requirement changed.

`maintenance_service.result` and `maintenance_service.evidence` already use the
shared validator. Both now reject partial receipts before reporting completeness.
The DAL also validates before considering final-stats backup demand. Connection
ownership, exception preservation, physical cleanup and backup dispatch code were
not changed. Pipeline and `file_utils` maintenance callers were inspected for
compatibility; no second validator or new command/view logic was added.

The existing `tests/test_maintenance_dal.py` successful fixture now includes the
five other seed kinds alongside its exercised post-import row. Its assertions
and failure/cleanup schedules remain intact. New
`tests/test_p02_d5b_generation_domains.py` covers generation domains, valid seeds,
maximum bigint, retained claims and order independence.

## Offline validation

| Packet | Result |
| --- | --- |
| Original D5b receipt and retained-payload tests | **69 passed**, unchanged test bytes; previous result was 46 passed / 23 failed. |
| Additional generation-domain regressions | **63 passed**, including bool/text/float/negative/overflow at validator/result/evidence entry points, required-generation NULL refusal and valid claim history. |
| Existing synchronous maintenance DAL/cleanup regressions | **14 passed** using the corrected six-kind fixture. |
| Total | **146 passed**, zero failures/errors/skips; one broader application cancellation case deliberately deselected. |

The one deselected test imports the wider application through `file_utils` and
uses the async pytest plugin. This bounded runner deliberately disables project
conftest/plugin autoload and refuses native driver/provider imports. Its existing
cancellation assertion was not changed or claimed as freshly tested. Current
coverage includes late reply plus cleanup failure, foreign ownership, unknown
release, admission closure, malformed responses and final-stats backup evidence.
Native cancellation/restart remains a separate D5 obligation.

The existing `.venv` interpreter ran the packet under the preserved external-work
guard with a 120-second outer cap. The pytest report records approximately
5.90 seconds. Two warnings reflect the deliberately disabled async plugin
(`asyncio_mode` option and the deselected test's mark); they are not failures or
permission to load broader application dependencies.

Ruff no-fix, direct-library Black formatting checks for all three changed files,
architecture validation and security-routing validation passed. The formatting
check used `black.format_str` without writes or worker processes, avoiding the
previous CLI process-exit issue. Document/deferred-item and whitespace/link checks
passed. The selector's generic full-suite, smoke and command-registration
recommendations were reviewed and skipped: this is the approved bounded offline
correction, with no command registration changes and no authorization for broad
application/native qualification. No packages were installed.

Independent source review found no correctness/security issues. Changes-only
scan **`31d27b05-c5b9-4d9d-8cab-dd98bec4e763`** completed with zero reportable
findings. Snapshot digest:
`745317daa9715ba5bae62a9c42e79d718b33e2b49638e6ba1e0ff7ae775dbf03`.
It includes the retained D5a working-tree delta, verified unchanged against its
previous review. Test files omitted by the generated source inventory were
reviewed explicitly. No whole-codebase scan or native test was performed. This
closeout document was added afterward as documentation only.

## Evidence and candidate binding

Private directory `.codex_artifacts/p025/d5b-receipt-correction/` contains:

- `before.json` and `before-*.py`: prior source bytes/hashes and original failure
  evidence bindings, saved before correction.
- `run_offline.py`, `correction-run.log`, `correction-results.xml`: separate
  guarded execution and result artifacts. No earlier run or receipt was replaced.
- `candidate-manifest.json`: corrected working-tree source hashes, exact changed
  files and tests, unchanged SQL pins, and a link to the immutable original
  64-row case manifest (42 states, 14 exports, six children, Q05 and Q06).
- `final-validation.json`: custody verification, test result counts, exact
  source/report hashes and explicit limits/native status.

The full 196-artifact retained audit remains intact. The original queued payload
again passed byte-identical reload; its hash remains
`24e9f15dc71d0e3ef2b0d2e08383f9c623bb37328521126336504b896775264c`.
The prior candidate manifest remains historical; the new manifest binds this
correction without relabelling historical SQL/output results as new passes.

Bot base remains `e7443e37212ca91e20d531b3684cc369d0fe1505` plus the existing
D5a.1 drain correction and this uncommitted receipt correction. SQL HEAD remains
`b924cedd53e29dd88c0e9e7b66208b4fdc1e53ba`; fixed payload remains
`ba5c6acbefba0eb89cb18842a7f6c6811096759b`. No commit, PR, package installation or
deployment occurred.

## Remaining gate

Q05's reproduced Bot validation gaps are closed at the source/offline-test level.
Full D5b remains unqualified: actual six-child execution, fresh 42-state/14-export
SQL output correctness, SQL arithmetic/name-generation behavior and physical
effects require the authorized target and operation packet described in the
preparation review. The retained database remains a read-only target in the last
approved observation, with missing formal prerequisites and unqualified full
structural/dependency state. No fresh native observation is implied here.

Before any native attempt, return a concrete reviewed qualification-state and
installation packet that can satisfy those gates under the existing limits.
If no suitable state is authorized, retain no-go; do not manufacture receipts,
replay the ready file, switch databases, grant access or relax a production gate.
D5c–f, balanced D5e costs, separate D6 authorization, P03/P04 and D7/P05 acceptance
remain outstanding as already recorded.

All original resource, timing, observation, isolation and ownership limits are
preserved. Original CI/drain failures, failed D5a.2 receipt and SQL 3961 evidence
are unchanged. The old failed session's missing closure proof remains unverified.
The **21-input allowance remains consumed**: zero new inputs, zero native
attempts and zero permission changes in this correction. No reset/restore,
new database copy, installation, replay, schedule or production/provider action.

References:
[preserved offline findings](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Offline%20Preparation%20Findings%20-%202026-11-11.md),
[preparation and native gates](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Preparation%20Review%20and%20Execution%20Plan%20-%202026-11-11.md),
[D5a closeout](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a%20Closeout%20and%20Feasibility%20-%202026-11-11.md).
