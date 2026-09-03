# F024 — Charts and insights harness

Feature-gated tests for `F024`. Keep test code in this directory.

- Gate: `F024_FEATURE`
- Targeted: `cargo xtask test-feature F024`
- Full: `cargo xtask test-all`
- Routes under test: `POST /api/v1/charts/query`, `GET /api/v1/charts/{id}`, `PATCH /api/v1/charts/{id}`, `GET /api/v1/sheets/{sheet_id}/burndown`, `GET /api/v1/time-series/{metric_id}`; events `chart.updated.v1` and `time-series.projected.v1`; tables `chart_definitions` and `time_series_points`.
- Fixtures: `testing/fixtures/charts.rs` reusing the F021, F022, and F023 fixtures — tenants A and B, report editor Dana and viewer Lee, report "Portfolio status" (100,000 rows, `Budget.margin` hidden from Lee), sheet "Sprint 12" (200 rows, `Status` column with 14 days of `cell_history`, `Points` numeric, `Assignee` person, `Start`/`End` dates, plus a 10,000-row 90-day variant), metric "Open high risks" (52 weekly values, plus flat 2-point and 10,000-point variants), dashboard "Weekly review" with one widget per chart kind.
- Determinism: fixed clock `2026-09-03T00:00:00Z`, timezone `America/New_York` including a DST boundary day, seed `0x0F24`, one schema per test worker and a tenant ID per test.
- Stubs: in-memory outbox recorder, JetStream stub for `charts.project`, F049 formatter fixtures, MSW handlers returning recorded success, empty, denied, stale, truncated, and 500 payloads for the five routes.
- Lanes: `requirements/` (traceability for FR-F024-01..12 and NFR-F024-01..04), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
- Evidence: `testing/evidence/F024/<lane>/`.
