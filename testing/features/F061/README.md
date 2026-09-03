# F061 — Update requests harness

Feature-gated tests for `F061`. Keep test code in this directory.

- Gate: `F061_FEATURE`
- Targeted: `cargo xtask test-feature F061`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/update_requests.rs` (tenants A and B, sheet `Site works` with 12 typed columns including a formula column and 250 rows, requester, sheet-admin, plain member, two internal recipients, external recipient `paul@contractor.example`, an open request scoped to 12 rows × 3 columns, plus completed, cancelled, and expired requests, a 100,000-row `reminder_schedules` generator, a recorded `NotificationService` returning fixed `notification_id`s, a recorded outbox, a fixed token seed, and the clock `2026-09-03T00:00:00Z` with an `Australia/Sydney` tenant for DST cadence cases).
- Public routes run without a session: API tests send no auth header and Playwright uses a browser context with no cookies, so token scope is the only authority under test.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
