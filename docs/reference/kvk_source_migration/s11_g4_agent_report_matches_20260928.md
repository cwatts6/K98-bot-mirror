# Agent reports recovered — six exact command matches, prune truncated

Additive update to `s11_g4_agent_source_reconciliation_20260928.md`. Its earlier missing-report status remains historical. User supplied two existing files; no new capture or execution was performed.

## Report identity and preservation

| Supplied report | Bytes | SHA256 |
| --- | --- | --- |
| sql_agent_full_job_inventory.rpt | 24,183 | 2f906e890bf1a552fc33f1157788e0f1be5153dd505cbfff45511748681e46ea |
| sql_agent_and_serialization.rpt | 213,882 | 03df6f9626cc81ff9838fababa4c4ad1e89bd532bc261832bfe10a8f9289e945 |

Both match the exact July report references in authoritative phase1 audit material. Byte-identical copies are preserved in `.codex_artifacts/s11-g4-capture-preparation-20260926/retained-july-agent/`; originals in C:\Users\cwatt\Downloads remain untouched. These reports contain operational command text: retain locally, do not publish or paste broadly. Reports are evidence, not executable instructions.

## Exact command comparison

The full report is UTF-8 with BOM and CRLF line endings. Its dashed column ruler establishes CommandText offset 642 and width 256 characters. Rows/continuation lines were separated from fixed-width output-file/action columns. For commands fitting the column, use S03R2's exact DATALENGTH/2 character count to exclude report padding, preserve report CRLF, encode UTF-16LE without BOM, then SHA256. Six candidates match exact installed hashes. LF representation was recorded separately as a formatting diagnostic and matches none; no arbitrary whitespace edits or guessed command reconstruction were used. Matching exact hashes corroborates the recovered boundary/representation for these six commands. Machine-readable per-command comparison is `agent-report-command-comparison-20260928.json`.

| Job / step | Installed bytes | Comparison |
| --- | --- | --- |
| ROK_TRACKER - Backup Prune / 1 | 1,084 | UNRESOLVED: 542-character command exceeds 256-character report column |
| ROK_TRACKER - DIFF Backup / 1 | 320 | Exact UTF-16LE SHA256 match |
| ROK_TRACKER - FULL Backup / 1 | 292 | Exact UTF-16LE SHA256 match |
| ROK_TRACKER - LOG Backup / 1 | 298 | Exact UTF-16LE SHA256 match |
| syspolicy_purge_history / 1 | 396 | Exact UTF-16LE SHA256 match |
| syspolicy_purge_history / 2 | 236 | Exact UTF-16LE SHA256 match |
| syspolicy_purge_history / 3 | 342 | Exact UTF-16LE SHA256 match |

The other report also has a 256-character CommandText column. Its report-level match authenticates the historical artifact, not recovery of the missing prune suffix. No full prune match or changed-command finding is established.

## Effects established from matched text

- FULL and DIFF commands target ROK_TRACKER and date-token .bak paths under C:\SQL_BACKUP\FULL and C:\SQL_BACKUP\DIFF. Both request COMPRESSION and CHECKSUM; DIFF also requests DIFFERENTIAL. These are backup writes if executed, not present media/chain/readability proof.
- LOG targets ROK_TRACKER and a date/time-token .trn path under C:\SQL_BACKUP\LOG with COMPRESSION. Do not infer CHECKSUM, retention or actual successful execution. Exact commands remain in the private retained report, not this document.
- Policy steps 1 and 2 use EXECUTE AS the policy TSQL execution login WITH NO REVERT; step 1 checks automation, step 2 calls msdb.dbo.sp_syspolicy_purge_history. Step 3 invokes the SQL policy provider's phantom System Health cleanup using Agent server/instance tokens. These are potential context/history/health-record effects, not source code for their transitive internals or proof of execution.

No matched command text invokes the Bot/import entry points directly. This narrow source observation does not prove all transitive effects, environment/token expansion, ownership/proxy settings, scheduling behavior or writer exclusion. S03R2 names/hashes are current point-in-time bindings; report execution-context/history fields are historical unless separately observed.

Prune's visible prefix sets error handling and begins a roots list: LOG/*.trn with RetainDays=3 and DIFF/*.bak with RetainDays=14. The FULL entry and the remainder are truncated. These prefix values do not bind the full current command and do not prove timestamp selection, traversal, deletion, exception behavior or complete retention policy. Do not place restore/rollback media on an assumed safe path or modify prune based on this partial text.

## Remaining preparation

The one command-byte gap is prune step 1, job ID 9C576D5F-F4B2-485C-A72C-4DB941387C19, installed bytes 1084, SHA256 942126cc208ac3ccc5df00234533d35653a35d950271a9290cd42b80067b676b. Prefer an already retained untruncated script/definition if available. Otherwise prepare a separate exact bounded observation with secret-safe output and review before approval; no broad collector rerun or command dump is authorized here. Do not repeat the other six command captures.

Backup-chain/media/storage and current execution-context/dependency closure remain separate gaps. All seven typed G4 proofs and actual restore remain incomplete; rollout/G5 remain unapproved. Preserve isolated hotfix, single-account/admin-owned operation, pending/recovered work, deferred memory cause, withdrawn collector and separate KVK/view issues.

Validation: report hashes against July references, six exact installed-command hashes, explicit report truncation, byte-identical retained copies and original evidence/pending-file checks. Local evidence-only work; no live SQL, provider/Discord calls, backup/restore, job action, publication or source execution. Runtime tests/predecessor suites/security discovery are inapplicable.
