---
id: T026
type: task
status: planned
parent_epic: E002
parent_feature: F007
parent_story: S013
depends_on: [T025]
owned_paths: [crates/domain/src/columns/**, services/api/src/columns/**, testing/features/F007/api/**, testing/features/F007/requirements/**]
feature_flag: F007_FEATURE
branch: t026-validation-engine
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 7
- Capability contract: `docs/capability-contracts.md` row F007

# T026 — Validation engine

## Identity

- Parent story: `S013` Column lifecycle
- Owner: platform
- Branch: `t026-validation-engine`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 7; `docs/capability-contracts.md` row F007

## Objective

Implement per-type normalization, the validation rule engine, the column service, and all six column HTTP routes with authorization, idempotency, optimistic concurrency, audit, outbox publication, and the async validate job.

## Specification

- Owned paths: `crates/domain/src/columns/{normalize.rs, validation.rs, validate_job.rs, errors.rs, service.rs}`, `services/api/src/columns/{mod.rs, routes.rs, handlers_column.rs, handlers_reorder.rs, handlers_validate.rs, job_dispatch.rs, dto.rs}`
- Contract/input: `CreateColumnRequest { type, label, description?, required?, width?, settings?, validation?, options? }`, `UpdateColumnRequest { label?, description?, required?, width?, hidden?, settings?, validation?, type?, options?, dry_run? }`, `ReorderColumnRequest { after_column_id? }`; headers `Idempotency-Key`, `If-Match`; validation rules `required | min | max | regex | allowed_options | date_range | unique`.
- Output/behavior: routes `GET/POST /api/v1/sheets/{sheet_id}/columns`, `PATCH/DELETE /api/v1/columns/{id}`, `POST /api/v1/columns/{id}/reorder`, `POST /api/v1/columns/{id}/validate` return `ColumnResponse`, `TypeChangePreview`, or `ValidateJobResponse`; a create or update writes the column, its one `column_settings` row, and its `column_validation_rules` rows atomically through `ColumnRepository`, replacing the rule set rather than merging it; `normalize` per type writes `cells.normalized` and `cells.display` through the F006 `CellRepository`; `evaluate` writes `cell_validation_states` with rule code and message through `CellValidationStateRepository`; the domain modules, handlers, and the job hold no SQL and take no SQLx dependency (decision 2.1); type or rule changes re-normalize synchronously up to 10,000 rows and dispatch job subject `columns.validate` above that; regex compiled with the `regex` crate under a 10 ms per-cell budget; events `column.created.v1`, `column.updated.v1`, `column.deleted.v1`, `column.reordered.v1` written to `outbox_events` in the same transaction; errors map per ticket section 4.
- Dependencies: T025 schema and enum; the `crates/persistence/src/columns/` repositories over those tables; F003 `authz::require(actor, Permission::SheetEdit, sheet)`; F004 `OutboxRepository` writer and JetStream job runtime; F006 `RowRepository` and `CellRepository`.
- Feature flag: `F007_FEATURE` gates router mounting and the job consumer registration.

## TDD

- Failing test first: `testing/features/F007/api/column_tests.rs::column_create_returns_version_one`, `::column_limit_501_rejected`, `::column_duplicate_label_conflicts`, `::column_rename_keeps_id_and_cells`, `::column_type_change_previews_invalid`, `::column_cross_tenant_not_found`, `::column_viewer_mutation_denied`; `testing/features/F007/api/validation_tests.rs::number_normalizes_with_precision`, `::person_outside_tenant_invalid`, `::regex_rule_records_code_and_message`, `::validate_job_acknowledges_under_two_seconds`
- Targeted command: `cargo xtask test-feature F007`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/columns.rs` tenants A and B, editor, viewer, one column per type; in-memory outbox recorder; inline job executor

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S013
- [ ] `finished_at` recorded
