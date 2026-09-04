# F069 e2e cases

File: `testing/features/F069/e2e/{home.spec.ts,home_permissions.spec.ts}`. Playwright against the seeded tenant with the three section slots stubbed. Flag `F069_FEATURE`.

- `sign_in_lands_on_home` — FR-F069-13: signing in as the seeded member lands on `/` with the five sections rendered and no route restore from the previous session.
- `opening_a_sheet_moves_it_to_top_of_recents` — FR-F069-07, FR-F069-08: opening `Cutover plan`, waiting one flush interval and returning to home puts it first under `Recently visited` with a visit count of one.
- `pin_from_sheet_header_appears_in_favourites` — FR-F069-05: starring `Vendor reviews` in the sheet header fills the star, shows the undo toast, and the sheet appears under `Favourites` on home without a reload.
- `unpin_from_home_removes_it_everywhere` — FR-F069-06: unstarring from the home card clears the star in the sheet header on the next visit.
- `first_run_user_sees_empty_state` — FR-F069-12: the brand-new member sees one centred panel with the workspace buttons and `Create a sheet`, and clicking a workspace navigates into it.
- `unshared_sheet_disappears_from_home` — FR-F069-09: an admin removes the member's access to a pinned and recently visited sheet; the member reloads home and it is gone from both sections with nothing indicating why.
- `unavailable_favourite_can_be_removed` — FR-F069-04: after the sheet is purged, `Show unavailable` lists the cached label and `Remove` clears it.
- `degraded_section_does_not_block_the_page` — FR-F069-02: with the approvals stub failing, the page still renders the other four sections and offers retry on the failed one.

Evidence: Playwright traces and network logs under `testing/evidence/F069/e2e/`.
