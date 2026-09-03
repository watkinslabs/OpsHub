# F012 requirements cases

Feature: Dependencies and Gantt. Flag `F012_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F012-REQ-001` | FR-F012-01 | api | editor creates FS link with lag 2 days → 201, version 1, `dependency.created.v1` |
| `F012-REQ-002` | FR-F012-02 | api | self link → 400 `self`; rows from two sheets → 400 `different_sheet` |
| `F012-REQ-003` | FR-F012-03 | api | Design→Build→Test exists, add Test→Design → 400 `cycle` with `cycle_path` of four ids, no row written |
| `F012-REQ-004` | FR-F012-04 | api, database | second link for the same pair → 409 `duplicate` with `existing_id` |
| `F012-REQ-005` | FR-F012-05 | api, performance | 20,000 links on a sheet, one more → 400 `field_errors.sheet_id = "limit"` |
| `F012-REQ-006` | FR-F012-06 | api | list 2,500 links → pages of 1,000; `row_id` and `kind` filters; PATCH lag with `If-Match`; DELETE emits `dependency.deleted.v1` |
| `F012-REQ-007` | FR-F012-07 | api | lag −1 day leads successor by one working day; 8 hours lag equals one working day; ±3,651 days → 400 |
| `F012-REQ-008` | FR-F012-08 | api, performance | critical path on seeded sheet → early/late dates, float, `is_critical` on longest chain |
| `F012-REQ-009` | FR-F012-09 | api | parent row spans min start/max finish of children; link to a parent → 400 `parent_row` |
| `F012-REQ-010` | FR-F012-10 | api, frontend | zero-duration row → milestone node, diamond in Gantt, float computed |
| `F012-REQ-011` | FR-F012-11 | api | preview +3 days → affected list, no cell writes; anchor date → whole sheet re-anchored across holiday |
| `F012-REQ-012` | FR-F012-12 | api, database | commit → one transaction, one audit event, one `schedule.shifted.v1`, new `schedule_version` |
| `F012-REQ-013` | FR-F012-13 | api, performance | 10,001 affected rows → 503 `shift_budget`, nothing written |
| `F012-REQ-014` | FR-F012-14 | frontend, e2e | Gantt bars, arrows, diamonds, critical toggle, drag and keyboard shift with preview; viewer read-only |
| `F012-REQ-015` | FR-F012-15 | api | tenant B on every route → 404; viewer mutations → 403 `denied` |
| `F012-NFR-001` | NFR-F012-01 | performance | 10k-row/20k-link critical path p95 < 500 ms; 1,000-successor shift p95 < 800 ms; list p95 < 500 ms |
| `F012-NFR-002` | NFR-F012-02 | api | cross-tenant, cross-sheet, role-negative, and preview-never-writes suite green |
| `F012-NFR-003` | NFR-F012-03 | accessibility | axe serious = 0; bars and arrows focusable; shift and link announced |
| `F012-NFR-004` | NFR-F012-04 | api | spans carry tenant, sheet, correlation, affected_rows; shift failure rolls back; three metrics exported |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F012/`.
