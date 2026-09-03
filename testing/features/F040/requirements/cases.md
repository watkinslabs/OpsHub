# F040 requirements cases

Feature: AI insights/automation. Flag `F040_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F040-REQ-001` | FR-F040-01 | api | scan request → 202 with `scan_id` and detector list; 20,001 estimated records → 400 `scope_too_large`; no entitlement → 403 |
| `F040-REQ-002` | FR-F040-02 | api | each of the six detectors fires only at its threshold and records `detector_version` and its metrics |
| `F040-REQ-003` | FR-F040-03 | api, database | insight and evidence written in one transaction; `evidence_count = 0` rejected by the check constraint |
| `F040-REQ-004` | FR-F040-04 | api | evidence index 99 on a 4-candidate set → insight discarded, no event, `ai-insight.evidence-rejected` audit |
| `F040-REQ-005` | FR-F040-05 | api, database | first scan publishes `ai-insight.generated.v1`; re-scan bumps `occurrence_count` and publishes nothing |
| `F040-REQ-006` | FR-F040-06 | api | list filters and cursor paging; insight citing the private sheet is absent for the viewer, present for the manager |
| `F040-REQ-007` | FR-F040-07 | api | detail returns confidence, uncertainty, `computed_at`, versions, token usage, ordered evidence; foreign id → 404 |
| `F040-REQ-008` | FR-F040-08 | api, frontend | dismiss with `If-Match` → `dismissed` and event; `kind_for_scope` sets `suppressed_until` 30 days out; stale version → 409 |
| `F040-REQ-009` | FR-F040-09 | api | propose → `pending`, diff, `preview_hash`, `expires_at` +24h, `ai-action.proposed.v1`, zero target writes |
| `F040-REQ-010` | FR-F040-10 | api | `delete_rows` → 400 `not_allowed`; target absent from evidence → 400 `target_not_in_evidence` |
| `F040-REQ-011` | FR-F040-11 | api, e2e | confirm needs `workflow-editor`, a user principal, `If-Match`, and a matching hash; token → 403; expired → 409 |
| `F040-REQ-012` | FR-F040-12 | api | `create_workflow_draft` confirm → F020 approval, `awaiting_approval`, no draft until `decision: approved` |
| `F040-REQ-013` | FR-F040-13 | api | run re-checks permission per target; permission lost → `denied` with no partial writes; `applied_targets` records versions |
| `F040-REQ-014` | FR-F040-14 | api | reject records reason and publishes `ai-action.rejected.v1`; rejecting an applied action → 409 |
| `F040-REQ-015` | FR-F040-15 | api, performance | 5th scan in an hour → 429; same scope inside 15 minutes → 429; budget short → 429 before any provider call; 5 errors open the breaker |
| `F040-REQ-016` | FR-F040-16 | api, e2e | markup payload stored escaped and rendered literally; `ai-insight.injection-blocked` audit names the vector |
| `F040-REQ-017` | FR-F040-17 | frontend, e2e | list grouped by severity, detail evidence table with deep links, propose and confirm dialogs, run timeline |
| `F040-NFR-001` | NFR-F040-01 | performance | 20,000-row scan < 10 min p95; list p95 < 400 ms at 5,000 insights; detail p95 < 300 ms; confirm→run start < 5 s |
| `F040-NFR-002` | NFR-F040-02 | api | every detector reads through the F039 retrieval reader; no model-authored id trusted; no non-human confirm path |
| `F040-NFR-003` | NFR-F040-03 | accessibility | axe serious/critical = 0; severity text plus icon; diff table headers and caption; confirm dialog focus trap |
| `F040-NFR-004` | NFR-F040-04 | api | scan idempotent per `scan_id` and resumable per detector; run idempotent per key; dead-letter after 2; metrics emitted |
| `F040-NFR-005` | NFR-F040-05 | api, performance | token usage and `cost_micros` per insight; ≤ 15,000 prompt tokens per 1,000-row detector pass; budget checked pre-call |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F040/`.
