# F063 e2e cases

File: `testing/features/F063/e2e/entra.spec.ts`. Playwright against the seeded tenant with the mock Entra authority and mock Graph. Flag `F063_FEATURE`.

- `connect_test_enable_sign_in_and_sign_in_with_microsoft` — FR-F063-02, FR-F063-03, FR-F063-04, FR-F063-12: the identity-admin copies the redirect URI, pastes tenant id, client id and secret, presses `Test connection`, sees `Connected · Contoso Ltd`, enables `Sign in`, signs out, and completes `Sign in with Microsoft` through the mock authority into an F038 session.
- `missing_consent_blocks_group_sync_until_granted` — FR-F063-03: the first test reports `Missing scope: GroupMember.Read.All` against the group-sync switch; after the mock grants consent a re-test enables it.
- `map_group_run_sync_and_see_counts` — FR-F063-06, FR-F063-12: the admin maps `Delivery Team` to the OpsHub group `Delivery`, runs a sync, and sees `Added 24, removed 2` with the members visible on the group.
- `destructive_sync_halts_for_review` — FR-F063-07: the mock delta returns 70 of 100 members; the run shows `needs_review`, the group is unchanged, and confirming applies the removals.
- `graph_mail_failure_falls_back_to_smtp` — FR-F063-08: with `mail` on and Graph `sendMail` returning `503`, the notification arrives over SMTP and the delivery shows both attempts.
- `disconnect_and_confirm_other_methods_still_work` — FR-F063-01, FR-F063-10: after `Disconnect`, the Microsoft button is gone, password and SAML sign-in still succeed, and the group and its members remain.
- `member_cannot_open_admin_entra` — FR-F063-11: a member visiting `/admin/entra` sees the denied page.

Evidence: Playwright traces and mock provider logs under `testing/evidence/F063/e2e/`.
