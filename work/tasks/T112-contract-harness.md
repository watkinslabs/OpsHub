---
id: T112
type: task
status: planned
parent_epic: E006
parent_feature: F028
parent_story: S056
depends_on: [T111]
owned_paths: [testing/features/F028/**]
feature_flag: F028_FEATURE
branch: t112-contract-harness
started_at: null
finished_at: null
---

# T112 — Contract harness

## Identity

- Parent story: `S056` Event delivery
- Owner: platform
- Branch: `t112-contract-harness`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 9; `docs/capability-contracts.md` row F028

## Objective

Complete the F028 harness with the OpenAPI contract suite, database constraint checks, the end-to-end developer console flow against the harness receiver, accessibility checks, and the dispatch throughput lane.

## Specification

- Owned paths: `testing/features/F028/api/{contract_tests.rs, negative_tests.rs}`, `testing/features/F028/database/constraint_tests.rs`, `testing/features/F028/e2e/developer.spec.ts`, `testing/features/F028/accessibility/developer.a11y.spec.ts`, `testing/features/F028/performance/{dispatch_bench.rs, openapi_bench.rs}`, `testing/features/F028/{README.md, requirements/cases.md}`
- Contract/input: committed `openapi/v1.json`; tenants A and B with one application and one webhook each; harness receiver with recorded requests; 120 seeded deliveries in mixed states with their attempt rows, seeded through the repositories; fixed signature vector `secret = 0x00..1f`, `timestamp = 1788393600`, body `{"id":"...","event":"row.updated.v1"}`.
- Output/behavior: contract tests validate every `Page<T>` response against the document schema for six representative list routes, every error against `Error`, and reject an undocumented route added to a scratch router; negatives prove `denied` for members, `not_found` for foreign IDs, suspended-token rejection, and payload scope filtering; database tests prove unique names, the idempotent delivery key, the attempt cap, and the normalized child tables; the E2E flow creates an application and webhook, updates a row, sees a `succeeded` delivery with the verified signature on the receiver, switches the receiver to 500, watches the webhook become disabled, re-enables, replays; accessibility runs axe on developer routes and drawers; performance proves 1,000 deliveries per minute with p95 dispatch latency under 5 s and `openapi.json` under 50 ms.
- Data access: `constraint_tests.rs` asserts the normalized shape — `api_application_scopes` rejects a duplicate `(application_id, scope)` and a scope failing the name check, `api_application_allowed_ips` rejects a duplicate CIDR and a twenty-first row, `webhook_events` rejects a duplicate pattern and a fifty-first row, `webhook_filters` rejects `filter_key` outside `workspace_id`/`sheet_id`, `webhook_delivery_attempts` rejects a duplicate `attempt_no` and a sixth attempt, deleting a webhook removes its event, filter, delivery, and attempt rows by cascade, and `webhook_deliveries.payload` is the only remaining `jsonb` column in the module. No test opens a connection or issues SQL of its own: every fixture write and every assertion read goes through the `crates/persistence/src/public-api/` repositories, except the constraint tests above, which deliberately drive the failing statement through the repository and assert the mapped `conflict`/`invalid` error (decision section 2.1).
- Dependencies: T109, T110, T111 implementations; `testing/harness/receiver.rs`; real JetStream from compose.
- Feature flag: `F028_FEATURE`

## TDD

- Failing test first: `testing/features/F028/api/contract_tests.rs::page_responses_match_openapi_schema`, `::error_responses_match_error_schema`, `::undocumented_route_fails_contract_gate`; `testing/features/F028/api/negative_tests.rs::suspended_application_token_rejected`, `::foreign_tenant_webhook_not_found`; `testing/features/F028/database/constraint_tests.rs::delivery_unique_per_webhook_event`, `::attempt_count_capped_at_five`, `::application_scope_row_unique`, `::allowed_ip_rows_capped_at_twenty`, `::webhook_event_pattern_row_unique`, `::webhook_event_rows_capped_at_fifty`, `::webhook_filter_key_check_rejects_unknown`, `::delivery_attempt_row_unique_per_attempt_no`, `::webhook_delete_cascades_children`; `testing/features/F028/e2e/developer.spec.ts::create_app_webhook_receive_signed_delivery`, `::failures_disable_then_reenable_and_replay`; `testing/features/F028/accessibility/developer.a11y.spec.ts::developer_routes_have_no_serious_violations`; `testing/features/F028/performance/dispatch_bench.rs::dispatch_1000_per_minute_p95`
- Targeted command: `cargo xtask test-feature F028`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/public_api.rs`; receiver port per worker; Playwright reads the receiver log through a harness endpoint

## Exit criteria

- [ ] Tests written before implementation and observed failing where the behavior is not yet present
- [ ] All seven lanes green in targeted and full modes with evidence under `testing/evidence/F028/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S056
- [ ] `finished_at` recorded
