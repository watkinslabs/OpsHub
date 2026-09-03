# F057 frontend cases

File: `testing/features/F057/frontend/{AssetGrid.test.tsx,AssetDetailDrawer.test.tsx,RightsForm.test.tsx,CollectionTree.test.tsx,RegisterAssetDialog.test.tsx}`. Vitest with MSW. Flag `F057_FEATURE`.

- `renders_tiles_with_badges` — FR-F057-13: 40 assets render virtualized tiles with approval and rights badges and alt text from title.
- `shows_loading_skeleton_then_tiles` — FR-F057-13: pending list shows skeleton tiles.
- `shows_empty_state_with_register` — FR-F057-13: no assets renders `Register your first asset`.
- `drawer_shows_not_usable_reason` — FR-F057-06: rejected or expired asset shows reason text.
- `rendition_panel_polls_until_ready` — FR-F057-03: pending → ready swaps placeholder for thumbnail; retry shown on failed.
- `validates_dates_and_territories` — FR-F057-05: `valid_until` before `valid_from` and territory `ZZ` blocked inline.
- `keyboard_expand_collapse` — FR-F057-13: ArrowRight expands, ArrowLeft collapses, live region announces.
- `register_dialog_lists_only_clean_files` — FR-F057-02: quarantined file absent from picker.
- `viewer_hides_mutation_controls` — FR-F057-13: viewer role hides register, rights, approval, archive.
- `unentitled_tenant_sees_upsell` — FR-F057-11: 403 with `entitlement: dam` renders `EntitlementUpsell`.
- `stale_asset_shows_reload_banner` — FR-F057-10: 409 on save shows `This asset changed`.
- `offline_disables_mutations` — FR-F057-13: offline badge and disabled actions.

Evidence: Vitest JUnit under `testing/evidence/F057/frontend/`.
