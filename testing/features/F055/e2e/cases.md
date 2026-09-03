# F055 e2e cases

File: `testing/features/F055/e2e/` (Playwright against the seeded tenant). Flag `F055_FEATURE`.

- `create_calendar_bind_two_sources_and_view_month` — FR-F055-01, FR-F055-02, FR-F055-13: editor creates `Launch`, binds a sheet and a view, and sees chips from both in month view.
- `drag_event_reschedules_row_and_persists` — FR-F055-06: dragging a chip two days later updates the source row and survives reload.
- `timezone_switch_moves_events_across_dst` — FR-F055-05: switching from `UTC` to `America/New_York` across the 2026-11-01 transition renders the documented times.
- `publish_feed_and_subscribe_anonymously` — FR-F055-07, FR-F055-08: publish, fetch the `.ics` in a session-free context, and parse the expected `VEVENT` set.
- `revoke_publication_breaks_the_feed` — FR-F055-07: after revoke the same URL returns 404 and the UI shows the publication as revoked.
- `viewer_without_source_access_sees_hidden_notice` — FR-F055-04, FR-F055-14: second user sees a subset of chips plus the hidden-sources notice and no editing controls.

Evidence: traces, videos, and fetched `.ics` bodies under `testing/evidence/F055/e2e/`.
