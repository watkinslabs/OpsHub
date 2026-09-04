---
id: T279
type: task
status: planned
parent_epic: E003
parent_feature: F070
parent_story: S140
depends_on: [S140, T278]
owned_paths: [apps/web/src/features/trash/**, services/api/src/trash/**, crates/domain/src/trash/**, testing/features/F070/frontend/**, testing/features/F070/api/**]
feature_flag: F070_FEATURE
branch: t279-trash-ui
started_at: null
finished_at: null
---

# T279 — Trash UI

## Identity

- Parent story: `S140` Restore and purge
- Owner: platform
- Branch: `t279-trash-ui`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6; `docs/capability-contracts.md` row F070; `docs/authorization-model.md` section 3.3

## Objective

Build the `/trash` screen and the purge-now action it drives: the table with its filters, countdown and blocked reasons, the restore and purge dialogs, and the `DELETE` route that only a compliance administrator may reach.

## Specification

- Owned paths: `apps/web/src/features/trash/{TrashPage.tsx, TrashFilters.tsx, TrashTable.tsx, TrashRow.tsx, RestoreDialog.tsx, PurgeDialog.tsx, BlockedReason.tsx, StaleBanner.tsx, EmptyTrash.tsx, api.ts, hooks.ts, routes.ts}`, `services/api/src/trash/handlers_purge.rs`, `crates/domain/src/trash/purge.rs`
- Contract/input: `TrashApi.listTrash(query)`, `restoreItem(kind, id)` and `purgeItem(kind, id, ifMatch)` from the generated client; `DELETE /api/v1/trash/{kind}/{id}` takes `Idempotency-Key` and `If-Match` carrying the entry's `source_version`.
- Output/behavior: `TrashPage` renders `DataGridPanel` with kind icon, title, original location, deleter, deleted time, days remaining and state, filters by kind, workspace, person and date range, and supports multi-select bulk restore; a `held` row shows the hold chip in place of the countdown; a `blocked` row shows `BlockedReason` with `Restore parent first` linking to the parent's entry; `StaleBanner` appears when the page envelope reports `stale`; `EmptyTrash` explains retention rather than showing a denied page, because for a caller who may read nothing the empty list is the correct answer; `RestoreDialog` names the destination path and the child count; `PurgeDialog` is the destructive variant, requires the item title retyped, traps focus, announces the result and returns focus to the row; `Purge` is rendered disabled with its reason for anyone without `compliance-admin`; `handlers_purge.rs` and `purge.rs` check `compliance-admin`, consult `LegalHoldPort::is_held` and return `409 conflict` code `legal_hold` when held, otherwise execute through `PurgeExecutorPort`, write the `trash.purge` audit event, publish `item.purged.v1` and return `204`. Colour, spacing, type and motion come from tokens; components come from `apps/web/src/ui` and icons from its registry.
- Data access: the web feature calls only the generated client; `purge.rs` and the handler hold no SQL and reach the owning tables through `TrashTarget::purge` and the entry row through `TrashEntryRepository` (decision section 2.1).
- Dependencies: T278 for the index and restore paths; F062 primitives, tokens and pattern components; F027 hold and purge executor ports.
- Feature flag: `F070_FEATURE` gates the route and the `DELETE` handler.

## TDD

- Failing test first: `testing/features/F070/frontend/TrashTable.test.tsx::renders_kind_location_deleter_and_countdown`, `::held_row_shows_hold_chip_instead_of_countdown`, `::blocked_row_offers_restore_parent_first`; `testing/features/F070/frontend/PurgeDialog.test.tsx::purge_dialog_requires_retyped_title`, `::purge_disabled_with_reason_without_compliance_admin`, `::purge_under_hold_shows_hold_name`; `testing/features/F070/frontend/TrashPage.test.tsx::shows_stale_banner_when_envelope_is_stale`, `::empty_state_explains_retention_for_a_caller_who_sees_nothing`, `::error_banner_shows_correlation_id`; `testing/features/F070/api/purge_tests.rs::purge_requires_compliance_admin`, `::purge_under_hold_returns_legal_hold_conflict`, `::purge_runs_through_shared_executor`, `::purge_rejects_stale_if_match`, `::purge_publishes_item_purged_and_audits`
- Targeted command: `cargo xtask test-feature F070`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/trash.rs` with MSW handlers for the three routes; a `PurgeExecutorPort` spy, a `LegalHoldPort` stub with a programmable held set, and both themes and densities for the component tests

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Route mounted in the web router at `/trash` and the workspace overflow menu entry added behind the flag
- [ ] No literal colour, spacing or duration; no direct vendor import; icons only through the registry
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S140
- [ ] `finished_at` recorded
