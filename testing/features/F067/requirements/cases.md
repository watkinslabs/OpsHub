# F067 requirements cases

Feature: System scale and load validation. Flag `F067_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F067-REQ-001` | FR-F067-01 | api | profile TOML parses into `Profile`; weights ≠ 100, duration ≤ ramps, duplicate name, unknown key, or unknown metric → exit 2 `profile.invalid` |
| `F067-REQ-002` | FR-F067-02 | api, e2e | the four shipped profiles carry their declared mix, rate, ramp, and duration; each completes one `smoke`-scale run |
| `F067-REQ-003` | FR-F067-03 | database | `smoke`, `tier1`, `full` declarations parse; a produced count differing from the declaration → exit 2 `dataset.count_mismatch` |
| `F067-REQ-004` | FR-F067-04 | database, performance | same `--seed` reproduces table checksums, a different seed does not; `smoke` seeds under 90 s; budget overrun → `dataset.timeout` |
| `F067-REQ-005` | FR-F067-05 | database | manifest records counts, crc32c, `generator_sha256`; cache restore equals a fresh build; `--verify` on a mutated table → `dataset.drift` |
| `F067-REQ-006` | FR-F067-06 | api | HTTP scenarios use `constant-arrival-rate`, WebSocket sessions use `ramping-vus`; script diverging from its profile → `profile.script_mismatch` |
| `F067-REQ-007` | FR-F067-07 | api | read p95 500 ms, write p95 800 ms, read p99 1500 ms, ack p95 2000 ms, `achieved_rate_ratio` 0.99, broadcast p95 250 ms each evaluated over the hold window only |
| `F067-REQ-008` | FR-F067-08 | api | pool wait, pool in-use ratio, outbox lag and backlog drain, queue depth and age, replication lag, RSS slope, 5xx rate, dead letters, conflict rate each fail the run when breached |
| `F067-REQ-009` | FR-F067-09 | api | client metrics from the k6 summary, server metrics from `metrics.toml` range queries; an empty series → exit 2 `metric.absent` and status `failed` |
| `F067-REQ-010` | FR-F067-10 | api, accessibility | flag set accepted; exit 0 pass/skip, 1 fail/regressed/aborted, 2 usage/profile/dataset/metric, 3 role; `--dry-run` contacts nothing |
| `F067-REQ-011` | FR-F067-11 | api | preflight order enforced; six skip reason codes emitted with exit 0; `--require-env` converts each into exit 2 |
| `F067-REQ-012` | FR-F067-12 | e2e | `gates.yml` unreferenced and no pull-request trigger; scheduled and dispatch runs recognised; milestone gate reports `release.scale_missing`, `release.scale_stale`, `release.scale_failed` |
| `F067-REQ-013` | FR-F067-13 | api | run directory holds the eight required files under the `run_id` format; tracked and untracked sets match `testing/evidence/README.md` |
| `F067-REQ-014` | FR-F067-14 | api | median-of-three reference; four comparison rules; absolute breach fails at once; first regression unconfirmed, second confirmed |
| `F067-REQ-015` | FR-F067-15 | api | promotion needs three consecutive passes and maintainer role or CI on `main`; superseded baseline archived; otherwise exit 3 writing nothing |
| `F067-REQ-016` | FR-F067-16 | frontend | `index.json` capped at 30 per profile and dataset; `report.md` carries six sections and table header cells |
| `F067-REQ-017` | FR-F067-17 | api | advisory lock plus lock file; second run → `concurrent_run`; lost lock or dead k6 → `aborted` at exit 1, excluded from the reference set |
| `F067-NFR-001` | NFR-F067-01 | performance | `--dry-run` < 200 ms; preflight < 35 s; evaluation and report < 10 s; 8-hour stream rendered < 60 s under 256 MiB |
| `F067-NFR-002` | NFR-F067-02 | database, api | checksums reproduce across machines and PostgreSQL 18 patch versions; ramp samples excluded; partial run is `aborted`; `run.exists` refuses an overwrite |
| `F067-NFR-003` | NFR-F067-03 | database, accessibility | synthetic data only on `@load.invalid`; production-allowlist host refused; `LOAD_ENV_TOKEN` absent from every evidence file |
| `F067-NFR-004` | NFR-F067-04 | api | commit, image digests, PostgreSQL settings, dataset hash, and k6 command line recorded; gate counters emitted |
| `F067-NFR-005` | NFR-F067-05 | accessibility | `--json` emits only the result document; verdict words present without color; exit codes separate outcomes; `report.md` is plain Markdown |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F067/`.
