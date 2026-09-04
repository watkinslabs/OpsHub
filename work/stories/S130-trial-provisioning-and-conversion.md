---
id: S130
type: story
status: planned
parent_epic: E006
parent_feature: F065
depends_on: [F002, F038, F064]
owned_paths: [crates/domain/src/signup/**, crates/persistence/src/signup/**, services/api/src/signup/**, services/worker/src/signup/**, apps/web/src/features/signup/**, testing/features/F065/**]
feature_flag: F065_FEATURE
branch: s130-trial-provisioning-and-conversion
started_at: null
finished_at: null
---

# S130 — Trial provisioning and conversion

## Identity

- Parent feature: `F065` Self-serve signup and trials
- Owner: platform
- Branch: `s130-trial-provisioning-and-conversion`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7; `docs/capability-contracts.md` row F065

## Vertical slice

As a verified prospect, I want completing the signup link to give me a real tenant that I administer, with a trial that has a stated length, a stated set of modules, a warned expiry, and a conversion path that keeps everything I built, so that evaluating OpsHub is never a throwaway sandbox and never a second, weaker way of creating a tenant.

## Requirements

- **SR-S130-01:** `POST /public/signup/{token}/complete` provisions in one `UnitOfWork` transaction: consume the token through `SignupTokenRepository::consume`, call the F002 `create_tenant` use case under a short-lived system `platform-operator` context with `plan: "free"` and `region: "us-east"`, write the trial entitlements, start the F064 subscription in `status: trialing`, publish `tenant.provisioned.v1`, and mint the first session through the F038 `SessionIssuer` with `auth_kind = signup` (covers FR-F065-10).
- **SR-S130-02:** No code path in this module writes `tenants`, `users`, `groups`, or `role_bindings`; the first user's `tenant-admin` binding comes from the F003 seed hook that F002 already calls, and the fixture provisioner spy fails the suite if any direct write is attempted (FR-F065-10, NFR-F065-02).
- **SR-S130-03:** A trial lasts 14 days, caps 10 active users and 5 GB of files, and sets F048 entitlements `state: trial` with `trial_ends_at` for `dynamic-views`, `workapps`, `calendar-app`, and `pivots` while the other six modules stay `state: none`; trial status lives in the subscription and entitlements, never in a second plan column on `tenants` (FR-F065-11).
- **SR-S130-04:** The hourly `signup.trial_lifecycle` job opens a 7-day grace at `trial_ends_at` in which the four trial modules evaluate `trial_expired` and core sheets stay writable, notifies the admin on grace days 0, 3, and 6 through F037, and at grace end calls the F002 suspend route so writes return `403 denied` with `reason = tenant_suspended` while all data and the export path survive (FR-F065-12).
- **SR-S130-05:** The `subscription.updated.v1` consumer flips the four entitlements from `trial` to `active`, clears `trial_ends_at`, lifts a grace suspension, and writes the `signup.converted` audit event; conversion recreates, copies, or migrates nothing, and a tenant converting on the last grace day keeps every row, file, and user (FR-F065-13).
- **SR-S130-06:** The nightly `signup.sweep` job abandons pending requests past `expires_at` with `signup.abandoned.v1`, scrubs `email`, `email_normalized`, `company_name`, `ip`, and `user_agent` at 7 days leaving `email_hash`, `status`, `tenant_id`, and the request's `signup_request_risk_flags` and `signup_request_utm` rows, and at 30 days deletes the row so `signup_tokens`, `signup_request_risk_flags`, and `signup_request_utm` cascade with it, every step through `SignupRequestRepository::{list_pending_past_expiry, mark_abandoned_batch, scrub_personal_data_batch, delete_requests_created_before}`, registered with the F027 retention registry as the non-tenant-configurable kind `signup_requests` (FR-F065-14).
- **SR-S130-07:** Provisioning is idempotent per token: a replayed completion after success returns `410 gone` with `reason: consumed` and never creates a second tenant, and because every write in the step list is issued by a repository enlisted in the one `UnitOfWork`, a failure in any step rolls back the tenant, the entitlements, the subscription, the `signup_requests` status change, and the token consumption together (NFR-F065-04, FR-F065-08).
- **SR-S130-08:** The completion page and the in-app trial surfaces render the remaining days from the F048 evaluate response, show a dismissible upgrade banner from day 11, an undismissible banner naming the suspension date during grace, and the F002 suspended notice with a live `Choose a plan` action afterwards (FR-F065-16, NFR-F065-03).

## Surfaces

- Infrastructure/container: JetStream consumer registration for `subscription.updated.v1` and the two scheduled jobs in the F004 worker registry; the trial window constants published as `TrialPolicy` so the UI and the jobs read one source
- Data access: `crates/persistence/src/signup/{request_repository.rs, token_repository.rs, reserved_slug_repository.rs}` created in S129 serve this slice unchanged — completion uses `SignupTokenRepository::{find_live_by_token_hash, consume}` and `SignupRequestRepository::mark_provisioned`, the lifecycle job uses `SignupRequestRepository::find_by_tenant_id`, and the sweep uses its four batch queries; `provisioning.rs`, `trial.rs`, the `services/worker/src/signup/` jobs and consumer, and the E2E and performance fixtures hold no SQL and no connection, and completion enlists these repositories plus the F002, F048, and F064 writers in one `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/signup/{provisioning.rs, trial.rs, ports.rs}` defining `TenantProvisioner`, `SessionIssuer`, `EntitlementWriter`, `SubscriptionStarter`, and `TrialPolicy`; `services/api/src/signup/handlers_complete.rs`
- Data/migration: no new tables; reads and updates `signup_requests` (`status`, `tenant_id`, `provisioned_at`, `scrubbed_at`), `signup_tokens.consumed_at`, and the `signup_request_risk_flags` and `signup_request_utm` children created by T257 in `services/api/migrations/*_signup_*.sql`
- React/UI: `apps/web/src/features/signup/{CompleteSignupPage.tsx, TrialBadge.tsx, TrialBanner.tsx}`
- Mocks/fixtures: `testing/fixtures/signup.rs` seeding through the S129 repositories only, a provisioner spy asserting F002 is the only tenant writer, `SessionIssuer` stub, F048 and F064 write spies, a provisioned trial tenant seeded at day 13, and a 100,000-request sweep generator

## TDD harness

- Test path: `testing/features/F065/{api,e2e,performance,frontend}/`
- Feature flag: `F065_FEATURE`
- Targeted command: `cargo xtask test-feature F065`
- Full command: `cargo xtask test-all`
- First failing tests: `complete_provisions_through_f002_use_case`, `first_user_gets_tenant_admin_from_seed_hook`, `trial_grants_four_modules_for_fourteen_days`, `replayed_completion_returns_gone_consumed`, `grace_end_suspends_tenant_without_data_loss`, `conversion_activates_entitlements_and_lifts_suspension`, `sweep_scrubs_pii_at_seven_days_and_keeps_flag_rows`, `sweep_deletes_request_and_child_rows_at_thirty_days`

## Exit criteria

- [ ] Requirement tests SR-S130-01 through SR-S130-08 written first and failing
- [ ] Tasks T259 and T260 complete and wired through the API router and worker registry
- [ ] Unit, API, E2E, performance, and negative tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/signup/handlers_complete.rs` mounted through `services/api/src/signup/routes.rs`; `services/worker/src/signup/{sweep.rs, trial_lifecycle.rs, subscription_consumer.rs}` registered in `services/worker/src/registry.rs`
- [ ] The provisioner spy proves `tenants`, `users`, and `role_bindings` are written only through the F002 use case
- [ ] Harness evidence for the trial lifecycle recorded under `testing/features/F065/e2e/`
- [ ] Handoff evidence recorded in the F065 ticket
