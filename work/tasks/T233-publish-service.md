---
id: T233
type: task
status: planned
parent_epic: E008
parent_feature: F059
parent_story: S117
depends_on: [S117]
owned_paths: [services/api/migrations/*_publishing_*.sql, crates/domain/src/publishing/**, services/api/src/publishing/**, services/worker/src/publishing/**, testing/features/F059/database/**, testing/features/F059/api/**]
feature_flag: F059_FEATURE
branch: t233-publish-service
started_at: null
finished_at: null
---

# T233 — Publish service

## Identity

- Parent story: `S117` Published artifacts
- Owner: platform
- Branch: `t233-publish-service`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 7; `docs/capability-contracts.md` row F059

## Objective

Create the publishing schema, the publication CRUD and list routes, and the snapshot refresh worker that renders targets as the publisher and records freshness.

## Specification

- Owned paths: `services/api/migrations/<ts>_publishing_create_tables.sql`, `services/api/migrations/<ts>_publishing_create_tables.down.sql`, `crates/domain/src/publishing/{mod.rs, publication.rs, snapshot.rs, errors.rs, schema.rs, service.rs, render.rs}`, `services/api/src/publishing/{mod.rs, routes.rs, handlers_publication.rs, dto.rs}`, `services/worker/src/publishing/{mod.rs, refresh_job.rs, scheduler.rs}`
- Contract/input: `CreatePublicationRequest { target, title, access, expires_at?, embed?, refresh_interval_s?, show_freshness? }`, `UpdatePublicationRequest`, list query `{ cursor?, limit?, target_kind?, target_id?, status? }`; job payload `{ tenant_id, publication_id, scheduled_at }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: DDL per ticket section 4; routes `GET/POST /api/v1/publications`, `PATCH/DELETE /api/v1/publications/{id}` return `PublicationResponse` (create also returns `TokenIssuedResponse` produced by T234's token module); validation of expiry, origins, interval, and duplicate active target; `refresh_snapshot` renders through `views::rows_for_actor`, `reports::rows_for_actor`, or `dashboards::widget_data_for_actor` as the publisher, strips hidden columns, comments, attachments, and tenant links, writes `publications/<id>/<generated_at>.json` to object storage, updates `snapshot_*` columns, records `last_error` on failure, and marks the publication `error` when the publisher lost access or the target is deleted; scheduler enqueues due refreshes and expires publications, publishing `publication.revoked.v1` on expiry; events `publication.created.v1`, `publication.updated.v1`, `publication.revoked.v1`.
- Dependencies: F013, F021, F023 for-actor renderers; F003 `authz::require(actor, Permission::Publish, target)`; F004 outbox and JetStream; MinIO client from F017.
- Feature flag: `F059_FEATURE` gates router mounting; migration runs regardless.
- Large-table note: `publication_views` is append-only and purged at 90 days; snapshot payloads live in object storage, not the database.

## TDD

- Failing test first: `testing/features/F059/database/migration_tests.rs::publishing_tables_exist_with_constraints`, `::expiry_beyond_30_days_rejected`, `::second_active_publication_same_target_rejected`, `::rollback_drops_tables`; `testing/features/F059/api/publication_tests.rs::publication_create_returns_token_once`, `::publication_expiry_over_30_days_invalid`, `::publication_stale_version_conflicts`, `::non_publisher_create_denied`, `::publication_cross_tenant_not_found`; `testing/features/F059/api/refresh_tests.rs::refresh_hides_hidden_columns`, `::refresh_marks_error_when_publisher_access_lost`, `::scheduler_expires_due_publications`
- Targeted command: `cargo xtask test-feature F059`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database; `testing/fixtures/publishing.rs`; MinIO prefix per worker; in-memory outbox and JetStream recorders

## Exit criteria

- [ ] Tests written before the migration and services and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes mounted behind the flag; worker registered in `services/worker/src/main.rs`; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S117
- [ ] `finished_at` recorded
