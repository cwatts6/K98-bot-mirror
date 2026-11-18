# P0 startup authority diagnostic capture

## Scope and evidence boundary

The previous startup completed with Discord online, but configuration publication
failed inside the authority. The first provider read had durable success; the next
request only had preparation evidence. The original authority exception was sent
to stderr, which the native hidden process does not inherit. Its underlying cause
cannot be established from the retained bot-side uncertainty message alone.

The separate event-cache timeout follows successful reads with no upcoming events:
readiness requires a nonempty upcoming-event list. That scheduler limitation does
not establish a provider failure and does not drive stats import/export. A pipeline
mutex refusal later cleared; it is not proof of the historical authority failure's
cause. Keep these observations separate until a correlated capture proves a link.

This release adds bounded diagnostic observations only. It does not change admission,
SQL, provider retries, request ordering, recovery decisions, imports, reporting
receipts or output URLs. No historical work is replayed. No SQL migration is needed.

## Capture contract

After the authority validates its protected manifest and evidence directory, it
writes `authority-diagnostics.jsonl` there, with two rotations of at most 256 KiB
each. Records contain UTC time, process/request identifiers, allowlisted stages,
exception types, SQLSTATE/native codes and bounded source basenames/functions/lines.
They exclude exception prose, credentials, raw SQL, payloads, locals and full paths.
The existing private timing-file custody checks also protect these files.

Capture includes request checkpoints, dispatch/connection failures and process
exceptions. Successful requests have a completion observation. Configuration-level
success must still come from its own receipts. Failures before a protected manifest
is accepted cannot safely use this file sink. Missing markers, rotated records and
logging failures never establish success. Diagnostics are not durable receipts and
cannot authorize recovery, release reservations or enable replay.

`Read-K98AuthorityDiagnostics.ps1` uses the protected task, policy, incarnation and
manifest bindings. It reads only bounded local files, restricts records to that
authority PID and creation time, and filters malformed/private fields. The report
contains operational identifiers and belongs in private support evidence.

## Operator validation after reviewed deployment

1. Deploy the reviewed private production release using its matching updater package.
   Use the single protected graceful restart requested by that updater. Do not add
   an extra restart, run scan 1231 again or repeat its completed reporting stages.
2. Leave normal import/export idle while startup settles, including the existing
   five-minute event-cache wait. Retain startup logs and the recovery report.
3. In elevated Windows PowerShell on MINI_AMD, collect the pinned authority evidence:

   ```powershell
   $ErrorActionPreference = 'Stop'
   & 'C:\discord_file_downloader\scripts\Read-K98AuthorityDiagnostics.ps1' |
       Set-Content -LiteralPath "$env:USERPROFILE\Downloads\K98-authority-diagnostics.json" -Encoding UTF8
   ```

4. Review capture-ready/serving markers and the first failing checkpoint together
   with configuration outcome receipts and the bot startup log. An isolated clean
   restart is evidence of that run only; it does not prove the earlier problem was
   transient or identify its cause. If it recurs, classify the captured error before
   choosing a corrective change.
5. Permit the next genuine normal import/export only after configuration publication
   and admission are verified healthy for that run, no unresolved writer/blocker is
   present, and captured failures are explained. Verify the new scan's import and
   report receipts and delivery to all eleven existing URLs separately. This is the
   remaining production acceptance, not something proved by deployment or diagnostics.

## Validation and review

Use the diagnostic and authority regression suites, strict collector fixtures under
Windows PowerShell 5.1, updater transition/compatibility tests and an isolated
protected updater rehearsal. Verify exact predecessor/target images and retain old
updater evidence. Review both mirror and private production diffs with Changes
security scans; Deep scan is off. Merge, deployment and production acceptance remain
separate operator decisions. No credential/configuration rotation is included.

### Deferred Optimisation
- Area: core/event_rehydration_lifecycle.py; core/scheduler_lifecycle.py
- Type: consistency
- Description: Successful event reads with zero upcoming events do not satisfy readiness; the five-minute startup waiter returns before a later refresh can start dependent tasks.
- Suggested Fix: In the P1 programme, distinguish successful empty cache from uninitialised cache and test a single supervised late-start path.
- Impact: medium
- Risk: medium
- Dependencies: Event lifecycle review and scheduler-specific acceptance; independent of stats export diagnostics.
