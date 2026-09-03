# F028 e2e cases

File: `testing/features/F028/e2e/developer.spec.ts`. Playwright against seeded tenant with the harness receiver. Flag `F028_FEATURE`.

- `create_app_webhook_receive_signed_delivery` — FR-F028-02, FR-F028-08, FR-F028-09, FR-F028-15: admin creates application `Finance sync`, copies the token, creates webhook for `row.updated.v1` on sheet `Budget`, edits a row; delivery log shows `succeeded` with 200; receiver log shows a valid signature.
- `failures_disable_then_reenable_and_replay` — FR-F028-10, FR-F028-11, FR-F028-12: receiver set to 500; clock advanced through the retry schedule for 10 events; webhook shows `disabled`; admin re-enables and replays the last delivery; receiver receives it with a new delivery ID.
- `api_client_pages_with_cursor_and_rate_limit` — FR-F028-04, FR-F028-07: scripted client lists 250 rows with `limit=100` across three pages and observes `X-RateLimit-Remaining` decreasing.
- `member_cannot_open_developer_console` — FR-F028-14: member visits `/admin/developer/webhooks` and sees the denied page.
- `secret_rotation_keeps_deliveries_flowing` — FR-F028-13: rotate secret, edit a row, receiver verifies with the old secret during grace and with the new secret after.
- `reference_page_matches_served_document` — FR-F028-01: reference page operation count equals `paths` count in `/api/v1/openapi.json`.

Evidence: Playwright traces and receiver logs under `testing/evidence/F028/e2e/`.
