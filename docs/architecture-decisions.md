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
- The schema is normalized to third normal form as the default. No repeating groups, no repeated columns (`option_1`, `option_2`), and no column holding a delimited list.
- Every enumerable set of values belongs to a child table with a foreign key, never an array column. `scopes`, `capabilities`, `permissions`, `tags`, `domains`, `events`, `origins` and their kind are rows, so they can be joined, constrained, indexed and audited.
- A closed enum whose members carry no data stays a `text` column with a `check` constraint. An enum whose members carry data, or that a tenant may extend, is a lookup table with a stable key.
- Every foreign key is declared, with `on delete restrict` by default and `cascade` only where the child cannot outlive its parent.
- `jsonb` is permitted only for genuinely user-defined, schema-less payloads: typed cell values, view and widget settings, event payloads, provider response snapshots, and diffs. It is never used for data the product filters, joins, sorts, aggregates, or enforces a constraint on. A `jsonb` column that the product queries by key is a modelling error and becomes a table.
- Denormalization is allowed only as a derived, rebuildable cache — never as the source of truth — and every such column or table names the query it serves and the job that rebuilds it.

## 2.2 Schema change

- Every schema change is **expand, migrate, contract** across three deploys, never one. Expand adds
  the new shape and keeps the old; migrate backfills and dual-writes until the read path is switched;
  contract removes the old shape only once no running version reads it.
- A single deploy never contains both a write to a new column and the removal of the old one. The
  running application must work against the schema before and after any migration it ships with,
  because a rollback runs the old binary against the new schema.
- Backfills run as resumable jobs in batches with a bounded rate, never as a statement inside a
  migration. A migration that would lock a large table for longer than a second is a backfill job.
- `NOT NULL` arrives as: add nullable, backfill, add a validated check, then set not-null. Indexes
  are created `CONCURRENTLY`. Renames are add-copy-drop across three deploys, never `ALTER … RENAME`.
- `cargo xtask check-migrations` enforces the mechanical half — naming, ordering, reversibility, and
  the banned statements. The staging discipline above is a review responsibility, and a migration
  that cannot state which of the three phases it is fails review.

## 2.1 Data access

- Every table is reached through exactly one data access class in `crates/persistence/src/<aggregate>/`, named `<Aggregate>Repository`: `UserRepository`, `SheetRepository`, `DepartmentRepository`, one per object type. Two classes never write the same table.
- All SQL lives in `crates/persistence`. No SQL string, `sqlx::query*` call, or connection is permitted in `crates/domain`, `services/*/src`, or any handler, job, or test outside that crate; the domain depends on repository traits, not on SQLx.
- Every repository implements the shared `Repository` contract: `get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, and `purge`. Beyond it, a repository exposes named, intention-revealing queries — never a generic query escape hatch.
- The tenant predicate, the soft-delete filter, the optimistic version check, the audit row, and the outbox enqueue are applied by the base contract, not by callers, so a new repository cannot forget them.
- Multi-table writes run inside one `UnitOfWork` that owns the transaction; a repository never opens its own transaction when it is handed one.
- `cargo xtask check-persistence` enforces all of the above and fails the build on a violation.

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

## 11. Environments, release and recovery

- Three environments, all from the same artifact: `dev` (ephemeral, per lane), `staging` (production
  shape, anonymised data, the only place a release candidate is proven), `production`. An image is
  built once and promoted; nothing is rebuilt per environment.
- Configuration differs by environment only through `RuntimeConfig` and the secret source. No
  environment branches in code, and no environment-specific build.
- Release is **rolling with health gates**: instances are replaced in batches, `/readyz` must pass
  before the next batch, and a failed batch stops the rollout with the previous version still
  serving. Feature-level risk is carried by flags (F048), which is why the deploy itself does not
  need canary weighting.
- Rollback is redeploying the previous image, which is safe because of the expand-migrate-contract
  rule in section 2.2: the previous binary always runs against the current schema.
- Recovery targets, which the backup and PITR design in F004 exists to meet: **RPO 5 minutes**
  (continuous WAL archiving) and **RTO 1 hour** for a full restore. Both are proven by the restore
  drill, not asserted — a drill that has not run in 30 days fails the release gate.
- Every deploy records the image digest, the migration set applied, and the flag state, so "what was
  running when this broke" is answerable without archaeology.
