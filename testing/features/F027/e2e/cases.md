# F027 e2e cases

File: `testing/features/F027/e2e/compliance.spec.ts`. Playwright against seeded tenant with two compliance-admin browser contexts. Flag `F027_FEATURE`.

- `hold_export_two_person_purge_review` — FR-F027-04, FR-F027-07, FR-F027-09, FR-F027-11: admin one applies hold `Case 2026-14` on workspace `Legal`, requests an export, downloads the ZIP; proposes a purge and reads the code; admin two opens the request, retypes the code, confirms; purge completes with `12,090 purged, 310 skipped`; admin one generates a review for `Finance` and revokes a stale guest.
- `proposer_cannot_confirm_own_purge` — FR-F027-09: admin one enters the correct code on their own proposal and sees the two-person message; status stays proposed.
- `expired_proposal_shows_conflict` — FR-F027-09: clock advanced 25 h; confirm shows "This proposal expired" and a `Propose again` action.
- `export_progress_visible_and_downloadable` — FR-F027-07, FR-F027-14: progress per kind updates; `Download` opens a signed URL; second download is audited.
- `tenant_admin_sees_denied_console` — FR-F027-13: tenant-admin without compliance role visits `/admin/compliance/retention` and sees the denied page.
- `retention_policy_edit_round_trip` — FR-F027-02: change `rows` purge to 365, reload, value persisted with new `updated_by`.

Evidence: Playwright traces and videos under `testing/evidence/F027/e2e/`.
