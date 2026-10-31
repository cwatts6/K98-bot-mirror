# Agent command source reconciliation — local evidence only

Outcome: seven installed command hashes retained; zero exact command-byte matches established. This is missing comparison material, not seven detected mismatches or missing source implementation. No live call, command dump, collector rerun, job control or source execution occurred.

## Evidence searched and retained

- S03R2 raw receipt and seal: five jobs/seven command hashes, installed UTF-16 sizes 236–1,084 bytes. All exact hashes remain in `received-S03R2-20260928T084728Z.txt`.
- September observation report and production metadata/bindings reports in `.codex_artifacts/s11-g4-observations-20260925`. The report expressly says command bodies and complete effects were deliberately not collected.
- Authoritative SQL repository deploy/migration/source paths and `performance_remediation/kingdomscandata4/phase1` audit/closure material. Searches found metadata collector definitions, not matching installed Agent command bodies. Backup rehearsal/preflight scripts and nightly schema-export retention source are different operations and are not substitutes for backup/prune job commands.
- The July audit identifies operator-held Agent reports. An ignored/hidden-inclusive filename search of its phase1 subtree found no corresponding Agent report files. This is a bounded search result, not proof that copies exist nowhere on disk.

Historical references in `C:\K98-bot-SQL-Server\performance_remediation\kingdomscandata4\phase1\audit_report.md`:

| Historical receipt | Report SHA256 |
| --- | --- |
| SQL Agent report, 2026-07-25 | 03DF6F9626CC81FF9838FABABA4C4AD1E89BD532BC261832BFE10A8F9289E945 |
| Full Agent inventory supplement, revision 20260725.1 | 2F906E890BF1A552FC33F1157788E0F1BE5153DD505CBFFF45511748681E46EA |

`06_collect_sql_agent_full_job_inventory.sql` documents that its output includes full step commands and can contain sensitive operational configuration. It was read as source only, never run. Finding that collector is not finding its output and creates no approval to rerun it. Do not request raw command text or credentials in chat.

## What the historical narrative establishes

The July audit describes four backup/prune jobs with no observed UPDATE_ALL2/import/Python/downloader references then. It describes syspolicy's three steps as automation verification, `msdb.dbo.sp_syspolicy_purge_history`, and phantom System Health cleanup. It records historical owners and successful historical outcomes.

These are dated narrative assertions backed by references to operator-held reports, not an exact binding to S03R2's installed command hashes. Do not promote the historical 'Agent does not schedule this import' conclusion into current exhaustive writer exclusion. Current names/step counts resembling history do not prove equal command bodies, context or dependencies.

| Current job | Current steps | Exact byte comparison | Remaining current-effects gap |
| --- | --- | --- | --- |
| ROK_TRACKER - Backup Prune | 1 | Unmatched: comparison bytes unavailable | Exact paths, selection/retention/deletion rules, dependencies, execution context |
| ROK_TRACKER - DIFF Backup | 1 | Unmatched: comparison bytes unavailable | Exact command/options/destinations and dependency/context |
| ROK_TRACKER - FULL Backup | 1 | Unmatched: comparison bytes unavailable | Exact command/options/destinations and dependency/context |
| ROK_TRACKER - LOG Backup | 1 | Unmatched: comparison bytes unavailable | Exact command/options/destinations and dependency/context; retain both enabled schedules |
| syspolicy_purge_history | 3 | Unmatched: comparison bytes unavailable | Bind historical description to exact current commands; context/dependencies remain separate |

No candidate bytes were available for a legitimate UTF-16 command comparison. Do not hash an entire .sql file and compare it to one installed command, synthesize likely commands, or trim/normalize whitespace until a hash happens to match. On receipt of an existing report, verify its report hash first, parse actual command boundaries and completeness, then compare exact unmodified UTF-16 command bytes with explicit encoding/newline limitations. Report-level hash is not a command-level hash. Do not print sensitive command content.

## Next missing nonsecret fact

Request only the already-known local path to the operator-held July full Agent inventory supplement (or existing saved command-definition evidence), if available. Unknown is acceptable. No new live capture or filesystem search on the Bot host is requested. If unavailable, retain all seven comparisons unresolved and prepare a separate narrowly scoped redacted observation only when needed; do not execute the broad historical collector.

Backup-chain/media readability, prune exclusions, isolated restore storage and actual restore remain separate. Do not reserve or restore to a path whose prune exposure is unknown. No new restore or provisioning authority follows.

All seven typed G4 proofs and actual restore remain incomplete; rollout/G5 remain unapproved. Preserve pending/recovered files, isolated hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues.

Validation: local read-only source/evidence searches and historical-report interpretation. Original 27 pending and 394 evidence files remain hash-unchanged. Documentation-only security-routing skip; runtime/predecessor tests, PR validators and security discovery inapplicable. No production or external action.
