# P02 D5c presentation V2: runner-only correction

The operator explicitly approved the runner correction, review and one additional
bounded offline pass. No further approval is needed for that single pass after
review. Stop and return findings before any runtime correction or native work.

## Exact correction and preserved contract

`scripts/run_p02_d5c_presentation_offline_v2.py` copies the original runner into a
new version and output folder. It removes only the unnecessary default-policy
initialization (`asyncio.set_event_loop(loop)`); `run_until_complete` supplies the
explicit no-IO loop and establishes the running-loop context. No import guard is
weakened and no Windows transport/default loop is initialized as a workaround.

The expected-refusal helper additionally checks the exact reason for each of its
seven existing negative controls. An unrelated lazy import cannot count as the
intended refusal. `tests/test_p02_d5c_presentation_offline.py` and all 35 case IDs
remain byte-identical. Application source is unchanged.

Fresh output: `.codex_artifacts/p025/d5c-presentation-offline-v2/`. The manifest
retains all 428 original pins and adds the failed original packet, intent, result,
adjudication, findings, review snapshot and the new runner/plan. Original evidence
is not overwritten. Create-new intent prevents a second V2 execution. No automatic
retry follows an incomplete or failed result, even if zero cases execute.

The same 300-second watchdog, 1 MiB diagnostics cap, no-IO loop, import/network/
driver/native/subprocess guards, owned output, and stop-on-first-failure apply.
No SQL, VM, provider, Discord client, retained-input access or application bootstrap
is authorized. Native balances remain 1,361 seconds (including the protected
1,000-second reserve) and 50 Windows-test seconds. The 21-input allowance stays
consumed. All mutation/retry limits from prior scopes remain unchanged.

## Review and pass

Before execution: parse the runner, compare its full delta to the failed original,
check exact 35-case selection and preservation lineage, inspect the selected async
startup/Mock paths in installed Python, freeze this three-file packet in an isolated
Git snapshot, and complete a **Changes** review with Deep off. The unchanged test
and directly supporting source are review context. Do not run qualification during
review. No change to the ordinary branch or index is needed.

After review, run exactly once:

```powershell
& 'C:/Program Files/Python311/python.exe' -I -S -B scripts/run_p02_d5c_presentation_offline_v2.py
```

Adjudicate every case and the seven exact guard reasons, task/thread cleanup,
elapsed/output limits, all preservation pins and original failed receipt. Save
findings separately. No production correction, native step or further pass follows.

The original packet's inert seams and proof limits remain: selected actual card,
Refresh and report-component bodies, not live Discord registration/authorization/
delivery, complete ZIP downloads, Windows transport or the effectful recovery
Refresh route. Passing this packet does not close all D5c groups or authorize D6.

## Validation routing

This is test tooling only, with no SQL contract/application-layer change. Syntax,
source-delta, manifest and whitespace checks plus the reviewed bounded pass are
the focused gates. Broad pytest/conftest, smoke/registration and selector execution
remain excluded because they can initialize unrelated transports and work. No PR
handoff or new general deferred item is introduced. Architecture/deferred/routing
checks are source review for this narrow packet; a separate SQL scan is inapplicable.
