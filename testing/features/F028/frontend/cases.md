# F028 frontend cases

File: `testing/features/F028/frontend/{ApplicationForm.test.tsx,TokenRevealDialog.test.tsx,WebhookForm.test.tsx,SecretRevealDialog.test.tsx,DeliveryLog.test.tsx,DeliveryDrawer.test.tsx,ReferencePage.test.tsx}`. Vitest with MSW. Flag `F028_FEATURE`.

- `validates_scopes_and_rate_limit` — FR-F028-02: `ApplicationForm` requires at least one scope and rejects rate limit 30 and 7,000 inline.
- `shows_token_once` — FR-F028-02: `TokenRevealDialog` shows the token, copy announces, closing hides permanently.
- `rejects_http_url` — FR-F028-08: `WebhookForm` blocks `http://` and shows the 400 `field_errors.url` for a private address.
- `event_picker_supports_wildcards` — FR-F028-08: selecting `row.*` renders the matched catalog events and caps at 50.
- `shows_attempts_and_replay` — FR-F028-12: `DeliveryLog` renders 120 deliveries with status text and icon; `Replay` calls `replayDelivery` and shows the new ID.
- `filters_deliveries_by_status_and_event` — FR-F028-12: filter controls change the query key and rendered rows.
- `disabled_webhook_shows_reason_and_reenable` — FR-F028-11: `disabled` row shows `consecutive_failures` reason; `Re-enable` calls `updateWebhook` with `status: active`.
- `drawer_shows_signature_sample` — FR-F028-15: `DeliveryDrawer` renders the envelope (4 KB cap) and a curl verification sample.
- `reference_page_renders_openapi` — FR-F028-15: `ReferencePage` renders operations grouped by tag from `getOpenApi`.
- `shows_denied_page_for_member` — FR-F028-14: member loading `/admin/developer/applications` sees the denied page.
- `shows_error_banner_with_correlation_id` — FR-F028-06: 500 renders banner with `correlation_id` and retry.

Evidence: Vitest JUnit under `testing/evidence/F028/frontend/`.
