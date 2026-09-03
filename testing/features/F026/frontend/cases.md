# F026 frontend cases

File: `testing/features/F026/frontend/{ConnectionForm.test.tsx,ConnectionTable.test.tsx,ScimTokenDialog.test.tsx,GroupMappingEditor.test.tsx,SamlErrorPage.test.tsx}`. Vitest with MSW. Flag `F026_FEATURE`.

- `validates_domains_and_https` — FR-F026-01: `ConnectionForm` rejects `Example.COM ` until lowercased, rejects `http://` SSO URL, enforces skew 0–300.
- `shows_duplicate_domain_field_error` — FR-F026-02: 409 with `field_errors.domains` renders inline under the domains field.
- `renders_certificate_expiry_warning` — FR-F026-16: certificate with `not_after` in 20 days shows the `AlertTriangle` warning row.
- `test_results_render_three_checks` — FR-F026-07: `TestResultList` shows certificate, SSO URL, and metadata checks with pass/fail.
- `activate_disabled_until_test_passes` — FR-F026-07: `Activate` button disabled when `last_test_at` is null or older than 24 h.
- `shows_token_once_and_copies` — FR-F026-09: `ScimTokenDialog` shows the token, `Copy` announces "Token copied", closing hides it permanently.
- `adds_mapping_with_role_picker` — FR-F026-14: `GroupMappingEditor` adds `opshub-admins → tenant-admin` and calls `updateConnection` with `group_mappings`.
- `shows_denied_page_for_member` — NFR-F026-02: member role loading `/admin/sso` renders the denied page.
- `shows_error_banner_with_correlation_id` — NFR-F026-04: 500 shows banner with `correlation_id` and retry.
- `stale_version_shows_reload_banner` — FR-F026-01: 409 on PATCH renders `This connection changed` with reload.
- `saml_error_page_maps_reason_codes` — FR-F026-04: `?code=expired` renders the expiry message and never renders assertion contents.

Evidence: Vitest JUnit under `testing/evidence/F026/frontend/`.
