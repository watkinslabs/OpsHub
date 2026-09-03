# F021 requirements cases

Feature: Cross-source reports. Flag `F021_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F021-REQ-001` | FR-F021-01 | api | editor creates report with one source → 201, version 1, `snapshot: null`; duplicate name → 409 |
| `F021-REQ-002` | FR-F021-02 | api | alias `Bad Alias`, foreign sheet id, column not on sheet → 400 with `definition.sources[i]` paths |
| `F021-REQ-003` | FR-F021-03 | api | link join Risks.project → Projects.id matches by row id; cycle and text-to-number join → 400 |
| `F021-REQ-004` | FR-F021-04 | api | `-7d` filter in `America/New_York` selects the expected rows; depth 5 tree → 400 |
| `F021-REQ-005` | FR-F021-05 | api | group by owner with sum(budget) → header rows with depth, key, aggregates, row_count |
| `F021-REQ-006` | FR-F021-06 | api | `DAYS(TODAY(), {projects.due})` evaluated per row; unparseable expression → 400 with parser message |
| `F021-REQ-007` | FR-F021-07 | api, database | refresh → 202 in < 2 s, snapshot succeeded with row_count, duration_ms, source_versions; second refresh → 409 |
| `F021-REQ-008` | FR-F021-08 | api, database | interval 60 enqueues once per hour; interval 4 → 400 |
| `F021-REQ-009` | FR-F021-09 | api | rows page 500, meta carries snapshot_id, stale, restricted_sources, hidden_columns |
| `F021-REQ-010` | FR-F021-10 | api, e2e | restricted viewer: Risks inner-join rows dropped; hidden `Budget.margin` removed |
| `F021-REQ-011` | FR-F021-11 | api | aggregate over hidden column null for viewer; owner policy with tenant setting → owner aggregates |
| `F021-REQ-012` | FR-F021-12 | api | list filters by workspace, folder, prefix; unreadable reports absent |
| `F021-REQ-013` | FR-F021-13 | api, database | stale If-Match → 409; definition change marks snapshots stale; tenant B → 404 |
| `F021-REQ-014` | FR-F021-14 | api, database | each mutation → audit row and outbox event; replay with different body → 409 |
| `F021-REQ-015` | FR-F021-15 | frontend, e2e | editor builds joins/filters; viewer shows stale banner and restricted bar |
| `F021-NFR-001` | NFR-F021-01 | performance | 100k-row rows page p95 < 500 ms; three-sheet refresh < 60 s |
| `F021-NFR-002` | NFR-F021-02 | api | cross-tenant, viewer, hidden-column, restricted-sheet, guest-link negatives green |
| `F021-NFR-003` | NFR-F021-03 | accessibility | axe serious = 0 on editor and viewer; keyboard join builder; live region |
| `F021-NFR-004` | NFR-F021-04 | api | refresh retries 3, dead-letters on 4th; spans carry report_id and run_id; metrics exported |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F021/`.
