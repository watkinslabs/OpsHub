# F052 frontend cases

File: `testing/features/F052/frontend/{FlowListPage.test.tsx,FlowEditorPage.test.tsx,MappingTable.test.tsx,RunHistoryPage.test.tsx,RunDrawer.test.tsx}`. Vitest with MSW. Flag `F052_FEATURE`.

- `FlowListPage.test.tsx::renders_flows_with_next_run_and_last_status` — FR-F052-14: seeded flow shows `Next run` in the viewer's timezone and `Last run: succeeded`.
- `FlowListPage.test.tsx::hides_run_for_non_admin` — FR-F052-12: editor session shows no `Run now` or `New flow`.
- `FlowListPage.test.tsx::shows_not_entitled_panel` — FR-F052-12: `useModuleAllowed` false renders `ModuleNotEntitled` with reason.
- `FlowListPage.test.tsx::shows_empty_state_with_new_flow` — FR-F052-14: no flows → `No flows yet` call to action.
- `FlowEditorPage.test.tsx::sample_preview_shows_first_20_rows` — FR-F052-14: uploaded sample renders 20 rows and source column headers.
- `FlowEditorPage.test.tsx::schedule_rejects_dense_cron_inline` — FR-F052-03: `*/5 * * * *` shows `Minimum interval is 15 minutes` before submit.
- `FlowEditorPage.test.tsx::shows_stale_banner_on_conflict` — FR-F052-11: PATCH 409 → `This flow changed` with reload.
- `MappingTable.test.tsx::mapping_table_flags_coercion_mismatch` — FR-F052-02: mapping `Amount` as `date` onto a currency column shows an inline error.
- `MappingTable.test.tsx::mapping_table_requires_keys_for_update` — FR-F052-02: strategy `update` with no key marks the key column selector invalid.
- `RunHistoryPage.test.tsx::run_drawer_polls_while_running` — FR-F052-14: `running` run refetches every 5 s and stops at `succeeded`.
- `RunDrawer.test.tsx::shows_counts_and_rejected_rows` — FR-F052-10: counts as labelled numbers; rejected table shows 12 rows with reasons.
- `RunDrawer.test.tsx::replay_disabled_when_archive_purged` — FR-F052-09: `archive_purged` run disables `Replay` with tooltip.
- `RunDrawer.test.tsx::shows_error_banner_with_correlation_id` — NFR-F052-04: 500 → banner with `correlation_id` and retry.
- `RunDrawer.test.tsx::offline_disables_replay` — FR-F052-14: `navigator.onLine=false` shows offline badge and disables `Replay`.

Evidence: Vitest JUnit under `testing/evidence/F052/frontend/`.
