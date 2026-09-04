---
id: T090
type: task
status: planned
parent_epic: E005
parent_feature: F023
parent_story: S045
depends_on: [T089]
owned_paths: [crates/domain/src/dashboards/**, crates/persistence/src/dashboards/**, services/api/src/dashboards/**, services/worker/src/dashboards/**, testing/features/F023/api/**]
feature_flag: F023_FEATURE
branch: t090-widget-registry
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 4, 7
- Capability contract: `docs/capability-contracts.md` row F023

# T090 — Widget registry

## Identity

- Parent story: `S045` Widget layout
- Owner: platform
- Branch: `t090-widget-registry`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 7; `docs/capability-contracts.md` row F023

## Objective

Implement the `WidgetResolver` registry with the four F023 resolvers, the per-scope widget cache, the refresh worker, and the eight dashboard routes with authorization, idempotency, concurrency, audit, and outbox events.

## Specification

- Owned paths: `crates/domain/src/dashboards/{registry.rs, resolvers/mod.rs, resolvers/table.rs, resolvers/report_embed.rs, resolvers/text.rs, resolvers/image.rs, cache.rs, service.rs}`, `crates/persistence/src/dashboards/{mod.rs, dashboard_repository.rs, dashboard_widget_repository.rs, widget_cache_repository.rs}`, `services/api/src/dashboards/{mod.rs, routes.rs, handlers_dashboard.rs, handlers_widgets.rs, handlers_data.rs, dto.rs}`, `services/worker/src/dashboards/{mod.rs, refresh_job.rs, scheduler.rs}`
- Contract/input: `trait WidgetResolver { kind, validate, resolve, source_versions }`; `ResolveContext { tenant_id, actor_id, scope: ViewerScope, clock, correlation_id }`; jobs `RefreshDashboardJob { dashboard_id, run_id, scope_key, actor_id }` and `RefreshWidgetJob { widget_id, scope_key, actor_id }`; DTOs from ticket section 4; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: `TableResolver` and `ReportEmbedResolver` call F021 `read_rows` through the F021 repository with the viewer scope (`limit ≤ 200`, the widget's `dashboard_widget_columns` rows in `position` order) and record the snapshot version; `TextResolver` sanitizes markdown to the allowed subset; `ImageResolver` returns an F017 signed URL only for scanned files; unregistered kinds yield `unavailable`; `cache.rs` calls `WidgetCacheRepository::{get_cache, put_cache}` by `(widget_id, scope_key)` and computes `stale` from the returned `widget_cache_sources` rows; `denied` comes from permission-checking the widget's `dashboard_widget_sources` rows, and `DashboardWidgetRepository::list_widgets_using_source(source_kind, source_id)` answers which widgets a deleted source breaks; this feature issues no SQL against another feature's tables and F036 shares are read through `ShareRepository`; routes `GET /api/v1/dashboards`, `POST /api/v1/dashboards`, `GET /api/v1/dashboards/{id}`, `PATCH /api/v1/dashboards/{id}`, `DELETE /api/v1/dashboards/{id}`, `PUT /api/v1/dashboards/{id}/widgets`, `POST /api/v1/dashboards/{id}/refresh`, `GET /api/v1/widgets/{id}/data` return the DTOs and error codes from ticket section 4; `refresh_job.rs` resolves widgets 8 at a time with a 20 s timeout, isolates failures per widget, writes cache entries and source versions through `put_cache` in one `UnitOfWork`, publishes `dashboard.refreshed.v1`, retries 3 times, dead-letters on the fourth failure, and is idempotent by `run_id`, holding no SQL string, `sqlx::query*` call, or connection; the nightly prune calls `prune_cache_unread_since(cutoff)`; `PUT /api/v1/dashboards/{id}/widgets` runs `replace_widgets` in one `UnitOfWork` that keeps retained widgets' cache, inserts new IDs, deletes omitted ones, and rewrites the source and column rows; events `dashboard.created.v1`, `dashboard.updated.v1`, `dashboard.deleted.v1` in the mutation transaction with audit rows carrying the widget diff.
- Dependencies: T089 schema, repositories, and grid validator; F021 `read_rows` and `ViewerScope`; F003 `authz::require(actor, Permission::DashboardEdit, workspace)`; F036 share lookup for read access; F017 signed URLs; F004 consumer registry.
- Feature flag: `F023_FEATURE` gates router mounting and consumer registration.

## TDD

- Failing test first: `testing/features/F023/api/dashboard_tests.rs::dashboard_create_returns_version_one`, `::dashboard_stale_version_conflicts`, `::dashboard_cross_tenant_not_found`, `::widgets_replace_keeps_cache_for_retained_ids`; `testing/features/F023/api/widget_data_tests.rs::widget_unknown_kind_rejected`, `::widget_data_unavailable_without_resolver`, `::widget_data_miss_enqueues_and_returns_computing`, `::widget_data_denied_for_restricted_source`, `::widget_data_never_crosses_scope`; `testing/features/F023/api/refresh_tests.rs::dashboard_refresh_isolates_widget_failure`, `::dashboard_refresh_active_conflicts`, `::refresh_job_dead_letters_after_four_failures`
- Targeted command: `cargo xtask test-feature F023`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/dashboards.rs` "Weekly review"; JetStream stub with failure injection; F017 signed URL stub; restricted viewer scope

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; consumers registered; OpenAPI regenerated without drift; `cargo xtask check-persistence` passes
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S045
- [ ] `finished_at` recorded
