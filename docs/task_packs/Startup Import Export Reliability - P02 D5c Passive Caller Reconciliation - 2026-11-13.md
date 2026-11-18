# P02 D5c passive caller reconciliation — 2026-11-13

This closes the outstanding source-to-wrapper mapping for **D5c C12's passive
presentation/non-interference requirement**. It does not add another test pass,
claim new Discord delivery, qualify effectful recovery Refresh, or close D5c as
a whole. The differently numbered programme caller C12 remains a separate P04
obligation.

The accepted 35-case receipt is `d5c-presentation-offline-v3/result.json`, SHA256
`d140d67bbb20fd00108f301ae86f2476b8b441635c7dd5ca97e05eb1dd662c69`.
Its original acceptance and two failed predecessors remain unchanged. The D5d
custody post-run adjudication reverified this receipt and all related preserved
source pins. No qualification result is derived from source inspection alone.

| Required passive route | Actual current path | Accepted evidence and bounded inference |
|---|---|---|
| Status command | `commands/admin_cmds.py:status_command` → `_health_card` → `operator_status_service.snapshot` | Actual extracted command and card bodies exercised, including acknowledgement failure; command decorators/Discord delivery were inert. Source confirms `_health_projection` directly calls the same snapshot. |
| Scheduled card | `bot_instance.py:_update_health_embed` → `_health_projection`/`_health_card` | Actual selected updater/card bodies returned the same projection as the command. Message creation, registration and alerts were transport seams. Source inspection confirms those wrappers use retained projection/message identity, not SQL/Sheets health probes. |
| Persistent health Refresh | `ui/views/health_view.py:HealthView.do_refresh` → bound `_health_card` | Actual callback/render bodies exercised for correct scope, wrong guild/channel/message, unbound/closed/concurrent cases, acknowledgement failure and edit failure/drain. No effectful recovery method is used by this Refresh. |
| Missing/busy/uncertain state | `operator_status_service.snapshot` → already-loaded `health_snapshot`/`snapshot` functions | Nine projection/card cases exercised. Missing evidence remains unknown; local capacity is not presented as SQL health. `_loaded` uses `sys.modules`, so absence does not initialize a source. The separately defined active `check_sql` has no edge from these presentation bodies. |
| Ordinary report health | `RecoveryService.download_report` → `recovery_report.build_report`/`_build_report` → `_monitor_report` | Actual monitor projection exercised for available, missing and failed evidence. The wrapper reads scoped stored incident pages and formats retained observations; it does not call adapter inspection, reconciliation or execution. |
| Complete report health | `RecoveryService.download_complete_report` → `recovery_complete_report.build_complete_report`/`_build` → `recovery_evidence_bundle.collect_components` | Actual component collection exercised for available, missing, failed and byte-bound evidence. The wrapper collects these components before stored incident pagination and archive assembly. Full ZIP construction/delivery is outside this new pass. |
| Report UI transport | `ui/views/recovery_view.py:report_call` → `call_recovery` with explicit report method | Source distinguishes report cancellation/drain and attachment authorization from recovery actions. No claim that arbitrary `call` methods or every recovery button are passive. |

The original D5 obligation reconciliation already records P01.3 F11 and programme
caller C08 as accepted at E82–E85 for passive command/card/Refresh and report
delivery. The present selected-source tests qualify the current P02 retained
presentation behavior; the wrapper trace resolves their remaining mapping gap.
It does not manufacture a requirement to repeat accepted live delivery merely
to refresh evidence. Publication, bot restart and later natural acceptance remain
separate from this D5 qualification.

**Disposition:** D5c C12 accepted for the named passive status/card/health-Refresh
and report-health non-interference paths. Source mapping is distinct from executed
case evidence. C06 still owns Recheck, recovery Refresh, accepted-action
reconciliation, group/batch and outcome-worker effects. D5d retains death/lost
acknowledgement/uncertain cleanup, and D5e retains measured cost/non-interference.
No native seconds, Windows-test seconds or additional inputs were consumed.
