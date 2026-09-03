---
id: T185
type: task
status: planned
parent_epic: E006
parent_feature: F047
parent_story: S093
depends_on: [S093]
owned_paths: [services/mcp/src/mcp/**, crates/contracts/src/mcp/**, crates/domain/src/mcp/**, testing/features/F047/api/**]
feature_flag: F047_FEATURE
branch: t185-mcp-server-boundary
started_at: null
finished_at: null
---

# T185 — MCP server boundary

## Identity

- Parent story: `S093` MCP resources
- Owner: platform
- Branch: `t185-mcp-server-boundary`
- Decision references: `docs/architecture-decisions.md` sections 1, 3, 8; `docs/capability-contracts.md` row F047

## Objective

Stand up `services/mcp` as the JSON-RPC 2.0 boundary for `POST /mcp/v1` and `GET /mcp/v1/sse`: envelope parsing and batching, bearer authentication and scope gating, the error-code map, the generated tool manifest served by `tools/list`, the SSE notification bridge, and the per-token rate buckets. Resource content itself is T186's work; this task owns everything between the socket and the adapter trait.

## Specification

- Owned paths: `services/mcp/src/mcp/{main.rs, jsonrpc.rs, dispatch.rs, auth.rs, sse.rs, state.rs, errors.rs}`, `crates/contracts/src/mcp/{mod.rs, manifest.rs, hash.rs}`, `crates/domain/src/mcp/{mod.rs, tools.rs, errors.rs, rate.rs, service.rs}`.
- Contract/input: JSON-RPC 2.0 request objects or a batch array of at most 10; methods `initialize`, `resources/list` `{ cursor?, kind? }`, `resources/read` `{ uri }`, `tools/list` `{}`, `tools/call` `{ name, arguments, confirmation_id? }`; header `Authorization: Bearer oh_...`; SSE query `Last-Event-Id`.
- Output/behavior: `initialize` returns `protocolVersion 2025-06-18`, `serverInfo { name: "opshub", version }`, and `capabilities { resources: { subscribe: true, listChanged: true }, tools: { listChanged: true }, logging: {} }`; an unsupported version returns `-32602` with `data.supported`; unknown method `-32601`; malformed JSON `-32700`; batch above 10 `-32602`. `auth.rs` resolves the F038 bearer token into `ActorContext`, requires the `mcp:access` scope, refuses cookies, and returns `-32001` with `data { code: "denied", reason: "invalid_token", correlation_id }` at HTTP 200. `errors.rs` maps `invalid → -32602`, `denied → -32001`, `not_found → -32002`, `conflict → -32003`, `rate_limited → -32004`, `unavailable → -32005`. `manifest.rs` derives the ten tool definitions and their draft 2020-12 input schemas from the same typed DTOs the OpenAPI generator uses, `hash.rs` writes `openapi/mcp-manifest.sha256`, and `tools/list` omits any tool whose `required_scope` is absent from the token. `rate.rs` implements the `calls` (600/min, burst 1,200), `mutations` (60/min), and `search` (120/min) token buckets against `mcp_rate_limits` with a single `INSERT ... ON CONFLICT DO UPDATE`, returning `retry_after_seconds`. `sse.rs` subscribes to the F004 bus, filters each event through `authz::check` before emitting `notifications/resources/updated`, emits `notifications/resources/list_changed` on grant changes, heartbeats `:heartbeat` every 15 s, caps 3 streams per token, replays by `Last-Event-Id` inside 60 s, and closes with `denied` on revocation or tenant suspension. `dispatch.rs` wraps every call in a span carrying `correlation_id` and `tool`, times it, and hands the audit record to the sink.
- Dependencies: F038 bearer authentication and scopes; F003 `authz::check`; F028 signed cursors and error vocabulary; F004 event bus, metrics, and pool; the `mcp_rate_limits` and `mcp_audit` tables created by T187.
- Feature flag: `F047_FEATURE` gates the `services/mcp` router and the SSE endpoint; the manifest builds regardless so the drift gate always runs.

## TDD

- Failing test first: `testing/features/F047/api/jsonrpc_tests.rs::initialize_negotiates_protocol_and_capabilities`, `::unsupported_protocol_version_returns_invalid`, `::unknown_method_returns_method_not_found`, `::malformed_json_returns_parse_error`, `::batch_over_ten_rejected`, `::domain_errors_map_to_jsonrpc_codes`; `testing/features/F047/api/auth_tests.rs::token_without_mcp_access_scope_denied`, `::revoked_token_denied_with_invalid_token_reason`, `::session_cookie_is_not_accepted`; `testing/features/F047/api/manifest_tests.rs::tools_list_omits_tools_without_scope`, `::manifest_hash_matches_checked_in_file`; `testing/features/F047/api/rate_tests.rs::calls_bucket_returns_rate_limited_with_retry_after`, `::mutations_bucket_is_separate_from_application_budget`; `testing/features/F047/api/sse_tests.rs::sse_stream_drops_events_after_grant_removed`, `::sse_resumes_by_last_event_id_within_window`, `::fourth_stream_per_token_rejected`
- Targeted command: `cargo xtask test-feature F047`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/mcp.rs` tokens with and without `mcp:access`; the in-process stub MCP client in `testing/harness/mcp/client.rs`; in-memory outbox bus; fixed clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `services/mcp` builds in the workspace, routes register behind the flag, and no test binds a network port
- [ ] `openapi/mcp-manifest.sha256` regenerated; `cargo xtask check-contracts` reports no drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S093
- [ ] `finished_at` recorded
