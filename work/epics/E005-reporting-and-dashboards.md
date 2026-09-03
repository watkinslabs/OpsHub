---
id: E005
type: epic
status: planned
owner: platform
target_milestone: M4
branch: e005-reporting-and-dashboards
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 7, 9
- Capability contract: `docs/capability-contracts.md` rows F021, F022, F023, F024, F025
- Product spec: `docs/product-capability-spec.md` section 5.6 (REPORT-01 to REPORT-04), section 6, phase 4

# E005 — Reporting and dashboards

## Outcome

Teams and leaders see current cross-work performance without exporting sheets to a spreadsheet. A PMO builds a report that joins rows from several sheets by stable column IDs, filters and groups them, adds calculated fields, and reads only the rows the viewer is allowed to see. Metrics summarize those reports into KPI values and period rollups with trend deltas. Dashboards arrange KPI cards, tables, charts, burndown, timeline, workload, text, image, and embedded reports on a shared grid, refresh on a schedule through cached worker jobs that expose last success, duration, source versions, and stale state, and are shared with the same ACL and expiring-link rules as every other resource. Every chart declares dimensions, measures, aggregation, timezone, formatting, and empty/error states. Drill-through opens the source row only when the viewer has access, hidden values stay out of aggregates unless tenant policy allows them, and PDF/PNG/CSV export runs asynchronously and records who exported what. Milestone M4; spec phase 4 exit: a PMO operates weekly portfolio reviews from governed dashboards.

## Scope

- Included: report query model (source selection, joins by stable IDs, filters, grouping, calculated fields, row-level permission filtering) and cached report snapshots (F021); metric definitions, KPI values, period rollups, trend comparison, and recompute jobs (F022); dashboard CRUD, widget registry with the ten widget types, 12-column layout, widget data cache, refresh policy, and sharing (F023); chart definitions, ad-hoc chart queries, time-series projections, burndown, timeline, and workload data (F024); secure drill-through and asynchronous PDF/PNG/CSV export with export records (F025).
- Included: audit events and outbox events for every mutation and refresh; permission-negative suites for cross-tenant, viewer, guest-link, and hidden-column cases; performance lanes at the 100,000-row and 500-column scale targets.
- Excluded: portfolio rollups and project health (F031), pivot outputs (F056), published dashboard embeds for anonymous audiences (F059), natural-language report generation (F039), WorkApps role experiences (F051), a separate analytics warehouse (spec section 10 keeps PostgreSQL projections as the only store).

## Child features

- F021 Cross-source reports: report definitions with sources, joins, filters, grouping, calculated fields, permission-filtered rows, and refreshable snapshots.
- F022 Metrics and summaries: metric definitions, cached KPI values, period rollups, trend deltas, and recompute runs.
- F023 Dashboard builder: dashboards, widget registry and layout, widget data cache with refresh state, and sharing.
- F024 Charts and insights: chart definitions and queries, bar/line/pie components, time-series projections, burndown, timeline, and workload.
- F025 Export/drill-through: access-checked drill-through to source rows and asynchronous PDF/PNG/CSV export with requester records.

## Exit criteria

- [ ] End-to-end scenario passes: a PMO editor creates report "Portfolio status" joining "Projects" and "Risks" sheets, groups by owner with a calculated "Days late" field, defines metric "Open risks" with a weekly rollup, places a KPI card, a bar chart, a burndown, and the report table on dashboard "Weekly review", schedules a 30-minute refresh, shares it with the leadership group, and a viewer opens it, sees stale state clear after refresh, drills into a risk row they can read, is denied drill into a row from a sheet they cannot read, and exports the dashboard to PDF with the export recorded against their user.
- [ ] Hidden-column and restricted-sheet values are absent from report rows, metric values, widget payloads, chart series, and exports for a viewer without access, verified by the permission lanes of F021 to F025.
- [ ] Refresh jobs for reports, metrics, dashboards, and time series expose `last_success_at`, `duration_ms`, `source_versions`, and `stale` and recover from worker failure through retry and dead-letter paths.
- [ ] All five features accepted: API, database, frontend, E2E, accessibility, and performance lanes green in `cargo xtask test-all`; `check-contracts` reports no route or event drift.
- [ ] Rollback verified per feature: flags off remove routes and worker consumers; down migrations run on an empty tenant.
