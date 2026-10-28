# S11 automatic startup and legacy audience compatibility

## Problem and resulting behavior

The first coordinated scan export stopped before a provider execution stream or
attempt was created. Its historical log retained only `ProgrammingError`.
An isolated native test separately reproduces a temporary application-lock
refusal as that exception class; the historical production error number remains
unknown. A subsequent recorded health read succeeded and its preparation closed.
Neither fact justifies blind replay of the failed job.

Offline delivery tests found a second, independently reproducible barrier: the
legacy adapter rejected an explicitly approved public-writer destination and
mixed private/public destinations despite their protected registration. The
adapter now consumes that registration and records the exact audience for every
legacy output. It makes no sharing changes. Private, public-reader and explicitly
registered public-editor outputs retain their real policy. An unexpected public
writer, domain audience, incomplete ACL response or changed post-write policy
fails closed. An ACL change after an attempt retains uncertainty.

`legacy_registered` is an explicit legacy-only receipt/staging classification;
`file_audiences` and the attempt's `legacy_audiences` must match the exact files.
Each part records its own `private`, `public_viewer` or `public_editor` state.
New-source index/generation parts cannot use the legacy classification. The SQL
companion migration extends one trusted CHECK only for `public_editor` on
`Role='output'`; it changes no existing row, grant, procedure or S11 pool policy.

## Trusted automatic startup

Manual publications pin concrete PIDs and creation times and cannot survive a
restart. The new administrative startup issuer owns publication; the authority
and Bot remain filtered, unelevated processes of the reviewed application user.
The existing SQL readiness wrapper can select the issuer through its existing
`BotScript` parameter. Its original wrapper bytes need not change.

The deployment installer must protect the scheduled action, issuer policy, seed
plan, source/dependency tree, state directory and incarnation files. The task's
administrative entry point must be reviewed explicitly; the task does not run
the Bot with its administrative token. The linked token supplies the issuer's
filtered identity but may be identification-only and unsuitable for launch.
The issuer duplicates the primary token from Windows' own desktop shell only
after it matches that linked identity's exact profile, native authentication ID,
session, group attributes and privilege attributes. A missing desktop, different
account/logon or changed capability fails closed. No process enumeration,
password collection, credential fallback or new account privilege is used.
The creation call uses Microsoft's documented [desktop-parent process attribute](https://devblogs.microsoft.com/oldnewthing/20190425-00/?p=102443)
to inherit that verified desktop token. Before any application instruction runs,
the suspended child's token must match the reviewed profile, logon and capability
attributes. The child then joins the issuer's protected job before resuming.

Before application imports, the issuer uses the gate's two-pass custody rule:
reject ordinary application ownership/write rights, then allow only the reviewed
private readers. The same rule applies to administrative policy, seed, history,
state and native creation parents/results. The ordinary runtime evidence store
retains its separate writable shared-account behavior.

Every incarnation has new paths, IPC nonce and protected manifests. The logical
deployment/review identities, source pins, SQL expectations, file exclusions,
credential custody and historical provider/operator observations stay fixed.
Only the native logon SID may vary within the otherwise exact reviewed ordinary
token profile. The current token observation is renewed truthfully; historical
review timestamps are not relabelled as fresh provider or SQL observations.

Each role is created suspended, assigned to an administrator-owned job and then
resumed. The venv redirector and watchdog descendants stay in that job. Gates
authenticate the pinned administrative pipe server; the issuer observes the
native client PID and verifies membership in the corresponding created job,
native image and exact ordinary token. A user-writable PID file/log marker does
not authorize publication. Live handles are checked again at atomic release.

A global administrator-owned mutex prevents concurrent host supervisors.
Immutable, sequenced records retain prior identities/publication hashes. A normal
watchdog restart returns control to the issuer; it never relaunches against old
manifests. Shutdown exits, while requested restart and a cleanly drained crash
receive a fresh pair. A crash storm stops for reconciliation.

Before a replacement, the issuer requires no conflicting/blocked registered
resource or unclosed account stream. An old SQL session is closed only when its
manifest is the exact retained predecessor and termination is proved by retained
handle identity/exit, or by both process creation times predating the documented
native [OS boot observation](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-operatingsystem).
A missing PID or elapsed lease is never termination proof. The existing SQL
procedure still checks all streams/enrollment and its version CAS. Jobs,
attempts, resources, inputs and provider requests are not replayed or reset.

Partial publication and unresolved work retain evidence and stop automatic
replacement. Same-boot unobserved supervisor termination requires reconciliation.
The issuer waits for actual authority drain; it imposes no forced drain timeout.

## Validation and deployment checkpoint

Local validation currently includes the legacy private/reader/editor fixture,
mixed recorded delivery, post-write ACL-change uncertainty, per-file receipt and
new-source exclusions; ordinary-token/profile renewal and immutable-record cases;
startup readiness/old-session/unknown-termination rejection; and native SQL CHECK
apply/rerun, old-row preservation, index/generation exclusion, malformed timestamp,
untrusted preimage and schema-mutex rejection.

The MINI_AMD native sleeping-child probe passed: the issuer was elevated, the
application child was unelevated, job membership was observed, the child read
its own token, and it exited successfully. No Bot, SQL, provider or task action
occurred in that probe. The full local suite passed 6,451 cases with 86 skips;
66 additional custody cases passed after the final custody correction.
Full issuer lifecycle validation remains required. These results do not establish
production startup, provider reliability, reboot acceptance or go-live. Separate
final Bot/SQL Changes reviews and private promotion checks precede deployment.

Deployment order: reviewed SQL CHECK/audit, protected source update, independent
expected-contract refresh/readback, protected automatic seed/policy/task
installation, normal start/restart acceptance, guarded retained-export test, then
the separate KVK activation decision and selected first baseline upload. Keep
intake/recovery closed until that decision. Do not re-enroll the existing pool,
rewrite enrollment provenance, replace legacy files or retry an uncertain job.
