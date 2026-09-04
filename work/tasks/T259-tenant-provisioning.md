---
id: T259
type: task
status: planned
parent_epic: E006
parent_feature: F065
parent_story: S130
depends_on: [S130, T257]
owned_paths: [crates/domain/src/signup/**, crates/persistence/src/signup/**, services/api/src/signup/**, services/worker/src/signup/**, apps/web/src/features/signup/**, testing/features/F065/api/**, testing/features/F065/e2e/**, testing/features/F065/performance/**]
feature_flag: F065_FEATURE
branch: t259-tenant-provisioning
started_at: null
finished_at: null
---

# T259 — Tenant provisioning

## Identity

- Parent story: `S130` trial provisioning and conversion
- Owner: platform
- Branch: `t259-tenant-provisioning`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 7; `docs/capability-contracts.md` row F065

## Objective

Implement `POST /public/signup/{token}/complete` and the trial lifecycle: one transaction that consumes the token and provisions through the F002 `create_tenant` use case, the trial entitlement grant, the F064 trial subscription, the first session, and the worker jobs that warn, suspend, convert, and sweep.

## Specification

- Owned paths: `crates/domain/src/signup/{provisioning.rs, trial.rs, ports.rs}`, `services/api/src/signup/handlers_complete.rs`, the completion and sweep call sites against `crates/persistence/src/signup/{request_repository.rs, token_repository.rs}` (created and owned by T257; this task adds no second writer of those tables), `services/worker/src/signup/{mod.rs, sweep.rs, trial_lifecycle.rs, subscription_consumer.rs}`, `apps/web/src/features/signup/{CompleteSignupPage.tsx, TrialBadge.tsx, TrialBanner.tsx}`
- Contract/input: `CompleteSignupRequest { slug, admin_display_name, timezone, accepted_terms_version }`; ports `TenantProvisioner::create_tenant(CreateTenantCommand)`, `SessionIssuer::issue(tenant_id, user_id, AuthKind::Signup)`, `EntitlementWriter::upsert(tenant_id, module, state, trial_ends_at)`, `SubscriptionStarter::start_trial(tenant_id, trial_days)`; constants in `TrialPolicy { days: 14, grace_days: 7, user_cap: 10, storage_cap_gb: 5, modules: ["dynamic-views","workapps","calendar-app","pivots"] }`.
- Output/behavior: completion runs one `UnitOfWork` transaction that consumes the token through `SignupTokenRepository::consume` (setting `signup_tokens.consumed_at`), calls `create_tenant` under a short-lived system `platform-operator` `ActorContext` with `{ name: company_name, slug, plan: "free", region: "us-east", admin_email, admin_display_name }` so F002 writes `tenants` and `users` and the F003 seed hook writes the `tenant-admin` binding, upserts the four trial entitlements with `trial_ends_at`, starts the F064 subscription in `status: trialing`, publishes `tenant.provisioned.v1`, mints the `__Host-oh_session` cookie, and returns `200 { tenant_id, slug, workspace_url, trial_ends_at }`. `SlugTaken` from F002 returns `409 conflict` with `field_errors.slug = "taken"` and leaves the token unconsumed; a replay after success returns `410 gone` with `reason: consumed`; any failure rolls back all steps together. `trial_lifecycle` runs hourly, enters grace at `trial_ends_at`, notifies the admin on grace days 0, 3, and 6 through F037, and at grace end calls the F002 suspend route, writing the `signup.trial-expired` and `signup.trial-suspended` audit events. `subscription_consumer` handles `subscription.updated.v1` with `status: active` by moving the four entitlements to `active`, clearing `trial_ends_at`, lifting a grace suspension, and writing `signup.converted`. `sweep` runs nightly in 1,000-row batches, one `UnitOfWork` per batch: abandon past `expires_at` with `signup.abandoned.v1`, scrub `email`, `email_normalized`, `company_name`, `ip`, and `user_agent` at 7 days while leaving the request's `signup_request_risk_flags` and `signup_request_utm` rows, delete the request at 30 days so `signup_tokens`, `signup_request_risk_flags`, and `signup_request_utm` cascade with it, and register the kind `signup_requests` with the F027 retention registry as non-tenant-configurable.
- Data access: `provisioning.rs`, `trial.rs`, `handlers_complete.rs`, `sweep.rs`, `trial_lifecycle.rs`, `subscription_consumer.rs`, and the E2E and benchmark fixtures contain no SQL, no connection, and no `sqlx::query*` call. They use `SignupTokenRepository::{find_live_by_token_hash, consume}`, `SignupRequestRepository::{mark_provisioned, find_by_tenant_id, list_pending_past_expiry, mark_abandoned_batch, scrub_personal_data_batch, delete_requests_created_before}`, and `ReservedSlugRepository::release_expired_pins` from T257, and completion enlists those repositories together with the F002 tenant repositories, the F048 entitlement writer, the F064 subscription starter, and the outbox in one `UnitOfWork`, which is what makes the all-or-nothing rollback below a transaction property rather than handler cleanup code (decision section 2.1).
- Dependencies: T257 schema, repositories, and routes; F002 `create_tenant` and suspend; F003 seed hook and audit writer; F038 `SessionIssuer`; F048 entitlement upsert; F064 subscription start and `subscription.updated.v1`; F037 notifications; F027 retention registry; F004 worker registry and outbox.
- Feature flag: `F065_FEATURE` gates the completion route and both scheduled jobs; the `subscription.updated.v1` consumer is registered only when the flag is on so a disabled deployment cannot flip entitlements.

## TDD

- Failing test first: `testing/features/F065/api/provisioning_tests.rs::complete_provisions_through_f002_use_case`, `::signup_module_never_writes_tenants_directly`, `::first_user_gets_tenant_admin_from_seed_hook`, `::trial_grants_four_modules_for_fourteen_days`, `::other_six_modules_stay_none`, `::slug_taken_at_completion_keeps_token_unconsumed`, `::replayed_completion_returns_gone_consumed`, `::failed_subscription_start_rolls_back_tenant`, `::completion_sets_session_cookie_with_signup_auth_kind`; `testing/features/F065/api/lifecycle_tests.rs::grace_marks_trial_modules_expired_but_sheets_writable`, `::grace_reminders_sent_on_days_zero_three_six`, `::grace_end_suspends_tenant_without_data_loss`, `::conversion_activates_entitlements_and_lifts_suspension`, `::sweep_scrubs_pii_at_seven_days_and_keeps_flag_rows`, `::sweep_deletes_request_and_child_rows_at_thirty_days`
- Targeted command: `cargo xtask test-feature F065`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/signup.rs` provisioner spy that fails on any direct tenant write, `SessionIssuer` stub, F048 and F064 write spies, a trial tenant seeded at day 13 with sheets, rows, and files, and a 100,000-request generator spread over 60 days for the sweep benchmark

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Provisioning proven transactional: a forced failure in each step leaves no tenant, entitlement, subscription, or consumed token
- [ ] Jobs and the consumer registered in `services/worker/src/registry.rs` behind the flag; owned-path and `cargo xtask check-persistence` checks pass
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S130
- [ ] `finished_at` recorded
