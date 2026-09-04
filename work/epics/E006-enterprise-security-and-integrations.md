---
id: E006
type: epic
status: planned
owner: platform
target_milestone: M5
branch: e006-enterprise-security-and-integrations
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 4, 7, 8
- Capability contract: `docs/capability-contracts.md` rows F026, F063, F064, F065, F027, F028, F029, F030, F047
- Product spec: `docs/product-capability-spec.md` sections 5.8 (SEC-01..03), 5.9 (INT-01..03), 5.9a (MCP-01..03), Phase 5

# E006 — Enterprise security and integrations

## Outcome

An enterprise tenant can federate login through SAML 2.0, provision and deprovision people and groups through SCIM 2.0, enforce retention and legal hold, export or purge its own data with a verified confirmation step, and produce access-review reports without a support ticket. The same tenant can integrate OpsHub with the tools it already runs: a versioned REST API described by generated OpenAPI 3.1, signed webhooks with replay, OAuth connections to Microsoft 365, Google Workspace, and Slack, first-party connectors for Jira, Salesforce, Box, Dropbox, Tableau, and read-only databases, and one MCP server that exposes permission-filtered resources and confirmed mutations to agent clients. Every integration path shares the mapping, cursor, conflict, retry, replay, and audit contracts from decisions section 7, so a failure in any adapter is observable and recoverable through the same run history. Milestone M5.

## Scope

- Included: SAML connections with certificate rotation and clock-skew tolerance, SCIM users/groups with suspended-user and ownership-transfer policy, group-to-role mapping; retention policies, legal holds, tenant export, two-step purge, access-review reports; OpenAPI generation from `crates/contracts`, pagination/filter/field-selection/rate-limit conventions, API applications, HMAC-SHA256 webhooks with delivery log and replay; encrypted OAuth vault and Microsoft 365, Google Workspace, and Slack adapters for notifications and calendar/channel sync; connector framework with typed adapters for Jira, Salesforce, Box, Dropbox, Tableau, and allowlisted read-only database sources; `services/mcp` JSON-RPC server with generated resource and tool schemas, scope checks, rate limits, audit, and mutation confirmation.
- Excluded: OIDC login, sessions, MFA, and API tokens (F038); tenant, user, and group CRUD (F002); RBAC engine and audit log storage (F003); CSV/XLSX import and export jobs (F010); notification channels and preferences (F037); document storage (F045); Bridge multi-step cross-system workflows (F054); Data Shuttle and DataMesh (F052, F053); entitlement packaging (F048); provider adapters for AI features (F039, F040).

## Child features

- F026 SSO/SCIM: SAML 2.0 login with signed assertions and SCIM 2.0 lifecycle sync with group-to-role mapping (`sso` module).
- F063 Microsoft Entra integration: an optional tenant-level Entra ID connection adding Microsoft sign-in, directory group sync, and Graph mail delivery alongside the existing password, OIDC and SAML methods (`entra` module).
- F064 Billing and subscriptions: plan lifecycle, usage metering, invoices, payment-failure handling, and the provider adapter behind one billing port (`billing` module).
- F065 Self-serve signup and trials: public signup with verified email, anti-abuse, reserved slugs, and trial tenant provisioning that hands off to F064 (`signup` module).
- F027 Governance/compliance: retention, legal hold, tenant export, verified purge, and access-review reports (`compliance` module).
- F028 API/webhooks: generated OpenAPI 3.1, API applications, list conventions, rate-limit headers, and signed webhook delivery (`public-api` module).
- F029 Microsoft/Google/Slack: OAuth vault with envelope-encrypted refresh tokens and notification/sync adapters for three providers (`integrations` module).
- F030 Jira/Salesforce/files: connector framework with mappings, cursors, conflict policy, and replay for Jira, Salesforce, Box, Dropbox, Tableau, and databases (`connectors` module).
- F047 MCP access server: one versioned MCP server in `services/mcp` with generated resources and tools, scope checks, rate limits, audit, and mutation confirmation (`mcp` module).

## Exit criteria

- [ ] Phase 5 scenario passes end to end: a pilot enterprise tenant administrator configures a SAML connection, a user from the configured domain signs in through the identity provider, SCIM creates and later suspends a second user whose sheets transfer to a named owner, the administrator applies a legal hold, runs a tenant export, and confirms a purge that skips held records.
- [ ] An API application created by the same administrator lists rows through `/api/v1` with cursor pagination and rate-limit headers, receives a signed `row.updated.v1` webhook, replays a failed delivery, and sees the webhook disabled after ten consecutive failures.
- [ ] An OAuth connection to Slack delivers a notification, a Jira sync creates rows from issues, a conflicting edit on both sides is surfaced in `/syncs/{id}/conflicts`, and a replayed run reproduces the same result with no duplicate rows.
- [ ] An MCP client lists resources filtered by the actor's ACLs, calls a read tool, proposes a mutation that requires confirmation, and the approved mutation appears in `/api/v1/mcp/audit`.
- [ ] Security review passes with cross-tenant, role, guest, and scope negatives green for all six features; integration retries and conflicts are visible in run history and metrics.
- [ ] All six features accepted with their harness lanes green, flags off by default, and rollback verified.
