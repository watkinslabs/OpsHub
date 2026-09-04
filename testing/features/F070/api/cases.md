# F070 api cases

File: `testing/features/F070/api/{projection_tests.rs,registry_tests.rs,index_tests.rs,restore_tests.rs,purge_tests.rs,sweep_tests.rs,negative_tests.rs}`. Flag `F070_FEATURE`.

- `projector_upserts_entry_from_sheet_deleted` — FR-F070-03: `sheet.deleted.v1` produces one row keyed `(tenant_id, kind, item_id)` with title, parent, `source_event_id` and `source_version`.
- `projector_discards_older_source_version` — FR-F070-03: redelivering version 4 after version 7 leaves the row untouched; the upsert predicate is what rejects it, not application code.
- `projector_deletes_entry_on_restored_event` — FR-F070-03: `row.restored.v1` removes the entry; a restoration arriving before its deletion leaves no entry behind.
- `projector_records_folder_update_carrying_deleted_at` — FR-F070-03: `folder.updated.v1` with `deleted_at` in `changed_fields` projects a `folder` entry; the same event without it is ignored.
- `projector_drops_foreign_tenant_event` — FR-F070-11: an event whose `tenant_id` differs from the entry it would touch is dropped and counted, never applied.
- `rebuild_matches_incremental_projection` — NFR-F070-05, FR-F070-04: after a randomized delete/restore/out-of-order sequence the rebuilt rows equal the live rows apart from `projected_at` and `projection_epoch`.
- `rebuild_epoch_swap_is_atomic` — FR-F070-04: a reader during the rebuild sees either the whole old epoch or the whole new one, never a mixture.
- `registry_refuses_duplicate_kind_key` — FR-F070-05: two specs claiming `sheet` abort start-up with the offending module named.
- `registry_refuses_unknown_resource_key` — FR-F070-05: a spec whose resource key is absent from the authorization model aborts start-up.
- `registry_accepts_a_kind_declared_outside_this_module` — FR-F070-05: the test-double kind declared in another crate appears in the registry with no change under this feature's owned paths.
- `index_orders_by_deleted_at_then_entry_id` — FR-F070-01: 120 entries page by cursor with stable order across a concurrent delete.
- `index_filters_by_kind_workspace_person_and_date` — FR-F070-01: each filter narrows independently and in combination; `q` prefix-matches titles case-insensitively.
- `index_page_is_acl_joined_not_post_filtered` — FR-F070-02, NFR-F070-01: with 200 hidden and 60 visible entries, `limit=50` returns 50 visible rows and a cursor, proving the filter runs before paging.
- `index_reports_stale_past_the_120_second_bound` — FR-F070-01: holding the projector 121 seconds sets `stale: true` and `as_of` to the last applied event time.
- `index_rejects_limit_above_200` — FR-F070-01: `limit=201` returns 400 `invalid` with `field_errors.limit`.
- `restore_puts_sheet_back_and_publishes_restored` — FR-F070-06: the sheet, its rows and its groups return with their original ids, `item.restored.v1` is published, and the entry is gone.
- `restore_checks_destination_parent_acl` — FR-F070-06: the caller may read the row but lacks `create` on the destination folder, so restore returns 403 `denied` and nothing is written.
- `restore_under_deleted_parent_conflicts_with_parent_named` — FR-F070-07: 409 `conflict` code `parent_deleted` with the parent's kind, title and entry id, entry marked `blocked`.
- `restore_of_missing_target_returns_not_found` — FR-F070-07: the owning row was purged, so restore is 404 and the entry carries `target_missing`.
- `restore_of_held_item_succeeds` — FR-F070-09: a hold blocks purge, not recovery.
- `restore_is_idempotent_under_replayed_key` — FR-F070-06: the same `Idempotency-Key` replayed returns the first result and restores once.
- `purge_requires_compliance_admin` — FR-F070-10: an editor with full access to the item receives 403 `denied` and the row survives.
- `purge_under_hold_returns_legal_hold_conflict` — FR-F070-09: 409 `conflict` code `legal_hold` naming the hold; nothing is deleted.
- `purge_runs_through_shared_executor` — FR-F070-10: the `PurgeExecutorPort` spy records the call, so the F027 audited path is provably the one that ran.
- `purge_rejects_stale_if_match` — FR-F070-10: `If-Match` below the entry's `source_version` returns 409 `conflict`.
- `purge_publishes_item_purged_and_audits` — FR-F070-10, NFR-F070-02: `item.purged.v1` and the `trash.purge` audit row carry kind, item id, title, actor and correlation id.
- `sweep_marks_expired_and_hands_batch_to_executor` — FR-F070-08: 1,200 expired entries are swept in three batches of 500, 500 and 200.
- `sweep_skips_held_entry_and_counts_it` — FR-F070-09: the held document stays, `state = 'held'`, and the held count is recorded on the purge request.
- `sweep_never_hard_deletes_directly` — FR-F070-08: with the executor stubbed to fail, no owning row is removed.
- `sweep_drops_entry_whose_row_was_restored` — FR-F070-08: an entry whose owning row is no longer soft-deleted is removed rather than purged.
- `sweep_resumes_after_worker_restart_without_double_purge` — NFR-F070-04: cancelling mid-batch and re-running purges each item once.
- `invisible_entry_returns_not_found` — FR-F070-02: an item the caller could not read before deletion is absent and its id is 404 on all three routes.
- `foreign_tenant_entry_returns_not_found` — FR-F070-11: tenant B ids on index, restore and purge return 404, never 403.
- `deleter_identity_grants_nothing` — FR-F070-02: the person who deleted an item they can no longer read still cannot see or restore it.
- `metrics_and_span_fields_present` — NFR-F070-04: the four metrics are emitted and every request and job span carries `tenant_id`, `actor_id`, `correlation_id` and `entry_id`.

Evidence: JUnit output, event stream logs and the executor spy report under `testing/evidence/F070/api/`.
