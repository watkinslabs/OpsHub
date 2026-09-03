# F013 requirements cases

Feature: Views. Flag `F013_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F013-REQ-001` | FR-F013-01 | api | viewer creates card view → 201, version 1, `owner_id` = actor; 101st view → 400 `view_limit` |
| `F013-REQ-002` | FR-F013-02 | api | filter with `gt` on a text column or 51 leaves → 400 `field_errors.settings.filter` |
| `F013-REQ-003` | FR-F013-03 | api | 6 sorts or unknown `group_by` column → 400; 5 sorts accepted |
| `F013-REQ-004` | FR-F013-04 | api | card lane on text column → 400; calendar without date column → 400; timeline with start/end → 201 |
| `F013-REQ-005` | FR-F013-05 | api | view rows → filtered, grouped, sorted pages of ≤ 500 with visible columns and primary only |
| `F013-REQ-006` | FR-F013-06 | api, frontend | calendar range in sheet timezone; recurrence occurrences read-only; 367-day range → 400 |
| `F013-REQ-007` | FR-F013-07 | frontend, e2e | lane drag patches lane cell; calendar and timeline drag call reschedule; 409 rolls back |
| `F013-REQ-008` | FR-F013-08 | api | PATCH with stale `If-Match` → 409; `is_default` set clears previous default; viewer patching sheet view → 403 |
| `F013-REQ-009` | FR-F013-09 | api, database | delete default → 400; delete other → shares revoked, GET → 404 |
| `F013-REQ-010` | FR-F013-10 | api, e2e | owner shares to group and link ≤ 30 days → 201 with URL; non-owner → 403; 31 days → 400; `GET /public/views/{token}` with no session resolves to a read-only `ViewLinkActor` and returns the filtered rows; expired, revoked, or unknown token → 404 |
| `F013-REQ-011` | FR-F013-11 | api | list shows own private, sheet, and shared views; other's private → absent and 404 by ID |
| `F013-REQ-012` | FR-F013-12 | api, database | each mutation → one audit event and one `view.*.v1` outbox event |
| `F013-REQ-013` | FR-F013-13 | frontend, e2e | switcher lists default first; card, calendar, timeline render; share dialog for owner |
| `F013-REQ-014` | FR-F013-14 | api, e2e | export with `view_id` → CSV rows equal the filtered view rows |
| `F013-NFR-001` | NFR-F013-01 | performance | filtered rows on 100k p95 < 500 ms; lane move p95 < 800 ms; month over 5k rows p95 < 500 ms |
| `F013-NFR-002` | NFR-F013-02 | api | cross-tenant 404; link actor cannot mutate; expired link 404; hidden rows absent |
| `F013-NFR-003` | NFR-F013-03 | accessibility | axe serious = 0 on three kinds; keyboard lane, day, and bar moves announced |
| `F013-NFR-004` | NFR-F013-04 | api | spans carry tenant, sheet, view, correlation; filter compile errors counted |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F013/`.
