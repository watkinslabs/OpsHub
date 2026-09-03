# F014 e2e cases

File: `testing/features/F014/e2e/forms.spec.ts`. Playwright against seeded tenant. Flag `F014_FEATURE`.

- `build_publish_submit_and_see_row` — FR-F014-01, FR-F014-04, FR-F014-10, FR-F014-15: admin builds "Request" with a conditional "Budget", publishes, opens the public link in a fresh context, submits, sees the confirmation page, and the row appears in the "Intake" grid with the submission linked.
- `public_form_mobile_submit` — FR-F014-03, FR-F014-13, NFR-F014-03: 375 px viewport; "Type" = "Purchase" reveals "Budget"; attaches one file; sticky submit works; confirmation shown.
- `embedded_form_submits_in_iframe` — FR-F014-16: host page embeds the snippet; submission inside the iframe succeeds; a host outside `frame_ancestors` is blocked.
- `closed_form_shows_notice` — FR-F014-15: clock moved past `closes_at`; public page shows the closed notice and no submit control.
- `validation_error_focuses_field` — FR-F014-12: invalid email pattern shows the configured message and moves focus to the field.
- `revoked_link_shows_not_found` — FR-F014-05: admin revokes the token; the open public page reloads to the not-found page without tenant details.
- `submitter_cannot_open_builder` — FR-F014-18: submitter navigates to the builder URL and sees the denied state.
- `draft_survives_reload` — FR-F014-14: requester fills three fields, reloads, values restored, submission succeeds.

Evidence: Playwright traces and videos under `testing/evidence/F014/e2e/`.
