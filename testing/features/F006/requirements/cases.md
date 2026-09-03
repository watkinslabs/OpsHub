# F006 requirements cases

Feature: Sheets/boards/items. Flag `F006_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F006-REQ-001` | FR-F006-01 | api | editor creates sheet → 201, version 1, default group returned |
| `F006-REQ-002` | FR-F006-02 | api | second sheet with same name in folder → 409 `conflict`, `field_errors.name` |
| `F006-REQ-003` | FR-F006-03 | api | 120 sheets → cursor pages of 50, filter by folder and prefix, sort by name |
| `F006-REQ-004` | FR-F006-04 | api | PATCH with stale `If-Match` → 409 with `current_version` |
| `F006-REQ-005` | FR-F006-05 | api, database | delete then restore → same sheet, group, and row IDs |
| `F006-REQ-006` | FR-F006-06 | api | create row with `after_row_id` → position between neighbours |
| `F006-REQ-007` | FR-F006-07 | api | list rows → position order, cells carry raw/display/validation |
| `F006-REQ-008` | FR-F006-08 | api | move row to another group → `row.moved.v1`, id unchanged |
| `F006-REQ-009` | FR-F006-09 | api, database | delete non-default group → rows in default group; delete default → 400 |
| `F006-REQ-010` | FR-F006-10 | api | replay same key → identical response, one row; different body → 409 |
| `F006-REQ-011` | FR-F006-11 | api, database | each mutation → one audit event and one outbox event |
| `F006-REQ-012` | FR-F006-12 | api | tenant B reads tenant A sheet and row → 404 |
| `F006-REQ-013` | FR-F006-13 | frontend, e2e | board drag and keyboard move update lane and version |
| `F006-REQ-014` | FR-F006-14 | frontend, e2e | viewer sees read-only; non-member sees not-found |
| `F006-NFR-001` | NFR-F006-01 | performance | 100k-row list p95 < 500 ms; row create p95 < 800 ms |
| `F006-NFR-002` | NFR-F006-02 | api | cross-tenant and role-negative suite green |
| `F006-NFR-003` | NFR-F006-03 | accessibility | axe serious = 0; keyboard card move announced |
| `F006-NFR-004` | NFR-F006-04 | api | spans carry tenant, sheet, correlation; outbox failure surfaces metric |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F006/`.
