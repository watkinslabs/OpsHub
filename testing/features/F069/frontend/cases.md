# F069 frontend cases

File: `testing/features/F069/frontend/{HomePage.test.tsx,HomeSectionCard.test.tsx,HomeEmptyState.test.tsx,FavoriteStar.test.tsx,FavoritesList.test.tsx,RecentsList.test.tsx}`. Vitest with MSW. Flag `F069_FEATURE`.

- `renders_sections_in_server_order` — FR-F069-01: the five sections appear in the order the payload lists them, and the order is identical at the three, two and one column breakpoints.
- `hides_unavailable_sections` — FR-F069-02: a section with `state: unavailable` renders nothing at all, not an empty card.
- `degraded_section_shows_correlation_id_and_retry` — FR-F069-02: a degraded approvals section shows the `correlation_id`, and retry refetches only the home query.
- `skeleton_reserves_final_height` — NFR-F069-03: the skeleton and the loaded section have the same height, so nothing shifts on arrival.
- `new_user_sees_single_centred_panel` — FR-F069-12: a first-run payload renders one panel with two workspace buttons and `Create a sheet`, not five empty cards.
- `no_workspace_access_offers_request_access_only` — FR-F069-12: `request_access` with no create action for a viewer with no readable workspace.
- `empty_reason_selects_the_copy` — FR-F069-12: `none_yet`, `all_clear` and `no_access` each render their own sentence.
- `toggle_is_optimistic_and_announces` — FR-F069-05: clicking `FavoriteStar` fills immediately, adds the row to the favourites list, and announces through a polite live region.
- `rolls_back_on_not_found_with_stale_message` — FR-F069-09: a `not_found` response reverts the toggle and shows `That item is no longer available`.
- `disabled_offline_with_badge` — NFR-F069-04: offline disables pin and unpin, shows the offline badge, and renders the cached home payload behind a banner.
- `unavailable_favourites_show_label_without_link` — FR-F069-04: `Show unavailable` renders greyed rows with the cached label, no link and a `Remove` action.
- `orders_by_last_visited_desc` — FR-F069-08: `RecentsList` puts the most recently visited target first and shows its visit count.
- `item_open_emits_telemetry_with_position` — FR-F069-13: opening an item emits `home_item_opened` with the section, target kind and position.

Evidence: Vitest JUnit under `testing/evidence/F069/frontend/`.
