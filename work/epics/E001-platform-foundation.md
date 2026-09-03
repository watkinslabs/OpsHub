---
id: E001
type: epic
status: planned
owner: platform
target_milestone: M1
branch: e001-platform-foundation
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 1, 2, 3, 4, 7, 9, 10
- Capability contract: `docs/capability-contracts.md` rows F001, F002, F038, F003, F004
- Product spec: `docs/product-capability-spec.md` sections 3, 4, 5.8, 6, 7 (Phase 0 and Phase 1), 10

# E001 — Platform foundation

## Outcome

A clean checkout boots the complete multi-tenant runtime (API, web, worker, realtime, PostgreSQL 18, NATS JetStream, MinIO, Mailpit) with `docker compose up`, and every later feature builds on the same five primitives: a validated Rust/React monorepo with CI gates, tenant/user/group records with tested isolation, OIDC login with sessions, refresh rotation, WebAuthn/TOTP MFA and scoped API tokens, deny-by-default RBAC plus resource ACLs with an append-only audit log, and a transactional outbox feeding JetStream jobs with tracing, metrics, health, readiness, backups and point-in-time recovery. The measurable outcome is that an administrator of a pilot tenant can log in with MFA, create users and groups, assign roles, inspect the audit trail, and an operator can prove a restore drill, all before any work-record feature exists.

## Scope

- Included: Cargo workspace, pnpm workspace, CI matrix and policy gates (F001); tenant, user and group lifecycle with the shared tenant fixture (F002); OIDC login, session store, refresh rotation, TOTP and WebAuthn factors, API tokens, rate-limit buckets and the tenant security policy (F038); roles, role bindings, resource ACLs, the `authz::require` middleware, the audit writer and audit query API (F003); compose baseline, typed configuration and secret sources, outbox relay, JetStream job transport, worker skeleton, OpenTelemetry tracing, Prometheus metrics, `/healthz`, `/readyz`, backups and PITR (F004).
- Excluded: SAML 2.0 and SCIM 2.0 provisioning (F026), retention, legal hold, tenant export and purge (F027), public API applications and webhooks (F028), workspaces and folders (F005), locale settings (F049), entitlements and feature-flag administration (F048), notifications (F037).

## Child features

- F001 Repository and CI: Rust 2024 workspace, React 19 app shell, `gates.yml` CI matrix, line-limit and attribution gates. Depends on F041, F042.
- F002 Tenant, users, and groups: `tenants`, `users`, `groups`, `group_members` tables, twelve admin routes, seven events, the reusable two-tenant fixture. Depends on F001.
- F038 Authentication and MFA: OIDC login, sessions, refresh tokens, TOTP and WebAuthn factors, API tokens, rate-limit buckets, tenant security policy, gateway `ActorContext`. Depends on F002.
- F003 Authorization and audit: roles, role bindings, resource ACLs, policy engine, `RequirePermission` middleware, append-only `audit_events`, audit query API. Depends on F002, F038.
- F004 Runtime operations: compose baseline, `RuntimeConfig` and `SecretSource`, transactional outbox, JetStream job transport, worker skeleton, tracing, metrics, health, readiness, backups, PITR. Depends on F001.

## Exit criteria

- [ ] From a clean checkout, `docker compose up` in `infra/compose` reaches healthy for postgres, nats, minio, mailpit, api, worker, realtime and web within 120 seconds, and `GET /readyz` on the API returns 200 with every component `ok`.
- [ ] The spec section 8 administrator scenario is executable end to end at the foundation level: a tenant-admin logs in through OIDC with a TOTP factor, creates a user and a group, binds the `editor` role to the group, restricts a resource with an explicit deny, and reads the resulting `audit_events` entries with matching `correlation_id` values through `GET /api/v1/audit-events`.
- [ ] Tenant isolation is proven: the F002 and F003 negative suites show every cross-tenant read returning `not_found` and every role-negative mutation returning `denied` for all E001 routes.
- [ ] MFA and sessions work: refresh reuse revokes the family, `mfa_required` blocks `/api/v1` routes until a factor is verified, API tokens authenticate with scoped `ActorContext`, and rate limits return `429 rate_limited` with `Retry-After`.
- [ ] CI blocks invalid tickets and forbidden attribution: `cargo xtask validate-work`, `validate-tickets`, `check-contracts`, `audit-range` and the 500-line gate are required status checks on `main`.
- [ ] Logs, traces, health and metrics are usable: one request produces a JSON log line, an OTLP trace and Prometheus samples sharing the same `correlation_id`; a restore drill from `opshub-backups` completes and its evidence is stored under `testing/evidence/F004/`.
- [ ] All five child features accepted, archived, and their flags documented with rollback steps.
