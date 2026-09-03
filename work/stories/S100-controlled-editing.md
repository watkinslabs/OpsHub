---
id: S100
type: story
status: planned
parent_epic: E008
parent_feature: F050
depends_on: [S099]
owned_paths: [crates/domain/src/dynamic-views/**, services/api/src/dynamic-views/**, apps/web/src/features/dynamic-views/**, testing/features/F050/**]
feature_flag: F050_FEATURE
branch: s100-controlled-editing
started_at: null
finished_at: null
---

# S100 — Controlled editing

## Identity

- Parent feature: `F050` Dynamic View
- Owner: platform
- Branch: `s100-controlled-editing`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6, 10; `docs/capability-contracts.md` row F050

## Vertical slice

As a vendor or team member with access to a dynamic view, I want to edit the fields the owner marked editable on the rows I am allowed to see, and as the owner I want to build the policy, preview the view, manage the public link, and review every edit, so that external updates flow into the sheet safely and traceably.

Out of this slice: view creation, policy validation, and token resolution (S099, already available); offline edit queueing (F058).

## Requirements

- **SR-S100-01:** `PATCH /api/v1/dynamic-views/{id}/rows/{row_id}` re-runs `check_edit` inside the transaction, rejects keys outside `editable_fields` with `403 denied` and `field_errors.cells.<column_id> = "not_editable"`, rejects rows outside the filter with `404 not_found`, and applies accepted cells through the F008 cell service as the owner with `on_behalf_of` (covers FR-F050-06).
- **SR-S100-02:** `edit_mode: assigned_rows` allows edits only where `assignment_column_id` equals the caller; `all_visible` allows any visible row; `none` returns `403 denied`; `allow_new_rows` creates a row pre-filled with filter equality values (FR-F050-03).
- **SR-S100-03:** Every accepted edit writes `dynamic_view_edits` with actor user or token, before/after cells, `correlation_id`, `applied_version`, and publishes `dynamic-view.row-edited.v1` without cell values (FR-F050-07, FR-F050-10).
- **SR-S100-04:** Token edits require `Idempotency-Key`, are limited to 60 per token per minute (`429 rate_limited`), and are refused when `allow_edit` is false, expired, or revoked (FR-F050-08).
- **SR-S100-05:** `RestrictedGrid` renders visible fields, marks editable cells, blocks others with a lock, applies edits optimistically, and rolls back on `conflict` or `denied` with the reason banner; `PublicViewPage` at `/dv/:token` renders the same grid with the inactive-link page for dead tokens (FR-F050-13, NFR-F050-03).
- **SR-S100-06:** `PolicyEditor`, `AudiencePanel`, `PublicLinkDialog`, `PreviewAsSelector`, and `EditsLog` let the owner author the policy, share, manage the link, preview as a user, and inspect edits with loading, error, denied, stale, and offline states (FR-F050-14).
- **SR-S100-07:** Single edit p95 is under 800 ms and the edit transaction never leaves an edit record without a cell change (NFR-F050-01, NFR-F050-04).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/dynamic-views/{edit.rs, edit_check.rs, service_edits.rs}`; `services/api/src/dynamic-views/{handlers_edit.rs, rate_limit.rs}`
- Data/migration: none new; uses `dynamic_view_edits` from S099
- React/UI: `apps/web/src/features/dynamic-views/{DynamicViewPage.tsx, RestrictedGrid.tsx, RestrictedCell.tsx, PolicyEditor.tsx, PredicateBuilder.tsx, FieldPicker.tsx, EditModeSelect.tsx, AudiencePanel.tsx, PublicLinkDialog.tsx, PreviewAsSelector.tsx, EditsLog.tsx, PublicViewPage.tsx, LinkInactivePage.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: seeded view with `assigned_rows` policy and two vendors; MSW handlers for component tests; Playwright uses the real API with a live token

## TDD harness

- Test path: `testing/features/F050/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F050_FEATURE`
- Targeted command: `cargo xtask test-feature F050`
- Full command: `cargo xtask test-all`
- First failing tests: `edit_outside_editable_fields_denied`, `edit_assigned_rows_only_for_current_user`, `edit_writes_record_and_event`, `token_edit_rate_limited_at_61`, `restricted_grid_locks_read_only_cells`, `owner_policy_to_vendor_edit_round_trip`

## Exit criteria

- [ ] Requirement tests SR-S100-01 through SR-S100-07 written first and failing
- [ ] Tasks T199 and T200 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/dynamic-views/DynamicViewPage.tsx` mounted at `/w/:workspaceId/dynamic-views/:id`; `PublicViewPage.tsx` mounted at `/dv/:token`
- [ ] Handoff evidence recorded in the F050 ticket
