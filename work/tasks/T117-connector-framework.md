---
id: T117
type: task
status: planned
parent_epic: E006
parent_feature: F030
parent_story: S059
depends_on: [S059]
owned_paths: [services/api/migrations/*_connectors_*.sql, crates/domain/src/connectors/**, services/api/src/connectors/**, services/worker/src/connectors/**, testing/features/F030/api/**, testing/features/F030/database/**]
feature_flag: F030_FEATURE
branch: t117-connector-framework
started_at: null
finished_at: null
---

# T117 — Connector framework

## Identity

- Parent story: `S059` Work sync
- Owner: platform
- Branch: `t117-connector-framework`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 7; `docs/capability-contracts.md` row F030

## Objective

Create the `connectors` schema and the shared connector framework: the registry that adds `jira` to the F029 provider list, the `Sync` aggregate and its lifecycle routes, the `RecordSource`/`RecordSink` adapter traits with the Jira implementation, the run trigger and scheduler, and run history.

## Specification

- Owned paths: `services/api/migrations/<ts>_connectors_create_tables.sql` and `.down.sql`, `crates/domain/src/connectors/{mod.rs, registry.rs, sync.rs, adapter.rs, errors.rs, service.rs, adapters/jira.rs}`, `services/api/src/connectors/{mod.rs, routes.rs, handlers_sync.rs, handlers_run.rs, dto.rs}`, `services/worker/src/connectors/{mod.rs, schedule.rs, webhook.rs}`
- Contract/input: `SyncRequest { connection_id, name, kind, source: { object, filter? }, target: { sheet_id }, direction, schedule, conflict_policy?, deletion_policy?, deletion_column_id?, mappings }`; `PATCH` body `{ expected_version, name?, schedule?, state?, conflict_policy?, deletion_policy?, source_filter?, reset_cursor_to? }`; list query `{ cursor?, limit?, connection_id?, connector?, kind?, state? }`; every mutation carries `Idempotency-Key`.
- Output/behavior: DDL for `syncs`, `sync_mappings`, `sync_runs`, `sync_cursors`, `sync_conflicts`, `sync_record_links` with the checks, unique constraints, and indexes in ticket section 4; routes `GET /api/v1/syncs`, `POST /api/v1/syncs`, `GET /api/v1/syncs/{id}`, `PATCH /api/v1/syncs/{id}`, `POST /api/v1/syncs/{id}/run`, `POST /api/v1/syncs/{id}/pause`, `GET /api/v1/syncs/{id}/runs`; `registry.rs` registers `jira` with `sync_kinds: [work]`, `cursor_kind: timestamp`, `api_version: "3"` into the F029 provider registry; `adapters/jira.rs` implements `RecordSource::list_changes` over `updated` with a 2-minute overlap window, `describe_fields` from `/rest/api/3/field`, and `RecordSink::upsert` writing status through the transition graph, all on the F029 `HttpClient` and `TokenSource`; `schedule.rs` enqueues due active syncs each minute for `every_5m`, `every_15m`, `hourly`, and `daily_at_02_00_utc`, skipping syncs whose connection is not `active`; `webhook.rs` verifies the Jira `jira:issue_updated` signature and enqueues within 30 s; trigger holds a PostgreSQL advisory lock on `sync_id` so a second run returns `409 conflict`; events `sync.updated.v1`, `sync-run.started.v1`; error mapping `UnsupportedKind|InvalidFilter → 400 invalid`, `ConnectionNotActive|RunInProgress|StaleVersion → 409 conflict`, `NotFound → 404 not_found`, `Denied → 403 denied`.
- Dependencies: F029 provider registry, `TokenSource`, and `HttpClient`; F028 pagination, error envelope, and correlation IDs; F006 sheet and column metadata for target validation; F003 `Permission::IntegrationAdmin` plus sheet edit check; F004 JetStream job transport.
- Feature flag: `F030_FEATURE` gates routes, the registry entry, and the scheduler; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F030/api/registry_tests.rs::registry_lists_jira_with_work_kind`, `::registry_never_reads_oauth_tokens_table`; `testing/features/F030/api/sync_tests.rs::create_sync_returns_paused_version_one`, `::create_sync_rejects_unsupported_direction`, `::create_sync_on_needs_reauth_connection_conflicts`, `::patch_sync_stale_version_conflicts`, `::activate_sync_without_mappings_rejected`, `::list_syncs_filters_by_connector_and_state`, `::trigger_run_second_time_conflicts`, `::run_history_reports_counters_and_cursors`, `::member_cannot_create_sync`, `::admin_without_sheet_edit_denied`, `::foreign_tenant_sync_not_found`; `testing/features/F030/api/jira_tests.rs::jira_list_changes_applies_overlap_window`, `::jira_status_without_transition_fails_permanent`, `::jira_webhook_signature_rejected`; `testing/features/F030/database/migration_tests.rs::connectors_tables_exist_with_constraints`, `::active_sync_tuple_unique`, `::rollback_drops_connectors_tables`
- Targeted command: `cargo xtask test-feature F030`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/connectors.rs`; Jira REST v3 mock in `testing/harness/connectors/` with programmable pages, transition graphs, clock skew, and 429/5xx injection; F029 `TokenSource` stub; fixed clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes, registry entry, and scheduler registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes and no file under `services/api/src/integrations/` or `crates/domain/src/integrations/` is modified
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S059
- [ ] `finished_at` recorded
