# F028 api cases

File: `testing/features/F028/api/{openapi_tests.rs,application_tests.rs,list_query_tests.rs,error_tests.rs,rate_limit_tests.rs,webhook_tests.rs,delivery_tests.rs,contract_tests.rs,negative_tests.rs}`. Flag `F028_FEATURE`.

- `openapi_document_lists_every_route` — FR-F028-01: every route in the router appears in `paths`; `Error` and `Page` schemas present; `info.version` equals the build.
- `openapi_drift_fails_check_contracts` — FR-F028-01: changing a DTO without regenerating `openapi/v1.json` makes `check-contracts` exit non-zero.
- `application_create_returns_client_id` — FR-F028-02: POST as tenant-admin → 201, `client_id`, `version: 1`, default rate limit 600.
- `application_suspend_rejects_tokens_within_5s` — FR-F028-03: PATCH `status: suspended` → token request 401 `denied` after at most 5 s.
- `application_member_denied` — FR-F028-14: member POST/PATCH/DELETE → 403 `denied`.
- `list_query_invalid_cursor_returns_field_error` — FR-F028-04: tampered cursor → 400 `field_errors.cursor`.
- `list_query_expired_cursor_rejected` — FR-F028-04: cursor older than 24 h → 400 `invalid`.
- `list_query_unknown_filter_field_rejected` — FR-F028-04: `filter=colour eq red` → 400 `field_errors.filter`.
- `list_query_fields_projection_keeps_id_and_version` — FR-F028-05: `fields=name` → items with exactly `id`, `version`, `name`.
- `error_body_echoes_correlation_id` — FR-F028-06: `X-Correlation-Id` supplied → same value in body and response header; missing → UUIDv7 generated.
- `rate_limit_headers_and_429` — FR-F028-07: 121 requests at 60/min → 120 OK with headers, 121st 429 with `Retry-After`.
- `allowed_ips_rejects_other_source` — NFR-F028-02: application with `allowed_ips` → request from another address 403 `denied`.
- `webhook_create_returns_secret_once` — FR-F028-08: 201 with `secret`; subsequent GET omits it; `webhook.updated.v1` published.
- `webhook_create_rejects_private_url` — NFR-F028-02: `https://10.0.0.5/x`, `https://localhost/x`, `https://169.254.169.254/` → 400 `invalid`.
- `delivery_signature_matches_vector` — FR-F028-09: fixed secret, timestamp, body → header `v1=` equals the precomputed HMAC-SHA256.
- `delivery_retry_schedule_and_exhausted` — FR-F028-10: receiver 500 → `next_attempt_at` offsets 60, 300, 1800, 7200, 43200 s ±10 %; fifth failure → `exhausted`, `webhook.failed.v1` once.
- `webhook_disabled_after_ten_exhausted` — FR-F028-11: tenth exhausted delivery → `status: disabled`, `disabled_reason: consecutive_failures`, `webhook.disabled.v1`.
- `delivery_success_resets_counter` — FR-F028-11: 9 exhausted then one success → `consecutive_failures 0`.
- `delivery_replay_new_id_within_30_days` — FR-F028-12: replay → 202, new delivery with `replay_of`; at 31 days → 409 `conflict`.
- `delivery_replay_disabled_webhook_conflicts` — FR-F028-12: replay on disabled webhook → 409 `conflict`.
- `webhook_rotate_secret_dual_signature_24h` — FR-F028-13: after rotation header carries two `v1=` values; old one absent at +25 h.
- `delivery_payload_filtered_by_scopes` — FR-F028-14: application without `comments:read` → `row.updated.v1` payload omits comment fields.
- `dispatcher_idempotent_after_restart` — NFR-F028-04: consumer restarted mid-batch → exactly one delivery per `(webhook_id, event_id)`.
- `dispatcher_rejects_dns_rebind_at_attempt` — NFR-F028-02: host resolving to a private address at attempt time → attempt `failed` with `error: private_address`.
- `page_responses_match_openapi_schema` — FR-F028-01: six list routes validated against their `Page` schema.
- `suspended_application_token_rejected` — FR-F028-03: token of suspended application → 401 on any route.
- `foreign_tenant_webhook_not_found` — FR-F028-14: tenant B webhook and delivery IDs → 404 from tenant A.
- `webhook_metrics_emitted` — NFR-F028-04: `webhook_delivery_total{status}` and `api_rate_limited_total` observed after the suite.

Evidence: JUnit output and receiver logs under `testing/evidence/F028/api/`.
