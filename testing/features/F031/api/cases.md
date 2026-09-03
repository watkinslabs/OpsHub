# F031 api cases

File: `testing/features/F031/api/{portfolio_tests.rs,rollup_tests.rs,permission_tests.rs}`. Flag `F031_FEATURE`.

- `portfolio_create_returns_version_one` — FR-F031-01: POST `/api/v1/portfolios` as admin returns 201, `version: 1`, `rollup_state: never`.
- `portfolio_duplicate_name_conflicts` — FR-F031-01: same name in the same workspace, different case → 409 `conflict`, `field_errors.name`.
- `portfolio_list_pages_filters_sorts` — FR-F031-02: 120 portfolios, `limit=50`, three pages; `workspace_id` filter; `sort=updated_at`.
- `portfolio_stale_version_conflicts` — FR-F031-03: `If-Match: 2` against version 3 → 409 with `current_version: 3`, no write.
- `portfolio_unknown_measure_key_invalid` — FR-F031-05: `measure_mappings.velocity` → 400 with `field_errors.measure_mappings`.
- `portfolio_replace_projects_records_diff` — FR-F031-04: PUT replaces 3 with 2 → audit diff `added: []`, `removed: [id]`, `portfolio.updated.v1`.
- `portfolio_replace_projects_rejects_foreign_sheet` — FR-F031-04: tenant B sheet id → 400 `field_errors.projects[1]`.
- `portfolio_replace_projects_over_limit_invalid` — FR-F031-04: 501 IDs → 400 `field_errors.projects = "too_many"`.
- `refresh_enqueues_and_acks_under_two_seconds` — FR-F031-06: POST refresh → 202 `{ job_id, requested_version }` within 2 s, `rollup_state: refreshing`.
- `refresh_while_refreshing_conflicts` — FR-F031-06: second POST during a running job → 409 `conflict`.
- `rollup_rows_preserve_source_ids_and_versions` — FR-F031-07, FR-F031-08: three rows with `project_sheet_id`, `source_versions.sheet_version`, `source_versions.baseline_id`, `computed_at`.
- `rollup_computes_schedule_and_budget_variance` — FR-F031-07: planned finish 5 days after baseline → `variance_days: 5`; actual 120 of 100 → `variance_pct: 20`.
- `rollup_marks_missing_column_measure` — FR-F031-05: project lacking mapped `budget_actual` → `budget.state: missing`, `status.state: ok`.
- `rollup_marks_deleted_project_missing` — FR-F031-14: soft-deleted member → `state: missing`, `reason: project_deleted`.
- `rollup_hides_denied_project_for_viewer` — FR-F031-09: viewer read → "Merger" row `state: denied`, null name, `excluded_project_count: 1`, totals exclude it.
- `rollup_reports_stale_after_threshold` — FR-F031-09: `stale_after_seconds: 60`, clock advanced 61 s → `stale: true`.
- `scheduled_refresh_skips_unchanged_portfolio` — FR-F031-10: tick with no member change → job run records `skipped`; after a row edit → refresh runs.
- `refresh_failure_retries_then_dead_letters` — NFR-F031-04: executor failing 4 times → dead letter, `rollup_state: failed`, `last_refresh_error` set.
- `portfolio_viewer_mutation_denied` — FR-F031-12: viewer POST/PATCH/PUT/refresh → 403 `denied`.
- `portfolio_cross_tenant_not_found` — FR-F031-12: tenant B on all seven routes → 404.
- `cross_tenant_all_routes_not_found` — NFR-F031-02: tenant B admin against tenant A IDs → 404 everywhere, no audit read event.
- `viewer_all_mutations_denied` — NFR-F031-02: viewer on every mutation route → 403 and no audit mutation row.
- `viewer_rollup_excludes_denied_project_from_totals` — NFR-F031-02: totals budget for viewer equals admin totals minus "Merger".
- `snapshot_stores_no_values_for_unreadable_project` — NFR-F031-02: `portfolio_rollups.rows` for a project denied to the tenant system actor has `state: denied` and no measure values.
- `guest_link_cannot_read_rollup` — NFR-F031-02: F036 guest link token on `/rollup` → 404.
- `mutation_writes_audit_and_outbox` — FR-F031-11: each mutation → one `audit_events` row and one `outbox_events` row.
- `request_span_carries_ids` — NFR-F031-04: span has `tenant_id`, `portfolio_id`, `job_id`, `correlation_id`.

Evidence: JUnit output and request logs under `testing/evidence/F031/api/`.
