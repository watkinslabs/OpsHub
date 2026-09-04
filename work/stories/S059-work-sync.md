---
id: S059
type: story
status: planned
parent_epic: E006
parent_feature: F030
depends_on: [F030]
owned_paths: [crates/domain/src/connectors/**, crates/persistence/src/connectors/**, services/api/src/connectors/**, services/worker/src/connectors/**, apps/web/src/features/connectors/**, services/api/migrations/*_connectors_*.sql, testing/features/F030/**]
feature_flag: F030_FEATURE
branch: s059-work-sync
started_at: null
finished_at: null
---

# S059 — Work sync

## Identity

- Parent feature: `F030` Jira/Salesforce/files
- Owner: platform
- Branch: `s059-work-sync`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 7; `docs/capability-contracts.md` row F030

## Vertical slice

As an integration administrator, I want to define a Jira sync against a sheet, map issue fields to columns with validated transforms, preview the result on real records, run it on a schedule or on demand, and see what every run did, so that a delivery board stays aligned with Jira without anyone copying issues by hand.

This slice delivers the connector framework itself — the registry, the sync aggregate, the mapping and transform layer, the API surface, the migration, and the `/admin/syncs` UI — with Jira as the first connector proving it. S060 adds the remaining connectors and the durability half (cursors, retry, replay) on top of the same engine.

## Requirements

- **SR-S059-01:** `ConnectorRegistry` registers `jira` into the F029 provider registry with `sync_kinds: [work]`, `directions: [inbound, outbound, bidirectional]`, `cursor_kind: timestamp`, and `api_version: "3"`; F030 code reads tokens only through the F029 `TokenSource` and never touches `oauth_tokens` (covers FR-F030-01, NFR-F030-02).
- **SR-S059-02:** `POST /api/v1/syncs`, `GET /api/v1/syncs`, `GET /api/v1/syncs/{id}`, `PATCH /api/v1/syncs/{id}`, and `POST /api/v1/syncs/{id}/pause` implement the sync lifecycle with `expected_version`, `Idempotency-Key`, `sync.updated.v1`, and `409 conflict` on stale versions, an inactive connection, or an unsupported direction (FR-F030-02, FR-F030-03, FR-F030-04).
- **SR-S059-03:** `PUT /api/v1/syncs/{id}/mappings` replaces the whole mapping set in one `SyncMappingRepository::replace_mapping_set` transaction that rewrites `sync_mappings`, `sync_mapping_transform_args`, and `sync_mapping_value_map` together, enforcing per-direction uniqueness of `external_field` and `column_id`, the 300-mapping cap, unique argument names and `value_map` external values per mapping, the `required`/`default_value` rule, and transform-to-column type compatibility with `field_errors["mappings[N].transform"]`; the request and response keep `transform: { name, args }` (FR-F030-05).
- **SR-S059-04:** The transform catalog `identity`, `trim`, `lower`, `upper`, `date_tz`, `datetime_format`, `number_scale`, `value_map`, `join`, `split`, `template`, and `lookup` is the `sync_mappings.transform_name` check constraint, its scalar arguments are `sync_mapping_transform_args` rows and its `value_map` pairs are `sync_mapping_value_map` rows loaded once per run through `list_mappings_with_transforms`; evaluation is pure, within 5 ms per cell, with no network or filesystem access, and a failing transform marks one record `mapping_failed` instead of aborting the run (FR-F030-06, NFR-F030-01, NFR-F030-02).
- **SR-S059-05:** `POST /api/v1/syncs/{id}/run` enqueues a run and returns `202` in under 2 s with per-sync concurrency 1, and `connectors.schedule` enqueues due active syncs for `every_5m`, `every_15m`, `hourly`, and `daily_at_02_00_utc`, skipping syncs whose F029 connection is not `active` and accepting a signature-verified Jira `jira:issue_updated` webhook as a fast path (FR-F030-07, FR-F030-08).
- **SR-S059-06:** The Jira adapter lists changes by `updated` with a 2-minute overlap window, describes fields through `/rest/api/3/field` including `customfield_*`, writes status through the legal transition graph, and fails a record `permanent` with code `no_transition` when none exists (FR-F030-16).
- **SR-S059-07:** `GET /api/v1/syncs/{id}/runs` returns run history from `SyncRunRepository::list_runs_for_sync` with `state`, `trigger`, the `records_read`, `records_created`, `records_updated`, `records_skipped`, `records_conflicted`, and `records_failed` columns presented as the `counters` object, durations, cursor before and after, and up to 50 `sync_run_failed_records` rows presented as `failed_samples` (FR-F030-11).
- **SR-S059-08:** `deletion_policy` `ignore`, `mark_deleted`, and `soft_delete` behave per spec and never issue a hard delete on either side; `mark_deleted` requires `deletion_column_id` (FR-F030-15).
- **SR-S059-09:** Every route requires `integration-admin` plus edit permission on `target_sheet_id`; a member gets `403 denied`, an admin without sheet edit rights gets `403 denied`, and foreign-tenant IDs get `404 not_found` (FR-F030-20).
- **SR-S059-10:** `/admin/syncs`, `/admin/syncs/new`, and `/admin/syncs/:syncId` render the sync list, the three-step wizard with the mapping editor and five-record preview, and the run history table with loading, empty, error, denied, and success states, keyboard-only mapping reorder, and axe-clean output (FR-F030-21, NFR-F030-03).

## Surfaces

- Infrastructure/container: no new services; the run job publishes to the existing JetStream stream and takes a PostgreSQL advisory lock keyed on `sync_id`
- Data access: `crates/persistence/src/connectors/{mod.rs, sync_repository.rs, mapping_repository.rs, run_repository.rs}` hold every SQL statement for this slice — `SyncRepository` owns `syncs` and `sync_database_objects`, `SyncMappingRepository` owns `sync_mappings`, `sync_mapping_transform_args`, and `sync_mapping_value_map`, `SyncRunRepository` owns `sync_runs` and `sync_run_failed_records`; the domain services, the `services/api/src/connectors` handlers, the Jira adapter, and `services/worker/src/connectors/{schedule.rs, webhook.rs}` depend on those traits and contain no `sqlx::query*` call or pool of their own (decision section 2.1)
- Rust service/API: `crates/domain/src/connectors/{mod.rs, registry.rs, sync.rs, errors.rs, service.rs, adapter.rs, mapping/{mod.rs, transform.rs, validate.rs}, adapters/jira.rs}`; `services/api/src/connectors/{mod.rs, routes.rs, handlers_sync.rs, handlers_mapping.rs, handlers_run.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_connectors_create_tables.sql` creating `syncs`, `sync_mappings`, `sync_mapping_transform_args`, `sync_mapping_value_map`, `sync_runs`, `sync_run_failed_records`, `sync_cursors`, `sync_conflicts`, `sync_conflict_fields`, `sync_record_links`, and `sync_database_objects` with the foreign keys, enum checks, and indexes from ticket section 4
- React/UI: `apps/web/src/features/connectors/{SyncListPage.tsx, SyncWizard.tsx, ConnectionObjectStep.tsx, MappingEditor.tsx, MappingRow.tsx, TransformPicker.tsx, MappingPreview.tsx, PolicyStep.tsx, SyncDetailPage.tsx, RunHistoryTable.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/connectors.rs`; the Jira REST v3 mock in `testing/harness/connectors/` with programmable pages, clock skew, transition graphs, and 429/5xx injection; F029 `TokenSource` stub

## TDD harness

- Test path: `testing/features/F030/{api,database,frontend}/`
- Feature flag: `F030_FEATURE`
- Targeted command: `cargo xtask test-feature F030`
- Full command: `cargo xtask test-all`
- First failing tests: `registry_lists_jira_with_work_kind`, `create_sync_rejects_unsupported_direction`, `create_sync_on_needs_reauth_connection_conflicts`, `replace_mappings_rejects_duplicate_column`, `replace_mappings_rewrites_transform_arg_rows`, `value_map_rejects_duplicate_external_value`, `transform_date_tz_converts_to_column_timezone`, `unknown_transform_returns_field_error`, `trigger_run_second_time_conflicts`, `jira_status_without_transition_fails_permanent`, `member_cannot_create_sync`

## Exit criteria

- [ ] Requirement tests SR-S059-01 through SR-S059-10 written first and failing
- [ ] Tasks T117 and T118 complete and wired through the API router and worker registry
- [ ] Unit, API, database, React, accessibility, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/connectors/routes.rs` mounted in `services/api/src/router.rs` at `/api/v1/syncs` and `/api/v1/sync-runs`; `services/worker/src/connectors/schedule.rs` registered in `services/worker/src/registry.rs`
- [ ] Handoff evidence recorded in the F030 ticket
