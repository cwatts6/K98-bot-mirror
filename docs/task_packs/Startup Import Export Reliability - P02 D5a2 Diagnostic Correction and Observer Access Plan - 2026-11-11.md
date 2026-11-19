# P02 D5a.2 diagnostic correction and observer-access plan — 2026-11-11

Status: **local correction and observer-access source review only; no new native
attempt or permission change**. The proposed next action is one access-only
diagnostic, subject to the operator's review of this plan. It does not authorize
the full inventory, installation, replay, rehearsal or later D5/D6 work.

## Finding and correction

The executed collector used
`HAS_PERMS_BY_NAME(NULL,'SERVER','VIEW SERVER PERFORMANCE STATE')` in both work
and observer checks. The server-level form requires **NULL for both securable
arguments**. Microsoft documents that an invalid class/permission can return
NULL, distinct from a denied permission's zero. The original receipt omitted
the raw value, so the defective query is a confirmed source error and a plausible
explanation of the stop, not proof of the exact value returned in that attempt.
It does **not establish that a grant is needed**.

Sources: [HAS_PERMS_BY_NAME](https://learn.microsoft.com/en-us/sql/t-sql/functions/has-perms-by-name-transact-sql?view=sql-server-ver17)
and [sys.dm_exec_sessions permissions](https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-objects/sys-dm-exec-sessions-transact-sql?view=sql-server-ver16).
The authoritative SQL repository also uses `NULL,NULL` for server permission
checks in `deploy/SqlDeploy.ModuleRelease.ps1:113`; its
`deploy/recovery/Observe-CheckpointBlocking.sql:2` identifies the SQL 2022
performance-state permission. These files were read as source, never executed.

The collector now:

- Uses the corrected check through one helper for both connections.
- Retains each connection's own session ID/login time, server/version, effective
  and original SQL login, and raw permission value **before** deciding whether
  it may proceed. NULL, zero, one and unexpected values remain distinct.
- Requires the pinned `MINI_AMD` / `16.0.1210.3` server and permission value one.
  There is no older-version permission fallback or alternate identity.
- Retains work/closure failure stages and bounded details, displays nested guest
  errors in the host summary, and distinguishes local disposal from server absence.
- Adds `AccessReviewOnly`, propagated through the owned worker into the guest.
  In that mode neither retained-file traversal/hashing nor target-database
  identity, modules, ledgers, receipts or resource queries execute.

## Evidence custody

The original failed receipt remains unchanged:
`.codex_artifacts/p025/d5a2-inventory-result-6ac0bdc278b94ce6a812c6d2a6a0a726.json`.
SHA-256: `de124a7df3233d3ef56f73b98cb74b00070aad9a122a7003cc3a978e55a55e34`.

Before editing, the executed collector, offline test, manifest and failed receipt
were copied byte-for-byte into `.codex_artifacts/p025/d5a2-diagnostic-correction/`.
`preservation.json` binds originals and copies to their execution hashes. The
earlier findings and adjudication remain historical records, not rewritten as
successful results. This document corrects their unresolved visibility diagnosis.

The prior input custody result remains 21 matching files / 1,638,735 bytes,
one ready, zero claimed, 20 archived. It proves custody at that observation,
not fresh runnable work or present database readiness. The **consumed 21-input
allowance remains consumed**. Original CI/local drain failures and SQL 3961
history are preserved; the earlier runtime correction is unchanged.

## Observer-access review

Use the **existing authenticated identity only**, through the same operator-owned
PowerShell Direct session. The operator previously entered `.\K98LabAdmin`
locally; this Windows account name does not itself prove SQL effective rights.
The new receipt will record the actual effective/original SQL login without
requesting or recording a password. No login, role, ownership or grant will change.

SQL Server permits a caller to inspect its own session. On the pinned SQL 2022
instance, seeing other sessions requires `VIEW SERVER PERFORMANCE STATE`.
Therefore the observer must establish that permission before treating the
absence of the prior work-session tuple as evidence. Merely receiving no rows
under restricted visibility is insufficient.

No separate approved observer account was established by this review. No
production credential, sysadmin substitution, impersonation or broad grant is
proposed. If the corrected check returns zero or NULL, return that evidence for
a separate decision; do not change permissions or retry. A future grant proposal
would need the verified principal, exact required scope and revocation/verification
plan. A successful probe may establish that no permission change is needed.

The old failed receipt did not preserve its session tuple. This probe **cannot
retroactively verify that old session's disappearance**. Do not guess its ID,
terminate sessions or relabel its closure. The observer connection's own disposal
is local evidence, not a third independently observed SQL closure. Any transport
or cleanup timeout remains an incomplete result.

## Exact next action proposed — not executed

1. In the same elevated Windows PowerShell 5.1 console, verify the amended
   collector hash below and invoke it **once with `-AccessReviewOnly`**, the
   existing `$global:D5a2Session`, unchanged manifest path and manifest hash.
   The collector rechecks the fixed host `9SX2VF4`, VM
   `2ac1b401-7076-4965-af71-de36ee0f9f9c` /
   `K98-MGE-Qualification-20261029`, Running state, zero adapters, session
   InstanceId `8818b422-6855-457c-a81e-ff95fc155c84`, and guest identity/process/disk
   gates. If the session changed or is unavailable, stop; do not reconnect.
2. Open one nonpooled, shared-memory, integrated-security connection to guest
   `master`. Set `LOCK_TIMEOUT 0`, set READ COMMITTED, then select its own
   session/version/login/raw permission fields. Save them before validating.
3. Dispose that work connection. If its exact tuple was obtained, open one
   sequential observer connection with the same authentication. Apply the same
   two session settings and own-session observation/check. Only after the
   observer passes, run the parameterized absence query below for the new
   work-session tuple. Dispose the observer. No session is killed.
4. Write a new bounded receipt and return it for local adjudication. Whether the
   result succeeds or fails, **stop there**. A full inventory continuation needs
   its own next reviewed plan; nothing follows automatically.

The only SELECT shapes in the proposed mode are:

```sql
SELECT session_id, login_time,
       CONVERT(nvarchar(128), SERVERPROPERTY('ServerName')) AS ServerName,
       CONVERT(nvarchar(128), SERVERPROPERTY('ProductVersion')) AS ProductVersion,
       SUSER_SNAME() AS EffectiveLogin, ORIGINAL_LOGIN() AS OriginalLogin,
       HAS_PERMS_BY_NAME(NULL,NULL,'VIEW SERVER PERFORMANCE STATE') AS CanObserveSessions
FROM sys.dm_exec_sessions WHERE session_id=@@SPID;

SELECT session_id, login_time FROM sys.dm_exec_sessions
WHERE session_id=@sid AND login_time=@login;
```

Bound: **one attempt, two sequential SQL connections, at most seven SQL
statements and three returned rows** for these fixed queries (success normally
returns two rows). Existing ceilings remain unchanged: 300 seconds overall,
260-second outer wait plus bounded stop handling, 210-second guest budget,
3-second commands, 5-second connects, zero lock wait, 48 statements,
512 rows/statement, 2,048 total rows and 1 MiB host receipt. No auto-retry.
The proposed mode reads **zero retained inputs** and never enters the target
database. The original 8 GiB **pre-start host** memory gate is retained; no
post-start host/guest free-memory floor is introduced. Existing host/guest disk
reserves remain 8 GiB. The running VM's memory/CPU/network settings are unchanged.

## Prepared bytes and offline validation

| File | SHA-256 |
| --- | --- |
| `scripts/collect_p02_d5a2_inventory.ps1` | `599e8d1bf171a68e270a999243b7265d5a486041b9b07773a1d27a9ae2cd4aaf` |
| `tests/validate_p02_d5a2_collector.ps1` | `f87ea06401705b9fda1a537f806e619495c0f1e93ab78048caccfa7a85a3716b` |
| `.codex_artifacts/p025/d5a2-inventory-manifest.json` (unchanged) | `f8fe5c5291baa5baf86502c3924d10eb48200c2dcb0d0e84f5e8e1ff82a743f1` |

Windows PowerShell 5.1 offline tests passed: parser; query accounting, overflow,
deadline and disposal; inert worker cancellation; both work/observer permission
allow/deny/NULL/invalid outcomes; session/raw-value preservation through JSON;
wrong version; failed observation stage; host/guest error-summary merging.
Only extracted helpers and inert commands ran; the operational collector did not.
Access-only input and target-database exclusion was checked by source control-flow
review. Native permissions, remoting serialization and server closure are not
certified by these offline tests.

Architecture, deferred-item and security-routing validators passed; explicit-path
test selection ran. Its Python full-suite, smoke-import, command-registration and
SQL application suggestions are skipped for this isolated operator PowerShell
amendment, which changes no Python application or SQL repository code. Existing
runtime-test evidence is retained rather than rerun without a new change.

Security routing: **Changes**, Deep off, Bot working tree against
`e7443e37212ca91e20d531b3684cc369d0fe1505`; current diagnostic source/test and
supporting pinned manifest reviewed. SQL repository is source-only and unchanged.
Changes scan `35c02989-2aee-4274-9d5a-8b6a861853a9` completed with zero
security findings, including independent architecture review. Reviewed working-tree
snapshot: `445b0cf479ddd64972ac1941974bb63c60074996998acedc1a7137f19b3cb3a1`.
Report: `C:\Users\cwatt\.codex\state\plugins\codex-security\scans\discord_file_downloader\e7443e37212ca91e20d531b3684cc369d0fe1505_20261111T140000Z_qiia13z8\report.md`.
This is source/security evidence, not native readiness certification. No measured
review token usage was supplied by the completed scan. This findings/plan document
is a subsequent documentation-only addition; its security routing is a documented
skip because it adds no executable behavior or authorization.

All broader D5 limits and pending obligations remain: no installations,
business SQL, replay/rehearsal, reset/restore, new input, scheduling change,
provider/production action or permission change. D5b–f, P03/P04 prerequisites,
separate D6 and later whole-flow acceptance remain open.

The [approved readiness plan](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a%20Readiness%20and%20Retained%20Data%20Plan%20-%202026-11-11.md)
and [failed-attempt findings](Startup%20Import%20Export%20Reliability%20-%20P02%20D5a2%20Bounded%20Inventory%20Result%20-%202026-11-11.md)
remain the scope and historical-evidence references. Target log/version-store,
metadata-hold and later cost/qualification limits remain in force for the phases
that exercise them; the proposed access-only probe does not enter that database.
