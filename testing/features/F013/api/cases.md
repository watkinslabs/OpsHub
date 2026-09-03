# F013 api cases

File: `testing/features/F013/api/{view_tests.rs,view_rows_tests.rs,view_share_tests.rs}`. Flag `F013_FEATURE`.

- `view_create_returns_version_one` — FR-F013-01: POST `/api/v1/views` as viewer returns 201, `version: 1`, `owner_id` = actor.
- `view_limit_100_per_sheet` — FR-F013-01: 100 views exist; the next POST → 400 `invalid`, `field_errors.sheet_id = "view_limit"`.
- `view_filter_rejects_type_mismatch` — FR-F013-02: `gt` on a text column and `contains` on a number column → 400 `field_errors.settings.filter`.
- `view_filter_rejects_51_leaves` — FR-F013-02: nested `and`/`or` with 51 leaves → 400; 50 leaves → 201.
- `view_sorts_capped_at_five` — FR-F013-03: 6 sorts → 400; unknown `group_by` → 400.
- `card_view_requires_select_lane_column` — FR-F013-04: lane on `Title` text → 400; lane on `Status` select → 201.
- `calendar_and_timeline_settings_validated` — FR-F013-04: calendar without date column → 400; timeline with `Start`/`End` datetime and `zoom=week` → 201; `gantt` block stored untouched.
- `view_rows_apply_filter_sort_group` — FR-F013-05: `Status in [Doing, Done]`, sort `Due desc`, group `Owner` → rows grouped then sorted; only visible and primary columns present.
- `view_rows_exclude_hidden_rows` — FR-F013-05, NFR-F013-02: viewer cannot read group `Restricted`; view rows never contain them even when the filter matches.
- `view_rows_page_limit_500` — FR-F013-05: `limit=501` → 400; 1,200 matching rows → three pages of 500, 500, 200.
- `calendar_rows_bounded_by_range` — FR-F013-06: `range_start=2026-09-01&range_end=2026-09-30` returns rows whose `Due` or `Start`/`End` intersect September in `America/New_York`.
- `range_over_366_days_invalid` — FR-F013-06: 367-day range → 400 `field_errors.range_end`.
- `view_default_toggle_clears_previous` — FR-F013-08: PATCH `is_default: true` on view B → view A `is_default` false in the same transaction.
- `view_stale_version_conflicts` — FR-F013-08: `If-Match: 2` against version 3 → 409 with `current_version: 3`, no write.
- `viewer_cannot_patch_sheet_view` — FR-F013-08: non-owner viewer PATCH on a `sheet` view → 403 `denied`; `sheet-editor` → 200.
- `view_default_delete_invalid` — FR-F013-09: DELETE on default → 400 `field_errors.is_default`; DELETE other → 204, GET → 404, shares `revoked_at` set.
- `view_share_link_expires_within_30_days` — FR-F013-10: `expires_at` 30 days → 201 with `/public/views/{token}`; 31 days → 400 `field_errors.expires_at`.
- `view_share_non_owner_denied` — FR-F013-10: editor who is not owner → 403; no `view_shares` row.
- `view_list_hides_unshared_private` — FR-F013-11: user B lists views → own private, sheet views, group-shared; user A's private absent and GET by ID → 404.
- `group_share_visible_to_member` — FR-F013-11: share to group → both members see the view; a non-member does not.
- `view_mutation_writes_audit_and_outbox` — FR-F013-12: create, update, delete, share → one `audit_events` row and one matching `view.*.v1` outbox row each.
- `view_idempotent_replay_returns_original` — FR-F013-12: same `Idempotency-Key` twice → one view, identical body; different body → 409.
- `view_cross_tenant_not_found` — NFR-F013-02: tenant B GET/PATCH/DELETE/rows/share on tenant A view → 404 on every route.
- `link_actor_cannot_mutate` — NFR-F013-02: token actor GET view and rows → 200; PATCH, DELETE, share, cell patch, reschedule → 403.
- `expired_link_not_found` — NFR-F013-02: token past `expires_at` or with `revoked_at` → 404.
- `export_with_view_id_matches_rows` — FR-F013-14: `POST /api/v1/exports { view_id }` → CSV row set equals view rows for the same actor.
- `view_request_span_and_metrics` — NFR-F013-04: span has `tenant_id`, `sheet_id`, `view_id`, `correlation_id`; bad filter increments `views_filter_compile_errors_total`.

Evidence: JUnit output and request logs under `testing/evidence/F013/api/`.
