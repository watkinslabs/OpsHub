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
owned_paths: [crates/domain/src/pivots/**, services/api/src/pivots/**, apps/web/src/features/pivots/**, services/api/migrations/*_pivots_*.sql, services/worker/src/pivots/**, testing/features/F056/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7, 9; `docs/capability-contracts.md` row F056
- Module slug: `pivots`

## 2. Requirement specification

### Problem and user outcome

Report editors need to summarize a sheet or report by dimensions (status by owner, cost by month) without exporting to a spreadsheet. Today the only aggregation lives in dashboard widgets, which cannot be re-cut or saved as a table.

As a report editor with the Pivot entitlement, I want to define a pivot over a sheet or report, compute it on demand or on a schedule, keep the last outputs, and materialize an output as a new sheet, so that leadership summaries are reproducible and permission-safe.

### Functional requirements

- **FR-F056-01:** An actor with `report-editor` on the source and the tenant entitlement `pivot` can create a pivot with `name`, `source: { kind: sheet|report, id }`, 1–3 `row_dimensions`, 0–2 `column_dimensions`, 1–10 `measures`, optional `filters`, and `refresh_policy: manual|hourly|daily`; the response returns a UUIDv7 `id` and `version` 1.
- **FR-F056-02:** Each dimension is `{ column_id, bucket?: day|week|month|quarter|year }`; `bucket` is valid only for `date`/`datetime` columns, otherwise the request returns `invalid` with `field_errors.row_dimensions[n].bucket = "not_a_date_column"`.
- **FR-F056-03:** Each measure is `{ column_id, aggregate: sum|count|avg|min|max|count_distinct, format? }`; `sum`, `avg`, `min`, `max` require `number`, `currency`, or `duration` columns, otherwise `invalid` with `field_errors.measures[n].aggregate = "type_mismatch"`.
- **FR-F056-04:** A tenant without the `pivot` entitlement or with `F056_FEATURE` off receives `denied` with `field_errors.entitlement = "pivot"` on every `/api/v1/pivots` route; a foreign tenant receives `not_found`.
- **FR-F056-05:** `POST /api/v1/pivots/{id}/compute` acknowledges within 2 s with a `pivot_outputs` row in state `queued`, enqueues the JetStream job `pivots.compute`, and the worker transitions the output to `running` then `succeeded` or `failed` with `error_code` in `{ timeout, source_deleted, source_too_large, permission_lost }`.
- **FR-F056-06:** The compute job aggregates only rows the requesting actor may read at compute time; rows hidden by ACL or field-level deny are excluded from every measure, and `row_count` reports visible rows only.
- **FR-F056-07:** A source with more than 100,000 visible rows fails with `source_too_large`; a job exceeding 30 s fails with `timeout`; both publish `pivot.computed.v1` with `status: failed`.
- **FR-F056-08:** `GET /api/v1/pivots/{id}/outputs` lists the newest 20 outputs by `computed_at desc` with `status`, `row_count`, `duration_ms`, `source_versions`, `computed_at`, `stale`, and `cells`; the 21st output prunes the oldest in the same transaction.
- **FR-F056-09:** An output is marked `stale: true` when any source sheet or report version recorded in `source_versions` is older than the current source version; the flag is computed on read, never stored.
- **FR-F056-10:** `POST /api/v1/pivots/{id}/outputs/{output_id}/materialize` creates a new sheet named `"<pivot name> <computed_at date>"` in the pivot's workspace with one column per dimension and measure and one row per output row, returns `{ sheet_id, version }`, and is idempotent per `Idempotency-Key`.
- **FR-F056-11:** `PATCH /api/v1/pivots/{id}` with `If-Match` updates `name`, dimensions, measures, filters, and `refresh_policy`; a stale version returns `conflict` with `current_version`; every accepted change publishes `pivot.updated.v1` with `changed_fields`.
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
- Font/icon/design tokens: Inter variable; Lucide `Table2`, `SigmaSquare`, `RefreshCw`, `FileOutput`, `AlertTriangle`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Canonical contract: aggregate `pivot`; module `pivots`; routes `GET /api/v1/pivots`, `POST /api/v1/pivots`, `PATCH /api/v1/pivots/{id}`, `DELETE /api/v1/pivots/{id}`, `POST /api/v1/pivots/{id}/compute`, `GET /api/v1/pivots/{id}/outputs`, `POST /api/v1/pivots/{id}/outputs/{output_id}/materialize`; events `pivot.updated.v1`, `pivot.computed.v1`; tables `pivots`, `pivot_outputs`; mutation role `report-editor`.
- Domain entities in `crates/domain/src/pivots/`: `Pivot { id, tenant_id, workspace_id, name, source: PivotSource, row_dimensions: Vec<Dimension>, column_dimensions: Vec<Dimension>, measures: Vec<Measure>, filters: FilterSet, refresh_policy: RefreshPolicy, version, audit fields, deleted_at }`, `Dimension { column_id, bucket: Option<DateBucket> }`, `Measure { column_id, aggregate: Aggregate, format: Option<NumberFormat> }`, `PivotOutput { id, pivot_id, status: OutputStatus, cells: Vec<OutputCell>, row_count, source_versions: BTreeMap<Uuid, i64>, computed_at, duration_ms, error_code }`.
- Use cases: `create_pivot`, `update_pivot`, `delete_pivot`, `list_pivots`, `request_compute`, `run_compute` (worker), `list_outputs`, `materialize_output`, `schedule_due_pivots` (worker cron), `validate_definition` (type checks against F007 column metadata).
- Aggregation: `crates/domain/src/pivots/aggregate.rs` streams visible rows from the F021 permission-aware query (`reports::query_rows_for_actor`) in pages of 5,000, groups by dimension keys with `DateBucket` truncation in the tenant timezone, and folds measures with exact decimal arithmetic for `sum`/`avg` and a `HashSet` for `count_distinct`.
- Events: `pivot.updated.v1` on create, update, and delete with `changed_fields`; `pivot.computed.v1` on every terminal output with `{ output_id, status, row_count, error_code, duration_ms }` in the payload; both carry `tenant_id`, `actor_id`, `aggregate_id`, `version`, `correlation_id`, `occurred_at`.
- Validation: name 1–200 chars, at most 50 filter clauses, `format` one of `number|currency|percent|duration`; `Idempotency-Key` required on every mutation and stored for 24 hours; `If-Match` compared inside the update transaction.
- API DTOs (`services/api/src/pivots/dto.rs`): `CreatePivotRequest`, `UpdatePivotRequest`, `PivotResponse`, `OutputResponse`, `Page<OutputResponse>`, `MaterializeResponse { sheet_id, version }`.
- Worker: `services/worker/src/pivots/compute_job.rs` consumes `pivots.compute` with payload `{ tenant_id, pivot_id, output_id, actor_id, correlation_id }`; `services/worker/src/pivots/scheduler.rs` enqueues due pivots.
- Authorization: `report-editor` on the source for create/update/delete/compute/materialize; `report-viewer` on the source for list and outputs; `authz::require_entitlement(tenant, "pivot")` before any role check; explicit deny wins.
- Error mapping: `PivotError::TypeMismatch → 400 invalid`, `PivotError::TooManyDimensions → 400 invalid`, `PivotError::EntitlementMissing → 403 denied`, `PivotError::NotFound → 404 not_found`, `PivotError::StaleVersion → 409 conflict`, `PivotError::ComputeInFlight → 409 conflict`, `PivotError::SourceTooLarge → 400 invalid`.

### PostgreSQL/SQLx

- Migration `*_pivots_*.sql` creates `pivots(id uuid pk, tenant_id uuid not null, workspace_id uuid not null, name text not null, source_kind text not null check (source_kind in ('sheet','report')), source_id uuid not null, row_dimensions jsonb not null, column_dimensions jsonb not null default '[]', measures jsonb not null, filters jsonb not null default '{}', refresh_policy text not null default 'manual', version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)` and `pivot_outputs(id uuid pk, tenant_id uuid not null, pivot_id uuid not null references pivots(id) on delete restrict, status text not null, cells jsonb, row_count integer, source_versions jsonb not null default '{}', requested_by uuid not null, computed_at timestamptz, duration_ms integer, error_code text, created_at timestamptz not null)`.
- Invariants: check `jsonb_array_length(row_dimensions) between 1 and 3`, `jsonb_array_length(column_dimensions) <= 2`, `jsonb_array_length(measures) between 1 and 10`; partial unique index `pivot_outputs_one_active_idx on (pivot_id) where status in ('queued','running')`; unique `pivots_tenant_workspace_name_idx on (tenant_id, workspace_id, lower(name)) where deleted_at is null`.
- Indexes: `pivot_outputs(pivot_id, computed_at desc)`, `pivots(tenant_id, workspace_id, updated_at desc)`, `pivots(tenant_id, refresh_policy) where refresh_policy <> 'manual' and deleted_at is null`.
- Audit events: `pivot.create`, `pivot.update`, `pivot.delete`, `pivot.compute`, `pivot.materialize` with field-level diffs; `outbox_events` rows for `pivot.updated.v1` and `pivot.computed.v1` written in the same transaction as the state change.
- Retention/deletion: outputs beyond 20 per pivot are deleted on insert; soft-deleted pivots and their outputs are purged by the F027 job; rollback drops both tables.

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
- [ ] Database migration/constraint tests: dimension count checks, one active output index, name uniqueness, rollback
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

- Depends on: F021 (permission-aware report query and row source), F048 (entitlement records and flag evaluation); decisions sections 2, 3, 4, 7; contracts row F056
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
- Migration adds `pivots` and `pivot_outputs`; rollback drops them. Feature is off by default behind `F056_FEATURE` and the `pivot` entitlement.
