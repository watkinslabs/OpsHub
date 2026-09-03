# F055 api cases

File: `testing/features/F055/api/{calendar_tests.rs,source_tests.rs,event_tests.rs,timezone_tests.rs,publication_tests.rs,ics_tests.rs,negative_tests.rs}`. Flag `F055_FEATURE`.

- `create_calendar_defaults_timezone_from_tenant` — FR-F055-01: request without `default_timezone` inherits the tenant zone; `Mars/Olympus` → 400 `invalid`.
- `replace_sources_rejects_more_than_twenty` — FR-F055-02: 21 sources → 400 `invalid`; 20 persist in `position` order.
- `replace_sources_rejects_non_date_start_column` — FR-F055-02: text column as `start_column_id` → 400 with `field_errors.start_column_id`.
- `events_window_capped_at_366_days` — FR-F055-03: 367-day window → 400 `invalid`; 366 days succeeds.
- `events_filtered_by_row_permission_per_source` — FR-F055-04: viewer denied on source 2 → only source 1 events and `hidden_sources: 1`.
- `date_only_column_yields_all_day_event` — FR-F055-05: date column → `all_day: true` with no offset applied.
- `dst_gap_and_overlap_resolve_deterministically` — FR-F055-05: 2026-03-29 01:30 Europe/London and 2026-11-01 01:30 America/New_York map to the instants fixed in the ticket.
- `reschedule_requires_matching_version` — FR-F055-06: stale `If-Match` → 409 `conflict`; matching version updates the row and returns the new version.
- `publish_hashes_token_and_caps_expiry` — FR-F055-07: response carries the feed URL once; the row stores only `token_hash`; `expires_in_days: 31` → 400.
- `revoke_publication_invalidates_feed` — FR-F055-07: revoke → `revoked_at` set and the next feed read → 404 `not_found`.
- `ics_feed_streams_rfc5545_without_session` — FR-F055-08: anonymous read → `text/calendar`, `X-WR-CALNAME`, one `VTIMEZONE` per zone, `UID` `<row_id>@<calendar_id>`.
- `ics_feed_omits_non_mapped_values` — FR-F055-09: comments, attachments, and unmapped columns absent from the body.
- `ics_feed_follows_publisher_permissions_at_request_time` — FR-F055-09: revoking the publisher's row access mid-life removes those events from the next fetch.
- `ics_feed_rate_limited_per_token` — NFR-F055-02: 61st read in a minute → 429 `rate_limited`.
- `unknown_and_expired_tokens_return_not_found` — FR-F055-08: random token and an expired publication both → 404 with no tenant detail.
- `mutations_require_idempotency_key_and_emit_events` — FR-F055-11: missing key → 400; replay returns the first result; `calendar.updated.v1` and `calendar.published.v1` observed on the outbox.
- `module_gate_denies_unentitled_tenant` — FR-F055-12: tenant without `calendar-app` → 403 `denied` on all seven routes.
- `foreign_tenant_calendar_not_found` — FR-F055-14: tenant B id → 404 on read, patch, sources, events, and publish.
- `viewer_cannot_replace_sources_or_publish` — FR-F055-14: read-only viewer → 403 `denied` on `PUT /sources` and `POST /publish`.

Evidence: JUnit output and request logs under `testing/evidence/F055/api/`.
