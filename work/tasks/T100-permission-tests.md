---
id: T100
type: task
status: planned
parent_epic: E005
parent_feature: F025
parent_story: S050
depends_on: [S050]
owned_paths: [testing/features/F025/requirements/**, testing/features/F025/accessibility/**, testing/features/F025/api/**, testing/features/F025/performance/**]
feature_flag: F025_FEATURE
branch: t100-permission-tests
started_at: null
finished_at: null
---

# T100 — Permission tests

## Identity

- Parent story: `S050` PDF/CSV export
- Owner: platform
- Branch: `t100-permission-tests`
- Decision references: `docs/architecture-decisions.md` sections 3, 6, 7; `docs/capability-contracts.md` row F025

## Objective

Prove that no drill result and no exported byte crosses a permission boundary: build the fixture actors, the permission-negative suite, the requirement traceability lane, and the accessibility checks for the new surfaces.

## Specification

- Owned paths: `testing/features/F025/{requirements/cases.md, api/permission_tests.rs, api/scope_bytes_tests.rs, accessibility/report_exports.a11y.spec.ts, performance/drill_bench.rs}` plus the fixture factory `testing/fixtures/report_exports.rs`
- Contract/input: actors `exporter` (report-viewer plus resource-exporter), `viewer` (report-viewer only), `restricted` (no read on sheet "Risks"), `tenant-admin`, share-link guest, and a tenant B actor; report "Portfolio status" with hidden column `Budget.margin`, an `aggregate_policy: owner` variant, and dashboard "Weekly review" holding one widget the viewer cannot read.
- Output/behavior: the suite asserts that drill marks restricted sheets `denied` with no cells, no deep link, and no row query issued; that CSV, XLSX, and PDF outputs contain neither the hidden column header nor any of its values when read back byte by byte; that a dashboard PDF requested by `restricted` renders the unreadable widget as a title-only tile; that `viewer` receives `403 denied` on both export creators while still being allowed to drill; that a share-link guest may drill but never export; that a non-requester download is `403 denied` and a `tenant-admin` download succeeds and is audited; that every tenant B id returns `404 not_found` on drill, status, and download; that a `scope_key` mismatch aborts the render; and that `drill-through.opened.v1`, `report-export.requested.v1`, `report-export.completed.v1`, and `report-export.failed.v1` carry the expected payload fields. Every database assertion in the suite reads through `ReportExportRepository` named queries rather than inline SQL: the tests contain no SQL string, `sqlx::query*` call, or connection, so `cargo xtask check-persistence` passes over the F025 lanes. The requirement lane maps FR-F025-01 through FR-F025-13 and NFR-F025-01 through NFR-F025-04 to lanes and cases, and the accessibility lane covers the drill panel, export dialog, export center, and tagged PDF structure.
- Dependencies: T097 drill route, T098 export routes and worker, T099 UI surfaces; F003 authorization engine; F036 share links; the deterministic render stub and MinIO prefix per worker.
- Feature flag: `F025_FEATURE` gates the suite; every case runs in targeted and full modes with a tenant per test.

## TDD

- Failing test first: `testing/features/F025/api/permission_tests.rs::viewer_without_exporter_role_denied_on_both_creators`, `::share_link_guest_may_drill_but_not_export`, `::non_requester_download_denied_and_audited`, `::tenant_admin_download_allowed`, `::foreign_tenant_export_status_not_found`, `::foreign_tenant_report_drill_not_found`; `testing/features/F025/api/scope_bytes_tests.rs::csv_bytes_exclude_hidden_column`, `::xlsx_bytes_exclude_hidden_column`, `::pdf_text_excludes_restricted_rows`, `::dashboard_pdf_hides_unreadable_widget_payload`, `::render_aborts_on_scope_key_mismatch`; `testing/features/F025/performance/drill_bench.rs::group_drill_p95_under_900ms`, `::row_drill_p95_under_400ms`
- Targeted command: `cargo xtask test-feature F025`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/report_exports.rs` builds the six actors, both tenants, the 100,000-row snapshot, the 250,000-row generator, and the dashboard with a denied widget; axe-core through Playwright; evidence written to `testing/evidence/F025/`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Every FR and NFR id in the ticket appears in the requirements lane with a lane assignment
- [ ] Permission-negative, tenant-isolation, byte-level scope, accessibility, and drill performance gates pass in targeted and full modes
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S050
- [ ] `finished_at` recorded
