# KVK16 configuration recovered from retained DB22

Chris identified the restored backup as the configuration source. A bounded read through master on `9SX2VF4\K98DEV` confirmed and extracted KVK16 rows from `S11_G4_Recovery_20260928_97337`. No separate local configuration file or production/Sheets read is needed for these historical settings. This supersedes that missing-file request in the preceding readiness notes.

Observed configuration:

- One DKP weights row: WeightT4X=10, WeightT5Y=20, WeightDeadsZ=40; EffectiveFromUTC `2026-09-28T07:47:08`. Native float bytes are retained alongside values.
- Nine windows. Baseline: start/end scan 1. Pass 4: start 15, end 24, sequence 2; note `Fight called 7th September 07:17`. First Altar: start 46, end 49. Remaining windows have null endpoints; do not invent them.
- Thirty-six kingdom/camp mappings; kingdom 1198 maps to CampID 2, Mercia.
- The bounded join to `KVK.KVK_Scan` returned zero matching rows for these KVK16 endpoint IDs. The window configuration is evidenced, but the historical endpoint file/hash/time mapping is not. This does not establish that all KVK16 scan data is absent. Reconcile the endpoint identities with retained input evidence before local import; do not blindly reuse production ScanIDs in a newly numbered test database.

The completed operation returned 47 rows (including its terminal marker), 5,570 JSONL bytes, in 0.1627324 seconds. The pinned launcher reported success; terminal and SQL receipts are retained under `.codex_artifacts/s11-kvk16-retained-config-20261001/`. `configuration.json` is a local derivation of those returned rows, not a runtime manifest or SQL installation.

Exact command SHA256: `1f77679308cc3164d6f0c6aa01f4a174ce7f30c3458e7a6386b36acfc92d52cc`. Operation manifest SHA256: `15b96e74e81746d7aa20ef51ce340ae54c94af793ee3c223e1510df9eecd7929`. Preparation seal SHA256: `938f8882565551758e648b2feda93721738b404152722171246f1017c185d7de`. Working/sealed copies and all generated evidence are bound by the new result seal.

The connection used the existing integrated original login and per-connection development TLS exception, with master as the connection database. The batch checked DB22's exact ID/name, ONLINE/RESTRICTED_USER/read-only/Broker-disabled state and full administrator visibility before reading its four explicitly named tables. It used only KVK_NO=16 predicates; no player/raw tables were read. Configuration caps were 32 weights, 64 windows and 128 camp mappings, with at most 129 endpoint rows. Total output cap: 354 rows / 256 KiB JSONL; connection timeout 5 seconds, query timeout 10 seconds, lock timeout 1 second, runner wall bound 30 seconds plus the retained launcher's 30-second termination allowance. No application DML, DDL, permission change, backup/restore or baseline operation occurred. Runner/launcher limitations remain as documented in the K98DEV preflight result; no global memory/disk quota is claimed.

The user's ongoing local-validation instruction and explicit identification of this backup supplied the scope. No old approval window was reused. The packet reused the byte-identical reviewed read runner and launcher; no runtime source or SQL source changed. Source review verified named columns in authoritative table definitions. No new application test or canonical security scan ran for this bounded read-only artifact. Preserve the original baseline's B02/B04R1/B05 qualifications; this new extraction does not repair or replace those historical records.

These are backup-time settings, not a claim about current production configuration. Camp mapping alone does not provide independent Kingdom/Camp aggregate observations. Full installation, endpoint reconciliation, report equivalence, provider reuse and complete typed G4/G5 acceptance remain distinct. DB22 remains protected and unchanged; no new ROK_TRACKER database was created by this operation.
