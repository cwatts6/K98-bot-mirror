# D5c pipeline retention remaining batch

The first offline pass stopped after 21 successful checks (seven controls and
fourteen import-stage behavioral scenarios) on import/late-association. Receipt,
intent, original test, runner and sealed review remain immutable. No native work,
new input, other thread or pending task occurred; all 824 pins were unchanged.

The fixture's broad `SELECT * FROM dbo.ExportPreparation` prefix also matched
`ExportPreparationResource`. The linked-receipt query therefore reached the wrong
argument assertion. This is a transport-fixture defect, not a production defect
or a failed product safeguard. V2 requires the space after the exact table name;
the existing four-table locked-evidence allowlist handles the related table.

The remaining batch contains 133 outstanding behavioral cases and seven runner
controls: 140 checks. The fourteen already-passed behavioral cases are excluded.
Every other behavior assertion and original loaded source body is unchanged.
The failed late-association case must now reach the original locked snapshot
comparison and refuse without mutation. Unexpected queries still fail closed.

Existing approval explicitly includes related corrections and additional offline
passes. V2 receives a fresh exclusive intent/result namespace and pins V1's
failure evidence. It retains the 300-second and 1 MiB ceilings, first-failure stop,
all original evidence and consumed allowances: 1260 native seconds, 1000 protected,
50 Windows seconds, 21 inputs consumed and 11/64 synthetic rows. It runs no SQL,
VM, business workload or application startup. No runtime source changes occur.

Changes review of the exact V1-to-V2 correction must complete before this one
additional bounded pass. On success, combine the fourteen prior accepted cases
and 133 new ones for 147 unique behavioral scenarios; controls are reported
separately. Until adjudication, the route countdown remains 22/73, 51 outstanding.
The original no-linked-producer and no-native-proof limitations remain intact.
