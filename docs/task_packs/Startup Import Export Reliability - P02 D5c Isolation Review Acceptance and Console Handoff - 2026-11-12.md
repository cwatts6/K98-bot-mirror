# P02 D5c isolation review acceptance and console handoff

The single approved isolation test is prepared; **native execution is pending**.
No isolation setting has been changed by this preparation. No new input, writer,
maintenance, stale-action, provider, report, import or deployment attempt occurred.

The initial five-file review completed as scan
`be90b067-ad4f-42ae-9266-758eb5d94a7e` at
`5a1ddd243f82749443f51a8d2fe6607a0591dcd1`. It found no reportable security issue
but identified an uncertain-process-launch correctness blocker. That snapshot,
review and offline failure evidence remain preserved. The narrow correction
records launch intent and successful return before reading the handle, explicitly
rejects a missing handle, and blocks both restoration and observer admission
while launch custody is unresolved.

The corrective three-file Changes review, Deep off, completed as scan
`6ffdf5ae-3fc6-40ff-9624-8b83cfa4ef61` at
`e1526635e1b25ff894a062721fa91359f9ffa309`. Canonical completion was read back:
coverage complete, no findings, no unresolved review tasks. Independent review
confirmed the original blocker resolved and found no further correctness blocker.
The reviewer independently reran 305 inert PowerShell checks successfully.
Six isolated Python tests passed on the unchanged actor. Ruff, architecture,
deferred-item, security-routing and diff whitespace checks passed; selector
recommendations and broad-test skip reasons are in the executable plan.

The completed corrective review reports 1,910,131 tokens total, including
1,895,936 cached input tokens, across two recorded threads. This is review usage,
not native test time or consumed-input allowance.

Use the exact executable plan:
`Startup Import Export Reliability - P02 D5c Approved Isolation Refusal Packet - 2026-11-12.md`.
Final pins:

- Wrapper `scripts/run_p02_d5c_isolation_off.ps1`:
  `9e5386046e67abc9314c773b5a0a3473d1e6a5242577241cb841e96e2e5fbfec`.
- Manifest `.codex_artifacts/p025/d5c-isolation-off-execution-packet.json`:
  `3f01f13e4cbe088d9fb6159065797fc77c2d955ad98824a8fbf0a97a20228e19`.
- Python actor:
  `73b9b4bb727dc979d0c640647104bfdb53abcf938b3a2e224a43f3386d097d93`.

All three corrected frozen files were rechecked after review, and no native intent
exists. Ordinary HEAD remains `e7443e37212ca91e20d531b3684cc369d0fe1505`; neither
review snapshot changed the normal index or branch. Production modules and the
SQL repository are unchanged by this packet.

Run once in the same elevated Windows PowerShell 5.1 console holding
`$global:D5bReportSession`. The assistant cannot access its authenticated session.
Return the summary, complete ReceiptPath and HostPacketElapsedSeconds. Stop on
any error or incomplete output; do not retry or manually toggle the database
setting. Cancel and report a hang before 60 seconds. Preserve the console and
all evidence for adjudication. Any uncertain restoration or cleanup blocks
further native work.

Balances before execution remain **1,421 native seconds**, **50 Windows-test
seconds**, **21 inputs consumed**, seven admitted fixture rows. This cycle does
not use Windows-test seconds. All existing caps, original evidence and later-phase
reserve remain unchanged. No writer or maintenance retry is available.

After execution, verify receipt/hash/lineage, exact prerequisite refusal, native
3952, one acknowledged OFF/ON cycle, stable restored setting, full fixture hash,
protected metadata/resources, process exit and physical SQL absence. Charge the
rounded-up full host elapsed time even on failure. Do not mark this case or D5c
complete merely because the wrapper reports a collected result. Remaining D5c
and D5d-f obligations, then separate D6 release/D7 acceptance, remain open.
