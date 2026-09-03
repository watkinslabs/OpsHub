---
id: T199
type: task
status: planned
parent_epic: E008
parent_feature: F050
parent_story: S100
depends_on: [S100]
owned_paths: [crates/domain/src/dynamic-views/**, services/api/src/dynamic-views/**, apps/web/src/features/dynamic-views/**, testing/features/F050/api/**, testing/features/F050/frontend/**]
feature_flag: F050_FEATURE
branch: t199-restricted-ui
started_at: null
finished_at: null
---

# T199 — Restricted UI

## Identity

- Parent story: `S100` Controlled editing
- Owner: platform
- Branch: `t199-restricted-ui`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6; `docs/capability-contracts.md` row F050

## Objective

Implement the controlled row edit route with edit records and build the restricted grid, policy editor, audience panel, public link dialog, edits log, and public view page wired to the real API.

## Specification

- Owned paths: `crates/domain/src/dynamic-views/{edit.rs, edit_check.rs, service_edits.rs}`, `services/api/src/dynamic-views/{handlers_edit.rs, rate_limit.rs}`, `apps/web/src/features/dynamic-views/{DynamicViewPage.tsx, RestrictedGrid.tsx, RestrictedCell.tsx, PolicyEditor.tsx, PredicateBuilder.tsx, FieldPicker.tsx, EditModeSelect.tsx, AudiencePanel.tsx, PublicLinkDialog.tsx, PreviewAsSelector.tsx, EditsLog.tsx, PublicViewPage.tsx, LinkInactivePage.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `EditRowRequest { cells: { column_id: value }, version }` with `Idempotency-Key`; generated `DynamicViewsApi`; route params `workspaceId`, `id`, `token`; `preview_as` query honoured for the owner only.
- Output/behavior: `PATCH /api/v1/dynamic-views/{id}/rows/{row_id}` runs `check_edit` in the transaction, applies via the F008 cell service as the owner with `on_behalf_of`, writes `dynamic_view_edits`, publishes `dynamic-view.row-edited.v1`, and enforces 60 token writes per minute; `RestrictedGrid` shows visible fields with editable cells marked and locked cells announced, optimistic edits with rollback on `conflict`/`denied`; `PolicyEditor` builds the predicate tree with depth and leaf limits mirrored client-side; `PublicLinkDialog` shows the raw link once with copy and revoke; `EditsLog` pages `['dynamic-view-edits', id, cursor]`; `PublicViewPage` renders the grid for `/dv/:token` and `LinkInactivePage` for `403`; states loading, empty, error with correlation ID, denied, stale, offline, module-not-entitled; telemetry `dynamic_view_policy_saved`, `dynamic_view_token_enabled`, `dynamic_view_token_revoked`, `dynamic_view_row_edited`, `dynamic_view_public_opened`.
- Dependencies: T198 routes and token; F008 cell service `apply_cells(actor, on_behalf_of, ...)`; F048 `useModuleAllowed('dynamic-views')` and `ModuleNotEntitled`; F013 grid primitives for cell rendering.
- Feature flag: `F050_FEATURE` read through the flag hook; routes not registered when off.

## TDD

- Failing test first: `testing/features/F050/api/edit_tests.rs::edit_outside_editable_fields_denied`, `::edit_assigned_rows_only_for_current_user`, `::edit_row_outside_filter_not_found`, `::edit_writes_record_and_event`, `::token_edit_rate_limited_at_61`, `::allow_new_rows_prefills_filter_values`; `testing/features/F050/frontend/RestrictedGrid.test.tsx::renders_only_visible_fields`, `::locks_read_only_cells`, `::rolls_back_on_denied`, `PolicyEditor.test.tsx::blocks_editable_not_visible`, `PublicLinkDialog.test.tsx::shows_link_once_and_revokes`, `PublicViewPage.test.tsx::inactive_token_shows_no_tenant_details`
- Targeted command: `cargo xtask test-feature F050`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the seeded view; two vendor users; role-switching session helper

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] API and component lanes pass; edit route mounted in `services/api/src/dynamic-views/routes.rs`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S100
- [ ] `finished_at` recorded
