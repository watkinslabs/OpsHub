# F055 frontend cases

File: `apps/web/src/features/calendar-app/__tests__/` run through `testing/features/F055/frontend/`. Flag `F055_FEATURE`.

- `MonthGrid renders events in tenant week-start order` — FR-F055-13: `week_start: monday` and `sunday` produce different first columns for the same month.
- `LayoutSwitch and TimezoneSwitcher write the URL` — FR-F055-13: switching to week view and `Asia/Tokyo` updates the query string and refetches with the new `tz`.
- `SourceLegend toggles hide and restore a source` — FR-F055-13: toggling source 2 removes its chips without refetching; state survives layout change.
- `HiddenSourcesNotice reports permission-hidden sources` — FR-F055-04: `hidden_sources: 2` renders the notice with the count and no source names.
- `EventChip drag rolls back on conflict` — FR-F055-06: mocked 409 restores the original slot and shows the stale-version message.
- `Read-only viewer hides editing affordances` — FR-F055-14: `can_edit: false` renders no drag handle, no `Edit sources`, and no `Publish`.
- `ModuleNotEntitled replaces the page without the module` — FR-F055-12: `useModuleAllowed('calendar-app')` false → entitlement state, no data request.
- `PublishDialog shows the feed URL once and the expiry` — FR-F055-07: URL is copyable, shown once, and re-opening the dialog offers revoke instead.
- `Loading, empty, error, and denied states render` — FR-F055-13: skeleton grid, empty-window message, error banner with `correlation_id`, denied state.

Evidence: component test report under `testing/evidence/F055/frontend/`.
