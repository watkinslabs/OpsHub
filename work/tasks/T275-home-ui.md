---
id: T275
type: task
status: planned
parent_epic: E003
parent_feature: F069
parent_story: S138
depends_on: [S138]
owned_paths: [apps/web/src/features/home/**, testing/features/F069/frontend/**, testing/features/F069/e2e/**, testing/features/F069/accessibility/**]
feature_flag: F069_FEATURE
branch: t275-home-ui
started_at: null
finished_at: null
---

# T275 — Home UI

## Identity

- Parent story: `S138` Favourites and recents
- Owner: platform
- Branch: `t275-home-ui`
- Decision references: `docs/architecture-decisions.md` sections 4, 6; `docs/capability-contracts.md` row F069; `docs/engineering-standards.md` sections 1–4

## Objective

Build the home screen at route `/` and the reusable favourite toggle every other surface mounts, with the section, empty, degraded, and offline states the ticket specifies and the artboard draws.

## Specification

- Owned paths: `apps/web/src/features/home/{HomePage.tsx, HomeSectionCard.tsx, HomeItemRow.tsx, HomeEmptyState.tsx, HomeSkeleton.tsx, FavoriteStar.tsx, FavoritesList.tsx, RecentsList.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: generated `HomeApi` with `getHome`, `listFavorites`, `addFavorite`, `removeFavorite`, `listRecents`; no hand-written duplicate of a server type; every component imports from `apps/web/src/ui` and every icon from the shared registry.
- Output/behavior: `/` is the index route and the post-sign-in landing route. `HomePage` renders the five sections in the server's order in a three, two, or one column layout at 1,280 px and 900 px breakpoints, keeping section order identical in every layout so tab order matches reading order. `HomeSectionCard` renders `ready`, `empty` with the copy selected by `empty_reason`, `degraded` with the `correlation_id` and a retry that refetches only `['home']`, `unavailable` by rendering nothing, and offline from the cached payload behind an offline banner. `HomeSkeleton` reserves the final height of each section so nothing shifts on load. `HomeEmptyState` renders the single centred first-run panel with up to three workspace buttons, `Create a sheet`, or `Ask an administrator for access`. `FavoriteStar` is a toggle button exported for other feature headers, with an accessible name naming the target and the resulting action, optimistic update against `['home']` and `['favorites']`, rollback with the stale message on `conflict` or `not_found`, a 5 s undo toast, and a polite live-region announcement. `FavoritesList` offers `Show unavailable`, which renders greyed rows with the cached label, no link, and `Remove`. Telemetry events `home_viewed`, `home_item_opened`, `favorite_added`, `favorite_removed`, `home_empty_state_shown`, `home_section_degraded`.
- Data access: the client reads only through the generated API client; no component computes permission, availability, or ordering locally, because the server already dropped what the caller may not see (ticket FR-F069-03).
- Dependencies: F062 design system for the card, button, skeleton, banner, toast, empty-state and live-region patterns and for every token; F005 workspace routes behind the onboarding suggestions; T273 for the home payload and T274 for the favourite routes.
- Feature flag: `F069_FEATURE` gates the index route; with the flag off the previous landing behaviour stands.

## TDD

- Failing test first: `testing/features/F069/frontend/HomePage.test.tsx::renders_sections_in_server_order`, `::hides_unavailable_sections`, `::degraded_section_shows_correlation_id_and_retry`, `::skeleton_reserves_final_height`; `testing/features/F069/frontend/HomeEmptyState.test.tsx::new_user_sees_single_centred_panel`, `::no_workspace_access_offers_request_access_only`; `testing/features/F069/frontend/FavoriteStar.test.tsx::toggle_is_optimistic_and_announces`, `::rolls_back_on_not_found_with_stale_message`, `::disabled_offline_with_badge`; `testing/features/F069/frontend/RecentsList.test.tsx::orders_by_last_visited_desc`; `testing/features/F069/e2e/home.spec.ts::sign_in_lands_on_home`, `::opening_a_sheet_moves_it_to_top_of_recents`, `::pin_from_sheet_header_appears_in_favourites`, `::first_run_user_sees_empty_state`; `testing/features/F069/accessibility/home.a11y.spec.ts::home_has_no_serious_violations_in_both_themes`, `::sections_are_labelled_regions_with_headings`, `::favourite_toggle_state_not_colour_only`
- Targeted command: `cargo xtask test-feature F069`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers over the `testing/fixtures/home.rs` payloads for a full user, a first-run user, a viewer with no workspace access, and a degraded approvals section; Playwright against the seeded tenant

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Index route registered behind the flag; `FavoriteStar` exported and consumed by at least one other feature header
- [ ] Screen matches `design/artboards/Home.dc.html`; where it cannot, the artboard is corrected, not the ticket
- [ ] axe reports zero serious or critical violations in both themes and both densities
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass, including no literal colour, spacing, or duration and no direct vendor import
- [ ] Handoff evidence recorded in S138
- [ ] `finished_at` recorded
