# P02 D5c relationship inventory correction - 2026-11-12

Status: failed inventory adjudicated; narrower V2 passed 112 offline checks
and completed Changes review. No native V2 execution is authorized by a test result.
Existing operator approval covers the bounded read-only handoff after review.

## Failure evidence and scope

Receipt `d5c-remaining-readiness-result-f071526a242948f7b5d72c3d340ee261.json`
matches SHA256 `A73BE4EC4EE41DE08343779A3FCCEA141DE008F16B443B5D71169E654BFCA891`.
Script and manifest hashes match the reviewed packet. The first 22 work
statements completed; `fixtureForeignKeys` failed on its 129th column-pair row,
after counting 128. Its partial detail rows were not retained. All three closure
statements completed: 26 total statements and 234 counted rows. The captured work
session birth was independently absent and both connections were disposed.
Host isolation was rechecked and the borrowed console session preserved.

Later paired state/resource checks were not reached. This remains an incomplete
inventory, not a new preservation/acceptance certificate. Preserve its script,
manifest, intent and receipt unchanged. Diagnosis is saved separately in
`.codex_artifacts/p025/d5c-remaining-readiness-failure-adjudication.json`.
Operator-reported outer elapsed time 1.1925655 seconds debits two seconds,
leaving **1,468 native seconds** and 468 of the proposed D5c allocation.
The original overall ceiling and later allocation remain unchanged; **21 inputs
remain consumed, zero new inputs**.

Earlier observations can guide planning only: all 21 fixed tables were present;
the completed post_import row retained generation 1 and first error 15247; the
four named application users had no matching server login in this copy. This
does not authorize authentication, impersonation, mapping repair or grants.
Both existing databases reported SNAPSHOT enabled; disabled-isolation coverage
remains unqualified and cannot be manufactured by a setting change.

## Correction and architecture

Owner: test-only PowerShell metadata collector and its pinned manifest. No Bot
runtime, commands/views, SQL repository object, schema or persistence change.
The V2 collector reuses the full reviewed V1 implementation, retaining all
identity, permission, resource, poststate and cleanup checks. It uses separate
create-new intent/receipt paths and additionally pins the failed V1 receipt.

Replace only `fixtureForeignKeys` with `fixtureForeignKeyCounts`: the same 21
fixed table names form the outer VALUES relation, with four scalar catalog
counts per table (incoming/outgoing constraints and column pairs). No detail rows
are packed into JSON/XML/strings, no truncation is used, and no cap is raised.
The original 128-detail-row failure remains visible; counts do not prove
dependency closure or authorize synthetic fixtures. Their purpose is to select
an exact smaller detail request, if needed, within existing bounds.

The remaining 33 SQL statements and expected preimages are unchanged. Totals
remain 34 statements, with maximum returned rows reduced from 308 to 201.
Original 48-command, 512-per-result, 2,048-total-row, 1-MiB receipt, three-second
statement, storage/log/version-store and zero-network limits remain unchanged.
The count result itself permits exactly 21 rows and refuses a 22nd.

The manifest now describes the unchanged actual deadlines: work admission stops
at 30 seconds; cleanup admission at 42; host stop at 45 plus ten seconds to join.
Manual cancellation/report is before 60 seconds. Full outer elapsed time,
including cleanup, is rounded up against the remaining 1,468 seconds.

No new maintenance demand, report/import/backup execution, fixture insertion,
permission change, SQL option change or retained-input read occurs. A missing
object or unsuitable count is a finding; no automatic repair or loop follows.

## Validation and review decision

All fixed names were checked against authoritative SQL table files and the
captured object inventory. The failed metadata query enumerated column pairs
across incoming and outgoing relationships; source FK declarations confirm that
individual relationships can involve multiple columns. No SQL syntax/runtime
acceptance is claimed from local source inspection.

112 offline PS5.1 checks passed, including parser/remoting, unchanged 33-query
comparison, exact four-count shape, no packed/truncated detail, 21-row acceptance,
22-row rejection and handle cleanup. Architecture, deferred-item and security
routing validators passed. Explicit-path test selector was run. Full pytest,
application smoke/command registration and release-native recommendations are
skipped for this isolated metadata-only correction; no app module or release
behavior changes, and no unbounded application/native startup is warranted.

Security decision: Changes review of the exact new collector, validator,
manifest and this plan against the reviewed V1 snapshot; Deep off. Existing
core helpers are reused without refactoring, no new background service or
production abstraction is introduced. SQL repository files are read-only
authority, so no SQL-repository patch review is needed.

After the one reviewed operator run, independently verify its receipt and
poststate/closure evidence, debit actual outer time, and use the counts to bound
the remaining concrete fixture/worker plan. D5c/d/e/f remain open; D6 deployment
is a later separate decision. No retry of completed D5b claims is proposed.

## Final preparation receipt

Changes scan `a5243359-e187-4592-9ffa-4e4871d90a22` completed with no findings,
covering all four files in `d16c6b3aef44b8b4349491d367093a5345fc6895` to
`0a06ce7f71538ad86dd8c71a201835c372aef61f`, Deep off. Completed sealed result
was read back. Measured review usage: 1,502,144 tokens, including 1,489,024 cached
input tokens. This is source review, not native acceptance.

Script SHA256: `5D631C9967A09E70F8C5025917039E1AA3486D141E5AAD64AEECC0F539DC3241`.
Manifest SHA256: `1b2f529f6f62be2a8a4b23ce605ef5cbc3efb326972824bbc1bd153031d108db`.
Original script/manifest/failed receipt and accepted reader-first receipt hashes
were rechecked unchanged. No V2 intent existed at preparation. This appended
status-only record changes no executable, manifest, test or security boundary;
no additional scan or runtime test is required for that prose update.
