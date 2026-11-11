> **Archived 11 November 2026:** Superseded planning or delivered D4 evidence. Use the [active D5 scope](../Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Scope%20and%20Handover%20-%202026-11-11.md). Preserve the historical body below; do not replay dated instructions.

# P02 D4b backup route visibility

Status: source correction under validation. Installed route qualification and the
remaining D4 slices are open. No backup, SQL Agent job or production change was run.

## Behaviour and affected callers

`log_backup.request_once` is shared by the owned maintenance backup worker and
`log_health._trigger_log_backup` during pre-admission. Its old `OBJECT_ID` probe
could interpret metadata hidden from the caller as an absent wrapper and choose
an alternate job route. The fixed metadata query runs in msdb without changing
the caller's current database, including callers connected to master.

A visible wrapper must report effective EXECUTE permission. A NULL object ID
permits a job route only under an existing msdb dbo context, which can establish
absence. Database VIEW DEFINITION alone is insufficient: an object-level DENY
can hide the wrapper while that database permission still reports true. Restricted
principals must have a visible, executable wrapper; this change adds no grants or
credentials. Unknown, denied, malformed or additional metadata results refuse
before dispatch.

The dispatch boundary remains unchanged: one chosen route, one request, no
fallback after an uncertain response. Acknowledgement is not backup completion.
Cleanup failure retains the connection and its known outcome under the accepted
D3 custody rules. Existing job-name/job-ID selection and schedules are unchanged.

## Evidence and remaining qualification

- 92 focused backup and historical-updater tests passed.
- 16 native local SQL tests passed: two permission/context cases and 14 affected
  final-stats maintenance cases. The permission fixture covers absent, hidden,
  visible-but-denied, executable and object-DENY-hidden wrappers.
- Native fixtures use disposable local databases; their inert wrapper is never
  dispatched and is not evidence of the installed wrapper definition. Dispatch
  responses are simulated. The real msdb check reads metadata only.
- All 88 existing transition entries retain their exact parsed content. The
  test-only source bridge authenticates the successor before exposing the prior
  hash to historical assertions. It grants no installation permission. A partial
  backup-only update still refuses; the combined release remains D4c/D4d work.

The source-of-truth SQL repo still lacks the actual installed msdb wrapper.
MINI_AMD's private collector receipt must establish its definition and bindings;
the actual runtime identity's effective route must be qualified separately. Do
not broaden permissions to satisfy this gate. The operator reports no manual
access by external tools; this does not establish absence of scheduled/internal
consumers or authorize retirement of any legacy procedure.

The D4b direct-child SQL companion is merged as SQL PR151 (`e0bbe794`), with
final-head CI and code review passing. That source merge does not deploy SQL or
close installed consumer qualification, F31, the combined migration or D4.

## Review gates

Architecture validation passed for the five changed Python files. Test selection
recommended the full suite, smoke imports, command registration and release
regressions. Full-suite validation belongs to the final combined candidate;
command registration is unchanged in this slice. Focused source-custody and
native affected-caller coverage are recorded above. Final lint, repository
validators and the separate Bot Changes security review are recorded in the PR.

Security routing: Changes review of this Bot branch from `f1539abc`, Deep off.
The changed permission/data-access boundary requires review. SQL PR151 has its
own separate completed Changes reviews; those do not cover this Bot patch.
