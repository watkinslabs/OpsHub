# F027 frontend cases

File: `testing/features/F027/frontend/{RetentionTable.test.tsx,LegalHoldTable.test.tsx,ExportProgress.test.tsx,PurgeWizard.test.tsx,PurgeConfirmDialog.test.tsx,DecisionTable.test.tsx}`. Vitest with MSW. Flag `F027_FEATURE`.

- `edits_policy_and_shows_field_errors` — FR-F027-01, FR-F027-02: editing `audit_events` purge to 200 shows the inline `field_errors.purge_after_days` message from the 400.
- `stale_policy_shows_reload_banner` — FR-F027-02: 409 on PUT renders the stale banner with reload.
- `new_hold_dialog_requires_scope_and_reason` — FR-F027-04: submit disabled until scope picked and reason entered.
- `export_progress_polls_until_completed` — FR-F027-07: progress bar advances per kind every 5 s and shows `Download` when `completed`.
- `export_button_disabled_while_running` — FR-F027-06: running export disables `Request export` with a running badge.
- `purge_wizard_shows_preview_counts` — FR-F027-08: preview renders `12,400 candidates` and `310 held` per kind.
- `button_disabled_until_code_matches` — FR-F027-09, FR-F027-14: `Permanently delete 12,090 records` enabled only when the typed code equals the issued code.
- `purge_confirm_denied_shows_two_person_message` — FR-F027-09: 403 renders "A different compliance administrator must confirm".
- `flagged_rows_first` — FR-F027-12: `DecisionTable` orders flagged principals first with the flag reason.
- `decision_table_bulk_revoke_flagged` — FR-F027-12: `Revoke all flagged guests` submits three `revoke` decisions and shows outcomes.
- `shows_denied_page_for_tenant_admin` — FR-F027-13: tenant-admin without compliance role sees the denied page on every route.
- `shows_error_banner_with_correlation_id` — NFR-F027-04: 500 renders banner with `correlation_id` and retry.

Evidence: Vitest JUnit under `testing/evidence/F027/frontend/`.
