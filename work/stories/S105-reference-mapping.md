---
id: S105
type: story
status: planned
parent_epic: E008
parent_feature: F053
depends_on: [F009, F035, F048]
owned_paths: [crates/domain/src/datamesh/**, services/api/src/datamesh/**, services/worker/src/datamesh/**, services/api/migrations/*_datamesh_*.sql, testing/features/F053/**]
feature_flag: F053_FEATURE
branch: s105-reference-mapping
started_at: null
finished_at: null
---

# S105 — Reference mapping

## Identity

- Parent feature: `F053` DataMesh
- Owner: platform
- Branch: `s105-reference-mapping`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 7, 10; `docs/capability-contracts.md` row F053

## Vertical slice

As a data administrator, I want to define a mapping between a master sheet and a target sheet by normalized key columns and field maps, and preview exactly which rows match, which would be created or updated, and which are ambiguous, so that I can trust the sync before any cell changes.

Out of this slice: executing the sync, write-back, conflicts, triggers, and the UI (S106); file ingestion (F052); external system sync (F030).

## Requirements

- **SR-S105-01:** `POST /api/v1/datamesh/mappings` and `PATCH /api/v1/datamesh/mappings/{id}` persist `match_keys`, `field_maps`, `sync_mode`, `unmatched_policy`, and `deletion_policy` with the validation rules of the ticket and return `MappingResponse` with `version`; same source and target sheet returns `400 invalid` (covers FR-F053-01, FR-F053-02).
- **SR-S105-02:** Field map validation rejects foreign columns, incompatible types without a transform, expressions the F035 parser rejects or over 200 AST nodes, and transforms on `bidirectional` maps with `400 invalid` and `field_errors.field_maps[i].<field>`; a target column already owned by another enabled mapping returns `409 conflict` (FR-F053-02).
- **SR-S105-03:** `compute_matches` normalizes keys per `Normalize`, joins source and target by `key_hash`, stores one match per source row and at most one per target row in `datamesh_matches`, and reports many-to-one and one-to-many cases as `ambiguous_match` conflicts (FR-F053-03).
- **SR-S105-04:** `POST /api/v1/datamesh/mappings/{id}/preview` returns counts and a 50-row sample without writing cells, completes within 30 seconds on 100,000 × 100,000 rows, caches by mapping version for 10 minutes, and redacts columns the caller cannot read (FR-F053-04, NFR-F053-01, NFR-F053-02).
- **SR-S105-05:** `GET /api/v1/datamesh/mappings` lists mappings with cursor paging; creating past `max_mappings` returns `409 conflict` with `field_errors.mappings = "limit_reached"`; every route sits behind `RequireModule(ModuleSlug::Datamesh)` (FR-F053-10, FR-F053-12).
- **SR-S105-06:** Every mapping mutation requires `Idempotency-Key` and `If-Match`, writes an audit row with diff, and publishes `mapping.updated.v1`; cross-tenant ids return `404 not_found` (FR-F053-11, FR-F053-13).

## Surfaces

- Infrastructure/container: none beyond the F004 baseline
- Rust service/API: `crates/domain/src/datamesh/{mod.rs, mapping.rs, field_map.rs, normalize.rs, matching.rs, preview.rs, errors.rs, service.rs}`; `services/api/src/datamesh/{mod.rs, routes.rs, handlers_mapping.rs, handlers_preview.rs, dto.rs}`; `services/worker/src/datamesh/{mod.rs, match_engine.rs}`
- Data/migration: `services/api/migrations/<ts>_datamesh_create_tables.sql` creating `datamesh_mappings`, `datamesh_matches`, `datamesh_runs`, `datamesh_conflicts` with the indexes from ticket section 4
- React/UI: none in this story (S106 covers the editor, preview, runs, and conflicts UI)
- Mocks/fixtures: `testing/fixtures/datamesh.rs` tenants A/B, data-admin, editor, viewer, active entitlement with limits, `Vendors master` (1,000 rows) and `Purchase requests` (1,200 rows) sheets; in-memory outbox recorder; 100,000-row generators for the preview benchmark

## TDD harness

- Test path: `testing/features/F053/api/`, `testing/features/F053/database/`, `testing/features/F053/performance/`
- Feature flag: `F053_FEATURE`
- Targeted command: `cargo xtask test-feature F053`
- Full command: `cargo xtask test-all`
- First failing tests: `mapping_create_returns_version_one`, `mapping_same_sheet_invalid`, `mapping_field_map_rejects_incompatible_types`, `mapping_expression_over_200_nodes_invalid`, `match_engine_flags_ambiguous_matches`, `preview_counts_match_fixture`, `preview_redacts_unreadable_columns`, `mapping_limit_reached_conflicts`

## Exit criteria

- [ ] Requirement tests SR-S105-01 through SR-S105-06 written first and failing
- [ ] Tasks T209 and T210 complete and wired through `services/api` router
- [ ] Unit, API, database, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/datamesh/routes.rs` mounted in `services/api/src/router.rs` behind `RequireModule(ModuleSlug::Datamesh)`; `services/worker/src/datamesh/match_engine.rs` used by the preview handler through `crates/domain/src/datamesh/preview.rs`
- [ ] Handoff evidence recorded in the F053 ticket
