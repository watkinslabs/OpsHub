# F053 frontend cases

File: `testing/features/F053/frontend/{MappingListPage.test.tsx,FieldMapTable.test.tsx,PreviewTab.test.tsx,RunsTab.test.tsx,ConflictsTab.test.tsx,ResolveDialog.test.tsx}`. Vitest with MSW. Flag `F053_FEATURE`.

- `MappingListPage.test.tsx::renders_mappings_with_mode_and_open_conflicts` — FR-F053-14: seeded mapping shows `on_change`, last run `succeeded`, and `2 open conflicts`.
- `MappingListPage.test.tsx::hides_sync_for_non_admin` — FR-F053-12: editor session shows no `Sync now` or `New mapping`.
- `MappingListPage.test.tsx::shows_not_entitled_panel` — FR-F053-12: `useModuleAllowed` false renders `ModuleNotEntitled`.
- `MappingListPage.test.tsx::shows_empty_state_with_new_mapping` — FR-F053-14: no mappings → `No mappings yet` call to action.
- `FieldMapTable.test.tsx::flags_incompatible_pair_inline` — FR-F053-02: `date → number` without transform shows an inline error before submit.
- `FieldMapTable.test.tsx::bidirectional_disables_transform` — FR-F053-02: choosing `bidirectional` disables the expression field with explanation.
- `FieldMapTable.test.tsx::shows_owned_by_mapping_error` — FR-F053-02: 409 `owned_by_mapping` renders on the target column cell with a link to the owning mapping.
- `PreviewTab.test.tsx::shows_counts_and_change_markers` — FR-F053-04: counts bar `matched 840 · unmatched 12 · update 96 · conflicts 2`; sample cells carry `update`/`conflict` markers with text.
- `PreviewTab.test.tsx::shows_timeout_state` — NFR-F053-01: `preview_timeout` renders a retry notice.
- `RunsTab.test.tsx::polls_while_running` — FR-F053-14: `running` run refetches every 5 s and stops at `succeeded`.
- `ConflictsTab.test.tsx::conflicts_tab_resolves_keep_target` — FR-F053-08: `keep_target` calls `resolveConflict`, row marked resolved, toast shown.
- `ConflictsTab.test.tsx::shows_row_moved_notice_on_conflict` — FR-F053-08: 409 rolls back the optimistic state and shows `Row changed since the conflict`.
- `ConflictsTab.test.tsx::filters_by_kind_and_status` — FR-F053-08: selecting `both_changed` and `open` requests the filtered page.
- `ResolveDialog.test.tsx::manual_value_validates_column_type` — FR-F053-08: text in a number column blocks submit with a field error.
- `ResolveDialog.test.tsx::offline_disables_resolve` — FR-F053-14: `navigator.onLine=false` shows offline badge and disables submit.
- `ConflictsTab.test.tsx::shows_error_banner_with_correlation_id` — NFR-F053-04: 500 → banner with `correlation_id` and retry.

Evidence: Vitest JUnit under `testing/evidence/F053/frontend/`.
