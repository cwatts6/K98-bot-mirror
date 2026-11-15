# B05 reconciliation — 2026-09-29

Operator report B05.rpt (41406 bytes) retained unchanged. Identity at09:08:33.1105224Z matches development9SX2VF4\K98DEV/master, MicrosoftAccount\cwattsconsulting@outlook.com, machine9SX2VF4, instanceK98DEV, engine16.0.1200.5 and sysadmin1. Completion09:08:54.2531993Z,21143ms, within approved window and total budget. All11 results,359665rows,118445202canonical bytes reconcile. No errors or warnings in supplied report.

All359 hash-range progress messages match exact disjoint1024-row ranges, in expected table/phase order. Object IDs and schema hashes match the sealed scope; counts meet caps, chunk counts equal ceiling(rows/4096), totals sum exactly. Empty Ingest_Negatives digest independently recomputed. Nonempty row hashes are operator SQL observations, not locally recomputed from private business rows. Per-phase timings/scratch/free-space peaks are not separately output; clean command completion supports passed cooperative guards, not independent resource telemetry.

| Table (KVK schema) | Exact rows | Reported table ms |
|---|---:|---:|
| KVK_AllPlayers_Stage | 52668 | 4978 |
| KVK_Camp_Windowed | 80 | 51 |
| KVK_CampMap | 128 | 22 |
| KVK_DKPWeights | 4 | 18 |
| KVK_Ingest_Diagnostics | 2 | 31 |
| KVK_Ingest_Negatives | 0 | 10 |
| KVK_Kingdom_Windowed | 920 | 73 |
| KVK_Player_Baseline | 33100 | 466 |
| KVK_Player_Windowed | 272474 | 15245 |
| KVK_Scan | 253 | 206 |
| KVK_Windows | 36 | 26 |

## Local command drift and recovery

At09:04:51Z immediately before operator execution instructions, every proposal-sealed file including B05.sql matched its approved hash. During receipt reconciliation B05.sql instead contained one newline byte, SHA25601ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b. Cause and timing relative to execution are unknown. Retained verbatim as retained-B05-current-drift-20260929.sql; original path not overwritten.

Reconstructed232624 approved bytes from unchanged B02.sql plus the exact recorded B05 generation transformations; saved separately as commands/B05-recovered-sealed-20260929.sql. SHA2566fa329a2f8f2931d0ac77545efefb26247bad8c4e10652a432815fde035801de matches approved proposal. Recovery is exact command preservation, not proof that those bytes were executed. Supplied output fully reconciles the approved scope/algorithm; executed-byte provenance stays qualified, as for B04R1. No rerun to repair this archival limitation.

## Consolidated baseline and remaining gates

The three separately completed B02 ProcConfig fingerprints (534rows), accepted B03+B04R1 raw-table coverage (2049960rows), and B05 eleven tables (359665rows) together capture the15-table historical baseline: **2410159rows**. See fifteen-table-baseline-reconciliation-20260929.json for all digest references/results. B02 later timeout and B04R1/B05 local script drift remain explicit qualifications. Raw table uses B04-keyset-v1; other14 use B02 framed multiset digest. Do not combine these as one database digest.

This completes the selected content-capture coverage, not the complete G4 preservation/receipt/fence proof or a fresh production comparison. Other352 catalog tables remain excluded from content scope. Recovered database was required to stay read-only/restricted/Broker-disabled. No new installation, backup/restore, production observation, rollout or G5 decision follows. All seven typed G4 proofs remain incomplete.

Operator should restore SSMS query timeout10seconds after control returns. No further live operation is requested by this receipt reconciliation. Next planning can use the consolidated baseline and retained restore/integrity results without rerunning them.
