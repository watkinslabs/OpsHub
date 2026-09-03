# F013 e2e cases

File: `testing/features/F013/e2e/views.spec.ts`. Playwright against seeded tenant. Flag `F013_FEATURE`.

- `create_card_view_and_move_card` — FR-F013-01, FR-F013-04, FR-F013-07, FR-F013-13: editor creates "Board by status" on `Status`, drags "Kickoff" from `Backlog` to `Doing`, reload shows the card in `Doing` and the grid cell reads `Doing`.
- `filter_and_sort_persist_across_reload` — FR-F013-02, FR-F013-03, FR-F013-05: add filter `Owner is_me` and sort `Due asc`, save, reload → same rows in the same order.
- `calendar_drag_reschedules_row` — FR-F013-06, FR-F013-07: calendar keyed on `Due`; drag "Kickoff" one week forward → event on the new day and grid `Due` updated.
- `timeline_zoom_and_drag` — FR-F013-04, FR-F013-07: timeline at `week` zoom; switch to `quarter`; drag a bar → reschedule applied and bar redrawn.
- `share_link_opens_read_only` — FR-F013-10, NFR-F013-02: owner creates a 30-day link; a logged-out browser opens it → rows visible, no drag handles, no switcher, tenant navigation absent.
- `private_view_hidden_from_other_user` — FR-F013-11: user B's switcher lacks user A's private view; direct URL → not-found page.
- `default_view_cannot_be_deleted` — FR-F013-09: delete on the default view is disabled with an explanatory tooltip; deleting another view returns to the default.
- `export_view_csv_matches` — FR-F013-14: export from a filtered view → download job completes, CSV has the same rows and columns as the view.

Evidence: Playwright traces and videos under `testing/evidence/F013/e2e/`.
