# F009 e2e cases

File: `testing/features/F009/e2e/hierarchy.spec.ts`. Playwright against seeded tenant. Flag `F009_FEATURE`.

- `indent_row_and_see_rollup_sum` — FR-F009-01, FR-F009-06, FR-F009-07: editor indents "Design" (Cost 4200) under "Phase 1", sets sum roll-up on Cost, "Phase 1" shows 4200; reload keeps hierarchy and value.
- `depth_limit_shows_reason` — FR-F009-03: indenting into a 20-deep chain shows the `depth_exceeded` toast and the row stays in place.
- `outdent_carries_children` — FR-F009-02: outdent a parent with two children; children remain under it at the new depth.
- `link_to_vendor_and_break_on_delete` — FR-F009-09, FR-F009-12: link Vendor cell to "Acme" in `Vendors`, chip shows; delete "Acme" in the other tab; chip turns broken; restore clears it.
- `pull_sync_updates_linked_cell` — FR-F009-13: edit "Acme" name in `Vendors`; the linked cell in `Plan` shows the new value after the change event.
- `viewer_cannot_indent_or_link` — FR-F009-14: viewer login sees the tree read-only with no indent, link, or roll-up controls.
- `redacted_link_for_restricted_viewer` — FR-F009-10: user with `Plan` but not `Vendors` access sees `Restricted` chip.
- `delete_parent_then_restore_subtree` — FR-F009-05: delete "Phase 1"; children disappear; restore from trash; children return with the same IDs.
- `keyboard_only_indent_and_expand` — FR-F009-15, NFR-F009-03: no mouse; `Tab` indents, `ArrowRight` expands, live region announces "Design level 2".

Evidence: Playwright traces and videos under `testing/evidence/F009/e2e/`.
