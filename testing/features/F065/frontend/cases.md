# F065 frontend cases

File: `testing/features/F065/frontend/{SignupForm.test.tsx,SlugField.test.tsx,VerifySentPage.test.tsx,CompleteSignupPage.test.tsx,ExpiredTokenPage.test.tsx,TrialBanner.test.tsx,InvitationForm.test.tsx}`. Vitest with MSW. Flag `F065_FEATURE`.

- `honeypot_is_hidden_and_untabbable` — FR-F065-04, NFR-F065-03: `company_website` is `aria-hidden`, has `tabindex="-1"`, and is never focused by keyboard traversal.
- `submit_disabled_until_turnstile_resolves` — FR-F065-04: the button stays disabled while `TurnstileField` is pending and enables on a verdict.
- `availability_message_is_identical_for_every_reason` — FR-F065-06: taken, reserved, and soft-reserved responses all render "That address is not available" with a locally generated suffix suggestion.
- `availability_check_is_debounced_and_deduplicated` — FR-F065-16: typing `acme` one character at a time issues one request after 400 ms, and a `429` is not retried.
- `success_screen_masks_the_address` — FR-F065-02: `VerifySentPage` shows `d***@acme.io`, the 24-hour window, and a `Resend` button disabled for 60 seconds.
- `expired_page_names_reason_without_identity` — FR-F065-08: `expired`, `consumed`, and `abandoned` render distinct plain-language messages and never show the email or tenant.
- `complete_page_prefills_and_validates_slug` — FR-F065-10: the requested slug is prefilled with `Available`; a `409` on submit renders `field_errors.slug` and keeps the form usable.
- `complete_page_shows_terms_version_drift` — FR-F065-10: a stale `accepted_terms_version` renders the re-accept prompt rather than a generic error.
- `trial_banner_states_by_days_remaining` — FR-F065-12: dismissible from day 11, undismissible during grace with the suspension date, and replaced by the F002 suspended notice afterwards.
- `trial_badge_reads_entitlement_evaluate` — FR-F065-11: `TrialBadge` renders days remaining from the F048 evaluate payload and no F065 call is made.
- `invitation_form_denies_non_operator` — FR-F065-15: a `tenant-admin` opening the invitation page sees the shared denied state.
- `error_banner_shows_correlation_id` — NFR-F065-04: a `503 unavailable` renders one banner with `correlation_id` and a retry action.

Evidence: Vitest JUnit under `testing/evidence/F065/frontend/`.
