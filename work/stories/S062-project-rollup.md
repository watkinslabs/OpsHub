---
id: S062
type: story
status: planned
parent_epic: E007
parent_feature: F031
depends_on: [S061]
owned_paths: [crates/domain/src/portfolios/**, services/api/src/portfolios/**, services/worker/src/portfolios/**, apps/web/src/features/portfolios/**, testing/features/F031/**]
feature_flag: F031_FEATURE
branch: s062-project-rollup
started_at: null
finished_at: null
---

# S062 — Project rollup

## Identity

- Parent feature: `F031` Portfolio rollups
- Owner: platform
- Branch: `s062-project-rollup`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6, 7; `docs/capability-contracts.md` row F031

## Vertical slice

As a portfolio viewer, I want to open a portfolio and see a refreshed rollup of every member project's status, schedule, budget, risk, value, and health with source IDs, last refresh time, and missing or restricted state, so that I can review the portfolio and drill into projects I am allowed to open.

## Requirements

- **SR-S062-01:** `POST /api/v1/portfolios/{id}/refresh` enqueues `portfolio.rollup.refresh`, returns `202 { job_id, requested_version }` within 2 seconds, sets `rollup_state: refreshing`, and returns `409 conflict` while a job for the portfolio is queued or running (FR-F031-06).
- **SR-S062-02:** The worker computes one `RollupRow` per member project with `status`, `schedule.variance_days` against the latest F015 baseline, `budget.variance_pct`, `risk_level`, `value`, and `health`, each with `state` in {`ok`, `missing`, `denied`, `error`}, and stores the snapshot in `portfolio_rollups` with `source_versions` and `computed_at` (FR-F031-07, FR-F031-08).
- **SR-S062-03:** A member project that is soft-deleted appears with `state: missing` and `reason: project_deleted`; a mapped column absent from a project yields `state: missing` on that measure only (FR-F031-05, FR-F031-14).
- **SR-S062-04:** `GET /api/v1/portfolios/{id}/rollup` returns the newest snapshot filtered for the actor: unreadable projects become `state: denied` with null name and values, totals exclude them, `excluded_project_count` is set, and `stale` is true when `computed_at` is older than `stale_after_seconds` (FR-F031-09).
- **SR-S062-05:** The scheduler refreshes `scheduled` portfolios every 15 minutes only when a member sheet version changed since `last_refresh_at`; a completed refresh publishes `portfolio.rollup-refreshed.v1` and a failed job after 3 retries dead-letters and sets `last_refresh_error` (FR-F031-10, FR-F031-11, NFR-F031-04).
- **SR-S062-06:** `PortfolioPage` renders `RollupTable` with totals, `Last refreshed`, stale badge, administrator-only `Refresh`, drill links only for `ok` rows, and loading, empty, error, refreshing, failed, denied, and stale states with keyboard navigation and a refresh live region (FR-F031-13, NFR-F031-03).
- **SR-S062-07:** Rollup read for 500 projects and refresh of 100 projects meet NFR-F031-01.

## Surfaces

- Infrastructure/container: worker job registration in `services/worker/src/portfolios/mod.rs` (F004 JetStream consumer)
- Rust service/API: `crates/domain/src/portfolios/{rollup.rs, measures.rs, service_rollup.rs}`; `services/api/src/portfolios/handlers_rollup.rs`; `services/worker/src/portfolios/{refresh_job.rs, scheduler.rs}`
- Data/migration: none new; uses `portfolio_rollups` from S061
- React/UI: `apps/web/src/features/portfolios/{PortfolioListPage.tsx, PortfolioPage.tsx, PortfolioHeader.tsx, RollupTable.tsx, RollupTotals.tsx, MeasureCell.tsx, ProjectPicker.tsx, NewPortfolioDialog.tsx, MeasureMappingEditor.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: three provisioned projects with one restricted for the viewer; 500-project generator for the performance lane; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F031/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F031_FEATURE`
- Targeted command: `cargo xtask test-feature F031`
- Full command: `cargo xtask test-all`
- First failing tests: `refresh_enqueues_and_acks_under_two_seconds`, `rollup_rows_preserve_source_ids_and_versions`, `rollup_marks_missing_column_measure`, `rollup_hides_denied_project_for_viewer`, `rollup_table_shows_stale_badge`, `rollup_read_500_projects_p95`

## Exit criteria

- [ ] Requirement tests SR-S062-01 through SR-S062-07 written first and failing
- [ ] Tasks T123 and T124 complete; UI wired to the real API through the generated client
- [ ] Unit, API, worker, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/portfolios/PortfolioPage.tsx` mounted at `/w/:workspaceId/portfolios/:portfolioId`, and `services/worker/src/portfolios/refresh_job.rs` registered in `services/worker/src/main.rs`
- [ ] Handoff evidence recorded in the F031 ticket
