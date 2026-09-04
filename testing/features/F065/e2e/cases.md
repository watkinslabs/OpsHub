# F065 e2e cases

File: `testing/features/F065/e2e/{signup.spec.ts,trial_lifecycle.spec.ts}`. Playwright against a seeded platform with the mock bot check and the mock mailbox. Flag `F065_FEATURE`.

- `signup_to_workspace` — FR-F065-01, FR-F065-08, FR-F065-10, FR-F065-16: a visitor submits `dana@acme.io` and `Acme Robotics`, opens the only message in the mock mailbox, completes with `acme-robotics`, and lands on `/w/acme-robotics` as a `tenant-admin` with the trial chip showing 14 days.
- `existing_customer_sees_nothing_different` — FR-F065-02: signing up with an address that already has an active user shows the same success screen; the mailbox holds the sign-in message and no completion link exists.
- `expired_link_recovery` — FR-F065-08: opening a 25-hour-old link shows `/signup/expired`, and `Start again` produces a fresh signup that completes normally.
- `slug_race_between_two_browsers` — FR-F065-07: two contexts both verify for `orbit`; the first completion wins, the second sees the slug error, picks `orbit-hq`, and both admins end in their own tenants.
- `trial_expiry_grace_and_suspension` — FR-F065-12: with the clock advanced past `trial_ends_at`, the workapps route is read-only while a sheet edit still saves; grace reminders appear in the mailbox on days 0, 3, and 6; after grace a sheet edit shows the suspended notice.
- `conversion_keeps_everything` — FR-F065-13: the suspended admin chooses a plan through the billing page, the banner clears, and the sheet, its 50 rows, and an uploaded file are byte-identical to a snapshot taken before expiry.
- `operator_invitation_flow` — FR-F065-15: an operator creates an invitation pinning `northwind`, the prospect completes it without a Turnstile challenge, and a competing self-serve attempt on that slug is refused.

Evidence: Playwright traces, mock mailbox dumps, and pre/post conversion snapshots under `testing/evidence/F065/e2e/`.
