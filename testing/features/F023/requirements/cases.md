# F023 requirements cases

Feature: Dashboard builder. Flag `F023_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F023-REQ-001` | FR-F023-01 | api | editor creates "Weekly review" → 201, version 1, `widgets: []`; duplicate name → 409 |
| `F023-REQ-002` | FR-F023-02 | api, database | overlap, `x + w > 12`, 41 widgets → 400 naming `widgets[i].position`; retained ids keep cache |
| `F023-REQ-003` | FR-F023-03 | api | each of the twelve kinds validated; `text` over 8,000 chars and unknown kind → 400 `widgets[i].config` |
| `F023-REQ-004` | FR-F023-04 | api, frontend | `kpi` widget without resolver → `unavailable`, `reason resolver_not_registered` |
| `F023-REQ-005` | FR-F023-05 | api | cache miss → computing and job; stale from source_versions; restricted source → denied, no payload |
| `F023-REQ-006` | FR-F023-06 | api | refresh → 202 < 2 s with widget_count; second → 409; `dashboard.refreshed.v1` counts succeeded and failed |
| `F023-REQ-007` | FR-F023-07 | api | interval targets scopes read in 24 h; on_open enqueues when cache > 60 s; override longer than interval → 400 |
| `F023-REQ-008` | FR-F023-08 | api | GET returns widgets with cache_summary and share_summary; list includes shared dashboards |
| `F023-REQ-009` | FR-F023-09 | api, e2e | group share grants view; link guest sees denied tile for Risks-backed table and cannot mutate |
| `F023-REQ-010` | FR-F023-10 | api, database | stale If-Match → 409; delete cascades widgets, cache, and links; tenant B → 404 on widget data |
| `F023-REQ-011` | FR-F023-11 | api, database | each mutation → audit with widget diff and outbox event; job retries then dead-letters |
| `F023-REQ-012` | FR-F023-12 | frontend, e2e | builder drag, resize, keyboard; viewer shows freshness badges and all eight states |
| `F023-REQ-013` | FR-F023-13 | frontend | client validation mirrors server limits; unsaved changes prompt; single `PUT widgets` |
| `F023-NFR-001` | NFR-F023-01 | performance | 40-widget GET p95 < 500 ms; cache hit p95 < 300 ms; refresh < 60 s; drag 60 fps |
| `F023-NFR-002` | NFR-F023-02 | api | cache never crosses scopes; link guest read-only; image requires scanned file |
| `F023-NFR-003` | NFR-F023-03 | accessibility | axe serious = 0 in builder and viewer; keyboard move/resize announced |
| `F023-NFR-004` | NFR-F023-04 | api | spans carry dashboard_id, widget_id, run_id, scope_key; one failing widget does not block others |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F023/`.
