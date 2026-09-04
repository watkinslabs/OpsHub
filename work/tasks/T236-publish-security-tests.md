---
id: T236
type: task
status: planned
parent_epic: E008
parent_feature: F059
parent_story: S118
depends_on: [T235]
owned_paths: [testing/features/F059/e2e/**, testing/features/F059/accessibility/**, testing/features/F059/performance/**, testing/features/F059/api/**]
feature_flag: F059_FEATURE
branch: t236-publish-security-tests
started_at: null
finished_at: null
---

# T236 — Publish security tests

## Identity

- Parent story: `S118` Embeds/access
- Owner: platform
- Branch: `t236-publish-security-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 4, 9; `docs/capability-contracts.md` row F059

## Objective

Prove that publication tokens cannot leak data, escalate to the API, or survive revocation, and that public and embed pages meet accessibility and performance budgets.

## Specification

- Owned paths: `testing/features/F059/api/security_tests.rs`, `testing/features/F059/e2e/publishing.spec.ts`, `testing/features/F059/e2e/embed-host.spec.ts`, `testing/features/F059/accessibility/publishing.a11y.spec.ts`, `testing/features/F059/performance/publish_bench.rs`
- Contract/input: security suite enumerates every `/api/v1` route from the OpenAPI document and presents a publication token as bearer, query, and cookie; leak suite diffs the public payload against the publisher's full view; Playwright serves `https://host.test` with an iframe pointing at `/embed/{token}` and a second host `https://evil.test`.
- Output/behavior: every API route rejects the token with `403 denied`; payload contains no hidden column, comment, attachment, tenant ID, or app link; revocation and expiry make public and embed routes return `404` within 5 s; rotation keeps the old token working for 10 minutes then `404`; `https://evil.test` embed shows the denied state; E2E covers publish → logged-out view → embed on allowed host → rotate → revoke; axe reports zero serious violations on public, embed, and dialog; performance lane records render p95 (< 500 ms for 12 widgets), refresh of a 10,000-row view (< 10 s), and rate-limit enforcement at 61 requests.
- Data access: every fixture and assertion in this lane goes through `crates/persistence/src/publishing/` — publications, origin rows, snapshot sources, tokens, and view rows are created with `PublicationRepository`, `PublicationTokenRepository`, and `PublicationViewRepository`, and read back with `list_allowed_origins`, `list_snapshot_sources`, `find_by_token_hash`, and `count_views_since`; no test opens a pool, issues `sqlx::query`, or asserts against raw SQL. `security_tests.rs` adds the database constraint cases for the new child tables — a duplicate `publication_allowed_origins` origin, an origin failing the `https` check, a duplicate `publication_snapshot_sources` source, cascade deletion of both children with the publication, and a `read_only = false` token — asserting the repository surfaces the constraint violation as a typed error rather than a panic; the migration-level versions of the same constraints live in T233's `testing/features/F059/database/migration_tests.rs` (decision section 2.1).
- Dependencies: T235 complete; OpenAPI document from F028 `GET /api/v1/openapi.json`; Playwright multi-origin harness from `testing/harness/`.
- Feature flag: `F059_FEATURE`

## TDD

- Failing test first: `testing/features/F059/api/security_tests.rs::token_rejected_on_every_api_route`, `::public_payload_has_no_hidden_or_tenant_data`, `::revoked_and_expired_tokens_404_within_5s`, `::rotated_token_grace_window`, `::duplicate_allowed_origin_row_rejected`, `::non_https_origin_row_rejected`, `::duplicate_snapshot_source_row_rejected`, `::child_rows_cascade_with_publication`, `::token_read_only_false_rejected`; `testing/features/F059/e2e/publishing.spec.ts::publish_view_logged_out_rotate_revoke`, `::tenant_access_requires_login`; `testing/features/F059/e2e/embed-host.spec.ts::embed_on_allowed_host_renders_and_resizes`, `::embed_on_unlisted_host_denied`; `testing/features/F059/accessibility/publishing.a11y.spec.ts::public_embed_dialog_have_no_serious_axe_violations`; `testing/features/F059/performance/publish_bench.rs::render_dashboard_12_widgets_p95`, `::refresh_10k_row_view_under_10s`, `::rate_limit_enforced_at_61`
- Targeted command: `cargo xtask test-feature F059`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: OpenAPI route enumerator; second and third origins in Playwright; fixed clock for expiry and grace; 10,000-row view fixture

## Exit criteria

- [ ] Security, E2E, accessibility, and performance lanes pass in targeted and full modes
- [ ] p95 targets from NFR-F059-01 recorded under `testing/evidence/F059/performance/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S118
- [ ] `finished_at` recorded
