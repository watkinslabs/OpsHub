# F061 e2e cases

File: `testing/features/F061/e2e/update_requests.spec.ts`. Playwright against the seeded tenant; public pages run in a browser context with no session cookie; email asserted in Mailpit. Flag `F061_FEATURE`.

- `external_recipient_completes_in_two_visits` — FR-F061-01, FR-F061-04, FR-F061-06, FR-F061-07: the requester sends 12 rows × 3 columns to `paul@contractor.example`; Paul opens the emailed link on a 390 px viewport, fills 9 fields, saves a draft, returns in a fresh context, completes the remaining 27, and submits; the sheet shows 36 changed cells and the request is `completed`.
- `reminder_fires_and_appears_in_mailpit` — FR-F061-10: with cadence `daily` the clock advances one day, the reminder job runs twice, and exactly one reminder email arrives; the detail drawer shows `reminder_count: 1`.
- `cancel_kills_every_link` — FR-F061-12: the requester cancels with a reason; all three recipient links then render the cancelled screen and the pending reminder never sends.
- `conflict_surfaces_when_owner_edits_first` — FR-F061-08: the recipient loads the form, the requester edits one of those rows in the grid, the recipient submits and sees the conflict panel, accepts the current value, and resubmits successfully.
- `partial_response_keeps_request_open` — FR-F061-09: one of two recipients completes their part; the request stays `open` with a `24 of 36 filled` indicator until the second recipient submits.
- `expired_link_shows_terminal_screen` — FR-F061-02: after `expires_at` passes and the expire job runs, the link renders the expired screen and the request shows `expired`.
- `change_log_and_audit_agree` — FR-F061-14: the detail drawer's change log matches `GET /api/v1/audit-events?correlation_id=` for the same response, including the external recipient attribution.
- `member_cannot_open_request_detail` — FR-F061-13: a member without `sheet.admin` visiting `/w/{workspace_id}/update-requests/{id}` sees the denied page.

Evidence: Playwright traces, Mailpit captures, and screenshots under `testing/evidence/F061/e2e/`.
