# F053 e2e cases

File: `testing/features/F053/e2e/datamesh.spec.ts`. Playwright against seeded tenant. Flag `F053_FEATURE`.

- `create_mapping_preview_sync_resolve` — FR-F053-01, FR-F053-04, FR-F053-05, FR-F053-06, FR-F053-08, FR-F053-14: admin creates `Vendors → Purchase requests` keyed by `Vendor ID` with `trim`, previews counts, presses `Sync now`, watches the run succeed with `updated 96`, opens `Conflicts`, resolves an `ambiguous_match` with `keep_target`, and sees it marked resolved.
- `provenance_link_visible_in_target_grid` — FR-F053-06: opening `Purchase requests` in the grid shows the `datamesh` link badge on `Terms` cells with the source row in the tooltip.
- `on_change_sync_after_source_edit` — FR-F053-09: editing `Payment terms` on the master sheet triggers one run within 90 s and the target cell updates.
- `both_changed_edit_creates_conflict` — FR-F053-07: editing `Vendor contact` on both sheets then syncing leaves both cells unchanged and shows a `both_changed` conflict side by side.
- `viewer_sees_read_only_tabs` — FR-F053-12, NFR-F053-02: viewer opens the mapping; no `Sync now`, `Resolve`, or `Edit` controls; preview hides unreadable columns.
- `tenant_without_entitlement_sees_panel` — FR-F053-12: tenant B admin opens `/w/{id}/datamesh` → `ModuleNotEntitled` panel.
- `flag_off_hides_module` — FR-F053-12: with `F053_FEATURE` off, navigation entry absent, route 404, source edits trigger no run.

Evidence: Playwright traces and videos under `testing/evidence/F053/e2e/`.
