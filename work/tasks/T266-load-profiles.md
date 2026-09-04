---
id: T266
type: task
status: planned
parent_epic: E000
parent_feature: F067
parent_story: S133
depends_on: [S133]
owned_paths: [automation/xtask/src/load/**, testing/load/profiles/**, testing/load/k6/**, testing/features/F067/api/**, testing/features/F067/e2e/**]
feature_flag: F067_FEATURE
branch: t266-load-profiles
started_at: null
finished_at: null
---

# T266 — Load profiles

## Identity

- Parent story: `S133` Load profiles and seeds
- Owner: platform
- Branch: `t266-load-profiles`
- Decision references: `docs/architecture-decisions.md` sections 3, 5, 9; `docs/capability-contracts.md` row F067

## Objective

Define the profile schema and its validation, author the four shipped profiles with their mixes, ramps and thresholds, and write the k6 scripts and shared library that execute them from the rendered profile rather than in-script constants.

## Specification

- Owned paths: `automation/xtask/src/load/profile.rs`, `testing/load/profiles/{steady-read.toml, concurrent-edit.toml, bulk-automation.toml, soak.toml}`, `testing/load/k6/{steady-read.js, concurrent-edit.js, bulk-automation.js, soak.js}`, `testing/load/k6/lib/{auth.js, sheets.js, ws.js, metrics.js}`
- Contract/input: `Profile { name, dataset, executor, duration_s, ramp_up_s, ramp_down_s, target_rate, mix: Vec<MixEntry { weight_pct, operation, params }>, thresholds: Vec<Threshold { metric, statistic, operator, value }>, comparison: Vec<Comparison { metric, rule }> }` parsed from TOML and rendered to JSON on a file descriptor for k6.
- Output/behavior: validation rejects weights not summing to 100, `duration_s` not exceeding `ramp_up_s + ramp_down_s`, a duplicate profile name, an unknown TOML key, and a threshold metric outside the catalog, exiting 2 with `profile.invalid`. `steady-read` runs 30 min (300 s ramp, 1,200 s hold at 2,000 req/s, 300 s down) with mix 60% `GET /api/v1/sheets/{id}/rows` at page size 100, 15% `GET /api/v1/sheets`, 10% `GET /api/v1/rows/{id}`, 10% saved-view reads, 5% `PATCH /api/v1/rows/{id}`. `concurrent-edit` runs 20 min holding 1,000 sessions on `GET /ws/v1/sheets/{id}` for one tenant's max-dimension sheet plus 1,000 sessions across 20 tenants, each sending one `PATCH /api/v1/sheets/{sheet_id}/cells` every 6 s with 40% of patches targeting the same 50 rows. `bulk-automation` runs 45 min with 200 concurrent 10,000-row `POST /api/v1/sheets/{sheet_id}/rows/bulk` imports while 50 automation rules per tenant fire on every write. `soak` runs 8 h at the `steady-read` mix reduced to 800 req/s plus 200 continuous edit sessions. HTTP scenarios use the `constant-arrival-rate` executor so offered load stays fixed when the system slows; only WebSocket sessions use `ramping-vus`. A script whose declared scenario set differs from its profile exits 2 with `profile.script_mismatch`; a mix entry naming a route absent from the capability catalog exits 2 with `profile.invalid`.
- Dependencies: T265 datasets and manifests; k6 v0.54.0 pinned by digest; F006, F008, and F046 routes reachable on the load environment.
- Feature flag: `F067_FEATURE` gates the `load-test` subcommand; profiles are inert data otherwise.

## TDD

- Failing test first: `testing/features/F067/api/profile_tests.rs::profile_weights_must_sum_to_one_hundred`, `::profile_duration_must_exceed_ramps`, `::profile_rejects_unknown_threshold_metric`, `::profile_rejects_unknown_toml_key`, `::profile_rejects_route_absent_from_catalog`, `::four_shipped_profiles_parse_with_declared_mixes`, `::rendered_json_matches_profile_toml`; `testing/features/F067/api/script_tests.rs::k6_script_scenarios_match_profile`, `::http_scenarios_use_constant_arrival_rate`, `::ws_sessions_use_ramping_vus`; `testing/features/F067/e2e/smoke_profile_tests.rs::each_profile_runs_at_smoke_scale`
- Targeted command: `cargo xtask test-feature F067`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/load.rs` fake k6 replaying recorded summaries from `testing/features/F067/api/fixtures/k6/`, a `smoke` dataset at 1/100 scale, and a catalog snapshot for the route-existence check

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] All four profiles validate, render, and complete one `smoke`-scale run each
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S133
- [ ] `finished_at` recorded
