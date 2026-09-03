---
id: T097
type: task
status: planned
parent_epic: E005
parent_feature: F025
parent_story: S049
depends_on: [S049]
owned_paths: [services/api/migrations/*_report_exports_*.sql, crates/domain/src/report_exports/**, services/api/src/report_exports/**, testing/features/F025/api/**, testing/features/F025/database/**]
feature_flag: F025_FEATURE
branch: t097-secure-drill-through
started_at: null
finished_at: null
---

# T097 — Secure drill-through

## Identity

- Parent story: `S049` Source drill-through
- Owner: platform
- Branch: `t097-secure-drill-through`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 6; `docs/capability-contracts.md` row F025

## Objective

Create the `report_exports` schema and implement viewer-scoped drill-through: the drill key codec, row and group resolution over F021 snapshots, denied-source handling, the drill route, and the `drill-through.opened.v1` event with its audit row.

## Specification

- Owned paths: `services/api/migrations/<ts>_report_exports_create_tables.sql` and `.down.sql`, `crates/domain/src/report_exports/{mod.rs, drill.rs, drill_key.rs, job.rs, errors.rs, service.rs}`, `services/api/src/report_exports/{mod.rs, routes.rs, handlers_drill.rs, dto.rs}`
- Contract/input: `GET /api/v1/reports/{id}/drill/{row_id}` where `row_id` is a snapshot UUIDv7 or `group:<base64url>`; query `snapshot_id?`, `cursor?`, `limit?` (1..200); caller context supplies tenant, actor, and the F021 `ViewerScope` with its `scope_key`.
- Output/behavior: `DrillResponse` for a row target and `DrillRowsPage` for a group target as specified in ticket section 4; `drill_key.rs` encodes canonical JSON of `{ widget_id, dimensions, filters, snapshot_id }` plus a truncated SHA-256 tag and rejects a bad tag with `DrillError::BadKey → 400 invalid`; `drill.rs` reads the snapshot through F021 `read_rows`, maps aliases to sheets from the report definition, batches one row query per readable sheet, marks unreadable sheets `denied` without issuing a query, strips hidden columns, and fills `restricted_sources`, `hidden_columns`, `meta.aggregate_scope`, and `meta.hidden_row_count`; unknown row → `404 not_found`, unretained `snapshot_id` → `409 conflict` with `reason: "snapshot_expired"` and the current snapshot; every call publishes `drill-through.opened.v1` and writes the `report.drill-through` audit row; deep links are `/w/{workspace_id}/sheets/{sheet_id}?row={source_row_id}` for allowed sources and `null` otherwise.
- Migration: `report_exports` with the columns, check constraints, unique `(tenant_id, requested_by, idempotency_key)`, and the three indexes from ticket section 4, plus the matching down migration.
- Dependencies: F021 `read_rows`, `ViewerScope`, and snapshot retention; F023 widget config for group dimensions; F003 authz `read` on the report; F036 share-link guest scope; F004 outbox and audit writer.
- Feature flag: `F025_FEATURE` gates the route; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F025/api/drill_tests.rs::drill_row_returns_sources_with_deep_links`, `::drill_row_unknown_id_returns_not_found`, `::drill_group_key_pages_contributing_rows`, `::drill_group_tampered_key_rejected`, `::drill_expired_snapshot_returns_conflict`, `::drill_denies_restricted_sheet_without_query`, `::drill_strips_hidden_columns`, `::drill_owner_policy_reports_hidden_row_count`, `::drill_publishes_opened_event_and_audit`, `::foreign_tenant_report_drill_not_found`; `testing/features/F025/database/migration_tests.rs::report_exports_table_exists_with_constraints`, `::idempotency_key_unique_per_requester`, `::rollback_drops_report_exports`
- Targeted command: `cargo xtask test-feature F025`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/report_exports.rs` (report "Portfolio status" with a 100,000-row snapshot, restricted "Risks" sheet, hidden `Budget.margin`, owner-policy variant, share-link guest); in-memory outbox recorder; fixed clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; route registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S049
- [ ] `finished_at` recorded
