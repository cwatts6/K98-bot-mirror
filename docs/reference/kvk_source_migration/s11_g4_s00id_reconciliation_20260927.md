# S00ID identity receipt — 2026-09-27

The operator supplied one tab-separated row, mapped positionally to the four columns in the exact approved S00ID query:

| Column | Supplied value |
|---|---|
| observed_utc | 2026-09-27 09:51:33.6387804 |
| server_name | mini_AMD |
| database_name | ROK_TRACKER |
| original_login | MicrosoftAccount\cwattsconsulting@outlook.com |

Raw row: `.codex_artifacts/s11-g4-capture-preparation-20260926/received-S00ID-20260927T095203Z.txt`. Its timestamp derives from SYSUTCDATETIME in the approved query and falls within the 09:50:22–10:10:22 UTC window. Start/end and elapsed duration were not supplied, so full duration compliance is not established. No error was supplied. Receipt time is 09:52:03Z, not execution time.

mini_AMD passes S01R1's lowercase server comparison and ROK_TRACKER matches its database target. The returned original login does not match the prior expected MINI_AMD\cwatt; it explains the identity-guard stop for this observed session, assuming the unchanged connection requested for S00ID. No session continuity proof beyond the operator workflow is claimed. The server's original-login value, UI principal label and Windows observer identity are separate evidence fields; do not declare them equivalent or infer account/SID mapping from spelling.

The existing Windows Authentication choice remains operator-confirmed. This observation does not establish a new credential, a second required Windows account, application SQL permissions or the future restricted application principal. Preserve the approved single-account model. Earlier SSMS display/operator statements are retained as their original sources rather than rewritten.

A proposed S01R2 can bind the guard to this exact server-reported original login, with every other metadata target and restriction preserved. That requires explicit operator acceptance of this SQL observer and the revised query; S00ID approval does not adopt it automatically or authorize a retry. No SQL has been executed by the assistant in this reconciliation.

All seven typed G4 proofs and actual restore remain incomplete. No S11 object-presence inference follows from S00ID. Original S01R1 guard failure remains preserved. Validation is local receipt/query comparison and evidence integrity checks only; no application/configuration/permission changes or PR, so runtime tests/pre-PR validators/new security scan are skipped for this additive record.
