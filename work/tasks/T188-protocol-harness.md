---
id: T188
type: task
status: planned
parent_epic: E006
parent_feature: F047
parent_story: S094
depends_on: [S094]
owned_paths: [testing/harness/mcp/**, testing/features/F047/requirements/**, testing/features/F047/e2e/**, testing/features/F047/accessibility/**, testing/features/F047/performance/**]
feature_flag: F047_FEATURE
branch: t188-protocol-harness
started_at: null
finished_at: null
---

# T188 — Protocol harness

## Identity

- Parent story: `S094` MCP tools and safety
- Owner: platform
- Branch: `t188-protocol-harness`
- Decision references: `docs/architecture-decisions.md` sections 8, 9; `docs/capability-contracts.md` row F047

## Objective

Build the stub MCP client and the protocol conformance script that exercise the whole F047 surface in process with no network listener, plus the requirements traceability, browser, accessibility, and performance lanes that hang off it.

## Specification

- Owned paths: `testing/harness/mcp/{mod.rs, client.rs, script.rs, frames.rs, bus.rs}`, `testing/features/F047/requirements/cases.md`, `testing/features/F047/e2e/mcp.spec.ts`, `testing/features/F047/accessibility/mcp.a11y.spec.ts`, `testing/features/F047/performance/{transport_bench.rs, stream_bench.rs}`.
- Contract/input: `StubMcpClient::connect(service: tower::Service)` drives `POST /mcp/v1` in process; `call(method, params) -> JsonRpcResponse` records every request and response frame in `frames.rs` with its `correlation_id`; `script.rs` holds the recorded conformance sequence `initialize`, `resources/list`, `resources/read`, `tools/list`, `tools/call get_record`, `tools/call update_record` (proposal), the REST approval, and `tools/call update_record` (retry with `confirmation_id`); `bus.rs` feeds the SSE bridge from an in-memory outbox so `notifications/resources/updated` is deterministic.
- Output/behavior: the harness asserts JSON-RPC framing (`jsonrpc: "2.0"`, echoed `id`, exactly one of `result` or `error`), the negotiated `protocolVersion 2025-06-18`, the tool manifest hash, the `confirmation_required` structuredContent shape, the one-shot consumption, and that the run produced exactly one `mcp_audit` row per method call with matching `correlation_id`; it fails when any frame carries token material, a resource body, or verbatim tool arguments. It binds no port and starts no external process, so the lane is parallel-safe with one schema and one tenant per worker. `requirements/cases.md` maps every `FR-F047-NN` and `NFR-F047-NN` to its lane and case id. The E2E lane drives `/admin/mcp` through Playwright against the seeded tenant while the stub client plays the script from the server side. The accessibility lane runs axe on `/admin/mcp` and the call drawer and asserts the diff description list, the countdown live region, and dialog focus return. The performance lane measures `initialize` and `tools/list` under 100 ms p95, `tools/call` overhead under 30 ms p95 over the equivalent REST use case, and 200 concurrent SSE streams under 200 MB resident.
- Dependencies: the transport and manifest from T185, adapters from T186, the confirmation gate and `/admin/mcp` page from T187; `testing/fixtures/mcp.rs` seed data; `cargo xtask test-feature` lane wiring and `testing/evidence/F047/` artifact paths.
- Feature flag: `F047_FEATURE` selects the suite; `cargo xtask test-all` enables it with every other suite.

## TDD

- Failing test first: `testing/features/F047/e2e/mcp.spec.ts::approve_pending_mutation_and_retry_succeeds`, `::expired_confirmation_shows_expired_and_disables_approve`, `::activity_table_shows_confirmation_required_then_allowed`; `testing/harness/mcp/script.rs::conformance_script_frames_match_recording`, `::every_response_is_result_xor_error`, `::no_frame_contains_token_or_resource_body`; `testing/features/F047/accessibility/mcp.a11y.spec.ts::approvals_page_has_no_serious_axe_violations`, `::diff_exposed_as_labelled_description_list`, `::countdown_announced_at_five_and_one_minute`, `::approve_dialog_traps_and_returns_focus`; `testing/features/F047/performance/transport_bench.rs::initialize_and_tools_list_under_100ms`, `::tool_call_overhead_under_30ms`; `testing/features/F047/performance/stream_bench.rs::two_hundred_streams_under_200mb`
- Targeted command: `cargo xtask test-feature F047`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/mcp.rs`; the in-memory outbox bus; fixed clock `2026-09-03T00:00:00Z`, UTC, fixed UUIDv7 seeds and HMAC cursor key so recorded frames compare byte for byte

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Conformance script covers all five JSON-RPC methods, both REST routes, and the SSE stream, and runs with no port bound and no external process
- [ ] `requirements/cases.md` names every FR-F047 and NFR-F047 id with its lane
- [ ] Evidence written to `testing/evidence/F047/` for the api, database, frontend, e2e, accessibility, and performance lanes
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S094
- [ ] `finished_at` recorded
