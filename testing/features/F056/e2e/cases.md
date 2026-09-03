# F056 e2e cases

File: `testing/features/F056/e2e/pivot.spec.ts`. Playwright against seeded entitled and unentitled tenants. Flag `F056_FEATURE`.

- `build_compute_materialize_open_sheet` — FR-F056-01, FR-F056-05, FR-F056-10, FR-F056-14: editor builds Owner × Status with sum(Amount), computes, sees grid, materializes, lands on the new sheet with matching totals.
- `stale_banner_after_source_edit` — FR-F056-09: second session edits an amount; first session reload shows stale banner; recompute clears it.
- `unentitled_tenant_sees_upsell` — FR-F056-04: user in the unentitled tenant opens `/w/{id}/pivots` and sees the upsell without builder.
- `viewer_reads_output_only` — FR-F056-14: viewer login sees latest output and no compute or materialize controls.
- `hidden_rows_absent_from_grid` — FR-F056-06: pivot over the report hiding 300 rows shows totals equal to the visible-row SQL reference.
- `compute_failure_shows_error_code` — FR-F056-07: source deleted mid-flow shows `source_deleted` chip and retry.

Evidence: Playwright traces and videos under `testing/evidence/F056/e2e/`.
