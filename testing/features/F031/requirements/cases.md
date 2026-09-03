# F031 requirements cases

Feature: Portfolio rollups. Flag `F031_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F031-REQ-001` | FR-F031-01 | api | admin creates portfolio "Q4 launches" → 201, version 1, `rollup_state: never`; duplicate name → 409 `field_errors.name` |
| `F031-REQ-002` | FR-F031-02 | api | 120 portfolios → cursor pages of 50, filter `workspace_id`, sort by name; detail carries `project_count` and `last_refresh_at` |
| `F031-REQ-003` | FR-F031-03 | api | PATCH with stale `If-Match` → 409 with `current_version`; policy change persisted |
| `F031-REQ-004` | FR-F031-04 | api, database | PUT 3 project IDs → membership replaced, audit lists added/removed; foreign ID → 400 `projects[i]`; 501 IDs → 400 |
| `F031-REQ-005` | FR-F031-05 | api | mapping to a column absent from one project → that measure `state: missing`, others `ok` |
| `F031-REQ-006` | FR-F031-06 | api | POST refresh → 202 with `job_id` in < 2 s; second POST while running → 409 |
| `F031-REQ-007` | FR-F031-07 | api | refreshed rows carry status, variance_days, budget variance_pct, risk_level, value, health with states |
| `F031-REQ-008` | FR-F031-08 | api, database | rows carry `project_sheet_id`, `template_version_id`, `source_versions`, `computed_at`; portfolio has `last_refresh_duration_ms` |
| `F031-REQ-009` | FR-F031-09 | api, frontend | viewer rollup shows "Merger" as denied with null values; totals exclude it; `stale` true after threshold |
| `F031-REQ-010` | FR-F031-10 | api | scheduler tick refreshes changed scheduled portfolio and skips unchanged one with skip recorded |
| `F031-REQ-011` | FR-F031-11 | api, database | each mutation → one audit row and `portfolio.updated.v1`; refresh → `portfolio.rollup-refreshed.v1` with changed project IDs |
| `F031-REQ-012` | FR-F031-12 | api | tenant B → 404 on all routes; viewer → 403 on mutations, 200 on reads |
| `F031-REQ-013` | FR-F031-13 | frontend, e2e | table with totals, last refreshed, stale badge, admin-only refresh, drill link only on `ok` rows |
| `F031-REQ-014` | FR-F031-14 | api | soft-deleted member project → row `state: missing`, `reason: project_deleted` until removed |
| `F031-NFR-001` | NFR-F031-01 | performance | 500-project rollup read p95 < 500 ms; 100-project refresh < 30 s; enqueue ack < 2 s |
| `F031-NFR-002` | NFR-F031-02 | api | snapshot holds no values for unreadable project; guest link → 404; cross-tenant suite green |
| `F031-NFR-003` | NFR-F031-03 | accessibility | axe serious = 0 on list and rollup; keyboard table navigation; refresh announced |
| `F031-NFR-004` | NFR-F031-04 | api | job retried 3 times then dead-lettered with `last_refresh_error`; spans carry tenant, portfolio, job, correlation |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F031/`.
