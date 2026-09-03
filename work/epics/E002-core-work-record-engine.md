---
id: E002
type: epic
status: planned
owner: platform
target_milestone: M1
branch: e002-core-work-record-engine
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 7, 9
- Capability contract: `docs/capability-contracts.md` rows F005, F006, F007, F008, F009, F035, F010
- Product spec: `docs/product-capability-spec.md` sections 4, 5.1, 5.2, 6

# E002 — Core work record engine

## Outcome

Every OpsHub feature reads and writes one canonical, typed work-record model. After this epic a team can open a workspace, organize sheets in folders, model work as rows with typed columns, edit cells in a virtualized grid with undo and bulk operations, nest rows into a hierarchy with roll-ups, link records across sheets by stable IDs, compute formulas incrementally with clear error codes, search the tenant's work, and move data in and out through CSV/XLSX import and CSV/XLSX/PDF export. Views, forms, automation, reporting, and integrations in later epics are projections over these records rather than new sources of truth (spec section 1.1 "typed work-record engine plus saved projections").

## Scope

- Included: workspaces, membership, and folder trees (F005); sheets, groups, rows, and cells with soft delete and restore (F006); the twelve typed column kinds with normalization and validation states (F007); grid inline editing, paste/fill, multi-select, undo/redo, frozen and per-user column layout, bulk edit, and cell history (F008); parent/child rows, indent/outdent, configurable roll-ups, and cross-sheet cell links (F009); the formula parser, AST, dependency graph, function library, incremental cycle-detected recalculation, and cross-sheet references by stable IDs (F035); tenant-scoped full-text search, CSV/XLSX import with preview, duplicate strategy, dry run, and resumable status, and CSV/XLSX/PDF export with permission filtering (F010). All mutations carry idempotency keys, optimistic versions, audit events, and outbox events.
- Excluded: saved views beyond grid and board (F013), date and working-calendar semantics (F011), dependencies and Gantt (F012), forms (F014), comments and attachments (F016, F017), live multi-user sheet patches (F046), report queries (F021), offline mobile editing (F058), conditional formatting (F060), report and dashboard exports (F025), tenant compliance exports and purge (F027).

## Child features

- F005 Workspace navigation: workspace CRUD, membership replacement, folder tree with move and cycle prevention (depends on F003, F004).
- F006 Sheets/boards/items: sheet, group, row, and cell records with grid and board rendering (depends on F005).
- F007 Typed columns: column lifecycle, twelve column types, normalization, validation engine, and validation states (depends on F006).
- F008 Grid editing: cell edit API, bulk cell/row operations, undo/redo batches, cell history, per-user layouts, virtual grid (depends on F007).
- F009 Hierarchy and links: row hierarchy with indent/outdent, roll-up rules, and cross-sheet cell links (depends on F007).
- F035 Formula engine: parser, function groups, dependency graph, incremental recalculation, error codes, cross-sheet references (depends on F007, F009).
- F010 Search/import/export: search index, import jobs with preview and commit, export jobs with download (depends on F008, F004).

## Exit criteria

- [ ] All seven child features accepted and archived with harness evidence under `testing/evidence/F005` through `testing/evidence/F010` and `F035`.
- [ ] The plan exit scenario runs end to end through the real UI and API: a user creates a workspace and sheet, adds typed columns, edits and validates cells in the grid, indents rows and links a record from another sheet, adds a formula column that recalculates on edit, searches for the row, imports a CSV with preview and dry run, exports XLSX and PDF, and restores a deleted row.
- [ ] The MVP acceptance scenario steps owned by this epic (spec section 8: edit tasks in grid and board views, export data, recover a deleted row) pass in `cargo xtask test-all`.
- [ ] Cross-tenant, role-negative, and guest-link negatives pass for every child feature; every mutation writes an audit event and an outbox event.
- [ ] Load tests meet spec section 6: reads under 500 ms p95 on 100,000-row and 500-column sheets, single-row writes under 800 ms p95, async jobs acknowledged under 2 s, formula recalculation within the 2 s budget.
- [ ] Accessibility (WCAG 2.2 AA), migration safety, contract drift, and feature-flag rollback gates pass for every child feature.
