# Windows ownership and access contract

Required for work touching protected source, updater packages, startup policy or
Windows file custody. Use with the [Promotion Guide](Promotion%20Guide.md) and
[S11 release contract](S11%20Deployment%20and%20Restart%20Contract.md).
This records existing boundaries and validation requirements; it does not install
new updater capabilities or authorize broader access.

## Establish execution context

Record machine, resolved workspace, running versus development checkout, actual
process identity/SID, elevation, shell version and approved operation. An account
being an administrator does not prove the process is elevated. Agent permission
to run outside its normal restrictions does not establish a Windows UAC admin
token. Identify surrogate-account test results explicitly.

Develop in an isolated mirror checkout. On MINI_AMD, use the installed updater
from elevated Windows PowerShell 5.1 under the reviewed deployment account.
Do not activate the bot environment or run development setup. Do not assume Git
is on the admin shell's PATH: the current explicit path is
`C:\Program Files\Git\cmd\git.exe`. Installed tools still authenticate configured
executable bindings; finding an executable is not sufficient.

## Ownership domains and permitted operations

Owner, group, ACL/inheritance, attributes, byte identity and open-handle history
are separate facts. Matching hashes or clean Git status does not establish
administrative custody. A matching owner does not prove safe access.

| Operation | Prerequisites | Boundary |
|---|---|---|
| Inspect | Bounded reads of exact paths and parent chain; owner SID, SDDL, attributes/numeric flags, inventory/hashes where applicable | Do not import bot code or invoke provider health probes for a filesystem diagnosis. |
| Prepare release | Installed updater, elevated PowerShell 5.1, authenticated private-main target and predecessor | May create packages and establish supported fresh-file custody; preparation is not a no-write diagnostic or deployment proof. |
| Create authenticated source files | Reviewed updater/repair path, verified bytes and protected parent/object identity | No arbitrary local copies into live source; do not treat existing objects as fresh. |
| Replace directory | Exact reviewed repair, verified inventory/metadata, fresh protected objects, retained original and resumable receipts | Changing ownership alone does not neutralize prior handles or establish fresh custody. |
| Install source/index and startup policy | Protected stages after verified drain, exact bindings and continuation receipts | No manual live pull/switch, reset/clean, formatting, tests, package install or ad hoc index repair. |
| Restart | Graceful restart once when requested by runner; verified drain and successor | Do not start the task or force restart to bypass preflight. |
| Recover/resume | Exact stage, receipts and authoritative outcome/ownership evidence | No evidence deletion, age-based claim release or blind replay. |
| Change SQL/runtime data/provider state/activation | Separately authorized workflow and its own evidence | Filesystem repair does not authorize these operations. |

Protected source, updater/startup policy and application-writable logs/caches/
queues/runtime data are distinct ownership domains. Never recursively apply one
ACL/owner policy across them. Inspect installed policy and script checks first.

## Failure and repair requirements

Retain the error, exact path/stage and repair/release receipts. Read metadata
before changing it. Check inventory/bytes, reparse points, hard links, alternate
streams and unsafe write access as required by the relevant contract. Distinguish
unsupported existing directories from fresh files the updater can safely establish.

Use a reviewed bounded repair with interruption/resume behavior. Preserve the
original and verify replacement bytes and permissions. Do not use blanket
takeown/icacls, ACL resets, recursive cleanup or attribute clearing to pass a guard.
Ownership/ACL changes do not revoke access already granted through open handles;
use fresh-object replacement where required by the custody contract.

The verified 24 October archive repair allowed `Directory|NotContentIndexed` only
on protected staging/replacement objects. That ordinary indexing flag was inherited
from the protected location, distinct from reparse/link hazards. This is not a
universal attribute allowance. Exact predecessor and other-object checks remain.
Document allowed flags per object role; reject unexplained metadata.

After verified repair, use supported preparation again. Fresh runtime checks can
find a different blocker even when filesystem repair succeeded.

## Provider stream preflight

An earlier preparation does not reserve a quiet interval. Health dashboard updates
and manual bot-status checks can start Google Sheets probes, and their work can
continue after the UI deadline. Use bounded SQL-only observations for the exact
account/stream/preparation to diagnose this gate; do not repeatedly refresh health.

Observe closure/completion before recommending retry. An open session is not an
open stream. Healthy monitoring or zero unresolved incidents does not certify
closure or delivery. Do not bypass the gate, force closure or infer staleness by
age. Future waiting/drain coordination must preserve ownership and uncertainty.

## Validation and diagnostics

Test actual Windows PowerShell 5.1 behavior: production-like ACL inheritance/default
owner, ordinary staging metadata, fresh objects, partial-stage resume, interruption
between renames, retained originals and prior/active handles. Include rejection of
changed bytes/inventory, reparse points, hard links, alternate streams and unsafe
ACLs. Verify rejected cases leave source and evidence intact.

Distinguish syntax checks, surrogate-account fixtures, real elevated rehearsal and
production receipts. Keep fixtures outside live source/runtime data. Test examples
with Git absent from PATH. In PowerShell 5.1, assign foreach output before piping
it. Errors should identify stage/path, observed versus required owner/access/
attributes and a bounded next action without exposing secrets.
