# F058 e2e cases

File: `testing/features/F058/e2e/{mobile.spec.ts,push.spec.ts}`. Playwright Pixel 7 emulation against seeded tenant with the push recorder. Flag `F058_FEATURE`.

- `install_edit_offline_reconnect_syncs` — FR-F058-01, FR-F058-03, FR-F058-04, FR-F058-08: install, go offline, edit 3 cells and submit a form, badge `4 pending`, reconnect, badge 0, server shows all changes.
- `conflict_card_keep_mine_and_take_theirs` — FR-F058-05, FR-F058-08: desktop session edits the same cell; mobile reconnect shows card; Keep mine wins on first, Take theirs on second.
- `lost_permission_rejected_at_sync` — FR-F058-05: admin downgrades user while offline; reconnect shows denied rejection and no change.
- `push_tap_opens_row_and_marks_read` — FR-F058-09, FR-F058-10: assignment push delivered; tap opens `/m/rows/{id}`; inbox shows read.
- `deep_link_requires_login` — FR-F058-09: logged-out user opens link, logs in, lands on the row.
- `logout_wipes_queue_and_cache` — FR-F058-11: logout with 2 queued ops clears storage; reopening shows empty queue.
- `flag_off_serves_responsive_web_only` — FR-F058-14: flag off shows no install prompt and `/m/home` is not found.

Evidence: Playwright traces and videos under `testing/evidence/F058/e2e/`.
