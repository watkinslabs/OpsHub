# F026 performance cases

File: `testing/features/F026/performance/{acs_bench.rs,scim_bench.rs}`. Runs against seeded tenant with fixed keys and clock. Flag `F026_FEATURE`.

- `acs_login_p95` — NFR-F026-01: 200 sequential ACS posts with RSA-SHA256 assertions; p95 < 800 ms including session creation.
- `scim_user_patch_p95` — NFR-F026-01: 200 `PATCH /scim/v2/Users/{id}` name updates; p95 < 500 ms.
- `scim_group_patch_500_members_p95` — NFR-F026-01: replace members with 500 users mapped to two roles; each request < 2 s, role bindings recomputed in one transaction.
- `suspend_with_40_owned_objects_within_budget` — FR-F026-11: suspension transfers 40 objects in under 5 s with outcome `applied`.
- `assertion_replay_cache_bounded` — FR-F026-04: 10,000 assertion IDs inserted; cleanup statement removes expired rows in under 200 ms using `saml_assertion_ids(expires_at)`.

Evidence: criterion summaries under `testing/evidence/F026/performance/`.
