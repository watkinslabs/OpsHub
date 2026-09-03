# F058 frontend cases

File: `testing/features/F058/frontend/{MobileShell.test.tsx,MobileGrid.test.tsx,RowDetailPage.test.tsx,MobileFormPage.test.tsx,Queue.test.tsx,ConflictCard.test.tsx,ServiceWorker.test.ts}`. Vitest with MSW at 360 px. Flag `F058_FEATURE`.

- `registers_service_worker_when_flag_on` — FR-F058-01: shell registers `sw.js` and shows the install prompt.
- `flag_off_hides_install_and_routes` — FR-F058-14: flag off renders no prompt and no `/m/*` routes.
- `mobile_grid_edits_cell_online` — FR-F058-12: tap Status cell, choose option, `PATCH cells` called with `If-Match`.
- `swipe_changes_visible_column` — FR-F058-12: horizontal swipe advances the secondary column.
- `stale_chip_on_conflict` — FR-F058-08: 409 from cells API shows `Updated on server` chip.
- `denied_cell_shows_lock` — FR-F058-05: denied response shows lock icon and message.
- `queue_stores_edit_offline` — FR-F058-03: offline edit lands in IndexedDB with `client_op_id` and pending chip.
- `queue_full_blocks_edits` — FR-F058-03: 500 queued ops disables editors with explanation.
- `sync_pushes_then_pulls_on_reconnect` — FR-F058-08: online event triggers push, then pull, badge drains to 0.
- `conflict_card_keep_mine_resubmits` — FR-F058-08: Keep mine re-queues with `server_version`; Take theirs writes server value locally.
- `revoke_wipes_queue_and_key` — FR-F058-11: revoke event clears IndexedDB, cache, and key; no refresh token in `localStorage`.
- `notificationclick_opens_deep_link` — FR-F058-10: service worker opens `/m/{deep_link}` and calls read endpoint.
- `submits_with_conditional_fields` — FR-F058-12: form page hides conditional field and submits through `FormsApi`.

Evidence: Vitest JUnit under `testing/evidence/F058/frontend/`.
