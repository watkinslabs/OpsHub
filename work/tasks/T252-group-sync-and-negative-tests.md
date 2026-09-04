---
id: T252
type: task
status: planned
parent_epic: E006
parent_feature: F063
parent_story: S126
depends_on: [T251]
owned_paths: [crates/domain/src/entra/**, services/api/src/entra/**, services/worker/src/entra/**, apps/web/src/features/entra/**, testing/features/F063/api/**, testing/features/F063/e2e/**, testing/features/F063/frontend/**]
feature_flag: F063_FEATURE
branch: t252-group-sync-and-negative-tests
started_at: null
finished_at: null
---

# T252 — Group sync and negative tests

## Identity

- Parent story: `S126` Graph mail and group sync
- Owner: platform
- Branch: `t252-group-sync-and-negative-tests`
- Decision references: `docs/architecture-decisions.md` sections 4, 7; `docs/capability-contracts.md` row F063

## Objective

Implement directory group sync onto existing F002 groups and F003 role bindings with delta tokens, bounds and a destructive-change halt, the mapping UI, and the permission-negative, tenant-isolation and additive-behaviour suite that proves Entra never replaces another sign-in method or group model.

## Specification

- Owned paths: `crates/domain/src/entra/{group_sync.rs, group_map.rs, diff.rs}`; `services/api/src/entra/{handlers_groups.rs, dto.rs}`; `services/worker/src/entra/group_sync.rs`; `apps/web/src/features/entra/{GroupMapTable.tsx, GroupPickerDialog.tsx, SyncResultBanner.tsx}`
- Contract/input: `GroupMapRequest { directory_group_id, directory_group_name, target_kind: group|role, target_id }` with `Idempotency-Key` and `If-Match`; `POST /api/v1/entra/sync-groups` takes `{ connection_id, confirm_destructive?: bool }` and returns `SyncResponse { status: completed|needs_review, groups, added, removed, delta_token_advanced, started_at, finished_at }`; `listDirectoryGroups(search)` proxies Graph `GET /v1.0/groups`.
- Output/behavior: the on-demand route and the nightly worker job read `GET /v1.0/groups` with delta tokens through `graph.rs`, resolve each `entra_group_map` row to an F002 group or an F003 role binding — no second group model — and diff membership. Members flagged `source: manual` are never removed. Bounds are 500 mapped groups and 50,000 members per run; a run whose diff would remove more than 20% of any mapped group's members ends `needs_review`, writes nothing, and only proceeds on a later run with `confirm_destructive: true`. Each add and removal writes an audit event naming the directory group as the reason, and the run writes `entra.group-sync` and publishes `entra.group-synced.v1` with counts. The job is idempotent per delta token, resumes after restart, falls back to a full read without duplicating members when the token has expired, dead-letters after 3 retries setting the connection to `error`, and emits `entra_group_sync_members_total{direction}`. A mapping whose target group belongs to another tenant is `404 not_found`; a connection without `group_sync` gives `409 conflict` on `field_errors.capabilities`; a non-`identity-admin` is `403 denied`. UI: `GroupMapTable` lists mappings with last counts and scrolls in its own container, `GroupPickerDialog` searches directory groups through `['entra-directory-groups', search]`, `SyncResultBanner` shows `Added 24, removed 2` or the `needs_review` explanation as text plus icon; telemetry `entra_group_mapped`, `entra_sync_run`.
- Dependencies: T249 connection and `graph.rs`; T251 for the shared breaker and throttling behaviour; F002 groups and membership `source`; F003 role bindings and audit; F004 job transport.
- Feature flag: `F063_FEATURE` gates the route, the job and the mapping UI.

## TDD

- Failing test first: `testing/features/F063/api/group_sync_tests.rs::sync_adds_and_removes_mapped_members`, `::sync_skips_manual_source_members`, `::sync_halts_needs_review_over_twenty_percent_removal`, `::confirm_destructive_applies_held_removals`, `::sync_writes_audit_per_member_with_group_reason`, `::sync_publishes_group_synced_with_counts`, `::expired_delta_token_falls_back_to_full_read`, `::sync_idempotent_after_restart`, `::sync_bounded_at_500_groups_and_50000_members`, `::role_target_binds_through_f003`, `::sync_without_group_sync_capability_conflicts`; `testing/features/F063/api/negative_tests.rs::member_denied_on_every_entra_route`, `::foreign_tenant_group_map_not_found`, `::mapping_to_other_tenants_group_not_found`, `::mutations_require_idempotency_key_and_if_match`, `::entra_enabled_leaves_password_totp_webauthn_oidc_saml_working`, `::disconnect_leaves_users_and_groups_intact`; `testing/features/F063/frontend/GroupMapTable.test.tsx::shows_last_counts_and_needs_review_text`, `testing/features/F063/frontend/GroupPickerDialog.test.tsx::searches_directory_groups`; `testing/features/F063/e2e/entra.spec.ts::connect_test_enable_sign_in_and_sign_in_with_microsoft`, `::map_group_run_sync_and_see_counts`, `::disconnect_and_confirm_other_methods_still_work`
- Targeted command: `cargo xtask test-feature F063`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: mock Graph groups delta in `testing/harness/providers/entra/` with an expirable delta token and a page that drops 30% of a 100-member group; `testing/fixtures/entra.rs` 500 directory groups and 50,000 members, manual and directory-sourced members, tenant B group, member and identity-admin actors; Playwright against the seeded tenant with the mock authority

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Route and nightly job registered behind the flag; OpenAPI regenerated without drift
- [ ] Destructive-change halt and the 500-group / 50,000-member bounds verified
- [ ] Permission-negative, tenant-isolation and additive-behaviour suites green
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S126
- [ ] `finished_at` recorded
