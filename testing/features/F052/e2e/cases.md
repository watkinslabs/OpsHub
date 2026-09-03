# F052 e2e cases

File: `testing/features/F052/e2e/data_shuttle.spec.ts`. Playwright against seeded tenant with MinIO. Flag `F052_FEATURE`.

- `create_flow_run_and_replay` — FR-F052-01, FR-F052-06, FR-F052-07, FR-F052-09, FR-F052-14: admin creates "Budget import" from a sample, maps `Cost center` as key with `update`, presses `Run now`, watches `queued → running → succeeded` with `rows_updated 100`, opens the drawer, replays, and sees a second run with `Replay of` link.
- `archive_download_uses_expiring_url` — FR-F052-08, NFR-F052-02: `Download archive` opens a signed URL; the same URL after 16 minutes returns 403.
- `scheduled_run_fires_after_next_run_at` — FR-F052-03, FR-F052-06: harness advances the scheduler clock past `next_run_at`; the run list shows a `scheduled` run within 60 s.
- `validation_abort_shows_rejected_rows` — FR-F052-04: file missing `Amount` in 12 rows with `abort` → run `failed`, drawer lists 12 rejected rows, sheet unchanged.
- `viewer_sees_read_only_history` — FR-F052-12, NFR-F052-02: viewer opens the flow; no `Run now`, `Replay`, or `Edit` controls.
- `tenant_without_entitlement_sees_panel` — FR-F052-12: tenant B admin opens `/w/{id}/data-shuttle` → `ModuleNotEntitled` panel.
- `flag_off_hides_module` — FR-F052-12: with `F052_FEATURE` off, navigation entry absent, route 404, scheduler does not fire.

Evidence: Playwright traces and videos under `testing/evidence/F052/e2e/`.
