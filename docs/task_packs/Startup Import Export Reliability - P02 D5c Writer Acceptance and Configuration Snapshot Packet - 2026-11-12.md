# P02 D5c writer acceptance and configuration snapshot packet

## Accepted writer-first evidence

Receipt `d5c-config-writer-first-v2-result-82d2e0c13195432992ed9a6fdefd370d.json`,
SHA256 `424cfd24f7f4fd417d90fde7692b9e843010dda3cad25cdbde808ef84f511372`, passes
independent saved-data adjudication. The writer observed temporary versions
4/23/20; the unchanged actual configuration reader returned the full expected
target at 3/22/19. All four writer stages acknowledged execution, fetch and drain.
Rollback acknowledged, followed by restored 3/22/19. Distinct reader/writer births,
managed reader cleanup, joined owned process, disposed outer connections and
session absence are verified. Protected metadata matches the accepted prestate.
The original failed packet and receipt remain unchanged and failed.

The result reserves 48 client/control units and records 114 rows. Host elapsed
2.4718982 seconds debits three: **1,430 native seconds, 50 Windows-test seconds,
171 configuration-scope seconds and 113 later-configuration-test seconds remain**.
21 inputs stay consumed. Seven fixture rows remain admitted; no new row, writer
retry or maintenance retry is available. The final 1,000 native seconds remain
reserved for later D5 slices. Evidence is in
`.codex_artifacts/p025/d5c-config-writer-first-v2-acceptance.json`.

## Next bounded read-only packet

The approved fixture plan includes a committed version change and one stale-action
refusal. The successful `target_data` read deliberately returns a limited target;
it is not the full snapshot compared by the settlement boundary. Capture the real
public `ConfigPreparationRecoveryDAL.snapshot` now, before the committed change,
so that later refusal uses actual saved observation evidence. Do not fabricate
that evidence from the proposal or substitute the limited target dictionary.

`scripts/p02_d5c_config_snapshot.py` loads the same pinned 17 whole production
modules in an isolated Python process. It supplies one exact connection factory
and a fixed target object. The actual public DAL owns its unchanged recovery
snapshot, shared schema guard, rollback, isolation restoration and close.
The harness performs no writer, settlement, commit, import, report, maintenance,
backup or provider operation. It changes no permissions, isolation settings,
VM resources, original database or retained input.

Expected full values come from the accepted seven-row preservation receipt,
with datetime formatting normalized to the existing DAL wire format. The read
must exactly match preparation, membership, resources, stream and zero linked
provider-request/event counts. These are expectations only: the next native
receipt must independently supply the actual snapshot. Synthetic closed stream
history is never proof of provider activity or physical worker death.

`scripts/collect_p02_d5c_config_snapshot.ps1` retains all 23 outer metadata
observations and both resource checks from writer V2. It uses a new folder,
create-new intent and receipts, exact source/runtime/SQL/lineage pins, owned
process deadline and post-disposal closure observer. No executed file is edited.
Versioned harness duplication preserves immutable native evidence; no production
refactor or new runtime abstraction is introduced.

## Bounds and SQL alignment

The one actor reserves 17 units: nine SELECT/guard statements and eight
connect/rollback/isolation/autocommit/close controls, returning at most ten rows.
Together with 23 metadata calls and six outer controls, the plan reserves 46 of
48 units and 147 maximum rows. It retains 512 rows/result, 2,048 total rows,
1 MiB receipts, 64 KiB staged source/output files, 128 KiB manifest and bounded
source expansion. No budget is refunded after an uncertain start.

The 20-second actor, 25-second parent, 30-second work, 42-second cleanup and
45+10-second outer bounds remain; manual cancellation ceiling is 60 seconds.
Actual host time is rounded up and debited from both remaining configuration and
native allocations. This SQL check does not debit the Windows file/IPC allocation.
There is one SQL reader plus the established outer work connection; the closure
observer starts only after physical disposal and joined child are confirmed.

Authoritative SQL definitions for ExportPreparation, ExportPreparationResource,
ExportResource, ExportExecutionStream, ExportProviderRequest and
ExportProviderRequestEvent were checked in `C:\K98-bot-SQL-Server\sql_schema`.
The pinned public DAL selects exact preparation/account and related membership,
owned resources, relevant streams and linked request/event counts. No guessed
columns or separate SQL repository changes are included. Existing table shapes
and date/GUID/binary mapping are exercised by inert-driver tests.

## Validation and continuation

Six isolated Python tests passed for actual full snapshot output, exact row/count
drift, identity/guard refusal, cleanup uncertainty, no mutation/producer locks and
source membership. 193 PowerShell checks passed for inherited controls, exact
manifest/source/lineage pins, remoted results, wrong accounting/identity/snapshot,
cleanup admission and primary-error precedence. Offline tests do not qualify
native behavior. Changes review with Deep off covers the four source/test files
and this plan before handoff; no native work is performed during review.

Ruff, focused architecture/deferred/routing checks and the explicit test selector
are required. Full application pytest, smoke imports, command registration and
release validation are skipped: production code, Discord routes, dependencies and
deployment controls are unchanged; this packet is confined to isolated test tooling.

After receipt adjudication, prepare the already-approved reader-first committed
3/22/19 to 4/23/20 transition. Its barrier must occur after the actual reader has
established its snapshot and before remaining related reads. Subsequent fresh
observation must see 4/23/20; the one actual settlement call using the saved old
full snapshot must refuse with SourceConflict before mutation. Preserve final
fixture rows and prove cleanup. Split the calls into bounded packets as necessary
to retain the 48-unit ceiling; do not weaken observations to fit a combined run.
No additional writer-first run is included. Any uncertainty stops dependent work.

The operator has already approved the seven-row fixture and bounded tests. This
read-only prerequisite needs no additional permission. D5c and later D5 slices,
separate D6 release authorization and live acceptance remain open.

## Final preparation receipt

Changes review `b76235be-7d30-485c-86a0-cc33d11aecd1` completed with zero findings
and sealed readback verified. Independent review covered all four source/test
files and supporting manifest/DAL; the parent reviewed this plan. Descriptive
labels inherited from the writer packet were corrected after the frozen review
snapshot. Independent exact-delta inspection confirms only comments/docstring,
intent/failure labels and consequent hash bindings changed. Python executable AST
is unchanged; final 193 PowerShell checks passed. A separate security discovery
scan is skipped for that precise non-control delta. The original manifest is
retained as `d5c-config-snapshot-pre-label-execution-packet.json`.

Final wrapper SHA256:
`34285bf8683755da4416588c117f525357449824888215a02ae423d19912f2e6`.
Final manifest SHA256:
`31a1579e56b27aba192fcb0cf9b5a84395ce35e42593331c052454322d359897`.
All source, lineage and SQL pins were rechecked; native intent is absent.
Preparation acceptance: `.codex_artifacts/p025/d5c-config-snapshot-preparation-acceptance.json`.
Review-reported usage: 3,654,612 tokens; no native-time/input debit from review.
Ruff, architecture (two Python files), deferred structure, security routing and
explicit selector completed successfully. The runtime-test skips above apply.
