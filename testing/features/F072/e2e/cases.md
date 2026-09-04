# F072 e2e cases

File: `testing/features/F072/e2e/inbound_email.spec.ts` with the corpus in `testing/features/F072/e2e/corpus/`. Playwright against a seeded tenant and the mock inbound provider. Flag `F072_FEATURE`.

- `forwarded_mail_becomes_row_with_attachment` — FR-F072-01, FR-F072-11, FR-F072-12, FR-F072-17: an editor creates an address on `Vendor intake`, maps subject, body, sender and attachments, copies the address, the mock delivers a DMARC-passing member message with one PDF; a row appears with the subject, the sanitised body and the sender as a contact, the PDF is attached, and the log shows one `Accepted` entry.
- `dmarc_failure_never_reaches_the_sheet` — FR-F072-05, FR-F072-07: the mock delivers a spoof of that member with `dmarc = fail`; the sheet row count is unchanged, the log shows `Rejected · DMARC fail` with no row link, and the transport stub recorded the uniform recipient-rejected bounce.
- `temperror_is_held_not_lost` — FR-F072-05: a `dkim = temperror` message shows as `Quarantined` with its held-until date, creates no row, and is still listed after the ingest job runs again.
- `reply_to_notification_appends_comment` — FR-F072-14: an assignment notification is sent for row 1482, the mock replies to its `Reply-To` plus-token address, and the comment appears on row 1482 with no new row created.
- `forged_reply_cannot_write_another_row` — FR-F072-14: the mock replies with `In-Reply-To` naming row 9001 and no plus token; row 9001 gains no comment and a new row appears on the address's own sheet instead.
- `rejected_and_quarantined_entries_visible_in_log` — FR-F072-15, FR-F072-17: the log filters to `rejected` and `quarantined` and shows the reason, the three authentication results and the sender for each.
- `rotation_keeps_old_address_working_then_stops_it` — FR-F072-03: after rotation the mock delivers to the old address on day 3 and the row is created and tagged, then on day 8 it is refused and no row appears.
- `viewer_cannot_open_inbound_settings` — FR-F072-01: a viewer navigates to the sheet's inbound email settings and sees the denied page.

Evidence: Playwright traces, mock provider logs and transport stub bounce records under `testing/evidence/F072/e2e/`.
