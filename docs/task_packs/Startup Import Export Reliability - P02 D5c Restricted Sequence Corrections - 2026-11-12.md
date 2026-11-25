# P02 D5c restricted sequence corrections

The complete first sequence was reviewed before native execution and withheld.
Frozen revision `32b43b30ece2e1c32e66205aacd7d8ecefe17cd0` and completed Changes
review `3a45b03c-da7a-41cd-bd89-51aa1b937f8e` preserve that evidence. The review
found no reportable security vulnerability, but three operational blockers.
No account creation, credential generation or further VM work occurred.

1. The denied case reserved 11 actor commands but could use 13 if the SELECT
   unexpectedly succeeded. The corrected actor has a mode-specific 11-command,
   one-row budget. If its first preparation execute succeeds, it raises failure
   immediately before fetching or reading resources/streams. The actual helper
   still rolls back, restores isolation and closes within the reserved 11.
2. Physical closure was tied to successful qualification. The wrapper now
   independently validates matching actor/process/SQL identity, process exit,
   acknowledged rollback/close and zero unresolved custody before checking the
   test verdict. A failed but physically closed test remains failed and can use
   the already-authorized guarded CleanupOnly stage. A definitive process
   non-start also permits cleanup; an ambiguous start, unreadable receipt,
   mismatched identity or unconfirmed closure remains blocked. Every removal
   still requires the generated SID and absence of its SQL sessions.
3. Timeout/fallback receipts subtracted only the current stage from the initial
   native balance. Both now use the same explicit conservative lower bound
   of 1,262 as the normal receipt. Exact whole-host debits are still adjudicated
   after each run; no prior time or input allowance is restored.

Eight offline Python tests and 164 PowerShell checks passed, including execution
under Windows PowerShell 5.1. New regressions cover unexpectedly successful
denied SELECT, closed-but-failed qualification, definite process non-start,
running/mismatched/unconfirmed actor rejection, and all fallback ledger paths.
The complete original sequence review plus a frozen Changes review of this
correction are required before Setup. Native SQL syntax/authentication remains
unproven until the approved qualification; no permission broadening is included.

Original limits remain: 1,412 native seconds, 179 restricted-scope seconds,
50 Windows-test seconds, 21 consumed inputs, zero new inputs. Setup/Positive/
Finish ceilings remain 45/45/60 seconds, 40/47/48 commands and 156/161/156 rows.
All original failures, seven fixture rows, candidate definitions, VM/resources,
no-retry limits and final 1,000-second later-phase reserve remain unchanged.
No runtime correction or production deployment is part of these harness fixes.

The first review's measured usage was 5,874,149 total tokens, including 5,813,120
cached input tokens, across two threads; this is the service's cumulative usage
record, not native test time. Completed review documents were read back and
sealed at `2026-11-12T20:09:28.081822Z`.
