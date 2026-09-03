# F040 e2e cases

File: `testing/features/F040/e2e/{insights.spec.ts,approval_gate.spec.ts,injection.spec.ts}`. Playwright against the seeded tenant with the F039 provider stub. Flag `F040_FEATURE`.

- `scan_review_evidence_and_apply` — FR-F040-01, FR-F040-03, FR-F040-09, FR-F040-11, FR-F040-13: the manager runs `Scan now` on `Launch plan`, opens the top `schedule_risk` insight, checks the four evidence rows and their versions, proposes `shift_dates +5 days`, reviews the diff, confirms, and sees the timeline reach `applied` with the four rows changed in the grid.
- `confirm_dialog_restates_target_count_and_risk` — FR-F040-11, FR-F040-17: the dialog states the target count, the risk class, and that the run executes as the confirming user; cancelling leaves the proposal `pending` and nothing changed.
- `high_risk_waits_for_approval` — FR-F040-12: confirming a `create_workflow_draft` proposal shows `Waiting for approval`; the approver approves in `/approvals`; the timeline then shows the draft created; a denial instead shows `Rejected`.
- `dismiss_and_suppress_kind` — FR-F040-08: dismissing with `kind_for_scope` removes the card and a re-scan does not bring it back; the suppression is visible on the filter chip.
- `viewer_cannot_propose_or_confirm` — FR-F040-11, NFR-F040-02: a `resource-viewer` sees insights but no `Propose action` control, and a direct confirm request is denied.
- `markup_payload_renders_as_literal_text` — FR-F040-16: an insight derived from a comment containing `<img onerror=alert(1)>` displays the literal text and the DOM snapshot contains no injected element.
- `budget_exhausted_blocks_scan` — FR-F040-15: on the near-ceiling tenant, `Scan now` shows the budget message and the stub transcript records no provider call.

Evidence: Playwright traces, DOM snapshots, and provider stub transcripts under `testing/evidence/F040/e2e/`.
