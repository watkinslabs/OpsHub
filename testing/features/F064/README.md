# F064 — Billing and subscriptions harness

Feature-gated tests for `F064`. Keep test code in this directory.

- Gate: `F064_FEATURE`
- Targeted: `cargo xtask test-feature F064`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/billing.rs` (tenants A and B; a `billing-admin`, a `tenant-admin` holding no billing role, and a member; one subscription per status `trialing`, `active`, `past_due`, `restricted`, `suspended`, `canceled`; a `manual` F048 entitlement on `bridge` for the override case; 18 months of daily `seats` and `storage_gb` samples plus hourly `automation_runs` deltas with one corrected day; 24 invoices; fixed clock `2026-09-03T00:00:00Z`, UTC, period `2026-09-01`–`2026-10-01`, prices `team 2900` and `enterprise 9900` cents).
- Payment provider: never contacted. `testing/harness/providers/billing/` implements the seven `PaymentProvider` operations, signs webhooks with the fixture secret pair, and can be told to return a proration mismatch, a timeout, a `429`, a duplicate event, an unknown customer, a forged signature, or a stale timestamp. No live key exists in any fixture and no test opens a connection to a real provider.
- Doubles: the F048 entitlement service and the F037 notifier are in-memory and record every call, so tests assert that F064 writes only `source: plan` entitlements and notifies once per dunning stage.
- Lanes: `requirements/` (traceability for every FR and NFR), `api/`, `database/` (append-only rules and the replay guard proven at the database level), `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names in that lane and the requirement IDs they prove.
