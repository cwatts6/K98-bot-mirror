# Supplied retention scripts — distinct from Agent Backup Prune

Operator supplied the only two prune-related script files they know. Record that answer; do not repeat the request for another known saved script as a prerequisite. Both were read only, never dot-sourced or executed.

| Supplied file | Bytes | SHA256 | Retained comparison |
| --- | --- | --- | --- |
| Invoke-NightlyProdSchemaExport.ps1 | 9328 | 832a7c67021d655bd4eb1d2011b6f5f372d1c56b17622033eb884e8e05d159cd | Exact H12 wrapper match |
| NightlyExportRetention.ps1 | 6898 | ce366a276b54c183af9cfdb2b5f9c927c3fd34e865ea59064efc27bfb0dcb11d | Exact H12 retention helper match |

Originals remain in C:\Users\cwatt\Downloads; byte-identical copies retained in `.codex_artifacts/s11-g4-capture-preparation-20260926/supplied-nightly-retention/`.

The wrapper belongs to the Windows scheduled task K98 SQL Nightly Schema Export already bound by H11/H12. It invokes the schema snapshot helper and branch-retention processing. Its source can fetch/prune Git refs, switch/pull SQL repository main, export schema, publish through helpers and send failure alerts. None of those operations were performed here.

NightlyExportRetention selects timestamp-named remote branches under an approved export/ prefix, sorts newest first, keeps RetainCount and deletes older remote branches with git push origin --delete, then logs results. Its fetch --prune concerns remote-tracking references. This is schema-export Git branch retention, not the visible SQL Agent backup-file roots list.

Neither supplied file contains the SQL Agent Backup Prune command captured partially in the July report. That Agent step is a separate 1,084-byte installed command with hash 942126cc208ac3ccc5df00234533d35653a35d950271a9290cd42b80067b676b; its visible prefix addresses C:\SQL_BACKUP\LOG/DIFF/FULL file retention, while the report truncates it at 256 characters. The supplied scripts do not close its missing command/deletion-policy evidence. No unsupported claim that they cannot be transitive dependencies is made without the full Agent command, but their bytes and purpose do not substitute for it.

Six other Agent commands remain exactly matched as recorded in `s11_g4_agent_report_matches_20260928.md`. Do not recapture them or rerun either supplied script. No more known untruncated prune source is available from the operator at this point. Next preparation, if required, is a separately approved narrowly scoped observation for that exact Agent job/step/hash with secret-safe output; no broad collector or live action is authorized now.

All seven typed G4 proofs and actual restore remain incomplete; no rollout/G5, backup/restore, job control, deployment or publication approval. Preserve all pending/recovered evidence, single-account/admin-owned model, isolated hotfix, deferred memory cause, withdrawn collector and separate KVK/view issues.

Validation: supplied file SHA256/length against H12, static source reading and byte-identical local copies. Evidence/documentation only; no runtime tests or security discovery warranted.
