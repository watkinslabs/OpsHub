# F032 frontend cases

File: `testing/features/F032/frontend/{HealthCard.test.tsx,OverrideDialog.test.tsx,GateTimeline.test.tsx,SubmitGateDialog.test.tsx,DecideGateDialog.test.tsx,IntakeForm.test.tsx,IntakeStatusPage.test.tsx,HealthModelEditor.test.tsx}`. Vitest with MSW. Flag `F032_FEATURE`.

- `health_card_shows_score_confidence_and_indicators` — FR-F032-14: fixture renders `Amber 61`, `confidence 100`, five indicator bars with inputs tooltips.
- `colour_has_text_label` — NFR-F032-03: every colour swatch has a visible text label and `aria-label`.
- `health_card_shows_override_banner` — FR-F032-06: overridden fixture shows `Overridden to Red by Dana: Vendor contract at risk` and time.
- `health_card_shows_expired_override` — FR-F032-06: past `expires_at` shows grey `Override expired` and effective colour from computed.
- `rejects_short_reason` — FR-F032-06: 9-character reason blocks save; server `invalid` rolls back optimistic colour.
- `renders_gates_in_sequence_with_decision` — FR-F032-07, FR-F032-09: ordered list shows three gates, approved gate shows approver and date.
- `submit_dialog_blocks_until_evidence_complete` — FR-F032-08: submit disabled until file picked and checklist complete.
- `shows_sequence_conflict_message` — FR-F032-08: `gate_sequence` conflict renders `Gate 1 must be approved first`.
- `hidden_for_non_approver` — FR-F032-13: editor session sees no `Approve`/`Reject` buttons; approver sees them.
- `decide_dialog_requires_reason_for_reject` — FR-F032-09: reject without reason blocks submit.
- `intake_form_validates_required_fields` — FR-F032-11: missing template, name, or budget shows field errors; currency must be three letters.
- `intake_status_polls_to_provisioned` — FR-F032-12: statuses `submitted` → `provisioning` → `provisioned` render in turn and the project link appears.
- `blocks_save_when_weights_not_hundred` — FR-F032-01: live total shows 99 and save is disabled.
- `shows_error_banner_with_correlation_id` — NFR-F032-04: 500 response shows banner with `correlation_id` and retry.
- `shows_empty_gates_state` — FR-F032-14: no gates renders `No gates defined by this template`.

Evidence: Vitest JUnit under `testing/evidence/F032/frontend/`.
