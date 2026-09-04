---
id: T226
type: task
status: planned
parent_epic: E008
parent_feature: F057
parent_story: S113
depends_on: [T225]
owned_paths: [crates/domain/src/assets/**, crates/persistence/src/assets/**, services/api/src/assets/**, testing/features/F057/api/**, testing/features/F057/requirements/**]
feature_flag: F057_FEATURE
branch: t226-metadata-rights
started_at: null
finished_at: null
---

# T226 — Metadata/rights

## Identity

- Parent story: `S113` Asset library
- Owner: platform
- Branch: `t226-metadata-rights`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4; `docs/capability-contracts.md` row F057

## Objective

Implement the tenant metadata schema validation, the usage-rights model with expiry derivation, and the rights route so assets carry typed, rights-aware metadata.

## Specification

- Owned paths: `crates/domain/src/assets/{metadata.rs, rights.rs, usable.rs}`, `crates/persistence/src/assets/{rights_repository.rs, metadata_field_repository.rs}`, `services/api/src/assets/{handlers_rights.rs, handlers_settings.rs}`
- Contract/input: the tenant schema is `asset_metadata_fields` rows (≤ 30 per tenant) of `{ key, label, kind: text|number|date|select|person, required, position }` with `select` choices as `asset_metadata_field_options` rows; the settings API keeps the same `[{ key, label, kind, options?, required? }]` JSON array shape, and `PATCH /api/v1/assets/{id}` validates supplied metadata against those rows; `SetRightsRequest { license, licensor?, valid_from?, valid_until?, territories?, channels?, notes? }`.
- Output/behavior: `validate_metadata` returns `field_errors.metadata.<key>` with `missing`, `type_mismatch`, or `unknown_key`; removing a schema field with existing values is rejected with `invalid`; `PUT /api/v1/assets/{id}/rights` upserts `asset_rights` and replaces its `asset_rights_territories` and `asset_rights_channels` rows, rejecting a code absent from `asset_territory_codes` and a channel outside the check constraint, requires `If-Match` on the asset, publishes `asset.rights-updated.v1`, and returns `territories` and `channels` as JSON string arrays unchanged; `derive_rights_state(rights, now, tz)` returns `none|active|expired` using end of day of the typed `valid_until` column in the tenant timezone, and the rights-expiry sweep behind the `rights_state` list filter reads `AssetRightsRepository::list_rights_expiring_before`; `derive_usable(approval_state, rights_state)` is true only for `approved` and not `expired`.
- Data access: `metadata.rs`, `rights.rs`, and `usable.rs` hold no SQL and take repository traits. `AssetRightsRepository` owns `asset_rights`, `asset_rights_territories`, `asset_rights_channels`, and the seeded read-only `asset_territory_codes`; `AssetMetadataFieldRepository` owns `asset_metadata_fields` and `asset_metadata_field_options` and answers `count_values_for_field` for the removal block; metadata values are written by `AssetRepository::replace_asset_metadata_values`, and a rights write commits its parent row and both child sets in one `UnitOfWork` (decision section 2.1).
- Dependencies: T225 tables and repositories, asset service; F049 tenant timezone; F003 audit writer.
- Feature flag: `F057_FEATURE`

## TDD

- Failing test first: `testing/features/F057/api/metadata_tests.rs::asset_metadata_type_mismatch_invalid`, `::asset_metadata_unknown_key_invalid`, `::schema_field_removal_blocked_with_values`; `testing/features/F057/api/rights_tests.rs::rights_set_publishes_event`, `::rights_expired_makes_asset_unusable`, `::rights_expiry_uses_tenant_end_of_day`, `::rights_invalid_territory_rejected`, `::rights_replace_rewrites_territory_rows`, `::rights_invalid_channel_rejected`, `::rights_viewer_denied`
- Targeted command: `cargo xtask test-feature F057`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: 5-field metadata schema fixture; rights windows around the fixed clock in `America/Los_Angeles`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Rights route mounted behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S113
- [ ] `finished_at` recorded
