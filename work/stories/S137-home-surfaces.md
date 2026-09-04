---
id: S137
type: story
status: planned
parent_epic: E003
parent_feature: F069
depends_on: [F005, F006, F013]
owned_paths: [crates/domain/src/home/**, crates/persistence/src/home/**, services/api/src/home/**, services/worker/src/home/**, apps/web/src/features/home/**, services/api/migrations/*_home_*.sql, testing/features/F069/**]
feature_flag: F069_FEATURE
branch: s137-home-surfaces
started_at: null
finished_at: null
---

# S137 — Home surfaces

## Identity

- Parent feature: `F069` Home and my work
- Owner: platform
- Branch: `s137-home-surfaces`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6; `docs/capability-contracts.md` row F069

## Vertical slice

As a member, I want signing in to land me on one screen that answers what is mine, what is late, what is waiting on me, and where I was, assembled in a single request and filtered to what I may see, so that I start work instead of navigating a tree.

## Requirements

- **SR-S137-01:** `GET /api/v1/home` returns the fixed envelope `{ generated_at, budget_ms, onboarding, sections }` with the five ordered section keys and their caps of 10, 10, 10, 12, and 20, setting `truncated` when the underlying set was larger, and takes no paging parameters (covers FR-F069-01).
- **SR-S137-02:** `HomeSectionProvider` and `HomeRegistry` in `crates/domain/src/home/registry.rs` compose the response: registered providers run concurrently under a 150 ms timeout each, an unregistered slot returns `state: "unavailable"`, and a timed-out or failed provider returns `state: "degraded"` with the `correlation_id` inside a `200` (FR-F069-02, NFR-F069-04).
- **SR-S137-03:** `TargetResolver::resolve_readable` is called once per distinct `target_kind` over the union of candidate targets, dropping anything the caller cannot read without any count, marker, or error that would reveal it, so the statement count is fixed at thirteen and does not grow with items, sheets, or rows (FR-F069-03, NFR-F069-01, NFR-F069-02).
- **SR-S137-04:** A target that is soft-deleted, archived, moved into an unreadable folder, or unshared vanishes from the response on the next read because resolution is per request and never cached across requests (FR-F069-09).
- **SR-S137-05:** `onboarding.state` is `new` for a caller with no favourites, no recents, and no non-empty registered section, carrying up to three readable workspaces, `create_sheet` when the caller may create one, and `request_access` when they can read no workspace; each empty section reports `none_yet`, `all_clear`, or `no_access` (FR-F069-12).
- **SR-S137-06:** Route `/` is the application index and the post-sign-in landing route, rendering one skeleton per section at final height, per-section degraded and empty states, and a single centred first-run panel rather than five empty cards (FR-F069-13, NFR-F069-03).
- **SR-S137-07:** Any authenticated principal may read home; the route never returns a denied page, never returns `unavailable` as a status, and maps its own failures only onto `invalid` and `not_found` (FR-F069-14).
- **SR-S137-08:** Home is under 400 ms p95 and 800 ms p99 at full caps, and the home route is instrumented with `home_request_duration_seconds`, `home_section_duration_seconds{section}`, and `home_section_state_total{section,state}` inside a span carrying `tenant_id`, `actor_id`, `correlation_id`, and the section key (NFR-F069-01, NFR-F069-04).

## Surfaces

- Data access: `crates/persistence/src/home/{mod.rs, favorite_repository.rs, recent_item_repository.rs}` hold every SQL statement this story reads; the aggregator, providers, resolvers, and handlers depend on those traits and on `WorkspaceRepository::list_visible_to`, `SheetRepository`, `RowRepository`, and `ViewRepository::list_visible_to` for target resolution, so `crates/domain/src/home` and `services/api/src/home` contain no `sqlx::query*` call or connection (decision 2.1)
- Rust service/API: `crates/domain/src/home/{mod.rs, model.rs, registry.rs, service.rs, onboarding.rs, errors.rs}`; `services/api/src/home/{mod.rs, routes.rs, handlers_home.rs, dto.rs}`
- React/UI: `apps/web/src/features/home/{HomePage.tsx, HomeSectionCard.tsx, HomeItemRow.tsx, HomeEmptyState.tsx, HomeSkeleton.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/home.rs`; `StubSectionProvider` and `StubTargetResolver` in `testing/harness/home/` with programmable latency and failure

## TDD harness

- Test path: `testing/features/F069/{api,frontend,performance,accessibility}/`
- Feature flag: `F069_FEATURE`
- Targeted command: `cargo xtask test-feature F069`
- Full command: `cargo xtask test-all`
- First failing tests: `home_returns_five_sections_under_their_caps`, `unregistered_slot_reports_unavailable`, `slow_provider_degrades_only_its_section`, `resolver_called_once_per_target_kind`, `unreadable_target_absent_without_marker`, `new_user_gets_onboarding_suggestions`, `empty_section_reports_its_reason`, `home_statement_count_is_thirteen_at_full_caps`

## Exit criteria

- [ ] Requirement tests SR-S137-01 through SR-S137-08 written first and observed failing
- [ ] Tasks T273 and T274 complete and wired through the API router
- [ ] Unit, API, React, accessibility, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/home/routes.rs` mounted in `services/api/src/router.rs` at `/api/v1/home`; `apps/web/src/features/home/routes.ts` registered as the index route
- [ ] Handoff evidence recorded in the F069 ticket
