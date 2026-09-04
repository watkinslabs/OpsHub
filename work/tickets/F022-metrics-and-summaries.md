---
id: F022
type: feature
status: planned
priority: P1
owner: platform
estimate: 5
target_milestone: M4
parent_epic: E005
depends_on: [F021]
blocks: [F024]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/metrics/**, crates/persistence/src/metrics/**, services/api/src/metrics/**, services/worker/src/metrics/**, apps/web/src/features/metrics/**, services/api/migrations/*_metrics_*.sql, testing/features/F022/**]
feature_flag: F022_FEATURE
flag_default: off
branch: f022-metrics-and-summaries
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 7, 9
- Capability contract: `docs/capability-contracts.md` row F022
- Product spec: `docs/product-capability-spec.md` section 5.6 REPORT-02 (KPI cards), REPORT-04 (summaries, trend analysis), section 6

# F022 — Metrics and summaries

## 1. Identity and dates

- Branch: `f022-metrics-and-summaries`
- Capability area: reporting (spec 5.6 REPORT-02 KPI cards, REPORT-04 portfolio summaries and trend analysis; low-level bullets: refresh jobs cached with last-success, duration, source versions, stale state; hidden values excluded from aggregates unless policy allows)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7; `docs/capability-contracts.md` row F022
- Aggregate: `metric`
- Module slug: `metrics`

## 2. Requirement specification

### Problem and user outcome

Leaders ask "how many open high risks do we have this week, and is that better than last week" and today someone counts rows by hand. They need a named metric that aggregates a report or sheet column under a filter, is computed into cached period values by a worker, compares against the previous period or a target, and shows only what the viewer is allowed to see.

As a report editor, I want to define metrics with an aggregation, period grain, formatting, and target, and have their values computed and cached with rollups and trend deltas, so that KPI cards and trend charts read governed numbers instead of ad-hoc counts.

### Functional requirements

- **FR-F022-01:** An actor with the `report-editor` role on the workspace can `POST /api/v1/metrics` with `{ name, workspace_id, source: { kind: report|sheet, id }, measure: { column_ref?, fn: count|count_distinct|sum|avg|min|max|percent_of, of_filter? }, filters?, period: { grain: day|week|month|quarter, timezone, week_start: monday|sunday }, format: { kind: number|currency|percent|duration, decimals: 0..4, currency_code? }, target?: { value, direction: up_is_good|down_is_good }, comparison: previous_period|same_period_last_year|target|none, scope_policy: viewer|owner }`; the response returns a UUIDv7 `id` and `version` 1; a `sum`/`avg` measure on a non-numeric column returns `400 invalid` with `field_errors["measure.column_ref"]`. The nested request and response bodies are unchanged; `MetricRepository` composes them from typed columns (`measure_fn`, `measure_source_id`, `measure_column_id`, `period_grain`, `period_timezone`, `week_start`, `format_kind`, `format_decimals`, `format_currency_code`, `target_value`, `target_direction`) and `metric_filters` rows, so member validation — allowed function, decimals 0..4, currency code present for `currency`, target value and direction set together, column reference present for `sum`/`avg`/`min`/`max` — is declarative in the schema and re-checked in the validator for the field-scoped error message.
- **FR-F022-02:** `percent_of` computes `100 × count(rows matching of_filter) ÷ count(rows matching filters)` and returns `null` when the denominator is 0; `of_filter` uses the F021 filter tree grammar with the same limits (depth 4, 50 predicates) and is stored as `metric_filters` rows with `role = 'of_filter'`, one row per predicate node keyed by `node_path`; a `percent_of` metric with no such row is rejected `400 invalid` with `field_errors["measure.of_filter"]`, enforced in the create transaction before it commits.
- **FR-F022-03:** `source.kind = report` reads the latest succeeded F021 snapshot and `source.kind = sheet` reads live rows; a metric whose source the actor cannot read returns `404 not_found` on create.
- **FR-F022-04:** `POST /api/v1/metrics/{id}/recompute` enqueues a `metrics.recompute` job and returns `202 { run_id, status: "queued" }` within 2 seconds; the worker writes one `metric_values` row per period bucket over the trailing window (`day`: 90 buckets, `week`: 52, `month`: 24, `quarter`: 8) with `value`, `sample_count`, `period_start`, `period_end`, and a `metric_runs` row with `status`, `duration_ms`, `rows_scanned`, `error` plus one `metric_run_sources` row per source carrying `source_kind`, `source_id`, and `source_version`; it publishes `metric.computed.v1`; a recompute while a run is active returns `409 conflict` from `find_active_run`. The `source_versions` field of the event and of `meta` is assembled from those rows and keeps its shape.
- **FR-F022-05:** Metric values are computed per `scope_key`: with `scope_policy: viewer` the job computes for the requesting viewer's `ViewerScope` (readable sheets and hidden columns from F021) and caches by `scope_key`; with `scope_policy: owner` the job computes once under the metric owner's scope and serves every viewer, which is permitted only when tenant policy `reports.aggregate_hidden_values` is `true`, otherwise `POST` and `PATCH` return `400 invalid` with `field_errors.scope_policy`.
- **FR-F022-06:** `GET /api/v1/metrics/{id}/values?from&to&grain?` returns `{ current: { value, formatted, period_start, period_end }, comparison: { kind, value, delta_abs, delta_pct, direction: better|worse|flat }, series: [{ period_start, value, sample_count }], meta: { run_id, computed_at, duration_ms, source_versions, stale, scope: viewer|owner } }` for the viewer's `scope_key`, read through `list_values`; `meta.source_versions` keeps its object shape and is assembled from the run's `metric_run_sources` rows. When no value exists for that scope it returns `current: null`, `meta.status = "computing"`, and enqueues a recompute for that scope.
- **FR-F022-07:** `meta.stale` is `true` when any `metric_run_sources` row for the run records a `source_version` behind the current sheet version or the source report has a newer succeeded snapshot; the comparison is a join from `metric_run_sources` to the source's current version rather than a scan of a JSON map; a stale metric is recomputed automatically at most once per 5 minutes per `scope_key` when read.
- **FR-F022-08:** Period rollups: `series` buckets are aligned on every read to the `period_timezone` and `week_start` columns, which are queried data and not a settings payload; `grain` in the query may be coarser than the metric grain (day → week → month → quarter) and rolls up by `sum` for `count`, `count_distinct` (recomputed, never summed), `sum`, and by weighted `avg` using `sample_count`; a finer grain than defined returns `400 invalid`.
- **FR-F022-09:** `comparison: previous_period` compares the latest complete bucket to the one before it; `same_period_last_year` compares to the bucket 1 year earlier; `target` compares to the `target_value` column; `direction` reads the `target_direction` column (default `up_is_good`) and `flat` when `|delta_pct| < 0.5`.
- **FR-F022-10:** Formatting follows F049 locale rules: `currency` uses `currency_code` (ISO 4217) and the viewer locale, `percent` appends `%` with `decimals`, `duration` renders `1d 4h`; `formatted` is computed server-side and echoed in `values`.
- **FR-F022-11:** `GET /api/v1/metrics` pages by cursor with `limit` 1..100 through `page_metrics`, filters by `workspace_id`, the `source_id` column, and `name` prefix, and returns only metrics whose source the actor can read; `PATCH /api/v1/metrics/{id}` requires `If-Match`, returns `409 conflict` on a stale version, and a change to `measure_fn`/`measure_column_id`, the `metric_filters` rows (replaced wholesale by `replace_filters`), the period columns, or `source` calls `delete_values_for_metric` to drop cached `metric_values` for every scope and publishes `metric.updated.v1`, all in the one `UnitOfWork` that owns the `PATCH`; `DELETE` soft-deletes and cancels queued runs; a foreign-tenant actor receives `404 not_found`.
- **FR-F022-12:** Every mutation requires `Idempotency-Key`, writes an `audit_events` row, and publishes `metric.updated.v1` through the outbox; the recompute job retries 3 times with backoff, dead-letters on the fourth failure, and is idempotent by `run_id`.
- **FR-F022-13:** The web app renders a KPI card (`formatted` value, comparison arrow and delta, target progress, sparkline of `series`, stale and computing badges) and a metric editor with source picker, measure, filters, period, format, target, comparison, and scope policy, with loading, empty, error, denied, stale, computing, and offline states.

### Non-functional requirements

- **NFR-F022-01 Performance:** `values` responds under 300 ms p95 from cache; a recompute over a 100,000-row source with 52 weekly buckets completes under 30 s and is acknowledged under 2 s; the KPI card renders within 100 ms of data arrival.
- **NFR-F022-02 Security/privacy:** values are cached and served by `scope_key`, never across viewers with different scopes; `owner` scope requires tenant policy; cross-tenant, viewer, restricted-source, and hidden-column negatives are in the harness.
- **NFR-F022-03 Accessibility:** KPI cards expose value, delta, and direction as text (arrows are decorative); sparklines have a text summary; the editor is keyboard operable and axe reports zero serious violations.
- **NFR-F022-04 Reliability/observability:** spans carry `tenant_id`, `metric_id`, `run_id`, `scope_key`; metrics `metric_recompute_duration_seconds`, `metric_recompute_failures_total`, `metric_values_cache_hits_total`; dead-letter alerts route to the operations channel.

### Scope

Included: metric CRUD, aggregation functions, `percent_of`, filters, period buckets, rollups, comparison and trend deltas, targets, formatting, per-scope cached values, recompute jobs with run history, stale detection, KPI card and metric editor components.

Excluded: dashboards and widget placement (F023), time-series projection and charts (F024), portfolio health scores (F031), report definitions and snapshots (F021), export (F025).

## 3. UX specification

- Entry points: report viewer toolbar `Add metric`; route `/w/{workspace_id}/metrics/{metric_id}/edit`; KPI cards are consumed by dashboards (F023/F024) and previewed in the editor.
- Primary flow: open report "Portfolio status", click `Add metric`, name "Open high risks", measure `count` with filter `Risks.status = Open and severity in [High, Critical]`, period `week` in `America/New_York`, comparison `previous_period`, target 5 `down_is_good`, save; the preview card shows `Computing`, then `7 ▼ 2 vs last week` with a red direction and a sparkline of 52 weeks.
- Loading: card skeleton; Empty: `No data yet` when `series` is empty; Error: card shows `Unavailable` with `correlation_id` on hover and a retry; Computing: badge with spinner; Stale: badge `Updated {computed_at}` with `Recompute`; Denied: editor read-only; Offline: recompute disabled.
- Responsive: cards are 2 columns under 640 px and 1 column under 400 px; the editor stacks under 1024 px.
- Keyboard: card is a focusable region with `Enter` opening the source report; editor fields in tab order; comparison arrows are `aria-hidden` with visible text `up`/`down`; focus ring tokens; reduced motion disables the sparkline draw animation.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide `Gauge`, `TrendingUp`, `TrendingDown`, `Minus`, `Target`, `RefreshCw`; color tokens `--kpi-better`, `--kpi-worse`, `--kpi-flat` from `apps/web/src/design/tokens.css` meeting 4.5:1 contrast.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/metrics/`: `Metric { id, tenant_id, workspace_id, name, source: MetricSource, measure: Measure { fn, source_id, column_id }, filters: Vec<MetricFilter { role, node_path, column_id, op, value }>, period: PeriodSpec { grain, timezone, week_start }, format: FormatSpec { kind, decimals, currency_code }, target: Option<Target { value, direction }>, comparison: Comparison, scope_policy: ScopePolicy, version, audit fields, deleted_at }`, `MetricValue { metric_id, scope_key, period_start, period_end, value: Option<Decimal>, sample_count, run_id, computed_at }`, `MetricRun { id, metric_id, scope_key, status: RunStatus, started_at, finished_at, duration_ms, source_versions: Vec<RunSource { source_kind, source_id, source_version }>, rows_scanned, error }`. The nested API bodies are these structs; the flat columns and child rows behind them are a repository concern.
- Use cases: `create_metric`, `update_metric`, `delete_metric`, `list_metrics`, `request_recompute`, `execute_recompute` (worker), `read_values` (rollup, comparison, formatting, stale), `invalidate_values`.
- Persistence (`crates/persistence/src/metrics/`): `MetricRepository` owns `metrics` and `metric_filters`; `MetricValueRepository` owns `metric_values`; `MetricRunRepository` owns `metric_runs` and `metric_run_sources`. Each implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds named queries `load_definition(metric_id)`, `replace_filters(metric_id, rows)`, `page_metrics(filter, cursor)`, `list_metrics_using_source(source_kind, source_id)`, `list_metrics_using_column(column_id)`, `find_active_run(metric_id, scope_key)`, `claim_recompute(metric_id, scope_key, run_id)`, `upsert_values(metric_id, scope_key, buckets)`, `list_values(metric_id, scope_key, from, to)`, `delete_values_for_metric(metric_id)`, `prune_runs_older_than(cutoff)`, `prune_unread_scopes(cutoff)`; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. One recompute run — run row, `metric_run_sources` rows, value buckets, outbox — is one `UnitOfWork`, and the FR-F022-11 definition change that deletes cached values for every scope runs in the same `UnitOfWork` as the `PATCH`. Source rows are read through F021's snapshot repository or the F006/F007/F008 repositories, never by this feature's SQL. Per decision 2.1 the use cases above depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/metrics`, `services/api/src/metrics`, `services/worker/src/metrics`, or the F022 test lanes.
- Aggregator `crates/domain/src/metrics/aggregate.rs`: folds rows supplied by F021's snapshot repository (`read_rows`) or the F006/F007/F008 row repositories under the `ViewerScope` into period buckets using `chrono-tz`; `rollup.rs` re-buckets to a coarser grain; `compare.rs` computes deltas; `format.rs` calls the F049 formatter.
- Worker `services/worker/src/metrics/{recompute_job.rs, stale_sweeper.rs}`: consumes `metrics.recompute` and calls `claim_recompute`, `upsert_values`, and the run recorder inside one `UnitOfWork` per run; the sweeper runs every 5 minutes and calls `prune_runs_older_than` and `prune_unread_scopes`. The job holds no SQL string, `sqlx::query*` call, or connection.
- API endpoints (`services/api/src/metrics/`): `GET /api/v1/metrics`, `POST /api/v1/metrics`, `PATCH /api/v1/metrics/{id}`, `DELETE /api/v1/metrics/{id}`, `GET /api/v1/metrics/{id}/values`, `POST /api/v1/metrics/{id}/recompute`; DTOs `CreateMetricRequest`, `UpdateMetricRequest`, `MetricResponse`, `MetricValuesResponse`, `RecomputeResponse { run_id, status }`.
- Events: `metric.updated.v1` (create, update, delete with `changed_fields`), `metric.computed.v1` (payload adds `run_id`, `scope_key`, `bucket_count`, `duration_ms`, `source_versions`).
- Authorization: `report-editor` on the workspace for mutations and recompute; reads require `read` on the source report or sheet; explicit deny wins; missing access maps to `not_found`.
- Validation limits: name 1..200, filters depth ≤ 4 and ≤ 50 predicates, `decimals` 0..4, `currency_code` ISO 4217, `target_value` finite decimal set with `target_direction`, `percent_of` requires at least one `of_filter` row, `sum`/`avg`/`min`/`max` require `measure_column_id`, window buckets fixed per grain.
- Error mapping: `MetricError::InvalidMeasure → 400 invalid`, `MetricError::ScopePolicyNotAllowed → 400 invalid`, `MetricError::FinerGrain → 400 invalid`, `MetricError::RunActive → 409 conflict`, `MetricError::StaleVersion → 409 conflict`, `MetricError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`, queue unavailable → `503 unavailable`.

### PostgreSQL/SQLx

- Migration `*_metrics_*.sql` creates five tables. `metrics(id uuid pk, tenant_id, workspace_id, name text, source_kind text, source_id uuid, measure_fn text not null, measure_source_id uuid null, measure_column_id uuid null references columns(id) on delete restrict, period_grain text not null, period_timezone text not null, week_start text not null, format_kind text not null, format_decimals smallint not null, format_currency_code char(3) null, target_value numeric null, target_direction text null, comparison text, scope_policy text default 'viewer', version bigint default 1, audit fields, deleted_at)` — no `jsonb` column remains on `metrics`: the product validates, filters, rolls up and compares on every one of these members, so each is a typed column or a child row.
- `metric_filters(id uuid pk, tenant_id uuid not null, metric_id uuid not null references metrics(id) on delete cascade, role text not null, node_path text not null, column_id uuid not null references columns(id) on delete restrict, op text not null, value jsonb null, created_at, created_by, unique (metric_id, role, node_path))` carries both the metric filter tree (`role = 'filter'`) and a `percent_of` numerator tree (`role = 'of_filter'`), mirroring F021's `report_filters` so the two features share one filter model. `value` stays `jsonb`: it is a typed cell value whose shape follows the referenced column's F007 type and is never read by key. The F021 grammar and its limits are unchanged — depth ≤ 4 (`node_path` segment count) and ≤ 50 predicates per `(metric_id, role)`, enforced by the validator.
- `metric_values(tenant_id, metric_id, scope_key text, period_start timestamptz, period_end timestamptz, value numeric null, sample_count int, run_id uuid, computed_at, primary key (metric_id, scope_key, period_start))`, `metric_runs(id uuid pk, tenant_id, metric_id, scope_key, status text, started_at, finished_at, duration_ms int, rows_scanned int, error text)`, `metric_run_sources(run_id uuid not null references metric_runs(id) on delete cascade, tenant_id uuid not null, source_kind text not null, source_id uuid not null, source_version bigint not null, created_at, primary key (run_id, source_kind, source_id))`. `metric_values` and `metric_runs` are derived, rebuildable caches, never a source of truth: they serve `GET /api/v1/metrics/{id}/values` and are rebuilt by the `metrics.recompute` job from F021 snapshots or live sheet rows.
- Invariants: `check (scope_policy in ('viewer','owner'))`, `check (comparison in ('previous_period','same_period_last_year','target','none'))`, `check (source_kind in ('report','sheet'))`, `check (measure_fn in ('count','count_distinct','sum','avg','min','max','percent_of'))`, `check (measure_fn not in ('sum','avg','min','max') or measure_column_id is not null)`, `check (period_grain in ('day','week','month','quarter'))`, `check (week_start in ('monday','sunday'))`, `check (format_kind in ('number','currency','percent','duration'))`, `check (format_decimals between 0 and 4)`, `check (format_kind <> 'currency' or format_currency_code is not null)`, `check (target_direction in ('up_is_good','down_is_good'))` with `check ((target_value is null) = (target_direction is null))`, `metric_filters check (role in ('filter','of_filter'))`, `metric_run_sources check (source_kind in ('report','sheet'))`; a `percent_of` metric must have at least one `role = 'of_filter'` row, which is not expressible as a row check and is enforced in the create/update transaction by `MetricRepository::replace_filters` before the insert commits; at most one run with `status in ('queued','running')` per `(metric_id, scope_key)` via partial unique index `metric_runs_active_idx`; `metric_values.metric_id` foreign key `on delete cascade`; `metrics.source_id` stays polymorphic because `source_kind` selects between `reports(id)` and `sheets(id)`, so no single foreign key is declarable — integrity is enforced by resolving the source through F021's report repository or F006's sheet repository on create and update (missing or unreadable ⇒ `404 not_found`, FR-F022-03) and by `list_metrics_using_source(source_kind, source_id)` when a source is deleted.
- Indexes: `metric_values(metric_id, scope_key, period_start desc)`, `metric_runs(metric_id, finished_at desc)`, `metrics(tenant_id, workspace_id, source_id)`, `metrics(measure_column_id)`, `metric_filters(column_id)`, `metric_run_sources(source_kind, source_id)`; `unique (metric_id, role, node_path)` on `metric_filters` is the declarative form of the old one-node-per-path rule inside the filter JSON.
- Audit events: `metric.create`, `metric.update`, `metric.delete`, `metric.recompute.request`, `metric.recompute.complete`.
- Retention/deletion: `metric_runs` older than 30 days pruned nightly through `prune_runs_older_than` (its `metric_run_sources` rows cascade); values for scopes unread for 14 days deleted through `prune_unread_scopes`; soft delete sets `deleted_at`; rollback drops the five tables `metric_run_sources`, `metric_runs`, `metric_values`, `metric_filters`, `metrics` in that order.

### React/TypeScript

- Routes: `/w/:workspaceId/metrics/new?source=report:{id}`, `/w/:workspaceId/metrics/:metricId/edit` in `apps/web/src/features/metrics/`; components `MetricEditor`, `MeasurePicker`, `PeriodForm`, `FormatForm`, `TargetForm`, `KpiCard`, `KpiDelta`, `Sparkline`, `MetricPreview`.
- State: TanStack Query keys `['metric-values', id, from, to, grain]` (staleTime 60 s, refetch every 5 s while `meta.status = computing`), `['metric-list', workspaceId, filters]`.
- API client: generated `MetricsApi` with `listMetrics`, `createMetric`, `updateMetric`, `deleteMetric`, `getMetricValues`, `recomputeMetric`.
- Telemetry: `metric_created`, `metric_recompute_requested`, `kpi_card_rendered` (with `stale`, `scope`), `kpi_card_opened_source`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F022-01 through FR-F022-13 in `testing/features/F022/requirements/cases.md`
- [ ] Failure/edge-case tests: sum on text column, percent_of zero denominator, finer grain request, owner scope without tenant policy, recompute while active, week alignment across DST
- [ ] Permission-negative and tenant-isolation tests: cross-tenant `not_found`, viewer mutation `denied`, restricted-source viewer gets scoped values, hidden column excluded from sum, scope_key never shared
- [ ] Rust unit tests: `crates/domain/src/metrics/` aggregator buckets, rollup weighted average, comparison direction, formatter
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: value primary key, active run index, measure/period/format/target check constraints, `metric_filters` unique `(metric_id, role, node_path)` and column restrict, `metric_run_sources` primary key and cascade, `metric_values` cascade, rollback of the five tables
- [ ] React component tests: `KpiCard` states, `MetricEditor` validation
- [ ] Browser E2E tests: define metric from a report, see computing then value, recompute, stale badge
- [ ] Accessibility tests: axe on card and editor, text alternatives for arrows and sparkline
- [ ] Performance/load tests: values p95 under 300 ms, 100,000-row recompute under 30 s

### Fast fanout configuration

- Test harness path: `testing/features/F022/`
- Feature flag: `F022_FEATURE`
- Fixture/seed factory: `testing/fixtures/metrics.rs` reuses the F021 three-sheet fixture and snapshot, adds metric "Open high risks" (count, weekly) and "Budget margin" (sum over hidden column) for editor, viewer, and restricted viewer scopes
- Deterministic test data: fixed clock `2026-09-03T00:00:00Z`, timezones `UTC` and `America/New_York` including the 2026-03-08 DST transition
- Mock/stub contracts: in-memory outbox recorder; in-memory JetStream stub for `metrics.recompute`; real F003 engine; F049 formatter with `en-US` and `de-DE` fixtures
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F022`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F022/`

## 6. Acceptance criteria

```gherkin
Feature: Metrics and summaries

Scenario: Weekly KPI with previous-period comparison
  Given report "Portfolio status" has 7 open high risks this week and 9 last week
  When editor Dana creates metric "Open high risks" with grain week and comparison previous_period and recomputes
  Then values returns current 7, delta_abs -2, direction better for down_is_good, and 52 weekly buckets
  And metric.updated.v1 and metric.computed.v1 are in the outbox

Scenario: Hidden column excluded from sum
  Given metric "Budget margin" sums Budget.margin which is hidden from viewer Lee
  When Lee reads values
  Then current.value is null, meta.scope is viewer, and the editor's value for the same metric is 41000

Scenario: Viewer cannot recompute or edit
  Given viewer Lee opens metric "Open high risks"
  When Lee sends PATCH or POST recompute
  Then the response is 403 denied

Scenario: Stale metric recomputed on read
  Given values were computed with a metric_run_sources row recording Risks at version 4
  When a Risks row changes to version 5 and Lee reads values
  Then meta.stale is true and one recompute run is queued for Lee's scope_key within 5 minutes
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F021 (report snapshots, filter grammar, `ViewerScope`, row reads); decisions sections 2, 3, 4, 7; contracts row F022
- Blocks: F024
- Conflicts with: none (disjoint owned paths)
- External dependencies: NATS JetStream for `metrics.recompute`; `chrono-tz` for period buckets
- Risks and mitigations: per-viewer scopes can multiply cache size, so scopes unread for 14 days are pruned and a tenant is capped at 200 scopes per metric with the oldest evicted; DST transitions shift bucket boundaries, so buckets are computed in the metric timezone and tested across the March and November transitions; `count_distinct` cannot be rolled up by summation, so rollups recompute it from the source snapshot.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F021 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F022/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory `testing/fixtures/metrics.rs` and F049 formatter fixtures available

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and recompute
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F022_FEATURE`, stop the recompute consumer, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can define metrics over reports and sheets with aggregation, period grain, formatting, targets, and comparisons, and read cached KPI values with rollups, trend deltas, and stale state.
- Values are computed per viewer scope so hidden values never enter a number a viewer is not allowed to see, unless tenant policy allows owner-scoped metrics.
- Migration adds `metrics`, `metric_filters`, `metric_values`, `metric_runs`, and `metric_run_sources`; rollback drops them. Feature is off by default behind `F022_FEATURE`.
