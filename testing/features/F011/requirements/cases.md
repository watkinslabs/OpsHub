# F011 requirements cases

Feature: Dates and schedules. Flag `F011_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F011-REQ-001` | FR-F011-01 | api | date, datetime, duration cells parse; malformed shapes → 400 `field_errors.<column_id>` |
| `F011-REQ-002` | FR-F011-02 | api, database | first calendar list → `Standard` default; create validates timezone, week, hours |
| `F011-REQ-003` | FR-F011-03 | api, database | PATCH sets new default → old default cleared in same transaction; stale `If-Match` → 409 |
| `F011-REQ-004` | FR-F011-04 | api, database | holiday and working exceptions applied; 401st exception → 400; duplicate date → 409 |
| `F011-REQ-005` | FR-F011-05 | api | PUT settings with number column as start → 400 `type_mismatch` |
| `F011-REQ-006` | FR-F011-06 | api | GET schedule → settings, calendar, paged rows, `unscheduled` rows with null start |
| `F011-REQ-007` | FR-F011-07 | api | Fri 2026-09-11 + 3 working days → Wed 2026-09-16; holiday skipped |
| `F011-REQ-008` | FR-F011-08 | api | reschedule with start and duration → end computed, version +1, `row.rescheduled.v1` |
| `F011-REQ-009` | FR-F011-09 | api | milestone row with duration 2 → 400 `field_errors.duration = "milestone"` |
| `F011-REQ-010` | FR-F011-10 | api | parent row with roll-up rule on start → 400 `parent_rollup` |
| `F011-REQ-011` | FR-F011-11 | api, database | every mutation → one audit event and one outbox event; replay returns original |
| `F011-REQ-012` | FR-F011-12 | api, frontend | datetime display uses sheet timezone; response carries `display_timezone` |
| `F011-REQ-013` | FR-F011-13 | api | tenant B calendar and schedule → 404; viewer mutation → 403 |
| `F011-REQ-014` | FR-F011-14 | frontend, e2e | settings panel and date editor show all states; snap preview before commit |
| `F011-NFR-001` | NFR-F011-01 | performance | schedule read p95 < 500 ms; reschedule p95 < 800 ms; arithmetic < 5 ms |
| `F011-NFR-002` | NFR-F011-02 | api | cross-tenant and role-negative suite green; invalid IANA name rejected |
| `F011-NFR-003` | NFR-F011-03 | accessibility | axe serious = 0; keyboard date picking with snap announcement |
| `F011-NFR-004` | NFR-F011-04 | api | spans carry tenant, sheet, calendar, correlation; metrics exported |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F011/`.
