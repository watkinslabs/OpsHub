# F072 frontend cases

File: `testing/features/F072/frontend/{AddressCard.test.tsx,AddressDialog.test.tsx,SenderPolicyField.test.tsx,AllowListEditor.test.tsx,MappingEditor.test.tsx,RotateAddressDialog.test.tsx,MessageLogTable.test.tsx,MessageDetailDrawer.test.tsx,AuthResultChips.test.tsx}`. Vitest with MSW. Flag `F072_FEATURE`.

- `copy_control_announces_success` — FR-F072-17: clicking `Copy address` writes the address to the clipboard and announces `Address copied` through a polite live region.
- `address_hidden_without_sheet_editor` — FR-F072-02: a response without the `address` field renders `Hidden` and no copy control instead of an empty string.
- `sender_policy_defaults_to_tenant_members` — FR-F072-06: the dialog opens on `Tenant members only` with a one-line explanation for each of the three options.
- `allow_list_editor_validates_patterns` — FR-F072-06: an entry that is neither an address nor a domain shows `field_errors.allow_list`; 201 entries are refused.
- `rejects_duplicate_source_and_column` — FR-F072-11: `MappingEditor` blocks a repeated source and a column already mapped, naming the conflict.
- `mapping_rejects_incompatible_column_type` — FR-F072-13: mapping `received_at` to a text column shows the type error before submit.
- `rotate_dialog_states_grace_and_finality` — FR-F072-03: the rotate dialog says the old address stops working after 7 days; the revoke dialog says immediately and that it is never reissued.
- `shows_accepted_rejected_and_quarantined_entries` — FR-F072-15: the log renders all three dispositions with the reason for the rejected one and the held-until date for the quarantined one.
- `links_accepted_entry_to_its_row` — FR-F072-11: an accepted entry links to its row; a rejected or quarantined entry renders no row link at all.
- `auth_chips_show_three_mechanisms_with_text` — NFR-F072-03: `AuthResultChips` renders SPF, DKIM and DMARC with their results as text plus icon, never colour alone.
- `drawer_shows_issues_and_attachment_dispositions` — FR-F072-12, FR-F072-13: the drawer lists each issue code with its column and each attachment with `stored`, `rejected_type`, `rejected_size`, `rejected_count` or `quarantined`.
- `drawer_never_renders_html_body` — FR-F072-10: a message whose source was HTML renders as text nodes only; no `dangerouslySetInnerHTML` and no outbound image request.
- `log_filters_by_disposition_and_sender` — FR-F072-15: filtering by `rejected` and a sender domain narrows the table and preserves the cursor.
- `shows_denied_page_without_sheet_editor` — FR-F072-01: a viewer loading the settings route sees the denied page rather than an empty form.
- `shows_error_banner_with_correlation_id` — NFR-F072-04: a 500 from the log route renders the banner with `correlation_id` and a retry control.

Evidence: Vitest JUnit under `testing/evidence/F072/frontend/`.
