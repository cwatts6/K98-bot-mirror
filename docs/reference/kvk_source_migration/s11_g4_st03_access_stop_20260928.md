# ST03 access-denied receipt — staging stopped

Operator receipt: MINI_AMD, ST03, Stopped, System.UnauthorizedAccessException, MarkerMatched=false. Started 2026-09-28T13:03:02.8408134Z, finished 13:03:02.8699359Z, reported 27 ms. Normal PowerShell prompt returned. Failure occurred within the approved time limit; this is not a timeout or continuation-input symptom.

Normalized user-supplied JSON is retained at `.codex_artifacts/s11-g4-capture-preparation-20260926/received-ST03-20260928T130323Z.json`. Receipt recorded 13:03:23Z. Original command/approval seals and previous receipts remain unchanged.

The exact attempted marker path is `\\tsclient\C\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11_G4_20260928_97337\route-marker.txt`. MarkerMatched=false is the initialized default on failure, not an observed unequal marker. The script exposes exception type but no failing-stage field; distinguish metadata/open/read failure location as unresolved. Do not infer marker absence, deletion, corruption, wrong machine or a failed hash check.

The console transcript shows the approved helper was invoked from the redirected repository path and returned ST03 JSON. This supports accessibility of that helper path, not general read/write access across the redirected C drive or verified target-machine identity.

## Source-grounded interpretation

ST02 reported Administrators ownership and inherited access entries for Administrators, SYSTEM, Creator Owner and the retained service-like SID. It did not establish the RDP client process's effective token or marker-file ACL. Access denial through drive redirection is consistent with a difference between local administrative access and redirected access to this protected SQL directory, but the token/ACL cause is not proved. No fresh token, ACL, service or SQL inspection has been performed. This is not evidence for reopening the deferred SQL memory investigation.

The selected protected SQL directory was not yet proven suitable for direct RDP transfer. Do not solve that by widening its ACL, running the RDP client elevated, altering service credentials, taking ownership, disabling protections or changing accounts under the earlier approval.

## Stop and retained state

The staging group's stop rule applies: no manual backup copy or ST04; no ST03 retry. ST01R1 source hashes and ST02 creation evidence remain valid historical observations. Retain the created root/media/marker unchanged; no cleanup. No database/data directory/restore has been established by these receipts. Do not infer whether any other operator action occurred beyond supplied evidence.

Next preparation option: use an exact new user-profile transfer inbox on development, verify its route/access/ACL and absence under a newly bounded packet, then plan an explicitly authorized local admin copy into the existing protected media directory with hash checks. This preserves the SQL directory's existing ACL and the single-account model. The inbox path, creation/copy commands, additional temporary-copy capacity/I/O and retention must be made concrete before requesting execution approval. No route preference question is reopened; admin manual copying and existing RDP redirection remain settled. This is a proposal, not a workaround already authorized or performed.

All seven G4 typed proofs and actual restore remain incomplete; rollout/G5 unapproved. Maintenance scheduling remains approved through 2026-09-29T09:23:23Z; it does not override this operation stop. Historical collector remains withdrawn, memory cause deferred, KVK/view issues separate.

Validation: local supplied-field/path reconciliation, original command/approval hash verification and preservation checks. No new live diagnostic or permission mutation; documentation-only receipt requires no runtime tests or discovery scan.
