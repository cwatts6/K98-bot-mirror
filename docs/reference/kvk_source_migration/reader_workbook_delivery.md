# Reader workbook delivery contract

The opt-in `reader_workbook_v1` transport renders the accepted Stage 4 projection.
Legacy `GoogleSheetsTransport` remains the default. No production factory is switched
by this implementation. Integrated acceptance has passed on disposable targets;
rollout and production activation remain separate operator decisions.

Cumulative and comparison reports require identical pinned kingdom-to-camp
membership across the included fights and independently published Overall report.
Camp IDs alone are not permanent group identities. Configuration version, row order
and camp-label changes are allowed when membership is unchanged. No-fight windows
do not contribute to this compatibility check; conflicting membership stops the
export before any provider write.

## Naming and delayed-write safety

Readable aliases are presentation only. Data, formatting, filters and index writes
address numeric sheet IDs, never mutable titles. Each registered file starts with
one verified blank grid. New IDs are allocated strictly above that grid's ID.
The existing owned retirement operation deletes all old grids and creates a blank
grid at `max(sheetId) + 1`. That surviving grid carries the allocation high-water
mark across restarts and season rollover; no previously issued ID is reused.
Exhausted IDs fail closed and require retiring the file itself.

Before any provider mutation, the coordinated worker records the full file-to-title-
to-ID bindings and original index grid ID in `dbo.ExportAttempt.ManifestJson`.
The existing hash, ownership fence and bounded JSON contract apply. Each part's
Drive description also retains its version, immutable content manifest, grid
bindings and index ID. Cold content reconciliation reads those bindings; it does
not recreate a plan from names. A delayed old data or index write can therefore
address only its old grid, which either remains its retained generation or no
longer exists. Checking a mutable title is never the write fence.

This transport refuses direct reuse of assigned files. Existing output-pool
retirement must first prove finality and complete the owned clear. Uncertain
mutations retain their claims and are never blindly replayed. A delayed allocation
or permission request is covered by the same all-writer retirement/finality gate;
numeric IDs alone do not authorize releasing that gate. All readers are retained
by default. Explicit operator retirement remains necessary for pool capacity.

The index remains one `Sheet1` with the machine pointer in A1:C1. Its write uses
the persisted grid ID, so an old season cannot address the replacement Sheet1.
Same-season publication continues to require the existing serialized durable
ownership and monotonically increasing fence; these are not replaced by the ID.

## Physical and type contract

Every reader table has five context rows, headers on row 6 and data from row 7.
The complete Report Directory is first in the first file and links every physical
partition. Report Guide links resolve across files. Aliases are case-insensitively
unique and at most 31 characters; full titles remain in row 1. Counts, decimals,
UTC date serials, blanks and text use explicit ExtendedValue types. IDs remain
text. No formulaValue or USER_ENTERED parsing is permitted. Unrepresentable
numbers stay blank in the reader and exact in the audit. Oversize or unsupported
control-character text fails before delivery rather than being silently truncated.

Readback checks literal types, numeric values, formats, headers, context, links,
grid IDs, dimensions, panes, filters and complete directory against the manifest.
Empty cells omitted by the provider and integral number serialization normalize
consistently; text "1" and number 1 remain distinct. Number formats are checked,
including percentage formatting applied once to the Tanking Score fraction.
Google's whole-cell hyperlink readback and duplicate quantized RGB style are
normalized narrowly; changed links, conflicting styles, formulas and rich-text
runs fail verification.

Both writers use bounded column widths: report names 340 pixels, player/camp/period
labels 240, source filenames 380, descriptive notes 420, UTC times 180 and numeric
columns 140. Text columns and headers wrap; numeric data stays on one line. Excel
uses corresponding character widths. Widths are included in the manifest, and
Google readback verifies every column. Only column pixel-size updates (80–480)
are admitted at the provider boundary; row resizing, hiding and arbitrary fields
are not admitted by this addition. All writes still address immutable grid IDs.

Partitions account for five context rows, the header, an empty data row when
needed, the complete directory and reserved cell headroom. Row limits also respect
Excel's 1,048,576 rows. All logical sheets and their own/cumulative pairing remain
in the complete guide/directory even when split across files. No provider file is
created implicitly. Capacity shortfalls return the existing setup-required result.

Local Excel output uses the same generation/partition functions and returns ZIP
bytes containing fixed-name XLSX parts, exact audit JSON, reader-exact JSON, the
versioned manifest and inert CSV files. Imported names cannot become archive paths
or executable formulas, including directory titles. Cross-file links require the
XLSX parts to remain together after extraction.

## Composition and SQL

`deliver_coordinated_export` accepts `ReaderSheetsTransport` only with an explicit
authorized `reader_guild_id`. It loads the Stage 2 frozen history and pinned intent
once, builds the Stage 4 checkpoints and physical generation, and preserves them
through publication. The old transport retains the old loader and manifest.
The captured legacy provider adapter is unchanged; the actual credential authority
protocol gains only bounded typed-cell/filter operations and bounded grid readback.

No Stage 5 SQL schema, ProcConfig or query changes are required. The authoritative
`dbo.ExportAttempt` definition supports the existing 65,536-byte UTF-16 JSON
manifest limit. Existing Stage 2 history schema must be installed before enabling
the optional reader loader. Larger partition manifests fail that existing bound
before writes.

## Acceptance and release boundary

The final Stage 6 combined regression passed 1,014 tests, including 14 actual SQL
cases on the approved disposable ExportHistory database. A full repository run
passed 7,537 tests with 105 explicit environment/opt-in skips and eight subtests;
the 14 relevant skipped SQL cases were subsequently exercised in the combined run.
The display/readback follow-up was verified separately after that full run.
Actual Google acceptance verified 62 synthetic reports plus directory, a fresh
transport readback, native numeric SUM/sort/filter and percentage display. Native
Excel checked 153 tabs across full, skipped-window and real KVK16 examples.
KVK16 source reconciliation covered 5,806 players, 36 kingdoms and four camps with
zero mismatches, including the 2,123 repaired derived ratios.

The offline replay contains only four retained input-file facts; it does not
reconstruct the original complete import-attempt ledger. Full history capture and
replay are covered by SQL integration fixtures. Live provider acceptance used the
transport directly; SQL coordinator integration used a fake provider. Large-season
provider throughput and source-copy locking remain rollout checks.

PR publication does not activate the reader, deploy SQL, change production flags,
republish historical results or backfill anything. The additive SQL migration must
precede any future authorized reader activation. Preserve old publications,
snapshots, receipts and outputs for audit/rollback.
