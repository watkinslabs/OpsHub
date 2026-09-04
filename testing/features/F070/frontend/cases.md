# F070 frontend cases

File: `testing/features/F070/frontend/{TrashPage.test.tsx,TrashTable.test.tsx,TrashFilters.test.tsx,RestoreDialog.test.tsx,PurgeDialog.test.tsx,BlockedReason.test.tsx,StaleBanner.test.tsx,EmptyTrash.test.tsx}`. Vitest with MSW. Flag `F070_FEATURE`.

- `renders_kind_location_deleter_and_countdown` — FR-F070-12: a `sheet` row shows the kind icon with its label, `Northfield Delivery / Migration`, the deleter's name and `30 days left`.
- `held_row_shows_hold_chip_instead_of_countdown` — FR-F070-09: a held entry renders the hold name where the countdown would be, and its `Purge` action is disabled.
- `blocked_row_offers_restore_parent_first` — FR-F070-07: a `parent_deleted` row shows the reason with a link to the parent's entry and no restore dialog.
- `filters_narrow_by_kind_workspace_person_and_date` — FR-F070-12: each control updates the query key and the request; clearing restores the unfiltered list.
- `bulk_selection_restores_selected_rows` — FR-F070-12: selecting three rows enables `Restore 3` and issues one restore per row, reporting partial failures individually.
- `restore_dialog_names_destination_and_child_count` — FR-F070-12: restoring `Cutover plan` states the destination path and `40 rows will come back`.
- `purge_dialog_requires_retyped_title` — FR-F070-10, NFR-F070-03: the action stays disabled until the title matches exactly, and the dialog states that it cannot be undone.
- `purge_disabled_with_reason_without_compliance_admin` — FR-F070-10: an editor sees `Purge` disabled with the reason, not a hidden control, so the rule is discoverable.
- `purge_under_hold_shows_hold_name` — FR-F070-09: a 409 `legal_hold` response renders the hold name and leaves the row in place.
- `shows_stale_banner_when_envelope_is_stale` — FR-F070-01: `stale: true` renders the banner with the `as_of` time and a `Refresh` action.
- `empty_state_explains_retention_for_a_caller_who_sees_nothing` — FR-F070-02: a member with no readable deletions sees the retention explanation, not a denied page.
- `error_banner_shows_correlation_id` — NFR-F070-04: a 500 renders the banner with the `correlation_id` and a retry.
- `offline_disables_restore_and_purge` — FR-F070-12: offline shows the badge and disables both mutations.
- `state_column_pairs_text_with_icon` — NFR-F070-03: `restorable`, `blocked`, `held` and `expired` each render a label beside a titled icon in both themes.

Evidence: Vitest JUnit under `testing/evidence/F070/frontend/`.
