---
id: T226
type: task
status: planned
parent_epic: E008
parent_feature: F057
parent_story: S113
depends_on: [T225]
owned_paths: [crates/domain/src/assets/**, services/api/src/assets/**, testing/features/F057/api/**, testing/features/F057/requirements/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F057

## Objective

Implement the tenant metadata schema validation, the usage-rights model with expiry derivation, and the rights route so assets carry typed, rights-aware metadata.

## Specification

- Owned paths: `crates/domain/src/assets/{metadata.rs, rights.rs, usable.rs}`, `services/api/src/assets/{handlers_rights.rs, handlers_settings.rs}`
- Contract/input: tenant schema `asset_metadata_fields: [{ key, label, kind: text|number|date|select|person, options?, required? }]` (≤ 30) stored in tenant settings and edited through `PATCH /api/v1/assets/{id}` metadata validation; `SetRightsRequest { license, licensor?, valid_from?, valid_until?, territories?, channels?, notes? }`.
- Output/behavior: `validate_metadata` returns `field_errors.metadata.<key>` with `missing`, `type_mismatch`, or `unknown_key`; removing a schema field with existing values is rejected with `invalid`; `PUT /api/v1/assets/{id}/rights` upserts `asset_rights`, requires `If-Match` on the asset, publishes `asset.rights-updated.v1`; `derive_rights_state(rights, now, tz)` returns `none|active|expired` using end of day of `valid_until` in the tenant timezone; `derive_usable(approval_state, rights_state)` is true only for `approved` and not `expired`.
- Dependencies: T225 tables and asset service; F049 tenant timezone; F003 audit writer.
- Feature flag: `F057_FEATURE`

## TDD

- Failing test first: `testing/features/F057/api/metadata_tests.rs::asset_metadata_type_mismatch_invalid`, `::asset_metadata_unknown_key_invalid`, `::schema_field_removal_blocked_with_values`; `testing/features/F057/api/rights_tests.rs::rights_set_publishes_event`, `::rights_expired_makes_asset_unusable`, `::rights_expiry_uses_tenant_end_of_day`, `::rights_invalid_territory_rejected`, `::rights_viewer_denied`
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
