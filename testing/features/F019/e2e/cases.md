# F019 e2e cases

File: `testing/features/F019/e2e/runs.spec.ts`. Playwright against seeded tenant with API and worker running. Flag `F019_FEATURE`.

- `row_edit_triggers_completed_run` — FR-F019-01, FR-F019-05, FR-F019-14: editor sets `Status` to `Approved` on row "Kickoff"; runs page shows a run moving to `Completed`; `Owner` column is set.
- `failed_run_retry_from_browser` — FR-F019-06, FR-F019-12: workflow with unreachable webhook fails; editor opens detail, reads error, clicks `Retry`, run re-queues after the webhook stub is fixed and completes.
- `cancel_running_run` — FR-F019-12: long-running step; editor cancels; status `Cancelled` after the step boundary.
- `inbound_webhook_creates_run` — FR-F019-04: signed POST to the token URL; run appears with trigger `webhook_received`.
- `disabled_workflow_stops_runs` — FR-F019-13: disable workflow; editing a row creates no new run; old runs still listed.
- `viewer_read_only_runs` — FR-F019-14: viewer login sees runs with no retry or cancel controls.
- `keyboard_only_retry` — NFR-F019-03: no mouse; arrow to failed run, `Enter`, `R`, confirm; run re-queued and announced.

Evidence: Playwright traces and videos under `testing/evidence/F019/e2e/`.
