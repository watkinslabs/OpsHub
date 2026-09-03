# F015 api cases

File: `testing/features/F015/api/{template_tests.rs,manifest_tests.rs,provision_tests.rs,baseline_tests.rs,variance_tests.rs}`. Flag `F015_FEATURE`.

- `template_create_and_copy_builtin` — FR-F015-01, FR-F015-05: POST as admin → 201 version 1; `copy_from` built-in `pmo` → tenant-owned draft with the same manifest.
- `template_duplicate_name_conflicts` — FR-F015-01: same name, different case → 409 `field_errors.name`.
- `template_list_filters_category_and_builtin` — FR-F015-05: `category=it&include_builtin=true` returns the built-in plus tenant templates; tenant B templates absent.
- `version_publish_is_immutable` — FR-F015-04: publish draft → `published_at` set, `template.published.v1`; second manifest on the same version → 409 `immutable`; new draft gets `version_number` 2.
- `manifest_rejects_dangling_key` — FR-F015-02: dependency `successor_key: "qa-9"` with no such row → 400 `field_errors.manifest.sheets[0].dependencies[2]`.
- `manifest_rejects_over_limits` — FR-F015-03: 21 sheets → `sheets`; 5,001 rows → `default_rows`; 2,097,153 bytes → `manifest_bytes`.
- `manifest_rejects_unknown_column_type` — FR-F015-02: column type `geo` → 400 with the column path.
- `builtin_seed_validates` — FR-F015-05: all ten built-in manifests pass `validate_manifest` and contain a sheet, a dependency, a form, and a card view.
- `builtin_mutation_denied` — FR-F015-14: PATCH or version create on a built-in → 403 `denied`.
- `template_cross_tenant_not_found` — FR-F015-14: tenant B GET/versions/provision → 404.
- `provision_returns_202_within_budget` — FR-F015-06: run `queued`, `id` returned, elapsed < 2 s, job recorded on `templates.provision`.
- `provision_rejects_draft_version` — FR-F015-06: draft `version_id` → 400 `not_published`.
- `provision_editor_denied` — FR-F015-14: sheet-editor without portfolio-admin → 403, no run row.
- `provision_run_completes_all_steps` — FR-F015-07: 120-row manifest → 2 sheets, 120 rows with dates `start + offset` on `Standard`, 34 dependencies, 1 card view, 1 draft form; `project.provisioned.v1` with `created_ids`.
- `provision_step_is_idempotent_on_replay` — NFR-F015-04: redelivering the job after the `rows` step → no duplicate rows, run completes.
- `provision_failure_rolls_back` — FR-F015-08: failing-dependency manifest → 3 attempts, status `failed`, created sheets soft-deleted, `provisioning.failed.v1` step `dependencies`.
- `provision_records_skipped_modules` — FR-F015-07: manifest with `workflows` and `dashboard` → steps `skipped` with `module_unavailable`.
- `run_poll_cross_workspace_not_found` — FR-F015-09: user outside workspace `Ops` GET run → 404.
- `baseline_capture_snapshots_all_rows` — FR-F015-10: 50 rows → 50 `baseline_rows`, `row_count` 50, `baseline.captured.v1`.
- `baseline_capture_excludes_deleted_rows` — FR-F015-10: soft-deleted row absent from the snapshot.
- `baseline_limit_twenty_conflicts` — FR-F015-10: 21st capture → 409 `field_errors.name = "limit"`.
- `baseline_duplicate_name_conflicts` — FR-F015-10: same name on the same sheet → 409.
- `baseline_editor_capture_denied` — FR-F015-14: editor POST → 403.
- `baseline_cross_tenant_not_found` — FR-F015-14: tenant B list/variance → 404.
- `baseline_idempotent_replay_returns_original` — FR-F015-13: same key twice → one baseline; different body → 409.
- `variance_reports_slipped_added_removed` — FR-F015-12: reschedule one row, add one, delete one → statuses `slipped`, `added`, `removed`; totals match.
- `variance_uses_working_calendar_days` — FR-F015-12: Friday to next Wednesday → `finish_variance_days` 3, not 5.
- `variance_measure_deltas_and_totals` — FR-F015-12: `effort` 10 → 14 gives `delta` 4; `max_finish_variance_days` is the largest slip.
- `mutations_write_audit_and_outbox` — FR-F015-13: template, version, provision, baseline mutations each → one audit and one outbox row; provisioning steps carry the run `correlation_id`.
- `request_span_carries_template_ids` — NFR-F015-04: spans have `tenant_id`, `template_id`, `run_id`, `correlation_id`; `provisioning_run_duration_ms` observed.

Evidence: JUnit output and request logs under `testing/evidence/F015/api/`.
