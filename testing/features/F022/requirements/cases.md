# F022 requirements cases

Feature: Metrics and summaries. Flag `F022_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F022-REQ-001` | FR-F022-01 | api | editor creates weekly count metric → 201, version 1; `sum` on text column → 400 `measure.column_ref` |
| `F022-REQ-002` | FR-F022-02 | api | `percent_of` with 3 of 12 rows → 25; zero denominator → null |
| `F022-REQ-003` | FR-F022-03 | api | report source reads latest snapshot; sheet source reads live rows; unreadable source → 404 |
| `F022-REQ-004` | FR-F022-04 | api, database | recompute → 202 < 2 s, 52 weekly values, run with duration_ms and source_versions; active → 409 |
| `F022-REQ-005` | FR-F022-05 | api | viewer scope null for hidden column; owner scope rejected without tenant policy |
| `F022-REQ-006` | FR-F022-06 | api | values returns current, comparison, series, meta; missing scope → computing and run enqueued |
| `F022-REQ-007` | FR-F022-07 | api | source version advances → meta.stale true; sweeper enqueues once per 5 min |
| `F022-REQ-008` | FR-F022-08 | api | day → week rollup aligned to Monday in `America/New_York`; week → day → 400 |
| `F022-REQ-009` | FR-F022-09 | api | 7 vs 9 with down_is_good → better; 0.3% change → flat |
| `F022-REQ-010` | FR-F022-10 | api | currency EUR in `de-DE` → `41.000,00 €`; duration → `1d 4h` |
| `F022-REQ-011` | FR-F022-11 | api, database | measure change deletes values for all scopes; stale If-Match → 409; tenant B → 404 |
| `F022-REQ-012` | FR-F022-12 | api, database | each mutation → audit and outbox rows; job retries 3 then dead-letters |
| `F022-REQ-013` | FR-F022-13 | frontend, e2e | KPI card shows value, delta text, sparkline, stale and computing badges |
| `F022-NFR-001` | NFR-F022-01 | performance | values p95 < 300 ms; 100k-row recompute < 30 s |
| `F022-NFR-002` | NFR-F022-02 | api | scope_key isolation between two viewers; cross-tenant and role negatives green |
| `F022-NFR-003` | NFR-F022-03 | accessibility | axe serious = 0; delta and sparkline have text alternatives |
| `F022-NFR-004` | NFR-F022-04 | api | spans carry metric_id, run_id, scope_key; recompute metrics exported |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F022/`.
