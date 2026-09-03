# F056 requirements cases

Feature: Pivot App. Flag `F056_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F056-REQ-001` | FR-F056-01 | api | entitled editor creates pivot with 2 row dims, 1 column dim, 3 measures → 201, version 1 |
| `F056-REQ-002` | FR-F056-02 | api | `bucket: month` on a text column → 400 `field_errors.row_dimensions[0].bucket` |
| `F056-REQ-003` | FR-F056-03 | api | `avg` on a select column → 400 `field_errors.measures[0].aggregate` |
| `F056-REQ-004` | FR-F056-04 | api | unentitled tenant → 403 `denied` with `entitlement: pivot`; foreign tenant → 404 |
| `F056-REQ-005` | FR-F056-05 | api | compute → 202 within 2 s, output `queued`, job on `pivots.compute` |
| `F056-REQ-006` | FR-F056-06 | api, database | report hiding 300 rows → `row_count` 1,700, hidden amounts absent from sums |
| `F056-REQ-007` | FR-F056-07 | api, performance | 100,001-row source → `failed` with `source_too_large`; 31 s job → `timeout` |
| `F056-REQ-008` | FR-F056-08 | api, database | 21 computes → 20 outputs, oldest pruned in the same transaction |
| `F056-REQ-009` | FR-F056-09 | api, frontend | source version bump → `stale: true` on read, banner in UI |
| `F056-REQ-010` | FR-F056-10 | api, e2e | materialize → sheet with dimension and measure columns; replay returns same sheet |
| `F056-REQ-011` | FR-F056-11 | api | PATCH with stale `If-Match` → 409; accepted change → `pivot.updated.v1` |
| `F056-REQ-012` | FR-F056-12 | api | hourly pivot with running output skipped by scheduler at `:00` |
| `F056-REQ-013` | FR-F056-13 | api | delete pivot → hidden from list and outputs; materialized sheet untouched |
| `F056-REQ-014` | FR-F056-14 | frontend, e2e | builder previews 200 cells, stale banner, editor-only actions |
| `F056-NFR-001` | NFR-F056-01 | performance | outputs read 5,000 cells p95 < 500 ms; 100k compute < 30 s |
| `F056-NFR-002` | NFR-F056-02 | api | entitlement, tenant, ACL, and hidden-value suite green; logs carry no cell values |
| `F056-NFR-003` | NFR-F056-03 | accessibility | axe serious = 0 on builder and grid; keyboard reorder announced |
| `F056-NFR-004` | NFR-F056-04 | api, performance | job retried 3 times then dead-lettered; metrics labelled by `error_code` |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F056/`.
