---
id: S094
type: story
status: planned
parent_epic: E006
parent_feature: F047
depends_on: [F047]
owned_paths: [crates/domain/src/mcp/**, services/api/src/mcp/**, apps/web/src/features/mcp/**, services/api/migrations/*_mcp_*.sql, testing/features/F047/**]
feature_flag: F047_FEATURE
branch: s094-mcp-tools-and-safety
started_at: null
finished_at: null
---

# S094 — MCP tools and safety

## Identity

- Parent feature: `F047` MCP access server
- Owner: platform
- Branch: `s094-mcp-tools-and-safety`
- Decision references: `docs/architecture-decisions.md` sections 8, 9; `docs/capability-contracts.md` row F047

## Vertical slice

As a tenant member whose assistant wants to change my work, I want every mutating MCP tool to pause and show me a field-level diff that I approve at `/admin/mcp` before anything is written, with the approval good for exactly one execution of exactly those arguments, and I want a tamper-proof log of every MCP call, so that giving an assistant write access is a reviewable act rather than a standing grant.

## Requirements

- **SR-S094-01:** The mutating tools `create_record`, `update_record`, `add_comment`, `assign_record`, `run_workflow` validate arguments, evaluate authorization, build a `ChangeSummary` of `{ field, before, after }`, insert a `pending` `mcp_confirmations` row with `arguments_hash` and `expires_at = now + 15 minutes`, publish `mcp.mutation-proposed.v1`, and return `structuredContent.code: confirmation_required` without writing (covers FR-F047-08).
- **SR-S094-02:** `POST /api/v1/mcp/confirmations/{id}/approve` requires a session actor that proposed it or a `tenant-admin`, requires `Idempotency-Key`, sets `approved`, publishes `mcp.mutation-confirmed.v1`, returns `409 conflict` for expired, approved, or consumed rows, and `404 not_found` cross-tenant (FR-F047-09).
- **SR-S094-03:** A retry carrying `confirmation_id` executes only when the row is `approved`, unexpired, and the arguments hash matches; it writes with `Idempotency-Key mcp:<confirmation_id>` and marks the row `consumed` in the same transaction, so a second retry returns `-32003` `conflict` and a changed argument returns `-32602` with `reason: arguments_changed` (FR-F047-10).
- **SR-S094-04:** The `mutations` rate bucket caps mutating tool calls at 60 per minute per token, separate from the F028 per-application budget, returning `-32004` with `retry_after_seconds` (FR-F047-12).
- **SR-S094-05:** `mcp_audit` records one row per call with `decision`, `outcome`, `error_code`, `duration_ms`, `redacted_field_count`, and `correlation_id`, is monthly-partitioned and append-only under the F003 `audit_immutable` trigger, and `GET /api/v1/mcp/audit` pages newest first with the documented filters, scoping non-admins to their own rows (FR-F047-11, FR-F047-14).
- **SR-S094-06:** `/admin/mcp` renders pending approvals with the tool, linked target resource, `ChangeSummaryDiff`, `ExpiryCountdown`, and an `Approve` confirm dialog, plus the `McpActivityTable` with filters, the call drawer, and the `ConnectClientPanel`; expired rows grey out in place and `409` renders as `Expired` rather than an error toast (FR-F047-15).
- **SR-S094-07:** `/admin/mcp` passes axe with zero serious or critical violations, exposes the diff as a labelled description list, announces the countdown at 5 minutes and 1 minute through a polite live region, traps focus in the dialog, and returns focus to the row's `Approve` button (NFR-F047-03).
- **SR-S094-08:** Confirmation expiry is swept every minute and re-checked at read time, `mcp_confirmations` carries the status checks and the partial unique index on open proposals, and metrics `mcp_calls_total`, `mcp_confirmations_total`, and `mcp_rate_limited_total` are emitted (NFR-F047-04).
- **SR-S094-09:** The protocol conformance harness drives the whole flow through the in-process stub MCP client with no network listener, replaying `initialize`, `resources/list`, `resources/read`, `tools/list`, a read `tools/call`, a mutating `tools/call`, the approval, and the retry, and asserting the recorded frames and the resulting `mcp_audit` rows (NFR-F047-02).

## Surfaces

- Infrastructure/container: none beyond the `services/mcp` service introduced in S093; the approval route is mounted on the existing session-authenticated `services/api` router
- Rust service/API: `crates/domain/src/mcp/{confirmation.rs, summary.rs, mutation.rs, audit.rs}`; `services/api/src/mcp/{mod.rs, routes.rs, handlers_audit.rs, handlers_confirmation.rs, dto.rs}`; the confirmation sweeper registered as a one-minute job
- Data/migration: `services/api/migrations/<ts>_mcp_create_tables.sql` and `.down.sql` creating `mcp_confirmations`, partitioned `mcp_audit` with the `audit_immutable` trigger, and `mcp_rate_limits` with the indexes from ticket section 4
- React/UI: `apps/web/src/features/mcp/{McpPage.tsx, PendingApprovalsTable.tsx, ChangeSummaryDiff.tsx, ApproveDialog.tsx, ExpiryCountdown.tsx, McpActivityTable.tsx, McpCallDrawer.tsx, ConnectClientPanel.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/mcp.rs` write-scoped tokens and a tenant-admin; `testing/harness/mcp/{client.rs, script.rs}` stub client and recorded conformance script; fixed clock for expiry cases

## TDD harness

- Test path: `testing/features/F047/{api,database,frontend,e2e,accessibility}/`
- Feature flag: `F047_FEATURE`
- Targeted command: `cargo xtask test-feature F047`
- Full command: `cargo xtask test-all`
- First failing tests: `mutating_tool_first_call_writes_nothing`, `proposal_returns_confirmation_required_with_diff`, `approve_requires_proposer_or_admin`, `retry_with_changed_arguments_rejected`, `approved_confirmation_consumed_once`, `mcp_audit_rows_are_immutable`, `audit_list_scopes_non_admin_to_own_rows`, `approvals_page_has_no_serious_axe_violations`

## Exit criteria

- [ ] Requirement tests SR-S094-01 through SR-S094-09 written first and observed failing
- [ ] Tasks T187 and T188 complete and wired through the `services/api` router and the `services/mcp` dispatcher
- [ ] API, database, frontend, E2E, and accessibility lanes pass in targeted and full modes, including permission-negative and cross-tenant cases
- [ ] Production call path named: `services/api/src/mcp/routes.rs` mounted in `services/api/src/router.rs` (`/api/v1/mcp`); `crates/domain/src/mcp/mutation.rs` invoked from `services/mcp/src/mcp/dispatch.rs`
- [ ] Migration applies and reverts on CI PostgreSQL 18 with partitions and the immutability trigger verified
- [ ] Handoff evidence recorded in the F047 ticket
