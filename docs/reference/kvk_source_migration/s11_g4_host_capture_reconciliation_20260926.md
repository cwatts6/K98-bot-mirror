# S11/G4 initial host capture reconciliation — 2026-09-26

Additive outcome record for `S11-G4-CAPTURE-20260926-R1`. Preserve the sealed preparation
packet and all historical receipts unchanged. H00, its specifically proposed hash follow-up,
and H01–H05 now have operator-supplied output. Each H operation had its own approval; none
authorizes later capture, rollout, provisioning, startup or G5.

Evidence directory: `.codex_artifacts/s11-g4-capture-preparation-20260926/`.
`received-*.txt` preserves the pasted text using UTF-8/LF; dated reconciliation JSON records
its hash and limitations. Filename timestamps are local receipt-recording times, not fabricated
execution timestamps. H00 supplies 22:05:32.3325834Z; the later outputs do not separately supply
observation UTC, elapsed time or exit code. No error is shown, but no measured-duration pass is
claimed. The approved original window was 22:04:41–22:24:41 UTC. Do not run anything after its
expiry by inheriting that window.

## Results and remaining meaning

| Capture | Supplied result | Limit |
| --- | --- | --- |
| H00 / H00-HASH | MINI_AMD\cwatt; SID S-1-5-21-2970367362-111206357-3835881402-1001; PowerShell 5.1.26100.9549; `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`, 495616 bytes, SHA256 `60c9b29843624dd8af6b6a7b26147753be6aeef65098b9a503cc50850afe410f` | Observer/tool pin only; initial hash was absent from mixed table output, then supplied separately; not Bot token proof |
| H01 | All 12 exact paths returned; no reparse attribute shown. Eight Bot-root/venv/data/log/download/.env paths retain inherited Authenticated Users allow mask `0x1301bf` (Modify + Synchronize) | Known protected-path gap remains. No ACL correction or full effective-access/credential-custody proof |
| H02 | All ten files returned, 597524 input bytes. Nine hashes match retained pins, including three isolated-hotfix modules, watchdog/entrypoint, requirements, .env and venv metadata/executable | Base Python hash newly observed, not independently approved distribution identity. Sampled on-disk hashes do not prove loaded code, whole tree or installed dependencies |
| H03 | Parent chain `5848 → 16840 → 15364 → 17508 → 7020`; alternating venv/base Python paths | Parent5848, exact script roles, native FILETIME and token attributes remain unknown; no peer adoption |
| H04 | Seven named tasks, one action/trigger each, all IgnoreNew; Restart daily has RestartCount3 / PT5M. RUN_Bot and K98 SQL Schema Export task states Disabled; their trigger Enabled values True | Arguments withheld, weekly day masks/intervals and other settings missing. Ready is not running; names/start boundaries are not complete schedule/effects evidence |
| H05 | C: NTFS; total510015827968 bytes; free223853539328 bytes (208.48 GiB) | Point-in-time capacity, not storage reservation, complete SQL file exclusions or restore sufficiency |

PID7020 matches the hotfix log's numeric PID. H03 identifies its executable as
`C:\Program Files\Python311\python.exe`; the earlier log reported the venv executable. These are
different evidence fields/sources. Do not assert a restart, extra Bot instance, confirmed script
role or authenticated continuity from them. H03 CreationDate strings lack timezone offsets and
native precision; preserve them without converting them to UTC or FILETIME.

The .env hash remains `0218bd3ef2eb1dc1cc3763235f2bd52b42e9a6fbb9eca17ef2d0133c0df62a9e`.
Its contents were not supplied or inspected. Intended KVK_DATA_CHANNEL installation stays unknown.
Base Python's newly observed SHA256 is
`5f7b89a612c9b8af1d6456cdfcd1dbe5ca630849e79aebced9bee9a6694952ec`.

## Startup identity settled; source effects reviewed locally

Operator confirms `\StartDLBotAfterSQL` is the normal manual restart/startup task, with action:

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\discord_file_downloader\start-bot-after-sql.ps1"
```

This is an action receipt, **not an instruction to execute it**. Do not ask for the task name again.
H04 confirms a Limited cwatt principal and logon trigger. Source exists in local checkout and
isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`; the local CRLF bytes equal its Git
content after line-ending normalization. Source-only hashes:

