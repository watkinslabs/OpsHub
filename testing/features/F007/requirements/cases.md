# F007 requirements cases

Feature: Typed columns. Flag `F007_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F007-REQ-001` | FR-F007-01 | api | editor creates `select` column → 201, version 1, position after last column |
| `F007-REQ-002` | FR-F007-02 | api, database | 500 columns exist → 501st POST → 400 `invalid`, `field_errors.sheet_id = column_limit` |
| `F007-REQ-003` | FR-F007-03 | api, database | second column `status` vs `Status` → 409 `conflict`, `field_errors.label` |
| `F007-REQ-004` | FR-F007-04 | api, e2e | rename `Estimate` to `Effort` → same id, cells and formula references resolve |
| `F007-REQ-005` | FR-F007-05 | api | PATCH type `file` → `number` → 400 `unsupported_conversion`; `text` → `number` accepted |
| `F007-REQ-006` | FR-F007-06 | api, frontend | type change on 3 rows with one bad value → `preview.invalid_count = 1`, `mode = sync`; 20,000 rows → `mode = async` |
| `F007-REQ-007` | FR-F007-07 | api | archive option `Done` → existing cell valid, new write rejected; `multi` accepts array |
| `F007-REQ-008` | FR-F007-08 | api | `"1,234.5"` in currency precision 2 USD → normalized `1234.50`, display `$1,234.50`; `"abc"` → `type_mismatch` |
| `F007-REQ-009` | FR-F007-09 | api | `2026-09-03` date, RFC 3339 datetime normalized; foreign-tenant user in `person` → `unknown_person` |
| `F007-REQ-010` | FR-F007-10 | api | each rule (`required`, `min`, `max`, `regex`, `allowed_options`, `date_range`, `unique`) records its name as `code` |
| `F007-REQ-011` | FR-F007-11 | api, performance | POST validate → `queued` under 2 s; job writes one state per cell; counts on column response |
| `F007-REQ-012` | FR-F007-12 | api | reorder after `Owner` → new position, `column.reordered.v1`; 70 moves to same spot → rebalance |
| `F007-REQ-013` | FR-F007-13 | api, frontend | delete, hide, or retype primary → 400 `field_errors.is_primary`; menu hides those actions |
| `F007-REQ-014` | FR-F007-14 | api, database | delete column → hidden from reads, cells retained, dependent formula state `missing reference` |
| `F007-REQ-015` | FR-F007-15 | api | create `formula` shell with null expression; cell write to formula column → 400 `field_errors.cells` |
| `F007-REQ-016` | FR-F007-16 | api | replay same key → one column; tenant B → 404 on every route; one audit and one outbox row per mutation |
| `F007-REQ-017` | FR-F007-17 | frontend, e2e | drawer adds column, preview shown before type change, validation icon carries message |
| `F007-NFR-001` | NFR-F007-01 | performance | 500-column list p95 < 500 ms; create p95 < 800 ms; 100k validate < 60 s |
| `F007-NFR-002` | NFR-F007-02 | api | cross-tenant, role, person-scope, and regex-budget negatives green |
| `F007-NFR-003` | NFR-F007-03 | accessibility | axe serious = 0 on drawer and menu; keyboard reorder; icon described |
| `F007-NFR-004` | NFR-F007-04 | api, database | spans carry tenant, sheet, column, correlation; job run recorded; outbox failure rolls back |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F007/`.
