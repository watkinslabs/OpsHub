---
id: S111
type: story
status: planned
parent_epic: E008
parent_feature: F056
depends_on: [F021, F048]
owned_paths: [crates/domain/src/pivots/**, services/api/src/pivots/**, services/api/migrations/*_pivots_*.sql, testing/features/F056/**]
feature_flag: F056_FEATURE
branch: s111-pivot-configuration
started_at: null
finished_at: null
---

# S111 — Pivot configuration

## Identity

- Parent feature: `F056` Pivot App
- Owner: platform
- Branch: `s111-pivot-configuration`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 7; `docs/capability-contracts.md` row F056

## Vertical slice

As a report editor with the Pivot entitlement, I want to define, validate, list, update, and delete a pivot over a sheet or report, and have the aggregation engine compute a permission-filtered result, so that a saved analysis definition exists before any output history or UI is built.

## Requirements

- **SR-S111-01:** `POST /api/v1/pivots` with `{ name, source, row_dimensions, column_dimensions?, measures, filters?, refresh_policy? }` validates cardinality (1–3 row, 0–2 column, 1–10 measures) and column types against F007 metadata, then inserts `pivots` and returns `PivotResponse` with version 1 (covers FR-F056-01, FR-F056-02, FR-F056-03).
- **SR-S111-02:** Every `/api/v1/pivots` route calls `authz::require_entitlement(tenant, "pivot")` first and returns `403 denied` with `field_errors.entitlement = "pivot"` when it is missing or `F056_FEATURE` is off; a foreign tenant receives `404 not_found` (FR-F056-04).
- **SR-S111-03:** `GET /api/v1/pivots` pages by cursor, filters by `workspace_id` and `source_id`, and sorts by `name` or `updated_at`; `PATCH /api/v1/pivots/{id}` requires `If-Match` and returns `409 conflict` with `current_version` when stale (FR-F056-11).
- **SR-S111-04:** `DELETE /api/v1/pivots/{id}` soft-deletes the pivot and hides its outputs; every mutation writes an audit event and publishes `pivot.updated.v1` with `changed_fields` (FR-F056-11, FR-F056-13).
- **SR-S111-05:** `crates/domain/src/pivots/aggregate.rs` folds only rows returned by the F021 permission-aware query for the requesting actor, buckets dates in the tenant timezone, and computes `sum`, `count`, `avg`, `min`, `max`, `count_distinct` with exact decimals (FR-F056-06).
- **SR-S111-06:** A source with more than 100,000 visible rows or a fold exceeding 50,000 cells stops with `PivotError::SourceTooLarge` (FR-F056-07).
- **SR-S111-07:** The migration creates `pivots` and `pivot_outputs` with the check constraints, unique name index, and one-active-output partial index from ticket section 4 (NFR-F056-02).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/pivots/{mod.rs, pivot.rs, dimension.rs, measure.rs, aggregate.rs, errors.rs, service.rs}`; `services/api/src/pivots/{mod.rs, routes.rs, handlers_pivot.rs, dto.rs, entitlement.rs}`
- Data/migration: `services/api/migrations/<ts>_pivots_create_tables.sql` and `.down.sql`
- React/UI: none in this story (S112 and T223 cover UI)
- Mocks/fixtures: `testing/fixtures/pivots.rs` entitled and unentitled tenants, editor, viewer, foreign tenant, 2,000-row sheet, report hiding 300 rows

## TDD harness

- Test path: `testing/features/F056/api/`, `testing/features/F056/database/`
- Feature flag: `F056_FEATURE`
- Targeted command: `cargo xtask test-feature F056`
- Full command: `cargo xtask test-all`
- First failing tests: `pivot_create_returns_version_one`, `pivot_bucket_on_text_column_invalid`, `pivot_missing_entitlement_denied`, `pivot_cross_tenant_not_found`, `aggregate_excludes_hidden_rows`, `aggregate_month_bucket_uses_tenant_timezone`

## Exit criteria

- [ ] Requirement tests SR-S111-01 through SR-S111-07 written first and failing
- [ ] Tasks T221 and T222 complete and wired through `services/api` router
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/pivots/routes.rs` mounted in `services/api/src/router.rs` behind `F056_FEATURE`
- [ ] Handoff evidence recorded in the F056 ticket
