# F062 e2e cases

File: `testing/features/F062/e2e/{shell,theme}.spec.ts` (Playwright against the story app). Flag `F062_FEATURE`.

- `theme_switch_has_no_flash_on_reload` — FR-F062-05: with dark stored, the first painted frame after reload is already dark; the light background never appears.
- `system_theme_follows_prefers_color_scheme` — FR-F062-05: with the choice unset, emulating dark and light flips the resolved theme without a stored value.
- `density_switch_changes_row_height` — FR-F062-07:
- `brand_switch_restyles_accents_only` — FR-F062-04: changing the tenant brand hue restyles accent, selection and focus surfaces and leaves every other token untouched. switching to `compact` changes measured row height from 36px to 28px and persists across reload.
- `app_shell_rail_width_persists_across_reload` — FR-F062-12: resizing the rail to 320px and reloading restores 320px within the 240–400px bounds.
- `rail_collapses_to_drawer_below_lg` — FR-F062-12: at 1,023px the rail becomes a drawer; at 639px the inspector becomes a sheet.
- `reorder_visible_to_another_member_of_the_view` — FR-F062-17: an entitled viewer reorders columns on a shared view and a second member opening it sees the same order.
- `upgrade_link_reaches_entitlements_page` — FR-F062-16: clicking a disabled Pro affordance's tooltip link lands on `/admin/entitlements` with the `data-grid-pro` row in view.
- `skip_to_content_reaches_main` — FR-F062-12: the first tab stop is skip-to-content and activating it moves focus into the content region.
- `shortcut_sheet_opens_with_question_mark` — FR-F062-12: `?` opens the shortcut sheet, `[` and `]` toggle rail and inspector, and `Escape` restores focus.

Evidence: traces, videos, and first-frame captures under `testing/evidence/F062/e2e/`.
