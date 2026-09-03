# F034 requirements cases

Feature: Workload/actuals. Flag `F034_FEATURE`. Every case maps to a ticket requirement ID and names the lane that proves it. Seed: `testing/fixtures/workload.rs` (Ana over-allocated in the week of 2026-10-12, `Design API` with 4 days of float, Ben as a reassign candidate, one colliding external entry, tenant B twin), clock `2026-09-03T00:00:00Z`.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F034-REQ-001` | FR-F034-01 | api, performance | workload for a week range → row per resource and period with `available_hours`, `allocated_hours`, `actual_hours`, `utilization_pct`, `status` and totals; 501 resources or 183 days → 400 `invalid` |
| `F034-REQ-002` | FR-F034-02 | api, database | `capacity.computed.v1` for Ana's over-allocated week → one `workload_conflicts` row, `over_hours` 6, `allocation_ids` recorded, `workload-conflict.detected.v1` published once; capacity raised → `resolved` with `resolved_at` |
| `F034-REQ-003` | FR-F034-03 | api | conflicts list pages open and resolved and returns `shift_within_float` for `Design API` (float 4 d) and up to three `reassign_to` candidates with `remaining_hours ≥ over_hours` |
| `F034-REQ-004` | FR-F034-04 | api, database | native entry with `hours` 6.25 on today → 201 with `source: native` and `cost_snapshot`; 0.1 h, 24.25 h, a future date, or a daily total above 24 h → 400 `invalid` with `field_errors.hours` |
| `F034-REQ-005` | FR-F034-05 | api | own entry inside 30-day lock → patched with `If-Match`; day 31 → 403 `denied`; `resource-admin` → allowed; patch of an external entry → 409 `conflict` `code_detail: external_entry` |
| `F034-REQ-006` | FR-F034-06 | api, performance | import of 2,000 entries → `{ created, updated, pending_reconciliation, rejected }`; replay of the same `(source_system, external_id)` updates instead of duplicating; one bad row rejects by index only |
| `F034-REQ-007` | FR-F034-07 | api, database | external hours matching `(resource_id, row_id, entry_date)` of a native entry → `reconciliation_state: pending`, excluded from `actual_hours`; no native row is modified or deleted |
| `F034-REQ-008` | FR-F034-08 | api, e2e | `keep_native` → external `rejected`; `accept_external` → native `superseded`, external `accepted`; `sum` → both count; each writes audit and `time-entry.reconciled.v1`; non-pending entry → 409 `conflict` |
| `F034-REQ-009` | FR-F034-09 | api, frontend | row effort returns `planned_hours`, `actual_hours`, `pending_external_hours`, `remaining_hours`, `variance_hours`, `variance_pct`, `by_resource`; `include_children=true` rolls up F009 descendants; costs only for `resource-admin` |
| `F034-REQ-010` | FR-F034-10 | api, performance | `effort_summaries` for `row`, `project`, and `resource_period` refresh within 60 s of `time-entry.recorded.v1`, `time-entry.reconciled.v1`, `allocation.*.v1`, `capacity.computed.v1`, with `computed_at` and `source_versions`; queued newer event → `stale: true` |
| `F034-REQ-011` | FR-F034-11 | api, database | every mutation without `Idempotency-Key` → 400 `invalid`; create, patch, delete, each imported entry, each reconciliation, and each newly opened conflict write `audit_events` and publish the contracted event with `changed_fields` |
| `F034-REQ-012` | FR-F034-12 | api | tenant B ids on entries, conflicts, and effort → 404 `not_found`; viewer import or reconcile → 403 `denied`; non-viewer sees only their own workload row and entries |
| `F034-REQ-013` | FR-F034-13 | frontend, e2e | heatmap, conflicts panel with `Shift` and `Reassign` calling the F033 allocation API, time entry sheet, reconciliation queue, and the task-row planned versus actual panel render and act |
| `F034-REQ-014` | FR-F034-14 | database, api | an update of `reconciled_by`, `reconciled_at`, `resolution`, or `reason` once set is rejected by the trigger; a superseded native entry stays readable with `superseded_by` |
| `F034-NFR-001` | NFR-F034-01 | performance | 1,000 resources over 12 weeks p95 < 500 ms; conflict detection < 30 s after the capacity event; entry create p95 < 800 ms; 2,000-entry import < 5 s |
| `F034-NFR-002` | NFR-F034-02 | api, accessibility | cost fields filtered in the DTO layer; notes absent from log fields; import targeting a foreign resource rejected per entry; cross-tenant, viewer, self-only, and non-admin reconciliation negatives |
| `F034-NFR-003` | NFR-F034-03 | accessibility, frontend | heatmap cells expose utilization as text with `meter` semantics; status shown by text and icon; time sheet keyboard editable; dialogs trap focus; axe serious = 0 |
| `F034-NFR-004` | NFR-F034-04 | performance, api | summary and conflict jobs idempotent by `(scope_id, source_version)`, retried 3 times, dead-lettered with `last_error`; import atomic; spans carry the five ids; `workload_summary_lag_seconds` and `conflict_detection_ms` exported |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F034/`.
