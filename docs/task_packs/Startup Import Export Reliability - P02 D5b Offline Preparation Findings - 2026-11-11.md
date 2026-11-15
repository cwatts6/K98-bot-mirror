# P02 D5b bounded offline preparation findings — 2026-11-11

**The authorized offline preparation is complete: 69 tests, 46 passed and
23 failed. Two receipt-validation gaps are reproduced. No runtime correction or
native attempt followed.** The failing assertions remain failing and unchanged;
they are not marked expected-failure or weakened. D5b native acceptance remains
blocked by the state/installation prerequisites in the preparation plan.

## Executed scope and results

New test-only files:

- `tests/test_p02_d5b_receipt_contract.py`: finite in-memory SQL response doubles,
  service completeness, backup-demand evidence and physical-cleanup controls.
- `tests/test_p02_d5b_retained_payload.py`: actual candidate serializer loaded
  with inert dependencies, original queued payload reload and exact numeric
  materialization. Private retained data requires explicit offline opt-in.

The completed bounded run used the existing `.venv` interpreter, disabled pytest
plugin autoload and project conftest, and installed an audit hook refusing socket
connections/DNS, subprocess launches and native SQL/provider imports. Backup
dispatch was replaced before invocation. No historical runner/installer was
imported. The outer local process cap was 120 seconds; the completed test run
took 5.002 seconds according to its XML report. The audit hook is a test guard,
not a claim of an operating-system security boundary.

| Outcome | Count | Meaning |
| --- | --- | --- |
| Missing-kind acceptance failures | 18 | Omitting each of the five kinds other than `post_import`, or returning only `post_import`, is accepted by each of DAL, service result and service evidence paths. |
| Claimed-generation validation failures | 5 | With due/completed generation 1, claimed generation 0, -1, 2, text `"1"` or 2^63 is accepted. |
| Other receipt/cleanup controls passed | 26 | Empty/missing-post-import responses, duplicate/foreign rows, invalid state/due/done/UUID, split result sets, complete/outstanding states, backup evidence, late error plus failed cleanup, foreign ownership and unknown release controls. |
| Payload/numeric compatibility passed | 20 | Original full payload reload; exact scalar type/value/decimal scale, finite-number refusal and bigint/decimal/NULL frame materialization. |

There were zero test errors or skips in the completed run. One pytest warning
reports the existing `asyncio_mode` option while its plugin is deliberately
disabled; these tests are synchronous. This does not change the pass/fail count.

## Reproduced findings and proposed correction

**D5B-Q05-A — incomplete six-kind response accepted.** Authoritative
`dbo.usp_update_stats` returns the six fixed kinds from `MaintenanceWork`.
`services/maintenance_dal.py:validate_receipts` checks membership/duplicates but
requires only `post_import`. `services/maintenance_service.py` computes complete
over the returned rows. Consequently an incomplete set of complete rows can
produce a complete result and complete evidence. Omitting `final_stats` also
removes the condition that would require its positive-demand backup evidence.
This is a reproduced malformed-response gap, not proof that ordinary SQL has
truncated a response in production.

Recommended correction, **not applied**: require exactly one row for every
member of the existing six-kind contract before either completeness or backup
dispatch/adjudication. Keep `result` and `evidence` using the same validation.
Do not infer a scoped response from missing rows; the current endpoint has no
such contract. Existing tests that use a post-import-only successful fixture
would need a truthful six-kind fixture plus explicit omission regressions.

**D5B-Q05-B — claimed-generation domain unchecked.** The authoritative
`MaintenanceWork` table constrains a non-null claimed generation to be positive
and at most the due generation, stored as SQL bigint. The worker records a claim
before child execution and retains claim fields through completion/failure.
The Bot currently validates due/completed generations but not claimed generation.
All five invalid cases above survive the DAL, with normal cleanup still performed.

Recommended correction, **not applied**: validate non-null claimed generation
against the SQL integer domain and due-generation bounds; use exact integer
typing so booleans are not treated as SQL integers. Validate related generation
domains consistently. Preserve legitimate NULL seed fields and historical claim
fields on complete/pending/failed/unknown rows. Do not invent a rule that every
completed row must clear its claim. Any additional state/claim pairing rule must
first be traced through actual SQL transitions and separately tested.

These are one tightly related receipt-contract family. A subsequent bounded
runtime correction should touch the shared validator and its focused fixtures,
preserve original errors/physical cleanup and rerun this exact failure packet.
It requires a new explicit implementation decision. It does not require or
authorize a native SQL attempt, migration, permission change or receipt repair.

## Candidate, case and original-evidence binding

Private evidence directory:
`.codex_artifacts/p025/d5b-offline-preparation/`.

- `before.json` binds Bot HEAD `e7443e37212ca91e20d531b3684cc369d0fe1505`,
  hashes of 2,817 tracked working-tree files, the existing approved drain patch,
  original custody records, operational logs and the two exact executed tests.
  This is a source inventory, not an installed/release package.
