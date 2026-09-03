---
id: T186
type: task
status: planned
parent_epic: E006
parent_feature: F047
parent_story: S093
depends_on: [S093]
owned_paths: [crates/domain/src/mcp/**, testing/features/F047/api/**, testing/features/F047/performance/**]
feature_flag: F047_FEATURE
branch: t186-resource-adapters
started_at: null
finished_at: null
---

# T186 — Resource adapters

## Identity

- Parent story: `S093` MCP resources
- Owner: platform
- Branch: `t186-resource-adapters`
- Decision references: `docs/architecture-decisions.md` sections 3, 8; `docs/capability-contracts.md` row F047

## Objective

Implement the `opshub://` URI scheme, the nine `ResourceAdapter` implementations behind `resources/list` and `resources/read`, the shared redaction and truncation pass, and the five side-effect-free read tools, all reading through the canonical domain read models rather than any parallel query path.

## Specification

- Owned paths: `crates/domain/src/mcp/{uri.rs, descriptor.rs, redaction.rs, read_tools.rs}` and `crates/domain/src/mcp/adapters/{mod.rs, workspace.rs, document.rs, folder.rs, project.rs, task.rs, ticket.rs, dashboard.rs, workflow.rs, audit.rs}`.
- Contract/input: `ResourceUri::parse` accepts `^opshub://(workspace|document|folder|project|task|ticket|dashboard|workflow|audit)/[0-9a-f-]{36}$`; `list(ctx, cursor, kind?)` takes the F028 signed cursor and a 100 cap; `read(ctx, id)` takes the parsed URI; read tools take `search_records { query (1–256), kinds?, workspace_id?, limit? (1–50, default 20) }`, `get_record { uri }`, `list_children { uri, cursor? }`, `get_report { uri, parameters? }`, `get_workflow_runs { uri, limit? (1–10) }`.
- Output/behavior: descriptors carry `uri`, `name`, `mimeType` (`text/markdown` for `document`, `application/json` otherwise), `description`, and `annotations.lastModified`. Every candidate passes `authz::require(&ctx, <kind>:read, resource)` before entering a page, so page sizes differ per actor and an invisible or absent URI both yield `NotVisible → -32002 not_found`. `document` reads the current F045 revision body with `revision` and `updated_at`; `folder` lists child folders and documents; `project`, `task`, and `ticket` return the typed record with resolved column values; `dashboard` returns widget definitions with last computed values; `workflow` returns the definition and its last 10 runs; `audit` returns the F003 audit page for the referenced resource. `redaction.rs` removes attributes the actor lacks `field:read` on into `annotations.redactedFields`, unconditionally strips the F027 secret list (token material, password hashes, webhook secrets, OAuth ciphertext), and truncates above 256 KB at a record boundary setting `annotations.truncated` and `annotations.nextCursor`. `search_records` returns `uri`, `title`, `snippet`, `score` ordered by rank, permission-filtered, never cached across actors, and stable for identical arguments within one second. Every read publishes `mcp.resource-read.v1` and hands an `McpAuditEntry` with `redacted_field_count` to the sink.
- Dependencies: F003 permission evaluation and audit reads; F045 documents, folders, and revisions; F006 typed records and column values; F028 cursor signing; the transport, manifest, and audit sink from T185.
- Feature flag: `F047_FEATURE` gates adapter registration in `adapters/mod.rs`; the domain crate compiles either way.

## TDD

- Failing test first: `testing/features/F047/api/uri_tests.rs::uri_round_trips_all_nine_kinds`, `::unknown_kind_returns_invalid`, `::foreign_tenant_id_returns_not_found`; `testing/features/F047/api/resource_tests.rs::resources_list_filtered_by_permission`, `::resources_list_pages_at_hundred_with_signed_cursor`, `::resource_read_invisible_uri_is_not_found`, `::document_read_returns_current_revision_body`, `::workflow_read_returns_definition_and_last_ten_runs`, `::every_resource_kind_has_a_permission_negative_case`; `testing/features/F047/api/redaction_tests.rs::resource_read_strips_unreadable_fields`, `::secret_fields_never_serialized`, `::oversized_body_truncated_at_record_boundary`; `testing/features/F047/api/read_tool_tests.rs::search_records_is_permission_filtered_and_ranked`, `::read_tools_write_nothing`, `::get_report_rejects_limit_over_fifty`; `testing/features/F047/performance/resource_bench.rs::resources_list_hundred_under_300ms`, `::document_read_100kb_under_400ms`
- Targeted command: `cargo xtask test-feature F047`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/mcp.rs` tenants A and B, three workspaces, 40 tasks with 12 visible to the read-only actor, 12 tickets, 6 documents with revisions, 2 dashboards, 2 workflows, and a 5,000-resource generator for the performance lane

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] All nine adapters registered and reachable through `resources/list` and `resources/read`; no adapter issues a query outside the canonical read models
- [ ] Permission-negative case present for every `ResourceKind` variant, enforced by an enumerating test
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S093
- [ ] `finished_at` recorded
