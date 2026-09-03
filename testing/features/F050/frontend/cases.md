# F050 frontend cases

File: `testing/features/F050/frontend/{RestrictedGrid.test.tsx,PolicyEditor.test.tsx,PublicLinkDialog.test.tsx,PublicViewPage.test.tsx,EditsLog.test.tsx}`. Vitest with MSW. Flag `F050_FEATURE`.

- `RestrictedGrid.test.tsx::renders_only_visible_fields` — FR-F050-13: seeded view renders `Task`, `Due`, `Vendor status` columns and 40 rows; no `Budget` header.
- `RestrictedGrid.test.tsx::locks_read_only_cells` — FR-F050-13: `Due` cells show the lock icon and `aria-readonly`; `Vendor status` cells are editable.
- `RestrictedGrid.test.tsx::rolls_back_on_denied` — FR-F050-06: edit returning 403 restores the cell and shows the `not editable` banner.
- `RestrictedGrid.test.tsx::shows_stale_banner_on_conflict` — FR-F050-06: 409 shows `This row changed` with reload.
- `RestrictedGrid.test.tsx::shows_empty_state_for_no_matching_rows` — FR-F050-04: empty page shows `No rows match this view for you`.
- `PolicyEditor.test.tsx::blocks_editable_not_visible` — FR-F050-02: unchecking a visible field clears its editable flag and blocks submit when inconsistent.
- `PolicyEditor.test.tsx::enforces_depth_and_leaf_limits` — FR-F050-02: fifth nesting level and 21st leaf are disabled with explanation.
- `PolicyEditor.test.tsx::assigned_rows_requires_person_column` — FR-F050-03: selecting `assigned_rows` shows the assignment column select limited to person columns.
- `PublicLinkDialog.test.tsx::shows_link_once_and_revokes` — FR-F050-05: enabling shows the raw link with copy; reopening shows `Link active until …` without the raw value; revoke calls `updateView` with `enable: false`.
- `PublicLinkDialog.test.tsx::rejects_expiry_over_30_days` — FR-F050-05: date picker blocks dates beyond 30 days.
- `PublicViewPage.test.tsx::inactive_token_shows_no_tenant_details` — FR-F050-13: 403 renders `This link is no longer active` with no workspace or sheet text.
- `PublicViewPage.test.tsx::offline_disables_edits` — FR-F050-13: `navigator.onLine=false` shows offline badge and disables cell editing.
- `EditsLog.test.tsx::lists_edits_with_actor_kind` — FR-F050-14: edits show `vendor 1` or `Public link` actor, changed columns, and time.
- `RestrictedGrid.test.tsx::module_not_entitled_panel` — FR-F050-11: `useModuleAllowed('dynamic-views')` false renders the shared panel.

Evidence: Vitest JUnit under `testing/evidence/F050/frontend/`.
