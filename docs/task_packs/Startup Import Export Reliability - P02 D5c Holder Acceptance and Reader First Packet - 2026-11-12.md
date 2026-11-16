# P02 D5c holder acceptance and reader-first packet - 2026-11-12

Status: holder-first guard protocol accepted; reader-first reviewed and ready for one attempt.

The holder-first receipt ending `47235e30af7a4d68b666d289a67a2948` matches
SHA256 `2D2ABD9E741583157C943D266987A8BB65EAC6852FEEFCE8424AD4E930846DB3`.
Independent adjudication checked all 24 observations, paired preimages, source
hashes, resource limits and process/SQL closure. Holder session60 and reader61
have distinct births/connections. The holder recorded Exclusive; the unchanged
reader returned ObservationBusy caused by SQLSTATE42000/native51966 without
entering its read body. Reader rollback, isolation restoration and close were
acknowledged. Holder release returned0/NoLock, its close was acknowledged, and
the independent observer found both actors absent. PID4160 exited normally.

The 42,336-byte receipt accounts for 48 reserved command units and41 reserved
row units: 24 actual wrapper statements/29rows plus the24-command/12-row child
reservation. The child actually executed five statements and read four rows.
Host1.0824652 seconds consumes two, leaving **1,471 native seconds**, including
471 of the proposed D5c allocation. **21 inputs remain consumed**. Original
evidence and the accepted baseline receipt are preserved. Acceptance is recorded
in `.codex_artifacts/p025/d5c-schema-holder-first-acceptance.json`.

## Reader-first packet

The contender connection is identified first but acquires no guard. The actual
managed reader then enters SNAPSHOT and records its Shared/Transaction ownership
of `K98:maintenance-schema:v1`. Only then does the contender request the exact
Exclusive/Session guard with zero wait. Required result is -1/NoLock.

After acknowledged reader rollback, isolation restoration, cursor close and
connection close, one separately scheduled contender admission is permitted.
It must acquire Exclusive, release successfully and report NoLock. This is a
planned post-drain admission following a known refusal; it never retries an
unknown acquisition, release or cleanup. Any unexpected admission/mode, failed
close, missing evidence or different result stops the packet. Both actor births
are distinct; both use the unique application ID checked by the final independent
session-absence query. The owned interpreter PID must match its receipt and exit
normally without forced termination.

The exact verified interpreter, extension and unchanged six-module bundle are
retained. No business mutation, maintenance child, input, replay, installation,
permission, impersonation, isolation-setting or resource change occurs. The
new script, manifest and intent names preserve the executed holder-first packet.
Both preceding accepted receipt hashes are checked before admission.

Limits remain24 wrapper statements +24 reserved child units =48, maximum64
wrapper rows +12 reserved child rows =76, one-MiB receipt, 20-second child
watchdog,25-second parent wait,45-second outer deadline plus10-second join and
60-second manual stop ceiling. Existing disk/log/version-store limits remain.
On the expected path the child executes seven statements and reads six rows.
The 24-wrapper-statement scope is unchanged from holder-first and preserves
the same paired identity/ownership/permission/claim/backup/resource checks.

Seven fake-driver cases pass: normal ordering, wrong holder identity, unexpected
contender admission, unknown reader close stopping later admission, failed later
admission without retry, wrong shared mode, and holder close attempted only once.
Ninety-four PowerShell offline checks and Ruff pass. These do not substitute for
the real native packet. Use the established isolated-packet selection rationale;
full application startup and full pytest remain outside this bounded scope.

Changes review of this exact source/test/manifest/doc snapshot is required before
handoff; Deep off. SQL source of truth confirms this existing schema guard and
owner modes. No SQL repository changes. Guard-order evidence does not qualify
actual maintenance-child overlap, production credentials or the remaining
D5c/d/e/f obligations.

## Reader-first handoff ready

Changes scan `b3af48d9-def6-4344-8265-f90d115bcfd5` completed with zero findings
and complete scoped coverage. Independent source review found no execution
blocker. Reviewed head: `7d4beb43253845b400f6bfb4d6b1eb3e1fdd52d4`.
Measured review usage:1,523,596 tokens including1,514,496 cached input tokens;
this consumes no native rehearsal time. Architecture/deferred/security-routing
checks and the explicit path-based test selector were also completed.

Wrapper SHA256:
`8FCBC2D0591512E45D48E4E7D6B17B23047E2EB5F01386CE2F8880F9820FA68B`.
Manifest SHA256:
`3ae7a5c14e435e781ffaaeeb4a242293fbb3ce3d72470eafa24d3b1835ed9d6b`.
Native balance remains1,471 seconds. Require one attempt's full host elapsed
time and immutable receipt, then adjudicate before further native work.
This final status addition changes no executable/manifest bytes.
