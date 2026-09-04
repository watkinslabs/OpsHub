---
id: S127
type: story
status: planned
parent_epic: E006
parent_feature: F064
depends_on: [F002, F048]
owned_paths: [crates/domain/src/billing/**, services/api/src/billing/**, services/worker/src/billing/**, apps/web/src/features/billing/**, services/api/migrations/*_billing_*.sql, testing/features/F064/**]
feature_flag: F064_FEATURE
branch: s127-subscription-and-plan-lifecycle
started_at: null
finished_at: null
---

# S127 — Subscription and plan lifecycle

## Identity

- Parent feature: `F064` Billing and subscriptions
- Owner: platform
- Branch: `s127-subscription-and-plan-lifecycle`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7; `docs/capability-contracts.md` row F064

## Vertical slice

As a billing administrator, I want one subscription record per tenant that I can read, change with a proration preview I see before I confirm, schedule down at the period end, cancel with grace to the period end, and have every change flow automatically into the F048 entitlements my team already relies on, so that packaging stops being an operator edit and a lapsed payment degrades my tenant in a predictable, notified order.

## Requirements

- **SR-S127-01:** `GET /api/v1/billing/subscription` returns the `subscription` aggregate with plan, status, period bounds, trial and schedule fields, dunning state, seats, allowances, and payment-method summary, and synthesizes a free `version: 0` response for a tenant with no `subscriptions` row (covers FR-F064-01).
- **SR-S127-02:** `PUT /api/v1/billing/subscription` validates `plan` against the F002 `free|team|enterprise` set, requires `If-Match` and `Idempotency-Key`, returns a write-free `ProrationPreview` under `preview: true`, applies upgrades immediately with provider proration, and rejects a preview that disagrees with the provider line items (FR-F064-02, FR-F064-03).
- **SR-S127-03:** Downgrades store `scheduled_plan` and `scheduled_effective_at` and are applied by `billing.apply_scheduled` within 5 minutes of the period end, with `apply: "immediate"` issuing a credit note instead of a refund (FR-F064-04).
- **SR-S127-04:** The `plan_entitlements` projector upserts F048 records with `source: "plan"` for the plan's module list and limits, skips any module whose stored `source` is `manual`, and F064 keeps no entitlement table and makes no gating decision (FR-F064-05).
- **SR-S127-05:** All provider access goes through the `PaymentProvider` port with the single `StripeAdapter` behind it; no provider type crosses into the domain, service, API, or worker code, and `POST /api/v1/billing/portal-session` returns a 15-minute hosted URL that is never logged or stored, rate-limited to 5 per tenant per hour (FR-F064-06, FR-F064-07).
- **SR-S127-06:** `POST /webhooks/billing/{provider}` verifies the HMAC-SHA256 signature and 300-second timestamp window, inserts `billing_webhook_events` and applies the effect in one transaction so a redelivery answers `duplicate` and applies nothing, and reconciles `subscription.updated` with provider state winning (FR-F064-08, FR-F064-09, FR-F064-10).
- **SR-S127-07:** The dunning ladder advances day 0 `past_due`, day 7 `restricted` suspending only plan-sourced entitlements, day 14 `suspended` read-only with export preserved, day 30 `canceled` to the free plan, notifying at every stage with the next step and its date and never deleting data or removing read access without notice (FR-F064-13).
- **SR-S127-08:** Trial expiry notifies at 7, 3, and 1 days, converts to `active` with a payment method and falls back to `free` without one, and never enters dunning; `cancel_at_period_end` preserves full access to `current_period_end` and then moves the tenant to `free` (FR-F064-14).
- **SR-S127-09:** Every billing route requires `billing-admin`, mutations write audit rows and publish `subscription.updated.v1`, a body carrying another `tenant_id` returns `400 invalid`, and cross-tenant ids return `not_found` (FR-F064-15, NFR-F064-02).
- **SR-S127-10:** `/admin/billing` renders the plan card, the plan-change dialog with the announced proration table, the cancel dialog, and the dunning banner stating stage, consequence, and next date, all keyboard reachable and free of serious axe violations (NFR-F064-03).

## Surfaces

- Infrastructure and container: provider credentials and signing secrets from the F004 secret manager under `billing/<provider>/api_key` and `billing/<provider>/signing_secret` with a two-secret rotation window; the webhook route mounted outside the session-auth layer
- Rust service and API: `crates/domain/src/billing/{mod.rs, plan.rs, subscription.rs, provider.rs, proration.rs, dunning.rs, webhook.rs, entitlements_projection.rs, errors.rs, service.rs, lifecycle.rs, adapters/{mod.rs, stripe.rs}}`; `services/api/src/billing/{mod.rs, routes.rs, handlers_subscription.rs, handlers_portal.rs, handlers_webhook.rs, dto.rs}`; `services/worker/src/billing/{mod.rs, dunning.rs, scheduled.rs, trial.rs, webhook_retry.rs}`
- Data and migration: `services/api/migrations/<ts>_billing_create_tables.sql` creating `subscriptions`, `invoices`, `usage_records`, and `billing_webhook_events` with the constraints and indexes in ticket section 4
- React and UI: `apps/web/src/features/billing/{BillingPage.tsx, PlanCard.tsx, PlanChangeDialog.tsx, ProrationPreviewTable.tsx, CancelDialog.tsx, DunningBanner.tsx, EntitlementSummary.tsx, PortalButton.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks and fixtures: `testing/fixtures/billing.rs`; the mock payment provider in `testing/harness/providers/billing/` with signing, portal, proration, timeout, and duplicate-event controls; in-memory F048 entitlement service and F037 notifier doubles

## TDD harness

- Test path: `testing/features/F064/{api,database,frontend}/`
- Feature flag: `F064_FEATURE`
- Targeted command: `cargo xtask test-feature F064`
- Full command: `cargo xtask test-all`
- First failing tests: `free_tenant_returns_synthetic_subscription`, `preview_matches_provider_line_items`, `upgrade_projects_plan_entitlements_with_source_plan`, `manual_entitlement_survives_plan_change`, `downgrade_schedules_for_period_end`, `webhook_replay_returns_duplicate_and_applies_nothing`, `webhook_bad_signature_rejected_without_state_change`, `dunning_day_seven_restricts_only_plan_entitlements`, `trial_expiry_without_payment_method_falls_back_to_free`, `tenant_admin_without_billing_admin_denied`

## Exit criteria

- [ ] Requirement tests SR-S127-01 through SR-S127-10 written first and observed failing
- [ ] Tasks T253 and T254 complete and wired through `services/api` router and `services/worker` registry
- [ ] Unit, API, database, React, accessibility, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/billing/routes.rs` mounted in `services/api/src/router.rs` at `/api/v1/billing` and `/webhooks/billing`; `services/worker/src/billing/{dunning.rs, scheduled.rs, trial.rs, webhook_retry.rs}` registered in `services/worker/src/registry.rs`
- [ ] A grep gate proves no provider type name appears outside `crates/domain/src/billing/adapters/stripe.rs`
- [ ] Handoff evidence recorded in the F064 ticket
