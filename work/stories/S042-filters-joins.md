---
id: S042
type: story
status: planned
parent_epic: E005
parent_feature: F021
depends_on: [S041]
owned_paths: [crates/domain/src/reports/**, services/api/src/reports/**, apps/web/src/features/reports/**, testing/features/F021/**]
feature_flag: F021_FEATURE
branch: s042-filters-joins
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F021

# S042 — Filters/joins

## Identity

- Parent feature: `F021` Cross-source reports
- Owner: platform
- Branch: `s042-filters-joins`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6; `docs/capability-contracts.md` row F021

## Vertical slice

As a report editor, I want to join my selected sheets by stable column IDs, filter the joined rows, group them with aggregates, and add calculated fields, and as a viewer I want to read the result in the browser with stale, restricted, and hidden-column state visible, so that the Friday consolidation spreadsheet disappears.

## Requirements

- **SR-S042-01:** `definition.joins` builds a tree from `sources[0]` where `link` columns match the right source row `id` and typed columns match by normalized value; cycles, disconnected sources, and type mismatches return `400 invalid` naming `definition.joins[i]` (FR-F021-03).
- **SR-S042-02:** `definition.filters` accepts the `and`/`or` tree with the 13 operators and relative date tokens resolved in `refresh_policy.timezone`; depth over 4 or more than 50 predicates returns `400 invalid` (FR-F021-04).
- **SR-S042-03:** `definition.group_by` up to 3 levels and `aggregates` up to 20 produce group header rows with `depth`, `key`, `aggregates`, and `row_count` computed at read time over the viewer-visible rows (FR-F021-05, FR-F021-11).
- **SR-S042-04:** `definition.calculated_fields` are parsed at save with the F035 parser and evaluated per row at refresh within the 2 second budget; a row exceeding budget shows display `#BUDGET` (FR-F021-06).
- **SR-S042-05:** With `aggregate_policy: "owner"` and tenant policy `reports.aggregate_hidden_values = true`, aggregates come from the owner-scope snapshot and `meta.aggregate_scope` is `owner`; otherwise hidden values are excluded (FR-F021-11).
- **SR-S042-06:** `ReportEditor` (sources, joins, filters, grouping, calculated fields, refresh policy) and `ReportViewer` (rows, group headers, stale banner, restricted-sources bar, refresh button) render loading, empty, error, denied, stale, computing, and offline states (FR-F021-15, NFR-F021-03).
- **SR-S042-07:** A 500-row page of a 100,000-row snapshot with permission filtering responds under 500 ms p95 and a three-sheet refresh completes under 60 s (NFR-F021-01).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/reports/{joins.rs, filters.rs, grouping.rs, calc.rs}` extending `compiler.rs` and `validate.rs`; `services/api/src/reports/handlers_rows.rs` group-at-read path
- Data/migration: none new; `report_filters` projection rows written by the service on save
- React/UI: `apps/web/src/features/reports/{ReportPage.tsx, ReportViewer.tsx, ReportTable.tsx, GroupHeaderRow.tsx, StaleBanner.tsx, RestrictedSourcesBar.tsx, ReportEditor.tsx, SourcePicker.tsx, JoinBuilder.tsx, FilterBuilder.tsx, GroupingPanel.tsx, CalculatedFieldEditor.tsx, RefreshPolicyForm.tsx, NewReportDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: three-sheet fixture with link column `Risks.project`; 100,000-row generator per sheet for the performance lane; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F021/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F021_FEATURE`
- Targeted command: `cargo xtask test-feature F021`
- Full command: `cargo xtask test-all`
- First failing tests: `join_by_link_column_matches_row_id`, `join_cycle_rejected`, `filter_relative_date_uses_timezone`, `group_aggregates_exclude_hidden_column`, `calculated_field_parse_error_names_field`, `report_rows_100k_p95`, `join_builder_keyboard_add_join`

## Exit criteria

- [ ] Requirement tests SR-S042-01 through SR-S042-07 written first and failing
- [ ] Tasks T083 and T084 complete; UI wired to the real API through the generated `ReportsApi` client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/reports/ReportPage.tsx` mounted at `/w/:workspaceId/reports/:reportId` and `/w/:workspaceId/reports/:reportId/edit`
- [ ] Handoff evidence recorded in the F021 ticket
