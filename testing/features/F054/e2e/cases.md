# F054 e2e cases

File: `testing/features/F054/e2e/bridge.spec.ts`. Playwright against seeded tenant with scripted connector mocks. Flag `F054_FEATURE`.

- `build_publish_run_retry_flow` — FR-F054-01, FR-F054-05, FR-F054-06, FR-F054-07, FR-F054-10: editor builds "Jira intake" (trigger, Jira create, approval wait, Slack post, update field), publishes version 1, runs with a test row, approves in the approval inbox, sees the Slack step fail with `rate_limited`, clicks `Retry step`, run reaches `succeeded` and the row shows the Jira key.
- `cycle_blocks_publish_with_highlighted_step` — FR-F054-04: pointing the last step back to step 2 shows the cycle error on publish and no version badge appears.
- `cancel_waiting_run` — FR-F054-09, FR-F054-14: run parked on a 10-minute delay; editor cancels; timeline shows remaining steps `cancelled`.
- `viewer_is_read_only` — FR-F054-14: viewer opens the flow and a run; no publish, run, retry, or cancel controls; forged POST from the console returns 403.
- `not_entitled_panel_shown` — FR-F054-13: tenant with suspended `bridge` entitlement opens `/bridge` and sees the panel with reason `suspended`.
- `flag_off_hides_bridge` — FR-F054-13: with `F054_FEATURE` off, the navigation entry is absent and `/bridge` renders not-found.
- `console_filters_and_pagination` — FR-F054-11: filter `status=failed` shows 12 of 200 runs; next page loads via cursor; deep link to a run opens the timeline.

Evidence: Playwright traces and videos under `testing/evidence/F054/e2e/`.
