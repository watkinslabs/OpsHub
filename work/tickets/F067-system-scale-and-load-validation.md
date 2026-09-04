---
id: F067
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M0
parent_epic: E000
depends_on: [F043, F044]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [automation/xtask/src/load/**, testing/load/profiles/**, testing/load/datasets/**, testing/load/seed/**, testing/load/k6/**, testing/load/gate/**, testing/evidence/F067/**, testing/features/F067/**]
feature_flag: F067_FEATURE
flag_default: off
branch: f067-system-scale-and-load-validation
started_at: null
finished_at: null
---

# F067 — System scale and load validation

## 1. Identity and dates

- Branch: `f067-system-scale-and-load-validation`
- Capability area: developer workflow control plane (spec section 6 scale target "10,000 tenants, 1 million users, 100,000 rows per sheet, 500 columns per sheet, and 1,000 concurrent edits per tenant; validate through load tests"; spec section 6 performance targets p95 interactive read < 500 ms, p95 single-row write < 800 ms, async ack < 2 s; spec section 8 release gates)
- Decision references: `docs/architecture-decisions.md` sections 1, 2, 7, 9, 10; `docs/capability-contracts.md` row F067
- Aggregate: `load-profile`
- Module slug: `load` (Rust module `automation/xtask/src/load/`; profiles, datasets, seed plans, k6 scripts and gate configuration under `testing/load/**`; evidence under `testing/evidence/F067/**`)
- Owned-path note: the catalog persistence cell `testing/load/**` is a two-segment glob that `content.rs` rejects as a catch-all, so `owned_paths` names its five real subtrees (`profiles`, `datasets`, `seed`, `k6`, `gate`) instead of the collapsed form.

- Design: this feature has no user surface; it ships tooling, runtime or contracts only.

## 2. Requirement specification

### Problem and user outcome

Every feature proves its own slice and nothing exercises the slices together. F002 loads 100,000 users, F008 drives 1,000 concurrent editors on one sheet, F046 holds 1,000 realtime sessions, F004 drains 10,000 outbox rows — each on an otherwise idle system. Contention does not appear in a single slice: it appears when a bulk import saturates the connection pool while automation rules fan out through the outbox and 1,000 editors wait on a WebSocket broadcast that is now behind a checkpoint. Spec section 6 sets a composite target and says to validate it with load tests, and today there is no dataset large enough to try, no profile that mixes the traffic, no thresholds on the resources that fail before latency does, and no place a result is recorded.

As a maintainer or release manager, I want `cargo xtask load-test <profile>` to build a deterministic composite dataset, drive a named traffic mix against a dedicated load environment, gate on pool saturation, outbox lag, queue depth, replication lag, memory growth, and error rate as well as latency, report `skipped` with a reason code when the environment is not there, and compare each run against a promoted baseline, so that a milestone ships on measured whole-system behavior instead of four independent slice benchmarks.

### Functional requirements

- **FR-F067-01:** Each profile is one TOML file `testing/load/profiles/<name>.toml` parsed into `Profile { name, dataset, executor, duration_s, ramp_up_s, ramp_down_s, target_rate, mix: Vec<MixEntry { weight_pct, operation, params }>, thresholds: Vec<Threshold { metric, statistic, operator, value }>, comparison: Vec<Comparison { metric, rule }> }`; weights must sum to 100, `duration_s` must exceed `ramp_up_s + ramp_down_s`, every `metric` must be a member of the metric catalog in FR-F067-07 and FR-F067-08, and an unknown key, a duplicate profile name, or an unknown metric exits 2 with `profile.invalid`.
- **FR-F067-02:** Four profiles ship. `steady-read`: 30 min (5 ramp / 20 hold at 2,000 req/s / 5 down) with mix 60% `GET /api/v1/sheets/{id}/rows` at page size 100, 15% `GET /api/v1/sheets`, 10% `GET /api/v1/rows/{id}`, 10% saved-view reads, 5% `PATCH /api/v1/rows/{id}`. `concurrent-edit`: 20 min holding 1,000 WebSocket sessions on one tenant's max-dimension sheet plus 1,000 sessions spread over 20 tenants, each session issuing one cell patch every 6 s (≈333 patches/s) with 40% of patches aimed at the same 50 rows to force version contention. `bulk-automation`: 45 min running 200 concurrent imports of 10,000 rows each through `POST /api/v1/sheets/{sheet_id}/rows/bulk` while 50 automation rules per tenant fire on every write. `soak`: 8 h at the `steady-read` mix reduced to 800 req/s plus 200 continuous edit sessions.
- **FR-F067-03:** Three datasets are defined in `testing/load/datasets/<name>.toml`. `smoke`: 10 tenants, 1,000 users, 1 sheet of 5,000 rows × 50 columns, 50 typical sheets — proves the harness, never the scale target. `tier1`: 1,000 tenants, 100,000 users, 1 max-dimension sheet (100,000 rows × 500 columns at 30% cell density), 200 typical sheets (2,000 rows × 30 columns at 80% density) — the scheduled dataset. `full`: 10,000 tenants, 1,000,000 users, 10 max-dimension sheets, 2,000 typical sheets — ≈4 million rows and ≈250 million cells, the dataset the milestone gate requires. Each file declares expected row counts per table, and the generator fails with `dataset.count_mismatch` when a produced count differs from the declaration.
- **FR-F067-04:** `cargo xtask load-test seed --dataset <name> --seed <u64>` builds a dataset deterministically: a ChaCha20 stream keyed by `(seed, table_ordinal, tenant_ordinal)` drives every value, UUIDv7 identifiers use a fixed timestamp base of `2026-01-01T00:00:00Z` plus the row ordinal so ids are reproducible, all rows load through `COPY … FROM STDIN BINARY` on 8 parallel connections, and secondary indexes and foreign keys are created after the load. Two runs with the same `--seed` produce byte-identical table checksums; a different `--seed` changes them. Reference machine (16 vCPU, 64 GiB, gp3 at 12,000 IOPS): `smoke` under 90 s, `tier1` under 25 min, `full` under 4 h, each enforced as a hard timeout that exits 2 with `dataset.timeout`.
- **FR-F067-05:** After a successful build the generator writes `testing/evidence/F067/datasets/<dataset>-<seed>.json` `{ dataset, seed, built_at, generator_sha256, postgres_version, counts: { <table>: n }, checksums: { <table>: crc32c }, duration_s }` and caches a `pg_dump -Fc` archive keyed `testing/load/seed/cache/<dataset>-<seed>.manifest`; a later run with the same dataset and seed restores from the cache (`tier1` under 12 min) instead of regenerating. `--verify` re-derives the checksums by sampling 1% of each table with a seeded sampler and exits 2 with `dataset.drift` on mismatch; `--rebuild` ignores the cache.
- **FR-F067-06:** k6 v0.54.0 executes the traffic. `testing/load/k6/<profile>.js` declares scenarios using the `constant-arrival-rate` executor (so offered load does not shrink when the system slows) and `ramping-vus` only for the WebSocket sessions of `concurrent-edit` and `soak`; shared code lives in `testing/load/k6/lib/{auth.js,sheets.js,ws.js,metrics.js}`. The script reads the mix and rates from the profile TOML rendered to JSON by the xtask, never from constants inside the script, and a script whose declared scenario set does not match its profile exits 2 with `profile.script_mismatch`.
- **FR-F067-07:** Latency and throughput metrics gated on every profile: `http_read_p95_ms` < 500, `http_write_p95_ms` < 800, `http_read_p99_ms` < 1500, `async_ack_p95_ms` < 2000, and `achieved_rate_ratio` (completed iterations ÷ offered iterations) ≥ 0.99. `concurrent-edit` and `soak` add `ws_broadcast_p95_ms` < 250 and `ws_session_drop_rate` < 0.005.
- **FR-F067-08:** Saturation and correctness metrics gated in addition to latency, because these fail first: `db_pool_wait_p99_ms` < 50 and `db_pool_in_use_ratio_p99` < 0.85; `outbox_lag_seconds_p99` < 5 with `outbox_backlog_rows` back under 1,000 within 120 s of ramp-down; `job_queue_depth_p99` < 5,000 and `job_oldest_age_seconds_p99` < 60; `replication_lag_bytes_p99` < 33554432 and `replication_lag_seconds_p99` < 10; `rss_slope_mib_per_hour` < 2.0 per process measured by least-squares regression over samples after minute 30 (reported with r², gated only on `soak`); `http_5xx_rate` < 0.001 and `dead_letter_count` = 0; `version_conflict_rate` < 0.03 on `concurrent-edit` with every retried conflict succeeding on the first retry.
- **FR-F067-09:** Client-side metrics come from the k6 end-of-test summary and its 10-second sample stream; server-side metrics come from Prometheus range queries defined in `testing/load/gate/metrics.toml` (one query per metric id, evaluated over the hold window only, ramp windows excluded). A metric whose query returns no series exits 2 with `metric.absent` and the run is `failed`, never `passed`, so a missing exporter cannot look like a clean result.
- **FR-F067-10:** `cargo xtask load-test <profile>` accepts `--dataset <name>`, `--seed <u64>`, `--baseline <path>`, `--compare <run_id>`, `--promote-baseline`, `--require-env`, `--dry-run`, and `--json`, and exits 0 on `passed` or `skipped`, 1 on `failed` or `regressed`, 2 on a usage, profile, dataset, or metric-collection error, and 3 on `role_required`. `--dry-run` renders the profile, resolves the dataset, prints the scenario plan and every threshold, and contacts nothing.
- **FR-F067-11:** Preflight runs before any traffic and checks, in order: `LOAD_ENV_URL` and `LOAD_ENV_TOKEN` are set; `GET {LOAD_ENV_URL}/readyz` returns 200 within 30 s; the k6 binary reports the pinned version; the dataset manifest for the profile's dataset exists and its `generator_sha256` matches the current generator; no other run holds the lock of FR-F067-17. A failed check produces `status: "skipped"` with `reason_code` in `env_unset`, `env_unreachable`, `runner_missing`, `dataset_missing`, `dataset_stale`, `concurrent_run`, prints `load-test <profile>: skipped (<reason_code>)`, writes the evidence record of FR-F067-13, and exits 0. `--require-env` converts every skip into exit 2 so a scheduled run pages instead of going quiet. A `skipped` run is never a pass for any gate.
- **FR-F067-12:** The gate never runs on a pull request and is not referenced by `gates.yml`. It runs from `.github/workflows/load.yml` on `schedule` — `tier1` with `steady-read` and `concurrent-edit` nightly at 03:00 UTC on `main`, `tier1` with `bulk-automation` and `soak` weekly on Saturday at 02:00 UTC — and on `workflow_dispatch` with profile, dataset, and seed inputs. The milestone gate consumes it: `verify-release --milestone M#` (FR-F044-15) requires, for every profile, a `passed` run on the `full` dataset whose commit is an ancestor of the milestone head and whose `finished_at` is within 14 days, and reports `release.scale_missing`, `release.scale_stale`, or `release.scale_failed` otherwise; a `skipped` run satisfies none of them.
- **FR-F067-13:** Evidence lands under `testing/evidence/F067/runs/<run_id>/` with `run_id = <YYYYMMDDTHHMMSSZ>-<profile>-<dataset>-<commit12>`, holding `result.json` `{ run_id, status: passed|failed|regressed|regressed_unconfirmed|skipped|aborted, profile, dataset, seed, commit, started_at, finished_at, metrics: [{ id, statistic, value, threshold, verdict, baseline_value, comparison_verdict }], reason_code?, reason? }`, `summary.json` (raw k6 summary), `metrics.ndjson.zst` (10-second samples of every series), `server-metrics.json` (Prometheus range results), `environment.json` (image digests plus `max_connections`, `shared_buffers`, `work_mem`, `checkpoint_timeout`, replica count), `dataset.json` (dataset, seed, manifest sha256), `commands.log`, and `report.md`. `result.json`, `environment.json`, `dataset.json`, `report.md`, `baseline/**`, and `index.json` are tracked; `summary.json`, `metrics.ndjson.zst`, and `server-metrics.json` are regenerated lane artifacts and stay untracked, matching `testing/evidence/README.md`.
- **FR-F067-14:** A run passes only when both the absolute thresholds and the regression comparison hold. The comparison reference is the median of the last three `passed` runs of the same profile and dataset, or the promoted baseline when fewer than three exist. Rules: latency and lag metrics regress when `value > reference * 1.10 + 15`; throughput and `achieved_rate_ratio` regress when `value < reference * 0.90`; saturation metrics (`db_pool_in_use_ratio_p99`, `job_queue_depth_p99`, `outbox_backlog_rows`, `rss_slope_mib_per_hour`) regress when `value > reference * 1.25`; error rates regress when `value > max(reference * 2, 0.001)`. Absolute breaches fail immediately; a regression alone yields `regressed_unconfirmed` on its first occurrence (exit 0, reported) and `regressed` (exit 1) when the next run of the same profile and dataset regresses on the same metric id, so one noisy run does not block a milestone and a real drift cannot hide behind noise.
- **FR-F067-15:** `--promote-baseline` writes `testing/evidence/F067/baseline/<profile>-<dataset>.json` `{ profile, dataset, promoted_at, promoted_by, promoted_from: [run_id; 3], commit, metrics: { <id>: value }, reason }` and requires the three most recent runs of that profile and dataset to be `passed` and `XTASK_ROLE=maintainer` with `XTASK_OWNER` set, or CI on `main`; otherwise it exits 3 with `baseline.role_required` and writes nothing. Promotion never overwrites history: the superseded file is kept as `baseline/archive/<profile>-<dataset>-<promoted_at>.json`.
- **FR-F067-16:** Each run appends to `testing/evidence/F067/index.json` `{ runs: [{ run_id, profile, dataset, status, commit, finished_at, key_metrics: { … } }] }` capped at the last 30 entries per profile and dataset, and renders `report.md` with the sections `Verdict`, `Environment`, `Dataset`, `Thresholds`, `Comparison`, and `Findings`, where `Thresholds` and `Comparison` are Markdown tables with header cells carrying metric id, statistic, value, threshold or reference, and verdict word.
- **FR-F067-17:** One run at a time per environment: the xtask takes an advisory lock in the load environment's PostgreSQL (`pg_try_advisory_lock` on a hash of `LOAD_ENV_URL`) plus a lock file `testing/load/gate/.run.lock` holding pid, run id, and start time. A second run reports `skipped` with `concurrent_run`. A run whose k6 process dies, whose lock is lost, or which is cancelled writes `status: "aborted"` with the partial metrics it holds and exits 1; an `aborted` run is never a pass and is excluded from the comparison reference set.

### Non-functional requirements

- **NFR-F067-01 Performance:** the gate's own cost is bounded — profile parsing and `--dry-run` under 200 ms; preflight under 35 s including the readiness probe; result evaluation, comparison, and report rendering under 10 s; the reporter streams `metrics.ndjson.zst` for an 8-hour `soak` (≈2.9 million samples) in under 60 s with under 256 MiB resident memory; seed generation meets the FR-F067-04 budgets.
- **NFR-F067-02 Reliability and determinism:** the same `--seed` reproduces identical table checksums across machines and PostgreSQL 18 patch versions; thresholds are evaluated only over the hold window so ramp behavior cannot pass or fail a run; a partial or interrupted run is `aborted`, never `passed`; the gate is idempotent — re-running an existing `run_id` refuses with `run.exists` rather than overwriting evidence.
- **NFR-F067-03 Security and privacy:** the generator produces synthetic data only, never a production dump; generated addresses use the `@load.invalid` domain and generated names come from a checked-in word list; the load environment is network-isolated, is authenticated by a dedicated `load-tenant-admin` service principal whose token is scoped to that environment, and refuses to start when `LOAD_ENV_URL` resolves to a host in the production allowlist; `LOAD_ENV_TOKEN` is redacted from `commands.log`, `report.md`, and every evidence file.
- **NFR-F067-04 Observability and auditability:** every run records the commit, image digests, PostgreSQL settings that change the result, the dataset manifest hash, and the exact k6 command line; `index.json` makes the trend queryable without unpacking a run; the xtask emits its own counters `load_gate_runs_total{profile,dataset,status}` and `load_gate_metric_verdict_total{metric,verdict}` to the load environment's Prometheus.
- **NFR-F067-05 Output accessibility:** every command supports `--json`; terminal verdicts carry a word (`pass`, `fail`, `skip`, `regressed`) alongside any symbol or color so the result survives a non-color terminal and a screen reader; exit codes distinguish the outcomes without reading text; `report.md` is plain Markdown with heading structure and table header cells rather than an image.

### Scope

Included: the profile and dataset schemas and their four profiles and three datasets; the deterministic seed generator with cache, restore, and verify; the k6 scripts and shared library; the metric catalog and Prometheus query set; latency, saturation, and correctness thresholds; the `cargo xtask load-test <profile>` command with preflight, skip reason codes, locking, and exit codes; evidence layout, index, report, baseline promotion, and regression comparison; the scheduled workflow and the milestone hook consumed by `verify-release`.

Excluded: the load environment's own provisioning (`infra/` owned by F001 and F004); per-feature performance suites, which stay in each feature's `performance` lane (F002 user load, F008 concurrent editors, F046 sessions, F004 outbox drain); production capacity planning, autoscaling policy, and cost modelling; chaos and failure-injection testing; the fanout evidence collector and release verifier themselves (F043, F044), which this feature calls rather than reimplements; any HTTP route, database migration, or React surface.

## 3. UX specification

- Entry points: `cargo xtask load-test <profile>` for the four profiles; `cargo xtask load-test seed --dataset <name> --seed <n>` for dataset builds; `cargo xtask load-test report --run <run_id>` to re-render a report from stored evidence. There is no web surface.
- Primary flow: a maintainer exports `LOAD_ENV_URL` and `LOAD_ENV_TOKEN`, runs `cargo xtask load-test steady-read --dataset tier1 --seed 42`, sees `restoring tier1-42 from cache (11m42s)`, then a live line per 30 s with offered rate, achieved rate, read p95, and pool in-use ratio, then a verdict block listing every metric with value, threshold, reference, and verdict word, ending `load-test steady-read: pass (run 20260903T031500Z-steady-read-tier1-9454136e0f1a)`.
- Skip flow: without `LOAD_ENV_URL` the command prints `load-test steady-read: skipped (env_unset) — LOAD_ENV_URL is not set; the load environment is provisioned outside CI`, writes the evidence record, and exits 0; the scheduled workflow adds `--require-env` so the same condition exits 2 and pages.
- Failure flow: a breached absolute threshold prints the metric, its value, its threshold, and the three samples nearest the worst window, then `load-test bulk-automation: fail (outbox_lag_seconds_p99 = 11.4, threshold < 5)`; a first-time regression prints `regressed (unconfirmed)` with the reference value and the run id to compare against.
- Progress and cancellation: `Ctrl-C` stops k6, releases both locks, writes `status: "aborted"`, and prints the partial metric table; the lock file names the pid holding a run so a stale lock is diagnosable.
- Output conventions: `--json` emits `result.json` on stdout and nothing else; the human output uses words plus symbols, never color alone; long tables wrap rather than truncate metric ids.

## 4. Technical specification

Canonical contract: aggregate `load-profile`; module `load`; surface `cargo xtask load-test <profile>`, `testing/load/**`, k6 profiles and seed generators; events none; persistence `testing/load/**` and `testing/evidence/F067/**`; role maintainer. Decision link: `docs/architecture-decisions.md` sections 1, 2, 7, 9, 10.

### Rust backend

- No Axum route, handler, DTO, or service is added; F067 owns no path under `services/`, `crates/`, or `apps/`. The implementation is the xtask module `automation/xtask/src/load/{mod.rs, profile.rs, dataset.rs, seed.rs, runner.rs, metrics.rs, thresholds.rs, compare.rs, evidence.rs, report.rs, lock.rs, preflight.rs}`, dispatched from the existing `automation/xtask/src/main.rs` arm for `load-test`.
- Types: `Profile`, `MixEntry`, `Threshold { metric, statistic, operator: Lt|Lte|Gt|Gte|Eq, value }`, `Comparison { metric, rule: LatencyDrift|ThroughputDrop|SaturationDrift|ErrorRateDrift }`, `Dataset { name, tenants, users, max_dimension_sheets, typical_sheets, rows_per_sheet, columns_per_sheet, cell_density, expected_counts }`, `SeedPlan`, `RunId`, `MetricSample { id, at, value }`, `MetricVerdict { id, value, threshold, verdict, baseline_value, comparison_verdict }`, `RunResult`, `SkipReason`, `LoadError`.
- Error mapping to exit codes: `LoadError::Usage | ProfileInvalid | DatasetTimeout | DatasetDrift | MetricAbsent | ScriptMismatch | RunExists → 2`; `LoadError::ThresholdBreach | RegressionConfirmed | Aborted → 1`; `LoadError::RoleRequired → 3`; a skip is not an error and returns 0.
- Data access (decision 2.1): the `load-profile` aggregate owns no table. The seed generator writes tenants, users, groups, sheets, rows, and cells through the existing `TenantRepository`, `UserRepository`, `GroupRepository`, `SheetRepository`, `RowRepository`, and `CellRepository` in `crates/persistence`, in dependency order and in batches, so the load dataset is written by the same classes the product uses and `automation/xtask/src/load/seed.rs` contains no SQL of its own; the load-time server settings are applied by the environment provisioning script, not by the generator.
- Process control: k6 is spawned with the rendered profile JSON on a file descriptor, its stdout parsed as NDJSON summaries, and its process group killed on cancellation; Prometheus range queries use a 10-second step and are retried three times with exponential backoff before `metric.absent`.
- Integration points: F043 `collect-artifacts` copies `testing/evidence/F067/runs/<run_id>/**` alongside lane artifacts; F044 `verify-release --milestone M#` reads `testing/evidence/F067/index.json` and the referenced `result.json` files to apply FR-F067-12.

### PostgreSQL/SQLx

- No migration is added and no table is owned; `services/api/migrations/` gains no `*_load_*.sql` file, and the database lane asserts that as a negative control.
- The generator writes to the load environment's database only through the `crates/persistence` repositories that own the schema of other features (`tenants`, `users`, `groups`, `group_members` from F002; `sheets`, `rows`, `cells` from F006), in dependency order, inside one `UnitOfWork` per tenant batch of 100, with `session_replication_role = replica` during load so foreign keys are validated once at the end rather than per row.
- Load-time settings applied to the load environment for the seed and reverted afterwards, recorded in `environment.json`: `maintenance_work_mem = 2GB`, `max_wal_size = 32GB`, `checkpoint_timeout = 30min`, `autovacuum = off` for the duration, followed by `VACUUM (ANALYZE)` on every touched table. Steady-state settings under measurement are pinned: `max_connections = 400`, `shared_buffers = 16GB`, `work_mem = 32MB`, `checkpoint_timeout = 5min`, one streaming replica.
- Cell density is applied per row by the seeded PRNG so the sparse `cells` layout is exercised realistically; the `full` dataset lands ≈4 million rows and ≈250 million cells, which the dataset manifest records as the authoritative counts.
- Server-side saturation metrics read `pg_stat_activity`, `pg_stat_replication`, and `pg_stat_bgwriter` through the Prometheus exporter of the load environment, and the outbox and queue metrics read `outbox_events`, `job_runs`, and `dead_letters` (F004) through the same exporter — read-only, never written by this feature.

### React/TypeScript

- No React route, component, hook, generated client operation, or design token is added; `apps/web/src/features/load/` is never created, and the frontend lane asserts its absence together with the absence of any `openapi/v1.json` operation carrying `x-opshub-feature: F067`.
- The only reader-facing artifact is `testing/evidence/F067/runs/<run_id>/report.md`, plain Markdown rendered by `report.rs`, whose required sections and table header cells are asserted in the frontend lane so the run record stays readable without a viewer.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F067-01 through FR-F067-17 and NFR-F067-01 through NFR-F067-05 in `testing/features/F067/requirements/cases.md`
- [ ] Failure/edge-case tests: weights summing to 99, unknown metric id, duration shorter than the ramps, k6 killed mid-run, Prometheus series absent, stale dataset manifest, lock held by another pid, `run_id` already present
- [ ] Permission-negative tests: `--promote-baseline` without `XTASK_ROLE=maintainer` exits 3 and writes nothing; a `LOAD_ENV_URL` in the production allowlist refuses to start; `LOAD_ENV_TOKEN` never appears in any evidence file
- [ ] Rust unit tests: profile and dataset parsing, threshold evaluation per operator, comparison arithmetic for all four rules, unconfirmed-then-confirmed regression sequencing, skip classification, run-id formatting, RSS regression slope
- [ ] Seed generator tests: same seed reproduces checksums, different seed does not, declared counts match produced counts, cache restore matches a fresh build, `--verify` catches a mutated table
- [ ] Harness negative controls: no route, no migration, no React surface, no OpenAPI operation, no entry in `gates.yml`
- [ ] Smoke-scale end-to-end: each of the four profiles runs against the `smoke` dataset at 1/100 scale and produces a complete evidence directory
- [ ] Output tests: `--json` is the only stdout content, verdict words present without color, `report.md` sections and table headers present
- [ ] Performance tests: seed budgets, preflight budget, reporter throughput and memory over a synthetic 8-hour sample stream

### Fast fanout configuration

- Test harness path: `testing/features/F067/`
- Feature flag: `F067_FEATURE`
- Fixture/seed factory: `testing/fixtures/load.rs` builds a temporary repository tree with `testing/load/profiles/`, `testing/load/datasets/`, a fake k6 binary that replays a recorded summary, a recorded Prometheus range-query server, a throwaway PostgreSQL 18 database for the generator, and a synthetic 8-hour sample stream for the reporter
- Deterministic test data: fixed generator seed `42`, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed commit `9454136e0f1a`, recorded k6 summaries under `testing/features/F067/api/fixtures/k6/`
- Mock/stub contracts: fake k6 that honors the pinned `--version` and exits with a scripted code; Prometheus stub returning empty, partial, and complete series; readiness endpoint stub returning 200, 503, and a timeout
- Parallel isolation: one temporary repository root and one database per test worker; the advisory lock uses a per-worker key so lock tests do not collide
- Targeted command: `cargo xtask test-feature F067`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F067/`

## 6. Acceptance criteria

```gherkin
Feature: Composite scale and load validation

Scenario: A composite run passes on absolute thresholds and comparison
  Given the tier1 dataset restored from seed 42 and a promoted baseline for steady-read
  When cargo xtask load-test steady-read --dataset tier1 --seed 42 runs against the load environment
  Then read p95 is under 500 ms, pool in-use ratio p99 is under 0.85, outbox lag p99 is under 5 s
  And result.json records every metric with value, threshold, reference, and verdict and status passed

Scenario: A missing load environment skips instead of passing silently
  Given LOAD_ENV_URL is not set
  When cargo xtask load-test soak runs
  Then it exits 0 with status skipped and reason_code env_unset
  And verify-release --milestone M0 reports release.scale_missing for the soak profile

Scenario: Saturation fails before latency does
  Given bulk-automation drives 200 concurrent imports of 10,000 rows while 50 rules per tenant fire
  When outbox lag p99 reaches 11.4 s while read p95 is still 380 ms
  Then the run fails on outbox_lag_seconds_p99 and exits 1

Scenario: A single noisy run does not block the milestone but a repeat does
  Given the last three passed concurrent-edit runs have ws_broadcast_p95_ms of 180, 185, and 182
  When a run reports 240 ms and the next run reports 244 ms
  Then the first is regressed_unconfirmed at exit 0 and the second is regressed at exit 1
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F043 (lane claiming and `collect-artifacts`, which gathers this feature's evidence directory); F044 (`verify-release --milestone`, which consumes the run records as the milestone scale gate); decisions sections 1, 2, 7, 9, 10; contracts row F067
- Blocks: none
- Conflicts with: none — the owned paths are the xtask `load` module, the five `testing/load` subtrees, and this feature's evidence and harness directories
- External dependencies: k6 v0.54.0; a dedicated load environment (3 API nodes at 4 vCPU / 8 GiB, 2 workers, PostgreSQL 18 primary at 16 vCPU / 64 GiB with one streaming replica, 3-node NATS JetStream, MinIO, Prometheus) provisioned outside this feature and addressed by `LOAD_ENV_URL`
- Risks and mitigations: the `full` dataset costs about 4 hours and roughly 60 GiB, mitigated by the seed cache, the `tier1` dataset for scheduled runs, and reserving `full` for the milestone gate; cloud noise producing false regressions, mitigated by the median-of-three reference, the 10% plus 15 ms latency band, and the unconfirmed-then-confirmed rule; a load run masquerading as a pass when the environment is missing, mitigated by explicit `skipped` records that no gate accepts and by `--require-env` on the scheduled job; the profiles drifting from the product as features land, mitigated by pinning the mix to catalog routes and failing `profile.invalid` when a referenced operation disappears; a generator change silently altering the dataset, mitigated by `generator_sha256` in the manifest and the `dataset_stale` skip reason
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F043 and F044 accepted and archived so `collect-artifacts` and `verify-release` exist to call
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F067/`
- [ ] Load environment reachable from CI with `LOAD_ENV_URL` and `LOAD_ENV_TOKEN` provisioned, or the skip path exercised in its absence
- [ ] Owned paths claimed and the `testing/load/**` subtrees created empty

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Each of the four profiles has produced one `passed` run on the `tier1` dataset and one on the `full` dataset with evidence under `testing/evidence/F067/`
- [ ] A promoted baseline exists per profile and dataset, and the regression path is proven by a seeded slowdown that yields `regressed_unconfirmed` then `regressed`
- [ ] The skip path is proven: no `LOAD_ENV_URL` yields exit 0 `skipped` and `verify-release --milestone M0` rejects it
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets`, `validate-work`, and `check-contracts` pass
- [ ] Rollback verified: disable `F067_FEATURE`, confirm `gates.yml` and pull requests are unaffected because the gate is scheduled and milestone-triggered only
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- `cargo xtask load-test <profile>` validates the spec section 6 scale target for the whole system at once: a deterministic seed generator builds `smoke`, `tier1`, and `full` composite datasets (up to 10,000 tenants, 1,000,000 users, 100,000-row × 500-column sheets), and four profiles — `steady-read`, `concurrent-edit`, `bulk-automation`, and an 8-hour `soak` — drive them while the gate measures connection-pool saturation, outbox lag, job queue depth, replication lag, memory growth, and error rate alongside latency.
- Runs are scheduled and milestone-triggered, never on pull requests; a missing load environment reports `skipped` with a reason code that no release gate accepts. Every run writes `testing/evidence/F067/runs/<run_id>/` and is compared against a promoted baseline, so a 10% drift is caught before an absolute threshold is. No route, table, migration, or UI is added; the feature is off by default behind `F067_FEATURE`.
