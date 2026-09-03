# F048 e2e cases

File: `testing/features/F048/e2e/entitlements.spec.ts`. Playwright against seeded tenant. Flag `F048_FEATURE`.

- `enable_trial_then_override_shows_module` — FR-F048-02, FR-F048-04, FR-F048-09, FR-F048-14: admin sets `data-shuttle` to trial until 2026-10-03 with `max_flows 5`, sets override on `F052_FEATURE` with reason, reloads, and `Data Shuttle` appears in workspace navigation.
- `kill_switch_removes_module_access` — FR-F048-06, FR-F048-10: platform operator kills `F052_FEATURE`; admin session opening `/data-shuttle` sees the not-entitled panel with reason `killed`.
- `expired_trial_shows_not_entitled` — FR-F048-09: `bridge` trial ended yesterday; opening `/bridge` shows the panel with `Trial expired` and a link to `/admin/entitlements`.
- `member_cannot_open_admin_pages` — FR-F048-14, NFR-F048-02: member navigates to `/admin/feature-flags` → denied state, no table rendered.
- `tenant_admin_platform_fields_locked` — FR-F048-04: admin opens `F050_FEATURE` drawer; lifecycle fields are read-only; API PATCH forged from the console returns 403.
- `flag_off_hides_admin_routes` — FR-F048-10: with `F048_FEATURE` off, `/admin/entitlements` is not-found and `/bridge` shows the panel with reason `not_entitled`.
- `stale_override_shows_conflict_banner` — FR-F048-11: second session changes the override; first session save shows the stale banner and reload restores the new value.

Evidence: Playwright traces and videos under `testing/evidence/F048/e2e/`.
