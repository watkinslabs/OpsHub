---
id: T109
type: task
status: planned
parent_epic: E006
parent_feature: F028
parent_story: S055
depends_on: [S055]
owned_paths: [services/api/migrations/*_public-api_*.sql, crates/contracts/src/public-api/**, crates/domain/src/public-api/**, services/api/src/public-api/**, apps/web/src/features/public-api/**, testing/features/F028/api/**, testing/features/F028/database/**, testing/features/F028/frontend/**]
feature_flag: F028_FEATURE
branch: t109-openapi-generation
started_at: null
finished_at: null
---

# T109 — OpenAPI generation

## Identity

- Parent story: `S055` REST API
- Owner: platform
- Branch: `t109-openapi-generation`
- Decision references: `docs/architecture-decisions.md` section 3; `docs/capability-contracts.md` row F028

## Objective

Create the `public-api` schema, generate the OpenAPI 3.1 document from typed contracts with a CI drift gate, and implement the API application registry and its admin pages.

## Specification

- Owned paths: `services/api/migrations/<ts>_public-api_create_tables.sql` and `.down.sql`, `crates/contracts/src/public-api/{mod.rs, openapi.rs, error.rs, page.rs}`, `crates/domain/src/public-api/{mod.rs, application.rs, errors.rs, service_app.rs}`, `services/api/src/public-api/{mod.rs, routes.rs, handlers_openapi.rs, handlers_application.rs, dto.rs}`, `apps/web/src/features/public-api/{DeveloperPage.tsx, ApplicationTable.tsx, ApplicationForm.tsx, TokenRevealDialog.tsx, ReferencePage.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `utoipa` derive annotations on every contract DTO and `#[utoipa::path]` on every handler registered in `services/api/src/router.rs`; `CreateApplicationRequest { name, description?, scopes, rate_limit_per_minute?, allowed_ips? }`, `UpdateApplicationRequest { name?, description?, scopes?, rate_limit_per_minute?, allowed_ips?, status? }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: `openapi.rs` builds `OpenApi` 3.1 with `info.version` from the build, schemas for every DTO, `Error`, `Page<T>`, security schemes `sessionCookie` and `apiToken`, and writes `openapi/v1.json`; `cargo xtask check-contracts` regenerates and fails on diff or on any router route absent from the document; `GET /api/v1/openapi.json` serves the embedded artifact with `ETag`; routes `GET/POST /api/v1/applications`, `PATCH/DELETE /api/v1/applications/{id}` return `ApplicationResponse { id, name, description, client_id, scopes, rate_limit_per_minute, allowed_ips, status, version, created_at, updated_at }`; suspension marks bound F038 tokens `suspended` and the auth layer rejects them within 5 s through the token cache TTL; delete revokes tokens; event `application.updated.v1`; audit `application.create|update|delete`; DDL for `api_applications`, `webhooks`, `webhook_deliveries` and indexes from ticket section 4.
- Dependencies: F038 `api_tokens` with `application_id` column and scope catalog; F003 authz and audit writer; F004 outbox writer.
- Feature flag: `F028_FEATURE` gates application routes and admin pages; `openapi.json` and migration are always on.

## TDD

- Failing test first: `testing/features/F028/api/openapi_tests.rs::openapi_document_lists_every_route`, `::openapi_document_validates_against_3_1_schema`, `::openapi_drift_fails_check_contracts`, `::openapi_served_with_etag_under_50ms`; `testing/features/F028/api/application_tests.rs::application_create_returns_client_id`, `::application_duplicate_name_conflicts`, `::application_suspend_rejects_tokens_within_5s`, `::application_member_denied`, `::application_foreign_tenant_not_found`; `testing/features/F028/database/migration_tests.rs::public_api_tables_exist_with_constraints`; `testing/features/F028/frontend/ApplicationForm.test.tsx::validates_scopes_and_rate_limit`, `TokenRevealDialog.test.tsx::shows_token_once`
- Targeted command: `cargo xtask test-feature F028`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/public_api.rs`; committed `openapi/v1.json` baseline; secret manager stub

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; `check-contracts` green with the committed document
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S055
- [ ] `finished_at` recorded
