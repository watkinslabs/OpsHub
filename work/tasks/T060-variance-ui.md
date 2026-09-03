---
id: T060
type: task
status: planned
parent_epic: E003
parent_feature: F015
parent_story: S030
depends_on: [T059]
owned_paths: [apps/web/src/features/templates/**, testing/features/F015/frontend/**, testing/features/F015/e2e/**, testing/features/F015/accessibility/**]
feature_flag: F015_FEATURE
branch: t060-variance-ui
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` section 6
- Capability contract: `docs/capability-contracts.md` row F015

# T060 — Variance UI

## Identity

- Parent story: `S030` Baseline compare
- Owner: platform
- Branch: `t060-variance-ui`
- Decision references: `docs/architecture-decisions.md` section 6; `docs/capability-contracts.md` row F015

## Objective

Build the baseline list, capture dialog, and variance panel with the Gantt overlay hook, and prove the whole template-to-baseline path with E2E and accessibility tests.

## Specification

- Owned paths: `apps/web/src/features/templates/{BaselineList.tsx, CaptureBaselineDialog.tsx, VariancePanel.tsx, VarianceRow.tsx, useBaselineOverlay.ts}`
- Contract/input: generated `TemplatesApi` client methods `captureBaseline`, `listBaselines`, `getVariance`; route `/w/:workspaceId/sheets/:sheetId/baselines`; search param `?baseline_id=` read by `useBaselineOverlay` and consumed by the F012 `GanttChart` overlay slot.
- Output/behavior: `BaselineList` shows name, captured date, row count, and measures with `Compare` and admin-only `Delete`; `CaptureBaselineDialog` validates name and measure selection and shows the pending row until `201`; `VariancePanel` renders totals cards, a virtualized table with frozen row name, status chips carrying text (`Slipped +3d`), a status filter, and `Open in Gantt` that sets `?baseline_id=`; states: loading, empty (`No baselines yet`), error with correlation ID, denied (capture hidden for non-admins), stale, offline; telemetry `baseline_captured`, `variance_viewed`.
- Dependencies: T059 routes; F012 Gantt overlay slot; F005 workspace shell navigation.
- Feature flag: `F015_FEATURE` read through the flag hook; routes and the Gantt menu item are not registered when off.

## TDD

- Failing test first: `testing/features/F015/frontend/BaselineList.test.tsx::lists_baselines_with_row_count`, `::hides_capture_for_non_admin`, `CaptureBaselineDialog.test.tsx::validates_name_and_measures`, `VariancePanel.test.tsx::variance_panel_shows_totals`, `::status_filter_narrows_rows`, `::open_in_gantt_sets_baseline_param`; `testing/features/F015/e2e/templates.spec.ts::provision_from_builtin_then_capture_baseline_and_view_variance`, `::failed_provisioning_shows_rollback`, `::editor_cannot_provision_or_capture`; `testing/features/F015/accessibility/templates.a11y.spec.ts::template_pages_have_no_serious_axe_violations`, `::variance_table_keyboard_navigation`
- Targeted command: `cargo xtask test-feature F015`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the baseline fixture; Playwright uses the real API and in-process worker against a seeded tenant with the built-in catalog

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component, E2E, and accessibility lanes pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S030
- [ ] `finished_at` recorded
