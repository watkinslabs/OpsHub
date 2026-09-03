---
id: S061
type: story
status: planned
parent_epic: E007
parent_feature: F031
depends_on: [F015, F021]
owned_paths: [crates/domain/src/portfolios/**, services/api/src/portfolios/**, services/api/migrations/*_portfolios_*.sql, testing/features/F031/**]
feature_flag: F031_FEATURE
branch: s061-portfolio-setup
started_at: null
finished_at: null
---

# S061 — Portfolio setup

## Identity

- Parent feature: `F031` Portfolio rollups
- Owner: platform
- Branch: `s061-portfolio-setup`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F031

## Vertical slice

As a portfolio administrator, I want to create a portfolio, set its refresh policy and measure mappings, and replace its member projects, so that a governed set of provisioned projects exists before any rollup is computed.

## Requirements

- **SR-S061-01:** `POST /api/v1/portfolios` with `{ name, workspace_id, description?, refresh_policy?, stale_after_seconds? }` creates a `portfolios` row and returns `PortfolioResponse` with version 1 and `rollup_state: never`; a duplicate case-insensitive name in the workspace returns `409 conflict` with `field_errors.name = "taken"` (covers FR-F031-01).
- **SR-S061-02:** `GET /api/v1/portfolios` pages by opaque cursor with `limit` ≤ 100, filters by `workspace_id`, sorts by `name` or `updated_at`, and `GET /api/v1/portfolios/{id}` returns `project_count`, `last_refresh_at`, and `rollup_state` (FR-F031-02).
- **SR-S061-03:** `PATCH /api/v1/portfolios/{id}` requires `If-Match`, accepts `name`, `description`, `refresh_policy`, `stale_after_seconds`, and `measure_mappings`; a stale version returns `409 conflict` with `current_version`, and a mapping with an unknown measure key returns `400 invalid` with `field_errors.measure_mappings` (FR-F031-03, FR-F031-05).
- **SR-S061-04:** `PUT /api/v1/portfolios/{id}/projects` replaces membership with ≤ 500 provisioned project sheet IDs from the same tenant; a foreign or non-project ID returns `400 invalid` with `field_errors.projects[i]`; 501 IDs returns `400 invalid` with `field_errors.projects = "too_many"` (FR-F031-04).
- **SR-S061-05:** Every mutation checks `Idempotency-Key`, writes an audit event (membership audit lists `added` and `removed`), and enqueues `portfolio.updated.v1` in the same transaction (FR-F031-11).
- **SR-S061-06:** A `portfolio-viewer` receives `403 denied` on POST, PATCH, and PUT routes; a foreign-tenant actor receives `404 not_found` on every route (FR-F031-12).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/portfolios/{mod.rs, portfolio.rs, mappings.rs, errors.rs, service.rs}`; `services/api/src/portfolios/{mod.rs, routes.rs, handlers_portfolio.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_portfolios_create_tables.sql` creating `portfolios`, `portfolio_projects`, `portfolio_rollups` with the indexes from ticket section 4
- React/UI: none in this story (S062 and T123 cover UI)
- Mocks/fixtures: `testing/fixtures/portfolios.rs` tenant A and B, portfolio-admin, portfolio-viewer, three provisioned project sheets; in-memory outbox recorder

## TDD harness

- Test path: `testing/features/F031/api/` and `testing/features/F031/database/`
- Feature flag: `F031_FEATURE`
- Targeted command: `cargo xtask test-feature F031`
- Full command: `cargo xtask test-all`
- First failing tests: `portfolio_create_returns_version_one`, `portfolio_duplicate_name_conflicts`, `portfolio_replace_projects_rejects_foreign_sheet`, `portfolio_replace_projects_over_limit_invalid`, `portfolio_viewer_mutation_denied`, `portfolio_cross_tenant_not_found`

## Exit criteria

- [ ] Requirement tests SR-S061-01 through SR-S061-06 written first and failing
- [ ] Tasks T121 and T122 complete; T121 schema verified and T122 refresh job consuming membership from this story
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/portfolios/routes.rs` mounted in `services/api/src/router.rs` behind `F031_FEATURE`
- [ ] Handoff evidence recorded in the F031 ticket
