# F067 frontend cases

F067 adds no React route, component, hook, generated client operation, or design token. This lane holds the negative controls for that claim and tests the one reader-facing artifact the feature does produce: the Markdown run report.

File: `testing/features/F067/frontend/{report_tests.rs,index_tests.rs,no_web_surface_tests.ts}`. Flag `F067_FEATURE`. Fixtures: recorded run directories for pass, fail, skip, and regression.

- `no_web_feature_module_or_openapi_operation_for_f067` — FR-F067-13: negative control — `apps/web/src/features/load/` does not exist, no generated client operation carries `x-opshub-feature: F067`, and no design token or route table entry references the feature.
- `report_md_has_required_sections_and_headers` — FR-F067-16: `report.md` carries `Verdict`, `Environment`, `Dataset`, `Thresholds`, `Comparison`, and `Findings`, and the two tables have header cells for metric id, statistic, value, threshold or reference, and verdict word.
- `report_renders_skip_reason_prominently` — FR-F067-11: a `skipped` run's report leads with the reason code and the sentence explaining that no gate accepts it, so a reader cannot mistake it for a pass.
- `report_marks_unconfirmed_regression_distinctly` — FR-F067-14: `regressed_unconfirmed` renders with the reference value, the regressing metric id, and the run id to compare against.
- `report_is_plain_markdown_not_an_image` — NFR-F067-05: no embedded image, no color-only signal, and every verdict is a word.
- `index_json_is_readable_without_unpacking_a_run` — FR-F067-16: the last 30 entries per profile and dataset expose status, commit, `finished_at`, and key metrics directly.

Evidence: rendered reports and index snapshots under `testing/evidence/F067/frontend/`.
