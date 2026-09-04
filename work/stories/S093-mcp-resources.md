---
id: S093
type: story
status: planned
parent_epic: E006
parent_feature: F047
depends_on: [F047]
owned_paths: [crates/domain/src/mcp/**, crates/persistence/src/mcp/**, crates/contracts/src/mcp/**, services/mcp/src/mcp/**, testing/features/F047/api/**, testing/features/F047/performance/**]
feature_flag: F047_FEATURE
branch: s093-mcp-resources
started_at: null
finished_at: null
---

# S093 — MCP resources

## Identity

- Parent feature: `F047` MCP access server
- Owner: platform
- Branch: `s093-mcp-resources`
- Decision references: `docs/architecture-decisions.md` sections 1, 2, 2.1, 3, 8; `docs/capability-contracts.md` row F047

## Vertical slice

As a tenant member running an MCP client, I want `initialize`, `resources/list`, `resources/read`, and `tools/list` to work against `POST /mcp/v1` with a scoped API token, returning only the workspaces, documents, folders, projects, tasks, tickets, dashboards, workflows, and audit history I am already allowed to read, with inaccessible fields stripped and oversized bodies truncated, so that an assistant can ground itself in my real work without ever seeing something I cannot see.

## Requirements

- **SR-S093-01:** `POST /mcp/v1` parses JSON-RPC 2.0 single and batched (≤ 10) envelopes, dispatches `initialize`, `resources/list`, `resources/read`, `tools/list`, and maps domain errors to `-32602`, `-32001`, `-32002`, `-32003`, `-32004`, `-32005`, `-32601`, and `-32700`; `initialize` negotiates `2025-06-18` and advertises `resources.subscribe` and `tools.listChanged` (covers FR-F047-01).
- **SR-S093-02:** The transport authenticates only by `Authorization: Bearer oh_...` through the F038 bearer path, requires the `mcp:access` scope, and rejects cookies and scope-less tokens with `-32001` `denied` and `reason: invalid_token` (FR-F047-02, NFR-F047-02).
- **SR-S093-03:** `resources/list` builds `opshub://<kind>/<id>` descriptors for the nine kinds seeded in `mcp_resource_kinds`, taking each descriptor's `mimeType` and `<kind>:read` permission from that lookup row rather than from a per-adapter constant, pages at 100 with the F028 signed cursor, filters every candidate through `authz::check` before it enters the page, and `resources/read` dispatches to the matching `ResourceAdapter`, returning `-32002` `not_found` for both invisible and absent URIs; the URI string in every request and response is unchanged (FR-F047-03, FR-F047-04).
- **SR-S093-04:** Redaction strips fields the actor lacks `field:read` on, lists them in `annotations.redactedFields`, unconditionally removes the F027 secret list, and truncates above 256 KB at a record boundary with `annotations.truncated` and `annotations.nextCursor` (FR-F047-05).
- **SR-S093-05:** `tools/list` serves the manifest generated from `crates/contracts/src/mcp/manifest.rs`, omits tools whose required scope the token lacks, and read tools `search_records`, `get_record`, `list_children`, `get_report`, `get_workflow_runs` execute side-effect free with permission-filtered results (FR-F047-06, FR-F047-07).
- **SR-S093-06:** `GET /mcp/v1/sse` streams `notifications/resources/updated` and `notifications/resources/list_changed` for events on readable resources, heartbeats every 15 s, caps at 3 streams per token, resumes by `Last-Event-Id` inside 60 s, and closes with `denied` on token revocation or tenant suspension (FR-F047-13, NFR-F047-04).
- **SR-S093-07:** Every method call writes one `mcp_audit` row through `McpAuditRepository::append_audit_entry` — the target stored as the `resource_kind`/`resource_id` column pair, arguments only as `arguments_digest` — and publishes `mcp.resource-read.v1` for reads and `mcp.tool-called.v1` for read-tool calls (FR-F047-11).
- **SR-S093-08:** The `calls` and `search` rate buckets in `mcp_rate_limits` are enforced per token at 600/min and 120/min, with capacity, burst, and window read from the `mcp_rate_limit_buckets` policy row the bucket foreign-keys into, returning `-32004` with `retry_after_seconds` (FR-F047-12).
- **SR-S093-09:** `initialize` and `tools/list` respond under 100 ms p95, `resources/list` of 100 descriptors under 300 ms p95, `resources/read` of a 100 KB document under 400 ms p95, and 200 concurrent SSE streams stay under 200 MB resident (NFR-F047-01).

## Surfaces

- Infrastructure/container: `services/mcp` added to the Cargo workspace and the compose stack, reaching PostgreSQL only through `crates/persistence` and subscribing to the F004 event bus; it holds no pool and no database credentials of its own, and no inbound port is bound during tests
- Data access: `crates/persistence/src/mcp/{mod.rs, audit_repository.rs, rate_limit_repository.rs, resource_kind_repository.rs}` hold every SQL statement this slice issues — `McpAuditRepository` (`mcp_audit` and its partitions), `RateLimitRepository` (`mcp_rate_limits` plus the `mcp_rate_limit_buckets` policy rows), `ResourceKindRepository` (`mcp_resource_kinds`) — and the adapters read F045, F006, F023, F018, and F003 data through those features' repositories; `crates/domain/src/mcp/` and `services/mcp/src/mcp/` contain no `sqlx::query*` call, no connection, and no SQL string (decision section 2.1)
- Rust service/API: `crates/domain/src/mcp/{mod.rs, uri.rs, descriptor.rs, redaction.rs, tools.rs, errors.rs, service.rs, rate.rs, adapters/{mod.rs, workspace.rs, document.rs, folder.rs, project.rs, task.rs, ticket.rs, dashboard.rs, workflow.rs, audit.rs}}`; `crates/contracts/src/mcp/{manifest.rs, hash.rs}`; `services/mcp/src/mcp/{main.rs, jsonrpc.rs, dispatch.rs, sse.rs, state.rs, auth.rs}`
- Data/migration: reads only; the `mcp_audit`, `mcp_rate_limits`, and lookup reads and writes use the tables created by T187's migration
- React/UI: none in this story; the manifest and endpoint URL feed the `ConnectClientPanel` delivered in S094
- Mocks/fixtures: `testing/fixtures/mcp.rs`; in-process stub MCP client in `testing/harness/mcp/client.rs`; in-memory outbox bus for SSE; fixed clock and HMAC cursor key

## TDD harness

- Test path: `testing/features/F047/{api,performance}/`
- Feature flag: `F047_FEATURE`
- Targeted command: `cargo xtask test-feature F047`
- Full command: `cargo xtask test-all`
- First failing tests: `initialize_negotiates_protocol_and_capabilities`, `unsupported_protocol_version_returns_invalid`, `token_without_mcp_access_scope_denied`, `resources_list_filtered_by_permission`, `resource_read_invisible_uri_is_not_found`, `resource_read_strips_unreadable_fields`, `descriptor_mime_type_comes_from_resource_kind_row`, `tools_list_omits_tools_without_scope`, `sse_stream_drops_events_after_grant_removed`

## Exit criteria

- [ ] Requirement tests SR-S093-01 through SR-S093-09 written first and observed failing
- [ ] Tasks T185 and T186 complete and wired through the `services/mcp` router
- [ ] Unit, API, and performance lanes pass in targeted and full modes, including the permission-negative and cross-tenant cases
- [ ] Production call path named: `services/mcp/src/mcp/dispatch.rs` mounted by `services/mcp/src/mcp/main.rs` (`POST /mcp/v1`, `GET /mcp/v1/sse`); adapters registered in `crates/domain/src/mcp/adapters/mod.rs`
- [ ] `openapi/mcp-manifest.sha256` regenerated and `cargo xtask check-contracts` reports no drift
- [ ] `cargo xtask check-persistence` reports no SQL outside `crates/persistence/src/mcp/`
- [ ] Handoff evidence recorded in the F047 ticket
