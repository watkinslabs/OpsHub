---
id: T110
type: task
status: planned
parent_epic: E006
parent_feature: F028
parent_story: S055
depends_on: [T109]
owned_paths: [crates/contracts/src/public-api/**, services/api/src/public-api/**, testing/features/F028/api/**, testing/features/F028/performance/**]
feature_flag: F028_FEATURE
branch: t110-pagination-errors
started_at: null
finished_at: null
---

# T110 — Pagination/errors

## Identity

- Parent story: `S055` REST API
- Owner: platform
- Branch: `t110-pagination-errors`
- Decision references: `docs/architecture-decisions.md` section 3; `docs/capability-contracts.md` row F028

## Objective

Implement the shared list-query extractor, signed cursors, filter grammar, field projection, error mapper, correlation-ID layer, per-application rate limiting, and allowed-IP enforcement mounted on the whole `/api/v1` router.

## Specification

- Owned paths: `crates/contracts/src/public-api/{list_query.rs, filter.rs, cursor.rs, projection.rs}`, `services/api/src/public-api/{middleware.rs, rate_limit.rs, correlation.rs, error_mapper.rs}`
- Contract/input: query `cursor`, `limit`, `filter` (`field op value` joined by `and`; operators `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`, `contains`, `is_null`; ≤ 10 terms), `sort` (≤ 3 keys, `-` prefix for descending), `fields`, `include_total`; header `X-Correlation-Id` (UUID); application token context from F038 with `application_id`, `rate_limit_per_minute`, `allowed_ips`.
- Output/behavior: `ListQuery<F: FilterSchema>` extractor validates fields against the route's schema and returns `400 invalid` with `field_errors.cursor`, `.filter`, `.sort`, or `.fields`; `SignedCursor` encodes `(sort keys, last values)` with HMAC-SHA256 and a 24-hour expiry; `Page<T> { items, next_cursor, has_more, total? }`; `projection.rs` keeps `id` and `version` always; `error_mapper.rs` converts every `ApiError` to `{ code, message, field_errors, correlation_id }` with statuses 400/403/404/409/429/503; `correlation.rs` echoes or generates the ID and attaches it to the tracing span; `rate_limit.rs` keeps a token bucket per application in F038 `rate_limit_buckets` (capacity 2x, refill `rate_limit_per_minute` per minute) and sets `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, and `Retry-After` on 429; `allowed_ips` mismatch returns `403 denied`; metric `api_rate_limited_total{application}`.
- Dependencies: T109 application registry; F038 token context and `rate_limit_buckets`; F004 tracing layer.
- Feature flag: `F028_FEATURE` gates the per-application rate limiter; list and error conventions are always on.

## TDD

- Failing test first: `testing/features/F028/api/list_query_tests.rs::list_query_invalid_cursor_returns_field_error`, `::list_query_expired_cursor_rejected`, `::list_query_unknown_filter_field_rejected`, `::list_query_filter_in_and_contains`, `::list_query_sort_three_keys_max`, `::list_query_fields_projection_keeps_id_and_version`, `::list_query_include_total_when_allowed`; `testing/features/F028/api/error_tests.rs::error_body_echoes_correlation_id`, `::error_generates_uuidv7_when_header_missing`; `testing/features/F028/api/rate_limit_tests.rs::rate_limit_headers_and_429`, `::rate_limit_burst_double_capacity`, `::allowed_ips_rejects_other_source`; `testing/features/F028/performance/list_bench.rs::list_conventions_overhead_under_20ms`
- Targeted command: `cargo xtask test-feature F028`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: application limited to 60 per minute; fixed clock for cursor expiry; 10,000-row sheet for list overhead

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Middleware mounted on the `/api/v1` tree in `services/api/src/router.rs`; existing feature list routes adopt `ListQuery` without behavior change
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S055
- [ ] `finished_at` recorded
