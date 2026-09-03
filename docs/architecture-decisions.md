# OpsHub architecture decisions

Status: FROZEN 2026-09-03. These decisions are prerequisites for implementation and ticket generation.

## 1. Runtime and repository

- Rust 2024 stable for `services/api`, `services/worker`, `services/realtime`, `services/mcp`, and shared crates.
- Axum + Tokio for HTTP/WebSocket services; SQLx + PostgreSQL 18 for transactional data.
- React 19 + TypeScript + Vite for `apps/web`; TanStack Router/Query for routes and server state.
- Monorepo paths: `apps/web`, `services/{api,worker,realtime,mcp}`, `crates/{domain,persistence,contracts,auth,events}`, `infra`, `testing`.

## 2. Canonical data model

- PostgreSQL is the only source of truth for tenant metadata, work records, permissions, workflows, documents, and audit history.
- Every tenant-owned row has UUIDv7 `id`, `tenant_id`, created/updated actor and timestamps, and `version`.
- Soft deletion is default; purge requires a privileged, audited job.
- All writes require an idempotency key and optimistic version check.
- Changes publish through a transactional outbox; consumers are idempotent.

## 3. API and events

- REST JSON API under `/api/v1`; OpenAPI 3.1 is generated from typed Rust contracts.
- Errors use `{ code, message, field_errors, correlation_id }`; clients branch on `code`, never message text.
- Cursor pagination uses opaque signed cursors; mutation responses return the new version.
- NATS JetStream is the event bus and durable job transport. Event names are `<aggregate>.<verb>.v1`.
- Webhooks use HMAC-SHA256 signatures, delivery IDs, exponential retry, replay, and disable-after-failure.

## 4. Identity and authorization

- OIDC is the primary login protocol; SAML 2.0 is the enterprise federation protocol.
- SCIM 2.0 manages users/groups; WebAuthn and TOTP provide MFA.
- Authorization is deny-by-default RBAC plus resource ACLs. Folder/document access inherits downward; explicit denies win.
- Every service receives `{ tenant_id, actor_id, roles, scopes, correlation_id }` from the authenticated gateway context.
- Authorization is enforced in service code and tested with cross-tenant, role, guest, link, and field-level negatives.

## 5. Files, documents, and collaboration

- S3-compatible object storage holds files and immutable document revisions; PostgreSQL stores metadata and checksums.
- ClamAV scanning and MIME/size allowlists run before a file becomes downloadable.
- Browser clients use WebSocket sessions for presence and sheet patches; document bodies use Automerge CRDT updates persisted by revision.
- Presence leases expire after 30 seconds and are renewed every 10 seconds.
- Reconnect requests missing revisions; unresolved conflicts remain visible and are never silently overwritten.

## 6. Web experience

- Self-hosted Inter variable font is the primary typeface with system sans fallback.
- Lucide SVG icons are the only functional icon set; icons require accessible labels and never replace text for destructive actions.
- CSS tokens define color, spacing, type, focus, motion, and density. WCAG 2.2 AA is the acceptance target.
- UI states are explicit: loading, empty, error, denied, stale, conflict, offline, and success.

## 7. Jobs and integrations

- `services/worker` consumes JetStream jobs with per-tenant quotas, bounded retries, dead letters, timeout, and run history.
- OAuth refresh tokens are encrypted with envelope keys from the deployment secret manager.
- External integrations use typed adapters behind a common cursor, mapping, conflict, and replay contract.
- Local development uses Docker Compose with PostgreSQL, NATS, MinIO, and Mailpit; production deploys the same images.

## 8. MCP

- `services/mcp` is one versioned MCP server over the canonical domain/API contracts; features do not create separate sources of truth.
- Resources are permission-filtered snapshots or cursors. Tools require actor context, scopes, idempotency keys, audit events, and mutation confirmation.
- MCP discovery and tool schemas are generated from `crates/contracts`; drift fails CI.

## 9. Testing

- Rust tests use `cargo test`; React tests use Vitest; browser tests use Playwright.
- Contract, permission-negative, migration, accessibility, concurrency, replay, and performance cases live under `testing/features/F###/`.
- Each feature flag is off by default and selects one suite; `test-all` enables every suite.
- Fixtures use isolated tenant IDs, deterministic seeds, UTC, fixed clocks, and unique worker IDs.

## 10. Ticket gate

- A ticket is build-ready only when it names its real aggregate, routes/events, schema changes, permission matrix, UI states, test files, rollout flag, and rollback.
- Generic route/resource names, empty dependency lists where dependencies exist, and “defined by child tasks” language are invalid.
