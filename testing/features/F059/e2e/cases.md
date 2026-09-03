# F059 e2e cases

File: `testing/features/F059/e2e/{publishing.spec.ts,embed-host.spec.ts}`. Playwright with origins `https://host.test` and `https://evil.test`. Flag `F059_FEATURE`.

- `publish_view_logged_out_rotate_revoke` — FR-F059-01, FR-F059-02, FR-F059-08, FR-F059-13: publish, copy link, logged-out context renders it, rotate keeps old link 10 min, revoke shows unavailable.
- `tenant_access_requires_login` — FR-F059-06: tenant-access link redirects to login, then renders; other tenant user sees not-found.
- `embed_on_allowed_host_renders_and_resizes` — FR-F059-07: iframe on `https://host.test` renders and parent receives height message.
- `embed_on_unlisted_host_denied` — FR-F059-07: iframe on `https://evil.test` shows "This embed is not allowed here".
- `stale_banner_after_refresh_failure` — FR-F059-05: storage outage simulated; public page shows stale banner; recovery clears it.
- `hidden_columns_absent_in_public_page` — FR-F059-04: hidden columns from the view never appear in the public DOM.
- `non_publisher_has_no_publish_menu` — FR-F059-13: editor without publisher role sees no `Publish` item.

Evidence: Playwright traces and videos under `testing/evidence/F059/e2e/`.
