# F008 api cases

File: `testing/features/F008/api/{cell_tests.rs,undo_tests.rs,bulk_tests.rs,feed_tests.rs,history_tests.rs,layout_tests.rs,concurrency_tests.rs,permission_tests.rs}`. Flag `F008_FEATURE`.

- `patch_cells_reports_per_cell_outcomes` — FR-F008-01: three edits (valid number, "abc" into number, stale version) → 200 with `applied`, `invalid: type_mismatch`, `conflict: current_row_version`.
- `patch_cells_writes_history_and_event` — FR-F008-02: one applied edit → row version +1, `cell_history` row with previous/new raw, audit row, `cell.updated.v1` with `changed_fields` and `correlation_id`.
- `patch_cells_rejects_201_edits` — FR-F008-01: 201 edits → 400 `invalid` with `field_errors.edits`.
- `patch_cells_idempotent_replay` — FR-F008-16: same key twice → identical response, one history row; different body → 409.
- `undo_reverts_last_batch` — FR-F008-06: patch then undo → previous raw restored, `undone_at` set, `edit.undone.v1` published.
- `undo_conflicts_when_other_user_changed_cell` — FR-F008-06: editor B changes a cell inside A's batch → A undo 409 listing that cell, nothing reverted.
- `redo_stack_discarded_by_new_edit` — FR-F008-07: undo, new patch, redo → 409 `empty_stack`.
- `stack_trimmed_to_50` — FR-F008-05: 51 patches → 50 batches for the actor, oldest gone.
- `bulk_cells_applies_and_emits_one_event` — FR-F008-03: 4,999 cells `mode: set` → all applied, exactly one `cells.bulk-updated.v1`.
- `bulk_cells_rejects_over_5000` — FR-F008-03: 5,001 target cells → 400 `field_errors.selection = "too_large"`.
- `bulk_cells_fill_continues_date_sequence` — FR-F008-12: source 2026-01-01 fill 5 rows → 2026-01-02 … 2026-01-06.
- `bulk_rows_returns_row_versions` — FR-F008-04: 1,000 rows `mode: set` → per-row versions, one `rows.bulk-updated.v1`.
- `bulk_batch_undo_reverts_all_cells` — FR-F008-05: bulk then undo → every cell restored in one batch.
- `changes_feed_orders_by_change_version` — FR-F008-08: 1,200 edits, `since=N`, `limit=1000` → ascending, `next_since` continues.
- `changes_feed_returns_actor_layout` — FR-F008-10: actor with saved layout → `layout` in feed response; other actor gets default.
- `history_pages_newest_first` — FR-F008-09: cell edited 5 times → 5 entries newest first, cursor works.
- `history_cross_tenant_not_found` — FR-F008-15: tenant B reads tenant A history → 404.
- `layout_upsert_rejects_hidden_primary` — FR-F008-10: `hidden_columns` containing primary → 400; `frozen_column_count: 6` → 400.
- `layout_is_private_per_user` — FR-F008-14: editor A layout not returned to editor B.
- `thousand_editors_no_lost_updates` — NFR-F008-02: 1,000 tasks patch overlapping cells → final value equals last applied version, losers got `conflict`.
- `bulk_rolls_back_on_outbox_failure` — NFR-F008-04: outbox fail-once → no cells, history, or batch written.
- `viewer_and_commenter_mutations_denied` — FR-F008-15: every mutation route → 403 `denied`.
- `cross_tenant_all_routes_not_found` — FR-F008-15: tenant B on all seven routes → 404.
- `server_rejects_client_bypassed_validation` — NFR-F008-02: required column cleared via bulk → per-cell `invalid: required`.
- `request_span_carries_batch_ids` — NFR-F008-04: span has `tenant_id`, `sheet_id`, `batch_id`, `cell_count`, `correlation_id`; `grid_cells_conflict_total` increments.

Evidence: JUnit output and request logs under `testing/evidence/F008/api/`.
