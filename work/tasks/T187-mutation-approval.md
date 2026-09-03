---
id: T187
type: task
status: planned
parent_epic: E006
parent_feature: F047
parent_story: S094
depends_on: [S094]
owned_paths: [services/api/migrations/*_mcp_*.sql, crates/domain/src/mcp/**, services/api/src/mcp/**, apps/web/src/features/mcp/**, testing/features/F047/api/**, testing/features/F047/database/**, testing/features/F047/frontend/**]
feature_flag: F047_FEATURE
branch: t187-mutation-approval
started_at: null
finished_at: null
---

# T187 — Mutation approval

## Identity

- Parent story: `S094` MCP tools and safety
- Owner: platform
- Branch: `t187-mutation-approval`
- Decision references: `docs/architecture-decisions.md` sections 8, 9; `docs/capability-contracts.md` row F047

## Objective

Create the `mcp` schema and implement the two-phase mutation gate: propose with a field-level change summary, approve through the REST route, consume exactly once on retry, log every call in an append-only partitioned audit table, and expose the approvals and activity page at `/admin/mcp`.

## Specification

- Owned paths: `services/api/migrations/<ts>_mcp_create_tables.sql` and `.down.sql`, `crates/domain/src/mcp/{confirmation.rs, summary.rs, mutation.rs, audit.rs}`, `services/api/src/mcp/{mod.rs, routes.rs, handlers_audit.rs, handlers_confirmation.rs, dto.rs}`, `apps/web/src/features/mcp/{McpPage.tsx, PendingApprovalsTable.tsx, ChangeSummaryDiff.tsx, ApproveDialog.tsx, ExpiryCountdown.tsx, McpActivityTable.tsx, McpCallDrawer.tsx, ConnectClientPanel.tsx, api.ts, hooks.ts, routes.ts}`.
- Contract/input: `tools/call` arguments for `create_record`, `update_record`, `add_comment`, `assign_record`, `run_workflow`, optionally carrying `confirmation_id`; `POST /api/v1/mcp/confirmations/{id}/approve` with an empty body and a required `Idempotency-Key`; `GET /api/v1/mcp/audit` with `cursor`, `limit` (≤ 200), `actor_id`, `method`, `tool`, `decision`, `outcome`, `resource_uri`, `correlation_id`, `occurred_from`, `occurred_to`.
- Output/behavior: the first mutating call validates arguments against the manifest schema, evaluates `authz::require`, builds `ChangeSummary { resource_uri, operation, changes: [{ field, before, after }] }`, inserts `mcp_confirmations` with `arguments_hash` (SHA-256 of canonical JSON), `status: pending`, `expires_at = now + 15 minutes`, publishes `mcp.mutation-proposed.v1`, and returns `isError: true` with `structuredContent { code: "confirmation_required", confirmation_id, expires_at, summary }` and no write. Approve requires the proposing actor or `tenant-admin`, sets `approved`, `approved_by`, `approved_at`, publishes `mcp.mutation-confirmed.v1`, returns `409 conflict` on expired, approved, or consumed rows and `404 not_found` cross-tenant. Retry with `confirmation_id` requires `approved`, unexpired, and a matching hash, runs the domain use case with `Idempotency-Key mcp:<confirmation_id>`, and marks `consumed` in the same transaction; mismatch returns `-32602` with `reason: arguments_changed`, wrong state returns `-32003`. Migration creates `mcp_confirmations`, monthly-partitioned append-only `mcp_audit` with the F003 `audit_immutable` trigger and three months of partitions, and `mcp_rate_limits`, with the checks, the partial unique index `mcp_confirmations_open_idx`, and the indexes listed in ticket section 4. A one-minute sweeper marks expired rows and expiry is also re-checked at read time. `/admin/mcp` renders the approvals table, the diff as a description list, the countdown announced at 5 and 1 minutes, the confirm dialog, the activity table with filters and the call drawer, and the connect panel; `409` renders in place as `Expired`.
- Dependencies: F003 `record_audit`, `authz::require`, and the immutability trigger; F038 sessions and tokens; F028 list conventions, error schema, and idempotency replay; F004 outbox and the job registry; the transport and manifest from T185; the summary inputs from T186 adapters.
- Feature flag: `F047_FEATURE` gates the two REST routes, the sweeper job, and the `/admin/mcp` route; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F047/api/mutation_tests.rs::mutating_tool_first_call_writes_nothing`, `::proposal_returns_confirmation_required_with_diff`, `::proposal_publishes_mutation_proposed_event`, `::retry_with_changed_arguments_rejected`, `::approved_confirmation_consumed_once`, `::pending_confirmation_retry_returns_conflict`, `::mutations_bucket_caps_at_sixty_per_minute`; `testing/features/F047/api/confirmation_route_tests.rs::approve_requires_proposer_or_admin`, `::approve_expired_returns_conflict`, `::approve_foreign_tenant_returns_not_found`, `::approve_replays_idempotency_key`; `testing/features/F047/api/audit_route_tests.rs::audit_list_scopes_non_admin_to_own_rows`, `::audit_list_filters_by_tool_and_decision`; `testing/features/F047/database/migration_tests.rs::mcp_tables_exist_with_checks_and_indexes`, `::mcp_audit_rows_are_immutable`, `::open_confirmation_unique_per_arguments_hash`, `::audit_partitions_created_three_months_ahead`, `::rollback_drops_mcp_tables`; `testing/features/F047/frontend/PendingApprovalsTable.test.tsx::renders_diff_and_countdown_for_pending_row`, `::expired_row_disables_approve_in_place`, `testing/features/F047/frontend/McpActivityTable.test.tsx::filters_by_decision_and_opens_drawer`
- Targeted command: `cargo xtask test-feature F047`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/mcp.rs` write-scoped token, proposing member, a second member, a tenant-admin, task `Ship beta` with `due_date 2026-09-10`; fixed clock for the 15-minute expiry cases; MSW handlers for the frontend lane

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18 with partitions, checks, and the immutability trigger verified
- [ ] Routes and the sweeper registered behind the flag; OpenAPI regenerated without drift
- [ ] No mutating `ToolHandler` can execute without a consumed confirmation, enforced by an enumerating test over the tool manifest
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S094
- [ ] `finished_at` recorded
