# F067 — System scale and load validation harness

Feature-gated tests for `F067`, the composite scale gate behind `cargo xtask load-test <profile>`. Keep test code in this directory.

- Gate: `F067_FEATURE`
- Targeted: `cargo xtask test-feature F067`
- Full: `cargo xtask test-all`
- What is under test: the xtask `load` module, the profile and dataset schemas under `testing/load/**`, the k6 scripts, the threshold and comparison arithmetic, and the evidence written to `testing/evidence/F067/**`. The tests never drive the real load environment; they drive stubs and a `smoke`-scale dataset.
- Fixtures: `testing/fixtures/load.rs` (temporary repository tree with `testing/load/profiles/` and `testing/load/datasets/`; fake k6 v0.54.0 replaying recorded NDJSON summaries from `api/fixtures/k6/`; Prometheus stub returning empty, partial, and complete series; readiness stub returning 200, 503, and a timeout; throwaway PostgreSQL 18 database per worker for the seed generator; recorded run directories for pass, fail, skip, abort, and two-run regression sequences; a synthetic 8-hour stream of 2.9 million samples; fixed seed `42`, fixed clock `2026-09-03T00:00:00Z`, fixed commit `9454136e0f1a`, UTC).
- Parallel isolation: one temporary repository root, one database, and one advisory-lock key per test worker, so the run-lock tests do not collide.
- Honest negative controls: F067 owns no route, table, migration, or React module. The `api` lane therefore tests the xtask module and asserts no `openapi/v1.json` operation carries `x-opshub-feature: F067`; the `database` lane tests the seed generator against a throwaway database and asserts `services/api/migrations/` gains no `*_load_*.sql`; the `frontend` lane asserts `apps/web/src/features/load/` is never created and checks the one reader-facing artifact, `report.md`.
- Lanes: `requirements/` (traceability for every FR and NFR id), `api/`, `database/`, `frontend/`, `e2e/`, `accessibility/` (CLI output contract), `performance/` (the harness's own cost budgets); each `cases.md` lists the test names implemented in that lane and the FR/NFR ids they prove.
