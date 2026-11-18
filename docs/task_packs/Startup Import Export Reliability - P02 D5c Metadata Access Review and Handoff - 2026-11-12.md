# P02 D5c metadata access review and handoff

The complete Setup/Diagnostic/Cleanup sequence is prepared and reviewed. Only the
Setup stage is ready for the next manual handoff. No native stage has run and no
temporary principal has been created by this preparation.

The operator's bounded scope approval remains in force. Full initial review
2dcef837-5bb6-4b55-834c-e4162a511bf8 completed with two operational blockers and no
reportable security vulnerability. The original packet is preserved at revision
685cb33447896f79fe150e845ea48529c4ba8857 and in the first-review evidence directory.
Both blockers were corrected before native work.

Correction review **2399b8e2-e81f-448d-b60f-1881e49ad484** completed and sealed at
2026-11-12T21:58:53.686376Z; canonical completed-artifact readback succeeded.
It reviewed revision 685cb33447896f79fe150e845ea48529c4ba8857 through
71d743410c1f88bfe63106a1c10b7af583a62589, Changes mode, Deep off. Parent and
independent review found no remaining operational blocker or reportable finding.
All six reviewed file hashes were verified unchanged after completion. The normal
HEAD remains e7443e37212ca91e20d531b3684cc369d0fe1505; the normal index is untouched.

Independent validation passed 14 Python tests, 151 Windows PowerShell 5.1 checks,
and whitespace validation. Architecture/deferred/security-routing checks passed.
Broad startup/release/full-suite skips remain justified in the execution plan.

The zero-direct-permissions expectation is a strict native acceptance condition,
not a claimed observed engine result. Unexpected rights stop Setup; no permission
repair is authorized. The new user is WITHOUT LOGIN, a non-authenticating user
type described in [Microsoft's CREATE USER reference](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-user-transact-sql?view=sql-server-ver16).

## Frozen execution pins

- Wrapper: `scripts/run_p02_d5c_metadata_access.ps1`
  SHA256 `1ff233d255b64918c61de5efb0ae0085d6061d823cc48d84115ccee6b8123674`.
- Actor: `scripts/p02_d5c_metadata_access.py`
  SHA256 `c94c0d6b368fa80b886a419b1c7b4b2063c13ed14b9cb9435a6a8e811c372044`.
- Manifest: `.codex_artifacts/p025/d5c-metadata-access-execution-packet.json`
  SHA256 `79b49283377cdda1ec735a2599478fc508fb25413264ccf6b8bf590c9d5d5a39`;
  68,090 bytes.

Setup adds only the approved new database user, records its exact generated birth,
checks inherited/direct rights and preserved records, then verifies closure. The
diagnostic and removal are separate stages after receipt adjudication. Existing
accounts, original evidence, original database and seven fixture rows are retained.

Initial balances: 1,398 native seconds, 50 Windows-test seconds, 21 inputs consumed,
zero new inputs. Setup is at most 60 seconds; the full three-stage scope is at most
180, preserving the 1,000-second later-slice reserve. Stage command ceilings are
36/48/35 and row reservations 143/152/142; all original hard caps remain unchanged.
No business workload, new fixture row, deployment or production correction occurs.
On failure, stop and return the receipt; no repeat, reset or manual account removal.

## Review usage, as reported by the tool

Original review: 3,174,549 total tokens, including 3,141,888 cached input tokens;
correction review: 2,784,744 total tokens, including 2,761,216 cached input tokens.
Each tool result reports source codex_rollout, threadCount 1 and complete coverage.
These are the review service's recorded figures, not native runtime seconds or a
billing calculation. Daybreak access was not granted; its advisory warning was
reported, and completed local canonical results were still readable.
