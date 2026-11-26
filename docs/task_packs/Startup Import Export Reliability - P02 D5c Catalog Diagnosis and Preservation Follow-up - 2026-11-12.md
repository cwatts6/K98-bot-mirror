# P02 D5c catalog diagnosis and preservation follow-up

## Finding and retained evidence

The one catalog attempt stopped on `exact ordered catalog column names`.
Receipt `d5c-fixture-catalog-result-c218a7094c2e44ffb68115912450d2df.json`
SHA256 `33FCE0B40EC284C962861AA17507CDC1518FF3C1B74C276C1900DC9612EA8AAA`
is preserved with its executed collector, manifest, intent and review history.
No rerun or database correction has occurred.

All seven catalog queries completed before the final assertion: 50 tables,
649 columns and all 115 foreign keys / 317 ordered column pairs were retained.
Every table and column name matches the source exactly, preserving multiplicity
and case. All FK child/parent column tuples match source, are enabled and trusted,
and use NO_ACTION; no enabled table trigger was reported.

Only `dbo.ExportResource` has a different physical column order. Its static
reference snapshot places `ActivePreparationID` fourth; the retained database
places it eighth. The authoritative migration
`C:\K98-bot-SQL-Server\migrations\20261001_001_legacy_export_preparation_installation.sql`
line 177 uses `ALTER TABLE ... ADD ActivePreparationID`, consistent with its
appended installed position. That migration source hash is
`3fb26b901274a6941a41d9d1363972e90e856fd106beb8f1493f7acce8591676`.
This explains why static CREATE order is not a valid installed ordinal contract;
it does not establish which historical migration command actually ran.

The defect is the collector's inappropriate ordered-name expectation. The prior
table-order correction concerned sorting table names and did not cover column
placement introduced by migrations. The original collector is not modified.
No column reorder, table rebuild or runtime correction is warranted. Future
fixture commands must use explicit named columns and validate their types,
nullability, defaults and constraints; this finding alone does not approve them.

The retained evidence also verifies unchanged initial protected records,
candidate definitions, original failure history, cached execution evidence,
initial reserves, and physical SQL connection closure. Both SQL connections
were disposed and the exact work-session birth was absent. The outer session
and VM isolation remained intact. The receipt used 34 reserved command units
and 1,075 rows. Full host time 1.760503 seconds costs two: **1,441 native seconds
and 50 Windows-test seconds remain**, 21 inputs are consumed and no maintenance
retry is available.

Nine final observations and the second resource sample were skipped after the
refusal. This is an incomplete packet, not a pass. Local adjudication is saved
in `.codex_artifacts/p025/d5c-fixture-catalog-failure-adjudication.json`.

## Concrete continuation

Run one separately named read-only preservation follow-up using the same
authenticated session and exact disposable database. It reuses the accepted
30 paired identity, protected-state, resource and cleanup observations verbatim.
It collects no catalog rows, starts no Python process and performs no workload,
fixture admission, permission, isolation, ownership, installation or VM change.

The packet is `scripts/collect_p02_d5c_catalog_poststate.ps1`, with manifest
`.codex_artifacts/p025/d5c-catalog-poststate-execution-packet.json`.
The failed receipt is a required immutable lineage pin. A new create-once intent
prevents repeat execution. Existing expected values and first-error history are
unchanged. Unknown SQL/job ownership remains retained and blocks dependent work.

Thirty statements plus six connection/cancellation units reserve **36/48 units**
and at most **171/2,048 rows**. Global 512-row/command and 1 MiB receipt limits
remain. Work admission ends at 30 seconds, cleanup admission at 42, outer stop
at 45 plus ten seconds to observe, and manual cancellation/report before 60.
Full host elapsed time is charged from 1,441; this metadata-only packet does not
consume the 50 remaining Windows-test seconds. All original resource limits,
fixed VM identity/resources/isolation and exact borrowed-session checks remain.

