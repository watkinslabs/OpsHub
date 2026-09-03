# F006 e2e cases

File: `testing/features/F006/e2e/sheet.spec.ts`. Playwright against seeded tenant. Flag `F006_FEATURE`.

- `create_sheet_add_row_move_card` — FR-F006-01, FR-F006-06, FR-F006-08, FR-F006-13: editor creates "Launch plan", adds row "Kickoff", switches to board, drags card to "Doing", reload shows card in "Doing".
- `duplicate_sheet_name_shows_field_error` — FR-F006-02: second "Launch plan" in the same folder shows inline name error.
- `restore_deleted_sheet` — FR-F006-05: delete sheet, open folder trash, restore, rows visible with same URL.
- `viewer_is_read_only` — FR-F006-14: viewer login sees grid and board without add/move controls.
- `non_member_sees_not_found` — FR-F006-14: user outside workspace opens sheet URL → not-found page.
- `concurrent_edit_shows_stale_banner` — FR-F006-04: second session renames sheet; first session's rename shows stale banner and reload.
- `keyboard_only_board_move` — FR-F006-13, NFR-F006-03: no mouse; card moved with Space/Arrow/Enter; live region announces move.

Evidence: Playwright traces and videos under `testing/evidence/F006/e2e/`.
