---
id: T285
type: task
status: planned
parent_epic: E003
parent_feature: F072
parent_story: S143
depends_on: [S143]
owned_paths: [services/api/migrations/*_inbound-email_*.sql, crates/domain/src/inbound-email/**, crates/persistence/src/inbound-email/**, services/api/src/inbound-email/**, testing/features/F072/api/**, testing/features/F072/database/**]
feature_flag: F072_FEATURE
branch: t285-address-provisioning
started_at: null
finished_at: null
---

# T285 — Address provisioning

## Identity

- Parent story: `S143` Inbound addresses
- Owner: platform
- Branch: `t285-address-provisioning`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 2.2, 4; `docs/capability-contracts.md` row F072

## Objective

Create the `inbound-email` schema and implement address minting, mapping and allow-list configuration, rotation, revocation, the address list route, and reply-token minting and claiming.

## Specification

- Owned paths: `services/api/migrations/<ts>_inbound-email_create_tables.sql` and `.down.sql`, `crates/domain/src/inbound-email/{mod.rs, address.rs, local_part.rs, policy.rs, errors.rs, service.rs}`, `crates/persistence/src/inbound-email/{mod.rs, address_repository.rs, message_repository.rs, reply_token_repository.rs}`, `services/api/src/inbound-email/{mod.rs, routes.rs, handlers_address.rs, dto.rs}`
- Contract/input: `CreateInboundAddressRequest { sheet_id, label?, sender_policy?, auth_policy?, allow_list?, mappings, max_messages_per_hour?, max_message_bytes?, rotate_from_id? }`; list query `{ cursor?, limit?, sheet_id?, status?, sender_policy? }`; deployment settings `inbound-email/domain` and the F004 CSPRNG source.
- Output/behavior: routes `GET /api/v1/inbound-addresses`, `POST /api/v1/inbound-addresses`, `DELETE /api/v1/inbound-addresses/{id}`. `local_part.rs` draws 110 bits from the CSPRNG and encodes 22 lowercase Crockford base32 characters, retrying on the `unique (domain, lower(local_part))` collision up to 3 times before returning `unavailable`; the value is derived from no sheet, tenant, timestamp or counter. `POST` writes the address, its `inbound_address_mappings` rows and its `inbound_address_senders` rows in one `UnitOfWork`, refuses a sixth `active` address on a sheet with `409 conflict` and `field_errors.sheet_id = "address_limit"`, validates `mappings` (1–7 entries, distinct sources, distinct columns, each column on the sheet), `allow_list` (1–200 rows, required when `sender_policy = 'allow_list'`), `max_messages_per_hour` 1–600 and `max_message_bytes` 1,048,576–52,428,800, and with `rotate_from_id` sets the predecessor's `rotation_grace_ends_at` to 7 days out. `DELETE` sets `status = 'revoked'`, `revoked_at` and `revoked_by`, keeps the row so the local part is never reissued, and revokes the address's reply tokens. `GET` pages by cursor, filters, and reassembles `mappings`, `allow_list` and the 30-day `accepted`/`rejected`/`quarantined` counts in one batched read per page, omitting the address string for actors without `sheet-editor`. `reply_token_repository.rs` mints a token as 32 CSPRNG bytes stored only as `sha256`, claims it in constant time under `expires_at`, `retired_at` and a 20-use cap, and revokes every token for a deleted row. Audit events `inbound-address.created`, `inbound-address.rotated`, `inbound-address.revoked`, `inbound-address.policy-updated`. DDL for the eight tables, checks and `concurrently` created indexes from ticket section 4, as an expand-phase migration that alters no existing table.
- Data access: `address.rs`, `local_part.rs`, `policy.rs`, `service.rs` and the two handler modules hold no SQL; every read and write goes through `InboundAddressRepository`, `InboundMessageRepository` and `InboundReplyTokenRepository` using the named queries in ticket section 4 with no generic query escape hatch, and the create, rotate and revoke paths each commit in one `UnitOfWork` (decision section 2.1).
- Dependencies: F006 sheets and columns for mapping validation; F003 authorization for `sheet-editor`; F004 secret manager and CSPRNG; F028 conventions, `Idempotency-Key` and `If-Match`.
- Feature flag: `F072_FEATURE` gates the routes; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F072/api/address_tests.rs::local_part_is_unguessable_and_unique`, `::local_part_never_encodes_sheet_or_tenant`, `::sixth_active_address_conflicts`, `::mapping_rejects_column_from_another_sheet`, `::allow_list_required_for_allow_list_policy`, `::rotation_sets_seven_day_grace_on_predecessor`, `::revoked_local_part_is_never_reissued`, `::address_hidden_from_actor_without_sheet_editor`, `::viewer_cannot_revoke_address`, `::foreign_tenant_address_not_found`; `testing/features/F072/api/token_tests.rs::reply_token_stored_only_as_hash`, `::reply_token_retired_after_twenty_uses`, `::reply_tokens_revoked_with_row`; `testing/features/F072/database/migration_tests.rs::inbound_email_tables_exist_with_constraints`, `::local_part_unique_across_revoked_rows`, `::message_unique_per_provider_message_id`, `::disposition_requires_row_or_comment`, `::cascade_on_sheet_delete`, `::rollback_drops_inbound_email_tables`
- Targeted command: `cargo xtask test-feature F072`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/inbound_email.rs`; fixed CSPRNG stream and fixed clock `2026-09-03T00:00:00Z`; tenants A and B with sheet `Vendor intake`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S143
- [ ] `finished_at` recorded
