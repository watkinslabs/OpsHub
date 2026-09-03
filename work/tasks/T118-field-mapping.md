---
id: T118
type: task
status: planned
parent_epic: E006
parent_feature: F030
parent_story: S059
depends_on: [S059]
owned_paths: [crates/domain/src/connectors/mapping/**, services/api/src/connectors/**, apps/web/src/features/connectors/**, testing/features/F030/api/**, testing/features/F030/frontend/**, testing/features/F030/accessibility/**]
feature_flag: F030_FEATURE
branch: t118-field-mapping
started_at: null
finished_at: null
---

# T118 — Field mapping

## Identity

- Parent story: `S059` Work sync
- Owner: platform
- Branch: `t118-field-mapping`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 6; `docs/capability-contracts.md` row F030

## Objective

Implement the field mapping layer — the transform catalog and evaluator, mapping validation, the atomic mapping replacement route, the five-record preview — and the `/admin/syncs` wizard and mapping editor that drive them.

## Specification

- Owned paths: `crates/domain/src/connectors/mapping/{mod.rs, transform.rs, validate.rs, preview.rs}`, `services/api/src/connectors/handlers_mapping.rs`, `apps/web/src/features/connectors/{SyncListPage.tsx, SyncWizard.tsx, ConnectionObjectStep.tsx, MappingEditor.tsx, MappingRow.tsx, TransformPicker.tsx, MappingPreview.tsx, PolicyStep.tsx, SyncDetailPage.tsx, RunHistoryTable.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `MappingSetRequest { expected_version, mappings: [{ external_field, column_id, direction, transform: { name, args }, required, default_value? }] }`; preview query `{ limit: 5 }` against the sync's live source.
- Output/behavior: `PUT /api/v1/syncs/{id}/mappings` deletes and reinserts the whole set in one transaction and returns the stored set with the new sync `version`; `transform.rs` implements the closed catalog `identity`, `trim`, `lower`, `upper`, `date_tz(tz)`, `datetime_format(pattern)`, `number_scale(factor)`, `value_map({external: opshub})`, `join(separator)`, `split(separator, index)`, `template(pattern)`, `lookup(sheet_id, key_column_id, value_column_id)` as pure functions with no network or filesystem access beyond `lookup`, a 5 ms per-cell budget, and `MappingError::{UnknownTransform, BadArgument, TypeMismatch, LookupMiss}`; `validate.rs` enforces per-direction uniqueness of `external_field` and `column_id`, the 300-mapping cap, `required` without `default_value` on a nullable external field, and transform output type against the F006 column type, reporting `field_errors["mappings[N].transform"]` and `field_errors["mappings[N].column_id"]`; `preview.rs` reads five source records through the adapter and returns mapped cell values plus per-field errors without writing; the wizard renders three steps with the mapping editor, keyboard reorder on `Alt+ArrowUp`/`Alt+ArrowDown`, a column picker filtered to compatible types, transform argument inputs, and `Preview 5 records`; all UI states — loading, empty, error with `correlation_id`, denied, and success — are rendered.
- Dependencies: T117 for the sync aggregate, routes, and Jira adapter `describe_fields`; F006 column types and the row lookup used by `lookup`; F028 error envelope with `field_errors`; F029 `TokenSource` for the preview call.
- Feature flag: `F030_FEATURE` gates the route and the `/admin/syncs` navigation entry.

## TDD

- Failing test first: `testing/features/F030/api/mapping_tests.rs::replace_mappings_is_atomic_on_validation_failure`, `::replace_mappings_rejects_duplicate_column`, `::replace_mappings_rejects_over_300`, `::required_without_default_rejected`, `::unknown_transform_returns_field_error`, `::transform_output_type_must_match_column`; `testing/features/F030/api/transform_tests.rs::transform_date_tz_converts_to_column_timezone`, `::transform_value_map_falls_back_to_default`, `::transform_lookup_miss_marks_record_mapping_failed`, `::transform_budget_under_five_milliseconds`; `testing/features/F030/api/preview_tests.rs::preview_returns_five_mapped_records_without_writing`; `testing/features/F030/frontend/MappingEditor.test.tsx::filters_column_picker_by_compatible_type`, `::reorders_rows_with_keyboard`; `testing/features/F030/frontend/MappingPreview.test.tsx::shows_per_field_mapping_errors`; `testing/features/F030/accessibility/syncs.a11y.spec.ts::wizard_steps_have_no_serious_violations`
- Targeted command: `cargo xtask test-feature F030`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/connectors.rs` sheet `Delivery board` with text, date, single-select, and person columns; Jira mock `describe_fields` payload including `customfield_10014`; MSW handlers for the mapping and preview routes; timezone `America/Chicago` cases against the fixed clock

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Mapping route mounted through `services/api/src/connectors/routes.rs`; `/admin/syncs` routes registered in the web router behind the flag
- [ ] Owned-path check passes
- [ ] File limit, lint, and axe gates pass
- [ ] Handoff evidence recorded in S059
- [ ] `finished_at` recorded
