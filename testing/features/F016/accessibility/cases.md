# F016 accessibility cases

File: `testing/features/F016/accessibility/comments.a11y.spec.ts`. axe-core via Playwright. Flag `F016_FEATURE`.

- `panel_and_activity_have_no_serious_axe_violations` — NFR-F016-03: zero `serious`/`critical` violations on the conversation panel with 5 threads and on the activity tab with 200 entries.
- `mention_combobox_follows_aria_pattern` — NFR-F016-03: composer has `role=combobox`, `aria-expanded`, `aria-controls` to a `listbox`; options have `aria-selected`; Escape closes the popup without closing the drawer.
- `new_reply_announced_by_live_region` — NFR-F016-03: submitting a reply announces "Reply posted by Ana" via `aria-live=polite`.
- `resolve_toggle_is_a_labelled_switch` — NFR-F016-03: `role=switch` with `aria-checked` and label "Resolve thread"; `R` shortcut toggles the focused thread.
- `edit_delete_menu_keyboard_reachable` — NFR-F016-03: comment menu opens with Enter, items navigable with arrows, delete requires a confirm dialog with text label, focus returns to the comment.
- `activity_filter_chips_have_pressed_state` — NFR-F016-03: chips use `aria-pressed`; contrast ≥ 4.5:1 in both states; focus ring visible.
- `reduced_motion_disables_thread_collapse_animation` — NFR-F016-03: `prefers-reduced-motion` removes collapse transition when resolving.

Evidence: axe JSON reports under `testing/evidence/F016/accessibility/`.
