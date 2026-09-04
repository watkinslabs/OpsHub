---
id: S133
type: story
status: planned
parent_epic: E000
parent_feature: F067
depends_on: [F043, F044]
owned_paths: [automation/xtask/src/load/**, testing/load/profiles/**, testing/load/datasets/**, testing/load/seed/**, testing/load/k6/**, testing/evidence/F067/**, testing/features/F067/**]
feature_flag: F067_FEATURE
branch: s133-load-profiles-and-seeds
started_at: null
finished_at: null
---

# S133 — Load profiles and seeds

## Identity

- Parent feature: `F067` System scale and load validation
- Owner: platform
- Branch: `s133-load-profiles-and-seeds`
- Decision references: `docs/architecture-decisions.md` sections 1, 2, 9; `docs/capability-contracts.md` row F067

## Vertical slice

As a maintainer, I want named load profiles with a declared traffic mix, duration, ramp and thresholds, three composite datasets sized against the spec section 6 scale target, and a seed generator that rebuilds any of them reproducibly from one `u64`, so that the traffic and the data a scale run measures are defined artifacts rather than a script someone tuned by hand.

## Requirements

- **SR-S133-01:** `testing/load/profiles/<name>.toml` parses into `Profile { name, dataset, executor, duration_s, ramp_up_s, ramp_down_s, target_rate, mix, thresholds, comparison }`; weights must sum to 100, `duration_s` must exceed `ramp_up_s + ramp_down_s`, every threshold metric must exist in the metric catalog, and any violation exits 2 with `profile.invalid` (covers FR-F067-01).
- **SR-S133-02:** The four shipped profiles carry the mixes and durations of FR-F067-02: `steady-read` (30 min, 2,000 req/s, 60/15/10/10/5 read-write split), `concurrent-edit` (20 min, 2,000 WebSocket sessions, ≈333 cell patches/s with 40% aimed at 50 shared rows), `bulk-automation` (45 min, 200 concurrent 10,000-row imports with 50 rules per tenant), and `soak` (8 h at 800 req/s plus 200 edit sessions) (FR-F067-02).
- **SR-S133-03:** `testing/load/datasets/{smoke,tier1,full}.toml` declare tenants, users, max-dimension sheets at 100,000 rows × 500 columns, typical sheets, cell density, and expected per-table row counts; a produced count differing from the declaration exits 2 with `dataset.count_mismatch` (FR-F067-03).
- **SR-S133-04:** `cargo xtask load-test seed --dataset <name> --seed <u64>` generates deterministically from a ChaCha20 stream keyed by `(seed, table_ordinal, tenant_ordinal)` with UUIDv7 ids based at `2026-01-01T00:00:00Z`, loads through `COPY … FROM STDIN BINARY` on 8 connections, builds indexes and foreign keys afterwards, and meets the budgets `smoke` < 90 s, `tier1` < 25 min, `full` < 4 h with a hard `dataset.timeout` (FR-F067-04, NFR-F067-01).
- **SR-S133-05:** The generator writes `testing/evidence/F067/datasets/<dataset>-<seed>.json` with counts, per-table crc32c checksums, `generator_sha256`, and duration, caches a `pg_dump -Fc` archive under `testing/load/seed/cache/`, restores `tier1` from that cache in under 12 min, and offers `--verify` (1% seeded sampling, `dataset.drift` on mismatch) and `--rebuild` (FR-F067-05).
- **SR-S133-06:** `testing/load/k6/<profile>.js` uses `constant-arrival-rate` for HTTP scenarios and `ramping-vus` only for WebSocket sessions, reads rates and mix from the profile rendered to JSON rather than in-script constants, shares `lib/{auth.js,sheets.js,ws.js,metrics.js}`, and exits 2 with `profile.script_mismatch` when its scenario set diverges from the profile (FR-F067-06).
- **SR-S133-07:** Profile mixes reference only routes present in the `docs/capability-contracts.md` rows they exercise — F006 sheet and row reads and writes, F008 cell and bulk endpoints, F046 sheet WebSocket sessions — so a removed route fails profile validation instead of silently skewing the mix (FR-F067-01, FR-F067-02).
- **SR-S133-08:** Generated data is synthetic only: addresses on `@load.invalid`, names from a checked-in word list, no production dump path, and the generator refuses to run against a host in the production allowlist (NFR-F067-03).
- **SR-S133-09:** Determinism is proven, not asserted: the same seed reproduces identical table checksums on a second machine and PostgreSQL 18 patch version, and a different seed changes them (NFR-F067-02, FR-F067-04).

## Surfaces

- Infrastructure/container: k6 v0.54.0 pinned by digest in the load runner image; the load environment's PostgreSQL 18 primary reached through `LOAD_ENV_URL`; seed-time settings `maintenance_work_mem = 2GB`, `max_wal_size = 32GB`, `autovacuum = off` applied and reverted by the generator
- Rust service/API: no route and no service change; `automation/xtask/src/load/{mod.rs, profile.rs, dataset.rs, seed.rs}` plus the `load-test` dispatch arm in `automation/xtask/src/main.rs`
- Data/migration: no migration; the generator writes the existing F002 `tenants`, `users`, `groups`, `group_members` and F006 `sheets`, `rows`, `cells` tables in dependency order on the load environment only
- React/UI: none; `apps/web/src/features/load/` is never created and its absence is a negative control
- Mocks/fixtures: `testing/fixtures/load.rs` with a temporary repository tree, a fake k6 binary replaying recorded summaries, and a throwaway PostgreSQL 18 database per test worker

## TDD harness

- Test path: `testing/features/F067/{api,database,performance}/`
- Feature flag: `F067_FEATURE`
- Targeted command: `cargo xtask test-feature F067`
- Full command: `cargo xtask test-all`
- First failing tests: `profile_weights_must_sum_to_one_hundred`, `profile_rejects_unknown_threshold_metric`, `profile_duration_must_exceed_ramps`, `four_shipped_profiles_parse_with_declared_mixes`, `dataset_counts_match_declaration`, `seed_is_deterministic_for_same_value`, `seed_differs_for_different_value`, `seed_cache_restore_matches_fresh_build`, `verify_detects_mutated_table`, `k6_script_scenarios_match_profile`

## Exit criteria

- [ ] Requirement tests SR-S133-01 through SR-S133-09 written first and failing
- [ ] Tasks T265 and T266 complete and wired through the `load-test` arm in `automation/xtask/src/main.rs`
- [ ] `smoke`, `tier1`, and `full` datasets built once each with manifests committed under `testing/evidence/F067/datasets/`
- [ ] Determinism, cache restore, and `--verify` proven on PostgreSQL 18 in CI
- [ ] Production call path named: `automation/xtask/src/main.rs` dispatches `load-test` into `automation/xtask/src/load/mod.rs`, which resolves the profile and dataset before handing the rendered plan to the runner of S134
- [ ] Handoff evidence recorded in the F067 ticket
