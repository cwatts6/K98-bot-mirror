# P01.5 PR review and deployment plan

**E98, 5 November 2026.** The operator authorized publication, review fixes, replies,
resolution and merge, and explicitly approved publication to the public mirror.
Deployment and live acceptance remain operator actions. Earlier approval-pending
statements are historical. Mirror review: [PR 489](https://github.com/cwatts6/K98-bot-mirror/pull/489).
The final handoff binds this plan to the merged private commit and packaged updater hashes.

## Scope and outcome

P01.5 addresses F23/F24/F25: optional EventSyncLog cannot gate calendar business work;
physical SQL/file work keeps one owner after cancellation or an observer deadline;
acknowledged generation/publication survives optional audit, index or presentation failure.
It covers startup, daily scheduling, direct service calls and existing admin commands.
There is one active mutation and at most one deferred scheduled intent. A direct request
while busy is refused without acquiring the active run's delivery identity.

This uses the P01.1/P01.2a evidence contract and recovery ZIP, P01.3 passive health,
P01.4 optional-work isolation, existing owned-work helpers and atomic JSON replacement.
It preserves the existing permissions, SQL schema, cache format, instance identity and
updater history. The auxiliary type index remains compatible. The operator reported no
known external consumers; the two files are not promised as an atomic pair.

The changes prevent the identified recurrence mechanisms: optional SQL contention cannot
hold the business transaction; timeouts do not admit overlapping physical work; lost commit
acknowledgement stays unknown; cleanup uncertainty retains custody; a failed index cannot
turn a confirmed primary publication into an apparent total failure that invites replay.
These are process-local guarantees, not distributed ownership or cross-restart exactly-once execution.

## Review dispositions

- Restore `refreshed_utc`, `generated_utc` and `published_utc` in standalone results using
  the existing run-start timestamp contract. Regression coverage exercises all three stages.
- Accept missing, empty or non-string optional terminal status as `outcome_unknown`;
  never invent success. The original error was already caught by the independent audit
  boundary, but normalization avoids losing the audit completion unnecessarily.
- Remove the command-contract test's dependency on a mirror-only Git SHA and working
  directory. Assert the authorization and option contract directly from a file-relative source path.
- Default unentered write counts to unavailable. Assign zero explicitly after confirmed
  rollback or empty-publication preservation; retain acknowledged positive counts and unknown commits.
- Retain the designed shutdown refusal when calendar cleanup is unconfirmed. It deliberately
  stops before shared client/executor destruction; continuing teardown is not proof that the
  retained native connection settled. Calendar and upload admissions close before the first await.
  Do not retry shutdown or restart merely because an observer timed out.

Review corrections refresh only the unpublished P01.5 updater successor. All 64 historical
transition records remain unchanged. Final PR checks, security Changes-review identities,
full regression results and exact private target are retained in the release handoff.

## Deployment prerequisites

1. Use the final reviewed release folder, whose name and hash manifest identify the private
   merge commit. Keep `Upgrade-K98InstalledUpdater.ps1` and `Install-K98UpdateTool.ps1` together.
2. The retained predecessor is private `e3508d122c384bfc750b0e80231554d0d93d8d75`
   (P01.4). Its installed-tool manifest SHA-256 is
   `10b9d0d5df6fc2a40ed84d633827e8826c474cdb0f559a8c05ecbd6934ba1d57`.
   This is prior deployment evidence, not a fresh machine inventory. The authenticated upgrade
   must verify the actual installation and refuse drift. If it differs, stop and review the actual state.
3. No SQL schema deployment, dependency installation, configuration edit or manual data repair
   is required. SQL source definitions were checked against `b1eeb8e894fec380c7a6d6c5cc5bbfd9dbc3470c`.
4. Use the reviewed deployment account on MINI_AMD and elevated **Windows PowerShell 5.1**.
   Keep the existing updater receipts and current recovery evidence. Do not deploy from the mirror.

## Operator sequence

From the transferred final release folder, compare the installer and upgrade script SHA-256
values with the final handoff. Then run:

```powershell
.\Upgrade-K98InstalledUpdater.ps1
& 'C:\ProgramData\K98\S11\updater\Update-K98.ps1' -PrepareOnly
```

The first command upgrades the installed updater through its authenticated predecessor contract.
It is not the initial-install path. The second prepares and validates the source update.
Confirm the prepared private-main target is the exact merge commit in the handoff, the source
compatibility decision accepts the fixed P01.5 family, and the preparation receipt reports success.
If private main has advanced, stop and review that additional delta before deploying it.

Run the normal protected update:

```powershell
& 'C:\ProgramData\K98\S11\updater\Update-K98.ps1'
```

Follow the runner's prompt for one `/ops graceful_restart`. Let it own drain, source replacement,
startup seed and verification. Do not substitute a live Git pull, manual scheduled-task start,
second restart, forced lock release or replay of an earlier update package.

## Validation and acceptance

| Check | Expected evidence | Stop or investigate |
| --- | --- | --- |
| Protected update | Exact private source commit, successful source/startup verification and retained update receipt | Wrong target, incomplete phase, admission refusal or failed startup verification |
| Existing commands | `/ops show_command_versions` and passive `/ops calendar_status` render normally | Missing commands, import errors or status exceptions |
| Calendar business | Natural startup/daily refresh or one operator-intended refresh records sync, generation and primary publication independently | Unknown commit, overlapping ownership, missing terminal evidence or cleanup unconfirmed |
| Cache | Primary count and generation agree with the acknowledged publication; index status is separately visible | Primary success erased by an index warning, or old/unknown index represented as fresh |
| Optional audit | Existing EventSyncLog completion binds to its acknowledged start ID; audit warning is separate from business success | Audit gates work, rebounds to another ID, retries or overwrites business outcome |
| Delivery | Discord response/pinned-calendar delivery has its own outcome | Delivery failure causes business resubmission |
| Evidence | Retain complete recovery ZIP and updater receipts; compare business, cleanup, audit and delivery facts | A status colour alone is used as proof of completion |

Source/startup verification is not fresh feature acceptance. Do not manufacture provider failures,
contention, cancellation or concurrent admin requests in production. Use legitimate/natural activity
and record what was actually exercised. Native local SQL qualification does not establish the
deployed SQL login's grants. Optional audit warnings can coexist with confirmed business success;
unconfirmed cleanup must remain blocked, even if the command appeared successful.

## Interruption, rollback and remaining delivery

On interruption, retain the phase receipt and evidence, establish which stages committed, and use
the supported recovery path for that phase. Never delete control files, force release on age,
blindly replay business work or infer completion from reservation release. Source rollback needs
a separately reviewed private target and authenticated reverse transition after work is settled;
the forward-only package does not authorize a manual downgrade.

P01.4 natural acceptance remains tracked separately. P01.6 and P02-P05 remain open, including
shared SQL connection policy (F26), snapshot contention, file-sharing behavior (F20), retained
pipeline continuation and incident-specific recovery. Keep the same outcome/cleanup/evidence
contract across those phases, reuse the existing test and native qualification harnesses, and
evaluate real latency/locking cost before adding observers. Do not introduce a generic executor,
retry framework or new persistent coordination layer without a demonstrated need and scope review.

For each remaining phase, freeze the runtime candidate before full regression and exact updater
packaging; inspect related callers and shutdown/recovery boundaries; preserve adverse runs; and
separate local qualification, PR approval, source deployment and natural acceptance in the tracker.

See the [design](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Whole%20Solution%20Design%20-%202026-11-05.md)
and [local qualification](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Local%20Implementation%20and%20Qualification%20-%202026-11-05.md)
for native fixtures, fixed cost gates, adverse evidence and residual limits.