- `case-manifest.json` contains **64 rows**: 42 detailed states, 14 exports,
  six actual maintenance children, Q05 and Q06. Each historical state/export
  has its paired reference/candidate capture hashes, exact historical query,
  authoritative SQL object definition and candidate reader/producer contract.
  Bracketed database/object names and the sanitized filename for
  `LATEST_T4&T5_KILLS` were resolved from SQL source, not guessed.
- All **196 retained artifacts** match the accepted audit's sizes/hashes.
  The retained independent oracle is bound by hash; its historical runner was
  not imported or rerun. The historical 42-state/14-export comparisons remain
  historical evidence, not passes for the new combined candidate.
- The original immutable payload remains 17,516,820 bytes, SHA-256
  `24e9f15dc71d0e3ef2b0d2e08383f9c623bb37328521126336504b896775264c`.
  The actual candidate loader reloaded it byte-for-byte: 14 sections,
  49,468 rows and 827,683 cells. Independent decoding preserved all retained
  sections, including name strings, without rewriting the original.
- Exact Python handling includes large signed integers, values above bigint,
  decimals including positive/negative halfway values, NULLs and nonfinite
  refusal. **This does not prove SQL rounding/overflow behavior, fresh latest-name
  selection, a new producer result or maintenance correctness.** Those native
  obligations remain explicit in the case manifest.

SQL source remains `b924cedd53e29dd88c0e9e7b66208b4fdc1e53ba`; fixed payload
commit `ba5c6acbefba0eb89cb18842a7f6c6811096759b`, D4 profile/script pins and all
original scope/resource limits remain unchanged. No source package was installed.

## Preserved incomplete harness attempts

The first offline run reached the test cases but pytest's XML report requested
Windows host information through `platform.uname`, which attempted a subprocess.
The audit hook refused it. Its original log, partial XML and executed runner are
retained. A report-only inert hostname adapter was added; the second attempt had
an incorrect constructor arity in that adapter and also left a preserved partial
report. Correcting that test-report adapter produced the third completed report.
The **two test files and all their assertions were identical across all three
attempts**. No connection boundary was relaxed and no runtime fix was made.

The first formatter invocation reformatted only the two new test files, then did
not return; a later formatter check also failed to return. Both owned processes
were cancelled. Ruff's explicit no-fix check passed. A default-interpreter Ruff
attempt initially reported the module absent; no dependency was installed, and
the existing virtual environment supplied Ruff. These tool limitations are not
test passes and do not alter the preserved failed-contract evidence.

## Validation and security review

Focused architecture validation passed for the two new Python files. Deferred
item/document validation and security-routing validation passed. The selector's
generic full-suite/smoke/registration recommendations are deliberately skipped:
the user authorized this bounded offline packet, not broad application imports
or opt-in native tests. No command registration or runtime path was changed.
No unrelated deferred item was created; the findings refine existing D5 Q05.

Changes-only security scan `de3c3b4a-55a6-487b-a0b5-a0eb03e9f069` completed with
zero reportable findings. Its source snapshot digest is
`7bc8ad03ffdb8ce606c80c46589a1ee61d16341975d14512480319798c173e1c`.
The tool requires the whole working-tree diff, so the retained D5a runtime and
collector changes were included and independently reviewed. The generated
inventory omitted tests; both new test files were reviewed explicitly, with
supporting prior tests read. This is neither a whole-codebase audit nor native
qualification. This findings document was added afterward as documentation only.

`final-validation.json` records candidate/custody comparisons, exact test and
report hashes, test totals, validation outcomes and remaining native gates.
Original failed receipts, CI/drain evidence and SQL 3961 evidence are preserved.
The old failed inventory's missing session-closure proof remains unverified.

## Stop point and next decision

The recommended next action is a **narrow offline runtime correction for the two
shared receipt-validation gaps**, followed by focused regression and Changes
review. Findings are returned now, before that correction. Full native D5b
remains no-go: the target is read-only, prerequisites are incomplete, and no
authorized suitable due-work/pre-state packet exists. Passing offline tests
after a correction would not remove those gates.

All original limits remain in force, including the fixed VM allocation/isolation,
resource and timing floors/caps, D5a.2 observation bounds and balanced D5e cost
requirements. The **21-input allowance remains consumed**. This packet consumed
zero inputs, attempted zero native operations and changed zero permissions.
No replay, installation, reset/restore, new copy, schedule change, production or
provider action occurred.

References:
[approved preparation plan](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Preparation%20Review%20and%20Execution%20Plan%20-%202026-11-11.md),
[D5a closeout](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a%20Closeout%20and%20Feasibility%20-%202026-11-11.md),
[full obligation reconciliation](Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Obligation%20Reconciliation%20-%202026-11-11.md).
