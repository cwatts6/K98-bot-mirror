# P02 D5c presentation V3 bootstrap correction

The operator approved this bootstrap correction, review and one additional bounded
offline pass. The pass runs only after completed exact Changes review. Return its
findings before runtime correction or native work; no further approval is needed
for this single pass and no automatic retry is included.

## Exact delta and startup review

`scripts/run_p02_d5c_presentation_offline_v3.py` copies V2 into a fresh version and
output folder. Its sole behavioural change is `import encodings.idna` alongside
the existing trusted-standard-library bootstrap imports, before guards. The codec
loads `stringprep`, `re`, `codecs` and `unicodedata.ucd_3_2_0`. The fixed ASCII host
uses its ASCII encoding fast path after codec lookup; it does not need punycode.
There is no probe, socket, default event-loop policy or provider call in this import.

Every runner/class/function body is byte-for-byte unchanged from V2. The same 35
cases and seven exact refusal assertions remain in the unchanged test file.
Relative imports, missing-module imports and prohibited modules remain refused
after bootstrap. The network check must reach the real `socket.getaddrinfo` audit
boundary; a simulated audit call or different refusal does not satisfy it.

Review the full startup and selected guard/async/Mock/report paths, not just the
new import. Check the actual installed codec dependencies, explicit no-IO loop,
all-None subprocess handles and file control. Pin the interpreter and relevant
standard-library sources/native Unicode module in the manifest as additional
read-only identities. These are runtime identities, not retained application inputs.
No application bootstrap, real Discord, SQL/provider or native Windows transport
is loaded by the selected source-body checks.

## Bounds and preservation

Fresh output: `.codex_artifacts/p025/d5c-presentation-offline-v3/`. Retain every V2
preservation pin and add both the V2 failure lineage and new versioned files.
The original and V2 runners, manifests, intents, results and findings stay intact.
Create-new intent/result, 300-second watchdog, 1 MiB diagnostics ceiling,
stop-on-first-failure and all guard boundaries remain unchanged.

Native budget stays **1,361 seconds**, with a protected **1,000-second** reserve;
Windows-test budget stays **50 seconds**. The **21-input allowance stays consumed**.
No old mutation/retry allowance is renewed. No PowerShell/VM step is needed.

## Review and execution

Freeze only this runner, manifest and plan in an isolated review snapshot. Review
as **Changes**, Deep off, with the unchanged test and directly relevant sources as
context. Ordinary branch/index and unrelated local changes stay unchanged.
Before execution, verify syntax, exact two-hunk source delta, identical class and
function ASTs, all pins, unchanged 35-case inventory and limits. Then execute once:

```powershell
& 'C:/Program Files/Python311/python.exe' -I -S -B scripts/run_p02_d5c_presentation_offline_v3.py
```

Adjudicate all case results, exact seven guard events, cleanup, total output/time,
all original and runtime hashes, and both failed receipts. Write findings separately
and stop. Another failure consumes this additional allowance even if no presentation
case runs. Review is static readiness, not evidence that the pass will succeed.

## Evidence limits and other validation

Retain the selected actual source-body/inert-transport scope. This is not proof of
live Discord registration/decorator authorization/delivery, complete ZIP/download
assembly, application bootstrap, Windows transport or C06 recovery Refresh.
No application or SQL contract changes are made. Broad pytest/conftest, smoke,
registration and selector execution remain excluded to prevent unrelated startup.
Architecture/deferred/security routing are focused source review for this tooling
delta; no PR, deployment or new general deferred item is included. D5c and the
later D5 groups are not closed merely by passing this packet; D6 stays separate.
