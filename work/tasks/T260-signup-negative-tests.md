---
id: T260
type: task
status: planned
parent_epic: E006
parent_feature: F065
parent_story: S130
depends_on: [S130, T258, T259]
owned_paths: [testing/features/F065/**]
feature_flag: F065_FEATURE
branch: t260-signup-negative-tests
started_at: null
finished_at: null
---

# T260 — Signup negative tests

## Identity

- Parent story: `S130` trial provisioning and conversion
- Owner: platform
- Branch: `t260-signup-negative-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 4, 9; `docs/capability-contracts.md` row F065

## Objective

Own the adversarial suite for the only unauthenticated write path in OpsHub: enumeration equivalence, token abuse, slug races, permission negatives, burst containment, and the retention proof that unverified personal data does not survive.

## Specification

- Owned paths: `testing/features/F065/{api/negative_tests.rs, api/enumeration_tests.rs, api/race_tests.rs, database/constraint_tests.rs, e2e/signup.spec.ts, e2e/trial_lifecycle.spec.ts, performance/signup_bench.rs, performance/sweep_bench.rs, requirements/cases.md}`
- Data access: no file in this suite opens a connection, writes SQL, or calls `sqlx::query*`. Every fixture write and every state assertion goes through the `crates/persistence/src/signup/` repositories — `SignupRequestRepository`, `SignupTokenRepository`, and `ReservedSlugRepository` — plus the F002, F048, and F064 repositories for cross-feature state, so the suite exercises the same code path as production and cannot pass on rows the repositories could not have produced. The sole exception is `database/constraint_tests.rs`, which asserts the constraints themselves by driving deliberate violations through the repositories and asserting the mapped database error (decision section 2.1).
- Contract/input: the routes `POST /public/signup`, `GET /public/signup/{token}`, `POST /public/signup/{token}/complete`, `GET /public/signup/availability`, and `POST /api/v1/signup/invitations`; the fixtures and spies from `testing/fixtures/signup.rs`.
- Output/behavior: the enumeration suite asserts identical status, headers, body bytes, and latency band across four cases — a new address, an address belonging to an active user, a taken slug, and a rate-suppressed request — and identical availability answers for taken, reserved, and soft-reserved slugs. The token suite covers expired, consumed, unknown, tampered, foreign-request, and sixth-attempt tokens, all resolving to `410 gone` or `429 rate_limited` with no oracle. The race suite drives two concurrent completions on one slug and asserts exactly one tenant, one `tenant.provisioned.v1`, a `409 conflict` for the loser, and an unconsumed loser token that then succeeds on a second name. The permission suite asserts anonymous and `tenant-admin` denial on `POST /api/v1/signup/invitations` and that a freshly provisioned admin cannot read or write any other tenant. The burst benchmark drives 10,000 attempts from one `/24` in 10 minutes and asserts at most 20 rows and 20 mails per hour with unchanged p95 on authenticated routes; the sweep benchmark proves 100,000 requests processed under 5 minutes with the 7-day scrub and 30-day delete applied exactly once, leaving no orphan in `signup_request_risk_flags` or `signup_request_utm`. The constraint suite proves the normalized shape holds against hostile input: `signup_request_risk_flags` rejects a duplicate `(request_id, flag)` and an off-vocabulary flag, `signup_request_utm` rejects a second row for one request, deleting a request cascades to its token, flag, and utm rows, `signup_requests.tenant_id` refuses a tenant delete while a provisioned request references it, and the `source` and `trial_days` checks reject out-of-range values. The E2E suites walk signup to workspace against the mock bot check and mock mailbox, recover from an expired link, and drive trial expiry, grace, suspension, and conversion, asserting sheets, rows, and files are byte-identical before and after conversion.
- Dependencies: T258 defences and T259 provisioning implemented; `testing/fixtures/signup.rs`; the mock mailbox and `StaticBotCheck` from the F065 harness; Playwright and criterion from the shared testing configuration.
- Feature flag: `F065_FEATURE`; the whole suite is skipped when the flag is off and runs in both targeted and full modes when on.

## TDD

- Failing test first: `testing/features/F065/api/enumeration_tests.rs::four_cases_share_status_body_and_latency_band`, `::availability_answer_identical_for_three_reasons`; `testing/features/F065/api/negative_tests.rs::tampered_token_returns_gone`, `::token_of_another_request_cannot_complete`, `::anonymous_cannot_create_invitation`, `::tenant_admin_cannot_create_invitation`, `::new_admin_cannot_read_other_tenant`; `testing/features/F065/api/race_tests.rs::concurrent_completions_provision_exactly_one_tenant`, `::race_loser_token_survives_and_succeeds_on_new_slug`; `testing/features/F065/database/constraint_tests.rs::duplicate_risk_flag_row_rejected`, `::unknown_risk_flag_rejected`, `::second_utm_row_for_request_rejected`, `::request_delete_cascades_to_token_flag_and_utm_rows`, `::provisioned_request_blocks_tenant_delete`, `::invalid_source_and_trial_days_rejected`; `testing/features/F065/performance/signup_bench.rs::burst_from_one_network_is_contained`; `testing/features/F065/performance/sweep_bench.rs::sweep_100k_requests_under_five_minutes`
- Targeted command: `cargo xtask test-feature F065`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/signup.rs` seeding exclusively through the F065 repositories, with the seeded tenant `acme`, an existing active user, a platform operator, live, expired, and consumed requests, a day-13 trial tenant with data, per-test IP range and rate-limit prefix, fixed clock, token, and pepper

## Exit criteria

- [ ] Tests written before implementation and observed failing, then green against T258 and T259
- [ ] Positive control recorded: removing the constant-time floor turns the enumeration suite red, restoring it turns it green
- [ ] Evidence for every lane collected under `testing/evidence/F065/`
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S130
- [ ] `finished_at` recorded
