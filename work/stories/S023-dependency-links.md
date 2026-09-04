---
id: S023
type: story
status: planned
parent_epic: E003
parent_feature: F012
depends_on: [F009, F011]
owned_paths: [crates/domain/src/dependencies/**, crates/persistence/src/dependencies/**, services/api/src/dependencies/**, services/api/migrations/*_dependencies_*.sql, testing/features/F012/**]
feature_flag: F012_FEATURE
branch: s023-dependency-links
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Capability contract: `docs/capability-contracts.md` row F012

# S023 — Dependency links

## Identity

- Parent feature: `F012` Dependencies and Gantt
- Owner: platform
- Branch: `s023-dependency-links`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F012

## Vertical slice

As a project editor, I want to create, list, update, and delete typed dependencies between rows of a sheet, have cycles and duplicates rejected, and read a critical path computed with the working calendar, so that the plan's ordering is explicit and the longest chain is visible before any Gantt UI exists.

## Requirements

- **SR-S023-01:** `POST /api/v1/dependencies` with `{ predecessor_row_id, successor_row_id, kind, lag?, lag_unit? }` inserts a `row_dependencies` row through `RowDependencyRepository`, returns `DependencyResponse` with version 1, and publishes `dependency.created.v1` (covers FR-F012-01).
- **SR-S023-02:** Self links, cross-sheet pairs, parent rows, and lag outside ±3,650 days or ±87,600 hours return `400 invalid` with the field error named in the ticket (FR-F012-02, FR-F012-07, FR-F012-09).
- **SR-S023-03:** A candidate edge that closes a cycle returns `400 invalid` with `field_errors.successor_row_id = "cycle"` and `details.cycle_path`; the check runs on the in-memory graph from `load_graph_for_sheet` while the use case holds F011's `lock_for_schedule(sheet_id)` row lock, so concurrent inserts cannot both pass (FR-F012-03).
- **SR-S023-04:** A duplicate pair, found by `RowDependencyRepository::find_pair`, returns `409 conflict` with `details.existing_id`; the 20,001st dependency on a sheet returns `400 invalid` with `field_errors.sheet_id = "limit"` (FR-F012-04, FR-F012-05).
- **SR-S023-05:** `GET /api/v1/sheets/{sheet_id}/dependencies` pages by cursor with `limit` ≤ 1,000 and `row_id`/`kind` filters; `PATCH` and `DELETE` require `If-Match`, emit `dependency.updated.v1` / `dependency.deleted.v1`, and write audit rows (FR-F012-06).
- **SR-S023-06:** `GET /api/v1/sheets/{sheet_id}/critical-path` runs the forward/backward pass for FS, SS, FF, SF with signed day and hour lag, rolls up parents, treats zero-duration rows as milestones, persists results through `ScheduleResultRepository::upsert_schedule_results`, and returns `is_critical` for zero-float rows (FR-F012-08, FR-F012-09, FR-F012-10).
- **SR-S023-07:** Foreign-tenant actors receive `404 not_found` on every route and viewers receive `403 denied` on mutations (FR-F012-15, NFR-F012-02).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/dependencies/{mod.rs, dependency.rs, graph.rs, cycle.rs, critical_path.rs, errors.rs, service.rs}` (no SQL); `crates/persistence/src/dependencies/{mod.rs, row_dependency_repository.rs, schedule_result_repository.rs}`; `services/api/src/dependencies/{mod.rs, routes.rs, handlers_dependency.rs, handlers_critical_path.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_dependencies_create_tables.sql` creating `row_dependencies` and `schedule_results` with indexes from ticket section 4
- React/UI: none in this story (S024 covers the Gantt)
- Mocks/fixtures: `testing/fixtures/dependencies.rs` tenant, sheet with F011 schedule settings and Mon–Fri calendar, editor, viewer, foreign tenant, 12 rows, 9 dependencies; in-memory outbox recorder

## TDD harness

- Test path: `testing/features/F012/api/` and `testing/features/F012/database/`
- Feature flag: `F012_FEATURE`
- Targeted command: `cargo xtask test-feature F012`
- Full command: `cargo xtask test-all`
- First failing tests: `dependency_create_returns_version_one`, `dependency_cycle_rejected_with_path`, `dependency_duplicate_pair_conflicts`, `critical_path_marks_zero_float_rows`, `dependency_cross_tenant_not_found`

## Exit criteria

- [ ] Requirement tests SR-S023-01 through SR-S023-07 written first and failing
- [ ] Tasks T045 and T046 complete and wired through `services/api` router
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/dependencies/routes.rs` mounted in `services/api/src/router.rs`
- [ ] Handoff evidence recorded in the F012 ticket
