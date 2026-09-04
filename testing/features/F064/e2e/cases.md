# F064 e2e cases

File: `testing/features/F064/e2e/{billing.spec.ts,dunning.spec.ts,usage.spec.ts}`. Playwright against a seeded tenant with the mock payment provider and its hosted-portal stand-in. Flag `F064_FEATURE`.

- `upgrade_with_preview_unlocks_modules` — FR-F064-02, FR-F064-03, FR-F064-05: a billing-admin opens `/admin/billing` on `team`, chooses `enterprise`, reads credit, charge, and net in the preview, confirms, and sees the plan card update and the entitlement panel list `bridge`, `workapps`, and `data-shuttle` as newly active with source plan.
- `schedule_downgrade_and_let_it_apply` — FR-F064-04: the admin schedules `enterprise` to `team`, sees the effective date, the clock advances past the period end, the scheduled job runs, and the premium modules disappear from the entitlement panel exactly then and not before.
- `dunning_notifies_and_degrades_in_order` — FR-F064-13: the mock fails an invoice; the banner shows `past_due` with the day 7 date; after day 7 the tenant is `restricted`, a premium module is unavailable, and a sheet edit still saves; after day 14 the tenant is read-only and each stage produced a notification.
- `suspended_tenant_can_still_export` — FR-F064-13: at day 14 a write is refused while the F027 export route returns a file, proving data access is never removed silently.
- `late_payment_recovers_full_access` — FR-F064-10: the mock marks the invoice paid; the banner clears, `status` returns to `active`, and every previously paused module is usable again.
- `open_hosted_portal_and_return` — FR-F064-07: `Manage payment method` opens the mock portal in a new tab and returning to `/admin/billing` shows the updated brand and last four digits.
- `usage_view_shows_correction_history` — FR-F064-12: the usage view shows the corrected day with the original value, the adjustment, and the reason, and the total for the month reflects the correction.
- `trial_expiry_falls_back_to_free` — FR-F064-14: a trialing tenant with no payment method passes `trial_ends_at`, lands on `free` with `status: active`, and sees no dunning banner.

Evidence: Playwright traces, provider mock logs, and notification double transcripts under `testing/evidence/F064/e2e/`.
