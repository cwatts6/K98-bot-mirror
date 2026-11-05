# S11 G4 H06 receipt addendum — 2026-09-27

This additive receipt updates the H06 proposed/awaiting-output status in the sealed capture preparation and host reconciliation. Earlier artifacts remain unchanged. It does not authorize another observation or rollout.

The operator supplied one startup-wrapper metadata row, retained in `.codex_artifacts/s11-g4-capture-preparation-20260926/received-H06-20260927T065625Z.txt`. The receipt was reconciled on 2026-09-27 at 06:56:25 UTC; this is not an execution timestamp.

## Result and limits

- Target: MINI_AMD, `C:\discord_file_downloader\start-bot-after-sql.ps1`.
- Reported size: 5,125 bytes. SHA256: `201b4f02e27890af0963422871549249fb36c0bfc0143e208822f4a1522c9b48`.
- Size and hash match the CRLF representation of the locally reviewed wrapper at isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`. The Git LF blob has a different, already retained hash; this is a known line-ending distinction.
- Reported owner: `MINI_AMD\cwatt`. The SDDL includes inherited Authenticated Users rights `0x1301bf` (Modify plus Synchronize), consistent with earlier Bot-path samples. This remains a custody/ACL release gap; it is not an effective-access certification or an instruction to change permissions.
- The supplied row contains no execution UTC, duration, exit status, or explicit before/after stability values. Execution within the approved 2026-09-26 22:37:23–22:57:23 UTC window and the 10-second budget cannot be established. Receipt after that window does not establish execution after it. Preserve the evidence without rerunning H06.
- This binds reported file bytes to reviewed source. It does not prove the scheduled task executed these bytes, the identity/token of the running Bot, successful dependency checks, S11 installation, or runtime admission.

H06 command SHA256 remains `0ef3848dfe9645e5a7d0aa6928cba33a7d546dadecc777d10128f4f185077bf3`; its approval and bounded one-file read scope are retained in `h06-approval-20260926T223723Z.json`. The wrapper was not invoked during this local reconciliation.

## Continuing boundary

The operator identifies `StartDLBotAfterSQL` as the manual restart/startup task. Its reviewed source can perform SQL, DNS, logging, and process-start operations if invoked; none is authorized by accepting this receipt. All seven typed G4 proofs and actual restore remain incomplete. Source implementation is not missing merely because installation/runtime evidence is incomplete.

The capture subpacket and host reconciliation retain the remaining identity, ACL/custody, key-metadata, provider, writer, SQL, and storage gaps. Their unapproved operations remain unapproved. Any further live capture needs its exact operation and current execution envelope approved; rollout and G5 require separate operator decisions. Keep the approved single-account model and settled report/output preferences.

Production remains on the isolated hotfix, not current production/main. Memory-cause investigation remains deferred; preserve the withdrawn collector without invocation. The empty KVK report and view-rehydration warning remain separate retained issues. No production, SQL, provider, Discord, backup/restore, activation, Git-publication, or task-control operation was performed for this addendum.
