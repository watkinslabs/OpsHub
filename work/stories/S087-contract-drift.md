---
id: S087
type: story
status: planned
parent_epic: E000
parent_feature: F044
depends_on: [F041, F042]
owned_paths: [automation/xtask/src/release.rs, testing/features/F044/**]
feature_flag: F044_FEATURE
branch: s087-contract-drift
started_at: null
finished_at: null
---

# S087 — Contract drift

## Identity

- Parent feature: `F044` Contract/release control
- Owner: platform
- Branch: `s087-contract-drift`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 8; `docs/capability-contracts.md` row F044

## Vertical slice

As a maintainer, I want `check-contracts` to prove that every ticket, the frozen catalog, the OpenAPI document, the event registry, the generated client, and the MCP schemas agree, and `check-migrations` to prove that every migration is named, paired, owned, ordered, immutable, and safe, so that drift between the contract and the code fails the commit instead of the release.

## Requirements

- **SR-S087-01:** `parse_catalog` builds `ContractRow` values from both tables, rejects empty cells, duplicate ids, malformed events, and unknown route prefixes, and enforces one row per feature ticket (covers FR-F044-01).
- **SR-S087-02:** Every route and event in a row appears verbatim in the ticket's section 4, and every route-like or event-like backticked string there is in the row; tooling rows compare `Surface` commands (FR-F044-02).
- **SR-S087-03:** Feature `owned_paths` contain the module-slug globs and the harness glob, and the ticket links the decisions file and cites its row (FR-F044-03).
- **SR-S087-04:** When present, OpenAPI operations, event registry constants and payload fields, the generated client hash, and the MCP schema hash and tool coverage match the catalog; absent inputs print `skipped` and pass (FR-F044-04, FR-F044-05, FR-F044-06).
- **SR-S087-05:** Migration filenames, `up`/`down` pairing, module ownership, and header comments are validated (FR-F044-07).
- **SR-S087-06:** Migration timestamps are unique and increasing, branch migrations are newer than `origin/main`'s newest, and files on `origin/main` are byte-identical (FR-F044-08).
- **SR-S087-07:** Destructive statements are classified statically and must be declared in the header and justified in the ticket; `down` files reference every created object (FR-F044-09, NFR-F044-02).
- **SR-S087-08:** Both commands support `--json`, show `expected`/`found` pairs, and meet the 3-second budget (FR-F044-16, NFR-F044-01, NFR-F044-03).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `automation/xtask/src/release.rs` (`ContractRow`, `Route`, `EventName`, `Catalog`, `OpenApiDoc`, `Migration`, `MigrationHeader`, `StatementKind`, `parse_catalog`, `check_ticket_against_row`, `check_openapi`, `check_event_registry`, `check_generated_client`, `check_mcp_schemas`, `check_contracts`, `load_migrations`, `check_migration_names`, `check_migration_order`, `check_migration_safety`, `check_migrations`)
- Data/migration: none executed; `services/api/migrations/*.sql` read statically
- React/UI: none (no UI)
- Mocks/fixtures: `testing/features/F044/fixtures/{catalog,openapi,migrations}` with feature `F900` module `widgets`, a fixture OpenAPI document, registry source, client and MCP manifests, and migration pairs including a destructive one

## TDD harness

- Test path: `testing/features/F044/api/`, `testing/features/F044/database/`, `testing/features/F044/performance/`
- Feature flag: `F044_FEATURE`
- Targeted command: `cargo xtask test-feature F044`
- Full command: `cargo xtask test-all`
- First failing tests: `catalog_row_with_empty_cell_rejected`, `ticket_missing_row_event_reported_with_expected_found`, `ticket_extra_route_not_in_row_reported`, `openapi_missing_route_reported_after_param_normalisation`, `stale_client_hash_reported`, `migration_without_down_reported`, `branch_migration_older_than_main_reported`, `drop_column_without_declaration_is_destructive`

## Exit criteria

- [ ] Requirement tests SR-S087-01 through SR-S087-08 written first and failing
- [ ] Tasks T173 and T174 complete; `check-contracts` and `check-migrations` dispatched from `main()` through `release.rs`
- [ ] Unit, CLI integration, static-analysis, and performance tests pass in targeted and full modes; the live repository passes both commands
- [ ] Production call path named: `release::check_contracts` and `release::check_migrations` dispatched from `main()` in `automation/xtask/src/main.rs`, invoked by `.githooks/pre-commit`, `.githooks/pre-push`, and `gates.yml`
- [ ] Handoff evidence recorded in the F044 ticket
