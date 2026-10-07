# ST02 staging creation receipt — 2026-09-28

Operator reports ST02 Completed on 9SX2VF4, FailureType=null, 25 ms. Started 12:34:41.7886747Z; finished 12:34:41.8091529Z. Reported stopwatch/UTC intervals differ slightly; preserve both without inventing precision. Within the ten-second cooperative/fifteen-second operator limits and maintenance window. Receipt recorded 12:34:59Z.

Normalized transcription is retained at `.codex_artifacts/s11-g4-capture-preparation-20260926/received-ST02-20260928T123459Z.json`. The user's console prefix showed the approved script hash check and local saved-file invocation; the normal prompt returned. No independent assistant host inspection occurred.

Created paths exactly match the approved new staging root `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11_G4_20260928_97337`, its media child and root-level route-marker.txt. Marker equals the expected 62-character value. AvailableFreeBytes=1,746,810,785,792, above 250 GiB. Capacity remains a snapshot, not a reservation.

Both returned directory ACLs have BUILTIN\Administrators owner and identical retained SDDL. Inherited entries include SYSTEM, Administrators/Creator Owner and the retained service-like SID S-1-5-80-2931557206-644353831-496829890-75705068-2459599927. No explicit ACL change was performed. Do not treat these entries as an independently established engine token/SID mapping or effective SQL media-read permission.

No data directory, database, MDF/LDF or backup media copy is established by this receipt. Existing database/file exclusions remain protected. Next is already-approved ST03 on MINI_AMD in the existing RDP session, checking the exact marker through tsclient. A byte-identical saved-file alias `commands/ST03.ps1` is prepared locally, SHA256 `092c4dcca5c90f4bd8a25d9450b10465797d53937c14c66b0f4c0ecdfa042a8d`. It may be invoked by a single hash-guarded line using its existing redirected-drive path; no helper-file copy is needed on production. It retains the approved read-only effects and fifteen-second cutoff. Do not copy backups before ST03 succeeds; stop on policy/access/error without workaround.

Validation: exact three target paths, marker value, capacity threshold and two ACL records reconciled; approved ST02/ST03 bytes and original 27 pending/394 evidence preservation checked. Receipt/alias preparation only, no live call. All seven G4 proofs and actual restore remain incomplete; rollout/G5 unapproved.
