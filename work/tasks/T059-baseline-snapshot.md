---
id: T059
type: task
status: planned
parent_epic: E003
parent_feature: F015
parent_story: S030
depends_on: [T058]
owned_paths: [crates/domain/src/templates/**, services/api/src/templates/**, testing/features/F015/api/**, testing/features/F015/database/**, testing/features/F015/performance/**]
feature_flag: F015_FEATURE
branch: t059-baseline-snapshot
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Capability contract: `docs/capability-contracts.md` row F015

# T059 — Baseline snapshot

## Identity

- Parent story: `S030` Baseline compare
- Owner: platform
- Branch: `t059-baseline-snapshot`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F015

## Objective

Implement baseline capture, listing, and the variance calculation over the sheet working calendar behind the three baseline routes.

## Specification

- Owned paths: `crates/domain/src/templates/{baseline.rs, variance.rs, service_baseline.rs}`, `services/api/src/templates/{handlers_baseline.rs, handlers_variance.rs}`
- Contract/input: `CaptureBaselineRequest { name, measures: [start|end|duration|effort|cost] }` with `Idempotency-Key`; list query `{ cursor?, limit? ≤ 100, sort? }`; variance query `{ cursor?, limit? ≤ 500, status? }`.
- Output/behavior: `POST /api/v1/sheets/{sheet_id}/baselines` requires `portfolio-admin`, resolves measure names to numeric or duration columns from the sheet schedule settings, runs one `INSERT INTO baseline_rows ... SELECT` from the F011 schedule read model, records `row_count`, emits `baseline.captured.v1`, and returns `201 BaselineResponse`; the 21st baseline returns `409 conflict`; `GET /api/v1/sheets/{sheet_id}/baselines` pages by `captured_at`; `GET /api/v1/baselines/{id}/variance` joins `baseline_rows` to current rows, computes `start_variance_days` and `finish_variance_days` with `working_days_between` on the sheet calendar, measure deltas, per-row `status` (`on_track`, `slipped`, `early`, `added`, `removed`), and `totals`; errors map per ticket section 4; metric `baseline_capture_rows`.
- Dependencies: T058 (run-created sheets used by the E2E path); F011 `read_schedule` and `working_days_between`; F006 row soft-delete state for `removed`.
- Feature flag: `F015_FEATURE`

## TDD

- Failing test first: `testing/features/F015/api/baseline_tests.rs::baseline_capture_snapshots_all_rows`, `::baseline_capture_excludes_deleted_rows`, `::baseline_limit_twenty_conflicts`, `::baseline_duplicate_name_conflicts`, `::baseline_editor_capture_denied`, `::baseline_cross_tenant_not_found`, `::baseline_idempotent_replay_returns_original`; `testing/features/F015/api/variance_tests.rs::variance_reports_slipped_added_removed`, `::variance_uses_working_calendar_days`, `::variance_measure_deltas_and_totals`; `testing/features/F015/database/baseline_tests.rs::baseline_rows_cascade_with_baseline`; `testing/features/F015/performance/baseline_bench.rs::baseline_capture_100k_under_30s`, `::variance_read_500_p95`
- Targeted command: `cargo xtask test-feature F015`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: sheet with 50 scheduled rows and effort/cost columns; 100,000-row generator with fixed seed; `Standard` calendar

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Capture and variance targets from NFR-F015-01 met in the performance lane
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S030
- [ ] `finished_at` recorded
