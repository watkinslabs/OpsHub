# F015 e2e cases

File: `testing/features/F015/e2e/templates.spec.ts`. Playwright against seeded tenant with the in-process worker. Flag `F015_FEATURE`.

- `provision_from_builtin_then_capture_baseline_and_view_variance` — FR-F015-05, FR-F015-06, FR-F015-07, FR-F015-10, FR-F015-12: admin provisions "PMO standard project" into `Ops` as "Q4 launch" starting 2026-10-05, waits for `completed`, opens the sheet, captures "Plan of record", reschedules "Kickoff" +3 working days, variance panel shows `Slipped +3d`.
- `failed_provisioning_shows_rollback` — FR-F015-08: failing-dependency template → status page shows `dependencies` failed, `Rolled back` badge, and the workspace tree has no new sheets.
- `editor_cannot_provision_or_capture` — FR-F015-14: editor sees the catalog without `Provision`, opens baselines without `Capture baseline`, and direct POSTs return 403.
- `publish_then_edit_creates_new_draft` — FR-F015-04: admin publishes version 1, edits the manifest, version history shows draft 2 and immutable 1.
- `gantt_overlay_from_variance_panel` — FR-F015-15: `Open in Gantt` renders baseline bars under current bars for slipped rows.
- `run_poll_denied_for_non_member` — FR-F015-09: user outside `Ops` opens the run URL → not-found page.
- `copy_builtin_and_provision_copy` — FR-F015-05: admin copies the `incidents` built-in, renames it, publishes, provisions it, run completes.

Evidence: Playwright traces and videos under `testing/evidence/F015/e2e/`.
