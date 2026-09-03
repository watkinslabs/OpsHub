# F056 api cases

File: `testing/features/F056/api/{pivot_tests.rs,output_tests.rs,aggregate_tests.rs,golden_tests.rs}`. Flag `F056_FEATURE`.

- `pivot_create_returns_version_one` — FR-F056-01: POST `/api/v1/pivots` as entitled editor returns 201 and `version: 1`.
- `pivot_bucket_on_text_column_invalid` — FR-F056-02: `bucket: month` on text column → 400 `field_errors.row_dimensions[0].bucket = not_a_date_column`.
- `pivot_avg_on_text_column_invalid` — FR-F056-03: `avg` on select column → 400 `field_errors.measures[0].aggregate = type_mismatch`.
- `pivot_missing_entitlement_denied` — FR-F056-04: unentitled tenant → 403 `denied`, `field_errors.entitlement = pivot` on all seven routes.
- `pivot_viewer_create_denied` — NFR-F056-02: `report-viewer` POST/PATCH/DELETE/compute → 403 `denied`.
- `pivot_cross_tenant_not_found` — FR-F056-04: tenant B on tenant A pivot → 404 on every route.
- `pivot_stale_version_conflicts` — FR-F056-11: `If-Match: 2` against version 3 → 409 with `current_version: 3`.
- `pivot_idempotent_replay_returns_original` — FR-F056-11: same key twice → one row; different body → 409.
- `pivot_mutation_writes_audit_and_outbox` — FR-F056-11: create/update/delete → audit row and `pivot.updated.v1`.
- `compute_enqueues_and_returns_queued` — FR-F056-05: 202 in < 2 s, `queued` output, one job on `pivots.compute`.
- `compute_while_running_conflicts` — FR-F056-05: second compute during `running` → 409 `conflict`.
- `compute_failed_publishes_error_code` — FR-F056-07: deleted source → `failed`, `source_deleted`, `pivot.computed.v1` status failed.
- `aggregate_excludes_hidden_rows` — FR-F056-06: report hiding 300 rows → `row_count` 1,700; sums exclude hidden amounts.
- `aggregate_month_bucket_uses_tenant_timezone` — FR-F056-02: rows at 2026-03-08 03:30 UTC bucket to March in `America/New_York`.
- `aggregate_count_distinct_and_decimal_sum` — FR-F056-03: `count_distinct` over person column; `sum` exact to 4 decimals.
- `aggregate_source_too_large` — FR-F056-07: 100,001 visible rows → `SourceTooLarge`.
- `outputs_prune_to_twenty` — FR-F056-08: 21 computes → 20 outputs, oldest removed.
- `output_stale_after_source_edit` — FR-F056-09: bump sheet version → `stale: true`.
- `materialize_is_idempotent` — FR-F056-10: replay same key → same `sheet_id`.
- `scheduler_skips_active_output` — FR-F056-12: hourly pivot with `running` output not enqueued at `:00`.
- `golden_pivots_match_sql_reference` — FR-F056-06: 12 golden definitions match SQL-computed cells.
- `compute_job_retries_then_dead_letters` — NFR-F056-04: transient failure retried 3 times, then dead letter and `pivot_compute_failures_total` incremented.

Evidence: JUnit output and request logs under `testing/evidence/F056/api/`.
