# P02 D5c bounded offline presentation packet

The operator approved one offline status-card, Refresh and report check pass.
This packet changes test tooling only. No application correction, native operation,
new input, account, permission, isolation or deployment change is included.

## Frozen execution

Run `scripts/run_p02_d5c_presentation_offline.py` once using the existing host
Python 3.11 with `-I -S -B`, only after its exact Changes review completes.
`.codex_artifacts/p025/d5c-presentation-offline/packet.json` fixes the case IDs,
source/evidence hashes and limits. A create-new intent prevents repeating the pass.
The runner has a 300-second watchdog, 1 MiB combined diagnostics ceiling and
stops at the first failure, including a swallowed boundary violation. Preserve
failure evidence and report before any correction or another pass.

Application bodies are selected from the frozen source AST without running module
startup. Health projection, card rendering, Refresh admission/acknowledgement/edit,
owned async drain, ordinary-report health collection and complete-report component
collection retain their actual source bodies. The real nested status command body
and scheduled update use the actual common card function. Its registration
decorators alone are removed, as in the existing passive-health regression.

Dependencies are explicit inert seams: Discord Embed/View/button primitives,
response/message objects, private response adapter, timing publication, pinned-card
lookup, alerts, task-monitor inventory and unrelated operation evidence. No real
Discord module, client, login or production configuration is loaded. The complete
report component collector uses an empty synthetic operation inventory and the
real redactor and component bounds. It does not assemble/download a ZIP or read
persisted incidents. C06 recovery Refresh remains excluded because it can perform
reconciliation and inspection.

The standard-library async loop uses a no-IO selector and no self-pipe. These tests
exercise coroutine ordering and draining, not Windows event-loop or transport
behaviour. Socket, subprocess, registry, ctypes/native imports, provider/SQL imports,
new threads/executors and unlisted reads/writes are refused. Code reads only pinned
source/evidence; writes are create-new intent/result files in its fresh folder.
Negative guard controls label and retain expected refusals. An unexpected attempted
operation fails the pass even if application code catches the exception.

## Selection and coverage

The 35 explicit case IDs in the manifest adapt these existing starting assertions
from `tests/test_passive_health.py`: missing-runtime, persistent Refresh ordering,
five Refresh rejection variants, failed-edit drain, passive command/adapters,
ordinary report, shared command/scheduled card and bounded complete health component.
The original pytest nodes are **not run**: their live Discord client and broad
module fixtures would exceed this scope. The new file names every actual case.
Additional controls cover stale, busy, cleanup-uncertain and uninitialized state,
an unbound/concurrent card, source absence/failure and oversized report components.

No claim is made for Discord persistent registration/restart, real deliveries,
full incident-report/ZIP pipeline, production bootstrap, cancellation under a real
Windows transport, or unrelated C01/C04/C05/C06/C09 cases. Tests and implementation
are not substitutes for native proof where required.

## Review and preservation

Security routing: **Changes**, Deep off, immutable packet-only Git snapshot.
Review the runner, tests, this plan and frozen manifest before execution. Supporting
application sources are read-only context. SQL contracts/schema are unchanged;
no SQL statements are added or executed, so a separate SQL repository review is
not applicable. Existing unrelated changes must remain untouched. No new general
refactor/deferred item is introduced by this test packet.

Static syntax and exact manifest/source checks precede review. Broad pytest,
conftest, smoke imports, registration and test selection execution are intentionally
skipped because they can start unrelated environments. Architecture, deferred and
routing gates are evaluated for this focused tooling/documentation delta; no PR,
merge or deployment is part of this task.

All retained small receipts, earlier offline runner evidence, operational logs and
selected application sources are hash-pinned before the pass and rechecked after.
No originals are replaced. Native time remains **1,361 seconds**, including the
protected 1,000-second later-phase reserve. Windows-test time remains **50 seconds**.
The **21-input allowance stays consumed**. No maintenance, writer, isolation or
metadata retry becomes available through this offline pass.
