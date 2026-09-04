---
id: T276
type: task
status: planned
parent_epic: E003
parent_feature: F069
parent_story: S138
depends_on: [S138]
owned_paths: [testing/features/F069/**]
feature_flag: F069_FEATURE
branch: t276-home-permission-tests
started_at: null
finished_at: null
---

# T276 — Home permission tests

## Identity

- Parent story: `S138` Favourites and recents
- Owner: platform
- Branch: `t276-home-permission-tests`
- Decision references: `docs/architecture-decisions.md` sections 2.1, 4; `docs/capability-contracts.md` row F069; `docs/authorization-model.md` sections 2 and 3.1

## Objective

Prove the two properties home cannot be shipped without: nothing appears on it that the caller may not read, and nobody can read another person's home.

## Specification

- Owned paths: `testing/features/F069/{requirements/cases.md, api/permission_tests.rs, api/isolation_tests.rs, e2e/home_permissions.spec.ts, README.md, feature.toml}`
- Contract/input: the fixture tenants A and B from `testing/fixtures/home.rs`, a member with 200 favourites and 100 recents, a second member, a `tenant-admin`, a `viewer` with no workspace access, and a sheet, row, view, and workspace whose ACLs the tests mutate.
- Output/behavior: the matrix asserts, for each of the eight target kinds, that an item the caller cannot read is absent from `GET /api/v1/home`, `GET /api/v1/recents`, and the default `GET /api/v1/favorites`, and that its absence is invisible — no count, no marker, no differing `truncated`, no differing latency class, and identical bodies whether the target was deleted, moved out of reach, unshared, or never existed. It asserts that `filter=unavailable` returns only the cached label with no `path` and nothing about why. It asserts that a `tenant-admin` reading either list sees only their own rows, that a tenant B principal gets `not_found` for a tenant A favourite id on `DELETE /api/v1/favorites/{id}`, and that revoking read access removes the item from both surfaces on the next request with no cache holding it. It asserts that `POST /api/v1/favorites` on an unreadable target returns `not_found` rather than `denied`, so the route cannot be used to probe existence. Each assertion is tied to a requirement id in `requirements/cases.md`, which lists every `FR-F069-` and `NFR-F069-` id in the ticket.
- Data access: the suite reads and mutates only through the public routes and the F003 ACL routes; it opens no connection and issues no SQL of its own, per decision 2.1, and asserts repository behaviour through observable responses.
- Dependencies: F003 ACL replace for revoking access mid-test; T273 and T274 for the routes under test; the shared negative-matrix helper in `testing/harness/`.
- Feature flag: `F069_FEATURE` enabled explicitly by both commands; a positive control disables it and asserts the routes are absent.

## TDD

- Failing test first: `testing/features/F069/api/permission_tests.rs::unreadable_target_absent_from_home`, `::unreadable_target_absent_from_recents`, `::unreadable_target_absent_from_favorites`, `::deleted_and_denied_bodies_are_identical`, `::truncated_flag_does_not_leak_dropped_items`, `::pin_of_unreadable_target_returns_not_found_not_denied`, `::revoking_access_takes_effect_on_next_request`; `testing/features/F069/api/isolation_tests.rs::tenant_admin_sees_only_own_favorites`, `::tenant_admin_sees_only_own_recents`, `::cross_tenant_favorite_delete_is_not_found`, `::cross_user_favorite_delete_is_not_found`, `::visit_by_one_user_never_appears_for_another`; `testing/features/F069/e2e/home_permissions.spec.ts::unshared_sheet_disappears_from_home`, `::unavailable_favourite_can_be_removed`
- Targeted command: `cargo xtask test-feature F069`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/home.rs`; `StubSectionProvider` returning items the caller may not read, so the drop happens in the aggregator and not in the provider; fixed clock; one schema per worker and one tenant per test

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Positive control recorded: remove the resolver's readable filter, observe RED on the absence assertions, restore, observe GREEN
- [ ] `requirements/cases.md` names every FR and NFR id in the F069 ticket
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S138
- [ ] `finished_at` recorded
