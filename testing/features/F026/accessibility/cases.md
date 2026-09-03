# F026 accessibility cases

File: `testing/features/F026/accessibility/sso.a11y.spec.ts`. axe-core via Playwright. Flag `F026_FEATURE`.

- `admin_sso_pages_have_no_serious_violations` — NFR-F026-03: zero `serious`/`critical` violations on `/admin/sso`, `/admin/sso/new`, and the connection detail with two certificates.
- `token_dialog_traps_focus_and_restores` — NFR-F026-03: `ScimTokenDialog` traps focus, `Escape` closes, focus returns to `Generate SCIM token`.
- `expiry_warning_announced` — NFR-F026-03: certificate expiry warning row has `role="status"` and is read by the screen reader on load.
- `token_copy_announced_by_live_region` — NFR-F026-03: activating `Copy` announces "Token copied" through a polite live region.
- `form_errors_linked_to_fields` — NFR-F026-03: domain and URL errors use `aria-describedby`; first invalid field receives focus on submit.
- `mapping_editor_keyboard_only` — NFR-F026-03: add, edit role picker, and remove mapping complete without a mouse; focus ring visible on each control.

Evidence: axe JSON reports under `testing/evidence/F026/accessibility/`.
