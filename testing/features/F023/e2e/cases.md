# F023 e2e cases

File: `testing/features/F023/e2e/{dashboard.spec.ts,visual.spec.ts}`. Playwright against seeded tenant. Flag `F023_FEATURE`.

- `build_save_share_and_view_as_guest` — FR-F023-01, FR-F023-02, FR-F023-09, FR-F023-12: editor builds "Weekly review" with four widgets, saves, shares with "Leadership", copies a link; guest opens the link and sees the denied tile for the Risks-backed table.
- `stale_badge_after_report_refresh` — FR-F023-05: report "Portfolio status" refreshes; dashboard viewer shows stale on the table widget; `Refresh` returns it to fresh.
- `viewer_cannot_open_builder` — FR-F023-10, NFR-F023-02: viewer navigates to `/edit` and sees the read-only viewer with no palette.
- `unregistered_kpi_shows_unavailable` — FR-F023-04: the seeded `kpi` widget renders the unavailable tile.
- `keyboard_only_build` — FR-F023-12, NFR-F023-03: no mouse; add a text widget from the palette, move it, resize it, save.
- `concurrent_edit_shows_conflict_banner` — FR-F023-10: second session saves widgets; first session's save shows the conflict banner and reload.
- `grid_matches_snapshots_at_three_widths` — FR-F023-12: visual snapshots at 1280, 800, 390 px within 0.1% pixel difference.

Evidence: Playwright traces, videos, and snapshots under `testing/evidence/F023/e2e/`.
