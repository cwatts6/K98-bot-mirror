# P02 D5c scope refusal review and handoff

The complete two-case packet is ready for the first native handoff. Native
behavior is not yet qualified. The first handoff is Stage WrongAccount only;
review its receipt before giving Stage WrongStorage. Both are already authorized
read-only D5 work and each has one attempt, without automatic retry.

## Frozen review and validation

Changes scan `19434870-53fe-413d-806c-3a1967704910`, Deep off, reviewed exact range
`e7443e37212ca91e20d531b3684cc369d0fe1505` to
`69cf944b3465bf70fb76cfb7242ca9e488a0a17e`. Completion and sealed readback are
verified at `2026-11-12T20:48:42.112038Z`. No security candidate or blocking
correctness finding remains. Parent and independent worker covered all six
frozen files, including tests, manifest and plan; the automated source inventory
listed three source-like entries, not the entire six-file coverage set.

Eight actual-DAL Python tests and 131 Windows PowerShell 5.1 checks passed, also
independently rerun by the reviewer. Architecture checked 52 Python files,
deferred validation checked 89 documents, security routing reported zero errors/
warnings, and the frozen diff passed whitespace checks. All six snapshot hashes
and original receipt lineage match. No native SQL/VM operation occurred.

The explicit selector recommends broad pytest, startup imports, registration
and release/schema/permission-repair suites. These are skipped with the rationale
in the execution plan: only isolated operational test tooling changed, and the
actual selected DAL/helper is exercised through inert transport. No application
runtime, deployment, schema or permission repair changed. Production guards are
unchanged. No second review of the same unchanged packet is required after its
first receipt passes adjudication.

Reported scan usage is 4,829,034 total tokens, including 4,776,192 cached input
tokens, across three recorded threads; this is service-reported cumulative
usage, not additional native time. Advisory Daybreak access was not granted;
review completion and canonical artifact readback succeeded.

## Exact handoff

- Script: `scripts/run_p02_d5c_scope_refusal.ps1`, SHA256
  `27c500106ba963b16e9bec663d48a6611c0e19c771359cf266dbf3ffc29f8afb`.
- Actor: `scripts/p02_d5c_scope_refusal.py`, SHA256
  `996b810042117dd406d5ec829a14ea8c97a1b3f2ee9a5a6ceb6941122bd2c0f8`.
- Manifest: `.codex_artifacts/p025/d5c-scope-refusal-execution-packet.json`, SHA256
  `2270541476c3a6b1b1c0f010e04caf550a56d46cd01166ab37f5f8f26abb99d2`.
- Manifest size 124,895 bytes; normal budget 44/48 units, 142 maximum planned rows.
- Same elevated PS5.1 console and `$global:D5bReportSession`; Stage WrongAccount.
- Return summary, ReceiptPath and full HostPacketElapsedSeconds. Stop on error
  or incomplete result without retry; cancel/report a hang before 60 seconds.
- Keep the console open. Do not invoke WrongStorage until the first receipt
  is accepted and its exact elapsed debit recorded.

Balances before execution: 1,406 native seconds, 50 Windows-test seconds,
21 inputs consumed and zero new inputs. Preserve the 1,000-second later reserve,
all original receipts and limits, and no writer/isolation/maintenance retry.
No account creation, data mutation or permission change is included.

## How much D5c remains

Seven D5c case groups remain partly open in the saved reconciliation: full
inspectors (C01), season/weights (C04), queue/pool/unowned-hold (C05), specific
action boundaries (C06), attribution variants (C07), remaining identity/factory
cases including this pair (C09), and presentation integration (C12). These are
unequal groups, not seven commands or a measured percentage. Accepted named
subcases remain accepted; no blanket replay is proposed. Further fixture or
permission exceptions still need exact proposals where required.

D5a and D5b are complete. D5d failure/restart work, D5e balanced cost checks and
D5f final reconciliation follow. D6 deployment remains a separate decision; no
P02 production deployment or first normal import/export is authorized here.
