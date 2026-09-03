# F047 — MCP access server harness

Feature-gated tests for `F047`. Keep test code in this directory.

- Gate: `F047_FEATURE`
- Targeted: `cargo xtask test-feature F047`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/mcp.rs` (tenants A and B; a read-only member with `mcp:access` and `records:read`; a write member with `records:write` and `workflows:run`; a tenant-admin; three workspaces with 40 tasks of which 12 are readable by the read-only member, 12 tickets, 6 documents with revisions, 2 dashboards, 2 workflows with 14 runs; one API token per actor; a 5,000-resource generator and a 1,000,000-row audit generator for the performance lane; fixed clock `2026-09-03T00:00:00Z`, UTC, fixed UUIDv7 seeds and HMAC cursor key).
- Protocol harness: `testing/harness/mcp/{client.rs, script.rs, frames.rs, bus.rs}` — an in-process JSON-RPC 2.0 stub MCP client over a `tower::Service` that binds no port and starts no external process, records every request and response frame, and replays the conformance script (`initialize`, `resources/list`, `resources/read`, `tools/list`, read `tools/call`, mutating `tools/call`, REST approval, retry). The SSE bridge is fed by the in-memory outbox bus in `bus.rs`.
- Manifest: tool schemas compare against `openapi/mcp-manifest.sha256`; drift fails `cargo xtask check-contracts`.
- Lanes: `requirements/` (traceability for every FR-F047 and NFR-F047 id), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the requirement IDs they prove.
