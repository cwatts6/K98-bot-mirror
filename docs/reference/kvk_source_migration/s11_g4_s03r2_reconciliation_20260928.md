# S03R2 receipt — SQL Agent metadata

Bounded observation COMPLETE. Operator supplied four expected result sets: identity, seven job/step rows across five jobs, six schedule attachments and completion. Both inventories are below their 65-row sentinel. Every present command has a 64-hex SHA256 and size below 1 MiB (range 236–1,084 bytes); no error supplied.

Raw attachment retained byte-for-byte at `.codex_artifacts/s11-g4-capture-preparation-20260926/received-S03R2-20260928T084728Z.txt` (9,907 bytes, below 128 KiB). Receipt recorded 2026-09-28T08:47:28Z. Server observed 08:47:11.6734247Z, completed 08:47:11.6791861Z, client completion 09:47:11.7377914+01:00 = 08:47:11.7377914Z, inside approval 08:43:37–09:03:37 UTC. Batch-start/stopwatch duration not supplied; result times do not establish full duration or timeout compliance.

Accepted mini_AMD / ROK_TRACKER / MicrosoftAccount\cwattsconsulting@outlook.com context matches, VIEW DEFINITION and database CONTROL both 1. Completion is consistent with the approved sysadmin observer gate passing; no raw role-check value emitted. Operator output is not independent attestation of executed bytes or connection continuity.

## Job and schedule facts

All five jobs and all six attached schedules report enabled=1. IDs, exact numeric fields and command hashes remain in the raw receipt.

| Job name | Steps | Subsystems | Attached schedule names (IDs) |
| --- | --- | --- | --- |
| ROK_TRACKER - Backup Prune | 1 | PowerShell; database_name NULL | Daily 02:00 (18) |
| ROK_TRACKER - DIFF Backup | 1 | TSQL; master | ROK_TRACKER DIFF daily 18:00 (17) |
| ROK_TRACKER - FULL Backup | 1 | TSQL; master | ROK_TRACKER FULL daily 01:00 (15) |
| ROK_TRACKER - LOG Backup | 1 | TSQL; master | ROK_TRACKER LOG q15 (16); ROK_TRACKER_LOG_q5 (19) |
| syspolicy_purge_history | 3 | TSQL, TSQL, PowerShell; master | syspolicy_purge_history_schedule (8) |

The two LOG schedules are separate enabled attachments on the same job. Preserve both; do not disable either or call the duplication erroneous from metadata alone. Schedule names are labels, not execution records or UTC timestamps. The receipt also retains recurrence/start/end numeric fields for later source-grounded interpretation. No next-run time, timezone, job history or successful execution was observed.

Hashes identify installed UTF-16 command bytes only. No command body was returned, so job names alone do not establish backup/prune paths, deletion rules, alert/network behavior, execution identity, proxy rights, dependent scripts or actual scope. Job/step counts do not establish successful effects or writer exclusion. No backup, prune, job start/stop or history purge was executed by this capture.

## Next local preparation

Compare the seven exact command hashes against already retained command/source evidence first, respecting UTF-16 encoding and line endings; do not emit retained secrets or use broad command dumps. Record unmatched bytes/effects as unresolved. If a missing nonsecret behavior needs a live observation, prepare an exact narrow operation after source review. Keep chain/media/storage and job execution context/history separate; no backup/restore or job control follows from this receipt.

Session metadata, task metadata and Agent metadata remain independent point-in-time inventories. They do not prove closed admission, owned drain, old-writer termination or absence of delayed effects. All seven typed G4 proofs and actual restore remain incomplete; rollout/G5 remain unapproved.

Preserve pending/recovered files, isolated hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues. No further live observation is authorized.

Validation: local counts, distinct job IDs, hash syntax and command-size limits, exact attachment copy, approval/proposal seals, original 27 pending/394 evidence hash preservation. Documentation/evidence-only; runtime/predecessor tests, pre-PR validators and security discovery skipped as inapplicable. No live call or runtime mutation by the assistant.
