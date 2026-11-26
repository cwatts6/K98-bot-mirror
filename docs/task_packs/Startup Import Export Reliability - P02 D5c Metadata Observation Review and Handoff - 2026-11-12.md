# P02 D5c metadata observation review and handoff

The failed Setup receipt was verified against the operator SHA256. Creation was
acknowledged; principal 15 exists in that observation. Both SQL connections closed.
Setup validation failed on its 32-hex SID assumption; the native SID is 56 hex
characters. One direct permission was also observed but remains unidentified.
Neither the diagnostic nor final fixture/preservation checks ran. The user remains
present; no native action or account correction was performed during this review.

The bounded read-only follow-up is ready for one manual run. It leaves the account
and guest state unchanged, captures its complete permission tuple, checks exact
birth identity and original accounts, and completes protected-record and cleanup
checks. Original Setup remains incomplete. No Setup retry, diagnostic or removal
is included in this handoff.

## Reviewed immutable packet

- Collector: `scripts/collect_p02_d5c_metadata_setup_observation.ps1`.
- Collector SHA256: `EA8BBCC291B84690BC53B52D05A3DBACC451C87D591D9DEE1D64E07D1E12C1E1`.
- Manifest: `.codex_artifacts/p025/d5c-metadata-setup-observation-execution-packet.json`.
- Manifest SHA256: `79fcd5ea844081d23dbba9226de0dc97e71aaa7e220dd7afc40097643d5722f0`.
- Changes review: `f614f916-c619-4a53-b63e-9b678335874b`, Deep off.
- Range: `71d743410c1f88bfe63106a1c10b7af583a62589` to `ab0560d8da6ba288ca9bb821567d658a78f005e9`.
- Completed and canonical sealed result read back successfully on 2026-11-12.
- All four frozen files reviewed; no reportable security finding or operational blocker.
- Parent and independent Windows PowerShell 5.1 validation: 365 checks passed.
- Immutable-range whitespace, deferred-item and security-routing validation passed.
- Architecture validator passed with zero Python files applicable. Test selector ran;
  broad application/startup/registration/release tests are skipped for the reasons
  in the frozen execution plan. No production source or SQL-repository file changed.
- Normal HEAD/index and all four reviewed hashes were reverified unchanged.

Tool-reported review usage: 3,796,820 total tokens, including 3,737,856 cached input
tokens, source `codex_rollout`, three threads. These are tool-reported review
accounting, not billing or native VM time. Daybreak advisory was not granted;
completed canonical local review results were nevertheless readable.

## Continuing limits and obligations

Charge two seconds for the 1.6438154-second host Setup attempt. Before this follow-up:
1,396 native seconds, 178 account-scope seconds, 50 Windows-test seconds and 21 inputs
consumed. Follow-up ceiling is 60 seconds, with 37 command units and 175 planned
maximum rows under unchanged hard caps. Later-phase reserve remains 1,000 seconds.

Keep the same elevated console/session open. On error or incomplete output, stop
without retrying or manually changing/removing the user. Return ReceiptPath and
HostPacketElapsedSeconds. No old Setup, Diagnostic or Cleanup command is suitable.

After receipt review, any corrected continuation must bind to the exact existing
birth identity without issuing CREATE. The same incorrect 32-hex assumption exists
in both the PowerShell principal validator and Python diagnostic actor, and the
tests used a synthetic 32-hex SID. Review/correct all these together if authorized
continuation is feasible. Identity preservation must precede eligibility assertions
so later failure cannot omit custody evidence. Rights acceptance remains dependent
on the follow-up; no grant, denial, revocation or ownership repair is inferred.
The diagnostic allowance is unused; it is not executable through this observation.
The approved exact-user removal still requires reviewed identity and closure proof.
No writer, isolation or maintenance retry is available. D5c and D6 release remain open.
