---
id: T160
type: task
status: planned
parent_epic: E008
parent_feature: F040
parent_story: S080
depends_on: [S080]
owned_paths: [crates/domain/src/ai-insights/**, testing/features/F040/api/**, testing/features/F040/e2e/**, testing/features/F040/accessibility/**, testing/features/F040/requirements/**]
feature_flag: F040_FEATURE
branch: t160-red-team-tests
started_at: null
finished_at: null
---

# T160 — Red-team tests

## Identity

- Parent story: `S080` Assisted actions
- Owner: platform
- Branch: `t160-red-team-tests`
- Decision references: `docs/architecture-decisions.md` sections 3, 7; `docs/capability-contracts.md` row F040

## Objective

Build the prompt-injection corpus and the adversarial suite that proves user-authored content cannot make the assistant fabricate evidence, cross a tenant boundary, widen the action allowlist, self-confirm an action, or inject markup into the insights UI. Implement the output sanitiser the suite drives.

## Specification

- Owned paths: `crates/domain/src/ai-insights/sanitize.rs`; `testing/features/F040/api/fixtures/injection/{exfiltration.json, escalation.json, allowlist.json, fabrication.json, markup.json, schema_break.json}`; `testing/features/F040/api/injection_tests.rs`; `testing/features/F040/e2e/injection.spec.ts`; `testing/features/F040/accessibility/insights.a11y.spec.ts`; `testing/features/F040/requirements/cases.md`
- Contract/input: 40 payloads across six vectors, each fixture entry `{ id, vector, carrier, payload, expectation }` where `carrier` is one of `row_text`, `comment_body`, `column_name`, `file_name`, `approval_note`, `workflow_step_name`, and `vector` is one of `exfiltration`, `escalation`, `allowlist`, `fabrication`, `markup`, `schema_break`. `sanitize(text) -> String` escapes `<`, `>`, `&`, `"` and strips markdown link and image syntax, leaving server-generated `deep_link` values as the only clickable targets.
- Output/behavior: the suite seeds each payload into tenant A content, runs a scan and a proposal against a provider stub that faithfully relays the injected instruction, and asserts that no `ai_actions` row is ever created with `status: confirmed` without a human confirm call; that every evidence reference resolves inside the retrieval set and any other reference discards the whole insight with `ai-insight.evidence-rejected`; that tenant B ids named in payloads never appear in any insight, event, log line, or prompt; that a payload naming `delete_rows` or `share_externally` never produces an accepted `action_kind`; that a narration violating the response schema is discarded rather than coerced; that markup payloads render as literal text with zero elements created in the DOM; and that each block writes `ai-insight.injection-blocked` with the vector and increments `ai_injection_blocked_total{vector}`. The requirements lane maps every FR and NFR id to its lane and case. A positive control removes the sanitiser and the index binding to prove the suite turns RED, then restores them.
- Dependencies: T157 scan and narration binding; T158 gate; T159 proposal and executor; the F039 provider stub for relaying payloads verbatim; F027 redaction list for the log assertions.
- Feature flag: `F040_FEATURE` gates the suite; it runs in both targeted and full modes and in the nightly security job.

## TDD

- Failing test first: `testing/features/F040/api/injection_tests.rs::injected_comment_cannot_create_confirmed_action`, `::injected_row_text_cannot_reference_other_tenant_records`, `::injected_payload_cannot_add_action_kind_outside_allowlist`, `::injected_payload_cannot_fabricate_evidence_ids`, `::narration_breaking_response_schema_is_discarded`, `::injection_block_writes_audit_and_metric`, `::prompt_never_contains_records_outside_retrieval_set`; `testing/features/F040/api/sanitize_tests.rs::escapes_html_in_summary`, `::strips_markdown_links_and_images`, `::keeps_server_generated_deep_links`; `testing/features/F040/e2e/injection.spec.ts::markup_payload_renders_as_literal_text`, `::confirm_dialog_cannot_be_auto_submitted_by_content`; `testing/features/F040/accessibility/insights.a11y.spec.ts::insights_routes_have_no_serious_violations`
- Targeted command: `cargo xtask test-feature F040`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: the six injection fixture files with 40 payloads total; a provider stub mode that echoes the injected instruction into the narration; tenant B seed records used only as forbidden strings in assertions; DOM snapshot assertions in Playwright

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] All 40 payloads pass with their recorded expectation; the corpus is versioned and each payload cites the vector it covers
- [ ] Positive control recorded: sanitiser and index binding removed → RED, restored → GREEN, evidence under `testing/evidence/F040/`
- [ ] Requirements lane maps every FR-F040 and NFR-F040 id
- [ ] Owned-path check, file limit, and lint gates pass
- [ ] Handoff evidence recorded in S080
- [ ] `finished_at` recorded