Adjudicate the later receipt against the failed attempt's initial observations
and accepted baseline. It can establish current unchanged preservation state;
it cannot retroactively recreate the skipped original poststate instant.
Do not rerun catalog collection or claim that the original failed packet passed.
On any error, preserve the follow-up evidence and stop without another attempt.

After preservation is established, use the existing captured catalog to finish
the source-only fixture feasibility plan. Exact new rows, rights/isolation
exceptions and balanced cost demand remain reserved for concrete approval.
D5c/d/e/f remain open. D6 release and later live acceptance are separate.

## Preparation checks and review boundary

100 offline PowerShell checks passed. They parse without invoking either
collector, compare all preserved helpers and SQL/expected-state bindings,
verify lineage hashes, row/command/budget limits, no catalog/actor path, retained
custody, deadline controls and absent execution intent. No native activity ran.

Architecture validation passed with zero Python files; deferred validation
passed for all three documents and security routing reported zero errors or
warnings. The explicit selector ran; its broad recommendations are addressed
by the following skips. Immutable whitespace checks remain required. Full application
pytest, smoke imports, command registration and release tests are skipped:
this follow-up changes no production Python, SQL source, deployment or command
behavior. It only removes catalog reads from the reviewed metadata wrapper.
No new production refactor or deferred optimisation item is introduced.

Security routing is a focused **Changes review**, Deep off, for this collector,
its offline validator and the three-document diagnosis/status delta. The SQL
repository remains read-only authority and has no changed review target.
Native handoff waits for completed review and final artifact hash verification.

## Reviewed follow-up ready

Changes review `d8fa49a7-1ee6-48a5-af02-40a49bb8ebe5` completed and sealed for
`51df5b56b17e97534de9389332aa24648860f66e` to
`466aaef4eb4a68766767abc8f06251b1ed2bc07f`. All five changed files were covered;
no security candidates or execution blockers were found. The completed canonical
result was read back. Measured usage was 1,780,610 total tokens, including
1,766,912 cached input tokens.

All five working files matched the immutable snapshot before this status-only
appendix. Sixteen lineage/history hashes matched, including the failed catalog
receipt. The original executed catalog script is unchanged. All 30 observations,
expected bindings, first-error history and hard limits remain unchanged. The
new intent is absent; normal HEAD is unchanged. Immutable whitespace checks
passed. Preparation acceptance is saved in
`.codex_artifacts/p025/d5c-catalog-poststate-preparation-acceptance.json`.

The one-time handoff uses script SHA256
`CB3194DAA4E7DB58FDE1D725B30E5A7363D7CE07F4912748FDF7DCEB892CD35D`
and manifest SHA256
`43ae28c0e3a6ea22956d8d19a1de7db0d9344df6058e8fb69afd5fff29a9941f`.
Use the existing `$global:D5bReportSession`, record full host elapsed time and
cancel/report a hang before 60 seconds. On error or incomplete output, preserve
evidence and stop without retry. Native follow-up is pending; the budget remains
1,441 native / 50 Windows-test seconds, with 21 inputs consumed and no maintenance
retry. No runtime correction or production action is included.

## Later preservation accepted

Receipt `d5c-catalog-poststate-result-fcb10ba360ed4a2490f40f178daf7fd3.json`, SHA256
`EB0FDDADB8081B0281C0B5B11C9512D3C18C6BED6FF8820135B73DFF76117FA2`, passes
all 30 observations, full protected-state comparisons and physical cleanup.
Its 36 reserved units and 109 rows stayed within limits. Full host 1.1728617
seconds costs two, leaving **1,439 native / 50 Windows-test seconds**, 21 inputs
consumed and no maintenance retry. The original catalog failure stays unchanged.
This later acceptance does not recreate its skipped poststate instant.
See the [next configuration fixture plan](Startup%20Import%20Export%20Reliability%20-%20P02%20D5c%20Preservation%20Acceptance%20and%20Configuration%20Fixture%20Plan%20-%202026-11-12.md).