- Git LF: `4fea1b4c1e7538ed8208925a47baa0bc120b7894eb9d927b5ffbbb6bbe3a67d9`.
- CRLF: `201b4f02e27890af0963422871549249fb36c0bfc0143e208822f4a1522c9b48`.

The reviewed source appends `logs\start-bot-wrapper.log` (creating its directory if absent), waits
for MSSQLSERVER and localhost TCP1433, makes DNS checks for discord.com and sheets.googleapis.com,
and optionally runs two Windows-auth SQL health metadata queries via sqlcmd on PATH. Each service/
TCP loop has a 300-second deadline and five-second polling; synchronous calls, DNS and the SQL
commands lack an equivalent enforced overall deadline. SQL commands do not specify `-d`, `-l` or
`-t`; unexpected health-check failures warn and allow startup to continue. No live query result or
health guarantee is inferred from that source. The script then starts venv Python with `run_bot.py`
in the Bot root, records a PID and exits. It does not explicitly stop an existing Bot or establish
the future S11 supervisor/process-binding/admission lifecycle. No script or configuration changed.

## Next narrow proposal: H06, not approved

Purpose: bind the newly identified production startup script to reviewed source without executing
or printing it. Exact command is in `commands/H06.txt`, SHA256
`0ef3848dfe9645e5a7d0aa6928cba33a7d546dadecc777d10128f4f185077bf3`.
Target: MINI_AMD, only `C:\discord_file_downloader\start-bot-after-sql.ps1`; same observer and
pinned Windows PowerShell. Reads leaf attributes, owner/SDDL, size and SHA256; no script invocation,
SQL/DNS/provider/Discord calls, task control or file/permission change. CPU/I/O/audit effects remain.

Budget: one attempt, ten-second operator cutoff, one MiB maximum input, eight KiB maximum output,
4096-character SDDL cap. Reject reparse/missing/oversized file, error or size/mtime drift; stop on
time/output limit and preserve partial output, no retry. H01 sampled parent metadata is retained,
not a race-free protected-path certification. Compare LF/CRLF domains explicitly; an unexpected
hash is a reconciliation stop, never permission to normalize/edit the production file.

Approval must name H06 and its command hash, Chris as operator/reviewer/abort owner, a new exact
20-minute UTC window if the old window expired, and a new development receipt filename. No H06
execution follows from H05 approval or from supplying the startup action. This extension has
local parse-only validation; it is not a replacement collector or live-tested helper.

## Outstanding gates and preserved boundaries

All seven typed v2 G4 proofs and actual restore remain incomplete. Remaining capture work:
native process/token/retained-handle bindings; final full source/config/interpreter/dependency map;
protected manifest/key/spool/origin/journal path ACLs; remaining task/service/manual writer effects;
nonsecret fresh identity/issuer/key-custody metadata; exact provider exclusions/access/enrollment
receipts; installed SQL shapes/signatures/grants and restricted effective capabilities; complete
development DB/physical-file exclusions, backup chain/retention/readability and restore budget.
SQL/provider groups remain held until exact client/identity/target bindings are approved. No task,
SQL job, service, provider permission, key, database or file has been changed by these captures.

Preserve one Windows account, admin-owned review/startup, fresh generated link/equivalent reports,
and the confirmed historical Editor `sheets-service@statsupdate.iam.gserviceaccount.com`.
Fresh S11 issuance is still separate; never request private key/token bytes.

Production remains the isolated hotfix by retained operator deployment evidence, not current
production/main. Successful startup, 409-row upload and14 Sheets exports are retained logged
outcomes, not rollout approval. No successful upload replay, memory-cause investigation or collector
rerun. Empty KVK reporting and view-rehydration warning stay separate. Original pending/recovered
files and historical seals stay untouched; no PR, Git publication, cleanup or new chat.

Retain all S6 open gates, both uncertain publication IDs, S8A/B/C distinctions and N/C/T/S/L/Q/P/R/D
cases. No change to owner/fence/version CAS, pending-only coalescing, daily fairness, provenance,
P/Q/R, 9,000,000-cell parts or8/16 bounds. Inventory is not drain, termination or no-delayed-effects
proof. Controlled rollout, actual restore and G5 still require separate exact operator decisions.

Validation: local evidence transcription/parse/hash/source comparisons only; no runtime tests,
predecessor runs, SQL/provider/Discord calls or new security scan. Documentation-only routing skip
is limited to this additive record; earlier code scans retain their exact historical scope.
