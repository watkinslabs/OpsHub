# F029 e2e cases

File: `testing/features/F029/e2e/integrations.spec.ts`. Playwright against seeded tenant with mock provider consent pages. Flag `F029_FEATURE`.

- `connect_slack_and_send_test` — FR-F029-02, FR-F029-03, FR-F029-09, FR-F029-15: admin clicks `Connect` on Slack, approves on the mock consent page, sees `Slack · Acme workspace · active`, sends a test to `#ops`, sees `Delivered`; mock log shows the Block Kit payload.
- `bind_calendar_and_see_conflict` — FR-F029-10, FR-F029-11: admin connects Google, binds `Launch plan` start and end columns with `newest_wins`, mock calendar shows 50 events; admin edits a row date, mock edits the same event later, sync runs, row shows the provider value and the connection page lists the conflict.
- `needs_reauth_reconnect_flow` — FR-F029-05: mock rejects refresh; after three refresh runs the row shows `needs_reauth`; `Reconnect` completes consent and restores `active`.
- `revoke_pauses_binding` — FR-F029-06: admin revokes Google; binding shows `paused`; sheet settings show the connection as revoked.
- `thread_reply_becomes_comment` — FR-F029-12: mock posts a thread reply to the test message; chat sync runs; the record's comments show the reply with the provider badge.
- `member_cannot_open_integrations` — FR-F029-14: member visits `/admin/integrations` and sees the denied page.

Evidence: Playwright traces and mock provider logs under `testing/evidence/F029/e2e/`.
