# P02 D5c rights inventory review acceptance and handoff

The read-only existing-rights inventory is ready for one attempt under existing
D5 preparation approval. Both account target-data orders are accepted; their
evidence and original failures remain unchanged. Current balance is **1,415 native
seconds, 50 Windows-test seconds, 21 inputs consumed and zero new inputs**.

Changes review `616e59f2-851d-45d7-9203-84a4e5d52d3d`, Deep off, completed and its
sealed documents were read back. Immutable range:
`6beec002f8293ff1b4e320a4d40076a3c832bc6f` to
`2f368a335e05f3aac2d7d091eaa64c29a72b7313`. All three files and the pinned
manifest were reviewed, including the tests and plan omitted by automatic source
inventory. Independent review found no correctness blockers or reportable
security candidates. 318 offline PowerShell checks, architecture, deferred,
security-routing and whitespace checks passed; explicit test selection ran.
Application/full pytest skips are justified in the plan. No native success claimed.

Measured scan usage: 2,756,868 total tokens, including 2,740,224 cached input tokens,
across two recorded threads. Review usage does not debit native test seconds.

Exact packet:

- `scripts/collect_p02_d5c_rights_inventory.ps1`, SHA256
  `ab4d1f3ec15a6fce62a9cceea669194c05a2c33fd6d9f32070edf32a6863b580`
- `.codex_artifacts/p025/d5c-rights-inventory-execution-packet.json`, SHA256
  `d77760b52ca70b17f39c4208bcd65e557da43a232c5a19fa28ca2c64a9ee0d1c`

It reads four existing principal mappings, transitive database roles/public and
relevant explicit permissions for seven fixed objects. All 30 protected metadata
observations remain, with physical SQL cleanup and original-history checks. It
does not impersonate, create accounts, grant/deny rights, change data/settings,
launch Python or dispatch any workload. Missing mapping/permission data is not
proof of authenticated access or effective denial; adjudication must preserve
metadata-visibility uncertainty and fixed-role semantics.

Bounds: 39/48 command units, 815/2,048 planned rows, 512 maximum per result, 60 host
seconds, unchanged resource/evidence limits. Windows-test allowance is unused.
Use the existing elevated Windows PowerShell 5.1 console holding
`$global:D5bReportSession`. Run once and return summary, ReceiptPath, SHA and full
host elapsed. Stop on error/incomplete result, with no retry, reset or deletion;
cancel/report a hang before 60 seconds. Receipt adjudication precedes any next
step. Any account, grant or impersonation exception still requires its own concrete
approval. No isolation, writer or maintenance retry or deployment is included.
