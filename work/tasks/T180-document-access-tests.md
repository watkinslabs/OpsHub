---
id: T180
type: task
status: planned
parent_epic: E004
parent_feature: F045
parent_story: S090
depends_on: [T179]
owned_paths: [crates/domain/src/documents/**, services/api/src/documents/**, testing/features/F045/api/**, testing/features/F045/e2e/**, testing/features/F045/requirements/**]
feature_flag: F045_FEATURE
branch: t180-document-access-tests
started_at: null
finished_at: null
---

# T180 — Document access tests

## Identity

- Parent story: `S090` Sharing and permissions
- Owner: platform
- Branch: `t180-document-access-tests`
- Decision references: `docs/architecture-decisions.md` section 4; `docs/capability-contracts.md` row F045

## Objective

Implement the inherited access walk, guest and link principal scoping, link rate limiting, and search visibility rules, and prove them with the permission-negative API suite and the end-to-end library scenarios.

## Specification

- Owned paths: `crates/domain/src/documents/{access.rs, principal.rs}`, `services/api/src/documents/{authz.rs, rate_limit.rs}`, `testing/features/F045/api/access_tests.rs`, `testing/features/F045/e2e/documents.spec.ts`, `testing/features/F045/requirements/cases.md`
- Contract/input: gateway context `{ tenant_id, actor_id, roles, scopes, correlation_id, principal_kind }`; F036 `share_grants(resource_id, principal_id, role, deny)` and `share_links(token_id, resource_id, expires_at, revoked_at)`; workspace setting `link_search_discoverable`.
- Output/behavior: `resolve_effective_access(path)` loads grants for every ID in `path` in one query, returns the highest role root-to-leaf, and returns `denied` when any level has `deny = true`; denied and missing access map to `404 not_found`; `PrincipalKind::{Guest, Link}` receive `403 denied` on root listings and on every mutation route; link principals pass through the F038 limiter keyed `link:{token_id}` at 60 requests per minute returning `429 rate_limited` with `Retry-After`; expired or revoked links return `404 not_found`; search results drop `search_visibility = hidden` nodes and link-only nodes unless `link_search_discoverable` is true; the `EffectiveAccessCache` memoizes walks per request.
- Dependencies: T179 UI for the E2E scenarios; F036 grant and link tables; F038 rate limiter; F003 audit writer for `document.access.denied` audit events on guest and link denials.
- Feature flag: `F045_FEATURE`

## TDD

- Failing test first: `testing/features/F045/api/access_tests.rs::explicit_deny_hides_descendants`, `::viewer_mutation_denied`, `::link_principal_cannot_list_root`, `::link_principal_reads_granted_subtree_only`, `::link_principal_rate_limited_after_60`, `::expired_link_not_found`, `::hidden_nodes_excluded_from_search`, `::document_cross_tenant_not_found`; `testing/features/F045/e2e/documents.spec.ts::create_folder_document_save_revision`, `::move_search_trash_restore`, `::link_principal_sees_only_granted_folder`, `::viewer_is_read_only`
- Targeted command: `cargo xtask test-feature F045`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: guest and link principal fixtures with a grant on `Runbooks` and a deny on `Finance`; Playwright runs against the real API on a seeded tenant with a fixed clock for link expiry

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] API permission-negative and E2E lanes pass; requirements table complete
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S090
- [ ] `finished_at` recorded
