# F049 accessibility cases

File: `testing/features/F049/accessibility/locale.a11y.spec.ts`. axe-core via Playwright. Flag `F049_FEATURE`.

- `locale_pages_have_no_serious_axe_violations` — NFR-F049-03: zero `serious`/`critical` violations on `/admin/locale` and `/me/locale` in `en-US`, `de-DE`, and `ja-JP`.
- `html_lang_updates_on_locale_change` — NFR-F049-03: after saving `pt-BR`, `<html lang="pt-BR">`; formatted values keep `<time datetime>` ISO attributes.
- `locale_change_announced_by_live_region` — NFR-F049-03: saving announces `Language changed to Deutsch` through the polite live region.
- `timezone_combobox_keyboard_operable` — NFR-F049-03: type-ahead `Ber`, `ArrowDown`, `Enter` selects `Europe/Berlin`; `Escape` closes without change; focus returns to the control after save.
- `pickers_have_labels_and_descriptions` — NFR-F049-03: every select exposes an accessible name and the current offset as description.
- `cjk_fallback_font_and_contrast` — NFR-F049-03: `ja-JP` text renders in the fallback stack with contrast ≥ 4.5:1; focus ring visible on every control.
- `reduced_motion_disables_preview_transition` — NFR-F049-03: `prefers-reduced-motion` removes the preview fade.

Evidence: axe JSON reports under `testing/evidence/F049/accessibility/`.
