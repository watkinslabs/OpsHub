---
id: S030
type: story
status: planned
parent_epic: E003
parent_feature: F015
depends_on: [S029]
owned_paths: [crates/domain/src/templates/**, crates/persistence/src/templates/**, services/api/src/templates/**, apps/web/src/features/templates/**, testing/features/F015/**]
feature_flag: F015_FEATURE
branch: s030-baseline-compare
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 9
- Capability contract: `docs/capability-contracts.md` row F015

# S030 — Baseline compare

## Identity

- Parent feature: `F015` Templates and baselines
- Owner: platform
- Branch: `s030-baseline-compare`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6, 9; `docs/capability-contracts.md` row F015

## Vertical slice

As a project manager, I want to capture a named baseline of my sheet's schedule and selected measures and later read the variance row by row and in totals, including as an overlay on the Gantt, so that slippage from the agreed plan is visible and measurable.

## Requirements

- **SR-S030-01:** `POST /api/v1/sheets/{sheet_id}/baselines` writes the selected measures as `baseline_measures` rows (checked against `start|end|duration|effort|cost`) and snapshots start, end, and duration into `baseline_rows` with a `baseline_row_measures` row per measure for every non-deleted row; header, measures, rows and row measures are one `BaselineRepository::capture_baseline_rows` call in one `UnitOfWork`, recording `row_count`, emitting `baseline.captured.v1`, and enforcing the 20-per-sheet limit with `409 conflict` (FR-F015-10).
- **SR-S030-02:** `GET /api/v1/sheets/{sheet_id}/baselines` uses `BaselineRepository::list` cursor paging sorted by `captured_at` and returns each baseline's measures from `baseline_measures`; baselines are immutable and only a `portfolio-admin` can soft-delete one, which cascades to measures, rows, and row measures (FR-F015-11).
- **SR-S030-03:** `GET /api/v1/baselines/{id}/variance` is served by `BaselineRepository::page_variance`, returning per-row start and finish variance in working days on the sheet calendar, measure deltas joined from `baseline_row_measures` to the current cell values, per-row status including `added` and `removed`, and totals aggregated over those rows, paged with `limit` ≤ 500 (FR-F015-12).
- **SR-S030-04:** Baseline mutations require `Idempotency-Key`, write an audit event, and publish through the outbox; cross-tenant baseline access returns `404 not_found` and a `sheet-editor` without `portfolio-admin` capturing a baseline receives `403 denied` (FR-F015-13, FR-F015-14).
- **SR-S030-05:** `BaselineList`, `CaptureBaselineDialog`, and `VariancePanel` render loading, empty, error, denied, stale, and offline states, and `?baseline_id=` drives the F012 Gantt overlay (FR-F015-15).
- **SR-S030-06:** Variance rows carry text labels beside colour, the table is keyboard navigable, and axe reports no serious violations (NFR-F015-03).
- **SR-S030-07:** Capture of a 100,000-row sheet completes under 30 s and a 500-row variance read responds under 500 ms p95 (NFR-F015-01).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/templates/{baseline.rs, variance.rs, service_baseline.rs}` depending only on repository traits; `crates/persistence/src/templates/{mod.rs, baseline_repository.rs}` holding every baseline and variance query; `services/api/src/templates/{handlers_baseline.rs, handlers_variance.rs}`
- Data/migration: none new; uses `baselines`, `baseline_measures`, `baseline_rows`, and `baseline_row_measures` from S029
- React/UI: `apps/web/src/features/templates/{BaselineList.tsx, CaptureBaselineDialog.tsx, VariancePanel.tsx, VarianceRow.tsx, useBaselineOverlay.ts}`
- Mocks/fixtures: sheet with 50 scheduled rows and effort/cost columns; 100,000-row generator for the capture benchmark; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F015/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F015_FEATURE`
- Targeted command: `cargo xtask test-feature F015`
- Full command: `cargo xtask test-all`
- First failing tests: `baseline_capture_snapshots_all_rows`, `baseline_limit_twenty_conflicts`, `variance_reports_slipped_added_removed`, `variance_uses_working_calendar_days`, `variance_panel_shows_totals`, `baseline_capture_100k_under_30s`

## Exit criteria

- [ ] Requirement tests SR-S030-01 through SR-S030-07 written first and failing
- [ ] Tasks T059 and T060 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/templates/VariancePanel.tsx` mounted at `/w/:workspaceId/sheets/:sheetId/baselines` and consumed by the F012 Gantt overlay
- [ ] Handoff evidence recorded in the F015 ticket
