# F065 — Self-serve signup and trials harness

Feature-gated tests for `F065`, the only unauthenticated write path in OpsHub. Keep test code in this directory.

- Gate: `F065_FEATURE`
- Targeted: `cargo xtask test-feature F065`
- Full: `cargo xtask test-all`
- Fixtures: `testing/fixtures/signup.rs` (empty platform with the 240 seeded `reserved_slugs`, an existing tenant `acme` with an active user, a platform operator, a pending request with a live token, an expired request, a consumed request, a day-13 trial tenant carrying sheets, rows, and files, and a generator for 100,000 requests spread over 60 days).
- Stubs: `StaticBotCheck` with a programmable Turnstile verdict map, `StaticMxResolver` with a domain-to-verdict map, an in-memory `NotificationSender` recording category, `dedupe_key`, and the rendered link, a `SessionIssuer` stub, F048 and F064 write spies, and a `TenantProvisioner` spy that fails the suite if any signup code path writes `tenants`, `users`, or `role_bindings` directly instead of calling the F002 `create_tenant` use case.
- Determinism: fixed clock `2026-09-03T00:00:00Z`, UTC, fixed UUIDv7 seeds, fixed 32-byte token value, fixed email pepper, per-test IP range, and a per-test rate-limit key prefix so buckets never leak across workers.
- Two gates are specific to this feature: the enumeration suite compares status, headers, body bytes, and latency band across four signup cases, and the provisioner spy proves tenant creation is never duplicated.
- Lanes: `requirements/` (traceability), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/`, `performance/`; each `cases.md` lists the test names implemented in that lane and the FR/NFR IDs they prove.
