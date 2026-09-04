# F064 frontend cases

File: `testing/features/F064/frontend/{PlanCard.test.tsx,PlanChangeDialog.test.tsx,ProrationPreviewTable.test.tsx,CancelDialog.test.tsx,DunningBanner.test.tsx,UsageCards.test.tsx,UsageTable.test.tsx,UsageCorrectionRow.test.tsx,InvoiceTable.test.tsx,EntitlementSummary.test.tsx}`. Vitest with MSW. Flag `F064_FEATURE`.

- `free_tenant_sees_upgrade_card` — FR-F064-01: a `version: 0` free subscription renders the upgrade card naming what `team` and `enterprise` unlock instead of an empty state.
- `announces_preview_before_confirm` — FR-F064-03: selecting `enterprise` loads the preview, announces it through a live region, and leaves the confirm button as the only commit path.
- `preview_table_shows_credit_charge_and_net` — FR-F064-03: credit, charge, net, effective date, and next invoice date are rendered as a described table with text labels, not a color-coded figure.
- `downgrade_shows_effective_date_and_kept_modules` — FR-F064-04: choosing `team` from `enterprise` shows the period-end date and lists the modules kept until then.
- `immediate_downgrade_confirmation_names_lost_modules` — FR-F064-04: the secondary action requires a confirmation naming every module that stops today.
- `dunning_banner_states_stage_consequence_and_date` — FR-F064-13: `past_due`, `restricted`, and `suspended` each render the consequence and the date of the next step with a portal link.
- `restricted_banner_says_sheets_remain_editable` — FR-F064-13: the `restricted` banner states that sheets stay editable and lists only the paused modules.
- `usage_cards_show_numeric_labels_beside_bars` — NFR-F064-03: each of the three cards shows the total, the allowance, and a numeric percentage label rather than a bar alone.
- `overage_shown_without_error_state` — FR-F064-12: usage above the allowance renders an `overage` badge and no error or blocking dialog.
- `corrected_day_shows_original_adjustment_and_reason` — FR-F064-12: the corrected row shows the original value, the signed adjustment, the reason, and the actor.
- `invoice_table_renders_lines_with_metric_and_quantity` — FR-F064-15: an expanded invoice shows per-line description, metric, quantity, unit amount, and amount.
- `entitlement_summary_reads_f048_not_billing` — FR-F064-05: the panel is populated from the F048 evaluate response and shows the `manual` `bridge` row as an operator override.
- `denied_page_for_non_billing_admin` — FR-F064-15: a tenant-admin without `billing-admin` loading `/admin/billing` sees the denied page.
- `provider_error_banner_states_nothing_was_charged` — NFR-F064-04: a 502 renders the `correlation_id`, a retry, and the assurance that no charge was made.

Evidence: Vitest JUnit under `testing/evidence/F064/frontend/`.
