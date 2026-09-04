---
id: F009
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M1
parent_epic: E002
depends_on: [F007]
blocks: [F035, F012, F053]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/persistence/src/links/**, crates/domain/src/links/**, services/api/src/links/**, apps/web/src/features/links/**, services/api/migrations/*_links_*.sql, testing/features/F009/**]
feature_flag: F009_FEATURE
flag_default: off
branch: f009-hierarchy-and-links
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 9
- Capability contract: `docs/capability-contracts.md` row F009

# F009 — Hierarchy and links

## 1. Identity and dates

- Branch: `f009-hierarchy-and-links`
- Capability area: core work record engine (spec 5.1 WORK-02 subtasks, WORK-04 WBS hierarchy, hierarchy low-level bullet; 5.2 DATA-02 cross-sheet references and linked records; section 4 Link entity and row rules "moves and hierarchy changes are events")
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 9; `docs/capability-contracts.md` row F009
- Module slug: `links`; aggregate: `row-link`

## 2. Requirement specification

### Problem and user outcome

Work is rarely flat. A project row has phases, phases have tasks, and a task's cost or status should summarize its children. Teams also keep related records in different sheets (a rate card, a customer list) and today copy values by hand, which drift. They need parent/child rows with configurable roll-ups and typed links to records in other sheets that survive renames and report when the target disappears.

As a sheet editor, I want to indent rows under a parent, see parent cells summarize their children, and link a cell to a row in another sheet by its stable ID, so that my sheet models real work breakdown and related data without duplication.

### Functional requirements

- **FR-F009-01:** `POST /api/v1/rows/{id}/indent` makes the row a child of the previous visible sibling in the same group, sets `row_hierarchy.parent_row_id`, `depth`, `path`, and `child_position`, moves the row's existing descendants with it, requires `If-Match` on the row version, and emits `row.reparented.v1` with `changed_fields: [parent_row_id, depth, path]`.
- **FR-F009-02:** `POST /api/v1/rows/{id}/outdent` moves the row to the position directly after its current parent at the parent's depth, carrying its descendants, and emits `row.reparented.v1`; outdenting a root row returns `400 invalid` with `field_errors.row_id = "already_root"`.
- **FR-F009-03:** Indent is rejected with `400 invalid` and `field_errors.row_id = "no_previous_sibling"` when the row is first in its group, `"depth_exceeded"` when the resulting depth of any moved descendant would exceed 20, and `"cycle"` when the target parent is the row itself or one of its descendants.
- **FR-F009-04:** `GET /api/v1/rows/{id}/children` returns direct children ordered by `child_position` with cursor paging (`limit` ≤ 500) and, with `depth=all`, the full subtree in depth-first `path` order including `depth` and `has_children` per row; soft-deleted rows are excluded.
- **FR-F009-05:** Soft-deleting a parent row through F006 soft-deletes its descendants in the same transaction; restoring the parent restores the descendants; restoring a child whose parent is still deleted returns `409 conflict` with `field_errors.parent_row_id = "deleted"`.
- **FR-F009-06:** `PUT /api/v1/columns/{id}/rollup` stores one `rollup_rules` row for a non-formula column with `function` one of `sum|min|max|avg|count|any|all|first|last|weighted_percent`, `source_column_id` (same sheet, type compatible with the function), an optional filter stored as at most one `rollup_rule_filters` row (a typed comparison naming a sibling column by foreign key), and for `any|all` on `select` columns an ordered priority stored as `rollup_rule_status_priorities` rows, one per option, replaced atomically with the rule; a `weighted_percent` rule additionally names `weight_column_id` of type `number` or `duration`; `{ function: null }` removes the rule and emits `rollup.recomputed.v1` with `cell_count` 0.
- **FR-F009-07:** After any `row.updated.v1`, `cell.updated.v1`, `cells.bulk-updated.v1`, `rows.bulk-updated.v1`, `row.reparented.v1`, `row.deleted.v1`, or `row.restored.v1` event on a sheet with roll-up rules, the consumer recomputes only the ancestors of the changed rows for the affected columns, writes each parent cell `raw` and `display` through the F006 `CellRepository` and its `cell_validation_states` row with state `valid`, and emits one `rollup.recomputed.v1` per column with `cell_count` and `duration_ms`.
- **FR-F009-08:** While a roll-up is being recomputed the parent cell keeps its previous value with `validation.state = pending`; a parent cell under a roll-up rule rejects direct edits from F008 with `400 invalid` and `field_errors.value = "rolled_up"`; a parent with no children shows blank with `validation.state = valid`.
- **FR-F009-09:** `POST /api/v1/links` with `{ source_row_id, source_column_id, target_sheet_id, target_row_id, target_column_id, link_type: inbound|outbound|bidirectional, sync_direction: pull|push|both }` requires `sheet-editor` on the source sheet and `sheet-viewer` on the target sheet, requires a source column of type `link`, requires the target column type to be one of the source column's `settings.accepted_types`, writes `cell_links`, copies the target cell value into the source cell `display`, and emits `link.created.v1`.
- **FR-F009-10:** `GET /api/v1/links` filters by `source_row_id`, `source_column_id`, `target_sheet_id`, `target_row_id`, or `status`, pages by cursor, and returns each link with the target sheet name and target row primary value that the actor is allowed to read; links whose target the actor cannot read are returned with `target_redacted: true` and no target values.
- **FR-F009-11:** `PATCH /api/v1/links/{id}` may change `target_row_id`, `target_column_id`, `link_type`, and `sync_direction` with `If-Match`; `DELETE /api/v1/links/{id}` soft-deletes the link, clears the source cell display, and emits `link.deleted.v1`; both re-run the target access and type checks.
- **FR-F009-12:** When a target row or target sheet is soft-deleted, or the target column is deleted or changes to an incompatible type, the consumer sets `cell_links.status = broken`, sets the source cell `validation.state = invalid` with code `broken_link`, and emits `link.updated.v1` with `changed_fields: [status]`; restoring the target reverses this within the same consumer.
- **FR-F009-13:** With `sync_direction = pull` or `both`, a `cell.updated.v1` on the target cell copies the new value into the source cell `display` and emits `link.updated.v1`; with `push` or `both`, an F008 edit on the source cell writes the target cell through the F008 domain service under the actor's target-sheet permission and returns `403 denied` when the actor lacks `sheet-editor` there.
- **FR-F009-14:** A target `sheet_id` or `row_id` belonging to another tenant, or a sheet the actor cannot read, returns `404 not_found` on create and patch; a viewer or commenter receives `403 denied` on indent, outdent, link create, link patch, link delete, and rollup put.
- **FR-F009-15:** The web grid shows hierarchy with indent guides, expand/collapse per parent, indent and outdent controls, linked cells as chips naming the target sheet with a broken state, a link picker that searches target rows, and a roll-up rule editor in the column header menu; every state (loading, empty, error, denied, pending, broken, conflict) is visible.
- **FR-F009-16:** Every mutation requires `Idempotency-Key`, writes an `audit_events` row with actor, action, before/after diff, and correlation ID, and publishes the matching event through the outbox in the same transaction.

### Non-functional requirements

- **NFR-F009-01 Performance:** `GET /children?depth=all` on a subtree of 10,000 descendants responds in under 500 ms p95 warm; indent and outdent respond in under 800 ms p95 including descendant path rewrites; a roll-up recompute over a 5,000-row tree with 5 rules completes in under 5 s.
- **NFR-F009-02 Security/privacy:** every hierarchy and link query carries the `tenant_id` predicate; link targets are checked against the target sheet ACL at creation, patch, read, and sync time; redacted targets never expose values through list, cell display, or events.
- **NFR-F009-03 Accessibility:** the grid uses `treegrid` semantics with `aria-level`, `aria-expanded`, and `aria-setsize`; indent/outdent and link actions are keyboard reachable; screen readers announce level changes and broken-link states; no serious axe violations.
- **NFR-F009-04 Reliability/observability:** the roll-up and link consumers are idempotent per `(aggregate_id, version)`; metrics `rollup_recompute_duration_ms`, `rollup_recompute_cells`, `links_broken_total`; spans carry `tenant_id`, `sheet_id`, `row_id`, `link_id`, and `correlation_id`.

### Scope

Included: row hierarchy table and path maintenance, indent/outdent, children listing, cascading soft delete/restore, roll-up rules and recompute consumer, cell links with typed compatibility, pull/push sync, broken-link detection, hierarchy and link UI, roll-up rule editor.

Excluded: formula functions `CHILDREN`/`PARENT`/`ANCESTORS`/`DESCENDANTS` (F035 reads `row_hierarchy`), schedule dependencies and Gantt roll-up of dates through working calendars (F012), reference-data synchronization across many sheets (F053), report joins (F021), portfolio roll-ups (F031), comments and attachments on linked rows (F016, F017).

## 3. UX specification

- Entry points: row context menu and toolbar `Indent` / `Outdent`; expand/collapse chevron on parent rows; `link` column cell click opens `LinkPicker`; column header menu `Roll-up` on number, currency, duration, date, select, and boolean columns.
- Primary flow: select row "Design", press `Indent`; the row nests under "Phase 1" with an indent guide and `Phase 1` shows a chevron; open `Cost` header menu, choose `Roll-up: sum of Cost`; `Phase 1` Cost shows a shimmer then `4,200`; click the `Vendor` link cell, search "Acme", pick the row from sheet `Vendors`; the cell shows a chip `Acme · Vendors`.
- Loading: shimmer on children while the subtree loads and on parent cells with `pending`; Empty: parent with no children shows a blank rolled-up cell; Error: banner with `correlation_id` and retry; Broken: chip turns amber with icon `Unlink` and tooltip "Target row deleted"; Denied: indent/outdent and link controls hidden for viewers, rolled-up cells show a lock tooltip "Computed from children"; Conflict: stale `If-Match` shows the reload banner; Success: toast on rule save.
- Permission-denied: link picker lists only sheets the actor can read; redacted targets render as `Restricted` chips with no value.
- Responsive: indent guides collapse to a depth badge under 768 px; link picker becomes a full-screen sheet under 640 px.
- Keyboard: `Tab` and `Shift+Tab` on a focused row (not in cell edit) indent and outdent; `ArrowRight`/`ArrowLeft` expand and collapse; `Enter` on a link cell opens the picker; `Escape` closes; focus returns to the originating cell; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `IndentIncrease`, `IndentDecrease`, `ChevronRight`, `Link2`, `Unlink`, `Sigma`; colors and spacing from `apps/web/src/design/tokens.css`.

## 4. Technical specification

Canonical contract: `docs/capability-contracts.md` row F009.

### Rust backend

- Domain entities in `crates/domain/src/links/`: `RowHierarchy { tenant_id, row_id, sheet_id, parent_row_id: Option<RowId>, depth: u8, path: String, child_position: FracIndex, version }`, `CellLink { id, tenant_id, source_row_id, source_column_id, target_sheet_id, target_row_id, target_column_id, link_type: LinkType, sync_direction: SyncDirection, status: LinkStatus, version, created/updated actor+time, deleted_at }`, `RollupRule { id, tenant_id, column_id, function: RollupFunction, source_column_id, weight_column_id: Option<ColumnId>, status_priority: Vec<OptionId>, filter: Option<RollupFilter>, version }` with the priority list and the filter loaded from their child tables.
- Modules: `hierarchy.rs` (path maintenance, subtree moves, depth check), `hierarchy_service.rs`, `link.rs`, `link_service.rs`, `rollup.rs` (functions and type compatibility), `rollup_service.rs`, `consumer.rs` (outbox subscriptions for roll-up recompute, pull sync, broken-link detection), `errors.rs`.
- Data access (decision 2.1): `RowHierarchyRepository` (`row_hierarchy`), `CellLinkRepository` (`cell_links`), and `RollupRuleRepository` (`rollup_rules`, `rollup_rule_status_priorities`, `rollup_rule_filters`) in `crates/persistence/src/links/`; recomputed cells are written through the F006 `CellRepository` and their validation rows through the F007 `CellValidationStateRepository`, so no table gains a second writer. The use cases below, the outbox consumers in `consumer.rs`, and the recompute job depend on those repository traits and the shared `UnitOfWork` and hold no SQL; subtree scans, reverse link lookups, and ancestor resolution are named repository queries (`subtree_by_path`, `links_to_target`, `ancestors_of`).
- Use cases: `indent_row`, `outdent_row`, `list_children`, `cascade_delete_subtree`, `cascade_restore_subtree`, `create_link`, `update_link`, `delete_link`, `list_links`, `set_rollup_rule`, `recompute_rollups(sheet_id, changed_row_ids, column_ids)`, `handle_change_event`.
- API endpoints (`services/api/src/links/`): `POST /api/v1/rows/{id}/indent`, `POST /api/v1/rows/{id}/outdent`, `GET /api/v1/rows/{id}/children`, `GET /api/v1/links`, `POST /api/v1/links`, `PATCH /api/v1/links/{id}`, `DELETE /api/v1/links/{id}`, `PUT /api/v1/columns/{id}/rollup`. DTOs `ReparentResponse { row_id, parent_row_id, depth, path, version }`, `ChildrenQuery { cursor?, limit?, depth? }`, `Page<ChildRowResponse>`, `CreateLinkRequest`, `UpdateLinkRequest`, `LinkResponse { ..., target_sheet_name, target_primary_value, target_redacted, status }`, `SetRollupRequest`, `RollupRuleResponse`.
- Events: `row.reparented.v1` (aggregate `row_id`), `link.created.v1`, `link.updated.v1`, `link.deleted.v1` (aggregate `link_id`), `rollup.recomputed.v1` (aggregate `column_id`, `cell_count`, `duration_ms`); contract envelope through the outbox. F035 subscribes to `row.reparented.v1`, `link.updated.v1`, and `rollup.recomputed.v1`, and its `CHILDREN`/`PARENT` functions read `row_hierarchy` through `HierarchyReader`.
- Authorization: `sheet-editor` on the source sheet for all mutations; `sheet-viewer` on the target sheet for link create/patch/read; push sync requires `sheet-editor` on the target; missing access maps to `not_found` for target IDs and `denied` for role failures on the source.
- Validation: depth ≤ 20; `limit` 1–500; `link_type` and `sync_direction` enums; roll-up function/type matrix (`sum|avg|min|max` on number, currency, duration; `min|max` also on date and datetime; `count` on any; `any|all|first|last` on select and boolean; `weighted_percent` on number with a number or duration weight); the filter row references a column of the same sheet and exactly one value column matching that column's type; priority rows reference options of the source column and carry distinct positions.
- Error mapping: `HierarchyError::NoPreviousSibling | AlreadyRoot | DepthExceeded | Cycle → 400 invalid`, `LinkError::IncompatibleType | NotLinkColumn → 400 invalid`, `RollupError::IncompatibleFunction → 400 invalid`, `StaleVersion → 409 conflict`, `ParentDeleted → 409 conflict`, `NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_links_*.sql` creates `row_hierarchy(tenant_id uuid not null, row_id uuid primary key references rows(id) on delete restrict, sheet_id uuid not null, parent_row_id uuid null references rows(id), depth smallint not null default 0 check (depth between 0 and 20), path text not null, child_position text not null, version bigint not null default 1, updated_by, updated_at)`, `cell_links(id uuid pk, tenant_id uuid not null, source_row_id uuid not null, source_column_id uuid not null, target_sheet_id uuid not null, target_row_id uuid not null, target_column_id uuid not null, link_type text not null check (link_type in ('inbound','outbound','bidirectional')), sync_direction text not null check (sync_direction in ('pull','push','both')), status text not null default 'active' check (status in ('active','broken')), version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `rollup_rules(id uuid pk, tenant_id uuid not null, column_id uuid not null unique, function text not null check (function in ('sum','min','max','avg','count','any','all','first','last','weighted_percent')), source_column_id uuid not null, weight_column_id uuid null, version bigint not null default 1, created_by, created_at, updated_by, updated_at)`, `rollup_rule_status_priorities(tenant_id uuid not null, rollup_rule_id uuid not null references rollup_rules(id) on delete cascade, option_id uuid not null references column_options(id) on delete restrict, position smallint not null, primary key (rollup_rule_id, option_id), unique (rollup_rule_id, position))`, `rollup_rule_filters(rollup_rule_id uuid primary key references rollup_rules(id) on delete cascade, tenant_id uuid not null, column_id uuid not null references columns(id) on delete restrict, operator text not null check (operator in ('eq','ne','lt','lte','gt','gte','contains','is_empty','is_not_empty')), value_text text, value_number numeric, value_datetime timestamptz, value_option_id uuid references column_options(id) on delete restrict)`.
- The roll-up priority list and filter are not `jsonb`: the priority is an ordered set of option ids the product resolves, orders and audits, and the filter is a typed comparison naming a column, so both become tables whose foreign keys stop a rule from surviving the option or column it points at (decision 2). `rollup_rule_status_priorities` keeps the ordering the array had through a `position` column that is unique per rule, and `rollup_rule_filters` is one optional row per rule, so a rule with no filter has no row exactly as `filter is null` meant.
- Invariants: `path` is the dot-joined chain of ancestor row IDs plus the row ID and is unique per sheet (`row_hierarchy_sheet_path_idx`); `parent_row_id` must be in the same sheet (trigger `row_hierarchy_same_sheet`); one active link per `(source_row_id, source_column_id)` enforced by a partial unique index where `deleted_at is null`; `rollup_rules.column_id` unique.
- Indexes: `row_hierarchy(sheet_id, path text_pattern_ops)` for subtree scans, `row_hierarchy(parent_row_id, child_position)` for direct children, `cell_links(target_sheet_id, target_row_id) where deleted_at is null` for reverse lookups and broken-link detection, `cell_links(tenant_id, source_row_id)`, `rollup_rules(tenant_id, column_id)`, `rollup_rule_status_priorities(rollup_rule_id, position)` for ordered reads and `rollup_rule_status_priorities(option_id)` plus `rollup_rule_filters(column_id)` so deleting an option or column finds the rules that depend on it.
- Audit events: `row.indent`, `row.outdent`, `link.create`, `link.update`, `link.delete`, `rollup.set`, `rollup.clear` with field-level diffs; recompute results are not audited.
- Retention/deletion: hierarchy rows follow the row's soft delete; link soft delete sets `deleted_at`; purge from F027 removes both with their rows; a deleted roll-up rule takes its priority and filter rows with it by cascade; rollback drops the five tables and the trigger.

### React/TypeScript

- Routes: none new; components mount inside the F008 grid and the F007 column header menu. Components in `apps/web/src/features/links/`: `HierarchyControls`, `IndentGuide`, `ChildRowsOutline`, `LinkPicker`, `LinkedCellRenderer`, `BrokenLinkBadge`, `RollupRuleEditor`, `RollupCellRenderer`.
- State: TanStack Query keys `['row-children', rowId, depth, cursor]`, `['links', rowId]`, `['links-by-target', sheetId, rowId]`, `['rollup-rule', columnId]`; indent/outdent mutations update the cached row and invalidate `['grid-rows', sheetId]`; link mutations invalidate `['links', rowId]` and the cell.
- API client: generated `LinksApi` with `indentRow`, `outdentRow`, `listChildren`, `listLinks`, `createLink`, `updateLink`, `deleteLink`, `setRollupRule`.
- Optimistic updates: indent/outdent apply locally and roll back on `invalid` or `conflict` with the reason in a toast; link creation shows the chip immediately and reverts on error.
- Telemetry: `row_indented`, `row_outdented`, `subtree_expanded`, `link_created`, `link_removed`, `link_broken_viewed`, `rollup_configured` with `sheet_id`, `row_id`, `column_id`, `depth`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F009-01 through FR-F009-16 in `testing/features/F009/requirements/cases.md`
- [ ] Failure/edge-case tests: indent first row, outdent root, depth 21, indent under own descendant, restore child of deleted parent, link to incompatible type, link to deleted target, push sync without target edit rights, roll-up on formula column
- [ ] Permission-negative and tenant-isolation tests: cross-tenant target `not_found`, unreadable target `not_found`, viewer indent `denied`, redacted target in list
- [ ] Rust unit tests: `crates/domain/src/links/` path rewrite, depth check, roll-up functions per type, status priority, weighted percent
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: depth check, same-sheet trigger, one active link per cell, unique rule per column, rollback
- [ ] React component tests: `HierarchyControls`, `LinkedCellRenderer`, `LinkPicker`, `RollupRuleEditor` states
- [ ] Browser E2E tests: indent, roll-up shows sum, link to another sheet, target deletion breaks link, keyboard indent
- [ ] Accessibility tests: axe on treegrid and picker, level announcements, broken-link announcement
- [ ] Performance/load tests: 10,000-descendant subtree list, indent p95, 5,000-row roll-up recompute

### Fast fanout configuration

- Test harness path: `testing/features/F009/`
- Feature flag: `F009_FEATURE`
- Fixture/seed factory: `testing/fixtures/links.rs` builds tenant A with editor, viewer, and sheets `Plan` (3-level tree, 60 rows, `Cost` number and `Status` select columns) and `Vendors` (20 rows), plus tenant B with a sheet `Foreign`
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC
- Mock/stub contracts: in-memory outbox recorder and consumer harness; authz uses the real F003 engine with fixture bindings; F008 cell write service used through its domain API
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F009`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F009/`

## 6. Acceptance criteria

```gherkin
Feature: Hierarchy and links

Scenario: Indent creates a child and the parent rolls up
  Given rows "Phase 1" and "Design" in sheet "Plan" and a sum roll-up on column "Cost"
  When an editor indents "Design" with Cost 4200
  Then "Design" has parent "Phase 1" and depth 1
  And "Phase 1" Cost shows 4200 after rollup.recomputed.v1

Scenario: Depth limit is enforced
  Given a chain of 21 nested rows
  When an editor indents a row that would make a descendant depth 21
  Then the response is 400 invalid with field_errors.row_id "depth_exceeded"

Scenario: Link to a vendor row
  Given a link column "Vendor" accepting text on sheet "Plan"
  When an editor links a cell to row "Acme" in sheet "Vendors"
  Then the cell displays "Acme", link.created.v1 is published
  And deleting the "Acme" row marks the link broken and the cell invalid

Scenario: Viewer cannot indent or link
  Given a viewer on sheet "Plan"
  When they POST /api/v1/rows/{id}/indent and POST /api/v1/links
  Then both responses are 403 denied and no events are published

Scenario: Cross-tenant target does not leak
  Given a sheet "Foreign" in tenant B
  When an editor in tenant A creates a link targeting it
  Then the response is 404 not_found
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F007 (`link` column type with `accepted_types`, cell validation object, select options for status priority); decisions sections 2–4, 6, 9; contracts row F009
- Blocks: F035, F012, F053
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: path rewrites on a large subtree move are bounded by chunked updates of 5,000 rows per statement inside one transaction; roll-up storms from bulk edits are coalesced per `(sheet_id, column_id)` with a 250 ms debounce in the consumer; push sync into a target sheet the actor cannot edit is rejected before any write so partial sync cannot occur.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F007 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F009/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory `testing/fixtures/links.rs` and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F009_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Rows can be indented into a hierarchy up to 20 levels, parent cells can roll up children with configurable functions, and link columns can reference rows in other sheets with broken-link detection.
- Migration adds `row_hierarchy`, `cell_links`, `rollup_rules`, `rollup_rule_status_priorities`, and `rollup_rule_filters`; rollback drops them. Feature is off by default behind `F009_FEATURE`.
