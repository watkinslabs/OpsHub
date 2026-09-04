---
id: T056
type: task
status: planned
parent_epic: E003
parent_feature: F014
parent_story: S028
depends_on: [T055]
owned_paths: [crates/domain/src/forms/**, crates/persistence/src/forms/**, services/api/src/forms/**, testing/features/F014/api/**, testing/features/F014/e2e/**, testing/features/F014/accessibility/**, testing/features/F014/performance/**]
feature_flag: F014_FEATURE
branch: t056-abuse-upload-tests
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 4, 5, 9
- Capability contract: `docs/capability-contracts.md` row F014

# T056 — Abuse/upload tests

## Identity

- Parent story: `S028` Public submission
- Owner: platform
- Branch: `t056-abuse-upload-tests`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 5, 9; `docs/capability-contracts.md` row F014

## Objective

Implement the rate limiter, CAPTCHA adapter, honeypot, and upload policy for public submissions, and prove them with abuse, upload, end-to-end, accessibility, and performance suites.

## Specification

- Owned paths: `crates/domain/src/forms/{spam.rs, uploads.rs}` (policy logic only, no SQL), `crates/persistence/src/forms/form_version_repository.rs` (the upload-policy and MIME-allowlist reads), `services/api/src/forms/{rate_limit.rs, captcha_adapter.rs}`, `testing/features/F014/{api/abuse_tests.rs, api/upload_tests.rs, e2e/forms.spec.ts, accessibility/forms.a11y.spec.ts, performance/submission_bench.rs}`
- Contract/input: buckets `form:{token}:{ip_hash}` at 60 per hour and `form:{token}` at 1,000 per day in F038 `rate_limit_buckets`; `CaptchaVerifier` trait with `verify(token, ip_hash) -> Result<bool, Unavailable>` implemented by a provider-neutral HTTP adapter configured by deployment secret and a stub in tests; honeypot field name randomised per version and enabled by `form_versions.honeypot_enabled`, CAPTCHA by `form_versions.captcha_enabled`; `UploadPolicy { max_files: 10, max_bytes: 26_214_400, mime_allowlist }` is loaded by `FormVersionRepository` from the `upload_max_files` and `upload_max_bytes` columns and the `form_version_upload_mime_types` rows, so the count and size caps are `check` constraints and the allowlist is matched by join, not by scanning a JSON array.
- Output/behavior: over-limit requests return `429 rate_limited` with `Retry-After` seconds and reason `rate_limited` before any database write; CAPTCHA failure and filled honeypot both return `400 invalid` with the same body shape and reasons `captcha_failed` and `honeypot` recorded only in the intake event; verifier outage returns `503 unavailable` and increments `form_captcha_unavailable_total`; uploads over `upload_max_files`, over `upload_max_bytes`, or with no matching `form_version_upload_mime_types` row reject with reason `upload_rejected` and `field_errors.<key>`; accepted files go through F017 when `F017_FEATURE` is on and otherwise are stored as `pending_attachments`; `ip_hash` is a salted SHA-256; payloads never appear in logs.
- Dependencies: T055 submission path; F038 rate-limit buckets; F017 upload API when present.
- Feature flag: `F014_FEATURE`

## TDD

- Failing test first: `testing/features/F014/api/abuse_tests.rs::submission_rate_limit_returns_429_with_retry_after`, `::daily_token_limit_enforced`, `::honeypot_filled_rejected_without_hint`, `::captcha_failure_rejected`, `::captcha_unavailable_fails_closed`, `::payload_over_one_megabyte_rejected`; `testing/features/F014/api/upload_tests.rs::upload_over_limit_rejected`, `::upload_mime_outside_allowlist_rejected`, `::upload_pending_when_files_flag_off`; `testing/features/F014/e2e/forms.spec.ts::build_publish_submit_and_see_row`, `::public_form_mobile_submit`, `::embedded_form_submits_in_iframe`, `::closed_form_shows_notice`; `testing/features/F014/performance/submission_bench.rs::public_schema_p95`, `::submission_accept_p95`, `::rate_limiter_burst`
- Targeted command: `cargo xtask test-feature F014`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: verifier stub keyed by token prefix; 40-field form for performance lane; Playwright mobile viewport profile against a seeded tenant; k6 burst script with fixed seed

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Abuse, upload, E2E, accessibility, and performance lanes pass; p95 targets from NFR-F014-01 met
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S028
- [ ] `finished_at` recorded
