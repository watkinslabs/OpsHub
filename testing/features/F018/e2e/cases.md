# F018 e2e cases

File: `testing/features/F018/e2e/workflow.spec.ts`. Playwright against seeded tenant. Flag `F018_FEATURE`.

- `create_test_publish_workflow` — FR-F018-01, FR-F018-07, FR-F018-09, FR-F018-14: editor opens `Automations`, builds `Status changed` + `Status eq Approved` + `Assign` + `Send in-app`, tests against row "Kickoff", publishes, list shows `Published v1`.
- `edit_after_publish_creates_draft` — FR-F018-06: add a third action to the published workflow; badge shows `Draft changes`; version summary still v1.
- `disable_stops_new_runs_state` — FR-F018-08: disable → badge `Disabled`; publish again → `Published v2`.
- `type_mismatch_blocks_publish` — FR-F018-03: `Amount starts_with` shows inline leaf error and `Publish` disabled.
- `viewer_sees_read_only_builder` — FR-F018-14: viewer login opens the workflow, no publish/disable controls, fields disabled.
- `non_member_sees_not_found` — FR-F018-14: user outside workspace opens workflow URL → not-found page.
- `keyboard_only_authoring` — NFR-F018-03: no mouse; trigger, condition, and two actions authored and reordered with keyboard; publish succeeds.

Evidence: Playwright traces and videos under `testing/evidence/F018/e2e/`.
