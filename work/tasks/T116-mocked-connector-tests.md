---
id: T116
type: task
status: planned
parent_epic: E006
parent_feature: F029
parent_story: S058
depends_on: [T115]
owned_paths: [testing/features/F029/**]
feature_flag: F029_FEATURE
branch: t116-mocked-connector-tests
started_at: null
finished_at: null
---

# T116 — Mocked connector tests

## Identity

- Parent story: `S058` Notifications/sync
- Owner: platform
- Branch: `t116-mocked-connector-tests`
- Decision references: `docs/architecture-decisions.md` sections 7, 9; `docs/capability-contracts.md` row F029

## Objective

Complete the F029 harness with recorded-response contract tests for the three providers, permission-negative and tenant-isolation suites, database constraint checks, the end-to-end connect, test, bind, and conflict browser flow, accessibility checks, and the sync and notification performance lanes.

## Specification

- Owned paths: `testing/features/F029/api/{provider_contract_tests.rs, negative_tests.rs}`, `testing/features/F029/database/constraint_tests.rs`, `testing/features/F029/e2e/integrations.spec.ts`, `testing/features/F029/accessibility/integrations.a11y.spec.ts`, `testing/features/F029/performance/{calendar_sync_bench.rs, notify_bench.rs}`, `testing/features/F029/{README.md, requirements/cases.md}`
- Contract/input: recorded provider responses under `testing/features/F029/api/fixtures/{microsoft,google,slack}/` for token exchange, refresh, revoke, userinfo, Graph delta pages, Calendar sync-token pages, `chat.postMessage`, `conversations.replies`, and error bodies; tenants A and B with one connection per provider; 1,000-row generator.
- Output/behavior: contract tests replay recorded responses through the adapters and assert parsed structures and error classes; negatives prove member denial, owner-only `notify-test`, `not_found` for foreign IDs, cross-tenant state rejection, and absence of token material in responses, logs, and audit rows; database tests prove one token row per connection, one active binding per sheet, cascade delete, and `refresh_failures` bounds; the E2E flow connects Slack through the mock consent page, sends a test to `#ops`, connects Google, binds `Launch plan` with `newest_wins`, edits a date on both sides, and sees the conflict entry; accessibility runs axe on integrations routes and dialogs and checks the popup hand-off announcement; performance proves a 1,000-row calendar sync under 5 minutes with mocked `429`s and notification p95 under 3 s.
- Dependencies: T113, T114, T115 implementations; `testing/harness/providers/` mock servers with consent pages; Playwright.
- Feature flag: `F029_FEATURE`

## TDD

- Failing test first: `testing/features/F029/api/provider_contract_tests.rs::microsoft_recorded_responses_parse`, `::google_recorded_responses_parse`, `::slack_recorded_responses_parse`; `testing/features/F029/api/negative_tests.rs::owner_can_test_but_not_revoke`, `::tokens_absent_from_logs_and_audit`, `::foreign_connection_not_found`; `testing/features/F029/database/constraint_tests.rs::one_active_binding_per_sheet`; `testing/features/F029/e2e/integrations.spec.ts::connect_slack_and_send_test`, `::bind_calendar_and_see_conflict`; `testing/features/F029/accessibility/integrations.a11y.spec.ts::integrations_routes_have_no_serious_violations`; `testing/features/F029/performance/calendar_sync_bench.rs::calendar_sync_1000_rows_under_5_minutes`, `testing/features/F029/performance/notify_bench.rs::notification_send_p95_under_3s`
- Targeted command: `cargo xtask test-feature F029`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/integrations.rs`; mock provider port per worker; recorded fixtures versioned with the provider API date

## Exit criteria

- [ ] Tests written before implementation and observed failing where the behavior is not yet present
- [ ] All seven lanes green in targeted and full modes with evidence under `testing/evidence/F029/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S058
- [ ] `finished_at` recorded
