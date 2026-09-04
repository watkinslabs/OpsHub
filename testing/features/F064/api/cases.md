# F064 api cases

File: `testing/features/F064/api/{proration_tests.rs,adapter_tests.rs,subscription_tests.rs,webhook_tests.rs,webhook_negative_tests.rs,dunning_tests.rs,metering_tests.rs,usage_tests.rs,invoice_tests.rs,failure_tests.rs,negative_tests.rs}`. Flag `F064_FEATURE`. Every provider call is served by the mock in `testing/harness/providers/billing/`.

- `mid_period_upgrade_credit_and_charge_round_half_up` — FR-F064-03: `team` to `enterprise` on 2026-09-16 of a 2026-09-01 to 2026-10-01 period yields credit 1450, charge 4950, net 3500 cents with half-up rounding.
- `equal_plans_net_zero` — FR-F064-03: a change to the current plan returns a zero net and writes nothing.
- `preview_mismatch_rejected_before_write` — FR-F064-03: mock returns line items one cent off; the change returns 502 `unavailable` and the subscription `version` is unchanged.
- `webhook_signature_verified_against_rotated_secret` — FR-F064-08: a body signed with either secret of the rotation pair verifies; a third secret does not.
- `stale_timestamp_rejected` — FR-F064-08: `t` 301 seconds old → 400 `invalid`, audit `billing.webhook-rejected`, no row written.
- `no_provider_type_outside_adapter` — FR-F064-06: a source scan over `crates/domain/src/billing`, `services/api/src/billing`, and `services/worker/src/billing` finds provider type names only in `adapters/stripe.rs`.
- `free_tenant_returns_synthetic_subscription` — FR-F064-01: a tenant with no `subscriptions` row returns `plan: free`, `status: active`, `version: 0`, not 404.
- `preview_writes_nothing` — FR-F064-02: `preview: true` returns a `ProrationPreview` and leaves `subscriptions` and the provider untouched.
- `enterprise_without_payment_method_conflicts` — FR-F064-02: 409 `conflict` with `field_errors.payment_method`.
- `stale_if_match_conflicts` — FR-F064-02: a stale `If-Match` returns 409 with `current_version` and no provider call.
- `upgrade_projects_plan_entitlements_with_source_plan` — FR-F064-05: `enterprise` upgrade upserts `workapps`, `bridge`, `datamesh`, `data-shuttle`, `assets`, `ai-assist`, `ai-insights` through the F048 double with `source: plan`.
- `manual_entitlement_survives_plan_change` — FR-F064-05: the `manual` `bridge` row is not written by the projector and stays active after a downgrade to `team`.
- `downgrade_schedules_for_period_end` — FR-F064-04: `enterprise` to `team` stores `scheduled_plan` and `scheduled_effective_at = 2026-10-01T00:00:00Z`; entitlements are unchanged until the job runs.
- `immediate_downgrade_issues_credit_note` — FR-F064-04: `apply: immediate` calls the adapter credit-note operation and applies entitlements at once.
- `portal_session_returns_short_lived_url` — FR-F064-07: `expires_at` is 15 minutes out and the URL is absent from the captured log sink and from every table.
- `webhook_replay_returns_duplicate_and_applies_nothing` — FR-F064-09: the same `provider_event_id` twice → second answers 200 `duplicate`, dunning stage unchanged, one event published.
- `unhandled_type_stored_as_ignored` — FR-F064-09: `customer.tax_id.created` is stored `ignored` and answered 200.
- `unknown_subscription_stored_as_ignored` — FR-F064-09: an event for an unmapped `provider_subscription_id` is stored `ignored` and matched to no tenant.
- `invoice_paid_clears_dunning_and_restores_entitlements` — FR-F064-10: from `restricted`, `invoice.paid` restores `active` and re-projects plan entitlements.
- `dunning_day_seven_restricts_only_plan_entitlements` — FR-F064-13: day 7 suspends `source: plan` rows only; a sheet write by a member still succeeds.
- `dunning_day_fourteen_keeps_export_available` — FR-F064-13: day 14 rejects writes with `denied` and allows the F027 export route.
- `dunning_notifies_each_stage_with_next_date` — FR-F064-13: the F037 double records one notification per stage naming the next stage and its date.
- `trial_expiry_without_payment_method_falls_back_to_free` — FR-F064-14: expiry sets `plan: free`, `status: active`, dunning stage 0.
- `cancel_at_period_end_preserves_access` — FR-F064-14: full access until `current_period_end`, then free plan and `subscription.updated.v1`.
- `meter_records_three_metrics_only` — FR-F064-11: one run writes `seats`, `storage_gb`, `automation_runs` and no fourth metric.
- `meter_rerun_is_idempotent_by_source_ref` — NFR-F064-04: a second run for the same `period_date` writes no rows.
- `seats_counts_active_users_with_role_binding` — FR-F064-11: deactivated users and users without a role binding are excluded.
- `storage_excludes_deleted_file_versions` — FR-F064-11: soft-deleted F017 files drop out of the next sample.
- `automation_runs_counted_at_terminal_status` — FR-F064-11: queued and running F019 rows are not counted; `dead_lettered` is.
- `adjustment_requires_reason_and_target` — FR-F064-12: a missing `reason` or `corrects_record_id` returns 400 `invalid`.
- `usage_query_folds_adjustments` — FR-F064-12: a sample of 42 with an adjustment of -3 reports 39 and `adjustments_applied: 1`.
- `usage_range_over_400_days_invalid` — FR-F064-12: a 401-day range and an inverted range both return 400.
- `overage_reported_without_blocking` — FR-F064-12: usage above the `team` allowance reports `overage` and no route returns an error.
- `invoice_finalized_publishes_invoice_issued` — FR-F064-10: the invoice row is upserted and `invoice.issued.v1` carries the period and total.
- `invoice_rebuilt_from_usage_matches_stored_lines` — FR-F064-11: an invoice recomputed from `usage_records` for 2026-08 equals the stored lines including the corrected day.
- `invoice_list_filters_and_pages_newest_first` — FR-F064-15: `status=paid` with cursor paging over 24 invoices in descending `issued_at`.
- `hosted_url_fetched_on_read_not_persisted` — FR-F064-15: the column does not exist and the adapter is called once per listed invoice page.
- `provider_timeout_leaves_version_unchanged` — NFR-F064-04: a timeout during `change_subscription` leaves the previous `version` and projects nothing.
- `portal_rate_limited_after_five_sessions` — FR-F064-07: the sixth request in an hour returns 429 `rate_limited`.
- `failed_webhook_retried_then_dead_lettered` — NFR-F064-04: five failures move the row to dead letter with an operator alert and the metrics emitted.
- `member_denied_on_every_billing_route` — FR-F064-15: a member receives 403 on all five `/api/v1/billing` routes.
- `tenant_admin_without_billing_admin_denied` — FR-F064-15: a tenant-admin holding no `billing-admin` role cannot change the plan or open the portal.
- `foreign_invoice_returns_not_found` — NFR-F064-02: a tenant B invoice id returns 404 for tenant A.
- `foreign_tenant_id_in_body_invalid` — FR-F064-15: a body naming another `tenant_id` returns 400 `invalid`.
- `cross_tenant_usage_never_returned` — NFR-F064-02: tenant A usage queries never include tenant B rows.

