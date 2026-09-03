---
id: S080
type: story
status: planned
parent_epic: E008
parent_feature: F040
depends_on: [F040]
owned_paths: [crates/domain/src/ai-insights/**, services/api/src/ai-insights/**, services/worker/src/ai-insights/**, apps/web/src/features/ai-insights/**, testing/features/F040/**]
feature_flag: F040_FEATURE
branch: s080-assisted-actions
started_at: null
finished_at: null
---

# S080 — Assisted actions

## Identity

- Parent feature: `F040` AI insights/automation
- Owner: platform
- Branch: `s080-assisted-actions`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 7; `docs/capability-contracts.md` row F040
- Child tasks: `T159` cost/safety controls, `T160` red-team tests

## Vertical slice

As a program manager, I want to turn an insight into a proposed change, see exactly which records would change and how, send high-risk proposals through approvals, and watch the confirmed run apply with my own permissions, so that assisted automation stays bounded, reviewable, affordable, and impossible to trigger by text hidden inside my own data.

## Requirements

- **SR-S080-01:** `POST /api/v1/ai/actions` creates a proposal only: status `pending`, a rendered `before`/`after` diff, `preview_hash`, `target_count` at most 25, `risk_class`, `expires_at = now + 24h`, and `ai-action.proposed.v1`; nothing is written to any target (covers FR-F040-09).
- **SR-S080-02:** `action_kind` is restricted to `set_field`, `assign_owner`, `shift_dates`, `create_workflow_draft`, `request_approval`, and `notify_owner`; parameters are validated against F007 column types and every target id must appear in the parent insight's evidence, otherwise `400 invalid` with `target_not_in_evidence` (FR-F040-10).
- **SR-S080-03:** `risk_class` is `high` for `create_workflow_draft`, `request_approval`, and `target_count > 5`; confirming a high proposal requests an F020 approval, sets `awaiting_approval` with `approval_id`, and executes only on `approval.decided.v1` with `decision: approved`, otherwise the action becomes `rejected` (FR-F040-12).
- **SR-S080-04:** The `ai-insights.action_run` job writes one `ai_action_runs` row per attempt, re-checks the confirming actor's permission on every target at execution time, fails the whole run with `error_class: denied` and no partial writes when a permission was lost, records `applied_targets` with resulting versions, and dead-letters after 2 retries at 1 concurrent run per tenant (FR-F040-13, NFR-F040-04).
- **SR-S080-05:** Safety limits are enforced before any provider call: 4 on-demand scans per tenant per hour, one per identical scope per 15 minutes, a budget reservation through the F039 provider boundary, per-scan caps of 20,000 records, 150,000 prompt tokens, 200 insights, 60 s per detector and 10 minutes total, and a 15-minute circuit breaker after 5 consecutive provider errors (FR-F040-15, NFR-F040-05).
- **SR-S080-06:** Model-authored text is escaped on write and rendered as plain text; the only clickable targets are server-generated `deep_link` values; retrieved record text is wrapped in a delimited untrusted block and cannot change the response schema; blocked attempts write `ai-insight.injection-blocked` with the vector (FR-F040-16, NFR-F040-02).
- **SR-S080-07:** The 40-payload red-team corpus proves that injected text cannot create a confirmed action, reference another tenant's records, widen the action-kind allowlist, fabricate evidence, or inject markup into the UI (FR-F040-04, FR-F040-16, NFR-F040-02).
- **SR-S080-08:** `/insights/actions/:actionId` renders the diff table, risk banner, confirm dialog restating target count and risk class, run timeline, denied and stale-preview states, and the remaining-budget banner for `tenant-admin` (FR-F040-17, NFR-F040-03).

## Surfaces

- Infrastructure/container: worker queue `ai-insights.action_run` with per-tenant concurrency 1 and a dead-letter queue; per-tenant rate-limiter and circuit-breaker state in the shared cache
- Rust service/API: `crates/domain/src/ai-insights/{proposal.rs, preview.rs, risk.rs, executor.rs, budget.rs, sanitize.rs}`; `services/api/src/ai-insights/{handlers_action.rs, dto.rs}`; `services/worker/src/ai-insights/{action_run.rs, approval_listener.rs}`
- Data/migration: no new tables; `ai_actions` and `ai_action_runs` from the S079 migration are populated here, including the `ai_action_runs(tenant_id, idempotency_key)` uniqueness used for replay safety
- React/UI: `apps/web/src/features/ai-insights/{ProposeActionDialog.tsx, ActionPreviewDiff.tsx, ConfirmActionDialog.tsx, ActionRunTimeline.tsx, BudgetBanner.tsx}`
- Mocks/fixtures: `testing/fixtures/ai_insights.rs` action seeds; F008 row-update, F018 draft-create, F020 approval, and F037 notification recorders; the injection corpus in `testing/features/F040/api/fixtures/injection/`

## TDD harness

- Test path: `testing/features/F040/{requirements,api,e2e,accessibility,performance}/`
- Feature flag: `F040_FEATURE`
- Targeted command: `cargo xtask test-feature F040`
- Full command: `cargo xtask test-all`
- First failing tests: `propose_action_writes_nothing_to_targets`, `unknown_action_kind_rejected`, `target_outside_evidence_rejected`, `high_risk_confirm_requests_approval_before_running`, `run_denied_when_permission_lost_after_confirm`, `budget_exhausted_blocks_scan_before_provider_call`, `injected_comment_cannot_create_confirmed_action`, `model_markup_is_escaped_on_render`

## Exit criteria

- [ ] Requirement tests SR-S080-01 through SR-S080-08 written first and observed failing
- [ ] Tasks T159 and T160 complete and wired through the API router and worker registry
- [ ] Unit, API, E2E, permission-negative, accessibility, performance, and red-team tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/ai-insights/handlers_action.rs` mounted through `services/api/src/ai-insights/routes.rs` in `services/api/src/router.rs`; `services/worker/src/ai-insights/action_run.rs` and `approval_listener.rs` registered in `services/worker/src/registry.rs`
- [ ] Handoff evidence recorded in the F040 ticket
