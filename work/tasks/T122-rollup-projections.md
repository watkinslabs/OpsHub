---
id: T122
type: task
status: planned
parent_epic: E007
parent_feature: F031
parent_story: S061
depends_on: [T121]
owned_paths: [crates/domain/src/portfolios/**, services/api/src/portfolios/**, services/worker/src/portfolios/**, testing/features/F031/api/**, testing/features/F031/requirements/**]
feature_flag: F031_FEATURE
branch: t122-rollup-projections
started_at: null
finished_at: null
---

# T122 — Rollup projections

## Identity

- Parent story: `S061` Portfolio setup
- Owner: platform
- Branch: `t122-rollup-projections`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 7; `docs/capability-contracts.md` row F031

## Objective

Implement the portfolio domain service, the seven portfolio HTTP routes, and the worker refresh job that projects each member project's measures into a stored rollup snapshot.

## Specification

- Owned paths: `crates/domain/src/portfolios/{mod.rs, portfolio.rs, mappings.rs, rollup.rs, measures.rs, errors.rs, service.rs, service_rollup.rs}`, `services/api/src/portfolios/{mod.rs, routes.rs, handlers_portfolio.rs, handlers_rollup.rs, dto.rs}`, `services/worker/src/portfolios/{mod.rs, refresh_job.rs, scheduler.rs}`
- Contract/input: `CreatePortfolioRequest { name, workspace_id, description?, refresh_policy?, stale_after_seconds? }`, `UpdatePortfolioRequest { name?, description?, refresh_policy?, stale_after_seconds?, measure_mappings? }`, `ReplaceProjectsRequest { project_sheet_ids }`, list query `{ cursor?, limit?, workspace_id?, sort? }`; headers `Idempotency-Key`, `If-Match`; job payload `{ tenant_id, portfolio_id, requested_version, correlation_id }`.
- Output/behavior: routes `GET/POST /api/v1/portfolios`, `GET/PATCH /api/v1/portfolios/{id}`, `PUT /api/v1/portfolios/{id}/projects`, `GET /api/v1/portfolios/{id}/rollup`, `POST /api/v1/portfolios/{id}/refresh` return `PortfolioResponse`, `RollupResponse`, or `RefreshAccepted` per ticket section 4; the job reads each project through the F021 `ReportQuery` executor in batches of 25, resolves `Measure` states (`ok`, `missing`, `denied`, `error`), computes `variance_days` against the latest F015 baseline and `variance_pct` for budget, writes `portfolio_rollups`, prunes to three snapshots, sets `rollup_state` and `last_refresh_*`, and publishes `portfolio.rollup-refreshed.v1`; the scheduler ticks every 15 minutes and enqueues `scheduled` portfolios whose member sheet versions changed; `read_rollup_for_actor` re-filters rows with F003 `authz::check` and sets `stale`; errors map per ticket section 4; events `portfolio.updated.v1` on create, update, and membership.
- Dependencies: T121 schema; F003 `authz::require(actor, Permission::PortfolioAdmin, workspace)`; F004 outbox writer and JetStream job transport; F015 `provisioning_runs` and `baselines`; F021 query executor.
- Feature flag: `F031_FEATURE` gates router mounting and job registration.

## TDD

- Failing test first: `testing/features/F031/api/portfolio_tests.rs::portfolio_create_returns_version_one`, `::portfolio_duplicate_name_conflicts`, `::portfolio_replace_projects_rejects_foreign_sheet`, `::portfolio_viewer_mutation_denied`, `::portfolio_cross_tenant_not_found`; `testing/features/F031/api/rollup_tests.rs::refresh_enqueues_and_acks_under_two_seconds`, `::refresh_while_refreshing_conflicts`, `::rollup_rows_preserve_source_ids_and_versions`, `::rollup_marks_missing_column_measure`, `::rollup_hides_denied_project_for_viewer`, `::scheduled_refresh_skips_unchanged_portfolio`
- Targeted command: `cargo xtask test-feature F031`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/portfolios.rs` tenants A and B, admin, viewer, three provisioned projects with baselines; in-memory outbox recorder; in-process job runner

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` and job registered in `services/worker/src/main.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S061
- [ ] `finished_at` recorded
