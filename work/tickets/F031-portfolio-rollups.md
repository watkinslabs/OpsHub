---
id: F031
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M6
parent_epic: E007
depends_on: [F015, F021]
blocks: [F032]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/portfolios/**, services/api/src/portfolios/**, services/worker/src/portfolios/**, apps/web/src/features/portfolios/**, services/api/migrations/*_portfolios_*.sql, testing/features/F031/**]
feature_flag: F031_FEATURE
flag_default: off
branch: f031-portfolio-rollups
started_at: null
finished_at: null
---

# F031 — Portfolio rollups

## 1. Identity and dates

- Branch: `f031-portfolio-rollups`
- Capability area: project and portfolio management (spec 5.7 PPM-02, PPM-04; low-level bullet "Portfolio roll-up preserves source project IDs, last refresh, missing-data state, and permission boundaries"; 5.6 REPORT-04 portfolio summaries)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7, 9; `docs/capability-contracts.md` row F031
- Aggregate: `portfolio`
- Module slug: `portfolios`

## 2. Requirement specification

### Problem and user outcome

A PMO runs weekly reviews across many projects that were provisioned from F015 templates. Today each project lives in its own sheet and the PMO consolidates status by hand. They need a portfolio record that lists member projects and a rollup projection that reads each project's status, schedule, budget, risk, value, and health through the permission-aware F021 query layer, remembers when it was computed, and says plainly when a value is missing or hidden.

As a portfolio administrator, I want to group projects into a portfolio and refresh a rollup that carries source project IDs, refresh time, and missing-data state, so that leadership sees one trustworthy summary and can drill into any project they are allowed to open.

### Functional requirements

- **FR-F031-01:** An actor with the `portfolio-admin` role on a workspace can create a portfolio with `name` (1–200 chars, unique per workspace case-insensitively), `workspace_id`, optional `description` (≤ 4,000 chars), `refresh_policy` (`manual` or `scheduled`), and `stale_after_seconds` (60–86,400, default 900); the response returns a UUIDv7 `id` and `version` 1; a duplicate name returns `conflict` with `field_errors.name`.
- **FR-F031-02:** `GET /api/v1/portfolios` lists portfolios the actor may read, paged by opaque cursor with `limit` 1–100, filter `workspace_id`, and sort `name` or `updated_at`; `GET /api/v1/portfolios/{id}` returns the portfolio with `project_count`, `last_refresh_at`, and `rollup_state` (`never`, `fresh`, `stale`, `refreshing`, `failed`).
- **FR-F031-03:** `PATCH /api/v1/portfolios/{id}` updates `name`, `description`, `refresh_policy`, `stale_after_seconds`, and `measure_mappings` with `If-Match`; a stale version returns `conflict` with `current_version`.
- **FR-F031-04:** `PUT /api/v1/portfolios/{id}/projects` replaces the member set with up to 500 `project_sheet_id` values that must be F015 provisioned project sheets in the same tenant; unknown or foreign-tenant IDs return `invalid` with `field_errors.projects[i]`, and the endpoint records `added` and `removed` IDs in the audit diff.
- **FR-F031-05:** `measure_mappings` maps each rollup measure (`status`, `planned_finish`, `budget_planned`, `budget_actual`, `risk_level`, `value`) to a stable column ID of the project template version; a mapping that references a column absent from a member project yields `state: missing` for that measure on that project, never an error.
- **FR-F031-06:** `POST /api/v1/portfolios/{id}/refresh` enqueues a rollup job, responds `202` within 2 seconds with `job_id`, sets `rollup_state` to `refreshing`, and returns `conflict` if a refresh for the same portfolio is already queued or running.
- **FR-F031-07:** The rollup worker computes, per member project, `status`, `schedule` (`planned_finish`, `baseline_finish`, `variance_days` using the latest F015 baseline), `budget` (`planned`, `actual`, `variance_pct`), `risk_level`, `value`, and `health` (from F032 when present, otherwise `missing`), each carrying `state` in {`ok`, `missing`, `denied`, `error`}, plus portfolio totals for budget and counts by status and health.
- **FR-F031-08:** Every rollup row preserves `project_sheet_id`, `project_name`, `template_version_id`, `source_versions` (sheet version and baseline ID used), and `computed_at`; the portfolio record stores `last_refresh_at`, `last_refresh_duration_ms`, and `last_refresh_error` when the job failed.
- **FR-F031-09:** `GET /api/v1/portfolios/{id}/rollup` returns the latest snapshot filtered to the requesting actor: projects the actor cannot read appear with `state: denied`, `project_name` null, and no measure values, and portfolio totals exclude them and report `excluded_project_count`; the response includes `stale: true` when `computed_at` is older than `stale_after_seconds`.
- **FR-F031-10:** Portfolios with `refresh_policy: scheduled` are refreshed by the worker every 15 minutes when at least one member project changed since `last_refresh_at`; unchanged portfolios are skipped and the skip is recorded in the job run.
- **FR-F031-11:** Every mutation requires `Idempotency-Key` and writes an `audit_events` row; `portfolio.updated.v1` is published for create, update, and membership changes and `portfolio.rollup-refreshed.v1` for every completed refresh with `changed_fields` naming the project IDs whose measures changed.
- **FR-F031-12:** Cross-tenant access to a portfolio by ID returns `not_found`; an actor with only `portfolio-viewer` receives `denied` on every mutation route and can read list, detail, and rollup.
- **FR-F031-13:** The web portfolio page renders the rollup as a table with one row per project, a totals header, a `Last refreshed` timestamp, a stale badge, a `Refresh` action for administrators, and a drill link that opens the project sheet only when the row state is `ok`.
- **FR-F031-14:** Deleting a member project (soft delete in F006) marks its rollup row `state: missing` with `reason: project_deleted` on the next refresh instead of dropping it, until an administrator removes it from the membership set.

### Non-functional requirements

- **NFR-F031-01 Performance:** `GET /rollup` for a portfolio with 500 projects responds in under 500 ms p95 from the stored snapshot; a refresh of 100 projects completes in under 30 seconds; refresh enqueue acknowledges in under 2 seconds (spec section 6).
- **NFR-F031-02 Security/privacy:** every rollup read applies the F021 row-level permission filter per project for the requesting actor; snapshot storage never contains values from projects the computing job could not read as the tenant system actor; cross-tenant and viewer-negative tests are in the harness.
- **NFR-F031-03 Accessibility:** the rollup table is a real `<table>` with column headers, sortable header buttons, and a live region announcing refresh completion; axe reports no serious violations; all actions are keyboard reachable.
- **NFR-F031-04 Reliability/observability:** refresh jobs are idempotent by `(portfolio_id, requested_version)`, retried up to 3 times with exponential backoff, and dead-lettered with `last_refresh_error` set; spans carry `tenant_id`, `portfolio_id`, `job_id`, and `correlation_id`; metric `portfolio_rollup_duration_ms` is exported.

### Scope

Included: portfolio CRUD, membership replacement, measure mappings, on-demand and scheduled rollup refresh, snapshot storage, permission-filtered rollup read, stale state, audit and outbox events, portfolio page with rollup table.

Excluded: health computation and override (F032), portfolio dashboards and charts (F023, F024), portfolio-level baselines (F015), programs as nested portfolios, exports of the rollup (F025), AI portfolio insights (F040).

## 3. UX specification

- Entry points: workspace sidebar `Portfolios`; route `/w/{workspace_id}/portfolios` (list) and `/w/{workspace_id}/portfolios/{portfolio_id}` (rollup); `New portfolio` button for administrators.
- Primary flow: administrator opens `Portfolios`, clicks `New portfolio`, enters name and refresh policy, submits, lands on an empty rollup with `Add projects`; selects provisioned projects from a searchable picker, saves, clicks `Refresh`; the table shows `Refreshing` then fills with status, schedule variance, budget, risk, value, and health columns and `Last refreshed` time.
- Loading: skeleton table with six columns; Empty: `No projects yet` with `Add projects`; Error: banner with `correlation_id` and retry; Success: toast `Rollup refreshed` and live-region announcement; Stale: amber badge `Stale since {time}` next to `Last refreshed`; Refreshing: spinner in header and disabled `Refresh`; Failed: red banner with `last_refresh_error` and `Retry`; Missing: cell shows `Missing` with tooltip reason; Denied: row shows `Restricted project` with no values.
- Permission-denied: viewers see no `Refresh`, `Add projects`, or edit affordances; non-members see the not-found page.
- Responsive: under 768 px the table becomes stacked cards per project with measure labels; totals header collapses into a summary strip.
- Keyboard: arrow keys move through cells, `Enter` on a project name opens the drill link, `R` triggers refresh for administrators, sortable headers are buttons; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062), Lucide icons `Briefcase`, `RefreshCw`, `AlertTriangle`, `Lock`, `ExternalLink`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/portfolios/`: `Portfolio { id, tenant_id, workspace_id, name, description, refresh_policy: RefreshPolicy, stale_after_seconds: u32, measure_mappings: MeasureMappings, last_refresh_at, last_refresh_duration_ms, last_refresh_error, version, audit fields, deleted_at }`, `PortfolioProject { portfolio_id, project_sheet_id, added_at, added_by }`, `RollupSnapshot { portfolio_id, computed_at, requested_version, rows: Vec<RollupRow>, totals: RollupTotals }`, `RollupRow { project_sheet_id, project_name, template_version_id, source_versions, status: Measure<String>, schedule: ScheduleMeasure, budget: BudgetMeasure, risk_level: Measure<String>, value: Measure<Decimal>, health: Measure<HealthColor>, state: RowState }`, `Measure<T> { value: Option<T>, state: MeasureState, reason: Option<String> }`.
- Use cases: `create_portfolio`, `update_portfolio`, `list_portfolios`, `get_portfolio`, `replace_projects`, `request_refresh`, `compute_rollup` (worker), `read_rollup_for_actor`.
- API endpoints (`services/api/src/portfolios/`): `GET /api/v1/portfolios`, `POST /api/v1/portfolios`, `GET /api/v1/portfolios/{id}`, `PATCH /api/v1/portfolios/{id}`, `PUT /api/v1/portfolios/{id}/projects`, `GET /api/v1/portfolios/{id}/rollup`, `POST /api/v1/portfolios/{id}/refresh`. DTOs: `CreatePortfolioRequest`, `UpdatePortfolioRequest`, `ReplaceProjectsRequest { project_sheet_ids: Vec<Uuid> }`, `PortfolioResponse`, `RollupResponse { computed_at, stale, excluded_project_count, totals, rows }`, `RefreshAccepted { job_id, requested_version }`.
- Worker (`services/worker/src/portfolios/`): job `portfolio.rollup.refresh` consumes `{ tenant_id, portfolio_id, requested_version, correlation_id }`; scheduler tick every 15 minutes selects scheduled portfolios with changed members; measures are read through the F021 `ReportQuery` executor as the tenant system actor with `permission_scope: project_sheet`, and F015 `baselines` for `baseline_finish`.
- Events: `portfolio.updated.v1`, `portfolio.rollup-refreshed.v1`; payload per contract conventions with `changed_fields`.
- Authorization: `portfolio-admin` for create, update, membership, refresh; `portfolio-viewer` for reads; per-project visibility resolved with F003 `authz::check(actor, Permission::SheetRead, project_sheet_id)` at read time; explicit deny wins; missing workspace access maps to `not_found`.
- Validation: name 1–200, description ≤ 4,000, projects ≤ 500, `stale_after_seconds` 60–86,400, mappings keyed by the six measure names only. Idempotency via `idempotency_keys` for 24 hours. Concurrency: `If-Match` compared in the update transaction.
- Error mapping: `PortfolioError::NameTaken → 409 conflict`, `PortfolioError::StaleVersion → 409 conflict`, `PortfolioError::RefreshInProgress → 409 conflict`, `PortfolioError::NotFound → 404 not_found`, `PortfolioError::InvalidProject(i) → 400 invalid` with `field_errors.projects[i]`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_portfolios_*.sql` creates `portfolios(id uuid pk, tenant_id uuid not null, workspace_id uuid not null, name text not null, description text, refresh_policy text not null default 'manual', stale_after_seconds int not null default 900, measure_mappings jsonb not null default '{}', last_refresh_at timestamptz, last_refresh_duration_ms int, last_refresh_error text, rollup_state text not null default 'never', version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `portfolio_projects(tenant_id, portfolio_id, project_sheet_id, added_by, added_at, primary key (portfolio_id, project_sheet_id))`, `portfolio_rollups(id uuid pk, tenant_id, portfolio_id, requested_version bigint, computed_at timestamptz not null, duration_ms int, rows jsonb not null, totals jsonb not null, source_versions jsonb not null)`.
- Invariants: unique partial index `portfolios_tenant_workspace_name_idx on (tenant_id, workspace_id, lower(name)) where deleted_at is null`; check `refresh_policy in ('manual','scheduled')`; check `stale_after_seconds between 60 and 86400`; `portfolio_projects.project_sheet_id` foreign key to `sheets(id)` with `on delete restrict`; unique `(portfolio_id, requested_version)` on `portfolio_rollups`; only the newest three snapshots per portfolio are retained by the worker.
- Indexes: `portfolios(tenant_id, workspace_id, updated_at desc)`, `portfolio_projects(project_sheet_id)`, `portfolio_rollups(portfolio_id, computed_at desc)`.
- Audit events: `portfolio.create`, `portfolio.update`, `portfolio.projects.replace` (with `added`/`removed`), `portfolio.refresh.request`, `portfolio.refresh.complete`, `portfolio.refresh.fail`.
- Retention/deletion: soft delete sets `deleted_at`; snapshots older than the three newest are deleted by the worker; migration rollback drops the three tables.

### React/TypeScript

- Routes: `/w/:workspaceId/portfolios`, `/w/:workspaceId/portfolios/:portfolioId` in `apps/web/src/features/portfolios/`; components `PortfolioListPage`, `PortfolioPage`, `PortfolioHeader`, `RollupTable`, `RollupTotals`, `MeasureCell`, `ProjectPicker`, `NewPortfolioDialog`, `MeasureMappingEditor`.
- State: TanStack Query keys `['portfolios', workspaceId, cursor]`, `['portfolio', id]`, `['portfolio-rollup', id]`; refresh mutation polls `['portfolio', id]` every 2 seconds while `rollup_state === 'refreshing'`.
- API client: generated `PortfoliosApi` with `listPortfolios`, `createPortfolio`, `getPortfolio`, `updatePortfolio`, `replaceProjects`, `getRollup`, `requestRefresh`.
- Optimistic updates: membership replace applies locally and rolls back on `invalid` with per-project errors in the picker.
- Telemetry: `portfolio_created`, `portfolio_opened`, `portfolio_projects_replaced`, `portfolio_refresh_requested`, `portfolio_drill_opened` with `portfolio_id` and `project_count`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F031-01 through FR-F031-14 in `testing/features/F031/requirements/cases.md`
- [ ] Failure/edge-case tests: duplicate name, stale version, refresh while refreshing, 501 projects, foreign-tenant project ID, mapping to missing column, deleted member project, failed job after 3 retries
- [ ] Permission-negative and tenant-isolation tests: cross-tenant read returns `not_found`, viewer mutation returns `denied`, rollup hides denied projects and excludes them from totals
- [ ] Rust unit tests: `crates/domain/src/portfolios/` measure state resolution, variance math, totals aggregation, stale computation
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: unique name index, policy check, membership foreign key, snapshot uniqueness, rollback
- [ ] React component tests: `RollupTable`, `PortfolioPage`, `ProjectPicker` states
- [ ] Browser E2E tests: create portfolio, add projects, refresh, stale badge, drill link, viewer read-only
- [ ] Accessibility tests: axe on list and rollup page, keyboard table navigation, refresh announcement
- [ ] Performance/load tests: 500-project rollup read p95 under 500 ms, 100-project refresh under 30 s

### Fast fanout configuration

- Test harness path: `testing/features/F031/`
- Feature flag: `F031_FEATURE`
- Fixture/seed factory: `testing/fixtures/portfolios.rs` builds tenant, workspace, portfolio-admin, portfolio-viewer, foreign tenant, three F015-provisioned projects with baselines (one unreadable by the viewer), and a portfolio with mappings
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC
- Mock/stub contracts: outbox publisher recorded in memory; F021 query executor real against fixture sheets; job queue in-process runner
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F031`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F031/`

## 6. Acceptance criteria

```gherkin
Feature: Portfolio rollups

Scenario: Refresh a portfolio of three projects
  Given portfolio "Q4 launches" with three provisioned projects and measure mappings
  When an administrator requests a refresh
  Then the request is accepted within 2 seconds
  And the rollup rows carry each project_sheet_id, status, variance_days, budget, risk_level, value, and computed_at
  And portfolio.rollup-refreshed.v1 is in the outbox

Scenario: Missing measure is reported, not failed
  Given project "Mobile app" lacks the mapped budget_actual column
  When the rollup is refreshed
  Then the budget measure for "Mobile app" has state missing and the other measures have state ok

Scenario: Viewer cannot see a restricted project
  Given a portfolio-viewer who has no access to project "Merger"
  When they read the rollup
  Then the "Merger" row has state denied and null values
  And totals exclude it and excluded_project_count is 1

Scenario: Viewer cannot mutate
  Given a portfolio-viewer
  When they PUT the project set or POST a refresh
  Then the response is 403 denied and no audit mutation is written

Scenario: Cross-tenant read does not leak
  Given a portfolio in tenant A
  When an administrator from tenant B requests it by id
  Then the response is 404 not_found
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F015 (provisioned project sheets, template versions, baselines), F021 (permission-aware report query executor); decisions sections 2–4, 7; contracts row F031
- Blocks: F032
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: a refresh that reads 500 projects through the report executor can exceed 30 s, so the worker reads projects in batches of 25 with a per-portfolio time budget of 120 s and records partial results with `state: error` rows; snapshot JSON can grow large, so rows are capped at 500 projects and older snapshots are pruned to three; the tenant system actor used for computation must never widen a viewer's access, so denied filtering is applied again at read time.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F015 and F021 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F031/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory with three provisioned projects available in `testing/fixtures/portfolios.rs`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, worker, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and refresh
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F031_FEATURE`, stop the refresh scheduler, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Administrators can create portfolios, add provisioned projects, and refresh a rollup of status, schedule, budget, risk, value, and health with source IDs, last refresh time, and missing-data state; viewers see only projects they may open.
- Migration adds `portfolios`, `portfolio_projects`, and `portfolio_rollups`; rollback drops them. Feature is off by default behind `F031_FEATURE`.
