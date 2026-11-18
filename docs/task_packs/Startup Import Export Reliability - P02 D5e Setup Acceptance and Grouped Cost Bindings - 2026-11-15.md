# P02 D5e setup acceptance and grouped cost bindings

## Accepted setup and accounting

The saved setup receipt `d5e-cost-setup-b15f3b85e0c34e4fa9dc0a9937f05d91-result.json`
matches SHA-256 `3e8f1233fe912f40f66dd0599577453a548010d48b442eb323c534b503ca42eb`.
All five copy steps completed; exact work-session closure and both disposals were
acknowledged, with no cleanup uncertainty or errors. Source pre/post observations,
the copied ledger, seven child modules and source provenance match prior evidence.

Database `K98_P025_D5e_Cost_20261115` is ID 11, birth
`2026-11-15 14:17:07.067`, with the expected owner, RCSI off and SNAPSHOT on.
Its retained COPY_ONLY/CHECKSUM backup is 10,165,309,440 bytes, below 32 GiB.
Q: has 80,482,598,912 free bytes. The 245.2811205 elapsed seconds charge **246**,
leaving **989 native seconds**, **49 Windows seconds**, and **12 row attempts**
(83/95 consumed). The one-database and one-backup extensions are consumed.
No input was added; the earlier 21-input allowance remains consumed.

| Scope | Completed | Expected |
| --- | ---: | ---: |
| Accepted D5d cases, accounting and D5e readiness | 100 | 100 |
| New grouped cost-binding checks | 0 | 8 |
| Fresh cost arms, including two warmups | 0 | 12 |
| Total including remaining binding and cost checks | 100 | 120 |

Setup acceptance is **1/1**, separately tracked as in the approved setup handoff.
The denominator increases from 112 to 120 because the eight new binding checks
are now explicit; no accepted check was removed or replayed. Offline controls
are also separate from native acceptance. The new setup acceptance JSON retains
the prior 100/112 checkpoint; this dated continuation adds the eight checks.

## Why binding collection precedes measured arms

The setup receipt contains seven maintenance definitions and four cross-database
references in copied utility/import modules, including msdb backup history and
master xp_cmdshell. It does not contain the new copy's complete report/demand
dependency graph, trigger/synonym definitions, or index/statistics branch state.
That is insufficient evidence to seal a measured packet with committed reports
and all six real maintenance children. This is not a failed setup or permission
to execute those utility/import modules.

The actual import child selects skip/reorganize/rebuild at fragmentation 10/30;
configuration selects physical work only above 1,000 pages and fragmentation
15/50. KVK output may create absent indexes. Post-import uses sp_updatestats.
The comparison must account for those changing branches, rather than treating
fresh due generations alone as equal physical work. The next packet collects
all these missing bindings in one read-only pass on the new database. It does
not dispatch a report, demand, maintenance child, backup, import or cost arm.

## Eight grouped checks

1. Retained database identities, old owner absence, fixture and evidence preservation.
2. Exact new cost-copy birth, owner, settings, file layout and competing sessions.
3. Unspent copied demands, historical first error 15247 and retained source counts.
4. Thirteen report/maintenance/demand entry points, transitive static dependencies,
   enabled-trigger edges, trigger definitions and synonyms. Cycles are bounded;
   reaching depth 16 refuses a completeness claim. Dynamic SQL remains subject to
   source review; captured metadata is not an automatic reachability approval.
5. Physical import/configuration branches, all user statistics modification counters,
   and KVK output index presence, without changing statistics or indexes.
6. All 57 report output shapes, nine summary cursors, actual log count and clocks.
7. Log below 70%, version store below 512 MiB, disk floors and retained backup size.
8. Physical collector closure and preservation accounting.

The packet is `scripts/observe_p02_d5e_cost_bindings.ps1`; its fixed, hashed query
manifest is `.codex_artifacts/p025/d5e-cost-bindings-packet-v2-20261115.json`.
It borrows the original console session and pins the accepted setup receipt,
preservation manifest and authoritative SQL files. It uses a new create-only
intent, retains unjoined collectors, and never reconnects, retries or deletes.

Bounds: **30 native seconds**, zero Windows seconds, zero rows/inputs/databases/
backups; 23-second guest admission budget, two-second metadata statements, zero
lock wait, 220 operations, 6,144 returned rows, 700,000 aggregate SQL JSON bytes
and a 1 MiB receipt. Each result set has its own smaller bound. Backup inspection
reads metadata only; it does not hash the 10 GiB file inside this envelope.
Unknown closure retains the full reservation. At maximum consumption **959 native
seconds** remain, including the planned 600-second measured packet and **359**
for later work. No extension is needed for this collection.

## Preparation, review and handoff

Windows PowerShell 5.1 offline controls cover create-only receipts, source pins,
deadline/statement/row/byte bounds, parameter binding, reader disposal, closure
identity gaps, exact new database birth, counters and read-only SQL. They run no
SQL, VM or cost arms. SQL names and physical thresholds were checked against the
source repository. Procedure-header/whitespace and quoted RowCount/backup rules
remain in the accepted core reference and regression evidence; nothing rewrites
those accepted tests or changes catalog bodies to hide mismatches.

Initial review found fourteen logical export labels incorrectly used as object
names, including export-12's two-column projection. That unexecuted manifest and
review snapshot remain retained. The corrected collector describes the actual
pinned SELECT text for all 57 outputs using parameter-bound SQL compiler metadata;
only the two explicit old database qualifiers become the approved cost-copy name.
It adds the actual output objects to the dependency roots and compares the exact
projected column sequence. All 57 mappings, especially export-12, have regression
controls. The final PowerShell control count is 140; this is still offline evidence.

The handoff manifest records final hashes, control counts, required repository
gates and the Changes review. A full pytest run, application smoke imports and
Discord registration are skipped: this packet changes qualification collection,
not application runtime or registration. No unrelated local changes are included.
Security routing selects Changes for the precise new packet/manifest/test/doc
snapshot, with Deep off; no SQL repository change or separate SQL diff is made.

After receipt adjudication, seal the twelve-arm measurement runner against these
bindings, with actual candidate observation/diagnostic code, equal warmups, five
balanced measured pairs, raw output/date/tie adjudication, physical comparability,
observer/refusal accounting and full cleanup. That runner remains outstanding;
this read-only packet cannot establish a cost pass. Existing approval for the
twelve fresh workload/log attempts persists; accepted claims must never be replayed.
