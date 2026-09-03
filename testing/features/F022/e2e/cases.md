# F022 e2e cases

File: `testing/features/F022/e2e/metric.spec.ts`. Playwright against seeded tenant. Flag `F022_FEATURE`.

- `define_metric_and_see_value` — FR-F022-01, FR-F022-04, FR-F022-13: editor adds "Open high risks" from the report toolbar, preview shows computing then "7 down 2 vs last week".
- `stale_badge_after_source_edit` — FR-F022-07: second session closes a risk; card shows stale badge; recompute shows 6.
- `rollup_grain_switch` — FR-F022-08: switching the preview grain from week to month re-renders 24 buckets.
- `restricted_viewer_sees_scoped_value` — FR-F022-05: restricted viewer opens the card and sees a count excluding Risks rows.
- `viewer_cannot_edit_metric` — FR-F022-11, NFR-F022-02: viewer opens the editor URL and sees read-only fields.
- `locale_formatting_in_card` — FR-F022-10: user with `de-DE` locale sees `41.000,00 €`.

Evidence: Playwright traces and videos under `testing/evidence/F022/e2e/`.
