# F019 frontend cases

File: `testing/features/F019/frontend/{RunTable.test.tsx,RunDetailPage.test.tsx,StepTimeline.test.tsx,RetryRunDialog.test.tsx,InboundWebhookCard.test.tsx}`. Vitest with MSW. Flag `F019_FEATURE`.

- `renders_status_badges_with_text_and_icon` — NFR-F019-03: six statuses render label text plus a Lucide icon, never color alone.
- `status_filter_chips_update_query` — FR-F019-11: clicking `Failed` chip refetches with `filter[status]=failed`.
- `polls_while_run_active_and_visible` — FR-F019-14: `queued` run refetches every 5 s; stops when `completed` or tab hidden.
- `step_timeline_shows_error_for_failed_step` — FR-F019-05: failed step 2 renders `StepErrorPanel` with `error.code` and attempt count.
- `run_detail_retry_rolls_back_on_conflict` — FR-F019-12: retry 409 restores `dead_lettered` badge and shows `This run already finished`.
- `viewer_hides_retry_and_cancel` — FR-F019-14: viewer role renders no `Retry`/`Cancel` buttons and a read-only note.
- `shows_not_found_for_foreign_run` — NFR-F019-02: 404 renders not-found page.
- `shows_error_banner_with_correlation_id` — NFR-F019-04: 500 response shows banner with `correlation_id` and retry.
- `offline_disables_controls` — FR-F019-14: `navigator.onLine=false` disables retry/cancel with offline badge.
- `table_collapses_to_cards_under_768` — FR-F019-14: narrow viewport renders card list with status, trigger, duration.
- `webhook_card_shows_url_and_rotate` — FR-F019-04: card renders `/api/v1/webhooks/inbound/{token}` and rotate emits `webhook_token_rotated`.
- `keyboard_shortcuts_open_dialogs` — NFR-F019-03: `R` opens retry dialog, `C` cancel dialog, `Escape` closes.

Evidence: Vitest JUnit under `testing/evidence/F019/frontend/`.
