# F051 performance cases

File: `testing/features/F051/performance/{manifest_bench.rs,shell_bench.spec.ts}`. Runs against the generated `large_app` (50 pages, 20 roles, 200 members) with fixed seed. Flag `F051_FEATURE`.

- `manifest_50_pages_20_roles_p95` — NFR-F051-01: 200 sequential `GET /apps/{slug}` as a user holding three roles via groups; p95 < 300 ms warm.
- `shell_nav_render_under_500ms` — NFR-F051-01: Playwright measures time from manifest response to navigation painted; p95 < 500 ms over 50 loads.
- `publish_large_manifest_p95` — FR-F051-04: 50 publishes of the large app; p95 < 800 ms including snapshot and outbox write.
- `member_lookup_uses_gin_index` — NFR-F051-01: role resolution for a user in 40 groups scans via the GIN index; p95 < 50 ms.

Evidence: criterion/k6 summaries under `testing/evidence/F051/performance/`.
