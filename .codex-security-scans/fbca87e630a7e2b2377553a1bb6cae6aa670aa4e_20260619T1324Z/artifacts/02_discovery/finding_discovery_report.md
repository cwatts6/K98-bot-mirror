# Finding Discovery Report

Scan target: commit fbca87e630a7e2b2377553a1bb6cae6aa670aa4e against b51c048aef15e5a8c3b162636a1c4c9fe83d3569.

Reviewed diff-scoped source files:
- kvk/rendering/kvk_rankings_csv.py
- kvk/services/kvk_rankings_export_service.py
- ui/views/kvk_rankings_views.py

Supporting evidence reviewed:
- kvk/services/kvk_rankings_service.py include_all behavior and internal lookup caps
- tests/test_kvk_rankings_service.py CSV filename/content/formula escaping/full-payload tests
- tests/test_kvk_rankings_browser_view.py private export, Honor channel gate, empty, oversized, upload-failure, and Top 100 exclusion tests
- commands/kvk_cmds.py command type preservation and Honor no-admin-override entry behavior by existing tests

Discovery disposition: no technically plausible security findings identified.

Rationale:
- The new export callback calls _ensure_interaction_allowed_for_mode before building or sending the CSV. Honor export therefore preserves the no-admin-override KVK stats channel gate at interaction time.
- The export response is deferred and sent ephemerally. Discord response text includes only generic status and row counts, not governor names, source labels, or other user-controlled text.
- CSV generation is in memory and routed through a service/formatter boundary. No filesystem path is created from user-controlled data, and no SQL is added to command, view, renderer, or export formatting modules.
- CSV text cells normalize embedded newlines and prefix formula-leading text after left-trim detection for =, +, -, and @. Numeric metric/supporting values are written as values rather than formulas.
- Discord upload size is checked before sending and upload failures produce private generic fallback errors.
- Records mode is not wired into export controls, and Top 100 is not reintroduced as a primary player control.

No candidates were emitted, so validation and attack-path analysis are not applicable for this fallback scan.
