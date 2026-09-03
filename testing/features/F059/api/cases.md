# F059 api cases

File: `testing/features/F059/api/{publication_tests.rs,token_tests.rs,refresh_tests.rs,embed_tests.rs,security_tests.rs}`. Flag `F059_FEATURE`.

- `publication_create_returns_token_once` — FR-F059-01, FR-F059-02: POST → 201, `token` present; GET never returns it.
- `publication_expiry_over_30_days_invalid` — FR-F059-01: `expires_at` 31 days → 400 `field_errors.expires_at`.
- `publication_bad_origin_invalid` — FR-F059-01: `http://intranet` origin → 400 `field_errors.embed.allowed_origins`.
- `publication_duplicate_active_target_conflicts` — FR-F059-01: second active link publication of the same view → 409.
- `publication_stale_version_conflicts` — FR-F059-09: `If-Match: 1` against version 2 → 409.
- `non_publisher_create_denied` — NFR-F059-02: editor without `publisher` → 403.
- `publication_cross_tenant_not_found` — FR-F059-11: tenant B on tenant A publication → 404.
- `token_stored_only_as_hash` — FR-F059-02: `publication_tokens.token_hash` equals SHA-256 of plaintext; no plaintext column.
- `rotate_token_grace_then_404` — FR-F059-02: old token renders for 10 minutes, then 404; `publication.updated.v1` with `["token"]`.
- `revoked_token_404_within_5s` — FR-F059-08: revoke, advance 5 s → public and embed 404; `publication.revoked.v1`.
- `expired_token_404` — FR-F059-08: clock past `expires_at` → 404; scheduler publishes `publication.revoked.v1` with reason expired.
- `public_render_returns_generated_at_and_stale_header` — FR-F059-05: response has `generated_at`, `X-OpsHub-Stale: false`.
- `public_render_stale_after_refresh_failure` — FR-F059-05: refresh job fails → `stale: true`, last snapshot still served.
- `public_render_error_state_when_target_deleted` — FR-F059-03: deleted dashboard → `error`, `reason: target_deleted`, empty payload.
- `refresh_hides_hidden_columns` — FR-F059-04: snapshot payload lacks the two hidden columns and comment counts.
- `refresh_marks_error_when_publisher_access_lost` — FR-F059-03: publisher removed from workspace → `error`, `publisher_access_lost`.
- `embed_sets_frame_ancestors_from_origins` — FR-F059-07: CSP header lists exactly the allowed origins; no `X-Frame-Options`.
- `embed_unlisted_origin_denied_state` — FR-F059-07: `Referer: https://evil.test` → denied state body, no data.
- `tenant_access_other_tenant_not_found` — FR-F059-06: tenant B session with tenant A tenant-access token → 404.
- `view_rows_sampled_per_minute` — FR-F059-10: 10 renders → 1 `publication_views` row; salted `client_hash`.
- `render_rate_limited_after_60_per_minute` — FR-F059-12: 61st request → 429 with `Retry-After`.
- `token_rejected_on_every_api_route` — FR-F059-14: OpenAPI-enumerated routes → 403 with bearer, query, and cookie presentation.
- `refresh_job_retries_then_dead_letters` — NFR-F059-04: storage failure ×3 → dead letter; `publication_refresh_failures_total` incremented.

Evidence: JUnit output and request logs under `testing/evidence/F059/api/`.
