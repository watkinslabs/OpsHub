---
id: T256
type: task
status: planned
parent_epic: E006
parent_feature: F064
parent_story: S128
depends_on: [S128, T254, T255]
owned_paths: [testing/features/F064/**]
feature_flag: F064_FEATURE
branch: t256-billing-negative-tests
started_at: null
finished_at: null
---

# T256 — Billing negative tests

## Identity

- Parent story: `S128` Usage metering and invoicing
- Owner: platform
- Branch: `t256-billing-negative-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 4, 9; `docs/capability-contracts.md` row F064

## Objective

Prove the failure surface of billing: permission denial, tenant isolation, webhook forgery and replay, provider failure mid-change, correction abuse, and the guarantee that no dunning stage removes read or export access without notice.

## Specification

- Owned paths: `testing/features/F064/{requirements,api,database,frontend,e2e,accessibility,performance}/` case files and the negative suites they name, plus `testing/features/F064/{README.md, feature.toml}`
- Contract and input: the six F064 routes, the four events, the mock payment provider controls (bad signature, stale timestamp, duplicate event, unknown customer, proration mismatch, timeout, `429`), tenants A and B, a `billing-admin`, a `tenant-admin` without billing rights, and a member.
- Output and behavior: assert `403 denied` for every non-`billing-admin` actor on all five `/api/v1/billing` routes; assert `404 not_found` for a foreign invoice id and that tenant B usage never appears in a tenant A query; assert `400 invalid` for a body carrying another `tenant_id`; assert a forged or stale-timestamp webhook changes nothing and writes `billing.webhook-rejected`; assert a replayed event answers `duplicate` and publishes no second event; assert a webhook naming an unknown `provider_subscription_id` is stored `ignored` and is never matched to a tenant by guesswork; assert a provider timeout during `change_subscription` leaves the local subscription at its previous `version` with no entitlement projection; assert a proration mismatch returns `502 unavailable` with nothing written; assert an adjustment without a reason or without `corrects_record_id` is rejected and a direct `UPDATE` or `DELETE` on `usage_records` raises; assert overage never returns an error; assert the normalized shape at the database level — `invoice_lines` rejects a duplicate `(invoice_id, line_no)` and disappears with its invoice, `subscription_payment_methods` rejects a second row for one subscription and an `exp_month` of 13, `credit_code_plans` rejects a duplicate `(credit_code_id, plan)` and a plan outside `free|team|enterprise`, a `usage_records.metric` outside the three metered values is rejected, and `billing_webhook_events.payload` is the only `jsonb` column in the module; assert each dunning stage emits an F037 notification naming the next step and its date, that day 7 leaves core sheets editable, that day 14 still permits export, and that no code path in `billing` deletes tenant data.
- Data access: no test opens a connection or issues SQL of its own. Every fixture write and every assertion reads through the `crates/persistence/src/billing/` repositories — `SubscriptionRepository`, `InvoiceRepository`, `UsageRecordRepository`, `WebhookEventRepository`, `CreditCodeRepository`, `CreditLedgerRepository` — except the constraint suite, which deliberately issues raw statements against the migrated schema to prove the database, not the application, rejects them (decision section 2.1).
- Dependencies: T254 and T255 for the routes and jobs under test; the F048 and F037 in-memory doubles; the mock payment provider; the F002 cross-tenant negative suite reused per NFR-F002-02.
- Feature flag: `F064_FEATURE` enabled explicitly by both the targeted and the full command.

## TDD

- Failing test first: `testing/features/F064/api/negative_tests.rs::member_denied_on_every_billing_route`, `::tenant_admin_without_billing_admin_denied`, `::foreign_invoice_returns_not_found`, `::foreign_tenant_id_in_body_invalid`, `::cross_tenant_usage_never_returned`; `testing/features/F064/api/webhook_negative_tests.rs::forged_signature_changes_nothing`, `::stale_timestamp_rejected_and_audited`, `::replayed_event_publishes_no_second_event`, `::unknown_subscription_stored_as_ignored`, `::oversized_body_rejected`; `testing/features/F064/api/failure_tests.rs::provider_timeout_leaves_version_unchanged`, `::proration_mismatch_returns_unavailable_without_write`, `::portal_rate_limited_after_five_sessions`; `testing/features/F064/database/append_only_tests.rs::usage_update_rejected`, `::usage_delete_rejected`, `::adjustment_without_reason_rejected`, `::invoice_line_number_unique_per_invoice`, `::invoice_lines_cascade_with_invoice`, `::one_payment_method_row_per_subscription`, `::payment_method_exp_month_out_of_range_rejected`, `::credit_code_plan_row_unique`, `::credit_code_plan_value_outside_f002_set_rejected`, `::usage_metric_outside_three_values_rejected`, `::webhook_payload_is_only_jsonb_column`; `testing/features/F064/e2e/dunning.spec.ts::dunning_notifies_and_degrades_in_order`, `::suspended_tenant_can_still_export`
- Targeted command: `cargo xtask test-feature F064`
- Full command: `cargo xtask test-all`
- Fixtures and mocks: `testing/fixtures/billing.rs` tenants A and B with the three actor roles; the mock payment provider fault controls; the F037 notifier double asserting one notification per dunning stage; a positive control that removes the webhook unique constraint, observes the replay test go red, restores it, and observes green

## Exit criteria

- [ ] Every negative test written before the behavior it guards and observed failing
- [ ] Positive control recorded for the replay guard and for the append-only rules
- [ ] Permission, isolation, webhook, provider-failure, correction, and dunning suites pass in targeted and full modes
- [ ] Evidence collected under `testing/evidence/F064/`
- [ ] Handoff evidence recorded in S128
- [ ] `finished_at` recorded
