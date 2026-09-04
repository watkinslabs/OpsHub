---
id: F015
type: feature
status: planned
priority: P1
owner: platform
estimate: 13
target_milestone: M2
parent_epic: E003
depends_on: [F012, F013, F014]
blocks: [F031]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/templates/**, crates/persistence/src/templates/**, services/api/src/templates/**, services/worker/src/templates/**, apps/web/src/features/templates/**, services/api/migrations/*_templates_*.sql, testing/features/F015/**]
feature_flag: F015_FEATURE
flag_default: off
branch: f015-templates-and-baselines
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 7, 9
- Capability contract: `docs/capability-contracts.md` row F015

# F015 — Templates and baselines

## 1. Identity and dates

- Branch: `f015-templates-and-baselines`
- Capability area: project standardization (spec 5.7 PPM-01, PPM-04 and the template-version and baseline bullets, 5.1 WORK-04 baselines and schedule variance, 5.11 Control Center template versions, section 8 MVP scenario "creates a workspace and project from a template")
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 7, 9; `docs/capability-contracts.md` row F015
- Aggregate: `project-template`
- Module slug: `templates`

## 2. Requirement specification

### Problem and user outcome

Every new project is rebuilt by hand: someone copies a sheet, re-creates columns, re-links dependencies, rebuilds the intake form, and forgets the views. PMOs cannot say which structure a project came from, and once the plan is running nobody can tell how far it drifted from what was agreed. Teams need governed, versioned project templates that provision a complete project in one asynchronous step, a catalog of starter templates for common use cases, and named baselines against which the current schedule is measured.

As a portfolio admin, I want to publish a template version, provision a project from it into a workspace with a start date, and later capture a baseline and read the variance, so that projects start standardized and drift is visible.

### Functional requirements

- **FR-F015-01:** A `portfolio-admin` can create a project template with `name` (1–120 chars, unique per tenant case-insensitive), `category` (one of `pmo`, `it`, `incidents`, `onboarding`, `change`, `vendors`, `marketing`, `crm`, `budget`, `compliance`, `custom`), `description` (≤ 2,000 chars), and `tags` (≤ 10, service-enforced, each stored as a `project_template_tags` row and unique per template case-insensitively); the response returns a UUIDv7 `id`, `version` 1, the tags read back from those rows, and no published version. The catalog filters by tag through `project_template_tags`.
- **FR-F015-02:** `POST /api/v1/project-templates/{id}/versions` accepts a `TemplateManifest` JSON document with `sheets[] { key, name, columns[], schedule_settings, default_rows[] (hierarchy by parent key, dates as offsets in working days from the project start), dependencies[] (predecessor_key, successor_key, type FS|SS|FF|SF, lag_days) }`, `forms[]`, `workflows[]`, `reports[]`, `dashboard`, `roles[] { role, placeholder }`, and `metadata`; the version is created as `draft` with `version_number` = previous + 1, or `400 invalid` with `field_errors.manifest.<path>` when a key reference, column type, or dependency is invalid.
- **FR-F015-03:** Manifest limits are enforced at validation: ≤ 20 sheets, ≤ 500 columns per sheet, ≤ 5,000 default rows in total, ≤ 20,000 dependencies, ≤ 2 MB serialized; exceeding any returns `400 invalid` with the limit name in `field_errors`.
- **FR-F015-04:** Publishing a draft version (`status: published` via the versions route with `action: publish`) makes it immutable, sets `published_at` and `current_version_id` on the template, and emits `template.published.v1`; any attempt to modify a published version returns `409 conflict` with `field_errors.status = "immutable"`; editing after publication creates a new draft.
- **FR-F015-05:** The migration seeds ten built-in templates (`is_builtin = true`), one per category PMO, IT, incidents, onboarding, change, vendors, marketing, CRM, budget, and compliance, each with a published version containing at least one sheet with schedule settings, default rows, at least one dependency, one intake form, and one card view; built-ins are listable and provisionable by every tenant, cannot be edited in place, and `POST /api/v1/project-templates` with `copy_from` clones a built-in into a tenant-owned draft.
- **FR-F015-06:** `POST /api/v1/project-templates/{id}/provision` with `{ version_id, workspace_id, project_name, start_date, role_assignments: { role: principal_id }, options: { include_forms, include_views } }` creates a `provisioning_runs` row in status `queued`, enqueues a JetStream job, and returns `202` with the run `id` within 2 s; a draft `version_id` returns `400 invalid` with `field_errors.version_id = "not_published"`.
- **FR-F015-07:** The worker executes the run as ordered steps `sheets`, `columns`, `rows`, `schedule_settings`, `dependencies`, `views`, `forms`, `roles`, one `provisioning_run_steps` row per step claimed and advanced individually; idempotency is declarative — every created object is written to `provisioning_run_artifacts` under `unique (run_id, step, item_key)`, so a replayed step re-reads the existing artifact row instead of creating a second object; default-row dates are resolved as `start_date + offset` on the sheet's working calendar (F011); dependencies call the F012 engine; views call F013; forms call F014 and are created as drafts; `workflows`, `reports`, and `dashboard` are `provisioning_run_steps` rows set to status `skipped` with `reason = 'module_unavailable'` until F018, F021, and F023 exist.
- **FR-F015-08:** A failed step retries up to 3 times with exponential backoff, its `attempt` counter incremented on the step row; on final failure the run moves to `failed`, every `provisioning_run_artifacts` row is read back ordered by `created_at desc` and its object soft-deleted in that reverse order (each step row set to `rolled_back`), and `provisioning.failed.v1` is emitted with `error_code` and the failing step; a completed run emits `project.provisioned.v1` with `created_ids` assembled from the artifact rows and grouped by `object_kind`.
- **FR-F015-09:** `GET /api/v1/provisioning-runs/{id}` returns `status` (`queued|running|completed|failed|rolled_back`), one `{ step, status, started_at, finished_at, created_count, error }` entry per `provisioning_run_steps` row in step order, `created_ids` (sheet, form, view IDs) still grouped by kind but assembled from `provisioning_run_artifacts`, `correlation_id`, and `version`; polling by a user without access to the target workspace returns `404 not_found`.
- **FR-F015-10:** `POST /api/v1/sheets/{sheet_id}/baselines` with `{ name (1–120, unique per sheet), measures: subset of [start, end, duration, effort, cost] }` writes one `baseline_measures` row per selected measure — the subset is a checked set of rows, not an array — and snapshots every non-deleted row's start, end, and duration into `baseline_rows` with one `baseline_row_measures` row per selected measure column, all in one transaction; it records `row_count` and `captured_at`, emits `baseline.captured.v1`, and returns `201`; a 21st baseline on a sheet returns `409 conflict` with `field_errors.name = "limit"`.
- **FR-F015-11:** `GET /api/v1/sheets/{sheet_id}/baselines` lists baselines with cursor paging and `sort=captured_at`; a baseline is immutable and can only be soft-deleted by a `portfolio-admin`.
- **FR-F015-12:** `GET /api/v1/baselines/{id}/variance` returns per row `{ row_id, baseline_start, current_start, start_variance_days, baseline_end, current_end, finish_variance_days, measures: { name: { baseline, current, delta } }, status: on_track|slipped|early|added|removed }` with day counts computed on the sheet working calendar, plus totals `{ rows_slipped, rows_early, rows_added, rows_removed, max_finish_variance_days }`, paged with `limit` ≤ 500; the `measures` map is built by joining `baseline_row_measures` to the current cell values, and the totals are SQL aggregates over those rows.
- **FR-F015-13:** Every mutation requires `Idempotency-Key` and `If-Match` where a version exists, writes an `audit_events` row, and publishes its event through the outbox in the same transaction; provisioning steps write one audit event per created object with the run ID as correlation.
- **FR-F015-14:** Cross-tenant access to a template, version, run, or baseline returns `404 not_found`; built-in templates are readable by every tenant but `PATCH` or version creation on a built-in returns `403 denied`; a `sheet-editor` without `portfolio-admin` calling provision or baseline capture receives `403 denied`.
- **FR-F015-15:** The web app provides a template catalog with category filter, a template detail page with the manifest summary and version history, a provision dialog with workspace, name, start date, and role pickers, a run status page with live step progress rendered from the per-step rows, a baseline list with capture dialog, and a variance panel that also drives the F012 Gantt baseline overlay through `?baseline_id=`.

### Non-functional requirements

- **NFR-F015-01 Performance:** provision request acknowledged under 2 s p95; a 500-row template with 200 dependencies completes provisioning under 60 s; baseline capture of a 100,000-row sheet completes under 30 s as a single transaction; variance read of 500 rows responds under 500 ms p95 (spec section 6).
- **NFR-F015-02 Security/privacy:** every query carries a `tenant_id` predicate; built-in template manifests contain no tenant data; role placeholders resolve only to principals in the target tenant; manifests are validated as data and never evaluated; cross-tenant, guest, and role-negative tests are part of the harness.
- **NFR-F015-03 Accessibility:** catalog, detail, provision dialog, run status, and variance panel meet WCAG 2.2 AA; step progress is announced through a live region; variance colors carry text labels and meet 4.5:1 contrast; `prefers-reduced-motion` disables progress animation.
- **NFR-F015-04 Reliability/observability:** provisioning jobs are idempotent per step, retried with backoff, dead-lettered after 3 failures with the run marked `failed`; metrics `provisioning_run_duration_ms`, `provisioning_step_failures_total`, `baseline_capture_rows`; spans carry `tenant_id`, `template_id`, `run_id`, `correlation_id`.

### Scope

Included: template CRUD, manifest validation, draft/publish versions, built-in catalog seed and copy, provisioning API, worker job with ordered idempotent steps, retry and rollback, run polling, baseline capture and list, variance calculation, catalog/provision/status/baseline/variance UI, Gantt overlay hook.

Excluded: workflow, report, and dashboard instantiation (F018, F021, F023), portfolio roll-up of provisioned projects (F031), stage gates and intake governance (F032), template marketplace or cross-tenant sharing, baseline auto-capture on schedule, resource baselines (F033).

## 3. UX specification

- Entry points: workspace `New project from template` button; route `/templates` (catalog), `/templates/{template_id}`, `/provisioning-runs/{run_id}`, sheet header `Baselines` menu at `/w/{workspace_id}/sheets/{sheet_id}/baselines`; Gantt toolbar `Compare to baseline`.
- Primary flow: open catalog, filter `PMO`, open `Standard project`, click `Provision`, choose workspace `Ops`, name `Q4 launch`, start date `2026-10-05`, assign `Project manager` role, submit; the status page shows steps completing (`Sheets 2/2`, `Rows 120/120`, `Dependencies 34/34`), then `Open project`; later open the sheet, `Baselines`, `Capture baseline` named `Plan of record`, then open the Gantt with `Compare to baseline` and read slipped rows in the variance panel.
- Loading: catalog card skeletons, status page step skeletons; Empty: `No templates yet` with `Create` or `Browse built-ins`; Error: banner with `correlation_id` and retry; Failed run: red step with error code, `Rolled back` badge, `Retry provisioning` action; Success: toast `Project provisioned` with link; Stale: `Template changed` banner; Offline: provision button disabled with badge.
- Permission-denied: non-admins see the catalog read-only with `Provision` hidden and an explanation; users outside the workspace see not-found for runs and baselines.
- Responsive: catalog grid collapses to one column under 640 px; variance table scrolls horizontally with the row name frozen.
- Keyboard: catalog cards are focusable with `Enter` to open; provision dialog traps focus; status steps are a list with `aria-current` on the running step; variance table supports arrow navigation and `Enter` to open the row.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `LayoutTemplate`, `Rocket`, `ListChecks`, `Flag`, `GitCompare`, `AlertTriangle`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Templates.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/templates/`: `ProjectTemplate { id, tenant_id, name, category: TemplateCategory, description, tags, is_builtin, current_version_id, version, audit fields, deleted_at }`, `TemplateVersion { id, template_id, version_number, status: VersionStatus, manifest: TemplateManifest, manifest_bytes, published_at, published_by, created_by, created_at }`, `TemplateManifest { sheets: Vec<SheetSpec>, forms: Vec<FormSpec>, workflows: Vec<RefSpec>, reports: Vec<RefSpec>, dashboard: Option<RefSpec>, roles: Vec<RoleSpec>, metadata: Metadata }`, `SheetSpec { key, name, columns: Vec<ColumnSpec>, schedule_settings: Option<ScheduleSpec>, default_rows: Vec<RowSpec>, dependencies: Vec<DependencySpec> }`, `ProvisioningRun { id, tenant_id, template_version_id, workspace_id, project_name, start_date, status: RunStatus, error_code, correlation_id, version }` with `StepResult` rows loaded from `provisioning_run_steps` and `RunArtifact` rows from `provisioning_run_artifacts` (`CreatedIds` is a response-shaping projection grouped by `object_kind`, never a stored column), `Baseline { id, tenant_id, sheet_id, name, captured_at, captured_by, row_count, version }` with its selected `Measure` set loaded from `baseline_measures`, `BaselineRow { baseline_id, row_id, start, end, duration_days }` with its values loaded from `baseline_row_measures` as `(measure, value)` rows, `VarianceRow`, `VarianceTotals`. `ProjectTemplate.tags` is a `Vec<Tag>` loaded from `project_template_tags`.
- Use cases: `create_template`, `copy_builtin`, `list_templates`, `get_template`, `create_version`, `publish_version`, `validate_manifest`, `request_provision`, `get_run`, `capture_baseline`, `list_baselines`, `compute_variance`; worker in `services/worker/src/templates/`: `provision_job.rs` with `run_step(step, ctx)`, `rollback_run`, and a `StepExecutor` trait implemented by `SheetsStep`, `ColumnsStep`, `RowsStep`, `ScheduleStep`, `DependenciesStep`, `ViewsStep`, `FormsStep`, `RolesStep`; the worker holds no SQL of its own — it calls the repositories below and the F006/F007/F011/F012/F013/F014 use cases, and each step's writes (the step row, the objects it creates, and their artifact rows) run in one `UnitOfWork` so a failed step rolls back atomically.
- Persistence (`crates/persistence/src/templates/`): `ProjectTemplateRepository` owns `project_templates` and `project_template_tags`; `TemplateVersionRepository` owns `template_versions`; `ProvisioningRunRepository` owns `provisioning_runs`, `provisioning_run_steps`, and `provisioning_run_artifacts`; `BaselineRepository` owns `baselines`, `baseline_measures`, `baseline_rows`, and `baseline_row_measures`. Each implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds named queries `list_with_builtins(tenant_id, category, cursor)`, `next_version_number(template_id)`, `publish_version(version_id)`, `claim_step(run_id, step)`, `record_artifact(run_id, step, item_key, object)`, `list_artifacts_for_rollback(run_id)`, `capture_baseline_rows(baseline_id, rows)`, `page_variance(baseline_id, cursor, limit)`; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. Baseline capture (header, measures, rows, row measures) runs in one `UnitOfWork` that owns the transaction, as does each provisioning step. Per decision 2.1 the use cases above depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/templates`, `services/api/src/templates`, or `services/worker/src/templates`.
- API endpoints (`services/api/src/templates/`): `GET /api/v1/project-templates`, `POST /api/v1/project-templates`, `GET /api/v1/project-templates/{id}`, `POST /api/v1/project-templates/{id}/versions`, `POST /api/v1/project-templates/{id}/provision`, `GET /api/v1/provisioning-runs/{id}`, `POST /api/v1/sheets/{sheet_id}/baselines`, `GET /api/v1/sheets/{sheet_id}/baselines`, `GET /api/v1/baselines/{id}/variance`. DTOs: `CreateTemplateRequest { name, category, description?, tags?, copy_from? }`, `TemplateResponse`, `CreateVersionRequest { manifest?, action: draft|publish, version_id? }`, `VersionResponse`, `ProvisionRequest`, `ProvisioningRunResponse`, `CaptureBaselineRequest`, `BaselineResponse`, `Page<VarianceRow>` with `totals`.
- Events: `template.published.v1`, `project.provisioned.v1`, `provisioning.failed.v1`, `baseline.captured.v1` with contract payload plus `changed_fields`; the job message is `templates.provision` on the JetStream work stream with `run_id` as the idempotency key.
- Authorization: `portfolio-admin` on the tenant for template mutations, provisioning, and baseline capture; `workspace-admin` on the target workspace is also required for provisioning; `sheet-viewer` reads baselines and variance; built-ins readable by all, mutable by none; explicit deny wins.
- Validation: manifest schema via typed `serde` structs with `deny_unknown_fields`; key uniqueness per sheet; dependency keys resolve within the same sheet; column types from the F007 enum; limits per FR-F015-03; baseline measures must map to numeric or duration columns.
- Error mapping: `TemplateError::NameTaken → 409 conflict`, `VersionImmutable → 409 conflict`, `NotPublished → 400 invalid`, `ManifestInvalid → 400 invalid`, `BuiltinReadOnly → 403 denied`, `BaselineLimit → 409 conflict`, `StaleVersion → 409 conflict`, `NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`, worker overload → `503 unavailable` on provision.

### PostgreSQL/SQLx

- Migration `*_templates_*.sql` creates `project_templates(id uuid pk, tenant_id uuid not null, name text not null, category text not null, description text, is_builtin bool not null default false, current_version_id uuid, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `project_template_tags(id uuid pk, tenant_id uuid not null, template_id uuid not null references project_templates(id) on delete cascade, tag text not null, created_by uuid not null, created_at timestamptz not null)`, `template_versions(id uuid pk, tenant_id uuid not null, template_id uuid not null references project_templates(id) on delete restrict, version_number int not null, status text not null check (status in ('draft','published')), manifest jsonb not null, manifest_bytes int not null, published_at timestamptz, published_by uuid, created_by, created_at)`, `provisioning_runs(id uuid pk, tenant_id uuid not null, template_version_id uuid not null references template_versions(id), workspace_id uuid not null, project_name text not null, start_date date not null, status text not null, error_code text, error_message text, correlation_id uuid not null, version bigint not null default 1, audit fields, started_at timestamptz, finished_at timestamptz)`, `provisioning_run_steps(run_id uuid not null references provisioning_runs(id) on delete cascade, tenant_id uuid not null, step text not null check (step in ('sheets','columns','rows','schedule_settings','dependencies','views','forms','roles','workflows','reports','dashboard')), status text not null check (status in ('pending','running','completed','failed','skipped','rolled_back')), reason text, started_at timestamptz, finished_at timestamptz, created_count int not null default 0, attempt smallint not null default 0, error_code text, error_message text, created_at timestamptz not null, primary key (run_id, step))`, `provisioning_run_artifacts(id uuid pk, tenant_id uuid not null, run_id uuid not null references provisioning_runs(id) on delete cascade, step text not null, item_key text not null, object_kind text not null check (object_kind in ('sheet','column','row','view','form','dependency','role_assignment')), object_id uuid not null, created_at timestamptz not null)`, `baselines(id uuid pk, tenant_id uuid not null, sheet_id uuid not null references sheets(id) on delete restrict, name text not null, captured_at timestamptz not null, captured_by uuid not null, row_count int not null, version bigint not null default 1, audit fields, deleted_at)`, `baseline_measures(baseline_id uuid not null references baselines(id) on delete cascade, tenant_id uuid not null, measure text not null check (measure in ('start','end','duration','effort','cost')), created_at timestamptz not null, primary key (baseline_id, measure))`, `baseline_rows(baseline_id uuid references baselines(id) on delete cascade, row_id uuid not null, start_date date, end_date date, duration_days numeric(10,2), primary key (baseline_id, row_id))`, `baseline_row_measures(baseline_id uuid not null, row_id uuid not null, tenant_id uuid not null, measure text not null, value numeric(20,4) null, created_at timestamptz not null, primary key (baseline_id, row_id, measure), foreign key (baseline_id, row_id) references baseline_rows(baseline_id, row_id) on delete cascade)`.
- `template_versions.manifest jsonb` is the only retained `jsonb` column and is a payload, not a queried structure: the `TemplateManifest` is a user-authored, versioned document of arbitrary breadth (sheets, columns, rows, dependencies, forms, workflows, reports, dashboard, roles, metadata), immutable after publish, size-capped by `manifest_bytes`, validated in memory by `validate_manifest` at save time and consumed whole by the provisioning job; the database never filters, joins or aggregates inside it. The provisioning job's queried projection is `provisioning_run_steps` and `provisioning_run_artifacts`.
- Invariants: unique `project_templates(tenant_id, lower(name)) where deleted_at is null`; unique `project_template_tags(template_id, lower(tag))` with the ≤ 10 tags per template limit enforced by the service in `create_template`/`copy_builtin` (a count check, since a row cap is not declarative); unique `template_versions(template_id, version_number)`; unique `provisioning_run_artifacts(run_id, step, item_key)`, which is FR-F015-07's idempotency key made declarative; `baseline_measures` and `baseline_row_measures` restrict measures to `start|end|duration|effort|cost` by `check`, replacing the former array subset; check `manifest_bytes <= 2097152`; published rows protected by a trigger `template_versions_immutable` that raises on `UPDATE` when `old.status = 'published'`; unique `baselines(sheet_id, lower(name)) where deleted_at is null`; built-ins use the reserved tenant `00000000-0000-7000-8000-000000000000` and are read through a union in the list query.
- Indexes: `project_templates(tenant_id, category, updated_at desc)`, `project_template_tags(tenant_id, lower(tag))` for catalog tag filtering, `template_versions(template_id, status)`, `provisioning_runs(tenant_id, workspace_id, created_at desc)`, `provisioning_runs(status) where status in ('queued','running')`, `provisioning_run_steps(run_id)`, `provisioning_run_artifacts(run_id, created_at desc)` serving FR-F015-08's reverse-order rollback and FR-F015-09's `created_ids`, `baselines(sheet_id, captured_at desc)`, `baseline_rows(row_id)`, `baseline_row_measures(baseline_id, measure)` serving FR-F015-12's measure deltas and totals.
- Seed: the same migration inserts the ten built-in templates, their `project_template_tags` rows, and their published version 1 manifests from `crates/domain/src/templates/builtin/*.json`, all under the reserved built-in tenant.
- Audit events: `template.create`, `template.copy`, `template-version.create`, `template-version.publish`, `provisioning.request`, `provisioning.step`, `provisioning.rollback`, `baseline.capture`, `baseline.delete`.
- Retention/deletion: templates and baselines soft-delete; runs are retained per tenant retention (F027); rollback drops `baseline_row_measures`, `baseline_rows`, `baseline_measures`, `baselines`, `provisioning_run_artifacts`, `provisioning_run_steps`, `provisioning_runs`, `template_versions`, `project_template_tags`, and `project_templates` in that order, together with the `template_versions_immutable` trigger.

### React/TypeScript

- Routes: `/templates`, `/templates/:templateId`, `/provisioning-runs/:runId`, `/w/:workspaceId/sheets/:sheetId/baselines` in `apps/web/src/features/templates/`; components `TemplateCatalogPage`, `TemplateCard`, `CategoryFilter`, `TemplateDetail`, `ManifestSummary`, `VersionHistory`, `ProvisionDialog`, `RoleAssignmentPicker`, `ProvisioningStatus`, `StepList`, `BaselineList`, `CaptureBaselineDialog`, `VariancePanel`, `VarianceRow`.
- State: TanStack Query keys `['templates', filters]`, `['template', id]`, `['provisioning-run', id]` (polled every 2 s while `queued|running`), `['baselines', sheetId]`, `['variance', baselineId, cursor]`; the Gantt reads `['variance', baselineId]` for its overlay.
- API client: generated `TemplatesApi` with `listTemplates`, `createTemplate`, `getTemplate`, `createVersion`, `provision`, `getRun`, `captureBaseline`, `listBaselines`, `getVariance`.
- Optimistic updates: none for provisioning (server-driven status); baseline capture shows a pending row until `201` arrives.
- Telemetry: `template_catalog_opened`, `template_provision_requested`, `provisioning_completed`, `provisioning_failed`, `baseline_captured`, `variance_viewed` with `template_id`, `run_id`, `baseline_id`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F015-01 through FR-F015-15 in `testing/features/F015/requirements/cases.md`
- [ ] Failure/edge-case tests: manifest with dangling key, 21st sheet, 2 MB + 1 byte manifest, publish twice, provision draft, step failure with rollback, 21st baseline, variance with removed rows
- [ ] Permission-negative and tenant-isolation tests: cross-tenant template/run/baseline return `not_found`; built-in mutation returns `denied`; editor provisioning returns `denied`
- [ ] Rust unit tests: `manifest.rs` validation, `variance.rs` day arithmetic, `provision_job.rs` step ordering and replay idempotency against `record_artifact`; persistence tests for `claim_step`, `list_artifacts_for_rollback`, `capture_baseline_rows`, and `page_variance`; `cargo xtask check-persistence` proves no SQL in domain, API, or worker
- [ ] API contract/integration tests: all nine routes with success and each error code
- [ ] Database migration/constraint tests: immutability trigger, uniqueness including `provisioning_run_artifacts(run_id, step, item_key)` and `project_template_tags(template_id, lower(tag))`, measure `check` constraints, cascade from `baselines` to `baseline_measures`/`baseline_rows`/`baseline_row_measures`, seed count, rollback of all ten tables
- [ ] React component tests: catalog, provision dialog, status page, variance panel states
- [ ] Browser E2E tests: provision from built-in, failed run rollback, capture baseline and read variance
- [ ] Accessibility tests: axe on all pages; keyboard provisioning; live-region progress
- [ ] Performance/load tests: provision ack, 500-row completion, 100,000-row baseline capture, variance read

### Fast fanout configuration

- Test harness path: `testing/features/F015/`
- Feature flag: `F015_FEATURE`
- Fixture/seed factory: `testing/fixtures/templates.rs` builds tenant, portfolio admin, editor, viewer, foreign tenant, workspace `Ops`, a custom template with a 120-row/34-dependency manifest, a 500-row load manifest, and a sheet with 50 scheduled rows
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, `Standard` working calendar
- Mock/stub contracts: outbox and JetStream recorded in memory; worker executed in-process by the harness runner; F012/F013/F014 services are real
- Parallel isolation: one schema per test worker, tenant ID per test, unique worker ID per job consumer
- Targeted command: `cargo xtask test-feature F015`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F015/`

## 6. Acceptance criteria

```gherkin
Feature: Project templates, provisioning, and baselines

Scenario: Provision a project from a built-in template
  Given the built-in "PMO standard project" template is published
  When a portfolio admin provisions it into workspace "Ops" as "Q4 launch" starting 2026-10-05
  Then the run reaches completed within 60 seconds with sheets, rows, dependencies, a card view, and a draft form
  And project.provisioned.v1 lists the created ids

Scenario: Failed step rolls back
  Given a template whose dependencies reference a key that the rows step could not create
  When provisioning runs
  Then the run is failed, created sheets are soft-deleted, and provisioning.failed.v1 names step "dependencies"

Scenario: Editor cannot provision
  Given a sheet-editor without portfolio-admin
  When they call POST /api/v1/project-templates/{id}/provision
  Then the response is 403 denied and no run is created

Scenario: Variance against a baseline
  Given baseline "Plan of record" captured on sheet "Q4 launch"
  When row "Kickoff" is rescheduled 3 working days later and variance is read
  Then Kickoff shows finish_variance_days 3 and status slipped, and totals.rows_slipped is 1
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F012 (dependencies, schedule results), F013 (saved views), F014 (forms), and through them F006, F007, F009, F011; decisions sections 2–4, 6, 7, 9; contracts row F015
- Blocks: F031
- Conflicts with: none (disjoint owned paths)
- External dependencies: none beyond the F004 JetStream transport
- Risks and mitigations: partial provisioning leaves orphans, so every step calls `record_artifact` before creating the next object and `rollback_run` walks `list_artifacts_for_rollback` in reverse `created_at` order; manifests may reference modules not yet shipped, so unknown-module entries are `skipped` rather than failing the run; baseline capture on 100,000 rows can hold a long transaction, so `BaselineRepository::capture_baseline_rows` writes `baseline_rows` and `baseline_row_measures` set-based from the schedule read model inside one `UnitOfWork`; built-in seed content can drift from column-type changes, so the seed is validated by the same `validate_manifest` in a migration test.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F012, F013, and F014 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F015/`
- [ ] Migration file name, built-in manifest files, and owned paths claimed
- [ ] Fixture factory `testing/fixtures/templates.rs`, in-process worker runner, and schema-per-worker isolation available

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/worker/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and every provisioning step
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets`, `check-contracts`, and `check-persistence` pass
- [ ] Rollback verified: disable `F015_FEATURE`, drain the `templates.provision` consumer, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Portfolio admins can publish versioned project templates, start from ten built-in use-case templates, provision complete projects asynchronously with rollback on failure, capture baselines, and read schedule variance in the Gantt.
- Migration adds `project_templates`, `project_template_tags`, `template_versions`, `provisioning_runs`, `provisioning_run_steps`, `provisioning_run_artifacts`, `baselines`, `baseline_measures`, `baseline_rows`, and `baseline_row_measures` and seeds the built-in catalog; rollback drops them. Feature is off by default behind `F015_FEATURE`.
