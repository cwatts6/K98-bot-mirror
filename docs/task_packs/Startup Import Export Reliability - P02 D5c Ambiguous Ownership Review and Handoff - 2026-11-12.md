# P02 D5c ambiguous ownership review and handoff

The disappearing-holder receipt is accepted separately. The next ambiguity
packet is ready for one manual attempt; no new native work ran during preparation.
Remaining balances: **1,400 native seconds**, **50 Windows-test seconds**, **21
inputs consumed**, zero new inputs; preserve 1,000 native seconds for later D5.
No prior maintenance, writer, isolation, foreign-scope or disappearance retry.

Ten Python tests and 146 Windows PowerShell 5.1 checks passed. The offline
comparison failure and exact pre-correction files remain preserved under
`d5c-ambiguity-offline-failure-ownership-comparison`. Architecture validation
checked 56 Python files, deferred validation checked 94 Markdown files, security
routing returned zero warnings/errors and frozen diff whitespace passed.
The test selector's full pytest, smoke imports, command-registration and unrelated
release/schema/permission-repair suites are skipped: only isolated qualification
tooling changed, with targeted actual-diagnostic and wrapper controls tested.
No application/native startup or runtime correction was performed.

Changes review `ed6bcc45-fc84-4058-8a84-5c0845a1f516` completed and sealed at
2026-11-12T21:26:46.252996Z. Deep was off; exact range
`e7443e37212ca91e20d531b3684cc369d0fe1505..93e4f86cb940ab3186175b93918114ef5f36dd6c`.
All six files were covered: parent actor/tests/plan and independent wrapper/
manifest review. No reportable security finding or operational blocker remains.
Canonical completed records were read back successfully. Reported usage was
2,485,118 tokens including 2,470,144 cached input tokens (tool-reported one-thread
accounting); these are review metrics, not native seconds.

## Frozen execution pins

- Wrapper `scripts/run_p02_d5c_holder_ambiguous.ps1` SHA256:
  `dc1d5bda65caa771d57e940a5cfce0e116c5f4c981a4e1ad7f520098e283525e`.
- Actor `scripts/p02_d5c_holder_ambiguous.py` SHA256:
  `2c0d3626dc8a4b4f0d90be98189d881decb1d5535d89e01305cdf35ebf1f76e8`.
- Manifest `.codex_artifacts/p025/d5c-holder-ambiguous-execution-packet.json`:
  `2c34b8df411635038e33456a28052763becfb9569806f6dbe0656fd64bc1e87f`.
- Stage `Ambiguous`, existing `$global:D5bReportSession` only.

All six hashes matched at handoff. The new intent
`d5c-holder-ambiguous-ambiguous-execution-intent.json` was absent. Preparation
acceptance is `d5c-holder-ambiguous-preparation-acceptance.json`.

Run once in the same elevated Windows PowerShell 5.1 console. Hash-check the
wrapper and invoke the exact manifest/stage while measuring full host elapsed.
Return the summary, ReceiptPath and HostPacketElapsedSeconds. Keep the console
open. Stop on any error/incomplete result without retry, reset, manual setting
change or evidence deletion. Cancel/report a hang before 60 seconds.

The test uses two actor sessions plus one observer. One holder owns Shared locks
under Session and Transaction lifetimes; one requester must be refused Exclusive.
The unchanged diagnostic must return unavailable with two exact ownership rows,
verified against independently observed session births and connection GUIDs.
Rollback occurs once before Session release, followed by reverse connection
closure, process exit, independent session absence and preserved records. There
are 46 reserved units and 153 planned rows within the existing hard caps.

No data, fixture, account, permissions, isolation, import, report, maintenance,
backup, provider or production change. No further native step follows until this
receipt is adjudicated. D5c and later D5 slices remain open; deployment is separate.
