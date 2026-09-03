---
id: T157
type: task
status: planned
parent_epic: E008
parent_feature: F040
parent_story: S079
depends_on: [S079]
owned_paths: [services/api/migrations/*_ai-insights_*.sql, crates/domain/src/ai-insights/**, services/api/src/ai-insights/**, services/worker/src/ai-insights/**, testing/features/F040/api/**, testing/features/F040/database/**]
feature_flag: F040_FEATURE
branch: t157-evidence-backed-insight-jobs
started_at: null
finished_at: null
---

# T157 — Evidence-backed insight jobs

## Identity

- Parent story: `S079` Risks and trends
- Owner: platform
- Branch: `t157-evidence-backed-insight-jobs`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 7; `docs/capability-contracts.md` row F040

## Objective

Create the `ai-insights` schema and implement the scan job: six deterministic detectors reading through the F039 permission-filtered retrieval reader, index-bound narration, evidence persistence, fingerprint dedupe and suppression, and the insight read and dismiss routes.

## Specification

- Owned paths: `services/api/migrations/<ts>_ai-insights_create_tables.sql` and `.down.sql`; `crates/domain/src/ai-insights/{mod.rs, insight.rs, evidence.rs, fingerprint.rs, narrator.rs, errors.rs, service.rs, detectors/{mod.rs, schedule_risk.rs, stalled_work.rs, overallocation.rs, missing_data.rs, throughput_trend.rs, approval_bottleneck.rs}}`; `services/api/src/ai-insights/{mod.rs, routes.rs, handlers_scan.rs, handlers_insight.rs, dto.rs}`; `services/worker/src/ai-insights/{mod.rs, scan.rs, expiry.rs}`
- Contract/input: `ScanRequest { scope: { workspace_id } | { sheet_ids: [uuid] }, detectors?: [String], since?: timestamptz }`; list query `{ cursor?, limit?, kind?, severity?, status?, sheet_id?, since?, scan_id?, sort? }`; `DismissRequest { reason, scope: "this" | "kind_for_scope" }` with `If-Match: <version>`; narration response schema `{ index, title, summary, severity, confidence, uncertainty_note, evidence_indexes: [u32] }` requested through the F039 provider boundary.
- Output/behavior: routes `POST /api/v1/ai/insights/scan` (202 with `scan_id`, `400 invalid` `scope_too_large` above 20,000 estimated records), `GET /api/v1/ai/insights`, `GET /api/v1/ai/insights/{id}`, `POST /api/v1/ai/insights/{id}/dismiss`. `detectors/*.rs` implement `Detector::candidates` with the thresholds in F040 FR-F040-02 and emit `Candidate { key, metrics, evidence }`; `narrator.rs::bind` accepts evidence only by index into that candidate set and discards the insight on an out-of-range index or a UUID in model text that is absent from the retrieval set, writing audit `ai-insight.evidence-rejected`; `fingerprint.rs` computes `sha256(kind || detector_version || scope_id || sorted evidence source ids)`; persistence writes the insight and its `ai_insight_evidence` rows in one transaction with `evidence_count > 0`, publishes `ai-insight.generated.v1` once per new fingerprint and only increments `occurrence_count`/`last_seen_at` on repeats; list reads drop any insight with an unreadable evidence record; dismiss publishes `ai-insight.dismissed.v1` and sets `suppressed_until = now + 30 days` for `kind_for_scope`; `scan.rs` checkpoints per detector so a restart resumes, `expiry.rs` marks insights past `expires_at`; DDL for the four tables, checks, and indexes from F040 section 4.
- Dependencies: F039 retrieval reader and provider boundary; F048 `ai_insights` entitlement; F012 dependencies, F016 comments, F020 approvals, F034 allocations as detector inputs; F004 job transport and outbox.
- Feature flag: `F040_FEATURE` gates the routes and both jobs; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F040/api/scan_tests.rs::scan_rejects_scope_over_twenty_thousand_records`, `::scan_returns_queued_scan_id`, `::scan_resumes_after_restart_without_duplicates`; `testing/features/F040/api/detector_tests.rs::schedule_risk_flags_rows_due_within_seven_days`, `::stalled_work_needs_fourteen_quiet_days`, `::overallocation_uses_iso_weeks_within_four_weeks`, `::missing_data_requires_ten_percent_null`, `::throughput_trend_needs_five_nonzero_weeks`, `::approval_bottleneck_flags_three_day_pending`; `testing/features/F040/api/evidence_tests.rs::insight_requires_at_least_one_evidence_row`, `::out_of_range_evidence_index_discards_insight`, `::model_text_with_foreign_uuid_discards_insight`, `::evidence_records_source_version_and_deep_link`; `testing/features/F040/api/insight_read_tests.rs::rescan_same_fingerprint_increments_occurrence_count`, `::insight_hidden_when_evidence_row_unreadable`, `::foreign_tenant_insight_returns_not_found`, `::dismiss_kind_for_scope_suppresses_for_thirty_days`; `testing/features/F040/database/migration_tests.rs::ai_insights_tables_exist_with_constraints`, `::evidence_count_check_rejects_zero`, `::open_fingerprint_unique_per_tenant`, `::rollback_drops_ai_insights_tables`
- Targeted command: `cargo xtask test-feature F040`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/ai_insights.rs`; the F039 provider stub at `testing/harness/ai/provider_stub.rs` with scripted narrations keyed by candidate hash; fixed clock `2026-09-03T00:00:00Z`; a private sheet readable only by the manager

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes and both jobs registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes and no path overlaps the F039 `ai-assist` module
- [ ] File limit, lint, and audit-event gates pass
- [ ] Handoff evidence recorded in S079
- [ ] `finished_at` recorded
