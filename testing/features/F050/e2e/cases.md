# F050 e2e cases

File: `testing/features/F050/e2e/dynamic_view.spec.ts`. Playwright against seeded tenant. Flag `F050_FEATURE`.

- `owner_policy_to_vendor_edit_round_trip` — FR-F050-02, FR-F050-06, FR-F050-07, FR-F050-14: owner creates `Vendor updates`, sets filter `Vendor = current user`, visible `Task`, `Due`, `Vendor status`, editable `Vendor status`, `assigned_rows`; vendor 1 logs in, sees 40 rows, edits one status; owner's `Edits` tab and sheet cell history show the change.
- `vendor_never_sees_other_vendor_rows` — FR-F050-04, FR-F050-12: vendor 2 session sees its own 40 rows; deep-linking vendor 1's row id returns not-found.
- `public_link_edit_then_revoke` — FR-F050-05, FR-F050-08, FR-F050-13: owner enables a 14-day link with editing; anonymous browser opens `/dv/{token}`, edits a status; owner revokes; anonymous reload shows `This link is no longer active`.
- `hidden_field_not_in_network_response` — NFR-F050-02: intercepted rows response body contains no `Budget` column id or value.
- `unshared_sheet_viewer_gets_not_found` — FR-F050-12: sheet viewer without share opens the view URL → not-found page.
- `not_entitled_tenant_sees_module_panel` — FR-F050-11: tenant with `dynamic-views` suspended opens the view → `ModuleNotEntitled` panel.
- `flag_off_hides_public_route` — FR-F050-11: with `F050_FEATURE` off, `/dv/{token}` is not-found and the sheet `Share` menu has no `Create dynamic view`.

Evidence: Playwright traces and videos under `testing/evidence/F050/e2e/`.
