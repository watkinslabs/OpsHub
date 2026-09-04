---
id: T209
type: task
status: planned
parent_epic: E008
parent_feature: F053
parent_story: S105
depends_on: [S105]
owned_paths: [services/api/migrations/*_datamesh_*.sql, crates/domain/src/datamesh/**, crates/persistence/src/datamesh/**, services/api/src/datamesh/**, testing/features/F053/database/**, testing/features/F053/api/**]
feature_flag: F053_FEATURE
branch: t209-mapping-schema
started_at: null
finished_at: null
---

# T209 — Mapping schema

## Identity

- Parent story: `S105` Reference mapping
- Owner: platform
- Branch: `t209-mapping-schema`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3; `docs/capability-contracts.md` row F053

## Objective

Create the six DataMesh tables with constraints and indexes, the mapping domain model with field-map validation, and the mapping list, create, and update routes behind the module guard.

## Specification

- Owned paths: `services/api/migrations/<ts>_datamesh_create_tables.sql`, `services/api/migrations/<ts>_datamesh_create_tables.down.sql`, `crates/domain/src/datamesh/{mod.rs, mapping.rs, field_map.rs, normalize.rs, errors.rs, service.rs, schema.rs}`, `crates/persistence/src/datamesh/{mod.rs, mapping_repository.rs}`, `services/api/src/datamesh/{mod.rs, routes.rs, handlers_mapping.rs, dto.rs}`
- Contract/input: DDL per F053 ticket section 4 — the `datamesh_mapping_match_keys` and `datamesh_mapping_field_maps` child tables that replace the former `match_keys`/`field_maps` `jsonb` columns, the `sync_mode`/`cron_expression` and cursor columns that replace `sync_mode jsonb` and `last_cursor jsonb`, declared foreign keys to `workspaces`, `sheets`, `columns`, `users`, and `datamesh_mappings`, `check (col in (...))` on every closed enum, the same-sheet check, target-row uniqueness in `datamesh_matches`, single-active-run and cursor-idempotency partial indexes, open-conflict uniqueness, and the listener and scheduler indexes; `CreateMappingRequest { name, source_sheet_id, target_sheet_id, match_keys, field_maps, sync_mode, unmatched_policy, deletion_policy }`, `UpdateMappingRequest` with `If-Match`; `Idempotency-Key` on every mutation; `validate_field_maps(source_cols, target_cols, maps)` using F007 column types and the F035 parser (`parse` only, 200-node cap); target-column ownership check across enabled mappings backed by the partial unique index on `datamesh_mapping_field_maps(tenant_id, target_column_id)`.
- Output/behavior: `GET /api/v1/datamesh/mappings`, `POST /api/v1/datamesh/mappings`, `PATCH /api/v1/datamesh/mappings/{id}` return `MappingResponse`; errors `400 invalid` with `field_errors.field_maps[i].<field>` or `field_errors.target_sheet_id = "same_as_source"`, `409 limit_reached` from the F048 entitlement `max_mappings`, `409 owned_by_mapping`, `409 conflict` on stale version, `404` cross-tenant; audit row and `mapping.updated.v1` written in the same transaction; `CreateMappingRequest`, `UpdateMappingRequest`, and `MappingResponse` keep `match_keys` and `field_maps` as JSON arrays and `sync_mode` as an object, so no external shape changes; `sqlx migrate run` and `revert` apply cleanly.
- Dependencies: F048 `RequireModule(ModuleSlug::Datamesh)` and limits; F003 authz and audit writer; F004 outbox writer; F006 sheet lookup; F007 column types; F035 parser.
- Data access: `MappingRepository` in `crates/persistence/src/datamesh/mapping_repository.rs` owns `datamesh_mappings`, `datamesh_mapping_match_keys`, and `datamesh_mapping_field_maps` and exposes `list_mappings_for_workspace`, `count_mappings_for_tenant`, `list_match_keys`, `replace_match_keys`, `list_field_maps`, `replace_field_maps`, and `find_field_map_owner_for_target_column`; `mapping.rs`, `field_map.rs`, `service.rs`, and the handlers hold no SQL and depend on the trait, and a create or update writes the mapping row, its match-key rows, its field-map rows, the audit row, and the outbox record in one `UnitOfWork` (decision section 2.1).
- Feature flag: `F053_FEATURE` gates router mounting.
- Large-table note: `datamesh_mapping_match_keys` and `datamesh_mapping_field_maps` hold at most 3 and 100 rows per mapping and are loaded with the parent in one query per mapping; `datamesh_matches` holds one row per source row per mapping; the `(mapping_id, key_hash)` index backs the join and is rebuilt per run.

## TDD

- Failing test first: `testing/features/F053/database/migration_tests.rs::datamesh_tables_exist_with_constraints`, `::same_sheet_mapping_rejected`, `::target_row_matched_once`, `::second_active_run_rejected`, `::duplicate_open_conflict_rejected`, `::match_key_ordinal_out_of_range_rejected`, `::field_map_row_unique_per_target_column`, `::target_column_owned_by_enabled_mapping_rejected`, `::scheduled_mapping_requires_cron_expression`, `::bidirectional_map_with_expression_rejected`, `::mapped_column_delete_restricted`, `::child_rows_cascade_on_mapping_purge`, `::rollback_drops_tables`; `testing/features/F053/api/mapping_tests.rs::mapping_create_returns_version_one`, `::mapping_same_sheet_invalid`, `::mapping_field_map_rejects_incompatible_types`, `::mapping_expression_over_200_nodes_invalid`, `::mapping_bidirectional_with_transform_invalid`, `::mapping_target_column_owned_conflicts`, `::mapping_limit_reached_conflicts`, `::mapping_no_entitlement_denied_by_guard`, `::mapping_cross_tenant_not_found`
- Targeted command: `cargo xtask test-feature F053`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; `testing/fixtures/datamesh.rs` tenants, entitlement, and the two sheets; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted in `services/api/src/router.rs` behind the guard; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S105
- [ ] `finished_at` recorded
