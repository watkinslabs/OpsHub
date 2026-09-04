---
id: F056
type: feature
status: planned
priority: P1
owner: platform
estimate: 5
target_milestone: M7
parent_epic: E008
depends_on: [F021, F048]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/pivots/**, crates/persistence/src/pivots/**, services/api/src/pivots/**, apps/web/src/features/pivots/**, services/api/migrations/*_pivots_*.sql, services/worker/src/pivots/**, testing/features/F056/**]
feature_flag: F056_FEATURE
flag_default: off
branch: f056-pivot-app
started_at: null
finished_at: null
---

# F056 — Pivot App

## 1. Identity and dates

- Branch: `f056-pivot-app`
- Capability area: advanced modules, Pivot App (spec 5.11 "configurable pivot dimensions/measures with saved outputs"; 5.6 REPORT-01, REPORT-04 permission-filtered aggregation and refresh state; section 10 entitlement records plus feature flags)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7, 9; `docs/capability-contracts.md` row F056
- Module slug: `pivots`

## 2. Requirement specification

### Problem and user outcome

Report editors need to summarize a sheet or report by dimensions (status by owner, cost by month) without exporting to a spreadsheet. Today the only aggregation lives in dashboard widgets, which cannot be re-cut or saved as a table.

As a report editor with the Pivot entitlement, I want to define a pivot over a sheet or report, compute it on demand or on a schedule, keep the last outputs, and materialize an output as a new sheet, so that leadership summaries are reproducible and permission-safe.

### Functional requirements

- **FR-F056-01:** An actor with `report-editor` on the source and the tenant entitlement `pivot` can create a pivot with `name`, `source: { kind: sheet|report, id }`, 1–3 `row_dimensions`, 0–2 `column_dimensions`, 1–10 `measures`, optional `filters`, and `refresh_policy: manual|hourly|daily`; the request and response keep those four JSON arrays, and the create writes one `pivot_row_dimensions`, `pivot_column_dimensions`, `pivot_measures`, and `pivot_filters` row per entry carrying its zero-based `position`, so read order equals request order. The response returns a UUIDv7 `id` and `version` 1.
- **FR-F056-02:** Each dimension is `{ column_id, bucket?: day|week|month|quarter|year }` stored as one `pivot_row_dimensions` or `pivot_column_dimensions` row whose `bucket` column carries the check constraint; `bucket` is valid only for `date`/`datetime` columns, otherwise the request returns `invalid` with `field_errors.row_dimensions[n].bucket = "not_a_date_column"` where `n` is the row's `position`.
- **FR-F056-03:** Each measure is `{ column_id, aggregate: sum|count|avg|min|max|count_distinct, format? }` stored as one `pivot_measures` row; a column may carry several measures but not the same `aggregate` twice. `sum`, `avg`, `min`, `max` require `number`, `currency`, or `duration` columns, otherwise `invalid` with `field_errors.measures[n].aggregate = "type_mismatch"`.
- **FR-F056-04:** A tenant without the `pivot` entitlement or with `F056_FEATURE` off receives `denied` with `field_errors.entitlement = "pivot"` on every `/api/v1/pivots` route; a foreign tenant receives `not_found`.
- **FR-F056-05:** `POST /api/v1/pivots/{id}/compute` acknowledges within 2 s with a `pivot_outputs` row in state `queued`, enqueues the JetStream job `pivots.compute`, and the worker transitions the output to `running` then `succeeded` or `failed` with `error_code` in `{ timeout, source_deleted, source_too_large, permission_lost }`.
- **FR-F056-06:** The compute job aggregates only rows the requesting actor may read at compute time; rows hidden by ACL or field-level deny are excluded from every measure, and `row_count` reports visible rows only.
- **FR-F056-07:** A source with more than 100,000 visible rows fails with `source_too_large`; a job exceeding 30 s fails with `timeout`; both publish `pivot.computed.v1` with `status: failed`.
- **FR-F056-08:** `GET /api/v1/pivots/{id}/outputs` lists the newest 20 outputs by `computed_at desc` with `status`, `row_count`, `duration_ms`, `source_versions`, `computed_at`, `stale`, and `cells`; `source_versions` is assembled into its JSON object shape from the output's `pivot_output_source_versions` rows, so the response body is unchanged; the 21st output prunes the oldest, its source-version rows cascading, in the same transaction.
- **FR-F056-09:** An output is marked `stale: true` when any `pivot_output_source_versions` row for it holds a `source_version` lower than that source's current version; the comparison is a join on read, the flag is never stored.
- **FR-F056-10:** `POST /api/v1/pivots/{id}/outputs/{output_id}/materialize` creates a new sheet named `"<pivot name> <computed_at date>"` in the pivot's workspace with one column per dimension and measure and one row per output row, returns `{ sheet_id, version }`, and is idempotent per `Idempotency-Key`.
- **FR-F056-11:** `PATCH /api/v1/pivots/{id}` with `If-Match` updates `name` and `refresh_policy` in place and replaces a supplied `row_dimensions`, `column_dimensions`, `measures`, or `filters` array wholesale as child rows (delete removed positions, upsert the rest) inside the same transaction as the parent row and version bump; a stale version returns `conflict` with `current_version`; every accepted change publishes `pivot.updated.v1` with `changed_fields`.
- **FR-F056-12:** Scheduled pivots (`hourly`, `daily`) are enqueued by the worker scheduler at `:00` UTC of each hour or day, skipping a pivot that already has a `queued` or `running` output.
- **FR-F056-13:** Deleting a pivot is a soft delete that hides it and its outputs; sheets already materialized are untouched.
- **FR-F056-14:** The web builder previews the first 200 aggregated cells from the latest `succeeded` output, shows the stale banner when `stale` is true, and offers `Compute now` and `Materialize` actions only to editors.

### Non-functional requirements

- **NFR-F056-01 Performance:** `GET /api/v1/pivots/{id}/outputs` responds in under 500 ms p95 for outputs of 5,000 cells; compute of a 100,000-row source with 3 dimensions and 5 measures completes in under 30 s p95 on the reference worker.
- **NFR-F056-02 Security/privacy:** entitlement, flag, tenant, and source ACL are checked in the domain service; hidden values never appear in `cells`, materialized sheets, logs, or error messages.
- **NFR-F056-03 Accessibility:** the builder and pivot grid pass axe with zero serious violations; dimension and measure editors are fully keyboard operable and announce added or removed fields.
- **NFR-F056-04 Reliability/observability:** compute jobs are idempotent on `(output_id)`, retried at most 3 times with backoff, dead-lettered after that, and expose `pivot_compute_duration_ms` and `pivot_compute_failures_total` metrics with `tenant_id` and `error_code` labels.

### Scope

Included: pivot definition CRUD, validation of dimensions and measures, async compute with permission-filtered aggregation, output history with stale detection, materialize to sheet, scheduled refresh, builder UI with preview.

Excluded: charts over pivot outputs (F024), export of outputs (F025), calculated measures using formulas beyond the six aggregates, pivot widgets in dashboards (F023 follow-up), cross-tenant sources.

## 3. UX specification

- Personas: report editor (builds and computes), executive viewer (reads outputs), tenant admin (grants the entitlement).
- Entry points: workspace tree item `New pivot`; report page action `Pivot this report`; route `/w/{workspace_id}/pivots/{pivot_id}`; list at `/w/{workspace_id}/pivots`.
- Primary flow: pick source, drag or select row dimensions and column dimensions, add measures with aggregate and format, click `Compute now`, watch the output status chip go `queued → running → succeeded`, inspect the grid, click `Materialize` to create a sheet and open it.
- Loading: skeleton grid with 6 placeholder rows; Empty: "No outputs yet" with `Compute now`; Error: banner with `error_code`, `correlation_id`, and `Retry`; Success: toast `Output ready` and `Sheet created`; Stale: amber banner `Source changed since this output` with `Recompute`; Conflict: `This pivot changed` with `Reload`; Offline: actions disabled with offline badge.
- Permission-denied: no entitlement renders the module upsell state with the admin contact; viewers see the latest output read-only without builder controls.
- Responsive: builder panel collapses to an accordion under 768 px; pivot grid scrolls horizontally with the first dimension column frozen.
- Keyboard: `Tab` through source, dimensions, measures; `Enter` adds the focused column; `Delete` removes a chip; `Alt+ArrowUp/Down` reorders dimensions; focus returns to the list after removal; reduced motion disables status chip animation.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide `Table2`, `SigmaSquare`, `RefreshCw`, `FileOutput`, `AlertTriangle`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Pivot.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/pivots/` holds `PivotRepository` (owns `pivots`, `pivot_row_dimensions`, `pivot_column_dimensions`, `pivot_measures`, `pivot_filters`) and `PivotOutputRepository` (owns `pivot_outputs`, `pivot_output_source_versions`); the definition child tables belong to the pivot object type and the source-version rows to the output object type, so no two classes write one table. Named queries — `PivotRepository`: `find_with_definition`, `list_for_workspace`, `find_by_source`, `replace_row_dimensions`, `replace_column_dimensions`, `replace_measures`, `replace_filters`, `list_due_for_refresh`, `claim_name`; `PivotOutputRepository`: `insert_queued_output`, `find_active_output`, `mark_running`, `mark_terminal`, `list_recent_outputs`, `prune_outputs_beyond_limit`, `record_source_versions`, `list_stale_output_ids`, `load_cells`. There is no generic query method on either. Every use case below depends on these two traits and contains no SQL; the API handlers, the `pivots.compute` worker job, the scheduler, and the materialize path call repositories only. A create, an update, a compute transition, and an output insert with pruning each run in one `UnitOfWork` that also carries the audit row and the outbox enqueue; materialize shares one `UnitOfWork` with the F006 sheet repositories. The compute path composes `PivotRepository::find_with_definition` with the F021 permission-aware row query under the requesting actor's context and never assembles a SQL string in a handler, job, or the aggregation engine.
- Canonical contract: aggregate `pivot`; module `pivots`; routes `GET /api/v1/pivots`, `POST /api/v1/pivots`, `PATCH /api/v1/pivots/{id}`, `DELETE /api/v1/pivots/{id}`, `POST /api/v1/pivots/{id}/compute`, `GET /api/v1/pivots/{id}/outputs`, `POST /api/v1/pivots/{id}/outputs/{output_id}/materialize`; events `pivot.updated.v1`, `pivot.computed.v1`; tables `pivots`, `pivot_outputs`; mutation role `report-editor`.
- Domain entities in `crates/domain/src/pivots/`: `Pivot { id, tenant_id, workspace_id, name, source: PivotSource, row_dimensions: Vec<Dimension>, column_dimensions: Vec<Dimension>, measures: Vec<Measure>, filters: FilterSet, refresh_policy: RefreshPolicy, version, audit fields, deleted_at }`, `Dimension { column_id, bucket: Option<DateBucket> }`, `Measure { column_id, aggregate: Aggregate, format: Option<NumberFormat> }`, `PivotOutput { id, pivot_id, status: OutputStatus, cells: Vec<OutputCell>, row_count, source_versions: BTreeMap<Uuid, i64>, computed_at, duration_ms, error_code }`. The `Vec` and `BTreeMap` fields are in-memory projections the repositories assemble from the child tables; the domain crate declares no SQLx type and holds no query.
- Use cases: `create_pivot`, `update_pivot`, `delete_pivot`, `list_pivots`, `request_compute`, `run_compute` (worker), `list_outputs`, `materialize_output`, `schedule_due_pivots` (worker cron), `validate_definition` (type checks against F007 column metadata).
- Aggregation: `crates/domain/src/pivots/aggregate.rs` takes the definition already loaded by `PivotRepository::find_with_definition` and streams visible rows from the F021 permission-aware query (`reports::query_rows_for_actor`, itself a named query on the F021 report repository) in pages of 5,000, groups by dimension keys with `DateBucket` truncation in the tenant timezone, and folds measures with exact decimal arithmetic for `sum`/`avg` and a `HashSet` for `count_distinct`.
- Events: `pivot.updated.v1` on create, update, and delete with `changed_fields`; `pivot.computed.v1` on every terminal output with `{ output_id, status, row_count, error_code, duration_ms }` in the payload; both carry `tenant_id`, `actor_id`, `aggregate_id`, `version`, `correlation_id`, `occurred_at`.
- Validation: name 1–200 chars, at most 50 filter clauses, `format` one of `number|currency|percent|duration`; `Idempotency-Key` required on every mutation and stored for 24 hours; `If-Match` compared inside the update transaction.
- API DTOs (`services/api/src/pivots/dto.rs`): `CreatePivotRequest`, `UpdatePivotRequest`, `PivotResponse`, `OutputResponse`, `Page<OutputResponse>`, `MaterializeResponse { sheet_id, version }`.
- Worker: `services/worker/src/pivots/compute_job.rs` consumes `pivots.compute` with payload `{ tenant_id, pivot_id, output_id, actor_id, correlation_id }` and reaches the database only through `PivotRepository` and `PivotOutputRepository`; `services/worker/src/pivots/scheduler.rs` enqueues due pivots from `PivotRepository::list_due_for_refresh` and skips those with `PivotOutputRepository::find_active_output`. Neither file holds a `sqlx::query*` call or opens a connection.
- Authorization: `report-editor` on the source for create/update/delete/compute/materialize; `report-viewer` on the source for list and outputs; `authz::require_entitlement(tenant, "pivot")` before any role check; explicit deny wins.
- Error mapping: `PivotError::TypeMismatch → 400 invalid`, `PivotError::TooManyDimensions → 400 invalid`, `PivotError::EntitlementMissing → 403 denied`, `PivotError::NotFound → 404 not_found`, `PivotError::StaleVersion → 409 conflict`, `PivotError::ComputeInFlight → 409 conflict`, `PivotError::SourceTooLarge → 400 invalid`.

### PostgreSQL/SQLx

- Migration `*_pivots_*.sql` creates `pivots(id uuid pk, tenant_id uuid not null, workspace_id uuid not null references workspaces(id) on delete restrict, name text not null, source_kind text not null check (source_kind in ('sheet','report')), source_id uuid not null, filter_match text not null default 'all' check (filter_match in ('all','any')), refresh_policy text not null default 'manual' check (refresh_policy in ('manual','hourly','daily')), version bigint not null default 1, created_by uuid not null references users(id) on delete restrict, created_at, updated_by uuid not null references users(id) on delete restrict, updated_at, deleted_at)` and `pivot_outputs(id uuid pk, tenant_id uuid not null, pivot_id uuid not null references pivots(id) on delete restrict, status text not null check (status in ('queued','running','succeeded','failed')), cells jsonb, row_count integer, requested_by uuid not null references users(id) on delete restrict, computed_at timestamptz, duration_ms integer, error_code text check (error_code in ('timeout','source_deleted','source_too_large','permission_lost')), created_at timestamptz not null)`. `source_id` is polymorphic across F006 sheets and F021 reports and therefore carries no foreign key; `source_kind` is checked in DDL and the referenced object is resolved and permission-checked by `PivotRepository::find_by_source` before any write.
- Normalized sets (decision section 2, no array or list-bearing columns): `pivot_row_dimensions(pivot_id uuid not null references pivots(id) on delete cascade, tenant_id uuid not null, position smallint not null check (position between 0 and 2), column_id uuid not null, bucket text null check (bucket in ('day','week','month','quarter','year')), primary key (pivot_id, position), unique (pivot_id, column_id))` and `pivot_column_dimensions(...same shape, position check between 0 and 1...)` replace `row_dimensions jsonb` and `column_dimensions jsonb`; `pivot_measures(pivot_id references pivots(id) on delete cascade, tenant_id, position smallint not null check (position between 0 and 9), column_id uuid not null, aggregate text not null check (aggregate in ('sum','count','avg','min','max','count_distinct')), format text null check (format in ('number','currency','percent','duration')), primary key (pivot_id, position), unique (pivot_id, column_id, aggregate))` replaces `measures jsonb`; `pivot_filters(pivot_id references pivots(id) on delete cascade, tenant_id, position smallint not null check (position between 0 and 49), column_id uuid not null, operator text not null check (operator in ('eq','ne','lt','lte','gt','gte','contains','not_contains','in','between','is_empty','is_not_empty')), value jsonb, primary key (pivot_id, position))` replaces `filters jsonb`, with the set's `all`/`any` mode moved to `pivots.filter_match`; `pivot_output_source_versions(output_id uuid not null references pivot_outputs(id) on delete cascade, tenant_id uuid not null, source_kind text not null check (source_kind in ('sheet','report')), source_id uuid not null, source_version bigint not null, primary key (output_id, source_id))` replaces `pivot_outputs.source_versions jsonb`, which staleness read by key. Each child cascades because it cannot outlive its pivot or output. The request and response DTOs keep `row_dimensions`, `column_dimensions`, and `measures` as JSON arrays, `filters` as its existing object carrying the ordered clause list and the match mode, and `source_versions` as a `{ source_id: version }` object; `PivotRepository` and `PivotOutputRepository` fan them out to rows on write and reassemble them by `position` on read, so no externally visible shape changes.
- `jsonb` audit: `pivot_filters.value` stays `jsonb` — it is one typed cell value (or a two-element bound for `between`) in F007's cell encoding, compared by the compiled query and never filtered on by key. `pivot_outputs.cells` stays `jsonb` — it is the materialized output grid replayed verbatim by `GET /api/v1/pivots/{id}/outputs` and by materialize, and nothing queries inside it; as a derived, rebuildable cache it names the query it serves (`PivotOutputRepository::load_cells`) and the job that rebuilds it (`pivots.compute` in `services/worker/src/pivots/compute_job.rs`, re-runnable from any definition and source at any time). `row_dimensions`, `column_dimensions`, `measures`, `filters`, and `source_versions` were queried, validated, permission-checked, and compiled into the aggregation query, so all five became tables. No other `jsonb` column exists in this module.
- Invariants: `position` checks bound each set at 3 row dimensions, 2 column dimensions, 10 measures, and 50 filter clauses, and the primary keys make positions dense and unique; "at least one row dimension and at least one measure" is asserted by `PivotRepository::replace_row_dimensions` and `replace_measures` inside the definition `UnitOfWork`, which refuses to commit an empty set and surfaces `400 invalid` with `field_errors.row_dimensions` or `field_errors.measures` per FR-F056-01; `pivot_row_dimensions`/`pivot_column_dimensions` unique `(pivot_id, column_id)` blocks the same column twice on one axis; `pivot_measures` unique `(pivot_id, column_id, aggregate)` allows sum and avg of one column but not two sums; `pivot_output_source_versions` primary key blocks a duplicate version row per source; partial unique index `pivot_outputs_one_active_idx on (pivot_id) where status in ('queued','running')`; unique `pivots_tenant_workspace_name_idx on (tenant_id, workspace_id, lower(name)) where deleted_at is null`.
- Indexes: `pivot_outputs(pivot_id, computed_at desc)`, `pivots(tenant_id, workspace_id, updated_at desc)`, `pivots(tenant_id, refresh_policy) where refresh_policy <> 'manual' and deleted_at is null`, `pivot_row_dimensions(tenant_id, pivot_id)`, `pivot_column_dimensions(tenant_id, pivot_id)`, `pivot_measures(tenant_id, pivot_id)`, `pivot_filters(tenant_id, pivot_id)` for definition load, `pivot_row_dimensions(column_id)` and `pivot_measures(column_id)` for the reverse column-usage lookup that revalidation uses when a source column changes type or disappears, and `pivot_output_source_versions(source_id, source_version)` for the staleness join in `list_stale_output_ids`.
- Audit events: `pivot.create`, `pivot.update`, `pivot.delete`, `pivot.compute`, `pivot.materialize` with field-level diffs; `outbox_events` rows for `pivot.updated.v1` and `pivot.computed.v1` written in the same transaction as the state change.
- Retention/deletion: outputs beyond 20 per pivot are deleted on insert by `PivotOutputRepository::prune_outputs_beyond_limit`, their `pivot_output_source_versions` rows cascading; soft-deleted pivots and their outputs are purged by the F027 job, which drops the definition child rows by cascade; rollback drops the seven tables, children before parents.

### React/TypeScript

- Routes: `/w/:workspaceId/pivots`, `/w/:workspaceId/pivots/new`, `/w/:workspaceId/pivots/:pivotId` in `apps/web/src/features/pivots/`; components `PivotListPage`, `PivotPage`, `PivotBuilder`, `SourcePicker`, `DimensionPicker`, `MeasureEditor`, `PivotGrid`, `OutputHistory`, `OutputStatusChip`, `MaterializeDialog`, `EntitlementUpsell`.
- State: TanStack Query keys `['pivots', workspaceId]`, `['pivot', id]`, `['pivot-outputs', id]`; compute mutation polls `['pivot-outputs', id]` every 2 s while an output is `queued` or `running`, stopping after `succeeded`/`failed`.
- API client: generated `PivotsApi` with `listPivots`, `createPivot`, `updatePivot`, `deletePivot`, `computePivot`, `listOutputs`, `materializeOutput`.
- Optimistic updates: definition edits apply locally and roll back on `conflict` with the stale banner; compute shows the `queued` chip immediately and reconciles with the polled output.
- Feature flag: `useFlag('F056_FEATURE')` and `useEntitlement('pivot')` gate route registration and the `New pivot` entry point.
- Telemetry: `pivot_created`, `pivot_computed`, `pivot_compute_failed`, `pivot_materialized`, `pivot_stale_recompute_clicked` with `pivot_id`, `source_kind`, `dimension_count`, `measure_count`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F056-01 through FR-F056-14 in `testing/features/F056/requirements/cases.md`
- [ ] Failure/edge-case tests: bucket on text column, avg on text column, 4 row dimensions, compute while running, source deleted mid-job, 21st output prunes oldest, stale after source edit
- [ ] Permission-negative and tenant-isolation tests: no entitlement denied, viewer compute denied, foreign tenant not_found, hidden rows excluded from sums
- [ ] Rust unit tests: `crates/domain/src/pivots/` aggregate fold, date bucketing across DST, decimal sums, count_distinct
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: `position` bounds on each definition child table, duplicate column on one axis rejected, duplicate `(column_id, aggregate)` measure rejected, duplicate `pivot_output_source_versions` row rejected, cascade delete of definition and source-version rows, one active output index, name uniqueness, rollback ordering
- [ ] React component tests: `PivotBuilder`, `PivotGrid`, `OutputHistory`, `MaterializeDialog` states
- [ ] Browser E2E tests: build pivot, compute, see grid, materialize, open sheet; stale banner after source edit
- [ ] Accessibility tests: axe on builder and grid, keyboard dimension reorder announced
- [ ] Performance/load tests: outputs read p95 under 500 ms, 100k-row compute under 30 s

### Fast fanout configuration

- Test harness path: `testing/features/F056/`
- Feature flag: `F056_FEATURE`
- Fixture/seed factory: `testing/fixtures/pivots.rs` builds tenant with `pivot` entitlement, tenant without it, editor, viewer, foreign tenant, a 2,000-row sheet with status/owner/amount/date columns, and a report over it with 300 hidden rows
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, tenant timezone `America/New_York` for bucketing cases
- Mock/stub contracts: in-memory JetStream recorder for `pivots.compute`; real F021 query engine; real F048 entitlement middleware with fixture records
- Parallel isolation: one schema per test worker, tenant ID per test, unique worker ID per compute job
- Targeted command: `cargo xtask test-feature F056`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F056/`

## 6. Acceptance criteria

```gherkin
Feature: Pivot definitions, compute, and saved outputs

Scenario: Compute a status by owner pivot
  Given an editor in a tenant with the pivot entitlement and a 2,000-row sheet
  When they create a pivot with row dimension "Owner", column dimension "Status", measure sum("Amount") and click Compute now
  Then an output reaches status succeeded within 30 seconds
  And pivot.computed.v1 is in the outbox with status succeeded

Scenario: Hidden rows are excluded from aggregates
  Given a report that hides 300 rows from the editor
  When the pivot over that report is computed
  Then row_count equals 1,700 and no hidden amount contributes to any sum

Scenario: Missing entitlement is denied
  Given a tenant without the pivot entitlement
  When a report editor calls POST /api/v1/pivots
  Then the response is 403 denied with field_errors.entitlement "pivot"

Scenario: Output becomes stale after a source edit
  Given a succeeded output recorded at sheet version 10
  When the sheet reaches version 11
  Then GET outputs reports stale true and the UI shows the recompute banner
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F021 (permission-aware report query and row source), F048 (entitlement records and flag evaluation); decisions sections 2, 2.1, 3, 4, 7; contracts row F056
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: large sources can exhaust worker memory, so aggregation streams pages of 5,000 rows and caps groups at 50,000 cells before failing with `source_too_large`; DST boundaries shift week/month buckets, so bucketing uses the tenant timezone with fixture cases on both transitions; scheduled pivots can pile up, so the scheduler skips pivots with an active output.
- Rollout: enable `F056_FEATURE` for the pilot tenant first, grant the `pivot` entitlement per tenant, and watch `pivot_compute_failures_total` for 48 hours before wider rollout.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F021 and F048 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F056/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory, JetStream recorder, and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and compute outcome
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F056_FEATURE`, revoke entitlement, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Report editors with the Pivot entitlement can define pivots over sheets and reports, compute them on demand or on a schedule, review saved outputs, and materialize an output as a sheet.
- Support: failed outputs show `error_code` and `correlation_id`; operators can inspect `pivots.compute` dead letters in the worker console.
- Migration adds `pivots` and `pivot_outputs` with the child tables `pivot_row_dimensions`, `pivot_column_dimensions`, `pivot_measures`, `pivot_filters`, and `pivot_output_source_versions`; rollback drops them children first. API request and response shapes are unchanged. Feature is off by default behind `F056_FEATURE` and the `pivot` entitlement.
