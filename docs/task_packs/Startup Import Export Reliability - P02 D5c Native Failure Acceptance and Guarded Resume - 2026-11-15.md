# P02 D5c native failure acceptance and guarded resume

## Decision and countdown

The failed final batch completed no acceptance scenario: D5c remains 9/12 families accepted, with 18 scenarios in three groups outstanding. The separate offline recovery-route result remains 73/73 accepted. Runner controls are not extra acceptance scenarios.

The original receipt `d5c-native-final-result-983fb31ec9fa45a39f3c525d4f884f26.json` has verified SHA256 `AD363CEA234E7CD0CBDEB44486B95F89ABD89249815860F6C51C58F5F038EF63`. Its original packet, intent, staged files and failure remain immutable. All owned native and observer connections closed, the owned process joined without forced termination, and no copy-fixture commit was attempted. Final protected-state comparisons were skipped by the failure; fresh preservation is a prerequisite, not an assumed outcome.

The database creation was acknowledged: `K98_P025_D5c_Hold_20261115`, ID9, creation timestamp `2026-11-15 07:59:24.150`. Source and exact counters (156 operations, 83 rows) locate the failure at the 81-foreign-key comparison, before the clean hold row or schema commit. The likely defect is comparing SQL linguistic name ordering against Python ordinal ordering. The failed receipt does not contain the raw key names, so this explanation remains an inference. The correction compares exact names and uniqueness independently of order and retains every enabled/trusted check. It records the observed key rows for subsequent adjudication.

## One grouped continuation

Existing complete-all-three-groups approval, broad bounded rerun approval and the explicit clean-database choice authorize this continuation. No additional database is created. No original attempt, acknowledged database creation or committed fixture is replayed.

1. Verify original host receipt and source lineage, guest evidence hashes, exact VM/session, resources and all existing copy protection checks.
2. Read only: verify the exact acknowledged database identity, owner, ONLINE/SIMPLE/SNAPSHOT OFF state, fixed original data/log files and size/growth ceilings, no competing database or old-packet sessions, and empty schema after the failed transaction. Verify all 55 proposed copy-row identities remain absent and the canonical owner is unchanged. Any mismatch stops before setup.
3. In the existing empty clean database, transactionally create the unchanged source-pinned schema and one labelled hold row; check every foreign key and table before commit, then enable SNAPSHOT as already approved for this separate test database.
4. Admit the same 55 proposed copy rows only after exact absence checks. Execute the unchanged 18 scenarios: six configuration, nine coordinated-read/discovery, and three stale final-action safeguards.
5. Verify exact resulting fixture values, retained canonical owner/history, all previous protected records, source definitions, permissions, resource reserves, process join and independent SQL session absence.

The new staging directory is `Q:\D5cFinalResume-20261115`; existing database files stay in `Q:\D5cFinal-20261115`. No folder, evidence, table or database is deleted. A new CreateNew intent and receipt identify the continuation. On any failure, preserve the result and stop; uncertain commits must never be replayed.

## Bounds and balances

Charge the complete operator elapsed 3.7402815 seconds conservatively: 1,256 native seconds remain, with a 1,000-second later-stage reserve. The continuation retains the 240-second total ceiling, 180-second child work, 190-second child cleanup, 200-second child watchdog, 30-second cases, 3-second statements and 5-second logins. Outer owner/cleanup deadlines remain unchanged. No time or operation reservation from the failed attempt is refunded.

The existing limits remain: 2,448 combined operations, 4,096 combined rows, 2,400/1,536 child limits including the existing cleanup reserve, 768 KiB manifest, 256 KiB staged file, 128 KiB encoded/512 KiB expanded source, 600 KiB child stream, 1 MiB combined receipt. The extra read-only resume checks fit inside those ceilings. Windows-test time remains 50 seconds. Synthetic rows consumed remain 11 of the approved 67; the same 56 proposed additions remain pending. Inputs consumed remain 21, with zero new inputs.

## Validation and review

Use isolated original-source bootstrap, the prior 19 harness controls against the continuation, focused order/duplicate/trust and resume-refusal controls, and Windows PowerShell 5.1 pure-function/remoting controls. Validate architecture, deferred-item format, test selection and security routing. No full bot startup, provider calls, VM execution or SQL occur during offline validation. Full application suites are skipped because this is isolated qualification tooling with no production changes.

Security decision: **Changes**, Deep off, restricted to the frozen continuation packet against the reviewed original packet. SQL/session/file/process effects require this review. The unchanged schema/source ledger remains authoritative and is reverified before handoff. No production Bot or SQL source, permission, deployment or runtime correction is included.

## Deferred optimisation

None introduced. The sorting issue is corrected within this qualification packet. Historical setup failures stay separate from the fixed 18-scenario acceptance countdown.
