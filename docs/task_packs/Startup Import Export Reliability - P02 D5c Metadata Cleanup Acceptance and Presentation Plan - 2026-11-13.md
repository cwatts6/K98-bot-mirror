# P02 D5c metadata cleanup acceptance and next offline check

## Accepted cleanup

Receipt `d5c-metadata-resume-result-de2614d2a1e3452db6f38cca53ab6d17.json`
matches SHA256 `bd57111e3605785eb12233115dc5e1f230e1b14e8823d60a7a072417f9fad20c`.
Local adjudication is saved in
`.codex_artifacts/p025/d5c-metadata-resume-cleanup-acceptance.json`.

The exact recorded ID 15 / SID / creation identity was checked before the
acknowledged DROP. The temporary database user is absent, with no same-name
server login. Existing user/login fingerprints are unchanged. All original 799
permissions and their fingerprint are restored, and the seven fixture rows,
maintenance completions and first error, ownership, candidate definitions,
statistics, original database protection and backup state are preserved.
Both SQL connections were disposed; the exact work-session birth and owned actor
application were absent. No new diagnostic actor or business workload ran.

The packet used 35 command units, 107 rows and 21,866 receipt bytes. Full host
elapsed time 0.7495559 seconds is charged as one second: **1,361 native seconds**
remain, including the protected 1,000-second later-phase reserve. Windows-test
time remains **50 seconds**. The **21-input allowance remains consumed**.

The temporary metadata-user scope is closed. Its 171 unused seconds do not
authorize another account or test. Setup, diagnostic and cleanup allowances are
consumed. Preserve both original Setup failure and all follow-up evidence; no
old script should be rerun. This closes the remaining denied-metadata and user
cleanup obligation. No claim is made about historical production lock ownership.

## Next bounded preparation: C12 presentation integration

The next useful work is offline and requires no new PowerShell/VM step. Extend
the earlier service-only status proof across the actual health-card, Refresh and
report handoffs. Current source inspection identifies:

- `services/operator_status_service.py`: snapshot reads already-loaded published
  observations; `check_sql` is a separate active path that must remain uncalled.
- `ui/views/health_view.py`: `HealthView.do_refresh` checks guild/channel/message,
  acknowledges before render, suppresses concurrent/closed refresh, and edits the
  existing card. The injected render must use the passive projection.
- `services/recovery_report.py` and `services/recovery_complete_report.py`:
  ordinary and complete report health components consume retained observations.
  Reading persisted incident evidence is not a fresh connectivity/provider probe.
- `services/recovery_service.py`: recovery `refresh` includes reconciliation and
  inspector work. It is an effectful recovery route, not interchangeable with the
  health card's Refresh button; keep it in C06 and out of passive acceptance.

Use the existing assertions in `tests/test_passive_health.py` as the starting
selection, without running the whole module or project conftest:

- `test_personal_stats_health_does_not_initialize_missing_runtime`
- `test_persistent_refresh_acknowledges_before_render_and_after_idle`
- `test_refresh_rejection_never_renders_or_edits`
- `test_refresh_failure_never_reposts_and_shutdown_waits_for_edit`
- `test_command_and_all_adapters_have_no_active_health_edges`
- `test_ordinary_report_uses_optional_passive_projection`
- `test_real_command_body_and_scheduled_adapter_share_passive_card`
- `test_complete_report_health_component_is_optional_and_bounded`

Before running, inspect the exact dependencies, fixtures and parameter expansion;
freeze actual node IDs and source hashes. Preserve the original offline runner
and its failures. A new bounded runner must retain refusal of network, real SQL,
provider dispatch, native pipe/file entry, subprocess and writes outside its
owned output folder. No Discord client/login or production configuration loads.
Do not simply disable the earlier Discord/native import guard to make the tests
start. Use reviewed inert transport/dependency seams, preserving real service and
view callback logic, and identify any remaining integration limitation explicitly.

Include negative controls for missing/stale/busy/cleanup-uncertain observations,
wrong-card scope, failed acknowledgement and a source attempting active work.
Freeze the complete test/runner packet and review its Changes diff before the
single bounded pass. The existing five-minute offline and 1 MiB diagnostic limits
apply. Stop on the first safety failure, preserve it, and return findings before
any runtime correction or repeat. This is preparation, not executed C12 evidence.

No new fixture, grant, user, setting, import, maintenance or provider request is
needed by this plan. Native balances and the later-phase reserve remain unchanged.

## Remaining scope and validation

D5a and D5b remain accepted. D5c still has partly open full-inspector (C01),
season/weights (C04), queue/pool/unowned-work (C05), action-boundary (C06),
factory/identity (C09), and presentation-integration (C12) groups. Do not convert
these unequal groups into a percentage. D5d fault/restart, D5e balanced cost and
D5f final evidence follow; D6 deployment remains separate and unauthorized here.

This turn changes local receipt-adjudication/bookkeeping and a source-only plan,
not the reviewed executable packet or application code. All six frozen packet
hashes were rechecked unchanged. A new security scan and runtime tests are skipped
for this adjudication-only delta; the completed Changes review remains applicable
to the byte-identical cleanup packet. The next executable offline packet will need
its own targeted tests and Changes review. Deferred/routing documentation checks
apply; no unrelated refactor or deferred optimisation item is introduced.
