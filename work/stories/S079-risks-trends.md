---
id: S079
type: story
status: planned
parent_epic: E008
parent_feature: F040
depends_on: [F040]
owned_paths: [crates/domain/src/ai-insights/**, crates/persistence/src/ai-insights/**, services/api/src/ai-insights/**, services/worker/src/ai-insights/**, apps/web/src/features/ai-insights/**, services/api/migrations/*_ai-insights_*.sql, testing/features/F040/**]
feature_flag: F040_FEATURE
branch: s079-risks-trends
started_at: null
finished_at: null
---

# S079 — Risks and trends

## Identity

- Parent feature: `F040` AI insights/automation
- Owner: platform
- Branch: `s079-risks-trends`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7; `docs/capability-contracts.md` row F040
- Child tasks: `T157` evidence-backed insight jobs, `T158` approval gate

## Vertical slice

As a program manager, I want to scan the work I can see and get ranked insights about schedule risk, stalled items, over-allocation, missing data, throughput trends, and approval bottlenecks, where each insight names the exact records, versions, and timestamps it came from, and where any change the assistant suggests is held in a gate until I confirm it, so that I can trust what I read and nothing changes behind my back.

## Requirements

- **SR-S079-01:** `POST /api/v1/ai/insights/scan` accepts a workspace or sheet-id scope, returns `202 { scan_id, status: "queued", detectors, estimated_records }`, records the request through `AiScanRepository::create_scan_with_detectors` as one `ai_scans` row with its `ai_scan_scope_sheets` and `ai_scan_detectors` children, enqueues `ai-insights.scan`, and rejects a scope estimated above 20,000 records with `400 invalid` `scope_too_large`; the response still carries `detectors` as a JSON array (covers FR-F040-01, FR-F040-15).
- **SR-S079-02:** The six detectors `schedule_risk`, `stalled_work`, `overallocation`, `missing_data`, `throughput_trend`, and `approval_bottleneck` produce deterministic candidates from the F039 permission-filtered retrieval reader, each carrying its threshold metrics and a `detector_version` (FR-F040-02, NFR-F040-02).
- **SR-S079-03:** Persisting an insight writes at least one `ai_insight_evidence` row with `source_kind`, `source_id`, `source_version`, `observed_value`, `observed_at`, and a server-generated `deep_link` in the same `UnitOfWork` transaction as the insight through `InsightRepository::insert_with_evidence`; those rows are the only storage of the cited records and `evidence_count > 0` is a database check over the derived count (FR-F040-03).
- **SR-S079-04:** Narration binds by index only: an `evidence_indexes` entry outside the candidate range, or any UUID in model text that is not in the retrieval set, discards the whole insight, suppresses `ai-insight.generated.v1`, and writes `ai-insight.evidence-rejected` (FR-F040-04, FR-F040-16).
- **SR-S079-05:** Fingerprint dedupe runs in `InsightRepository::upsert_by_fingerprint` and updates an existing `open` insight's `occurrence_count`, `last_seen_at`, `severity`, and `confidence` instead of inserting a second row, enforced by the unique index on `(tenant_id, fingerprint) where status = 'open'` (FR-F040-05).
- **SR-S079-06:** `GET /api/v1/ai/insights` filters by `kind`, `severity`, `status`, `sheet_id`, `since`, and `scan_id`, pages by cursor, sorts by severity then `last_seen_at`, and omits any insight whose evidence includes a record the caller cannot read (FR-F040-06, NFR-F040-01).
- **SR-S079-07:** `GET /api/v1/ai/insights/{id}` returns confidence, uncertainty note, `computed_at`, `detector_version`, `model`, `prompt_version`, token usage, and the ordered evidence list; a foreign-tenant id returns `404 not_found` (FR-F040-07).
- **SR-S079-08:** `POST /api/v1/ai/insights/{id}/dismiss` honours `If-Match`, publishes `ai-insight.dismissed.v1`, and for `scope: "kind_for_scope"` sets `suppressed_until = now + 30 days` so later scans skip that fingerprint (FR-F040-08).
- **SR-S079-09:** The `ai_actions` gate exists before any assisted action can run: an action reaches `confirmed` only through `POST /api/v1/ai/actions/{id}/confirm` with `workflow-editor`, a `user` principal, `If-Match`, and a matching `preview_hash`; hash mismatch and expiry both return `409 conflict`, and `POST /api/v1/ai/actions/{id}/reject` publishes `ai-action.rejected.v1` (FR-F040-11, FR-F040-14).
- **SR-S079-10:** `/insights` and `/insights/:insightId` render list, detail, evidence table with deep links, dismiss dialog, loading, empty, denied, error, and rate-limited states, with severity as text plus a labelled icon (FR-F040-17, NFR-F040-03).

## Surfaces

- Infrastructure/container: nightly scan schedule at 02:00 tenant-local registered in the worker scheduler; the F048 `ai_insights` entitlement checked at the API boundary
- Data access: `crates/persistence/src/ai-insights/{mod.rs, scan_repository.rs, insight_repository.rs, action_repository.rs}` hold every SQL statement for this slice — `AiScanRepository` owns `ai_scans`, `ai_scan_scope_sheets`, and `ai_scan_detectors`; `InsightRepository` owns `ai_insights` and `ai_insight_evidence`; `AiActionRepository` owns `ai_actions` and `ai_action_targets`. The detectors, `narrator.rs`, `service.rs`, `gate.rs`, the `services/api/src/ai-insights` handlers, and the `scan.rs`/`expiry.rs` jobs depend on those traits and contain no `sqlx::query*` call or connection; insight-plus-evidence and dismissal-plus-suppression writes run in one `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/ai-insights/{mod.rs, insight.rs, evidence.rs, fingerprint.rs, narrator.rs, safety.rs, errors.rs, service.rs, detectors/{mod.rs, schedule_risk.rs, stalled_work.rs, overallocation.rs, missing_data.rs, throughput_trend.rs, approval_bottleneck.rs}, action.rs, gate.rs}`; `services/api/src/ai-insights/{mod.rs, routes.rs, handlers_scan.rs, handlers_insight.rs, handlers_action.rs, dto.rs}`; `services/worker/src/ai-insights/{mod.rs, scan.rs, expiry.rs}`
- Data/migration: `services/api/migrations/<ts>_ai-insights_create_tables.sql` creating `ai_scans`, `ai_scan_scope_sheets`, `ai_scan_detectors`, `ai_insights`, `ai_insight_evidence`, `ai_actions`, `ai_action_targets`, `ai_action_runs`, and `ai_action_run_targets` with the foreign keys, closed-enum checks, and indexes in F040 section 4
- React/UI: `apps/web/src/features/ai-insights/{InsightsPage.tsx, InsightFilters.tsx, InsightCard.tsx, SeverityBadge.tsx, ScanDialog.tsx, InsightDetail.tsx, EvidenceTable.tsx, DismissDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/ai_insights.rs`; the F039 provider stub at `testing/harness/ai/provider_stub.rs` with scripted narrations and forced errors; a private sheet visible only to the manager for the permission-filtering cases

## TDD harness

- Test path: `testing/features/F040/{requirements,api,database,frontend}/`
- Feature flag: `F040_FEATURE`
- Targeted command: `cargo xtask test-feature F040`
- Full command: `cargo xtask test-all`
- First failing tests: `scan_rejects_scope_over_twenty_thousand_records`, `schedule_risk_flags_rows_due_within_seven_days`, `insight_requires_at_least_one_evidence_row`, `out_of_range_evidence_index_discards_insight`, `model_text_with_foreign_uuid_discards_insight`, `rescan_same_fingerprint_increments_occurrence_count`, `insight_hidden_when_evidence_row_unreadable`, `dismiss_kind_for_scope_suppresses_for_thirty_days`, `confirm_requires_human_principal`, `scan_detector_row_resumes_after_restart`, `duplicate_detector_row_rejected`

## Exit criteria

- [ ] Requirement tests SR-S079-01 through SR-S079-10 written first and observed failing
- [ ] Tasks T157 and T158 complete and wired through the API router and worker registry
- [ ] Unit, API, database, React, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/ai-insights/routes.rs` mounted in `services/api/src/router.rs` at `/api/v1/ai/insights` and `/api/v1/ai/actions`; `services/worker/src/ai-insights/scan.rs` and `expiry.rs` registered in `services/worker/src/registry.rs`
- [ ] Handoff evidence recorded in the F040 ticket
