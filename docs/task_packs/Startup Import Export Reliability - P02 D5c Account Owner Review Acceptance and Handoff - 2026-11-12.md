# P02 D5c account owner-first review acceptance and handoff

The corrected packet is ready for one native attempt under the existing D5c
lock-only approval. It has not run; its create-once intent is absent. No additional
permission, data, isolation-setting or maintenance approval is implied.

## Accepted prior result and limits

C10 isolation refusal/restoration passed saved-evidence adjudication. Its receipt
`d5c-isolation-off-result-331dc98e08a24d5187fe77b6611f25f3.json` has SHA256
`2c806c7f73c4f564c7849c71eadfb23d334d3a80b88b20f0e4ac7be66d8523cf`.
Its 1.7095893 host seconds debit two, leaving **1,419 native seconds and 50
Windows-test seconds**. Inputs consumed remain **21**, new inputs zero. The
isolation cycle, writer and maintenance allowances have no retry available.
Original receipts, failure histories and seven fixture rows remain preserved.

## Review outcome

The initial completed Changes scan `0097fcc8-2de8-48ce-97da-4cb85ca50002`
identified a missing diagnostic-dependency/error-attribution blocker. Original
snapshot and manifest remain preserved. The correction adds only unchanged
diagnostic modules to the test bundle and retains first-failure facts and bounded
cause records separately from cleanup failures. No production module changed.

Corrective Changes scan `136a1f42-dc32-4cdb-b30c-2f4db62b0c16`, Deep off,
completed and sealed successfully, then was read back. Its immutable range is
`e18eb3ccd450335b4da04597b4dccade126366aa` to
`6c63b595449e4c9b7116acb277da4e14100e8ef9`. All four changed files were covered,
including tests and the plan omitted from the automatic two-source inventory.
Independent review confirmed the original blocker is closed, with no remaining
correctness blockers or reportable security findings in this diff.

Eight isolated Python tests and 221 PowerShell checks passed. Ruff and diff
whitespace checks passed. Earlier architecture/deferred/security-routing checks
and the selector passed; broader test skips remain justified in the execution
plan. These are offline checks, not evidence of native success.

Measured corrective scan usage: 1,483,231 total tokens, including 1,453,824 cached
input tokens, across two recorded threads. This is review usage, not native time.

## Exact packet

- Wrapper: `scripts/run_p02_d5c_account_owner_first.ps1`
- Wrapper SHA256: `388e74a7fde8067e758af22be61eef6d8ea17ff15f06b1a8fe2ff191fc3e845e`
- Actor SHA256: `ac5deac4095e9c784dae1fe3f86c591545246bc32a276c57c1a8750aa1f13bb0`
- Manifest: `.codex_artifacts/p025/d5c-account-owner-first-execution-packet.json`
- Manifest SHA256: `efc8ecfa7d1ff484245dec5c19b28394cfade36a7fac2bb54890ac9cfa52cc29`

Frozen file hashes and manifest were verified again after review. Ordinary HEAD
and index were not changed by the isolated review snapshot.

The packet holds the existing fixture account lock, invokes the actual target-data
reader on a separate connection, verifies the holder remains exclusive after
reader closure, then rolls back/closes and checks preservation and physical SQL
absence. At most 48 command units, 144 planned rows, 60 host seconds, unchanged
resource floors and evidence-size caps. It creates no fixture rows or work demand.
No import, report, maintenance, backup or provider request is dispatched.

Use only the existing elevated Windows PowerShell 5.1 console and authenticated
`$global:D5bReportSession`. Run once, return ReceiptPath, SHA and full host elapsed
time. Stop on any error or incomplete result; do not retry, reset work, delete
evidence or change settings. Cancel/report a hang before 60 seconds. Receipt
adjudication is required before any following native work. The full inspector,
reverse ordering and remaining D5c/D5d-f obligations remain open; this packet does
not authorize D6 deployment or D7 live acceptance.
