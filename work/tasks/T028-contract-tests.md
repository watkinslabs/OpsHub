---
id: T028
type: task
status: planned
parent_epic: E002
parent_feature: F007
parent_story: S014
depends_on: [T027]
owned_paths: [testing/features/F007/api/**, testing/features/F007/requirements/**, testing/features/F007/performance/**, testing/features/F007/e2e/**]
feature_flag: F007_FEATURE
branch: t028-contract-tests
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 9
- Capability contract: `docs/capability-contracts.md` row F007

# T028 — Contract tests

## Identity

- Parent story: `S014` Validation
- Owner: platform
- Branch: `t028-contract-tests`
- Decision references: `docs/architecture-decisions.md` sections 3, 9; `docs/capability-contracts.md` row F007

## Objective

Complete the F007 harness: OpenAPI contract tests for all six routes and four events, the requirements traceability table, the end-to-end browser flow, and the performance lane for column list, create, and the 100,000-row validate job.

## Specification

- Owned paths: `testing/features/F007/api/{contract_tests.rs, event_tests.rs}`, `testing/features/F007/requirements/cases.md`, `testing/features/F007/e2e/columns.spec.ts`, `testing/features/F007/performance/{column_list_bench.rs, validate_job_bench.rs}`
- Contract/input: generated `openapi/v1.json` schemas for `CreateColumnRequest`, `UpdateColumnRequest`, `ReorderColumnRequest`, `ColumnResponse`, `TypeChangePreview`, `ValidateJobResponse`; outbox payload schema `{ tenant_id, actor_id, aggregate_id, version, changed_fields, correlation_id, occurred_at }`; seeded tenant with a 500-column sheet and a 100,000-row sheet.
- Output/behavior: every route response validates against its schema for success and each error code (`invalid`, `denied`, `not_found`, `conflict`); every mutation produces exactly one outbox event whose name is one of `column.created.v1`, `column.updated.v1`, `column.deleted.v1`, `column.reordered.v1` with correct `changed_fields`; E2E covers add select column, reorder, type change with preview, validate column, viewer read-only; performance lane asserts p95 column list < 500 ms at 500 columns, create p95 < 800 ms, validate job under 60 s with acknowledgement under 2 s; `cargo xtask check-contracts` passes with no drift.
- Dependencies: T027 UI for E2E; T026 routes; `testing/harness/` Playwright and k6 runners; seeded fixtures from `testing/fixtures/columns.rs`.
- Feature flag: `F007_FEATURE` selects the suite; `test-all` includes it.

## TDD

- Failing test first: `testing/features/F007/api/contract_tests.rs::every_column_route_matches_openapi`, `::error_codes_match_schema`, `testing/features/F007/api/event_tests.rs::each_mutation_emits_one_named_event`; `testing/features/F007/e2e/columns.spec.ts::add_select_column_reorder_and_validate`, `::viewer_cannot_edit_columns`; `testing/features/F007/performance/column_list_bench.rs::column_list_500_p95`, `validate_job_bench.rs::validate_100k_rows_under_60s`
- Targeted command: `cargo xtask test-feature F007`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: real API against seeded tenant; k6 for latency percentiles; fixed seed and clock

## Exit criteria

- [ ] Tests written before the remaining implementation gaps and observed failing
- [ ] Contract, requirements, E2E, and performance lanes pass; evidence under `testing/evidence/F007/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S014
- [ ] `finished_at` recorded
