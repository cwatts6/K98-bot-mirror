# P02 D5c account reader-first review acceptance and handoff

One account reader-first native attempt is ready within the existing lock-only
D5c authorization. The accepted owner-first receipt and original evidence remain
preserved. Current balance: **1,417 native seconds, 50 Windows-test seconds, 21
inputs consumed, zero new inputs.** No isolation, writer or maintenance retry.

The exact five-file Changes review, Deep off, completed successfully and its
sealed documents were read back: scan `38c1f585-e5d8-4812-ba0b-9e1e9aa1962d`,
range `6c63b595449e4c9b7116acb277da4e14100e8ef9` to
`6beec002f8293ff1b4e320a4d40076a3c832bc6f`. Independent source/wrapper/test review
and parent scope review found no remaining correctness blockers or reportable
security findings. Ten Python tests and 226 PowerShell checks passed; Ruff,
architecture/deferred/security-routing and whitespace checks passed. Broader
suite skips are recorded in the execution plan. No native result is claimed.

Measured scan usage was 2,415,985 total tokens, including 2,389,376 cached input
tokens, across two recorded threads. This does not debit native execution time.

Exact frozen packet:

- `scripts/run_p02_d5c_account_reader_first.ps1`: SHA256
  `f8b6e187e7d479168e254b777880b5a99f3baa59965ab169d4139da0c0ce5a06`
- `scripts/p02_d5c_account_reader_first.py`: SHA256
  `2622101a2be6ae1d82bfffdd1d8619ccff2bfc43b1c36bc7f4651beb7bccd30d`
- `.codex_artifacts/p025/d5c-account-reader-first-execution-packet.json`: SHA256
  `4af8f41a1c15c7e1fbf2bc9700f4a5cf8b7fa10c2b48d4818a16b0d6feac1aeb`

The actual reader fetches the preparation first. The fixed test hook then acquires
the account lock on a separate identified connection while that read remains
open. The reader continues without changed data or substituted production guards.
Require the exact target, exclusive holder after reader closure, rollback/close,
unchanged protected records and independent physical session absence.

Use only the existing elevated Windows PowerShell 5.1 console and authenticated
`$global:D5bReportSession`. Run once and return ReceiptPath, SHA and full host
elapsed time. The unchanged bounds include 48 command units, 144 planned rows,
60 host seconds, original resource floors and evidence-size caps. No new rows,
permissions, settings, provider requests, import, report, maintenance or backup.
Stop on error or incomplete output without retry/reset/deletion; cancel/report a
hang before 60 seconds. The next receipt must be adjudicated before further native
work. Full inspector coverage, wider D5c and D5d-f remain open; deployment is
separate. Ordinary Git HEAD/index remain unchanged by the isolated review snapshot.
