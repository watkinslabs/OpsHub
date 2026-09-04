---
id: T273
type: task
status: planned
parent_epic: E003
parent_feature: F069
parent_story: S137
depends_on: [S137]
owned_paths: [crates/domain/src/home/**, services/api/src/home/**, testing/features/F069/api/**, testing/features/F069/performance/**]
feature_flag: F069_FEATURE
branch: t273-home-aggregation
started_at: null
finished_at: null
---

# T273 — Home aggregation

## Identity

- Parent story: `S137` Home surfaces
- Owner: platform
- Branch: `t273-home-aggregation`
- Decision references: `docs/architecture-decisions.md` sections 2.1, 3, 4; `docs/capability-contracts.md` row F069

## Objective

Build the `home` aggregate: the section provider registry, the batched permission-filtered target resolver, the onboarding computation, and the `GET /api/v1/home` route that returns all of it in one bounded request.

## Specification

- Owned paths: `crates/domain/src/home/{mod.rs, model.rs, registry.rs, service.rs, onboarding.rs, errors.rs}`, `services/api/src/home/{mod.rs, routes.rs, handlers_home.rs, dto.rs}`
- Contract/input: no query parameters; the caller's `ActorContext` carries `tenant_id`, `user_id`, and `correlation_id`; the registry is built at start-up from the providers and resolvers each feature registers.
- Output/behavior: `GET /api/v1/home` returns `HomeResponse { generated_at, budget_ms, onboarding, sections }` with the five ordered keys `assigned`, `approvals`, `mentions`, `recents`, `favorites` at caps 10, 10, 10, 12, 20 and `truncated` per section. `HomeSectionProvider { key, cap, load }` and `TargetResolver { kind, resolve_readable }` are defined in `registry.rs`; `HomeRegistry` runs registered providers concurrently under a 150 ms timeout each, marks an unregistered slot `unavailable`, marks a failed or timed-out one `degraded` with the `correlation_id`, unions the returned `TargetRef`s, calls `resolve_readable` exactly once per distinct `target_kind`, drops unresolved targets silently, truncates to the caps, and computes `onboarding` from the result plus `WorkspaceRepository::list_visible_to` capped at three suggestions. Section `empty_reason` is `none_yet`, `all_clear`, or `no_access`. Errors map `HomeError::UnknownTargetKind` and `::InvalidCursor` to `invalid` and `::TargetNotReadable` and `::Missing` to `not_found`; a degraded section never changes the `200` status.
- Data access: `service.rs`, `registry.rs`, `onboarding.rs`, and the handler hold no SQL; favourites and recents are read through `FavoriteRepository::list_for_user` and `RecentItemRepository::list_for_user` from T274, target resolution goes through the repository that already owns each table, and no connection is opened outside `crates/persistence` (decision 2.1).
- Dependencies: F003 `authz::require` and the readable-resource predicate; F005 `WorkspaceRepository::list_visible_to`; F006 `SheetRepository` and `RowRepository`; F013 `ViewRepository::list_visible_to`; T274 for the two repositories this route reads.
- Feature flag: `F069_FEATURE` gates the route and the registry; an unflagged deployment mounts neither.

## TDD

- Failing test first: `testing/features/F069/api/home_tests.rs::home_returns_five_sections_under_their_caps`, `::unregistered_slot_reports_unavailable`, `::slow_provider_degrades_only_its_section`, `::failing_provider_degrades_with_correlation_id`, `::empty_registry_still_returns_two_hundred`, `::unreadable_target_absent_without_marker`, `::missing_resolver_drops_that_kind`; `testing/features/F069/api/onboarding_tests.rs::new_user_gets_onboarding_suggestions`, `::viewer_without_workspace_gets_request_access`, `::empty_section_reports_its_reason`; `testing/features/F069/performance/home_bench.rs::home_statement_count_is_thirteen_at_full_caps`, `::resolver_called_once_per_target_kind`, `::home_p95_under_400ms`
- Targeted command: `cargo xtask test-feature F069`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/home.rs`; `StubSectionProvider` and `StubTargetResolver` in `testing/harness/home/` with programmable latency, error, and item count; fixed clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Route registered behind the flag; OpenAPI regenerated without drift
- [ ] Statement count asserted, not only duration
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S137
- [ ] `finished_at` recorded
