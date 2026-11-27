# P02 D5c restricted preflight review and handoff

The first read-only stage is ready under the approved bounded test-account scope.
No account setup, reader test, grant/deny, credential generation or native
preflight has run. The complete remaining setup/positive/denial-and-cleanup
sequence still requires implementation, offline validation and review before
account creation. Read the Restricted Scope Approval and Preflight Packet for
the four-stage allocation and exact source boundaries.

280 PowerShell 5.1 offline checks passed. Architecture validation passed for
48 Python files, deferred validation for 81 Markdown files and security-routing
validation with zero errors/warnings. The explicit selector ran. Full pytest,
startup imports, command registration and release/permission-repair suites are
skipped: no application, registration, schema or release source changed and those
suites do not exercise this read-only PowerShell collector. Frozen-range
whitespace and all three working-file hashes passed.

Changes review, Deep off, completed once and its sealed result was read back:

- Scan `adf9af20-320e-4d22-be4c-e653f21887d3`.
- Base `e8ee2d47b06d583ee1a74a6a0752766223a592e2`.
- Head `90e1aeb513c4fc5cc291e7782e01fe974bbbe69e`.
- Complete three-file coverage; zero findings.
- Sealed `2026-11-12T19:35:36.839188Z`.
- Parent implementation review; dedicated capability preflight worker. No
  independent implementation review is claimed.
- Tool-reported usage: 2,449,523 input including 2,432,512 cached; 3,850 output
  including 475 reasoning; total 2,453,373 across two threads.

The initial isolated snapshot hit object-store write permissions. The authorized
retry verified its isolated index had no staged delta, completed successfully,
and left the ordinary branch/index untouched. A draft review-record field was
corrected before finalization; final completion was called once and passed.

## Exact console handoff

Use the same elevated Windows PowerShell 5.1 console holding
`$global:D5bReportSession`. One attempt only, no automatic repeat.

- Script `scripts/collect_p02_d5c_restricted_preflight.ps1`.
- SHA256 `6cff925ba758b98315b7b3204aa34625f5b9b331d02daea5a209e92ce059ae68`.
- Manifest `.codex_artifacts/p025/d5c-restricted-preflight-execution-packet.json`.
- SHA256 `0414819bbb38f229ab601ed800a717d36fbbe01f2fc9164283ca77380b22c7ff`.
- 33/48 commands, 776/2,048 maximum rows; unchanged per-result and evidence caps.
- 45-second whole-host ceiling within the approved cumulative 180-second scope.
- Before attempt: 1,413 native seconds and 50 Windows-test seconds, 21 inputs
  consumed, zero new inputs; final 1,000 native seconds reserved for later slices.

Return ReceiptPath, displayed summary and HostPacketElapsedSeconds. Stop on any
error/incomplete output; cancel/report a hang before 45 seconds. Preserve every
receipt and do not retry or change settings. No isolation, writer or maintenance
retry is available. Receipt adjudication must establish auth-mode and inherited
permission feasibility before setup preparation is finalized. If prerequisites
fail, report that without changing sign-in mode, existing rights or VM settings.
