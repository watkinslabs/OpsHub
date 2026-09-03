# F023 api cases

File: `testing/features/F023/api/{dashboard_tests.rs,grid_tests.rs,widget_data_tests.rs,refresh_tests.rs,sharing_tests.rs,permission_tests.rs}`. Flag `F023_FEATURE`.

- `dashboard_create_returns_version_one` — FR-F023-01: POST `/api/v1/dashboards` as editor → 201, `version: 1`, `widgets: []`.
- `dashboard_duplicate_name_conflicts` — FR-F023-01: same name, same folder → 409 `field_errors.name`.
- `widgets_overlap_rejected` — FR-F023-02: table at (0,0,6,4) and text at (3,2,6,2) → 400 `widgets[1].position`.
- `widgets_exceeding_forty_rejected` — FR-F023-02: 41 widgets → 400.
- `widgets_replace_keeps_cache_for_retained_ids` — FR-F023-02: PUT with same id → `widget_cache` row retained; omitted widget deleted.
- `widget_unknown_kind_rejected` — FR-F023-03: kind `gauge` → 400 `widgets[0].config`.
- `widget_config_validated_per_kind` — FR-F023-03: `text` with 8,001 chars, `image` without `alt`, `table` with `limit 201` → 400.
- `widget_data_unavailable_without_resolver` — FR-F023-04: `kpi` widget → `status unavailable`, `reason resolver_not_registered`.
- `widget_data_miss_enqueues_and_returns_computing` — FR-F023-05: first read → `computing`, one `dashboards.refresh-widget` job.
- `widget_data_stale_when_snapshot_advances` — FR-F023-05: report snapshot 12 → 13 → `status stale`.
- `widget_data_denied_for_restricted_source` — FR-F023-05: restricted viewer reads Risks-backed table → `denied`, `payload` absent.
- `widget_data_never_crosses_scope` — NFR-F023-02: editor's cached payload is not returned to the restricted viewer.
- `dashboard_refresh_acknowledged_with_count` — FR-F023-06: 202 with `widget_count 5` under 2 s.
- `dashboard_refresh_active_conflicts` — FR-F023-06: second refresh for the same scope → 409.
- `dashboard_refresh_isolates_widget_failure` — FR-F023-06, NFR-F023-04: image resolver fails → four widgets fresh, one error, `failed_count 1`.
- `refresh_job_dead_letters_after_four_failures` — FR-F023-11: injected failures → 3 retries then dead letter.
- `on_open_policy_enqueues_when_cache_old` — FR-F023-07: cache 61 s old → job; 30 s old → none.
- `interval_targets_recent_scopes_only` — FR-F023-07: scope unread for 25 h not refreshed.
- `refresh_override_longer_than_interval_invalid` — FR-F023-07: override 120 with interval 30 → 400.
- `dashboard_get_returns_cache_and_share_summary` — FR-F023-08: `cache_summary` per widget, `share_summary.shared_with_count 1`.
- `dashboard_list_includes_shared` — FR-F023-08: viewer with group share sees the dashboard.
- `share_link_guest_gets_denied_widget` — FR-F023-09: link guest → table `denied`, text `fresh`.
- `share_link_guest_cannot_mutate_or_refresh` — FR-F023-09: PUT widgets, PATCH, refresh → 403.
- `expired_share_link_not_found` — FR-F023-09: link past 30 days → 404.
- `dashboard_stale_version_conflicts` — FR-F023-10: `If-Match: 1` vs 2 → 409.
- `dashboard_delete_cascades_widgets_cache_links` — FR-F023-10: widgets `deleted_at` set, cache rows removed, `share-link.revoked.v1`.
- `dashboard_cross_tenant_not_found` — FR-F023-10: tenant B on every route → 404.
- `foreign_tenant_widget_data_not_found` — FR-F023-10: tenant B `GET /widgets/{id}/data` → 404.
- `dashboard_mutation_writes_audit_with_widget_diff` — FR-F023-11: PUT → audit `added`, `removed`, `moved` ids and `dashboard.updated.v1`.
- `dashboard_idempotent_replay_returns_original` — FR-F023-11: same key twice → one row; different body → 409.
- `dashboard_viewer_mutation_denied` — NFR-F023-02: viewer PUT/PATCH/DELETE/refresh → 403.
- `image_widget_requires_scanned_file` — NFR-F023-02: unscanned file → resolver `error`, no URL.
- `request_span_carries_dashboard_ids` — NFR-F023-04: span has `dashboard_id`, `widget_id`, `run_id`, `scope_key`.

Evidence: JUnit output and request logs under `testing/evidence/F023/api/`.