Evidence: JUnit output and provider mock request logs under `testing/evidence/F064/api/`.
- `credit_code_batch_returns_plaintext_once_and_stores_only_hash` — FR-F064-16: a 50-code batch returns 50 plaintexts; the table holds only `code_hash`; no plaintext appears in the response of any later read, the audit row, or `credit-code.issued.v1`.
- `credit_code_mint_requires_platform_operator` — FR-F064-16: a `billing-admin` without the operator role receives 403 `denied`.
- `credit_redemption_is_single_use` — FR-F064-17: the first redemption returns the new balance; the second returns 409 `conflict` with `reason: already_redeemed`.
- `concurrent_redemption_yields_exactly_one_winner` — FR-F064-17: two simultaneous redemptions of one code produce one success and one `already_redeemed`, and the ledger holds exactly one `redemption` entry.
- `redemption_failures_are_distinguished` — FR-F064-17: unknown, expired and restriction-violating codes return `invalid_code`, `expired` and `not_applicable`, and no response reveals a code's value.
- `redemption_is_rate_limited_per_tenant` — FR-F064-17, NFR-F064-02: the 6th attempt within an hour returns 429 `rate_limited`.
- `credit_balance_is_the_ledger_sum` — FR-F064-18: the balance equals the sum of signed entries after a redemption, an application, an expiry and an adjustment; no mutable total column exists.
- `credit_covers_invoice_without_provider_charge` — FR-F064-18: a balance at or above the invoice total marks it `paid_by_credit` and the provider mock records no charge.
- `partial_credit_reduces_amount_due` — FR-F064-18: a smaller balance reduces the due amount, the remainder is charged, and the carried balance is zero.
- `credit_covering_failure_prevents_dunning` — FR-F064-18, FR-F064-13: a tenant in `past_due` whose credit covers the invoice returns to `active` on the next run and never reaches `restricted`.
- `unused_credit_expires_with_ledger_entry` — FR-F064-18: expiry writes an `expiry` entry reducing the balance and the 14-day notification is queued once.

