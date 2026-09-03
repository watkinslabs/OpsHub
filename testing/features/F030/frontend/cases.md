# F030 frontend cases

File: `testing/features/F030/frontend/{SyncListPage.test.tsx,SyncWizard.test.tsx,MappingEditor.test.tsx,TransformPicker.test.tsx,MappingPreview.test.tsx,RunHistoryTable.test.tsx,FailedRecordTable.test.tsx,ReplayDialog.test.tsx,ConflictQueue.test.tsx,ConflictDiff.test.tsx,MergeChooser.test.tsx}`. Vitest with MSW. Flag `F030_FEATURE`.

- `empty_list_prompts_for_a_connection` — FR-F030-21: no active F029 connection → the list explains that a connection is required and links to `/admin/integrations`.
- `list_shows_state_trigger_and_open_conflicts` — FR-F030-03: rows render connector, direction, `paused`/`active`/`error`, last run state, and the open-conflict count as text plus icon.
- `wizard_blocks_step_two_until_object_valid` — FR-F030-02: an invalid JQL filter keeps `Next` disabled and shows the connector's validation message.
- `filters_column_picker_by_compatible_type` — FR-F030-05: mapping `duedate` offers only date columns; picking a text column shows `field_errors["mappings[0].column_id"]`.
- `transform_picker_renders_arguments_per_transform` — FR-F030-06: `date_tz` shows a timezone input, `value_map` a key/value table, `lookup` three pickers.
- `shows_per_field_mapping_errors` — FR-F030-06: preview response with a `LookupMiss` marks that field red and keeps the other four records rendered.
- `reorders_rows_with_keyboard` — NFR-F030-03: `Alt+ArrowDown` moves a mapping row and announces the new position; no pointer-only path exists.
- `run_history_expands_failed_records` — FR-F030-11: expanding a `partial` run shows `external_id`, classification, and provider code for each sample.
- `replay_dialog_names_record_count` — FR-F030-12: `Dry-run replay` confirmation states the 40 failed records and renders the returned projection.
- `shows_both_values_per_field` — FR-F030-13: `ConflictDiff` renders OpsHub value, external value, and both timestamps per field with labelled columns.
- `requires_a_choice_for_every_conflicting_field` — FR-F030-14: `MergeChooser` keeps `Apply` disabled until each conflicting field has a side selected.
- `bulk_keep_external_capped_at_one_hundred` — FR-F030-21: selecting 101 conflicts disables the bulk action and explains the cap.
- `shows_denied_page_for_member` — FR-F030-20: member loading `/admin/syncs` sees the denied page and no data request is issued.
- `shows_error_banner_with_correlation_id` — NFR-F030-04: a 500 from the run history query renders a banner with `correlation_id` and a retry control.

Evidence: Vitest JUnit under `testing/evidence/F030/frontend/`.
