# P02 D5c reader-first acceptance and fresh snapshot packet

## Accepted reader-first result

Receipt `d5c-config-reader-first-result-507553c632e44e009b00e611858de7b3.json`,
SHA256 `e37a7f2498a0b4a0f465a97989da168712ce784030c55053ff603b17514a191c`,
passes saved-evidence adjudication. The actual reader retained the original
3/22/19 view across the distinct writer's acknowledged commit of 4/23/20.
The exact three changes, distinct sessions, protected metadata, reader rollback,
isolation restoration, process exit and physical SQL closure were verified.
The writer's conditional cleanup rollback was a no-op after commit; it did not
restore the test versions. The one approved committed transition is consumed.

The receipt reserves 48 commands and records 111 actual rows. Host time
1.3664851 seconds debits two. Remaining balances are **1,425 native seconds,
50 Windows-test seconds, 166 configuration-scope seconds and 108 follow-up test
seconds**. The final 1,000 native seconds remain reserved for later D5 work.
The 21-input allowance remains consumed; seven fixture rows exist and no rows
are added. No writer-first or maintenance retry is available. Original failed
receipts remain failed and all original evidence is preserved.

Acceptance is saved in `.codex_artifacts/p025/d5c-config-reader-first-acceptance.json`.
Fresh durable observation is still required before the stale-action test.

## Next authorized read-only packet

`scripts/collect_p02_d5c_config_fresh_snapshot.ps1` invokes the unchanged actual
full-snapshot actor `scripts/p02_d5c_config_snapshot.py`. It requires the full
saved snapshot with only the three approved committed versions changed to
4/23/20, then verifies protected metadata, resources and physical cleanup.
It does not write, settle, restore versions, import, report, run maintenance,
dispatch backups or contact a provider. Permissions, settings and original
database remain unchanged. The later stale-action refusal is a separate packet.

This is a new create-once attempt within the existing seven-row fixture approval.
Manual ceiling is 60 seconds within the remaining 108-second test allocation.
Existing 46-command reservation, 147 planned rows and all per-result, total row,
receipt, manifest, staged source, resource and cleanup limits are unchanged.
Native host elapsed time is rounded up and debited once; this SQL observation
does not debit the Windows-test allocation. Failure stops without replay.

## Review and validation

Six offline Python tests and 195 PowerShell checks passed. A separate exact
comparison of the finished files verified that the wrapper differs from the
reviewed full-snapshot parent only in attempt/custody names, remaining-time
literals and manifest pin. All 23 SQL statement objects, actor bytes, runtime
bindings and 17 production modules are unchanged. Decompressed payload differences
are exactly the preparation version and two resource versions in both expected
projections. All other manifest differences are explanatory text, lineage,
remaining balances and consequent bundle pins. Both new lineage receipts hash
correctly. No native attempt has run.

Focused Ruff and architecture validation passed. The explicit test selector
completed; its broad application recommendations are skipped for the reasons
below. Deferred-item validation passed for both updated documents and security
routing validation passed with zero errors or warnings.

Review evidence: `.codex_artifacts/p025/review_d5c_fresh_equivalence.py`,
`d5c-config-fresh-snapshot-equivalence.json` and the offline Python/PowerShell logs.
The authoritative SQL source pins remain enforced by the existing validator;
no SQL repository changes occur. No production refactor or new deferred item is
introduced by this mechanical test instance.

**Security review decision: documented skip of a new scan.** The inspected target
is the new wrapper, its two test files and generated execution manifest compared
with the already-reviewed full-snapshot packet. These changes instantiate fixed
test expectations and rename evidence custody paths without changing executable
control flow, SQL/data-access behavior, permissions, dependencies, input handling,
deployment or persistence logic. Parent Changes review
`b76235be-7d30-485c-86a0-cc33d11aecd1` completed with zero findings. This packet
received the exact-equivalence review above; no new security scan is claimed.
Codebase/Deep review does not apply. Any non-mechanical change requires routing
again before handoff.

Full application pytest, smoke imports, command registration and deployment
tests are skipped because no application/runtime, Discord, dependency or release
code changes. Focused tests cover this fixed test instance. Offline success is
not native acceptance. D5c/d/e/f remain open; P02 is not deployed by this packet.

## Handoff pins

- Script SHA256: `70d9212c82d4cf9101323bdab43686da68103827b615c1f8ce8ad24b446f02e2`.
- Manifest: `.codex_artifacts/p025/d5c-config-fresh-snapshot-execution-packet.json`.
- Manifest SHA256: `485c73011f3f5878800557343fb54aa37db71ad8838458804693916a5cb008eb`.
- Manifest bytes: 125521, below the unchanged 128 KiB limit.
- Run once in the existing elevated PowerShell 5.1 console using
  `$global:D5bReportSession`; retain the receipt and full host elapsed time.
- Stop on error/incomplete output. No retry, test-value restoration or evidence
  deletion. Adjudicate the full durable snapshot before any stale settlement.
