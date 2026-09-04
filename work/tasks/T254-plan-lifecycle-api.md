---
id: T254
type: task
status: planned
parent_epic: E006
parent_feature: F064
parent_story: S127
depends_on: [S127, T253]
owned_paths: [crates/domain/src/billing/**, services/api/src/billing/**, services/worker/src/billing/**, apps/web/src/features/billing/**, testing/features/F064/api/**, testing/features/F064/frontend/**, testing/features/F064/e2e/**]
feature_flag: F064_FEATURE
branch: t254-plan-lifecycle-api
started_at: null
finished_at: null
---

# T254 — Plan lifecycle API

## Identity

- Parent story: `S127` Subscription and plan lifecycle
- Owner: platform
- Branch: `t254-plan-lifecycle-api`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 7; `docs/capability-contracts.md` row F064

## Objective

Implement the subscription read and change routes, the portal session route, the signed webhook route with transactional replay protection, the entitlement projection into F048, the dunning, scheduled-change and trial jobs, and the `/admin/billing` plan surface.

## Specification

- Owned paths: `services/api/src/billing/{mod.rs, routes.rs, handlers_subscription.rs, handlers_portal.rs, handlers_webhook.rs, dto.rs}`; `services/worker/src/billing/{mod.rs, dunning.rs, scheduled.rs, trial.rs, webhook_retry.rs}`; `crates/domain/src/billing/{service.rs, lifecycle.rs, dunning.rs, entitlements_projection.rs}` added beside the T253 modules without editing them; `apps/web/src/features/billing/{BillingPage.tsx, PlanCard.tsx, PlanChangeDialog.tsx, ProrationPreviewTable.tsx, CancelDialog.tsx, DunningBanner.tsx, EntitlementSummary.tsx, PortalButton.tsx, api.ts, hooks.ts, routes.ts}`
- Contract and input: `ChangeSubscriptionRequest { plan, apply, cancel_at_period_end?, preview? }` with `If-Match` and `Idempotency-Key`; webhook body up to 512 KB with a `t=<unix>` signature header; portal request with no body; the F048 service call `upsert_entitlement(module, state, limits, source: Plan)`.
- Output and behavior: routes `GET /api/v1/billing/subscription`, `PUT /api/v1/billing/subscription`, `POST /api/v1/billing/portal-session`, `POST /webhooks/billing/{provider}`; a missing subscription row is answered as the synthetic free subscription at `version: 0`; upgrades apply immediately after the local proration matches the provider line items to the cent, downgrades store `scheduled_plan` and `scheduled_effective_at` and are applied by `scheduled.rs` within 5 minutes of the period end; the webhook handler inserts `billing_webhook_events` and applies the effect in one transaction so a redelivery answers `200 {"status":"duplicate"}`, an unhandled type stores `ignored`, and an unknown customer stores `ignored`; `entitlements_projection.rs` writes plan-derived F048 records and never touches a row whose `source` is `manual`; `dunning.rs` advances day 0, 7, 14, and 30 with an F037 notification at each stage naming the next step and its date, restricting only plan-sourced entitlements at day 7 and leaving export available at day 14; `trial.rs` notifies at 7, 3, and 1 days and converts or falls back to `free`; events `subscription.updated.v1`, `invoice.payment-failed.v1`; portal URLs are excluded from logs; every route requires `billing-admin` except the signature-authenticated webhook.
- Dependencies: T253 for the schema, port, proration, and signature verification; F048 for the entitlement service and module limit schemas; F037 for notifications; F004 for the outbox, scheduler, and realtime invalidation; F003 for `billing-admin` and audit rows.
- Feature flag: `F064_FEATURE` gates the router mount, the worker jobs, and the `/admin/billing` route.

## TDD

- Failing test first: `testing/features/F064/api/subscription_tests.rs::free_tenant_returns_synthetic_subscription`, `::preview_writes_nothing`, `::upgrade_projects_plan_entitlements_with_source_plan`, `::manual_entitlement_survives_plan_change`, `::downgrade_schedules_for_period_end`, `::immediate_downgrade_issues_credit_note`, `::enterprise_without_payment_method_conflicts`, `::stale_if_match_conflicts`; `testing/features/F064/api/webhook_tests.rs::webhook_replay_returns_duplicate_and_applies_nothing`, `::webhook_bad_signature_rejected_without_state_change`, `::unknown_provider_returns_not_found`, `::unhandled_type_stored_as_ignored`; `testing/features/F064/api/dunning_tests.rs::dunning_day_seven_restricts_only_plan_entitlements`, `::dunning_day_fourteen_keeps_export_available`, `::late_payment_clears_dunning_and_restores_entitlements`, `::trial_expiry_without_payment_method_falls_back_to_free`; `testing/features/F064/api/negative_tests.rs::tenant_admin_without_billing_admin_denied`; `testing/features/F064/frontend/PlanChangeDialog.test.tsx::announces_preview_before_confirm`; `testing/features/F064/e2e/billing.spec.ts::upgrade_with_preview_unlocks_modules`
- Targeted command: `cargo xtask test-feature F064`
- Full command: `cargo xtask test-all`
- Fixtures and mocks: `testing/fixtures/billing.rs` with one subscription per status and a `manual` `bridge` entitlement; the mock payment provider with proration mismatch, timeout, `429`, and duplicate-event controls; in-memory F048 and F037 doubles that record calls; fixed clock and period bounds

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Routes mounted in `services/api/src/router.rs` at `/api/v1/billing` and `/webhooks/billing`, jobs registered in `services/worker/src/registry.rs`, OpenAPI regenerated without drift
- [ ] Projection verified to write only `source: plan` records and to leave `manual` rows untouched
- [ ] Owned-path check passes
- [ ] File limit, lint, and axe gates pass for `/admin/billing`
- [ ] Handoff evidence recorded in S127
- [ ] `finished_at` recorded
