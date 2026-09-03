---
id: T173
type: task
status: planned
parent_epic: E000
parent_feature: F044
parent_story: S087
depends_on: [S087]
owned_paths: [automation/xtask/src/release.rs, testing/features/F044/api/**, testing/features/F044/requirements/**, testing/features/F044/performance/**]
feature_flag: F044_FEATURE
branch: t173-openapi-event-drift
started_at: null
finished_at: null
---

# T173 — OpenAPI/event drift

## Identity

- Parent story: `S087` Contract drift
- Owner: platform
- Branch: `t173-openapi-event-drift`
- Decision references: `docs/architecture-decisions.md` sections 3, 8; `docs/capability-contracts.md` row F044

## Objective

Implement catalog parsing and the ticket, OpenAPI, event registry, generated client, and MCP schema drift checks behind `check-contracts`, replacing the row-existence check in `main.rs`.

## Specification

- Owned paths: `automation/xtask/src/release.rs` (`ContractRow`, `Route`, `EventName`, `Catalog`, `OpenApiDoc`, `Operation`, `parse_catalog`, `check_ticket_against_row`, `check_owned_paths_against_row`, `check_openapi`, `check_event_registry`, `check_generated_client`, `check_mcp_schemas`, `check_contracts`)
- Contract/input: `docs/capability-contracts.md` tables; feature tickets from the F041 `WorkGraph`; optional `openapi/v1.json`, `crates/events/src/registry.rs`, `apps/web/src/api/generated/manifest.json`, `services/mcp/schemas/manifest.json`
- Output/behavior: findings `contract.catalog`, `contract.row_missing`, `contract.row_orphan`, `contract.route_missing_in_ticket`, `contract.event_missing_in_ticket`, `contract.route_not_in_row`, `contract.event_not_in_row`, `contract.paths_mismatch`, `contract.decision_link`, `openapi.route_missing`, `openapi.orphan_operation`, `openapi.feature_mismatch`, `events.registry_missing`, `events.registry_orphan`, `events.payload_shape`, `client.stale`, `mcp.schema_stale`, `mcp.tool_missing`; each drift message carries `expected: <x>, found: <y>` and the line in the ticket or document; route paths normalised by replacing `{…}` segments with `{}` before comparison, raw path kept in the message; absent optional inputs print `skipped: <path> absent`; `check-contracts` also runs `validate-decisions` first as today
- Dependencies: F041 loader and reporter; F042 glob helpers for path implication
- Feature flag: `F044_FEATURE`
- Budget: under 3 s for 61 tickets, 2 MiB OpenAPI, 500 migrations

## TDD

- Failing test first: `testing/features/F044/api/catalog_tests.rs::catalog_row_with_empty_cell_rejected`, `::event_without_v1_rejected`, `::duplicate_row_id_rejected`, `::ticket_missing_row_event_reported_with_expected_found`, `::ticket_extra_route_not_in_row_reported`, `::tooling_row_compares_surface_commands`, `::owned_paths_missing_module_glob_reported`, `testing/features/F044/api/openapi_tests.rs::openapi_missing_route_reported_after_param_normalisation`, `::orphan_operation_without_internal_flag_reported`, `::event_registry_payload_shape_checked`, `::stale_client_hash_reported`, `::mcp_manifest_hash_and_tool_coverage_checked`, `::absent_optional_inputs_skipped`, `testing/features/F044/performance/contracts_bench.rs::check_contracts_under_3s`
- Targeted command: `cargo xtask test-feature F044`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/features/F044/fixtures/{catalog,openapi}`; generated 61-ticket tree for the benchmark

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `check-contracts` dispatched from `main()` through `release.rs`; live repository passes with optional inputs skipped
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S087
- [ ] `finished_at` recorded
